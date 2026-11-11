"""Title & overlay families v2 (2026-11-07). Reads ../style.json (typography + layout.<family>), measures text with the
real fonts, writes an EffectCraft project per render (text is baked, so no template props are needed).

Families: reconstruction-tag, location-stamp, stat-counter, timeline-strip, then-now, source-tag, credit-line,
story-tracker, kinetic-quote.  Typography roles (one voice per job):
  Georgia      = editorial voice (names, titles, quotes)
  Montserrat   = data voice (labels, tags, numbers)
  Courier New  = evidence voice (place/date stamps, typed records)
"""
import json
import os
import re
import subprocess

import _common as C

FPS_NUM, FPS_DEN = 24000, 1001
DT = FPS_DEN / FPS_NUM


# ----------------------------------------------------------------------------- small JSX helpers
def _r(v):
    return round(float(v), 3)


def _t(v):
    return round(float(v), 5)


def _v(v):
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(str(_r(x)) for x in v) + "]"
    return str(_r(v))


def keys(var, prop, pairs):
    out = [f'var _p = {var}.property("{prop}");']
    for t, val in pairs:
        out.append(f"_p.setValueAtTime({_t(t)}, {_v(val)});")
    return "\n".join(out) + "\n"


def ramp(t0, frames, v0, v1, fn):
    """Per-frame key list from v0 to v1 (scalars or lists) over `frames` frames starting at t0."""
    out = []
    for f in range(frames + 1):
        p = fn(f / float(frames)) if frames else 1.0
        if isinstance(v0, (list, tuple)):
            val = [a + (b - a) * p for a, b in zip(v0, v1)]
        else:
            val = v0 + (v1 - v0) * p
        out.append((t0 + f * DT, val))
    return out


def envelope(var, s, t_in, t_out, pos=None, slide=(0, 0), max_op=100.0, animate_pos=True, in_frames=None, out_frames=None,
             out_slide=None):
    """Fade (+ optional slide) in at t_in, hold, fade (+ slide) out at t_out. pos = resting [x, y]."""
    a = s["animation"]
    fi = in_frames or a["in_frames"]
    fo = out_frames or a["out_frames"]
    # Opacity keys MUST be sparse endpoints: EC re-interpolates dense eased key
    # sequences and the fade never completes (measured, probe8). Position/Scale
    # stay dense-eased; opacity fades become linear spans.
    ein, eout = C.ease(s, "type_in"), C.ease(s, "type_out")  # position only; opacity keys are sparse
    op = [(0.0, 0.0), (t_in, 0.0), (round(t_in + fi * DT, 4), max_op), (t_out, max_op),
          (round(t_out + fo * DT, 4), 0.0)] if fo else \
        [(0.0, 0.0) if t_in > 0 else None, (t_in, 0.0),
         (round(t_in + fi * DT, 4), max_op)]
    op = [k for k in op if k is not None]
    js = keys(var, "Opacity", op)
    if pos is not None and animate_pos:
        osl = out_slide if out_slide is not None else (-slide[0] * 0.0, slide[1] * 0.0)
        p0 = [pos[0] + slide[0], pos[1] + slide[1], 0]
        p1 = [pos[0], pos[1], 0]
        p2 = [pos[0] + osl[0], pos[1] + osl[1], 0]
        js += keys(var, "Position", ramp(t_in, fi, p0, p1, ein) + ramp(t_out, fo, p1, p2, eout))
    elif pos is not None:
        js += f'{var}.property("Position").setValue({_v([pos[0], pos[1], 0])});\n'
    return js


def text(var, name, txt, font, size, hexcol, just, x, y, tracking=None, leading=None, op=100.0):
    js = C.text_layer_jsx(var, name, txt, font, size, C.hex_to_rgb(hexcol), just, x, y, tracking, leading)
    return js


def solid(var, name, hexcol, cx, cy, w, h, anchor_left=False):
    rgb = C.hex_to_rgb(hexcol)
    js = f'var {var} = comp.layers.addSolid([{rgb[0]}, {rgb[1]}, {rgb[2]}], "{name}", {max(1, int(round(w)))}, {max(1, int(round(h)))}, 1.0);\n'
    if anchor_left:
        js += f'{var}.property("Anchor Point").setValue([0, {_r(h / 2.0)}, 0]);\n'
    js += f'{var}.property("Position").setValue({_v([cx, cy, 0])});\n'
    return js


def shadow(var, softness, opacity, distance=2):
    return (f'var {var}Ds = {var}.property("Effects").addProperty("Drop Shadow");\n'
            f'{var}Ds.property("Softness").setValue({softness});\n'
            f'{var}Ds.property("Opacity").setValue({opacity});\n'
            f'{var}Ds.property("Distance").setValue({distance});\n'
            f'{var}Ds.property("Direction").setValue(180);\n')


def scrim(s, var, t_in, t_out, alpha):
    c = s["canvas"]
    js = solid(var, "Scrim", s["typography"]["colors"]["charcoal"], c["width"] / 2, c["height"] / 2, c["width"], c["height"])
    return js + envelope(var, s, t_in, t_out, max_op=alpha * 100.0, animate_pos=False)


def comp_jsx(name, total):
    return (f'var comp = app.project.items.addComp("{name}", 1920, 1080, 1.0, {_t(total)}, {FPS_NUM / FPS_DEN});\n'
            'comp.bgColor = [0, 0, 0];\n')


def finish_jsx():
    return 'app.project.save(new File("__PROJ_PATH__"));\nwriteLn("ECPROJ_SAVED");\n'


def save_project(s, jsx, out_dir, base, dry=False):
    os.makedirs(out_dir, exist_ok=True)
    proj = os.path.normpath(os.path.join(out_dir, base + ".ecproj"))
    jsx = jsx.replace("__PROJ_PATH__", proj.replace("\\", "/"))
    jpath = os.path.join(out_dir, "_temp_build.jsx")
    with open(jpath, "w", encoding="utf-8") as f:
        f.write(jsx)
    if dry:
        return None
    res = subprocess.run([s["toolchain"]["effectcraft_cli"], "script", jpath], capture_output=True, text=True)
    if "ECPROJ_SAVED" not in res.stdout:
        raise SystemExit("JSX error: " + (res.stderr or res.stdout)[-2000:])
    os.remove(jpath)
    return proj


def tw(s, font, size, txt, tracking=0):
    l, a, r, b = C.ink(s, font, size, txt, tracking)
    return l, a, r, b, (r - l)


def T(s):
    return s["typography"]


def col(s, k):
    return s["typography"]["colors"][k]


def adv_cursor(s, font, size):
    return C.font_for(s, font, size).getlength("M")


def hold(values, L):
    return float(values.get("Hold", L["hold_seconds"]))


