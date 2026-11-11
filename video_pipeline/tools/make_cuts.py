#!/usr/bin/env python
"""Cut list generator and validator for video editing.

Converts word timestamps (words.json) and keep decisions (keep.json)
into a validated cut list (cuts.json) and an owner-reviewable markdown table (cuts_review.md).

Rules enforced:
  - Pad 0.08 s before first word and 0.12 s after last word of each kept piece (fallback path).
  - Waveform snap (default ON, uses the source audio; --no-snap to disable; --snap-audio to point at other audio):
      ASR word times run 40-60 ms late and abut each other, so a cut at a transcript word boundary
      is NOT a cut at a pause. Each kept piece's START moves to the lowest-energy frame boundary within
      [prev_word_end, word_start + 20 ms] and its END to the lowest-energy frame boundary within
      [word_end - 20 ms, next_word_start]. Energy = RMS of the 40 ms window that the edit exposes
      (after the start / before the end), computed from 10 ms-hop RMS of 16 kHz mono audio.
      The window may extend --snap-slop-ms (default 80) past the neighbour word's ASR time ONLY
      into audio quieter than --snap-floor-db (default -35 dBFS), so a cut word's energy is never entered.
  - Never reach into a word that is cut on the fallback path: clamp to ceil(prev_cut*fps) / floor(next_cut*fps),
    except that a kept word is never clipped (start <= floor(word_start*fps), end >= ceil(word_end*fps)).
  - Split close gaps symmetrically so no two pieces ever overlap.
  - Validate keep ranges: reject overlaps/duplicates with ValueError; merge adjacent index ranges.
  - Snap to whole frames at the source's exact rational fps (via ffprobe, no silent fallback).
  - Exclusive end frames: dur_frames = end_frame - start_frame.
  - Minimum segment length: 6 frames (configurable). Never extend into cut words; reject slivers.
  - Per-edge audit data in cuts.json ("edges") and a "Edit-point warnings" section in cuts_review.md:
    zero-pause edits (neighbouring words abut), edges whose exposed 40 ms energy is above -28 dBFS,
    and a remedy (2-frame audio crossfade, or the nearest word boundary that has a real pause).

Usage:
  python make_cuts.py --words words.json --keep keep.json --out cuts.json [--review cuts_review.md]
                      [--snap-audio media.mp4 | --no-snap] [--snap-slop-ms 80] [--snap-floor-db -35]
  python make_cuts.py --selftest
Exit codes: 0 ok, 1 media/IO error, 2 invalid input (overlapping keep ranges, sliver, bad indices).
"""
import argparse
from fractions import Fraction
import json
import math
import os
import subprocess
import sys
import tempfile

SPEECH_DB = -28.0  # same threshold cut_audit uses for "speech energy at the edit"


def get_media_fps(source_path):
    """Retrieve exact rational fps and duration from source file via ffprobe.

    No silent fallback: raises FileNotFoundError or RuntimeError if missing or unreadable.
    Prefers r_frame_rate, falls back to avg_frame_rate only if r_frame_rate is invalid.
    """
    if not source_path:
        raise ValueError("Source media path is required to determine frame rate.")
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source media file not found: {source_path}")

    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate,avg_frame_rate,duration",
        "-show_entries", "format=duration", "-of", "json", source_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed for '{source_path}':\n{proc.stderr.strip()}")

    data = json.loads(proc.stdout)
    streams = data.get("streams", [])
    if not streams:
        raise RuntimeError(f"No video streams found in '{source_path}'")

    stream = streams[0]
    r_rate = stream.get("r_frame_rate", "")
    avg_rate = stream.get("avg_frame_rate", "")

    rate_to_use = r_rate if (r_rate and r_rate != "0/0" and r_rate != "N/A") else avg_rate
    if not rate_to_use or rate_to_use in ("0/0", "N/A"):
        raise RuntimeError(f"Could not determine valid frame rate from '{source_path}' (r={r_rate}, avg={avg_rate})")

    if "/" in rate_to_use:
        num, den = map(int, rate_to_use.split("/"))
        if den == 0:
            raise RuntimeError(f"Invalid frame rate denominator 0 in '{rate_to_use}'")
        fps_ratio = Fraction(num, den)
        fps_str = rate_to_use
    else:
        flt = float(rate_to_use)
        fps_ratio = Fraction(flt).limit_denominator(10000)
        fps_str = str(fps_ratio)

    dur = float(stream.get("duration") or data.get("format", {}).get("duration", 0.0))
    return fps_ratio, fps_str, dur


# ---------------------------------------------------------------------------
# Audio energy envelope + waveform snap
# ---------------------------------------------------------------------------

def load_power_envelope(media_path, sr=16000, hop_ms=10):
    """Mean-square power per hop_ms bucket of 16 kHz mono audio (decoded via ffmpeg).

    Returns (power ndarray, hop_seconds). Raises RuntimeError when the media has no decodable audio.
    """
    import numpy as np

    if not os.path.exists(media_path):
        raise FileNotFoundError(f"Snap audio file not found: {media_path}")
    cmd = ["ffmpeg", "-v", "error", "-i", media_path, "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg audio decode failed for '{media_path}': {proc.stderr.decode(errors='ignore').strip()}")
    if not proc.stdout:
        raise RuntimeError(f"No audio stream in '{media_path}' (use --no-snap for silent media)")
    x = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    return power_from_samples(x, sr, hop_ms)


