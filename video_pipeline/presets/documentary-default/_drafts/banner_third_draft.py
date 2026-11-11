"""banner-third draft (Mixkit template 305, 'Accented Banner Lower-third'): dark plate with a crisp solid border
slides in from the left and decelerates, bold uppercase headline + wide-tracked uppercase subhead ride the plate,
the border strokes draw on once the plate stops, hold, then the whole block slides out to the right.
Bottom-left anchored. Plate size is measured from the real fonts; nothing about it is hardcoded."""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PRESET = os.path.dirname(_HERE)
if _PRESET not in sys.path:
    sys.path.insert(0, _PRESET)

import _common as C  # noqa: E402
from _families_v2 import (DT, T, _r, _v, col, comp_jsx, envelope, finish_jsx, hold, keys, ramp, solid, text,  # noqa: E402
                          tw)

LAYOUT_DEFAULTS = {
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


def _stroke(var, name, hexcol, x, y, w, h, ax, ay):
    """Solid with an explicit anchor (scaling grows from that edge); (x, y) = anchor position."""
    rgb = C.hex_to_rgb(hexcol)
    return (f'var {var} = comp.layers.addSolid([{rgb[0]}, {rgb[1]}, {rgb[2]}], "{name}", '
            f'{max(1, int(round(w)))}, {max(1, int(round(h)))}, 1.0);\n'
            f'{var}.property("Anchor Point").setValue({_v([ax, ay, 0])});\n'
            f'{var}.property("Position").setValue({_v([x, y, 0])});\n')


def build_banner_third(s, v):
    L = {**LAYOUT_DEFAULTS, **s["layout"].get("banner_third", {})}
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
        js += keys(var, "Opacity", [(0.0, 0.0), (s0, 0.0), (s0 + 2 * DT, bop), (t_out, bop)]
                   + ramp(t_out, a_out, bop, 0.0, eout))
        js += keys(var, "Position", [(0.0, rest), (t_out, rest)]
                   + ramp(t_out, a_out, rest, [x + dout, y, 0], eout))
    return js + finish_jsx(), total, {"block": [px0, py0, px1, py1]}