def balanced_wrap(s, font, size, txt, max_w, max_lines):
    """Line breaks that read like an editor set them: honours manual '|' breaks, keeps the greedy line count,
    then picks the break set with the most even widths, preferring breaks after punctuation and no 1-word orphans."""
    import itertools
    if "|" in txt:
        lines = [" ".join(x.split()) for x in txt.split("|")]
        f = C.font_for(s, font, size)
        for ln in lines:
            if f.getlength(ln) > max_w:
                raise SystemExit(f"BUILD ERROR: manual line '{ln}' is wider than {max_w}px")
        if len(lines) > max_lines:
            raise SystemExit("BUILD ERROR: too many manual lines")
        return lines
    greedy = C.wrap(s, font, size, txt, max_w, max_lines)
    n = len(greedy)
    words = " ".join(txt.split()).split(" ")
    if n == 1:
        return greedy
    f = C.font_for(s, font, size)
    best, best_cost = greedy, None
    for cuts in itertools.combinations(range(1, len(words)), n - 1):
        idx = (0,) + cuts + (len(words),)
        lines = [" ".join(words[idx[i]:idx[i + 1]]) for i in range(n)]
        ws = [f.getlength(ln) for ln in lines]
        if max(ws) > max_w:
            continue
        cost = (max(ws) - min(ws)) / max_w
        cost -= 0.35 * sum(1 for ln in lines[:-1] if re.search(r"[.,;:!?—]$", ln))
        cost += 0.6 * sum(1 for ln in lines if len(ln.split()) == 1)
        if best_cost is None or cost < best_cost:
            best, best_cost = lines, cost
    return best


# ----------------------------------------------------------------------------- 1. reconstruction-tag
def build_reconstruction_tag(s, v):
    L, ty = s["layout"]["reconstruction_tag"], T(s)
    font, size = ty["font_label"], ty["sizes"]["tag"]
    C.assert_min_font(s, size)
    label = v.get("Label", "RECONSTRUCTION").upper()
    l, a, r, b, w = tw(s, font, size, label, L["tracking"])
    sx0, sy0, _, _ = C.safe_rect(s)
    ph = L["pad_y"] * 2 + a + b
    pw = L["pad_x"] + L["dot_size"] + L["dot_gap"] + w + L["pad_x"]
    C.assert_inside_safe(s, "reconstruction tag", sx0, sy0, sx0 + pw, sy0 + ph)
    a_in, a_out = s["animation"]["in_frames"], s["animation"]["out_frames"]
    t_out = a_in * DT + hold(v, L)
    total = t_out + a_out * DT
    js = comp_jsx("Reconstruction_Tag", total)
    js += solid("pl", "Plate", col(s, "charcoal"), sx0 + pw / 2, sy0 + ph / 2, pw, ph)
    js += envelope("pl", s, 0, t_out, max_op=L["plate_alpha"] * 100, animate_pos=False)
    js += solid("bd", "TopRule", col(s, "signal_red"), sx0 + pw / 2, sy0 + 1.5, pw, 3)
    js += envelope("bd", s, 0, t_out, animate_pos=False)
    dcx = sx0 + L["pad_x"] + L["dot_size"] / 2
    base = sy0 + L["pad_y"] + a
    dcy = base - a / 2
    js += solid("dot", "Dot", col(s, "signal_red"), dcx, dcy, L["dot_size"], L["dot_size"])
    blink = [(0, 0.0)] + ramp(0, a_in, 0.0, 100.0, C.ease(s, "type_in"))
    t, on = a_in * DT, True
    half = L["blink_period"] / 2.0
    while t + half < t_out:
        t += half
        on = not on
        blink.append((t, 100.0 if on else L["blink_min_alpha"] * 100))
    blink += ramp(t_out, a_out, blink[-1][1], 0.0, C.ease(s, "type_out"))
    js += keys("dot", "Opacity", blink)
    x = sx0 + L["pad_x"] + L["dot_size"] + L["dot_gap"] - l
    js += text("lb", "Label", label, font, size, col(s, "ivory"), "LEFT_JUSTIFY", x, base, tracking=L["tracking"])
    js += envelope("lb", s, 0, t_out, animate_pos=False)
    return js + finish_jsx(), total, {"plate": [sx0, sy0, sx0 + pw, sy0 + ph]}


# ----------------------------------------------------------------------------- 2. location-stamp
def build_location_stamp(s, v):
    L, ty = s["layout"]["location_stamp"], T(s)
    font = ty["font_mono"]
    s1, s2 = ty["sizes"]["stamp_primary"], ty["sizes"]["stamp_secondary"]
    C.assert_min_font(s, s1, s2)
    l1, l2 = v["Place"].upper(), v.get("Date", "").upper()
    f1 = C.font_for(s, font, s1)
    f2 = C.font_for(s, font, s2)
    _, a1, _, b1, w1 = tw(s, font, s1, l1)
    _, a2, _, b2, w2 = tw(s, font, s2, l2) if l2 else (0, 0, 0, 0, 0)
    sx0, _, sx1, sy1 = C.safe_rect(s)
    block_h = L["rule_height"] + L["rule_gap"] + a1 + b1 + (L["line_gap"] + a2 + b2 if l2 else 0)
    top = sy1 - block_h - L["plate_pad_y"]
    sx0 = sx0 + L["plate_pad_x"]
    C.assert_inside_safe(s, "location stamp", sx0 - L["plate_pad_x"], top - L["plate_pad_y"], sx0 + max(w1, w2) + f1.getlength("M") + L["plate_pad_x"], sy1)
    rule_y = top + L["rule_height"] / 2
    base1 = top + L["rule_height"] + L["rule_gap"] + a1
    base2 = base1 + b1 + L["line_gap"] + a2
    cps = L["chars_per_second"]
    t_rule = 0.0
    t1 = t_rule + L["rule_frames"] * DT
    t2 = t1 + len(l1) / cps + L["line2_delay"]
    t_done = t2 + (len(l2) / cps if l2 else 0)
    t_out = t_done + hold(v, L)
    total = t_out + s["animation"]["out_frames"] * DT
    js = comp_jsx("Location_Stamp", total)
    bw = max(w1, w2) + adv_cursor(s, font, s1) + 2 * L["plate_pad_x"]
    bh = block_h + 2 * L["plate_pad_y"]
    bx0, by0 = sx0 - L["plate_pad_x"], top - L["plate_pad_y"]
    if L["plate_alpha"] > 0:
        js += solid("bp", "Plate", col(s, "charcoal"), bx0 + bw / 2, by0 + bh / 2, bw, bh)
        js += envelope("bp", s, 0, t_out, animate_pos=False, max_op=L["plate_alpha"] * 100)
    js += solid("ru", "Rule", col(s, "gold_accent"), sx0, rule_y, L["rule_width"], L["rule_height"], anchor_left=True)
    js += keys("ru", "Scale", ramp(t_rule, L["rule_frames"], [0, 100, 100], [100, 100, 100], C.ease(s, "type_in")))
    js += envelope("ru", s, 0, t_out, animate_pos=False, in_frames=2)

    def typed(var, name, line, size, color, base, t0):
        j = text(var, name, line, font, size, col(s, color), "LEFT_JUSTIFY", sx0, base)
        j += f'var {var}St = {var}.property("Source Text");\n'
        for i in range(len(line) + 1):
            j += f'var _d = {var}St.value; _d.text = {json.dumps(line[:i])}; {var}St.setValueAtTime({_t(t0 + i / cps if i else 0)}, _d);\n'
        j += shadow(var, L["shadow_softness"], L["shadow_opacity"])
        j += envelope(var, s, 0, t_out, animate_pos=False, in_frames=1)
        return j

    js += typed("ln1", "Place", l1, s1, "ivory", base1, t1)
    if l2:
        js += typed("ln2", "Date", l2, s2, "gold", base2, t2)
    # underscore cursor that steps with the typing, then blinks
    adv1, adv2 = f1.getlength("M"), f2.getlength("M")
    ch = L["cursor_height"]
    js += solid("cu", "Cursor", col(s, "gold_accent"), sx0, base1 + 8, adv1 * 0.9, ch, anchor_left=True)
    pos = []
    for i in range(len(l1) + 1):
        tt = t1 + i / cps
        pos += [(tt - 0.002, [sx0 + adv1 * max(0, i - 1), base1 + 8, 0]), (tt, [sx0 + adv1 * i, base1 + 8, 0])]
    if l2:
        for i in range(len(l2) + 1):
            tt = t2 + i / cps
            prev = [sx0 + adv2 * max(0, i - 1), base2 + 8, 0] if i else pos[-1][1]
            pos += [(tt - 0.002, prev), (tt, [sx0 + adv2 * i, base2 + 8, 0])]
    js += keys("cu", "Position", [p for p in pos if p[0] >= 0])
    blink = [(0, 0.0), (t1, 100.0)]
    t = t_done
    on = True
    while t + 0.5 < t_out:
        t += 0.5
        on = not on
        blink.append((t - 0.002, 0.0 if on else 100.0))
        blink.append((t, 100.0 if on else 0.0))
    blink += [(t_out, 0.0)]
    js += keys("cu", "Opacity", blink)
    return js + finish_jsx(), total, {"block": [sx0, top, sx0 + max(w1, w2), sy1]}


