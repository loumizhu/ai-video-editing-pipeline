"""SFX build + verify. Spec lives in ../style.json `audio.*`; catalogue in ../sfx.json.

ONE metric per class (stated identically in sfx.md, sfx.json, style.json):
  events (9 files) : true peak (EBU R128 `peak=true`, dBTP) normalised to audio.sfx_peak_target_dbtp +/- audio.sfx_peak_tolerance_db
  bed (room tone)  : integrated loudness (LUFS) normalised to audio.room_tone_target_lufs +/- audio.room_tone_tolerance_lu
Why peak for events: clicks and hits are 0.05-0.4 s long, so integrated LUFS is dominated by the silence around them and
cannot be reached without a limiter. A peak target sits the event audibly under VO peaks (master ceiling - margin).
Integrated LUFS / momentary max are recorded in sfx.json for information only, never gated.

  python sfx_tool.py build    download sources (URLs in sfx.json), fade, normalise, write WAVs + measured fields into sfx.json
  python sfx_tool.py verify   re-measure the shipped WAVs and check them against the spec (exit 1 on any failure)
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import _common as C  # noqa: E402

STYLE = os.path.join(HERE, "..", "style.json")
CATALOGUE = os.path.join(HERE, "..", "sfx.json")
UA = {"User-Agent": "Mozilla/5.0"}


def measure(path):
    r = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-v", "verbose", "-i", path, "-af", "ebur128=peak=true:framelog=verbose", "-f", "null", "-"], capture_output=True, text=True)
    t = r.stderr
    m = [float(x) for x in re.findall(r"M:\s*(-?[\d.]+)\s+S:", t)]
    i = float(re.findall(r"I:\s+(-?[\d.]+) LUFS\n\s+Threshold", t)[-1])
    tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", t)[-1])
    return {"lufs_i": i, "lufs_m_max": max(m) if m else None, "true_peak_dbtp": tp}


def probe_duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip())


def sample0(path):
    with wave.open(path) as w:
        n = w.getnframes()
        data = np.frombuffer(w.readframes(min(n, 4)), dtype="<i2")
        return int(abs(data[:2]).max()), w.getframerate(), w.getnchannels(), w.getsampwidth() * 8, n / w.getframerate()


def render(src, dst, fade_s, gain_db):
    dur = probe_duration(src)
    af = f"afade=t=in:ss=0:d={fade_s},afade=t=out:st={dur - fade_s:.6f}:d={fade_s},volume={gain_db:.4f}dB"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-ar", "48000", "-ac", "2", "-af", af, "-c:a", "pcm_s16le", dst], check=True)


def download(url, dst):
    """urllib first; fall back to curl (Windows schannel trust store) when Python's CA bundle rejects the host."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r, open(dst, "wb") as o:
            o.write(r.read())
    except Exception:
        subprocess.run(["curl", "-s", "-L", "-f", "-A", UA["User-Agent"], "-o", dst, url], check=True)


