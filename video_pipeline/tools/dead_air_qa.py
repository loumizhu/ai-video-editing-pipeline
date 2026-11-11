#!/usr/bin/env python
"""QA Script: Dead Air & Unintended Silence Detector.

Detects silent sections exceeding N seconds (default 0.6s) in the final audio/video mix,
excluding marked intentional pauses.

Fix 16 additions:
  - Validates input file existence and checks FFmpeg return code; exits 2 on error.
  - Requires valid media duration from ffprobe; exits 2 on parsing failure.
  - Rejects missing --allowed-pauses file with exit code 2.
  - Handles trailing silence at EOF (silence_start with no silence_end).

Writes JSON + Markdown report. Exits 0 on PASS, 1 on FAIL, 2 on usage/processing error.

Usage:
  python dead_air_qa.py --media cut.mp4 [--max-silence 0.6] [--noise-floor -35] [--out-json report.json] [--out-md report.md]
"""
import argparse
import json
import os
import re
import subprocess
import sys


def time_to_tc(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def get_media_duration(media_path):
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=nw=1:nk=1",
        media_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError(f"Could not determine media duration for '{media_path}': {proc.stderr.strip()}")
    try:
        dur = float(proc.stdout.strip())
        if dur <= 0:
            raise RuntimeError(f"Non-positive media duration {dur} for '{media_path}'")
        return dur
    except ValueError:
        raise RuntimeError(f"Invalid duration string '{proc.stdout.strip()}' for '{media_path}'")


def scan_dead_air(media_path, total_duration, max_silence=0.6, noise_floor=-35, allowed_pauses=None):
    cmd = [
        "ffmpeg",
        "-v",
        "info",
        "-i",
        media_path,
        "-af",
        f"silencedetect=noise={noise_floor}dB:d={max_silence}",
        "-f",
        "null",
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg silencedetect failed (exit {proc.returncode}):\n{proc.stderr.strip()}")

    stderr = proc.stderr

    # Parse silence entries
    # [silencedetect @ ...] silence_start: 12.34
    # [silencedetect @ ...] silence_end: 14.56 | silence_duration: 2.22
    silences = []
    current_start = None

    for line in stderr.splitlines():
        start_match = re.search(r"silence_start:\s*([\d\.]+)", line)
        if start_match:
            current_start = float(start_match.group(1))

        end_match = re.search(r"silence_end:\s*([\d\.]+)\s*\|\s*silence_duration:\s*([\d\.]+)", line)
        if end_match and current_start is not None:
            s_end = float(end_match.group(1))
            s_dur = float(end_match.group(2))
            silences.append({"start": round(current_start, 3), "end": round(s_end, 3), "duration": round(s_dur, 3)})
            current_start = None

    # Fix 16: Handle trailing silence at EOF (silence_start with no matching silence_end)
    if current_start is not None:
        s_end = round(total_duration, 3)
        s_dur = round(max(0.0, s_end - current_start), 3)
        if s_dur >= max_silence:
            silences.append({"start": round(current_start, 3), "end": s_end, "duration": s_dur})

    allowed_list = allowed_pauses or []
    defects = []

    for s in silences:
        # Check if silence falls within an allowed pause window
        is_allowed = False
        allowed_label = ""
        for ap in allowed_list:
            if s["start"] >= (ap.get("start", 0) - 0.2) and s["end"] <= (ap.get("end", 0) + 0.2):
                is_allowed = True
                allowed_label = ap.get("label", "intentional pause")
                break

        if not is_allowed and s["duration"] >= max_silence:
            defects.append(
                {
                    "start": s["start"],
                    "end": s["end"],
                    "start_tc": time_to_tc(s["start"]),
                    "end_tc": time_to_tc(s["end"]),
                    "duration": s["duration"],
                    "status": "FAIL",
                    "reason": f"Dead air duration {s['duration']:.2f}s exceeds limit {max_silence:.2f}s",
                }
            )
        else:
            s["status"] = "ALLOWED" if is_allowed else "PASS"
            s["label"] = allowed_label

    return silences, defects


def main():
    ap = argparse.ArgumentParser(description="Scan audio for excessive silence / dead air (Fix 16).")
    ap.add_argument("--media", required=True, help="Input media file (video or audio)")
    ap.add_argument("--max-silence", type=float, default=0.6, help="Maximum allowed silence in seconds (default: 0.6)")
    ap.add_argument("--noise-floor", type=float, default=-35.0, help="Noise threshold in dB (default: -35.0)")
    ap.add_argument("--allowed-pauses", help="Path to JSON file with allowed pauses list")
    ap.add_argument("--out-json", help="Output JSON report path")
    ap.add_argument("--out-md", help="Output Markdown report path")

    args = ap.parse_args()

    # Fix 16: Error if input media is missing
    if not os.path.exists(args.media):
        print(f"Error: Media file not found: {args.media}", file=sys.stderr)
        sys.exit(2)

    # Fix 16: Error if --allowed-pauses points to missing file
    allowed = []
    if args.allowed_pauses:
        if not os.path.exists(args.allowed_pauses):
            print(f"Error: --allowed-pauses file not found: {args.allowed_pauses}", file=sys.stderr)
            sys.exit(2)
        try:
            with open(args.allowed_pauses, "r", encoding="utf-8") as f:
                allowed = json.load(f)
        except Exception as e:
            print(f"Error reading --allowed-pauses JSON file: {e}", file=sys.stderr)
            sys.exit(2)

    # Fix 16: Check that media duration can be parsed; exit 2 on error
    try:
        total_duration = get_media_duration(args.media)
    except Exception as e:
        print(f"Error reading media duration: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        all_silences, defects = scan_dead_air(
            args.media,
            total_duration,
            max_silence=args.max_silence,
            noise_floor=args.noise_floor,
            allowed_pauses=allowed,
        )
    except Exception as e:
        print(f"Dead air scan error: {e}", file=sys.stderr)
        sys.exit(2)

    has_fail = len(defects) > 0
    overall_status = "FAIL" if has_fail else "PASS"

    out_json = args.out_json or os.path.splitext(args.media)[0] + "_dead_air_qa.json"
    out_md = args.out_md or os.path.splitext(args.media)[0] + "_dead_air_qa.md"

    report_payload = {
        "tool": "dead_air_qa",
        "media": os.path.abspath(args.media),
        "total_duration_s": round(total_duration, 3),
        "max_silence_limit": args.max_silence,
        "noise_floor_db": args.noise_floor,
        "overall_status": overall_status,
        "total_silences_detected": len(all_silences),
        "unapproved_dead_air_count": len(defects),
        "defects": defects,
        "all_silences": all_silences,
    }

    os.makedirs(os.path.dirname(os.path.abspath(out_json)), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)

    md_lines = [
        "# Dead Air & Unintended Silence Audit Report",
        f"**Media:** `{os.path.basename(args.media)}`  ",
        f"**Overall Status:** **{overall_status}**  ",
        f"**Media Duration:** {total_duration:.2f}s  ",
        f"**Max Silence Limit:** `{args.max_silence}s` | **Noise Floor:** `{args.noise_floor} dBFS`  ",
        f"**Total Silences Detected:** {len(all_silences)} | **Defective Windows:** {len(defects)}  \n",
    ]

    if defects:
        md_lines.extend(
            [
                "| Defect # | Range (s) | Timecodes | Duration (s) | Reason |",
                "|:---:|:---:|:---:|:---:|:---|",
            ]
        )
        for idx, d in enumerate(defects, 1):
            md_lines.append(
                f"| {idx} | {d['start']:.2f}s – {d['end']:.2f}s | `{d['start_tc']}` – `{d['end_tc']}` | "
                f"**{d['duration']:.2f}s** | {d['reason']} |"
            )
    else:
        md_lines.append("> [!NOTE]\n> No unapproved dead air detected. All pauses comply with limits.\n")

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print(
        f"Dead air scan complete: {overall_status} ({len(defects)} defects found) "
        f"-> {out_json} (md: {out_md})"
    )

    if has_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
