# Step 02: Voice & Timing

## Links
- **Hub:** [[Vcut_End_to_End_Pipeline_Architecture]] · **Contracts:** [[Vcut_Data_Contracts#3.2 timing.json]] · **Decision:** [[Vcut_Decision_Log#ADR-015 — Timing source]]
- **Previous:** [[01_Scriptwriting_Engine]] (after **G2**) · **Runs in parallel with:** 03a candidate search, 04a audio sourcing
- **Next:** [[03_Shot_Planning_and_Visuals]] (shot plan needs `timing.json`) · [[04_Music_SFX_and_Ducking]]

---

## Purpose
Produce the narration, the **master clock of the edit**, as per-unit audio files with exact unit boundaries
and frame-accurate word timing. Measure the real duration and send any chapter that misses its budget back
to the script.

## Inputs → Outputs
| In | Out |
|---|---|
| `script_manifest.json` (units, `text_spoken`, `token_map`), `project.yaml` `voice`, `channel_profile.yaml` (calibrated WPM, lexicon), `00_input/recordings/` if the owner uploaded narration | `voice/units/<unit_id>.wav` (48 kHz / 24-bit PCM), `voice/timing.json`, QC section, per-chapter durations; readable copies in `02_voice/` incl. `narration_full.wav` |

## Voice choices (setup form)
| Engine | Where it runs | Timing source | Notes |
|---|---|---|---|
| **Qwen3-TTS** (default, the owner's local set-up) | Local GPU | **Forced alignment** (no native timestamps in its README) | Apache-2.0 code; confirm the weights' licence on the model card before `final` use. Voice cloning only of the owner's own voice ([[Vcut_Decision_Log#ADR-008 — Narration voice]]) |
| Kokoro-82M | Local GPU | Native token timestamps (English) | Free, Apache-2.0 |
| ElevenLabs | Cloud, paid plan | Native (`/with-timestamps`) | Costs credits; counted against the budget |
| **My recording** | Uploaded at setup to `00_input/recordings/` | Forced alignment | See "Human-narration path" below; no TTS at all |

## Process
1. **Calibrate the voice (once per voice + engine + speed).** Synthesise a fixed calibration paragraph and store the measured WPM on spoken text in the channel profile. 01 budgets from this, not from a generic "140–160 WPM".
2. **Synthesise per unit** (a paragraph or short beat, not per sentence: strict per-sentence synthesis on context-free engines resets prosody every sentence).
   - Fixed voice and settings per project.
   - Lexicon applied on every call.
   - ElevenLabs: chain context with `previous_request_ids` (request stitching is not available on `eleven_v3`).
   - Qwen3-TTS: the same reference clip and seed for every unit of a project, so the voice stays consistent; units run one at a time on the GPU queue.
3. **Audio format policy.** Request PCM/WAV where the engine and plan allow (ElevenLabs PCM at 44.1 kHz needs the Pro tier or above; otherwise its MP3 must be decoded). Decode and resample **everything to 48 kHz / 24-bit WAV before any concatenation** (Kokoro and Edge-TTS output 24 kHz). **Never concatenate MP3s**: encoder priming offsets shift audio against timestamps.
4. **Pauses are inserted silence**, not markup: lengths come from the script (`pause_after_ms`: sentence / paragraph / chapter break). Unit offsets are then exact, in samples.
5. **Word timing ladder** ([[Vcut_Decision_Log#ADR-015 — Timing source]]):
   1. **TTS-native:** ElevenLabs `/with-timestamps` (character-level `alignment` / `normalized_alignment`, which can be null); Kokoro `KPipeline` token `start_ts` / `end_ts` (**English only**); Edge-TTS `boundary="WordBoundary"` (its default is SentenceBoundary; prototype only).
   2. **Forced alignment of the known spoken text:** WhisperX (wav2vec2), Montreal Forced Aligner, or ctc-forced-aligner with a **commercially licensed** model (its default MMS model is CC-BY-NC).
   3. **ASR fallback:** flagged `asr_fallback` and approximate.

   Native timings are mapped back to `line_id`/word through `token_map`, so "twenty twenty-four" points at "2024".
6. **QC: faster-whisper as a checker, not an aligner.** Transcribe each unit and compute the word error rate against `text_spoken`. A unit above threshold (e.g. WER > 5%) is re-synthesised with a respelling (**loop L3**, max 2 tries), then flagged as a red review marker. *(v1 called faster-whisper "forced alignment" with "millisecond-exact" timestamps. It is a transcriber with heuristic cross-attention/DTW word times, and it does not diarise. The requirement is now **frame-accurate: cuts ±1 frame, captions ±2 frames**.)*
7. **Voice stem levels.** Level-match units against each other, then normalise the dialogue stem to an **internal reference of about −18 LUFS integrated** (AES TD1008 speech guidance), with a **−3 dBTP** true-peak ceiling. Programme loudness is set **only at the final mix** ([[07_Human_Review_and_Delivery#Mix & loudness QC]]). *(v1 normalised the voice stem to −14 LUFS, a whole-programme reference.)* **No denoiser on TTS**: clean synthetic speech gains nothing from it.

### Duration re-fit (loop L1)
After synthesis, compare each chapter's real duration with its budget:
- **within ±5%:** accept;
- **otherwise:** adjust TTS speed within ±5%;
- **if still out:** send that chapter back to 01 for a trim or extension. Only the changed units are re-voiced, and the human approves the text diff (a light G2 re-approval).

At most 2 rounds, then report.

**Mode S (owner's script):** chapters have no word budget, so L1 runs only if the project sets a
`target_duration`, and it compares the **whole video**, not each chapter. It may adjust TTS speed within ±5%;
beyond that it **never trims the owner's text**. It reports the delta at a light G2 re-approval, with suggested
cuts (lowest-priority lines) the owner may accept through `vcut edit`, or the owner accepts the new length.

### Human-narration path (owner records the script)
The recording can be uploaded **at setup**, before anything else runs (the owner already has it), or after G2 if the owner wants to record from the locked script.
1. If recording after G2: export a per-unit teleprompter script from the locked manifest.
2. The recording is in `00_input/recordings/`: one file per unit, **or one continuous take per chapter** (more natural to read). A continuous take is forced-aligned to the chapter's text first and split into unit files at the aligned unit boundaries, so the contracts stay the same.
3. Noise reduction (DeepFilterNet, **48 kHz WAV only**; confirm the pretrained-weights licence before calling it commercial-safe) with an A/B check and wet/dry blend.
4. **Forced alignment** of the known text.

The output contracts are the same as for TTS. This is also the voice choice that most reduces the inauthentic-content risk ([[Vcut_Decision_Log#ADR-008 — Narration voice]]).

## Voice & likeness policy
- **Cloning:** only the **owner's own verified voice**. ElevenLabs Professional Voice Clones are limited to your own voice. Otherwise use library or stock voices. The channel profile records the voice id and its licence.
- Narrating with your own cloned voice is exempt from YouTube's synthetic-content disclosure. A synthetic voice presented as **another real person** is not exempt, and it is banned in Vcut.

## LLM vs deterministic code
All code. The LLM may only *suggest* respellings for QC failures, and those go through the lexicon at G2.

## Failure modes & fallbacks
| Failure | Response |
|---|---|
| Engine timeout or quota | Retry with backoff; resume per unit (cached by text + voice + settings hash) |
| Null native alignment | Forced-align that unit |
| WER over threshold after 2 tries | Keep it, add a red marker on that line for G4 |
| Chapter off budget after 2 rounds | Proceed and report the duration delta at G3 |

## Cost & time
- **Qwen3-TTS, Kokoro, own recording:** $0, local GPU queue.
- **ElevenLabs** (Multilingual v2, 1 credit per character): ≈40–60k credits per 45-minute video including regenerations. That is above Starter's 30k a month; Creator is 121k. **Paid tiers only**: the free tier has no commercial licence. Record `plan_tier_at_generation` per unit in the ledger.

## Tools
Qwen3-TTS (local, default) · Kokoro-82M (Apache-2.0, 8 languages / 54 voices in v1.0) · ElevenLabs (paid) · owner's recording · WhisperX / MFA / ctc-forced-aligner · faster-whisper (QC) · DeepFilterNet (human voice only) · FFmpeg (`ebur128` measuring, resampling).
**Edge-TTS: prototype only** (unofficial Microsoft endpoint, no commercial licence, breaks when its rotating token goes stale). **Adobe Podcast Enhance: manual tool, no public API.** Details: [[Vcut_Tool_Allowlist#Voice & timing]].

## Acceptance tests
- Σ unit durations + inserted pauses = timeline voice length, to the sample.
- 100% of `words[]` have `source` set; no `asr_fallback` in a `final`-tier run without a marker.
- Re-voicing one unit leaves every other unit file's hash unchanged.
