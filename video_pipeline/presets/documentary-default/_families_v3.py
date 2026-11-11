"""Families v3 (2026-11-07): people identification + evidence overlays.

  person-pin         1-3 people in ONE frame: ring on the person, leader line, name/role plate (positions supplied by
                     the plan, never guessed from faces).
  people-panel       1-3 portraits side by side (images embedded and cropped on a focus point) with names + roles.
  group-legend       "IN THIS PHOTO" band for group photos whose left-to-right order is not documented.
  article-highlight  Typeset clipping on paper (outlet, meta line, verbatim body) with a marker sweep over the quote.
  photo-annotation   Ellipse draws around a detail in a still, leader line, label plate.
"""
import os

from PIL import Image

import _common as C
from _families_v2 import (DT, BUILDERS, T, _r, _t, _v, balanced_wrap, col, comp_jsx, envelope, finish_jsx, hold, keys,
                          ramp, shadow, solid, text, tw)


def solid_anchor(var, name, hexcol, x, y, w, h, anchor):
    """Solid whose anchor sits at one edge: anchor in left|right|top|bottom; (x, y) = that edge's midpoint."""
    rgb = C.hex_to_rgb(hexcol)
    ax = {"left": 0, "right": w, "top": w / 2, "bottom": w / 2}[anchor]
    ay = {"left": h / 2, "right": h / 2, "top": 0, "bottom": h}[anchor]
    return (f'var {var} = comp.layers.addSolid([{rgb[0]}, {rgb[1]}, {rgb[2]}], "{name}", {max(1, int(round(w)))}, {max(1, int(round(h)))}, 1.0);\n'
            f'{var}.property("Anchor Point").setValue([{_r(ax)}, {_r(ay)}, 0]);\n'
            f'{var}.property("Position").setValue({_v([x, y, 0])});\n')


def ellipse(var, name, cx, cy, w, h, stroke_hex, stroke_w, fill_hex=None):
    """EffectCraft shape layers draw their contents relative to the comp centre, so Position is an offset from (960, 540)."""
    js = f'var {var} = comp.layers.addShape(); {var}.name = "{name}";\n'
    js += f'var {var}G = {var}.property("Contents").addProperty("ADBE Vector Group").property("Contents");\n'
    js += f'{var}G.addProperty("ADBE Vector Shape - Ellipse").property("Size").setValue([{_r(w)}, {_r(h)}]);\n'
    if fill_hex:
        f = C.hex_to_rgb(fill_hex)
        js += f'{var}G.addProperty("ADBE Vector Graphic - Fill").property("Color").setValue([{f[0]}, {f[1]}, {f[2]}]);\n'
    sc = C.hex_to_rgb(stroke_hex)
    js += (f'var {var}S = {var}G.addProperty("ADBE Vector Graphic - Stroke"); {var}S.property("Color").setValue([{sc[0]}, {sc[1]}, {sc[2]}]);'
           f' {var}S.property("Stroke Width").setValue({stroke_w});\n')
    js += f'var {var}Tr = {var}G.addProperty("ADBE Vector Filter - Trim");\n'
    js += f'{var}.property("Position").setValue({_v([cx - 960, cy - 540])});\n'
    return js


