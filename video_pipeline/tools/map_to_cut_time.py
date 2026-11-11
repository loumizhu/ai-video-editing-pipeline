#!/usr/bin/env python3
"""map_to_cut_time.py - Map source timestamps or transcript word indices to cut-timeline time and frames.

Uses cuts.json kept segments to map a source-time anchor onto the cut timeline.
If the requested anchor falls within removed material, it raises an error and lists valid ranges.
Also provides word listing utility to inspect transcript word indices.
"""

import argparse
from fractions import Fraction
import json
import os
import sys

TICKS_PER_SEC = 254016000000
RESOLVE_START_FRAME = 86400  # 01:00:00:00 at 24/23.976 fps


def parse_fps(cuts_data, override_fps=None):
    if override_fps:
        if "/" in str(override_fps):
            num, den = map(int, str(override_fps).split("/"))
            return Fraction(num, den)
        return Fraction(float(override_fps)).limit_denominator(10000)

    fn = cuts_data.get("fps_num")
    fd = cuts_data.get("fps_den")
    if isinstance(fn, int) and isinstance(fd, int) and fn > 0 and fd > 0:
        return Fraction(fn, fd)

    fps_val = cuts_data.get("fps")
    if fps_val:
        if "/" in str(fps_val):
            num, den = map(int, str(fps_val).split("/"))
            return Fraction(num, den)
        return Fraction(float(fps_val)).limit_denominator(10000)

    return Fraction(24000, 1001)


