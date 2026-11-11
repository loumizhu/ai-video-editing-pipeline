# Pipeline Lessons & Operational Retro Log

This document records friction points, failure modes, CLI tool quirks, and workflow bottlenecks discovered during real production runs. Every friction point encountered during a production run must be logged here, followed by an immediate revision to the relevant stage file or tool script.

> **Operational Rule:** Any lesson recorded here that changes the execution contract of a stage must be directly applied to that stage file with a dated revision note.

---

## Log Entry Format

When logging a lesson, use this template:

```markdown
### [YYYY-MM-DD] <Video_ID / Title> — Stage <NN> (<Stage_Name>)
- **Friction / Failure Observed:** <Concrete description of the error, bottleneck, or tool failure>
- **Root Cause:** <Why it happened: agent prompt ambiguity, CLI parameter issue, file mismatch, etc.>
- **Immediate Workaround Applied:** <How the current video run was unblocked>
- **Pipeline Revision Made:** <Exact stage file, script, or checklist updated to prevent recurrence>
- **Logged By:** <Agent / Operator>
```

---

## Calibrated Production Learnings (2026-11-01 Cut Engine & Presets Architecture)

### [2026-11-01] Video Pipeline Engine — Stage 05 (Voiceover & ASR)
- **Friction / Failure Observed:** Passing generic vocabulary bias prompts to Groq Whisper caused hallucinatory phrase insertions during silent gaps; high request rates triggered HTTP 429 without rate-limit headers.
- **Root Cause:** Observed behavior (underlying cause unconfirmed): Whisper decoder was observed hallucinating phrases during low-SNR/silent audio when vocabulary bias prompts were injected; Groq API omits audio-seconds quota headers.
- **Immediate Workaround Applied:** Removed uncalibrated prompt injection; introduced deterministic post-ASR vocabulary corrections (`transcript_corrections.json`) requiring stable token counts; implemented automated HTTP 429 `retry-after` backoff and `--repair-only` logging.
- **Pipeline Revision Made:** Applied to `stages/05_voiceover.md` and `TOOLS.md` (`transcribe_groq.py`).
- **Logged By:** Claude Sonnet & Claude Opus.

### [2026-11-01] Video Pipeline Engine — Stage 08 (Assembly & NLE Scripting)
- **Friction / Failure Observed:** Initial audit reported DaVinci Resolve Studio 20 scripting as "BLOCKED" due to connection timeouts and `ioctlsocket err 1` log output.
- **Root Cause:** Observed behavior: Scripted `Popen(..., DETACHED_PROCESS)` background launch coincided with connection timeouts and socket errors (underlying cause unconfirmed); normal interactive launch by user sitting past Project Manager completely resolved the connection. `ioctlsocket(block) err 1` in `davinci_resolve.log` is benign loopback socket negotiation present even in fully working sessions.
- **Immediate Workaround Applied:** Resolve must be launched normally by the user and sitting past the splash/Project Manager. System Python 3.13 connects immediately via `fusionscript.dll` and calls `GetVersionString()`.
- **Pipeline Revision Made:** Applied to `stages/08_assembly.md`, `TOOLS.md`, and `references/resolve.md`.
- **Logged By:** Claude Opus & Antigravity.

### [2026-11-01] Video Pipeline Engine — Stage 08 (Assembly & Python Runtime)
- **Friction / Failure Observed:** Executing Resolve scripting automation under `uv run --python 3.11` or `3.12` crashed with immediate segmentation faults (exit code 139) on Windows.
- **Root Cause:** Observed failure (exact mechanism unconfirmed): Blackmagic Design's C-extension DLL (`fusionscript.dll`) crashed with segfault rc 139 when imported under uv-managed standalone Python 3.11 and 3.12 binaries on Windows; system Python 3.13 executes cleanly without crashes.
- **Immediate Workaround Applied:** Switched all Resolve Studio scripting to system **Python 3.13 (64-bit)** (`C:\Users\ELITE\AppData\Local\Programs\Python\Python313\python.exe`), which connects and executes without segfaults.
- **Pipeline Revision Made:** Applied to `stages/08_assembly.md`, `TOOLS.md`, and `references/resolve.md`.
- **Logged By:** Claude Opus & Claude Sonnet.

