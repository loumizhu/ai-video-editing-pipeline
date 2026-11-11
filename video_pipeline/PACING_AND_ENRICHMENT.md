# Pacing, Still-Hold & Enrichment Standard

**Revision 2026-11-09.** Single authority for: how long a still image may stay on screen, how a still is made to *follow the narration*, beat emotion analysis, pacing presets, the motion library, variation tracking, the asset audit, the edit report and the style-memory feedback loop.

> **Supersedes** (these older numbers are wrong or too loose): Toolkit §4.1 "never hold an unmoving frame > 4.5 s" (unenforced); `video-editor` SKILL §9.5 "no still holds longer than ~10 s" and §10.2 "stills <= 8 s"; Vcut 03b "maximum hold 4-8 s". Where this file and another disagree on pacing, this file wins.
> **Numbers live in JSON, not prose:** [pacing_presets.json](presets/pacing/pacing_presets.json) · [motion_library.json](presets/pacing/motion_library.json) · [enrichment_catalog.json](presets/pacing/enrichment_catalog.json). The tools read those files. Change a number there and only there.

---

## 0. The card (what an agent must remember)

| Rule | documentary_standard (default) | slow_reflective | tense_fast | shorts_vertical |
|---|---|---|---|---|
| Target shot | 3.5-4.5 s | 4.5-6.5 s | 2.0-3.5 s | 1.5-3.0 s |
| **Soft cap** (past it a still needs enrichment events) | **4.5 s** | 6.5 s | 3.5 s | 3.0 s |
| **Hard cap** (never exceeded, QA FAIL) | **6.0 s** | 8.0 s | 4.5 s | 4.0 s |
| Longest event-free stretch inside a long still | 3.5 s | 4.5 s | 2.5 s | 2.0 s |
| Reading plate (document / quote still) | +1.0 s on both caps (the 8.0 s ceiling still clamps) | same | same | same |
| Intensity 4 / 5 beats | caps x 0.85 / x 0.70, never below the preset floor (doc: 3.0 / 4.0 / 2.4 s; tense: 2.5 / 3.2 / 1.8 s) | | | |
| Absolute ceiling, any preset | 8.0 s | | | |

**A 12-second still is never valid.** The only way to have 12 seconds of narration over one subject is several *different* shots about it.

---

## 1. Why stills drag (root cause, found in the code)

| # | Cause | Where | Effect |
|---|---|---|---|
| 1 | Shot count is `min(images available, span / 2.6 s)`. One image for a 12 s paragraph = one 12 s shot. | `build_full_edit.py visual_plan()` (still true: the builder cannot invent pictures; since 2026-11-09 it reports every hold over the cap in `still_hold_warnings.json` and the QA gate fails it) | The hold length depended on research luck, not on a rule. |
| 2 | "Same idea" stills were *merged* into one longer shot (owner rule: never two pictures of the same idea back to back). | same | Merging **extended** the hold with no limit. |
| 3 | The caps (`~10 s`, `<= 8 s`) were far above the 3.5-4.5 s cadence and were checked **per beat**, not per picture. | SKILL §9.5 / §10.2, `beats_qa.py` | A picture could pass while sitting through two beats. |
| 4 | The only cure applied to a still was a Ken Burns zoom. A zoom is motion, **not information**. | all builders | The image keeps saying the same thing for 12 s. |
| 5 | Nothing connected *what the narration says* to *what appears on screen*. | stage 06 | Stills stayed generic while the line named a person, a number, a date, a document. |

The fix has five parts: **cap it** (section 2), **enrich it** (3), **know the line** (4), **vary the rhythm** (5-7), **verify it by code** (8-9).

---

## 2. The Still-Hold Budget

### 2.1 Definitions
- **Still run:** the uninterrupted on-screen time of one still, **or of several stills of the same `asset_group` / near-duplicate pictures**. A run ends only at a **distinct shot**: different picture, footage, or a full-frame plate (map, card, quote...). Ken Burns, crop changes, dissolves and overlays do **not** reset it.
- **Enrichment event:** a change the viewer can *see*, that the narration *motivates*, anchored to a spoken word (`at_ms`). Tier A (in-frame camera: detail crop, reveal, punch-in, focus pull) and tier B (overlay: annotation, keyword, stat, stamp, lower third...) count. Tier C/D (plates, cutaways) end the run instead. **Audio-only events (SFX, music swell) never count.** Full list: [enrichment_catalog.json](presets/pacing/enrichment_catalog.json).

