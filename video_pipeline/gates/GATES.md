# Human Approval Gates (G1, G2, G3, G3b, G4: Five Gates)

Autonomous agents orchestrate research, drafting, and mechanical tooling, but **agents are strictly prohibited from generating, modifying, or signing approval records**. Human gates enforce editorial, ethical, and legal integrity.

> *Note: Plain-text project paths (e.g. `_pipeline/`, `06_script_edit_plan/`, `09_upload/`) are relative to working directory `Videos-Scripts/<NN>_<Slug>/`. Markdown links are relative to this file.*

---

## Gate Architecture Overview

| Gate | Stage Trigger | Gate Name | What Is Presented to Human | Saved Approval Record Path |
|---|---|---|---|---|
| **G1** | Post-Stage 01 | **Topic & Feasibility Gate** | `_pipeline/01_scout_dossier.md` & `01_research/FACT_BASELINE.md`: Proof of concept (≥2 channels 100k+), outlier spike (≥5x), RPM tier ($10–18), star/franchise fit. | `_pipeline/approvals/G1_topic.md` |
| **G2** | Post-Stage 03 | **Hook & Architecture Gate** | `_pipeline/03_hook_outline.md`: Single held-back hook engine, 0–60s crucible opening, loops map (≥5 loops / 20m), 85–95% reveal timing. | `_pipeline/approvals/G2_hook_outline.md` |
| **G3** | Post-Stage 04 | **Script Gate** | `06_script_edit_plan/Video_<NN>_Script_Draft_2.md` + Opus separate rating (1–10): Full script (2,700–4,500 words or 650–800 words for tribute profile), truth tiers, all 17 points of §10 Pre-Flight Checklist. | `_pipeline/approvals/G3_script.md` |
| **G3b** | Mid-Stage 05 (or Deferred) | **Final Narration Gate** | `06_script_edit_plan/take_01.wav` (full master WAV), `whisper_diff.txt` (WER + word check), `loudness_readout.txt` (-16 LUFS), and `audition_sample.wav`. *(Deferred if Voicebox offline; approved before publish)*. | `_pipeline/approvals/G3b_voice.md` |
| **G4** | Post-Stage 10 | **Final Cut & Delivery Gate** | `09_upload/final_master.mp4`, `09_upload/master_loudness_readout.txt`, `09_upload/captions.srt`, `09_upload/metadata.json`, 4 thumbnail plates, and `_pipeline/10_final_qa_report.md`. *(Separate editing-review vs ready-to-publish status)*. | `_pipeline/approvals/G4_final_cut.md` |

---

## Operator Hash Command

When verifying artifacts at any gate, run this PowerShell command to calculate the SHA-256 hash:
```powershell
Get-FileHash -Algorithm SHA256 "path/to/artifact"
```

---

## Detailed Gate Specifications

### G1: Topic & Feasibility Gate
- **Trigger:** Worker completes Stage 01 and passes Sonnet review.
- **Operator Review Checklist:**
  1. Does the subject center on a household-name star, creator, or titan?
  2. Proof of concept verified (≥2 competitor videos with 100k+ views on exact premise in last 4 months)?
  3. Outlier rule satisfied (<50k sub channel spiking ≥5x views)?
  4. RPM tier confirmed ($10–$15 Hollywood/Nostalgia or $12–$18 Corporate)?
  5. Live facts verified in `01_research/FACT_BASELINE.md`?
- **Action (Human Operator):** Human operator copies `templates/approval.md` to `_pipeline/approvals/G1_topic.md`, records SHA-256 hashes of `_pipeline/01_scout_dossier.md` and `01_research/FACT_BASELINE.md`, records hashes in `00_STATUS.md`, and marks `decision: APPROVED`. If rejected, snapshot copy to `old/` + note in `LESSONS.md`.

