# Master Orchestrator Architecture & Production Protocol

## Purpose
The **00_ORCHESTRATOR** governs the deterministic end-to-end lifecycle of YouTube video essay production. It establishes strict role boundaries, file-based handoffs, resume state machines, bypass policies, and human approval gates across 11 discrete stages (plus sub-stage 06a, the beat map).

> **Absolute Rule:** All operational decisions, stage transfers, and gate evaluations are governed by files on disk. Zero reliance on conversational memory. If an agent crashes or restarts, state is fully reconstructed from disk.

---

## 1. Multi-Agent Routing & Review Topology

Production routes specialized intelligence across models to maximize factual fidelity, narrative tension, and editorial rigor, adhering strictly to the **Max 3 Passes** cross-model review loop:

| Stage | Stage Name | Assigned Worker Model | Reviewer Model | Review Criteria / Skill Reference |
|---|---|---|---|---|
| **01** | Scout & Validation | Antigravity *(Gemini Flash)* | Claude Sonnet | [research.md](../../.agents/skills/orchestrate/reviewers/research.md): Household-name anchor, spike ratio, RPM tier, live fact baseline. |
| **02** | Competitor DNA | Antigravity *(Gemini Flash)* | Claude Sonnet | [research.md](../../.agents/skills/orchestrate/reviewers/research.md): Gap analysis, top 250 comments, quote provenance in `QUOTE_PROOF.md`. |
| **03** | Hook & Outline | Claude Sonnet | Claude Opus | [script.md](../../.agents/skills/orchestrate/reviewers/script.md): Single held-back hook (first hook 20–40 s, fresh hook every ~60–90 s, reveal 85–95%), progressive open loops (≥5/20m), sensory anchors. *(Overridden to Sonnet writer / Opus reviewer per AGENTS.md)*. |
| **04** | Scriptwriting | Antigravity *(Draft)* → Opus *(Final)* | Claude Sonnet | [script.md](../../.agents/skills/orchestrate/reviewers/script.md): Café-friend tone, zero sensational adjectives, truth tiers, all 17 points of §10 Pre-Flight. Claude Opus reviews notes, rewrites final draft, and delivers separate 1–10 rating. |
| **05** | Voiceover & Timing | Tool (`voicebox_cli.py`) + Antigravity | Claude Sonnet | [code.md](../../.agents/skills/orchestrate/reviewers/code.md): Narration-only purity, pronunciation lexicon, -16 LUFS, Whisper WER diff. (Bypass active if Voicebox down). |
| **06a** | Beat Map *(Revision 2026-11-09)* | Antigravity *(Gemini 4 Argon, judgement task)* + code mapping | Claude Sonnet | Rubric in [PACING_AND_ENRICHMENT.md §4](PACING_AND_ENRICHMENT.md): emotion / intensity 1-5 / function / info_type / anchor_phrase per beat; intensity 5 <= 20 %; AI never writes timecodes. |
| **06b** | Colour Script *(Revision 2026-11-09)* | Antigravity *(Gemini 4 Argon, judgement task)* + `color_script.py` | Claude Sonnet | [COLOR_SCRIPT.md](COLOR_SCRIPT.md): `story_logic` + 4-8 phases by beat id, subtle (<= 3.0 dE), >= 20 s per phase, archival/document/face/B&W protection; `color_script.py plan` PASS, `qa` strip + phase sheet + 70 % strip reviewed. |
| **06** | Shot Planning | Antigravity *(Gemini Flash)* | Claude Sonnet | [code.md](../../.agents/skills/orchestrate/reviewers/code.md): Still-hold budget (`still_hold_qa.py` PASS: hard cap 6.0 s, soft 4.5 s needs events), preset cadence (3.5–4.5s cuts, 5.0–6.0s text cards), enrichment + rationale, motion library, `variation_report.py` PASS, toolkit schema fields. |
| **07** | Assets & Conform | Tool (`yt-dlp`/`ffmpeg`/Pillow) + Antigravity | Claude Sonnet | [code.md](../../.agents/skills/orchestrate/reviewers/code.md): 1080p/30fps Rec.709 conform, licensing ledger, audio manifest, Fair Use doctrine, `asset_audit.py` PASS (crop-aware resolution, duplicates, coverage). |
| **07b**| Graphics Build | Tool (`render_*.py` + `ffmpeg`) + Antigravity | Claude Sonnet | [code.md](../../.agents/skills/orchestrate/reviewers/code.md): Custom callouts, purposeful maps, article highlights, zero FilmCraft presets, manifest & contact sheet. |
| **08** | Assembly & Mix | Tool (`ffmpeg`/`filmcraft-cli`) + Antigravity | Claude Sonnet | [code.md](../../.agents/skills/orchestrate/reviewers/code.md): Native FilmCraft timeline project (`.fcproj`), 3-layer mix (-16 LUFS dialogue, ducked score -24/-28 dB, <-1.5 dBTP), zero third-party NLE. |
| **09** | Packaging & CTR | Antigravity + Grok *(Titles)* | Claude Sonnet | [packaging.md](../../.agents/skills/orchestrate/reviewers/packaging.md): 5-title cluster, 4 distinct thumbnail plates, 0.5s visual friction test, 120px check. |
| **10** | Final QA & Delivery| Tool (`ffmpeg`) + Antigravity | Claude Sonnet / Opus | [code.md](../../.agents/skills/orchestrate/reviewers/code.md): Forensic EBU R128 loudness on master, audio/video sync, packaging subject flag, Opus final rating. |

