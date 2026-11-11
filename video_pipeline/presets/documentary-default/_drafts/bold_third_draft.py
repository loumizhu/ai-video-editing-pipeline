"""Bold third draft: house recreation of Mixkit template 312 ('Bold Lower-third').

A bold uppercase accent heading stamped in, a thin white clearance line sweeping under it as it lands, a hold,
then a fast heading exit while the line retracts. Bottom-left anchored in the safe area like line-third.
Motion is position/opacity/scale keys only (Linear Wipe is unusable in EffectCraft; see build_line_third).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRESET_DIR = os.path.dirname(HERE)
if PRESET_DIR not in sys.path:
    sys.path.insert(0, PRESET_DIR)

import _common as C  # noqa: E402
from _families_v2 import (DT, col, comp_jsx, finish_jsx, hold, keys, ramp, shadow, solid, text,  # noqa: E402
                          tw)

LAYOUT_DEFAULTS = {
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
    L = {**LAYOUT_DEFAULTS, **s["layout"].get("bold_third", {})}
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

    cx, cy = x_l + w1 / 2.0, head_base - (a1 - b1) / 2.0  # stamp pivot = heading ink centre, not the baseline origin
    js = comp_jsx("Bold_Third", total)
    js += solid("ln", "ClearanceLine", L["line_color"], x_l, line_cy, line_w, L["line_h"], anchor_left=True)
    js += keys("ln", "Scale", [(0.0, [0, 100, 100])]
               + ramp(t_line0, int(L["line_sweep_frames"]), [0, 100, 100], [100, 100, 100], ein)
               + ramp(t_out, int(L["line_retract_frames"]), [100, 100, 100], [0, 100, 100], eout))
    js += text("hd", "Heading", head, f, z, acc, "LEFT_JUSTIFY", x_l - l1, head_base, tracking=tr)
    js += shadow("hd", L["shadow_softness"], L["shadow_opacity"], L["shadow_distance"])
    js += keys("hd", "Opacity", [(0.0, 0.0)] + ramp(e0, int(L["stamp_op_frames"]), 0.0, 100.0, ein)
               + ramp(t_out, fo, 100.0, 0.0, eout))
    js += 'var rig = comp.layers.addNull();\nrig.name = "StampRig";\n'
    js += f'rig.property("Position").setValue([{round(cx, 3)}, {round(cy, 3)}, 0]);\n'
    js += 'hd.parent = rig;\n'
    sf, st = float(L["stamp_scale_from"]), float(L["exit_scale_to"])
    js += keys("rig", "Position", ramp(e0, fi, [cx, cy - L["stamp_drop_px"], 0], [cx, cy, 0], ein))
    js += keys("rig", "Scale", ramp(e0, fi, [sf, sf, 100], [100, 100, 100], epop)
               + ramp(t_out, fo, [100, 100, 100], [st, st, 100], eout))
    return js + finish_jsx(), total, {"block": [x_l, head_top, x_l + max(w1, line_w), sy1]}
