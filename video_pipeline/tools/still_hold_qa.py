#!/usr/bin/env python
"""QA Script: Still-Hold Budget (no image stays on screen too long) - revision 2026-11-09.

Standard: ../PACING_AND_ENRICHMENT.md section 2. Limits come from ../presets/pacing/pacing_presets.json.

A STILL RUN is the uninterrupted time one picture (or several pictures of the same asset_group / near-duplicates) is on
screen, ended only by a distinct shot: different picture, footage, or a full-frame plate (map, card, quote...). Ken Burns,
crop changes and overlays do not reset it.

FAIL rules
  STILL_HARD    run longer than the preset hard cap (documentary_standard: 6.0 s; slow 8.0; tense 4.5), scaled down on
                high-intensity beats. Fix: add distinct shots (cutaway, plate); never return to an earlier picture.
  STILL_SOFT    run longer than the soft cap (4.5 s) whose longest event-free interval exceeds the preset's enrich_gap_s.
                Fix: add an enrichment event (detail crop, annotation, keyword...) at the suggested time, or cut.
  (waiver)      an OWNER can waive one run with "still_hold_waiver": "<reason>" on a clip (shot plan slot or assignment row).
                The waiver is honoured ONLY when this tool is started with --allow-waivers (the owner's flag, never an agent's):
                the FAIL becomes WARN STILL_WAIVED. Without the flag the FAIL stands and a WAIVER_IGNORED warning is added.
  PLATE_HOLD    a full-frame plate on screen longer than 8.0 s (reading plates included)
  NO_MOTION     a still with no motion assignment (every slot needs an effect), when the plan carries motion data at all.
  REUSE         the same still appears in two separate runs (owner rule 2026-11-08: every visual once, never A-B-A).
                --allow-reuse downgrades this to WARN.
WARN rules
  PLATE_LONG    plate longer than the preset's card length + 1 s;  PLATE_UNTYPED  plate without plate_type / recognisable graphic fields
  MEDIA_TYPE    media_type "video" declared on a picture file (counted as a still)
  WEAK_RECOMPOSE a detail_crop / reveal that does not re-frame by >= 35 % of the area (or has no target_rect): not counted as an event
  GROUP_MERGE   one run contains several different pictures of the same idea (this is how a 12 s hold hides).
  EVENT_TIME    enrichment events without a time (assumed at the clip start, so they cover only the first moments).
  UNKNOWN_TYPE  enrichment type not in enrichment_catalog.json (counted as no event).
  MEDIA_GAP     (--media) rendered video has no scene change for longer than the hard cap (heuristic; verify by eye).

Writes JSON + Markdown. Exit 0 PASS, 1 FAIL, 2 usage/processing error.

Usage:
  python still_hold_qa.py --shot-plan shot_plan.json [--preset documentary_standard] [--assets-report asset_audit.json]
  python still_hold_qa.py --beats beats.json --assign assignments.json [--beat-map beat_map.json]
  python still_hold_qa.py ... --media cut.mp4 --out-json qa_still_hold.json --out-md qa_still_hold.md
"""
from __future__ import annotations

import argparse
import math
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pacing_lib as P  # noqa: E402


def media_cut_gaps(media: str, threshold: float) -> tuple[list[float], float]:
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", media],
                               capture_output=True, text=True, check=True).stdout.strip())
    proc = subprocess.run(["ffmpeg", "-v", "info", "-i", media, "-vf", f"select='gt(scene,{threshold})',showinfo", "-an", "-f", "null", "-"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-600:])
    cuts = [float(m.group(1)) for m in re.finditer(r"pts_time:([\d.]+)", proc.stderr)]
    return sorted(set(cuts)), dur


def similar_from_report(path: str | None):
    if not path:
        return None
    rep = P.load_json(path)
    nset = {frozenset((P.norm_asset(p[0]), P.norm_asset(p[1]))) for p in rep.get("similar_pairs", [])}
    return lambda a, b: frozenset((a, b)) in nset