---

## 2. Directory Layout & Storage Rules

Every video project adheres to the exact layout established in Video 010 (`Videos-Scripts/<NN>_<Slug>/`), detailed in full in [STANDARD_FOLDER_STRUCTURE.md](templates/STANDARD_FOLDER_STRUCTURE.md):

> **Core Production Mandates:**
> 1. **No Third-Party NLE**: We do not use DaVinci Resolve Studio or Adobe Premiere Pro. All timeline authoring and video assembly are performed in **FilmCraft** via `filmcraft-cli` automation or the FilmCraft desktop app.
> 2. **Dedicated Source & Export Symmetry**: `07_Video_Edit/` and `08_thumbnail/` maintain strict internal separation between raw source/project assets (`Source/`) and rendered video/image outputs (`Export/`).

```text
Videos-Scripts/<NN>_<Slug>/
├── _pipeline/                                 ← Machine-readable pipeline tracking
│   ├── 00_STATUS.md                           ← Master tracking board (copied from templates/video_STATUS.md)
│   ├── brief.md                               ← Kick-off brief (7 owner decisions)
│   ├── BYPASS_LOG.md                          ← Log of all technical bypasses & deferred tasks
│   ├── 01_scout_dossier.md                    ← Stage 01 topic validation findings
│   ├── 02_dna_report.md                       ← Stage 02 audience gaps & retention leaks
│   ├── 02_sources.md                          ← Relative links to competitor downloads in Channel Niche & Audience
│   ├── 03_hook_outline.md                     ← Stage 03 hook engine & loop map
│   ├── 04_review_notes.md                     ← Sonnet line audit of script draft
│   ├── 04_opus_rating.md                      ← Opus final rating (1–10) and script sign-off
│   ├── 05_pronunciation_lexicon.md            ← Phonetic respellings for proper nouns
│   ├── 05_voice_choice.md                     ← Voice profile, daemon check, voice status
│   ├── 10_final_qa_report.md                  ← Stage 10 forensic QA metrics
│   └── approvals/                             ← Human approval records (signed by human only)
│       ├── G1_topic.md                        ← Topic gate approval
│       ├── G2_hook_outline.md                 ← Hook & outline gate approval
│       ├── G3_script.md                       ← Script gate approval
│       ├── G3b_voice.md                       ← Final narration gate approval (deferred if Voicebox down)
│       └── G4_final_cut.md                    ← Final release cut approval
├── 01_research/                               ← Research dossiers & primary verification
│   ├── FACT_BASELINE.md                       ← Step 0 live verified facts (dates, statements, charities)
│   └── QUOTE_PROOF.md                         ← Verbatim quotes, raw broadcast links, timestamps
├── 02_reference_videos/                       ← Competitor notes, transcripts & comment summaries
├── 03_media/                                  ← Video clips (raw & conformed), contact sheets
│   ├── VERIFIED_SOUNDBITES.md                 ← Broadcast audio/clip verification
│   ├── BEST_LINES_SELFCHECK.txt               ← Framing and eyes-on-speaker visual proof
│   └── scored_clips.wav                       ← Isolated dialogue quotes to be scored
├── 03_media/                                 ← Archival photography, document scans, cutout PNGs
│   ├── asset_audit.json / .md                 ← Asset audit (Stage 07): resolution after planned push, aspect, duplicates, coverage
│   ├── research_requests.json                 ← What to find next: beat, narration text, reason, shots needed
├── 05_music/                                  ← Music tracks, seamless loops, SFX
│   ├── primary_bed.wav                        ← Cataloged main score bed
│   └── 08_audio_manifest.json                 ← Track metadata, BPM loop math, licensing ledger
├── 06_script_edit_plan/                       ← Script drafts, timing, and shot plans
│   ├── Video_<NN>_Script_Draft_1.md           ← Working script drafts (numbered, never "FINAL")
│   ├── Video_<NN>_Script_Draft_2.md           ← Final script by Claude Opus
│   ├── Video_<NN>_Script_Draft_2_VoiceOver.md ← Pure narration only (no titles, no cues, no signing)
│   ├── visual_intents.md                      ← Visual intents tagged during outline & script (Stage 06)
│   ├── audition_sample.wav                    ← 20–30s non-gate owner audition sample (or placeholder)
│   ├── chapters/                              ← Per-chapter raw WAV renders and chapter_<N>.md splits
│   ├── concat_list.txt                        ← Chapter demuxer list for take_01_raw.wav
│   ├── take_01_raw.wav                        ← Concatenated raw voiceover before normalization
│   ├── take_01.wav                            ← Full concatenated master voiceover (-16 LUFS or scratch)
│   ├── whisper_diff.txt                       ← Automated Whisper diff with WER figure (or estimated note)
│   ├── loudness_readout.txt                   ← EBU R128 loudnorm readout proof
│   ├── timing.json                            ← Word/sentence timestamps (estimated: true if bypassed)
│   ├── shot_plan.json                         ← Preset-paced shot slots (documentary_standard 3.5–4.5s, text cards 5.0–6.0s) with toolkit fields, enrichments, motion picks, rationale
│   ├── beat_map.json                          ← Stage 06a: emotion / intensity / function / info_type per beat (templates/beat_map.example.json)
│   ├── color_script.json                      ← Stage 06b: story logic + colour phases by beat id (templates/color_script.example.json)
│   ├── color/                                 ← color_assign.json, color_plan.md (phase cards), looks/*.fcpreset + *.cube, strip.png, phase_sheet.png, strip_overgrade.png, qa_color.md
│   ├── qa_still_hold.json / .md               ← Still-hold budget report (Stage 06 gate; no still over its hard cap)
│   ├── variation_log.json / edit_report.md    ← Variation tracking + edit report with rationale (Stage 06 draft, regenerated at Stage 08)
│   ├── PREFLIGHT_01.md                        ← §10 Pre-flight checklist verification (17 points)
│   └── NAMING_REVERENCE_CHECK.txt             ← Grep check proof across scripts, cards, captions, meta
├── 07_Video_Edit/                             ← Video editing workspace (FilmCraft; NO NLE USED)
│   ├── PROGRESS.md                            ← Edit assembly progress, drift verification & stem logs
│   ├── Source/                                ← Video editor source workspace (FilmCraft project & inputs)
│   │   ├── <slug>.fcproj                      ← Native FilmCraft timeline project (primary target)
│   │   ├── vcut_timeline.json                 ← Canonical multitrack timeline (Vcut §3.5)
│   │   ├── concat_clips.txt                   ← Visual assembly concat demuxer list
│   │   ├── graphics/                          ← Custom-rendered overlay graphics (Stage 07b)
│   │   │   ├── graphics_manifest.json         ← Manifest of all custom overlay assets
│   │   │   ├── contact_sheet.png              ← Visual proof contact sheet of rendered overlays
│   │   │   └── *.png / *.mp4                  ← Individual callouts, maps, article highlights
│   │   ├── stems/                             ← Conformed audio stems & loudness reports
│   │   │   ├── dialogue_norm.wav              ← Dialogue stem normalized to -16 LUFS
│   │   │   ├── ducked_bed.wav                 ← Dynamic ducked music bed stem (-24 dB / -28 dB)
│   │   │   ├── mixed_audio.wav                ← 3-layer mix (dialogue + ducked music -24/-28 dB)
│   │   │   └── stem_loudness.txt              ← Stem loudness and relative offset verification readout
│   │   ├── proof_frames/                      ← Visual proof frames verifying cuts & text placement
│   │   ├── motion_log.json                    ← Motion library picks per still (builders)
│   │   ├── still_hold_warnings.json           ← Builder warning for any still over the hold cap
│   │   └── media/                             ← Local proxy media / cache used by FilmCraft
│   └── Export/                                ← Video editor exported renders
│       ├── preview_rough_cut.mp4              ← Preview rough cut for review (Gate G4)
│       ├── edit_report.md / variation_log.json ← Edit report with rationale + owner feedback block (feeds style memory)
│       ├── qa_still_hold.json / .md           ← Still-hold budget on the built cut (+ rendered scene-change scan)
│       ├── <slug>_assembly_v01.mp4            ← Versioned video exports from FilmCraft
│       └── loudness_readout.txt               ← Assembly mix loudness verification readout
├── 08_thumbnail/                              ← Thumbnail workpad
│   ├── PROGRESS.md                            ← Thumbnail progress & A/B/C concept log
│   ├── thumbnail_brief.md                     ← Visual brief (focal point, contrast, text ≤4 words)
│   ├── Source/                                ← Layered PhotoCraft (.pcraft) and PSD working files
│   ├── Export/                                ← 1280x720 finalized candidate design plates (v1..v4)
│   └── Mobile_Test/                           ← Mobile 120px legibility test render
├── 09_upload/                                 ← Turnkey release package
│   ├── final_master.mp4                       ← Published master video render
│   ├── master_loudness_readout.txt            ← Forensic EBU R128 master loudness verification readout
│   ├── captions.srt                           ← Subtitle captions
│   ├── thumb_1.png .. thumb_4.png             ← 4 pre-sized final thumbnails (1280x720)
│   ├── metadata.json                          ← 5-title cluster, description, tags, chapters
│   └── upload_checklist.md                    ← Human upload verification checklist
├── 10_process_and_learnings/                  ← Mandatory retro folder
│   ├── CONCLUSION_SUMMARY.md                  ← Video outcome, audio loudness stats, refinements
│   └── PROCESS_ENHANCEMENT_GUIDE.md           ← Friction points merged into Video_Pipeline/LESSONS.md
└── _archive/                                  ← Superseded drafts, outtakes, and obsolete files
    ├── superseded_scripts/
    └── rejected_media/
```

