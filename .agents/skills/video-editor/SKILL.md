---
name: video-editor
description: One-entry-point video editor executing Jason Cooperson's cut-and-finish loop in FilmCraft or DaVinci Resolve Studio with house presets, code QA, honest truth reporting, and preset baking. Use when the owner says 'edit this video', or asks to cut, caption, grade or finish a video in FilmCraft or Resolve.
---

# Video Editor

> **Voice engine order (owner rule, 2026-11-07):** 1) **Voicebox** with the **Jessica from Ihateediting** profile (channel voice) → 2) **ElevenLabs** (fallback) → 3) **Edge TTS** (last resort). **Never Windows TTS (SAPI / System.Speech / pyttsx3)**, not even for placeholder or scratch tracks. Use a silent or tone placeholder plus estimated timing instead of a robotic voice.


One entry point for video editing across FilmCraft and DaVinci Resolve Studio.

## 0. Read First, CWD & Professional Timeline Organization
- **Working Directory:** All commands must run from the repository root: `E:\((_atWork_))\Ytube_Channel`. All tool paths use `Videos-Scripts/Video_Pipeline/tools/...`.
- **Adapter Reference:** Read `references/filmcraft.md` or `references/resolve.md` before executing NLE commands.

### Professional Project Bin Organization (7-Tier Hierarchy)
Never dump imported assets into the project root. Every asset in FilmCraft must be organized into its dedicated bin via `file.newBin` and `project.moveToBin`:
1. `01_Footage`: Primary A-roll, raw camera cards, host talking head.
2. `02_Audio`: External audio takes, sync speech, voiceover WAVs.
3. `03_B-Roll`: Cutaways, archival clips, screen captures, secondary footage.
4. `04_Graphics`: Lower thirds, title plates, chapter cards, quote pullouts (ProRes 4444 `.mov` with alpha).
5. `05_SFX`: Foley hits, whooshes, UI pops, camera shutter, paper slides (`.wav`).
6. `06_Music`: Ducked background music beds, ambient stems.
7. `07_Sequences`: Master cut sequences, sub-assemblies.

### Multi-Track Sequence Layout & Track Color Styling
Build sequences with 4 Video and 4 Audio tracks minimum (`video: 4, audio: 4`). Every track must be explicitly named and color-styled via `timeline.setTrack`:
- `V1`: `V1 - Primary / A-Roll` | Label: `Forest` (Green `#295c2d`)
- `V2`: `V2 - B-Roll / Inserts` | Label: `Cerulean` (Blue `#23535a`)
- `V3`: `V3 - Graphics / Titles` | Label: `Mango` (Orange `#803f17`)
- `V4`: `V4 - Overlays / Grain` | Label: `Lavender` (Purple `#6b1c82`)
- `A1`: `A1 - Dialogue / Sync` | Label: `Forest` (Green `#295c2d`)
- `A2`: `A2 - Sound Effects (SFX)` | Label: `Rose` (Pink `#801836`)
- `A3`: `A3 - Music Bed` | Label: `Violet` (Purple `#380ea7`)
- `A4`: `A4 - Ambience / Scratch` | Label: `Tan` (Brown `#6c5b47`)
- `C1`: `C1 - Captions / Subtitles` | Label: `Tan` (Captions `#c8b48a`)

### Role-Based Clip Color Coding
Every clip on the timeline and every media item in the bin must carry its standard editorial role color via `edit.label`:
- **A-Roll / Primary Dialogue (V1 / A1):** `Forest` (Green)
- **B-Roll / Cutaway Footage (V2):** `Cerulean` (Blue) or `B-Roll`
- **Motion Graphics / Lower-Thirds (V3):** `Mango` (Orange) or `Graphics`
- **Fullscreen Overlays / Grain / Transitions (V4):** `Lavender` (Purple) or `Visual Effects`
- **Sound Effects (A2):** `Rose` (Pink) or `Sound Effects`
- **Music Bed (A3):** `Violet` (Indigo) or `Music`
- **Ambience / Room Tone (A4):** `Tan` (Brown) or `Ambience`