# ----------------------------------------------------------------------------- 3. stat-counter
def _fmt_num(n, mode, decimals):
    if mode == "plain":
        return f"{n:.{decimals}f}" if decimals else str(int(round(n)))
    return f"{n:,.{decimals}f}" if decimals else f"{int(round(n)):,}"


def build_stat_counter(s, v):
    L, ty = s["layout"]["stat_counter"], T(s)
    fn, fl, fc = ty["font_number"], ty["font_label"], ty["font_secondary"]
    sn, sl, sc = ty["sizes"]["stat_number"], ty["sizes"]["stat_label"], ty["sizes"]["stat_context"]
    C.assert_min_font(s, sn, sl, sc)
    start, end = float(v.get("From", 0)), float(v["To"])
    mode, dec = v.get("Format", "comma"), int(v.get("Decimals", 0))
    pre, suf = v.get("Prefix", ""), v.get("Suffix", "")
    final = pre + _fmt_num(end, mode, dec) + suf
    label = v["Label"].upper()
    ctx = v.get("Context", "")
    _, an, _, bn, wn = tw(s, fn, sn, final)
    _, al, _, bl, wl = tw(s, fl, sl, label, L["label_tracking"])
    ac = bc = wc = 0
    if ctx:
        _, ac, _, bc, wc = tw(s, fc, sc, ctx)
    cx = s["canvas"]["width"] / 2
    block_h = an + L["gap_number_rule"] + L["rule_height"] + L["gap_rule_label"] + al + bl + (L["gap_label_context"] + ac + bc if ctx else 0)
    top = L["center_y"] - block_h / 2
    C.assert_inside_safe(s, "stat counter", cx - max(wn, wl, wc) / 2, top, cx + max(wn, wl, wc) / 2, top + block_h)
    bn_y = top + an
    rule_y = bn_y + L["gap_number_rule"] + L["rule_height"] / 2
    bl_y = rule_y + L["rule_height"] / 2 + L["gap_rule_label"] + al
    bc_y = bl_y + bl + L["gap_label_context"] + ac
    a_in, a_out = s["animation"]["in_frames"], s["animation"]["out_frames"]
    t_count = a_in * DT * 0.5
    n_frames = max(2, int(round(L["count_seconds"] / DT)))
    t_label = t_count + L["count_seconds"] * 0.55
    t_out = t_count + L["count_seconds"] + hold(v, L)
    total = t_out + a_out * DT
    js = comp_jsx("Stat_Counter", total)
    js += scrim(s, "sc", 0, t_out, L["scrim_alpha"])
    js += text("nm", "Number", final, fn, sn, col(s, "ivory"), "CENTER_JUSTIFY", cx, bn_y)
    js += 'var nmSt = nm.property("Source Text");\n'
    ec = C.ease(s, "type_in")
    for f in range(n_frames + 1):
        val = start + (end - start) * ec(f / float(n_frames))
        js += f'var _d = nmSt.value; _d.text = {json.dumps(pre + _fmt_num(val, mode, dec) + suf)}; nmSt.setValueAtTime({_t(t_count + f * DT if f else 0)}, _d);\n'
    js += shadow("nm", 24, 60, 0)
    js += envelope("nm", s, t_count, t_out, pos=[cx, bn_y], slide=(0, 24))
    js += solid("ru", "Rule", col(s, "gold_accent"), cx, rule_y, L["rule_width"], L["rule_height"])
    js += keys("ru", "Scale", ramp(t_label, a_in, [0, 100, 100], [100, 100, 100], ec))
    js += envelope("ru", s, t_label, t_out, animate_pos=False, in_frames=2)
    js += text("lb", "Label", label, fl, sl, col(s, "gold"), "CENTER_JUSTIFY", cx, bl_y, tracking=L["label_tracking"])
    js += envelope("lb", s, t_label, t_out, pos=[cx, bl_y], slide=(0, 18))
    if ctx:
        js += text("cx", "Context", ctx, fc, sc, col(s, "ivory"), "CENTER_JUSTIFY", cx, bc_y)
        js += envelope("cx", s, t_label + 0.25, t_out, pos=[cx, bc_y], slide=(0, 18), max_op=85)
    return js + finish_jsx(), total, {"block": [cx - max(wn, wl, wc) / 2, top, cx + max(wn, wl, wc) / 2, top + block_h]}