> **Colour Script Standard (Revision 2026-11-09):** the story-driven grade (phases, per-shot looks, protection of archival, documents, faces and B&W, colour QA) is defined in [COLOR_SCRIPT.md](COLOR_SCRIPT.md).

> **Pacing Standard (Revision 2026-11-09):** still-hold caps, enrichment ladder, beat map, pacing presets, motion library, variation tracking, asset audit, edit report and the style-memory feedback loop are defined in [PACING_AND_ENRICHMENT.md](PACING_AND_ENRICHMENT.md); derivatives (alternate cuts, Shorts, chapters, thumbnails) in [DERIVATIVES.md](DERIVATIVES.md). Channel-level taste lives in `Videos-Scripts/_style_memory/style_memory.md` and is loaded at Stages 03 and 06.

> **Competitor Video Storage Rule ([AGENTS.md §1](../../AGENTS.md)):** Raw competitor video downloads and full comment dumps are never stored in temporary directories. They are stored in `Channel Niche & Audience/<Niche_Folder>/<Video_Title>_[<Video_ID>]/` with `.mp4`, `metadata.json`, `comments_top250.json`, `transcripts/`, `audio/`, and forensic report. The pipeline file `_pipeline/02_sources.md` contains relative links to these folders.

---

## 3. Pipeline State Machine & Status Codes