def leader_and_plate(s, p, i, ax, ay, dirn, length, lines, t0, t_out, L, extra_gap=0.0):
    """Leader from (ax, ay) in dirn, then a charcoal plate with a gold bar holding `lines` = [(txt, font, size, color, tracking)].
    Returns (jsx, plate_box)."""
    gold, ein = col(s, "gold_accent"), C.ease(s, "type_in")
    meas = [tw(s, f, sz, txt, trk or 0) for txt, f, sz, _, trk in lines]
    cw = max(m[4] for m in meas)
    ch = sum(m[1] + m[3] for m in meas) + L["text_gap"] * (len(lines) - 1)
    pw = L["bar_width"] + L["pad_x"] * 2 + cw
    ph = ch + 2 * L["pad_y"]
    lw = L["leader_width"]
    sx0, sy0, sx1, sy1 = C.safe_rect(s)
    if dirn == "up":
        ex, ey = ax, ay - extra_gap - length
        px0, py0 = ex - pw / 2, ey - ph
    elif dirn == "down":
        ex, ey = ax, ay + extra_gap + length
        px0, py0 = ex - pw / 2, ey
    elif dirn == "left":
        ex, ey = ax - extra_gap - length, ay
        px0, py0 = ex - pw, ey - ph / 2
    else:
        ex, ey = ax + extra_gap + length, ay
        px0, py0 = ex, ey - ph / 2
    cx0 = min(max(px0, sx0), sx1 - pw)
    cy0 = min(max(py0, sy0), sy1 - ph)
    if (dirn in ("left", "right") and abs(cx0 - px0) > 1) or (dirn in ("up", "down") and abs(cy0 - py0) > 1):
        raise SystemExit(f"BUILD ERROR: {p}{i} label does not fit {dirn} of its target inside the safe area; "
                         "shorten the text, shorten Length or change Dir")
    px0, py0 = cx0, cy0
    C.assert_inside_safe(s, f"{p}{i} plate", px0, py0, px0 + pw, py0 + ph)
    js = ""
    t_lead = t0 + 4 * DT
    if dirn in ("up", "down"):
        y0 = ay - extra_gap if dirn == "up" else ay + extra_gap
        js += solid_anchor(f"{p}ld{i}", f"Leader{i}", gold, ax, y0, lw, length, "bottom" if dirn == "up" else "top")
        js += keys(f"{p}ld{i}", "Scale", [(0, [100, 0, 100])] + ramp(t_lead, L["leader_frames"], [100, 0, 100], [100, 100, 100], ein))
    else:
        x0 = ax - extra_gap if dirn == "left" else ax + extra_gap
        js += solid_anchor(f"{p}ld{i}", f"Leader{i}", gold, x0, ay, length, lw, "right" if dirn == "left" else "left")
        js += keys(f"{p}ld{i}", "Scale", [(0, [0, 100, 100])] + ramp(t_lead, L["leader_frames"], [0, 100, 100], [100, 100, 100], ein))
    js += envelope(f"{p}ld{i}", s, t0, t_out, animate_pos=False, in_frames=2)
    t_pl = t_lead + L["leader_frames"] * DT * 0.6
    nudge = {"up": (0, 14), "down": (0, -14), "left": (14, 0), "right": (-14, 0)}[dirn]
    js += solid(f"{p}pl{i}", f"Plate{i}", col(s, "charcoal"), px0 + pw / 2, py0 + ph / 2, pw, ph)
    js += envelope(f"{p}pl{i}", s, t_pl, t_out, pos=[px0 + pw / 2, py0 + ph / 2], slide=nudge, max_op=L["plate_alpha"] * 100)
    js += solid(f"{p}br{i}", f"Bar{i}", gold, px0 + L["bar_width"] / 2, py0 + ph / 2, L["bar_width"], ph)
    js += envelope(f"{p}br{i}", s, t_pl, t_out, pos=[px0 + L["bar_width"] / 2, py0 + ph / 2], slide=nudge)
    y = py0 + L["pad_y"]
    for k, ((txt, f, sz, c, trk), m) in enumerate(zip(lines, meas)):
        base = y + m[1]
        x = px0 + L["bar_width"] + L["pad_x"] - m[0]
        js += text(f"{p}t{i}_{k}", f"Text{i}_{k}", txt, f, sz, col(s, c), "LEFT_JUSTIFY", x, base, tracking=trk)
        js += envelope(f"{p}t{i}_{k}", s, t_pl + 0.06 * (k + 1), t_out, pos=[x, base], slide=nudge)
        y = base + m[3] + L["text_gap"]
    return js, [px0, py0, px0 + pw, py0 + ph]


