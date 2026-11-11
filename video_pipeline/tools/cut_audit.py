#!/usr/bin/env python
"""QA Script: Cut Audio Discontinuity & Speech Clip Auditor.

For every edit point in a rendered cut timeline, extracts the audio waveform
and measures RMS energy, waveform step discontinuity, and spectral continuity
across 40 ms on either side of the cut (Fix 13).

Flags cuts that land inside active speech energy (clipped word/phoneme),
hard click step jumps, or phase/spectral discontinuities.

Threshold rationale (documented in accordance with Fix 13):
  - Speech threshold (-28.0 dBFS default): Conversational speech typically sits
    between -18 and -26 dBFS. Ambient room tone / pauses sit below -35 dBFS.
    A threshold near -28 dBFS cleanly distinguishes unclipped pause room-tone
    from speech phonemes cut mid-vowel/consonant.
  - Click jump threshold (0.15 default): Normalized sample step jump across cut.
  - Spectral flux threshold (0.20 default): Cosine distance between normalized
    FFT spectra across non-silent boundary points.

Every failing edit gets a remedy line: the neighbouring transcript words and gaps (when cuts.json carries the
"edges" data written by make_cuts), and either "apply a 2-frame audio crossfade at edit N" or
"move the keep boundary to word i" (the nearest word boundary with a real pause).

Known limits (by design, documented): the click test is an absolute step threshold, so a click inside very quiet
audio (e.g. a 90-degree phase jump at -31 dBFS, step 0.04) PASSES; the spectral test only runs when both sides
are above -35 dBFS. There is no fps default: cuts.json must carry fps_num/fps_den.

Writes JSON + Markdown report. Exits 0 on PASS, 1 on FAIL, 2 on bad input.

Usage:
  python cut_audit.py --media cut.mp4 --cuts cuts.json [--speech-thresh -28.0] [--click-thresh 0.15] [--out-json report.json] [--out-md report.md]
"""
import argparse
from fractions import Fraction
import json
import math
import os
import subprocess
import sys
import numpy as np


def extract_pcm16_mono(media_path, sample_rate=48000):
    """Extract audio from media into raw float32 array in [-1.0, 1.0]."""
    if not os.path.exists(media_path):
        raise FileNotFoundError(f"Media file not found: {media_path}")

    cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        media_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-f",
        "s16le",
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg audio extraction failed for '{media_path}':\n{proc.stderr.decode(errors='ignore')}")

    raw = proc.stdout
    if not raw:
        return np.zeros(0, dtype=np.float32), sample_rate

    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    return samples, sample_rate


def rms_db(samples):
    if len(samples) == 0:
        return -96.0
    mean_sq = np.mean(samples**2)
    if mean_sq <= 1e-10:
        return -96.0
    return float(20.0 * np.log10(np.sqrt(mean_sq)))


