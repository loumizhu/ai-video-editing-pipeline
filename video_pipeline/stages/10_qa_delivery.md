# Stage 10: Final Quality Assurance, Packaging Review & Delivery

## Purpose
Execute forensic quality assurance over the complete release package before human Gate G4 sign-off. Run five automated code QA verification scripts (`cut_audit.py`, `dead_air_qa.py`, `flash_scan.py`, `graphics_qa.py`, `still_hold_qa.py`), measure post-export loudness with explicit true peak detection, list packaging subject flags for the owner, enforce formal naming compliance, compile the final QA report (`_pipeline/10_final_qa_report.md`), and secure human Gate G4 approval. Following G4, consolidate learnings into the retrospective log.
Reference: [Vcut Step 05: Timeline Manifest and QA](../../../../Vcut/05_Timeline_Manifest_and_QA.md) and [Vcut Data Contracts §3.7](../../../../Vcut/Vcut_Data_Contracts.md#37-vcut_deliverablesjson).

> *Note: Plain-text project paths (e.g. `09_upload/`, `07_Video_Edit/`) are relative to working directory `Videos-Scripts/<NN>_<Slug>/`. Markdown links are relative to this stage file.*

## Inputs
- `07_Video_Edit/<slug>.fcproj` or DaVinci Resolve Studio project (assembled native timeline).
- `07_Video_Edit/preview_rough_cut.mp4` (preview video from assembly).
- `07_Video_Edit/graphics/*` (custom rendered graphic overlays).
- `06_script_edit_plan/cuts.json` (planned cuts list).
- `09_upload/*` (turnkey upload package from Stage 09: metadata, thumbnails, captions).
- `_pipeline/05_voice_choice.md` (voice status: confirmed or pending).

## Outputs
- `09_upload/final_master.mp4` (fully mastered 1080p60/30 H.264 video).
- `09_upload/master_loudness_readout.txt` (forensic EBU R128 audit executed on exported master with `peak=true`).
- `09_upload/qa_cut_audit.json` / `.md` (cut boundary audio clipping and discontinuity audit; Revision 2026-11-01).
- `09_upload/qa_dead_air.json` / `.md` (unintended pause and dead air audit > 0.6s; Revision 2026-11-01).
- `09_upload/qa_flash_scan.json` / `.md` (WCAG 2.3.1 photosensitive flash hazard screen; Revision 2026-11-01).
- `09_upload/qa_graphics.json` / `.md` (graphics canvas edge and 90% title-safe margin audit; Revision 2026-11-01).
- `09_upload/qa_still_hold.json` / `.md` (still-hold budget: no still run over its cap; Revision 2026-11-09).
- `07_Video_Edit/Export/edit_report.md` + `variation_log.json` (edit report with rationale; owner feedback block; Revision 2026-11-09).
- `_pipeline/10_final_qa_report.md` (forensic audit: audio levels, visual continuity, packaging subject flags, 5 QA tool proofs, and BYPASS_LOG summary).
- `06_script_edit_plan/NAMING_REVERENCE_CHECK.txt` (extended with grep proof on `captions.srt`).
- *(Human-produced: `_pipeline/approvals/G4_final_cut.md` signed by human operator only; records ready-to-publish vs editing-review status).*
- *(Post-G4 Retrospective Outputs):*
  - `10_process_and_learnings/CONCLUSION_SUMMARY.md` (project retro, metrics, loudness stats; cite Video 010).
  - `10_process_and_learnings/PROCESS_ENHANCEMENT_GUIDE.md` (distilled lessons merged into `LESSONS.md`).
  - `Videos-Scripts/_style_memory/style_memory.md` (owner feedback from `edit_report.md` section 6 converted to dated, bounded taste rules; Revision 2026-11-09).

## Executor & Reviewer Chain
- **Worker:** Antigravity (QA execution, master render, packaging consolidation), effort: medium.
- **Reviewer:** Claude Sonnet via [code.md](../../../.agents/skills/orchestrate/reviewers/code.md).
- **Final Delivery Rating:** Claude Opus reviews final QA report and delivers rating (1–10).

## Tools
- `ffmpeg` (master export with libx264/AAC 320k; forensic `-af ebur128=framelog=verbose:peak=true`).
- `python ../Video_Pipeline/tools/cut_audit.py` (**VERIFIED; Revision 2026-11-01**; audio discontinuity, click, and speech clipping auditor; exits 1 on FAIL, interior cuts only).
- `python ../Video_Pipeline/tools/dead_air_qa.py` (**VERIFIED; Revision 2026-11-01**; silence and dead air scanner).
- `python ../Video_Pipeline/tools/flash_scan.py` (**VERIFIED; Revision 2026-11-01**; photosensitive flash screening).
- `python ../Video_Pipeline/tools/graphics_qa.py` (**VERIFIED; Revision 2026-11-01**; canvas bounds and title-safe margin verifier; cap-height floor is guarded by EffectCraft build-time 45px rule).
- `python ../Video_Pipeline/tools/still_hold_qa.py` (**VERIFIED; Revision 2026-11-09**; still-hold budget on the plan plus a heuristic scene-change scan of the master; exits 1 on FAIL).
- `python ../Video_Pipeline/tools/color_script.py qa --video 09_upload/final_master.mp4` (**VERIFIED; Revision 2026-11-09**; colour script on the master: rendered strip row, `RENDER_DRIFT`, text contrast, skin, clipping; exits 1 on FAIL).
- PowerShell / Python (artifact SHA-256 calculation, cleanup automation).
- Grep script scanning `captions.srt` for formal naming compliance.

## Steps
1. **Master Video Export:** Render full master before gate sign-off:
   ```bash
   ffmpeg -y -i "07_Video_Edit/preview_rough_cut.mp4" -c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p -c:a aac -b:a 320k "09_upload/final_master.mp4"
   ```
2. **Forensic Loudness Verification (Post-Export):** Measure re-encoded master audio with explicit true peak detection:
   ```bash
   ffmpeg -i "09_upload/final_master.mp4" -af "ebur128=framelog=verbose:peak=true" -f null - 2> "09_upload/master_loudness_readout.txt"
   ```
   If live narration is present, verify dialogue at -16 LUFS and master true peak ceiling strictly below -1.5 dBTP. If `voice_status: pending_owner_recording`, mark dialogue loudness and ducking DEFERRED in the report and audit open music bed level only (-24 to -28 LUFS).
3. **Automated Forensic Code QA Suite (Revision 2026-11-01; 5th script added 2026-11-09):** Run the 5 mandatory code QA verification scripts against master deliverables. Run all five scripts to completion (do not halt on non-zero exit; `cut_audit.py` exits 1 on FAIL):
   ```bash
   # 1. Auditory cut boundary inspection (speech clipping, waveform step clicks, spectral jumps):
   python ../Video_Pipeline/tools/cut_audit.py --media "09_upload/final_master.mp4" --cuts "06_script_edit_plan/cuts.json" --out-json "09_upload/qa_cut_audit.json" --out-md "09_upload/qa_cut_audit.md"

   # 2. Dead air and excessive pause scan (> 0.6s):
   python ../Video_Pipeline/tools/dead_air_qa.py --media "09_upload/final_master.mp4" --out-json "09_upload/qa_dead_air.json" --out-md "09_upload/qa_dead_air.md"

   # 3. Photosensitive luminance flash hazard screening (WCAG 2.3.1):
   python ../Video_Pipeline/tools/flash_scan.py --media "09_upload/final_master.mp4" --out-json "09_upload/qa_flash_scan.json" --out-md "09_upload/qa_flash_scan.md"

   # 4. Graphic overlay placement and title-safe margin audit:
   python ../Video_Pipeline/tools/graphics_qa.py --input "07_Video_Edit/graphics" --out-json "09_upload/qa_graphics.json" --out-md "09_upload/qa_graphics.md"

   # 5. Still-hold budget (no image on screen past its cap) + rendered-master scene-change scan:
   python ../Video_Pipeline/tools/still_hold_qa.py --shot-plan "06_script_edit_plan/shot_plan.json" --assets-report "03_media/asset_audit.json" --media "09_upload/final_master.mp4" --out-json "09_upload/qa_still_hold.json" --out-md "09_upload/qa_still_hold.md"
   ```
   *Note: `cut_audit.py` audits interior edit points only; head and tail are checked manually. If `cut_audit.py` fails, the owner must decide between applying a 2-frame crossfade in the NLE or shifting the keep boundary.*
   Confirm zero dropped frames, lip-sync alignment, packaging subject flags listed for owner, and run formal naming grep on `09_upload/captions.srt` appending to `NAMING_REVERENCE_CHECK.txt`.
4. **Compile QA Report & Bypass Audit:** Record forensic results in `_pipeline/10_final_qa_report.md` including findings from the 5 QA tools. Summarize all entries from `_pipeline/BYPASS_LOG.md` for the owner, listing deferred tasks and re-time requirements.
5. **Opus Delivery Rating:** Claude Opus reviews deliverable package and scores 1–10. Score < 7 reopens weakest stage once.
6. **Human Gate G4 & Integrity Rule:** Human operator inspects `09_upload/final_master.mp4` and packaging.
   - **Publish-Ready Package Rule:** If `voice_status` is not `confirmed` or `timing.json` has `"estimated": true`, Gate G4 approves the video for **editing review only**. The pipeline **refuses to issue a publish-ready package** until the owner records real narration, executes the Re-time Procedure, and signs `_pipeline/approvals/G3b_voice.md`.
   - Once G3b is signed and audio re-timed, G4 grants full `ready_to_publish: true` sign-off.
7. **Post-G4 Learnings Consolidation (Video 010):** Following G4 sign-off, write `10_process_and_learnings/CONCLUSION_SUMMARY.md` and `10_process_and_learnings/PROCESS_ENHANCEMENT_GUIDE.md`. Merge any stage-level friction points into `Video_Pipeline/LESSONS.md`.
7b. **Feedback Loop (Revision 2026-11-09):** hand the owner `07_Video_Edit/Export/edit_report.md` (section 5 lists the five riskiest choices; section 6 is the feedback block). After the owner fills it, convert each point into a style-memory rule (`id`, one-line testable rule, evidence video + timestamp, strength `tried` / `preferred` / `always`, date) in `Videos-Scripts/_style_memory/style_memory.md` (template `templates/style_memory.md`): max 40 active rules, merge before adding, newest wins unless `always`, never relax a hard cap or a licence/truth rule. A rule confirmed on 3 videos is proposed for `bake-preset`; agents never edit presets or `always` rules without the owner. Optional Shorts / alternate cuts: [DERIVATIVES.md](../DERIVATIVES.md).
8. **Archive & Cleanup:** Move superseded draft files to `old/`. After operator approval, purge temporary scratch run directory (`temp_can_del_later/_runs/<date>_<task>/`).

## Acceptance Checklist
- [ ] `09_upload/final_master.mp4` exported and verified with zero video/audio defects.
- [ ] Post-export loudness audit confirms dialogue -16 LUFS and true peak <-1.5 dBTP (or marked DEFERRED if pending voiceover).
- [ ] 5 automated code QA scripts executed and reports generated: `cut_audit`, `dead_air_qa`, `flash_scan`, `graphics_qa` (Revision 2026-11-01) and `still_hold_qa` (Revision 2026-11-09; PASS or owner-waived).
- [ ] Colour (Revision 2026-11-09): `09_upload/qa_color.md` PASS; human checks done: strip shape matches the story, archival not stylised beyond recognition, master viewed on a phone at low brightness and on a monitor (subtle looks must neither vanish nor turn muddy).
- [ ] `BYPASS_LOG.md` summarized in `10_final_qa_report.md` with explicit owner hand-off.
- [ ] Publish-ready package refused if voiceover is pending or estimated (editing review approval permitted with separate ready-to-publish flag).
- [ ] Grep check on `captions.srt` confirms formal naming reverence in `NAMING_REVERENCE_CHECK.txt`.\n- [ ] `09_upload/` contains turnkey package: master MP4, master loudness readout, 5 QA reports, SRT, 4 thumbnails, metadata, and checklist.
- [ ] Claude Opus scores deliverable ≥7/10.
- [ ] Human operator signs `_pipeline/approvals/G4_final_cut.md`.
- [ ] Post-G4 `CONCLUSION_SUMMARY.md` and `PROCESS_ENHANCEMENT_GUIDE.md` completed, and the style memory updated from the owner's edit-report feedback.

## Reviewer & Rater
- Claude Sonnet reviews technical QA; Claude Opus delivers final release rating.

## Human Gate
- **Yes — Gate G4 (Final Cut & Delivery Gate):** Final human release gate. Release video cannot be uploaded without human signature.

## Failure & Retry
- If audio or video QA fails, reopen Stage 08 (Assembly). If Opus scores < 7, address flagged defects. Max 3 passes.

<span style="color: purple;">[AI Agent]</span>
