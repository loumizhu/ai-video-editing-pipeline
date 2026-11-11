"""Draft: center-title — recreation of Mixkit template 196 ("Center-aligned simple animated title").

Centred three-line block for chapter/act cards: wide-tracked uppercase kicker, thin white rule that draws on
after the kicker lands, oversized bold title with a soft overshoot, then a light accent subheading. Exit mirrors
the entry in reverse order. Animation is position/opacity/scale keys only (no wipes).

Every x offset comes from tw() ink metrics, so each line is optically centred on the canvas centre rather than
advance-width centred.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRESET_DIR = os.path.dirname(HERE)
if PRESET_DIR not in sys.path:
    sys.path.insert(0, PRESET_DIR)

import _common as C
from _families_v2 import (DT, T, col, comp_jsx, envelope, finish_jsx, hold, keys, ramp, shadow, solid, text, tw)


LAYOUT_DEFAULTS = {
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
    L = {**LAYOUT_DEFAULTS, **s["layout"].get("center_title", {})}

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

    accent = v.get("AccentColor")
    if not accent:
        accent = col(s, L["accent_key"])
    elif not str(accent).startswith("#"):
        accent = col(s, str(accent))

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
    js += shadow("tt", L["shadow_softness"], L["shadow_opacity"], L["shadow_distance"])
    js += keys("tt", "Opacity", [(0.0, 0.0)] + ramp(t_t, int(L["title_frames"]), 0.0, 100.0, ein)
               + ramp(t_out_t, xf, 100.0, 0.0, eout))
    js += keys("tt", "Position", ramp(t_t, int(L["title_frames"]), [tx, t_base + L["title_rise"]], [tx, t_base], epop)
               + ramp(t_out_t, xf, [tx, t_base], [tx, t_base + rise_out], eout))

    js += text("sb", "Sub", sub, fs, zs, accent, "LEFT_JUSTIFY", sx, s_base, tracking=ts)
    js += envelope("sb", s, t_s, t_out_s, pos=[sx, s_base], slide=(0, L["sub_rise"]),
                   out_slide=(0, rise_out), in_frames=int(L["sub_frames"]), out_frames=xf)

    return js + finish_jsx(), total, {"block": [cx - block_w / 2.0, top, cx + block_w / 2.0, bottom]}
