# Vcut — Data Contracts

> **The only place artifact fields are defined.** Step docs link here and never redefine a field.
> Changing a field means bumping that artifact's schema major version and updating its producer and
> consumers in the same change. Implementation: one JSON Schema per artifact (validated at every stage
> boundary; invalid data fails the stage).
>
> Decisions behind this doc: [[Vcut_Decision_Log#ADR-003 — Canonical timeline artifact]],
> [[Vcut_Decision_Log#ADR-015 — Timing source]]. Hub: [[Vcut_End_to_End_Pipeline_Architecture]].

---

## 1. Conventions

### 1.1 Common header (every JSON artifact)
```json
{
  "schema": "vcut.<artifact>/<major>",
  "project_id": "ai_video_essay_001",
  "run_id": "r0007",
  "created_at": "2026-10-12T14:03:22Z",
  "produced_by": {
    "stage": "02_voice", "stage_version": "0.1.0",
    "tool": "kokoro", "tool_version": "0.9.4", "model": "Kokoro-82M",
    "params_hash": "sha256:…", "prompt_hash": "sha256:… (LLM stages only)"
  },
  "inputs": [ { "artifact": "script/script_manifest.json", "sha256": "…" } ]
}
```

### 1.2 Stable IDs
| ID | Format | Rule |
|---|---|---|
| `chapter_id` | `ch03` | Order is the `chapters[]` array, never the number |
| `line_id` | `ch03.l017` | **Immutable once issued.** New lines get the next free number; lines are never renumbered |
| `unit_id` | `ch03.u004` | A TTS synthesis unit (a paragraph or beat) = an ordered list of `line_id`s |
| `claim_id` | `c0042` | One factual claim with sources ([[01_Scriptwriting_Engine]]) |
| `beat_id` | `b0137` | One visual intent anchored to a word span |
| `slot_id` | `s0201` | One timed visual slot in the shot plan |
| `asset_id` | `a_<first 12 hex of sha256>` | Content-addressed; the same file always has the same id |
| `clip_id` | `k0201` | One placed item on the timeline |
| `marker_id` | `m014` | One marker |
| word ref | `(line_id, word_idx)` | `word_idx` indexes `spoken_tokens` of that line, 0-based |

### 1.3 Time model
- **Upstream (02 voice):** seconds as decimals, plus exact sample offsets at 48 000 Hz.
- **Placement intent (03–04):** an **anchor** `{line_id, word, edge: "start"|"end", offset_frames}`, never an absolute time. Re-voicing one line therefore re-times everything after it automatically.
- **Timeline (05):** integer **frames** at a rational `rate` `{num, den}` (default `30/1`, [[Vcut_Decision_Log#ADR-010 — Delivery format]]). Frame 0 = timeline start; the adapter adds Resolve's start frame (default `01:00:00:00`).
- **Source ranges:** integer frames in the **source's own rate**, taken from `media_inventory` (ffprobe), never assumed.
- **Quantiser (05, deterministic):** one function converts anchors to frames. Rule: snap to the nearest frame boundary, then apply `offset_frames` (default −2: cut slightly *before* the keyword). Audio offsets stay in samples.

### 1.4 Paths
Artifacts store **project-root-relative POSIX paths** plus `asset_id`. Compilers resolve them to absolute
paths or `file://` URLs at emit time from the declared `project_root`. No artifact holds an absolute path,
which keeps projects movable. Windows special characters in paths (e.g. `E:\((_atWork_))`) are tested in M0.
- **Two layers per video** ([[Vcut_Decision_Log#ADR-019 — Per-video folder organisation]]): artifacts live in the system folder `.vcut/` under the roots below; the numbered, human-readable folders are a **view** rebuilt from `current/` by the runner (§2.1). No stage ever reads from the view; the owner's only writable folder is `00_input/`.

---

## 2. Artifact catalogue
Paths are relative to one of these roots, written as prefixes in `pipeline.yaml` (revised 2026-10-26 for ADR-019):
- `{input}` = `projects/<project_id>/00_input/`: everything the owner supplies (script, instructions, brief, recordings, own media). Read-only for Vcut;
- `{project}` = `projects/<project_id>/`: `project.yaml`, `STATUS.md`;
- `{system}` = `projects/<project_id>/.vcut/`: approvals, overrides, the content-addressed `assets/` and ledger, `current/`, cache, agent tasks — shared across runs so a re-run never re-downloads;
- `{run}` = `projects/<project_id>/.vcut/runs/<run_id>/`, for per-run artifacts. For a stage the run **inherited**, it resolves to the source run's folder, through `run_manifest.json` (§3.8).

In the table below, "project" in the Root column means `{system}` unless the path starts with `00_input/` (`{input}`) or is `project.yaml` (`{project}`).

| Artifact | Root | Producer (stage id) | Consumers | Schema |
|---|---|---|---|---|
| `project.yaml` | project | human (setup form, 00) | runner, all stages | `vcut.project/1` (§3.10) |
| `00_input/script.(md\|txt\|docx)` | input | human (00), script start | 01a intake | verbatim; hashed, never modified by Vcut |
| `00_input/instructions.md` | input | human (00), optional | 01a intake | free text; its mapping is shown at G2 |
| `00_input/brief.yaml` | input | human (00), brief start | 01a (Mode W) | `vcut.brief/2` (editorial fields only; see 00) |
| `00_input/recordings/*` | input | human (00), optional | 02 | audio files, any of WAV/FLAC/MP3; conformed by 02 |
| `00_input/media/*` (+ licence notes) | input | human (00), optional | 03a (searched first) | ledger entry created by 03c with `provider: owner` |
| `channel_profile.yaml` | vault root | human | 00 (pre-fills the setup form), 01–07 | `vcut.channel/2` (see 00) |
| `libraries/effects/<category>/<preset_id>/preset.yaml` | vault | human / Vcut library tools (templates made once in each editor) | 03b, 04b, 05, 06 | `vcut.effect/2` (§3.11) |
| `pipeline.yaml` | project (or vault default) | human / template (00) | orchestrator | `vcut.pipeline/3` (§3.7; the file on disk is still `/2` until the runner migrates) |
| `approvals/G1…G4.json` | project | the owner (Storyboard click or `vcut approve` on a TTY) **or the runner applying the owner's autopilot policy**; HMAC-signed | orchestrator | `vcut.approval/2` (adds `policy`, `hmac`) |
| `agent_tasks/<task_id>/task.json`, `answer.json` | project | runner (task), agent app (answer) | the stage that asked | `vcut.agenttask/1`; answer schema per task |
| `overrides.yaml` | project | human (G3) | 03b, 03c | `vcut.overrides/1` |
| `script/intake.json` | run | 01a (Mode S) | 01b | `vcut.intake/1` (§3.9) |
| `research/claims.json` (+ `research/sources/`) | run | 01b (Mode S) · 01a (Mode W) | 01b, 07b | `vcut.claims/2` (adds `verdict`, `proposed_edit`, §3.9) |
| `script/outline.json` | run | 01a (Mode W) | 01b (G1) | `vcut.outline/1` |
| `script/script_manifest.json` | run | 01b | 02, 03, 04, 05, 07 | `vcut.script/2` |
| `voice/timing.json` (+ `voice/units/*.wav`) | run | 02 | 03b, 03e, 04b, 05, 07b | `vcut.timing/1` |
| `shots/candidates.json` | run | 03a | 03b | `vcut.candidates/1` |
| `audio/shortlist.json` | run | 04a | 04b | `vcut.audioshortlist/1` |
| `shots/shot_plan.json` (+ `contact_sheet.html`) | run | 03b | 03c (G3), 03e, 05 | `vcut.shotplan/1` |
| `ledger/<stage_id>.jsonl` | run | 03c, 03d, 04a, 05 (append-only) | runner (merge only) | `vcut.ledgerpatch/1` |
| `assets/asset_registry.json` (+ `assets/`, `assets/conformed/`) | project | **runner only**, merging the ledger fragments | 03d, 03e, 05, 06, 07 | `vcut.assets/1` |
| `shots/cut_list.json` | run | 03e | 04b, 05 | `vcut.cutlist/1` |
| `audio/audio_plan.json` | run | 04b | 05 | `vcut.audioplan/1` |
| `timeline/vcut_timeline.json` | run | 05 | 06, 07 | `vcut.timeline/1` (**canonical**) |
| `timeline/exports/vcut.fcpxml` (1.10), `vcut.otio` | run | 05 | 06, archive | derived, never edited |
| `qa/qa_report.json` | run | 05 | 05b, 06, 07a (G4) | `vcut.qa/1` |
| `preview/rough_cut.mp4` | run | 06 (editor render: FilmCraft, Resolve Studio) or 05b (FFmpeg approximation, free Resolve) | human (G4) | derived; not the master ([[Vcut_Decision_Log#ADR-017 — Preview render]]) |
| `nle/package/` (`vcut.fcpxml`, `vcut.otio`, `media/`, `markers.csv`, `titles.csv`, `README_import.md`) | run | 06 (always, as a backup) | human: manual import if the native build fails | derived ([[06_NLE_Adapters#The interchange package (always built)]]) |
| `nle/<editor>/build_report.json` (+ Resolve `.drp` or FilmCraft `build.jsonl` + `.fcproj`, audit `.otio`) | run | 06 (native build in the chosen editor) | 07 | `vcut.build/1`; `<editor>` ∈ `resolve`, `filmcraft` |
| `delivery/final_timeline.(fcpxml\|otio)` | run | human export from the NLE after G4 (or automated readback) | 07b | NLE's own format; read-only input |
| `qa/loudness_report.json` | run | 07a | 07a (G4) | `vcut.loudness/1` |
| `delivery/*` | run | 05 (credits draft, disclosure), 07a (master, stems), 07b (rest) | human / YouTube | see [[07_Human_Review_and_Delivery]] |
| `run_report.json` | run | every stage | human | `vcut.runreport/1` |
| `run_manifest.json` | run | runner | runner, all path resolution | `vcut.runmanifest/1` (§3.8) |
| `current/<stage_id>.json` | project | runner only | runner | `vcut.current/1` (§3.8) |

### 2.1 The readable view (numbered folders)
Rebuilt by the runner whenever a stage completes, as hard links (copies if linking fails) to the files that
`current/` points at. Machine artifacts go under each folder's `data/`; readable renderings sit beside them.

| View path | Comes from | Readable extras written by the runner |
|---|---|---|
| `01_script/data/` | `{run}/script/*`, `{run}/research/claims.json` | `script_locked.md`, `claims.md`, `sources/` |
| `02_voice/units/`, `02_voice/data/timing.json` | `{run}/voice/*` | `narration_full.wav` (all units + pauses, one file) |
| `03_media/<NN>_<chapter-slug>/` | placed assets, by chapter, in timeline order | file names `<slot_id>_<3-word slug>__<source>.<ext>`; `alternates/<slot_id>/` |
| `03_media/overlays/`, `03_media/data/`, `03_media/contact_sheet.html` | overlay clips used; `{run}/shots/*` | `titles.md` (every title/card and its text, for reading) |
| `04_audio/music/`, `04_audio/sfx/`, `04_audio/data/` | `{run}/audio/*`, placed music/SFX | `music_ducked.wav` when baked |
| `05_timeline/data/`, `05_timeline/preview.mp4` | `{run}/timeline/*`, `{run}/preview/rough_cut.mp4` | `qa_report.md` |
| `06_editor/package/`, `06_editor/resolve/`, `06_editor/filmcraft/` | `{run}/nle/*` | — |
| `07_delivery/` | `{run}/delivery/*` | — |
| `STATUS.md` | `run_manifest.json`, `run_report.json`, pending gates | — |

---

## 3. Key schemas

### 3.1 script_manifest.json
Display text and spoken text are **separate layers**. Visual/SFX intents are **never** embedded in the text
(the original `[B-ROLL: …]` brackets risked being read aloud by TTS).
```json
{
  "schema": "vcut.script/2",
  "mode": "script",
  "source_ref": { "file": "00_input/script.md", "sha256": "…" },
  "language": "en", "locale": "en-GB",
  "hook": { "chosen": "h2", "variants": [ { "id": "h1", "line_ids": ["ch01.l001"] }, { "id": "h2", "line_ids": ["ch01.l001b"] } ] },
  "chapters": [
    { "chapter_id": "ch01", "title": "The Problem", "word_budget": 420, "mood": "tense",
      "promises_paid": ["p1"],
      "units": [ { "unit_id": "ch01.u001", "line_ids": ["ch01.l001", "ch01.l002"], "pause_after_ms": 600 } ],
      "lines": [
        { "line_id": "ch01.l002",
          "text_display": "In 2024, data centres used 4% of US electricity.",
          "text_spoken":  "In twenty twenty-four, data centres used four percent of U S electricity.",
          "spoken_tokens": ["In","twenty","twenty-four","data","centres","used","four","percent","of","U","S","electricity"],
          "token_map": [[0,0],[1,1],[1,2],[2,3]],
          "claim_ids": ["c0007"] }
      ] }
  ],
  "visual_beats": [
    { "beat_id": "b0003", "anchor": { "line_id": "ch01.l002", "word_start": 3, "word_end": 11 },
      "source": "llm",
      "type": "stock_video", "description": "rows of servers in a cold aisle, slow dolly",
      "search_queries": ["data center server aisle", "server racks blue light", "cloud infrastructure hallway"],
      "must_show": ["server racks"], "negative_terms": ["text", "logo", "people faces"],
      "orientation": "landscape", "min_s": 2.0, "max_s": 7.0, "priority": 2,
      "fallback": ["stock_photo", "text_card", "base_layer"],
      "on_screen_text": null, "chart": null, "sfx_intent": null,
      "context_sentiment": "neutral" }
  ],
  "lexicon_ref": "channel_profile.yaml#lexicon",
  "editorial_checklist": { "named_people_or_orgs": true, "medical_financial_election": false, "made_for_kids": false }
}
```
`type` ∈ `stock_video | stock_photo | own_media | commons_image | article_capture | article_card | person_card | org_card | map | ai_video | archival_inbox | chart | text_card | title | base_layer` (types added 2026-10-26 for the documentary style; `article_capture` and `commons_image` with CC-BY-SA need a `rights_decision`).
- `effects[]` (optional, per beat): preset ids from the effects library with values, e.g. `[{ "preset": "txt.location_stamp", "values": { "text": "VIENNA, AUSTRIA" } }, { "preset": "mot.push_in" }]`. `source` per effect ∈ `author_cue | style_rule | llm`.
- `entity` (optional): `{ "kind": "person|org|place", "name": "…", "wikidata": "Q…" }` for person/org cards and maps, so 03 can look up a licensed photo, logo or coordinates.
- `mode` ∈ `script` (Mode S) `| brief` (Mode W). `source_ref` is required in Mode S and points at the verbatim source.
- Mode S rule: each line's `text_display` equals the owner's sentence with cues removed. A change is only possible through an accepted `proposed_edit` applied with `vcut edit` (header `produced_by.stage: human_edit`).
- `hook` is `null` in Mode S unless the owner marks variants.
- `visual_beats[].source` ∈ `author_cue | llm | heuristic`. Author cues take precedence and are never overwritten by AI or heuristics.
- Schema bumped to `/2` on 2026-10-26 for `mode`, `source_ref` and `visual_beats[].source`.

### 3.2 timing.json
```json
{
  "schema": "vcut.timing/1",
  "sample_rate": 48000,
  "units": [ { "unit_id": "ch01.u001", "file": "voice/units/ch01.u001.wav", "sha256": "…",
               "offset_samples": 0, "duration_samples": 659200, "source": "tts_native" } ],
  "lines": [ { "line_id": "ch01.l002", "start_s": 4.120, "end_s": 9.870 } ],
  "words": [ { "line_id": "ch01.l002", "word": 3, "start_s": 5.010, "end_s": 5.330, "source": "tts_native" } ],
  "qc": [ { "unit_id": "ch01.u001", "wer": 0.0, "status": "ok" } ],
  "chapters": [ { "chapter_id": "ch01", "start_s": 0.0, "end_s": 142.3, "budget_s": 150.0 } ]
}
```
`source` ∈ `tts_native | forced_alignment | asr_fallback` (an `asr_fallback` timing is flagged as approximate).

### 3.3 shot_plan.json
One row per slot; frames are *derived* from anchors and recomputed if timing changes.
```json
{ "slot_id": "s0003", "beat_id": "b0003", "track_role": "broll",
  "anchor_in":  { "line_id": "ch01.l002", "word": 3,  "edge": "start", "offset_frames": -2 },
  "anchor_out": { "line_id": "ch01.l003", "word": 0,  "edge": "start", "offset_frames": -2 },
  "min_frames": 45, "max_frames": 210,
  "candidates": [ { "asset_ref": "pexels:3129957", "score": 0.81, "qc": { "text": false, "logo": false, "watermark": false } },
                  { "asset_ref": "pexels:855564",  "score": 0.74, "qc": { "text": false, "logo": false, "watermark": false } } ],
  "chosen": "pexels:3129957", "generative": false, "est_cost_usd": 0.0, "review": null }
```

**Optional pacing fields (ADR-022, 2026-11-09).** All optional; absent fields keep the old behaviour, with unknown media treated as a still.
```json
{ "media_type": "image|video|plate", "asset_group": "g_rotary_phone",
  "beat": { "emotion": "calm|tension|grief|joy|neutral", "intensity": 3 },
  "anchor_phrase": "the rotary phone",
  "preset": "documentary_standard",
  "motion": { "move": "detail_crop", "target_rect": [0.55, 0.3, 0.3, 0.3], "at_ms": 21500 },
  "enrichments": [ { "type": "photo_annotation", "at_ms": 18500, "anchor_word": "phone", "rationale": "…" } ],
  "transition_in": "cut", "sfx": ["sfx_paper_slide.wav"],
  "rationale": "one sentence tying a major choice to the line",
  "still_hold_waiver": "OWNER ONLY: reason" }
```
`enrichments[].type` ∈ the ids of `presets/pacing/enrichment_catalog.json`; times are absolute timeline milliseconds like the anchors (frames stay derived). Beat rows live in `beat_map.json` (`pipeline.beat_map/1`: `beat`, `emotion`, `intensity` 1-5, `function`, `info_type`, `anchor_phrase`, `priority`, `evidence`).

### 3.4 asset_registry.json — licence and provenance ledger
The validator refuses any placed asset whose entry is missing, or whose `commercial_use_ok` is not `true`.
**Write rule** ([[Vcut_Decision_Log#ADR-005 — Orchestration runtime]]): stages never write this file. They
append records to `{run}/ledger/<stage_id>.jsonl`: `{"op": "upsert", "entry": {…}}` for a new asset, or
`{"op": "patch", "asset_id": "…", "set": {…}, "append": {"usage": [ … ]}}`. The runner merges the fragment when the
stage completes, under a lock with an atomic rename. If two records disagree on `licence` or
`commercial_use_ok` for one `asset_id`, the merge fails instead of letting the last write win. Readers
select entries by the `asset_id`s their inputs reference, and hash only those entries into their cache key.
```json
{ "asset_id": "a_3f9c2e81b0d4", "sha256": "…", "kind": "video",
  "path": "assets/video/pexels_3129957.mp4", "conformed_path": "assets/conformed/a_3f9c2e81b0d4.mov",
  "provider": "pexels", "provider_asset_id": "3129957",
  "source_url": "https://www.pexels.com/video/3129957/", "author": "…",
  "licence": { "id": "pexels-license", "url": "https://www.pexels.com/license/", "terms_snapshot_sha256": "…",
               "commercial_use_ok": true, "attribution": "courtesy",
               "restrictions": ["no identifiable people in a bad light", "no implied endorsement"] },
  "retrieved_at": "2026-10-12", "plan_tier_at_generation": null,
  "synthetic": { "is_synthetic": false, "kind": null, "realism": null, "depicts_real_person_place_event": false,
                 "model": null, "prompt": null, "seed": null },
  "rights_decision": null,
  "inventory": { "container": "mp4", "vcodec": "h264", "rate": { "num": 25, "den": 1 }, "vfr": false,
                 "duration_frames": 450, "width": 3840, "height": 2160, "has_alpha": false,
                 "color_transfer": "bt709", "audio": null },
  "usage": [ { "project_id": "ai_video_essay_001", "clip_id": "k0014" } ] }
```
- `attribution` ∈ `required` (CC-BY) · `courtesy` (Pexels/Pixabay) · `none`.
- `rights_decision` is **mandatory** for `archival_inbox` assets: `{ approved_by, date, basis: "licence|public_domain|owner|fair_use_rationale", note }`.
- `plan_tier_at_generation` is mandatory for generated media (ElevenLabs, Suno, Luma, …), because commercial rights depend on the plan at generation time.

### 3.5 vcut_timeline.json — canonical
Constrained to structures OTIO and FCPXML can represent: ordered tracks, no overlap on one track,
transitions only between *adjacent* clips, fades as clip properties.
```json
{
  "schema": "vcut.timeline/1",
  "timeline": { "name": "ai_video_essay_001_v007", "rate": { "num": 30, "den": 1 },
                "start_timecode": "01:00:00:00", "width": 1920, "height": 1080,
                "audio_sample_rate": 48000, "duration_frames": 5400 },
  "tracks": [
    { "id": "V1", "kind": "video", "index": 1, "role": "base_layer" },
    { "id": "V2", "kind": "video", "index": 2, "role": "broll" },
    { "id": "V3", "kind": "video", "index": 3, "role": "graphics" },
    { "id": "V4", "kind": "video", "index": 4, "role": "overlay" },
    { "id": "A1", "kind": "audio", "index": 1, "role": "voice", "layout": "mono" },
    { "id": "A2", "kind": "audio", "index": 2, "role": "sync", "layout": "stereo" },
    { "id": "A3", "kind": "audio", "index": 3, "role": "sfx", "layout": "stereo" },
    { "id": "A4", "kind": "audio", "index": 4, "role": "music", "layout": "stereo" },
    { "id": "A5", "kind": "audio", "index": 5, "role": "music_unducked", "layout": "stereo", "muted": true }
  ],
  "clips": [
    { "clip_id": "k0001", "track": "V1", "asset_id": "a_7c1e09aa41f2",
      "record": { "start": 0, "duration": 5400 }, "source": { "in": 0, "out": 5400, "rate": { "num": 30, "den": 1 } },
      "speed": 1.0, "fit": "fill", "audio": "none" },
    { "clip_id": "k0014", "track": "V2", "asset_id": "a_3f9c2e81b0d4", "slot_id": "s0003",
      "record": { "start": 75, "duration": 150 },
      "source": { "in": 30, "out": 155, "rate": { "num": 25, "den": 1 } },
      "speed": 1.0, "fit": "fill", "audio": "none",
      "fade_in_frames": 8, "fade_out_frames": 0,
      "motion": null, "effects": [{ "preset": "look.archival" }],
      "alternates": ["a_91d07c3e55ab", "a_be4410f2c9d1"] },
    { "clip_id": "k0201", "track": "V3", "asset_id": null,
      "record": { "start": 80, "duration": 90 },
      "title": { "preset": "txt.location_stamp", "variant": "amber", "values": { "place": "VIENNA, AUSTRIA" } } },
    { "clip_id": "k0101", "track": "A1", "asset_id": "a_ch01u001wav", "unit_id": "ch01.u001",
      "record": { "start": 0, "duration": 412 }, "source": { "in": 0, "out": 659200, "unit": "samples" },
      "gain_db": 0.0 },
    { "clip_id": "k0301", "track": "A4", "asset_id": "a_51aa8e0c7d23", "chapter_id": "ch01",
      "record": { "start": 0, "duration": 4269 }, "source": { "in": 0, "out": 6830400, "unit": "samples" },
      "gain_db": 0.0, "fade_in_frames": 30, "fade_out_frames": 45 }
  ],
  "transitions": [
    { "between": ["k0014", "k0015"], "type": "tr.cross_dissolve", "alignment": "center", "duration_frames": 15 }
  ],
  "ducking": { "carrier": "fairlight_ducker", "music_tracks": ["A4"], "key_tracks": ["A1", "A2"],
               "depth_db": 10.0, "attack_ms": 100, "hold_ms": 600, "release_ms": 800, "min_gap_ms": 1500 },
  "markers": [
    { "marker_id": "m001", "kind": "chapter", "frame": 0,    "duration_frames": 1,  "name": "The Problem" },
    { "marker_id": "m014", "kind": "review",  "frame": 1356, "duration_frames": 30, "name": "Low-confidence B-roll",
      "note": "s0042 score 0.21 — alternates in bin B-Roll/ch02/s0042" }
  ],
  "delivery": { "container": "mp4", "vcodec": "h264", "width": 1920, "height": 1080, "rate": { "num": 30, "den": 1 },
                "audio": "48k stereo", "loudness_target_lufs": -14.0, "true_peak_max_dbtp": -1.0 },
  "compliance": { "ledger_ref": "assets/asset_registry.json", "disclosure_required": false, "credits_ref": "delivery/credits.txt" }
}
```
Field rules:
- `source.out` is required for video. The validator checks `(out − in)` ≈ `record.duration × source_rate ÷ timeline_rate ÷ speed` (±1 frame) and that `in ≥ 0`, `out ≤ inventory.duration_frames`.
- **Handles:** `in` and `duration_frames − out` must each be ≥ 1 s of source wherever the source allows, and ≥ the dissolve's needs for `center`/`end` alignment. A shortfall downgrades the transition to a cut and adds a review marker.
- `audio` on a video clip: `none` (placed video-only) or `sync` (its embedded sound goes to **A2**, linked, and joins the ducking key).
- `gain_db` is relative to the asset's **normalised** loudness, which 04 stores in the ledger. Without that normalisation, manifest gains are meaningless.
- `ducking.depth_db` is a positive **reduction relative to the bed's open level**. `min_gap_ms`: pauses shorter than this never swell the music (prevents pumping between sentences).
- `ducking.carrier` ∈ `fairlight_ducker | filmcraft_keyframes | baked_stem`. With `baked_stem`, A4 holds the ducked render and A5 the muted, un-ducked original. `fairlight_ducker` is valid only when `project.yaml` `editor.target` is `resolve` (Vcut template); `filmcraft_keyframes` (the computed envelope as volume keyframes, or FilmCraft's `essentialSound.generateDucking`) only for `filmcraft` once its matrix cell is ✔; otherwise 05 compiles `baked_stem` ([[Vcut_Decision_Log#ADR-004 — Carriers for effects the Resolve API cannot set]]).
- `motion`: `null` or `{ "preset": "mot.push_in", "carrier": "native" | "baked", "start_rect": [x,y,w,h], "end_rect": [x,y,w,h], "ease": "in_out" }` in normalised coordinates. `native` = Motion keyframes (FilmCraft) or Dynamic Zoom / Fusion comp (Resolve), per the capability matrix for the chosen editor; `baked` only for presets that opt in (M3).
- `markers[].kind` ∈ `chapter | review | licence | info`. Colour is **derived** per editor, never stored: chapter = Blue, review = Yellow, licence = Red (FilmCraft: Rose), info = Green. Only `kind: chapter` feeds YouTube chapters (in FilmCraft it is also a chapter marker).
- **Effects and titles (revised 2026-10-27, [[Vcut_Decision_Log#ADR-021 — One editor: everything native and editable]]):** everything here is built **natively** by 06 from the preset's implementation for the chosen editor; nothing is pre-rendered.
  - **Title clips** (`title` instead of an `asset_id`) sit on **V3**: `{ "preset", "variant", "values" }`. `values` keys are the preset's template fields (§3.11); they are text, never times. The owner edits them in the editor.
  - **Effects on a clip:** `effects[]` = `[{ "preset": "<id>", "variant": "…", "params": { … } }]` (looks, light leak, grain, vignette, shake), applied as that editor's effect stack or grade.
  - **Overlay clips** (dust, scratches, burns, paper) sit on **V4** with `"blend": "screen|add|overlay|multiply|normal"` and `"opacity"`.
  - **Transitions:** `transitions[].type` is a preset id (`tr.cross_dissolve`, `tr.dip_black`, `tr.light_leak`…); 06 maps it to the editor's transition.
  - A paired SFX is an ordinary A3 clip whose `linked_to` names the title, effect or transition it belongs to.
  - A preset with no implementation for the chosen editor is a **validation error** (05 `CARRIER`), never silently baked.
- Exports (backup package): OTIO gets Vcut data under `metadata["vcut"]`. Marker colours map lossily, since OTIO 0.18 has 11 colour names and Resolve has 16. FCPXML is written at version **1.10**. Titles go to `titles.csv`, since interchange does not carry the editors' native titles.

### 3.6 qa_report.json
`{ errors: [{code, clip_id|slot_id|asset_id, message}], warnings: [...], stats: {coverage_pct, max_hold_s, reuse_max, sfx_per_min, est_integrated_lufs, est_true_peak_dbtp, cost_usd_actual} }`.
Any `errors` entry blocks 06. Error codes are listed in [[05_Timeline_Manifest_and_QA#Validation rules]].

### 3.7 pipeline.yaml (the pipeline orchestration manifest)
Defines the stage DAG, tool choices, file hand-offs and human gates, without a database. Stage ids are the
ones in the canonical stage table ([[Vcut_End_to_End_Pipeline_Architecture#3. Canonical stage table]]).
**Target version `vcut.pipeline/3` (2026-10-26).** Changes from `/2`: `roles.<role>.provider` enum including
`agent` and `none` ([[Vcut_Decision_Log#ADR-016 — AI providers and the no-AI path]]); stage `modes`
([[Vcut_Decision_Log#ADR-005 — Orchestration runtime]], entry modes); `resource` value `resolve` replaced by `nle`;
stages `01a_intake`, `05b_preview` added and `06_resolve` renamed `06_nle_build`. The root `pipeline.yaml` is still
`/2` until the runner is migrated ([[Vcut_Plan_Review_2026-10-26#Impact on existing code]]).
```yaml
schema: vcut.pipeline/3
pipeline_id: string
version: string
ledger:                              # shared asset ledger (§3.4 write rule)
  registry: string                   # "{project}/assets/asset_registry.json"; written by the runner only
  fragment: string                   # "{run}/ledger/{stage_id}.jsonl"
  writers: string[]                  # stage ids allowed to emit ledger fragments
  merge: on_stage_complete
  library_registry: string           # channel library ledger; runner-only (library adds, after G4)
roles:                               # AI roles; stages reference "role:<name>", never a model name
  <role>:                            # drafting | tagging | vision
    provider: cloud | local | agent | none
    model: string | null             # cloud: vendor model id; local: Ollama tag; agent: agent id; none: null
    # bound per project in channel_profile.yaml `ai`; this file holds the default (none)
stages:
  - id: string                       # e.g. "01a_intake", "03b_shot_plan"
    name: string
    doc: string                      # the step doc that specifies the stage
    modes?: ("S" | "W")[]            # default both; a stage outside the project's mode is skipped and its edges dropped
    depends_on: string[]             # stage ids; [] = root. Defines the DAG (parallel branches allowed)
    resource: network | gpu | cpu | nle | human        # scheduling class (00 Run model); `nle` = needs Resolve/FilmCraft running
    tool_choice: Record<string, string | string[] | null>   # tool ids from the Allow-list, or "role:<name>"
    inputs:
      artifacts: string[]            # "{run}/…" or "{project}/…" paths (§2); "name#key" = one key of a file
    outputs:
      artifacts: string[]            # a trailing "/" means a folder
    approval?:                       # present = the runner halts after this stage until approved
      gate: "G1" | "G2" | "G3" | "G4"
      approves: string[]             # artifacts whose sha256 the approval file records
loops:                               # the only backward edges
  - id: "L1" | "L2" | "L3" | "L4"
    from: string                     # stage id that detects the condition
    to: string | string[]            # stage id(s) re-run
    trigger: string
    max_rounds: integer
    reapproval: "G1" | "G2" | "G3" | "G4" | null   # gate to re-approve if approved content changes
```
Rules:
- **No tunables.** `pipeline.yaml` holds orchestration only. Thresholds, depths, loudness targets, tolerances, delivery format and Resolve naming are defined once, in the step docs, this file or `channel_profile.yaml`.
- A stage runs when every `depends_on` stage is complete and all its declared input artifacts exist and validate against their schemas.
- **Gates bind to content, not to runs.** `approvals/<gate>.json` = `{gate, approved_by, approved_at, notes, policy: "review" | "auto", hashes: {artifact: sha256}, hmac}` (`vcut.approval/2`). With `policy: auto`, `approved_by` is `autopilot (policy set by <owner> at <time>)`. The runner refuses a file whose `hmac` (keyed from Windows Credential Manager) does not verify. A stage downstream of a gate refuses to run unless the current hashes of that gate's `approves` list match. A later run whose approved artifacts are unchanged needs no new approval.
- A loop (except L3, which is internal to 02) starts a **new run** from its `to` stage. Everything upstream is inherited, and the item cache limits the work to the items the loop changes. After `max_rounds` the runner continues and reports the condition (step docs define each loop's fallback).

### 3.8 run_manifest.json and current/ pointers
How a run inherits unchanged stage outputs ([[Vcut_Decision_Log#ADR-005 — Orchestration runtime]], "Runs and inheritance").
`runs/<run_id>/run_manifest.json`, written by the runner as stages resolve:
```json
{ "schema": "vcut.runmanifest/1", "project_id": "ai_video_essay_001", "run_id": "r0008",
  "parent_run_id": "r0007", "started_by": "vcut edit script/script_manifest.json", "pipeline_sha256": "…",
  "stages": {
    "01a_research_outline": { "status": "inherited", "from_run": "r0005", "fingerprint": "sha256:…" },
    "01b_script":           { "status": "ran", "fingerprint": "sha256:…", "reason": "input changed: human_edit" },
    "02_voice":             { "status": "ran", "fingerprint": "sha256:…", "items": { "cached": 61, "computed": 1 } },
    "03a_candidates":       { "status": "inherited", "from_run": "r0007", "fingerprint": "sha256:…" }
  } }
```
`current/<stage_id>.json`, one file per stage, written by the runner only (atomic rename):
```json
{ "schema": "vcut.current/1", "stage_id": "02_voice", "run_id": "r0008", "fingerprint": "sha256:…",
  "completed_at": "2026-10-15T10:02:11Z", "outputs": { "voice/timing.json": "sha256:…", "voice/units/": "sha256:… (tree hash)" } }
```
- `status` ∈ `inherited | ran | failed | skipped`. Only `ran` with every item complete advances `current/`.
- **Fingerprint** = sha256 over the stage id, `stage_version`, the resolved `tool_choice` (tool versions and the model bound to each role), params and prompt hashes, and the input artifact hashes as resolved in this run.
- **Pinned stages** (outputs approved by a gate): a fingerprint that differs *only* in tools, versions or models keeps the approved output, logged as `"status": "inherited", "pin_warning": "<what changed>"`. A change to an input artifact re-runs the stage.
- **Path resolution:** `{run}/<path>` for an inherited stage resolves to `runs/<from_run>/<path>`. Artifact headers keep the `run_id` that produced them.
- **Item cache:** `{project}/cache/items/<stage_id>/<item_hash>/`. A re-run stage materialises cache hits into its run folder as hard links where the filesystem allows, or as copies otherwise.

### 3.9 intake.json (Mode S) and claims verdicts
`script/intake.json`, written by 01a in Mode S. It is the parsed script **before** research and beats; 01b turns it into `script_manifest.json`.
```json
{
  "schema": "vcut.intake/1",
  "source_ref": { "file": "00_input/script.md", "sha256": "…", "format": "markdown" },
  "instructions_ref": { "file": "00_input/instructions.md", "sha256": "…" },
  "settings_from_instructions": [
    { "text": "target 8 minutes", "maps_to": "target_duration_min", "value": [7.5, 8.5], "applied": true },
    { "text": "keep it moody", "maps_to": null, "applied": false }
  ],
  "chapters": [ { "chapter_id": "ch01", "title": "The Problem", "title_source": "heading",
                  "units": [ { "unit_id": "ch01.u001", "line_ids": ["ch01.l001", "ch01.l002"] } ],
                  "lines": [ { "line_id": "ch01.l002", "text_display": "In 2024, data centres used 4% of US electricity.",
                               "source_span": { "start_char": 312, "end_char": 361 } } ] } ],
  "cues": [ { "cue_id": "q007", "kind": "visual", "text": "aerial of a substation at dusk",
              "anchor": { "line_id": "ch01.l003", "word": 0 }, "recognised": true },
            { "cue_id": "q008", "kind": "unknown", "text": "B-ROLL: city lights", "anchor": { "line_id": "ch01.l004", "word": 0 },
              "recognised": false } ],
  "duration_estimate_s": 482.0,
  "segmentation": { "provider": "none", "notes": ["ch02 had no heading; split after 380 words"] }
}
```
- `cues[].kind` ∈ `visual | chart | card | effect | image | clip | music | sfx | pause | say | unknown`. `unknown` cues are never spoken and must be resolved at G2 (under autopilot an unknown cue stops the run at G2, ADR-009).
- `source_span` lets the G2 page show each line in the context of the original file.

**Claims (`vcut.claims/2`)**, one entry per claim, adding to `/1`: `line_id` + word span; `verdict` ∈ `supported | partly | contradicted | not_found | unchecked`; `verdict_by` ∈ `ai | human`; `sources[]` with URL, retrieval date and a verbatim quote; and an optional `proposed_edit` `{ "line_id", "from", "to", "reason", "status": "pending | accepted | rejected" }`. G2 cannot be approved while any claim is `unchecked`, `contradicted` or `not_found` without an accepted edit or an explicit owner override.

### 3.10 project.yaml (setup options)
Written by the setup form ([[Vcut_Decision_Log#ADR-018 — Project setup options and autopilot]]); example in [[00_Brief_and_Orchestrator#`project.yaml` — the setup choices]]. Every field except `title` and the starting file has a default from `channel_profile.yaml`.

| Field | Type / values | Notes |
|---|---|---|
| `schema` | `vcut.project/1` | |
| `project_id` | `<YYYY-MM-DD>_<slug>` | Also the folder name |
| `title` | string | |
| `start_from` | `brief \| script \| script_with_cues` | Decides which 01 stages run (`modes`: brief = W, others = S) |
| `own_recording` | bool | `true` → 02 aligns `00_input/recordings/` instead of synthesising |
| `reviews` | map gate → `review \| auto` | G1_outline, G2_script, G3_media. G4 is always the owner |
| `autopilot` | bool | `true` overrides every `reviews` entry to `auto` and sets `editor.open_when_done` |
| `editor` | `{ target: resolve \| filmcraft, open_when_done: bool }` | Default `resolve`. The **one** editor 06 builds in (autopilot ends there); also decides which preset implementations and carriers 05 compiles |
| `ai` | map role → `antigravity \| claude_code \| claude_desktop \| hermes \| ollama:<model> \| cloud:<model> \| none` | Roles: drafting, tagging, vision |
| `voice` | `{ engine: qwen3_tts \| kokoro \| elevenlabs \| recording, voice_id, speed }` | |
| `style` | `{ preset, look, effect_density: low \| medium \| high, text_style }` | Ids from [[Vcut_Effects_Library]] |
| `media` | `{ sources: [...], article_captures: bool, generative: bool, photo_share: 0–1 }` | Sources from the Allow-list only |
| `length` | `{ target_min: [min, max] \| null }` | Optional for a script start |
| `money` | `{ budget_usd, autopilot_spend_limit_usd }` | 0 = free sources only |
| `output` | `{ captions, chapters, preview }` | bools |
| `privacy` | `cloud_allowed \| local_only` | `local_only` forbids cloud AI, cloud TTS and cloud generation |
| `created_by`, `created_at` | string | Recorded so auto-approvals can name who set the policy |

### 3.11 Effect presets
`libraries/effects/<category>/<preset_id>/preset.yaml` ([[Vcut_Decision_Log#ADR-020 — Documentary effects library]], [[Vcut_Decision_Log#ADR-021 — One editor: everything native and editable]]):
```yaml
schema: vcut.effect/2
id: txt.location_stamp
name: "Location stamp (typewriter)"
category: text                     # look | overlay | motion | transition | text | document | people | data
kind: title                        # title | transition | effect_stack | overlay_clip
track: V3                          # V3 titles · V4 overlay clips · the clip's own track for effect stacks
fields:                            # what a beat or the owner may set; defaults apply otherwise (text only, never times)
  place:    { type: string, max_chars: 40, required: true }
  position: { type: enum, options: [bottom_left, top_left, center], default: bottom_left }
duration_s: { default: 3.0, min: 1.5, max: 6.0 }
variants: [mono_white, amber]      # rotated by the variety rule
events:                            # the template's fixed animation timing, for SFX sync (code computes frames)
  first_char_frame: 4
  frames_per_char: 2
sfx: { category: typewriter, cue: per_character, file_pool: ["typewriter/key_*.wav"], end: "typewriter/carriage_return.wav" }
density: { max_per_min: 2, min_gap_s: 20 }
rights: { needs_rights_decision: false }
implementations:                   # one per editor; a missing editor = preset not offered there
  resolve:   { fusion_title: "resolve/vcut_location_stamp.setting", inputs: { place: "StyledText" } }   # input names checked at M0a
  filmcraft: { template: "filmcraft/vcut_location_stamp.fcgt", controls: { place: "place" } }
tested: { resolve: null, filmcraft: null }   # date of the last M0a/upgrade probe that built it
preview: preview.mp4
licence: { assets: owned_or_procedural }   # licences of bundled fonts, textures, overlay clips, in the ledger
```
- `implementations.<editor>` by `kind`:
  - `title` → Resolve `fusion_title` + input map; FilmCraft `template` + control map.
  - `transition` → Resolve `{ fcpxml: "cross_dissolve" }` (or an API name on Studio ≥21.1); FilmCraft `{ effect: "cross_dissolve" }`.
  - `effect_stack` → Resolve `{ drx: "resolve/….drx" }` or `{ lut: "….cube" }`; FilmCraft `{ commands: "filmcraft/effects.jsonl" }` (effect ids + params, values as `{placeholders}`).
  - `overlay_clip` → `{ media: "overlay_media/…", blend, opacity }`, the same for both editors.
- An implementation may say `{ baked: true }` only from M3, and only when the owner allowed opt-in pre-renders in the setup form.

---

## 4. Invalidation table
| Change | Re-run | Kept |
|---|---|---|
| Edit the script source file (Mode S) | 01a intake; 01b for changed lines (claims, beats); G2 re-approval of the diff; then as "edit text of line L" for each changed line | `line_id`s of unchanged sentences, their units, claims and slots |
| Change `instructions.md` | 01a settings mapping; whatever the changed setting feeds (e.g. duration check, voice → 02) | everything else |
| Change an AI role's provider or model | nothing for gate-pinned stages (01a, 01b, 03b keep their output with a pin warning; `vcut run --from <stage>` regenerates on purpose); unpinned stages that use the role re-run | everything else |
| Change the editor (`editor.target`) | 05 (implementations and carriers, e.g. ducking), 05b, 06 | script, voice, assets |
| Change a `project.yaml` option | from the first stage that reads it (e.g. `voice` → 02; `style`/`effect_density` → 03b effects, 05, 06; `editor` → 05, 06; `reviews`/`autopilot` → nothing re-runs, only pending gates change) | everything upstream |
| The owner edits a title, effect or transition in the editor | nothing re-runs; the change lives in the editor (07 diffs it for statistics) | everything |
| Change a preset in the library | 05, 05b, 06 for videos that use it (only on `vcut run`; never silently) | everything else |
| Edit text of line L (after G2) | that line's **unit** in 02 → re-quantise all anchors (05) → 06 new timeline version | every other unit, all sourced assets, slots not anchored to L |
| Change lexicon entry | units containing that token (02) | everything else |
| Swap a slot's chosen candidate | 03 fill for that slot → 05 → 06 | voice, other slots |
| Change brief budget / caps | G3 plan re-estimate | all produced artifacts |
| Change channel profile visual style | 03 base layer, 05, 06 | script, voice, stock |
| New pinned Resolve or FilmCraft version | M0a probe for that editor (every preset's `tested` date reset), then 05 (if a carrier changes) and 06 | all upstream |