# ----------------------------------------------------------------------------- person-pin
def build_person_pin(s, v):
    L, ty = s["layout"]["person_pin"], T(s)
    ppl = v["People"]
    if not 1 <= len(ppl) <= 3:
        raise SystemExit("BUILD ERROR: person-pin takes 1-3 people (use group-legend for more)")
    C.assert_min_font(s, ty["sizes"]["person_name"], ty["sizes"]["person_role"])
    a_in, a_out = s["animation"]["in_frames"], s["animation"]["out_frames"]
    t_last = 0.2 + L["stagger"] * (len(ppl) - 1)
    t_out = t_last + L["leader_frames"] * DT + a_in * DT + hold(v, L)
    total = t_out + a_out * DT
    js = comp_jsx("Person_Pin", total)
    boxes = []
    pop = C.ease(s, "type_pop")
    for i, p in enumerate(ppl):
        t0 = 0.2 + L["stagger"] * i
        ax, ay = float(p["X"]), float(p["Y"])
        d = L["dot_size"]
        js += ellipse(f"dt{i}", f"Ring{i}", ax, ay, d, d, col(s, "gold_accent"), 3, col(s, "charcoal"))
        js += keys(f"dt{i}", "Scale", [(0, [0, 0])] + ramp(t0, 8, [0, 0], [100, 100], pop))
        js += envelope(f"dt{i}", s, t0, t_out, animate_pos=False, in_frames=3)
        lines = [(p["Name"], ty["font_primary"], ty["sizes"]["person_name"], "ivory", None)]
        if p.get("Role"):
            lines.append((p["Role"].upper(), ty["font_label"], ty["sizes"]["person_role"], "gold", L["role_tracking"]))
        j, box = leader_and_plate(s, "pp", i, ax, ay, p.get("Dir", "up"), float(p.get("Length", 90)), lines, t0, t_out, L,
                                  extra_gap=d / 2 + 2)
        js += j
        boxes.append(box)
    return js + finish_jsx(), total, {"plates": boxes[0]}


# ----------------------------------------------------------------------------- photo-annotation
def build_photo_annotation(s, v):
    L, ty = s["layout"]["photo_annotation"], T(s)
    C.assert_min_font(s, ty["sizes"]["annotation_label"])
    cx, cy, w, h = float(v["X"]), float(v["Y"]), float(v["W"]), float(v["H"])
    a_in, a_out = s["animation"]["in_frames"], s["animation"]["out_frames"]
    t0 = 0.25
    t_out = t0 + L["draw_frames"] * DT + 0.4 + a_in * DT + hold(v, L)
    total = t_out + a_out * DT
    js = comp_jsx("Photo_Annotation", total)
    js += ellipse("ring", "Ring", cx, cy, w, h, col(s, "gold_accent"), L["stroke"])
    js += f'var _tp = ringTr.property("End"); _tp.setValueAtTime(0, 0);\n'
    for t, val in ramp(t0, L["draw_frames"], 0.0, 100.0, C.ease(s, "type_in")):
        js += f"_tp.setValueAtTime({_t(t)}, {_r(val)});\n"
    js += shadow("ring", 10, 60, 0)
    js += envelope("ring", s, t0, t_out, animate_pos=False, in_frames=1)
    dirn = v.get("Dir", "right")
    edge = {"right": (cx + w / 2, cy), "left": (cx - w / 2, cy), "up": (cx, cy - h / 2), "down": (cx, cy + h / 2)}[dirn]
    lines = [(v["Label"].upper(), ty["font_label"], ty["sizes"]["annotation_label"], "ivory", L["tracking"])]
    if v.get("Sub"):
        lines.append((v["Sub"], ty["font_secondary"], ty["sizes"]["person_role"], "gold", None))
    LL = dict(L, bar_width=5, pad_x=L["label_pad_x"], pad_y=L["label_pad_y"], text_gap=8, leader_frames=10)
    j, box = leader_and_plate(s, "an", 0, edge[0], edge[1], dirn, float(v.get("Length", 120)), lines,
                              t0 + L["draw_frames"] * DT * 0.7, t_out, LL, extra_gap=L["label_gap"] * 0.2)
    js += j
    return js + finish_jsx(), total, {"plate": box}


