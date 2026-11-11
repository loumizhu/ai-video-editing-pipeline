# Step 05: Timeline Manifest, QA & Preview Render

## Links
- **Hub:** [[Vcut_End_to_End_Pipeline_Architecture]] · **Contracts:** [[Vcut_Data_Contracts#3.5 vcut_timeline.json — canonical]], [[Vcut_Data_Contracts#3.6 qa_report.json]]
- **Decisions:** [[Vcut_Decision_Log#ADR-003 — Canonical timeline artifact]], [[Vcut_Decision_Log#ADR-017 — Preview render]], [[Vcut_Decision_Log#ADR-021 — One editor: everything native and editable]]
- **Previous:** [[03_Shot_Planning_and_Visuals]] (`cut_list.json`), [[04_Music_SFX_and_Ducking]] (`audio_plan.json`), [[02_Voice_and_Timing]] (`timing.json`)
- **Next:** [[06_NLE_Adapters]] ∥ 05b preview render (below) → [[07_Human_Review_and_Delivery]]

---

## Purpose
**Compile** every upstream decision into the one canonical timeline. This step is deterministic: no LLM,
and the same inputs always give byte-identical output. It also **exports** OTIO and FCPXML from that
timeline, and **validates** it so defects are caught by a machine, not by a human scrubbing 45 minutes.
*Renamed from "Vcut JSON & OTIO Blueprint": v1 presented JSON and OTIO as co-equal sources of truth, which drift.*

## Inputs → Outputs
| In | Out |
|---|---|
| `cut_list.json`, `audio_plan.json`, `timing.json`, `asset_registry.json`, `script_manifest.json` (chapters), `brief.yaml` (budget), `channel_profile.yaml` (delivery), `project.yaml` (`editor.target`), effects library (`preset.yaml`) | `timeline/vcut_timeline.json` (canonical) |
| | `timeline/exports/vcut.otio`, `timeline/exports/vcut.fcpxml` (FCPXML 1.10; derived, never edited) |
| | `qa/qa_report.json`, `delivery/credits_draft.txt`, `delivery/disclosure.json` |
| 05b (only when the editor cannot render the preview itself): `vcut_timeline.json`, conformed media, `qa_report.json` | `preview/rough_cut.mp4` |

## Process
1. **Quantise.** One function resolves every anchor `(line_id, word, edge, offset_frames)` to an integer frame at the timeline rate, using the rounding rule in [[Vcut_Data_Contracts#1.3 Time model]]. Seconds never reach the timeline.
2. **Assemble.**
   - Tracks in fixed order (V1 base layer · V2 B-roll · V3 titles · V4 overlay clips · A1 voice per unit · A2 sync · A3 SFX · A4 music · A5 un-ducked music if baked).
   - Clips with `source.in/out` in their own native rate; transitions between adjacent clips only; fades as clip properties.
   - The `ducking` block, the `delivery` block, and the `compliance` block.
   - **Presets for the chosen editor:** each title, effect, motion and transition is written as its preset id + values; 05 checks that the preset has an implementation for `editor.target` and that its capability-matrix cell is ✔ ([[Vcut_Decision_Log#ADR-021 — One editor: everything native and editable]]). Ducking gets its native carrier (Resolve Ducker, FilmCraft keyframes) or the baked stem ([[Vcut_Decision_Log#ADR-004 — Carriers for effects the Resolve API cannot set]]).
   - **SFX sync for presets:** paired SFX frames are computed from the preset's declared event offsets.
3. **Markers.** Typed by `kind`; colour is derived per editor (chapter = Blue, review = Yellow, licence = Red / FilmCraft Rose, info = Green). Each has an `id` (carried into Resolve `customData`, FilmCraft marker comment) and `duration_frames ≥ 1`.
   - **Chapter** markers come from script chapters.
   - **Review** markers come from low-confidence slots, QC failures and QA warnings.
   - **Licence** markers come from assets that need a human rights look.
4. **Compliance.**
   - Compute `disclosure_required` from the ledger's synthetic flags ([[Vcut_Decision_Log#ADR-014 — AI-content disclosure]]).
   - Generate `credits_draft.txt` from the ledger: CC-BY credits are **required** (title, author, link, licence); Pexels and Pixabay credits are courtesy.
5. **Exports** (for the backup package and audit; the editor itself is built from `vcut_timeline.json` by 06).
   - **OTIO** via the core `opentimelineio` library. Vcut data goes under `metadata["vcut"]`. Marker colours map lossily (OTIO 0.18 has 11 names, Resolve 16).
   - **FCPXML 1.10** from **Vcut's own writer**: Resolve exports 1.9/1.10 and FilmCraft's README lists 1.9–1.11, so 1.10 is read by both. Media paths are written relative to the package folder (06). Since OTIO 0.17 the FCPXML adapter lives outside core. The community `otio-fcpx-xml-adapter` is not in the official plugin bundle and has had no release since 2023.
   - **Round-trip test:** compile → export → re-read → compare every clip's record/source range.
6. **Validate** (below), then write `qa_report.json`. **Any error blocks 05b and 06** and routes back to the owning stage (loop L4). Warnings become yellow markers and appear on the G4 review page.

## 05b — Preview render
A watchable rough cut ([[Vcut_Decision_Log#ADR-017 — Preview render]]). **When the chosen editor can render headless (FilmCraft; Resolve Studio), 06 renders the preview from the built timeline instead, so it shows the real titles and effects; 05b is then skipped.** On free Resolve, 05b runs in parallel with 06 as below.
1. **Input:** `vcut_timeline.json` and the conformed media. Never the FCPXML, so the preview shows what Vcut *meant*, and any difference after NLE import is the NLE's.
2. **Render per chapter** with FFmpeg (one filter graph per chapter, then a stream-copy concat), so a 45-minute video never needs a single giant graph, and a changed chapter re-renders alone (item cache by chapter hash).
3. **What it applies:** cuts, source ranges, scaling/fit, fades and dissolves, push-ins as simple zooms, overlay clips with their blend mode, baked ducking stems, titles as plain text (FFmpeg `drawtext`), voice/music/SFX mix at manifest gains. Template animations, grades and editor effects are **not** simulated; the preview says "approximate" in its first-frame slate.
4. **Burnt-in review aids:** a small caption with the chapter title and timecode, and each review/licence marker's name for its duration. A clean version (`--clean`) can be rendered on request.
5. **Encode:** H.264 (NVENC when available), 1080p or 720p (`preview.resolution` in the channel profile), AAC stereo. It is **not** the master and is never uploaded.

**Acceptance:** the preview's duration equals `timeline.duration_frames` exactly; a frame grabbed at each clip's `record.start + 1` shows that clip (spot-checked on the M0 fixture).

## Validation rules
| Code | Rule | Severity |
|---|---|---|
| `SCHEMA` | Every artifact validates against its JSON Schema | error |
| `COVERAGE_V1` | V1 base layer covers `[0, duration]` with zero gaps | error |
| `OVERLAP` | No two clips overlap on one track (except via a declared transition) | error |
| `SRC_RANGE` | `0 ≤ source.in < source.out ≤ inventory.duration_frames`; duration consistent with record × rate ratio ÷ speed (±1 frame) | error |
| `HANDLES` | Each transition's alignment has enough handle; otherwise downgrade to a cut + review marker | warning |
| `LICENCE` | Every placed asset has a ledger entry with `commercial_use_ok: true`; archival assets have a `rights_decision`; generated assets have `plan_tier_at_generation` | error |
| `FORMAT` | Container/codec on the whitelist of the chosen editor's pinned version (Resolve codec list; FilmCraft `probe` per the M0a test); overlay clips with alpha are ProRes 4444 / PNG / TIFF / EXR; audio 48 kHz PCM | error |
| `CARRIER` | Every preset used has an implementation for the chosen editor and a ✔ matrix cell; `baked` only for presets that opted in (M3) | error |
| `SCRIPT_FIDELITY` | Mode S: each line's `text_display` equals the source sentence minus cues, unless changed by an accepted `human_edit` | error |
| `FILES` | Every referenced file exists and its hash matches the ledger | error |
| `REUSE` | No provider asset twice; near-duplicate similarity below threshold; channel re-use cap respected | warning |
| `MAX_HOLD` | No visual held longer than the section's maximum | warning |
| `SFX_DENSITY` | Transitional SFX per minute ≤ budget | warning |
| `MUSIC_COVER` | A4 covers chapter spans except `music_off`; no segment ends abruptly | warning |
| `CHAPTERS` | If YouTube chapters will be published: first chapter at 00:00, ≥3 chapters ascending, each ≥10 s (YouTube rules); hook shorter than 10 s merged into chapter 1. A script with fewer than 3 chapters (common for short Mode S scripts) publishes **no** chapter list: warning, not error | error / warning |
| `LOUDNESS_EST` | Quick audio-only mixdown: estimated integrated loudness and true peak within tolerance of the delivery target | warning |
| `SYNC_AUDIO` | Clips with `audio: sync` actually have an audio stream; VO does not overlap archival speech | error |
| `BUDGET` | Actual spend ≤ `budget_usd` | error |

## LLM vs deterministic code
All code. This stage exists so that **no LLM ever writes timecodes, gains or serialisation** (v1 had "the AI agent compiles … in/out timestamps").

## Acceptance tests
- Compiling the same inputs twice gives byte-identical `vcut_timeline.json` and exports.
- The round-trip OTIO test reproduces every clip range exactly.
- Each validation rule has a fixture that triggers it (M0).
- The same project compiled for `editor.target: resolve` and `filmcraft` differs only in carrier choices (ducking) and marker colour names, each listed in `qa_report.json`.