# ----------------------------------------------------------------------------- 4. timeline-strip
def build_timeline_strip(s, v):
    L, ty = s["layout"]["timeline_strip"], T(s)
    fy, flb = ty["font_number"], ty["font_secondary"]
    sy_, sl = ty["sizes"]["timeline_year"], ty["sizes"]["timeline_label"]
    C.assert_min_font(s, sy_, sl)
    ev = v["Events"]
    n = len(ev)
    if not 2 <= n <= L["max_events"]:
        raise SystemExit(f"BUILD ERROR: timeline-strip needs 2..{L['max_events']} events, got {n}")
    active = int(v.get("Active", n - 1))
    sx0, _, sx1, sy1 = C.safe_rect(s)
    inner_w = sx1 - sx0 - 2 * L["pad_x"]
    colw = inner_w / n
    labels = [balanced_wrap(s, flb, sl, e["Label"], colw - L["col_gutter"], L["max_label_lines"]) for e in ev]
    nlines = max(len(x) for x in labels)
    _, ay, _, by, _ = tw(s, fy, sy_, "0123456789")
    _, alb, _, blb, _ = tw(s, flb, sl, "Hgy")
    label_h = alb + (nlines - 1) * L["label_leading"] + blb
    plate_h = L["pad_y"] + ay + by + L["year_gap"] + L["dot_size"] + L["label_gap"] + label_h + L["pad_y"]
    ptop = sy1 - plate_h
    C.assert_inside_safe(s, "timeline plate", sx0, ptop, sx1, sy1)
    year_base = ptop + L["pad_y"] + ay
    line_y = year_base + by + L["year_gap"] + L["dot_size"] / 2
    label_base = line_y + L["dot_size"] / 2 + L["label_gap"] + alb
    xs = [sx0 + L["pad_x"] + colw * (i + 0.5) for i in range(n)]
    a_in, a_out = s["animation"]["in_frames"], s["animation"]["out_frames"]
    t0 = a_in * DT
    stg = L["event_stagger"]
    t_last = t0 + stg * (n - 1)
    t_out = t_last + a_in * DT + hold(v, L)
    total = t_out + a_out * DT
    js = comp_jsx("Timeline_Strip", total)
    js += solid("pl", "Plate", col(s, "charcoal"), (sx0 + sx1) / 2, ptop + plate_h / 2, sx1 - sx0, plate_h)
    js += envelope("pl", s, 0, t_out, pos=[(sx0 + sx1) / 2, ptop + plate_h / 2], slide=(0, 30), max_op=L["plate_alpha"] * 100)
    js += solid("bt", "PlateTopRule", col(s, "gold_accent"), (sx0 + sx1) / 2, ptop + 1, sx1 - sx0, 2)
    js += envelope("bt", s, 0, t_out, pos=[(sx0 + sx1) / 2, ptop + 1], slide=(0, 30), max_op=70)
    js += solid("ln", "Line", col(s, "gold_accent"), xs[0], line_y, xs[-1] - xs[0], L["line_height"], anchor_left=True)
    js += keys("ln", "Scale", [(0, [0, 100, 100])] + ramp(t0, int(round((t_last - t0) / DT)) or 1, [0, 100, 100], [100, 100, 100], lambda p: p))
    js += envelope("ln", s, t0, t_out, animate_pos=False, in_frames=2, max_op=60)
    pop = C.ease(s, "type_pop")
    for i, e in enumerate(ev):
        ti = t0 + stg * i
        hot = i == active
        dsz = L["dot_size"] * (1.0 if hot else 0.75)
        js += solid(f"d{i}", f"Dot{i}", col(s, "gold_accent") if hot else col(s, "ivory"), xs[i], line_y, dsz, dsz)
        js += f'd{i}.property("Rotation").setValue(45);\n'
        js += keys(f"d{i}", "Scale", [(0, [0, 0, 100])] + ramp(ti, 10, [0, 0, 100], [100, 100, 100], pop))
        js += envelope(f"d{i}", s, ti, t_out, animate_pos=False, in_frames=4)
        js += text(f"y{i}", f"Year{i}", e["Year"], fy, sy_, col(s, "gold") if hot else col(s, "ivory"), "CENTER_JUSTIFY", xs[i], year_base)
        js += envelope(f"y{i}", s, ti, t_out, pos=[xs[i], year_base], slide=(0, 16))
        js += text(f"l{i}", f"Label{i}", "\r".join(labels[i]), flb, sl, col(s, "ivory"), "CENTER_JUSTIFY", xs[i], label_base,
                   leading=L["label_leading"])
        js += envelope(f"l{i}", s, ti + 0.12, t_out, pos=[xs[i], label_base], slide=(0, 16), max_op=100 if hot else 80)
    return js + finish_jsx(), total, {"plate": [sx0, ptop, sx1, sy1]}


