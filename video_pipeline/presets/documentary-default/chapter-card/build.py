"""Chapter-card builder: scrim plate + chapter number + hairline + wrapped title. Reads ../style.json.

  python build.py [--values chapter-card.json.example] [--style ../style.json] [--out-dir .] [--emit-values out.json] [--dry]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import _common as C  # noqa: E402


def build(style, values, out_dir, emit_values=None, dry=False):
    canvas, typo, anim = style["canvas"], style["typography"], style["animation"]
    sizes, colors, L = typo["sizes"], typo["colors"], style["layout"]["chapter_card"]
    C.assert_min_font(style, sizes["chapter_number"], sizes["chapter_title"])
    sx0, sy0, sx1, sy1 = C.safe_rect(style)
    cx = canvas["width"] / 2.0

    chapter = values["Chapter"]
    slack = typo["measure_slack_px"]
    max_text_w = (sx1 - sx0) - 2 * L["pad_x"] - slack
    title_lines = C.wrap(style, typo["font_primary"], sizes["chapter_title"], values["Title"], max_text_w, L["max_title_lines"])

    cl, ca, cr, cb = C.ink(style, typo["font_numeric"], sizes["chapter_number"], chapter, tracking=L["chapter_tracking"])
    t_ink = [C.ink(style, typo["font_primary"], sizes["chapter_title"], ln) for ln in title_lines]
    content_w = max([cr - cl] + [r - l for (l, a, r, b) in t_ink]) + slack

    # vertical stack, measured from the top of the chapter line ink
    top = 0.0
    chap_base = top + ca
    hair_top = chap_base + cb + L["gap_chapter_hairline"]
    hair_bot = hair_top + L["hairline_height"]
    first_base = hair_bot + L["gap_hairline_title"] + t_ink[0][1]
    last_base = first_base + (len(title_lines) - 1) * L["title_leading"]
    bottom = last_base + t_ink[-1][3]
    block_h = bottom - top
    plate_h = block_h + 2 * L["pad_y"]
    plate_w = content_w + 2 * L["pad_x"]
    plate_y = L["center_y"] - plate_h / 2.0
    plate_x = cx - plate_w / 2.0
    C.assert_inside_safe(style, "chapter-card plate", plate_x, plate_y, plate_x + plate_w, plate_y + plate_h)
    dy = plate_y + L["pad_y"] - top                     # shift stack into the plate
    chap_base, hair_top, first_base = chap_base + dy, hair_top + dy, first_base + dy

    tm = C.Timing(style, anim["in_frames"], anim["out_frames"], L["hold_seconds"])
    ein, eout, slide = C.ease(style, "type_in"), C.ease(style, "type_out"), anim["slide_px"]
    gold, gold_accent, ivory = C.hex_to_rgb(colors["gold"]), C.hex_to_rgb(colors["gold_accent"]), C.hex_to_rgb(colors["ivory"])

    jsx = f'var comp = app.project.items.addComp("Chapter_Card", {canvas["width"]}, {canvas["height"]}, 1.0, {tm.total}, {tm.fps});\ncomp.bgColor = [0, 0, 0];\n'
    jsx += C.glass_jsx("cc", style, tm, ein, eout, plate_x, plate_y, plate_w, plate_h, 0, L["plate_alpha"], slide)
    jsx += C.text_layer_jsx("chapL", "ChapterLayer", chapter, typo["font_numeric"], sizes["chapter_number"], gold, "CENTER_JUSTIFY", cx, chap_base, tracking=L["chapter_tracking"])
    jsx += C.slide_fade_jsx("chapL", tm, ein, eout, cx, chap_base, slide, 100.0) + "\n"
    jsx += C.solid_jsx("hairL", "HairlineDivider", gold_accent, cx - L["hairline_width"] / 2.0, hair_top, L["hairline_width"], L["hairline_height"])
    jsx += C.slide_fade_jsx("hairL", tm, ein, eout, cx, hair_top + L["hairline_height"] / 2.0, slide, L["hairline_alpha"] * 100.0) + "\n"
    jsx += C.text_layer_jsx("titleL", "TitleLayer", "\r".join(title_lines), typo["font_primary"], sizes["chapter_title"], ivory, "CENTER_JUSTIFY", cx, first_base, leading=L["title_leading"])
    jsx += C.slide_fade_jsx("titleL", tm, ein, eout, cx, first_base, slide, 100.0) + "\n"
    jsx += 'app.project.save(new File("__PROJ_PATH__"));\nwriteLn("ECPROJ_SAVED");\n'

    C.write_values(emit_values, {"Chapter": chapter, "Title": "\r".join(title_lines)})
    res = C.run_jsx_and_export(style, jsx, out_dir, "chapter-card", "Documentary Chapter Card",
                               [("ChapterLayer", "Chapter"), ("TitleLayer", "Title")], dry)
    box = dict(plate=[plate_x, plate_y, plate_x + plate_w, plate_y + plate_h], title_lines=title_lines)
    print("chapter-card plate box", [round(v, 1) for v in box["plate"]], "title lines", len(title_lines))
    return box, res


if __name__ == "__main__":
    ap = C.common_args("Chapter-card builder")
    a = ap.parse_args()
    style = C.load_style(a.style or os.path.join(HERE, "..", "style.json"))
    values = C.read_values(a.values or os.path.join(HERE, "chapter-card.json.example"), {})
    build(style, values, a.out_dir or HERE, a.emit_values, a.dry)