### Timeline Markers & Chapter Architecture
Use FilmCraft markers (`markers.add`, `markers.addChapter`, `markers.addRange`) to provide professional timeline grooming and navigation:
1. **Chapter Markers (`Cyan`):** Placed with `markers.addChapter` at major section beginnings (Intro Hook, Core Story, Demo/Proof, Breakdown, Outro/CTA) with clear names for YouTube chapters.
2. **Edit Cut & Beat Markers (`Yellow`):** Placed with `markers.add` at kept edit boundaries carrying segment summary notes.
3. **Graphic / Sync Cue Markers (`Green` / `Blue`):** Placed at the exact frame where a lower-third, quote card, or B-roll snaps to spoken dialogue.
4. **SFX Impact Markers (`Rose` / `Magenta`):** Placed at the downbeat or visual impact frame where SFX hits trigger.
5. **Editorial Review / Warning Markers (`Red` / `Amber`):** Placed during QA to flag any tight trims, micro-pauses, or audio dips requiring review.

### Professional Editing Hygiene & Asset Ingestion
- **No External Pre-Clipping (Preserve Full Trim Handles):** When downloading or sourcing clips (via `youtube-downloader-analyzer`, web search, or stock) where only a portion will be used, **do not hard-clip or trim the media outside of FilmCraft prior to import**.
  - Keep and import the full downloaded video asset into the project bin (`03_B-Roll` or `01_Footage`).
  - Perform all clipping, trimming, and in/out point selection inside FilmCraft using `sourceIn` and `duration` on the timeline. This preserves complete media handles so the editor or human owner can extend, slip, or adjust the edit directly in the NLE at any time without re-downloading.
  - **Exception for Prohibitively Enormous Media:** If a source video is massive (e.g. multi-hour livestream, huge 4K file that would strain storage or bandwidth), download a section but **always include generous safety handles** (at least +15s to +30s of pre-roll and post-roll margin before and after the needed section) so that timing adjustments and crossfades remain possible inside FilmCraft.
- **Sync Integrity:** Video and sync audio must remain paired frame-for-frame with 0 drift.
- **Clean Boundaries:** Minimum cut duration is 6 frames. Zero 1-frame residual slivers.
- **Headroom & Leveling:** Dialogue on A1 mastered to -14 LUFS; SFX on A2 calibrated -12 to -18 dB relative to voice; Music on A3 ducked to -24 dB during speech.
- **Project Handoff:** Always set project notes via `project.setNotes` summarizing project name, source footage, fps, segment counts, and track layout.

## 1. Hard Rules & STOP Gates
1. **New Projects Only:** Create a fresh named project; never write into existing work.
2. **Owner Interactions & STOP Gates:** Ask the owner only for: startup choices, required app clicks, cut-list approval (STOP), cut_audit FAIL remedy decision (STOP), and preset bake approval (STOP).
3. **Fail Twice:** If any step fails twice, stop and report.
4. **No Redundant Transcription:** Check if `<dir>/words.json` exists. If copying cached words from elsewhere, place it at `<dir>/words.json` first (cache is path-keyed; confirm it matches the media). Never re-transcribe existing media. Pass `--force` only when re-timing manual cuts.
5. **Never Mutate Committed Presets:** NEVER pass `-UpdateTemplate` in editing runs. Every render writes to the project folder via `-Values` and `-Out`. Updating committed presets is strictly reserved for `bake-preset` on explicit owner approval.
6. **Licensing & Integrity:** Log every external asset in `03_clips/asset_registry.json` (pipeline) or `<dir>/asset_registry.json` (standalone). Zero deceptive bait (AGENTS.md §2).
7. **No Framerate Forcing:** Never pass `-r` to FFmpeg. Never flatten a cut into a single video clip.
8. **Professional Organization Mandatory:** Always initialize the 7 standard bins, 4V/4A color-styled tracks, clip role colors, and timeline markers on FilmCraft projects.
9. **Zero Pre-Clipping for NLE Media:** Never tight-clip external video downloads before importing into FilmCraft. Import full downloaded media (or padded with at least +15s to +30s handles if the file is massive) and perform all trimming on the NLE timeline.

## 2. Caveats to Say Out Loud
1. Waveform snap thresholds recalibrate on the first real owner voiceover.
2. Mixkit SFX are preview-quality MP3s; replace with master WAVs when requested.
3. Typography 56px/48px is an active taste call pending owner confirmation via `bake-preset`.
4. The LUT carries color only; grain and vignette must be applied separately (method `[DOCUMENTED-NOT-TESTED]`).
5. `flash_scan.py` is a software guideline screen (WCAG 2.3.1), not a certified broadcast Harding FPA test.
6. DaVinci Resolve grade automation is `[DOCUMENTED-NOT-TESTED]`; unverified Resolve calls are tagged `[UNVERIFIED]`.

