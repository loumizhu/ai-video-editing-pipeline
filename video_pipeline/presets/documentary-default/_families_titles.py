# ----------------------------------------------------------------------------- title expansion (v3.4): four families
# New families for varied video types, all recreation-grounded (Mixkit free templates) and all built with the
# shared helpers in _families_v2. Motion is position/opacity/scale keys only — EffectCraft's Linear Wipe is
# unreliable (see build_line_third docstring). Geometry is measured from the real fonts via tw(); nothing hardcoded.
# Registered into BUILDERS by the hook at the bottom of _families_v2.py.
TITLE_BUILDERS = {}

import _common as C
from _families_v2 import (DT, T, _v, col, comp_jsx, envelope, finish_jsx, hold, keys, ramp, shadow, solid,
                          text, tw)


def _accent_or_exit(s, v):
    a = (v.get("AccentColor") or "").strip()
    if not a:
        return col(s, "gold_accent")
    if a.startswith("#"):
        return a
    try:
        return col(s, a)
    except KeyError:
        raise SystemExit(f"BUILD ERROR: AccentColor '{a}' is neither a palette key nor a #hex color")


def _stroke(var, name, hexcol, x, y, w, h, ax, ay):
    """Solid with an explicit anchor (scaling grows from that edge); (x, y) = anchor position."""
    rgb = C.hex_to_rgb(hexcol)
    return (f'var {var} = comp.layers.addSolid([{rgb[0]}, {rgb[1]}, {rgb[2]}], "{name}", '
            f'{max(1, int(round(w)))}, {max(1, int(round(h)))}, 1.0);\n'
            f'{var}.property("Anchor Point").setValue({_v([ax, ay, 0])});\n'
            f'{var}.property("Position").setValue({_v([x, y, 0])});\n')


# ----------------------------------------------------------------------------- 11. bold-third (Mixkit 312)
BOLD_DEFAULTS = {
    "hold_seconds": 3.4,
    "lead_in": 0.25,
    "heading_font": "Montserrat-ExtraBold",
    "heading_size": 104,           # 112 pushed 'CHARLOTTE BEAUMONT' past the 1400px limit; 104 keeps 2-word names
    "heading_tracking": 10,
    "accent_color": None,          # None -> typography.colors.gold_accent; "AccentColor" value overrides
    "max_heading_w": 1400,
    "gap_heading_line": 26,
    "line_color": "#FFFFFF",
    "line_h": 6,
    "line_overhang_px": 20,        # clearance line runs a hair past the last glyph, like line-third's rule
    "stamp_frames": 9,             # scale slam: 128% -> 100% with easeOutBack, so it visibly compresses on landing
    "stamp_op_frames": 5,          # opacity lands before the scale settles; the slam reads as one hit
    "stamp_scale_from": 128.0,
    "stamp_drop_px": 18.0,
    "line_delay_frames": 0,        # line starts with the stamp and finishes just after it, under the heading
    "line_sweep_frames": 11,
    "exit_frames": 6,              # fast name exit; the retracting line is the slower tail
    "exit_scale_to": 96.0,
    "line_retract_frames": 10,
    "shadow_softness": 18,
    "shadow_opacity": 55,
    "shadow_distance": 3,
}


