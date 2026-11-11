# Transitions Skill — Editorial Decision System (Stage 06 Shot Plan & Stage 08 Assembly)

> **Skill ID:** `video_pipeline/skills/transitions` · **Applies to:** Stage 06 (shot planning), Stage 08 (assembly), Stage 10 (QA)
> **Single sources of truth:** frame counts and effect IDs live in [presets/documentary-default/transitions.md](../../presets/documentary-default/transitions.md) §2/§2c; this skill governs the *decision* of when, why, and which.

---

## 0. Prime Directive

A transition is a **grammatical claim about time, place, or point of view**. It is punctuation, not decoration. Every visible transition asserts one sentence to the viewer:

- **Hard cut** → "next thing, same here-and-now."
- **Cross dissolve** → "time passed, or these two images belong together."
- **Dip to black** → "a chapter has ended."
- **Wipe / whip** → "a deliberate, energetic shift."

If the agent cannot write that sentence for a specific cut, the answer is a **hard cut — no exceptions**. Professional edits keep **85%+ of all cuts as hard cuts (industry norm ~90%)**; the skill of a senior editor is measured by the transitions they *declined* to add.

**Murch's Rule of Six governs every edit point**, in strict priority: (1) emotion, (2) story, (3) rhythm, (4) eye-trace, (5) 2D picture continuity, (6) 3D space/time continuity. A transition that improves #5–6 while hurting #1–2 is wrong.

---

## 1. When a Visible Transition IS Needed (exhaustive list)

Apply a non-cut transition **only** when at least one of these holds:

| # | Trigger | Evidence in the material |
|---|---|---|
| N1 | **Time passage** — hours, days, years elapse between shots | Narration says "by 1938…", "three years later"; day→night still pair; montage compressing a campaign |
| N2 | **Place change** — scene moves to a new location | Narration moves from the person to the city; still plate → map → interior |
| N3 | **Chapter/act boundary** | Beat map marks an act finale; a major milestone lands; section restarts |
| N4 | **Perspective/subjectivity shift or reveal** | Entering memory, flashback, dream, or a character's inner state; entering archival/B&W material; a wipe reveal of new archival evidence, a map, or a territorial view |
| N5 | **Thematic linking** — two images form a deliberate visual rhyme | Match/graphic dissolve: same shape, motion, or composition across shots |
| N6 | **Energy change (short-form only)** | `shorts-vertical` preset: attention reset, topic signal, or energy maintenance between sections |

**Gate question:** can the agent name N1–N6 in one sentence, citing the actual narration text or beat-map beat ID? If not → hard cut.

## 2. When NOT to Use a Transition (hard prohibitions)

1. **Between two takes/shots of the same subject in near-identical framing.** A dissolve there claims time passed when nothing changed — the viewer sees the lie. Fix: hard cut, cutaway, or reframe (≥30° / a clear size change).
2. **Inside continuous action.** A hand reaching, a door opening, a person walking — never interrupt continuous motion with a dissolve or wipe.
3. **Inside a continuous dialogue scene** with no time/place change.
4. **To cover a bad cut.** A dissolve over a bad cut is a slow bad cut. Fix the cut: cutaway, reframe, different take, or a sound bridge — never an effect.
5. **Between two shots of the same moment** (e.g., two interview angles) — dissolves falsely imply elapsed time.
6. **On rapid sequences.** Fast montage chains (>1 cut per 2 s) carry their own energy; any transition slows every join and kills the pace.
7. **When the only reason is "the edit felt boring," "more dynamic," or "it's trendy."** These are the signature tells of amateur work. Transitions are background actors, never stars.
8. **No ornamental style mixing.** The preset's functional vocabulary is grammar, not style, and is always allowed where its trigger applies: `cross_dissolve` (scene), `dip_to_black_legacy` (act), `film_dissolve_legacy` (archival memory), `non_additive_dissolve` (documents), `wipe` (evidence reveal), `whip_legacy` (urgent leap). What is forbidden: any decorative effect *outside* that vocabulary, using a vocabulary effect where its trigger does not apply, and a different effect on every cut — the viewer can no longer learn what a transition means.

**Anti-patterns (never ship):** glitch/strobe packs, page peels, ripple/twirl/cube/zoom-pack effects, light-leak/film-burn overlays not in the preset vocabulary, and any transition style that appears exactly once in the video (the "lone flourish" draws disproportionate attention).

## 3. Which Transition to Use (decision table)

Resolve top-down — the specific narrative triggers first; the generic J/L row and the default hard-cut row are the last matches:

