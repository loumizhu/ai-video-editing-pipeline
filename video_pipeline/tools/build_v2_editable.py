"""v2 of the full edit: same cut, audio and timing as v1, plus
  * every title/overlay as a NATIVE FilmCraft graphic (live text + shape layers, editable in FilmCraft)
  * atmosphere overlays from the asset library (35mm grain, dust specks, soft light) in SCREEN blend
  * hidden ALT tracks holding the researcher's alternative images under each shot (drag onto V1 to swap)
v1 (19_Child_Stars_Full_Edit_v1.fcproj) is left untouched.
    python build_v2_editable.py [--export]
"""
import glob, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import build_full_edit as B  # noqa: E402
import edit_plan as P  # noqa: E402
import fc_native_gfx as N  # noqa: E402
from fc_session import FCSession  # noqa: E402

NAME = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--name=")), "19_Child_Stars_Full_Edit_v2_Editable")
LIB = os.environ.get("VIDEO_ASSET_LIBRARY", r"E:\((Video_Editing_Asset_Library))\(( Video Overlays & Effects Library ))\01_Dust_Particles_Atmosphere")
OVD = os.path.join(B.FULL, "overlays")
TDIR = os.path.join(B.PRESET, "filmcraft_templates")
os.makedirs(TDIR, exist_ok=True)
fc, ticks, fr = B.fc, B.ticks, B.fr

# overlay usage: (overlay, opacity %, track, paragraph ranges [from, to] inclusive)
GRAIN_RANGES = [("P000", "P010"), ("P011", "P028"), ("P040", "P051"), ("P066", "P092")]   # period stories: 1970-1985 stills
SPECKS_RANGES = [("P000", "P008"), ("P082", "P082")]                                     # reconstructions
LIGHT_RANGES = [("P037", "P038"), ("P073", "P073"), ("P085", "P086"), ("P103", "P106")]   # warm emotional beats
TRACKS = [("V1", "V1 - Primary / A-Roll", "Forest"), ("V2", "V2 - FX: 35mm Grain (Overlay)", "Lavender"),
          ("V3", "V3 - FX: Dust / Light (Screen)", "Lavender"), ("V4", "V4 - Graphics (native, editable)", "Mango"),
          ("V5", "V5 - Graphics 2 (native, editable)", "Mango"), ("V6", "V6 - Panel portrait 1", "Cerulean"),
          ("V7", "V7 - Panel portrait 2", "Cerulean"), ("V8", "V8 - Panel portrait 3", "Cerulean"),
          ("V9", "V9 - ALT A (hidden: drag to V1)", "Iris"), ("V10", "V10 - ALT B (hidden: drag to V1)", "Iris"),
          ("V11", "V11 - ALT C (hidden: drag to V1)", "Iris"),
          ("A1", "A1 - Dialogue / Sync", "Forest"), ("A2", "A2 - Sound Effects (SFX)", "Rose"), ("A3", "A3 - Music Bed", "Violet"),
          ("A4", "A4 - Ambience / Scratch", "Tan")]


def loops():
    """Library clips are 3-8 s loops; make 5-minute loop copies (library untouched)."""
    os.makedirs(OVD, exist_ok=True)
    out = {}
    for n in ("film35", "specks", "softlight"):
        dst = os.path.join(OVD, f"{n}_loop300.mp4")
        if not os.path.exists(dst):
            B.sh(["ffmpeg", "-y", "-hide_banner", "-stream_loop", "-1", "-i", os.path.join(LIB, n + ".mp4"), "-t", "300", "-an",
                  "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p", dst])
        out[n] = dst
    return out


def para_span(segs, total, a, b):
    ids = B.PIDS
    i0, i1 = ids.index(a), ids.index(b)
    keep = set(ids[i0:i1 + 1])
    starts = [s["start"] for s in segs if s["pid"] in keep]
    ends = []
    for k, s in enumerate(segs):
        if s["pid"] in keep:
            ends.append(segs[k + 1]["start"] if k + 1 < len(segs) else total)
    return min(starts), max(ends)


def overlay_spans(segs, total, ranges, exclude_sb=True):
    spans = []
    for a, b in ranges:
        s0, s1 = para_span(segs, total, a, b)
        cuts = sorted((s["start"], s["start"] + s["dur"]) for s in segs if s["kind"] == "sb" and s0 <= s["start"] < s1) if exclude_sb else []
        cur = s0
        for c0, c1 in cuts:
            if c0 - cur > 1.0:
                spans.append((cur, c0))
            cur = max(cur, c1)
        if s1 - cur > 1.0:
            spans.append((cur, s1))
    out = []
    for a, b in spans:  # split > 290 s
        while b - a > 290:
            out.append((a, a + 290)); a += 290
        out.append((a, b))
    return [(fr(a), fr(b)) for a, b in out]