# ----------------------------------------------------------------------------- people-panel
def build_people_panel(s, v):
    L, ty = s["layout"]["people_panel"], T(s)
    pans = v["Panels"]
    n = len(pans)
    if not 1 <= n <= 3:
        raise SystemExit("BUILD ERROR: people-panel takes 1-3 portraits")
    fn, fr, ft = ty["font_primary"], ty["font_label"], ty["font_label"]
    sn, sr, st_ = ty["sizes"]["panel_name"], ty["sizes"]["panel_role"], ty["sizes"]["panel_title"]
    C.assert_min_font(s, sn, sr, st_)
    sx0, sy0, sx1, sy1 = C.safe_rect(s)
    g = L["gutter"]
    pw = (sx1 - sx0 - g * (n - 1)) / n if n > 1 else 760
    ph = L["panel_h"]
    total_w = pw * n + g * (n - 1)
    left = (sx0 + sx1) / 2 - total_w / 2
    top = L["panel_top"]
    a_in, a_out = s["animation"]["in_frames"], s["animation"]["out_frames"]
    t_last = 0.15 + L["stagger"] * (n - 1)
    t_out = t_last + a_in * DT + 0.3 + hold(v, L)
    total = t_out + a_out * DT
    cnv = s["canvas"]
    js = comp_jsx("People_Panel", total)
    js += solid("bg", "Background", col(s, "charcoal"), cnv["width"] / 2, cnv["height"] / 2, cnv["width"], cnv["height"])
    js += envelope("bg", s, 0, t_out, animate_pos=False, max_op=L["bg_alpha"] * 100, in_frames=6)
    if v.get("Title"):
        title = v["Title"].upper()
        _, at, _, bt, wt = tw(s, ft, st_, title, L["title_tracking"])
        tb = top - L["title_gap"]
        C.assert_inside_safe(s, "panel title", 960 - wt / 2, tb - at, 960 + wt / 2, tb + bt)
        js += text("ti", "Title", title, ft, st_, col(s, "slate"), "CENTER_JUSTIFY", 960, tb, tracking=L["title_tracking"])
        js += envelope("ti", s, 0.05, t_out, pos=[960, tb], slide=(0, 16))
    for i, p in enumerate(pans):
        t0 = 0.15 + L["stagger"] * i
        x0 = left + i * (pw + g)
        pcx, pcy = x0 + pw / 2, top + ph / 2
        img = p["Image"]
        with Image.open(img) as im:
            iw, ih = im.size
        sc = max(pw / iw, ph / ih) * float(p.get("Zoom", 1.0))
        fx, fy = float(p.get("FX", iw / 2)), float(p.get("FY", ih / 2))
        # keep the focus point centred but never expose the image edge
        half_w, half_h = pw / 2 / sc, ph / 2 / sc
        fx = min(max(fx, half_w), iw - half_w)
        fy = min(max(fy, half_h), ih - half_h)
        lx, ly = pcx + (iw / 2 - fx) * sc, pcy + (ih / 2 - fy) * sc
        ml, mt = fx - half_w, fy - half_h
        mr, mb = fx + half_w, fy + half_h
        js += (f'var im{i} = comp.layers.add(app.project.importFile(new ImportOptions(new File("{img.replace(chr(92), "/")}"))));\n'
               f'im{i}.property("Scale").setValue([{_r(sc * 100)}, {_r(sc * 100)}, 100]);\n'
               f'var mk{i} = im{i}.property("Masks").addProperty("Mask"); var sh{i} = new Shape();'
               f' sh{i}.vertices = [[{_r(ml)}, {_r(mt)}], [{_r(mr)}, {_r(mt)}], [{_r(mr)}, {_r(mb)}], [{_r(ml)}, {_r(mb)}]];'
               f' sh{i}.closed = true; mk{i}.property("Mask Path").setValue(sh{i});\n')
        js += envelope(f"im{i}", s, t0, t_out, pos=[lx, ly], slide=(0, 40))
        js += solid(f"fr{i}", f"Rule{i}", col(s, "gold_accent"), pcx, top + ph + 1, pw, L["frame_px"] + 1)
        js += envelope(f"fr{i}", s, t0, t_out, pos=[pcx, top + ph + 1], slide=(0, 40))
        _, an, _, bn, wn = tw(s, fn, sn, p["Name"])
        nb = top + ph + L["name_gap"] + an * 0.25
        if wn > pw:
            raise SystemExit(f"BUILD ERROR: name '{p['Name']}' ({wn:.0f}px) wider than panel {pw:.0f}px")
        js += text(f"nm{i}", f"Name{i}", p["Name"], fn, sn, col(s, "ivory"), "CENTER_JUSTIFY", pcx, nb)
        js += envelope(f"nm{i}", s, t0 + 0.12, t_out, pos=[pcx, nb], slide=(0, 20))
        if p.get("Role"):
            rl = balanced_wrap(s, fr, sr, p["Role"].upper(), pw - 20, 2)
            _, ar, _, br, _ = tw(s, fr, sr, rl[0], L["role_tracking"])
            rb = nb + bn + L["role_gap"] + ar
            last = rb + (len(rl) - 1) * sr * 1.15 + br
            C.assert_inside_safe(s, f"panel {i} role", x0, top, x0 + pw, last)
            js += text(f"ro{i}", f"Role{i}", "\r".join(rl), fr, sr, col(s, "gold"), "CENTER_JUSTIFY", pcx, rb,
                       tracking=L["role_tracking"], leading=round(sr * 1.15))
            js += envelope(f"ro{i}", s, t0 + 0.2, t_out, pos=[pcx, rb], slide=(0, 20))
    return js + finish_jsx(), total, {"panels": [left, top, left + total_w, top + ph]}