def build():
    style = C.load_style(STYLE)
    au = style["audio"]
    cat = json.load(open(CATALOGUE, encoding="utf-8"))
    with tempfile.TemporaryDirectory() as wd:
        for f in cat["files"]:
            ext = os.path.splitext(f["source_url"])[1].split("?")[0]
            raw = os.path.join(wd, f["name"] + ext)
            download(f["source_url"], raw)
            dst = os.path.join(HERE, f["name"])
            fade = au["fade_ms"] / 1000.0
            render(raw, dst, fade, 0.0)
            m0 = measure(dst)
            if f["kind"] == "event":
                gain = au["sfx_peak_target_dbtp"] - m0["true_peak_dbtp"]
            else:
                gain = au["room_tone_target_lufs"] - m0["lufs_i"]
            render(raw, dst, fade, gain)
            for _ in range(2):                                       # one refinement pass for 16-bit rounding
                m = measure(dst)
                err = (au["sfx_peak_target_dbtp"] - m["true_peak_dbtp"]) if f["kind"] == "event" else (au["room_tone_target_lufs"] - m["lufs_i"])
                if abs(err) < 0.05:
                    break
                gain += err
                render(raw, dst, fade, gain)
            m = measure(dst)
            s0, sr, ch, bits, dur = sample0(dst)
            f.update({"measured": m, "gain_applied_db": round(gain, 2), "duration_seconds": round(dur, 3), "sample_rate_hz": sr, "channels": ch, "bit_depth": bits,
                      "sample_0_amplitude": s0, "file_size_bytes": os.path.getsize(dst)})
            print(f["name"], m, "gain", round(gain, 2))
    cat["loudness_spec"] = {k: au[k] for k in ("sfx_peak_target_dbtp", "sfx_peak_tolerance_db", "room_tone_target_lufs", "room_tone_tolerance_lu", "fade_ms")}
    cat["loudness_spec"]["metric_events"] = "true peak (dBTP, ebur128 peak=true)"
    cat["loudness_spec"]["metric_bed"] = "integrated loudness (LUFS, ebur128)"
    json.dump(cat, open(CATALOGUE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


def spec_problems(style, cat):
    """Spec-level consistency (no audio measured): style.json vs sfx.json vs the mix ceilings."""
    au = style["audio"]
    bad = []
    if au["sfx_peak_target_dbtp"] + au["sfx_peak_tolerance_db"] > au["master_true_peak_max_dbtp"] - au["sfx_vs_master_peak_margin_db"]:
        bad.append(f"spec: SFX peak ceiling {au['sfx_peak_target_dbtp'] + au['sfx_peak_tolerance_db']} is not {au['sfx_vs_master_peak_margin_db']} dB under master ceiling {au['master_true_peak_max_dbtp']}")
    if au["room_tone_target_lufs"] + au["room_tone_tolerance_lu"] > au["dialogue_target_lufs"] - 10:
        bad.append("spec: room tone is not >=10 LU under dialogue")
    for k in ("sfx_peak_target_dbtp", "sfx_peak_tolerance_db", "room_tone_target_lufs", "room_tone_tolerance_lu", "fade_ms"):
        if cat.get("loudness_spec", {}).get(k) != au[k]:
            bad.append(f"sfx.json loudness_spec.{k} != style.json audio.{k}")
    return bad


def verify():
    style = C.load_style(STYLE)
    au = style["audio"]
    cat = json.load(open(CATALOGUE, encoding="utf-8"))
    bad = spec_problems(style, cat)
    print(f"{'file':28s} {'class':6s} {'metric':>10s} {'target':>8s} {'tol':>5s} {'I':>7s} {'Mmax':>7s} {'TP':>6s} {'s0':>3s}  ok")
    for f in cat["files"]:
        p = os.path.join(HERE, f["name"])
        m = measure(p)
        s0, sr, ch, bits, dur = sample0(p)
        if f["kind"] == "event":
            val, tgt, tol, unit = m["true_peak_dbtp"], au["sfx_peak_target_dbtp"], au["sfx_peak_tolerance_db"], "dBTP"
        else:
            val, tgt, tol, unit = m["lufs_i"], au["room_tone_target_lufs"], au["room_tone_tolerance_lu"], "LUFS"
        ok = abs(val - tgt) <= tol + 1e-9 and s0 == 0 and sr == 48000 and bits == 16
        if not ok:
            bad.append(f"{f['name']}: {val} {unit} vs {tgt}+/-{tol}, sample0={s0}, {sr} Hz {bits}-bit")
        print(f"{f['name']:28s} {f['kind']:6s} {val:>8.2f}{unit[:1]:>2s} {tgt:>8.1f} {tol:>5.1f} {m['lufs_i']:>7.1f} {str(m['lufs_m_max']):>7s} {m['true_peak_dbtp']:>6.1f} {s0:>3d}  {'PASS' if ok else 'FAIL'}")
    for f in cat["files"]:
        for k in ("source_url", "page_url", "license_url"):
            if not f.get(k):
                bad.append(f"{f['name']}: missing {k}")
    print("RESULT:", "PASS" if not bad else "FAIL")
    for b in bad:
        print("  -", b)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["build", "verify"])
    a = ap.parse_args()
    build() if a.cmd == "build" else verify()
