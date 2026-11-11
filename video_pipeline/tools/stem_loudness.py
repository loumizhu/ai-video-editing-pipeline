#!/usr/bin/env python3
"""stem_loudness.py - Measures integrated loudness (LUFS) and True Peak (dBTP) for audio stems.
Can analyze a single audio file or a folder of stems (dialogue, music, sfx, mix).
Outputs stem_loudness.txt formatted for stage 08 QA.
"""

import argparse
import os
import re
import subprocess
import sys

def measure_loudness(audio_path):
    """Runs ffmpeg ebur128 filter and extracts Integrated Loudness and True Peak."""
    cmd = [
        "ffmpeg", "-nostats", "-i", audio_path,
        "-filter_complex", "ebur128=peak=true",
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    output = result.stderr

    i_match = re.search(r'Integrated loudness:\s+I:\s+([-\d.]+)\s+LUFS', output)
    lra_match = re.search(r'Loudness range:\s+LRA:\s+([-\d.]+)\s+LU', output)
    tp_match = re.search(r'True peak:\s+Peak:\s+([-\d.]+)\s+dBFS', output)

    return {
        "file": os.path.basename(audio_path),
        "path": audio_path,
        "integrated_lufs": float(i_match.group(1)) if i_match else None,
        "lra_lu": float(lra_match.group(1)) if lra_match else None,
        "true_peak_dbtp": float(tp_match.group(1)) if tp_match else None
    }

def main():
    parser = argparse.ArgumentParser(description="Analyze audio stem loudness (EBU R128)")
    parser.add_argument('--input', '-i', required=True, nargs='+', help="One or more audio files to analyze")
    parser.add_argument('--out', '-o', default="stem_loudness.txt", help="Output text report path")
    args = parser.parse_args()

    results = []
    for path in args.input:
        if os.path.exists(path):
            print(f"Measuring {path}...")
            res = measure_loudness(path)
            results.append(res)
        else:
            print(f"Warning: {path} not found, skipping", file=sys.stderr)

    out_lines = [
        "# STEM LOUDNESS REPORT (EBU R128 / ITU-R BS.1770-4)",
        "| Stem / File | Integrated (LUFS) | Target Range | True Peak (dBTP) | Target Max | Status |",
        "|---|---|---|---|---|---|"
    ]

    for r in results:
        fname = r["file"].lower()
        i_lufs = r["integrated_lufs"]
        tp = r["true_peak_dbtp"]
        
        # Determine target
        if "voice" in fname or "dialogue" in fname or "take" in fname:
            target_i = "-16.0 +/- 1.0"
            target_tp = "<= -1.0"
            pass_i = i_lufs is not None and (-17.0 <= i_lufs <= -15.0)
            pass_tp = tp is not None and tp <= -1.0
        elif "music" in fname or "bed" in fname:
            target_i = "-24.0 to -28.0 (ducked)"
            target_tp = "<= -3.0"
            pass_i = i_lufs is not None and (-28.5 <= i_lufs <= -23.5)
            pass_tp = tp is not None and tp <= -3.0
        elif "mix" in fname or "master" in fname or "rough" in fname:
            target_i = "-14.0 +/- 1.0"
            target_tp = "<= -1.0"
            pass_i = i_lufs is not None and (-15.0 <= i_lufs <= -13.0)
            pass_tp = tp is not None and tp <= -1.0
        else:
            target_i = "N/A"
            target_tp = "<= -1.0"
            pass_i = True
            pass_tp = tp is not None and tp <= -1.0

        status = "PASS" if (pass_i and pass_tp) else "REVIEW"
        i_str = f"{i_lufs:.1f} LUFS" if i_lufs is not None else "N/A (silent/placeholder)"
        tp_str = f"{tp:.1f} dBTP" if tp is not None else "-inf dBTP"
        out_lines.append(f"| `{r['file']}` | {i_str} | {target_i} | {tp_str} | {target_tp} | {status} |")

    report_text = "\n".join(out_lines) + "\n"
    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"Report written to {args.out}")

if __name__ == '__main__':
    main()
