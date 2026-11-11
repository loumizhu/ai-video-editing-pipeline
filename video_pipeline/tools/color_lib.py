"""Colour-script library (COLOR_SCRIPT.md). Pure numpy/PIL; FilmCraft only for measured per-look LUTs.

Looks are OFFSETS from the house grade (presets/documentary-default/style.json grade.*), in FilmCraft Lumetri units
(see presets/color/color_rules.json _comment for what one unit does, measured on a gray ramp 2026-11-09).

Main pieces
  validate_script()      structural + rule checks of the agent-written color_script.json (phases by BEAT id, never timecodes)
  phase_times()          beat ids -> seconds (code maps beats to time; the AI never writes a timecode)
  shot_look()            phase offsets -> per-shot offsets: stepped blend at cuts, protection (faces, documents, archival,
                         B&W), cast normalisation, owner/agent grade_adjust; every change is logged with a reason
  to_lumetri()/fcpreset  offsets + house grade -> FilmCraft preset dict (one preset per unique look)
  preview_apply()        analytic preview of a look on an image (coefficients fitted to the 2026-11-09 probes)
  measure_lut()          exact per-look 3D LUT measured through FilmCraft's own Lumetri (also a Resolve LUT)
  image_stats()          luma / Lab / clipping / cast / B&W / RMS contrast / faces (OpenCV Haar, optional)
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from typing import Any

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
VP = os.path.dirname(HERE)
RULES_PATH = os.path.join(VP, "presets", "color", "color_rules.json")
STYLE_PATH = os.path.join(VP, "presets", "documentary-default", "style.json")
GRADE_DIR = os.path.join(VP, "presets", "documentary-default", "grade")
LUMA709 = np.array([0.2126, 0.7152, 0.0722])

NUMERIC = ("temperature", "tint", "saturation", "contrast", "blacks", "fade", "grain", "vignette", "exposure")
CARD_ALIASES = {"temp": "temperature", "sat": "saturation", "blacks_lift": "blacks", "faded_film": "fade"}
SPLIT_LEVELS_PER_TINT = 70.0   # tint 0.1 off neutral -> 7 levels at the end of the ramp (probe 2026-11-09)


# ----------------------------------------------------------------------------- io
def load_json(p: str) -> Any:
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def load_rules(p: str | None = None) -> dict:
    return load_json(p or RULES_PATH)


def house_grade(style_path: str | None = None) -> dict:
    return load_json(style_path or STYLE_PATH)["grade"]


# ----------------------------------------------------------------------------- colour maths
def hex_rgb(h: str) -> np.ndarray:
    h = h.strip().lstrip("#")
    if len(h) != 6:
        raise ValueError(f"bad hex colour {h!r}")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)


def srgb_to_lab(rgb255: np.ndarray) -> np.ndarray:
    c = np.clip(np.asarray(rgb255, dtype=float) / 255.0, 0, 1)
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
    xyz = c @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], axis=-1)


def delta_e(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.linalg.norm(srgb_to_lab(a) - srgb_to_lab(b), axis=-1)


def wcag_contrast(a: np.ndarray, b: np.ndarray) -> float:
    def rl(c):
        c = np.asarray(c, float) / 255.0
        c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
        return float(c @ LUMA709)
    la, lb = sorted((rl(a), rl(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def hue_deg(rgb255: np.ndarray) -> np.ndarray:
    lab = srgb_to_lab(rgb255)
    return np.degrees(np.arctan2(lab[..., 2], lab[..., 1])) % 360


def rgb_hue_deg(rgb255: np.ndarray) -> float:
    """HSV hue (what the Lumetri HSL qualifier keys on)."""
    r, g, b = (np.asarray(rgb255, float) / 255.0).tolist()
    mx, mn = max(r, g, b), min(r, g, b)
    if mx - mn < 1e-6:
        return 0.0
    if mx == r:
        h = ((g - b) / (mx - mn)) % 6
    elif mx == g:
        h = (b - r) / (mx - mn) + 2
    else:
        h = (r - g) / (mx - mn) + 4
    return float(h * 60.0)


def tone_vector(hex_or_none: str | None, levels: float) -> np.ndarray:
    """Split-tone hex -> per-channel shift (levels at the extreme of the ramp). Only the hue of the hex matters; its
    strength is `levels` (the largest channel shift)."""
    if not hex_or_none or levels <= 0:
        return np.zeros(3)
    c = hex_rgb(hex_or_none)
    c = c - c.mean()
    m = np.abs(c).max()
    return np.zeros(3) if m < 1e-6 else c / m * float(levels)


# ----------------------------------------------------------------------------- reference chart (delta-E budget)
def reference_chart() -> np.ndarray:
    """Neutral ramp + skin tones + soft primaries + a typical archival sepia: what 'how strong is this look' is judged on."""
    ramp = [[v, v, v] for v in (16, 40, 70, 100, 128, 160, 190, 220, 240)]
    skin = [[224, 172, 140], [198, 134, 103], [141, 85, 60], [90, 56, 38]]
    prim = [[170, 60, 55], [60, 120, 70], [60, 80, 150], [200, 170, 60], [90, 150, 160], [140, 90, 140]]
    sepia = [[112, 94, 72], [180, 160, 128], [60, 50, 40]]
    return np.array(ramp + skin + prim + sepia, dtype=float)


# ----------------------------------------------------------------------------- offsets
def normalize_card(card: dict) -> dict:
    """Card fields (their names or ours) -> canonical offsets dict."""
    o: dict[str, Any] = {}
    for k, v in card.items():
        k2 = CARD_ALIASES.get(k, k)
        if k2 in NUMERIC and v is not None:
            o[k2] = float(v)
    o["shadow_tone"] = card.get("shadow_tone")
    o["highlight_tone"] = card.get("highlight_tone")
    o["split_levels"] = float(card.get("split_levels", 0) or 0)
    return o


def zero_offsets() -> dict:
    return {**{k: 0.0 for k in NUMERIC}, "shadow_vec": [0.0, 0.0, 0.0], "highlight_vec": [0.0, 0.0, 0.0], "motif_hue": None, "motif_sat": 100.0}


def to_internal(o: dict) -> dict:
    z = zero_offsets()
    for k in NUMERIC:
        z[k] = float(o.get(k, 0.0) or 0.0)
    lv = float(o.get("split_levels", 0) or 0)
    z["shadow_vec"] = tone_vector(o.get("shadow_tone"), lv).tolist()
    z["highlight_vec"] = tone_vector(o.get("highlight_tone"), lv).tolist()
    return z


def clamp_internal(z: dict, caps: dict) -> tuple[dict, list[str]]:
    out, log = copy.deepcopy(z), []
    for k in ("temperature", "tint", "saturation", "contrast", "blacks", "fade", "vignette", "grain"):
        cap = caps.get(k)
        if cap is None:
            continue
        v = out[k]
        c = max(-cap, min(cap, v))
        if abs(c - v) > 1e-9:
            log.append(f"{k} {v:+g} clamped to {c:+g}")
            out[k] = c
    lv = caps.get("split_levels")
    for key in ("shadow_vec", "highlight_vec"):
        v = np.array(out[key])
        m = np.abs(v).max() if v.size else 0
        if lv is not None and m > lv + 1e-9:
            log.append(f"{key} {m:.1f} levels clamped to {lv}")
            out[key] = (v / m * lv).tolist()
    if out.get("motif_hue") is not None and caps.get("motif_sat"):
        if out["motif_sat"] > caps["motif_sat"]:
            log.append(f"motif_sat {out['motif_sat']:g} clamped to {caps['motif_sat']}")
            out["motif_sat"] = float(caps["motif_sat"])
    return out, log


def lerp_internal(a: dict, b: dict, w: float) -> dict:
    out = zero_offsets()
    for k in NUMERIC:
        out[k] = a[k] + (b[k] - a[k]) * w
    for k in ("shadow_vec", "highlight_vec"):
        out[k] = (np.array(a[k]) + (np.array(b[k]) - np.array(a[k])) * w).tolist()
    # motif: fade strength, keep the hue of whichever side has one
    ha, hb = a.get("motif_hue"), b.get("motif_hue")
    sa = a.get("motif_sat", 100.0) if ha is not None else 100.0
    sb = b.get("motif_sat", 100.0) if hb is not None else 100.0
    out["motif_hue"] = hb if (w >= 0.5 and hb is not None) or ha is None else ha
    out["motif_sat"] = sa + (sb - sa) * w if out["motif_hue"] is not None else 100.0
    return out


def scale_internal(z: dict, s: float) -> dict:
    """Every offset times s (over-grade check: s = 0.7)."""
    return lerp_internal(zero_offsets(), z, s) if s != 1 else copy.deepcopy(z)


def round_internal(z: dict) -> dict:
    out = copy.deepcopy(z)
    for k in NUMERIC:
        out[k] = round(out[k], 2)
    for k in ("shadow_vec", "highlight_vec"):
        out[k] = [round(x, 2) for x in out[k]]
    out["motif_sat"] = round(out["motif_sat"], 1)
    if out["motif_hue"] is not None:
        out["motif_hue"] = round(out["motif_hue"], 1)
    return out


def look_key(z: dict) -> str:
    return hashlib.sha1(json.dumps(round_internal(z), sort_keys=True).encode()).hexdigest()[:8]


# ----------------------------------------------------------------------------- protection
def protect(z: dict, roles: set[str], rules: dict, options: dict) -> tuple[dict, list[str]]:
    """Scale a shot's offsets for faces, documents, archival material and black-and-white sources."""
    pr = rules["protection"]
    out, log = copy.deepcopy(z), []
    chroma = 1.0
    if "face" in roles:
        chroma = min(chroma, pr["face"]["chroma"])
        lo, hi = pr["face"]["saturation_min"], pr["face"]["saturation_max"]
        if not lo <= out["saturation"] <= hi:
            log.append(f"face: saturation {out['saturation']:+.1f} held to [{lo},{hi}]")
            out["saturation"] = min(hi, max(lo, out["saturation"]))
    if "document" in roles:
        d = pr["document"]
        chroma = min(chroma, d["chroma"])
        if out["contrast"] < d["contrast_min"]:
            log.append(f"document: contrast {out['contrast']:+.1f} -> {d['contrast_min']} (a grade never lowers text contrast)")
            out["contrast"] = float(d["contrast_min"])
        for k, cap in (("blacks", d["blacks_max"]), ("fade", d["fade_max"])):
            if out[k] > cap:
                log.append(f"document: {k} {out[k]:+.1f} -> {cap}")
                out[k] = float(cap)
        out["saturation"] = min(d["saturation_max"], max(d["saturation_min"], out["saturation"]))
    if "archival" in roles:
        a = pr["archival"].get(options.get("era", "faithful_archival"), {})
        chroma = min(chroma, a.get("chroma", 1.0))
        for k in ("contrast", "saturation"):
            if k in a:
                out[k] *= a[k]
        if "grain_max" in a and out["grain"] > a["grain_max"]:
            out["grain"] = float(a["grain_max"])
            log.append("archival: no added grain (the source already has it)")
    if "bw" in roles:
        b = pr["bw_source"].get(options.get("bw", "neutral"), {"chroma": 0.0})
        chroma = min(chroma, b.get("chroma", 0.0))
        out["saturation"] = 0.0
        out["motif_hue"], out["motif_sat"] = None, 100.0
        if "fixed_temperature" in b:
            out["temperature"] = float(b["fixed_temperature"])
            log.append(f"b&w source: fixed {options.get('bw')} tone (temperature {b['fixed_temperature']:+d})")
            chroma_temp_done = True
        else:
            chroma_temp_done = False
    else:
        chroma_temp_done = False
    if chroma < 1.0:
        if not chroma_temp_done:
            out["temperature"] *= chroma
        out["tint"] *= chroma
        out["shadow_vec"] = (np.array(out["shadow_vec"]) * chroma).tolist()
        out["highlight_vec"] = (np.array(out["highlight_vec"]) * chroma).tolist()
        if out["motif_hue"] is not None:
            out["motif_sat"] = 100.0 + (out["motif_sat"] - 100.0) * chroma
        log.append(f"chroma offsets x{chroma:g} ({', '.join(sorted(roles))})")
    return out, log