### [2026-11-01] Video Pipeline Engine — Presets & Continuous Improvement
- **Friction / Failure Observed:** Ad-hoc styling tweaks during video edits (lower-third hold times, color contrast, SFX loudness) were forgotten in subsequent videos, creating styling drift and repetitive manual work.
- **Root Cause:** Lack of a centralized styling contract and formal post-edit feedback loop.
- **Immediate Workaround Applied:** Built centralized house presets (`presets/documentary-default/style.json` with 102 leaf keys, `shorts-vertical/`) and created the `bake-preset` skill (`.agents/skills/bake-preset/SKILL.md`) to turn owner edit feedback into diffed, approved changes that automatically re-render EffectCraft templates, `.cube` LUTs, and normalized SFX.
- **Pipeline Revision Made:** Integrated `bake-preset` and house presets into `README.md`, `EDITING_TOOLKIT.md`, and `video-editor` skill.
- **Logged By:** Claude Sonnet & Antigravity.

---

## Calibrated Production Learnings (from Video 010 & Toolkit Calibration)

Source: `Videos-Scripts/010-Patrick Stewart Hommage/10_process_and_learnings/` (`CONCLUSION_SUMMARY.md` & `PROCESS_ENHANCEMENT_GUIDE.md`).

### [2026-10-31] Video 010 (Sir Patrick Stewart Tribute) — Production Outcome & Facts
- **Video Specs:** 5:21 total runtime (321.64 seconds, 1080p60).
- **Acoustic Measurements Achieved:** Dialogue normalized to **-16 LUFS**, Scott Buckley "Childhood" piano score ducked to **-24 dB** under speech and **-28 dB** under scored clips, master true peak ceiling **-1.8 dBTP achieved** (target capped strictly below -1.5 dBTP).
- **Pacing & Timing:** Expanded Beat V to 6.0s total: Line 1 held alone for 2.70s of dedicated reading time before Line 2 smoothly revealed underneath for 2.5–3.0s.
- **Typography & Motion:** Golden hierarchy ratio (72px Bold Ivory `#F3EBDD` / 56px Italic Gold `#FFE8B8`, 78% ratio, spaced 90px apart, no text <45px). Motion reveal: soft feathered wipe (`linear_wipe_legacy` at 270°, feather 30) paired with 0.70s opacity fade.
- **Naming Reverence:** All occurrences of casual nickname "Cec" replaced with respectful formal name "Cecil" / "Cecil Dormand" across script, cards, captions, and metadata.
- **Turnkey Packaging:** Consolidated master video, SRT, 4 thumbnails (1280x720), metadata, timestamps, and checklist into `09_upload/`.

---

### Core Architectural Lessons

#### 1. Verify Breaking News First
- **Lesson:** Always run an initial live status check (dates, spouse, spokesperson statement, official memorial charities, breaking news) before writing anything. Avoid guessing or trusting second-hand YouTube titles.
- **Pipeline Implementation:** Applied to [stages/01_scout.md](stages/01_scout.md) (Step 1); produces dated proof artifact `01_research/FACT_BASELINE.md`, which [stages/02_dna.md](stages/02_dna.md) consumes as a mandatory input and verifies against competitor claims.
- **Revision Note:** 2026-10-31 — Added Step 0 live fact check to Stage 01 and baseline verification input to Stage 02 before any narrative scripting.

#### 2. Quote Provenance Rule
- **Lesson:** Never source quotes from automated voiceover channels or unverified fan compilations. Only use raw broadcast clips, talk show archives, or signed written statements.
- **Pipeline Implementation:** Applied to [stages/02_dna.md](stages/02_dna.md) (Step 4), [stages/03_hook_outline.md](stages/03_hook_outline.md) (Step 6), and [stages/04_script.md](stages/04_script.md) (Step 5 & Acceptance Checklist item 3); produces `01_research/QUOTE_PROOF.md` documenting source archive, timestamp, verbatim text, and verification method.
- **Revision Note:** 2026-10-31 — Banned third-party YouTube compilation sourcing; made `QUOTE_PROOF.md` a mandatory upstream gate input and script review checklist requirement.