## 3. Startup & Preflight
Ask the owner once, in a single message, for missing choices:
- (a) **NLE Target:** `FilmCraft` or `DaVinci Resolve Studio`. If Resolve: owner launches normally, waits past splash/Project Manager, external scripting enabled (`Preferences > System > General > External scripting = Local`), agent never starts Resolve, system Python 3.13 only. Run `python Videos-Scripts/Video_Pipeline/tools/build_cut_resolve.py --check`.
- (b) **Preset:** `documentary-default` (default) or `shorts-vertical` (for 9:16). *Note:* `shorts-vertical` has `render.ps1` at its root, outputs `renders/vertical_keyword_pop.mov/png`, inherits `documentary-default` (no grade/sfx folders); only keyword-pop is proven at 9:16; the 9:16 Resolve/FilmCraft timeline build is UNTESTED (values schema: `presets/documentary-default/keyword-pop/keyword-pop.json.example`, which `shorts-vertical/render.ps1` uses by default).
- (c) **Mode:** `Fast First Pass` (cut + graphics) or `Full Assembly` (+ grade, SFX, ducked music).
- (d) **Input Media:** Owner-recorded VO, Voicebox TTS (`take_01.wav`), or raw/archival footage (`talking_head.mp4`).

Run preflight check:
```bash
python Videos-Scripts/Video_Pipeline/tools/check_setup.py
```

## 4. Model & Effort Guidance
Follow AGENTS.md §5 for model routing: Opus = planning, final scripts, final rating; Sonnet = reviews only; Antigravity = all coding, research, fact-checks. (Jason: "Opus high = best; Sonnet = cheaper").

## 5. Step-by-Step Workflow

### Step 1: Transcribe & Correct
```bash
python Videos-Scripts/Video_Pipeline/tools/transcribe_groq.py --input <media> --out <dir>/words.json --corrections <dir>/transcript_corrections.json
```
If `<dir>/words.json` exists, cached words are reused.

### Step 2: Choose Cut & Secure Owner Approval
1. Inspect word indices:
   ```bash
   python Videos-Scripts/Video_Pipeline/tools/map_to_cut_time.py --words <dir>/words.json --list-words
   ```
2. Write `<dir>/keep.json`: `{"keep": [{"from_word": <i>, "to_word": <j>, "note": "..."}]}` (inclusive 0-based indices).
3. Generate cuts with waveform audio snapping:
   ```bash
   python Videos-Scripts/Video_Pipeline/tools/make_cuts.py --words <dir>/words.json --keep <dir>/keep.json --out <dir>/cuts.json --review <dir>/cuts_review.md --source <media>
   ```
4. Display `<dir>/cuts_review.md` and edit warnings to the owner.
5. **STOP:** Wait for explicit owner approval before building the timeline.

### Step 3: Build Timeline & Verify Frame-for-Frame (0 Drift)
- **FilmCraft:** Automatically builds with 7 standard bins (`01_Footage`..`07_Sequences`), 4V/4A styled tracks (`timeline.setTrack`), `Forest` role-colored clips (`edit.label`), and section/chapter markers (`markers.addChapter`, `markers.add`):
  ```bash
  python Videos-Scripts/Video_Pipeline/tools/build_cut_filmcraft.py --cuts <dir>/cuts.json --out <dir>/<slug>.fcproj --captions --words <dir>/words.json
  ```
- **DaVinci Resolve Studio:** (System Python 3.13 only)
  ```bash
  python Videos-Scripts/Video_Pipeline/tools/build_cut_resolve.py --cuts <dir>/cuts.json --project-name <slug>
  ```
  Both builders verify 0 frame drift. For Resolve, remind owner to confirm Playback frame rate in Project Settings.

### Step 4: Graphics from House Preset (NO -UpdateTemplate)
1. Write `<dir>/values_<family>.json` following schema in `Videos-Scripts/Video_Pipeline/presets/<preset>/<family>/<family>.json.example`.
2. Render ProRes 4444 alpha `.mov` into project folder:
   ```powershell
   powershell -NoProfile -File Videos-Scripts/Video_Pipeline/presets/<preset>/<family>/render.ps1 -Values <dir>/values_<family>.json -Out <dir>/graphics/<family>.mov
   ```
   *(For `shorts-vertical`: `render.ps1` is at preset root, `-Out <dir>/graphics/vertical_keyword_pop.mov`).*