Stage progress is tracked in `_pipeline/00_STATUS.md` via six strict states:

```text
       ┌───────────┐
       │ ⏳ Waiting │
       └─────┬─────┘
             │ (upstream output + gate approval verified via SHA-256)
             ▼
       ┌───────────┐
       │ ▶ Running │
       └─────┬─────┘
             │ (worker artifacts produced and validated)
             ▼
       ┌───────────┐
       │ 🔄 In Rev │
       └─────┬─────┘
             ├──▶ Rejected (Pass < 3) ──▶ ↩ Re-work ──▶ (Revises & increments pass count)
             │                                              │
             │                                              ▼
             │                                        ┌───────────┐
             │                                        │ ▶ Running │
             │                                        └───────────┘
             ├──▶ Rejected (Pass = 3) ──▶ ⚠️ Blocked ──▶ (Escalates to Opus Arbitration)
             │
             └──▶ Accepted ──▶ ✅ Done ──▶ [Next Stage: ⏳ Waiting]
```

---

## 4. Invalidation, Hash Verification & Resume Protocol

### Crash & Interruption Recovery Rules
1. **If status is `▶ Running` upon session restart:** The worker crashed or was aborted mid-step. The outputs on disk are untrusted. Re-run the stage from scratch.
2. **If status is `🔄 In Review` upon session restart:** The review was interrupted. Re-run the review against the existing output, preserving the current pass count.
3. **If status is `↩ Re-work`:** Worker executes the next pass addressing reviewer findings. Pass count increments.
4. **If status is `⏳ Waiting` but approval file exists:** Inspect `_pipeline/approvals/G<N>_*.md`. If the approved artifact's current SHA-256 matches the approval record, advance the stage board to `▶ Running`.

