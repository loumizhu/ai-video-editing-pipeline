"""Regenerate the house grade artifacts from style.json `grade.*` (the bake skill calls this after any grade edit).

  house-style.fcpreset : FilmCraft preset (lumetri + noise + vignette) written from style.json numbers
  house-look.cube      : 3D LUT (float, LUT_3D_SIZE from style.json) for FilmCraft `lumetri.setInputLut` and Resolve `SetLUT`
  calibration_report.json : fit quality of the LUT against FilmCraft's own Lumetri

How the LUT is built (so it is float, not 8-bit sampled):
  FilmCraft's pipeline output is 8-bit, so sampling a LUT directly from renders would give 1/255 steps.
  Instead the script pushes a gray ramp (256 levels) and 3,000 random colour patches through FilmCraft's Lumetri
  with the SAME numbers (headless, fresh zz_test_* project, EXR float readout), then fits a model:
    stage P  per-channel curves  (exposure, contrast, blacks, whites, temperature, tint: probed, they act per channel)
    stage B  luma-ratio gain     (highlights, shadows: probed, they scale RGB by T(luma)/luma)
    stage S  saturation s about Rec.709 luma (s fitted by least squares on the colour patches)
  Each stage's curve is a smoothing spline over the 256 ramp samples of a sub-preset that holds only that stage's numbers.
  The stage order (P->B or B->P) is chosen by held-out error. The model is evaluated on the LUT grid in float and
  validated on 3,000 held-out patches (calibration_report.json).

  python build_grade.py [--style ../style.json] [--no-calibrate]   (--no-calibrate: only rewrite the .fcpreset)
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import uuid

import numpy as np
from PIL import Image
from scipy.interpolate import UnivariateSpline

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import _common as C  # noqa: E402

FILMCRAFT = r"C:\Program Files\FilmCraft\filmcraft-cli.exe"
FCPRESET = os.path.join(HERE, "house-style.fcpreset")
CUBE = os.path.join(HERE, "house-look.cube")
LUMA709 = np.array([0.2126, 0.7152, 0.0722])
PRESET_NAME = "HouseStyle_Documentary"


# ------------------------------------------------------------------ fcpreset
def build_fcpreset(style):
    """Return the preset dict: keeps every untouched Lumetri/noise/vignette param from the file on disk, overwrites the numbers."""
    g = style["grade"]
    with open(FCPRESET, "r", encoding="utf-8") as f:
        preset = json.load(f)
    p = preset["presets"][0]
    p["name"] = PRESET_NAME
    for fx in p["effects"]:
        name = fx["effect"]
        if name == "lumetri":
            for k, v in g["lumetri"].items():
                fx["params"][k]["value"] = {"Float": float(v)}
        elif name == "noise":
            n = g["noise"]
            fx["params"]["amount"]["value"] = {"Float": float(n["amount"])}
            fx["params"]["color"]["value"] = {"Bool": bool(n["color"])}
            fx["params"]["grain_size"]["value"] = {"Float": float(n["grain_size"])}
        elif name == "vignette":
            vg = g["vignette"]
            for k in ("amount", "midpoint", "feather", "roundness"):
                fx["params"][k]["value"] = {"Float": float(vg[k])}
    return preset


def lumetri_only(preset):
    import copy

    p = copy.deepcopy(preset)
    p["presets"][0]["name"] = "HouseStyle_CalibLumetri"
    p["presets"][0]["effects"] = [e for e in p["presets"][0]["effects"] if e["effect"] == "lumetri"]
    return p


# ------------------------------------------------------------------ FilmCraft helpers
def fc(args, cwd=None, check=True):
    r = subprocess.run([FILMCRAFT] + args, capture_output=True, text=True, cwd=cwd)
    if check and r.returncode:
        raise SystemExit(f"filmcraft-cli {' '.join(args[:4])} failed:\n{r.stdout[-600:]}\n{r.stderr[-600:]}")
    return r


def read_exr(path, w, h):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "gbrpf32le", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype="<f4").reshape(3, h, w)
    return np.stack([a[2], a[0], a[1]], axis=-1)


def oetf(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def push_through_preset(image_path, preset_dict, w, h, workdir):
    """Fresh zz_test_* project -> still on V1 -> presets.import + presets.apply in ONE run -> EXR float readout (display-encoded, 0..255 floats)."""
    proj = os.path.join(workdir, "zz_test_grade_" + uuid.uuid4().hex[:8] + ".fcproj")
    fc(["--save-as", proj, "exec", "file.newProject", json.dumps({"name": "zz_test_grade"})])
    fc(["--project", proj, "--save", "exec", "file.newSequence", json.dumps({"name": "s", "width": w, "height": h, "fps": 24, "sampleRate": 48000, "video": 4, "audio": 2, "mix": "Stereo"})])
    item = json.loads(fc(["--project", proj, "--save", "import", image_path]).stdout)["items"][0]
    clip = json.loads(fc(["--project", proj, "--save", "exec", "timeline.place", json.dumps({"item": item, "track": "V1", "seconds": 0, "duration": {"seconds": 2.0}, "insert": False})]).stdout)["clips"][0]
    pre = os.path.join(workdir, "calib.fcpreset")
    with open(pre, "w", encoding="utf-8") as f:
        json.dump(preset_dict, f)
    name = preset_dict["presets"][0]["name"]
    exr = os.path.join(workdir, "out.exr").replace("\\", "/")
    lines = [
        {"id": "presets.import", "params": {"path": pre.replace("\\", "/")}},
        {"id": "presets.apply", "params": {"preset": name, "clips": [clip]}},
        {"id": "file.exportMedia", "params": {"path": exr, "format": "exr", "range": "custom", "startSeconds": 0.5, "endSeconds": 0.5417, "wait": True}},
    ]
    jl = os.path.join(workdir, "run.jsonl")
    with open(jl, "w") as f:
        for l in lines:
            f.write(json.dumps(l) + "\n")
    for old in os.listdir(workdir):
        if old.startswith("out") and old.endswith(".exr"):
            os.remove(os.path.join(workdir, old))
    fc(["--project", proj, "run", jl])
    return oetf(read_exr(os.path.join(workdir, "out000.exr"), w, h)) * 255.0


# ------------------------------------------------------------------ chart
RAMP_Y, PATCH_Y0, PATCH = 40, 140, 24
RAMP_W = 7


def make_chart(path, seed, n_patches=3000, w=1920, h=1080):
    rng = np.random.default_rng(seed)
    cols = w // PATCH
    patches = rng.integers(0, 256, size=(n_patches, 3)).astype(np.uint8)
    img = np.zeros((h, w, 3), np.uint8)
    for i in range(256):
        img[RAMP_Y - 20: RAMP_Y + 20, i * RAMP_W:(i + 1) * RAMP_W, :] = i
    pos = []
    for k, rgb in enumerate(patches):
        r, c = divmod(k, cols)
        y, x = PATCH_Y0 + r * PATCH, c * PATCH
        img[y:y + PATCH, x:x + PATCH, :] = rgb
        pos.append((y + PATCH // 2, x + PATCH // 2))
    Image.fromarray(img).save(path)
    return patches.astype(float), pos


def read_chart(out, pos):
    ramp = np.array([out[RAMP_Y, i * RAMP_W + RAMP_W // 2, :] for i in range(256)])
    patches = np.array([out[y - 3:y + 4, x - 3:x + 4, :].reshape(-1, 3).mean(axis=0) for y, x in pos])
    return ramp, patches


# ------------------------------------------------------------------ model
NEUTRAL = {"exposure": 0.0, "contrast": 0.0, "highlights": 0.0, "shadows": 0.0, "whites": 0.0, "blacks": 0.0, "saturation": 100.0, "temperature": 0.0, "tint": 0.0}
STAGE_P = ("exposure", "contrast", "blacks", "whites", "temperature", "tint")
STAGE_B = ("highlights", "shadows")


def sub_preset(preset, keys, include_sat=False):
    """lumetri-only preset where only `keys` (and optionally saturation) carry the style numbers; the rest are neutral."""
    import copy

    p = lumetri_only(preset)
    for fx in p["presets"][0]["effects"]:
        for k in NEUTRAL:
            full = preset_value(preset, k)
            v = full if (k in keys or (include_sat and k == "saturation")) else NEUTRAL[k]
            fx["params"][k]["value"] = {"Float": float(v)}
    return p


def preset_value(preset, key):
    for fx in preset["presets"][0]["effects"]:
        if fx["effect"] == "lumetri":
            return fx["params"][key]["value"]["Float"]


def fit_curves(ramp):
    """Smoothing spline per channel over the 256-level ramp. 8-bit readout noise sigma = 1/sqrt(12) levels."""
    x = np.arange(256, dtype=float)
    sigma2 = 1.0 / 12.0
    return [UnivariateSpline(x, ramp[:, c], k=3, s=256 * sigma2) for c in range(3)]


def stage_p(curves_p, x):
    return np.clip(np.stack([curves_p[c](x[..., c]) for c in range(3)], axis=-1), 0.0, 255.0)   # engine clamps between stages


def stage_b(curve_b, t):
    L = (t * LUMA709).sum(axis=-1, keepdims=True)
    Lc = np.maximum(L, 1.0)
    return np.clip(t * (curve_b(Lc) / Lc), 0.0, 255.0)


def model_apply(m, rgb255):
    curves_p, curve_b, s, order = m
    t = stage_b(curve_b, stage_p(curves_p, rgb255)) if order == "PB" else stage_p(curves_p, stage_b(curve_b, rgb255))
    L = (t * LUMA709).sum(axis=-1, keepdims=True)
    return L + s * (t - L)


def fit_saturation(m0, patches_in, patches_out):
    curves_p, curve_b, _, order = m0
    t = stage_b(curve_b, stage_p(curves_p, patches_in)) if order == "PB" else stage_p(curves_p, stage_b(curve_b, patches_in))
    L = (t * LUMA709).sum(axis=-1, keepdims=True)
    d_in, d_out = (t - L).ravel(), (patches_out - L).ravel()
    return float((d_in * d_in).sum() and (d_in * d_out).sum() / (d_in * d_in).sum())


def write_cube(path, m, size, title):
    g = np.linspace(0.0, 1.0, size)
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")            # file order: R fastest, then G, then B
    grid = np.stack([r, gg, b], axis=-1).reshape(-1, 3) * 255.0
    out = np.clip(model_apply(m, grid) / 255.0, 0.0, 1.0)
    lines = [f'TITLE "{title}"', f"LUT_3D_SIZE {size}", "DOMAIN_MIN 0.0 0.0 0.0", "DOMAIN_MAX 1.0 1.0 1.0"]
    lines += [f"{a:.8f} {c:.8f} {d:.8f}" for a, c, d in out]
    with open(path, "w", encoding="utf-8") as f:
        f.write(chr(10).join(lines) + chr(10))
    return out


def cube_settings(style):
    return style["grade"]["cube"]["size"], style["grade"]["cube"]["title"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--style", default=os.path.join(HERE, "..", "style.json"))
    ap.add_argument("--no-calibrate", action="store_true")
    ap.add_argument("--out-dir", default=HERE, help="where to write the .fcpreset/.cube/report (default: this folder)")
    a = ap.parse_args()
    style = C.load_style(a.style)
    out_dir = os.path.abspath(a.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    preset = build_fcpreset(style)
    with open(os.path.join(out_dir, "house-style.fcpreset"), "w", encoding="utf-8") as f:
        json.dump(preset, f, indent=2)
    print("wrote", os.path.join(out_dir, "house-style.fcpreset"))
    if a.no_calibrate:
        return
    size, title = cube_settings(style)
    w, h = style["canvas"]["width"], style["canvas"]["height"]
    pP, pB, pF = sub_preset(preset, STAGE_P), sub_preset(preset, STAGE_B), sub_preset(preset, STAGE_P + STAGE_B, include_sat=True)
    with tempfile.TemporaryDirectory(prefix="zz_test_grade_") as wd:
        train_png, hold_png = os.path.join(wd, "train.png"), os.path.join(wd, "hold.png")
        p_in, pos = make_chart(train_png, seed=1)
        q_in, qpos = make_chart(hold_png, seed=2)
        ramp_p, _ = read_chart(push_through_preset(train_png, pP, w, h, wd), pos)
        ramp_b, _ = read_chart(push_through_preset(train_png, pB, w, h, wd), pos)
        _, p_out = read_chart(push_through_preset(train_png, pF, w, h, wd), pos)
        _, q_out = read_chart(push_through_preset(hold_png, pF, w, h, wd), qpos)
    curves_p = fit_curves(ramp_p)
    curve_b = fit_curves(ramp_b)[1]
    best = None
    for order in ("PB", "BP"):
        s = fit_saturation((curves_p, curve_b, 1.0, order), p_in, p_out)
        m = (curves_p, curve_b, s, order)
        err = np.abs(model_apply(m, q_in) - q_out)
        if best is None or err.mean() < best[2].mean():
            best = (m, order, err)
    m, order, hold_err = best
    s = m[2]
    train_err = np.abs(model_apply(m, p_in) - p_out)
    ramp_fit = np.stack([curves_p[c](np.arange(256.0)) for c in range(3)], axis=1)
    report = {
        "style": os.path.abspath(a.style),
        "lumetri": style["grade"]["lumetri"],
        "stage_order": order,
        "saturation_fitted": round(s, 5),
        "saturation_param_pct": style["grade"]["lumetri"]["saturation"],
        "held_out_patches": int(len(q_in)),
        "held_out_abs_err_levels": {"mean": round(float(hold_err.mean()), 3), "p99": round(float(np.percentile(hold_err, 99)), 3), "max": round(float(hold_err.max()), 3)},
        "train_abs_err_levels_mean": round(float(train_err.mean()), 3),
        "stage_p_spline_vs_measured_levels": {"mean": round(float(np.abs(ramp_fit - ramp_p).mean()), 3), "max": round(float(np.abs(ramp_fit - ramp_p).max()), 3)},
        "cube": {"size": size, "decimals": 8},
    }
    gray = np.repeat(np.arange(256.0)[:, None], 3, axis=1)
    gm = model_apply(m, gray)
    report["gray_ramp_model_deviation_from_identity_levels"] = {f"in_{i}": [round(float(v), 2) for v in (gm[i] - i)] for i in (0, 8, 16, 32, 64, 128, 192, 240, 255)}
    out = write_cube(os.path.join(out_dir, "house-look.cube"), m, size, title)
    report["cube"]["black_corner_rgb_255"] = [round(float(v) * 255, 3) for v in out[0]]
    with open(os.path.join(out_dir, "calibration_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps({k: report[k] for k in ("stage_order", "saturation_fitted", "held_out_abs_err_levels", "gray_ramp_model_deviation_from_identity_levels", "cube")}, indent=2))


if __name__ == "__main__":
    main()