| Situation | Use | FilmCraft ID (`applyVideoTransition`) | Timing (from transitions.md §2c) | Paired audio (canonical SFX file) | Cap (transitions.md §2) |
|---|---|---|---|---|---|
| N1/N2 time or place shift (scene level) | **Cross dissolve** | `cross_dissolve` | 12 f @ 23.976 (0.50 s) | Ambient crossfade / room tone | ≤1 / 60 s |
| N3 act/chapter boundary | **Dip to black** | `dip_to_black_legacy` | 24 f (1.0 s) | Sub boom (`sfx_sub_boom.wav`) | ≤1 / 300 s, act only |
| N4 memory/flashback/archival entry | **Film dissolve** | `film_dissolve_legacy` | 16 f (0.667 s) | Film reel/shutter texture | ≤1 / 180 s |
| N5 thematic visual rhyme on stills/documents | **Non-additive dissolve** | `non_additive_dissolve` | 12 f (0.50 s) | Paper slide (`sfx_paper_slide.wav`) | ≤1 / 120 s |
| N4 reveal of archival evidence / map / territorial view | **Wipe (feathered 30)** | `wipe` | 12 f (0.50 s) | Soft whoosh (`sfx_whoosh_soft.wav`) | ≤1 / 120 s |
| N1 fast temporal leap / montage pacing shift | **Whip** | `whip_legacy` | 10 f (0.417 s) | Quick whoosh (`sfx_whoosh_fast.wav`) | ≤1 / 180 s |
| N6 short-form energy shift | **Whip *or* wipe** (see selection logic below) | `whip_legacy` / `wipe` | whip 10 f, wipe 12 f | Whoosh starting before the cut, peak at it | per-effect caps above |
| Interview/VO bridging any two beats (no stronger trigger above) | **J-cut / L-cut (split edit)** | *(none — audio track split)* | Audio lead 8–18 frames | Dialogue/VO carries the cut | ≤2 / 60 s |
| Default; nothing above applies | **Hard cut** | *(none)* | 0 frames | Room tone continuity | Unlimited |

**Selection sub-rules:**
- **Whip vs wipe (deterministic):** use `whip_legacy` when the join is a **temporal** leap or energy reset and both sides carry directional motion the whip can match (motion in the same screen direction); use `wipe` when the join is a **spatial/evidentiary** reveal — the incoming shot uncovers a new place, map, territory, or piece of archival evidence. If neither condition holds, hard cut.
- **Duration discipline:** most transitions ≤0.5 s; 1.0 s (act dip only) is the ceiling and must be a deliberate, repeated style choice, not a one-off.
- **Motion rule:** never dissolve from a moving shot to a static one or vice versa; let movement resolve before a static frame.
- **Direction rule:** whip/wipe must match screen direction — outgoing motion left→right, incoming enters on the same axis.
- **Handles rule:** a centered transition consumes handle frames on both sides. If either clip lacks handles (trimmed stills, hard-out archival), use a hard cut or move the transition to the available edge. Never freeze-frame to fake a handle.
- **Audio-first rule:** prefer solving the join in audio (J/L-cut, room tone, music beat) *before* reaching for a picture effect. Use sound to soften a cut before reaching for a dissolve.

## 4. How Professionals Make a Good Transition (craft tips)

1. **Motivate inside the scene.** Four motivations, in power order: story (new info the viewer needs *now*), movement (action begun invites completion), sound (off-screen sound pulls the eye), look (eyeline leads the cut).
2. **Cut on action, not after it.** Cut mid-gesture, mid-turn, mid-footstep; the viewer's eye follows the movement and skips over the edit.
3. **Audio leads the picture.** The whoosh starts 3–8 frames before the cut and peaks at it; impacts land on the first frame of the new shot; risers resolve on the cut, never after it.
4. **Time picture changes to the music/SFX waveform**, not to arbitrary frames. A music hit and a visual change landing 3 frames apart reads as sloppiness.
5. **Respect eye-trace.** Place the next shot's focal point near where the viewer's eye already sits (or deliberately re-anchor it with motion — nothing in between).
6. **Vary rhythm.** Same-length shots feel mechanical; vary shot length for emphasis and breathing, and let transitions breathe with the score instead of decorating every boundary.
7. **One vocabulary, repeated.** The same transition shape at every chapter boundary becomes the video's identity; a random one-off becomes noise.
8. **Protect legibility.** No transition may swallow a face, text card, or document mid-effect; shorten or realign so key frames stay readable.
9. **Never review a transition in a loop.** Play at normal speed with at least several shots of context before and after, on the target device (phone check for shorts).

