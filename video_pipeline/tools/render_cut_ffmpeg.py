#!/usr/bin/env python
"""Deterministic fallback MP4 cut renderer using FFmpeg.

Constructs a single filtergraph (trim/atrim per segment -> concat),
using exact frame bounds (trim=start_frame=X:end_frame=Y) for video
and sample-exact timestamps derived from Fraction(frame, fps) for audio (Fix 12).
Encodes to H.264 + AAC with -fps_mode passthrough (never -r to avoid duplicated frames),
verifies the rendered output's frame count against cuts.json via ffprobe (exits 1 if None),
and asserts A/V length match within a 1.5-frame tolerance. fps comes from cuts.json (no default) and must equal
the source's fps; segments past the source's last frame are rejected.

Usage:
  python render_cut_ffmpeg.py --cuts cuts.json --out cut.mp4 [--media source.mp4]
"""
import argparse
from fractions import Fraction
import json
import math
import os
import subprocess
import sys


def require_fps(cuts_data):
    """fps_num/fps_den are mandatory in cuts.json: a silent default corrupts every frame position."""
    fn, fd = cuts_data.get("fps_num"), cuts_data.get("fps_den")
    if not isinstance(fn, int) or not isinstance(fd, int) or fn <= 0 or fd <= 0:
        raise ValueError(f"cuts.json has no valid fps_num/fps_den (got {fn!r}/{fd!r}); refusing to guess a frame rate")
    return Fraction(fn, fd)


def probe_source_frames(source_path):
    """ffprobe the source video. Returns (frame_count, fps Fraction). No default fps: raises if unreadable."""
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate,nb_frames,duration", "-show_entries", "format=duration",
        "-of", "json", source_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise ValueError(f"ffprobe failed for '{source_path}': {proc.stderr.strip()}")
    data = json.loads(proc.stdout)
    streams = data.get("streams") or []
    if not streams:
        raise ValueError(f"No video stream in '{source_path}'")
    st = streams[0]
    rate = st.get("r_frame_rate")
    if not rate or "/" not in rate or rate.startswith("0/"):
        raise ValueError(f"Source '{source_path}' reports no usable r_frame_rate ({rate!r})")
    num, den = map(int, rate.split("/"))
    fps = Fraction(num, den)
    nb = st.get("nb_frames")
    if nb and nb != "N/A":
        frames = int(nb)
    else:
        dur = float(st.get("duration") or data.get("format", {}).get("duration") or 0.0)
        frames = math.floor(dur * fps)
    return frames, fps


def check_against_source(segments, fps, source_path):
    """Reject a cut list whose frame rate differs from the source or whose segments run past the source's last frame."""
    frames, src_fps = probe_source_frames(source_path)
    if src_fps != fps:
        raise ValueError(f"cuts.json fps {fps} != source fps {src_fps} ({source_path})")
    for idx, seg in enumerate(segments):
        if seg["end_frame"] > frames:
            raise ValueError(
                f"Segment #{idx+1} end_frame {seg['end_frame']} is past the source's {frames} frames "
                f"(valid exclusive end <= {frames})"
            )
    return frames


def validate_cuts(cuts_data):
    """Validate internal cuts.json consistency."""
    segments = cuts_data.get("segments", [])
    if not segments:
        raise ValueError("No segments in cuts.json to render.")
    for idx, seg in enumerate(segments):
        sf = seg.get("start_frame")
        ef = seg.get("end_frame")
        df = seg.get("dur_frames")
        if sf is None or ef is None or df is None:
            raise ValueError(f"Segment #{idx+1} missing frame boundary fields (start_frame, end_frame, dur_frames)")
        if df != (ef - sf):
            raise ValueError(
                f"Segment #{idx+1} internal inconsistency: dur_frames ({df}) != end_frame ({ef}) - start_frame ({sf})"
            )
        if df <= 0:
            raise ValueError(f"Segment #{idx+1} has non-positive duration: {df} frames")
        if idx > 0:
            prev_ef = segments[idx - 1]["end_frame"]
            if sf < prev_ef:
                raise ValueError(
                    f"Segment #{idx+1} source start_frame ({sf}) is before previous segment end_frame ({prev_ef}) (non-monotonic/overlapping source order)"
                )