# ----------------------------------------------------------------------------- 5. then-now
def build_then_now(s, v):
    L, ty = s["layout"]["then_now"], T(s)
    fl, fn = ty["font_label"], ty["font_primary"]
    sl, sn = ty["sizes"]["tag"], ty["sizes"]["then_now_name"]
    C.assert_min_font(s, sl, sn)
    tl, tn = v.get("Then_Label", "ON SCREEN").upper(), v["Then"]
    nl, nn = v.get("Now_Label", "IN REAL LIFE").upper(), v["Now"]
    _, atl, _, btl, wtl = tw(s, fl, sl, tl, L["label_tracking"])
    lt, atn, rt, btn, wtn = tw(s, fn, sn, tn)
    _, anl, _, bnl, wnl = tw(s, fl, sl, nl, L["label_tracking"])
    _, ann, _, bnn, wnn = tw(s, fn, sn, nn)
    cx = s["canvas"]["width"] / 2
    content_w = max(wtl, wtn, wnl, wnn)
    pw = content_w + 2 * L["pad_x"]
    ph = (L["pad_y"] + atl + btl + L["label_gap"] + atn + btn + L["row_gap"] + L["divider_height"] + L["row_gap"]
          + anl + bnl + L["label_gap"] + ann + bnn + L["pad_y"])
    ptop = L["center_y"] - ph / 2
    C.assert_inside_safe(s, "then-now plate", cx - pw / 2, ptop, cx + pw / 2, ptop + ph)
    y = ptop + L["pad_y"] + atl
    b_tl = y
    b_tn = b_tl + btl + L["label_gap"] + atn
    div_y = b_tn + btn + L["row_gap"] + L["divider_height"] / 2
    b_nl = div_y + L["divider_height"] / 2 + L["row_gap"] + anl
    b_nn = b_nl + bnl + L["label_gap"] + ann
    a_in, a_out = s["animation"]["in_frames"], s["animation"]["out_frames"]
    t_strike = L["strike_at"]
    t_now = t_strike + L["strike_frames"] * DT + L["now_delay"]
    t_out = t_now + a_in * DT + hold(v, L)
    total = t_out + a_out * DT
    ein = C.ease(s, "type_in")
    js = comp_jsx("Then_Now", total)
    js += solid("pl", "Plate", col(s, "charcoal"), cx, ptop + ph / 2, pw, ph)
    js += envelope("pl", s, 0, t_out, pos=[cx, ptop + ph / 2], slide=(0, 30), max_op=L["plate_alpha"] * 100)
    for nm, yy in (("bt", ptop + 1), ("bb", ptop + ph - 1)):
        js += solid(nm, nm, col(s, "gold_accent"), cx, yy, pw, 2)
        js += envelope(nm, s, 0, t_out, pos=[cx, yy], slide=(0, 30), max_op=70)
    js += text("tl", "ThenLabel", tl, fl, sl, col(s, "slate"), "CENTER_JUSTIFY", cx, b_tl, tracking=L["label_tracking"])
    js += envelope("tl", s, 0, t_out, pos=[cx, b_tl], slide=(0, 30))
    js += text("tn", "Then", tn, fn, sn, col(s, "ivory"), "CENTER_JUSTIFY", cx, b_tn)
    dim = ramp(t_strike, L["strike_frames"], 100.0, L["dim_alpha"] * 100, ein)
    # opacity exit keys must be sparse: EC re-interpolates dense eased ramps so the fade never completes (probe8)
    js += keys("tn", "Opacity", [(0, 0.0)] + ramp(t_strike, L["strike_frames"], 100.0, L["dim_alpha"] * 100, ein)
               + [(round(t_strike, 5), L["dim_alpha"] * 100), (round(t_out, 5), L["dim_alpha"] * 100),
                  (round(t_out + a_out * DT, 5), 0.0)])
    js += keys("tn", "Position", ramp(0, a_in, [cx, b_tn + 30, 0], [cx, b_tn, 0], ein))
    sk_y = b_tn - atn * 0.36
    js += solid("sk", "Strike", col(s, "signal_red"), cx - wtn / 2 - 10, sk_y, wtn + 20, L["strike_height"], anchor_left=True)
    js += keys("sk", "Scale", [(0, [0, 100, 100])] + ramp(t_strike, L["strike_frames"], [0, 100, 100], [100, 100, 100], ein))
    js += envelope("sk", s, t_strike, t_out, animate_pos=False, in_frames=1)
    js += solid("dv", "Divider", col(s, "gold_accent"), cx, div_y, L["divider_width"], L["divider_height"])
    js += envelope("dv", s, t_strike, t_out, animate_pos=False)
    js += text("nl", "NowLabel", nl, fl, sl, col(s, "gold_accent"), "CENTER_JUSTIFY", cx, b_nl, tracking=L["label_tracking"])
    js += envelope("nl", s, t_now, t_out, pos=[cx, b_nl], slide=(0, 22))
    js += text("nn", "Now", nn, fn, sn, col(s, "gold"), "CENTER_JUSTIFY", cx, b_nn)
    js += envelope("nn", s, t_now + 0.1, t_out, pos=[cx, b_nn], slide=(0, 22))
    return js + finish_jsx(), total, {"plate": [cx - pw / 2, ptop, cx + pw / 2, ptop + ph]}


# ----------------------------------------------------------------------------- 6. source-tag
def build_source_tag(s, v):
    L, ty = s["layout"]["source_tag"], T(s)
    fl, fs = ty["font_label"], ty["font_secondary"]
    sz = ty["sizes"]["tag"]
    C.assert_min_font(s, sz)
    tier = v.get("Tier", "QUOTED").upper()
    if tier not in L["tiers"]:
        raise SystemExit(f"BUILD ERROR: Tier must be one of {list(L['tiers'])}")
    bg, fg = L["tiers"][tier]
    src = v["Source"]
    lt, at, rt, bt, wt = tw(s, fl, sz, tier, L["chip_tracking"])
    ls, as_, rs, bs, ws = tw(s, fs, sz, src)
    _, sy0, sx1, sy1 = C.safe_rect(s)
    asc, dsc = max(at, as_), max(bt, bs)
    chip_w = wt + 2 * L["chip_pad_x"]
    chip_h = asc + dsc + 2 * L["chip_pad_y"]
    pw = L["pad_x"] + chip_w + L["gap"] + ws + L["pad_x"]
    ph = chip_h + 2 * L["pad_y"]
    px0, py0 = sx1 - pw, sy1 - ph
    C.assert_inside_safe(s, "source tag", px0, py0, sx1, sy1)
    base = py0 + L["pad_y"] + L["chip_pad_y"] + asc
    a_in, a_out = s["animation"]["in_frames"], s["animation"]["out_frames"]
    t_out = a_in * DT + hold(v, L)
    total = t_out + a_out * DT
    sl = (L["slide_px"], 0)
    js = comp_jsx("Source_Tag", total)
    js += solid("pl", "Plate", col(s, "charcoal"), px0 + pw / 2, py0 + ph / 2, pw, ph)
    js += envelope("pl", s, 0, t_out, pos=[px0 + pw / 2, py0 + ph / 2], slide=sl, max_op=L["plate_alpha"] * 100)
    cx0 = px0 + L["pad_x"]
    js += solid("ch", "Chip", col(s, bg), cx0 + chip_w / 2, py0 + ph / 2, chip_w, chip_h)
    js += envelope("ch", s, 0, t_out, pos=[cx0 + chip_w / 2, py0 + ph / 2], slide=sl)
    js += text("ct", "Tier", tier, fl, sz, col(s, fg), "LEFT_JUSTIFY", cx0 + L["chip_pad_x"] - lt, base, tracking=L["chip_tracking"])
    js += envelope("ct", s, 0, t_out, pos=[cx0 + L["chip_pad_x"] - lt, base], slide=sl)
    sx = cx0 + chip_w + L["gap"] - ls
    js += text("st", "Source", src, fs, sz, col(s, "ivory"), "LEFT_JUSTIFY", sx, base)
    js += envelope("st", s, 0.08, t_out, pos=[sx, base], slide=sl)
    return js + finish_jsx(), total, {"plate": [px0, py0, sx1, sy1]}


