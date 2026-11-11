#!/usr/bin/env python
"""QA Script: Asset Audit before editing (resolution, aspect, duplicates, missing coverage) - revision 2026-11-09.

Standard: ../PACING_AND_ENRICHMENT.md section 8; runs at the end of Stage 07, before 07b / 08.

Checks (each image against the CROP the plan will actually use, not just its raw size):
  MISSING_FILE      asset not found on disk                                         FAIL (WARN with --allow-missing)
  CORRUPT           file cannot be decoded                                          FAIL
  BLANK             almost uniform picture (std-dev < 6)                            FAIL
  TOO_SMALL         upscale ratio vs 1080p after the planned push > --fail-upscale  FAIL (default 2.5)
  SOFT_UPSCALE      upscale ratio > --warn-upscale (default 1.35)                   WARN (reduce zoom or add grain)
  ASPECT_PORTRAIT   portrait/square picture: 16:9 cover crops most of it            WARN (use fit + blurred plate, inset, or panel)
  ASPECT_PANORAMA   aspect >= 2.2: use mot.pan / pan_wide instead of a push         INFO
  DUPLICATE         perceptual hash distance <= --dup-hamming (default 4)           WARN, FAIL if used within 20 s of each other
  SIMILAR           distance <= --similar-hamming (default 10)                      WARN, FAIL if used within 20 s of each other
  MISSING_ASSET     slot / beat has no asset assigned                               FAIL
  COVERAGE_DEFICIT  narration time one idea has to carry exceeds the still budget   FAIL over hard cap, WARN over soft cap
  UNUSED            file in --assets-dir that no slot uses                          INFO

Outputs: asset_audit.json (with similar_pairs for still_hold_qa --assets-report), asset_audit.md, research_requests.json
(what to find: beat, text, reason, needed count). Exit 0 PASS, 1 FAIL, 2 error.

Usage:
  python asset_audit.py --assets-dir 03_media/conformed --shot-plan 06_script_edit_plan/shot_plan.json --out-json 03_media/asset_audit.json
  python asset_audit.py --beats beats.json --assign assignments.json [--beat-map beat_map.json] [--assets-root DIR]
"""
from __future__ import annotations

import argparse
import itertools
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pacing_lib as P  # noqa: E402

try:
    from PIL import Image, ImageOps, ImageStat
except ImportError:  # pragma: no cover
    print("Error: Pillow is required (pip install Pillow)", file=sys.stderr)
    sys.exit(2)

IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
VID_EXT = P.VIDEO_EXT


def dhash(img: "Image.Image") -> int:
    g = img.convert("L").resize((9, 8), Image.LANCZOS)
    px = list(g.getdata())
    bits = 0
    for r in range(8):
        for c in range(8):
            bits = (bits << 1) | (1 if px[r * 9 + c] > px[r * 9 + c + 1] else 0)
    return bits


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def probe_video(path: str) -> dict | None:
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                              "-of", "csv=p=0:s=,", path], capture_output=True, text=True, check=True).stdout.split()
        w, h = out[0].split(",")[:2]
        return {"width": int(w), "height": int(h), "duration": float(out[-1].split(",")[-1])}
    except Exception:  # noqa: BLE001
        return None


def min_visible_fraction(clip: P.Clip, lib: dict) -> float:
    """Smallest visible window (fraction of the cover-fitted frame) the planned motion reaches."""
    m = P._resolve_move(clip.motion, lib)
    mot = clip.raw.get("motion") if isinstance(clip.raw.get("motion"), dict) else {}
    rects = []
    for key in ("start_rect", "end_rect"):
        r = mot.get(key)
        if isinstance(r, list) and len(r) == 4:
            rects.append(r)
    if not rects and m:
        mv = lib["moves"][m]
        for key in ("start_rect", "end_rect"):
            r = mv.get(key)
            if isinstance(r, list):
                rects.append(r)
            elif r == "target_rect":
                t = mot.get("target_rect") or clip.raw.get("target_rect")
                rects.append(t if isinstance(t, list) and len(t) == 4 else [0, 0, 0.65, 0.65])
    if not rects and clip.motion in ("mot.push_in", "mot.pull_out"):
        rects = [[0.05, 0.05, 0.9, 0.9]]
    return min([max(r[2], r[3]) for r in rects] or [1.0])


def resolve(asset: str | None, root: str | None, registry: dict | None = None) -> str | None:
    """Find the file for a plan asset string: provider ref via the registry, as written, under --assets-root, or by basename."""
    if not asset:
        return None
    if registry and P.norm_asset(asset) in registry:
        asset = registry[P.norm_asset(asset)]
    if os.path.exists(asset):
        return asset
    if root:
        for cand in (os.path.join(root, asset), os.path.join(root, os.path.basename(asset))):
            if os.path.exists(cand):
                return os.path.normcase(os.path.abspath(cand))
    return None