def build_bold_third(s, v):
    """Bold stamped heading + thin white clearance line that sweeps out under it as it lands; fast exit,
    slower line retract. Quick name/tag stamps for talking-head footage. All in layout.bold_third."""
    L = {**BOLD_DEFAULTS, **s["layout"].get("bold_third", {})}
    f, z, tr = L["heading_font"], L["heading_size"], L["heading_tracking"]
    C.assert_min_font(s, z)
    head = " ".join(str(v.get("Heading", "")).split()).upper()
    if not head:
        raise SystemExit("BUILD ERROR: 'Heading' must be non-empty (got blank/whitespace)")
    l1, a1, r1, b1, w1 = tw(s, f, z, head, tr)
    if w1 > L["max_heading_w"]:
        raise SystemExit(f"BUILD ERROR: heading '{head}' is {w1:.0f}px wide, limit {L['max_heading_w']}px")
    acc = v.get("AccentColor") or L["accent_color"] or col(s, "gold_accent")

    sx0, _, _, sy1 = C.safe_rect(s)
    x_l = sx0
    line_w = w1 + L["line_overhang_px"]
    line_cy = sy1 - L["line_h"] / 2.0
    head_base = line_cy - L["line_h"] / 2.0 - L["gap_heading_line"] - b1
    head_top = head_base - a1
    C.assert_inside_safe(s, "bold third", x_l, head_top, x_l + max(w1, line_w), sy1)

    e0 = float(L["lead_in"])
    fi, fo = int(L["stamp_frames"]), int(L["exit_frames"])
    t_land = e0 + fi * DT
    t_line0 = e0 + int(L["line_delay_frames"]) * DT
    t_line1 = t_line0 + int(L["line_sweep_frames"]) * DT
    t_out = max(t_land, t_line1) + hold(v, L)  # hold starts only once heading and line are both settled
    total = t_out + max(fo, int(L["line_retract_frames"])) * DT
    ein, epop, eout = C.ease(s, "type_in"), C.ease(s, "type_pop"), C.ease(s, "type_out")

    # stamp pivot = heading ink centre; EC drops text-opacity keys when a text layer is parented to a null
    # (measured), so the slam scales the layer itself via an ink-centre anchor instead of a parent rig.
    ax, ay = (l1 + r1) / 2.0, (b1 - a1) / 2.0          # anchor in baseline-left layer space
    cx = x_l + (r1 - l1) / 2.0
    cy = head_base + ay                                # == head_base - (a1 - b1) / 2.0
    js = comp_jsx("Bold_Third", total)
    js += solid("ln", "ClearanceLine", L["line_color"], x_l, line_cy, line_w, L["line_h"], anchor_left=True)
    # scale embed: sweep draw on type_in, retract exit on sparse endpoint keys (EC re-interpolates dense
    # eased scale-out and stuck it mid-shrink at the cut, measured)
    js += keys("ln", "Scale", [(0.0, [0, 100, 100])]
               + ramp(t_line0, int(L["line_sweep_frames"]), [0, 100, 100], [100, 100, 100], ein)
               + [(round(t_out, 4), [100.0, 100.0, 100.0]),
                  (round(t_out + (int(L["line_retract_frames"]) - 1) * DT, 4), [0.0, 100.0, 100.0]),
                  (round(total, 4), [0.0, 100.0, 100.0])])
    js += text("hd", "Heading", head, f, z, acc, "LEFT_JUSTIFY", x_l - l1, head_base, tracking=tr)
    js += f'hd.property("Anchor Point").setValue([{round(ax, 3)}, {round(ay, 3)}, 0]);\n'
    # Drop Shadow removed: EC ignores text-layer opacity keyframes when the effect is present (measured)
    # opacity exit MUST be sparse endpoints: EC re-interpolates dense eased
    # opacity ramps and the fade never completes (measured, probe8)
    js += keys("hd", "Opacity", [(0.0, 0.0), (e0, 0.0)]
               + [(round(e0 + int(L["stamp_op_frames"]) * DT, 4), 100.0), (round(t_out, 4), 100.0),
                  (round(t_out + fo * DT, 4), 0.0)])
    sf, st = float(L["stamp_scale_from"]), float(L["exit_scale_to"])
    js += keys("hd", "Position", [(0.0, [round(x_l - l1, 3), round(head_base, 3), 0])]
               + ramp(e0, fi, [round(cx, 3), round(cy - L["stamp_drop_px"], 3), 0], [round(cx, 3), round(cy, 3), 0], ein))
    js += keys("hd", "Scale", [(0.0, [100.0, 100.0, 100.0])]
               + ramp(e0, fi, [sf, sf, 100], [100, 100, 100], epop)
               + ramp(t_out, fo, [100, 100, 100], [st, st, 100], eout))
    return js + finish_jsx(), total, {"block": [x_l, head_top, x_l + max(w1, line_w), sy1]}