## 5. Machine-Executable Decision Procedure (Stage 06 / Stage 08 agents)

For each edit point, run the steps in order. Every step either passes (continue to the next step) or hits a `FAIL` line that names the outcome and ends the run. STEP 7 is always the last step executed.

```
STEP 1  MOTIVATION   Name N1–N6 (§1) in one sentence citing narration/beat ID.
        FOUND    -> STEP 2.
        NOT FOUND -> STEP 4 (audio-bridge test; a plain beat join may still
                    earn a J/L-cut). If STEP 4 also fails -> HARD CUT. Done.
STEP 2  PROHIBITION  Check ALL of §2.1–2.8 clear AND the chosen cut matches
                     no Anti-pattern (§2 anti-patterns block).
        FAIL -> HARD CUT. Done.
STEP 3  CAPS         Check ALL caps from the §3 table:
                     cross_dissolve ≤1/60s · dip_to_black ≤1/300s (act only)
                     wipe ≤1/120s · whip ≤1/180s · film_dissolve ≤1/180s
                     non_additive ≤1/120s · J/L ≤2/60s
                     TOTAL dynamic transitions ≤1 per 60 s runtime AND
                     ≤10 per 10 min per video.
        FAIL -> HARD CUT (or defer to next eligible boundary).
STEP 4  AUDIO BRIDGE Reached from STEP 1 (no N-trigger): can this plain
                     same-scene beat join be carried by audio alone — next
                     narration/dialogue/ambience led 8–18 f early (J/L-cut)
                     or a room-tone bridge, with no time/place/act change?
        YES -> J/L-CUT (verify the J/L cap ≤2/60s from the §3 table;
               if exceeded -> HARD CUT). Go to STEP 7 and record it.
        NO  -> HARD CUT. Done.
        (Reached from STEP 3 with an N-trigger standing: keep the audio
        lead paired with the effect and go to STEP 5.)
STEP 5  SELECT       Pick from §3 table by situation, top-down; on the N6
                     row apply the whip-vs-wipe selection logic in §3.
                     Record the effect ID EXACTLY as in the table
                     (no invented IDs).
STEP 6  TECHNICAL    Handles exist on both sides? Motion/duration/direction
                     sub-rules (§3) pass?
        FAIL -> HARD CUT (log the why in edit_report.md).
STEP 7  RECORD       Log: beat ID, effect, frames, SFX file, motivation
                     sentence in shot_plan.json / edit_report.md.
```

**QA verification order (Stage 10 / cut_audit extension):**
1. Mute test — every transition noticeable without sound is suspect.
2. Delete test — strip all visible transitions; if nothing is lost, they were decoration.
3. Failure triage (per Sparki classes): editorial (meaning unclear) → rebuild the relationship; rhythmic (drags) → retime; spatial (jumps) → reframe/match motion; technical (frozen frames) → check handles; audio (click/collision) → edit audio separately; hierarchy (uniform intensity) → restore cuts; legibility → shorten.
4. Full-sequence style-consistency pass at normal speed on the export device.

## 6. Format Variants

- **`documentary-default` (long-form):** hard-cut-first, dissolve as scene grammar, dip-to-black as act grammar. All caps and frame counts from transitions.md §2c. Restraint is the house style.
- **`shorts-vertical` (short-form):** transitions may *add* energy (N6): whip pans, zoom punches, match cuts on motion are acceptable per-section tools. A "zoom punch" here means a **hard-cut punch-in reframe (115–130% scale on the cut)** — never an optical zoom-transition plugin, which is banned by §2's anti-patterns. Still: matched motion direction, SFX peak at the cut, one style family per video, and a hard cut when content on both sides is already strong (abruptness itself re-engages attention).

## 7. Fallbacks

| Failure | Fallback |
|---|---|
| Effect unavailable in FilmCraft CLI | Hard cut + audio J-cut (default fallback per transitions.md §1) |
| Missing handles on archival stills | Hard cut, or move transition to the clip's available edge |
| SFX asset missing | Room-tone crossfade only; never drop the transition's audio pairing silently — log in BYPASS_LOG.md |
| Cap conflict (two eligible boundaries in one minute) | Keep the transition at the narratively stronger boundary; hard cut the other |

---

*Research basis: 22 professional sources (FILMPAC, Adobe, MasterClass, NYFA, Storyblocks, StudioBinder, insideeditors, Sparki, Lumira, Zella, MediaScaleUp, MotionVFX, Vimeo, Domer, Wreltik and others), reconciled 2026-11-09 with this preset's existing vocabulary, caps and frame-count single source.*
