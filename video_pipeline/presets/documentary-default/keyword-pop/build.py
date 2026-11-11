"""Keyword-pop builder: one word/number, scale overshoot (easeOutBack baked 1 key/frame). Reads ../style.json.
Also imported by presets/shorts-vertical/build.py (which passes its merged style).

  python build.py [--values keyword-pop.json.example] [--style ../style.json] [--out-dir .] [--emit-values out.json] [--dry]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import _common as C  # noqa: E402


def build(style, values, out_dir, emit_values=None, dry=False, comp_name="Keyword_Pop", title="Documentary Keyword Pop"):
    canvas, typo, anim = style["canvas"], style["typography"], style["animation"]
    sizes, colors, L = typo["sizes"], typo["colors"], style["layout"]["keyword_pop"]
    C.assert_min_font(style, sizes["keyword_pop"])
    word = values["Keyword"]
    font, size = typo["font_numeric"], sizes["keyword_pop"]

    l, a, r, b = C.ink(style, font, size, word)
    adv = C.font_for(style, font, size).getlength(word)
    anchor_x = (l + r) / 2.0 - adv / 2.0           # ink centre relative to the centre-justified origin
    anchor_y = -(a - b) / 2.0                      # ink centre relative to the baseline (up is negative)

    ein, eout, epop = C.ease(style, "type_in"), C.ease(style, "type_out"), C.ease(style, "type_pop")
    tm = C.Timing(style, L["in_frames"], L["out_frames"], L["hold_seconds"])
    start, out_end = L["start_scale_pct"], L["out_scale_pct"]

    in_scales = [start + (100.0 - start) * epop(f / float(tm.in_frames)) for f in range(tm.in_frames + 1)]
    peak = max(in_scales) / 100.0
    half_w, half_h = (r - l) / 2.0 * peak, (a + b) / 2.0 * peak
    C.assert_inside_safe(style, "keyword-pop at peak scale", L["center_x"] - half_w, L["center_y"] - half_h,
                         L["center_x"] + half_w, L["center_y"] + half_h)

    scale_in, op_in, scale_out, op_out = [], [], [], []
    for f in range(tm.in_frames + 1):
        sc = round(in_scales[f], 2)
        scale_in.append(f"propScale.setValueAtTime({tm.t_in(f)}, [{sc}, {sc}, 100.0]);")
        op_in.append(f"propOp.setValueAtTime({tm.t_in(f)}, {round(100.0 * ein(f / float(tm.in_frames)), 2)});")
    for f in range(tm.out_frames + 1):
        p = eout(f / float(tm.out_frames))
        sc = round(100.0 - (100.0 - out_end) * p, 2)
        scale_out.append(f"propScale.setValueAtTime({tm.t_outf(f)}, [{sc}, {sc}, 100.0]);")
        op_out.append(f"propOp.setValueAtTime({tm.t_outf(f)}, {round(100.0 * (1.0 - p), 2)});")

    jsx = f'var comp = app.project.items.addComp("{comp_name}", {canvas["width"]}, {canvas["height"]}, 1.0, {tm.total}, {tm.fps});\ncomp.bgColor = [0, 0, 0];\n'
    jsx += C.text_layer_jsx("kwLayer", "KeywordLayer", word, font, size, C.hex_to_rgb(colors["gold"]), "CENTER_JUSTIFY", L["center_x"], L["center_y"])
    jsx += f'kwLayer.property("Anchor Point").setValue([{round(anchor_x, 3)}, {round(anchor_y, 3)}, 0]);\n'
    jsx += f'''var propScale = kwLayer.property("Scale");
{chr(10).join(scale_in)}
propScale.setValueAtTime({round(tm.t_out, 5)}, [100.0, 100.0, 100.0]);
{chr(10).join(scale_out)}
var propOp = kwLayer.property("Opacity");
{chr(10).join(op_in)}
propOp.setValueAtTime({round(tm.t_out, 5)}, 100.0);
{chr(10).join(op_out)}
app.project.save(new File("__PROJ_PATH__"));
writeLn("ECPROJ_SAVED");
'''
    C.write_values(emit_values, {"Keyword": word})
    res = C.run_jsx_and_export(style, jsx, out_dir, "keyword-pop", title, [("KeywordLayer", "Keyword")], dry)
    box = dict(peak_box=[L["center_x"] - half_w, L["center_y"] - half_h, L["center_x"] + half_w, L["center_y"] + half_h], peak_scale=peak)
    print("keyword-pop peak box", [round(v, 1) for v in box["peak_box"]], "peak scale", round(peak, 4))
    return box, res


if __name__ == "__main__":
    ap = C.common_args("Keyword-pop builder")
    a = ap.parse_args()
    style = C.load_style(a.style or os.path.join(HERE, "..", "style.json"))
    values = C.read_values(a.values or os.path.join(HERE, "keyword-pop.json.example"), {})
    build(style, values, a.out_dir or HERE, a.emit_values, a.dry)