def evaluate(clips, presets, lib, cat, default_preset, similar=None, allow_reuse=False, allow_waivers=False):
    runs = P.build_runs(clips, lib, similar)
    counting = P.counting_types(cat, lib)
    findings: list[dict] = []
    table: list[dict] = []

    def add(sev, code, where, msg, fix=""):
        findings.append({"severity": sev, "code": code, "where": where, "message": msg, "fix": fix})

    plan_has_motion = any(c.motion for c in clips if c.kind == "still")
    for r in runs:
        lim = P.run_limits(r, presets, default_preset)
        label = f"{r.clips[0].id}" + (f"..{r.clips[-1].id}" if len(r.clips) > 1 else "")
        where = f"{label} @ {P.tc(r.start)}-{P.tc(r.end)} ({r.dur:.1f}s)"
        gap, mid = P.longest_gap(r, counting)
        waiver = next((c.raw.get("still_hold_waiver") for c in r.clips if c.raw.get("still_hold_waiver")), None)
        row = {"run": label, "start": round(r.start, 3), "end": round(r.end, 3), "dur": round(r.dur, 2), "assets": len(r.assets),
               "events": len([e for e in r.events if e.type in counting]), "longest_gap": round(gap, 2), **lim, "status": "PASS"}
        broken = r.dur > lim["hard"] + 1e-6 or (r.dur > lim["soft"] + 1e-6 and gap > lim["gap"] + 1e-6)
        if waiver and broken and not allow_waivers:
            add("WARN", "WAIVER_IGNORED", where, f"a still_hold_waiver is present ({waiver}) but --allow-waivers was not given; it has no effect.")
        for w in r.warnings:
            add("WARN", "WEAK_RECOMPOSE", where, w)
        if waiver and allow_waivers and broken:
            add("WARN", "STILL_WAIVED", where, f"{r.dur:.1f}s still waived by the owner: {waiver}")
            row["status"] = "WAIVED"
        elif r.dur > lim["hard"] + 1e-6:
            n = P.needed_distinct_assets(r.dur, lim["soft"])
            cuts = ", ".join(P.tc(r.start + k * r.dur / n)[3:8] for k in range(1, n))
            add("FAIL", "STILL_HARD", where,
                f"still held {r.dur:.1f}s > hard cap {lim['hard']:.1f}s ({lim['preset']}, intensity {lim['intensity']}).",
                f"Need >= {n} distinct shots; place a cutaway or full-frame plate on the words that change topic (about {cuts}). "
                "Never return to an earlier picture. Fix order: enrichment_catalog.json fix_order_for_long_still.")
            row["status"] = "FAIL"
        elif r.dur > lim["soft"] + 1e-6 and gap > lim["gap"] + 1e-6:
            add("FAIL", "STILL_SOFT", where,
                f"still held {r.dur:.1f}s > soft cap {lim['soft']:.1f}s with an event-free stretch of {gap:.1f}s (limit {lim['gap']:.1f}s).",
                f"Add a tier A/B enrichment event around {P.tc(mid)[3:8]} (detail crop, annotation, keyword) or cut to a second shot.")
            row["status"] = "FAIL"
        if len(r.assets) > 1:
            add("WARN", "GROUP_MERGE", where, f"{len(r.assets)} pictures of the same idea share one run; the viewer sees one long hold.",
                "Treat as one still for the cap. Replace the weaker picture with a different idea or footage.")
        inferred = [e for e in r.events if e.inferred]
        if inferred and r.dur > lim["soft"]:
            add("WARN", "EVENT_TIME", where, f"{len(inferred)} enrichment event(s) have no time; assumed at the clip start.",
                "Give each event at_ms (anchored to the spoken word).")
        for e in r.events:
            if e.type not in cat["types"] and e.type not in lib["moves"]:
                add("WARN", "UNKNOWN_TYPE", where, f"enrichment type '{e.type}' not in enrichment_catalog.json (counted as no event).")
        table.append(row)

    cfg = P.preset_for(default_preset, presets)[1]
    for c in clips:
        for fl in c.flags:
            if fl == "media_type_mismatch":
                add("WARN", "MEDIA_TYPE", f"{c.id} @ {P.tc(c.start)}", "declared video but the file is a picture; counted as a still.")
        if c.kind == "plate":
            pcfg = P.preset_for(c.preset or default_preset, presets)[1]
            if c.dur > presets["still_policy"]["reading_plate_hard_max_s"] + 1e-6:
                add("FAIL", "PLATE_HOLD", f"{c.id} @ {P.tc(c.start)} ({c.dur:.1f}s)", f"plate on screen {c.dur:.1f}s > {presets['still_policy']['reading_plate_hard_max_s']:.1f}s.",
                    "Split the plate (second card, cutaway) or shorten it.")
            elif c.dur > pcfg["card_s"][1] + 1.0:
                add("WARN", "PLATE_LONG", f"{c.id} @ {P.tc(c.start)}", f"plate {c.dur:.1f}s is long for the {pcfg['card_s']} s card range.")
            if not c.plate_type:
                add("WARN", "PLATE_UNTYPED", f"{c.id} @ {P.tc(c.start)}", "plate has no plate_type / map / article / extras fields; a mislabelled picture would dodge the still cap.",
                    "Set plate_type (map, article_card, quote_card, stat_plate, narration_plate...).")
    if plan_has_motion:
        for c in clips:
            if c.kind == "still" and not c.motion:
                add("FAIL", "NO_MOTION", f"{c.id} @ {P.tc(c.start)}", "still has no motion assignment.",
                    "Pick a move from motion_library.json (pacing_lib.pick_motion).")
    seen: dict[str, list[int]] = {}
    for i, r in enumerate(runs):
        for a in r.assets:
            seen.setdefault(a, []).append(i)
    for a, idx in seen.items():
        if len(idx) > 1:
            first, other = runs[idx[0]], runs[idx[1]]
            ping = idx[1] - idx[0] == 2
            add("WARN" if allow_reuse else "FAIL", "REUSE", f"{first.clips[0].id} / {other.clips[0].id}",
                f"{os.path.basename(a)} appears in {len(idx)} separate runs{' (A-B-A ping-pong)' if ping else ''}.",
                "Owner rule: every visual once. Replace the repeat with a new asset or a plate.")
    stills = [c for c in clips if c.kind == "still"]
    summary = {
        "clips": len(clips), "stills": len(stills), "still_runs": len(runs),
        "longest_run_s": round(max([r.dur for r in runs] or [0]), 2),
        "runs_over_soft": sum(1 for t in table if t["dur"] > t["soft"]),
        "runs_failed": sum(1 for t in table if t["status"] == "FAIL"),
        "events_total": sum(t["events"] for t in table),
    }
    return findings, table, summary