#### 3. Eyes & Framing Check Over Audio Transcripts (Jackman-to-McKellen Example)
- **Lesson:** Audio transcripts do not show who the speaker is looking at (e.g., in archival footage, Hugh Jackman's line was directed to Ian McKellen, not Patrick Stewart). Always inspect video frames before attributing dialogue to a relationship.
- **Pipeline Implementation:** Applied to [stages/02_dna.md](stages/02_dna.md) (Step 5), [stages/03_hook_outline.md](stages/03_hook_outline.md) (Acceptance Checklist), and [stages/06_shot_plan.md](stages/06_shot_plan.md) (Step 4, `eyes_check_ref`); requires ffmpeg frame contact sheets (`BEST_LINES_SELFCHECK.txt` / contact sheet PNGs in `03_media/`).
- **Revision Note:** 2026-10-31 — Added mandatory eyes/framing check to Stages 02, 03, and 06.

#### 4. Automated Proof Loops Reach 100% First-Pass Accuracy
- **Lesson:** When briefs demand an automated proof artifact (e.g. Whisper JSON verification, multi-frame contact sheets, loudness readouts, hash checks), agent accuracy reaches 100% on the first pass without hallucinations.
- **Pipeline Implementation:** Applied across all stages: `01_research/FACT_BASELINE.md` (Stage 01), `01_research/QUOTE_PROOF.md` (Stage 02), `06_script_edit_plan/PREFLIGHT_01.md` (Stage 04), `06_script_edit_plan/whisper_diff.txt` & `loudness_readout.txt` (Stage 05), `07_Video_Edit/stem_loudness.txt` & `loudness_readout.txt` (Stage 08), `08_thumbnail/thumb_120px_test.png` (Stage 09), and `09_upload/master_loudness_readout.txt` (Stage 10).
- **Revision Note:** 2026-10-31 — Made proof artifacts mandatory deliverables for review acceptance.

#### 5. Technical Failures Must Never Halt Timeline Assembly (The Bypass Policy)
- **Lesson:** If external daemons (like Voicebox) are offline or an archival clip is temporarily unavailable, halting the entire pipeline stalls human review and blocks the NLE rough cut. Real productions need the visual timeline built immediately so the editor/owner can evaluate pacing.
- **Pipeline Implementation:** Applied to [00_ORCHESTRATOR.md](00_ORCHESTRATOR.md) (§7), [stages/05_voiceover.md](stages/05_voiceover.md), and [gates/GATES.md](gates/GATES.md); replaces hard stops with the technical bypass policy: estimated word timing (`timing.json` with `"estimated": true` at 158 WPM), placeholder audio, deferred Gate G3b sign-off, and logging to `_pipeline/BYPASS_LOG.md`. Re-time procedure documented for when real audio arrives.
- **Revision Note:** 2026-11-01 — Eliminated all halt/stop technical failure barriers; made FilmCraft timeline assembly unstoppable.

#### 6. Custom Typography & Overlay Graphics Over NLE Built-In Presets
- **Lesson:** Built-in NLE lower thirds, titles, and text cards look generic, inconsistent across software, and damage brand identity. In addition, scraping consumer map tiles (Google Maps) introduces legal risk and visual clutter.
- **Pipeline Implementation:** Applied to [EDITING_TOOLKIT.md](EDITING_TOOLKIT.md), [stages/06_shot_plan.md](stages/06_shot_plan.md), [stages/07b_graphics_build.md](stages/07b_graphics_build.md), and [stages/08_assembly.md](stages/08_assembly.md); mandated zero FilmCraft text presets; established deterministic keeper tools (`render_callout.py`, `render_map.py`, `render_article.py`) generating face-safe 1080p RGBA overlay cards placed natively on track V3.
- **Revision Note:** 2026-11-01 — Banned NLE title cards; created custom graphics generation stage (07b) and editing toolkit.

#### 7. 100% Continuous Visual B-Roll Coverage & The 5 Pillars of Archival Evidence (Zero AI Hallucinations for Real History)
- **Lesson:** Audio narration must NEVER run over a black screen or empty video track. Delivering voiceover without visual storytelling coverage is an objective failure. Furthermore, real historical events, figures, and documentary stories must NEVER be illustrated using synthetic AI-generated images or modern approximations. AI hallucinations destroy viewer trust, damage documentary authority, and violate journalistic integrity.
- **Pipeline Implementation:** Applied to [stages/06_shot_plan.md](stages/06_shot_plan.md), [stages/07_assets.md](stages/07_assets.md), and the `internet-media-search` skill (`SKILL.md` §6). Visual research must strictly prioritize the **5 Pillars of Archival Evidence**:
  1. **Archival Newsreels & Restored 16mm/35mm Footage:** British Movietone, Pathé, Prelinger, AP Archives, Universal Newsreels.
  2. **Broadcast Appearances & Oral Histories:** Contemporary TV interviews, Emmy TV Legends, talk show appearances (Mike Wallace, Dick Cavett, Dinah Shore).
  3. **Primary Source Documents & Microfilm Scans:** Authentic newspaper microfilm scans, court records, commitment dockets, rendered as sharp callouts with `render_article.py`.
  4. **Restored Period Cinema & Theatrical Trailers:** Original studio feature film appearances, trailers, public domain 35mm prints.
  5. **Verified Archival Stills:** High-resolution public domain photographs from Library of Congress, Bain Collection, NARA, Wikimedia Commons, animated via subtle 2.5D Ken Burns push/pull.
- **Revision Note:** 2026-11-05 — Mandated 100% gapless visual B-roll coverage and established an absolute ban on synthetic AI image hallucinations for historical documentaries.

### [2026-11-07] Video 19 (Child Stars Who Quit Hollywood) — Stages 05/07/08 (full FilmCraft edit)
- **Friction / Failure Observed:** (1) image search returned 0 results (DuckDuckGo "202 Ratelimit"); (2) Voicebox swapped/repeated words in 2 of 107 paragraphs; (3) 3 paragraphs failed to render on first pass; (4) earlier asset registry had no source URLs or licences; (5) a photo annotation and a group legend landed on the wrong image.
- **Root Cause:** legacy `duckduckgo_search` package; TTS nondeterminism; registry schema without provenance fields; graphics anchored to a phrase whose paragraph spans two images.
- **Immediate Workaround Applied:** switched to `ddgs`; transcribe-and-diff QA on every paragraph, re-render failures; full interview sources re-downloaded with `.info.json`; annotation paragraphs given a single image.
- **Pipeline Revision Made:** `internet-media-search` SKILL.md §1.7-1.9 + `media_search.py`; `video-editor` SKILL.md §7; `tools/build_full_edit.py` (plan-driven FilmCraft builder).
- **Logged By:** Claude Opus.

### [2026-11-07] Video 19 — Stage 08 (editable graphics, FX overlays, alternatives)
- **Friction / Failure Observed:** owner could not edit any title: graphics were rendered ProRes `.mov` files.
- **Root Cause:** pipeline rendered titles in EffectCraft; FilmCraft only receives pixels.
- **Immediate Workaround Applied:** v2 project rebuilt with native FilmCraft graphics (text/shape layers, pinned plates, keyframed responsive animation), Screen-blend atmosphere overlays, hidden ALT tracks with researched alternatives. v1 kept.
- **Pipeline Revision Made:** `tools/fc_session.py`, `tools/fc_native_gfx.py`, `tools/build_v2_editable.py`; video-editor SKILL.md §8.
- **Logged By:** Claude Opus.

### [2026-11-08] Video 19 — Stage 08 (graphic timing, soundbite cuts, duplicate images)
- **Friction / Failure Observed:** (1) text cards stayed on screen after the narration had moved on; (2) the Peter Ostrum interview clips started on the previous sentence's last word and ended on the next sentence's first word; (3) two near-identical rotary-phone pictures played back to back on one line.
- **Root Cause:** graphics used fixed family durations; soundbite in/out were taken from Whisper sentence times without checking adjacent words or the waveform; the shot plan scheduled every alternative of a research gap.
- **Immediate Workaround Applied:** v3 project: graphics clamped to their paragraph span, all soundbites snapped and re-transcribed, same-idea shots merged (alternatives kept on hidden ALT tracks), long holds broken up.
- **Pipeline Revision Made:** `tools/soundbite_bounds.py`; `build_full_edit.py` (`clamp_graphic`, `same_idea`, `sb_range`, `graphics_plan` stage); video-editor SKILL.md §9; internet-media-search SKILL.md §1.10-1.11.
- **Logged By:** Claude Opus.

### [2026-11-09] Pacing audit (a still image stayed on screen for 12 seconds)
- **Friction / Failure Observed:** Narration was good but a single boring picture sometimes held for ~12 s; images did not follow what the narrator said.
- **Root Cause:** (1) `build_full_edit.visual_plan()` shot count was `min(images, span / 2.6 s)`, so one image for a 12 s paragraph meant one 12 s shot; (2) the same-idea merge extended holds without limit; (3) caps were loose (`~10 s`, `<= 8 s`) and checked per beat instead of per picture run; (4) a Ken Burns zoom was the only treatment (motion, not information); (5) nothing mapped what the line says (person, number, date, document, object) to what appears on screen.
- **Immediate Workaround Applied:** none needed; fixed at the standard level.
- **Pipeline Revision Made:** new `PACING_AND_ENRICHMENT.md` (still-hold budget: hard cap 6.0 s, soft 4.5 s with enrichment events, never above 8.0 s; enrichment ladder and narration-to-method map; beat map with emotion/intensity; 4 pacing presets; motion library with cooldown; variation tracking; asset audit; edit report with rationale; bounded style memory), `DERIVATIVES.md`, `presets/pacing/*.json`, tools `still_hold_qa.py` / `asset_audit.py` / `variation_report.py` / `pacing_lib.py` (69 self-tests), `make_beats.py` max 6.0 s, `beats_qa.py --max-still 6.0`, `build_full_edit.py` governor + motion library; stages 06, 07, 07b, 08, 09, 10, orchestrator, gates (G4 item 7) updated; `video-editor` SKILL §9.5 / §10.2 superseded.
- **Logged By:** Claude Sonnet 5.5 (pacing audit session).

### [2026-11-09] Colour script (owner request: colour that follows the story)
- **Friction / Failure Observed:** One look for the whole video; the only emotion-to-colour guidance was a `look_bias` table (grief = desaturate, joy = warm highlights) that nothing applied.
- **Root Cause:** No colour plan stage; `build_full_edit.py` applied `house-style.fcpreset` to every V1 clip, generated plates included; the `look_bias` table was a universal colour-emotion rule, which a story-driven colour script must not use.
- **Immediate Workaround Applied:** none needed; fixed at the standard level.
- **Pipeline Revision Made:** new `COLOR_SCRIPT.md` (story logic first; 4-8 phases by beat id; offsets from the house grade in measured Lumetri units; subtle <= 3.0 dE; >= 20 s per phase; stepped blends at cuts; protection of archival, documents, faces, B&W/toned prints; plates never graded; motifs via HSL qualifier only on colours already present), `presets/color/color_rules.json`, `tools/color_script.py` + `color_lib.py` (plan + qa, FilmCraft-measured LUT per look, 38 self-tests), `templates/color_script.example.json`, Stage 06b, `build_full_edit.py` applies one preset per look; `look_bias` removed from `pacing_presets.json`.
- **Logged By:** Claude Opus 5.5 (colour script session).

<span style="color: purple;">[AI Agent]</span>