# ----------------------------------------------------------------------------- group-legend
def build_group_legend(s, v):
    L, ty = s["layout"]["group_legend"], T(s)
    fl, fn, fc = ty["font_label"], ty["font_primary"], ty["font_secondary"]
    sl, sn, sc = ty["sizes"]["legend_label"], ty["sizes"]["legend_names"], ty["sizes"]["person_role"]
    C.assert_min_font(s, sl, sn, sc)
    label = v.get("Label", "In this photo").upper()
    names = v["Names"]
    cap = v.get("Caption", "")
    sx0, sy0, sx1, sy1 = C.safe_rect(s)
    inner = sx1 - sx0 - 2 * L["pad_x"]
    f = C.font_for(s, fn, sn)
    sep = "   ·   "
    rows, cur, curw = [], [], 0.0
    for nm in names:
        w = f.getlength(nm) + (f.getlength(sep) if cur else 0)
        if cur and curw + w > inner:
            rows.append(cur)
            cur, curw = [], 0.0
            w = f.getlength(nm)
        cur.append(nm)
        curw += w
    rows.append(cur)
    if len(rows) > 2:
        raise SystemExit("BUILD ERROR: group-legend fits 2 rows of names; shorten or split")
    _, al, _, bl, wl = tw(s, fl, sl, label, L["label_tracking"])
    _, an, _, bn, _ = tw(s, fn, sn, "Hgy")
    _, ac, _, bc, _ = tw(s, fc, sc, cap or "Hgy")
    row_h = an + bn
    ph = L["pad_y"] * 2 + al + bl + L["line_gap"] + row_h * len(rows) + L["line_gap"] * (len(rows) - 1) + ((L["caption_gap"] + ac + bc) if cap else 0)
    py0 = sy1 - ph
    C.assert_inside_safe(s, "group legend", sx0, py0, sx1, sy1)
    a_in, a_out = s["animation"]["in_frames"], s["animation"]["out_frames"]
    t_out = a_in * DT + L["name_stagger"] * len(names) + hold(v, L)
    total = t_out + a_out * DT
    js = comp_jsx("Group_Legend", total)
    js += solid("pl", "Plate", col(s, "charcoal"), (sx0 + sx1) / 2, py0 + ph / 2, sx1 - sx0, ph)
    js += envelope("pl", s, 0, t_out, pos=[(sx0 + sx1) / 2, py0 + ph / 2], slide=(0, 30), max_op=L["plate_alpha"] * 100)
    js += solid("tr", "TopRule", col(s, "gold_accent"), (sx0 + sx1) / 2, py0 + 1, sx1 - sx0, 2)
    js += envelope("tr", s, 0, t_out, pos=[(sx0 + sx1) / 2, py0 + 1], slide=(0, 30), max_op=80)
    x = sx0 + L["pad_x"]
    lb = py0 + L["pad_y"] + al
    js += text("lb", "Label", label, fl, sl, col(s, "gold_accent"), "LEFT_JUSTIFY", x, lb, tracking=L["label_tracking"])
    js += envelope("lb", s, 0.05, t_out, pos=[x, lb], slide=(0, 20))
    y = lb + bl + L["line_gap"] + an
    k = 0
    for r, row in enumerate(rows):
        xx = x
        for j, nm in enumerate(row):
            if j:
                js += text(f"sp{k}", f"Sep{k}", "·", fn, sn, col(s, "gold_accent"), "CENTER_JUSTIFY", xx + f.getlength(sep) / 2, y)
                js += envelope(f"sp{k}", s, a_in * DT + L["name_stagger"] * k, t_out, pos=[xx + f.getlength(sep) / 2, y], slide=(0, 16))
                xx += f.getlength(sep)
            js += text(f"nm{k}", f"Name{k}", nm, fn, sn, col(s, "ivory"), "LEFT_JUSTIFY", xx, y)
            js += envelope(f"nm{k}", s, a_in * DT + L["name_stagger"] * k, t_out, pos=[xx, y], slide=(0, 16))
            xx += f.getlength(nm)
            k += 1
        y += row_h + L["line_gap"]
    if cap:
        if C.font_for(s, fc, sc).getlength(cap) > inner:
            raise SystemExit(f"BUILD ERROR: group-legend caption is wider than {inner:.0f}px; shorten it")
        cb = py0 + ph - L["pad_y"] - bc
        js += text("cp", "Caption", cap, fc, sc, col(s, "slate"), "LEFT_JUSTIFY", x, cb)
        js += envelope("cp", s, a_in * DT + L["name_stagger"] * k, t_out, pos=[x, cb], slide=(0, 16))
    return js + finish_jsx(), total, {"plate": [sx0, py0, sx1, sy1]}


