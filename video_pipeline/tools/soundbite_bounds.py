"""Snap a soundbite's in/out to clean sentence boundaries AND to the quietest point between words.

Rules (owner, 2026-11-08: "clip caught mid sentence"):
  1. The first kept word starts a sentence (the word before it ends with . ? !), the last kept word ends one.
     Exception `partial=True` (a VO line hands over mid-sentence on purpose): only rule 2 applies.
  2. No cut inside a word: the cut sits in the gap between two words, at the lowest-energy 10 ms in that gap
     (Whisper word times drift, so the gap is widened by 0.12 s and checked on the waveform).
  3. Breathing room: up to 0.25 s before the first word and 0.30 s after the last word when the gap allows.
CLI:  python soundbite_bounds.py <media> <words.json> <approx_in> <approx_out> [--partial]
"""
import json, subprocess, sys

import numpy as np

SR = 16000
END = (".", "?", "!", '."', '?"', '!"')


def _pcm(media, t0, t1):
    t0 = max(0.0, t0)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{max(0.02, t1 - t0):.3f}", "-i", media, "-ac", "1", "-ar", str(SR),
                          "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32), t0


def quietest(media, a, b):
    """Time of the lowest-RMS 10 ms window inside [a, b]."""
    if b - a < 0.02:
        return (a + b) / 2
    x, t0 = _pcm(media, a, b)
    win = int(SR * 0.01)
    if len(x) < win * 2:
        return (a + b) / 2
    n = len(x) // win
    rms = np.sqrt((x[: n * win].reshape(n, win) ** 2).mean(axis=1))
    k = int(np.argmin(rms))
    return t0 + (k + 0.5) * win / SR


def _w(x):
    return (x.get("word") or x.get("text") or "").strip()


def snap(media, words, approx_in, approx_out, partial=False, media_dur=None):
    ws = [w for w in words if _w(w)]
    # first word: nearest word start to approx_in that begins a sentence (unless partial)
    cand = [i for i, w in enumerate(ws) if w["start"] >= approx_in - (0.05 if partial else 0.6)]
    i0 = cand[0]
    if not partial:
        while i0 > 0 and not _w(ws[i0 - 1]).endswith(END):
            # walk forward to the next sentence start if close, else backward
            nxt = next((j for j in range(i0, len(ws)) if j > 0 and _w(ws[j - 1]).endswith(END)), None)
            if nxt is not None and ws[nxt]["start"] - approx_in < 2.0:
                i0 = nxt
                break
            i0 -= 1
    cand = [i for i, w in enumerate(ws) if w["end"] <= approx_out + 0.15]
    i1 = cand[-1]
    while i1 > i0 and not _w(ws[i1]).endswith(END):
        i1 -= 1
    prev_end = ws[i0 - 1]["end"] if i0 > 0 else 0.0
    next_start = ws[i1 + 1]["start"] if i1 + 1 < len(ws) else (media_dur or ws[i1]["end"] + 1.0)
    first, last = ws[i0]["start"], ws[i1]["end"]
    # in-point: inside the gap before the first word, quietest spot, at most 0.25 s ahead of it
    lo = max(prev_end - 0.12, first - 0.25) if i0 > 0 else max(0.0, first - 0.25)
    t_in = quietest(media, lo, first + 0.06) if i0 > 0 else lo
    t_in = min(t_in, first)
    hi = min(next_start + 0.12, last + 0.30)
    if media_dur:
        hi = min(hi, media_dur - 0.02)
    t_out = quietest(media, last - 0.06, hi) if i1 + 1 < len(ws) else hi
    t_out = max(t_out, last)
    return {"in": round(t_in, 3), "out": round(t_out, 3), "first": _w(ws[i0]), "last": _w(ws[i1]),
            "text": " ".join(_w(w) for w in ws[i0:i1 + 1]), "gap_before": round(first - prev_end, 3), "gap_after": round(next_start - last, 3)}


if __name__ == "__main__":
    m, wj, a, b = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
    d = json.load(open(wj, encoding="utf-8"))
    print(json.dumps(snap(m, d["words"] if isinstance(d, dict) else d, a, b, "--partial" in sys.argv), indent=1, ensure_ascii=False))