def load_registry(path: str | None) -> dict:
    """asset_registry.json (Vcut 3.4): 'provider:provider_asset_id' and 'owner:<asset_id>' -> conformed_path or path."""
    if not path:
        return {}
    d = P.load_json(path)
    rows = d.get("assets", d) if isinstance(d, dict) else d
    out = {}
    for r in rows if isinstance(rows, list) else rows.values():
        p = r.get("conformed_path") or r.get("path")
        if not p:
            continue
        if r.get("provider") and r.get("provider_asset_id"):
            out[P.norm_asset(f"{r['provider']}:{r['provider_asset_id']}")] = p
        if r.get("asset_id"):
            out[P.norm_asset(r["asset_id"])] = p
            out[P.norm_asset(f"owner:{r['asset_id']}")] = p
    return out


def audit(clips, canvas, root, assets_dir, opts, lib, presets, beats=None, registry=None):
    cw, ch = canvas
    findings: list[dict] = []
    requests: list[dict] = []
    info: dict[str, dict] = {}

    def add(sev, code, where, msg, fix=""):
        findings.append({"severity": sev, "code": code, "where": where, "message": msg, "fix": fix})

    used_assets: dict[str, list[P.Clip]] = {}
    raw_of: dict[str, str] = {}
    for c in clips:
        if c.kind == "plate":
            continue
        if not c.asset:
            add("FAIL", "MISSING_ASSET", f"{c.id} @ {P.tc(c.start)}", "no asset assigned.", "Run the candidate fallback chain (stage 07), then a narration_plate.")
            requests.append({"id": c.id, "start": round(c.start, 2), "dur": round(c.dur, 2), "text": c.anchor_phrase or "", "reason": "missing", "needed": 1})
            continue
        used_assets.setdefault(c.asset, []).append(c)
        raw_of.setdefault(c.asset, c.asset_raw or c.asset)
    if assets_dir:
        # a plan name ("ok.jpg") and the scanned file of the same path are ONE asset: key by the plan string when it is used
        known = {}
        for key in list(used_assets):
            r = resolve(raw_of.get(key, key), root, registry)
            if r:
                known[os.path.normcase(os.path.abspath(r))] = key
        for d, _, fs in os.walk(assets_dir):
            for f in fs:
                ext = os.path.splitext(f)[1].lower()
                if ext in IMG_EXT | VID_EXT:
                    p = os.path.normcase(os.path.abspath(os.path.join(d, f)))
                    if p not in known:
                        used_assets.setdefault(p, [])

    hashes: dict[str, int] = {}
    for asset, cl in used_assets.items():
        path = resolve(raw_of.get(asset, asset), root, registry)
        rec: dict = {"path": path, "clips": [c.id for c in cl]}
        info[asset] = rec
        if not path:
            sev = "WARN" if opts["allow_missing"] else "FAIL"
            add(sev, "MISSING_FILE", ", ".join(c.id for c in cl[:4]) or asset, f"asset not found on disk: {asset}", "Re-acquire or swap (stage 07 fallback chain).")
            for c in cl:
                requests.append({"id": c.id, "start": round(c.start, 2), "dur": round(c.dur, 2), "text": c.anchor_phrase or "", "reason": "missing_file", "needed": 1})
            continue
        ext = os.path.splitext(path)[1].lower()
        if ext in VID_EXT:
            pv = probe_video(path)
            rec.update({"kind": "video", **(pv or {})})
            if pv and (pv["width"] < cw or pv["height"] < ch):
                add("WARN", "SOFT_UPSCALE", asset, f"video is {pv['width']}x{pv['height']} (< {cw}x{ch}).", "Prefer a 1080p source or use it brief and muted.")
            if pv:
                for c in cl:
                    if c.dur > pv["duration"] + 0.05:
                        add("FAIL", "COVERAGE_DEFICIT", c.id, f"slot needs {c.dur:.1f}s but the clip is {pv['duration']:.1f}s.", "Pick a longer clip or split the slot.")
            continue
        try:
            with Image.open(path) as im0:
                im = ImageOps.exif_transpose(im0)
                im.load()
                iw, ih = im.size
                sd = sum(ImageStat.Stat(im.convert("L")).stddev)
                h = dhash(im)
        except Exception as e:  # noqa: BLE001
            add("FAIL", "CORRUPT", asset, f"cannot decode image: {e}", "Re-download.")
            continue
        hashes[asset] = h
        ar = iw / ih
        rec.update({"kind": "image", "width": iw, "height": ih, "aspect": round(ar, 3), "stddev": round(sd, 1)})
        if sd < 6.0:
            add("FAIL", "BLANK", asset, "picture is almost uniform (blank or failed render).", "Replace.")
        cover = max(cw / iw, ch / ih)
        worst = 1.0
        for c in cl:
            f = min_visible_fraction(c, lib)
            worst = max(worst, cover / f)
        if not cl:
            worst = cover
        rec["upscale"] = round(worst, 2)
        if worst > opts["fail_upscale"]:
            add("FAIL", "TOO_SMALL", f"{os.path.basename(path)} {iw}x{ih}", f"needs {worst:.2f}x upscale at {cw}x{ch} after the planned move.", "Find a larger copy, or reduce zoom (push_slow), or place it small on a plate/panel.")
            for c in cl:
                requests.append({"id": c.id, "start": round(c.start, 2), "dur": round(c.dur, 2), "text": c.anchor_phrase or "", "reason": f"too_small {iw}x{ih}", "needed": 1})
        elif worst > opts["warn_upscale"]:
            add("WARN", "SOFT_UPSCALE", f"{os.path.basename(path)} {iw}x{ih}", f"needs {worst:.2f}x upscale; will look soft.", "Cap the push to push_slow, add film grain, or swap.")
        target = cw / ch
        vis = min(ar / target, target / ar)  # share of the picture that survives a cover-fit to the canvas
        if vis < 0.6:
            add("WARN", "ASPECT_PORTRAIT", f"{os.path.basename(path)} {iw}x{ih}", f"aspect {ar:.2f}: a {cw}x{ch} cover crop keeps only {vis:.0%} of the picture.", "Use fit + blurred background plate, or people-panel / inset on a texture plate.")
        elif ar >= target * 1.24:
            add("INFO", "ASPECT_PANORAMA", f"{os.path.basename(path)} {iw}x{ih}", f"aspect {ar:.2f}: wide.", "Use pan_wide / drift, not a push.")

    # duplicates
    pairs = []
    keys = list(hashes)
    for a, b in itertools.combinations(keys, 2):
        d = hamming(hashes[a], hashes[b])
        if d <= opts["similar_hamming"]:
            pairs.append([a, b, d])
    for a, b, d in pairs:
        close = False
        for ca in used_assets.get(a, []):
            for cb in used_assets.get(b, []):
                if max(0.0, cb.start - ca.end, ca.start - cb.end) < 20.0:  # on-screen gap between the two uses
                    close = True
        code = "DUPLICATE" if d <= opts["dup_hamming"] else "SIMILAR"
        sev = "FAIL" if close else "WARN"
        add(sev, code, f"{os.path.basename(a)} ~ {os.path.basename(b)}", f"perceptual distance {d}/64" + (" and used within 20 s of each other." if close else "."),
            "Keep one. Two pictures of the same idea back to back read as one long hold.")

    # coverage deficit (one idea has to carry too much narration)
    sim_set = {frozenset((P.norm_asset(a), P.norm_asset(b))) for a, b, _ in pairs}
    sim = (lambda a, b: frozenset((a, b)) in sim_set)
    for r in P.build_runs(clips, lib, sim):
        lim = P.run_limits(r, presets, opts["preset"])
        if r.dur > lim["hard"] + 1e-6:
            need = P.needed_distinct_assets(r.dur, lim["soft"])
            add("FAIL", "COVERAGE_DEFICIT", f"{r.clips[0].id} @ {P.tc(r.start)}", f"{r.dur:.1f}s of narration rests on {len(r.assets)} picture(s) of ONE idea (hard cap {lim['hard']:.1f}s).",
                f"Source >= {need - 1} more distinct shot(s) or build plates (map / card / quote / narration_plate).")
            requests.append({"id": r.clips[0].id, "start": round(r.start, 2), "dur": round(r.dur, 2), "text": r.clips[0].anchor_phrase or "", "reason": "coverage_deficit", "needed": need - 1})
        elif r.dur > lim["soft"] + 1e-6:
            add("WARN", "COVERAGE_DEFICIT", f"{r.clips[0].id} @ {P.tc(r.start)}", f"{r.dur:.1f}s on one idea (soft cap {lim['soft']:.1f}s): needs enrichment events or a second shot.")
    if beats:
        assigned = {c.id.split(".")[0] for c in clips}
        for b in beats:
            if not b.get("locked") and b["id"] not in assigned:
                add("FAIL", "MISSING_ASSET", f"{b['id']} @ {P.tc(b['start'])}", "beat has no assignment.", "Research or fallback chain.")
                requests.append({"id": b["id"], "start": b["start"], "dur": b.get("dur"), "text": b.get("text", ""), "reason": "missing", "needed": 1})
    if assets_dir:
        for asset, cl in used_assets.items():
            if not cl:
                add("INFO", "UNUSED", os.path.basename(asset), "in the assets folder but not used by any slot.")
    # beat text for requests
    if beats:
        txt = {b["id"]: b.get("text", "") for b in beats}
        for q in requests:
            if not q["text"]:
                q["text"] = txt.get(q["id"].split(".")[0], "")
    return findings, requests, info, pairs


