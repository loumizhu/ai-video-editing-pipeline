#!/usr/bin/env python
"""QA Script: Photosensitive Flash Screen (guideline-based).

This is a screening heuristic modelled on the WCAG 2.3.1 "general flash" definition. It is NOT a certified
ITU-R BT.1702 / Harding FPA test and must not be quoted as compliance.

Method:
  - Decode the video to 160x90 grayscale at the source frame rate and convert to linear relative luminance
    (sRGB transfer, 0..1).
  - Track per-pixel excursions. A change counts only if the luminance moved by >= --threshold (default 0.10 =
    10% of maximum luminance) on >= --area-ratio (default 25%) of the frame. Each reversal of direction after
    such an excursion is one "opposing change".
  - A flash is a PAIR of opposing changes (an increase then a decrease, or the reverse). In any rolling 1.0 s
    window, N opposing changes = N // 2 flashes. More than --max-flashes (default 3) flashes in one second FAILS.
  - Smooth sine fades therefore pass up to 3 Hz (a 1 Hz fade = 1 flash/s, a 2 Hz fade = 2 flashes/s) while a
    5 Hz on/off flash = 5 flashes/s fails.

Not covered (do not rely on this for broadcast sign-off): saturated-red flashes, spatial patterns/stripes,
the 10-degree visual-field area (frame area is used instead), the darker-image (< 0.8 luminance) rule, and
frame-rate conversion effects. The frame rate comes from ffprobe with no default; an unreadable rate is an error.

Writes JSON + Markdown report. Exits 0 on PASS, 1 on FAIL (clean error on bad input).

Usage:
  python flash_scan.py --media video.mp4 [--threshold 0.10] [--area-ratio 0.25] [--max-flashes 3] [--out-json report.json] [--out-md report.md]
"""
import argparse
from fractions import Fraction
import json
import math
import os
import subprocess
import sys
import numpy as np


def time_to_tc(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def get_video_fps(media_path):
    if not os.path.exists(media_path):
        raise FileNotFoundError(f"Media file not found: {media_path}")

    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate,avg_frame_rate", "-of", "json", media_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed for '{media_path}':\n{proc.stderr.strip()}")

    data = json.loads(proc.stdout)
    streams = data.get("streams", [])
    if not streams:
        raise RuntimeError(f"No video streams found in '{media_path}'")

    for key in ("r_frame_rate", "avg_frame_rate"):
        rate = streams[0].get(key)
        if rate and "/" in rate:
            num, den = map(int, rate.split("/"))
            if num > 0 and den > 0:
                return num / den
    raise RuntimeError(f"No usable frame rate reported for '{media_path}' (refusing to guess)")


def _linear_lut():
    c = np.arange(256, dtype=np.float32) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


def find_reversals(lum, thresh, area_thresh):
    """lum: (frames, pixels) linear luminance. Returns [(frame_index, new_direction, delta)] reversal events.

    Direction starts unknown; the first >= thresh excursion on >= area_thresh of the frame sets it. After that each
    reversal of >= thresh from the running extreme (per pixel) on >= area_thresh of the frame is one opposing change.
    """
    n = lum.shape[0]
    events = []
    direction = 0
    ref_hi = lum[0].copy()
    ref_lo = lum[0].copy()
    ref = None
    for i in range(1, n):
        cur = lum[i]
        if direction == 0:
            ref_hi = np.maximum(ref_hi, cur)
            ref_lo = np.minimum(ref_lo, cur)
            if np.mean(cur - ref_lo >= thresh) >= area_thresh:
                direction, ref = +1, cur.copy()
            elif np.mean(ref_hi - cur >= thresh) >= area_thresh:
                direction, ref = -1, cur.copy()
        elif direction == +1:
            ref = np.maximum(ref, cur)
            if np.mean(ref - cur >= thresh) >= area_thresh:
                events.append((i, -1, float(np.max(ref - cur))))
                direction, ref = -1, cur.copy()
        else:
            ref = np.minimum(ref, cur)
            if np.mean(cur - ref >= thresh) >= area_thresh:
                events.append((i, +1, float(np.max(cur - ref))))
                direction, ref = +1, cur.copy()
    return events