def alternatives(path):
    base = os.path.basename(path)
    if base.startswith("SHOT_"):
        grp = base[:8]  # SHOT_xx_
        d = os.path.dirname(path)
        return [f for f in sorted(glob.glob(os.path.join(d, grp + "*"))) if f != path and f.endswith(".png")]
    if base.startswith("NEW_"):
        g = base.split("_")[1]  # Gxx / Hxx
        d = os.path.dirname(path)
        return [f for f in sorted(glob.glob(os.path.join(d, f"NEW_{g}_*"))) if f != path]
    return []


def main():
    lay = B.L(); segs = lay["segs"]
    v1, total = B.visual_plan()
    gm = json.load(open(os.path.join(HERE, "graphics_manifest.json"), encoding="utf-8"))
    ov = loops()
    proj = os.path.join(HERE, NAME + ".fcproj")
    if os.path.exists(proj):
        os.remove(proj)
    B.sh([B.FC, "--save-as", proj, "exec", "file.newProject", json.dumps({"name": NAME})])
    bins = {}
    for b in ["01_Footage", "02_Audio", "03_B-Roll", "03b_Alternatives", "04_Graphics", "04b_FX_Overlays", "05_SFX", "06_Music", "07_Sequences"]:
        r = json.loads(fc("exec", "file.newBin", json.dumps({"name": b}), project=proj, save=True))
        bins[b] = r.get("bin")
    # alternatives per V1 still
    alt_place = []
    for c in v1:
        if c["kind"] != "still":
            continue
        used_here = {c["file"]}
        alts = [a for a in alternatives(c["file"]) if a not in used_here][:3]
        for k, a in enumerate(alts):
            alt_place.append((k, a, c["start"], c["end"]))
    sfx_files = sorted({os.path.join(B.PRESET, "sfx", x[2]) for x in P.SFX})
    files = {}
    for c in v1:
        files.setdefault(c["file"], "01_Footage" if c["kind"] == "video" else "03_B-Roll")
    for s in segs:
        if s["kind"] == "vo":
            files.setdefault(s["src"], "02_Audio")
    for _, a, _, _ in alt_place:
        files.setdefault(a, "03b_Alternatives")
    for g in gm:
        if g["family"] == "people-panel":
            for p in g["values"]["Panels"]:
                files.setdefault(os.path.normpath(p["Image"]), "03_B-Roll")
    for f in ov.values():
        files.setdefault(f, "04b_FX_Overlays")
    for f in sfx_files:
        files.setdefault(f, "05_SFX")
    files.setdefault(os.path.join(B.STEMS, "music_ducked.wav"), "06_Music")
    for f in sorted(glob.glob(os.path.join(B.FULL, "music", "*.mp3"))):
        files.setdefault(f, "06_Music")
    flist = list(files)
    ids = []
    for i in range(0, len(flist), 40):
        out = json.loads(fc("import", *flist[i:i + 40], project=proj, save=True))
        if out.get("errors"):
            raise SystemExit(f"import errors {out['errors']}")
        ids += out["items"]
    item = dict(zip(flist, ids))

    L1 = [{"id": "file.newSequence", "params": {"name": NAME + "_Master", "width": 1920, "height": 1080, "fps": 23.976, "video": 11, "audio": 4}}]
    for t, n, lab in TRACKS:
        L1.append({"id": "timeline.setTrack", "params": {"track": t, "name": n, "label": lab}})
    for c in v1:
        p = {"item": item[c["file"]], "track": "V1", "time": ticks(c["start"]), "duration": ticks(c["end"]) - ticks(c["start"]), "insert": False}
        p.update({"audioTrack": "A1", "sourceIn": ticks(c["src_in"]), "video": True, "audio": True} if c["kind"] == "video" else {"video": True, "audio": False})
        L1.append({"id": "timeline.place", "params": p})
    for s in segs:
        if s["kind"] == "vo":
            L1.append({"id": "timeline.place", "params": {"item": item[s["src"]], "track": "A1", "time": ticks(s["start"]), "sourceIn": ticks(s["src_in"]),
                                                          "duration": ticks(s["dur"]), "insert": False, "video": False, "audio": True}})
    for k, a, st, en in alt_place:
        L1.append({"id": "timeline.place", "params": {"item": item[a], "track": f"V{9 + k}", "time": ticks(st), "duration": ticks(en) - ticks(st),
                                                      "insert": False, "video": True, "audio": False}})
    fx_spans = {"film35": overlay_spans(segs, total, GRAIN_RANGES), "specks": overlay_spans(segs, total, SPECKS_RANGES),
                "softlight": overlay_spans(segs, total, LIGHT_RANGES)}
    for n, spans in fx_spans.items():
        for a, b in spans:
            L1.append({"id": "timeline.place", "params": {"item": item[ov[n]], "track": "V2" if n == "film35" else "V3", "time": ticks(a),
                                                          "duration": ticks(b) - ticks(a), "insert": False, "video": True, "audio": False}})
    pw = B.para_words()
    sfx_place = []
    for pid, ph, f, gdb in P.SFX:
        t = B.anchor_time(pid, ph, pw)
        p = os.path.join(B.PRESET, "sfx", f)
        d = min(B.dur(p), 3.0)
        sfx_place.append((t, p, d, gdb))
        L1.append({"id": "timeline.place", "params": {"item": item[p], "track": "A2", "time": ticks(max(0, t - 0.05)), "duration": ticks(d), "insert": False, "video": False, "audio": True}})
    L1.append({"id": "timeline.place", "params": {"item": item[os.path.join(B.STEMS, "music_ducked.wav")], "track": "A3", "time": 0, "duration": ticks(total), "insert": False, "video": False, "audio": True}})
    L1.append({"id": "markers.addChapter", "params": {"time": 0, "name": "Intro: The Golden Ticket"}})
    for s in segs:
        if s["kind"] == "chapter":
            L1.append({"id": "markers.addChapter", "params": {"time": ticks(s["start"]), "name": f"{s['label']}: {s['title'].title()}"}})
        if s["kind"] == "sb":
            sb = P.SB[s["key"]]
            L1.append({"id": "markers.add", "params": {"target": "program", "time": ticks(s["start"]), "name": f"Soundbite: {sb['who']}", "comment": sb["risk"],
                                                       "color": "Red" if sb["risk"].startswith("T3") else "Blue"}})
    jl = os.path.join(HERE, "_v2_build.jsonl")
    open(jl, "w", encoding="utf-8").write("\n".join(json.dumps(x, ensure_ascii=False) for x in L1) + "\n")
    out = fc("run", jl, project=proj, save=True)
    bad = [ln for ln in out.splitlines() if '"ok":false' in ln]
    print("pass1", len(L1), "commands,", len(bad), "failed", bad[:3], flush=True)

    # pass 2: clip-level settings
    seq = json.loads(fc("inspect", "sequence", project=proj))
    vt = {t["name"]: t["items"] for t in seq["video"]}
    at = {t["name"]: t["items"] for t in seq["audio"]}
    get = lambda d, pre: [v for k, v in d.items() if k.startswith(pre + " ")][0]
    v1c, a1c, a2c, a3c = get(vt, "V1"), get(at, "A1"), get(at, "A2"), get(at, "A3")
    L2 = []
    stills = [c for c in v1c if str(c["name"]).lower().endswith(".png")]
    vids = [c for c in v1c if not str(c["name"]).lower().endswith(".png")]
    for k, c in enumerate(stills):
        a, b = c["start"], c["end"] - B.TPF
        z0, z1 = (100.0, 107.0) if k % 2 == 0 else (107.0, 100.0)
        dx = [(-22, 0), (22, -10), (0, -18), (-14, 12)][k % 4]
        for prm, va, vb in (("scale", z0, z1), ("position", [960, 540], [960 + dx[0], 540 + dx[1]])):
            L2.append({"id": "effects.setParam", "params": {"clip": c["clip"], "effect": "motion", "param": prm, "value": va, "time": a, "keyframe": True}})
            L2.append({"id": "effects.setParam", "params": {"clip": c["clip"], "effect": "motion", "param": prm, "value": vb, "time": b, "keyframe": True}})
    for c in vids:
        L2.append({"id": "clip.fillFrame", "params": {"clips": [c["clip"]]}})
    for c in v1c[1:]:
        L2.append({"id": "sequence.applyVideoTransition", "params": {"clip": c["clip"], "effect": "cross_dissolve", "frames": 10, "edge": "in", "align": "center"}})
    gain = {ticks(s["start"]): s.get("gain_db", 0.0) for s in segs if s["kind"] in ("vo", "sb")}
    for c in a1c:
        g = gain.get(c["start"], min(gain.items(), key=lambda kv: abs(kv[0] - c["start"]))[1])
        if abs(g) > 0.05:
            L2.append({"id": "clip.audioGain", "params": {"clips": [c["clip"]], "mode": "set", "db": g}})
    for c, (t, p, d, gdb) in zip(sorted(a2c, key=lambda x: x["start"]), sorted(sfx_place)):
        L2.append({"id": "clip.audioGain", "params": {"clips": [c["clip"]], "mode": "set", "db": gdb}})
    # FX overlays: fill frame, Overlay blend for V2 grain (Screen banned to prevent milky blacks), Screen for V3 light
    op = {"V2": 30, "V3": None}
    for tname in ("V2", "V3"):
        for c in get(vt, tname):
            b_mode = "Overlay" if tname == "V2" else "Screen"
            o = 30 if tname == "V2" else (55 if "specks" in c["name"] else 32)
            L2.append({"id": "clip.fillFrame", "params": {"clips": [c["clip"]]}})
            L2.append({"id": "effects.setParam", "params": {"clip": c["clip"], "effect": "opacity", "param": "blend", "value": b_mode}})
            for tt, vv in ((c["start"], 0), (c["start"] + ticks(0.6), o), (c["end"] - ticks(0.6), o), (c["end"] - B.TPF, 0)):
                L2.append({"id": "effects.setParam", "params": {"clip": c["clip"], "effect": "opacity", "param": "opacity", "value": vv, "time": tt, "keyframe": True}})
            L2.append({"id": "edit.label", "params": {"clips": [c["clip"]], "label": "Lavender"}})
    alt_clips = [c["clip"] for k in (9, 10, 11) for c in get(vt, f"V{k}")]
    if alt_clips:
        L2.append({"id": "edit.label", "params": {"clips": alt_clips, "label": "Iris"}})
    for k in (9, 10, 11):
        L2.append({"id": "timeline.setTrack", "params": {"track": f"V{k}", "enabled": False}})
    L2.append({"id": "edit.label", "params": {"clips": [c["clip"] for c in v1c], "label": "Forest"}})
    L2.append({"id": "edit.label", "params": {"clips": [c["clip"] for c in a2c], "label": "Rose"}})
    L2.append({"id": "edit.label", "params": {"clips": [c["clip"] for c in a3c], "label": "Violet"}})
    L2.append({"id": "presets.import", "params": {"path": os.path.join(B.PRESET, "grade", "house-style.fcpreset").replace("\\", "/")}})
    L2.append({"id": "presets.apply", "params": {"preset": "HouseStyle_Documentary", "clips": [c["clip"] for c in v1c]}})
    L2.append({"id": "captions.import", "params": {"path": os.path.join(HERE, "captions.srt").replace("\\", "/"), "name": "C1 - Captions / Subtitles", "language": "en"}})
    by_bin = {}
    for f, b in files.items():
        by_bin.setdefault(b, []).append(item[f])
    for b, its in by_bin.items():
        L2.append({"id": "project.moveToBin", "params": {"items": its, "bin": bins[b]}})
    L2.append({"id": "project.moveToBin", "params": {"items": [seq["id"]], "bin": bins["07_Sequences"]}})
    jl2 = os.path.join(HERE, "_v2_build2.jsonl")
    open(jl2, "w", encoding="utf-8").write("\n".join(json.dumps(x, ensure_ascii=False) for x in L2) + "\n")
    out2 = fc("run", jl2, project=proj, save=True)
    bad2 = [ln for ln in out2.splitlines() if '"ok":false' in ln]
    print("pass2", len(L2), "commands,", len(bad2), "failed", bad2[:3], flush=True)

    # pass 3: native graphics via a live engine session
    s = FCSession(proj)
    lane_end = {3: -1.0, 4: -1.0}
    made, fails = [], []
    for g in sorted(gm, key=lambda x: x["time"]):
        trk = 3 if g["time"] >= lane_end[3] else 4
        lane_end[trk] = g["time"] + g["dur"]
        vals = dict(g["values"])
        vals.pop("Hold", None)

        def portrait(i, path, center, size, g=g):
            path = os.path.normpath(path)
            r = s.run("timeline.place", {"item": item[path], "track": f"V{6 + i}", "time": ticks(g["time"]), "duration": ticks(g["dur"]), "insert": False, "audio": False})
            c = r["clips"][0]
            sc = size[1] / 1080 * 100
            w = 1920 * sc / 100
            crop = max(0.0, (w - size[0]) / 2 / w * 100)
            s.run("effects.setParam", {"clip": c, "effect": "motion", "param": "scale", "value": round(sc, 3)})
            s.run("effects.setParam", {"clip": c, "effect": "motion", "param": "position", "value": list(center)})
            s.run("effects.apply", {"clips": [c], "effect": "crop"})
            s.run("effects.setParam", {"clip": c, "effect": "crop", "param": "left", "value": round(crop, 2)})
            s.run("effects.setParam", {"clip": c, "effect": "crop", "param": "right", "value": round(crop, 2)})
            t0 = ticks(g["time"] + 0.3 + i * 0.3)
            for tt, vv in ((t0, 0), (t0 + ticks(0.5), 100), (ticks(g["time"] + g["dur"] - 0.4), 100), (ticks(g["time"] + g["dur"]) - B.TPF, 0)):
                s.run("effects.setParam", {"clip": c, "effect": "opacity", "param": "opacity", "value": vv, "time": tt, "keyframe": True})
            s.run("clip.rename", {"clip": c, "name": f"Portrait {i + 1}: " + os.path.basename(path)[:50]})

        try:
            clip, err = None, None
            for tr in [trk, 7 - trk] + [5, 6, 7]:
                try:
                    clip = N.build_graphic(s, g["family"], vals, g["time"], g["dur"], tr, portrait_place=portrait)
                    break
                except Exception as e:
                    err = e
                    if "is not free" not in str(e):
                        raise
            if clip is None:
                raise err
            made.append((g["id"], g["family"], clip))
            s.run("markers.add", {"target": "program", "time": ticks(g["time"]), "name": f"Gfx: {g['family']}", "comment": f"{g['pid']} {g['phrase'] or ''} (native, editable)", "color": "Green"})
        except Exception as e:
            fails.append((g["id"], g["family"], str(e)[:300]))
            print("GFX FAIL", g["id"], g["family"], str(e)[:300], flush=True)
    # one reusable template per family into the user's Graphics Templates (best effort)
    tmpl = []
    seen = set()
    for gid, fam, clip in made:
        if fam in seen:
            continue
        seen.add(fam)
        try:
            tp = os.path.join(TDIR, f"House_{fam}.fcgt")
            s.run("graphics.template.export", {"clip": clip, "name": f"House - {fam}", "category": "Publora House Style",
                                               "description": f"documentary-default {fam}, native layers", "path": tp})
            try:
                s.run("graphics.template.install", {"path": tp})
            except Exception:
                pass
            tmpl.append(fam)
        except Exception as e:
            print("template export failed", fam, str(e)[:200])
    notes = (f"{NAME}: v2 of the full edit with EDITABLE native graphics. Graphics on V4/V5 are FilmCraft Graphic clips: select one, "
             "edit text/font/colour/position in Essential Graphics; plates are pinned to their text and resize with it; in/out animation "
             "is keyframed inside Responsive intro/outro (trim freely). V2/V3 = 35mm grain / dust / soft light overlays in Screen blend. "
             "V9-V11 = hidden alternative images for each shot (drag onto V1 to swap). Narration Voicebox 'Jessica from Ihateediting'.")
    s.run("project.setNotes", {"text": notes})
    s.run("file.save", {})
    s.close()
    rep = {"project": proj, "total_s": total, "v1": len(v1c), "native_graphics": len(made), "graphics_failed": fails, "templates": tmpl,
           "alternatives": len(alt_place), "fx_clips": {k: len(v) for k, v in fx_spans.items()}, "pass1_failed": len(bad), "pass2_failed": len(bad2)}
    json.dump(rep, open(os.path.join(HERE, NAME + "_build_report.json"), "w"), indent=1)
    print(json.dumps(rep))
    if "--export" in sys.argv:
        exp = os.path.join(B.FULL, "Export", NAME + "_preview.mp4")
        fc("exec", "file.exportMedia", json.dumps({"path": exp.replace("\\", "/"), "format": "h264", "loudnessLufs": -14.0, "wait": True}), project=proj)
        print("export ->", exp)


if __name__ == "__main__":
    main()