# ----------------------------------------------------------------------------- 7. credit-line
def build_credit_line(s, v):
    L, ty = s["layout"]["credit_line"], T(s)
    fl, fr, fn = ty["font_label"], ty["font_secondary"], ty["font_primary"]
    st_, sr, sn = ty["sizes"]["tag"], ty["sizes"]["credit_role"], ty["sizes"]["credit_name"]
    C.assert_min_font(s, st_, sr, sn)
    title, role, name = v.get("Title", "").upper(), v["Role"], v["Name"].upper()
    _, at, _, bt, wt = tw(s, fl, st_, title, L["title_tracking"]) if title else (0, 0, 0, 0, 0)
    lr, ar, rr, br, wr = tw(s, fr, sr, role)
    ln_, an, rn, bn, wn = tw(s, fn, sn, name, L["name_tracking"])
    cx, cy = s["canvas"]["width"] / 2, L["center_y"]
    g = L["gutter"] / 2
    row_base = cy + max(ar, an) / 2
    title_base = row_base - max(ar, an) - L["title_gap"]
    C.assert_inside_safe(s, "credit row", cx - g - wr, title_base - at, cx + g + wn, row_base + max(br, bn) + L["crawl_px"])
    a_in, a_out = s["animation"]["in_frames"], s["animation"]["out_frames"]
    t_in = L["lead_in"]
    t_out = t_in + a_in * DT + hold(v, L)
    total = t_out + a_out * DT
    c = s["canvas"]
    js = comp_jsx("Credit_Line", total)
    js += solid("bg", "Black", "#000000", c["width"] / 2, c["height"] / 2, c["width"], c["height"])
    nin = int(round(t_in / DT)) or 1
    js += keys("bg", "Opacity", [(0.0, 0.0), (t_in, 0.0), (round(nin * DT, 5), 100.0), (round(t_out, 5), 100.0),
                                 (round(t_out + a_out * DT, 5), 0.0)])
    crawl = L["crawl_px"]

    def crawl_keys(var, x, y):
        return keys(var, "Position", [(0, [x, y + crawl / 2, 0]), (total, [x, y - crawl / 2, 0])])

    if title:
        js += text("ti", "Title", title, fl, st_, col(s, "slate"), "CENTER_JUSTIFY", cx, title_base, tracking=L["title_tracking"])
        js += envelope("ti", s, t_in, t_out, animate_pos=False) + crawl_keys("ti", cx, title_base)
    js += text("ro", "Role", role, fr, sr, col(s, "ivory"), "RIGHT_JUSTIFY", cx - g, row_base)
    js += envelope("ro", s, t_in + 0.2, t_out, animate_pos=False, max_op=75) + crawl_keys("ro", cx - g, row_base)
    js += text("na", "Name", name, fn, sn, col(s, "ivory"), "LEFT_JUSTIFY", cx + g - ln_, row_base, tracking=L["name_tracking"])
    js += envelope("na", s, t_in + 0.2, t_out, animate_pos=False) + crawl_keys("na", cx + g - ln_, row_base)
    return js + finish_jsx(), total, {"row": [cx - g - wr, title_base - at, cx + g + wn, row_base + max(br, bn)]}


# ----------------------------------------------------------------------------- 8. story-tracker
def build_story_tracker(s, v):
    L, ty = s["layout"]["story_tracker"], T(s)
    fl, sz = ty["font_label"], ty["sizes"]["tag"]
    C.assert_min_font(s, sz)
    items = [x.upper() for x in v["Items"]]
    act = int(v["Active"])
    prev = int(v.get("Previous", act))
    meas = [tw(s, fl, sz, it, L["tracking"]) for it in items]
    asc = max(m[1] for m in meas)
    dsc = max(m[3] for m in meas)
    widths = [m[4] for m in meas]
    num_txt = f"{act + 1:02d}/{len(items):02d}"
    nl_, na, _, nb, nw = tw(s, fl, sz, num_txt, L["tracking"])
    content_w = nw + L["num_gap"] + sum(widths) + L["item_gap"] * (len(items) - 1)
    pw = content_w + 2 * L["pad_x"]
    ph = L["pad_y"] * 2 + asc + dsc + L["underline_gap"] + L["underline_h"]
    _, sy0, sx1, _ = C.safe_rect(s)
    px0 = sx1 - pw
    C.assert_inside_safe(s, "story tracker", px0, sy0, sx1, sy0 + ph)
    base = sy0 + L["pad_y"] + asc
    ul_y = base + dsc + L["underline_gap"] + L["underline_h"] / 2
    a_in, a_out = s["animation"]["in_frames"], s["animation"]["out_frames"]
    t_move = a_in * DT + 0.2
    t_out = t_move + L["move_frames"] * DT + hold(v, L)
    total = t_out + a_out * DT
    sl = (0, -24)
    js = comp_jsx("Story_Tracker", total)
    js += solid("pl", "Plate", col(s, "charcoal"), px0 + pw / 2, sy0 + ph / 2, pw, ph)
    js += envelope("pl", s, 0, t_out, pos=[px0 + pw / 2, sy0 + ph / 2], slide=sl, max_op=L["plate_alpha"] * 100)
    x = px0 + L["pad_x"]
    js += text("nu", "Counter", num_txt, fl, sz, col(s, "gold_accent"), "LEFT_JUSTIFY", x - nl_, base, tracking=L["tracking"])
    js += envelope("nu", s, 0, t_out, pos=[x - nl_, base], slide=sl)
    x += nw + L["num_gap"]
    centers = []
    for i, it in enumerate(items):
        lft = meas[i][0]
        if i == act:
            color, op = "gold", 100
        elif i < act:
            color, op = "ivory", L["done_alpha"] * 100
        else:
            color, op = "ivory", L["inactive_alpha"] * 100
        js += text(f"it{i}", f"Item{i}", it, fl, sz, col(s, color), "LEFT_JUSTIFY", x - lft, base, tracking=L["tracking"])
        js += envelope(f"it{i}", s, 0, t_out, pos=[x - lft, base], slide=sl, max_op=op)
        centers.append((x, widths[i]))
        x += widths[i] + L["item_gap"]
    ax, aw = centers[act]
    px_, pw_ = centers[prev]
    js += solid("ul", "Underline", col(s, "gold_accent"), ax, ul_y, aw, L["underline_h"], anchor_left=True)
    ein = C.ease(s, "type_in")
    js += keys("ul", "Position", ramp(t_move, L["move_frames"], [px_, ul_y, 0], [ax, ul_y, 0], ein))
    js += keys("ul", "Scale", ramp(t_move, L["move_frames"], [pw_ / aw * 100, 100, 100], [100, 100, 100], ein))
    js += envelope("ul", s, 0, t_out, animate_pos=False)
    return js + finish_jsx(), total, {"plate": [px0, sy0, sx1, sy0 + ph]}


# ----------------------------------------------------------------------------- 9. kinetic-quote
def _word_times(words, wpm, pause):
    t, out = 0.0, []
    for w in words:
        out.append(t)
        t += 60.0 / wpm
        if re.search(r"[.,;:!?—]$", w):
            t += pause
    return out