def power_from_samples(x, sr=16000, hop_ms=10):
    import numpy as np

    hop = int(round(sr * hop_ms / 1000.0))
    n = len(x) // hop
    if n == 0:
        raise RuntimeError("Audio shorter than one 10 ms hop")
    p = (x[: n * hop].astype(np.float64).reshape(n, hop) ** 2).mean(axis=1)
    return p, hop_ms / 1000.0


def window_db(power, hop_s, t, side, window_s=0.04):
    """dBFS (RMS) of the 40 ms window an edit at time t exposes: 'after' = [t, t+40ms), 'before' = [t-40ms, t)."""
    import numpy as np

    k = int(round(t / hop_s))
    w = int(round(window_s / hop_s))
    seg = power[k : k + w] if side == "after" else power[max(0, k - w) : max(0, k)]
    if len(seg) == 0:
        return -96.0
    m = float(np.mean(seg))
    if m <= 1e-10:
        return -96.0
    return 10.0 * math.log10(m)


def snap_edge(kind, power, hop_s, fps, spec_lo, spec_hi, slop, floor_db, tol_db, target_frame, min_frame, max_frame):
    """Pick the frame boundary with the quietest exposed 40 ms window.

    Candidates inside the spec window [spec_lo, spec_hi] are always allowed. Candidates in the slop
    extension (start: below spec_lo, end: above spec_hi) are allowed only if quieter than floor_db.
    Among candidates within tol_db of the quietest, the one nearest to target_frame wins.
    Returns {"frame", "db", "in_spec"} or None when no frame boundary qualifies.
    """
    fpsf = float(fps)
    if kind == "start":
        lo_f = math.ceil((spec_lo - slop) * fpsf - 1e-9)
        hi_f = math.floor(spec_hi * fpsf + 1e-9)
        side = "after"
    else:
        lo_f = math.ceil(spec_lo * fpsf - 1e-9)
        hi_f = math.floor((spec_hi + slop) * fpsf + 1e-9)
        side = "before"
    lo_f = max(lo_f, min_frame)
    if max_frame is not None:
        hi_f = min(hi_f, max_frame)
    cands = []
    for f in range(lo_f, hi_f + 1):
        t = f / fpsf
        db = window_db(power, hop_s, t, side)
        in_spec = (spec_lo - 1e-9) <= t <= (spec_hi + 1e-9)
        if in_spec or db <= floor_db:
            cands.append({"frame": f, "db": db, "in_spec": in_spec})
    if not cands:
        return None
    best = min(c["db"] for c in cands)
    pool = [c for c in cands if c["db"] <= best + tol_db]
    return min(pool, key=lambda c: (abs(c["frame"] - target_frame), c["frame"]))


# ---------------------------------------------------------------------------
# Keep-range validation
# ---------------------------------------------------------------------------

def validate_and_merge_keep_ranges(keep_ranges, num_words):
    """Sort, validate, and merge keep ranges.

    Raises ValueError on invalid indices, overlaps, or duplicates.
    Merges adjacent index ranges (next.from_word == prev.to_word + 1).
    """
    if not keep_ranges:
        return []

    sorted_keep = sorted(keep_ranges, key=lambda x: (x["from_word"], x.get("to_word", x["from_word"])))
    merged = []

    for k in sorted_keep:
        fw = k["from_word"]
        tw = k["to_word"]
        if fw < 0 or tw >= num_words or fw > tw:
            raise ValueError(f"Invalid keep range [{fw}..{tw}] for words length {num_words}")

        if not merged:
            merged.append(dict(k))
        else:
            prev = merged[-1]
            if fw <= prev["to_word"]:
                raise ValueError(
                    f"Overlapping or duplicate keep ranges: [{prev['from_word']}..{prev['to_word']}] and [{fw}..{tw}]"
                )
            elif fw == prev["to_word"] + 1:
                prev["to_word"] = tw
                prev_note = prev.get("note", "").strip()
                curr_note = k.get("note", "").strip()
                if curr_note:
                    prev["note"] = f"{prev_note}; {curr_note}".strip("; ")
            else:
                merged.append(dict(k))

    return merged


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

def _suggest_boundary(kind, words, fw, tw, lo_word, hi_word, power, hop_s, fps_ratio, slop, floor_db, tol_db):
    """Nearest word boundary (by word distance) that has a real pause; None if none within +-8 words."""
    n = len(words)
    fpsf = float(fps_ratio)
    for dist in range(1, 9):
        for j in (fw - dist, fw + dist) if kind == "start" else (tw - dist, tw + dist):
            if j < lo_word or j > hi_word or j < 0 or j >= n:
                continue
            if kind == "start":
                spec_lo = words[j - 1]["end"] if j > 0 else 0.0
                spec_hi = words[j]["start"] + 0.02
                tgt = round((words[j]["start"] - 0.08) * fpsf)
            else:
                spec_lo = words[j]["end"] - 0.02
                spec_hi = words[j + 1]["start"] if j < n - 1 else words[j]["end"] + 0.5
                tgt = round((words[j]["end"] + 0.12) * fpsf)
            c = snap_edge(kind, power, hop_s, fps_ratio, spec_lo, spec_hi, slop, floor_db, tol_db, tgt, 0, None)
            if c and c["db"] <= floor_db:
                return {"word": j, "text": words[j]["word"], "time_s": round(c["frame"] / fpsf, 3), "db": round(c["db"], 1)}
    return None