def scan_flashes(media_path, luminance_delta_thresh=0.10, area_thresh=0.25, max_flashes_per_sec=3):
    fps = get_video_fps(media_path)
    w, h = 160, 90
    frame_size = w * h

    cmd = ["ffmpeg", "-v", "error", "-i", media_path, "-vf", f"scale={w}:{h},format=gray", "-f", "rawvideo", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    raw, stderr = proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg decoding failed:\n{stderr.decode(errors='ignore').strip()}")

    if len(raw) < frame_size:
        return [], 0, fps, []

    total_frames = len(raw) // frame_size
    codes = np.frombuffer(raw[: total_frames * frame_size], dtype=np.uint8).reshape((total_frames, frame_size))
    lum = _linear_lut()[codes]

    events = find_reversals(lum, luminance_delta_thresh, area_thresh)
    ev_times = np.array([e[0] for e in events], dtype=np.float64) / fps if events else np.array([])
    ev_delta = [e[2] for e in events]

    window_s = 1.0
    hazard_windows = []
    for idx, t in enumerate(ev_times):
        mask = (ev_times >= t) & (ev_times <= t + window_s)
        n_changes = int(mask.sum())
        flashes = n_changes // 2
        if flashes > max_flashes_per_sec:
            if not hazard_windows or (t > hazard_windows[-1]["end_s"]):
                peak = float(max(d for d, m in zip(ev_delta, mask) if m))
                hazard_windows.append(
                    {
                        "start_s": round(float(t), 3),
                        "end_s": round(float(t + window_s), 3),
                        "start_tc": time_to_tc(t),
                        "end_tc": time_to_tc(t + window_s),
                        "flashes_in_sec": flashes,
                        "opposing_changes_in_sec": n_changes,
                        "peak_delta": round(peak, 3),
                        "status": "FAIL",
                        "reason": (
                            f"{flashes} flashes ({n_changes} opposing luminance changes) in a 1.0 s window exceeds the "
                            f"guideline limit of {max_flashes_per_sec} flashes/s"
                        ),
                    }
                )

    return hazard_windows, total_frames, fps, ev_times.tolist()


def main():
    ap = argparse.ArgumentParser(
        description="Photosensitive flash screen (guideline-based, modelled on WCAG 2.3.1; not a certified BT.1702/Harding test)."
    )
    ap.add_argument("--media", required=True, help="Input video media file")
    ap.add_argument(
        "--threshold", type=float, default=0.10,
        help="Minimum luminance change as a fraction of maximum relative luminance (default: 0.10 = 10%%)",
    )
    ap.add_argument(
        "--area-ratio", type=float, default=0.25,
        help="Minimum fraction of the frame affected by a change (default: 0.25)",
    )
    ap.add_argument(
        "--max-flashes", type=int, default=3,
        help="Maximum flashes (pairs of opposing changes) in any 1.0 second window (default: 3)",
    )
    ap.add_argument("--out-json", help="Output JSON report path")
    ap.add_argument("--out-md", help="Output Markdown report path")

    args = ap.parse_args()

    if not os.path.exists(args.media):
        print(f"Error: Media file not found: {args.media}", file=sys.stderr)
        sys.exit(1)

    try:
        hazards, total_frames, fps, change_times = scan_flashes(
            args.media,
            luminance_delta_thresh=args.threshold,
            area_thresh=args.area_ratio,
            max_flashes_per_sec=args.max_flashes,
        )
    except Exception as exc:
        print(f"Error during flash scan: {exc}", file=sys.stderr)
        sys.exit(1)

    has_fail = len(hazards) > 0
    overall_status = "FAIL" if has_fail else "PASS"

    out_json = args.out_json or os.path.splitext(args.media)[0] + "_flash_scan.json"
    out_md = args.out_md or os.path.splitext(args.media)[0] + "_flash_scan.md"

    report_payload = {
        "tool": "flash_scan",
        "disclaimer": "guideline-based screen modelled on WCAG 2.3.1; not a certified BT.1702 / Harding test",
        "media": os.path.abspath(args.media),
        "total_frames_analyzed": total_frames,
        "video_fps": round(fps, 3),
        "luminance_threshold_fraction": args.threshold,
        "area_threshold_ratio": args.area_ratio,
        "max_flashes_per_sec_limit": args.max_flashes,
        "overall_status": overall_status,
        "total_opposing_changes": len(change_times),
        "hazard_windows_count": len(hazards),
        "hazards": hazards,
    }

    os.makedirs(os.path.dirname(os.path.abspath(out_json)), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)

    md_lines = [
        "# Photosensitive Flash Screen Report (guideline-based)",
        f"**Media:** `{os.path.basename(args.media)}`  ",
        f"**Overall Status:** **{overall_status}**  ",
        f"**Total Frames Analyzed:** {total_frames} ({round(total_frames/fps, 2)}s @ {round(fps, 3)} fps)  ",
        f"**Rule:** more than {args.max_flashes} flashes (pairs of opposing luminance changes of >= {int(args.threshold*100)}% of max luminance over >= {int(args.area_ratio*100)}% of the frame) in any 1 s window. "
        "Heuristic screen modelled on WCAG 2.3.1, not a certified BT.1702/Harding test; red flashes and patterns are not checked.  ",
        f"**Opposing changes detected:** {len(change_times)} | **Hazard windows:** {len(hazards)}  \n",
    ]

    if hazards:
        md_lines.extend(
            [
                "| Hazard # | Window (s) | Timecodes | Flashes / Sec | Peak Delta (luminance) | Reason |",
                "|:---:|:---:|:---:|:---:|:---:|:---|",
            ]
        )
        for idx, hz in enumerate(hazards, 1):
            md_lines.append(
                f"| {idx} | {hz['start_s']:.3f}s - {hz['end_s']:.3f}s | `{hz['start_tc']}` - `{hz['end_tc']}` | "
                f"**{hz['flashes_in_sec']}/s** | {hz['peak_delta']} | {hz['reason']} |"
            )
    else:
        md_lines.append(f"> No window exceeds {args.max_flashes} flashes per second on >= {int(args.area_ratio*100)}% of the frame.\n")

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print(
        f"Flash scan complete: {overall_status} ({len(hazards)} hazard windows) "
        f"-> {out_json} (md: {out_md})"
    )

    if has_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
