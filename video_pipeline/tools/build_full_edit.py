"""Build the full FilmCraft edit of video 19 from edit_plan.py.

Stages (each writes to disk, re-runnable):
  layout   -> Source/layout.json          VO paragraph placements + soundbites + chapter gaps (timeline seconds)
  audio    -> Source/stems/*.wav          dialogue timeline, VO-only timeline, music bed, ducked music
  words    -> Source/vo_timeline.words.json  Groq word timings on the timeline (for anchors + captions)
  graphics -> Source/graphics/*.mov       EffectCraft house families, Hold matched to the narration
  fcproj   -> Source/19_Child_Stars_Full_Edit_v1.fcproj
  python build_full_edit.py all | layout | audio | words | graphics | fcproj | export
"""
import json, os, re, subprocess, sys, glob, math

HERE = os.path.dirname(os.path.abspath(__file__))
FULL = os.path.dirname(HERE)                         # 07_Video_Edit/Full_Edit_v1
PROJ = os.path.normpath(os.path.join(FULL, "..", ".."))  # video project root
VP = os.path.normpath(os.path.join(PROJ, "..", "Video_Pipeline"))
PRESET = os.path.join(VP, "presets", "documentary-default")
FC = r"C:\Program Files\FilmCraft\filmcraft-cli.exe"
TPS = 254016000000
FPS = 24000 / 1001
TPF = 10594584000
NAME = "19_Child_Stars_Full_Edit_v1"
sys.path.insert(0, HERE)
import edit_plan as P  # noqa
sys.path.insert(1, os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", "Video_Pipeline", "tools")))
tools_cand = os.path.abspath(os.path.dirname(__file__))
if tools_cand not in sys.path:
    sys.path.insert(1, tools_cand)
import soundbite_bounds as SBB  # noqa
try:  # pacing standard (PACING_AND_ENRICHMENT.md): still-hold cap + motion library
    import pacing_lib as PL  # noqa
except Exception:  # builder keeps working without it
    PL = None


def resolve_sfx(f):
    p1 = os.path.join(PRESET, "sfx", f)
    if os.path.exists(p1):
        return p1
    central = r"E:\((Video_Editing_Asset_Library))\(( Production Audio Library ))\02_SFX"
    if os.path.exists(central):
        for r, _, files in os.walk(central):
            if f in files:
                return os.path.join(r, f)
    return p1


def sb_range(sb):
    """Sentence-bounded, silence-snapped in/out for a soundbite (never mid-sentence, never mid-word)."""
    src = os.path.join(PROJ, sb["src"]) if sb["src"].startswith("03_") else os.path.join(FULL, sb["src"])
    base = os.path.splitext(os.path.basename(src))[0]
    wj = os.path.join(FULL, "media_new", "transcripts", base + ".words.json")
    d = json.load(open(wj, encoding="utf-8"))
    r = SBB.snap(src, d["words"] if isinstance(d, dict) else d, sb["in"], sb["out"], partial=bool(sb.get("split")), media_dur=dur(src))
    return src, r["in"], r["out"]

STEMS = os.path.join(HERE, "stems"); os.makedirs(STEMS, exist_ok=True)
GDIR = os.path.join(HERE, "graphics"); os.makedirs(GDIR, exist_ok=True)
PARAS = json.load(open(os.path.join(FULL, "vo", "paragraphs.json"), encoding="utf-8"))
PIDS = [p["id"] for p in PARAS]


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    if r.returncode != 0:
        raise SystemExit(f"FAILED {cmd[:3]}: {(r.stderr or r.stdout)[-1200:]}")
    return r.stdout + r.stderr


def fc(*args, project=None, save=False):
    cmd = [FC, "--compact"] + (["--project", project] if project else []) + (["--save"] if save else []) + list(args)
    return sh(cmd)


def color_groups(v1c, ca, ticks_fn, probe_s=0.25):
    """Colour script (COLOR_SCRIPT.md): map V1 clips to their planned look by the planned shot whose span contains the
    clip's start + probe_s (robust to small layout offsets; a neighbouring shot inside one phase carries the same look).
    Returns ({look: (fcpreset_path, [clip ids])}, [unmatched clip ids -> house grade]). Clips matched to a shot the
    plan marks graded:false (generated plates) get no grade at all."""
    shots = sorted(ca.get("shots", []), key=lambda s: s["start"])
    groups, unmatched = {}, []
    for c in v1c:
        t = c["start"] + ticks_fn(probe_s)
        best = next((s for s in shots if ticks_fn(s["start"]) <= t < ticks_fn(s["end"])), None)
        if best is None:
            unmatched.append(c["clip"])
            continue
        if not best.get("graded"):
            continue
        lk = best["look"]
        groups.setdefault(lk, (ca["looks"][lk]["fcpreset"], []))[1].append(c["clip"])
    return groups, unmatched


def fr(sec):  # snap seconds to frame grid
    return round(sec * FPS) / FPS


def ticks(sec):
    return int(round(sec * FPS)) * TPF


def media(alias):
    kind, key = alias.split(":", 1)
    if kind == "E":
        return os.path.join(PROJ, "03_media", "conformed", P.E[key])
    if kind == "N":
        m = glob.glob(os.path.join(FULL, "media_new", "conformed", f"NEW_{key}_*.png"))
        if not m:
            raise SystemExit(f"missing media {alias}")
        return m[0]
    raise SystemExit(alias)


def dur(path):
    return float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).strip())


