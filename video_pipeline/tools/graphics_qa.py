#!/usr/bin/env python
"""QA Script: Graphic Overlays & Title-Safe Boundary Auditor.

Scans overlay graphics (PNG with alpha, or alpha video keyframes in a folder or file):
  - Uses the actual image dimensions for the canvas, warning if they differ from --width/--height (Fix 15).
  - Checks if the graphic bounding box sits inside 90% title-safe area.
  - Flags if graphics touch any canvas edge (e.g. left edge clipping, right edge clipping).
  - Estimates text cap height and applies check to text-like content (warns on non-text/plates).

Writes JSON + Markdown report. Exits 0 on PASS, 1 on FAIL.

Usage:
  python graphics_qa.py --input graphics_folder [--width 1920] [--height 1080] [--out-json report.json] [--out-md report.md]
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile
import numpy as np
from PIL import Image


def get_alpha_bbox(img_path):
    """Load image and get alpha bounding box and actual dimensions."""
    with Image.open(img_path) as im:
        im_rgba = im.convert("RGBA")
        w, h = im_rgba.size
        alpha = np.array(im_rgba.split()[-1])
        mask = alpha > 10
        if not np.any(mask):
            return None, w, h, 0, 0.0
        y_indices, x_indices = np.where(mask)
        left, right = int(np.min(x_indices)), int(np.max(x_indices)) + 1
        top, bottom = int(np.min(y_indices)), int(np.max(y_indices)) + 1
        total_mask_pixels = int(np.sum(mask))
        bbox_area = max(1, (right - left) * (bottom - top))
        fill_ratio = total_mask_pixels / bbox_area
        return (left, top, right, bottom), w, h, total_mask_pixels, fill_ratio


def estimate_cap_height(img_path, bbox):
    """Estimate cap height from connected text components or vertical stroke runs in alpha image."""
    if not bbox:
        return 0, False
    with Image.open(img_path) as im:
        im_rgba = im.convert("RGBA")
        left, top, right, bottom = bbox
        crop = np.array(im_rgba.crop(bbox).split()[-1])

        row_density = np.mean(crop > 20, axis=1)
        active_rows = np.where(row_density > 0.05)[0]
        if len(active_rows) == 0:
            return bottom - top, False

        lines = []
        cur_line_start = active_rows[0]
        prev_r = active_rows[0]
        for r in active_rows[1:]:
            if r - prev_r > 3:  # gap between text lines
                lines.append((cur_line_start, prev_r))
                cur_line_start = r
            prev_r = r
        lines.append((cur_line_start, prev_r))

        line_heights = [end_r - start_r + 1 for start_r, end_r in lines]
        # In typography, cap height is approximately 70-75% of text line bounding height
        estimated_cap = int(max(line_heights) * 0.75) if line_heights else (bottom - top)
        # Text-like content typically has multiple lines or row density variation < 0.8
        is_text_like = len(lines) >= 1 and np.mean(row_density) < 0.85
        return max(estimated_cap, 1), is_text_like


def audit_graphic(
    file_path,
    target_w=1920,
    target_h=1080,
    title_safe_ratio=0.90,
    min_cap_height=45,
    enforce_cap_height=False,
):
    ext = os.path.splitext(file_path)[1].lower()
    is_video = ext in [".mov", ".mp4", ".mkv", ".webm"]
    temp_png = None

    try:
        inspect_path = file_path
        if is_video:
            td = tempfile.mkdtemp()
            temp_png = os.path.join(td, "frame.png")
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-ss", "0.5", "-i", file_path, "-vframes", "1", temp_png],
                check=True,
            )
            inspect_path = temp_png

        bbox, actual_w, actual_h, alpha_pixels, fill_ratio = get_alpha_bbox(inspect_path)
        if bbox is None:
            return {
                "file": os.path.basename(file_path),
                "status": "PASS",
                "notes": "Empty alpha channel / no graphics rendered",
                "reasons": [],
                "warnings": [],
            }

        left, top, right, bottom = bbox
        bbox_w = right - left
        bbox_h = bottom - top

        # Fix 15: Use actual image dimensions as canvas
        canvas_w = actual_w
        canvas_h = actual_h

        warnings = []
        if actual_w != target_w or actual_h != target_h:
            warnings.append(
                f"Image dimensions ({actual_w}x{actual_h}) differ from target ({target_w}x{target_h}); "
                f"evaluating boundaries against actual image canvas."
            )

        # Title-safe boundaries on actual canvas
        margin_x = round((1.0 - title_safe_ratio) / 2.0 * canvas_w)
        margin_y = round((1.0 - title_safe_ratio) / 2.0 * canvas_h)
        safe_left = margin_x
        safe_top = margin_y
        safe_right = canvas_w - margin_x
        safe_bottom = canvas_h - margin_y

        reasons = []

        # 1. Edge-touching check (left, top, right, bottom)
        touches_left = left <= 0
        touches_top = top <= 0
        touches_right = right >= canvas_w
        touches_bottom = bottom >= canvas_h

        if touches_left:
            reasons.append(f"Graphic touches or clips LEFT canvas edge (left={left} <= 0)")
        if touches_top:
            reasons.append(f"Graphic touches or clips TOP canvas edge (top={top} <= 0)")
        if touches_right:
            reasons.append(f"Graphic touches or clips RIGHT canvas edge (right={right} >= {canvas_w})")
        if touches_bottom:
            reasons.append(f"Graphic touches or clips BOTTOM canvas edge (bottom={bottom} >= {canvas_h})")

        # 2. Title-safe boundary check
        outside_left = left < safe_left
        outside_top = top < safe_top
        outside_right = right > safe_right
        outside_bottom = bottom > safe_bottom

        if outside_left:
            reasons.append(f"Graphic extends outside 90% title-safe area (left={left} < {safe_left})")
        if outside_top:
            reasons.append(f"Graphic extends outside 90% title-safe area (top={top} < {safe_top})")
        if outside_right:
            reasons.append(f"Graphic extends outside 90% title-safe area (right={right} > {safe_right})")
        if outside_bottom:
            reasons.append(f"Graphic extends outside 90% title-safe area (bottom={bottom} > {safe_bottom})")

        # 3. Cap-height check (applied to text-like content; warned on solid plates / non-text)
        est_cap, is_text_like = estimate_cap_height(inspect_path, bbox)
        if est_cap < min_cap_height:
            if is_text_like or enforce_cap_height:
                reasons.append(f"Estimated text cap height ({est_cap}px) below required minimum of {min_cap_height}px")
            else:
                warnings.append(
                    f"Estimated element height ({est_cap}px) below {min_cap_height}px cap height threshold "
                    f"(treated as advisory warning for graphical plate/shape with fill ratio {fill_ratio:.2f})"
                )

        status = "FAIL" if len(reasons) > 0 else "PASS"

        return {
            "file": os.path.basename(file_path),
            "canvas_dims": f"{canvas_w}x{canvas_h}",
            "bbox": {
                "left": left,
                "top": top,
                "right": right,
                "bottom": bottom,
                "width": bbox_w,
                "height": bbox_h,
            },
            "fill_ratio": round(fill_ratio, 2),
            "estimated_cap_height_px": est_cap,
            "status": status,
            "reasons": reasons,
            "warnings": warnings,
        }

    finally:
        if temp_png and os.path.exists(temp_png):
            try:
                os.remove(temp_png)
                os.rmdir(os.path.dirname(temp_png))
            except Exception:
                pass


def main():
    ap = argparse.ArgumentParser(
        description="QA Script: Graphic Overlays & Title-Safe Boundary Auditor (Fix 15)."
    )
    ap.add_argument("--input", required=True, help="Input directory of graphics or single graphic file")
    ap.add_argument("--width", type=int, default=1920, help="Expected canvas width (default: 1920)")
    ap.add_argument("--height", type=int, default=1080, help="Expected canvas height (default: 1080)")
    ap.add_argument("--title-safe", type=float, default=0.90, help="Title-safe ratio (default: 0.90 = 90% safe area)")
    ap.add_argument("--min-cap-height", type=int, default=45, help="Minimum text cap height in pixels (default: 45)")
    ap.add_argument("--enforce-cap-height", action="store_true", help="Enforce cap height check strictly on all assets")
    ap.add_argument("--out-json", help="Output JSON report path")
    ap.add_argument("--out-md", help="Output Markdown report path")

    args = ap.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input path not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    if os.path.isdir(args.input):
        patterns = ["*.png", "*.mov", "*.mp4", "*.mkv", "*.webm"]
        files = []
        for pat in patterns:
            files.extend(glob.glob(os.path.join(args.input, pat)))
    else:
        files = [args.input]

    if not files:
        print(f"No graphic assets (.png, .mov, etc.) found in {args.input}", file=sys.stderr)
        sys.exit(0)

    asset_reports = []
    has_failure = False

    for f in sorted(files):
        res = audit_graphic(
            f,
            target_w=args.width,
            target_h=args.height,
            title_safe_ratio=args.title_safe,
            min_cap_height=args.min_cap_height,
            enforce_cap_height=args.enforce_cap_height,
        )
        asset_reports.append(res)
        if res["status"] == "FAIL":
            has_failure = True

    overall_status = "FAIL" if has_failure else "PASS"

    out_json = args.out_json or os.path.join(
        os.path.dirname(os.path.abspath(args.input)),
        f"{os.path.splitext(os.path.basename(args.input))[0]}_graphics_qa.json",
    )
    out_md = args.out_md or os.path.splitext(out_json)[0] + ".md"

    report_payload = {
        "tool": "graphics_qa",
        "input": os.path.abspath(args.input),
        "total_assets_inspected": len(asset_reports),
        "overall_status": overall_status,
        "canvas_dimensions": f"{args.width}x{args.height}",
        "title_safe_ratio": args.title_safe,
        "min_cap_height_limit": args.min_cap_height,
        "assets": asset_reports,
    }

    os.makedirs(os.path.dirname(os.path.abspath(out_json)), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)

    md_lines = [
        "# Graphic Overlays & Title-Safe Boundary Audit Report",
        f"**Input:** `{os.path.basename(args.input)}`  ",
        f"**Overall Status:** **{overall_status}**  ",
        f"**Total Assets Inspected:** {len(asset_reports)}  ",
        f"**Canvas Standard:** `{args.width}x{args.height}` | **Title Safe:** `{int(args.title_safe*100)}%` | **Min Cap Height:** `{args.min_cap_height}px`  \n",
        "| Asset File | Canvas | BBox [L,T,R,B] | Cap H (px) | Status | Reasons / Warnings |",
        "|:---|:---:|:---:|:---:|:---:|:---|",
    ]

    for a in asset_reports:
        bb = a.get("bbox", {})
        bb_str = f"[{bb.get('left')},{bb.get('top')},{bb.get('right')},{bb.get('bottom')}]" if bb else "-"
        notes = []
        if a.get("reasons"):
            notes.extend([f"FAIL: {r}" for r in a["reasons"]])
        if a.get("warnings"):
            notes.extend([f"WARN: {w}" for w in a["warnings"]])
        notes_str = "; ".join(notes) if notes else "Compliant (inside title-safe)"

        md_lines.append(
            f"| `{a['file']}` | {a.get('canvas_dims', '-')} | `{bb_str}` | {a.get('estimated_cap_height_px', '-')} | **{a['status']}** | {notes_str} |"
        )

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print(
        f"Graphics QA complete: {overall_status} ({len(asset_reports)} assets inspected) "
        f"-> {out_json} (md: {out_md})"
    )

    if has_failure:
        sys.exit(1)


if __name__ == "__main__":
    main()
