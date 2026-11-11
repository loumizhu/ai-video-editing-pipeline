# STATUS — <NN>_<Video_Title>

- **Video Folder:** `Videos-Scripts/<NN>_<Video_Title>/`
- **Topic / Premise:** <One sentence premise centered on a household-name star/franchise>
- **Length Profile:** `documentary_long` (Default: 15 min–3 h, ~150 words/min; 45–120 min suits TV/older audiences) | `tribute_short` (Opt-in: 4:30–5:15, 650–800 words)
- **Target Runtime:** <e.g. 22:00 or 5:15>
- **Started:** <YYYY-MM-DD>
- **Orchestrator:** Claude Opus / Sonnet
- **Working Pipeline Dir:** `_pipeline/`

## Stage Board

| Stage | Name | Worker (Tool / Agent) | Reviewer | Pass | Status | Gate | Primary Artifact Output |
|---|---|---|---|---|---|---|---|
| 01 | Scout & Validation | Antigravity *(Gemini Flash)* | Claude Sonnet | 0/3 | ⏳ | G1 (Topic) | `_pipeline/01_scout_dossier.md` |
| 02 | Competitor DNA | Antigravity *(Gemini Flash)* | Claude Sonnet | 0/3 | ⏳ | — | `_pipeline/02_dna_report.md` |
| 03 | Hook & Outline | Claude Sonnet | Claude Opus | 0/3 | ⏳ | G2 (Hook) | `_pipeline/03_hook_outline.md` |
| 04 | Scriptwriting | Antigravity *(Draft)* $\rightarrow$ Opus *(Final)* | Claude Sonnet | 0/3 | ⏳ | G3 (Script) | `06_script_edit_plan/Video_<NN>_Script_Draft_2.md` |
| 05 | Voiceover & Timing | Tool (`voicebox_cli.py`) + Antigravity | Claude Sonnet | 0/3 | ⏳ | G3b (Final Narration Gate) | `06_script_edit_plan/take_01.wav` & `timing.json` |
| 06 | Shot Planning | Antigravity *(Gemini Flash)* | Claude Sonnet | 0/3 | ⏳ | — | `06_script_edit_plan/shot_plan.json` |
| 07 | Assets & Conform | Tool (`yt-dlp`/`ffmpeg`/Pillow) + Antigravity | Claude Sonnet | 0/3 | ⏳ | — | `03_media/` & `03_media/` conformed |
| 07b| Graphics Build | Tool (`render_*.py` + `ffmpeg`) + Antigravity | Claude Sonnet | 0/3 | ⏳ | — | `07_Video_Edit/Source/graphics/` & manifest |
| 08 | Assembly & Mix | Tool (`ffmpeg`/`filmcraft-cli`) + Antigravity | Claude Sonnet | 0/3 | ⏳ | — | `07_Video_Edit/Source/<slug>.fcproj` & preview |
| 09 | Packaging & CTR | Antigravity + Grok *(Titles)* | Claude Sonnet | 0/3 | ⏳ | — | `09_upload/metadata.json` & `captions.srt` |
| 10 | Final QA & Delivery| Tool (`ffmpeg`) + Antigravity | Claude Sonnet / Opus | 0/3 | ⏳ | G4 (Final Cut & Delivery Gate)| `09_upload/final_master.mp4` |

**Status Icons:** `⏳` waiting · `▶` running · `🔄` in review · `↩` rejected/re-work · `✅` accepted · `⚠️` escalated/blocked

## Technical Bypasses Logged
*(Bypasses recorded from `_pipeline/BYPASS_LOG.md`)*
- None active.

## Artifact Checksums (SHA-256)
- `_pipeline/brief.md`: `<sha256>`
- `_pipeline/01_scout_dossier.md`: `<sha256>`
- `_pipeline/approvals/G1_topic.md`: `<sha256>`
- `01_research/FACT_BASELINE.md`: `<sha256>`
- `_pipeline/02_dna_report.md`: `<sha256>`
- `_pipeline/03_hook_outline.md`: `<sha256>`
- `_pipeline/approvals/G2_hook_outline.md`: `<sha256>`
- `_pipeline/04_review_notes.md`: `<sha256>`
- `06_script_edit_plan/Video_<NN>_Script_Draft_2.md`: `<sha256>`
- `_pipeline/approvals/G3_script.md`: `<sha256>`
- `06_script_edit_plan/Video_<NN>_Script_Draft_2_VoiceOver.md`: `<sha256>`
- `06_script_edit_plan/audition_sample.wav`: `<sha256>`
- `06_script_edit_plan/take_01.wav`: `<sha256>`
- `06_script_edit_plan/whisper_diff.txt`: `<sha256>`
- `_pipeline/approvals/G3b_voice.md`: `<sha256>`
- `06_script_edit_plan/timing.json`: `<sha256>`
- `06_script_edit_plan/shot_plan.json`: `<sha256>`
- `05_music/08_audio_manifest.json`: `<sha256>`
- `07_Video_Edit/Source/graphics/graphics_manifest.json`: `<sha256>`
- `07_Video_Edit/Source/graphics/contact_sheet.png`: `<sha256>`
- `07_Video_Edit/Source/<slug>.fcproj`: `<sha256>`
- `07_Video_Edit/Source/concat_clips.txt`: `<sha256>`
- `07_Video_Edit/Source/stems/stem_loudness.txt`: `<sha256>`
- `07_Video_Edit/Source/vcut_timeline.json`: `<sha256>`
- `07_Video_Edit/Export/preview_rough_cut.mp4`: `<sha256>`
- `07_Video_Edit/Export/loudness_readout.txt`: `<sha256>`
- `09_upload/captions.srt`: `<sha256>`
- `09_upload/metadata.json`: `<sha256>`
- `09_upload/final_master.mp4`: `<sha256>`
- `09_upload/master_loudness_readout.txt`: `<sha256>`
- `_pipeline/10_final_qa_report.md`: `<sha256>`
- `_pipeline/approvals/G4_final_cut.md`: `<sha256>`
- `10_process_and_learnings/CONCLUSION_SUMMARY.md`: `<sha256>`
- `10_process_and_learnings/PROCESS_ENHANCEMENT_GUIDE.md`: `<sha256>`

## Execution Log
- `<YYYY-MM-DD HH:MM>` Initialized video project status board.