def speech_bounds(wav):
    out = sh(["ffmpeg", "-hide_banner", "-i", wav, "-af", "silencedetect=noise=-42dB:d=0.12", "-f", "null", "-"])
    d = dur(wav)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    s0 = ends[0] if starts and starts[0] < 0.02 and ends else 0.0
    s1 = starts[-1] if starts and (not ends or len(starts) > len(ends) or ends[-1] >= d - 0.02) else d
    if s1 <= s0:
        s0, s1 = 0.0, d
    return max(0.0, s0 - 0.06), min(d, s1 + 0.14)


def load_words(path):
    d = json.load(open(path, encoding="utf-8"))
    return d["words"] if isinstance(d, dict) else d


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


# ------------------------------------------------------------------ layout
def stage_layout():
    chap = {c[0]: c for c in P.CHAPTERS}
    after = {v["after"]: k for k, v in P.SB.items() if v.get("after")}
    split = {v["split"][0]: (k, v["split"][1]) for k, v in P.SB.items() if v.get("split")}
    segs, t = [], 0.6
    for pid in PIDS:
        wav = os.path.join(FULL, "vo", "paras", pid + ".wav")
        if not os.path.exists(wav):
            raise SystemExit(f"missing VO {wav}")
        if pid in chap:
            segs.append({"kind": "chapter", "pid": pid, "start": fr(t), "dur": fr(chap[pid][4]), "label": chap[pid][1], "title": chap[pid][2], "bg": chap[pid][3]})
            t += chap[pid][4]
        a, b = speech_bounds(wav)
        if pid in split:
            sbk, phrase = split[pid]
            wj = os.path.join(FULL, "vo", "paras", pid + ".words.json")
            if not os.path.exists(wj):
                sh([sys.executable, os.path.join(VP, "tools", "transcribe_groq.py"), "--input", wav, "--out", wj])
            ws = load_words(wj)
            hits = [w for w in ws if norm(w.get("word", w.get("text", ""))) == norm(phrase)]
            b = hits[-1]["start"] - 0.02
            segs.append({"kind": "vo", "pid": pid, "start": fr(t), "src": wav, "src_in": a, "dur": fr(b - a), "split": True})
            t += (b - a) + 0.05
            sb = P.SB[sbk]
            src, a_in, a_out = sb_range(sb)
            segs.append({"kind": "sb", "pid": pid, "key": sbk, "start": fr(t), "src": src, "src_in": a_in, "dur": fr(a_out - a_in)})
            t += a_out - a_in + P.PAUSE.get(pid, 0.6)
            continue
        segs.append({"kind": "vo", "pid": pid, "start": fr(t), "src": wav, "src_in": a, "dur": fr(b - a)})
        t += (b - a) + P.PAUSE.get(pid, 0.45)
        if pid in after:
            sb = P.SB[after[pid]]
            t += 0.2
            src, a_in, a_out = sb_range(sb)
            segs.append({"kind": "sb", "pid": pid, "key": after[pid], "start": fr(t), "src": src, "src_in": a_in, "dur": fr(a_out - a_in)})
            t += a_out - a_in + 0.55
    total = fr(t + 2.5)
    json.dump({"total": total, "segs": segs}, open(os.path.join(HERE, "layout.json"), "w", encoding="utf-8"), indent=1)
    print("layout", len(segs), "segments", round(total, 1), "s")


def L():
    return json.load(open(os.path.join(HERE, "layout.json"), encoding="utf-8"))


