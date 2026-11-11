"""Shared helpers for every preset builder. Nothing visual is defined here: all numbers come from style.json.

Provides: style loading (+ base_preset merge for variants), access tracking (dead-key detection),
easing, keyframe JSX, font-metric measuring / wrapping, glass plates, EffectCraft export.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
META_KEYS = {"preset_name", "version", "description", "base_preset"}


# ----------------------------------------------------------------------------- style loading
def deep_merge(base, overrides):
    merged = dict(base)
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged


class Tracked(dict):
    """dict that records every key path read through [] or .get() (used by check_style.py)."""

    def __init__(self, data, path="", seen=None):
        super().__init__()
        self._path = path
        self.seen = seen if seen is not None else set()
        for k, v in data.items():
            dict.__setitem__(self, k, Tracked(v, f"{path}{k}.", self.seen) if isinstance(v, dict) else v)

    def __getitem__(self, k):
        self.seen.add(self._path + str(k))
        return dict.__getitem__(self, k)

    def get(self, k, default=None):
        if k in self:
            return self[k]
        return default

    def items(self):
        for k in list(self.keys()):
            yield k, self[k]


def load_style(path, track=False):
    """Load a style file. If it has base_preset, deep-merge it over ../<base_preset>/style.json."""
    with open(path, "r", encoding="utf-8") as f:
        style = json.load(f)
    base = style.get("base_preset")
    if base:
        with open(os.path.join(os.path.dirname(os.path.abspath(path)), "..", base, "style.json"), "r", encoding="utf-8") as f:
            style = deep_merge(json.load(f), style)
    return Tracked(style) if track else style


def leaf_paths(d, prefix=""):
    out = []
    for k, v in d.items():
        if isinstance(v, dict):
            out += leaf_paths(v, f"{prefix}{k}.")
        else:
            out.append(prefix + k)
    return out


def hex_to_rgb(h):
    h = h.lstrip("#")
    return [round(int(h[i:i + 2], 16) / 255.0, 6) for i in (0, 2, 4)]


# ----------------------------------------------------------------------------- easing
def _out_cubic(t, c1=None):
    return 1.0 - (1.0 - t) ** 3


def _in_cubic(t, c1=None):
    return t ** 3


def _out_back(t, c1=1.70158):
    c3 = c1 + 1.0
    return 1.0 + c3 * ((t - 1.0) ** 3) + c1 * ((t - 1.0) ** 2)


EASES = {"easeOutCubic": _out_cubic, "easeInCubic": _in_cubic, "easeOutBack": _out_back}


def ease(style, role):
    """role in type_in | type_out | type_pop -> callable(t)."""
    e = style["animation"]["easing"]
    fn = EASES[e[role]]
    c1 = e["overshoot_c1"]
    return lambda t: fn(t, c1)


# ----------------------------------------------------------------------------- timing / keyframes
class Timing:
    def __init__(self, style, in_frames, out_frames, hold_seconds):
        c = style["canvas"]
        self.num, self.den = c["frame_rate_num"], c["frame_rate_den"]
        self.fps = self.num / self.den
        self.in_frames, self.out_frames = in_frames, out_frames
        self.dt_in = in_frames * self.den / self.num
        self.dt_out = out_frames * self.den / self.num
        self.hold = hold_seconds
        self.total = round(self.dt_in + hold_seconds + self.dt_out, 4)
        self.t_out = self.dt_in + hold_seconds

    def t_in(self, f):
        return round(f * self.den / self.num, 5)

    def t_outf(self, f):
        return round(self.t_out + f * self.den / self.num, 5)


def slide_fade_jsx(var, tm, ein, eout, base_x, base_y, slide_px, max_op, animate_pos=True):
    """Keyframes: 1 key per frame in/out, hold key between. `var` is a JS layer variable name."""
    lines = []
    if animate_pos:
        lines.append(f'var pos = {var}.property("Position");')
    lines.append(f'var op = {var}.property("Opacity");')
    for f in range(tm.in_frames + 1):
        p = ein(f / float(tm.in_frames))
        t = tm.t_in(f)
        if animate_pos:
            lines.append(f"pos.setValueAtTime({t}, [{round(base_x, 3)}, {round(base_y + slide_px * (1.0 - p), 3)}, 0]);")
        lines.append(f"op.setValueAtTime({t}, {round(max_op * p, 3)});")
    if animate_pos:
        lines.append(f"pos.setValueAtTime({round(tm.t_out, 5)}, [{round(base_x, 3)}, {round(base_y, 3)}, 0]);")
    lines.append(f"op.setValueAtTime({round(tm.t_out, 5)}, {round(max_op, 3)});")
    for f in range(tm.out_frames + 1):
        p = eout(f / float(tm.out_frames))
        t = tm.t_outf(f)
        if animate_pos:
            lines.append(f"pos.setValueAtTime({t}, [{round(base_x, 3)}, {round(base_y + slide_px * p, 3)}, 0]);")
        lines.append(f"op.setValueAtTime({t}, {round(max_op * (1.0 - p), 3)});")
    return "\n".join(lines)


def text_layer_jsx(var, layer_name, text, font, size, rgb, justification, base_x, base_y, tracking=None, leading=None):
    t = text.replace("\\", "\\\\").replace('"', '\\"').replace("\r", "\\r").replace("\n", "\\r")
    extra = ""
    if tracking is not None:
        extra += f"{var}Doc.tracking = {tracking};\n"
    if leading is not None:
        extra += f"{var}Doc.leading = {leading};\n"
    return f"""var {var} = comp.layers.addText("{t}");
{var}.name = "{layer_name}";
var {var}St = {var}.property("Source Text");
var {var}Doc = {var}St.value;
{var}Doc.font = "{font}";
{var}Doc.fontSize = {size};
{var}Doc.fillColor = [{rgb[0]}, {rgb[1]}, {rgb[2]}];
{var}Doc.justification = ParagraphJustification.{justification};
{extra}{var}St.setValue({var}Doc);
{var}.property("Position").setValue([{round(base_x, 3)}, {round(base_y, 3)}, 0]);
"""


def solid_jsx(var, name, rgb, x, y, w, h):
    """Rectangle with top-left (x, y), size (w, h). Position keys are set later by slide_fade_jsx at centre."""
    return f'var {var} = comp.layers.addSolid([{rgb[0]}, {rgb[1]}, {rgb[2]}], "{name}", {int(round(w))}, {int(round(h))}, 1.0);\n'


# ----------------------------------------------------------------------------- font metrics
_font_cache = {}


def font_for(style, font_name, size):
    key = (font_name, size)
    if key not in _font_cache:
        typo = style["typography"]
        fname = typo["measure_files"][font_name]
        dirs = [os.path.join(HERE, "fonts"), os.path.expandvars(typo["measure_fonts_dir"]),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")]
        path = next((os.path.join(d, fname) for d in dirs if os.path.exists(os.path.join(d, fname))), None)
        if not path:
            raise SystemExit(f"BUILD ERROR: font file {fname} for {font_name} not found in {dirs}")
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def ink(style, font_name, size, text, tracking=0):
    """Ink box of one line relative to its baseline origin: (left, above, right, below) in px, above/below positive.
    tracking is AE units (1/1000 em) applied per character gap."""
    f = font_for(style, font_name, size)
    pad = size * 2
    w = int(f.getlength(text)) + pad * 2 + 8
    h = size * 4
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).text((pad, size * 2), text, font=f, fill=255, anchor="ls")
    a = np.array(im) > 40
    ys, xs = np.where(a)
    left, right = xs.min() - pad, xs.max() + 1 - pad
    above, below = size * 2 - ys.min(), ys.max() + 1 - size * 2
    if tracking and len(text) > 1:
        right += (len(text) - 1) * tracking / 1000.0 * size
    return float(left), float(above), float(right), float(below)


def wrap(style, font_name, size, text, max_w, max_lines):
    """Greedy word wrap from real glyph advances. Returns list of lines; raises if impossible."""
    f = font_for(style, font_name, size)
    words = " ".join(text.replace("\r", " ").replace("\n", " ").split()).split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if f.getlength(trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    for ln in lines:
        l, a, r, b = ink(style, font_name, size, ln)
        if r - l > max_w + 0.5:
            raise SystemExit(f"BUILD ERROR: single token '{ln[:40]}' is {r-l:.0f}px wide, limit {max_w}px at size {size}")
    if len(lines) > max_lines:
        raise SystemExit(f"BUILD ERROR: text needs {len(lines)} lines (max {max_lines}) at {max_w}px measure. Shorten it.")
    return lines


def safe_rect(style):
    c = style["canvas"]
    return (c["safe_margin_x"], c["safe_margin_top"], c["width"] - c["safe_margin_x"], c["height"] - c["safe_margin_bottom"])


def assert_inside_safe(style, name, x0, y0, x1, y1):
    sx0, sy0, sx1, sy1 = safe_rect(style)
    if x0 < sx0 or y0 < sy0 or x1 > sx1 or y1 > sy1:
        raise SystemExit(
            f"BUILD ERROR: {name} box [{x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f}] is outside the safe rect "
            f"[{sx0},{sy0},{sx1},{sy1}]. Shorten the text or lower the size in style.json."
        )


def assert_min_font(style, *sizes):
    m = style["typography"]["min_font_size"]
    for s in sizes:
        if s < m:
            raise SystemExit(f"BUILD ERROR: font size {s} < typography.min_font_size {m} (LESSONS: no text under 45px)")


# ----------------------------------------------------------------------------- glass plate
def glass_jsx(prefix, style, tm, ein, eout, x, y, w, h, border_px, plate_alpha, slide_px, with_bar=False, bar=None):
    """Charcoal plate + optional gold border (4 solids) + optional accent bar. Returns JSX string.
    x,y,w,h = top-left box in canvas px. All pieces get the same slide+fade keyframes at their own centre."""
    colors = style["typography"]["colors"]
    charcoal, gold = hex_to_rgb(colors["charcoal"]), hex_to_rgb(colors["gold_accent"])
    glass = style["layout"]["glass"]
    out = []

    def piece(var, name, rgb, px, py, pw, ph, op):
        out.append(solid_jsx(var, name, rgb, px, py, pw, ph))
        out.append(slide_fade_jsx(var, tm, ein, eout, px + pw / 2.0, py + ph / 2.0, slide_px, op))

    piece(f"{prefix}Plate", "GlassPlate", charcoal, x, y, w, h, plate_alpha * 100.0)
    if border_px:
        ba = glass["border_alpha"] * 100.0
        piece(f"{prefix}BT", "BorderTop", gold, x, y, w, border_px, ba)
        piece(f"{prefix}BB", "BorderBottom", gold, x, y + h - border_px, w, border_px, ba)
        piece(f"{prefix}BL", "BorderLeft", gold, x, y + border_px, border_px, h - 2 * border_px, ba)
        piece(f"{prefix}BR", "BorderRight", gold, x + w - border_px, y + border_px, border_px, h - 2 * border_px, ba)
    if with_bar:
        piece(f"{prefix}Bar", "AccentBar", gold, bar[0], bar[1], bar[2], bar[3], 100.0)
    return "\n".join(out)


# ----------------------------------------------------------------------------- EffectCraft
def run_jsx_and_export(style, jsx, out_dir, base_name, comp_title, props, dry=False):
    """Run JSX (which must writeLn ECPROJ_SAVED after saving base_name.ecproj), expose props, export template.
    props = [(layer_name, property_label)]."""
    os.makedirs(out_dir, exist_ok=True)
    proj = os.path.normpath(os.path.join(out_dir, base_name + ".ecproj"))
    tmpl = os.path.normpath(os.path.join(out_dir, base_name + ".ectemplate"))
    jsx = jsx.replace("__PROJ_PATH__", proj.replace("\\", "/"))
    jsx_path = os.path.join(out_dir, "_temp_build.jsx")
    with open(jsx_path, "w", encoding="utf-8") as f:
        f.write(jsx)
    cli = style["toolchain"]["effectcraft_cli"]
    if dry:
        os.remove(jsx_path)
        return None
    res = subprocess.run([cli, "script", jsx_path], capture_output=True, text=True)
    if "ECPROJ_SAVED" not in res.stdout:
        raise SystemExit("JSX error: " + (res.stderr or res.stdout))
    os.remove(jsx_path)
    subprocess.run([cli, "--project", proj, "--save", "exec", "essential.setName", "--params", json.dumps({"comp": 1, "name": comp_title})], check=True, capture_output=True)
    for layer, label in props:
        subprocess.run([cli, "--project", proj, "--save", "exec", "essential.addProperty", "--params",
                        json.dumps({"comp": 1, "layer": layer, "path": "text/sourceText", "name": label})], check=True, capture_output=True)
    subprocess.run([cli, "--project", proj, "exec", "essential.exportTemplate", "--params",
                    json.dumps({"comp": 1, "path": tmpl, "name": comp_title})], check=True, capture_output=True)
    return proj, tmpl


def common_args(description):
    import argparse

    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--style", default=None, help="style.json (default: ../style.json)")
    ap.add_argument("--values", default=None, help="values JSON (text is measured to size plates / wrap lines)")
    ap.add_argument("--out-dir", default=None, help="where .ecproj/.ectemplate go (default: this folder)")
    ap.add_argument("--emit-values", default=None, help="write the resolved values JSON (wrapped text) here for render")
    ap.add_argument("--dry", action="store_true", help="measure + generate JSX only; do not call EffectCraft")
    return ap


def read_values(path, defaults):
    vals = dict(defaults)
    if path:
        with open(path, "r", encoding="utf-8") as f:
            vals.update(json.load(f))
    return vals


def write_values(path, values):
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(values, f, ensure_ascii=False, indent=2)
