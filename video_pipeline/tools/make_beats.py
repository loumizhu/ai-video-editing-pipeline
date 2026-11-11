"""Split a narrated timeline into visual BEATS (one picture or clip per beat).

A beat is a sentence or half-sentence of narration, 2.5-6 s long (the still-hold cap, PACING_AND_ENRICHMENT.md: one beat = one visual), with the words spoken in it,
so a visual can be chosen for exactly what is being said and placed when it is said.

    python make_beats.py --layout layout.json --words vo_timeline.words.json --out beats.json
                         [--lock "148.2-160.0" ...] [--min 2.5] [--max 6.0]

Output: [{"id": "B001", "pid": "P003", "start": s, "end": s, "text": "...", "locked": false}]
Soundbite and chapter segments are not beats (they carry their own picture).
--lock ranges (timeline seconds) mark beats an editor already illustrated by hand; builders keep them.
"""
import argparse, json, re


def load_words(p):
    d = json.load(open(p, encoding="utf-8"))
    return d["words"] if isinstance(d, dict) else d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", required=True)
    ap.add_argument("--words", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lock", action="append", default=[])
    ap.add_argument("--min", type=float, default=2.5)
    ap.add_argument("--max", type=float, default=6.0)
    a = ap.parse_args()
    lay = json.load(open(a.layout, encoding="utf-8"))
    segs, total = lay["segs"], lay["total"]
    words = load_words(a.words)
    locks = [tuple(float(x) for x in r.split("-")) for r in a.lock]
    beats = []
    for i, s in enumerate(segs):
        if s["kind"] != "vo":
            continue
        span_end = segs[i + 1]["start"] if i + 1 < len(segs) else total
        ws = [w for w in words if s["start"] - 0.15 <= (w["start"] + w["end"]) / 2 <= s["start"] + s["dur"] + 0.15]
        if not ws:
            beats.append({"pid": s["pid"], "start": s["start"], "end": span_end, "words": []})
            continue
        # sentence chunks
        chunks, cur = [], []
        for w in ws:
            cur.append(w)
            if re.search(r"[.?!:;]$", w.get("word", w.get("text", "")).strip()):
                chunks.append(cur); cur = []
        if cur:
            chunks.append(cur)
        # split long chunks at a comma (or the middle word), merge short ones forward
        out = []
        for c in chunks:
            todo = [c]
            while todo:
                c = todo.pop(0)
                d = c[-1]["end"] - c[0]["start"]
                if d > a.max and len(c) > 4:
                    mid = (c[0]["start"] + c[-1]["end"]) / 2
                    cands = [k for k in range(2, len(c) - 2) if c[k - 1].get("word", "").strip().endswith(",")] or list(range(2, len(c) - 2))
                    k = min(cands, key=lambda k: abs(c[k]["start"] - mid))
                    todo[:0] = [c[:k], c[k:]]
                else:
                    out.append(c)
        merged = []
        for c in out:
            if merged and (c[-1]["end"] - c[0]["start"] < a.min or merged[-1][-1]["end"] - merged[-1][0]["start"] < a.min) \
                    and c[-1]["end"] - merged[-1][0]["start"] <= a.max + 0.5:
                merged[-1] = merged[-1] + c
            else:
                merged.append(c)
        for k, c in enumerate(merged):
            st = s["start"] if k == 0 else c[0]["start"] - 0.05
            beats.append({"pid": s["pid"], "start": st, "end": None, "words": c})
        beats[-1]["end"] = span_end
    # each beat ends where the next starts (within the same paragraph); the last one runs to the span end
    for k in range(len(beats) - 1):
        if beats[k]["end"] is None:
            beats[k]["end"] = beats[k + 1]["start"]
    res = []
    for n, b in enumerate(beats, 1):
        txt = " ".join(w.get("word", w.get("text", "")).strip() for w in b["words"])
        lk = any(b["start"] < r1 - 0.3 and b["end"] > r0 + 0.3 for r0, r1 in locks)
        res.append({"id": f"B{n:03d}", "pid": b["pid"], "start": round(b["start"], 3), "end": round(b["end"], 3),
                    "dur": round(b["end"] - b["start"], 2), "text": txt, "locked": lk})
    json.dump(res, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    ds = [r["dur"] for r in res]
    over = [r["id"] for r in res if r["dur"] > a.max + 0.5]
    print(f"{len(res)} beats, mean {sum(ds) / len(ds):.1f} s, max {max(ds):.1f} s, locked {sum(r['locked'] for r in res)}")
    if over:
        print(f"WARN {len(over)} beat(s) longer than {a.max + 0.5:.1f} s ({', '.join(over[:8])}): give each a second visual (assignment 'sub') or a plate")


if __name__ == "__main__":
    main()