# ----------------------------------------------------------------------------- house + offsets -> Lumetri
def to_lumetri(house: dict, z: dict) -> dict:
    """Absolute FilmCraft values: house grade + offsets. Returns {'lumetri': {...}, 'noise': {...}, 'vignette': {...}}."""
    lum = dict(house["lumetri"])
    lum["temperature"] = lum.get("temperature", 0.0) + z["temperature"]
    lum["tint"] = lum.get("tint", 0.0) + z["tint"]
    lum["saturation"] = lum.get("saturation", 100.0) * (1.0 + z["saturation"] / 100.0)
    lum["contrast"] = lum.get("contrast", 0.0) + z["contrast"]
    lum["blacks"] = lum.get("blacks", 0.0) + z["blacks"]
    lum["exposure"] = lum.get("exposure", 0.0) + z["exposure"]
    lum["faded_film"] = max(0.0, z["fade"])
    lum["shadow_tint"] = [float(np.clip(0.5 + v / SPLIT_LEVELS_PER_TINT, 0, 1)) for v in z["shadow_vec"]] + [1.0]
    lum["highlight_tint"] = [float(np.clip(0.5 + v / SPLIT_LEVELS_PER_TINT, 0, 1)) for v in z["highlight_vec"]] + [1.0]
    if z.get("motif_hue") is not None and abs(z.get("motif_sat", 100.0) - 100.0) > 0.5:
        lum["hsl_on"] = True
        lum["hsl_hue"] = float(z["motif_hue"])
        lum["hsl_sat"] = float(z["motif_sat"])
    else:
        lum["hsl_on"] = False
    noise = dict(house["noise"])
    noise["amount"] = max(0.0, noise.get("amount", 0.0) + z["grain"])
    vig = dict(house["vignette"])
    vig["amount"] = vig.get("amount", 0.0) - z["vignette"]   # card vignette +6 = 6 more units of darkening
    return {"lumetri": lum, "noise": noise, "vignette": vig}


