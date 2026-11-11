# Standard Video Project Folder Structure (YTube_Channel)

## Purpose & Core Philosophy
This document codifies the standard folder structure for every video essay produced in `YTube_Channel/Videos-Scripts/<NN>_<Slug>/`. 
Based on field-tested learnings from **Video 010 (Patrick Stewart Homage)** and the **Faceless YouTube Markdown Video Pipeline**, this layout delivers:
1. **Human Legibility**: A clean, chronological 11-stage layout (00 to 10) matching the real-world production lifecycle, with zero root clutter.
2. **AI Agent Determinism**: Predictable, immutable file-based handoffs where output files of Stage $N$ become input files of Stage $N+1$.
3. **Dedicated Workpad Symmetry (`Source/` & `Export/`)**: Stages that involve editing and rendering—specifically `07_Video_Edit/` and `08_thumbnail/`—strictly isolate raw editable source files from rendered export deliverables.
4. **No Third-Party NLE Mandate**: Traditional heavy NLEs (Adobe Premiere Pro, DaVinci Resolve Studio) are **not** used. All video editing and timeline assembly are driven by **FilmCraft** (via `filmcraft-cli` automation or FilmCraft GUI) alongside deterministic Python/FFmpeg tooling.

---

## Master Directory Layout

```text
Videos-Scripts/<NN>_<Slug>/
│
├── 00_planning/                                 ← Master control, brief, approvals & review log
│   ├── 00_MASTER_PLAN.md                        ← Premise, runtime, hook engine, held-back reveal & task schedule
│   ├── 01_ORCHESTRATION_LOG.md                  ← Chronological log of multi-agent tasks & state machine transitions
│   ├── BRIEF.md                                 ← 7 owner briefing decisions (topic, tone, reveal, faces, music)
│   ├── STATUS.md                                ← Live tracking board across stages 01–10 (video_STATUS.md)
│   ├── BYPASS_LOG.md                            ← Explicit log of any technical fallbacks / deferred gates
│   ├── approvals/                               ← Human sign-off records (Human-only: G1, G2, G3, G3b, G4)
│   │   ├── G1_topic.md
│   │   ├── G2_hook_outline.md
│   │   ├── G3_script.md
│   │   ├── G3b_voice.md
│   │   └── G4_final_cut.md
│   └── reviews/                                 ← Cross-agent review passes (e.g. T1_review_v1.md, T4_review_v2.md)
│
├── 01_research/                                 ← Source verification & factual baseline
│   ├── PROGRESS.md                              ← Stage status, tools used, and deliverables
│   ├── FACT_BASELINE.md                         ← Step-0 verified dates, statements, bios, and charity anchors
│   ├── QUOTE_PROOF.md                           ← Verbatim quotes, raw broadcast links, and exact timestamps
│   ├── sources.csv                              ← Structured catalog of primary research sources
│   └── articles/                                ← Clean markdown extracts or saved PDFs of primary articles
│
├── 02_reference_videos/                         ← Competitor intelligence & YouTube niche trends
│   ├── PROGRESS.md
│   ├── SYNTHESIS.md                             ← Retention leaks, commentary gaps, and competitor structural analysis
│   ├── references.csv                           ← Competitor video links, runtimes, view velocity & outlier spikes
│   └── transcripts/                             ← Cleaned word transcripts with timestamped soundbite cues
│
├── 03_media/                                    ← Video footage & dialogue soundbites
│   ├── PROGRESS.md
│   ├── VERIFIED_SOUNDBITES.md                   ← Log of selected dialogue soundbites & attribution proof
│   ├── BEST_LINES_CLIPLIST.csv                  ← Exact In/Out timestamps, speaker, framerate, and cut notes
│   ├── _sources/                                ← Full-length raw downloads (yt-dlp)
│   └── _cuts/                                   ← Conformed, frame-accurate trimmed clips (1080p CFR Rec.709)
│
├── 03_media/                                   ← Archival photos, portraits & graphic stills
│   ├── PROGRESS.md
│   ├── 01_early_life/                           ← Categorized chronological photo bins
│   ├── 02_career_milestones/                    ← Role/event specific stills
│   ├── 03_portraits_hero/                       ← High-resolution master subject portraits
│   ├── 04_costars_and_guests/                   ← Context & co-star stills (for video & thumbnail pairing)
│   ├── cutouts/                                 ← Transparent PNGs (produced by local bg-remove ensemble)
│   ├── contact_sheets/                          ← Multi-image grid visual proofs for rapid curation
│   └── _review/                                 ← Image curation log, KEEP / REJECT lists, and rejected bin
│
├── 05_audio/                                    ← Music score, sound effects & voice stems
│   ├── PROGRESS.md
│   ├── AUDIO_MANIFEST.json                      ← Track names, BPM, key, license proof & ducking parameters
│   ├── music/                                   ← Curated royalty-free score beds (e.g. Scott Buckley tracks)
│   ├── sfx/                                     ← Whooshes, cinematic hits, tape stops, room tones
│   └── voiceover/                               ← (Optional) Voicebox neural TTS stems, normalized to -16 LUFS
│
├── 06_script_and_edl/                           ← Narrative architecture & timing
│   ├── PROGRESS.md
│   ├── Script_Draft_01.md                       ← Working narrative draft with café-friend tone
│   ├── Script_Draft_02_FINAL.md                 ← Locked script passing all 17 points of §10 Pre-Flight
│   ├── VoiceOver_Clean.md                       ← Pure narration text (no brackets, no cues) for TTS/recording
│   ├── TextCards_Manifest.md                    ← On-screen typographic cards (titles, dates, quotes)
│   ├── Shot_Plan.csv                            ← 3.5–4.5s visual slots mapped against timeline seconds
│   └── PREFLIGHT_CHECKLIST.md                   ← Verification checklist proof across script, cards, and meta
│
├── 07_Video_Edit/                               ← Video editing workspace (FilmCraft; NO NLE USED)
│   ├── PROGRESS.md                              ← Edit assembly progress, drift verification & stem logs
│   ├── Source/                                  ← Editor project workspace & inputs for FilmCraft
│   │   ├── <slug>.fcproj                        ← Native FilmCraft timeline project (primary target)
│   │   ├── <slug>.fcproj.bak                    ← FilmCraft auto-save backup
│   │   ├── vcut_timeline.json                   ← Canonical multitrack timeline (Vcut §3.5)
│   │   ├── concat_clips.txt                     ← FFmpeg demuxer list for visual assembly
│   │   ├── graphics/                            ← Custom-rendered overlay graphics (Stage 07b)
│   │   │   ├── graphics_manifest.json           ← Manifest of all custom overlay assets
│   │   │   ├── contact_sheet.png                ← Visual proof contact sheet of rendered overlays
│   │   │   └── *.png / *.mp4                    ← Individual callouts, maps, article highlights
│   │   ├── stems/                               ← Conformed audio stems & loudness reports
│   │   │   ├── dialogue_norm.wav                ← Dialogue stem normalized to -16 LUFS
│   │   │   ├── ducked_bed.wav                   ← Dynamic ducked music bed stem (-24 dB / -28 dB)
│   │   │   ├── mixed_audio.wav                  ← 3-layer master audio mix
│   │   │   └── stem_loudness.txt                ← Stem loudness and relative offset verification
│   │   ├── proof_frames/                        ← Visual proof keyframes verifying cuts & safe margins
│   │   └── media/                               ← Local proxy media / cache used by FilmCraft
│   └── Export/                                  ← Video editor exported renders
│       ├── preview_rough_cut.mp4                ← Preview rough cut render for human gate G4 sign-off
│       ├── <slug>_assembly_v01.mp4              ← Intermediate / versioned assembly exports
│       └── loudness_readout.txt                 ← Assembly mix loudness verification readout
│
├── 08_thumbnail/                                ← Packaging visual design & mobile tests
│   ├── PROGRESS.md                              ← Thumbnail progress & A/B/C concept log
│   ├── THUMBNAIL_BRIEF.md                       ← Focal subject, high contrast, text ≤ 4 words, emotion
│   ├── Source/                                  ← Raw PSDs, PhotoCraft templates, layered elements
│   ├── Export/                                  ← 1280x720 finalized candidate plates (v1, v2, v3, v4)
│   └── Mobile_Test/                             ← 120px scale simulation & mock mobile feed visual checks
│
├── 09_upload/                                   ← Turnkey final release package
│   ├── FINAL_MASTER_<Slug>.mp4                  ← Final 1080p/4K master export
│   ├── Captions.srt                             ← Frame-accurate subtitles/captions
│   ├── METADATA.md                              ← 5-title cluster, description, chapters, tags, charity links
│   ├── METADATA.json                            ← Machine-readable packaging for direct YouTube Studio API
│   ├── UPLOAD_CHECKLIST.md                      ← Final pre-publish verification sheet
│   └── thumbnails/                              ← Selected final thumbnail images ready for YouTube upload
│
├── 10_process_and_learnings/                    ← Post-mortem & preset calibration
│   ├── CONCLUSION_SUMMARY.md                    ← Video analytics, runtime metrics, audio loudness report
│   └── LESSONS_TO_BAKE.md                       ← Specific edits/rules to merge back into Video_Pipeline/LESSONS.md
│
└── _archive/                                    ← Outtakes & superseded drafts (replaces loose old/ folders)
    ├── superseded_scripts/
    └── rejected_media/
```