# ----------------------------------------------------------------------------- 12. banner-third (Mixkit 305)
BANNER_DEFAULTS = {
    "hold_seconds": 3.2,
    "lead_in": 0.25,
    "heading_font": "Montserrat-ExtraBold",
    "heading_size": 92,
    "heading_tracking": 20,
    "heading_color": "ivory",
    "sub_font": "Montserrat-Regular",
    "sub_size": 46,
    "sub_tracking": 140,
    "sub_color": "gold_accent",
    "max_heading_w": 1480,
    "max_sub_w": 1480,
    "pad_x": 52,
    "pad_y": 44,
    "gap_heading_sub": 18,
    "plate_alpha": 0.92,
    "border_px": 5,
    "border_opacity": 1.0,
    "border_draw_frames": 16,
    "border_side_delay_frames": 4,
    "border_delay": 0.0,
    "slide_in_pad": 48,
    "slide_out_px": 560,
}


def build_banner_third(s, v):
    """Dark bordered plate slides in from the left and decelerates, heading + wide-tracked subhead ride it,
    border strokes draw on after the plate stops, hold, then the block slides out right. Heavyweight interview
    contexts. Plate is measured from the real fonts; nothing about it is hardcoded. All in layout.banner_third."""
    L = {**BANNER_DEFAULTS, **s["layout"].get("banner_third", {})}
    ty = T(s)
    f1, z1, tr1 = L["heading_font"], int(L["heading_size"]), L["heading_tracking"]
    f2, z2, tr2 = L["sub_font"], int(L["sub_size"]), L["sub_tracking"]
    C.assert_min_font(s, z1, z2)
    head = " ".join(str(v.get("Heading", "")).split()).upper()
    sub = " ".join(str(v.get("Sub", "")).split()).upper()
    if not head or not sub:
        raise SystemExit("BUILD ERROR: 'Heading' and 'Sub' must both be non-empty (got blank/whitespace)")
    if head == sub:
        raise SystemExit("BUILD ERROR: 'Heading' and 'Sub' are identical after uppercasing")
    l1, a1, _, b1, w1 = tw(s, f1, z1, head, tr1)
    l2, a2, _, b2, w2 = tw(s, f2, z2, sub, tr2)
    if w1 > L["max_heading_w"]:
        raise SystemExit(f"BUILD ERROR: heading '{head}' is {w1:.0f}px wide, limit {L['max_heading_w']}px")
    if w2 > L["max_sub_w"]:
        raise SystemExit(f"BUILD ERROR: sub '{sub}' is {w2:.0f}px wide, limit {L['max_sub_w']}px")

    sx0, _, sx1, sy1 = C.safe_rect(s)
    bw = int(L["border_px"])
    # plate from measurement only: widest line + side padding, both ink heights + vertical padding
    pw = max(w1, w2) + 2 * L["pad_x"]
    ph = 2 * L["pad_y"] + a1 + b1 + L["gap_heading_sub"] + a2 + b2
    if pw > sx1 - sx0:
        raise SystemExit(f"BUILD ERROR: banner plate is {pw:.0f}px wide, safe width is {sx1 - sx0}px")
    px0, py1 = sx0, sy1
    py0, px1 = py1 - ph, px0 + pw
    C.assert_inside_safe(s, "banner third", px0, py0, px1, py1)

    head_base = py0 + L["pad_y"] + a1
    sub_base = head_base + b1 + L["gap_heading_sub"] + a2
    head_x = px0 + L["pad_x"] - l1
    sub_x = px0 + L["pad_x"] - l2

    a_in, a_out = s["animation"]["in_frames"], s["animation"]["out_frames"]
    t_in = float(L["lead_in"])
    t_stop = t_in + a_in * DT                      # plate has decelerated to rest here
    df = int(L["border_draw_frames"])
    sd = min(int(L["border_side_delay_frames"]), df - 1)
    t_draw0 = t_stop + float(L["border_delay"])    # border starts drawing only after the plate stops
    t_ready = t_draw0 + df * DT
    t_out = t_ready + hold(v, L)
    total = t_out + a_out * DT
    ein, eout = C.ease(s, "type_in"), C.ease(s, "type_out")

    plate_hex = v.get("PlateColor", col(s, "charcoal"))
    accent_hex = v.get("AccentColor", col(s, "gold_accent"))
    din = pw + L["slide_in_pad"]                   # starts fully clear of its resting left edge
    dout = float(L["slide_out_px"])
    slide = (-din, 0)
    out_slide = (dout, 0)
    cx, cy = px0 + pw / 2.0, py0 + ph / 2.0

    js = comp_jsx("Banner_Third", total)
    js += solid("pl", "Plate", plate_hex, cx, cy, pw, ph)
    js += envelope("pl", s, t_in, t_out, pos=[cx, cy], slide=slide, out_slide=out_slide,
                   max_op=L["plate_alpha"] * 100)
    js += text("hd", "Heading", head, f1, z1, col(s, L["heading_color"]), "LEFT_JUSTIFY", head_x, head_base,
               tracking=tr1)
    js += envelope("hd", s, t_in, t_out, pos=[head_x, head_base], slide=slide, out_slide=out_slide)
    js += text("sb", "Sub", sub, f2, z2, accent_hex, "LEFT_JUSTIFY", sub_x, sub_base, tracking=tr2)
    js += envelope("sb", s, t_in, t_out, pos=[sub_x, sub_base], slide=slide, out_slide=out_slide)

    bop = L["border_opacity"] * 100.0
    strokes = (
        ("bt", "BorderTop", px0, py0 + bw / 2.0, pw, bw, 0, bw / 2.0, 0, df),
        ("bb", "BorderBottom", px0, py1 - bw / 2.0, pw, bw, 0, bw / 2.0, 0, df),
        ("bl", "BorderLeft", px0 + bw / 2.0, py0 + bw, bw, ph - 2 * bw, bw / 2.0, 0, sd, df - sd),
        ("br", "BorderRight", px1 - bw / 2.0, py0 + bw, bw, ph - 2 * bw, bw / 2.0, 0, sd, df - sd),
    )
    for var, name, x, y, w, h, ax, ay, delay, frames in strokes:
        rest = [x, y, 0]
        js += _stroke(var, name, accent_hex, x, y, w, h, ax, ay)
        s0 = t_draw0 + delay * DT
        grow = [0, 100, 100] if name in ("BorderTop", "BorderBottom") else [100, 0, 100]
        js += keys(var, "Scale", [(0.0, grow)] + ramp(s0, max(1, frames), grow, [100, 100, 100], ein))
        js += keys(var, "Opacity", [(0.0, 0.0), (s0, 0.0), (s0 + 2 * DT, bop), (t_out, bop),
                                    (round(t_out + a_out * DT, 4), 0.0)])
        js += keys(var, "Position", [(0.0, rest), (t_out, rest)]
                   + ramp(t_out, a_out, rest, [x + dout, y, 0], eout))
    return js + finish_jsx(), total, {"block": [px0, py0, px1, py1]}


