"""Quote-pullout builder: glass plate + wrapped verbatim quote + attribution. Reads ../style.json.
Wrapping is computed from real glyph advances against layout.quote_pullout.max_text_width.

  python build.py [--values quote-pullout.json.example] [--style ../style.json] [--out-dir .] [--emit-values out.json] [--dry]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import _common as C  # noqa: E402


def build(style, values, out_dir, emit_values=None, dry=False):
    canvas, typo, anim = style["canvas"], style["typography"], style["animation"]
    sizes, colors, L = typo["sizes"], typo["colors"], style["layout"]["quote_pullout"]
    glass = style["layout"]["glass"]
    C.assert_min_font(style, sizes["quote_body"], sizes["quote_author"])
    sx0, sy0, sx1, sy1 = C.safe_rect(style)
    cx = L["center_x"]
    slack = typo["measure_slack_px"]

    limit = min(L["max_text_width"], (sx1 - sx0) - 2 * L["pad_x"] - slack)   # never wider than the safe rect allows
    lines = C.wrap(style, typo["font_secondary"], sizes["quote_body"], values["Quote"], limit, L["max_lines"])
    attr = values["Attribution"]
    q_ink = [C.ink(style, typo["font_secondary"], sizes["quote_body"], ln) for ln in lines]
    a_ink = C.ink(style, typo["font_primary"], sizes["quote_author"], attr)
    content_w = max([r - l for (l, a, r, b) in q_ink] + [a_ink[2] - a_ink[0]]) + slack

    first_base = q_ink[0][1]
    last_base = first_base + (len(lines) - 1) * L["leading"]
    attr_base = last_base + q_ink[-1][3] + L["attribution_gap"] + a_ink[1]
    block_h = attr_base + a_ink[3]
    plate_h = block_h + 2 * L["pad_y"]
    plate_w = content_w + 2 * L["pad_x"]
    plate_y = L["center_y"] - plate_h / 2.0
    plate_x = cx - plate_w / 2.0
    C.assert_inside_safe(style, "quote-pullout plate", plate_x, plate_y, plate_x + plate_w, plate_y + plate_h)
    dy = plate_y + L["pad_y"]
    first_base, attr_base = first_base + dy, attr_base + dy

    tm = C.Timing(style, anim["in_frames"], anim["out_frames"], L["hold_seconds"])
    ein, eout, slide = C.ease(style, "type_in"), C.ease(style, "type_out"), anim["slide_px"]
    gold, ivory = C.hex_to_rgb(colors["gold"]), C.hex_to_rgb(colors["ivory"])

    jsx = f'var comp = app.project.items.addComp("Quote_Pullout", {canvas["width"]}, {canvas["height"]}, 1.0, {tm.total}, {tm.fps});\ncomp.bgColor = [0, 0, 0];\n'
    jsx += C.glass_jsx("qp", style, tm, ein, eout, plate_x, plate_y, plate_w, plate_h, L["border_px"], glass["plate_alpha"], slide)
    jsx += C.text_layer_jsx("quoteL", "QuoteLayer", "\r".join(lines), typo["font_secondary"], sizes["quote_body"], ivory, "CENTER_JUSTIFY", cx, first_base, leading=L["leading"])
    jsx += C.slide_fade_jsx("quoteL", tm, ein, eout, cx, first_base, slide, 100.0) + "\n"
    jsx += C.text_layer_jsx("attrL", "AttributionLayer", attr, typo["font_primary"], sizes["quote_author"], gold, "CENTER_JUSTIFY", cx, attr_base)
    jsx += C.slide_fade_jsx("attrL", tm, ein, eout, cx, attr_base, slide, 100.0) + "\n"
    jsx += 'app.project.save(new File("__PROJ_PATH__"));\nwriteLn("ECPROJ_SAVED");\n'

    C.write_values(emit_values, {"Quote": "\r".join(lines), "Attribution": attr})
    res = C.run_jsx_and_export(style, jsx, out_dir, "quote-pullout", "Documentary Quote Pullout",
                               [("QuoteLayer", "Quote"), ("AttributionLayer", "Attribution")], dry)
    box = dict(plate=[plate_x, plate_y, plate_x + plate_w, plate_y + plate_h], lines=lines)
    print("quote-pullout plate box", [round(v, 1) for v in box["plate"]], "lines", len(lines))
    return box, res


if __name__ == "__main__":
    ap = C.common_args("Quote-pullout builder")
    a = ap.parse_args()
    style = C.load_style(a.style or os.path.join(HERE, "..", "style.json"))
    values = C.read_values(a.values or os.path.join(HERE, "quote-pullout.json.example"), {})
    build(style, values, a.out_dir or HERE, a.emit_values, a.dry)