### G2: Hook & Architecture Gate
- **Trigger:** Sonnet completes Stage 03 and passes Opus review.
- **Operator Review Checklist:**
  1. Single held-back hook: Does the first hook land within 20–40 s (ONE core mystery, open by 60 s), with a fresh hook every ~60–90 s and no corpse cold opens or throat-clearing?
  2. Core reveal held back to 85–95% of estimated runtime?
  3. Progressive open loops: ≥5 loops per 20 min (or ≥3 loops for tribute profile), with ≥2 active across chapter boundaries?
  4. Scene anchors: Are physical rooms, concrete dates, documents, and sensory cues mapped for each beat?
- **Action (Human Operator):** Human operator creates `_pipeline/approvals/G2_hook_outline.md` with SHA-256 hash of `_pipeline/03_hook_outline.md`, records hash in `00_STATUS.md`, and marks `decision: APPROVED`. If rejected, snapshot copy to `old/` + note in `LESSONS.md`.

### G3: Script Gate
- **Trigger:** Antigravity drafts script, Sonnet reviews, and Claude Opus produces final script draft (`Video_<NN>_Script_Draft_2.md`) with a separate 1–10 quality rating.
- **Operator Review Checklist:**
  1. Opus rating: Does Claude Opus separate rating meet or exceed 8/10?
  2. Narration tone: Café-friend narration, fresh human details, understated peak moments?
  3. Adjective discipline: Zero sensational judgment words (*predatory, cruel, shocking, horrific*)?
  4. Truth tiers explicitly annotated throughout (`[documented]`, `[reported]`, `[alleged]`, `[speculative]`)?
  5. Quotes proven in `01_research/QUOTE_PROOF.md` against raw broadcast archives?
  6. Script passes **all 17 points of §10 Pre-Flight Checklist** in [STORYTELLING_WRITING_RULES.md](../../../Tips-Playbook/STORYTELLING_WRITING_RULES.md)?
  7. Strict numbered draft naming (`Draft_1`, `Draft_2`... never "FINAL")?
- **Action (Human Operator):** Human operator inspects script and Opus rating, creates `_pipeline/approvals/G3_script.md` with SHA-256 hash of `06_script_edit_plan/Video_<NN>_Script_Draft_2.md` and records Opus rating, records hash in `00_STATUS.md`, and marks `decision: APPROVED`. If rejected, snapshot copy to `old/` + note in `LESSONS.md`.

### G3b: Final Narration Gate (Mid-Stage 05 or Deferred)
- **Standard Trigger:** Full narration render completed, concatenated to `take_01.wav`, normalized to -16 LUFS, and verified via Whisper diff and loudness readout. *(Note: Short 20–30s audition is a non-gate owner confirmation recorded earlier in `_pipeline/05_voice_choice.md`).*
- **Bypass Deferral Rule:** If local Voicebox daemon is offline or the owner elects to record voiceover later, Stage 05 executes the technical bypass (estimated timing from word count at 158 WPM, placeholder audio track). Gate G3b is **deferred, not skipped**. Downstream production proceeds through Stages 06, 07, 07b, and 08 FilmCraft project assembly.
- **Publish Blocking:** Gate G3b must be audited, re-timed, and signed by the human operator before publishing and before Gate G4 ready-to-publish release approval.
- **Operator Review Checklist:**
  1. Audition profile and tone confirmed in `_pipeline/05_voice_choice.md`?
  2. Master narration `06_script_edit_plan/take_01.wav` verified for natural pacing, clear diction, and emotional warmth?
  3. `06_script_edit_plan/whisper_diff.txt` shows acceptable Word Error Rate (WER) and zero mangled proper nouns or formal names?
  4. `06_script_edit_plan/loudness_readout.txt` confirms -16 LUFS integrated loudness and true peak below -1.5 dBTP?
- **Action (Human Operator):** Human operator listens to master narration (or reviewed excerpts), creates `_pipeline/approvals/G3b_voice.md` with SHA-256 hashes of `06_script_edit_plan/take_01.wav`, `06_script_edit_plan/audition_sample.wav`, `06_script_edit_plan/whisper_diff.txt`, and `06_script_edit_plan/loudness_readout.txt`, records hashes in `00_STATUS.md`, and marks `decision: APPROVED`.