# ------------------------------------------------------------------ audio stems
def mix_segments(segs, total, out, kinds):
    parts, inputs = [], []
    for s in segs:
        if s["kind"] not in kinds:
            continue
        i = len(inputs) // 2
        inputs += ["-i", s["src"]]
        gain = s.get("gain_db", 0.0)
        parts.append(f"[{i}:a]atrim={s['src_in']:.4f}:{s['src_in'] + s['dur']:.4f},asetpts=PTS-STARTPTS,aresample=48000,"
                     f"aformat=channel_layouts=mono,volume={gain}dB,afade=t=in:d=0.02,afade=t=out:st={max(0, s['dur'] - 0.03):.3f}:d=0.03,"
                     f"adelay={int(s['start'] * 1000)}:all=1[a{i}]")
    n = len(parts)
    fg = ";".join(parts) + ";" + "".join(f"[a{k}]" for k in range(len(inputs) // 2)) + f"amix=inputs={n}:normalize=0:dropout_transition=0,apad=whole_dur={total:.3f},atrim=0:{total:.3f}[o]"
    script = out + ".filter.txt"
    open(script, "w").write(fg)
    sh(["ffmpeg", "-y", "-hide_banner"] + inputs + ["-filter_complex_script", script, "-map", "[o]", "-ar", "48000", "-c:a", "pcm_s16le", out])


def lufs(path, start=None, d=None):
    cmd = ["ffmpeg", "-hide_banner"] + (["-ss", str(start), "-t", str(d)] if start is not None else []) + ["-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"]
    out = sh(cmd)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", out)
    return float(m[-1]) if m else -23.0


def stage_audio():
    lay = L(); segs, total = lay["segs"], lay["total"]
    # loudness: every VO paragraph and every soundbite to -16 LUFS (clip gain, also applied in FilmCraft)
    for s in segs:
        if s["kind"] in ("vo", "sb"):
            v = lufs(s["src"], s["src_in"], s["dur"]) if s["dur"] > 0.6 else -16.0
            s["gain_db"] = round(max(-12, min(14, -16.0 - v)), 2) if v > -60 else 0.0
    json.dump(lay, open(os.path.join(HERE, "layout.json"), "w", encoding="utf-8"), indent=1)
    mix_segments(segs, total, os.path.join(STEMS, "vo_only_timeline.wav"), {"vo"})
    mix_segments(segs, total, os.path.join(STEMS, "dialogue_timeline.wav"), {"vo", "sb"})
    sbonly = [s for s in segs if s["kind"] == "sb"]
    mix_segments(sbonly, total, os.path.join(STEMS, "soundbites_timeline.wav"), {"sb"})
    # music bed: one track per section, crossfaded 2.5 s, looped when short
    starts = {}
    for s in segs:
        starts.setdefault(s["pid"], s["start"])
    secs = [(starts[p], f, off) for p, f, off in P.MUSIC]
    inputs, parts = [], []
    for i, (st, f, off) in enumerate(secs):
        en = secs[i + 1][0] + 2.5 if i + 1 < len(secs) else total
        ln = en - st
        src = os.path.join(FULL, "music", f)
        if not os.path.exists(src):
            central_f = os.path.join(r"E:\((Video_Editing_Asset_Library))\(( Production Audio Library ))\01_Music\All_Tracks", f)
            if os.path.exists(central_f):
                os.makedirs(os.path.join(FULL, "music"), exist_ok=True)
                try:
                    os.link(central_f, src)
                except Exception:
                    shutil.copy2(central_f, src)
        inputs += ["-stream_loop", "-1", "-i", src]
        parts.append(f"[{i}:a]atrim={off}:{off + ln:.3f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,"
                     f"afade=t=in:d=2.5,afade=t=out:st={max(0, ln - 2.5):.3f}:d=2.5,adelay={int(st * 1000)}:all=1[m{i}]")
    n = len(parts)
    fg = ";".join(parts) + ";" + "".join(f"[m{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0,apad=whole_dur={total:.3f},atrim=0:{total:.3f},afade=t=out:st={total - 4:.3f}:d=4[o]"
    raw = os.path.join(STEMS, "music_bed_raw.wav")
    open(raw + ".filter.txt", "w").write(fg)
    sh(["ffmpeg", "-y", "-hide_banner"] + inputs + ["-filter_complex_script", raw + ".filter.txt", "-map", "[o]", "-ar", "48000", "-c:a", "pcm_s16le", raw])
    # bed to -18 LUFS open level, then two-level sidechain ducking with true-peak limiter (-1 dBTP ceiling)
    lv = lufs(raw)
    fg2 = (f"[2:a]volume={-18.0 - lv:.2f}dB[bed];[0:a]aformat=channel_layouts=mono,asplit=1[k1];[1:a]aformat=channel_layouts=mono[k2];"
           "[bed][k1]sidechaincompress=threshold=0.0265:ratio=20:attack=100:release=600:makeup=1[b1];"
           "[b1][k2]sidechaincompress=threshold=0.010:ratio=20:attack=100:release=600:makeup=1[b2];"
           "[b2]alimiter=limit=0.891:level=false[o]")
    sh(["ffmpeg", "-y", "-hide_banner", "-i", os.path.join(STEMS, "vo_only_timeline.wav"), "-i", os.path.join(STEMS, "soundbites_timeline.wav"),
        "-i", raw, "-filter_complex", fg2, "-map", "[o]", "-ar", "48000", "-c:a", "pcm_s16le", os.path.join(STEMS, "music_ducked.wav")])
    print("audio stems done", round(total, 1), "s; bed open level", round(lv, 1))


# ------------------------------------------------------------------ words
def stage_words():
    out = os.path.join(HERE, "vo_timeline.words.json")
    sh([sys.executable, os.path.join(VP, "tools", "transcribe_groq.py"), "--input", os.path.join(STEMS, "vo_only_timeline.wav"), "--out", out, "--force"])
    print("words ->", out)


def para_words():
    ws = load_words(os.path.join(HERE, "vo_timeline.words.json"))
    segs = [s for s in L()["segs"] if s["kind"] == "vo"]
    by = {}
    for w in ws:
        mid = (w["start"] + w["end"]) / 2
        for s in segs:
            if s["start"] - 0.15 <= mid <= s["start"] + s["dur"] + 0.15:
                by.setdefault(s["pid"], []).append(w)
                break
    return by


def anchor_time(pid, phrase, pw):
    segs = {s["pid"]: s for s in L()["segs"] if s["kind"] == "vo"}
    s = segs[pid]
    if not phrase:
        return s["start"]
    for w in pw.get(pid, []):
        if norm(w.get("word", w.get("text", ""))).startswith(norm(phrase)):
            return max(s["start"], w["start"] - 0.1)
    print(f"  ! anchor '{phrase}' not heard in {pid}, using paragraph start")
    return s["start"]


def para_end(pid):
    ss = [s for s in L()["segs"] if s["pid"] == pid and s["kind"] in ("vo", "sb")]
    return max(s["start"] + s["dur"] for s in ss)


# ------------------------------------------------------------------ graphics
def render_family(fam, values, out):
    vp = out + ".values.json"
    json.dump(values, open(vp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    r = subprocess.run([sys.executable, os.path.join(PRESET, "render_family.py"), "--family", fam, "--values", vp, "--out", out],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"{fam} failed: {(r.stderr or r.stdout)[-800:]}")
    return dur(out)


def gfx_list():
    """[(id, pid, phrase, family, values)] incl. chapter cards and people panels."""
    out = []
    for i, (pid, ph, fam, vals) in enumerate(P.G):
        out.append((f"G{i:02d}", pid, ph, fam, dict(vals)))
    for i, c in enumerate(P.CHAPTERS):
        out.append((f"C{i}", c[0], "__chapter__", "chapter-card", {"Chapter": c[1], "Title": c[2]}))
    for i, (pid, ph, v) in enumerate(P.PANELS):
        panels = []
        for a, nm, role in v["Panels"]:
            panels.append({"Image": media(a).replace("\\", "/"), "Name": nm, "Role": role, "FX": 960, "FY": 470})
        out.append((f"PP{i}", pid, ph, "people-panel", {"Title": v["Title"], "Panels": panels}))
    return out


def para_span_end(pid):
    """End of the paragraph's on-screen span: start of the next segment that belongs to another paragraph."""
    segs = L()["segs"]
    idx = [i for i, x in enumerate(segs) if x["pid"] == pid]
    nxt = idx[-1] + 1
    return segs[nxt]["start"] if nxt < len(segs) else L()["total"], (segs[nxt] if nxt < len(segs) else None)


def clamp_graphic(pid, t, d, family):
    """A text card about a paragraph must leave when the narration moves on (owner rule 2026-11-08).
    Short paragraphs may borrow the next VO paragraph, never a soundbite or a chapter card."""
    end, nxt = para_span_end(pid)
    lim = end - 0.15
    if lim - t < 2.4 and nxt is not None and nxt["kind"] == "vo":
        lim = min(para_span_end(nxt["pid"])[0] - 0.15, t + d)
    return max(1.6, min(d, lim - t))


def stage_graphics_plan():
    """Native-graphics plan: anchor times + durations clamped to the narration (no rendering)."""
    import fc_native_gfx as NG
    pw = para_words()
    man = []
    for gid, pid, ph, fam, vals in gfx_list():
        if ph == "__chapter__":
            t = [x for x in L()["segs"] if x["kind"] == "chapter" and x["pid"] == pid][0]["start"] + 0.15
            d = NG.DEFAULT_DUR[fam]
        else:
            t = anchor_time(pid, ph, pw)
            for cs in L()["segs"]:
                if cs["kind"] == "chapter" and cs["start"] - 0.5 <= t < cs["start"] + 5.4:
                    t = cs["start"] + 5.4
            if isinstance(vals.get("Hold"), str) and vals["Hold"].startswith("auto:"):
                hp = vals["Hold"].split(":")[1]
                d = max(2.5, para_end(hp) - t + 0.3)
            elif fam in ("quote-pullout", "kinetic-quote") and ph is None:
                d = max(3.0, para_end(pid) - t + 0.5)
            else:
                d = NG.DEFAULT_DUR[fam]
            hold_pid = vals["Hold"].split(":")[1] if isinstance(vals.get("Hold"), str) and vals["Hold"].startswith("auto:") else pid
            d = clamp_graphic(hold_pid, t, d, fam) if hold_pid == pid else min(d, para_span_end(hold_pid)[0] - 0.15 - t)
        vals.pop("Hold", None)
        man.append({"id": gid, "pid": pid, "phrase": ph, "family": fam, "time": fr(t), "dur": fr(d), "file": None, "values": vals})
        print(gid, fam, pid, round(t, 2), round(d, 2), flush=True)
    json.dump(man, open(os.path.join(HERE, "graphics_manifest.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def stage_graphics():
    pw = para_words()
    man = []
    for gid, pid, ph, fam, vals in gfx_list():
        if ph == "__chapter__":
            t = [s for s in L()["segs"] if s["kind"] == "chapter" and s["pid"] == pid][0]["start"] + 0.15
        else:
            t = anchor_time(pid, ph, pw)
            for cs in L()["segs"]:
                if cs["kind"] == "chapter" and cs["start"] - 0.5 <= t < cs["start"] + 5.4:
                    t = cs["start"] + 5.4  # never stack a graphic on a chapter card
        if isinstance(vals.get("Hold"), str) and vals["Hold"].startswith("auto:"):
            end = para_end(vals["Hold"].split(":")[1])
            vals["Hold"] = round(max(2.0, end - t - 1.2), 2)
        elif fam in ("quote-pullout", "kinetic-quote") and ph is None:
            vals["Hold"] = round(max(2.5, para_end(pid) - t - 0.6), 2)
        out = os.path.join(GDIR, f"{gid}_{fam}.mov")
        d = render_family(fam, vals, out)
        man.append({"id": gid, "pid": pid, "phrase": ph, "family": fam, "time": fr(t), "dur": fr(d), "file": out, "values": vals})
        print(gid, fam, pid, round(t, 2), round(d, 2), flush=True)
    json.dump(man, open(os.path.join(HERE, "graphics_manifest.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)


# ------------------------------------------------------------------ captions
def srt_t(x):
    h, r = divmod(x, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)) % 1000:03d}"


def stage_captions():
    ws = load_words(os.path.join(HERE, "vo_timeline.words.json"))
    lay = L()
    allw = [(w["start"], w["end"], w.get("word", w.get("text", "")).strip()) for w in ws]
    tdir = os.path.join(FULL, "media_new", "transcripts")
    for s in lay["segs"]:
        if s["kind"] != "sb":
            continue
        base = os.path.splitext(os.path.basename(s["src"]))[0]
        sw = load_words(os.path.join(tdir, base + ".words.json"))
        for w in sw:
            if s["src_in"] - 0.05 <= w["start"] and w["end"] <= s["src_in"] + s["dur"] + 0.05:
                off = s["start"] - s["src_in"]
                allw.append((w["start"] + off, w["end"] + off, w.get("word", w.get("text", "")).strip()))
    allw.sort()
    cues, cur = [], []
    for w in allw:
        if cur and (len(" ".join(x[2] for x in cur + [w])) > 42 or w[0] - cur[-1][1] > 0.6):
            cues.append(cur); cur = []
        cur.append(w)
        if w[2].endswith((".", "?", "!")) and len(" ".join(x[2] for x in cur)) > 18:
            cues.append(cur); cur = []
    if cur:
        cues.append(cur)
    with open(os.path.join(HERE, "captions.srt"), "w", encoding="utf-8") as f:
        for i, c in enumerate(cues, 1):
            f.write(f"{i}\n{srt_t(c[0][0])} --> {srt_t(max(c[-1][1], c[0][0] + 0.8))}\n{' '.join(x[2] for x in c)}\n\n")
    print("captions", len(cues))


# ------------------------------------------------------------------ FilmCraft
def group_of(path):
    b = os.path.basename(path)
    if b.startswith("SHOT_"):
        return b[:7]
    if b.startswith("NEW_"):
        return b.split("_")[1]
    return b


_STOP = {"the", "of", "a", "b", "and", "in", "with", "still", "photo", "portrait", "1970s", "1980s", "vintage", "wide", "close", "closeup"}


def _slug_tokens(path):
    b = os.path.splitext(os.path.basename(path))[0]
    b = re.sub(r"^SHOT_\d+_\d{4}-\d{4}_A\d_", "", b)
    b = re.sub(r"^NEW_[GH]\d+_\d+_", "", b)
    return b.split("_")


def same_idea(a, b):
    """Two alternatives of ONE visual idea (e.g. two rotary-phone pictures): same research group and near-identical subject.
    Different places/people from one research beat (Berkeley -> UCLA -> Beverly Hills) are NOT the same idea."""
    if group_of(a) != group_of(b):
        return False
    ta, tb = _slug_tokens(a), _slug_tokens(b)
    if ta[:2] == tb[:2]:
        return True
    sa, sb_ = {x for x in ta if x not in _STOP}, {x for x in tb if x not in _STOP}
    return len(sa & sb_) / max(1, len(sa | sb_)) >= 0.4


def visual_plan():
    lay = L(); segs = lay["segs"]; total = lay["total"]
    # spans: each segment owns time until the next segment starts
    spans = []
    for i, s in enumerate(segs):
        en = segs[i + 1]["start"] if i + 1 < len(segs) else total
        spans.append((s, s["start"] if i else 0.0, en))
    v1 = []
    for s, a, b in spans:
        if s["kind"] == "sb":
            v1.append({"kind": "video", "file": s["src"], "start": a, "end": b, "src_in": s["src_in"] - (s["start"] - a), "sb": s["key"]})
            continue
        if s["kind"] == "chapter":
            v1.append({"kind": "still", "file": media(s["bg"]), "start": a, "end": b})
            continue
        if s.get("split"):
            vis = P.V[s["pid"]][:2]
        else:
            vis = P.V[s["pid"]]
        n = max(1, min(len(vis), int((b - a) // 2.6)))
        vis = vis[:n]
        step = (b - a) / n
        for k, al in enumerate(vis):
            v1.append({"kind": "still", "file": media(al), "start": a + k * step, "end": a + (k + 1) * step, "pid": s["pid"]})
    # frame-snap boundaries, keep contiguous
    for c in v1:
        c["start"], c["end"] = fr(c["start"]), fr(c["end"])
    for i in range(1, len(v1)):
        v1[i]["start"] = v1[i - 1]["end"]
    # merge consecutive stills that are the same image OR the same image group (e.g. two rotary-phone
    # alternatives for one line): the second adds nothing; it stays available on the hidden ALT tracks
    # The still-hold cap beats the same-idea merge: a merge that would keep one idea on screen longer than the preset's
    # hard cap is NOT done (a second picture of the same idea is the lesser evil next to a 9-12 s hold).
    hard = 6.0
    if PL:
        _p = PL.load_presets()
        hard = _p["presets"][_p["default_preset"]]["still_hard_max_s"]
    out = []
    for c in v1:
        if out and c["kind"] == "still" and out[-1]["kind"] == "still" and (out[-1]["file"] == c["file"] or same_idea(out[-1]["file"], c["file"]))                 and (c["end"] - out[-1]["start"]) <= hard + 1e-6:
            out[-1]["end"] = c["end"]
        else:
            out.append(c)
    # report every still that is still too long (QA stage 10 FAILs on it; the builder never stops, per the bypass policy)
    long_runs = []
    for c in out:
        if c["kind"] == "still" and c["end"] - c["start"] > hard + 1e-6:
            long_runs.append({"file": os.path.basename(c["file"]), "start": round(c["start"], 2), "dur": round(c["end"] - c["start"], 2),
                              "fix": "add distinct shots / plates (enrichment_catalog.json fix_order_for_long_still) or run asset_audit.py for research requests"})
    if long_runs:
        print(f"WARN {len(long_runs)} still(s) longer than the {hard}s hold cap; worst {max(r['dur'] for r in long_runs)}s -> still_hold_warnings.json")
    json.dump(long_runs, open(os.path.join(HERE, "still_hold_warnings.json"), "w", encoding="utf-8"), indent=1)
    return out, total


def stage_fcproj():
    lay = L(); segs = lay["segs"]
    v1, total = visual_plan()
    gm = json.load(open(os.path.join(HERE, "graphics_manifest.json"), encoding="utf-8"))
    proj = os.path.join(HERE, NAME + ".fcproj")
    if os.path.exists(proj):
        os.remove(proj)
    sh([FC, "--save-as", proj, "exec", "file.newProject", json.dumps({"name": NAME})])
    # bins first
    bins = {}
    for b in ["01_Footage", "02_Audio", "03_B-Roll", "04_Graphics", "05_SFX", "06_Music", "07_Sequences"]:
        r = json.loads(fc("exec", "file.newBin", json.dumps({"name": b}), project=proj, save=True))
        bins[b] = r.get("bin") or r.get("id") or r.get("result", {}).get("bin")
    sfx_files = sorted({resolve_sfx(x[2]) for x in P.SFX})
    files = {}  # path -> bin
    for c in v1:
        files.setdefault(c["file"], "01_Footage" if c["kind"] == "video" else "03_B-Roll")
    for s in segs:
        if s["kind"] == "vo":
            files.setdefault(s["src"], "02_Audio")
    for g in gm:
        files.setdefault(g["file"], "04_Graphics")
    for f in sfx_files:
        files.setdefault(f, "05_SFX")
    files.setdefault(os.path.join(STEMS, "music_ducked.wav"), "06_Music")
    for f in sorted(glob.glob(os.path.join(FULL, "music", "*.mp3"))):
        files.setdefault(f, "06_Music")
    flist = list(files)
    ids = []
    for i in range(0, len(flist), 40):
        out = json.loads(fc("import", *flist[i:i + 40], project=proj, save=True))
        if out.get("errors"):
            raise SystemExit(f"import errors {out['errors']}")
        ids += out["items"]
    item = dict(zip(flist, ids))
    lines = [{"id": "file.newSequence", "params": {"name": NAME + "_Master", "width": 1920, "height": 1080, "fps": 23.976, "video": 4, "audio": 4}}]
    for t, n, lab in (("V1", "V1 - Primary / A-Roll", "Forest"), ("V2", "V2 - B-Roll / Inserts", "Cerulean"), ("V3", "V3 - Graphics / Titles", "Mango"),
                      ("V4", "V4 - Graphics 2 / Overlays", "Lavender"), ("A1", "A1 - Dialogue / Sync", "Forest"), ("A2", "A2 - Sound Effects (SFX)", "Rose"),
                      ("A3", "A3 - Music Bed", "Violet"), ("A4", "A4 - Ambience / Scratch", "Tan")):
        lines.append({"id": "timeline.setTrack", "params": {"track": t, "name": n, "label": lab}})
    for c in v1:
        p = {"item": item[c["file"]], "track": "V1", "time": ticks(c["start"]), "duration": ticks(c["end"]) - ticks(c["start"]), "insert": False}
        if c["kind"] == "video":
            p.update({"audioTrack": "A1", "sourceIn": ticks(c["src_in"]), "video": True, "audio": True})
        else:
            p.update({"video": True, "audio": False})
        lines.append({"id": "timeline.place", "params": p})
    for s in segs:
        if s["kind"] == "vo":
            lines.append({"id": "timeline.place", "params": {"item": item[s["src"]], "track": "A1", "time": ticks(s["start"]), "sourceIn": ticks(s["src_in"]),
                                                             "duration": ticks(s["dur"]), "insert": False, "video": False, "audio": True}})
    lane_end = {"V3": -1.0, "V4": -1.0}
    for g in sorted(gm, key=lambda x: x["time"]):
        g["track"] = "V3" if g["time"] >= lane_end["V3"] else "V4"
        lane_end[g["track"]] = g["time"] + g["dur"]
    for g in gm:
        lines.append({"id": "timeline.place", "params": {"item": item[g["file"]], "track": g["track"], "time": ticks(g["time"]), "duration": ticks(g["dur"]),
                                                         "insert": False, "video": True, "audio": False}})
    pw = para_words()
    sfx_place = []
    for pid, ph, f, gdb in P.SFX:
        t = anchor_time(pid, ph, pw)
        p = resolve_sfx(f)
        d = min(dur(p), 3.0)
        sfx_place.append((t, p, d, gdb))
        lines.append({"id": "timeline.place", "params": {"item": item[p], "track": "A2", "time": ticks(max(0, t - 0.05)), "duration": ticks(d), "insert": False, "video": False, "audio": True}})
    lines.append({"id": "timeline.place", "params": {"item": item[os.path.join(STEMS, "music_ducked.wav")], "track": "A3", "time": 0, "duration": ticks(total), "insert": False, "video": False, "audio": True}})
    # markers
    for s in segs:
        if s["kind"] == "chapter":
            lines.append({"id": "markers.addChapter", "params": {"time": ticks(s["start"]), "name": f"{s['label']}: {s['title'].title()}"}})
    lines.append({"id": "markers.addChapter", "params": {"time": 0, "name": "Intro: The Golden Ticket"}})
    for s in segs:
        if s["kind"] == "sb":
            sb = P.SB[s["key"]]
            col = "Red" if sb["risk"].startswith("T3") else "Blue"
            lines.append({"id": "markers.add", "params": {"target": "program", "time": ticks(s["start"]), "name": f"Soundbite: {sb['who']}", "comment": sb["risk"], "color": col}})
    for g in gm:
        lines.append({"id": "markers.add", "params": {"target": "program", "time": ticks(g["time"]), "name": f"Gfx: {g['family']}", "comment": f"{g['pid']} {g['phrase'] or ''}", "color": "Green"}})
    jl = os.path.join(HERE, "_build.jsonl")
    open(jl, "w", encoding="utf-8").write("\n".join(json.dumps(x, ensure_ascii=False) for x in lines) + "\n")
    out = fc("run", jl, project=proj, save=True)
    bad = [ln for ln in out.splitlines() if '"ok":false' in ln]
    if bad:
        print("WARN", len(bad), "commands failed:", bad[:5])
    # second pass: clip ids from the sequence
    seq = json.loads(fc("inspect", "sequence", project=proj))
    vt = {t["name"]: t for t in seq["video"]}
    at = {t["name"]: t for t in seq["audio"]}
    tr = lambda d, pre: [t for n, t in d.items() if n.startswith(pre)][0]["items"]
    v1c, v3c, a1c, a2c, a3c = tr(vt, "V1"), tr(vt, "V3") + tr(vt, "V4"), tr(at, "A1"), tr(at, "A2"), tr(at, "A3")
    l2 = []
    stills = [c for c in v1c if str(c["name"]).lower().endswith(".png")]
    vids = [c for c in v1c if not str(c["name"]).lower().endswith(".png")]
    if PL:
        _lib, _pres, _hist, _mlog = PL.load_motion_library(), PL.load_presets(), [], []
    for k, c in enumerate(stills):
        a, b = c["start"], c["end"] - TPF
        if PL:  # motion library: emotion/intensity default to neutral/2 until a beat_map is wired in; faces assumed present
            r = PL.pick_motion(_lib, _pres, emotion="neutral", intensity=2, subject="wide", duration_s=(c["end"] - c["start"]) / TPS,
                               history=_hist, faces=True, total_stills=k)
            mv = _lib["moves"][r["move"]]
            (z0, p0), (z1, p1) = PL.rect_to_scale_pos(mv["start_rect"]), PL.rect_to_scale_pos(mv["end_rect"])
            _hist.append({"move": r["move"], "direction": r["direction"]})
            _mlog.append({"clip": str(c["name"]), "start_ticks": a, "move": r["move"], "direction": r["direction"], "reason": r["reason"]})
        else:
            z0, z1 = (100.0, 107.0) if k % 2 == 0 else (107.0, 100.0)
            dx = [(-22, 0), (22, -10), (0, -18), (-14, 12)][k % 4]
            p0, p1 = [960, 540], [960 + dx[0], 540 + dx[1]]
        for prm, v0, v1_ in (("scale", z0, z1), ("position", p0, p1)):
            l2.append({"id": "effects.setParam", "params": {"clip": c["clip"], "effect": "motion", "param": prm, "value": v0, "time": a, "keyframe": True}})
            l2.append({"id": "effects.setParam", "params": {"clip": c["clip"], "effect": "motion", "param": prm, "value": v1_, "time": b, "keyframe": True}})
    if PL:
        json.dump(_mlog, open(os.path.join(HERE, "motion_log.json"), "w", encoding="utf-8"), indent=1)
    for c in vids:
        l2.append({"id": "clip.fillFrame", "params": {"clips": [c["clip"]]}})
    # gains: VO paragraphs & soundbites to -16 LUFS, SFX trims
    gain = {}
    for s in segs:
        if s["kind"] in ("vo", "sb"):
            gain[ticks(s["start"])] = s.get("gain_db", 0.0)
    for c in a1c:
        g = gain.get(c["start"])
        if g is None:
            g = min(gain.items(), key=lambda kv: abs(kv[0] - c["start"]))[1]
        if abs(g) > 0.05:
            l2.append({"id": "clip.audioGain", "params": {"clips": [c["clip"]], "mode": "set", "db": g}})
    for c, (t, p, d, gdb) in zip(sorted(a2c, key=lambda x: x["start"]), sorted(sfx_place)):
        l2.append({"id": "clip.audioGain", "params": {"clips": [c["clip"]], "mode": "set", "db": gdb}})
    # role colours
    l2.append({"id": "edit.label", "params": {"clips": [c["clip"] for c in v1c], "label": "Forest"}})
    l2.append({"id": "edit.label", "params": {"clips": [c["clip"] for c in v3c], "label": "Mango"}})
    l2.append({"id": "edit.label", "params": {"clips": [c["clip"] for c in a2c], "label": "Rose"}})
    l2.append({"id": "edit.label", "params": {"clips": [c["clip"] for c in a3c], "label": "Violet"}})
    # transitions: short dissolves between V1 shots
    for c in v1c[1:]:
        l2.append({"id": "sequence.applyVideoTransition", "params": {"clip": c["clip"], "effect": "cross_dissolve", "frames": 10, "edge": "in", "align": "center"}})
    # grade: colour script looks when Source/color/color_assign.json exists and PASSed (COLOR_SCRIPT.md), else the house look
    ca_path = next((p for p in (os.path.join(HERE, "color", "color_assign.json"),
                                os.path.join(PROJ, "06_script_edit_plan", "color", "color_assign.json")) if os.path.exists(p)), None)
    ca = json.load(open(ca_path, encoding="utf-8")) if ca_path else None
    if not ca:
        print("NOTE no color_assign.json in Source/color or 06_script_edit_plan/color: house look on every V1 clip")
    house_clips = [c["clip"] for c in v1c]
    if ca and ca.get("verdict") == "PASS":
        groups, house_clips = color_groups(v1c, ca, ticks)
        for look, (pre, clips) in groups.items():   # same-run rule: import and apply in this one pass-2 run
            l2.append({"id": "presets.import", "params": {"path": pre.replace("\\", "/")}})
            l2.append({"id": "presets.apply", "params": {"preset": look, "clips": clips}})
        print(f"colour script: {len(groups)} looks on {sum(len(v[1]) for v in groups.values())} clips; {len(house_clips)} unmatched -> house look")
    elif ca:
        print("WARN colour script verdict is not PASS: house look used everywhere (fix color_plan.md and re-run color_script.py plan)")
    if house_clips:
        l2.append({"id": "presets.import", "params": {"path": os.path.join(PRESET, "grade", "house-style.fcpreset").replace("\\", "/")}})
        l2.append({"id": "presets.apply", "params": {"preset": "HouseStyle_Documentary", "clips": house_clips}})
    # captions
    l2.append({"id": "captions.import", "params": {"path": os.path.join(HERE, "captions.srt").replace("\\", "/"), "name": "C1 - Captions / Subtitles", "language": "en"}})
    # bins
    by_bin = {}
    for f, b in files.items():
        by_bin.setdefault(b, []).append(item[f])
    for b, its in by_bin.items():
        if bins.get(b):
            l2.append({"id": "project.moveToBin", "params": {"items": its, "bin": bins[b]}})
    if bins.get("07_Sequences"):
        l2.append({"id": "project.moveToBin", "params": {"items": [seq["id"]], "bin": bins["07_Sequences"]}})
    notes = (f"{NAME}. Narration: Voicebox 'Jessica from Ihateediting' (107 paragraph clips on A1, -16 LUFS clip gain). "
             f"23.976 fps, 1920x1080, {total / 60:.1f} min. V1 {len(v1c)} shots (Ken Burns stills + {len(vids)} sync soundbites), "
             f"V3 {len(v3c)} house graphics, A2 SFX, A3 ducked music (Kevin MacLeod CC BY 4.0). Red markers = Content ID risk soundbites. "
             "Source plan: Source/edit_plan.py; rebuild: python Source/build_full_edit.py fcproj")
    l2.append({"id": "project.setNotes", "params": {"text": notes}})
    jl2 = os.path.join(HERE, "_build2.jsonl")
    open(jl2, "w", encoding="utf-8").write("\n".join(json.dumps(x, ensure_ascii=False) for x in l2) + "\n")
    out2 = fc("run", jl2, project=proj, save=True)
    bad2 = [ln for ln in out2.splitlines() if '"ok":false' in ln]
    if bad2:
        print("WARN pass2", len(bad2), "failed; first:", bad2[:4])
    rep = {"project": proj, "total_s": total, "v1": len(v1c), "stills": len(stills), "videos": len(vids), "v3": len(v3c), "a1": len(a1c), "a2": len(a2c),
           "a3": len(a3c), "pass1_failed": len(bad), "pass2_failed": len(bad2)}
    json.dump(rep, open(os.path.join(HERE, NAME + "_build_report.json"), "w"), indent=1)
    print(json.dumps(rep))


def stage_export():
    proj = os.path.join(HERE, NAME + ".fcproj")
    exp = os.path.join(FULL, "Export"); os.makedirs(exp, exist_ok=True)
    out = os.path.join(exp, NAME + "_preview.mp4")
    fc("exec", "file.exportMedia", json.dumps({"path": out.replace("\\", "/"), "format": "h264", "loudnessLufs": -14.0, "wait": True}), project=proj)
    print("export ->", out)


if __name__ == "__main__":
    st = sys.argv[1] if len(sys.argv) > 1 else "all"
    steps = {"graphics_plan": stage_graphics_plan, "layout": stage_layout, "audio": stage_audio, "words": stage_words, "graphics": stage_graphics, "captions": stage_captions,
             "fcproj": stage_fcproj, "export": stage_export}
    if st == "all":
        for k in ("layout", "audio", "words", "graphics", "captions", "fcproj"):
            steps[k]()
    else:
        for k in st.split(","):
            steps[k]()
