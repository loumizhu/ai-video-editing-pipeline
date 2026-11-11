# Faceless YouTube Markdown Video Pipeline

A deterministic, Markdown-orchestrated production system for creating 15 min–3 h, high-retention, high-RPM documentary videos centered on household-name stars and franchises.

This pipeline replaces bloated web dashboards with a reliable, inspectable architecture:
**Structured Markdown Stage Files + Deterministic CLI Tools + Human Approval Gates**, operated by an AI orchestrator (Claude) delegating to specialized models and CLI utilities.

> **Unified Entry Point (Revision 2026-11-01):** When the owner says *"edit this video"*, the umbrella **`video-editor` skill** (`.agents/skills/video-editor/SKILL.md`) executes Jason Cooperson's proven cut-and-finish loop on our stack: transcribe → cut list (owner approves) → build in FilmCraft → graphics from house presets → grade/SFX/music → QA by code → honest truth report → bake learnings into presets (`bake-preset`). Zero third-party NLEs (Resolve / Premiere) are used.

---

## 1. Core Principles

1. **Deterministic Separation:** Mechanical tasks (scraping, audio normalization, video conforming, rendering, custom graphics, hashing) are handled exclusively by deterministic CLI tools (`ffmpeg`, `yt-dlp`, `Pillow`, `filmcraft-cli`, `voicebox`, `render_*.py`, `make_cuts.py`, `build_cut_*.py`, `map_to_cut_time.py`). AI agents are reserved strictly for research synthesis, narrative architecture, scriptwriting, and review scoring.
2. **File-Based Handoff:** The pipeline relies zero on conversational memory. The output filenames of Stage $N$ serve directly as the input filenames of Stage $N+1$. Any stage can be stopped, inspected, or resumed directly from disk.
3. **Five Human Approval Gates:** Mandatory human sign-offs at Topic (G1), Hook/Outline (G2), Script (G3), Final Narration Gate (G3b), and Final Cut (G4). Agents cannot self-approve.
4. **Bypass Policy (Unstoppable Timeline):** No technical failure (Voicebox offline, aligner missing, asset missing) stops a video from reaching FilmCraft. Technical blockers are bypassed with logged fallbacks; Gate G3b is deferred until publish; integrity rules (facts, quotes, licensing, gates) are never bypassed.
5. **No Third-Party NLE:** Production uses FilmCraft (`filmcraft-cli` / GUI) exclusively. Zero third-party NLEs (Adobe Premiere Pro, DaVinci Resolve Studio) are permitted.
6. **Dedicated Source & Export Subfolders:** Stages involving creative editing (`07_Video_Edit/` and `08_thumbnail/`) strictly isolate project inputs (`Source/`) from generated video/image outputs (`Export/`).
7. **Custom Graphics & House Presets:** Zero built-in NLE default title or lower-third presets. All text, character callouts, purposeful maps, and article highlights are generated from our house-style presets (`presets/documentary-default/`) or custom scripts and placed natively on timeline tracks V3/V4.
8. **Pacing & Enrichment (Revision 2026-11-09):** no still image stays on screen past its hard cap (6.0 s on `documentary_standard`, never above 8.0 s); a still past 4.5 s must carry enrichment events anchored to the narration (detail crop, annotation, keyword, stat...); cut first, enrich second, decorate never. Beat emotion/intensity drives pacing, motion, music and look; motion moves are logged and never repeated closely; every major creative choice carries a rationale; owner feedback updates a bounded style memory. See [PACING_AND_ENRICHMENT.md](PACING_AND_ENRICHMENT.md).
8b. **Colour Script (Revision 2026-11-09):** the grade follows the story: 4-8 colour phases by beat id, each an offset from the house look, subtle by default (<= 3.0 dE on the reference chart), shifting at most every 20 s, with archival, documents, faces and B&W protected and generated graphics never graded ([COLOR_SCRIPT.md](COLOR_SCRIPT.md)).
9. **Editorial Standards:** Adheres to café-friend narration, zero sensational judgment adjectives (*predatory, cruel, shocking*), explicit truth tiers (`[documented]`, `[reported]`, `[alleged]`, `[speculative]`), single held-back hook (first hook within 20–40 s, reveal at 85–95%), a fresh hook every ~60–90 s, progressive open loops (≥5 per 20m), and shock-forward packaging that stays on the real subject (owner-checked).
10. **Notion Policy:** Archival only on explicit user request; never sync, create, or update task cards ([AGENTS.md §1](../../AGENTS.md)).
11. **Workspace & Run Folders:** Multi-agent scratch runs execute in `temp_can_del_later/_runs/<YYYY-MM-DD>_<task-slug>/` per `AGENTS.md` §5 and are deleted after approval; permanent project assets and pipeline state live in `Videos-Scripts/<NN>_<Slug>/`.