def _set(param: dict, v: Any) -> None:
    kind = next(iter(param["value"]))
    if kind == "Float":
        param["value"] = {"Float": float(v)}
    elif kind == "Bool":
        param["value"] = {"Bool": bool(v)}
    elif kind == "Color":
        param["value"] = {"Color": [float(x) for x in v]}
    else:
        param["value"] = {kind: v}


def fcpreset(template: dict, name: str, values: dict, lumetri_only: bool = False) -> dict:
    """Clone the house .fcpreset and write the look's absolute values into it."""
    p = copy.deepcopy(template)
    pr = p["presets"][0]
    pr["name"] = name
    if lumetri_only:
        pr["effects"] = [e for e in pr["effects"] if e["effect"] == "lumetri"]
    for fx in pr["effects"]:
        vals = values.get(fx["effect"], {})
        for k, v in vals.items():
            if k in fx["params"]:
                _set(fx["params"][k], v)
    return p


def house_template() -> dict | None:
    p = os.path.join(GRADE_DIR, "house-style.fcpreset")
    return load_json(p) if os.path.exists(p) else None


# ----------------------------------------------------------------------------- analytic preview
def preview_apply(rgb255: np.ndarray, house: dict, z: dict, vignette: bool = True) -> np.ndarray:
    """Approximate the FilmCraft Lumetri look (house + offsets) on an sRGB image (H,W,3 or N,3; 0..255 float).
    Coefficients fitted to single-parameter gray-ramp probes through FilmCraft (2026-11-09); per-parameter error about
    1 level. It ignores grain. Use measure_lut() for an exact look when FilmCraft is available."""
    v = to_lumetri(house, z)
    L_ = v["lumetri"]
    x = np.asarray(rgb255, dtype=float).copy()
    if L_.get("exposure"):
        g = 2.0 ** (0.5 * L_["exposure"])   # probe: exposure 0.5 -> +22 at 128
        x = np.clip(x * g, 0, 255)                 # probe: 240 -> 255 (+15), i.e. a plain gain that clips
    t, ti = L_.get("temperature", 0.0), L_.get("tint", 0.0)
    x[..., 0] *= 1 + 0.00156 * t
    x[..., 2] *= 1 - 0.00156 * t
    x[..., 1] *= 1 - 0.00156 * ti
    c, b, f = L_.get("contrast", 0.0), L_.get("blacks", 0.0), L_.get("faded_film", 0.0)
    x = x + 0.27 * c * np.sin(np.pi * (np.clip(x, 0, 255) - 128) / 128) + 0.45 * b * (1 - np.clip(x, 0, 255) / 255) + 0.29 * f * (128 - x) / 128
    x = np.clip(x, 0, 255)
    Lm = (x * LUMA709).sum(-1, keepdims=True) / 255.0
    sv = (np.array(L_["shadow_tint"][:3]) - 0.5) * SPLIT_LEVELS_PER_TINT
    hv = (np.array(L_["highlight_tint"][:3]) - 0.5) * SPLIT_LEVELS_PER_TINT
    x = x + (1 - Lm) * sv + Lm * hv
    Ly = (x * LUMA709).sum(-1, keepdims=True)
    x = Ly + (L_.get("saturation", 100.0) / 100.0) * (x - Ly)
    if L_.get("hsl_on"):
        flat = x.reshape(-1, 3)
        mx, mn = flat.max(1), flat.min(1)
        d = np.maximum(mx - mn, 1e-6)
        r, g_, bb = flat[:, 0], flat[:, 1], flat[:, 2]
        h = np.where(mx == r, ((g_ - bb) / d) % 6, np.where(mx == g_, (bb - r) / d + 2, (r - g_) / d + 4)) * 60
        dist = np.abs((h - L_["hsl_hue"] + 180) % 360 - 180)
        rng = 30.0
        w = np.clip(1 - np.maximum(dist - rng / 2, 0) / 20.0, 0, 1) * (d > 12)
        Lf = (flat * LUMA709).sum(1, keepdims=True)
        flat = Lf + (1 + (L_["hsl_sat"] / 100.0 - 1) * w[:, None] * 0.7) * (flat - Lf)
        x = flat.reshape(x.shape)
    if vignette and x.ndim == 3:
        hgt, wid = x.shape[:2]
        yy, xx = np.mgrid[0:hgt, 0:wid]
        r2 = (((xx - wid / 2) / (wid / 2)) ** 2 + ((yy - hgt / 2) / (hgt / 2)) ** 2) / 2
        x = x * (1 + v["vignette"]["amount"] / 100.0 * 0.9 * r2)[..., None]
    return np.clip(x, 0, 255)