def render_md(status, args_desc, summary, table, findings, media_note):
    L = [f"# Still-Hold Budget QA: **{status}**", "", args_desc, "",
         f"clips {summary['clips']} | stills {summary['stills']} | still runs {summary['still_runs']} | longest run **{summary['longest_run_s']}s** "
         f"| runs over soft cap {summary['runs_over_soft']} | failing runs {summary['runs_failed']}", ""]
    if media_note:
        L += [media_note, ""]
    fails = [f for f in findings if f["severity"] == "FAIL"]
    warns = [f for f in findings if f["severity"] == "WARN"]
    if fails:
        L += ["## FAIL", "", "| Code | Where | Problem | Fix |", "|---|---|---|---|"]
        L += [f"| {f['code']} | {f['where']} | {f['message']} | {f['fix']} |" for f in fails] + [""]
    if warns:
        L += ["## WARN", "", "| Code | Where | Problem |", "|---|---|---|"] + [f"| {f['code']} | {f['where']} | {f['message']} |" for f in warns] + [""]
    long_rows = sorted([t for t in table if t["dur"] > t["soft"]], key=lambda t: -t["dur"])[:25]
    if long_rows:
        L += ["## Longest still runs", "", "| Run | Start | Dur (s) | Soft | Hard | Events | Longest gap | Status |", "|---|---|---|---|---|---|---|---|"]
        L += [f"| {t['run']} | {P.tc(t['start'])} | {t['dur']} | {t['soft']} | {t['hard']} | {t['events']} | {t['longest_gap']} | {t['status']} |" for t in long_rows]
    if not fails:
        L += ["", "> No still run breaks the budget."]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Still-hold budget QA (no image on screen too long).")
    ap.add_argument("--shot-plan")
    ap.add_argument("--beats")
    ap.add_argument("--assign")
    ap.add_argument("--beat-map")
    ap.add_argument("--preset", help="default preset (pacing_presets.json); clips may override with their own 'preset'")
    ap.add_argument("--presets-file")
    ap.add_argument("--assets-report", help="asset_audit.json: its similar_pairs merge near-duplicate stills into one run")
    ap.add_argument("--allow-reuse", action="store_true")
    ap.add_argument("--allow-waivers", action="store_true", help="OWNER ONLY: honour still_hold_waiver fields (agents must not pass this)")
    ap.add_argument("--media", help="rendered cut; heuristic scene-change gap scan")
    ap.add_argument("--scene-threshold", type=float, default=0.30)
    ap.add_argument("--out-json")
    ap.add_argument("--out-md")
    a = ap.parse_args()
    try:
        if a.shot_plan:
            clips = P.load_clips_shot_plan(a.shot_plan, a.beat_map)
            src = a.shot_plan
        elif a.beats and a.assign:
            clips = P.load_clips_beats(a.beats, a.assign, a.beat_map)
            src = f"{a.beats} + {a.assign}"
        else:
            print("Error: give --shot-plan or --beats and --assign", file=sys.stderr)
            sys.exit(2)
        presets = P.load_presets(a.presets_file)
        lib, cat = P.load_motion_library(), P.load_catalog()
        similar = similar_from_report(a.assets_report)
        findings, table, summary = evaluate(clips, presets, lib, cat, a.preset, similar, a.allow_reuse, a.allow_waivers)
        media_note = ""
        if a.media:
            hard = P.preset_for(a.preset, presets)[1]["still_hard_max_s"]
            cuts, dur = media_cut_gaps(a.media, a.scene_threshold)
            pts = [0.0] + cuts + [dur]
            gaps = [(b - x, x, b) for x, b in zip(pts, pts[1:]) if b - x > hard]
            for g, x, b in gaps:
                findings.append({"severity": "WARN", "code": "MEDIA_GAP", "where": f"{P.tc(x)}-{P.tc(b)} ({g:.1f}s)",
                                 "message": f"no scene change for {g:.1f}s in the rendered video (> {hard:.1f}s); possible overlong still.",
                                 "fix": "Verify by eye. Heuristic: dissolves and Ken Burns can hide cuts."})
            media_note = f"Rendered-video scan: {len(cuts)} scene changes at threshold {a.scene_threshold}; {len(gaps)} gap(s) over {hard:.1f}s."
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        print(f"Still-hold QA error: {e}", file=sys.stderr)
        sys.exit(2)
    fails = [f for f in findings if f["severity"] == "FAIL"]
    status = "FAIL" if fails else "PASS"
    payload = {"tool": "still_hold_qa", "revision": "2026-11-09", "source": src, "preset": a.preset or presets["default_preset"],
               "overall_status": status, "summary": summary, "runs": table, "findings": findings}
    md = render_md(status, f"Source: `{src}` | preset: `{payload['preset']}`", summary, table, findings, media_note)
    P.write_report(a.out_json, a.out_md, payload, md)
    print(f"Still-hold QA: {status} | longest run {summary['longest_run_s']}s | {len(fails)} fail, "
          f"{len(findings) - len(fails)} warn" + (f" -> {a.out_json}" if a.out_json else ""))
    if not (a.out_json or a.out_md):
        print(md[:3000])
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