### 2.2 Rules
1. **Hard cap** (card above): a run longer than this fails. No exceptions by agents.
2. **Soft cap:** a run between soft and hard cap is allowed only if its **longest event-free interval** (run edges count as boundaries) is <= the preset gap. 5.0 s on `documentary_standard` needs an event between ~1.5 s and ~3.5 s.
3. **Every still has a motion assignment** from the motion library.
4. **A still is shown once per video and never A-B-A** (owner rule 2026-11-08). Fix a long hold with a *new* shot, never by going back to an earlier picture.
5. **The cap beats the same-idea merge.** If merging two pictures of one idea would exceed the hard cap, do not merge; use the second picture as a separate shot or replace one of them with a different idea.
6. **Owner waiver only:** the owner can set `"still_hold_waiver": "<reason>"` on a slot **and** run QA with `--allow-waivers`. Without that flag the FAIL stands (`WAIVER_IGNORED`), so an agent cannot waive itself. Agents never pass the flag.
7. **No dummy resets:** a video clip or plate shorter than 1.0 s does not end a still run; a plate longer than 8.0 s fails `PLATE_HOLD`; a plate without a `plate_type` warns (`PLATE_UNTYPED`); a picture file declared as `video` is still counted as a still (`MEDIA_TYPE`); a `detail_crop` / `reveal` counts as an event only if it really re-frames (target area <= 65 % of the frame), else `WEAK_RECOMPOSE`.

### 2.3 Fix order for a still that is too long (cheapest, most honest first)
1. **Cut:** add a distinct asset (second picture, B-roll, archival footage) on the words where the topic changes.
2. **Plate:** replace part of the hold with a full-frame plate: map (only if geography is the point), article card, quote card, stat plate, then/now, split screen.
3. **Enrich** (only for 4.5-6.0 s): keep the picture and place tier A/B events so no gap exceeds the preset gap.
4. **Nothing exists:** build a `narration_plate`: a key-fact or quote card from the line itself (verbatim or verified fact) on a texture plate, 2.5-3.5 s. Always buildable, so the bypass policy holds: never a black slot, never a stall.

### 2.4 Worked example (the 12-second case)
Narration: 12 s about a phone call; one rotary-phone photo.
`still_hold_qa.py` -> `STILL_HARD 12.0 s > 6.0 s; need >= 3 distinct shots (cuts near 00:04, 00:08)`.
`asset_audit.py` -> research request `coverage_deficit, needed 2`.
Fix: 0-4 s the phone photo, opening with a `reveal` on "the receiver" -> 4-8 s archival footage of a switchboard (cutaway) -> 8-12 s a different picture, the newspaper clipping, with a `date_strip` "14 MARCH 1974" and a `detail_crop` onto the headline. The phone photo is not used again. Longest run 4.0 s. PASS.

### 2.5 Where it is enforced
| Point | Tool | Behaviour |
|---|---|---|
| Stage 06 beats | `make_beats.py` (max 6.0 s) | One beat = one visual; longer beats get a second visual (`sub`). |
| Stage 06 shot plan | `still_hold_qa.py --shot-plan` + `variation_report.py` | FAIL blocks Stage 06 acceptance. |
| Stage 07 | `asset_audit.py` | Coverage deficit becomes research requests; fallback chain ends in `narration_plate`. |
| Stage 08 build | `build_full_edit.py` (cap beats merge; writes `still_hold_warnings.json`; picks moves from the library) | Never stops the build (bypass policy); the warning feeds the QA gate. |
| Stage 08 / 10 | `still_hold_qa.py` (plan or beats) + `--media` rendered-video scan | PASS required for G4 (or owner waiver). |
| Any time | `beats_qa.py --max-still 6.0` | Same cap per beat. |

---

## 3. Making the image follow the narration (enrichment)

**Principle: cut first, enrich second, decorate never.** An overlay that adds no information is noise; the viewer must learn something new every time the picture changes.

### 3.1 The ladder
| Tier | What | Examples (house tool) | Counts as event? |
|---|---|---|---|
| **A** In-frame camera | Re-frame the *same* picture so it shows something new | detail crop, reveal, punch-in, focus pull, 2.5D parallax (opt-in) | yes (parallax: no) |
| **B** Overlay on the picture | Annotate, label, emphasise | photo-annotation (ellipse + label), spotlight (dim the rest), keyword pop, kinetic quote, stat counter, location stamp, date strip, person pin, lower third, group legend, source tag, article highlight, timeline strip | yes |
| **C** Full-frame plate | Replace the still for a beat | map, article card, quote card, then/now, split screen, photo stack, stat plate, **narration plate** | ends the run |
| **D** Cutaway | Other material | related B-roll / ALT image, archival footage insert | ends the run |
| **S** Support | Sound only | SFX accent, music swell | never counts |