def compute_cuts(
    words,
    keep_ranges,
    fps_ratio,
    pad_before=0.08,
    pad_after=0.12,
    min_frames=6,
    media_duration=None,
    power=None,
    hop_s=0.01,
    snap_slop_s=0.08,
    snap_floor_db=-35.0,
    snap_tol_db=3.0,
    speech_db=SPEECH_DB,
):
    """Compute frame-accurate cut segments adhering to all padding and safety rules.

    When `power` (10 ms-hop mean-square envelope of the source audio) is given, edges are waveform-snapped.
    """
    num_words = len(words)
    if not keep_ranges or num_words == 0:
        return []

    merged_keep = validate_and_merge_keep_ranges(keep_ranges, num_words)
    fpsf = float(fps_ratio)
    one_frame_s = 1.0 / fpsf

    # First pass: raw boundaries and cut limits in seconds
    raw_pieces = []
    for k in merged_keep:
        fw = k["from_word"]
        tw = k["to_word"]
        raw_start = words[fw]["start"]
        raw_end = words[tw]["end"]
        text = " ".join(w["word"] for w in words[fw : tw + 1])
        prev_cut_limit = words[fw - 1]["end"] if fw > 0 else 0.0
        if tw < num_words - 1:
            next_cut_limit = words[tw + 1]["start"]
        else:
            next_cut_limit = media_duration if media_duration else (raw_end + pad_after + 10.0)
        raw_pieces.append(
            {
                "from_word": fw, "to_word": tw, "raw_start": raw_start, "raw_end": raw_end,
                "prev_cut_limit": prev_cut_limit, "next_cut_limit": next_cut_limit,
                "text": text, "note": k.get("note", ""),
            }
        )

    # Second pass: apply padding clamped to cut word boundaries
    padded_segments = []
    for p in raw_pieces:
        q = dict(p)
        q["start"] = max(p["raw_start"] - pad_before, p["prev_cut_limit"])
        q["end"] = min(p["raw_end"] + pad_after, p["next_cut_limit"])
        padded_segments.append(q)

    # Third pass: resolve close gaps between consecutive kept segments (split symmetrically)
    for i in range(len(padded_segments) - 1):
        seg1 = padded_segments[i]
        seg2 = padded_segments[i + 1]
        if seg1["end"] > seg2["start"]:
            mid = (seg1["raw_end"] + seg2["raw_start"]) / 2.0
            seg1["end"] = mid
            seg2["start"] = mid

    # Fourth pass: frame snapping
    final_segments = []
    last_end_frame = 0
    max_media_frames = math.floor(media_duration * fps_ratio) if media_duration else None

    for i, seg in enumerate(padded_segments):
        fw, tw = seg["from_word"], seg["to_word"]

        if fw > 0:
            min_start_frame = math.ceil(seg["prev_cut_limit"] * fps_ratio)
        else:
            min_start_frame = 0
        if tw < num_words - 1:
            max_end_frame = math.floor(seg["next_cut_limit"] * fps_ratio)
        elif max_media_frames is not None:
            max_end_frame = max_media_frames
        else:
            max_end_frame = round(seg["end"] * fps_ratio) + 1000

        # Pad-based fallback frames. A kept word is never clipped, even where it abuts a cut word.
        pad_start = max(round(seg["start"] * fps_ratio), min_start_frame)
        pad_start = min(pad_start, math.floor(seg["raw_start"] * fps_ratio))
        pad_end = min(round(seg["end"] * fps_ratio), max_end_frame)
        pad_end = max(pad_end, math.ceil(seg["raw_end"] * fps_ratio))
        if max_media_frames is not None:
            pad_end = min(pad_end, max_media_frames)

        start_frame, end_frame = pad_start, pad_end
        start_src = end_src = "pad"
        if power is not None:
            tgt_s = round(seg["start"] * fps_ratio)
            c = snap_edge(
                "start", power, hop_s, fps_ratio,
                spec_lo=seg["prev_cut_limit"], spec_hi=seg["raw_start"] + 0.02,
                slop=snap_slop_s, floor_db=snap_floor_db, tol_db=snap_tol_db,
                target_frame=tgt_s, min_frame=last_end_frame, max_frame=None,
            )
            if c:
                start_frame, start_src = c["frame"], "audio"
            tgt_e = round(seg["end"] * fps_ratio)
            c = snap_edge(
                "end", power, hop_s, fps_ratio,
                spec_lo=seg["raw_end"] - 0.02, spec_hi=seg["next_cut_limit"],
                slop=snap_slop_s, floor_db=snap_floor_db, tol_db=snap_tol_db,
                target_frame=tgt_e, min_frame=start_frame + 1, max_frame=max_media_frames,
            )
            if c:
                end_frame, end_src = c["frame"], "audio"

        # Non-overlap with previous kept segment
        if start_frame < last_end_frame:
            start_frame = last_end_frame
            start_src = "pad"

        # Min-frame enforcement: NEVER extend into a cut word.
        clamped_span = end_frame - start_frame
        if clamped_span < min_frames:
            shortfall = min_frames - clamped_span
            avail_end = max(0, max_end_frame - end_frame)
            add_end = min(shortfall, avail_end)
            end_frame += add_end
            shortfall -= add_end
            if shortfall > 0:
                avail_start = max(0, start_frame - max(min_start_frame, last_end_frame))
                sub_start = min(shortfall, avail_start)
                start_frame -= sub_start
                shortfall -= sub_start
            if (end_frame - start_frame) < min_frames:
                raise ValueError(
                    f"sliver: keep range [{fw}..{tw}] cannot reach {min_frames} frames "
                    f"without entering a cut word (clamped available frames: {end_frame - start_frame} for '{seg['text']}')"
                )

        # Edge audit data
        edges = {}
        for kind in ("start", "end"):
            frame = start_frame if kind == "start" else end_frame
            src = start_src if kind == "start" else end_src
            if kind == "start":
                nb = words[fw - 1] if fw > 0 else None
                gap = (seg["raw_start"] - nb["end"]) if nb else None
                nb_word = nb["word"] if nb else None
            else:
                nb = words[tw + 1] if tw < num_words - 1 else None
                gap = (nb["start"] - seg["raw_end"]) if nb else None
                nb_word = nb["word"] if nb else None
            e = {
                "source": src,
                "neighbor_word": nb_word,
                "gap_s": round(gap, 3) if gap is not None else None,
                "zero_pause": bool(gap is not None and gap < one_frame_s),
                "db": None,
                "clean": None,
                "remedy": None,
            }
            if power is not None:
                db = window_db(power, hop_s, frame / fpsf, "after" if kind == "start" else "before")
                e["db"] = round(db, 1)
                e["clean"] = db <= speech_db
                if not e["clean"]:
                    prev_to = final_segments[-1]["to_word"] if (kind == "start" and final_segments) else -1
                    nxt_from = padded_segments[i + 1]["from_word"] if i + 1 < len(padded_segments) else num_words
                    sug = _suggest_boundary(
                        kind, words, fw, tw,
                        lo_word=prev_to + 1 if kind == "start" else fw,
                        hi_word=tw if kind == "start" else nxt_from - 1,
                        power=power, hop_s=hop_s, fps_ratio=fps_ratio,
                        slop=snap_slop_s, floor_db=snap_floor_db, tol_db=snap_tol_db,
                    )
                    if kind == "start" and i == 0:
                        xf = "apply a 2-frame audio fade-in at the head"
                    elif kind == "end" and i == len(padded_segments) - 1:
                        xf = "apply a 2-frame audio fade-out at the tail"
                    else:
                        xf = "apply a 2-frame audio crossfade at this edit"
                    if sug:
                        e["remedy"] = (
                            f"{xf}, or move the keep boundary to word {sug['word']} ('{sug['text']}', "
                            f"{sug['time_s']}s, {sug['db']} dBFS pause)"
                        )
                    else:
                        e["remedy"] = f"{xf} (no pause within 8 words; speech is continuous here)"
            edges[kind] = e

        exact_start = float(Fraction(start_frame, 1) / fps_ratio)
        exact_end = float(Fraction(end_frame, 1) / fps_ratio)
        dur_frames = end_frame - start_frame

        final_segments.append(
            {
                "cut_index": i + 1,
                "start": round(exact_start, 3),
                "end": round(exact_end, 3),
                "start_frame": start_frame,
                "end_frame": end_frame,
                "dur_frames": dur_frames,
                "dur_s": round(float(Fraction(dur_frames, 1) / fps_ratio), 3),
                "text": seg["text"],
                "note": seg["note"],
                "from_word": fw,
                "to_word": tw,
                "edges": edges,
            }
        )
        last_end_frame = end_frame

    return final_segments