### G4: Final Cut & Delivery Gate
- **Trigger:** Stage 10 finishes forensic QA, renders `09_upload/final_master.mp4`, and compiles release package in `09_upload/`.
- **Publish-Ready vs Editing-Review Status:**
  - If voiceover is pending (`voice_status: pending_owner_recording`) or timing is estimated, Gate G4 approves the video for **editing review only**. A publish-ready package is refused until real narration arrives, re-time is executed, and Gate G3b is approved.
  - When voiceover is confirmed and G3b signed, Gate G4 grants full **Ready to Publish** approval.
- **Operator Review Checklist:**
  1. Audio mix: Dialogue -16 LUFS, background music ducked to -24 dB / -28 dB (verified via stem loudness in `07_Video_Edit/stem_loudness.txt` and `07_Video_Edit/loudness_readout.txt`), mix ceiling below -1.5 dBTP on `09_upload/master_loudness_readout.txt` and `final_master.mp4`? *(Exempt if pending voiceover; bed level checked)*.
  2. Packaging subject check (owner call): Is the packaging about the video's real subject? Shock-forward style is fine.
  3. Thumbnail friction: Passes 0.5s visual friction test, focal subject ≥40%, text ≤4 non-repeating words, readable at 120px?
  4. Master video: `09_upload/final_master.mp4` verified with zero black frames, audio-video sync locked?
  5. Turnkey package: Captions SRT, master loudness readout, 4 thumbnails, metadata with mid-rolls, and upload checklist present in `09_upload/`?
  6. Bypass Log: All items in `_pipeline/BYPASS_LOG.md` reviewed and acknowledged?
  7. Pacing (Revision 2026-11-09): `09_upload/qa_still_hold.md` is PASS (no still run over its hard cap; any `STILL_WAIVED` line was waived by the owner, who re-ran `still_hold_qa.py --allow-waivers`), and the owner has read `07_Video_Edit/Export/edit_report.md` section 5 "review these first" and filled section 6 feedback (feeds the style memory).
  8. Colour (Revision 2026-11-09): does `09_upload/color/strip.png` follow the story's shape, and does the master look right on your phone and your monitor? `qa_color.md` PASS.
- **Action (Human Operator):** Human operator inspects master video and package, creates `_pipeline/approvals/G4_final_cut.md` with SHA-256 hashes of `09_upload/final_master.mp4`, `09_upload/master_loudness_readout.txt`, `09_upload/captions.srt`, `09_upload/metadata.json`, and `_pipeline/10_final_qa_report.md`, records hashes in `00_STATUS.md`, and marks `decision: APPROVED` (specifying editing review or ready-to-publish). If rejected, snapshot copy to `old/` + note in `LESSONS.md`.

---

## Non-Bypassable Integrity Rules

While technical failures are bypassed to allow timeline assembly in FilmCraft, **editorial and ethical gates are NEVER bypassable**:
1. **Fact & Quote Verification:** Primary proof in `FACT_BASELINE.md` and `QUOTE_PROOF.md` is mandatory.
2. **Licensing & Fair Use:** Media cannot be released without an entry in `asset_registry.json`.
3. **Packaging Subject:** Packaging is owner-checked: shock-forward is fine as long as it is about the video's real subject. Agents flag concerns; they never block.
4. **Human Gate Signatures:** Only the human operator signs G1, G2, G3, G3b, and G4.
5. **G3b-Before-Publish Rule:** A video cannot receive ready-to-publish G4 release approval or be uploaded with scratch audio or estimated voiceover.

---

## Downstream Invalidation & Security Rule

1. If an approved artifact is modified after gate sign-off, its recalculated SHA-256 hash will mismatch the approval record.
2. The orchestrator immediately invalidates all downstream stages, setting their board status to `⏳ Waiting`.
3. Downstream production cannot proceed until the human operator signs an updated approval file.

<span style="color: purple;">[AI Agent]</span>
