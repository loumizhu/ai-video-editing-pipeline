# Stage 05: Voiceover Preparation & Audio Synthesis

> **Voice engine order (owner rule, 2026-11-07):** 1) **Voicebox** with the **Jessica from Ihateediting** profile (channel voice) → 2) **ElevenLabs** (fallback) → 3) **Edge TTS** (last resort). **Never Windows TTS (SAPI / System.Speech / pyttsx3)**, not even for placeholder or scratch tracks. Use a silent or tone placeholder plus estimated timing instead of a robotic voice.


## Purpose
Prepare a clean narration-only copy, audition and synthesize master voiceover via local Voicebox (Qwen3-TTS), normalize to -16 LUFS, and generate sentence/word-level `timing.json` matching canonical Vcut §3.2. If Voicebox is offline, execute the technical bypass (estimated timing at 158 WPM with outline chapters + placeholder track) so production proceeds to FilmCraft. When real voiceover arrives (synthesized or owner-recorded), transcribe via Groq Whisper to measure real timing and process multi-take recordings through the cut contract.
Reference: [Vcut Step 02: Voice and Timing](../../../../Vcut/02_Voice_and_Timing.md) and [Vcut Data Contracts §3.2](../../../../Vcut/Vcut_Data_Contracts.md#32-timingjson).

> *Note: Plain-text project paths (e.g. `_pipeline/`, `06_script_edit_plan/`) are relative to working directory `Videos-Scripts/<NN>_<Slug>/`. Markdown links are relative to this stage file.*

## Inputs
- `06_script_edit_plan/Video_<NN>_Script_Draft_2.md` & `_pipeline/approvals/G3_script.md` (approved script; on retry, uses `Draft_3`).
- `_pipeline/03_hook_outline.md` (chapter structure and timestamps for text segmentation).
- `_pipeline/brief.md` (voice profile selection and delivery instructions).

## Outputs
- `06_script_edit_plan/Video_<NN>_Script_Draft_2_VoiceOver.md` (narration ONLY: zero title, zero headings, zero cues, zero signing; on retry, named `..._Draft_3_VoiceOver.md`).
- `06_script_edit_plan/chapters/chapter_<N>.md` (per-chapter spoken text split from VoiceOver.md).
- `_pipeline/05_pronunciation_lexicon.md` (phonetic respelling table for proper nouns).
- `_pipeline/05_voice_choice.md` (profile name, daemon preflight status, `voice_status: confirmed | pending_owner_recording`).
- `06_script_edit_plan/audition_sample.wav` (20–30s non-gate owner audition sample or placeholder).
- `06_script_edit_plan/chapters/chapter_<N>.wav` & `concat_list.txt` (per-chapter WAV renders and demuxer file).
- `06_script_edit_plan/take_01_raw.wav` (concatenated raw WAV prior to normalization).
- `06_script_edit_plan/take_01.wav` (concatenated master normalized WAV: 48kHz PCM, -16 LUFS, TP -1.8 dBTP, or calibrated placeholder).
- `06_script_edit_plan/words.json` (word-level timestamps from `transcribe_groq.py`; Revision 2026-11-01).
- `06_script_edit_plan/timing.json` (canonical Vcut §3.2 schema: `schema`, `start_s`/`end_s`, `lines`, `words`, `chapters`, `units`, list `qc`; `"estimated": true` if bypassed, transitioning to measured when real VO is transcribed; Revision 2026-11-01).
- `06_script_edit_plan/cuts.json` & `cuts_review.md` (cut contract produced by `make_cuts.py` if owner-recorded takes are used; Revision 2026-11-01).
- `06_script_edit_plan/whisper_diff.txt` & `06_script_edit_plan/loudness_readout.txt`.
- `_pipeline/BYPASS_LOG.md` (updated if Voicebox bypass was triggered).

## Executor
- **Worker / Tool:** Tool (`voicebox_cli.py` + `ffmpeg` + `transcribe_groq.py` + `make_cuts.py`) + Antigravity (runner & proof check).

## Tools
- `python ../Video_Pipeline/tools/estimate_timing.py` (reads sanitised `VoiceOver.md` and `--outline`, outputs `timing.json` matching Vcut §3.2 at 158 WPM).
- `python ../Video_Pipeline/tools/make_placeholder_vo.py` (generates calibrated 48kHz mono PCM silent WAV placeholder).
- `python .agents/skills/voicebox/scripts/voicebox_cli.py` (local Qwen3-TTS engine; 800-char chunks, 50ms crossfade).
- `python ../Video_Pipeline/tools/transcribe_groq.py` (**VERIFIED; Revision 2026-11-01**; word-timed ASR via Groq whisper-large-v3, gap repair, vocabulary corrections, rate-limit retry; replaces unverified local whisper).
- `python ../Video_Pipeline/tools/make_cuts.py` (**VERIFIED; Revision 2026-11-01**; frame-snapped cut contract with waveform audio energy analysis for multi-take voiceover cuts).
- `ffmpeg` (chapter concatenation via demuxer; loudness normalization via `loudnorm`: -16 LUFS, TP -1.8 dBTP, ebur128 with `peak=true`).

## Steps
1. **Text Sanitization & Pronunciation Lexicon:** Strip all cues, brackets, headings, and signatures into `Video_<NN>_Script_Draft_2_VoiceOver.md` before bypass evaluation so exact word counts exist. Create phonetic respelling table in `_pipeline/05_pronunciation_lexicon.md`.
2. **Daemon Preflight Check & Bypass Evaluation:** Run `python .agents/skills/voicebox/scripts/voicebox_cli.py --status`. If daemon is offline or owner records later: **DO NOT HALT.** Execute technical bypass from working directory `Videos-Scripts/<NN>_<Slug>/`:
   - Run `python ../Video_Pipeline/tools/estimate_timing.py --script "06_script_edit_plan/Video_<NN>_Script_Draft_2_VoiceOver.md" --outline "_pipeline/03_hook_outline.md" --out "06_script_edit_plan/timing.json" --wpm 158`. Output matches canonical `vcut.timing/1` (§3.2: `start_s`/`end_s`, `line_id`, `chapter_id`, list `qc`, `units`, `words`, `chapters`) with `"estimated": true`.
   - Run `python ../Video_Pipeline/tools/make_placeholder_vo.py --timing "06_script_edit_plan/timing.json" --out "06_script_edit_plan/take_01.wav" --sample-rate 48000 --channels 1` (or `ffmpeg -y -f lavfi -i anullsrc=r=48000:cl=mono -t <dur> -c:a pcm_s16le take_01.wav`).
   - Record `voice_status: pending_owner_recording` in `_pipeline/05_voice_choice.md`.
   - Log entry to `_pipeline/BYPASS_LOG.md`, mark Gate G3b deferred, and advance to Stage 06. Cloud TTS fallback remains prohibited.
3. **Voice Audition (If Online):** Render 20–30s sample to `audition_sample.wav` using default voice **"Jessica from Ihateediting"**.
4. **Chapter Text Splitting & Synthesis:** Split `VoiceOver.md` by outline chapters into `chapters/chapter_<N>.md`. Render each chapter via `voicebox_cli.py --file ... --profile "..." --out ...`.
5. **Concatenation & Normalization:** Concatenate chapter files via demuxer into `take_01_raw.wav` and normalize to -16 LUFS (TP -1.8 dBTP) *(Working directory: Videos-Scripts/<NN>_<Slug>/)*:
   ```bash
   ffmpeg -y -f concat -safe 0 -i "06_script_edit_plan/chapters/concat_list.txt" -c copy "06_script_edit_plan/take_01_raw.wav"
   ffmpeg -y -i "06_script_edit_plan/take_01_raw.wav" -af "loudnorm=I=-16:TP=-1.8:LRA=11:print_format=summary" -ar 48000 "06_script_edit_plan/take_01.wav"
   ffmpeg -y -i "06_script_edit_plan/take_01.wav" -af "ebur128=framelog=verbose:peak=true" -f null - 2> "06_script_edit_plan/loudness_readout.txt"
   ```
6. **Word Timing Transcription & Diff Proof (Revision 2026-11-01):** Transcribe `take_01.wav` via Groq whisper-large-v3 to produce word timestamps and text verification proof:
   ```bash
   python ../Video_Pipeline/tools/transcribe_groq.py --input "06_script_edit_plan/take_01.wav" --out "06_script_edit_plan/words.json" --corrections "06_script_edit_plan/transcript_corrections.json"
   ```
   `[TO BUILD]` Compare transcribed text against `VoiceOver.md` and write `whisper_diff.txt` reporting WER percentage.
7. **Timing Manifest & Cut Contract Generation (Revision 2026-11-01):**
   - `[TO BUILD]` **Measured Timing:** When real VO is transcribed, generate measured `06_script_edit_plan/timing.json` matching canonical Vcut §3.2 schema (`vcut.timing/1` with measured `start_s`/`end_s`, `line_id`, `chapter_id`, list `qc`, `units`, `words`, and `chapters`, setting `"estimated": false`). Currently handled via `estimate_timing.py` prior to transcription.
   - **Owner-Recorded VO Cut Contract:** If the owner provides raw multi-take voiceover recordings, formulate keep ranges in `06_script_edit_plan/keep.json` and generate the cut contract via `make_cuts.py`:
     ```bash
     python ../Video_Pipeline/tools/make_cuts.py --words "06_script_edit_plan/words.json" --keep "06_script_edit_plan/keep.json" --out "06_script_edit_plan/cuts.json" --review "06_script_edit_plan/cuts_review.md" --snap-audio "06_script_edit_plan/take_01_raw.wav"
     ```
     Inspect `cuts_review.md` for edit-point warnings (zero-pause edges, speech at cuts) before proceeding.
8. **Gate G3b Protocol:** If live narration synthesized, human audits audio and signs `_pipeline/approvals/G3b_voice.md`. If bypassed, G3b is deferred until real VO is supplied, transcribed, and re-timed.

## Acceptance Checklist
- [ ] `VoiceOver.md` sanitized and contains 100% spoken narration only (zero metadata, zero cues).
- [ ] `chapters/chapter_<N>.md` split by outline chapters; `concat_list.txt` generated.
- [ ] `_pipeline/05_voice_choice.md` records daemon status and voice status.
- [ ] `take_01.wav` produced (master normalized to -16 LUFS or calibrated 48kHz mono placeholder track).
- [ ] `words.json` generated via `transcribe_groq.py` with vocabulary corrections applied (Revision 2026-11-01).
- [ ] `timing.json` generated matching canonical Vcut §3.2 schema (`start_s`/`end_s`, `lines`, `words`, `chapters`, list `qc`, `units`; measured timing when real VO is used, estimated if bypassed).
- [ ] If owner-recorded VO used: `cuts.json` and `cuts_review.md` generated via `make_cuts.py` with waveform snapping verified (Revision 2026-11-01).
- [ ] Gate G3b signed (or formally marked deferred in `_pipeline/BYPASS_LOG.md`).

## Reviewer
- Claude Sonnet via [code.md](../../../.agents/skills/orchestrate/reviewers/code.md).

## Human Gate
- **Gate G3b (Final Narration Gate):** Approves master narration. Under bypass policy, G3b is deferred and must be signed before publishing (prior to Gate G4).

## Failure & Retry
- Voicebox offline -> Log to `_pipeline/BYPASS_LOG.md`, generate estimated `timing.json` + placeholder track, mark Gate G3b deferred, advance to Stage 06.
- Synthesis defect -> Re-render chapter with modified phonetic respelling in `_pipeline/05_pronunciation_lexicon.md`.