# ----------------------------------------------------------------------------- article-highlight
def build_article_highlight(s, v):
    L, ty = s["layout"]["article_highlight"], T(s)
    fm, fmeta, fb, ff = ty["font_primary"], ty["font_label"], ty["font_body"], ty["font_secondary"]
    sm, smeta, sb = ty["sizes"]["article_masthead"], ty["sizes"]["article_meta"], ty["sizes"]["article_body"]
    C.assert_min_font(s, sm, smeta, sb)
    body = " ".join(v["Body"].split())
    hl = " ".join(v["Highlight"].split())
    hs = body.find(hl)
    if hs < 0:
        raise SystemExit("BUILD ERROR: Highlight must be an exact substring of Body (verbatim quote rule)")
    he = hs + len(hl)
    cw = L["card_w"]
    tw_ = cw - 2 * L["pad_x"]
    lines = C.wrap(s, fb, sb, body, tw_, L["max_body_lines"])
    fbody = C.font_for(s, fb, sb)
    lead = sb * L["body_leading_ratio"]
    _, am, _, bm, wm = tw(s, fm, sm, v["Outlet"])
    meta = v.get("Meta", "").upper()
    _, amt, _, bmt, wmt = tw(s, fmeta, smeta, meta or "H", L["meta_tracking"])
    _, ab, _, bb, _ = tw(s, fb, sb, "Hgy")
    foot = v.get("Footer", "")
    _, af, _, bf, wf = tw(s, ff, smeta, foot or "H")
    ch = (L["pad_y"] + am + bm + (12 + amt + bmt if meta else 0) + L["rule_gap"] + 2 + L["rule_gap"] + ab + lead * (len(lines) - 1) + bb
          + ((L["footer_gap"] + af + bf) if foot else 0) + L["pad_y"])
    cx, cy = 960.0, float(L["center_y"])
    x0, y0 = cx - cw / 2, cy - ch / 2
    C.assert_inside_safe(s, "article card", x0, y0, x0 + cw, y0 + ch)
    tx = x0 + L["pad_x"]
    mb = y0 + L["pad_y"] + am
    metab = mb + bm + 12 + amt
    rule_y = (metab + bmt if meta else mb + bm) + L["rule_gap"]
    first = rule_y + 2 + L["rule_gap"] + ab
    a_in, a_out = s["animation"]["in_frames"], s["animation"]["out_frames"]
    t_hl = a_in * DT + L["highlight_delay"]
    # highlight segments per line
    segs, off = [], 0
    for li, ln in enumerate(lines):
        a, b = off, off + len(ln)
        lo, hi = max(a, hs), min(b, he)
        if lo < hi:
            xs = tx + fbody.getlength(ln[:lo - a])
            xe = tx + fbody.getlength(ln[:hi - a])
            segs.append((li, xs, xe))
        off = b + 1
    t = t_hl
    timed = []
    for li, xs, xe in segs:
        dur = max(4 * DT, (xe - xs) / L["sweep_px_per_s"])
        timed.append((li, xs, xe, t, dur))
        t += dur
    t_out = t + hold(v, L)
    total = t_out + a_out * DT
    ein = C.ease(s, "type_in")
    names = []
    js = comp_jsx("Article_Highlight", total)
    cnv = s["canvas"]
    js += solid("sc", "Scrim", col(s, "charcoal"), cnv["width"] / 2, cnv["height"] / 2, cnv["width"], cnv["height"])
    js += envelope("sc", s, 0, t_out, animate_pos=False, max_op=L["dim_alpha"] * 100)
    js += solid("cd", "Paper", L["paper"], cx, cy, cw, ch)
    js += shadow("cd", 40, 70, 12)
    names.append("cd")
    js += text("mh", "Masthead", v["Outlet"], fm, sm, L["ink"], "LEFT_JUSTIFY", tx, mb)
    names.append("mh")
    if meta:
        js += text("mt", "Meta", meta, fmeta, smeta, "#6B6F76", "LEFT_JUSTIFY", tx, metab, tracking=L["meta_tracking"])
        names.append("mt")
    js += solid("ru", "Rule", L["ink"], cx, rule_y + 1, cw - 2 * L["pad_x"], 2)
    js += 'ru.property("Opacity").setValue(35);\n'
    names.append("ru")
    for k, (li, xs, xe, ts, dur) in enumerate(timed):
        base = first + li * lead
        hy0, hy1 = base - ab - L["highlight_pad_y"], base + bb + L["highlight_pad_y"]
        js += solid_anchor(f"hl{k}", f"Highlight{k}", L["highlight"], xs - 6, (hy0 + hy1) / 2, xe - xs + 12, hy1 - hy0, "left")
        js += f'hl{k}.property("Opacity").setValue({_r(L["highlight_alpha"] * 100)});\n'
        js += keys(f"hl{k}", "Scale", [(0, [0, 100, 100]), (ts, [0, 100, 100])] + ramp(ts, max(1, int(round(dur / DT))), [0, 100, 100], [100, 100, 100], lambda p: p))
        names.append(f"hl{k}")
    js += text("bd", "Body", "\r".join(lines), fb, sb, L["ink"], "LEFT_JUSTIFY", tx, first, leading=round(lead))
    names.append("bd")
    if foot:
        fb_y = y0 + ch - L["pad_y"] - bf
        js += text("ft", "Footer", foot, ff, smeta, "#6B6F76", "LEFT_JUSTIFY", tx, fb_y)
        names.append("ft")
    for nm in names:
        mo = 35.0 if nm == "ru" else (L["highlight_alpha"] * 100 if nm.startswith("hl") else 100.0)
        js += envelope(nm, s, 0, t_out, animate_pos=False, max_op=mo)
    # card rig: parent everything to a null, then move / tilt / push the null
    js += f'var rig = comp.layers.addNull(); rig.name = "CardRig"; rig.property("Position").setValue([{_r(cx)}, {_r(cy)}]);\n'
    for nm in names:
        js += f"{nm}.parent = rig;\n"
    tilt = L["tilt_deg"]
    js += keys("rig", "Position", ramp(0, a_in, [cx, cy + 60], [cx, cy], ein))
    js += keys("rig", "Rotation", ramp(0, a_in, tilt * 2.5, tilt, ein))
    js += keys("rig", "Scale", ramp(0, a_in, [94, 94], [100, 100], ein) + [(t_out, [100 + L["push_pct"], 100 + L["push_pct"]])])
    return js + finish_jsx(), total, {"card": [x0, y0, x0 + cw, y0 + ch]}


BUILDERS.update({
    "person-pin": build_person_pin,
    "photo-annotation": build_photo_annotation,
    "people-panel": build_people_panel,
    "group-legend": build_group_legend,
    "article-highlight": build_article_highlight,
})
