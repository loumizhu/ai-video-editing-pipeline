"""Draft family: drop-title (Mixkit template 240 'Drop Text Title' recreation).

A bold uppercase heading drops from above, overshoots its resting line, then springs back; an accent
rule (plus an optional small tag) pops in underneath once the heading settles; the block holds, then
everything fades while the heading is plucked upward. Geometry/timing live in layout.drop_title with
LAYOUT_DEFAULTS as the fallback for styles that do not define the family yet.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRESET = os.path.dirname(HERE)
if PRESET not in sys.path:
    sys.path.insert(0, PRESET)

import _common as C
from _families_v2 import (DT, col, comp_jsx, envelope, finish_jsx, hold, keys, ramp, shadow, solid, text, tw)


LAYOUT_DEFAULTS = {
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


def _accent(s, v):
    a = (v.get("AccentColor") or "").strip()
    if not a:
        return col(s, "gold_accent")
    if a.startswith("#"):
        return a
    try:
        return col(s, a)
    except KeyError:
        raise SystemExit(f"BUILD ERROR: AccentColor '{a}' is neither a palette key nor a #hex color")


def build_drop_title(s, v):
    L = {**LAYOUT_DEFAULTS, **s["layout"].get("drop_title", {})}
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
    js += shadow("hd", L["shadow_softness"], L["shadow_opacity"], L["shadow_distance"])
    js += envelope("hd", s, t0, t_out, animate_pos=False, in_frames=L["fade_in_frames"])
    js += keys("hd", "Position", pos)
    sq = float(L["impact_squash_pct"])
    if sq:
        js += keys("hd", "Scale", [(t0, [100, 100, 100]), (t_over, [100, 100, 100]),
                                   (t_over + 2 * DT, [100, 100 - sq, 100])]
                   + ramp(t_over + 2 * DT, L["settle_frames"], [100, 100 - sq, 100], [100, 100, 100], epop))

    # accent rule grows from its left edge with a back-eased pop
    js += solid("ru", "TagRule", _accent(s, v), sx0, rule_cy, rule_w, L["rule_h"], anchor_left=True)
    js += keys("ru", "Scale", [(t_rule, [0, 100, 100])]
               + ramp(t_rule, L["tag_pop_frames"], [0, 100, 100], [100, 100, 100], epop))
    js += envelope("ru", s, t_rule, t_out, animate_pos=False, in_frames=2)

    if tag:
        js += text("tg", "TagLabel", tag, f2, z2, col(s, L["tag_color"]), "LEFT_JUSTIFY", tx, tag_base,
                   tracking=tr2)
        js += envelope("tg", s, t_rule, t_out, animate_pos=False, in_frames=L["tag_pop_frames"])
        js += keys("tg", "Position", ramp(t_rule, L["tag_pop_frames"],
                                          [tx, tag_base + L["tag_rise_px"], 0], [tx, tag_base, 0], ein))

    return js + finish_jsx(), total, {"block": [sx0, top, sx0 + box_w, bottom]}