### 3.2 What the line says decides the method (`info_type` in the beat map)
| The narration... | First choice | Fallback |
|---|---|---|
| names a person | lower third / person pin | rack focus, detail crop |
| describes a place or journey that **is** the story | map | location stamp, pull-back |
| mentions a place only | location stamp | B-roll cutaway |
| states a number or amount | stat counter / stat plate | keyword pop |
| jumps in time | date strip / location stamp | timeline strip |
| reads a quote | kinetic quote (<= 25 words) / quote card | source tag |
| cites a document or headline | article highlight / article card | detail crop + source tag |
| points at an object or detail | photo annotation / detail crop | spotlight, reveal |
| singles out one face in a group | spotlight / person pin | detail crop |
| contrasts two things | split screen / then-now | B-roll cutaway |
| runs through a list of proofs | photo stack / timeline strip | B-roll cutaway |
| turns on one pivot word | keyword pop / punch-in | detail crop |
| is emotional, nothing concrete | pull-back / rack focus | B-roll cutaway |
| has period footage | archival insert | B-roll cutaway |
| has nothing available | narration plate | - |

### 3.3 Rules
1. **Anchor to a word.** Every enrichment carries `anchor_word` / `at_ms`; it appears <= 2 frames before the spoken word and leaves with its sentence (existing `clamp_graphic` rule).
2. **Motivated, not decorative.** `rationale` is required for tier C/D choices (section 9).
3. **Density caps still apply** (per 10 min, in the catalog): map 2, article 3, keyword pop 2, stat 3, kinetic quote 3, date strip 2, photo stack 1, split screen 2, punch-in 3. Tier A detail crops are uncapped but obey the motion rules (section 6). This is why *cut first*: the capped graphics cannot carry a whole video.
4. **Map guard unchanged:** a place merely mentioned never gets a map (Toolkit 2.3). Never an AI face of a real person. Never synthetic imagery for real history (LESSONS #7).
5. **Layout hygiene unchanged:** no two families in the same screen corner; blur under full-screen text (SKILL §10.5); titles inside the safe area.
6. **Sound supports, never substitutes.** An SFX on a still with no visual change is a failure of imagination, not an enrichment.
7. **J/L-cut the picture change:** the next picture may lead the audio by 8-18 frames at a topic change, never lag the word that names it.

---

## 4. Beat map: emotion, intensity, function

A beat = one sentence or half-sentence of narration (`make_beats.py`: 2.5-6 s). The beat-map agent rates **every** beat once; that one analysis drives pacing, motion, music, SFX and look.

### 4.1 Schema (`06_script_edit_plan/beat_map.json`, template `templates/beat_map.example.json`)
```json
{ "schema": "pipeline.beat_map/1",
  "beats": [
    { "beat": "B014", "emotion": "tension", "intensity": 4, "function": "turn",
      "info_type": "document", "anchor_phrase": "the 1974 court order", "priority": 5,
      "evidence": "short, declarative; stakes named; pause before 'order'" } ] }
```
| Field | Values | Used for |
|---|---|---|
| `emotion` | `calm` `tension` `grief` `joy` `neutral` (plain exposition) | motion choice, transition, music, SFX, look bias |
| `intensity` | 1-5 (1 = barely felt, 3 = engaged, 5 = the peak of the chapter) | shot-length scale, **tighter** still caps (4: x0.85, 5: x0.70), motion intensity, music lift |
| `function` | `hook` `exposition` `turn` `reveal` `payoff` `breather` | which beats may never be cut for a short version (`priority`), where to place pattern interrupts |
| `info_type` | `person` `place` `number` `date` `quote` `document` `object` `contrast` `list` `abstract` | enrichment selection (3.2) |
| `anchor_phrase` | exact words of the beat the picture must show | shot-plan `anchor_phrase`, asset search query, QA of picture vs words |
| `priority` | 1-5 | cut order for the short version and Shorts |

### 4.2 Rules
1. **AI rates by beat id; code maps beats to times.** No AI writes a timecode (Vcut principle 3). Worker: Argon-class model (judgement), reviewer: Sonnet.
2. **Rubric over vibes:** intensity 5 = the chapter's peak (max 20 % of beats); a chapter has >= 3 distinct intensity levels; mean intensity 2.5-3.2; adjacent beats differ by <= 2 unless `function` is `turn` or `reveal`.
3. **Deterministic cross-check** (code, no AI): speaking rate of the beat vs the video mean, silence before/after it, sentence length, punctuation. A beat the model rated 5 that is slower than mean and has no pause is flagged for re-rating.
4. **The map is an input to the colour script and music**, not a decoration: intensity curve -> music bed lift and riser placement (stage 04); emotion, intensity and `function: turn/reveal` tell the colour script *where* a phase may change. *Which way* the colour moves comes from the story logic in [COLOR_SCRIPT.md](COLOR_SCRIPT.md), never from the emotion (the old `look_bias` column was a universal colour-emotion rule and is removed, revision 2026-11-09).

### 4.3 What each emotion does (`pacing_presets.json emotions`)
| Emotion | Motions | Transition | Music / SFX | Colour |
|---|---|---|---|---|
| calm | drift, slow push, wide pan | cut or soft dissolve | steady bed, room tone | per colour script |
| tension | push-in, detail crop, reveal, micro handheld | cut; whip at the peak only | bed rises 2-4 dB, riser into the reveal, sub hit on key word | per colour script |
| grief | pull-back, drift, slow push | slow dissolve, dip to black on release | thin pad, duck 2 dB deeper, silence preferred | per colour script (longer holds) |
| joy | push-in, pan, reveal | cut; light-leak on a celebratory turn | brighter bed (+1-2 dB), soft shimmer | per colour script |
| neutral | slow push, drift, pull-back | cut | unchanged | per colour script |

---

## 5. Pacing presets

Four named presets (numbers in section 0 and [pacing_presets.json](presets/pacing/pacing_presets.json)). A preset also defines motion intensity band, hard-cut share, dynamic-transition budget, pattern-interrupt interval, SFX density and music behaviour.

| Preset | Use for |
|---|---|
| `slow_reflective` | grief, reckoning, tribute tone, quiet epilogues |
| `documentary_standard` | default for narrated essays |
| `tense_fast` | hooks, cold opens, escalations, investigation turns |
| `shorts_vertical` | 9:16 derivatives (DERIVATIVES.md) |

Selection: **video default** in `brief.md` (`pacing_preset:`; default `documentary_standard`) -> **chapter override** (the hook chapter defaults to `tense_fast`) -> **per-beat modulation** by intensity (shot length scales 1.25x at intensity 1 down to 0.70x at 5; caps only ever tighten). Presets are a *pacing* axis, independent of the visual style preset (`presets/documentary-default/`).

A preset change never relaxes the absolute 8.0 s ceiling or the "every still once" rule.

---

## 6. Motion style library

[motion_library.json](presets/pacing/motion_library.json): `push_slow`, `push_in`, `pull_back`, `drift_left`, `drift_right`, `pan_wide`, `reveal`, `detail_crop`, `punch_in`, `handheld_micro`, `rack_focus`, `parallax_25d` (opt-in). Each move has rects (start/end, normalized), direction, intensity 1-5, fitting emotions and subjects, `faces_safe`, `counts_as_event`, and what it requires (`target_rect`, wide aspect).

**Selection (`pacing_lib.pick_motion`, deterministic):**
1. Hard filters: emotion avoid-list, preset intensity band, subject, faces (anchor on the eyes; `handheld_micro` never on faces/documents), `target_rect` present when required, wide aspect for `pan_wide`, duration (< 2 s: no intensity > 3).
2. **Cooldown:** a move is not reused within the last 2 slots; no 3rd identical move in a row (was 4 in the old toolkit); **no same lateral direction twice**; one move <= 35 % of all stills.
3. Score: emotion preference order, intensity fit, direction change, least-recently-used.
4. **Log every pick** to `motion_log.json` (`id`, `move`, `direction`, `reason`); `variation_report.py` reads it.

Only moves with `counts_as_event: true` (detail crop, reveal, punch-in, focus pull) help a long still; a push or drift is motion, not information. `rect_to_scale_pos(rect)` converts a rect into FilmCraft `motion` scale/position keyframes (verified numerically; Resolve motion scripting remains unverified, Toolkit 2.4).

---

## 7. Variation tracking

`variation_report.py` logs motions, transitions, SFX and enrichments with times and enforces:

| Severity | Rule |
|---|---|
| FAIL | same motion 3x in a row · same dynamic transition on 3 consecutive cuts · dynamic transitions above the preset budget · an enrichment type above its per-10-min cap |
| WARN | same lateral drift twice in a row · one move > 35 % · hard-cut share below the preset minimum · same SFX twice within 20 s · > 25 % of shots outside the preset range · a motion on the emotion's avoid list (punch-in on grief) · major choice without rationale |

Hard cuts are the default (documentary_standard >= 85 %). A 10-frame dissolve on *every* cut (video 19 build) is a `CUT_SHARE` warning.

---

## 8. Asset audit (before editing)

`asset_audit.py`, end of Stage 07. Judges each picture **against the crop the plan will use**, not its raw size.

| Code | Meaning | Severity |
|---|---|---|
| `TOO_SMALL` | upscale > 2.5x at 1080p after the planned push | FAIL |
| `SOFT_UPSCALE` | upscale > 1.35x | WARN (use `push_slow`, add grain, or swap) |
| `ASPECT_PORTRAIT` | portrait / square: 16:9 cover shows < 60 % of it | WARN (fit + blurred plate, inset, panel) |
| `ASPECT_PANORAMA` | aspect >= 2.2 | INFO (use `pan_wide` / drift) |
| `DUPLICATE` / `SIMILAR` | perceptual hash distance <= 4 / <= 10 of 64 | WARN; FAIL if used within 20 s of each other |
| `BLANK` / `CORRUPT` / `MISSING_FILE` / `MISSING_ASSET` | unusable or absent | FAIL |
| `COVERAGE_DEFICIT` | one idea must carry narration longer than the hard cap | FAIL (WARN over soft cap) |
| `UNUSED` | in the folder, no slot uses it | INFO |

Outputs: `asset_audit.json`, `asset_audit.md`, **`research_requests.json`** (beat, narration text, reason, how many more shots are needed). Loop: audit -> research requests -> `media_search.py` (max 2 rounds) -> fallback chain -> `narration_plate`. `similar_pairs` from the audit feed `still_hold_qa.py --assets-report` so near-duplicates count as one run.

---

## 9. Edit report with rationale

`variation_report.py --out-md edit_report.md` -> `07_Video_Edit/Export/edit_report.md`. Sections: summary numbers, flags, **creative choices and why**, enrichment ledger vs caps, "review these first", owner feedback block.

**What needs a `rationale`** (recorded in the shot plan at decision time, never reconstructed afterwards): any dynamic transition, any full-frame plate, any tier C/D enrichment, any beat at intensity >= 4, any preset override, anything flagged `major`. Format: one sentence tying the choice to the line (*"Whip pan: first time the narrator leaves Mirfield for London; marks the act break"*). The owner reads section 5 ("review these first": the five riskiest choices) and corrects the agent there; corrections go to the style memory.

---

## 10. Feedback loop and style memory

| File | Role | Written by |
|---|---|---|
| `Videos-Scripts/_style_memory/style_memory.md` (template `templates/style_memory.md`) | Channel-level **taste**: dated rules with evidence and strength | Agent, after owner feedback |
| `edit_report.md` section 6 | Owner's raw feedback per video (liked / disliked / too slow at / overlays) | Owner |
| `LESSONS.md` | Pipeline bugs and tool friction (unchanged) | Agent |
| `presets/` | Baked, owner-approved defaults (`bake-preset` skill) | Owner approves |

**Load:** Stage 03 (choose preset, hook feel) and Stage 06 (mandatory input) read the style memory first; the shot plan header records `style_memory_rules_applied: [ids]`.
**Update:** after G4, the agent converts the owner's feedback into rules: `id`, one-line rule, `evidence` (video, timestamp), `strength` (`tried` -> `preferred` -> `always`), `date`. Conflicts: newest wins unless the owner said "always". **Bounded:** max 40 active rules; merge or retire before adding. **Promotion:** a rule confirmed on 3 videos is proposed for `bake-preset`; agents never edit presets or the memory's `always` rules without the owner.
Memory is *taste*, caps are *law*: a style rule can never relax a hard cap, a licence rule or a truth-tier rule.

---

## 11. Verdict on the ten editing tips

| # | Tip | Verdict | What we took and where it lives | What the tip gets wrong or leaves out |
|---|---|---|---|---|
| 1 | Beat detection + emotion (1-5) | **ADOPT, first** | Section 4: `beat_map.json`, Stage 06a, mapping tables in `pacing_presets.json` | Emotion says *how* to cut, not *what* to show. Added `info_type`, `function`, `anchor_phrase`, `priority`: those fix the boring-still problem. Raw LLM ratings are noisy: rubric, distribution limits and a deterministic cross-check added. |
| 2 | Pacing presets | **ADOPT** | Section 5 + `pacing_presets.json` (4 presets with numbers) | The tip has no numbers and no stillness cap. A "slow and reflective" preset without a hard cap is how 12-second stills happen. |
| 3 | Motion style library | **ADOPT, upgraded** | Section 6 + `motion_library.json` + `pick_motion` + builder integration | A Ken Burns variant is not enrichment. Only re-framing moves count as events. Added face-safety, cooldown, direction rule, usage-share cap. |
| 4 | Asset audit | **ADOPT; should have existed** | Section 8 + `asset_audit.py` + `research_requests.json` | The tip checks raw resolution; ours checks resolution **after the planned push** and finds narration that rests on too few pictures (the 12 s detector). |
| 5 | Alternate cuts | **ADOPT, opt-in** | `DERIVATIVES.md` section 1 | A "faster edit" with fixed narration is only a visual-rhythm change; a "shorter version" needs a narration cut list (`make_cuts.py` + beat `priority`). Each variant multiplies QA, so generate on request only. Orchestrator tool `[TO BUILD]`. |
| 6 | Shorts / Reels, re-crop each shot | **ADOPT as a post-G4 derivative** | `DERIVATIVES.md` section 2, `shorts_vertical` preset | Re-cropping is correct but needs a per-shot focus rect (face-safe), burned captions and the 9:16 safe window already in `presets/shorts-vertical`. Reframe tool `[TO BUILD]`. Never auto-publish. |
| 7 | Auto-chaptering + thumbnails | **ADOPT as inputs to Stage 09** | `DERIVATIVES.md` section 3, Stage 09 | Candidates feed the existing packaging rules (0.5 s friction test, subject flag, 120 px legibility); they do not replace them. Tools `[TO BUILD]`. |
| 8 | Variation tracking | **ADOPT, built** | Section 7 + `variation_report.py` | The tip says "so nothing repeats too closely" with no threshold. Thresholds are in the card; the old toolkit's "max 3 identical" is tightened to 2. |
| 9 | Edit report with rationale | **ADOPT, built** | Section 9 + `variation_report.py` | A rationale reconstructed after the fact is fiction. It is recorded in the shot plan when the choice is made, and only for major choices so the report stays readable. |
| 10 | Feedback loop / style memory | **ADOPT with guardrails** | Section 10 + `templates/style_memory.md` | Unbounded memory becomes contradictory mush. Bounded (40 rules), evidence-backed, strength-graded, owner-gated promotion. Taste never overrides caps, licensing or truth tiers. |

**Known limits (code cannot see these; the Sonnet reviewer and the owner must):** a photo pre-cut into several files with different names and no `asset_group` looks like different pictures to the hash; a `plate_type` is trusted, not verified against the rendered graphic; the `--media` scene scan is a heuristic (WARN only). Detail crops are motion on one asset, not separate files; if a crop file is unavoidable, give the crops the same `asset_group`.

**What none of the tips cover and this standard adds:** a numeric hard cap on any single image · the narration-to-method map · QA with exit codes (advice an agent can ignore is not a rule) · research requests that close the loop with Stage 07 · licensing/truth guardrails on every overlay.

---

## 12. Stage map

| Stage | New / changed |
|---|---|
| 03 Hook & outline | pick `pacing_preset`; load style memory |
| **06a Beat map** (new sub-step) | `beat_map.json` |
| **06b Colour script** (new sub-step, 2026-11-09) | `color_script.json` -> `color_script.py plan` gate ([COLOR_SCRIPT.md](COLOR_SCRIPT.md)) |
| 06 Shot plan | hold budget, enrichments, motion picks, rationale; `still_hold_qa` + `variation_report` gate |
| 07 Assets | `asset_audit` gate; research-request loop |
| 07b Graphics | build the enrichments listed in the plan |
| 08 Assembly | motion log; `still_hold_qa --media`; `edit_report.md`; optional alternate cuts |
| 09 Packaging | chapters + thumbnail candidates |
| 10 QA & delivery | 5th QA script (`still_hold_qa`); edit report; post-G4 style-memory update; optional Shorts |

<span style="color: purple;">[AI Agent]</span>
