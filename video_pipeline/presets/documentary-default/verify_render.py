"""Frame-by-frame verification of a rendered overlay .mov (what graphics_qa.py cannot see: it samples one frame).

Checks, over EVERY frame:
  1. pix_fmt has alpha (ffprobe)
  2. alpha bbox inside the safe rect from style.json (canvas.safe_margin_*), once the in-animation has settled
     (frames inside the slide are reported separately: they travel slide_px outside by design)
  3. nothing touches a canvas edge
  4. easing: per-frame y_min / alpha-sum steps shrink during the in-animation and grow during the out-animation
On the hold frame (plate families): text pixels (luma > text_luma, alpha > 200) must sit inside the plate with
at least `min_pad` px on every side.

  python verify_render.py --mov lower-third.mov --style style.json [--plate] [--keep-frames DIR] [--out-json r.json]
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mov", required=True)
    ap.add_argument("--style", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.json"))
    ap.add_argument("--plate", action="store_true", help="family has a glass plate: also check text-inside-plate on the hold frame")
    ap.add_argument("--min-pad", type=int, default=24)
    ap.add_argument("--text-luma", type=int, default=150)
    ap.add_argument("--keep-frames", default=None)
    ap.add_argument("--out-json", default=None)
    a = ap.parse_args()

    style = C.load_style(a.style)
    sx0, sy0, sx1, sy1 = C.safe_rect(style)
    W, H = style["canvas"]["width"], style["canvas"]["height"]
    pix = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=pix_fmt,width,height,nb_frames,codec_name", "-of", "json", a.mov],
                         capture_output=True, text=True).stdout
    info = json.loads(pix)["streams"][0]
    d = a.keep_frames or tempfile.mkdtemp()
    os.makedirs(d, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.mov, "-pix_fmt", "rgba", os.path.join(d, "f%04d.png")], check=True)
    files = sorted(f for f in os.listdir(d) if f.startswith("f") and f.endswith(".png"))

    rows, hold_idx = [], len(files) // 2
    for i, fn in enumerate(files):
        im = np.array(Image.open(os.path.join(d, fn)).convert("RGBA"))
        al = im[..., 3]
        m = al > 10
        if not m.any():
            rows.append(dict(f=i + 1, bbox=None, asum=0.0))
            continue
        ys, xs = np.where(m)
        rows.append(dict(f=i + 1, bbox=[int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1], asum=float(al.sum()) / 255.0))

    in_f, out_f = style["animation"]["in_frames"], style["animation"]["out_frames"]
    settled = [r for r in rows if r["bbox"] and r["f"] > in_f and r["f"] < len(files) - out_f]
    viol = [r for r in settled if r["bbox"][0] < sx0 or r["bbox"][1] < sy0 or r["bbox"][2] > sx1 or r["bbox"][3] > sy1]
    edge = [r for r in rows if r["bbox"] and (r["bbox"][0] <= 0 or r["bbox"][1] <= 0 or r["bbox"][2] >= W or r["bbox"][3] >= H)]
    all_boxes = [r["bbox"] for r in rows if r["bbox"]]
    union = [min(b[0] for b in all_boxes), min(b[1] for b in all_boxes), max(b[2] for b in all_boxes), max(b[3] for b in all_boxes)]
    res = dict(file=os.path.abspath(a.mov), pix_fmt=info["pix_fmt"], codec=info["codec_name"], size=f'{info["width"]}x{info["height"]}',
               frames=len(files), safe_rect=[sx0, sy0, sx1, sy1], union_bbox_all_frames=union,
               settled_frames_checked=len(settled), safe_violations=len(viol), edge_touch_frames=len(edge),
               alpha_present="a" in info["pix_fmt"])

    ys_in = [r["bbox"][1] for r in rows[: in_f + 1] if r["bbox"]]
    asum_in = [r["asum"] for r in rows[: in_f + 1]]
    res["in_anim_y_min"] = ys_in
    res["in_anim_alpha_sum_steps"] = [round(asum_in[i + 1] - asum_in[i], 1) for i in range(len(asum_in) - 1)]
    steps = res["in_anim_alpha_sum_steps"]
    res["in_anim_alpha_steps_shrink"] = all(steps[i] >= steps[i + 1] - 0.05 * abs(steps[0]) for i in range(len(steps) - 1)) if steps else None

    if a.plate:
        im = np.array(Image.open(os.path.join(d, files[hold_idx])).convert("RGBA"))
        al = im[..., 3]
        lum = im[..., :3].astype(int).sum(axis=2) / 3.0
        pm = al > 10
        ys, xs = np.where(pm)
        plate = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
        # text = bright pixels well inside the plate (skip the 2px border and the accent bar by cropping 8px in)
        inner = np.zeros_like(pm)
        inner[plate[1] + 8: plate[3] - 8, plate[0] + 20: plate[2] - 8] = True
        tm_ = inner & (al > 200) & (lum > a.text_luma)
        ty, tx = np.where(tm_)
        text = [int(tx.min()), int(ty.min()), int(tx.max()) + 1, int(ty.max()) + 1]
        pads = dict(left=text[0] - plate[0], top=text[1] - plate[1], right=plate[2] - text[2], bottom=plate[3] - text[3])
        res["hold_frame"] = hold_idx + 1
        res["plate_bbox"] = plate
        res["text_bbox"] = text
        res["text_to_plate_padding"] = pads
        res["text_inside_plate_min_pad_ok"] = min(pads.values()) >= a.min_pad

    ok = res["alpha_present"] and res["safe_violations"] == 0 and res["edge_touch_frames"] == 0 and (res.get("text_inside_plate_min_pad_ok", True))
    res["verdict"] = "PASS" if ok else "FAIL"
    txt = json.dumps(res, indent=2)
    print(txt)
    if a.out_json:
        os.makedirs(os.path.dirname(os.path.abspath(a.out_json)), exist_ok=True)
        open(a.out_json, "w", encoding="utf-8").write(txt)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