# ----------------------------------------------------------------------------- measured LUT (FilmCraft)
def filmcraft_available() -> bool:
    return os.path.exists(r"C:\Program Files\FilmCraft\filmcraft-cli.exe")


def measure_lut(preset_dict: dict, workdir: str, size: int = 17) -> np.ndarray:
    """Push a size^3 patch grid through FilmCraft's own Lumetri (lumetri-only preset) and return the LUT
    (size,size,size,3) in 0..255, index [r,g,b]. Readout is 8-bit (+/-0.5 level)."""
    import sys
    from PIL import Image
    sys.path.insert(0, GRADE_DIR)
    import build_grade as G  # noqa: E402  (FilmCraft helpers: fresh zz_test project, same-run import+apply, EXR readout)

    os.makedirs(workdir, exist_ok=True)
    P, w, h = 16, 1920, 1080
    cols = w // P
    lv = np.linspace(0, 255, size)
    grid = np.stack(np.meshgrid(lv, lv, lv, indexing="ij"), -1).reshape(-1, 3)
    img = np.zeros((h, w, 3), np.uint8)
    pos = []
    for k, rgb in enumerate(grid):
        r, c = divmod(k, cols)
        y0, x0 = r * P, c * P
        img[y0:y0 + P, x0:x0 + P] = np.round(rgb).astype(np.uint8)
        pos.append((y0 + P // 2, x0 + P // 2))
    chart = os.path.join(workdir, "lut_chart.png")
    Image.fromarray(img).save(chart)
    out = G.push_through_preset(chart, preset_dict, w, h, workdir)
    vals = np.array([out[y - 4:y + 4, x - 4:x + 4].reshape(-1, 3).mean(0) for y, x in pos])
    return vals.reshape(size, size, size, 3)


def apply_lut(rgb255: np.ndarray, lut: np.ndarray) -> np.ndarray:
    """Trilinear 3D LUT lookup (lut index [r,g,b], values 0..255)."""
    n = lut.shape[0]
    x = np.clip(np.asarray(rgb255, float), 0, 255) / 255.0 * (n - 1)
    i0 = np.clip(np.floor(x).astype(int), 0, n - 2)
    f = x - i0
    out = np.zeros_like(x)
    for dr in (0, 1):
        for dg in (0, 1):
            for db in (0, 1):
                w = (f[..., 0] if dr else 1 - f[..., 0]) * (f[..., 1] if dg else 1 - f[..., 1]) * (f[..., 2] if db else 1 - f[..., 2])
                out += w[..., None] * lut[i0[..., 0] + dr, i0[..., 1] + dg, i0[..., 2] + db]
    return out


def write_cube(path: str, lut: np.ndarray, title: str) -> None:
    n = lut.shape[0]
    lines = [f'TITLE "{title}"', f"LUT_3D_SIZE {n}", "DOMAIN_MIN 0.0 0.0 0.0", "DOMAIN_MAX 1.0 1.0 1.0"]
    for b in range(n):          # .cube order: red fastest
        for g in range(n):
            for r in range(n):
                v = np.clip(lut[r, g, b] / 255.0, 0, 1)
                lines.append(f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
    with open(path, "w", encoding="ascii") as f:
        f.write("\n".join(lines) + "\n")


def read_cube(path: str) -> np.ndarray:
    n, rows = 0, []
    with open(path, encoding="ascii") as f:
        for ln in f:
            s = ln.split()
            if not s or s[0].startswith("#"):
                continue
            if s[0] == "LUT_3D_SIZE":
                n = int(s[1])
            elif len(s) == 3:
                try:
                    rows.append([float(t) for t in s])
                except ValueError:
                    pass
    a = np.array(rows).reshape(n, n, n, 3) * 255.0      # [b][g][r]
    return np.transpose(a, (2, 1, 0, 3))


# ----------------------------------------------------------------------------- image stats
def load_image(path: str, max_side: int = 480) -> np.ndarray:
    from PIL import Image
    im = Image.open(path)
    im.draft("RGB", (max_side, max_side))
    im = im.convert("RGB")
    im.thumbnail((max_side, max_side))
    return np.asarray(im, dtype=float)


def detect_faces(rgb: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Frontal faces (x, y, w, h) with OpenCV's Haar cascade. Returns [] when OpenCV (opencv-python) is not usable:
    the shot-plan `subject` field (portrait, person, face...) then decides the face role on its own."""
    try:
        import cv2
        g = (rgb @ LUMA709).astype(np.uint8)
        casc = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
        if casc.empty():
            return []
        m = max(24, int(min(g.shape) * 0.08))
        return [tuple(int(v) for v in r) for r in casc.detectMultiScale(g, 1.1, 6, minSize=(m, m))]
    except Exception:
        return []


def face_detection_available() -> bool:
    try:
        import cv2
        return not cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")).empty()
    except Exception:
        return False


def image_stats(rgb: np.ndarray, rules: dict | None = None) -> dict:
    rules = rules or load_rules()
    nz = rules["normalize"]
    flat = rgb.reshape(-1, 3)
    luma = flat @ LUMA709
    lab = srgb_to_lab(flat)
    chroma = np.hypot(lab[:, 1], lab[:, 2])
    sel = (chroma < nz["neutral_chroma"]) & (luma > 40) & (luma < 215)
    share = float(sel.mean())
    cast = {"r_minus_b": 0.0, "g_minus_rb": 0.0, "neutral_share": share}
    if share >= nz["min_neutral_share"]:
        m = flat[sel].mean(0)
        cast["r_minus_b"] = float(m[0] - m[2])
        cast["g_minus_rb"] = float(m[1] - (m[0] + m[2]) / 2)
    hue_ok = chroma > 3
    toned_mono = False
    if hue_ok.mean() > 0.2:
        ang = np.arctan2(lab[hue_ok, 2], lab[hue_ok, 1])
        R = float(np.hypot(np.cos(ang).mean(), np.sin(ang).mean()))
        toned_mono = bool(R > 0.9 and chroma.mean() < 18)   # sepia / cyanotype / toned print: one hue only
    return {
        "toned_mono": toned_mono,
        "luma_p5": float(np.percentile(luma, 5)), "luma_p50": float(np.percentile(luma, 50)), "luma_p95": float(np.percentile(luma, 95)),
        "luma_rms": float(luma.std()), "mean_rgb": flat.mean(0).round(2).tolist(), "mean_lab": lab.mean(0).round(2).tolist(),
        "chroma_mean": float(chroma.mean()), "is_bw": bool(chroma.mean() < rules["protection"]["bw_detect_chroma"]),
        "clip_low": float((flat.min(1) <= 1).mean() * 100), "clip_high": float((flat.max(1) >= 254).mean() * 100),   # any channel clipped loses detail (a tinted blown highlight counts)
        "cast": cast,
    }


def cast_correction(stats: dict, rules: dict) -> tuple[float, float, str | None]:
    """Counter-offsets (temperature, tint) for a measured colour cast; (0, 0, None) when there is none to correct."""
    nz = rules["normalize"]
    c = stats["cast"]
    if c["neutral_share"] < nz["min_neutral_share"]:
        return 0.0, 0.0, None
    rb, g = c["r_minus_b"], c["g_minus_rb"]
    t = ti = 0.0
    if abs(rb) > nz["cast_threshold_levels"]:
        t = max(-nz["max_temperature"], min(nz["max_temperature"], -rb * nz["strength"] * nz["temperature_per_level"]))
    if abs(g) > nz["cast_threshold_levels"]:
        ti = max(-nz["max_tint"], min(nz["max_tint"], g * nz["strength"] * nz["tint_per_level"]))
    if t == 0 and ti == 0:
        return 0.0, 0.0, None
    return t, ti, f"cast R-B {rb:+.1f}, G-RB {g:+.1f} levels on neutral pixels -> temperature {t:+.1f}, tint {ti:+.1f}"


def look_strength(house: dict, z: dict) -> float:
    """Mean dE of the reference chart: look vs house (how nameable the look is)."""
    ch = reference_chart()
    return float(delta_e(preview_apply(ch, house, z, vignette=False), preview_apply(ch, house, zero_offsets(), vignette=False)).mean())


def look_distance(house: dict, a: dict, b: dict) -> float:
    ch = reference_chart()
    return float(delta_e(preview_apply(ch, house, a, vignette=False), preview_apply(ch, house, b, vignette=False)).mean())


# ----------------------------------------------------------------------------- beats -> time
def beat_times_from_beats(beats: list[dict]) -> dict[str, tuple[float, float]]:
    return {b["id"]: (float(b["start"]), float(b["end"])) for b in beats if "id" in b}


def beat_times_from_shot_plan(slots: list[dict]) -> dict[str, tuple[float, float]]:
    out: dict[str, list[float]] = {}
    for s in slots:
        if isinstance(s.get("pipeline_ext"), dict):   # Vcut 3.3 nesting, same as pacing_lib
            s = {**s, **s["pipeline_ext"]}
        bid = s.get("beat_id") or s.get("beat_ref")
        if not bid:
            continue
        if "start_ms" in s:
            a, b = s["start_ms"] / 1000.0, s["end_ms"] / 1000.0
        elif "start_s" in s:
            a, b = float(s["start_s"]), float(s["end_s"])
        else:
            continue
        r = out.setdefault(str(bid), [a, b])
        r[0], r[1] = min(r[0], a), max(r[1], b)
    return {k: (v[0], v[1]) for k, v in out.items()}


def phase_times(phases: list[dict], bt: dict[str, tuple[float, float]]) -> list[tuple[float, float]]:
    return [(bt[p["from_beat"]][0], bt[p["to_beat"]][1]) for p in phases]