def time_to_tc(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def require_fps(cuts_data):
    """fps_num/fps_den are mandatory: a silent default corrupts every timecode."""
    fn, fd = cuts_data.get("fps_num"), cuts_data.get("fps_den")
    if not isinstance(fn, int) or not isinstance(fd, int) or fn <= 0 or fd <= 0:
        raise ValueError(f"cuts.json has no valid fps_num/fps_den (got {fn!r}/{fd!r}); refusing to guess a frame rate")
    return Fraction(fn, fd)


def build_remedy(cut_index, timecode, out_seg, in_seg, reasons):
    """Per-failing-edit actionable line: neighbouring words, gaps, and what to do."""
    speech_pre = any(r.startswith("Pre-cut") for r in reasons)
    speech_post = any(r.startswith("Post-cut") for r in reasons)
    e_out = (out_seg or {}).get("edges", {}).get("end") or {}
    e_in = (in_seg or {}).get("edges", {}).get("start") or {}
    out_words = ((out_seg or {}).get("text") or "").split()
    in_words = ((in_seg or {}).get("text") or "").split()
    parts = [f"Edit {cut_index} at {timecode}:"]
    if out_words:
        g = e_out.get("gap_s")
        parts.append(
            f"outgoing clip ends on '{out_words[-1]}'"
            + (f" (next source word '{e_out.get('neighbor_word')}', gap {g:.3f} s{', zero-pause' if e_out.get('zero_pause') else ''})" if g is not None else "")
            + ";"
        )
    if in_words:
        g = e_in.get("gap_s")
        parts.append(
            f"incoming clip starts on '{in_words[0]}'"
            + (f" (previous source word '{e_in.get('neighbor_word')}', gap {g:.3f} s{', zero-pause' if e_in.get('zero_pause') else ''})" if g is not None else "")
            + "."
        )
    suggestions = []
    if speech_pre and e_out.get("remedy"):
        suggestions.append("outgoing side: " + e_out["remedy"])
    if speech_post and e_in.get("remedy"):
        suggestions.append("incoming side: " + e_in["remedy"])
    if not suggestions:
        suggestions.append(f"apply a 2-frame audio crossfade at edit {cut_index}")
    parts.append("Remedy: " + "; ".join(suggestions) + ".")
    return " ".join(parts)


def audit_cuts(
    media_path,
    segments,
    fps_ratio,
    speech_thresh_db=-28.0,
    click_jump_thresh=0.15,
    spectral_flux_thresh=0.20,
):
    samples, sr = extract_pcm16_mono(media_path, sample_rate=48000)
    window_samples = int(0.040 * sr)  # 40 ms window

    results = []
    has_failure = False

    accum_frames = 0
    # Edit points occur at boundaries between consecutive segments
    for i in range(len(segments) - 1):
        accum_frames += segments[i]["dur_frames"]

        # Compute timeline position frame-accurately from frames / fps (Fix 13)
        timeline_pos = float(Fraction(accum_frames, 1) / fps_ratio)
        sample_idx = int(round(timeline_pos * sr))

        # Pre-cut 40ms window
        pre_start = max(0, sample_idx - window_samples)
        pre_samples = samples[pre_start:sample_idx]

        # Post-cut 40ms window
        post_end = min(len(samples), sample_idx + window_samples)
        post_samples = samples[sample_idx:post_end]

        pre_db = rms_db(pre_samples)
        post_db = rms_db(post_samples)

        # 1. Waveform step jump across boundary
        step = 0.0
        if 0 < sample_idx < len(samples):
            step = float(abs(samples[sample_idx] - samples[sample_idx - 1]))

        # 2. Spectral flux / continuity across boundary (Fix 13)
        spectral_flux = 0.0
        if len(pre_samples) >= 64 and len(post_samples) >= 64:
            min_len = min(len(pre_samples), len(post_samples))
            fft_pre = np.abs(np.fft.rfft(pre_samples[-min_len:]))
            fft_post = np.abs(np.fft.rfft(post_samples[:min_len]))
            norm_pre = np.linalg.norm(fft_pre)
            norm_post = np.linalg.norm(fft_post)
            if norm_pre > 1e-4 and norm_post > 1e-4:
                cos_sim = float(np.dot(fft_pre / norm_pre, fft_post / norm_post))
                spectral_flux = float(max(0.0, 1.0 - cos_sim))

        reasons = []
        # Flag if cut lands inside active speech energy (clipped word)
        if pre_db > speech_thresh_db:
            reasons.append(f"Pre-cut speech energy clipped ({pre_db:.1f} dB > {speech_thresh_db:.1f} dB)")
        if post_db > speech_thresh_db:
            reasons.append(f"Post-cut speech energy clipped ({post_db:.1f} dB > {speech_thresh_db:.1f} dB)")
        if step > click_jump_thresh:
            reasons.append(f"Waveform step click ({step:.3f} > {click_jump_thresh:.3f})")

        # Flag spectral discontinuity on non-silent cuts
        if pre_db > -35.0 and post_db > -35.0 and spectral_flux > spectral_flux_thresh:
            reasons.append(f"Mid-sound spectral/phase discontinuity ({spectral_flux:.3f} > {spectral_flux_thresh:.3f})")

        status = "FAIL" if len(reasons) > 0 else "PASS"
        remedy = None
        if status == "FAIL":
            has_failure = True
            remedy = build_remedy(i + 1, time_to_tc(timeline_pos), segments[i], segments[i + 1], reasons)

        results.append(
            {
                "cut_index": i + 1,
                "timecode": time_to_tc(timeline_pos),
                "timeline_seconds": round(timeline_pos, 3),
                "pre_rms_db": round(pre_db, 1),
                "post_rms_db": round(post_db, 1),
                "waveform_step": round(step, 3),
                "spectral_flux": round(spectral_flux, 3),
                "status": status,
                "reasons": reasons,
                "remedy": remedy,
            }
        )

    return results, has_failure


def main():
    ap = argparse.ArgumentParser(
        description="QA Script: Cut Audio Discontinuity & Speech Clip Auditor (Fix 13).\n"
                    "Analyzes 40ms pre- and post-cut windows at each edit point for speech clipping,\n"
                    "waveform step jumps, and spectral discontinuities."
    )
    ap.add_argument("--media", required=True, help="Input media file (video or audio)")
    ap.add_argument("--cuts", required=True, help="Input cuts.json")
    ap.add_argument(
        "--speech-thresh",
        type=float,
        default=-28.0,
        help="Speech energy threshold in dBFS (default: -28.0; normal speech: -20 to -26 dBFS, pauses: < -35 dBFS)",
    )
    ap.add_argument(
        "--click-thresh",
        type=float,
        default=0.15,
        help="Maximum waveform sample jump across boundary (default: 0.15)",
    )
    ap.add_argument(
        "--spectral-thresh",
        type=float,
        default=0.20,
        help="Maximum spectral flux distance across boundary (default: 0.20)",
    )
    ap.add_argument("--out-json", help="Output JSON report path")
    ap.add_argument("--out-md", help="Output Markdown report path")

    args = ap.parse_args()

    if not os.path.exists(args.media):
        print(f"Error: Media file not found: {args.media}", file=sys.stderr)
        sys.exit(2)
    if not os.path.exists(args.cuts):
        print(f"Error: Cuts file not found: {args.cuts}", file=sys.stderr)
        sys.exit(2)

    try:
        with open(args.cuts, "r", encoding="utf-8") as f:
            cuts_data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error: cannot read cuts file {args.cuts}: {e}", file=sys.stderr)
        sys.exit(2)

    segments = cuts_data.get("segments", [])
    if len(segments) <= 1:
        print("Fewer than 2 segments; no internal edit points to audit.")
        sys.exit(0)

    try:
        fps_ratio = require_fps(cuts_data)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    # Derive dur_frames if missing in minimal test cuts
    for s in segments:
        if "dur_frames" not in s:
            if "dur_s" in s:
                s["dur_frames"] = round(s["dur_s"] * fps_ratio)
            elif "start_frame" in s and "end_frame" in s:
                s["dur_frames"] = s["end_frame"] - s["start_frame"]

    try:
        cuts_results, has_fail = audit_cuts(
            args.media,
            segments,
            fps_ratio,
            speech_thresh_db=args.speech_thresh,
            click_jump_thresh=args.click_thresh,
            spectral_flux_thresh=args.spectral_thresh,
        )
    except Exception as exc:
        print(f"Cut audit error: {exc}", file=sys.stderr)
        sys.exit(2)

    out_json = args.out_json or os.path.splitext(args.media)[0] + "_cut_audit.json"
    out_md = args.out_md or os.path.splitext(args.media)[0] + "_cut_audit.md"

    overall_status = "FAIL" if has_fail else "PASS"

    report_payload = {
        "tool": "cut_audit",
        "media": os.path.abspath(args.media),
        "total_edit_points": len(cuts_results),
        "overall_status": overall_status,
        "speech_threshold_db": args.speech_thresh,
        "click_threshold": args.click_thresh,
        "spectral_threshold": args.spectral_thresh,
        "cuts": cuts_results,
    }

    os.makedirs(os.path.dirname(os.path.abspath(out_json)), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)

    # Markdown report
    md_lines = [
        "# Cut Audio Continuity Audit Report",
        f"**Media:** `{os.path.basename(args.media)}`  ",
        f"**Overall Status:** **{overall_status}**  ",
        f"**Total Edit Points:** {len(cuts_results)}  ",
        f"**Speech Threshold:** `{args.speech_thresh} dBFS` | **Click Threshold:** `{args.click_thresh}` | **Spectral Threshold:** `{args.spectral_thresh}`  \n",
        "| Edit # | Timecode | Pre RMS (dB) | Post RMS (dB) | Step | Spectral | Status | Reasons |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|",
    ]
    for c in cuts_results:
        reasons_str = "; ".join(c["reasons"]) if c["reasons"] else "None"
        md_lines.append(
            f"| {c['cut_index']} | `{c['timecode']}` | {c['pre_rms_db']} | {c['post_rms_db']} | "
            f"{c['waveform_step']} | {c['spectral_flux']} | **{c['status']}** | {reasons_str} |"
        )
    failing = [c for c in cuts_results if c["status"] == "FAIL"]
    if failing:
        md_lines.append("")
        md_lines.append("## Remedies")
        md_lines.append("")
        for c in failing:
            md_lines.append(f"- {c['remedy']}")

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print(
        f"Cut audit complete: {overall_status} ({len(cuts_results)} edit points audited) "
        f"-> {out_json} (md: {out_md})"
    )

    for c in cuts_results:
        if c["status"] == "FAIL":
            print(f"  FAIL edit {c['cut_index']}: {'; '.join(c['reasons'])}")
            print(f"    {c['remedy']}")

    if has_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
