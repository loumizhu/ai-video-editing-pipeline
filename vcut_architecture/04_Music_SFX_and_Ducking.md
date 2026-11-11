# Step 04: Music, SFX & Ducking

## Links
- **Hub:** [[Vcut_End_to_End_Pipeline_Architecture]] · **Contracts:** [[Vcut_Data_Contracts#3.5 vcut_timeline.json — canonical]] (`ducking`, A3/A4/A5 clips)
- **04a runs after:** [[01_Scriptwriting_Engine]] (G2), in parallel with [[02_Voice_and_Timing]]
- **04b runs after:** [[03_Shot_Planning_and_Visuals]] (`cut_list.json`) · **Next:** [[05_Timeline_Manifest_and_QA]]

---

## Purpose
Design the soundtrack under the narration. The work is: pick and fit licensed music per chapter, place a
*small* number of well-synced SFX, and specify ducking that stays **editable in Resolve or FilmCraft** (at minimum, the un-ducked bed is there to redo it).
*Renamed from "Audio & SFX Mastering": nothing here masters. The final mix is measured in [[07_Human_Review_and_Delivery#Mix & loudness QC]].*

*Why the split into 04a/04b:* in v1, step 04 was drawn as parallel to 02 yet needed the voice track (for
ducking), chapter time spans (for music) and visual cut points (for SFX). Those only existed after the
timeline was compiled. Sourcing depends only on the script; placement waits for the cut list.

## Inputs → Outputs
| In | Out |
|---|---|
| 04a: chapter moods (`script_manifest.json`), `channel_profile.yaml` (libraries, SFX budget) | Music + SFX shortlist (with ledger entries) |
| 04b: `cut_list.json`, `timing.json`, shortlist | `audio/audio_plan.json` (A3 SFX, A4 music segments, A5 un-ducked copy if baked, ducking spec), optional baked stems |

## 04a — Sourcing (script-only dependency)
- **Music** comes from a **human-curated licensed library** (`libraries/music/`). Each track has a ledger entry with its **licence file or certificate**, plus mood / energy / tempo tags. The owner adds tracks to `libraries/music/<mood>/` with their licence file (or to one video via `00_input/media/`).
  - The pipeline **ranks** tracks per chapter by mood and energy, with no reuse across adjacent chapters.
  - It never auto-downloads from subscription sites. Epidemic Sound and Artlist need partner agreements for API use. The plan you hold must match your legal entity (an individual creator plan vs a business plan).
- **SFX** come from a **curated local library** built once from CC0 and owned packs (whooshes, clicks, risers, impacts) and reused. Live Freesound look-ups are a rare top-up:
  - filter by licence **at query time** (`license:"Creative Commons 0"`; CC-BY only with an auto-credit);
  - **never** use CC-BY-NC or Sampling+;
  - authorise OAuth2 once (needed for original files);
  - stay within 500 original downloads/day.
  
  Freesound's API terms say commercial API use is negotiated case by case, so **ask UPF/MTG before relying on it**.
- **Loudness pre-normalisation:** every music and SFX asset is measured and normalised (music to a fixed reference level; SFX by peak / short-term loudness), and the measured value is stored in the ledger. *Without this, v1's `base_volume_db: -16` meant a different level on every track.*

## 04b — Placement (after `cut_list.json`)

### Music fitting
- **Per-chapter music plan:** mood, energy, start/end frames from the chapter spans, and an **end type** (back-timed natural ending · fade · stinger). Explicit `music_off` ranges for serious beats.
- **Length fitting:** detect beats and bars, then edit or loop **only on bar boundaries** with short crossfades. Prefer tracks that ship stems or loop versions. *(v1 showed one finite track spanning the whole timeline with no fades; that would stop mid-chapter or cut off abruptly.)*
- **Bed-to-bed transitions:** either a 1–3 s crossfade placed on a **designed pause** in the narration, or a hard cut under a transition SFX at the chapter marker. Never change music mid-sentence.
- Each bed segment is its own A4 clip with `source` range and `fade_in`/`fade_out`.

### SFX placement (one authority, a budget, real sync)
- **Authority and merge:**
  - the script owns **narrative** SFX (`sfx_intent` on a beat, e.g. "register ding on the price reveal");
  - 04 owns **transitional** SFX, derived from cut classes: only "major" cuts (section change, pattern interrupt);
  - **effect presets own their paired SFX** ([[Vcut_Effects_Library]]): a typewriter location stamp brings its key clicks (one per character, synced to the template's letter timing) and carriage return; a highlighter sweep its squeak; a person card its whoosh. They are placed on A3, linked to the title, effect or transition, and count toward the density budget;
  - script intent wins on its slot, then preset SFX, then transitional SFX;
  - no second SFX within 12 frames.
- **Density budget:** at most `max_transitional_per_min` from the channel profile (default 2), never under key lines, and the same file is not reused within 3 minutes.
- **Sync:** each SFX asset stores a `sync_offset` (detected transient or peak), and `record.start = cut_frame − sync_offset`. Risers are back-timed to **end** on the boundary. Preset SFX sync to the **event offsets declared in the preset** (e.g. first letter at +4 frames, then one every 2 frames), because the editor template's animation timing is fixed; code turns them into frames, and M0a checks them against a frame render from each editor.
- **Variety:** each SFX category keeps several files (e.g. 6 typewriter keys, 4 whooshes); 04b rotates them so the same file does not repeat back to back.

### Ducking specification
- **Two-level bed model** instead of "duck whenever speech is detected":
  - the bed sits at its **under-voice** level during narration;
  - it **opens** only in gaps ≥ `min_gap_ms` (default 1500 ms — designed pauses and chapter breaks);
  - `hold_ms` (default 600) bridges breaths between sentences, so the music never pumps.
- Defaults are starting values to tune at M1: `depth_db` 10 (relative to the open level), attack 100 ms, release 800 ms.
- **The envelope is computed from `timing.json`**, not from speech detection. Key tracks: A1 voice **and A2 sync/archival speech**.
- **Carrier into the NLE**, ranked ([[Vcut_Decision_Log#ADR-004 — Carriers for effects the Resolve API cannot set]]):
  1. **Native in the chosen editor (preferred, [[Vcut_Decision_Log#ADR-021 — One editor: everything native and editable]]):**
     - **Resolve:** the Fairlight **Ducker** on the music track keyed from the voice, pre-configured in the Vcut template project;
     - **FilmCraft:** the computed envelope written as **volume keyframes** on the music clips (`effects.setParam` on the clip's `volume.level`, code-computed frames), or FilmCraft's own `essentialSound.generateDucking`, whichever the M0a probe passes.
  2. **Fallback (any editor, until its cell is ✔):** a **baked ducked stem** on A4 (FFmpeg `sidechaincompress` or the computed envelope applied offline), with the **un-ducked bed muted on A5**, so the owner can redo it in the editor. The FFmpeg preview (05b) uses the same stem.
  
  OTIO is **not** a carrier: it has no standard volume-automation schema. *v1's three different duck depths (14 dB, 14–18 dB, and −16→−28 = 12 dB) are replaced by the single `depth_db`.*

## LLM vs deterministic code
- **AI:** chapter mood labels (from 01) and narrative SFX intent (from 01). The owner's `[music: …]` and `[sfx: …]` cues override both. *With AI `none`:* author cues, else the channel profile's first mood for every chapter and no narrative SFX.
- **Code:** ranking, beat/bar detection, fitting, sync offsets, density rules and the envelope.

## Failure modes & fallbacks
| Failure | Response |
|---|---|
| No library track fits a chapter mood | Reuse the nearest-mood bed from a non-adjacent chapter, or `music_off` + review marker |
| Track shorter than chapter and no clean loop point | Back-time the ending and fade in under the previous segment; mark for review |
| SFX library has no match for an intent | Skip it; it is optional, never placed by a raw search |

## Licence & policy constraints
- **MusicGen removed:** model weights are CC-BY-NC 4.0. **Udio removed:** downloads disabled since Oct 2025 (secondary reports). **Free Music Archive "API" removed:** no current documentation found.
- **Pixabay Music:** manual only (the Pixabay API has no audio endpoint). Keep the licence certificate, since some tracks are registered with Content ID (third-party reports).
- **Suno:** manual, on a paid plan only (commercial rights only for songs made while subscribed; Pro 20 / Premier 60 downloads a month). Record the plan per track. No unofficial API wrappers.
- AI music that is the **main focus** of a video triggers YouTube disclosure; a ducked bed does not ([[Vcut_Decision_Log#ADR-014 — AI-content disclosure]]).

## Tools
FFmpeg (`ebur128`, `loudnorm` measure mode, `sidechaincompress` for baked stems) · beat/bar detection (e.g. librosa) · Freesound API (licence-filtered) · Resolve Fairlight Ducker (via template). Details: [[Vcut_Tool_Allowlist#Audio]].

## Acceptance tests
- A4 covers every chapter span except declared `music_off` ranges; no segment ends without a fade or a back-timed ending.
- Transitional SFX per minute ≤ budget; every SFX sync point lands within ±1 frame of its cut.
- No music asset without a stored licence file; no Freesound asset whose licence is not CC0 or CC-BY.