3. Run automated graphics QA and per-frame alpha verification:
   ```bash
   python Videos-Scripts/Video_Pipeline/tools/graphics_qa.py --input <dir>/graphics/<family>.png --out-json <dir>/qa_graphics.json --out-md <dir>/qa_graphics.md
   python Videos-Scripts/Video_Pipeline/presets/documentary-default/verify_render.py --mov <dir>/graphics/<family>.mov --plate --out-json <dir>/qa_verify_render.json
   ```

### Step 5: Overlay Placement on CUT Timeline, Grade, SFX & Ducking (Full Mode)
1. **Map Anchor to Cut Timeline:**
   ```bash
   python Videos-Scripts/Video_Pipeline/tools/map_to_cut_time.py --cuts <dir>/cuts.json --words <dir>/words.json --word-index <idx>
   ```
   *Returns timeline time, ticks, and Resolve record frame. An anchor within 0.15 s of a kept range edge snaps to it (cuts are snapped into words, so the first word of a kept range may start slightly earlier). It errors only if the anchor is in removed material farther than that; pick a phrase inside a kept range or ask the owner to keep it.*
2. **Professional Asset Placement & Styling:**
   - **FilmCraft Graphics on V3:**
     Import asset into project, move to bin `04_Graphics`, set item label to `Mango`, place on `V3` via tick formula (`seconds * 254016000000`), and add a green cue marker on the timeline:
     ```powershell
     # Import & route to bin
     & "C:\Program Files\FilmCraft\filmcraft-cli.exe" --project <dir>/<slug>.fcproj --save import <dir>\graphics\<family>.mov
     # Inspect imported ID, move to bin 4 (04_Graphics), label Mango
     & "C:\Program Files\FilmCraft\filmcraft-cli.exe" --project <dir>/<slug>.fcproj --save exec project.moveToBin '{"items":[<item_id>],"bin":4}'
     & "C:\Program Files\FilmCraft\filmcraft-cli.exe" --project <dir>/<slug>.fcproj --save exec edit.label '{"items":[<item_id>],"label":"Mango"}'

     # Place on V3 and add sync marker in single JSONL run:
     # {"id":"timeline.place","params":{"item":<item_id>,"track":"V3","time":<timeline_ticks>,"duration":<dur_ticks>,"insert":false}}
     # {"id":"markers.add","params":{"target":"program","time":<timeline_ticks>,"name":"Gfx: <family>","comment":"<family> lower third / graphic in","color":"Green"}}
     & "C:\Program Files\FilmCraft\filmcraft-cli.exe" --project <dir>/<slug>.fcproj --save run place_graphics.jsonl
     ```
   - **FilmCraft B-Roll on V2 (Full Handles):**
     Import full unclipped downloaded asset into `03_B-Roll`, set item label to `Cerulean`, and place on `V2` with non-destructive in/out points (`sourceIn`, `duration`). Never hard-crop externally prior to import.
   - **FilmCraft SFX on A2:**
     Import sound effect, move to bin `05_SFX`, set item label to `Rose`, place on `A2` (`track:"A2"`, omit `audioTrack`), and add hit marker:
     ```powershell
     & "C:\Program Files\FilmCraft\filmcraft-cli.exe" --project <dir>/<slug>.fcproj --save import <sfx_path>.wav
     & "C:\Program Files\FilmCraft\filmcraft-cli.exe" --project <dir>/<slug>.fcproj --save exec project.moveToBin '{"items":[<sfx_item_id>],"bin":5}'
     & "C:\Program Files\FilmCraft\filmcraft-cli.exe" --project <dir>/<slug>.fcproj --save exec edit.label '{"items":[<sfx_item_id>],"label":"Rose"}'
     # Place on A2: {"id":"timeline.place","params":{"item":<sfx_item_id>,"track":"A2","time":<sfx_ticks>,"duration":<sfx_dur_ticks>,"insert":false,"video":false,"audio":true}}
     # Marker: {"id":"markers.add","params":{"target":"program","time":<sfx_ticks>,"name":"SFX: <name>","color":"Rose"}}
     ```
   - **FilmCraft Music on A3:**
     Import music track, move to bin `06_Music`, set item label to `Violet`, place on `A3` (`track:"A3"`, omit `audioTrack`).
   - **DaVinci Resolve:** (System Python 3.13) Add track `V3` if needed, then append via scripting API:
     ```python
     while tl.GetTrackCount("video") < 3: tl.AddTrack("video")
     mp.AppendToTimeline([{"mediaPoolItem": item, "trackIndex": 3, "recordFrame": resolve_record_frame, "mediaType": 1}])
     ```