### Verification Command & Hash Recording
- Hashes are calculated and verified using deterministic SHA-256.
- **PowerShell Verification Command:**
  ```powershell
  Get-FileHash -Algorithm SHA256 "path/to/artifact"
  ```
- **Python Verification:**
  ```bash
  python -c "import hashlib, sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "path/to/artifact"
  ```
- All output hashes are recorded in `templates/stage_out.md` upon completion and mirrored into `_pipeline/00_STATUS.md`.

### Downstream Invalidation Rule
If an upstream file is modified after completion (e.g., editing `Video_<NN>_Script_Draft_2.md` after Stage 04 approval):
1. Compute the new SHA-256 hash.
2. The hash mismatch immediately invalidates all downstream stages (05 through 10).
3. The orchestrator resets all downstream stages in `00_STATUS.md` to `⏳ Waiting`.
4. Downstream artifacts must be re-executed to preserve end-to-end data integrity.

---

## 5. Cross-Model Review Protocol (Max 3 Passes)

- **Review Standards:** Scored strictly 1–5 across checklist items. Pass requires **zero scores below 4**.
- **Pass 1 Reject:** Reviewer lists specific actionable defects. Worker revises.
- **Pass 2 Reject:** Worker addresses remaining gaps.
- **Pass 3 Reject:** Orchestrator halts. Status transitions to `⚠️ Blocked`. Claude Opus arbitrates (accepts with noted caveats, orders single re-brief, or escalates to human operator).

---

## 6. Human Gate Protocol

Five human checkpoints ensure absolute editorial, acoustic, and ethical integrity:
1. **G1 (Topic & Feasibility Gate):** Post-Stage 01 (`_pipeline/approvals/G1_topic.md`).
2. **G2 (Hook & Architecture Gate):** Post-Stage 03 (`_pipeline/approvals/G2_hook_outline.md`).
3. **G3 (Script Gate):** Post-Stage 04 (`_pipeline/approvals/G3_script.md`).
4. **G3b (Final Narration Gate):** Mid-Stage 05 full narration WAV + Whisper diff + loudness readout (`_pipeline/approvals/G3b_voice.md`). **Deferred Rule:** If Voicebox is offline or the owner plans to record narration later, G3b is deferred, not skipped; the timeline proceeds to FilmCraft assembly with estimated timing and scratch audio. G3b must be approved prior to publishing (Gate G4).
5. **G4 (Final Cut & Delivery Gate):** Post-Stage 10 master render, master loudness readout, and packaging (`_pipeline/approvals/G4_final_cut.md`).