def list_words(words_path, as_json=False):
    if not os.path.exists(words_path):
        raise FileNotFoundError(f"words.json not found: {words_path}")
    with open(words_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    words = data.get("words", [])
    if as_json:
        print(json.dumps([{"index": idx, **w} for idx, w in enumerate(words)], indent=2))
    else:
        for idx, w in enumerate(words):
            word_txt = w.get("word", "")
            start = w.get("start", 0.0)
            end = w.get("end", 0.0)
            print(f"[{idx:4d}] {word_txt:<24} ({start:7.3f}s - {end:7.3f}s)")
    return len(words)


SNAP_TOLERANCE_S = 0.15  # cuts are snapped into a word, so an anchor word may start slightly outside its kept range


def map_source_time_to_cut(cuts_data, source_time, override_fps=None, snap_tol=SNAP_TOLERANCE_S):
    segments = cuts_data.get("segments", [])
    if not segments:
        raise ValueError("cuts.json contains no segments")

    fps_ratio = parse_fps(cuts_data, override_fps)
    fps_float = float(fps_ratio)

    prior_frames = 0
    prior_seconds = 0.0

    for idx, seg in enumerate(segments):
        start = seg.get("start", 0.0)
        end = seg.get("end", 0.0)
        dur_f = seg.get("dur_frames", int(round((end - start) * fps_float)))
        dur_s = seg.get("dur_s", dur_f / fps_float)

        # Allow small epsilon tolerance for edge alignment
        if (start - 0.001) <= source_time <= (end + 0.001):
            offset_s = max(0.0, min(source_time - start, dur_s))
            timeline_time_s = prior_seconds + offset_s
            timeline_frame = prior_frames + int(round(offset_s * fps_float))
            ticks = int(round(timeline_time_s * TICKS_PER_SEC))
            resolve_record_frame = RESOLVE_START_FRAME + timeline_frame

            return {
                "source_time_s": round(source_time, 4),
                "cut_index": idx + 1,
                "segment_note": seg.get("note", ""),
                "segment_start_s": round(start, 4),
                "segment_end_s": round(end, 4),
                "offset_in_segment_s": round(offset_s, 4),
                "timeline_time_s": round(timeline_time_s, 4),
                "timeline_frame": timeline_frame,
                "timeline_ticks": ticks,
                "resolve_record_frame": resolve_record_frame,
                "fps": str(fps_ratio),
                "fps_float": round(fps_float, 4),
            }

        prior_frames += dur_f
        prior_seconds += dur_s

    # Not inside any kept range: snap to the nearest segment edge if it is within tolerance
    # (make_cuts snaps cut starts/ends into words, so the first word of a kept range can start a few ms earlier).
    best = None
    for seg in segments:
        for edge in (seg.get("start", 0.0), seg.get("end", 0.0)):
            gap = abs(source_time - edge)
            if gap <= snap_tol and (best is None or gap < best[0]):
                best = (gap, edge)
    if best is not None:
        result = map_source_time_to_cut(cuts_data, best[1], override_fps, snap_tol=0.0)
        result["snapped_from_s"] = round(source_time, 4)
        result["snap_gap_s"] = round(best[0], 4)
        return result

    # Anchor falls in removed material
    kept_ranges = [f"Cut #{i+1}: [{s.get('start', 0.0):.3f}s..{s.get('end', 0.0):.3f}s]" for i, s in enumerate(segments)]
    raise ValueError(
        f"Anchor source time {source_time:.3f}s falls inside removed cut material (not present in any kept segment).\n"
        f"Kept ranges:\n  " + "\n  ".join(kept_ranges)
    )


def main():
    parser = argparse.ArgumentParser(description="Map source time or word index to cut-timeline position.")
    parser.add_argument("--cuts", help="Path to cuts.json")
    parser.add_argument("--source-time", type=float, help="Source time in seconds")
    parser.add_argument("--word-index", type=int, help="0-based word index in words.json")
    parser.add_argument("--words", help="Path to words.json (required if --word-index or --list-words)")
    parser.add_argument("--list-words", action="store_true", help="List all words and indices from words.json")
    parser.add_argument("--fps", help="Override FPS fraction (e.g. 24000/1001)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    args = parser.parse_args()

    if args.list_words:
        if not args.words:
            sys.exit("Error: --words <path/to/words.json> is required with --list-words")
        list_words(args.words, as_json=args.json)
        return

    if not args.cuts:
        sys.exit("Error: --cuts <path/to/cuts.json> is required for timeline mapping")

    if not os.path.exists(args.cuts):
        sys.exit(f"Error: cuts file not found: {args.cuts}")

    with open(args.cuts, "r", encoding="utf-8") as f:
        cuts_data = json.load(f)

    source_time = None
    anchor_info = ""

    if args.word_index is not None:
        if not args.words:
            sys.exit("Error: --words <path/to/words.json> is required with --word-index")
        if not os.path.exists(args.words):
            sys.exit(f"Error: words file not found: {args.words}")
        with open(args.words, "r", encoding="utf-8") as f:
            wdata = json.load(f)
        words = wdata.get("words", [])
        if args.word_index < 0 or args.word_index >= len(words):
            sys.exit(f"Error: word index {args.word_index} out of range [0..{len(words)-1}]")
        target_w = words[args.word_index]
        source_time = target_w.get("start", 0.0)
        anchor_info = f"Word [{args.word_index}] '{target_w.get('word')}' ({source_time:.3f}s)"
    elif args.source_time is not None:
        source_time = args.source_time
        anchor_info = f"Source time {source_time:.3f}s"
    else:
        sys.exit("Error: Specify either --source-time <sec> or --word-index <idx> (or --list-words)")

    try:
        result = map_source_time_to_cut(cuts_data, source_time, args.fps)
    except ValueError as e:
        sys.exit(f"Error: {e}")

    if args.json:
        result["anchor_info"] = anchor_info
        print(json.dumps(result, indent=2))
    else:
        print(f"--- Timeline Mapping for {anchor_info} ---")
        print(f"Landed Cut Segment : #{result['cut_index']} ('{result['segment_note']}')")
        print(f"Cut Timeline Time  : {result['timeline_time_s']:.4f} s")
        print(f"Cut Timeline Frame : {result['timeline_frame']} (at {result['fps']} fps)")
        print(f"FilmCraft Ticks    : {result['timeline_ticks']} ticks")
        print(f"Resolve RecordFrame: {result['resolve_record_frame']} (01:00:00:00 base)")


if __name__ == "__main__":
    main()