# ----------------------------------------------------------------------------- 13. center-title (Mixkit 196)
CENTER_DEFAULTS = {
    "lead_in": 0.20,
    "hold_seconds": 3.0,
    "center_y": 540,

    "kicker_font": "Montserrat-Bold",
    "kicker_size": 46,
    "kicker_tracking": 260,
    "kicker_color": "ivory",
    "kicker_frames": 14,
    "kicker_rise": 20,

    "underline_gap": 18,
    "underline_h": 3,
    "underline_color": "#FFFFFF",
    "underline_frames": 10,

    "gap_underline_title": 34,
    "title_font": "Montserrat-ExtraBold",
    "title_size": 112,
    "title_color": "ivory",
    "title_frames": 20,
    "title_rise": 44,
    "max_title_w": 1300,

    "gap_title_sub": 40,
    "sub_font": "Montserrat-Regular",
    "sub_size": 48,
    "sub_tracking": 80,
    "accent_key": "gold",
    "sub_frames": 14,
    "sub_rise": 22,

    "stagger_title": 0.55,
    "stagger_sub": 0.45,
    "exit_stagger": 0.10,
    "exit_frames": 10,
    "exit_rise": 18,

    "shadow_softness": 26,
    "shadow_opacity": 50,
    "shadow_distance": 2,
}