def probe_rendered_media(video_path):
    """Retrieve video frames, video duration, audio duration, and fps from rendered media."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-count_frames",
        "-show_entries",
        "stream=index,codec_type,nb_read_frames,nb_frames,duration,r_frame_rate",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        video_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(proc.stdout)
    streams = data.get("streams", [])
    format_dur = float(data.get("format", {}).get("duration", 0.0))

    v_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})

    v_nb = v_stream.get("nb_read_frames") or v_stream.get("nb_frames")
    landed_frames = int(v_nb) if (v_nb and v_nb != "N/A") else None

    v_dur = float(v_stream.get("duration") or format_dur)
    a_dur = float(a_stream.get("duration") or format_dur)
    r_rate = v_stream.get("r_frame_rate", "")

    return landed_frames, v_dur, a_dur, r_rate


def main():
    ap = argparse.ArgumentParser(description="Render frame-accurate cut MP4 via FFmpeg single filtergraph.")
    ap.add_argument("--cuts", required=True, help="Input cuts.json")
    ap.add_argument("--out", required=True, help="Output MP4 file path")
    ap.add_argument("--media", help="Optional override for source video path")
    ap.add_argument("--crf", type=int, default=18, help="H.264 CRF quality (default: 18)")
    ap.add_argument("--preset", default="fast", help="x264 preset (default: fast)")

    args = ap.parse_args()

    with open(args.cuts, "r", encoding="utf-8") as f:
        cuts_data = json.load(f)

    try:
        validate_cuts(cuts_data)
    except ValueError as e:
        sys.exit(f"Invalid cuts.json: {e}")

    source_path = os.path.abspath(args.media or cuts_data.get("source"))
    if not os.path.exists(source_path):
        sys.exit(f"Source video not found: {source_path}")

    segments = cuts_data["segments"]
    try:
        fps_ratio = require_fps(cuts_data)
        check_against_source(segments, fps_ratio, source_path)
    except ValueError as e:
        sys.exit(f"Invalid cuts.json: {e}")

    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Build single filtergraph using exact frame boundaries for video and
    # sample-exact timestamps derived from Fraction(frame, fps) for audio (Fix 12)
    v_parts = []
    a_parts = []
    concat_inputs = []

    for idx, seg in enumerate(segments):
        sf = seg["start_frame"]
        ef = seg["end_frame"]

        # Sample-exact audio timestamps derived from rational Fraction(frame, fps)
        start_sec = float(Fraction(sf, 1) / fps_ratio)
        end_sec = float(Fraction(ef, 1) / fps_ratio)

        v_label = f"v{idx}"
        a_label = f"a{idx}"

        v_parts.append(f"[0:v]trim=start_frame={sf}:end_frame={ef},setpts=PTS-STARTPTS[{v_label}]")
        a_parts.append(f"[0:a]atrim=start={start_sec:.6f}:end={end_sec:.6f},asetpts=PTS-STARTPTS[{a_label}]")
        concat_inputs.append(f"[{v_label}][{a_label}]")

    n = len(segments)
    concat_filter = f"{''.join(concat_inputs)}concat=n={n}:v=1:a=1[outv][outa]"
    filter_complex = f"{';'.join(v_parts)};{';'.join(a_parts)};{concat_filter}"

    cmd = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-i",
        source_path,
        "-filter_complex",
        filter_complex,
        "-map",
        "[outv]",
        "-map",
        "[outa]",
        "-c:v",
        "libx264",
        "-preset",
        args.preset,
        "-crf",
        str(args.crf),
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-fps_mode",
        "passthrough",
        out_path,
    ]

    print(f"Rendering {n} cuts from '{source_path}' to '{out_path}' via FFmpeg...")
    subprocess.run(cmd, check=True)

    # Verify frame count and A/V sync against cuts.json (Fix 12)
    planned_frames = sum(s["dur_frames"] for s in segments)
    landed_frames, v_dur, a_dur, r_rate = probe_rendered_media(out_path)

    # Exit non-zero if landed_frames is None (Fix 12)
    if landed_frames is None:
        print("ERROR: ffprobe could not determine landed video frame count.", file=sys.stderr)
        sys.exit(1)

    drift = abs(landed_frames - planned_frames)
    if drift != 0:
        print(
            f"ERROR: Frame count drift! Planned: {planned_frames}, Landed: {landed_frames} (drift: {drift})",
            file=sys.stderr,
        )
        sys.exit(1)

    # Assert A/V length with tolerance of 1.5 frames (AAC priming/padding makes exactly 1 frame too strict)
    one_frame_sec = float(Fraction(1, 1) / fps_ratio)
    av_diff = abs(v_dur - a_dur)
    if av_diff > (one_frame_sec * 1.5):
        print(
            f"ERROR: A/V length mismatch exceeds 1.5 frames! Video: {v_dur:.4f}s, Audio: {a_dur:.4f}s, "
            f"Diff: {av_diff:.4f}s > 1.5 frames ({one_frame_sec * 1.5:.4f}s)",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        f"Render VERIFIED: {out_path} ({landed_frames} frames, {r_rate}, "
        f"video={v_dur:.3f}s, audio={a_dur:.3f}s, delta={av_diff*1000:.1f}ms <= 1.5 frames)"
    )


if __name__ == "__main__":
    main()