def main() -> None:
    ap = argparse.ArgumentParser(description="Asset audit: resolution, aspect, duplicates, missing coverage.")
    ap.add_argument("--assets-dir")
    ap.add_argument("--assets-root", help="folder for relative asset names in the plan")
    ap.add_argument("--registry", help="asset_registry.json: maps provider refs (pexels:123, owner:img_01) to their conformed files")
    ap.add_argument("--shot-plan")
    ap.add_argument("--beats")
    ap.add_argument("--assign")
    ap.add_argument("--beat-map")
    ap.add_argument("--canvas", default="1920x1080")
    ap.add_argument("--preset")
    ap.add_argument("--warn-upscale", type=float, default=1.35)
    ap.add_argument("--fail-upscale", type=float, default=2.5)
    ap.add_argument("--dup-hamming", type=int, default=4)
    ap.add_argument("--similar-hamming", type=int, default=10)
    ap.add_argument("--allow-missing", action="store_true")
    ap.add_argument("--out-json")
    ap.add_argument("--out-md")
    ap.add_argument("--requests-out")
    a = ap.parse_args()
    try:
        cw, ch = (int(x) for x in a.canvas.lower().split("x"))
        beats = None
        if a.shot_plan:
            clips = P.load_clips_shot_plan(a.shot_plan, a.beat_map)
        elif a.beats and a.assign:
            clips = P.load_clips_beats(a.beats, a.assign, a.beat_map)
            beats = P.load_json(a.beats)
        elif a.assets_dir:
            clips = []
        else:
            print("Error: give --shot-plan, or --beats and --assign, or --assets-dir", file=sys.stderr)
            sys.exit(2)
        lib, presets = P.load_motion_library(), P.load_presets()
        opts = {"warn_upscale": a.warn_upscale, "fail_upscale": a.fail_upscale, "dup_hamming": a.dup_hamming,
                "similar_hamming": a.similar_hamming, "allow_missing": a.allow_missing, "preset": a.preset}
        root = a.assets_root or a.assets_dir
        findings, requests, info, pairs = audit(clips, (cw, ch), root, a.assets_dir, opts, lib, presets, beats, load_registry(a.registry))
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        print(f"Asset audit error: {e}", file=sys.stderr)
        sys.exit(2)
    fails = [f for f in findings if f["severity"] == "FAIL"]
    status = "FAIL" if fails else "PASS"
    payload = {"tool": "asset_audit", "revision": "2026-11-09", "canvas": [cw, ch], "overall_status": status, "assets_checked": len(info),
               "fail_count": len(fails), "warn_count": sum(1 for f in findings if f["severity"] == "WARN"),
               "similar_pairs": pairs, "findings": findings, "assets": info, "research_requests": requests}
    L = [f"# Asset Audit: **{status}**", "", f"{len(info)} assets | canvas {cw}x{ch} | {len(fails)} fail | {payload['warn_count']} warn | {len(requests)} research request(s)", ""]
    for sev in ("FAIL", "WARN", "INFO"):
        rows = [f for f in findings if f["severity"] == sev]
        if rows:
            L += [f"## {sev}", "", "| Code | Where | Problem | Fix |", "|---|---|---|---|"] + [f"| {f['code']} | {f['where']} | {f['message']} | {f['fix']} |" for f in rows] + [""]
    if requests:
        L += ["## Research requests", "", "| Id | At | Dur | Reason | Need | Narration |", "|---|---|---|---|---|---|"]
        L += [f"| {q['id']} | {P.tc(q['start'])[3:8]} | {q['dur']} | {q['reason']} | {q['needed']} | {(q['text'] or '')[:70]} |" for q in requests]
    P.write_report(a.out_json, a.out_md, payload, "\n".join(L) + "\n")
    if a.requests_out:
        P.write_report(a.requests_out, None, {"requests": requests}, "")
    print(f"Asset audit: {status} | {len(info)} assets | {len(fails)} fail, {payload['warn_count']} warn | {len(requests)} research request(s)"
          + (f" -> {a.out_json}" if a.out_json else ""))
    if not (a.out_json or a.out_md):
        print("\n".join(L)[:3000])
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
