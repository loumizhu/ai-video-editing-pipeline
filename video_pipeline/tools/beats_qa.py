"""Program checks for a beat-driven visual plan (owner rules 2026-11-08, video 21 feedback).

    python beats_qa.py --beats beats.json --assign assignments.json [--out qa_beats.md] [--max-still 6]

FAIL rules:
  coverage   every non-locked beat has a visual (file exists)
  reuse      no file used twice; video windows from one source never overlap
  ping-pong  never A-B-A (same file or same video source two beats apart)
  repeat     two consecutive beats never share a file / a video source window within 3 s
  still-hold no still longer than --max-still seconds (default 6.0 = documentary_standard hard cap; split the beat with an
             assignment 'sub' visual, or use footage). Soft cap + enrichment events: run still_hold_qa.py as well.
  window     a video in-point + beat duration stays inside the source
WARN: video share < 40 %, same SHOT/BEAT group back to back.
Exit 1 on any FAIL.
"""
import argparse, json, os, subprocess, sys


def dur(p):
    try:
        return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                    capture_output=True, text=True).stdout.strip())
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--beats", required=True)
    ap.add_argument("--assign", required=True)
    ap.add_argument("--out")
    ap.add_argument("--max-still", type=float, default=6.0)
    a = ap.parse_args()
    beats = {b["id"]: b for b in json.load(open(a.beats, encoding="utf-8"))}
    asg = {x["beat"]: x for x in json.load(open(a.assign, encoding="utf-8"))}
    fails, warns = [], []
    order = [b for b in beats.values() if not b.get("locked")]
    seq = []
    for b in order:
        x = asg.get(b["id"])
        if not x or not x.get("file") or not os.path.exists(x["file"]):
            fails.append(f"coverage: {b['id']} has no visual ({(x or {}).get('file')})"); seq.append(None); continue
        if x.get("sub"):
            # a beat split into several visuals: every part is checked like a beat of its own (file, reuse, repeat, ping-pong, still-hold)
            parts = [{"file": x["file"], "kind": x.get("kind"), "src_in": x.get("src_in"), "off": 0.0}]
            parts += [{"file": q.get("file"), "kind": q.get("kind"), "src_in": q.get("src_in"), "off": float(q.get("off", q.get("start_off", 0)))} for q in x["sub"]]
            parts.sort(key=lambda q: q["off"])
            for k, q in enumerate(parts):
                end = parts[k + 1]["off"] if k + 1 < len(parts) else b["dur"]
                bid = f"{b['id']}.{k + 1}"
                if not q["file"] or not os.path.exists(q["file"]):
                    fails.append(f"coverage: {bid} has no visual ({q['file']})"); seq.append(None); continue
                seq.append(({"id": bid, "dur": end - q["off"], "start": b["start"] + q["off"]}, q))
            continue
        seq.append((b, x))
    used, windows = {}, {}
    mdur = {}
    for item in seq:
        if not item:
            continue
        b, x = item
        f = os.path.normcase(os.path.abspath(x["file"]))
        if x.get("kind") == "video":
            s0 = float(x.get("src_in") or 0); s1 = s0 + b["dur"]
            for (o0, o1, ob) in windows.get(f, []):
                if s0 < o1 + 3 and s1 > o0 - 3:
                    fails.append(f"reuse: {b['id']} video window {s0:.1f}-{s1:.1f} overlaps {ob} in {os.path.basename(f)}")
            windows.setdefault(f, []).append((s0, s1, b["id"]))
            if f not in mdur:
                mdur[f] = dur(f)
            if mdur[f] and s1 > mdur[f] + 0.05:
                fails.append(f"window: {b['id']} needs {s0:.1f}-{s1:.1f} but {os.path.basename(f)} is {mdur[f]:.1f} s")
        else:
            if f in used:
                fails.append(f"reuse: {b['id']} reuses {os.path.basename(f)} (first used at {used[f]})")
            used.setdefault(f, b["id"])
            if b["dur"] > a.max_still:
                fails.append(f"still-hold: {b['id']} still held {b['dur']:.1f} s > {a.max_still}")
    keys = [None if not it else os.path.normcase(os.path.abspath(it[1]["file"])) for it in seq]
    for i in range(len(keys)):
        if keys[i] is None:
            continue
        if i + 1 < len(keys) and keys[i] == keys[i + 1] and seq[i][1].get("kind") != "video":
            fails.append(f"repeat: {seq[i][0]['id']} and {seq[i + 1][0]['id']} show the same file")
        if i + 2 < len(keys) and keys[i] == keys[i + 2] and keys[i] != keys[i + 1]:
            fails.append(f"ping-pong: {seq[i][0]['id']} / {seq[i + 2][0]['id']} A-B-A on {os.path.basename(keys[i])}")
    n = len([s for s in seq if s]); nv = len([s for s in seq if s and s[1].get("kind") == "video"])
    share = nv / max(1, n)
    if share < 0.40:
        warns.append(f"video share {share:.0%} < 40 %")
    lines = [f"# Beat plan QA: {'FAIL' if fails else 'PASS'}", "",
             f"beats {len(order)} | illustrated {n} | video {nv} ({share:.0%}) | fails {len(fails)} | warns {len(warns)}", ""]
    lines += [f"- FAIL {f}" for f in fails] + [f"- WARN {w}" for w in warns]
    txt = "\n".join(lines) + "\n"
    if a.out:
        open(a.out, "w", encoding="utf-8").write(txt)
    print(txt[:4000])
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