def build_kinetic_quote(s, v):
    L, ty = s["layout"]["kinetic_quote"], T(s)
    fq, fl = ty["font_quote"], ty["font_label"]
    sq, sa, sm = ty["sizes"]["kinetic_quote"], ty["sizes"]["tag"], ty["sizes"]["quote_mark"]
    quote, attr = v["Quote"].strip(), v["Attribution"].upper()
    if len(quote.replace("|", " ").split()) <= L["short_quote_words"]:
        sq = ty["sizes"]["kinetic_quote_short"]
    C.assert_min_font(s, sq, sa)
    lines = balanced_wrap(s, fq, sq, quote, L["max_width"], L["max_lines"])
    quote = " ".join(quote.replace("|", " ").split())
    f = C.font_for(s, fq, sq)
    line_w = [f.getlength(ln) for ln in lines]
    block_w = max(line_w)
    _, aq, _, bq, _ = tw(s, fq, sq, "Hgy")
    lead = sq * L["leading_ratio"]
    _, aa, _, ba, wa = tw(s, fl, sa, attr, L["attr_tracking"])
    lm, am, rm, bm, wm = tw(s, fq, sm, "“")
    block_h = am + bm * 0 + L["mark_gap"] + aq + (len(lines) - 1) * lead + bq + L["attribution_gap"] + aa + ba
    cx = s["canvas"]["width"] / 2
    left = cx - block_w / 2
    top = L["center_y"] - block_h / 2
    C.assert_inside_safe(s, "kinetic quote", left - 4, top, left + max(block_w, wa) + 4, top + block_h)
    mark_base = top + am
    first_base = mark_base + L["mark_gap"] + aq
    attr_base = first_base + (len(lines) - 1) * lead + bq + L["attribution_gap"] + aa
    words = quote.split()
    emph = set()
    if v.get("Emphasis"):
        ew = v["Emphasis"].split()
        for i in range(len(words) - len(ew) + 1):
            if [w.strip("\"'“”") for w in words[i:i + len(ew)]] == [w.strip("\"'“”") for w in ew]:
                emph.update(range(i, i + len(ew)))
    t0 = L["lead_in"]
    rel = v.get("Word_Times") or _word_times(words, float(v.get("WPM", L["wpm"])), L["punct_pause"])
    if len(rel) != len(words):
        raise SystemExit(f"BUILD ERROR: Word_Times has {len(rel)} entries for {len(words)} words")
    t_words = [t0 + r for r in rel]
    t_attr = t_words[-1] + L["attr_delay"]
    t_out = t_attr + hold(v, L)
    total = t_out + s["animation"]["out_frames"] * DT
    js = comp_jsx("Kinetic_Quote", total)
    js += scrim(s, "sc", 0, t_out, L["scrim_alpha"])
    js += text("qm", "QuoteMark", "“", fq, sm, col(s, "gold_accent"), "LEFT_JUSTIFY", left - lm, mark_base)
    js += envelope("qm", s, 0.05, t_out, pos=[left - lm, mark_base], slide=(0, 20), max_op=90)
    wi = 0
    for li, ln in enumerate(lines):
        base = first_base + li * lead
        lw = ln.split(" ")
        for k, w in enumerate(lw):
            x = left + f.getlength(" ".join(lw[:k]) + (" " if k else ""))
            c = "gold_accent" if wi in emph else "ivory"
            var = f"w{wi}"
            js += text(var, f"W{wi}", w, fq, sq, col(s, c), "LEFT_JUSTIFY", x, base)
            js += shadow(var, 20, 55, 0)
            js += envelope(var, s, t_words[wi], t_out, pos=[x, base], slide=(0, L["rise_px"]), in_frames=L["word_frames"])
            wi += 1
    js += text("at", "Attribution", "— " + attr, fl, sa, col(s, "gold_accent"), "LEFT_JUSTIFY", left, attr_base, tracking=L["attr_tracking"])
    js += envelope("at", s, t_attr, t_out, pos=[left, attr_base], slide=(0, 16))
    return js + finish_jsx(), total, {"block": [left, top, left + block_w, top + block_h]}