> **Absolute Constraint:** AI agents are strictly prohibited from generating, modifying, or signing gate approvals. Every gate record must be written and signed by the human operator with verified SHA-256 hashes recorded in `00_STATUS.md`. If rejected at any gate, the human operator creates a snapshot copy to `_archive/` with a note in `LESSONS.md`.

---

## 7. Bypass Policy & Unstoppable FilmCraft Timeline Protocol

### The Core Law
**Nothing technical may stop a video from reaching FilmCraft.** Any daemon, tool, asset, or network failure that would otherwise block timeline assembly must be bypassed with a documented fallback, logged in `_pipeline/BYPASS_LOG.md`, and summarized for the owner. Downstream stages proceed autonomously.

### Master Technical Bypass Table

| Failure Event | Stage | Automated Fallback Mechanism | Downstream Impact & Deferral | Deferred Work Required |
|---|---|---|---|---|
| **Voicebox Daemon Offline / Unavailable** | 05 | Generate `timing.json` with `"estimated": true` from word count at calibrated narration rate (158 WPM; Vcut `channel_profile.yaml`). Render silent/scratch placeholder WAV (`take_01.wav`) of exact estimated duration. Record `voice_status: pending_owner_recording` in `_pipeline/05_voice_choice.md`. | Pipeline proceeds uninterrupted through Stages 06, 07, 07b, and 08. **Gate G3b is deferred, not skipped.** | Execute defined **Re-time Procedure** when owner delivers narration; approve G3b before publishing. |
| **Whisper / Aligner Missing** | 05 | First-line fallback: execute `transcribe_groq.py` if `GROQ_API_KEY` is present (Revision 2026-11-01). If key is absent or offline, calculate linear word/sentence timestamps from script word counts or utilize owner-supplied audio with manual intervals. | Sentence timestamps in `timing.json` populated with `"alignment": "interpolated"`. | Run forced alignment or `transcribe_groq.py` audit when unblocked. |
| **Stock / Archival Asset Not Found** | 07 | Follow strict fallback chain: (1) First alternate candidate from shot plan → (2) Generated purposeful map or graphic card → (3) Stylized color/grain plate with citation. **Never leave slot empty.** | Conformed clip generated for 100% of required slots. | Swap plate for archival footage in FilmCraft inspector if desired. |
| **Custom Graphic Script Error** | 07b | Fallback chain: (1) Alternate simplified renderer (Pillow static 1080p card) → (2) Flagged placeholder overlay card with typography. | Overlay asset rendered and logged in `graphics_manifest.json`. | Re-render dynamic graphic and relink in FilmCraft project. |
| **yt-dlp / Network Failure** | 01, 02, 07 | Fallback to cached local assets in `Channel Niche & Audience/` or Wikimedia public domain archives. | Sourcing proceeds with documented offline sources. | Fetch broadcast video if higher quality is required later. |
| **Missing Music Bed** | 07, 08 | Select secondary cataloged score track from `05_music/` manifest or insert calibrated ambient tone bed. | Assembly mix proceeds with documented bed. | Swap music track on track A4 in FilmCraft timeline. |
| **FilmCraft Scripting CLI Error** | 08 | Fallback chain: (1) `filmcraft-cli import` of individual conformed clips → (2) Generate FCPXML/OTIO interchange package + FFmpeg preview render (`07_Video_Edit/Export/preview_rough_cut.mp4`). | Video preview and interchange package available for review. | Open interchange package directly in FilmCraft GUI. |

### Logging Schema (`_pipeline/BYPASS_LOG.md`)
Every applied technical bypass appends a structured record:
```markdown
### [YYYY-MM-DD HH:MM] Stage <NN> — Bypass: <Component_Name>
- **Failure:** <Root cause and error message>
- **Fallback Triggered:** <Exact fallback executed>
- **Downstream Artifact:** <Generated fallback file and SHA-256>
- **Deferred Gate/Action:** <Gate G3b / Retime / Relink requirement>
```
