#!/usr/bin/env python
"""Self-tests for the pacing toolchain (still_hold_qa, asset_audit, variation_report, pacing_lib). Revision 2026-11-09.

Plants known defects in synthetic plans / pictures / a rendered clip and asserts the exit code and the finding codes.
Needs Pillow; the rendered-video case needs ffmpeg (skipped with a note if missing).

  python tests/run_pacing_selftests.py
Exit 0 when every case passes, 1 otherwise.
"""
from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, TOOLS)
import pacing_lib as P  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

PY = sys.executable
TMP = tempfile.mkdtemp(prefix="pacing_selftest_")
RESULTS: list[tuple[str, bool, str]] = []


def case(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if (detail and not ok) else ""))


def write(name: str, obj) -> str:
    p = os.path.join(TMP, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return p


def run(tool: str, *args: str) -> tuple[int, dict | None, str]:
    out_json = os.path.join(TMP, f"{tool}_{abs(hash(args)) % 10**8}.json")
    cmd = [PY, os.path.join(TOOLS, tool + ".py"), *args, "--out-json", out_json]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    data = None
    if os.path.exists(out_json):
        with open(out_json, encoding="utf-8") as f:
            data = json.load(f)
    return proc.returncode, data, proc.stdout + proc.stderr


def codes(data: dict | None, sev: str | None = None) -> set[str]:
    return {f["code"] for f in (data or {}).get("findings", []) if sev is None or f["severity"] == sev}


def slot(i, a, b, asset, move="push_slow", **kw):
    s = {"slot_id": f"s{i}", "start_ms": int(a * 1000), "end_ms": int(b * 1000), "media_type": "image", "selected_asset": asset}
    if move:
        s["motion"] = {"move": move}
    s.update(kw)
    return s


def plan(slots) -> str:
    return write(f"plan_{random.random():.6f}.json", {"slots": slots})


# ------------------------------------------------------------------ still_hold_qa
def t_still_hold() -> None:
    moves = ["push_slow", "drift_left", "pull_back", "push_in", "drift_right"]
    clean = [slot(i, i * 4, i * 4 + 4, f"img{i}.jpg", moves[i % 5]) for i in range(8)]
    rc, d, _ = run("still_hold_qa", "--shot-plan", plan(clean))
    case("still_hold: clean 4 s stills PASS", rc == 0 and d["overall_status"] == "PASS", str(codes(d)))

    rc, d, _ = run("still_hold_qa", "--shot-plan", plan([slot(0, 0, 4, "a.jpg"), slot(1, 4, 16, "b.jpg", "push_in"), slot(2, 16, 20, "c.jpg", "drift_left")]))
    case("still_hold: 12 s still FAILS STILL_HARD", rc == 1 and "STILL_HARD" in codes(d, "FAIL"), str(codes(d)))
    case("still_hold: suggests >= 3 distinct shots", any("Need >= 3" in f["fix"] for f in d["findings"]))

    rc, d, _ = run("still_hold_qa", "--shot-plan", plan([slot(0, 0, 5, "a.jpg")]))
    case("still_hold: 5 s still with no event FAILS STILL_SOFT", rc == 1 and "STILL_SOFT" in codes(d, "FAIL"), str(codes(d)))

    rc, d, _ = run("still_hold_qa", "--shot-plan", plan([slot(0, 0, 5, "a.jpg", enrichments=[{"type": "keyword_pop", "at_ms": 2500}])]))
    case("still_hold: 5 s still with keyword at 2.5 s PASSES", rc == 0, str(codes(d)))

    rc, d, _ = run("still_hold_qa", "--shot-plan", plan([slot(0, 0, 5, "a.jpg", enrichments=[{"type": "keyword_pop", "at_ms": 600}])]))
    case("still_hold: event at 0.6 s leaves a 4.4 s gap -> FAIL", rc == 1 and "STILL_SOFT" in codes(d, "FAIL"), str(codes(d)))

    rc, d, _ = run("still_hold_qa", "--shot-plan", plan([slot(0, 0, 5, "a.jpg", "detail_crop")]))
    case("still_hold: detail_crop WITHOUT a target_rect does not count (WEAK_RECOMPOSE)", rc == 1 and "WEAK_RECOMPOSE" in codes(d, "WARN"), str(codes(d)))
    sl = slot(0, 0, 5, "a.jpg")
    sl["motion"] = {"move": "detail_crop", "target_rect": [0.5, 0.3, 0.4, 0.4]}
    rc, d, _ = run("still_hold_qa", "--shot-plan", plan([sl]))
    case("still_hold: detail_crop with a real target_rect counts as the event", rc == 0, str(codes(d)))
    sl["motion"] = {"move": "detail_crop", "target_rect": [0.0, 0.0, 0.99, 0.99]}
    rc, d, _ = run("still_hold_qa", "--shot-plan", plan([sl]))
    case("still_hold: a 1 % 'crop' does not count", rc == 1 and "WEAK_RECOMPOSE" in codes(d, "WARN"), str(codes(d)))

    rc, d, _ = run("still_hold_qa", "--shot-plan", plan([slot(0, 0, 5, "a.jpg", enrichments=[{"type": "sfx_accent", "at_ms": 2500}])]))
    case("still_hold: audio-only event does NOT count", rc == 1, str(codes(d)))

    rc, d, _ = run("still_hold_qa", "--shot-plan", plan([slot(0, 0, 3, "a.jpg", asset_group="g1"), slot(1, 3, 6.5, "b.jpg", "drift_left", asset_group="g1")]))
    case("still_hold: same-group stills merge into one 6.5 s run -> FAIL + GROUP_MERGE",
         rc == 1 and "STILL_HARD" in codes(d, "FAIL") and "GROUP_MERGE" in codes(d, "WARN"), str(codes(d)))

    rc, d, _ = run("still_hold_qa", "--shot-plan", plan([slot(0, 0, 9, "a.jpg", still_hold_waiver="owner: deliberate long hold on the letter")]))
    case("still_hold: a waiver WITHOUT --allow-waivers is ignored (agent cannot waive itself)", rc == 1 and "WAIVER_IGNORED" in codes(d, "WARN") and "STILL_HARD" in codes(d, "FAIL"), str(codes(d)))
    wp = plan([slot(0, 0, 9, "a.jpg", still_hold_waiver="owner: deliberate long hold on the letter")])
    rc, d, _ = run("still_hold_qa", "--shot-plan", wp, "--allow-waivers")
    case("still_hold: owner waiver + --allow-waivers turns the FAIL into STILL_WAIVED warn", rc == 0 and "STILL_WAIVED" in codes(d, "WARN"), str(codes(d)))

    rc, d, _ = run("still_hold_qa", "--shot-plan", plan([slot(0, 0, 4, "a.jpg")]), "--preset", "tense_fast")
    case("still_hold: tense_fast 4 s still needs an event", rc == 1 and "STILL_SOFT" in codes(d, "FAIL"), str(codes(d)))

    rc, d, _ = run("still_hold_qa", "--shot-plan", plan([slot(0, 0, 4, "a.jpg", beat={"emotion": "tension", "intensity": 5})]))
    case("still_hold: intensity 5 tightens the cap (4 s now needs an event)", rc == 1 and "STILL_SOFT" in codes(d, "FAIL"), str(codes(d)))

    rc, d, _ = run("still_hold_qa", "--shot-plan", plan([slot(0, 0, 5.5, "doc.png", reading=True, subject="document")]))
    case("still_hold: reading plate gets +1 s allowance", rc == 0, str(codes(d)))

    aba = [slot(0, 0, 4, "a.jpg"), slot(1, 4, 8, "b.jpg", "drift_left"), slot(2, 8, 12, "a.jpg", "pull_back")]
    rc, d, _ = run("still_hold_qa", "--shot-plan", plan(aba))
    case("still_hold: A-B-A reuse FAILS", rc == 1 and "REUSE" in codes(d, "FAIL"), str(codes(d)))
    rc, d, _ = run("still_hold_qa", "--shot-plan", plan(aba), "--allow-reuse")
    case("still_hold: --allow-reuse downgrades to WARN", rc == 0 and "REUSE" in codes(d, "WARN"), str(codes(d)))

    rc, d, _ = run("still_hold_qa", "--shot-plan", plan([slot(0, 0, 4, "a.jpg"), slot(1, 4, 8, "b.jpg", None)]))
    case("still_hold: still without motion FAILS NO_MOTION", rc == 1 and "NO_MOTION" in codes(d, "FAIL"), str(codes(d)))

    long_plate = [slot(0, 0, 4, "a.jpg"), {"slot_id": "p", "start_ms": 4000, "end_ms": 7000, "visual_type": "graphics", "media_type": "plate"}, slot(2, 7, 11, "b.jpg", "drift_left")]
    rc, d, _ = run("still_hold_qa", "--shot-plan", plan(long_plan := long_plate))
    case("still_hold: a plate ends the run (no false merge)", rc == 0, str(codes(d)))

    # beats + assignments, with and without sub-visuals
    beats = write("beats.json", [{"id": "B001", "pid": "P1", "start": 0.0, "end": 9.0, "dur": 9.0, "text": "nine seconds on one thing", "locked": False}])
    a1 = write("asg1.json", [{"beat": "B001", "file": "x.jpg", "kind": "image", "motion": "push_slow"}])
    rc, d, _ = run("still_hold_qa", "--beats", beats, "--assign", a1)
    case("still_hold: beat mode, 9 s beat on one still FAILS", rc == 1 and "STILL_HARD" in codes(d, "FAIL"), str(codes(d)))
    a2 = write("asg2.json", [{"beat": "B001", "file": "x.jpg", "kind": "image", "motion": "push_slow", "sub": [{"file": "y.jpg", "kind": "image", "off": 4.5, "motion": "drift_left"}]}])
    rc, d, _ = run("still_hold_qa", "--beats", beats, "--assign", a2)
    case("still_hold: beat mode, sub-visual splits 9 s into 4.5 + 4.5 -> PASS (own motion per part)", rc == 0, str(codes(d)))
    a3 = write("asg3.json", [{"beat": "B001", "file": "x.jpg", "kind": "image", "motion": "push_slow", "group": "g", "sub": [{"file": "y.jpg", "kind": "image", "off": 4.5, "motion": "drift_left", "group": "g"}]}])
    rc, d, _ = run("still_hold_qa", "--beats", beats, "--assign", a3)
    case("still_hold: beat mode, both parts in one group merge back into a 9 s run -> FAIL", rc == 1 and "STILL_HARD" in codes(d, "FAIL"), str(codes(d)))

    # --- loopholes found in review
    lie = slot(0, 0, 12, "photo.png")
    lie["media_type"] = "video"
    rc, d, _ = run("still_hold_qa", "--shot-plan", plan([lie]))
    case("still_hold: a PNG declared 'video' is still counted as a still (12 s FAILS)", rc == 1 and "STILL_HARD" in codes(d, "FAIL") and "MEDIA_TYPE" in codes(d, "WARN"), str(codes(d)))

    dummy = [slot(0, 0, 6, "a.jpg"), {"slot_id": "d", "start_ms": 6000, "end_ms": 6100, "media_type": "plate", "plate_type": "narration_plate"}, slot(2, 6.1, 12, "a.jpg", "pull_back")]
    rc, d, _ = run("still_hold_qa", "--shot-plan", plan(dummy))
    case("still_hold: a 0.1 s dummy plate cannot reset the run (12 s FAILS)", rc == 1 and "STILL_HARD" in codes(d, "FAIL"), str(codes(d)))

    bigplate = [{"slot_id": "p", "start_ms": 0, "end_ms": 12000, "media_type": "plate", "plate_type": "quote_card"}]
    rc, d, _ = run("still_hold_qa", "--shot-plan", plan(bigplate))
    case("still_hold: a 12 s plate FAILS PLATE_HOLD", rc == 1 and "PLATE_HOLD" in codes(d, "FAIL"), str(codes(d)))
    rc, d, _ = run("still_hold_qa", "--shot-plan", plan([{"slot_id": "p", "start_ms": 0, "end_ms": 3000, "media_type": "plate"}]))
    case("still_hold: untyped plate warns PLATE_UNTYPED", "PLATE_UNTYPED" in codes(d, "WARN"), str(codes(d)))

    nested = {"slot_id": "n", "start_ms": 0, "end_ms": 9000, "pipeline_ext": {"media_type": "image", "selected_asset": "z.jpg", "motion": {"move": "push_slow"}}}
    rc, d, _ = run("still_hold_qa", "--shot-plan", plan([nested]))
    case("still_hold: fields nested under pipeline_ext are read (9 s FAILS)", rc == 1 and "STILL_HARD" in codes(d, "FAIL"), str(codes(d)))

    bm = write("bm.json", {"beats": [{"beat": "B9", "emotion": "tension", "intensity": 5, "priority": 5}]})
    sl = slot(0, 0, 4, "a.jpg")
    sl["beat_id"] = "B9"
    rc, d, _ = run("still_hold_qa", "--shot-plan", plan([sl]), "--beat-map", bm)
    case("still_hold: --beat-map is merged into a shot plan by beat_id (intensity 5 tightens the cap)", rc == 1 and "STILL_SOFT" in codes(d, "FAIL"), str(codes(d)))

    rc, d, _ = run("still_hold_qa", "--shot-plan", plan([slot(0, 0, 3.0, "a.jpg", beat={"intensity": 5})]))
    case("still_hold: cap floor keeps an intensity-5 documentary beat from getting an impossible cap", rc == 0, str(codes(d)))

    rc, _, out = run("still_hold_qa", "--shot-plan", os.path.join(TMP, "missing.json"))
    case("still_hold: missing input exits 2", rc == 2, out[-120:])

    if shutil.which("ffmpeg"):
        vid = os.path.join(TMP, "gap.mp4")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=red:s=320x180:r=25:d=3", "-f", "lavfi", "-i", "color=c=blue:s=320x180:r=25:d=10",
                        "-filter_complex", "concat=n=2:v=1:a=0", "-pix_fmt", "yuv420p", vid], check=True)
        rc, d, _ = run("still_hold_qa", "--shot-plan", plan(clean), "--media", vid)
        case("still_hold: rendered video with a 10 s no-cut stretch -> MEDIA_GAP warn", "MEDIA_GAP" in codes(d, "WARN"), str(codes(d)))
    else:
        case("still_hold: media scan skipped (ffmpeg missing)", True)