def build_center_title(s, v):
    """Centred chapter/act card: wide-tracked kicker with a drawing underline, big bold title with a soft
    overshoot, light accent subheading. Staggered entry (kicker -> title -> sub), reverse-order exit. Every x
    offset comes from tw() ink metrics so each line is optically centred. All in layout.center_title."""
    L = {**CENTER_DEFAULTS, **s["layout"].get("center_title", {})}

    kicker = " ".join(str(v.get("Kicker", "")).split()).upper()
    title = " ".join(str(v.get("Title", "")).split())
    sub = " ".join(str(v.get("Sub", "")).split()).upper()
    for label, val in (("Kicker", kicker), ("Title", title), ("Sub", sub)):
        if not val:
            raise SystemExit(f"BUILD ERROR: center-title '{label}' is blank")

    fk, tk = L["kicker_font"], L["kicker_tracking"]
    ft = L["title_font"]
    fs, ts = L["sub_font"], L["sub_tracking"]
    zk, zt, zs = int(L["kicker_size"]), int(L["title_size"]), int(L["sub_size"])
    C.assert_min_font(s, zk, zt, zs)

    kl, ka, kr, kb, kw = tw(s, fk, zk, kicker, tk)
    tl, ta, tr, tb, twn = tw(s, ft, zt, title)
    sl, sa, sr, sb, swn = tw(s, fs, zs, sub, ts)
    if twn > L["max_title_w"]:
        raise SystemExit(f"BUILD ERROR: title '{title}' is {twn:.0f}px wide, limit {L['max_title_w']}px")

    cx = s["canvas"]["width"] / 2.0
    cy = float(L["center_y"])
    block_w = max(kw, twn, swn)
    block_h = (ka + kb + L["underline_gap"] + L["underline_h"] + L["gap_underline_title"]
               + ta + tb + L["gap_title_sub"] + sa + sb)
    top = cy - block_h / 2.0
    bottom = top + block_h
    C.assert_inside_safe(s, "center title", cx - block_w / 2.0, top, cx + block_w / 2.0, bottom)

    k_base = top + ka
    ul_y = k_base + kb + L["underline_gap"] + L["underline_h"] / 2.0
    t_base = ul_y + L["underline_h"] / 2.0 + L["gap_underline_title"] + ta
    s_base = t_base + tb + L["gap_title_sub"] + sa

    # layer x puts the ink box (not the advance box) on the centre line
    kx = cx - kw / 2.0 - kl
    tx = cx - twn / 2.0 - tl
    sx = cx - swn / 2.0 - sl

    accent = _accent_or_exit(s, v) if v.get("AccentColor") else col(s, L["accent_key"])

    # stagger: kicker -> title -> sub; the rule waits for the kicker to land
    t_k = float(L["lead_in"])
    t_t = t_k + float(L["stagger_title"])
    t_s = t_t + float(L["stagger_sub"])
    t_u = t_k + int(L["kicker_frames"]) * DT

    t_hold = max(t_s + int(L["sub_frames"]) * DT,
                 t_t + int(L["title_frames"]) * DT,
                 t_u + int(L["underline_frames"]) * DT) + hold(v, L)
    t_out_s = t_hold                                  # exit in reverse: sub first
    t_out_t = t_hold + float(L["exit_stagger"])
    t_out_k = t_hold + 2 * float(L["exit_stagger"])
    total = t_out_k + int(L["exit_frames"]) * DT

    ein, eout, epop = C.ease(s, "type_in"), C.ease(s, "type_out"), C.ease(s, "type_pop")
    xf = int(L["exit_frames"])
    rise_out = -float(L["exit_rise"])

    js = comp_jsx("Center_Title", total)

    js += text("kk", "Kicker", kicker, fk, zk, col(s, L["kicker_color"]), "LEFT_JUSTIFY", kx, k_base, tracking=tk)
    js += envelope("kk", s, t_k, t_out_k, pos=[kx, k_base], slide=(0, L["kicker_rise"]),
                   out_slide=(0, rise_out), in_frames=int(L["kicker_frames"]), out_frames=xf)

    # underline spans the measured kicker ink width; scale-X draw, pre-keyed at 0 so it is hidden until t_u
    js += solid("ul", "Underline", L["underline_color"], cx - kw / 2.0, ul_y, kw, L["underline_h"], anchor_left=True)
    js += keys("ul", "Scale", [(0.0, [0, 100, 100])]
               + ramp(t_u, int(L["underline_frames"]), [0, 100, 100], [100, 100, 100], ein))
    js += envelope("ul", s, t_u, t_out_k, animate_pos=False, in_frames=1, out_frames=xf)

    # title opacity on type_in, position on type_pop so the landing carries the soft overshoot
    js += text("tt", "Title", title, ft, zt, col(s, L["title_color"]), "LEFT_JUSTIFY", tx, t_base)
    # Drop Shadow removed: EC ignores text-layer opacity keyframes when the effect is present (measured)
    js += keys("tt", "Opacity", [(0.0, 0.0), (t_t, 0.0),
                                 (round(t_t + int(L["title_frames"]) * DT, 4), 100.0), (round(t_out_t, 4), 100.0),
                                 (round(t_out_t + xf * DT, 4), 0.0)])
    js += keys("tt", "Position", ramp(t_t, int(L["title_frames"]), [tx, t_base + L["title_rise"]], [tx, t_base], epop)
               + ramp(t_out_t, xf, [tx, t_base], [tx, t_base + rise_out], eout))

    js += text("sb", "Sub", sub, fs, zs, accent, "LEFT_JUSTIFY", sx, s_base, tracking=ts)
    js += envelope("sb", s, t_s, t_out_s, pos=[sx, s_base], slide=(0, L["sub_rise"]),
                   out_slide=(0, rise_out), in_frames=int(L["sub_frames"]), out_frames=xf)

    return js + finish_jsx(), total, {"block": [cx - block_w / 2.0, top, cx + block_w / 2.0, bottom]}