---

## 2. Pipeline File Map

```text
Videos-Scripts/Video_Pipeline/
├── README.md                    ← Entry point, protocol, and quickstart (this file)
├── 00_ORCHESTRATOR.md           ← Routing, state machine, folder structure, bypass policy
├── EDITING_TOOLKIT.md           ← Transitions, callouts, purposeful maps, effects, rhythm
├── COLOR_SCRIPT.md             ← Story-driven colour script: phases, per-shot looks, protection, colour QA (Revision 2026-11-09)
├── PACING_AND_ENRICHMENT.md     ← Still-hold caps, enrichment ladder, beat map, pacing presets, motion library, variation, asset audit, edit report, style memory (Revision 2026-11-09)
├── DERIVATIVES.md               ← Alternate cuts, Shorts/Reels (9:16), auto-chapters, thumbnail candidates
├── TOOLS.md                     ← Catalog of verified deterministic tools, commands, and gaps
├── LESSONS.md                   ← Ongoing operational retro log for friction points & fixes
├── gates/
│   └── GATES.md                 ← Human approval gates (G1, G2, G3, G3b, G4) specifications
├── presets/                     ← Reusable house-style presets & templates (Revision 2026-11-01)
│   ├── documentary-default/     ← 16:9 master preset (style.json, grade LUT, SFX, graphics templates)
│   ├── shorts-vertical/         ← 9:16 vertical override preset (kinetic pop, safe window)
│   └── pacing/                  ← pacing_presets.json, motion_library.json, enrichment_catalog.json (numbers read by the pacing tools)
├── tools/                       ← Deterministic keeper scripts for graphics, cuts, audio, and QA
│   ├── check_setup.py           ← Preflight environment inspector (FFmpeg, Python, FilmCraft, keys)
│   ├── transcribe_groq.py       ← Groq whisper-large-v3 word ASR with gap repair & corrections
│   ├── make_cuts.py             ← Frame-snapped cut contract with waveform audio energy snapping
│   ├── map_to_cut_time.py       ← Source time / word index to cut-timeline mapping & word index utility
│   ├── build_cut_filmcraft.py   ← Deterministic FilmCraft project builder & 0-drift verifier
│   ├── render_cut_ffmpeg.py     ← Single-filtergraph cut MP4 renderer & A/V sync verifier
│   ├── cut_audit.py             ← Cut boundary audio discontinuity & speech clipping auditor
│   ├── dead_air_qa.py           ← Excessive silence & dead air scanner (>0.6s)
│   ├── flash_scan.py            ← WCAG 2.3.1 photosensitive flash hazard screen
│   ├── graphics_qa.py           ← Graphic overlay canvas bounds & title-safe verifier
│   ├── stem_loudness.py         ← Forensic EBU R128 audio stem loudness report generator
│   ├── render_callout.py        ← Character introduction callout renderer (face-safe RGBA)
│   ├── render_map.py            ← Geographically accurate map & route draw-on renderer (Natural Earth)
│   ├── render_article.py        ← Article display with exact substring marker-sweep highlight
│   ├── render_card.py           ← Overlay cards (date strips, stamps, big stats, keywords, chapters)
│   ├── write_graphics_manifest.py ← Scans graphics and generates graphics_manifest.json
│   ├── color_script.py          ← Colour script: per-shot looks from story phases (plan) + strip / phase sheet / text, skin, clipping QA (qa)
│   ├── color_lib.py             ← Colour maths, look offsets, protection, Lumetri presets, measured LUTs
│   ├── still_hold_qa.py         ← Still-hold budget QA: no image on screen past its cap (+ rendered-video scan)
│   ├── asset_audit.py           ← Asset audit: resolution after planned push, aspect, duplicates, coverage, research requests
│   ├── variation_report.py      ← Variation tracking (motion/transition/SFX/enrichment) + edit report with rationale
│   ├── pacing_lib.py            ← Shared library: presets, clip loaders, still runs, motion picker, rect→keyframes
│   ├── make_beats.py / beats_qa.py / beats_contact.py ← Beat-driven visual plan (beats ≤ 6 s; beats_qa still cap 6 s)
│   ├── estimate_timing.py       ← Narration timing estimator at calibrated rate (158 WPM)
│   ├── make_placeholder_vo.py   ← 48kHz mono PCM silent WAV placeholder generator
│   └── data/                    ← Natural Earth 1:50m vector GeoJSON data + LICENSE.txt
├── templates/
│   ├── STANDARD_FOLDER_STRUCTURE.md ← Master standard video project folder layout specification
│   ├── brief.md                 ← Kick-off brief template (from Video 010 checklist)
│   ├── video_STATUS.md          ← Per-video master tracking board
│   ├── color_script.example.json ← Colour script template (story logic, phases by beat id, motifs)
│   ├── beat_map.example.json    ← Beat map template (emotion, intensity, function, info_type)
│   ├── style_memory.md          ← Channel taste-memory template (feedback loop)
│   ├── stage_in.md              ← Worker assignment brief template
│   ├── stage_out.md             ← Worker deliverable output template
│   └── approval.md              ← Human gate sign-off record template
└── stages/
    ├── 01_scout.md              ← Topic validation, proof of concept & outlier spikes
    ├── 02_dna.md                ← Competitor DNA, transcripts & comment friction analysis
    ├── 03_hook_outline.md       ← Single held-back hook, loops map, visual intents
    ├── 04_script.md             ← 15 min–3 h scriptwriting, truth tiers & §10 pre-flight (17 points)
    ├── 05_voiceover.md          ← Voicebox neural TTS, Groq word timing, cut contract (bypassable)
    ├── 06_shot_plan.md          ← Beat map (06a), preset pacing + still-hold budget (3.5–4.5s cuts, 6 s hard cap), enrichment, toolkit schemas
    ├── 07_assets.md             ← Media acquisition, Fair Use check, conform & candidate fallback
    ├── 07b_graphics_build.md    ← Preset overlay generation & QA (callouts, maps, articles, contact sheet)
    ├── 08_assembly.md           ← FilmCraft timeline build, 3-layer mix & preview (zero third-party NLE)
    ├── 09_packaging.md          ← 5-title cluster, thumbnail variants & 0.5s friction test
    └── 10_qa_delivery.md        ← Forensic QA (5 code QA scripts incl. still-hold), EBU R128 audit, Human G4 gate & mastering, style-memory update
```

