#!/usr/bin/env python
"""Variation tracking + Edit Report with rationale (revision 2026-11-09).

Standard: ../PACING_AND_ENRICHMENT.md sections 7 and 9. Reads the same plan inputs as still_hold_qa.py.

Writes variation_log.json (motions, transitions, SFX, enrichments with times) and edit_report.md (summary, flags,
rationale table, owner review prompts, feedback block that feeds the style memory).

FAIL rules (exit 1)
  MOTION_RUN        same motion on more than max_consecutive_same_move stills in a row (default 2 -> the 3rd identical fails)
  TRANSITION_RUN    same DYNAMIC transition on 3 consecutive cuts
  TRANSITION_BUDGET dynamic transitions above the preset budget (per 10 min, scaled to the video length)
  ENRICH_CAP        a tier B/C enrichment type above its cap_per_10min in any 10-minute window (map + map_overlay share one cap)
WARN rules
  DIRECTION_RUN     same lateral drift direction 3 times in a row
  MOTION_SHARE      one move above 35 % of the stills (10+ stills)
  CUT_SHARE         hard-cut share below the preset minimum
  SFX_REPEAT        same SFX file twice within 20 s
  SHOT_LENGTH       more than 25 % of shots outside the preset's shot range (scaled by beat intensity)
  EMOTION_MOTION    motion on the emotion's avoid list (e.g. punch_in on a grief beat)
  NO_RATIONALE      a major creative choice without a rationale (dynamic transition, plate, tier C/D enrichment, intensity >= 4, 'major')

Usage:
  python variation_report.py --shot-plan shot_plan.json --out-json variation_log.json --out-md edit_report.md [--preset tense_fast]
  python variation_report.py --beats beats.json --assign assignments.json [--beat-map beat_map.json]
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pacing_lib as P  # noqa: E402

CAP_GROUPS = {"map": "map", "map_overlay": "map"}


def window_counts(times: list[float], width: float = 600.0) -> int:
    ts = sorted(times)
    best, j = 0, 0
    for i, t in enumerate(ts):
        while ts[j] < t - width:
            j += 1
        best = max(best, i - j + 1)
    return best


def analyse(clips, presets, lib, cat, default_preset):
    findings: list[dict] = []

    def add(sev, code, where, msg):
        findings.append({"severity": sev, "code": code, "where": where, "message": msg})

    total = max([c.end for c in clips] or [0.0])
    stills = [c for c in clips if c.kind == "still"]
    pname, pcfg = P.preset_for(default_preset, presets)
    rules = lib["selection_rules"]

    # motion
    mlog = []
    for c in stills:
        mv = P._resolve_move(c.motion, lib) or c.motion
        d = lib["moves"][mv]["direction"] if mv in lib["moves"] else None
        mlog.append({"id": c.id, "start": round(c.start, 2), "move": mv, "direction": d, "emotion": c.emotion, "intensity": c.intensity})
    run, prev = 0, None
    for m in mlog:
        if m["move"] and m["move"] == prev:
            run += 1
        else:
            run, prev = 1, m["move"]
        if m["move"] and run > rules["max_consecutive_same_move"]:
            add("FAIL", "MOTION_RUN", f"{m['id']} @ {P.tc(m['start'])}", f"'{m['move']}' used {run} times in a row (max {rules['max_consecutive_same_move']}).")
    drun, pd = 0, None
    for m in mlog:
        if m["direction"] in ("left", "right") and m["direction"] == pd:
            drun += 1
        else:
            drun, pd = 1, m["direction"]
        if drun == 2 and m["direction"] in ("left", "right"):
            add("WARN", "DIRECTION_RUN", f"{m['id']} @ {P.tc(m['start'])}", f"drift {m['direction']} twice in a row (rule: never the same lateral direction twice).")
    mc = Counter(m["move"] for m in mlog if m["move"])
    if len(stills) >= 10:
        for mv, n in mc.items():
            if n / len(stills) > rules["max_share_of_stills"]:
                add("WARN", "MOTION_SHARE", mv, f"'{mv}' is {n / len(stills):.0%} of stills (cap {rules['max_share_of_stills']:.0%}).")
    for c, m in zip(stills, mlog):
        avoid = presets["emotions"].get(c.emotion or "", {}).get("avoid_motions", [])
        if m["move"] in avoid:
            add("WARN", "EMOTION_MOTION", f"{c.id} @ {P.tc(c.start)}", f"'{m['move']}' on a {c.emotion} beat (avoid list).")

    # transitions
    tlog = []
    for c in clips:
        t = (c.transition_in or "cut").lower()
        t = "cut" if t in ("hard_cut", "hard cut", "none", "cut") else t
        tlog.append({"id": c.id, "start": round(c.start, 2), "type": t})
    dyn = [t for t in tlog if t["type"] != "cut"]
    cut_share = 1 - len(dyn) / max(1, len(tlog))
    if tlog and cut_share + 1e-9 < pcfg["hard_cut_share_min"]:
        add("WARN", "CUT_SHARE", pname, f"hard cuts are {cut_share:.0%} of transitions (preset minimum {pcfg['hard_cut_share_min']:.0%}).")
    allowed_dyn = pcfg["max_dynamic_transitions_per_10min"] * (total / 600.0 if total < 600 else 1.0)
    allowed_dyn = max(1, math.ceil(allowed_dyn))
    if window_counts([t["start"] for t in dyn]) > allowed_dyn:
        add("FAIL", "TRANSITION_BUDGET", pname, f"{window_counts([t['start'] for t in dyn])} dynamic transitions in a 10-minute window (budget {allowed_dyn}).")
    for i in range(2, len(tlog)):
        a, b, c3 = tlog[i - 2], tlog[i - 1], tlog[i]
        if a["type"] != "cut" and a["type"] == b["type"] == c3["type"]:
            add("FAIL", "TRANSITION_RUN", f"{c3['id']} @ {P.tc(c3['start'])}", f"'{a['type']}' on 3 consecutive cuts.")

    # sfx
    slog = []
    for c in clips:
        for s in c.sfx:
            slog.append({"id": c.id, "start": round(c.start, 2), "sfx": s})
    last: dict[str, float] = {}
    for s in sorted(slog, key=lambda x: x["start"]):
        if s["sfx"] in last and s["start"] - last[s["sfx"]] < 20.0:
            add("WARN", "SFX_REPEAT", f"{s['id']} @ {P.tc(s['start'])}", f"'{s['sfx']}' repeated after {s['start'] - last[s['sfx']]:.0f}s.")
        last[s["sfx"]] = s["start"]

    # enrichments
    elog = []
    for c in clips:
        for e in c.events:
            elog.append({"id": c.id, "t": round(e.t, 2), "type": e.type})
        mt = P.motion_event_type(c.motion, lib)
        if mt and not any(e.type == mt for e in c.events):
            elog.append({"id": c.id, "t": round(c.motion_at if c.motion_at is not None else c.start + c.dur / 2, 2), "type": mt})
        if c.kind == "plate":
            elog.append({"id": c.id, "t": round(c.start, 2), "type": (c.plate_type or "plate")})
    by_group: dict[str, list[float]] = {}
    for e in elog:
        g = CAP_GROUPS.get(e["type"], e["type"])
        by_group.setdefault(g, []).append(e["t"])
    for g, ts in by_group.items():
        cap = cat["types"].get(g, {}).get("cap_per_10min")
        if cap is None:
            continue
        if pname == "shorts_vertical" and g in ("keyword_pop", "punch_in"):
            continue  # Shorts use a keyword on every second shot by design
        allowed = cap if total >= 600 else max(1, math.ceil(cap * total / 600.0))
        if window_counts(ts) > allowed:
            add("FAIL", "ENRICH_CAP", g, f"{window_counts(ts)} x '{g}' in a 10-minute window (cap {allowed}).")

    # shot lengths
    out = 0
    for c in clips:
        cp = P.preset_for(c.preset or default_preset, presets)[1]
        lo, hi = cp["card_s"] if c.kind == "plate" else cp["shot_s"]
        sc = presets["intensity_scale"].get(str(int(c.intensity or 3)), {"shot_scale": 1.0})["shot_scale"]
        if c.dur < lo * min(1.0, sc) - 0.15 or c.dur > hi * sc + 0.15:
            out += 1
    if clips and out / len(clips) > 0.25:
        add("WARN", "SHOT_LENGTH", pname, f"{out}/{len(clips)} shots ({out / len(clips):.0%}) outside the {pname} range {pcfg['shot_s']} s.")

    # rationale
    majors = []
    for c in clips:
        reasons = []
        if (c.transition_in or "cut").lower() not in ("cut", "hard_cut", "hard cut", "none"):
            reasons.append(f"transition {c.transition_in}")
        if c.kind == "plate":
            reasons.append("full-frame plate")
        for e in c.events:
            t = cat["types"].get(e.type, {}).get("tier")
            if t in ("C", "D"):
                reasons.append(f"{e.type}")
        if (c.intensity or 0) >= 4:
            reasons.append(f"intensity {c.intensity}")
        if c.preset:
            reasons.append(f"preset override {c.preset}")
        if c.major:
            reasons.append("flagged major")
        if reasons:
            majors.append({"id": c.id, "start": round(c.start, 2), "choice": "; ".join(reasons), "rationale": c.rationale or "", "anchor": c.anchor_phrase or ""})
    missing = [m for m in majors if not m["rationale"]]
    if missing:
        add("WARN", "NO_RATIONALE", f"{len(missing)} clip(s)", "major choices without a rationale: " + ", ".join(m["id"] for m in missing[:12]) + (" ..." if len(missing) > 12 else ""))

    runs = P.build_runs(clips, lib)
    counting = P.counting_types(cat, lib)
    longest = max([r.dur for r in runs] or [0.0])
    stats = {
        "duration_s": round(total, 1), "clips": len(clips), "stills": len(stills), "videos": sum(1 for c in clips if c.kind == "video"),
        "plates": sum(1 for c in clips if c.kind == "plate"), "longest_still_run_s": round(longest, 2),
        "mean_shot_s": round(sum(c.dur for c in clips) / max(1, len(clips)), 2), "hard_cut_share": round(cut_share, 3),
        "motions_used": dict(mc), "enrichment_events": sum(1 for e in elog if e["type"] in counting),
    }
    return findings, {"motion_log": mlog, "transition_log": tlog, "sfx_log": slog, "enrichment_log": elog, "rationale": majors, "stats": stats}, pname, pcfg


def render_md(status, src, pname, findings, log, cat) -> str:
    s = log["stats"]
    L = [f"# Edit Report: **{status}**", "", f"Source `{src}` | preset `{pname}`", "",
         "## 1. Summary", "",
         f"- Duration {s['duration_s']}s | {s['clips']} shots ({s['stills']} stills, {s['videos']} footage, {s['plates']} plates) | mean shot {s['mean_shot_s']}s",
         f"- Longest still run **{s['longest_still_run_s']}s** | enrichment events {s['enrichment_events']} | hard cuts {s['hard_cut_share']:.0%}",
         "- Motions used: " + (", ".join(f"{k} x{v}" for k, v in sorted(s["motions_used"].items(), key=lambda kv: -kv[1])) or "none logged"), ""]
    fails = [f for f in findings if f["severity"] == "FAIL"]
    warns = [f for f in findings if f["severity"] == "WARN"]
    L += ["## 2. Flags", ""]
    if not findings:
        L += ["No variation problems found.", ""]
    else:
        L += ["| Severity | Code | Where | Problem |", "|---|---|---|---|"] + [f"| {f['severity']} | {f['code']} | {f['where']} | {f['message']} |" for f in fails + warns] + [""]
    L += ["## 3. Creative choices and why", ""]
    if log["rationale"]:
        L += ["| Shot | Time | Choice | Narration anchor | Why |", "|---|---|---|---|---|"]
        L += [f"| {m['id']} | {P.tc(m['start'])[3:8]} | {m['choice']} | {m['anchor'][:40]} | {m['rationale'] or '**missing**'} |" for m in log["rationale"]]
    else:
        L += ["No major choices recorded."]
    L += ["", "## 4. Enrichment ledger", ""]
    cnt = Counter(e["type"] for e in log["enrichment_log"])
    if cnt:
        L += ["| Type | Tier | Count | Cap / 10 min |", "|---|---|---|---|"]
        L += [f"| {k} | {cat['types'].get(k, {}).get('tier', '?')} | {v} | {cat['types'].get(k, {}).get('cap_per_10min', '-')} |" for k, v in cnt.most_common()]
    else:
        L += ["None."]
    L += ["", "## 5. Review these first (owner)", ""]
    picks = sorted(log["rationale"], key=lambda m: (bool(m["rationale"]), m["start"]))[:5]
    L += [f"- {m['id']} at {P.tc(m['start'])[3:8]}: {m['choice']}" for m in picks] or ["- nothing flagged"]
    L += ["", "## 6. Owner feedback (fill after viewing; the agent copies it into the style memory)", "",
          "- Liked:", "- Disliked:", "- Too slow / too fast at:", "- Overlays: too many / too few at:", "- Keep for next video:", ""]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description="Variation tracking and edit report with rationale.")
    ap.add_argument("--shot-plan")
    ap.add_argument("--beats")
    ap.add_argument("--assign")
    ap.add_argument("--beat-map")
    ap.add_argument("--preset")
    ap.add_argument("--out-json")
    ap.add_argument("--out-md")
    a = ap.parse_args()
    try:
        if a.shot_plan:
            clips, src = P.load_clips_shot_plan(a.shot_plan, a.beat_map), a.shot_plan
        elif a.beats and a.assign:
            clips, src = P.load_clips_beats(a.beats, a.assign, a.beat_map), f"{a.beats} + {a.assign}"
        else:
            print("Error: give --shot-plan or --beats and --assign", file=sys.stderr)
            sys.exit(2)
        presets, lib, cat = P.load_presets(), P.load_motion_library(), P.load_catalog()
        findings, log, pname, _ = analyse(clips, presets, lib, cat, a.preset)
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        print(f"Variation report error: {e}", file=sys.stderr)
        sys.exit(2)
    fails = [f for f in findings if f["severity"] == "FAIL"]
    status = "FAIL" if fails else "PASS"
    payload = {"tool": "variation_report", "revision": "2026-11-09", "source": src, "preset": pname, "overall_status": status, "findings": findings, **log}
    P.write_report(a.out_json, a.out_md, payload, render_md(status, src, pname, findings, log, cat))
    print(f"Variation report: {status} | {len(fails)} fail, {len(findings) - len(fails)} warn | longest still {log['stats']['longest_still_run_s']}s"
          + (f" -> {a.out_md}" if a.out_md else ""))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