def collect_edit_warnings(segments):
    """Flat list of edit-point warnings: zero-pause edges and edges with speech energy at the cut."""
    out = []
    n = len(segments)
    for i, s in enumerate(segments):
        for kind in ("start", "end"):
            e = s.get("edges", {}).get(kind)
            if not e:
                continue
            if kind == "start" and i == 0:
                where = "head (start of cut)"
            elif kind == "end" and i == n - 1:
                where = "tail (end of cut)"
            elif kind == "end":
                where = f"edit {i + 1} (outgoing, after '{s['text'].split()[-1]}')"
            else:
                where = f"edit {i} (incoming, before '{s['text'].split()[0]}')"
            if e.get("clean") is False or e.get("zero_pause"):
                out.append({"cut": s["cut_index"], "edge": kind, "where": where, **e})
    return out


def generate_review_markdown(words, segments, cuts_file, review_path):
    """Generate owner-reviewable markdown table showing kept and removed text."""
    lines = [
        "# Cut List Review Document",
        f"**Cuts File:** `{os.path.basename(cuts_file)}`  ",
        f"**Total Kept Cuts:** {len(segments)}  ",
        f"**Total Kept Duration:** {sum(s['dur_s'] for s in segments):.2f}s ({sum(s['dur_frames'] for s in segments)} frames)  \n",
        "## Editorial Segments\n",
        "| Cut # | Kept Range (s) | Frames [In..Out) | Dur (s / f) | Kept Transcript | Removed Before Cut | Note |",
        "|:---:|:---:|:---:|:---:|:---|:---|:---|",
    ]

    last_word_idx = -1
    for s in segments:
        fw = s["from_word"]
        tw = s["to_word"]
        if last_word_idx + 1 < fw:
            removed_text = " ".join(w["word"] for w in words[last_word_idx + 1 : fw])
            if len(removed_text) > 60:
                removed_text = removed_text[:57] + "..."
        else:
            removed_text = "*(none / adjacent)*"

        range_s = f"{s['start']:.2f}s – {s['end']:.2f}s"
        frames_str = f"[{s['start_frame']}..{s['end_frame']})"
        dur_str = f"{s['dur_s']:.2f}s ({s['dur_frames']}f)"
        note = s.get("note", "") or "-"
        lines.append(
            f"| **{s['cut_index']}** | {range_s} | `{frames_str}` | {dur_str} | \"{s['text']}\" | *{removed_text}* | {note} |"
        )
        last_word_idx = tw

    if last_word_idx + 1 < len(words):
        trailing = " ".join(w["word"] for w in words[last_word_idx + 1 :])
        lines.append(f"\n**Trailing Removed Text:** *\"{trailing}\"*")

    warnings = collect_edit_warnings(segments)
    lines.append("\n## Edit-point warnings\n")
    if not warnings:
        lines.append("None: every edge is snapped to a pause and no neighbouring words abut.\n")
    else:
        lines.append(
            "Zero-pause = the transcript gives no gap between the kept word and its cut neighbour (ASR times abut and run "
            "40-60 ms late, so the transcript cannot prove a pause exists). Energy is the RMS of the 40 ms the edit exposes; "
            f"above {SPEECH_DB:.0f} dBFS it is speech and cut_audit will FAIL it.\n"
        )
        lines.append("| Where | Edge source | Gap to neighbour | Exposed 40 ms energy | Flags | Remedy |")
        lines.append("|:---|:---:|:---:|:---:|:---|:---|")
        for w in warnings:
            flags = []
            if w.get("zero_pause"):
                flags.append("zero-pause edit")
            if w.get("clean") is False:
                flags.append("SPEECH AT EDGE")
            gap = "-" if w.get("gap_s") is None else f"{w['gap_s']:.3f}s ('{w.get('neighbor_word')}')"
            db = "n/a (no audio)" if w.get("db") is None else f"{w['db']} dBFS"
            lines.append(
                f"| {w['where']} | {w['source']} | {gap} | {db} | {', '.join(flags)} | {w.get('remedy') or 'verify by ear'} |"
            )
        lines.append("")

    content = "\n".join(lines) + "\n"
    with open(review_path, "w", encoding="utf-8") as f:
        f.write(content)
    return content


