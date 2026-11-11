"""Before/after measurement of the house grade on real frames, through FilmCraft (fresh zz_test_* projects).

For each source frame renders: preset (house-style.fcpreset, full: lumetri+noise+vignette, imported and applied in ONE run),
preset_lumetri (same preset minus noise/vignette) and cube (house-look.cube via lumetri.setInputLut), then reports
Rec.709 luma p5/p50/p95, share of pixels < 8/255, and mean |luma diff| between each pair.

  python measure_grade.py --frames a.png b.png c.png --out-dir DIR [--names bridge bright dark]
Writes DIR/<name>_{before,preset,preset_lumetri,cube}.png and DIR/grade_measurements.json
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
import uuid

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_grade as G  # noqa: E402

W709 = G.LUMA709


def luma(img):
    return (np.asarray(img.convert("RGB"), dtype=float) * W709).sum(axis=2)


def stats(l):
    return {"p5": round(float(np.percentile(l, 5)), 2), "p50": round(float(np.percentile(l, 50)), 2), "p95": round(float(np.percentile(l, 95)), 2), "below_8_pct": round(float((l < 8).mean() * 100), 2)}


def render(png, mode, preset_path, cube_path, out_png, wd):
    w, h = Image.open(png).size
    proj = os.path.join(wd, "zz_test_grade_" + uuid.uuid4().hex[:8] + ".fcproj")
    G.fc(["--save-as", proj, "exec", "file.newProject", json.dumps({"name": "zz_test_grade"})])
    G.fc(["--project", proj, "--save", "exec", "file.newSequence", json.dumps({"name": "s", "width": w, "height": h, "fps": 24, "sampleRate": 48000, "video": 4, "audio": 2, "mix": "Stereo"})])
    item = json.loads(G.fc(["--project", proj, "--save", "import", png]).stdout)["items"][0]
    clip = json.loads(G.fc(["--project", proj, "--save", "exec", "timeline.place", json.dumps({"item": item, "track": "V1", "seconds": 0, "duration": {"seconds": 2.0}, "insert": False})]).stdout)["clips"][0]
    if mode == "cube":
        G.fc(["--project", proj, "--save", "exec", "lumetri.setInputLut", json.dumps({"clip": clip, "path": cube_path.replace("\\", "/")})])
    elif mode in ("preset", "preset_lumetri"):
        p = json.load(open(preset_path, encoding="utf-8"))
        if mode == "preset_lumetri":
            p = G.lumetri_only(p)
        name = p["presets"][0]["name"]
        pf = os.path.join(wd, mode + ".fcpreset")
        json.dump(p, open(pf, "w", encoding="utf-8"))
        jl = os.path.join(wd, mode + ".jsonl")
        with open(jl, "w") as f:
            f.write(json.dumps({"id": "presets.import", "params": {"path": pf.replace("\\", "/")}}) + "\n")
            f.write(json.dumps({"id": "presets.apply", "params": {"preset": name, "clips": [clip]}}) + "\n")
        G.fc(["--project", proj, "--save", "run", jl])   # --save keeps the applied effects; render is a separate command
    G.fc(["--project", proj, "render", "--seconds", "0.5", "--out", out_png])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", nargs="+", required=True)
    ap.add_argument("--names", nargs="+", default=None)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--preset", default=os.path.join(HERE, "house-style.fcpreset"))
    ap.add_argument("--cube", default=os.path.join(HERE, "house-look.cube"))
    a = ap.parse_args()
    names = a.names or [os.path.splitext(os.path.basename(f))[0] for f in a.frames]
    os.makedirs(a.out_dir, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(prefix="zz_test_grade_") as wd:
        for name, src in zip(names, a.frames):
            rgb_src = os.path.join(wd, name + "_src.png")
            Image.open(src).convert("RGB").save(rgb_src)
            outs = {"before": rgb_src}
            for mode in ("preset", "preset_lumetri", "cube"):
                o = os.path.join(a.out_dir, f"{name}_{mode}.png")
                render(rgb_src, mode, a.preset, a.cube, o, wd)
                outs[mode] = o
            shutil.copyfile(rgb_src, os.path.join(a.out_dir, f"{name}_before.png"))
            L = {k: luma(Image.open(v)) for k, v in outs.items()}
            r = {"clip": name, **{k: stats(v) for k, v in L.items()}}
            r["p5_shift_preset_vs_before"] = round(r["preset"]["p5"] - r["before"]["p5"], 2)
            r["p5_shift_cube_vs_before"] = round(r["cube"]["p5"] - r["before"]["p5"], 2)
            r["mean_diff_preset_vs_cube"] = round(float(np.abs(L["preset"] - L["cube"]).mean()), 3)
            r["mean_diff_preset_lumetri_vs_cube"] = round(float(np.abs(L["preset_lumetri"] - L["cube"]).mean()), 3)
            r["mean_diff_before_vs_preset"] = round(float(np.abs(L["before"] - L["preset"]).mean()), 3)
            results.append(r)
            print(json.dumps(r))
    with open(os.path.join(a.out_dir, "grade_measurements.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