3. **Grade:**
   - **FilmCraft:** Import and apply preset to sequence video clips (clip IDs from `inspect sequence`):
     ```json
     {"id":"presets.import","params":{"path":"E:/((_atWork_))/Ytube_Channel/Videos-Scripts/Video_Pipeline/presets/documentary-default/grade/house-style.fcpreset"}}
     {"id":"presets.apply","params":{"preset":"HouseStyle_Documentary","clips":[10,13,16,19,22]}}
     ```
   - **Resolve:** Apply `house-look.cube` LUT `[UNVERIFIED / DOCUMENTED-NOT-TESTED]`. Spatial grain and vignette must be applied separately via node graph or V4 35mm grain overlay.
4. **Ducking:**
   - **FilmCraft Native:** `essentialSound.setType` (dialogue, music) + `essentialSound.generateDucking` (fixed -15 dB, 0.8s release, no attack ramp).
   - **FFmpeg Recipe (Default for Documentary VO):** Two-level sidechain ducking (-24 dB dialogue / -28 dB soundbites, 100ms attack).

### Step 6: Automated QA Verification & Cut Audit STOP
Run all forensic QA scripts (do not abort on non-zero exit; `cut_audit.py` exits 1 on FAIL):
```bash
python Videos-Scripts/Video_Pipeline/tools/render_cut_ffmpeg.py --cuts <dir>/cuts.json --out <dir>/cut_render.mp4
python Videos-Scripts/Video_Pipeline/tools/cut_audit.py --media <dir>/cut_render.mp4 --cuts <dir>/cuts.json --out-json <dir>/qa_cut_audit.json --out-md <dir>/qa_cut_audit.md
python Videos-Scripts/Video_Pipeline/tools/dead_air_qa.py --media <dir>/cut_render.mp4 --out-json <dir>/qa_dead_air.json --out-md <dir>/qa_dead_air.md
python Videos-Scripts/Video_Pipeline/tools/flash_scan.py --media <dir>/cut_render.mp4 --out-json <dir>/qa_flash.json --out-md <dir>/qa_flash.md
python Videos-Scripts/Video_Pipeline/tools/stem_loudness.py --input <dir>/cut_render.mp4 --out <dir>/stem_loudness.txt
```
*Note: `cut_audit.py` inspects interior edit boundaries; head and tail are not audited.*
**STOP:** If `cut_audit.py` returns FAIL, present the remedy to the owner (apply 2-frame crossfade in NLE vs move keep boundary = changes the sentence). The owner must decide the remedy.

### Step 7: Export Master & Comprehensive Truth Report
1. **Export Master Video:**
   - **FilmCraft:**
     ```powershell
     & "C:\Program Files\FilmCraft\filmcraft-cli.exe" --project <dir>/<slug>.fcproj exec file.exportMedia '{"path":"<dir>/master.mp4","format":"h264","loudnessLufs":-14.0,"wait":true}'
     ```
   - **DaVinci Resolve:**
     ```python
     proj.SetCurrentRenderFormatAndCodec("mp4", "H264")
     proj.SetRenderSettings({"TargetDir": "<dir>", "CustomName": "master"})
     job = proj.AddRenderJob()
     proj.StartRendering(job)
     while proj.IsRenderingInProgress(): time.sleep(0.5)
     ```
2. **Master QA Run:** Re-run `stem_loudness.py`, `dead_air_qa.py`, `flash_scan.py`, and `cut_audit.py` against exported `master.mp4`.
3. **Truth Report:** Write `<dir>/truth_report.md` using `references/truth_report.md`.

### Step 8: Bake Learnings
When owner requests styling, timing, or loudness changes, run `bake-preset` (`.agents/skills/bake-preset/SKILL.md`). Preset updates require a shown diff and explicit owner approval.

## 6. Specialized Follow-up Workflows

