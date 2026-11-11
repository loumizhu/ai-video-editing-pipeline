"""Shared library for the pacing / still-hold / enrichment tools (revision 2026-11-09).

Used by still_hold_qa.py, asset_audit.py, variation_report.py and (optionally) the NLE builders.
Standard: ../PACING_AND_ENRICHMENT.md. Numbers live in ../presets/pacing/*.json, never here.

Two input styles are normalised to one list of `Clip` objects:
  * shot_plan.json         (stage 06: {"slots": [...]} or a bare list; start_ms/end_ms per slot)
  * beats.json + assignments.json (+ optional beat_map.json)   (narrated beat builds, make_beats.py)

Execution flow of a QA tool: load_clips_*() -> build_runs() -> run_limits() -> compare -> report.
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

HERE = os.path.dirname(os.path.abspath(__file__))
PACING_DIR = os.path.normpath(os.path.join(HERE, "..", "presets", "pacing"))

VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
PLATE_KINDS = {"plate", "graphic", "graphics", "card", "chapter"}


# ----------------------------------------------------------------------------- data files
def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def load_presets(path: str | None = None) -> dict:
    return load_json(path or os.path.join(PACING_DIR, "pacing_presets.json"))


def load_motion_library(path: str | None = None) -> dict:
    return load_json(path or os.path.join(PACING_DIR, "motion_library.json"))


def load_catalog(path: str | None = None) -> dict:
    return load_json(path or os.path.join(PACING_DIR, "enrichment_catalog.json"))


# ----------------------------------------------------------------------------- model
@dataclass
class Event:
    t: float                      # absolute timeline seconds
    type: str
    inferred: bool = False        # True when the plan gave no time and we assumed the clip start


@dataclass
class Clip:
    id: str
    kind: str                     # 'still' | 'video' | 'plate'
    asset: str | None
    start: float
    end: float
    group: str | None = None
    motion: str | None = None     # move id (push_slow...) or preset id (mot.push_in)
    motion_at: float | None = None
    events: list[Event] = field(default_factory=list)
    emotion: str | None = None
    intensity: int | None = None
    priority: int | None = None
    preset: str | None = None
    reading: bool = False         # document / text still the viewer must read
    transition_in: str | None = None
    sfx: list[str] = field(default_factory=list)
    rationale: str | None = None
    subject: str | None = None
    anchor_phrase: str | None = None
    major: bool = False
    asset_raw: str | None = None   # asset string exactly as written in the plan (for resolving against --assets-root)
    plate_type: str | None = None  # for plates: map | article_card | quote_card | stat_plate | narration_plate | ...
    flags: list[str] = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    @property
    def dur(self) -> float:
        return self.end - self.start


def norm_asset(a: Any) -> str | None:
    if a is None or a == "":
        return None
    s = str(a)
    if ":" in s and not os.path.isabs(s) and not s[1:3] == ":\\":
        return s  # provider ref such as pexels:3129957 / owner:img_01
    return os.path.normcase(os.path.abspath(s)) if (os.path.isabs(s) or "/" in s or "\\" in s) else os.path.normcase(s)


IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def _kind_from(visual_type: str | None, media_type: str | None, asset: str | None) -> tuple[str, list[str]]:
    """Return (kind, flags). A picture file can never be declared 'video' to dodge the still caps; graphics PNGs may be plates."""
    mt = (media_type or "").lower()
    vt = (visual_type or "").lower()
    ext = os.path.splitext(asset.split("?")[0])[1].lower() if asset else ""
    if mt in PLATE_KINDS or (not mt and vt in PLATE_KINDS):
        return "plate", []
    if mt in ("video", "footage", "clip"):
        if ext in IMAGE_EXT:
            return "still", ["media_type_mismatch"]  # declared video, file is a picture
        return "video", []
    if mt in ("image", "still", "photo"):
        return "still", []  # includes a still pre-rendered to a clip (stage 07 'still slot' MP4)
    if ext in VIDEO_EXT:
        return "video", []
    return "still", []  # conservative: unknown media is treated as a still


# ----------------------------------------------------------------------------- event helpers
LEGACY_EXTRA_TYPE = {
    "date_strip": "date_strip", "stamp": "stamp", "big_number": "stat_counter", "spotlight": "spotlight",
    "keyword_pop": "keyword_pop", "soundbite_card": "kinetic_quote", "split_screen": "split_screen",
    "photo_stack": "photo_stack", "chapter_title": "chapter_card",
}
PRESET_EVENT_MOTION = {"mot.zoom_punch": "punch_in", "mot.focus_pull": "rack_focus", "mot.magnifier": "detail_crop"}


def _ev_time(e: dict, clip_start: float) -> tuple[float, bool]:
    if "at_ms" in e:
        return e["at_ms"] / 1000.0, False
    if "t_s" in e:
        return float(e["t_s"]), False
    if "at" in e:
        return float(e["at"]), False
    if "offset_ms" in e:
        return clip_start + e["offset_ms"] / 1000.0, False
    if "offset_s" in e or "off" in e:
        return clip_start + float(e.get("offset_s", e.get("off"))), False
    return clip_start, True


def _events_from(rows: Iterable[dict] | None, clip_start: float) -> list[Event]:
    out: list[Event] = []
    for e in rows or []:
        t, inferred = _ev_time(e, clip_start)
        out.append(Event(t=t, type=str(e.get("type", "unknown")), inferred=inferred))
    return out


# ----------------------------------------------------------------------------- loaders
def _beat_map_index(beat_map_path: str | None) -> dict[str, dict]:
    if not beat_map_path:
        return {}
    raw = load_json(beat_map_path)
    rows = raw.get("beats", raw) if isinstance(raw, dict) else raw
    return {r["beat"] if "beat" in r else r["id"]: r for r in rows}


def _plate_type(s: dict) -> str | None:
    if s.get("plate_type"):
        return str(s["plate_type"])
    if s.get("map"):
        return "map"
    if s.get("article"):
        return "article_card"
    for x in s.get("extras") or []:
        t = x.get("type")
        if t in ("photo_stack", "split_screen", "chapter_title", "big_number", "soundbite_card"):
            return {"chapter_title": "chapter_card", "big_number": "stat_plate", "soundbite_card": "quote_card"}.get(t, t)
    for e in s.get("enrichments") or []:
        if str(e.get("type")) in ("map", "article_card", "quote_card", "then_now", "split_screen", "photo_stack", "stat_plate", "narration_plate"):
            return str(e["type"])
    return None


def load_clips_shot_plan(path: str, beat_map_path: str | None = None) -> list[Clip]:
    d = load_json(path)
    slots = d.get("slots", d) if isinstance(d, dict) else d
    bm = _beat_map_index(beat_map_path)
    clips: list[Clip] = []
    for i, s in enumerate(slots):
        if isinstance(s.get("pipeline_ext"), dict):  # Vcut section 3.3 nesting: ext fields override
            s = {**s, **s["pipeline_ext"]}
        bmeta = bm.get(str(s.get("beat_id", s.get("beat_ref", ""))), {})
        if "start_ms" in s:
            a, b = s["start_ms"] / 1000.0, s["end_ms"] / 1000.0
        elif "start_s" in s:
            a, b = float(s["start_s"]), float(s["end_s"])
        else:
            continue
        asset_raw = s.get("selected_asset") or s.get("chosen")
        asset = norm_asset(asset_raw)
        kind, kflags = _kind_from(s.get("visual_type"), s.get("media_type"), str(asset_raw) if asset_raw else None)
        mot = s.get("motion")
        motion = mot.get("move") or mot.get("preset") if isinstance(mot, dict) else mot
        motion_at = (mot.get("at_ms") / 1000.0) if isinstance(mot, dict) and "at_ms" in mot else None
        beat = {**bmeta, **(s.get("beat") or {})}
        ev = _events_from(s.get("enrichments"), a)
        # legacy toolkit fields count as events on a non-plate slot
        if kind != "plate":
            if s.get("callout"):
                ev.append(Event(a + 0.3, "lower_third", True))
            mp = s.get("map")
            if mp:
                ev.append(Event(a + 0.3, "map_overlay" if mp.get("alpha_overlay") else "map", True))
            art = s.get("article")
            if art:
                ev.append(Event(a + 0.5, "article_highlight", True))
            for x in s.get("extras") or []:
                t = LEGACY_EXTRA_TYPE.get(x.get("type"))
                if t and t not in ("chapter_card", "photo_stack", "split_screen", "texture_bed"):
                    tt, inf = _ev_time(x, a)
                    ev.append(Event(tt, t, inf))
        tr = s.get("transitions") or s.get("transition_in")
        if isinstance(tr, list):
            tr = tr[0].get("type") if tr else None
        elif isinstance(tr, dict):
            tr = tr.get("type")
        sfx = s.get("sfx") or []
        if isinstance(sfx, str):
            sfx = [sfx]
        clips.append(Clip(
            id=str(s.get("slot_id", f"slot{i}")), kind=kind, asset=asset, start=a, end=b,
            group=s.get("asset_group"), motion=motion, motion_at=motion_at, events=ev,
            emotion=beat.get("emotion", s.get("emotion")), intensity=beat.get("intensity", s.get("intensity")),
            priority=beat.get("priority", s.get("priority")), preset=s.get("preset"),
            asset_raw=str(asset_raw) if asset_raw else None, plate_type=_plate_type(s) if kind == "plate" else None, flags=kflags,
            reading=bool(s.get("reading")), transition_in=tr, sfx=[str(x if isinstance(x, str) else x.get("file", x.get("id", x))) for x in sfx],
            rationale=s.get("rationale"), subject=s.get("subject"),
            anchor_phrase=s.get("anchor_phrase") or bmeta.get("anchor_phrase"), major=bool(s.get("major")), raw=s))
    clips.sort(key=lambda c: c.start)
    return clips


def load_clips_beats(beats_path: str, assign_path: str, beat_map_path: str | None = None) -> list[Clip]:
    beats = {b["id"]: b for b in load_json(beats_path)}
    asg = load_json(assign_path)
    bm: dict[str, dict] = {}
    if beat_map_path:
        raw = load_json(beat_map_path)
        rows = raw.get("beats", raw) if isinstance(raw, dict) else raw
        bm = {r["beat"] if "beat" in r else r["id"]: r for r in rows}
    clips: list[Clip] = []
    for x in asg:
        b = beats.get(x.get("beat"))
        if not b or b.get("locked"):
            continue
        meta = bm.get(b["id"], {})
        parts = [{"file": x.get("file"), "kind": x.get("kind"), "off": 0.0, "motion": x.get("motion"), "group": x.get("group")}]
        for sub in x.get("sub") or []:
            parts.append({"file": sub.get("file"), "kind": sub.get("kind"), "off": float(sub.get("off", sub.get("start_off", 0))),
                          "motion": sub.get("motion") or x.get("motion_sub"), "group": sub.get("group")})
        parts.sort(key=lambda p: p["off"])
        for k, p in enumerate(parts):
            a = b["start"] + p["off"]
            e = b["start"] + parts[k + 1]["off"] if k + 1 < len(parts) else b["end"]
            asset = norm_asset(p["file"])
            kind, kflags = _kind_from(None, p["kind"], str(p["file"]) if p["file"] else None)
            ev: list[Event] = []
            for r in (x.get("events") or x.get("enrich") or []):
                t, inf = _ev_time(r, b["start"])
                if a - 1e-6 <= t <= e + 1e-6:
                    ev.append(Event(t, str(r.get("type", "unknown")), inf))
            mot = p["motion"]
            motion = mot.get("move") or mot.get("preset") if isinstance(mot, dict) else mot
            clips.append(Clip(
                id=b["id"] if len(parts) == 1 else f"{b['id']}.{k + 1}", kind=kind, asset=asset, start=a, end=e,
                group=p["group"], motion=motion, events=ev, asset_raw=str(p["file"]) if p["file"] else None, flags=kflags,
                plate_type=x.get("plate_type") if kind == "plate" else None,
                emotion=meta.get("emotion"), intensity=meta.get("intensity"), priority=meta.get("priority"),
                preset=x.get("preset") or meta.get("preset"), reading=bool(x.get("reading")),
                transition_in=x.get("transition_in"), sfx=list(x.get("sfx") or []), rationale=x.get("rationale"),
                subject=x.get("subject"), anchor_phrase=meta.get("anchor_phrase"), major=bool(x.get("major")), raw=x))
    clips.sort(key=lambda c: c.start)
    return clips


# ----------------------------------------------------------------------------- runs
@dataclass
class Run:
    clips: list[Clip]
    events: list[Event]
    start: float
    end: float
    warnings: list[str] = field(default_factory=list)

    @property
    def dur(self) -> float:
        return self.end - self.start

    @property
    def assets(self) -> list[str]:
        out: list[str] = []
        for c in self.clips:
            if c.asset and c.asset not in out:
                out.append(c.asset)
        return out


def _resolve_move(motion: str | None, lib: dict) -> str | None:
    if not motion:
        return None
    moves = lib["moves"]
    if motion in moves:
        return motion
    if motion in PRESET_EVENT_MOTION:
        return PRESET_EVENT_MOTION[motion]
    return None


def motion_event_type(motion: str | None, lib: dict) -> str | None:
    """Return the enrichment type a motion produces (detail_crop, reveal, punch_in, rack_focus) or None."""
    m = _resolve_move(motion, lib)
    if m and lib["moves"].get(m, {}).get("counts_as_event"):
        return m
    return None


def _area(r: list[float]) -> float:
    return r[2] * r[3]


def recompose_ok(c: Clip, mt: str, min_change: float) -> tuple[bool, str]:
    """detail_crop / reveal only count when they really re-frame: area change >= min_change (default 0.35)."""
    if mt not in ("detail_crop", "reveal"):
        return True, ""
    mot = c.raw.get("motion") if isinstance(c.raw.get("motion"), dict) else {}
    tr = mot.get("target_rect") or c.raw.get("target_rect")
    if isinstance(tr, list) and len(tr) == 4:
        change = 1.0 - _area(tr)
        return change >= min_change, f"target_rect covers {_area(tr):.0%} of the frame (needs <= {1 - min_change:.0%})"
    sr, er = mot.get("start_rect"), mot.get("end_rect")
    if isinstance(sr, list) and isinstance(er, list) and len(sr) == 4 and len(er) == 4:
        change = abs(1.0 - _area(er) / max(1e-6, _area(sr)))
        return change >= min_change, f"start/end rect area changes only {change:.0%} (needs >= {min_change:.0%})"
    return False, "no target_rect (or start/end rect) given, so the re-frame cannot be verified"


def build_runs(clips: list[Clip], lib: dict | None = None,
               similar: Callable[[str, str], bool] | None = None, max_gap_s: float = 0.25,
               min_break_s: float = 1.0, min_change: float | None = None) -> list[Run]:
    """Group consecutive stills of the same idea into runs.

    A video clip or plate of at least `min_break_s` ends the run, as does a distinct still. A shorter video/plate
    (a dummy 0.1 s card) is ignored, so it cannot be used to reset the still budget.
    """
    lib = lib or load_motion_library()
    if min_change is None:
        min_change = load_presets()["still_policy"]["recompose_min_area_change"]
    runs: list[Run] = []
    cur: list[Clip] = []
    last_end = 0.0

    def same_idea(a: Clip, b: Clip) -> bool:
        if a.asset and a.asset == b.asset:
            return True
        if a.group and a.group == b.group:
            return True
        return bool(similar and a.asset and b.asset and similar(a.asset, b.asset))

    def close() -> None:
        nonlocal cur
        if cur:
            start, end = cur[0].start, cur[-1].end
            evs: list[Event] = []
            warns: list[str] = []
            for c in cur:
                for e in c.events:
                    if start - 1e-6 <= e.t <= end + 1e-6:
                        evs.append(e)
                mt = motion_event_type(c.motion, lib)
                if mt:
                    ok, why = recompose_ok(c, mt, min_change)
                    if ok:
                        ev_at = lib["moves"].get(_resolve_move(c.motion, lib) or "", {}).get("event_at", 0.5)
                        t = c.motion_at if c.motion_at is not None else (c.start + (ev_at if isinstance(ev_at, (int, float)) else 0.5) * c.dur)
                        evs.append(Event(t, mt))
                    else:
                        warns.append(f"{c.id}: '{mt}' does not count as an event: {why}")
            runs.append(Run(cur, sorted(evs, key=lambda e: e.t), start, end, warns))
            cur = []

    for c in clips:
        if c.kind != "still":
            if cur and c.dur < min_break_s:
                last_end = max(last_end, c.end)
                continue
            close()
            continue
        if cur and (c.start - max(cur[-1].end, last_end) > max_gap_s or not same_idea(cur[-1], c)):
            close()
        cur.append(c)
        last_end = c.end
    close()
    return runs


# ----------------------------------------------------------------------------- limits
def preset_for(name: str | None, presets: dict) -> tuple[str, dict]:
    n = name or presets["default_preset"]
    if n not in presets["presets"]:
        n = presets["default_preset"]
    return n, presets["presets"][n]


def run_limits(run: Run, presets: dict, default_preset: str | None = None) -> dict:
    name, cfg = preset_for(run.clips[0].preset or default_preset, presets)
    inten = max([c.intensity for c in run.clips if c.intensity] or [3])
    scale = presets["intensity_scale"].get(str(int(inten)), {"cap_scale": 1.0})["cap_scale"]
    fl = cfg.get("cap_floor", {"soft": 0, "hard": 0, "gap": 0})
    soft = min(cfg["still_soft_max_s"], max(fl["soft"], cfg["still_soft_max_s"] * scale))   # intensity tightens, never below the floor
    hard = min(cfg["still_hard_max_s"], max(fl["hard"], cfg["still_hard_max_s"] * scale))
    gap = min(cfg["enrich_gap_s"], max(fl["gap"], cfg["enrich_gap_s"] * scale))
    if any(c.reading for c in run.clips):
        soft, hard = soft + 1.0, hard + 1.0
    hard = min(hard, presets["still_policy"]["absolute_hard_max_s"])
    return {"preset": name, "intensity": int(inten), "soft": round(soft, 3), "hard": round(hard, 3), "gap": round(gap, 3)}


def longest_gap(run: Run, counting: set[str]) -> tuple[float, float]:
    """Longest event-free interval inside the run (run edges count as boundaries) and its midpoint."""
    pts = sorted([run.start, run.end] + [e.t for e in run.events if e.type in counting])
    best, mid = 0.0, run.start
    for a, b in zip(pts, pts[1:]):
        if b - a > best:
            best, mid = b - a, (a + b) / 2
    return best, mid


def counting_types(cat: dict, lib: dict) -> set[str]:
    s = {k for k, v in cat["types"].items() if v.get("counts_as_event")}
    s |= {k for k, v in lib["moves"].items() if v.get("counts_as_event")}
    return s


def needed_distinct_assets(dur: float, soft: float) -> int:
    return max(1, math.ceil(dur / soft))


# ----------------------------------------------------------------------------- motion geometry
def rect_to_scale_pos(rect: list[float], width: int = 1920, height: int = 1080) -> tuple[float, list[float]]:
    """Normalized visible-window rect -> (scale %, [pos_x, pos_y]) for FilmCraft motion keyframes (centre = [W/2, H/2])."""
    x, y, w, h = rect
    s = 1.0 / max(w, h)
    cx, cy = x + w / 2.0, y + h / 2.0
    return round(100.0 * s, 3), [round(width / 2 - (cx - 0.5) * width * s, 2), round(height / 2 - (cy - 0.5) * height * s, 2)]


def rect_area(rect: list[float]) -> float:
    return rect[2] * rect[3]


# ----------------------------------------------------------------------------- motion picker
def pick_motion(lib: dict, presets: dict, *, preset: str | None = None, emotion: str = "neutral", intensity: int = 3,
                subject: str = "wide", duration_s: float = 4.0, history: list[dict] | None = None,
                has_target: bool = False, faces: bool = False, aspect: float = 1.5, allow_optional: bool = False,
                total_stills: int = 0) -> dict:
    """Choose a motion move deterministically. history = [{'move','direction'}, ...] oldest first.

    Returns {'move','reason','candidates'}. Hard filters first (emotion avoid-list, preset intensity band, subject, faces,
    requirements, cooldown, share cap), then a score: emotion preference order, intensity fit, direction change, recency.
    """
    history = history or []
    rules = lib["selection_rules"]
    pname, pcfg = preset_for(preset, presets)
    emo = presets["emotions"].get(emotion, presets["emotions"]["neutral"])
    lo, hi = pcfg["motion_intensity"]
    recent = [h["move"] for h in history[-rules["cooldown_slots"]:]]
    last_dir = history[-1]["direction"] if history else None
    counts: dict[str, int] = {}
    for h in history:
        counts[h["move"]] = counts.get(h["move"], 0) + 1
    cands = []
    for mid, m in lib["moves"].items():
        if m.get("optional") and not allow_optional:
            continue
        if mid in emo.get("avoid_motions", []):
            continue
        if not (lo <= m["intensity"] <= hi) and mid not in ("push_slow",):
            continue
        if m["intensity"] > max(intensity, lo) + 1:
            continue
        if subject not in m["subjects"]:
            continue
        if faces and not m["faces_safe"]:
            continue
        if m.get("requires") and "target_rect" in m["requires"] and not has_target:
            continue
        if mid == "pan_wide" and aspect < 1.9:
            continue
        if mid in recent:
            continue
        if total_stills >= 10 and counts.get(mid, 0) / max(1, total_stills) >= rules["max_share_of_stills"]:
            continue
        if duration_s < 2.0 and m["intensity"] > 3:
            continue
        pref = emo["motions"]
        score = (5 - pref.index(mid)) if mid in pref else 0
        score += 2 - abs(m["intensity"] - intensity) * 0.5
        if rules["no_same_direction_twice"] and last_dir and m["direction"] == last_dir and last_dir in ("left", "right"):
            score -= 4
        elif last_dir and m["direction"] == last_dir:
            score -= 1
        score -= counts.get(mid, 0) * 0.25
        cands.append((score, mid))
    if not cands:  # relax: ignore cooldown and share, keep safety filters
        for mid, m in lib["moves"].items():
            if (not m.get("optional") and (not faces or m["faces_safe"]) and subject in m["subjects"]
                    and "target_rect" not in (m.get("requires") or "") and mid not in emo.get("avoid_motions", [])
                    and not (mid == "pan_wide" and aspect < 1.9)):
                cands.append((0, mid))
    cands.sort(key=lambda t: (-t[0], t[1]))
    move = cands[0][1] if cands else "push_slow"
    return {"move": move, "direction": lib["moves"][move]["direction"], "reason": f"{emotion}/{intensity} {subject} {duration_s:.1f}s preset={pname}",
            "candidates": [m for _, m in cands[:4]]}


# ----------------------------------------------------------------------------- misc
def tc(seconds: float) -> str:
    h, r = divmod(int(seconds), 3600)
    m, s = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s:02d}.{int(round((seconds - int(seconds)) * 1000)):03d}"


def write_report(json_path: str | None, md_path: str | None, payload: dict, md: str) -> None:
    if json_path:
        os.makedirs(os.path.dirname(os.path.abspath(json_path)), exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    if md_path:
        os.makedirs(os.path.dirname(os.path.abspath(md_path)), exist_ok=True)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)