# ----------------------------------------------------------------------------- 10. line-third
def build_line_third(s, v):
    """House adaptation of Mixkit 'Simple bottom third' (mixkit.co template 311): bold uppercase heading above a
    solid rule, wide-tracked subheading below it. Reveal is a per-glyph cascade: the heading's characters fade in
    left->right and the subhead's right->left, timed so the appearance front follows the template's decelerating
    sweep, with a white caret block riding the front; the exit mirrors the entry (reverse stagger), then the rule
    retracts. (Linear Wipe was measured unusable in EffectCraft: font/placement-dependent, inconsistent boundary
    semantics.) All numbers in layout.line_third."""
    L = s["layout"]["line_third"]
    ty = T(s)
    f1, z1, tr1 = L["heading_font"], L["heading_size"], L["heading_tracking"]
    f2, z2, tr2 = L["sub_font"], L["sub_size"], L["sub_tracking"]
    C.assert_min_font(s, z1, z2)
    head, sub = " ".join(v["Heading"].split()).upper(), " ".join(v["Sub"].split()).upper()
    if not head or not sub:
        raise SystemExit("BUILD ERROR: 'Heading' and 'Sub' must both be non-empty (got blank/whitespace)")
    l1, a1, r1, b1, w1 = tw(s, f1, z1, head, tr1)
    l2, a2, r2, b2, w2 = tw(s, f2, z2, sub, tr2)
    if w1 > L["max_heading_w"]:
        raise SystemExit(f"BUILD ERROR: heading '{head}' is {w1:.0f}px wide, limit {L['max_heading_w']}px")
    if w2 > L["max_sub_w"]:
        raise SystemExit(f"BUILD ERROR: sub '{sub}' is {w2:.0f}px wide, limit {L['max_sub_w']}px")
    sx0, _, _, sy1 = C.safe_rect(s)
    x_l = sx0
    span = max(w1, w2)
    rule_x = x_l
    rule_w = span + L["rule_project_px"]
    sub_baseline = sy1 - b2
    sub_ink_top = sub_baseline - a2
    rule_top = sub_ink_top - L["gap_rule_sub"] - L["rule_h"]
    rule_cy = rule_top + L["rule_h"] / 2.0
    head_base = rule_top - L["gap_heading_rule"] - b1
    head_ink_top = head_base - a1
    C.assert_inside_safe(s, "line third", rule_x, head_ink_top, rule_x + rule_w, sy1)
    x1h, x1s = x_l + w1 + 2.0, x_l + w2 + 2.0
    top = head_ink_top

    e0 = float(L["lead_in"])
    wf_h, wf_s = int(L["wipe_frames"]), int(L["sub_wipe_frames"])
    wf_e = int(L["exit_wipe_frames"])
    t_in_h = e0 + wf_h * DT
    t_in_s = e0 + wf_s * DT
    t_out0 = max(t_in_h, t_in_s) + hold(v, L)   # hold starts after BOTH reveals finish (sub wipe is 34f)
    t_out1 = t_out0 + wf_e * DT
    t_r0 = t_out1
    total = t_r0 + int(L["rule_retract_frames"]) * DT
    ein, eout = C.ease(s, "type_in"), C.ease(s, "type_out")

    def pinv(fn, y):
        """Inverse of a monotonic 0..1 easing: bisect p with fn(p) = y."""
        y = min(1.0, max(0.0, y))
        lo, hi = 0.0, 1.0
        for _ in range(40):
            mid = (lo + hi) / 2.0
            if fn(mid) < y:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2.0

    # per-glyph cascade: chars fade in as the (virtual) reveal front passes their center, fade out on reverse sweep
    def cascade(prefix, name, txt, font, size, hexcol, tracking, x_l, base, ink_left, front0, front1, rtl,
                t_in0, wf_in, t_out0, t_out1):
        """Char layers for one line. front0->front1 is the entry sweep (origin end -> far end reversed for rtl).
        Returns JSX."""
        f = C.font_for(s, font, size)
        tr_px = tracking / 1000.0 * size
        g_in, g_out = int(L["glyph_frames"]), int(L["glyph_out_frames"])
        js = ""
        cum = 0.0
        for i, ch in enumerate(txt):
            if ch == " ":
                cum += f.getlength(" ") + tr_px
                continue
            l_i, _, r_i, _ = C.ink(s, font, size, ch)
            js += text(f"{prefix}{i}", f"{name}", ch, font, size, hexcol, "LEFT_JUSTIFY",
                       (x_l - ink_left) + cum - l_i, base)
            cx = x_l + cum + (r_i - l_i) / 2.0
            # entry: a char appears when the reveal front (sweeping front0 -> front1) reaches its center
            t_ap = t_in0 + wf_in * DT * pinv(ein, (cx - front0) / (front1 - front0))
            # exit: a char dies when the erase front (sweeping the opposite way) reaches it
            if rtl:  # erase mirrors the reveal: the sub dies left->right (leftmost char first)
                p_out = pinv(eout, (cx - front1) / (front0 - front1))
            else:
                p_out = pinv(eout, (front1 - cx) / (front1 - front0))
            t_die = t_out0 + (t_out1 - t_out0) * p_out
            js += keys(f"{prefix}{i}", "Opacity", [(0.0, 0.0), (round(t_ap, 5), 0.0),
                       (round(t_ap + g_in * DT, 5), 100.0), (round(t_die, 5), 100.0),
                       (round(t_die + g_out * DT, 5), 0.0)]) + "\n"
            cum += f.getlength(ch) + tr_px
        return js

    # caret fronts (densely keyed, verified solid-position mechanism)
    def front_keys(t0, frames, x0, x1, fn):
        return [(t0 + i * DT, x0 + (x1 - x0) * fn(i / float(frames))) for i in range(frames + 1)]

    hc_front = front_keys(e0, wf_h, x_l - 2.0, x1h, ein) + [(t_out0, x1h)] \
        + front_keys(t_out0, wf_e, x1h, x_l - 4.0, eout)
    sc_front = front_keys(e0, wf_s, x1s, x_l - 2.0, ein) + [(t_out0, x_l - 2.0)] \
        + front_keys(t_out0, wf_e, x_l - 2.0, x1s, eout)

    caret_op = [(0.0, 0.0), (e0 - 0.01, 0.0), (e0 + 0.01, 100.0), (t_in_h - 2 * DT, 100.0), (t_in_h, 0.0),
                (t_out0, 0.0), (t_out0 + 0.01, 100.0), (t_out1 - 2 * DT, 100.0), (t_out1, 0.0)]
    sub_caret_op = [(0.0, 0.0), (e0 - 0.01, 0.0), (e0 + 0.01, 100.0), (t_in_s - 2 * DT, 100.0), (t_in_s, 0.0),
                    (t_out0, 0.0), (t_out0 + 0.01, 100.0), (t_out1 - 2 * DT, 100.0), (t_out1, 0.0)]

    js = comp_jsx("Line_Third", total)
    js += solid("ru", "Rule", L["rule_color"], rule_x, rule_cy, rule_w, L["rule_h"])
    js += f'ru.property("Anchor Point").setValue([{round(rule_w, 2)}, {round(L["rule_h"] / 2.0, 2)}, 0]);\n'
    js += f'ru.property("Position").setValue([{round(rule_x + rule_w, 2)}, {round(rule_cy, 2)}, 0]);\n'
    fr_r = int(L["rule_draw_frames"])
    js += keys("ru", "Scale", [(0.0, [0, 100, 100])]
               + ramp(e0, fr_r, [0, 100, 100], [100, 100, 100], ein)
               + [(round(t_r0, 4), [100, 100, 100]),
                  (round(t_r0 + (int(L["rule_retract_frames"]) - 1) * DT, 4), [0, 100, 100]),
                  (round(total, 4), [0, 100, 100])])

    js += cascade("h", "Heading", head, f1, z1, L["heading_color"], tr1, x_l, head_base, l1,
                  x_l - 2.0, x1h, False, e0, wf_h, t_out0, t_out1)
    hc_h = a1 + b1  # caret matches the heading ink height and its vertical ink center
    js += solid("hc", "HeadingBlock", L["caret_color"], 0, 0, L["caret_w"], hc_h)
    js += f'hc.property("Anchor Point").setValue([{round(L["caret_w"] / 2.0, 2)}, {round(hc_h / 2.0, 2)}, 0]);\n'
    js += keys("hc", "Position", [(t, [round(fx + L["caret_w"] / 2.0 - 6.0, 2), round(head_base + (b1 - a1) / 2.0, 2), 0])
                                  for t, fx in hc_front]) + "\n"
    js += keys("hc", "Opacity", caret_op) + "\n"

    js += cascade("sb", "Sub", sub, f2, z2, L["sub_color"], tr2, x_l, sub_baseline, l2,
                  x1s, x_l - 2.0, True, e0, wf_s, t_out0, t_out1)
    sc_h = a2 + b2  # same for the sub caret, on the sub line itself
    js += solid("sc", "SubBlock", L["caret_color"], 0, 0, L["sub_caret_w"], sc_h)
    js += f'sc.property("Anchor Point").setValue([{round(L["sub_caret_w"] / 2.0, 2)}, {round(sc_h / 2.0, 2)}, 0]);\n'
    sc_cy = sub_baseline + (b2 - a2) / 2.0
    js += keys("sc", "Position", [(t, [round(fx - L["sub_caret_w"] / 2.0 + 6.0, 2), round(sc_cy, 2), 0])
                                  for t, fx in sc_front]) + "\n"
    js += keys("sc", "Opacity", sub_caret_op) + "\n"
    return js + finish_jsx(), total, {"block": [rule_x, top, rule_x + rule_w, sy1]}


# ----------------------------------------------------------------------------- title expansion (v3.4)
BUILDERS = {
    "reconstruction-tag": build_reconstruction_tag,
    "location-stamp": build_location_stamp,
    "stat-counter": build_stat_counter,
    "timeline-strip": build_timeline_strip,
    "then-now": build_then_now,
    "source-tag": build_source_tag,
    "credit-line": build_credit_line,
    "story-tracker": build_story_tracker,
    "kinetic-quote": build_kinetic_quote,
    "line-third": build_line_third,
}

from _families_titles import TITLE_BUILDERS as _TITLE_BUILDERS  # noqa: E402  (module imports this file)
BUILDERS.update(_TITLE_BUILDERS)


def build(family, style, values, out_dir, dry=False):
    jsx, total, box = BUILDERS[family](style, values)
    proj = save_project(style, jsx, out_dir, family, dry)
    return proj, total, box
