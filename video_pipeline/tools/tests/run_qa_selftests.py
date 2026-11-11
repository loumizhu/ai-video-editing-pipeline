#!/usr/bin/env python
"""QA Automated Test Runner & Planted-Defect Media Generator.

Generates reproducible planted-defect and clean reference media into a TEMPORARY directory
(default: a fresh tempfile dir, deleted at the end; pass --artifacts-dir to keep the media),
then runs every QA tool against its planted defect, clean case, fooling case and bad input.
Each case asserts the exit code AND the reason string the tool reports (not just PASS/FAIL).

Cases:
  cut_audit   : loud vowel splice (energy), quiet -31 dBFS vowel change (isolates the SPECTRAL measure),
                clean room tone, documented limit (quiet 90-degree phase jump passes), missing media, cuts without fps,
                remedy line for failing edits
  flash_scan  : 1 Hz fade PASS, 2 Hz fade PASS, 5 Hz flash FAIL, missing media
  graphics_qa : 720p graphic on right edge FAIL, left edge FAIL, compliant PASS, missing input
  dead_air_qa : tail silence FAIL, 1.5 s dead air FAIL, clean PASS, missing media (exit 2), missing allowed-pauses (exit 2)
  check_setup : latest "Running DaVinci Resolve" line of a multi-session log wins
  make_cuts / transcribe_groq : their own --selftest suites

Usage:
  python run_qa_selftests.py [--artifacts-dir DIR]
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image

TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PYTHON_EXE = sys.executable
SR = 48000


# ---------------------------------------------------------------------------
# MEDIA GENERATORS (committed for 100% reproducibility)
# ---------------------------------------------------------------------------

def write_wav(path, samples, sample_rate=SR):
    ints = np.clip(np.asarray(samples) * 32767, -32768, 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(ints.tobytes())


def two_tone_splice(f1, f2, amp, duration=4.0):
    """Tone f1 until 2.0 s, then f2 (phase restarted at 0), both at amplitude amp."""
    t = np.linspace(0, duration, int(SR * duration), endpoint=False)
    s = amp * np.sin(2 * np.pi * f1 * t)
    mid = int(SR * 2.0)
    s[mid:] = amp * np.sin(2 * np.pi * f2 * (t[mid:] - t[mid]))
    return s


def generate_loud_vowel_wav(path):
    """225 -> 230 Hz splice at amp 0.08 = -24.9 dBFS RMS: fails on ENERGY."""
    write_wav(path, two_tone_splice(225, 230, 0.08))


def generate_quiet_vowel_wav(path):
    """225 -> 900 Hz splice at amp 0.04 = -31.0 dBFS RMS on both sides: below the -28 dBFS energy threshold,
    so only the SPECTRAL measure can catch it."""
    write_wav(path, two_tone_splice(225, 900, 0.04))


def generate_quiet_phase_jump_wav(path):
    """Same 225 Hz tone at -31 dBFS with a 90-degree phase jump at 2.0 s. Documented limit: PASSES (step 0.04 < 0.15)."""
    t = np.linspace(0, 4.0, int(SR * 4.0), endpoint=False)
    s = 0.04 * np.sin(2 * np.pi * 225 * t)
    mid = int(SR * 2.0)
    s[mid:] = 0.04 * np.sin(2 * np.pi * 225 * t[mid:] + np.pi / 2)
    write_wav(path, s)


def generate_clean_roomtone_wav(path, duration=4.0):
    rng = np.random.default_rng(42)
    write_wav(path, rng.normal(0, 0.008, int(SR * duration)))


def generate_tail_silence_wav(path):
    t = np.linspace(0, 3.0, int(SR * 3.0), endpoint=False)
    write_wav(path, np.concatenate([0.2 * np.sin(2 * np.pi * 440 * t), np.zeros(int(SR * 2.0))]))


def generate_dead_air_wav(path):
    t = np.linspace(0, 1.0, int(SR * 1.0), endpoint=False)
    tone = 0.2 * np.sin(2 * np.pi * 440 * t)
    write_wav(path, np.concatenate([tone, np.zeros(int(SR * 1.5)), tone]))


def generate_fade_mp4(path, hz, duration=4.0, fps=24):
    """Smooth full-range sine luminance fade at `hz` cycles/s."""
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c=black:s=160x90:r={fps}:d={duration}",
         "-vf", f"geq=lum='127.5*(1+sin(2*PI*{hz}*T))':cb=128:cr=128", "-c:v", "libx264", "-pix_fmt", "yuv420p", path],
        check=True,
    )


def generate_5hz_flash_mp4(path, duration=1.2, fps=24):
    """Frames 0-2 white, 3-4 black, repeating: ~4.8 flashes/s (MUST FAIL)."""
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c=black:s=160x90:r={fps}:d={duration}",
         "-vf", "geq=lum='if(lt(mod(N,5),3),255,0)':cb=128:cr=128", "-c:v", "libx264", "-pix_fmt", "yuv420p", path],
        check=True,
    )


def generate_graphics_pngs(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    im_left = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    im_left.paste(Image.new("RGBA", (600, 130), (20, 40, 80, 240)), (0, 850))
    p_left = os.path.join(out_dir, "defect_touching_left.png")
    im_left.save(p_left)

    im_720p = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    im_720p.paste(Image.new("RGBA", (580, 151), (200, 30, 30, 240)), (700, 500))
    p_720p = os.path.join(out_dir, "defect_720p_right_edge.png")
    im_720p.save(p_720p)

    im_safe = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    im_safe.paste(Image.new("RGBA", (600, 120), (30, 120, 200, 240)), (150, 880))
    p_safe = os.path.join(out_dir, "clean_title_safe.png")
    im_safe.save(p_safe)
    return p_left, p_720p, p_safe


# ---------------------------------------------------------------------------
# TEST SUITE RUNNER
# ---------------------------------------------------------------------------

def run_cmd(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode, proc.stdout, proc.stderr


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_suite(art_dir):
    os.makedirs(art_dir, exist_ok=True)
    results = []  # (name, expectation text, ok, detail)

    def check(name, expect, ok, detail=""):
        results.append((name, expect, bool(ok), detail))

    p_loud = os.path.join(art_dir, "vowel_loud.wav")
    p_quiet = os.path.join(art_dir, "vowel_quiet_31db.wav")
    p_phase = os.path.join(art_dir, "phase_jump_quiet.wav")
    p_clean = os.path.join(art_dir, "clean_roomtone.wav")
    p_tail = os.path.join(art_dir, "tail_silence.wav")
    p_dead = os.path.join(art_dir, "dead_air_15s.wav")
    p_fade1 = os.path.join(art_dir, "fade_1hz.mp4")
    p_fade2 = os.path.join(art_dir, "fade_2hz.mp4")
    p_flash5 = os.path.join(art_dir, "flash_5hz.mp4")
    generate_loud_vowel_wav(p_loud)
    generate_quiet_vowel_wav(p_quiet)
    generate_quiet_phase_jump_wav(p_phase)
    generate_clean_roomtone_wav(p_clean)
    generate_tail_silence_wav(p_tail)
    generate_dead_air_wav(p_dead)
    generate_fade_mp4(p_fade1, 1)
    generate_fade_mp4(p_fade2, 2)
    generate_5hz_flash_mp4(p_flash5)
    p_left_png, p_720p_png, p_safe_png = generate_graphics_pngs(art_dir)

    cuts_2seg = os.path.join(art_dir, "cuts_2seg.json")
    with open(cuts_2seg, "w") as f:
        json.dump(
            {
                "fps": "24", "fps_num": 24, "fps_den": 1,
                "segments": [
                    {"start_frame": 0, "end_frame": 48, "dur_frames": 48, "dur_s": 2.0, "text": "alpha beta"},
                    {"start_frame": 48, "end_frame": 96, "dur_frames": 48, "dur_s": 2.0, "text": "gamma delta"},
                ],
            },
            f,
        )
    cuts_nofps = os.path.join(art_dir, "cuts_nofps.json")
    with open(cuts_nofps, "w") as f:
        json.dump({"segments": [{"start_frame": 0, "end_frame": 48, "dur_frames": 48}, {"start_frame": 48, "end_frame": 96, "dur_frames": 48}]}, f)

    # ------------------------------------------------------------------ cut_audit
    ca = os.path.join(TOOLS_DIR, "cut_audit.py")

    def audit(media, tag, extra=()):
        oj = os.path.join(art_dir, f"audit_{tag}.json")
        rc, out, err = run_cmd([PYTHON_EXE, ca, "--media", media, "--cuts", cuts_2seg, "--out-json", oj,
                                "--out-md", os.path.join(art_dir, f"audit_{tag}.md"), *extra])
        return rc, out, err, (load_json(oj) if os.path.exists(oj) else None)

    rc, out, err, rep = audit(p_loud, "loud")
    reasons = " | ".join(rep["cuts"][0]["reasons"]) if rep else ""
    check("cut_audit: loud vowel splice (-24.9 dBFS)", "rc 1, reason 'speech energy clipped'",
          rc == 1 and "speech energy clipped" in reasons, f"rc={rc} reasons={reasons!r}")
    check("cut_audit: failing edit prints a remedy line", "stdout has 'Remedy:' and '2-frame audio crossfade at edit 1'",
          "Remedy:" in out and "apply a 2-frame audio crossfade at edit 1" in out and rep and rep["cuts"][0]["remedy"].startswith("Edit 1 at "),
          out.strip().splitlines()[-1] if out.strip() else "")

    rc, out, err, rep = audit(p_quiet, "quiet")
    reasons = " | ".join(rep["cuts"][0]["reasons"]) if rep else ""
    check("cut_audit: quiet -31 dBFS vowel change isolates the SPECTRAL measure",
          "rc 1, reason 'spectral/phase discontinuity', NO 'speech energy' reason, both sides < -28 dB",
          rc == 1 and "spectral/phase discontinuity" in reasons and "speech energy" not in reasons
          and rep["cuts"][0]["pre_rms_db"] < -28 and rep["cuts"][0]["post_rms_db"] < -28,
          f"rc={rc} pre={rep and rep['cuts'][0]['pre_rms_db']} post={rep and rep['cuts'][0]['post_rms_db']} reasons={reasons!r}")

    rc, out, err, rep = audit(p_clean, "clean")
    check("cut_audit: clean room-tone cut", "rc 0, no reasons, PASS",
          rc == 0 and rep and rep["overall_status"] == "PASS" and rep["cuts"][0]["reasons"] == [], f"rc={rc}")

    rc, out, err, rep = audit(p_phase, "phase")
    check("cut_audit: DOCUMENTED LIMIT quiet 90-degree phase jump passes", "rc 0 (known blind spot, step 0.04 < 0.15)",
          rc == 0 and rep and rep["cuts"][0]["waveform_step"] < 0.15, f"rc={rc} step={rep and rep['cuts'][0]['waveform_step']}")

    rc, out, err = run_cmd([PYTHON_EXE, ca, "--media", os.path.join(art_dir, "nonexistent.mp4"), "--cuts", cuts_2seg])
    check("cut_audit: missing media", "rc 2, 'Media file not found'", rc == 2 and "Media file not found" in err and "Traceback" not in err, f"rc={rc} err={err.strip()[:80]!r}")

    rc, out, err = run_cmd([PYTHON_EXE, ca, "--media", p_clean, "--cuts", cuts_nofps])
    check("cut_audit: cuts.json without fps is refused", "rc 2, message names fps_num/fps_den",
          rc == 2 and "fps_num/fps_den" in err, f"rc={rc} err={err.strip()[:100]!r}")

    # ------------------------------------------------------------------ flash_scan
    fs = os.path.join(TOOLS_DIR, "flash_scan.py")

    def flash(media, tag):
        oj = os.path.join(art_dir, f"flash_{tag}.json")
        rc, out, err = run_cmd([PYTHON_EXE, fs, "--media", media, "--out-json", oj, "--out-md", os.path.join(art_dir, f"flash_{tag}.md")])
        return rc, out, err, (load_json(oj) if os.path.exists(oj) else None)

    rc, out, err, rep = flash(p_fade1, "1hz")
    check("flash_scan: 1 Hz smooth fade", "rc 0, PASS, 0 hazards", rc == 0 and rep["overall_status"] == "PASS" and rep["hazard_windows_count"] == 0, f"rc={rc}")
    rc, out, err, rep = flash(p_fade2, "2hz")
    check("flash_scan: 2 Hz smooth fade", "rc 0, PASS (2 flashes/s <= 3)", rc == 0 and rep["overall_status"] == "PASS" and rep["hazard_windows_count"] == 0,
          f"rc={rc} changes={rep and rep['total_opposing_changes']}")
    rc, out, err, rep = flash(p_flash5, "5hz")
    hz = rep["hazards"][0] if rep and rep["hazards"] else {}
    check("flash_scan: 5 Hz on/off flash", "rc 1, reason names 'flashes' and the 3/s limit, >= 4 flashes in the window",
          rc == 1 and "exceeds the guideline limit of 3 flashes/s" in hz.get("reason", "") and hz.get("flashes_in_sec", 0) >= 4,
          f"rc={rc} hazard={hz.get('reason')!r}")
    rc, out, err = run_cmd([PYTHON_EXE, fs, "--media", os.path.join(art_dir, "nonexistent_flash.mp4")])
    check("flash_scan: missing media", "rc 1, 'Media file not found', no traceback", rc == 1 and "Media file not found" in err and "Traceback" not in err, f"rc={rc}")
    with open(os.path.join(TOOLS_DIR, "flash_scan.py"), encoding="utf-8") as f:
        src = f.read()
    check("flash_scan: no BT.1702 compliance claim", "docstring says guideline-based / not certified",
          "NOT a certified" in src and "BT.1702 compliant" not in src, "")

    # ------------------------------------------------------------------ graphics_qa
    gq = os.path.join(TOOLS_DIR, "graphics_qa.py")

    def gfx(png, tag):
        oj = os.path.join(art_dir, f"gfx_{tag}.json")
        rc, out, err = run_cmd([PYTHON_EXE, gq, "--input", png, "--out-json", oj, "--out-md", os.path.join(art_dir, f"gfx_{tag}.md")])
        return rc, out, err, (load_json(oj) if os.path.exists(oj) else None)

    rc, out, err, rep = gfx(p_720p_png, "720p")
    reasons = " | ".join(rep["assets"][0]["reasons"]) if rep else ""
    check("graphics_qa: 720p graphic touching right edge", "rc 1, 'RIGHT canvas edge' + title-safe reason on the real 1280 canvas",
          rc == 1 and "RIGHT canvas edge (right=1280 >= 1280)" in reasons and "title-safe" in reasons, f"rc={rc} reasons={reasons!r}")
    rc, out, err, rep = gfx(p_left_png, "left")
    reasons = " | ".join(rep["assets"][0]["reasons"]) if rep else ""
    check("graphics_qa: graphic touching left edge", "rc 1, 'LEFT canvas edge (left=0 <= 0)'", rc == 1 and "LEFT canvas edge (left=0 <= 0)" in reasons, f"rc={rc} reasons={reasons!r}")
    rc, out, err, rep = gfx(p_safe_png, "safe")
    check("graphics_qa: compliant title-safe graphic", "rc 0, no reasons", rc == 0 and rep["assets"][0]["reasons"] == [], f"rc={rc}")
    rc, out, err = run_cmd([PYTHON_EXE, gq, "--input", os.path.join(art_dir, "nonexistent_graphic.png")])
    check("graphics_qa: missing input", "rc 1, 'Input path not found'", rc == 1 and "Input path not found" in err, f"rc={rc}")

    # ------------------------------------------------------------------ dead_air_qa
    da = os.path.join(TOOLS_DIR, "dead_air_qa.py")

    def dead(media, tag, extra=()):
        oj = os.path.join(art_dir, f"dead_{tag}.json")
        rc, out, err = run_cmd([PYTHON_EXE, da, "--media", media, "--out-json", oj, "--out-md", os.path.join(art_dir, f"dead_{tag}.md"), *extra])
        return rc, out, err, (load_json(oj) if os.path.exists(oj) else None)

    rc, out, err, rep = dead(p_tail, "tail")
    d = rep["defects"][0] if rep and rep["defects"] else {}
    check("dead_air_qa: trailing silence at EOF (no silence_end)", "rc 1, one defect 2.0 s long ending at EOF, reason 'exceeds limit'",
          rc == 1 and abs(d.get("duration", 0) - 2.0) < 0.1 and "exceeds limit" in d.get("reason", ""), f"rc={rc} defect={d}")
    rc, out, err, rep = dead(p_dead, "air")
    d = rep["defects"][0] if rep and rep["defects"] else {}
    check("dead_air_qa: 1.5 s unapproved silence", "rc 1, reason 'Dead air duration 1.50s exceeds limit 0.60s'",
          rc == 1 and d.get("reason") == "Dead air duration 1.50s exceeds limit 0.60s", f"rc={rc} defect={d}")
    rc, out, err, rep = dead(p_clean, "clean", ("--max-silence", "0.6", "--noise-floor", "-35.0"))
    check("dead_air_qa: clean room tone", "rc 0, 0 defects", rc == 0 and rep["defects"] == [], f"rc={rc}")
    rc, out, err = run_cmd([PYTHON_EXE, da, "--media", os.path.join(art_dir, "nonexistent_audio.wav")])
    check("dead_air_qa: missing media", "rc 2, 'Media file not found'", rc == 2 and "Media file not found" in err, f"rc={rc}")
    rc, out, err = run_cmd([PYTHON_EXE, da, "--media", p_clean, "--allowed-pauses", os.path.join(art_dir, "missing_pauses.json")])
    check("dead_air_qa: missing --allowed-pauses", "rc 2, '--allowed-pauses file not found'", rc == 2 and "--allowed-pauses file not found" in err, f"rc={rc}")

    # ------------------------------------------------------------------ check_setup log parsing
    sys.path.insert(0, TOOLS_DIR)
    try:
        import check_setup
        log = os.path.join(art_dir, "fake_resolve.log")
        with open(log, "w", encoding="utf-8") as f:
            f.write("INFO | Running DaVinci Resolve Studio v19.1.0.0001 (Windows/MSVC x86_64)\n")
            f.write("noise line\n" * 300)
            f.write("INFO | Running DaVinci Resolve Studio v20.0.1.0006 (Windows/MSVC x86_64)\n")
            f.write("tail noise\n" * 5)
        got = check_setup.parse_resolve_log_version(log)
        check("check_setup: latest Resolve session wins", "'DaVinci Resolve Studio v20.0.1.0006' (not the oldest v19.1)",
              got == "DaVinci Resolve Studio v20.0.1.0006", f"got={got!r}")
        check("check_setup: missing log", "None", check_setup.parse_resolve_log_version(os.path.join(art_dir, "nope.log")) is None, "")
    finally:
        sys.path.pop(0)

    # ------------------------------------------------------------------ engine self-tests
    for script in ("make_cuts.py", "transcribe_groq.py"):
        rc, out, err = run_cmd([PYTHON_EXE, os.path.join(TOOLS_DIR, script), "--selftest"])
        check(f"{script} --selftest", "rc 0 and 'PASSED CLEANLY'", rc == 0 and "PASSED CLEANLY" in out, f"rc={rc} {err.strip()[-120:]}")

    print("=" * 78)
    print("QA Self-Test Suite Results Matrix")
    print("=" * 78)
    all_ok = True
    for name, expect, ok, detail in results:
        all_ok &= ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}\n         expect: {expect}" + ("" if ok else f"\n         got: {detail}"))
    print("=" * 78)
    if all_ok:
        print(f"ALL {len(results)} QA SELF-TESTS PASSED.")
        return 0
    print(f"FAILURES: {sum(1 for r in results if not r[2])} of {len(results)}")
    return 1


def main():
    ap = argparse.ArgumentParser(description="Run the complete QA self-test matrix.")
    ap.add_argument("--artifacts-dir", default=None, help="Keep generated media/reports here (default: a temp dir, deleted afterwards)")
    args = ap.parse_args()
    if args.artifacts_dir:
        sys.exit(run_suite(args.artifacts_dir))
    with tempfile.TemporaryDirectory(prefix="qa_selftests_") as td:
        sys.exit(run_suite(td))


if __name__ == "__main__":
    main()