# ------------------------------------------------------------------ asset_audit
def make_img(path, size, seed, noise=True):
    rnd = random.Random(seed)
    im = Image.new("RGB", size, (rnd.randrange(256), rnd.randrange(256), rnd.randrange(256)))
    dr = ImageDraw.Draw(im)
    for _ in range(40):
        x0, y0 = rnd.randrange(size[0]), rnd.randrange(size[1])
        dr.rectangle([x0, y0, x0 + rnd.randrange(10, size[0] // 2), y0 + rnd.randrange(10, size[1] // 2)], fill=(rnd.randrange(256), rnd.randrange(256), rnd.randrange(256)))
    im.save(path, quality=92)


def t_asset_audit() -> None:
    d = os.path.join(TMP, "assets")
    os.makedirs(d, exist_ok=True)
    make_img(os.path.join(d, "ok.jpg"), (2400, 1350), 1)
    make_img(os.path.join(d, "small.jpg"), (800, 450), 2)
    make_img(os.path.join(d, "dupA.jpg"), (2400, 1350), 3)
    shutil.copy(os.path.join(d, "dupA.jpg"), os.path.join(d, "dupB.jpg"))
    Image.open(os.path.join(d, "dupA.jpg")).resize((1920, 1080)).save(os.path.join(d, "dupB.jpg"), quality=70)
    make_img(os.path.join(d, "portrait.jpg"), (900, 1400), 4)
    Image.new("RGB", (2000, 1200), (30, 30, 30)).save(os.path.join(d, "blank.png"))
    with open(os.path.join(d, "corrupt.jpg"), "w") as f:
        f.write("not an image")
    sl = [slot(0, 0, 4, "ok.jpg"), slot(1, 4, 8, "small.jpg", "drift_left"), slot(2, 8, 12, "dupA.jpg", "pull_back"), slot(3, 12, 16, "dupB.jpg", "push_in"),
          slot(4, 16, 20, "portrait.jpg", "drift_right"), slot(5, 20, 24, "blank.png", "push_slow"), slot(6, 24, 28, "corrupt.jpg", "pull_back"),
          slot(7, 28, 32, "ghost.jpg", "drift_left"), {"slot_id": "s8", "start_ms": 32000, "end_ms": 36000, "media_type": "image", "motion": {"move": "push_in"}}]
    rc, data, _ = run("asset_audit", "--assets-dir", d, "--shot-plan", plan(sl))
    got = codes(data)
    for code in ("TOO_SMALL", "DUPLICATE", "ASPECT_PORTRAIT", "BLANK", "CORRUPT", "MISSING_FILE", "MISSING_ASSET"):
        case(f"asset_audit: detects {code}", code in got, str(sorted(got)))
    case("asset_audit: adjacent duplicates are FAIL", any(f["code"] == "DUPLICATE" and f["severity"] == "FAIL" for f in data["findings"]))
    case("asset_audit: exits 1 on FAIL", rc == 1)
    case("asset_audit: ok.jpg raises no finding", not any("ok.jpg" in f["where"] for f in data["findings"] if f["severity"] != "INFO"))
    case("asset_audit: similar_pairs exported for still_hold_qa", any({os.path.basename(p[0]).lower(), os.path.basename(p[1]).lower()} == {"dupa.jpg", "dupb.jpg"} for p in data["similar_pairs"]))
    case("asset_audit: research requests written", len(data["research_requests"]) >= 3)

    # deficit: one idea carrying 12 s
    d2 = os.path.join(TMP, "assets2")
    os.makedirs(d2, exist_ok=True)
    make_img(os.path.join(d2, "one.jpg"), (2400, 1350), 9)
    rc, data, _ = run("asset_audit", "--assets-dir", d2, "--shot-plan", plan([slot(0, 0, 12, "one.jpg")]))
    case("asset_audit: 12 s on one picture -> COVERAGE_DEFICIT FAIL", rc == 1 and "COVERAGE_DEFICIT" in codes(data, "FAIL"), str(codes(data)))
    case("asset_audit: deficit request asks for >= 2 more shots", any(q["reason"] == "coverage_deficit" and q["needed"] >= 2 for q in data["research_requests"]))

    # chained near-duplicates from similar_pairs make still_hold_qa merge them
    d3 = os.path.join(TMP, "assets3")
    os.makedirs(d3, exist_ok=True)
    make_img(os.path.join(d3, "p1.jpg"), (2400, 1350), 11)
    Image.open(os.path.join(d3, "p1.jpg")).resize((2000, 1125)).save(os.path.join(d3, "p2.jpg"), quality=80)
    pl = plan([slot(0, 0, 3.5, os.path.join(d3, "p1.jpg")), slot(1, 3.5, 7, os.path.join(d3, "p2.jpg"), "drift_left")])
    rc, rep, _ = run("asset_audit", "--assets-dir", d3, "--shot-plan", pl)
    rep_path = write("audit_for_hold.json", rep)
    rc, hd, _ = run("still_hold_qa", "--shot-plan", pl, "--assets-report", rep_path)
    case("still_hold: near-duplicate stills merge via --assets-report -> 7 s run FAILS", rc == 1 and "STILL_HARD" in codes(hd, "FAIL"), str(codes(hd)))

    # relative sub-path + --assets-root, provider ref + --registry
    d4 = os.path.join(TMP, "assets4")
    os.makedirs(os.path.join(d4, "conformed"), exist_ok=True)
    make_img(os.path.join(d4, "conformed", "r1.jpg"), (2400, 1350), 21)
    make_img(os.path.join(d4, "conformed", "r2.jpg"), (2400, 1350), 22)
    reg = write("registry.json", {"assets": [{"asset_id": "a_x1", "provider": "pexels", "provider_asset_id": "3129957", "conformed_path": os.path.join(d4, "conformed", "r2.jpg")}]})
    rc, data, _ = run("asset_audit", "--assets-root", d4, "--registry", reg, "--shot-plan", plan([slot(0, 0, 4, "conformed/r1.jpg"), slot(1, 4, 8, "pexels:3129957", "drift_left")]))
    case("asset_audit: relative sub-path resolves under --assets-root and provider ref via --registry", rc == 0 and "MISSING_FILE" not in codes(data), str(codes(data)))

    rc, data, _ = run("asset_audit", "--assets-dir", d2, "--shot-plan", plan([slot(0, 0, 4, "one.jpg")]), "--canvas", "1080x1920")
    case("asset_audit: a 16:9 picture on a 9:16 canvas warns (aspect check follows the canvas)", "ASPECT_PORTRAIT" in codes(data, "WARN"), str(codes(data)))

    rc, _, out = run("asset_audit", "--shot-plan", os.path.join(TMP, "nope.json"))
    case("asset_audit: missing input exits 2", rc == 2, out[-120:])


# ------------------------------------------------------------------ variation_report
def t_variation() -> None:
    same = [slot(i, i * 4, i * 4 + 4, f"i{i}.jpg", "push_slow") for i in range(4)]
    rc, d, _ = run("variation_report", "--shot-plan", plan(same))
    case("variation: 4 identical motions FAIL MOTION_RUN", rc == 1 and "MOTION_RUN" in codes(d, "FAIL"), str(codes(d)))

    ok = [slot(i, i * 4, i * 4 + 4, f"i{i}.jpg", m) for i, m in enumerate(["push_slow", "drift_left", "pull_back", "drift_right", "push_in", "push_slow"])]
    rc, d, _ = run("variation_report", "--shot-plan", plan(ok))
    case("variation: varied motions PASS", rc == 0, str(codes(d)))

    tr = [slot(i, i * 4, i * 4 + 4, f"i{i}.jpg", m, transitions=[{"type": "tr.cross_dissolve"}]) for i, m in enumerate(["push_slow", "drift_left", "pull_back", "drift_right"])]
    rc, d, _ = run("variation_report", "--shot-plan", plan(tr))
    case("variation: 3 identical dynamic transitions FAIL", rc == 1 and "TRANSITION_RUN" in codes(d, "FAIL"), str(codes(d)))
    case("variation: low hard-cut share warns", "CUT_SHARE" in codes(d, "WARN"), str(codes(d)))

    kp = [slot(i, i * 100, i * 100 + 4, f"i{i}.jpg", ["push_slow", "drift_left", "pull_back"][i % 3], enrichments=[{"type": "keyword_pop", "at_ms": i * 100000 + 1000}]) for i in range(3)]
    rc, d, _ = run("variation_report", "--shot-plan", plan(kp))
    case("variation: 3 keyword pops in 5 min FAIL ENRICH_CAP", rc == 1 and "ENRICH_CAP" in codes(d, "FAIL"), str(codes(d)))

    sf = [slot(0, 0, 4, "a.jpg", "push_slow", sfx=["whoosh.wav"]), slot(1, 4, 8, "b.jpg", "drift_left", sfx=["whoosh.wav"])]
    rc, d, _ = run("variation_report", "--shot-plan", plan(sf))
    case("variation: same SFX within 20 s warns", "SFX_REPEAT" in codes(d, "WARN"), str(codes(d)))

    gr = [slot(0, 0, 4, "a.jpg", "punch_in", beat={"emotion": "grief", "intensity": 3}, rationale="x")]
    rc, d, _ = run("variation_report", "--shot-plan", plan(gr))
    case("variation: punch_in on a grief beat warns EMOTION_MOTION", "EMOTION_MOTION" in codes(d, "WARN"), str(codes(d)))

    dr = [slot(0, 0, 4, "a.jpg", "drift_left"), slot(1, 4, 8, "b.jpg", "drift_left")]
    rc, d, _ = run("variation_report", "--shot-plan", plan(dr))
    case("variation: same lateral drift twice in a row warns DIRECTION_RUN", "DIRECTION_RUN" in codes(d, "WARN"), str(codes(d)))

    pi = []
    for i in range(4):
        sl = slot(i, i * 60, i * 60 + 4, f"i{i}.jpg", None)
        sl["motion"] = {"move": "punch_in"}
        pi.append(sl)
    rc, d, _ = run("variation_report", "--shot-plan", plan(pi))
    case("variation: 4 punch-ins in 3 min FAIL ENRICH_CAP (motion-based events are counted)", rc == 1 and "ENRICH_CAP" in codes(d, "FAIL"), str(codes(d)))

    pl = [{"slot_id": f"p{i}", "start_ms": i * 40000, "end_ms": i * 40000 + 3000, "media_type": "plate", "plate_type": "map", "rationale": "x"} for i in range(4)]
    rc, d, _ = run("variation_report", "--shot-plan", plan(pl))
    case("variation: 4 maps in 3 min FAIL ENRICH_CAP (plate types are counted)", rc == 1 and "ENRICH_CAP" in codes(d, "FAIL"), str(codes(d)))

    npl = [{"slot_id": f"n{i}", "start_ms": i * 200000, "end_ms": i * 200000 + 3000, "media_type": "plate", "plate_type": "narration_plate", "rationale": "x"} for i in range(4)]
    rc, d, _ = run("variation_report", "--shot-plan", plan(npl))
    case("variation: narration_plate (last-resort fallback) is not trapped by a tiny cap", "ENRICH_CAP" not in codes(d, "FAIL"), str(codes(d)))

    sk = [slot(i, i * 4, i * 4 + 3, f"i{i}.jpg", ["push_slow", "drift_left", "pull_back"][i % 3], enrichments=[{"type": "keyword_pop", "at_ms": i * 4000 + 1000}]) for i in range(6)]
    rc, d, _ = run("variation_report", "--shot-plan", plan(sk), "--preset", "shorts_vertical")
    case("variation: shorts_vertical is exempt from the long-form keyword cap", "ENRICH_CAP" not in codes(d, "FAIL"), str(codes(d)))

    mj = [slot(0, 0, 4, "a.jpg", "push_slow", beat={"emotion": "tension", "intensity": 5})]
    out_md = os.path.join(TMP, "edit_report.md")
    rc = subprocess.run([PY, os.path.join(TOOLS, "variation_report.py"), "--shot-plan", plan(mj), "--out-md", out_md], capture_output=True, text=True).returncode
    md = open(out_md, encoding="utf-8").read() if os.path.exists(out_md) else ""
    case("variation: edit report written with rationale table + feedback block", "Creative choices and why" in md and "Owner feedback" in md and "**missing**" in md)


# ------------------------------------------------------------------ pacing_lib
def t_lib() -> None:
    s, pos = P.rect_to_scale_pos([0.05, 0.05, 0.9, 0.9])
    case("lib: rect_to_scale_pos centred push", abs(s - 111.111) < 0.01 and pos == [960.0, 540.0], f"{s} {pos}")
    s, pos = P.rect_to_scale_pos([0.0, 0.03, 0.92, 0.92])
    case("lib: rect_to_scale_pos left window shifts image right", pos[0] > 960 and s > 100, f"{s} {pos}")

    lib, pres = P.load_motion_library(), P.load_presets()
    hist: list[dict] = []
    seq = []
    for i in range(14):
        r = P.pick_motion(lib, pres, emotion="neutral", intensity=2, subject="wide", duration_s=4.0, history=hist, total_stills=i, aspect=1.78)
        hist.append({"move": r["move"], "direction": r["direction"]})
        seq.append(r["move"])
    run_ok = all(not (seq[i] == seq[i + 1] == seq[i + 2]) for i in range(len(seq) - 2))
    lateral_ok = all(not (hist[i]["direction"] == hist[i + 1]["direction"] and hist[i]["direction"] in ("left", "right")) for i in range(len(hist) - 1))
    case("lib: pick_motion never repeats a move 3x or a lateral direction twice", run_ok and lateral_ok, str(seq))
    grief = {P.pick_motion(lib, pres, emotion="grief", intensity=2, subject="portrait", history=[], faces=True)["move"] for _ in range(1)}
    case("lib: grief + face never picks punch_in / handheld", not (grief & {"punch_in", "handheld_micro"}), str(grief))
    r = P.pick_motion(lib, pres, emotion="tension", intensity=4, subject="object", has_target=False)
    case("lib: moves needing target_rect are skipped without one", r["move"] not in ("detail_crop", "reveal"), r["move"])
    r = P.pick_motion(lib, pres, emotion="tension", intensity=4, subject="object", has_target=True, preset="tense_fast")
    case("lib: tense_fast with a target can pick an event move", r["move"] in lib["moves"], r["move"])


def main() -> None:
    try:
        t_lib()
        t_still_hold()
        t_asset_audit()
        t_variation()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    bad = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} pacing self-test cases passed")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