---

## 3. How to Start a New Video

1. **Invoke Editor or Scaffold Directory:**
   - For an automated editing pass, invoke the **`video-editor` skill** (`.agents/skills/video-editor/SKILL.md`).
   - For a full end-to-end documentary cycle, scaffold the Video 010 standard layout under `Videos-Scripts/<NN>_<Slug>/` per [STANDARD_FOLDER_STRUCTURE.md](templates/STANDARD_FOLDER_STRUCTURE.md):
     `00_planning/`, `01_research/`, `02_reference_videos/`, `03_media/`, `03_media/`, `05_audio/`, `06_script_edit_plan/`, `07_Video_Edit/Source/`, `07_Video_Edit/Export/`, `08_thumbnail/Source/`, `08_thumbnail/Export/`, `09_upload/`, `10_process_and_learnings/`, and `_archive/`.
2. **Fill the Kick-Off Brief:**
   Copy `templates/brief.md` to `Videos-Scripts/<NN>_<Slug>/00_planning/brief.md` and complete the 7 owner decisions.
3. **Initialize Status Board:**
   Copy `templates/video_STATUS.md` to `Videos-Scripts/<NN>_<Slug>/00_planning/00_STATUS.md`.
4. **Trigger Stage 01:**
   Issue worker brief following `stages/01_scout.md` and `templates/stage_in.md`.
5. **Follow the State Machine:**
   Step through stages 01 to 10 with cross-model reviews (max 3 passes) and halt at human gates G1, G2, G3, G3b, and G4.

---

## 4. First-Run Protocol (Field Testing & Calibration)

Before deploying autonomous delegation across multiple projects, run **ONE real video** through this pipeline end-to-end:

1. **Step-by-Step Manual Guidance:** Execute each stage individually from Stage 01 through Stage 10.
2. **Observe Friction:** Watch for tool quirks (yt-dlp cookies, ffmpeg filtergraph syntax, audio ducking thresholds, TTS pronunciation).
3. **Log Every Issue:** Immediately record every failure mode into [LESSONS.md](LESSONS.md).
4. **Surgically Revise:** Update the affected stage file or tool recipe before running the next stage.
5. **Freeze Baseline:** Once the pilot passes Stage 10 and Gate G4, copy stage files to a dated snapshot in `temp_can_del_later/` or record the verified release in `LESSONS.md`.

---

## 5. Architectural References

- **Standard Folder Specification:** [STANDARD_FOLDER_STRUCTURE.md](templates/STANDARD_FOLDER_STRUCTURE.md)
- **Umbrella Editor Skill:** [video-editor](../../.agents/skills/video-editor/SKILL.md)
- **Preset Calibration & Bake Skill:** [bake-preset](../../.agents/skills/bake-preset/SKILL.md)
- **Pipeline Runner & Routing:** [00_ORCHESTRATOR.md](00_ORCHESTRATOR.md)