# ---------------------------------------------------------------------------
# Self-test (literal, hand-computed expectations; no tautologies; artifacts in a tempdir)
# ---------------------------------------------------------------------------

def _synth_power(segments_db, total_s, sr=16000, hop_ms=10):
    """Build a power envelope from [(t0, t1, dBFS)] blocks (rest = -80 dBFS). Pure numpy, no ffmpeg."""
    import numpy as np

    n = int(round(total_s * 1000 / hop_ms))
    p = np.full(n, 10 ** (-80 / 10.0))
    for t0, t1, db in segments_db:
        p[int(round(t0 * 100)) : int(round(t1 * 100))] = 10 ** (db / 10.0)
    return p, hop_ms / 1000.0


def run_selftest():
    """Self-test: literal expected frames, fps fraction in output, reason strings, CLI errors. Artifacts go to a tempdir."""
    print("Running make_cuts.py self-test suite...")
    fps_ratio = Fraction(24000, 1001)

    mock_words = [
        {"word": "Hello", "start": 10.0, "end": 10.5},      # 0
        {"word": "world", "start": 12.0, "end": 12.5},      # 1
        {"word": "tight1", "start": 15.00, "end": 15.10},   # 2 cut
        {"word": "tightKeep", "start": 15.15, "end": 15.20},# 3 keep (50 ms gaps both sides)
        {"word": "tight2", "start": 15.25, "end": 15.35},   # 4 cut
        {"word": "adjA", "start": 20.0, "end": 20.5},       # 5
        {"word": "adjB", "start": 20.55, "end": 21.0},      # 6 adjacent to 5
        {"word": "gapA", "start": 25.0, "end": 25.1},       # 7 kept
        {"word": "cutMiddle", "start": 25.14, "end": 25.16},# 8 cut word in between
        {"word": "gapB", "start": 25.20, "end": 25.3},      # 9 kept
        {"word": "single", "start": 30.0, "end": 30.05},    # 10
    ]

    # TC1: pad values with LITERAL expected frames (hand computed at 24000/1001):
    #   start: (10.00-0.08)=9.92 s * 23.976024 = 237.84 -> 238 ; end: (10.5+0.12)=10.62 s * 23.976024 = 254.63 -> 255
    res1 = compute_cuts(mock_words, [{"from_word": 0, "to_word": 0}], fps_ratio, min_frames=1)
    assert (res1[0]["start_frame"], res1[0]["end_frame"], res1[0]["dur_frames"]) == (238, 255, 17), (
        f"TC1: expected (238, 255, 17), got {(res1[0]['start_frame'], res1[0]['end_frame'], res1[0]['dur_frames'])}"
    )
    print("  [PASS] TC1: literal pad frames 238..255 (17 f) at 24000/1001")

    # TC2: kept word 50 ms from cut neighbours cannot reach 6 frames -> sliver, reason string asserted
    try:
        compute_cuts(mock_words, [{"from_word": 3, "to_word": 3}], fps_ratio, min_frames=6)
        raise AssertionError("TC2: expected ValueError")
    except ValueError as e:
        assert str(e).startswith("sliver: keep range [3..3] cannot reach 6 frames without entering a cut word"), str(e)
    print("  [PASS] TC2: sliver rejected with reason 'sliver: keep range [3..3] cannot reach 6 frames ...'")

    # TC3: overlap / duplicate raise with both ranges named
    try:
        compute_cuts(mock_words, [{"from_word": 0, "to_word": 2}, {"from_word": 1, "to_word": 4}], fps_ratio)
        raise AssertionError("TC3: expected ValueError")
    except ValueError as e:
        assert str(e) == "Overlapping or duplicate keep ranges: [0..2] and [1..4]", str(e)
    try:
        compute_cuts(mock_words, [{"from_word": 5, "to_word": 6}, {"from_word": 5, "to_word": 6}], fps_ratio)
        raise AssertionError("TC3: expected ValueError")
    except ValueError as e:
        assert str(e) == "Overlapping or duplicate keep ranges: [5..6] and [5..6]", str(e)
    print("  [PASS] TC3: overlap and duplicate raise ValueError naming both ranges")

    # TC4: adjacent index ranges merge into one piece with literal frames
    #   start 19.92 s -> 477.6 -> 478 ; end 21.12 s -> 506.4 -> 506 ; floor/ceil guards: floor(20.0*fps)=479, ceil(21.0*fps)=504 (no effect)
    res4 = compute_cuts(
        mock_words, [{"from_word": 5, "to_word": 5, "note": "first"}, {"from_word": 6, "to_word": 6, "note": "second"}],
        fps_ratio, min_frames=6,
    )
    assert len(res4) == 1 and (res4[0]["from_word"], res4[0]["to_word"]) == (5, 6)
    assert (res4[0]["start_frame"], res4[0]["end_frame"]) == (478, 506), (res4[0]["start_frame"], res4[0]["end_frame"])
    assert res4[0]["note"] == "first; second"
    print("  [PASS] TC4: adjacent merge -> one piece [478..506), notes joined")

    # TC5: close gap (kept 7 and 9, cut word 8 between): no overlap, literal split frame
    #   Hand computation at 23.976024 fps: piece 1 start 24.92 s -> 597.48 -> 597. Padded ends collide, so the gap splits at
    #   mid = (25.1+25.2)/2 = 25.15 s -> 603 f, but the cut word 8 starts at 25.14 s (602.76 f), so piece 1 ends at floor = 602.
    #   Piece 2 starts at ceil(25.16 s = 603.24 f) = 604 (cut word end), ends 25.42 s -> 609.47 -> 609.
    res5 = compute_cuts(mock_words, [{"from_word": 7, "to_word": 7}, {"from_word": 9, "to_word": 9}], fps_ratio, min_frames=1)
    got5 = [(s["start_frame"], s["end_frame"]) for s in res5]
    assert got5 == [(597, 602), (604, 609)], got5
    print("  [PASS] TC5: close gap around a cut word -> [597..602) and [604..609), no overlap")

    # TC6: single short word in silence, min_frames=6 -> exact literal: start 29.92 s*23.976=717.3->717 ; end 30.17 s*23.976=723.3->723 => 6 f
    res6 = compute_cuts(mock_words, [{"from_word": 10, "to_word": 10}], fps_ratio, min_frames=6)
    assert (res6[0]["start_frame"], res6[0]["end_frame"], res6[0]["dur_frames"]) == (717, 723, 6), res6[0]
    print("  [PASS] TC6: single-word keep -> exactly [717..723) = 6 f")

    # TC7: waveform snap on synthetic audio (abutting words, real pause 90 ms before the onset, speech tail after the end)
    #   words (24 fps): cutA 0.50-1.00 | keepB 1.00-1.60 (ASR abuts both sides) | cutC 1.60-2.20
    #   audio: cutA speech 0.50-0.93, silence 0.93-1.03, keepB speech 1.03-1.55, silence 1.55-1.70, cutC speech 1.70-2.20
    #   Start: frame 24 (1.000 s) exposes [1.00,1.04) which already holds 10 ms of onset (-26 dB); frame 23 (0.958 s) exposes
    #   [0.96,1.00), pure silence, and lies 42 ms before the ASR start, inside the 80 ms slop and quiet -> 23.
    #   End: frame 38 (1.583 s) exposes [1.54,1.58) with 10 ms of speech (-26 dB); frame 39 (1.625 s) exposes pure silence -> 39.
    snap_words = [
        {"word": "cutA", "start": 0.50, "end": 1.00},
        {"word": "keepB", "start": 1.00, "end": 1.60},
        {"word": "cutC", "start": 1.60, "end": 2.20},
    ]
    p, hs = _synth_power([(0.50, 0.93, -20), (1.03, 1.55, -20), (1.70, 2.2, -20)], 3.0)
    fps24 = Fraction(24, 1)
    rs = compute_cuts(snap_words, [{"from_word": 1, "to_word": 1}], fps24, min_frames=1, media_duration=3.0, power=p, hop_s=hs)
    s = rs[0]
    assert (s["start_frame"], s["end_frame"]) == (23, 39), (s["start_frame"], s["end_frame"])
    # same words with snapping off: start at the ASR boundary, frame 24; end clamps at floor(1.60*24)=38 but the kept
    # word is protected up to ceil(1.60*24)=39
    ns = compute_cuts(snap_words, [{"from_word": 1, "to_word": 1}], fps24, min_frames=1, media_duration=3.0)
    assert (ns[0]["start_frame"], ns[0]["end_frame"]) == (24, 39), (ns[0]["start_frame"], ns[0]["end_frame"])
    assert s["edges"]["start"]["source"] == "audio" and s["edges"]["end"]["source"] == "audio"
    assert s["edges"]["start"]["zero_pause"] is True and s["edges"]["end"]["zero_pause"] is True
    assert s["edges"]["start"]["clean"] is True and s["edges"]["end"]["clean"] is True
    print("  [PASS] TC7: abutting ASR words snap to real pauses: start 23 (pad-only: 24), end 39, both edges clean, zero-pause flagged")

    # TC8: continuous speech -> cannot be clean; flagged with a remedy string; never reports clean
    p2, hs2 = _synth_power([(0.0, 3.0, -20)], 3.0)
    r2 = compute_cuts(snap_words, [{"from_word": 1, "to_word": 1}], fps24, min_frames=1, media_duration=3.0, power=p2, hop_s=hs2)
    e2 = r2[0]["edges"]
    assert e2["start"]["clean"] is False and e2["end"]["clean"] is False
    assert e2["start"]["remedy"].startswith("apply a 2-frame audio fade-in at the head"), e2["start"]["remedy"]
    assert e2["end"]["remedy"].startswith("apply a 2-frame audio fade-out at the tail"), e2["end"]["remedy"]
    assert "no pause within 8 words" in e2["start"]["remedy"], e2["start"]["remedy"]
    # an interior edit gets the crossfade wording
    r2b = compute_cuts(snap_words + [{"word": "cutD", "start": 2.2, "end": 2.8}], [{"from_word": 0, "to_word": 0}, {"from_word": 2, "to_word": 2}],
                       fps24, min_frames=1, media_duration=3.0, power=p2, hop_s=hs2)
    assert r2b[0]["edges"]["end"]["remedy"].startswith("apply a 2-frame audio crossfade at this edit"), r2b[0]["edges"]["end"]["remedy"]
    assert len(collect_edit_warnings(r2)) == 2
    print("  [PASS] TC8: continuous speech -> both edges flagged SPEECH AT EDGE with crossfade remedy")

    # TC9: remedy proposes a real pause when one exists nearby
    nine = [
        {"word": "a", "start": 0.0, "end": 0.5}, {"word": "b", "start": 0.5, "end": 1.0},
        {"word": "c", "start": 1.0, "end": 1.5}, {"word": "d", "start": 1.5, "end": 2.0},
        {"word": "e", "start": 2.0, "end": 2.5},
    ]
    p3, hs3 = _synth_power([(0.0, 0.9, -20), (1.2, 3.0, -20)], 3.0)  # pause 0.9-1.2 s
    r3 = compute_cuts(nine, [{"from_word": 1, "to_word": 3}], fps24, min_frames=1, media_duration=3.0, power=p3, hop_s=hs3)
    # starting at word 1 (0.5 s) is inside speech; the pause is before word 2 (1.0 s)
    st = r3[0]["edges"]["start"]
    assert st["clean"] is False and "move the keep boundary to word 2" in st["remedy"], st["remedy"]
    print(f"  [PASS] TC9: remedy names the nearest real pause: {st['remedy']}")

    # TC10: end-to-end CLI on generated media at 24000/1001 (tempdir): fps fraction in output + independent ffprobe frame count
    with tempfile.TemporaryDirectory(prefix="make_cuts_selftest_") as td:
        media = os.path.join(td, "m.mp4")
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=gray:s=160x90:r=24000/1001:d=35",
             "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", "-t", "35", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", media],
            check=True,
        )
        words_path = os.path.join(td, "words.json")
        keep_path = os.path.join(td, "keep.json")
        cuts_path = os.path.join(td, "out", "cuts.json")
        with open(words_path, "w", encoding="utf-8") as f:
            json.dump({"source": media, "words": mock_words}, f)
        with open(keep_path, "w", encoding="utf-8") as f:
            json.dump({"keep": [{"from_word": 0, "to_word": 0}, {"from_word": 10, "to_word": 10}]}, f)
        proc = subprocess.run(
            [sys.executable, os.path.abspath(__file__), "--words", words_path, "--keep", keep_path, "--out", cuts_path],
            capture_output=True, text=True,
        )
        assert proc.returncode == 0, proc.stderr
        cuts = json.load(open(cuts_path, encoding="utf-8"))
        assert (cuts["fps"], cuts["fps_num"], cuts["fps_den"]) == ("24000/1001", 24000, 1001), cuts["fps"]
        got = [(s["start_frame"], s["end_frame"], s["dur_frames"]) for s in cuts["segments"]]
        assert got == [(238, 255, 17), (717, 723, 6)], got  # hand-computed literals (silent audio: snap prefers pad target)
        assert cuts["total_frames"] == 23
        # independent frame count: render with ffmpeg trim and count frames with ffprobe
        out_mp4 = os.path.join(td, "r.mp4")
        render = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "render_cut_ffmpeg.py"),
             "--cuts", cuts_path, "--out", out_mp4],
            capture_output=True, text=True,
        )
        assert render.returncode == 0, render.stderr
        pr = subprocess.run(
            ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames",
             "-of", "default=nw=1:nk=1", out_mp4], capture_output=True, text=True, check=True)
        assert int(pr.stdout.strip()) == 23, pr.stdout
        review = open(os.path.join(td, "out", "cuts_review.md"), encoding="utf-8").read()
        assert "## Edit-point warnings" in review
        print("  [PASS] TC10: CLI writes fps 24000/1001, frames [(238,255),(717,723)]; ffprobe counts 23 rendered frames")

        # TC11: CLI turns ValueError into a clean error, exit 2, no traceback
        with open(keep_path, "w", encoding="utf-8") as f:
            json.dump({"keep": [{"from_word": 0, "to_word": 2}, {"from_word": 1, "to_word": 4}]}, f)
        bad = subprocess.run(
            [sys.executable, os.path.abspath(__file__), "--words", words_path, "--keep", keep_path, "--out", cuts_path],
            capture_output=True, text=True,
        )
        assert bad.returncode == 2, bad.returncode
        assert "Traceback" not in bad.stderr
        assert "Overlapping or duplicate keep ranges: [0..2] and [1..4]" in bad.stderr, bad.stderr
        print("  [PASS] TC11: overlapping keep -> exit 2, clean message, no traceback")

    print("ALL 11 SELF-TEST CASES PASSED CLEANLY.")