---

## Detailed Rules & Conventions

### 1. The `07_Video_Edit/` Rule: `Source/` vs `Export/`
- **No Third-Party NLE**: Production does not rely on DaVinci Resolve Studio or Adobe Premiere Pro. All timeline authoring is executed in **FilmCraft** via `filmcraft-cli` or the FilmCraft desktop interface.
- **`07_Video_Edit/Source/`**: Contains everything FilmCraft needs to open, edit, and reconstruct the timeline:
  - The master `.fcproj` project file.
  - Custom graphic overlays (`graphics/`) generated from house presets.
  - Conformed audio stems (`stems/`), ducked music beds, and dialogue stems.
  - Timeline alignment files (`vcut_timeline.json`, `concat_clips.txt`).
  - Visual verification proof sheets (`proof_frames/`).
- **`07_Video_Edit/Export/`**: Contains only the resulting video renders from FilmCraft:
  - Rough cut preview (`preview_rough_cut.mp4`) used for Gate G4 review.
  - Master candidate renders prior to final packaging into `09_upload/`.

### 2. Symmetry with `08_thumbnail/`
Following the same clean architecture, `08_thumbnail/` separates layered working files from release assets:
- **`08_thumbnail/Source/`**: Master PhotoCraft (`.pcraft`) and Photoshop (`.psd`) layered project files with live smart objects, adjustment layers, and layer masks.
- **`08_thumbnail/Export/`**: 1280x720 RGB candidate plates for A/B testing (`thumb_v1.png`, `thumb_v2.png`, etc.).

### 3. The `PROGRESS.md` Contract
Every numbered stage folder must contain a `PROGRESS.md` file. It allows any human editor or AI agent to instantly determine:
- **Status**: `[WAITING | IN_PROGRESS | READY_FOR_REVIEW | PASSED]`
- **Active Worker & Reviewer**: The assigned models and tools.
- **Key Artifacts Produced**: Direct paths to output files.
- **CLI Commands Executed**: Exact command lines (e.g. `ffmpeg`, `filmcraft-cli`, `yt-dlp`).

### 4. Zero Root-Level Clutter Rule
- Stray image downloads must never sit in the root (unlike Video 010 where loose images appeared in root `Images/`). They belong in `03_media/` under specific subfolders.
- Temporary or scratch scripts run only in `temp_can_del_later/`.
- Obsolete drafts or cutaways move into `_archive/` rather than floating in loose or unorganized directories.