# ----------------------------------------------------------------------------- 14. drop-title (Mixkit 240)
DROP_DEFAULTS = {
    "hold_seconds": 3.0,
    "lead_in": 0.25,
    "center_y": 360,
    "heading_font": "Montserrat-ExtraBold",
    "heading_size": 108,
    "heading_tracking": 10,
    "heading_color": "ivory",
    "max_heading_w": 1300,
    "drop_px": 150,
    "overshoot_px": 28,
    "fall_frames": 9,
    "settle_frames": 7,
    "fade_in_frames": 5,
    "impact_squash_pct": 4.0,
    "shadow_softness": 24,
    "shadow_opacity": 55,
    "shadow_distance": 3,
    "gap_heading_rule": 24,
    "rule_h": 6,
    "rule_notch_px": 140,
    "rule_min_w": 120,
    "tag_delay": 0.12,
    "tag_pop_frames": 10,
    "tag_rise_px": 14,
    "gap_rule_tag": 18,
    "tag_font": "Montserrat-Bold",
    "tag_size": 46,
    "tag_tracking": 80,
    "tag_color": "gold",
    "max_tag_w": 1300,
    "exit_rise_px": 26,
}


def build_drop_title(s, v):
    """Heading drops from above, overshoots and springs back onto its line; accent rule (plus an optional small
    tag) pops in after the settle; hold, then everything fades and the heading is plucked upward. Section/step
    stamps in the upper third. All in layout.drop_title."""
    L = {**DROP_DEFAULTS, **s["layout"].get("drop_title", {})}
    f1, f2 = L["heading_font"], L["tag_font"]
    z1, z2 = L["heading_size"], L["tag_size"]
    tr1, tr2 = L["heading_tracking"], L["tag_tracking"]
    C.assert_min_font(s, z1, z2)
    head = " ".join((v.get("Heading") or "").split()).upper()
    if not head:
        raise SystemExit("BUILD ERROR: drop-title needs a non-empty 'Heading'")
    tag = " ".join((v.get("Tag") or "").split())
    l1, a1, r1, b1, w1 = tw(s, f1, z1, head, tr1)
    if w1 > L["max_heading_w"]:
        raise SystemExit(f"BUILD ERROR: heading '{head}' is {w1:.0f}px wide, limit {L['max_heading_w']}px")
    if tag:
        l2, a2, r2, b2, w2 = tw(s, f2, z2, tag, tr2)
        if w2 > L["max_tag_w"]:
            raise SystemExit(f"BUILD ERROR: tag '{tag}' is {w2:.0f}px wide, limit {L['max_tag_w']}px")
    else:
        l2 = a2 = b2 = w2 = 0

    # the rule is a notch shorter than the measured heading ink, never wider than the heading itself
    rule_w = w1 - L["rule_notch_px"]
    if rule_w < L["rule_min_w"]:
        rule_w = min(w1, L["rule_min_w"])

    # stacked block: heading ink + rule + optional tag ink, centred on the upper-third line
    block_h = a1 + b1 + L["gap_heading_rule"] + L["rule_h"]
    if tag:
        block_h += L["gap_rule_tag"] + a2 + b2
    sx0, sy0, sx1, sy1 = C.safe_rect(s)
    top = L["center_y"] - block_h / 2.0
    head_base = top + a1
    rule_top = head_base + b1 + L["gap_heading_rule"]
    rule_cy = rule_top + L["rule_h"] / 2.0
    tag_base = rule_top + L["rule_h"] + L["gap_rule_tag"] + a2
    bottom = (tag_base + b2) if tag else (rule_top + L["rule_h"])
    hx = sx0 - l1
    tx = (sx0 - l2) if tag else sx0
    box_w = max(w1, rule_w, w2)
    C.assert_inside_safe(s, "drop title", sx0, top, sx0 + box_w, bottom)

    a_out = s["animation"]["out_frames"]
    ein, eout, epop = C.ease(s, "type_in"), C.ease(s, "type_out"), C.ease(s, "type_pop")

    # fall accelerates into an oversized key, then a decelerating spring-back lands on the line
    t0 = float(L["lead_in"])
    t_over = t0 + L["fall_frames"] * DT
    t_settle = t_over + L["settle_frames"] * DT
    t_rule = t_settle + L["tag_delay"]
    t_tag_done = t_rule + L["tag_pop_frames"] * DT
    t_out = t_tag_done + hold(v, L)
    total = t_out + a_out * DT

    y_start = head_base - L["drop_px"]
    y_over = head_base + L["overshoot_px"]
    pos = ramp(t0, L["fall_frames"], [hx, y_start, 0], [hx, y_over, 0], eout)
    pos += ramp(t_over, L["settle_frames"], [hx, y_over, 0], [hx, head_base, 0], ein)[1:]
    pos += [(t_out, [hx, head_base, 0])]
    # plucked out: accelerating rise while everything else fades
    pos += ramp(t_out, a_out, [hx, head_base, 0], [hx, head_base - L["exit_rise_px"], 0], eout)[1:]

    js = comp_jsx("Drop_Title", total)
    js += text("hd", "Heading", head, f1, z1, col(s, L["heading_color"]), "LEFT_JUSTIFY", hx, head_base, tracking=tr1)
    # Drop Shadow removed: EC ignores text-layer opacity keyframes when the effect is present (measured)
    js += envelope("hd", s, t0, t_out, animate_pos=False, in_frames=L["fade_in_frames"])
    js += keys("hd", "Position", pos)
    sq = float(L["impact_squash_pct"])
    if sq:
        js += keys("hd", "Scale", [(t0, [100, 100, 100]), (t_over, [100, 100, 100]),
                                   (t_over + 2 * DT, [100, 100 - sq, 100])]
                   + ramp(t_over + 2 * DT, L["settle_frames"], [100, 100 - sq, 100], [100, 100, 100], epop))

    # accent rule grows from its left edge with a back-eased pop
    js += solid("ru", "TagRule", _accent_or_exit(s, v), sx0, rule_cy, rule_w, L["rule_h"], anchor_left=True)
    js += keys("ru", "Scale", [(0.0, [0, 100, 100]), (t_rule, [0, 100, 100])]
               + ramp(t_rule, L["tag_pop_frames"], [0, 100, 100], [100, 100, 100], epop))
    js += envelope("ru", s, t_rule, t_out, animate_pos=False, in_frames=2)

    if tag:
        js += text("tg", "TagLabel", tag, f2, z2, col(s, L["tag_color"]), "LEFT_JUSTIFY", tx, tag_base,
                   tracking=tr2)
        js += envelope("tg", s, t_rule, t_out, animate_pos=False, in_frames=L["tag_pop_frames"])
        js += keys("tg", "Position", ramp(t_rule, L["tag_pop_frames"],
                                          [tx, tag_base + L["tag_rise_px"], 0], [tx, tag_base, 0], ein))

    return js + finish_jsx(), total, {"block": [sx0, top, sx0 + box_w, bottom]}


TITLE_BUILDERS.update({
    "bold-third": build_bold_third,
    "banner-third": build_banner_third,
    "center-title": build_center_title,
    "drop-title": build_drop_title,
})

try:
    import _families_v2
    _families_v2.BUILDERS.update(TITLE_BUILDERS)
except Exception:
    pass