### A. Asset Placement by Transcript Anchor & B-Roll Trimming
When owner says: *"At the part where I say '<phrase>', place <asset>"*:
1. Find word index in `words.json` or source timestamp.
2. Run `map_to_cut_time.py` to get cut-timeline position.
3. Import full unclipped media into `03_B-Roll` (or padded with $\ge$ 15s–30s handles if massive).
4. Place on `V2` (B-roll) or `V3` (graphics) with `sourceIn` and `duration` so the clip can be slipped, rolled, or extended inside FilmCraft at will.

### B. Manual Cut Re-Timing
When owner makes a manual edit in NLE:
1. Export updated audio from NLE.
2. Re-run `transcribe_groq.py` with `--force` on modified audio.
3. Re-build captions via `build_cut_filmcraft.py --captions` or re-import `words.srt` into Resolve.

## 7. Full narrated documentary build (proven on video 19, 2026-11-07)
For a script-driven edit (TTS narration + stills + soundbites), use the plan-driven builder instead of the cut engine:
`Videos-Scripts/Video_Pipeline/tools/build_full_edit.py` with an `edit_plan.py` next to it (copy both from `19_Child_Stars_Who_Quit_Hollywood_And_Never_Came_Back/07_Video_Edit/Full_Edit_v1/Source/`).
- Narration: one Voicebox WAV per paragraph (Jessica), each placed as its own A1 clip trimmed to speech, clip gain to -16 LUFS. Years spelled out for TTS ("nineteen seventy"), names respelled (Ke Huy Quan -> "Kay Hwee Kwan"), quotation marks removed.
- QA every paragraph: transcribe the VO timeline and diff against the script; Voicebox swaps or repeats words (seen: "won supporting best actor", "1970 1970"). Re-render those paragraphs.
- Soundbites: split a VO paragraph at a word so the real speaker finishes the sentence (e.g. VO "he thanked" -> Ke Huy Quan "my Goonies brother for life, Jeff Cohen").
- Stills: Ken Burns via `effects.setParam` motion `scale`/`position` keyframes (`time` = timeline ticks, `keyframe: true`), 10-frame cross dissolves.
- Graphics: anchors resolved from word timings; never stack a graphic on a chapter card; overlapping graphics go to V4. A graphic that points at something in an image (photo-annotation, group-legend) must sit on that image's span only.
- Music: per-chapter Kevin MacLeod beds, crossfaded, two-level sidechain ducked by FFmpeg, one stem on A3.

## 8. Editable-graphics standard (owner rule, 2026-11-07)
- **Titles/overlays must be editable inside FilmCraft.** Build them as NATIVE FilmCraft Graphic clips (live text + shape layers) with `Videos-Scripts/Video_Pipeline/tools/fc_native_gfx.py`, driven through a live engine session (`tools/fc_session.py`, wraps `filmcraft-cli mcp` so clip/layer ids come back). Rendered EffectCraft `.mov` graphics are now preview/QA only.
  - Plates are shape layers PINNED to their text (`graphics.pin`): edit the text and the plate resizes.
  - Animation = layer keyframes (`graphics.set` with `time` + `keyframe:true`) inside `graphics.setResponsiveTime` intro/outro, so trimming keeps in/out moves.
  - Multi-part text (quote + attribution, emphasis words, tracker items) = one layer with `graphics.setCharStyle` ranges, so edits reflow.
  - Portrait panels: real image clips on their own tracks (motion scale + crop), names/frames on the graphic.
  - One template per family is exported to `presets/documentary-default/filmcraft_templates/House_<family>.fcgt` (needs an explicit `path`).
  - Overlapping graphics: next lane up; `graphics.newText` fails with "Vn is not free here" when the track is occupied.
- **Atmosphere FX** from `E:\((Video_Editing_Asset_Library))\(( Video Overlays & Effects Library ))\01_Dust_Particles_Atmosphere`: film35 (grain, 40%), specks (dust, 55%), softlight (light, 32%), all `effects.setParam opacity blend "Screen"`, fill frame, 0.6 s opacity fades, on their own V tracks under the graphics. Grain on period stills (archival eras), specks on reconstructions, soft light on emotional beats; never over modern interview clips. Loop the 3-8 s library clips to 5 min copies in the edit folder (library untouched).
- **Alternatives tracks:** every alternative image the researcher found for a shot (other A1/A2/A3 of the same SHOT, other picks of the same search gap) goes on hidden tracks V9-V11 ("ALT A/B/C", `timeline.setTrack enabled:false`) at the same time as the chosen image, plus bin `03b_Alternatives`, so the owner can drag a swap onto V1.
- Reference build: `Videos-Scripts/Video_Pipeline/tools/build_v2_editable.py` (video 19).

