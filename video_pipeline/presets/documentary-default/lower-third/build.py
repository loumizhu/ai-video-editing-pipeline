"""Lower-third builder. Reads ../style.json; sizes the glass plate from measured text; exports .ectemplate.

  python build.py [--values lower-third.json.example] [--style ../style.json] [--out-dir .] [--emit-values out.json] [--dry]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import _common as C  # noqa: E402


def build(style, values, out_dir, emit_values=None, dry=False):
    canvas, typo, anim = style["canvas"], style["typography"], style["animation"]
    sizes, colors, L = typo["sizes"], typo["colors"], style["layout"]["lower_third"]
    glass = style["layout"]["glass"]
    C.assert_min_font(style, sizes["name_primary"], sizes["role_secondary"])

    name, role = values["Name"], values["Role"]
    nl, na, nr, nb = C.ink(style, typo["font_primary"], sizes["name_primary"], name)
    rl, ra, rr, rb = C.ink(style, typo["font_secondary"], sizes["role_secondary"], role)
    slack = typo["measure_slack_px"]
    content_w = max(nr - nl, rr - rl) + slack

    plate_w = L["text_offset_x"] + content_w + L["pad_right"]
    plate_h = L["pad_y"] + na + nb + L["line_gap"] + ra + rb + L["pad_y"]
    plate_x = canvas["safe_margin_x"]
    plate_y = canvas["height"] - canvas["safe_margin_bottom"] - plate_h
    C.assert_inside_safe(style, "lower-third plate", plate_x, plate_y, plate_x + plate_w, plate_y + plate_h)

    origin_x = plate_x + L["text_offset_x"] - nl           # ink left lands on plate_x + text_offset_x
    name_base = plate_y + L["pad_y"] + na
    role_base = name_base + nb + L["line_gap"] + ra
    bar = (plate_x + L["bar_inset_x"], plate_y + L["bar_inset_y"], L["bar_width"], plate_h - 2 * L["bar_inset_y"])

    tm = C.Timing(style, anim["in_frames"], anim["out_frames"], L["hold_seconds"])
    ein, eout, slide = C.ease(style, "type_in"), C.ease(style, "type_out"), anim["slide_px"]

    jsx = f'var comp = app.project.items.addComp("Lower_Third", {canvas["width"]}, {canvas["height"]}, 1.0, {tm.total}, {tm.fps});\ncomp.bgColor = [0, 0, 0];\n'
    jsx += C.glass_jsx("lt", style, tm, ein, eout, plate_x, plate_y, plate_w, plate_h, L["border_px"], glass["plate_alpha"], slide, True, bar)
    jsx += C.text_layer_jsx("nameL", "NameLayer", name, typo["font_primary"], sizes["name_primary"], C.hex_to_rgb(colors["ivory"]), "LEFT_JUSTIFY", origin_x, name_base)
    jsx += C.slide_fade_jsx("nameL", tm, ein, eout, origin_x, name_base, slide, 100.0) + "\n"
    jsx += C.text_layer_jsx("roleL", "RoleLayer", role, typo["font_secondary"], sizes["role_secondary"], C.hex_to_rgb(colors["gold"]), "LEFT_JUSTIFY", origin_x, role_base)
    jsx += C.slide_fade_jsx("roleL", tm, ein, eout, origin_x, role_base, slide, 100.0) + "\n"
    jsx += 'app.project.save(new File("__PROJ_PATH__"));\nwriteLn("ECPROJ_SAVED");\n'

    C.write_values(emit_values, {"Name": name, "Role": role})
    res = C.run_jsx_and_export(style, jsx, out_dir, "lower-third", "Documentary Lower Third",
                               [("NameLayer", "Name"), ("RoleLayer", "Role")], dry)
    box = dict(plate=[plate_x, plate_y, plate_x + plate_w, plate_y + plate_h], name_baseline=name_base, role_baseline=role_base)
    print("lower-third plate box", [round(v, 1) for v in box["plate"]], "baselines", round(name_base, 1), round(role_base, 1))
    return box, res


if __name__ == "__main__":
    ap = C.common_args("Lower-third builder")
    a = ap.parse_args()
    style = C.load_style(a.style or os.path.join(HERE, "..", "style.json"))
    values = C.read_values(a.values or os.path.join(HERE, "lower-third.json.example"), {})
    build(style, values, a.out_dir or HERE, a.emit_values, a.dry)
