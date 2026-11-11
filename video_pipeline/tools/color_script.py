#!/usr/bin/env python
"""Colour script: plan the per-shot grade from the story, then check it (COLOR_SCRIPT.md, revision 2026-11-09).

  plan  color_script.json (agent-written, phases by BEAT id) + timeline  ->  color_assign.json, color_plan.md,
        looks/<look>.fcpreset (one FilmCraft preset per unique look; build_full_edit.py applies them),
        looks/<look>.cube with --measure (exact LUT measured through FilmCraft's Lumetri; also the Resolve LUT)
  qa    color_assign.json + the pictures (+ --video the rendered cut)  ->  strip.png, strip_overgrade.png,
        phase_sheet.png, strip.json, qa_color.json / .md

plan FAIL codes (exit 1)
  SCHEMA          missing story_logic / phases / per-phase intent or reason
  TIMECODE        a phase carries a timecode ("time", "start", "end"): phases are given by beat id only (code maps time)
  BEAT_UNKNOWN    from_beat / to_beat not in the timeline
  TILING          phases leave a gap, overlap, or do not cover the first and last beat
  PHASE_COUNT     fewer than 3 or more than 10 phases (4-8 is the target: WARN outside it)
  SHIFT_TOO_SOON  a phase shorter than 12 s (two shifts < 12 s apart) unless montage:true. 12-20 s: WARN
  CUT_NO_REASON   transition_in cut (abrupt colour shift) without a story reason
  CALLBACK_REF / MOTIF_REF   callback_of or motif id that does not exist
  TOO_STRONG      a phase look (after clamping) exceeds the intensity's delta-E budget (nameable filter)
plan WARN codes
  CLAMPED         a requested offset was beyond the intensity cap and was clamped
  NO_IDENTITY     adjacent phases differ by < 1.0 dE: the viewer cannot feel the shift (merge or differentiate)
  CALLBACK_DRIFT  a callback phase differs from the phase it echoes by > 1.0 dE (silenced by "callback_variation": "<story reason>")
  FLICKER         temperature direction alternates phase after phase (random flicker, not an arc)
  UNIVERSAL_RULE  a reason reads like a universal colour-emotion rule ("blue = sad"); derive meaning from this story
  ACCENT_TEXT     phase accent below 3:1 against the charcoal plate: never use it for text
  NO_IMAGE        a shot's picture was not found (graded with the phase look, no cast correction / face check)
  ADJUST_NO_REASON grade_adjust without a reason
qa FAIL codes
  TEXT_CONTRAST   document shot: the look lowers luma RMS contrast by > 3 % vs the house grade alone
  CLIPPING        the look adds > 1.0 % clipped pixels vs the house grade alone (> 0.3: WARN)
  SKIN            detected face: hue shift > 6 deg or chroma change > 15 % vs the house grade alone
qa WARN codes
  NEIGHBOR_JUMP   consecutive shots of one phase jump in exposure (p50 luma > 25 levels), cast or saturation (x2)
  RENDER_DRIFT    (--video) rendered frame mean differs from the planned look by > 6 dE (look not applied?)

Usage
  python color_script.py plan --script color_script.json --beats beats.json --assign assignments.json \
         [--beat-map beat_map.json] [--assets-root DIR] [--registry asset_registry.json] --out-dir color [--measure]
  python color_script.py plan --script color_script.json --shot-plan shot_plan.json ... --out-dir color
  python color_script.py qa --assign-file color/color_assign.json [--assets-root DIR] [--video cut.mp4] --out-dir color
Exit 0 PASS, 1 FAIL, 2 usage/processing error.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import color_lib as C  # noqa: E402
import pacing_lib as P  # noqa: E402

TIMECODE_KEYS = ("time", "start", "end", "start_s", "end_s", "timecode")
UNIVERSAL_RX = re.compile(r"\b(blue|red|green|yellow|orange|purple|warm|cool|cold|teal|gray|grey)\s*(=|means|equals|is for|signals|represents)\s*(sad|happy|danger|calm|anger|fear|love|hope|death|joy|grief)", re.I)


# ============================================================================ plan
def beat_order(bt: dict) -> list[str]:
    return sorted(bt, key=lambda k: (bt[k][0], k))


def phase_offsets(script: dict, rules: dict, caps: dict, options: dict) -> tuple[list[dict], list[dict]]:
    """Per phase: internal offsets (base + phase, clamped, motif) and the issues found on the way."""
    issues: list[dict] = []
    base = C.to_internal(C.normalize_card(script.get("base_look") or {}))
    motifs = {m["id"]: m for m in script.get("motifs") or [] if "id" in m}
    out = []
    for ph in script["phases"]:
        z = C.to_internal(C.normalize_card(ph))
        for k in C.NUMERIC:
            z[k] += base[k]
        for k in ("shadow_vec", "highlight_vec"):
            if not any(z[k]):
                z[k] = base[k]
        z, log = C.clamp_internal(z, caps)
        for m in log:
            issues.append({"level": "WARN", "code": "CLAMPED", "phase": ph["id"], "msg": m})
        mid = ph.get("motif")
        if mid and options.get("motifs", True):
            if mid not in motifs:
                issues.append({"level": "FAIL", "code": "MOTIF_REF", "phase": ph["id"], "msg": f"motif {mid} not defined in motifs[]"})
            else:
                m = motifs[mid]
                strength = float((m.get("per_phase") or {}).get(ph["id"], 1.0))
                z["motif_hue"] = C.rgb_hue_deg(C.hex_rgb(m["hex"]))
                z["motif_sat"] = 100.0 + (caps["motif_sat"] - 100.0) * max(0.0, min(1.0, strength))
        out.append(z)
    return out, issues


def validate(script: dict, bt: dict, rules: dict, house: dict) -> tuple[list[dict], dict]:
    """Rule checks of color_script.json. Returns (issues, context)."""
    I: list[dict] = []
    opts = {**rules["defaults"], **(script.get("options") or {})}
    PR = rules["phases"]

    def add(level, code, msg, phase=None):
        I.append({"level": level, "code": code, "phase": phase, "msg": msg})

    for k, allowed in rules["options"].items():
        if opts.get(k) not in allowed:
            add("FAIL", "SCHEMA", f"options.{k} = {opts.get(k)!r}; allowed {allowed}")
            opts[k] = rules["defaults"][k]
    caps = rules["intensity_caps"][opts["intensity"]]

    if len(str(script.get("story_logic") or "").strip()) < 40:
        add("FAIL", "SCHEMA", "story_logic missing or under 40 characters: say what colour means in THIS story before any phase (principle 6)")
    phases = script.get("phases") or []
    if not phases:
        add("FAIL", "SCHEMA", "no phases")
        return I, {"options": opts, "caps": caps, "phases": [], "times": [], "z": []}
    ids = [p.get("id") for p in phases]
    for p in phases:
        pid = p.get("id", "?")
        for k in ("id", "name", "intent", "reason", "from_beat", "to_beat"):
            if not p.get(k):
                add("FAIL", "SCHEMA", f"phase {pid}: missing {k}", pid)
        tk = [k for k in TIMECODE_KEYS if k in p]
        if tk:
            add("FAIL", "TIMECODE", f"phase {pid}: {tk} present. Give the phase by from_beat/to_beat only; code maps beats to time", pid)
        for k in ("from_beat", "to_beat"):
            if p.get(k) and p[k] not in bt:
                add("FAIL", "BEAT_UNKNOWN", f"phase {pid}: {k} {p[k]} not in the timeline", pid)
        if UNIVERSAL_RX.search(str(p.get("reason", "")) + " " + str(p.get("intent", ""))):
            add("WARN", "UNIVERSAL_RULE", f"phase {pid}: reason reads like a universal colour rule; tie it to this story's own logic", pid)
        if p.get("callback_of") and p["callback_of"] not in ids:
            add("FAIL", "CALLBACK_REF", f"phase {pid}: callback_of {p['callback_of']} unknown", pid)
        tr = p.get("transition_in") or {}
        if isinstance(tr, str):
            tr = {"type": "cut" if "cut" in tr.lower() else "blend", "seconds": float(re.findall(r"[\d.]+", tr)[0]) if re.findall(r"[\d.]+", tr) else PR["blend_s"]["default"]}
            p["transition_in"] = tr
        if tr.get("type") == "cut" and not tr.get("reason"):
            add("FAIL", "CUT_NO_REASON", f"phase {pid}: colour shifts on a hard cut without a story reason (shock, loss, sudden change)", pid)
        if p.get("accent"):
            cr = C.wcag_contrast(C.hex_rgb(p["accent"]), C.hex_rgb("#0F1218"))
            if cr < rules["qa"]["accent_contrast_min"]:
                add("WARN", "ACCENT_TEXT", f"phase {pid}: accent {p['accent']} is {cr:.1f}:1 on the charcoal plate; never use it for text", pid)
    if any(i["level"] == "FAIL" and i["code"] in ("SCHEMA", "BEAT_UNKNOWN", "TIMECODE") for i in I):
        return I, {"options": opts, "caps": caps, "phases": phases, "times": [], "z": []}

    order = beat_order(bt)
    pos = {b: i for i, b in enumerate(order)}
    spans = sorted(((pos[p["from_beat"]], pos[p["to_beat"]], p) for p in phases), key=lambda x: x[0])
    phases = [s[2] for s in spans]
    exp = 0
    for a, b, p in spans:
        if b < a:
            add("FAIL", "TILING", f"phase {p['id']}: to_beat before from_beat", p["id"])
        if a != exp:
            add("FAIL", "TILING", f"phase {p['id']} starts at {p['from_beat']}; expected {order[exp] if exp < len(order) else 'end'} (gap or overlap)", p["id"])
        exp = b + 1
    if exp != len(order):
        add("FAIL", "TILING", f"phases end at beat {order[exp - 1]}; the timeline runs to {order[-1]}")
    n = len(phases)
    if n < PR["min_count"] or n > PR["max_count"]:
        add("FAIL", "PHASE_COUNT", f"{n} phases (allowed {PR['min_count']}-{PR['max_count']}, target {PR['target_min']}-{PR['target_max']})")
    elif not PR["target_min"] <= n <= PR["target_max"]:
        add("WARN", "PHASE_COUNT", f"{n} phases (target {PR['target_min']}-{PR['target_max']}; more dilutes the effect)")
    times = C.phase_times(phases, bt)
    for (a, b), p in zip(times, phases):
        d = b - a
        if d < PR["hard_min_shift_interval_s"] and not p.get("montage"):
            add("FAIL", "SHIFT_TOO_SOON", f"phase {p['id']} lasts {d:.1f} s: colour shifts < {PR['hard_min_shift_interval_s']:g} s apart (mark montage:true only for a real montage)", p["id"])
        elif d < PR["min_shift_interval_s"] and not p.get("montage"):
            add("WARN", "SHIFT_TOO_SOON", f"phase {p['id']} lasts {d:.1f} s (< {PR['min_shift_interval_s']:g} s between shifts)", p["id"])
    script = {**script, "phases": phases}
    zs, iss = phase_offsets(script, rules, caps, opts)
    I += iss
    strengths = []
    for z, p in zip(zs, phases):
        s = C.look_strength(house, z)
        strengths.append(s)
        if s > caps["delta_e_budget"] + 1e-6:
            add("FAIL", "TOO_STRONG", f"phase {p['id']}: look strength {s:.2f} dE > {caps['delta_e_budget']} budget for '{opts['intensity']}' (a viewer could name the filter)", p["id"])
    for i in range(1, n):
        d = C.look_distance(house, zs[i - 1], zs[i])
        if d < PR["identity_min_delta_e"]:
            add("WARN", "NO_IDENTITY", f"{phases[i - 1]['id']} -> {phases[i]['id']}: only {d:.2f} dE apart; the shift will not read", phases[i]["id"])
    idx = {p["id"]: k for k, p in enumerate(phases)}
    for k, p in enumerate(phases):
        if p.get("callback_of") in idx and not p.get("callback_variation"):
            d = C.look_distance(house, zs[k], zs[idx[p["callback_of"]]])
            if d > PR["callback_max_delta_e"]:
                add("WARN", "CALLBACK_DRIFT", f"{p['id']} echoes {p['callback_of']} but differs by {d:.2f} dE; the echo may not be felt", p["id"])
    signs = [int(np.sign(round(z["temperature"], 1))) for z in zs]
    alt = sum(1 for i in range(2, n) if signs[i] and signs[i] == signs[i - 2] and signs[i] == -signs[i - 1]
              and not phases[i].get("callback_of"))
    if alt >= rules["qa"]["flicker_alternations_warn"]:
        add("WARN", "FLICKER", f"temperature alternates direction {alt} times across consecutive phases: random flicker, not an arc. Move the colour one way per story movement")
    return I, {"options": opts, "caps": caps, "phases": phases, "times": times, "z": zs, "strength": strengths}


def shot_roles(clip: P.Clip, stats: dict | None, faces: list, rules: dict) -> set[str]:
    pr = rules["protection"]
    r: set[str] = set()
    subj = str(clip.subject or "").lower()
    if faces or any(w in subj for w in pr["face_subjects"]):
        r.add("face")
    if clip.reading or any(w in subj for w in pr["document_subjects"]):
        r.add("document")
    arch = clip.raw.get("archival") if isinstance(clip.raw, dict) else None
    if arch is None or arch:
        r.add("archival")
    if stats and (stats["is_bw"] or stats["toned_mono"]):
        r.add("bw")
    return r


def plan(a) -> int:
    rules = C.load_rules(a.rules)
    house = C.house_grade(a.style)
    script = C.load_json(a.script)
    if a.shot_plan:
        clips = P.load_clips_shot_plan(a.shot_plan, a.beat_map)
        d = C.load_json(a.shot_plan)
        bt = C.beat_times_from_shot_plan(d.get("slots", d) if isinstance(d, dict) else d)
    else:
        clips = P.load_clips_beats(a.beats, a.assign, a.beat_map)
        bt = C.beat_times_from_beats(C.load_json(a.beats))
    issues, ctx = validate(script, bt, rules, house)
    fails = [i for i in issues if i["level"] == "FAIL"]
    os.makedirs(a.out_dir, exist_ok=True)
    looks_dir = os.path.join(a.out_dir, "looks")
    if fails and not ctx.get("z"):
        return finish_plan(a, issues, ctx, [], {}, house)

    from asset_audit import load_registry, resolve  # noqa: E402
    registry = load_registry(a.registry)
    phases, times, zs, opts = ctx["phases"], ctx["times"], ctx["z"], ctx["options"]
    PR = rules["phases"]
    shots, looks = [], {}
    for c in clips:
        row = {"id": c.id, "start": round(c.start, 3), "end": round(c.end, 3), "asset": c.asset_raw, "kind": c.kind}
        if c.kind == "plate":
            row.update(graded=False, why="generated graphic: house palette, never graded")
            shots.append(row)
            continue
        mid = (c.start + c.end) / 2
        k = next((i for i, (s, e) in enumerate(times) if s - 1e-6 <= mid < e + 1e-6), len(times) - 1 if mid >= times[-1][0] else 0)
        ph = phases[k]
        z = zs[k]
        w = 1.0
        tr = ph.get("transition_in") or {}
        sharp = opts.get("arc") == "sharp"
        if k > 0 and tr.get("type", "cut" if sharp else "blend") == "blend":
            S = min(PR["blend_s"]["max"], max(PR["blend_s"]["min"], float(tr.get("seconds", PR["blend_s"]["default"]))))
            T0 = times[k][0]
            if mid < T0 + S:
                step = PR["blend_step"]
                w = max(step, min(1.0, round(((mid - T0) / S) / step) * step))
                z = C.lerp_internal(zs[k - 1], zs[k], w)
        log: list[str] = []
        path = resolve(c.asset_raw or c.asset, a.assets_root, registry)
        stats, faces = None, []
        if path and os.path.splitext(path)[1].lower() in (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"):
            try:
                img = C.load_image(path)
                stats = C.image_stats(img, rules)
                faces = C.detect_faces(img)
            except Exception as e:  # unreadable picture: keep going, flag it
                log.append(f"image unreadable: {e}")
        elif c.kind == "still":
            issues.append({"level": "WARN", "code": "NO_IMAGE", "phase": ph["id"], "msg": f"{c.id}: picture not found ({c.asset_raw}); phase look applied without cast/face checks"})
        roles = shot_roles(c, stats, faces, rules)
        z, plog = C.protect(z, roles, rules, opts)
        log += plog
        if stats and "bw" not in roles and c.raw.get("normalize", True) is not False:
            t, ti, why = C.cast_correction(stats, rules)
            if why:
                z["temperature"] += round(t)
                z["tint"] += round(ti)
                log.append("normalize: " + why)
        adj = c.raw.get("grade_adjust") if isinstance(c.raw, dict) else None
        if isinstance(adj, dict):
            if not adj.get("reason"):
                issues.append({"level": "WARN", "code": "ADJUST_NO_REASON", "phase": ph["id"], "msg": f"{c.id}: grade_adjust without a reason"})
            for kk, cap in rules["normalize"]["grade_adjust_caps"].items():
                if kk in adj:
                    v = max(-cap, min(cap, float(adj[kk])))
                    z[kk] += v
                    log.append(f"grade_adjust {kk} {v:+g} ({adj.get('reason', 'no reason')})")
        z = C.round_internal(z)
        key = C.look_key(z)
        name = f"CS_{ph['id']}_{key}"
        if name not in looks:
            looks[name] = {"phase": ph["id"], "offsets": z}
        row.update(graded=True, phase=ph["id"], blend_w=w, roles=sorted(roles), look=name, image=path if stats else None,
                   faces=len(faces), stats=stats, log=log)
        shots.append(row)
    # write the presets (+ measured LUTs)
    tmpl = C.house_template()
    if not tmpl:
        issues.append({"level": "FAIL", "code": "NO_PRESET_TEMPLATE", "phase": None,
                       "msg": f"house .fcpreset not found in {C.GRADE_DIR}: run presets/documentary-default/grade/build_grade.py --no-calibrate"})
    os.makedirs(looks_dir, exist_ok=True)
    measured = 0
    for name, lk in looks.items():
        vals = C.to_lumetri(house, lk["offsets"])
        lk["values"] = vals
        if tmpl:
            pre = C.fcpreset(tmpl, name, vals)
            with open(os.path.join(looks_dir, name + ".fcpreset"), "w", encoding="utf-8") as f:
                json.dump(pre, f, indent=1)
            lk["fcpreset"] = os.path.join(looks_dir, name + ".fcpreset")
            if a.measure and C.filmcraft_available():
                lut = C.measure_lut(C.fcpreset(tmpl, name + "_lum", vals, lumetri_only=True), os.path.join(a.out_dir, "_measure"), a.lut_size)
                C.write_cube(os.path.join(looks_dir, name + ".cube"), lut, name)
                lk["cube"] = os.path.join(looks_dir, name + ".cube")
                measured += 1
    house_cube = None
    if measured:   # the QA baseline must come from the same measurement as the looks
        lut = C.measure_lut(C.fcpreset(tmpl, "CS_HOUSE_lum", C.to_lumetri(house, C.zero_offsets()), lumetri_only=True), os.path.join(a.out_dir, "_measure"), a.lut_size)
        house_cube = os.path.join(looks_dir, "CS_HOUSE.cube")
        C.write_cube(house_cube, lut, "CS_HOUSE")
    ctx["house_cube"] = house_cube
    if a.measure and not measured:
        issues.append({"level": "WARN", "code": "NO_MEASURE", "phase": None, "msg": "FilmCraft or the house .fcpreset not found: no measured LUTs; QA uses the analytic preview"})
    if not C.face_detection_available():
        issues.append({"level": "WARN", "code": "NO_FACE_DETECT", "phase": None,
                       "msg": "OpenCV face detection unavailable (pip install opencv-python): only shots with subject portrait/person/face are skin-protected"})
    return finish_plan(a, issues, ctx, shots, looks, house)


def finish_plan(a, issues, ctx, shots, looks, house) -> int:
    fails = [i for i in issues if i["level"] == "FAIL"]
    phases, times = ctx.get("phases", []), ctx.get("times", [])
    payload = {"schema": "pipeline.color_assign/1", "verdict": "FAIL" if fails else "PASS", "options": ctx.get("options"),
               "intensity_caps": ctx.get("caps"),
               "phases": [{"id": p["id"], "name": p.get("name"), "intent": p.get("intent"), "reason": p.get("reason"),
                           "from_beat": p.get("from_beat"), "to_beat": p.get("to_beat"),
                           "start": round(t[0], 3) if t else None, "end": round(t[1], 3) if t else None,
                           "palette": p.get("palette"), "accent": p.get("accent"), "music": p.get("music"),
                           "transition_in": p.get("transition_in"), "callback_of": p.get("callback_of"),
                           "offsets": C.round_internal(z) if z else None, "strength_de": round(s, 2) if s is not None else None}
                          for p, t, z, s in zip(phases, times or [None] * len(phases), ctx.get("z") or [None] * len(phases),
                                                ctx.get("strength") or [None] * len(phases))],
               "house_cube": ctx.get("house_cube"),
               "looks": {k: {kk: vv for kk, vv in v.items()} for k, v in looks.items()},
               "shots": shots, "issues": issues}
    md = [f"# Colour plan - {payload['verdict']}", "",
          f"Options: {ctx.get('options')}  ", f"{len(phases)} phases, {len(looks)} unique looks, "
          f"{sum(1 for s in shots if s.get('graded'))} graded shots, {sum(1 for s in shots if not s.get('graded'))} graphics left ungraded.", ""]
    if issues:
        md += ["## Issues", "| Level | Code | Phase | What |", "|---|---|---|---|"]
        md += [f"| {i['level']} | {i['code']} | {i.get('phase') or ''} | {i['msg']} |" for i in issues]
        md.append("")
    md += ["## Phase cards", ""]
    for ph in payload["phases"]:
        o = ph["offsets"] or {}
        md += [f"### {ph['id']} {ph['name']}  ({P.tc(ph['start']) if ph['start'] is not None else '?'} - {P.tc(ph['end']) if ph['end'] is not None else '?'}, beats {ph['from_beat']}-{ph['to_beat']})",
               f"- Intent: {ph['intent']}", f"- Why (story logic): {ph['reason']}",
               f"- Palette: {' '.join(ph['palette'] or [])}  accent: {ph['accent'] or '-'}  music: {ph['music'] or '-'}",
               f"- Offsets vs house: temp {o.get('temperature', 0):+g}, tint {o.get('tint', 0):+g}, sat {o.get('saturation', 0):+g} %, contrast {o.get('contrast', 0):+g}, "
               f"blacks {o.get('blacks', 0):+g}, fade {o.get('fade', 0):+g}, split shadows {o.get('shadow_vec')}, highlights {o.get('highlight_vec')}, "
               f"grain {o.get('grain', 0):+g}, vignette {o.get('vignette', 0):+g}, motif {o.get('motif_hue')}/{o.get('motif_sat')}",
               f"- Strength: {ph['strength_de']} dE (budget {(ctx.get('caps') or {}).get('delta_e_budget')})  transition in: {ph['transition_in'] or 'start'}"
               + (f"  callback of {ph['callback_of']}" if ph["callback_of"] else ""), ""]
    if shots:
        md += ["## Shots", "| Shot | Time | Phase | Blend | Roles | Look | Notes |", "|---|---|---|---|---|---|---|"]
        for s in shots:
            if not s.get("graded"):
                md.append(f"| {s['id']} | {P.tc(s['start'])} | - | - | - | none | {s.get('why')} |")
            else:
                md.append(f"| {s['id']} | {P.tc(s['start'])} | {s['phase']} | {s['blend_w']:g} | {', '.join(s['roles'])} | {s['look']} | {'; '.join(s['log'])} |")
    os.makedirs(a.out_dir, exist_ok=True)
    P.write_report(os.path.join(a.out_dir, "color_assign.json"), os.path.join(a.out_dir, "color_plan.md"), payload, "\n".join(md) + "\n")
    print(f"colour plan {payload['verdict']}: {len(fails)} FAIL, {len(issues) - len(fails)} WARN, {len(looks)} looks -> {a.out_dir}")
    for i in fails[:12]:
        print(f"  FAIL {i['code']}: {i['msg']}")
    return 1 if fails else 0


# ============================================================================ qa
def graded(img: np.ndarray, house: dict, look: dict, scale: float = 1.0, use_cube: bool = True) -> np.ndarray:
    z = look["offsets"] if scale == 1 else C.scale_internal(look["offsets"], scale)
    if use_cube and scale == 1 and look.get("cube") and os.path.exists(look["cube"]):
        out = C.apply_lut(img, C.read_cube(look["cube"]))
        v = C.to_lumetri(house, z)["vignette"]["amount"]
        h, w = out.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        r2 = (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 2
        return np.clip(out * (1 + v / 100.0 * 0.9 * r2)[..., None], 0, 255)
    return C.preview_apply(img, house, z)


def frame_at(video: str, t: float, w: int = 192) -> np.ndarray | None:
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-vf", f"scale={w}:-2",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    if r.returncode or not r.stdout:
        return None
    n = len(r.stdout) // 3
    h = n // w
    return np.frombuffer(r.stdout[:w * h * 3], np.uint8).reshape(h, w, 3).astype(float)


def face_hue_chroma(img: np.ndarray, faces: list) -> tuple[float, float] | None:
    if not faces:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    reg = img[y + h // 4: y + 3 * h // 4, x + w // 4: x + 3 * w // 4].reshape(-1, 3)
    lab = C.srgb_to_lab(reg).mean(0)
    return float(np.degrees(np.arctan2(lab[2], lab[1])) % 360), float(np.hypot(lab[1], lab[2]))


def skin_locus_hue_chroma(base: np.ndarray, graded_img: np.ndarray, min_share: float = 0.02):
    """Pixels in the usual skin locus (L* 25-85, a* 4-25, b* 8-30) of the house-graded picture, measured in both images."""
    lb = C.srgb_to_lab(base.reshape(-1, 3))
    m = (lb[:, 0] > 25) & (lb[:, 0] < 85) & (lb[:, 1] > 4) & (lb[:, 1] < 25) & (lb[:, 2] > 8) & (lb[:, 2] < 30)
    if m.mean() < min_share:
        return None, None
    lg = C.srgb_to_lab(graded_img.reshape(-1, 3))[m].mean(0)
    lb = lb[m].mean(0)
    return ((float(np.degrees(np.arctan2(lb[2], lb[1])) % 360), float(np.hypot(lb[1], lb[2]))),
            (float(np.degrees(np.arctan2(lg[2], lg[1])) % 360), float(np.hypot(lg[1], lg[2]))))


def draw_strip(rows: list[tuple[str, list[tuple[float, np.ndarray]]]], phases: list[dict], total: float, path: str, width: int = 1600) -> None:
    from PIL import Image, ImageDraw
    rh, band = 80, 26
    H = len(rows) * (rh + 18) + band + 8
    im = Image.new("RGB", (width, H), (24, 24, 28))
    d = ImageDraw.Draw(im)
    y = 0
    for label, sw in rows:
        d.text((4, y + 2), label, fill=(220, 220, 220))
        y += 16
        for (t0, t1), col in sw:
            x0, x1 = int(t0 / total * width), max(int(t0 / total * width) + 1, int(t1 / total * width))
            d.rectangle([x0, y, x1, y + rh], fill=tuple(int(v) for v in np.clip(col, 0, 255)))
        y += rh + 2
    for ph in phases:
        if ph.get("start") is None:
            continue
        x0, x1 = int(ph["start"] / total * width), int(ph["end"] / total * width)
        d.rectangle([x0, y + 2, x1 - 1, y + band], outline=(200, 200, 200))
        d.text((x0 + 4, y + 7), f"{ph['id']} {ph.get('name') or ''}"[: max(1, (x1 - x0) // 7)], fill=(230, 230, 230))
    im.save(path)


def qa(a) -> int:
    rules = C.load_rules(a.rules)
    house = C.house_grade(a.style)
    A = C.load_json(a.assign_file)
    Q = rules["qa"]
    looks, phases, shots = A["looks"], A["phases"], [s for s in A["shots"] if s.get("graded")]
    issues: list[dict] = []
    total = max([s["end"] for s in A["shots"]] + [p["end"] or 0 for p in phases] + [1.0])
    zero = C.zero_offsets()
    sw_full, sw_over, sw_base, sw_render, sw_dir, sheet, unchecked = [], [], [], [], [], {}, []
    prev = None
    for s in shots:
        lk = looks[s["look"]]
        img = None
        if s.get("image") and os.path.exists(s["image"]):
            img = C.load_image(s["image"], 320)
        if img is None:
            unchecked.append(s["id"])
            continue
        g = graded(img, house, lk)
        hc = A.get("house_cube")
        if lk.get("cube") and hc and os.path.exists(lk["cube"]) and os.path.exists(hc):   # same method for baseline and look
            base = graded(img, house, {"offsets": zero, "cube": hc})
        else:
            base = C.preview_apply(img, house, zero)
        over = graded(img, house, lk, scale=Q["overgrade_scale"], use_cube=False)
        full_prev = C.preview_apply(img, house, lk["offsets"])
        gs, bs = C.image_stats(g, rules), C.image_stats(base, rules)
        span = (s["start"], s["end"])
        sw_full.append((span, g.reshape(-1, 3).mean(0)))
        ref = C.preview_apply(np.array([[128.0, 128.0, 128.0], [190.0, 190.0, 190.0], [70.0, 70.0, 70.0]]), house, lk["offsets"], vignette=False).mean(0)
        sw_dir.append((span, 128 + (ref - ref.mean()) * 3 + (ref.mean() - 129.3) * 3))
        sw_over.append((span, over.reshape(-1, 3).mean(0)))
        sw_base.append((span, full_prev.reshape(-1, 3).mean(0)))
        sheet.setdefault(s["phase"], []).append(g)
        tag = f"{s['id']} ({P.tc(s['start'])})"
        if "document" in s["roles"] and bs["luma_rms"] > 1 and gs["luma_rms"] < bs["luma_rms"] * (1 - Q["text_contrast_drop_max"]):
            issues.append({"level": "FAIL", "code": "TEXT_CONTRAST", "shot": s["id"],
                           "msg": f"{tag}: luma RMS {bs['luma_rms']:.1f} -> {gs['luma_rms']:.1f} (-{(1 - gs['luma_rms'] / bs['luma_rms']) * 100:.1f} %); text must stay readable"})
        d_low = max(0.0, gs["clip_low"] - bs["clip_low"])     # lifted shadows must not hide blown highlights
        d_high = max(0.0, gs["clip_high"] - bs["clip_high"])
        dc = d_low + d_high
        lvl = "FAIL" if dc > Q["clip_increase_fail_pts"] else "WARN" if dc > Q["clip_increase_warn_pts"] else None
        if lvl:
            issues.append({"level": lvl, "code": "CLIPPING", "shot": s["id"], "msg": f"{tag}: look adds {dc:.2f} % clipped pixels (shadows +{d_low:.2f}, highlights +{d_high:.2f})"})
        if "face" in s["roles"]:
            faces = C.detect_faces(img)
            fb, fg = face_hue_chroma(base, faces), face_hue_chroma(g, faces)
            if not fb:   # no detector / no frontal face: fall back to skin-locus pixels of the house-graded picture
                fb, fg = skin_locus_hue_chroma(base, g)
            if not fb:
                issues.append({"level": "WARN", "code": "SKIN_UNVERIFIED", "shot": s["id"],
                               "msg": f"{tag}: face role but no face or skin-tone pixels found; check skin by eye"})
            elif fb[1] > 4:
                dh = abs((fg[0] - fb[0] + 180) % 360 - 180)
                dch = abs(fg[1] - fb[1]) / fb[1]
                if dh > Q["skin_hue_shift_max_deg"] or dch > Q["skin_sat_change_max"]:
                    issues.append({"level": "FAIL", "code": "SKIN", "shot": s["id"],
                                   "msg": f"{tag}: skin hue {dh:.1f} deg / chroma {dch * 100:.0f} % off the house grade; reduce the look on this shot"})
        if prev and prev[0]["phase"] == s["phase"] and prev[0].get("blend_w", 1) == 1 and s.get("blend_w", 1) == 1:
            ps = prev[1]
            msgs = []
            roles2 = set(s["roles"]) | set(prev[0]["roles"])
            docs = "document" in roles2          # paper is meant to be brighter than a scene
            mono = "bw" in roles2                # a toned print keeps its tone on purpose
            if not docs and abs(gs["luma_p50"] - ps["luma_p50"]) > Q["neighbor_luma_warn"]:
                msgs.append(f"median luma {ps['luma_p50']:.0f} -> {gs['luma_p50']:.0f}")
            if not mono and abs(gs["cast"]["r_minus_b"] - ps["cast"]["r_minus_b"]) > 8 and min(gs["cast"]["neutral_share"], ps["cast"]["neutral_share"]) > 0.05:
                msgs.append(f"neutral R-B {ps['cast']['r_minus_b']:+.0f} -> {gs['cast']['r_minus_b']:+.0f}")
            if not mono and abs(gs["cast"]["g_minus_rb"] - ps["cast"]["g_minus_rb"]) > 8 and min(gs["cast"]["neutral_share"], ps["cast"]["neutral_share"]) > 0.05:
                msgs.append(f"neutral G-RB (green/magenta) {ps['cast']['g_minus_rb']:+.0f} -> {gs['cast']['g_minus_rb']:+.0f}")
            if not docs and not mono and min(gs["chroma_mean"], ps["chroma_mean"]) > 6 and max(gs["chroma_mean"], ps["chroma_mean"]) / min(gs["chroma_mean"], ps["chroma_mean"]) > 2:
                msgs.append(f"saturation x{max(gs['chroma_mean'], ps['chroma_mean']) / min(gs['chroma_mean'], ps['chroma_mean']):.1f}")
            if msgs:
                issues.append({"level": "WARN", "code": "NEIGHBOR_JUMP", "shot": s["id"],
                               "msg": f"{prev[0]['id']} -> {s['id']} ({P.tc(s['start'])}), same phase: {', '.join(msgs)}. Story reason? Else grade_adjust on the outlier"})
        prev = (s, gs)
        if a.video:
            fr = frame_at(a.video, (s["start"] + s["end"]) / 2)
            if fr is not None:
                m = fr.reshape(-1, 3).mean(0)
                sw_render.append((span, m))
                de = float(C.delta_e(m, g.reshape(-1, 3).mean(0)))
                if de > 6:
                    issues.append({"level": "WARN", "code": "RENDER_DRIFT", "shot": s["id"],
                                   "msg": f"{tag}: rendered frame mean is {de:.1f} dE from the planned look (look missing, wrong clip, or motion/overlay on the frame)"})
    os.makedirs(a.out_dir, exist_ok=True)
    rows = [("Colour script strip (graded mean per shot" + (", measured LUTs" if any(l.get("cube") for l in looks.values()) else ", analytic preview") + ")", sw_full)]
    rows.append(("Look direction only (gray through each shot's look, deviation x3): the shape of the colour arc", sw_dir))
    if sw_render:
        rows.append(("Rendered cut (frame mean at shot midpoint)", sw_render))
    draw_strip(rows, phases, total, os.path.join(a.out_dir, "strip.png"))
    draw_strip([("Over-grade check: full look (preview)", sw_base), (f"Same looks at {int(Q['overgrade_scale'] * 100)} % - keep this if the story reads as well", sw_over)],
               phases, total, os.path.join(a.out_dir, "strip_overgrade.png"))
    # squint sheet
    from PIL import Image, ImageDraw
    tw, th, per = 128, 72, 8
    ids = [p["id"] for p in phases if p["id"] in sheet]
    im = Image.new("RGB", (120 + per * (tw + 4), max(1, len(ids)) * (th + 6)), (24, 24, 28))
    d = ImageDraw.Draw(im)
    for r, pid in enumerate(ids):
        d.text((4, r * (th + 6) + th // 2 - 6), pid, fill=(230, 230, 230))
        picks = sheet[pid][:: max(1, len(sheet[pid]) // per)][:per]
        for c, g in enumerate(picks):
            t = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).resize((tw, th))
            im.paste(t, (120 + c * (tw + 4), r * (th + 6)))
    im.save(os.path.join(a.out_dir, "phase_sheet.png"))
    strip = {"phases": [{k: p[k] for k in ("id", "name", "start", "end")} | {"mean_rgb": np.mean([c for (sp, c) in sw_full if p["start"] is not None and p["start"] <= (sp[0] + sp[1]) / 2 < p["end"]] or [[0, 0, 0]], axis=0).round(1).tolist()} for p in phases],
             "shots": [{"start": sp[0], "end": sp[1], "mean_rgb": np.round(c, 1).tolist(), "hex": "#%02X%02X%02X" % tuple(int(v) for v in np.clip(c, 0, 255))} for sp, c in sw_full]}
    with open(os.path.join(a.out_dir, "strip.json"), "w", encoding="utf-8") as f:
        json.dump(strip, f, indent=1)
    fails = [i for i in issues if i["level"] == "FAIL"]
    verdict = "FAIL" if fails else "PASS"
    md = [f"# Colour QA - {verdict}", "", f"{len(shots) - len(unchecked)} graded shots checked; {len(fails)} FAIL, {len(issues) - len(fails)} WARN.",
          f"Not checked from source (footage, or picture not found: {len(unchecked)}): {', '.join(unchecked[:40]) or 'none'}. Run qa with --video on the render to cover them.", "",
          "Look at: `strip.png` (does the colour follow the story's shape?), `phase_sheet.png` (squint: does each phase have its own identity?), "
          "`strip_overgrade.png` (does the 70 % version read as well? then keep it). Human checks left: authenticity of archival, phone + monitor display.", ""]
    if issues:
        md += ["| Level | Code | Shot | What |", "|---|---|---|---|"] + [f"| {i['level']} | {i['code']} | {i.get('shot', '')} | {i['msg']} |" for i in issues]
    P.write_report(os.path.join(a.out_dir, "qa_color.json"), os.path.join(a.out_dir, "qa_color.md"),
                   {"verdict": verdict, "issues": issues, "shots_checked": len(shots)}, "\n".join(md) + "\n")
    print(f"colour QA {verdict}: {len(fails)} FAIL, {len(issues) - len(fails)} WARN -> {a.out_dir}")
    for i in fails[:12]:
        print(f"  FAIL {i['code']}: {i['msg']}")
    return 1 if fails else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p1 = sp.add_parser("plan")
    p1.add_argument("--script", required=True)
    p1.add_argument("--beats")
    p1.add_argument("--assign")
    p1.add_argument("--shot-plan")
    p1.add_argument("--beat-map")
    p1.add_argument("--assets-root")
    p1.add_argument("--registry")
    p1.add_argument("--out-dir", required=True)
    p1.add_argument("--measure", action="store_true", help="measure each look's LUT through FilmCraft (exact preview + Resolve .cube)")
    p1.add_argument("--lut-size", type=int, default=17)
    p2 = sp.add_parser("qa")
    p2.add_argument("--assign-file", required=True)
    p2.add_argument("--video")
    p2.add_argument("--out-dir", required=True)
    for p in (p1, p2):
        p.add_argument("--rules")
        p.add_argument("--style")
    a = ap.parse_args()
    try:
        if a.cmd == "plan":
            if not a.shot_plan and not (a.beats and a.assign):
                ap.error("plan needs --shot-plan, or --beats and --assign")
            sys.exit(plan(a))
        sys.exit(qa(a))
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