## 9. Timing & shot-choice rules (owner feedback, 2026-11-08)
1. **Text cards leave with their narration.** A graphic about a paragraph ends before the narration moves to the next paragraph (`clamp_graphic` in `build_full_edit.py`). A short paragraph may borrow the NEXT narration paragraph only, never a soundbite or a chapter card. Only deliberate spans (the "Reconstruction" label over a whole dramatized scene) may run longer, and only via an explicit `Hold: "auto:<last paragraph>"`.
2. **Soundbites never start or end mid-sentence.** Every interview clip is snapped by `Video_Pipeline/tools/soundbite_bounds.py`: first word starts a sentence, last word ends one, and each cut sits at the quietest 10 ms between two words (Whisper word times drift, so the gap is checked on the waveform). Speakers often run sentences together with no pause: a timestamp a few hundredths early still catches the previous word ("...too. And when people..."). Only a deliberate hand-over from a VO line (`split`) may start mid-sentence, and it still cuts between words. If a pre-cut source file ends inside a word, keep only the complete sentences (or re-download the full source).
3. **Verify every soundbite by ear-proxy:** extract the exact cut and re-transcribe it; the transcript must begin and end on whole sentences.
4. **Never show two pictures of the same idea back to back** (two rotary phones on one line). Alternatives of one idea (same research group + near-identical subject) are merged into one shot; the other goes to the hidden ALT tracks. Different places or people from one research beat (Berkeley -> UCLA -> Beverly Hills) stay separate shots.
5. **No still holds longer than ~10 s** unless a graphic covers it; break long holds with a relevant second image.

## 10. Beat edit, blur under text, maps (owner rules, 2026-11-08 — video 21 v2 feedback)
The v2 build placed 2-3 alternatives per *shot* across whole paragraphs; the owner saw A-B-A-B ping-pong, pictures before they were mentioned, and almost no footage. The narrated build is now beat-driven:
1. **Beats:** `python Video_Pipeline/tools/make_beats.py --layout Source/layout.json --words Source/vo_timeline.words.json --out Source/beats.json [--lock a-b ...]` (one beat = one sentence or half-sentence, 2.5-7 s). `--lock` = ranges the owner already fixed by hand; never overwrite them.
2. **One visual per beat, placed on its words** (start = beat start). Research follows internet-media-search §1A and returns `Source/assignments.json`. Footage >= 40 %, muted B-roll, every visual once, never A-B-A, stills <= 8 s.
3. **Gate before building:** `python Video_Pipeline/tools/beats_qa.py --beats Source/beats.json --assign Source/assignments.json --out qa/qa_beats.md` must PASS.
4. **Build on the owner's latest project, not from scratch:** when the owner has edited the project, back it up (`*_OWNER_EDIT_<date>.fcproj`), diff its V1 against the plan, keep the owner's clips (lock their ranges) and rebuild only the rest: `Source/build_v3_beats.py --src <owner.fcproj> --out <v3.fcproj> --lock ... --export` (video 21 reference). Audio, graphics, captions and markers stay untouched.
5. **Blur under full-screen text:** when a quote card / kinetic quote / stat / article card / then-now / credit line is on screen, the V1 picture under it gets FilmCraft **Gaussian Blur** (`effects.apply` `gaussian_blur`, `blurriness` keyframes): 0 -> 18 over 0.35 s as the text arrives, held, then back to 0 over 0.25 s right after the text leaves. Lower thirds and location stamps do not blur.
6. **Maps:** places that matter (moves, trips, where an event happened) get an AniMaps clip on their beat (`D:\((_atWork_))\360-Viewer-Project\AniMaps`, `node scripts/agent-runner.mjs ... --output x.webm`, then ffmpeg to H.264 mp4). Plan them in `Source/maps_plan.json` (`beat`, `name`, `args`).
7. **Review the result by frames, not by report:** sample one frame per beat around the first and last 2 minutes plus every 30 s, tile them, and look for repeats, early pictures and wrong subjects before handing over.