def main():
    ap = argparse.ArgumentParser(description="Make frame-accurate cuts list from words and keep decisions.")
    ap.add_argument("--words", help="Input words.json")
    ap.add_argument("--keep", help="Input keep.json")
    ap.add_argument("--out", help="Output cuts.json")
    ap.add_argument("--review", help="Output cuts_review.md")
    ap.add_argument("--source", help="Optional override for source video path")
    ap.add_argument("--min-frames", type=int, default=6, help="Minimum segment frame length (default: 6)")
    ap.add_argument("--pad-before", type=float, default=0.08, help="Seconds before first word (default: 0.08)")
    ap.add_argument("--pad-after", type=float, default=0.12, help="Seconds after last word (default: 0.12)")
    ap.add_argument("--snap-audio", help="Media file whose audio drives the waveform snap (default: the source video)")
    ap.add_argument("--no-snap", action="store_true", help="Disable waveform snapping (pad-only edges)")
    ap.add_argument("--snap-slop-ms", type=float, default=80.0, help="How far past a neighbour word's ASR time the snap may look, only into audio below --snap-floor-db (default: 80)")
    ap.add_argument("--snap-floor-db", type=float, default=-35.0, help="Quiet floor for slop candidates, dBFS (default: -35)")
    ap.add_argument("--selftest", action="store_true", help="Run self-tests and exit")

    args = ap.parse_args()

    if args.selftest:
        run_selftest()
        sys.exit(0)

    if not args.words or not args.keep or not args.out:
        ap.error("--words, --keep, and --out are required unless --selftest is passed.")

    with open(args.words, "r", encoding="utf-8") as f:
        words_data = json.load(f)
    with open(args.keep, "r", encoding="utf-8") as f:
        keep_data = json.load(f)

    words = words_data.get("words", [])
    keep_list = keep_data.get("keep", [])

    source_path = args.source or words_data.get("source")
    if not source_path:
        sys.exit("Error: No source media path provided via --source or inside words.json")

    try:
        fps_ratio, fps_str, duration = get_media_fps(source_path)
    except Exception as e:
        sys.exit(f"Error reading media frame rate: {e}")

    power, hop_s = None, 0.01
    if not args.no_snap:
        snap_media = args.snap_audio or source_path
        try:
            power, hop_s = load_power_envelope(snap_media)
        except Exception as e:
            sys.exit(f"Error loading audio for waveform snap: {e}")

    try:
        segments = compute_cuts(
            words, keep_list, fps_ratio,
            pad_before=args.pad_before, pad_after=args.pad_after, min_frames=args.min_frames,
            media_duration=duration, power=power, hop_s=hop_s,
            snap_slop_s=args.snap_slop_ms / 1000.0, snap_floor_db=args.snap_floor_db,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    cuts_payload = {
        "source": os.path.abspath(source_path),
        "fps": fps_str,
        "fps_num": fps_ratio.numerator,
        "fps_den": fps_ratio.denominator,
        "source_duration_s": round(duration, 3),
        "snap": {
            "enabled": power is not None,
            "audio": os.path.abspath(args.snap_audio or source_path) if power is not None else None,
            "slop_ms": args.snap_slop_ms,
            "floor_db": args.snap_floor_db,
        },
        "total_segments": len(segments),
        "total_frames": sum(s["dur_frames"] for s in segments),
        "total_duration_s": round(sum(s["dur_s"] for s in segments), 3),
        "segments": segments,
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(cuts_payload, f, indent=2)

    review_path = args.review or os.path.splitext(args.out)[0] + "_review.md"
    generate_review_markdown(words, segments, args.out, review_path)

    warnings = collect_edit_warnings(segments)
    n_zero = sum(1 for w in warnings if w.get("zero_pause"))
    n_speech = sum(1 for w in warnings if w.get("clean") is False)
    print(
        f"Built {len(segments)} cuts ({cuts_payload['total_frames']} frames, {cuts_payload['total_duration_s']}s) "
        f"-> {args.out} (review: {review_path}); edge warnings: {n_zero} zero-pause, {n_speech} with speech energy at the edit"
    )


if __name__ == "__main__":
    main()
