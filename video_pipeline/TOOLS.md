# Deterministic Tools Catalog & Boundary Guide

This catalog strictly separates **deterministic CLI tools** (mechanical execution: downloads, media transforms, audio normalization, custom graphics rendering, hashing) from **agent intelligence** (creative writing, outline architecture, research synthesis, review scoring).

> **Core Rule:** Never spawn an AI agent for work handled by a CLI tool or deterministic script.

---

## 1. Verified Local Tools (Directly Executed & Confirmed)

| Tool / Binary | Location / Command | Observed Version / Status | Stages | Purpose & Confirmed Capabilities |
|---|---|---|---|---|
| **`ffmpeg.exe`** | `C:\Users\ELITE\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe` | **VERIFIED**<br>`v7.1.1-full_build` | 05, 07, 07b, 08, 10 | Loudness normalization (`-af loudnorm=I=-16:TP=-1.8:LRA=11`), 1080p/30fps video conform, chapter WAV concat demuxer (`-f concat -safe 0`), two-level dynamic sidechain ducking (`sidechaincompress` with `amix normalize=0`: -24 dB relative to speech / -28 dB relative to scored clips), forensic EBU R128 loudness measurement with true peak (`-af ebur128=framelog=verbose:peak=true`), stem loudness verification (`stem_loudness.txt`), contact sheet generation (`hstack`/`tile`), and master muxing (libx264 + AAC 320k). (Tested on 2026-10-31 / 2026-11-01.) |
| **`yt-dlp.exe`** | `C:\Users\ELITE\AppData\Local\Programs\Python\Python313\Scripts\yt-dlp.exe` | **VERIFIED**<br>`2026.08.19` | 01, 02, 07 | JSON metadata dump (`--dump-json`), comments scraping (`--write-comments`), auto subtitles (`--write-auto-subs`), section clipping (`--download-sections`). Uses `--cookies-from-browser firefox` and Node EJS solver. |
| **`python.exe`** | `C:\Users\ELITE\AppData\Local\Programs\Python\Python313\python.exe` | **VERIFIED**<br>`Python 3.13.7` | All (01–10) | Deterministic script automation, SHA-256 hash checks, text sanitization, timing parsing. Mandatory for DaVinci Resolve Studio automation (uv 3.11/3.12 segfaults). |
| **`node.exe`** | `C:\Program Files\nodejs\node.exe` | **VERIFIED**<br>`v22.19.0` | 02, 07 | Runtime for yt-dlp challenge execution and JavaScript script transforms. |
| **`Pillow`** (PIL) | System Python 3.13 environment | **VERIFIED**<br>`10.4.0` / `13.0.0` compatible | 07, 07b, 08, 09 | Aspect-ratio letterboxing, image resizing, contact sheet compositing, thumbnail plate generation, mechanical 120px scale render. |
| **`filmcraft-cli`** | `C:\Program Files\FilmCraft\filmcraft-cli.exe` | **VERIFIED on fresh project**<br>`filmcraft-cli 0.15.0` | 06, 08 | Headless NLE driver. Verified: `exec file.newProject`, `exec file.newSequence`, `import`, `exec timeline.place` (ticks), `exec sequence.applyVideoTransition`, `exec effects.setParam`, `effects.setInterpolation` (eased keyframing), Lumetri LUT application (`lumetri.setInputLut`), native auto-ducking (-15 dB, zero attack ramp), and top-level `loudnessLufs` export (-14.1 LUFS). Zero built-in text presets. |
| **`FilmCraft Bridge`**| `filmcraft.exe --control 8080` / `filmcraft-cli --bridge` | **VERIFIED**<br>`0.15.0` | 08 | Live GUI control bridge authenticated with 64-hex `$env:FILMCRAFT_CONTROL_TOKEN`. Enables headless read-back and mutation on running GUI. |
| **`FilmCraft MCP Server`**| `filmcraft-cli mcp` | **UNEXERCISED / DOCUMENTED**<br>`0.15.0` | 08 | MCP wrapper over bridge commands registered in Antigravity config for interactive inspection. |
| **`effectcraft-cli`**| `C:\Program Files\EffectCraft\effectcraft-cli.exe` | **VERIFIED**<br>`0.19.0` | 07b, 08 | Motion graphics template compiler and renderer. Verified: JSX Bezier easing (`KeyframeEase`), template values injection, left-justified text layout without edge clipping, and ProRes 4444 RGBA `.mov` rendering for house presets. |
| **`DaVinci Resolve Studio`**| `C:\Program Files\Blackmagic Design\DaVinci Resolve\Resolve.exe` | **VERIFIED**<br>`Studio 20.0.1.6` | 08, 10 | Professional NLE target. Scripting verified via system Python 3.13 (`fusionscript.dll`). Supports deterministic timeline generation via single `AppendToTimeline` and frame-accurate verification. Playback frame rate set manually in Project Settings. |
| **`Resolve MCP`** | `tools/vendor/davinci-resolve-mcp` | **VERIFIED**<br>`samuelgursky v4.18.2` | 08 | 37 compound tools registered in `.mcp.json` and gemini config. Used for interactive timeline queries, grading inspection, and editor assistance while Resolve Studio is open. |
| **`estimate_timing.py`** | `Videos-Scripts/Video_Pipeline/tools/estimate_timing.py` | **VERIFIED**<br>`Python 3.13` | 05 | Narration timing estimator at calibrated rate (158 WPM). Generates `timing.json` matching canonical Vcut §3.2 schema (`vcut.timing/1`: `start_s`/`end_s`, `line_id`, `chapter_id`, list `qc`, `units`, `words`, `chapters`), `"estimated": true`, and outline chapter ingestion (`--outline` / `--chapters-dir`). Tested 2026-11-01. |
| **`make_placeholder_vo.py`** | `Videos-Scripts/Video_Pipeline/tools/make_placeholder_vo.py` | **VERIFIED**<br>`Python 3.13 + wave` | 05 | Generates calibrated 48000 Hz 16-bit mono PCM silent WAV placeholder for Voicebox bypass. Tested 2026-11-01. |
| **`stem_loudness.py`** | `Videos-Scripts/Video_Pipeline/tools/stem_loudness.py` | **VERIFIED**<br>`Python 3.13 + ffmpeg` | 08, 10 | Forensic EBU R128 audio stem loudness report generator (`stem_loudness.txt`). Measures Integrated LUFS, LRA, and True Peak. Tested 2026-11-01. |
| **`render_callout.py`** | `Videos-Scripts/Video_Pipeline/tools/render_callout.py` | **VERIFIED**<br>`Python 3.13 + Pillow` | 07b | Custom character introduction callout renderer. Generates face-safe 1080p RGBA PNG overlay cards (Ivory `#F3EBDD` / Gold `#FFE8B8` glass backplate). Verified on `callout_sample.png` 2026-11-01 with prominent high-contrast sample watermark badge. |
| **`render_map.py`** | `Videos-Scripts/Video_Pipeline/tools/render_map.py` | **VERIFIED (All 6 Types)**<br>`Python 3.13 + Pillow` | 07b | Geographically accurate cartography renderer using real Natural Earth 1:50m Vector Data (Public Domain). Conformal Mercator projection with equal-scale axes (identical scale k in px/rad), Pillow polygon rasterizer with viewport clipping, collision-avoiding pin labels, computed haversine distances, projection-computed scale bar, and transparent overlay mode (`--alpha-overlay`). |
| **`render_article.py`** | `Videos-Scripts/Video_Pipeline/tools/render_article.py` | **VERIFIED**<br>`Python 3.13 + Pillow` | 07b | Custom article display and text highlight renderer. Generates newspaper/press plate with exact character substring highlight geometry (no line overflow), solid black redaction boxes (`--redact`), and sweep frames. Verified on `article_sample.png` 2026-11-01. |
| **`render_card.py`** | `Videos-Scripts/Video_Pipeline/tools/render_card.py` | **VERIFIED**<br>`Python 3.13 + Pillow` | 07b | Custom card renderer for date strips (`time.timeline_bar`), angled document stamps (`txt.stamp`), metric counters (`txt.big_number`), kinetic keywords (`txt.keyword_pop`), and chapter cards (`txt.chapter_title`). Tested 2026-11-01. |
| **`write_graphics_manifest.py`** | `Videos-Scripts/Video_Pipeline/tools/write_graphics_manifest.py` | **VERIFIED**<br>`Python 3.13 + Pillow` | 07b | Scans graphics directory, classifies transparent overlays vs full-frame plates based on intended role and alpha channel, resolves licences from ledger/registry, computes SHA-256 hashes, and writes `graphics_manifest.json`. Tested 2026-11-01. |
| **`photocraft-cli`**| `C:\Program Files\PhotoCraft\photocraft-cli.exe` | **VERIFIED** (CLI binary confirmed)<br>`0.18.0 (8a87a457a)` | 08, 09 | Non-destructive image layer operations, color grading, thumbnail plate processing. |
| **`voicebox_cli.py`** | `.agents/skills/voicebox/scripts/voicebox_cli.py` | **VERIFIED** (CLI verified; daemon required) | 05 | Local neural TTS CLI. Options verified with `--help`: `--max-chunk-chars 800`, `--crossfade-ms 50`, `--instruct`, `--profile`. Probing `--status` and `--profiles` confirmed daemon status check. When daemon offline, bypass policy takes over (estimated timing + placeholder track). |
| **`vcut CLI`** | `uv run --directory "E:\((_atWork_))\Vcut\" vcut` | **VERIFIED** (`--help` confirmed) | 08 | Click CLI with `approve`, `board`, `new`, `run`, `status`. Invoked via `uv run`. |

---

### AI Video Editor Engine (Revision 2026-11-01)
All scripts in `Videos-Scripts/Video_Pipeline/tools/`. System Python 3.13 only (uv 3.11/3.12 segfault with Resolve). Run with `PYTHONUTF8=1`.

| Tool | Status | Purpose | Command |
|---|---|---|---|
| `transcribe_groq.py` | **VERIFIED WITH CAVEATS** | Word-timed ASR via Groq whisper-large-v3. Gap/hallucination repair on turbo, `--corrections` vocabulary fixes, `--repair-only` appends to existing repairs logs. 429 handled with `retry-after`. Caveat: cache is keyed on path only, not media hash. | `python transcribe_groq.py --input media.mp4 --out words.json [--corrections c.json] [--no-repair]` |
| `make_cuts.py` | **VERIFIED WITH CAVEATS** | `words.json` + `keep.json` -> `cuts.json` + `cuts_review.md`. Frame-snapped at source's exact rational fps, exclusive end frames, 6-frame minimum. Waveform snap on by default. Caveat: snap thresholds (80ms slop, -35 dBFS floor) calibrated on clean documentary speech. | `python make_cuts.py --words words.json --keep keep.json --out cuts.json [--no-snap] [--snap-audio media]` |
| `map_to_cut_time.py` | **VERIFIED** | Source seconds or word index -> cut-timeline seconds and frames using `cuts.json`. Errors if anchor falls in removed material. Includes `--list-words` helper. | `python map_to_cut_time.py --cuts cuts.json --words words.json --word-index N` / `--list-words` |
| `render_cut_ffmpeg.py` | **VERIFIED** | Fallback MP4 preview: single trim/atrim -> concat filtergraph, H.264+AAC, `-fps_mode passthrough`, ffprobe frame-count and A/V (1.5-frame) verification. | `python render_cut_ffmpeg.py --cuts cuts.json --out cut.mp4` |
| `build_cut_filmcraft.py` | **VERIFIED** | New `.fcproj`, V1+A1 placed back to back, verified frame for frame (clips, srcIn, total, sequence fps), writes `<stem>_build_report.json`, exit 1 on drift. `--captions` builds captions from `words.json`. | `python build_cut_filmcraft.py --cuts cuts.json --out p.fcproj [--captions --words words.json]` |
| `build_cut_resolve.py` | **VERIFIED WITH CAVEATS** | New Resolve Studio project, fps set before timeline, single `AppendToTimeline`, verified on V1+A1 with contiguity from 01:00:00:00. Caveat: system Python 3.13 only; Playback frame rate set manually by owner. | `python build_cut_resolve.py --check` / `--cuts cuts.json --project-name zz_x [--delete-project]` |
| `cut_audit.py` | **VERIFIED WITH CAVEATS** | Audio at each interior edit (40 ms either side): speech energy > -28 dBFS, step click, spectral jump. Prints remedy per failing edit. Caveats: interior edits only; head and tail not audited; exit 1 on FAIL. | `python cut_audit.py --media cut.mp4 --cuts cuts.json` |
| `dead_air_qa.py` | **VERIFIED** | Silences longer than N s (default 0.6s), trailing silence included, `--allowed-pauses` JSON. | `python dead_air_qa.py --media cut.mp4` |
| `flash_scan.py` | **VERIFIED WITH CAVEATS** | Photosensitivity screen modelled on WCAG 2.3.1: > 3 flashes in any 1s. Caveat: software screening guideline only, not certified hardware Harding FPA test. | `python flash_scan.py --media cut.mp4` |
| `graphics_qa.py` | **VERIFIED WITH CAVEATS** | Overlay PNG bounding box vs canvas edges and 90% title-safe area. Caveat: cap-height check passes trivially on plate families; build-time 45px floor is true guard. | `python graphics_qa.py --input folder_or_png` |
| `check_setup.py` | **VERIFIED** | One line per component (FFmpeg, Python, FilmCraft, EffectCraft, Resolve Studio, scripting, Groq key, Voicebox). Installs nothing. | `python check_setup.py` |
| `tests/run_qa_selftests.py` | **VERIFIED** | 25-case matrix with planted defects, asserting exit codes and reason strings; runs `make_cuts` and `transcribe_groq` selftests. | `python tests/run_qa_selftests.py` |

---

### Pacing, Still-Hold & Edit-Report Tooling (Revision 2026-11-09)
All in `Videos-Scripts/Video_Pipeline/tools/`, numbers in `presets/pacing/*.json`. System Python 3.13 + Pillow; `ffmpeg`/`ffprobe` only for `--media` scans and video probing. Self-test: `python tests/run_pacing_selftests.py` (**69/69 cases pass**).

| Tool | Status | Purpose | Command |
|---|---|---|---|
| `pacing_lib.py` | **VERIFIED** | Shared library: preset/motion/catalog loaders, plan loaders (shot plan or beats+assignments), still-run builder, caps, `pick_motion`, `rect_to_scale_pos` | `import pacing_lib` |
| `color_script.py` | **VERIFIED (self-tests + FilmCraft-measured looks; not yet run on a real video)** | Colour script ([COLOR_SCRIPT.md](COLOR_SCRIPT.md)). `plan`: validates `color_script.json` (story logic, phases by beat id tiling every beat, 4-8 phases, >= 20 s per phase, subtle dE budget, cut shifts need a reason, callbacks, motifs), then per shot: phase look, stepped blend at cuts, protection (archival, documents, faces, B&W/toned prints, plates never graded), cast correction, `grade_adjust`; writes `color_assign.json`, `color_plan.md`, one `.fcpreset` per look and with `--measure` a FilmCraft-measured `.cube` per look. `qa`: strip (+ look-direction row, + rendered row with `--video`), phase sheet, 70 % over-grade strip, `TEXT_CONTRAST` / `CLIPPING` / `SKIN` FAIL, `NEIGHBOR_JUMP` / `RENDER_DRIFT` WARN. Exit 0/1/2 | `python color_script.py plan --script color_script.json --shot-plan shot_plan.json --assets-root 03_media --out-dir color --measure` · `python color_script.py qa --assign-file color/color_assign.json [--video cut.mp4] --out-dir color` |
| `color_lib.py` | **VERIFIED** | Colour maths (Lab, dE, WCAG), look offsets, clamps, blends, protection, Lumetri preset writer, analytic preview (0.82 dE mean from FilmCraft), FilmCraft LUT measurement, `.cube` read/write, image stats. Self-test: `python tests/run_color_selftests.py` (**45/45 cases pass**) | library |
| `still_hold_qa.py` | **VERIFIED** | Still-hold budget: FAIL on a still run over its hard cap, over the soft cap without enrichment events, a still without motion, a picture shown twice; owner waivers (only with the owner's `--allow-waivers`); plate checks (`PLATE_HOLD`, untyped plates, dummy-card resets ignored); heuristic rendered-video scene-gap scan. Exit 0/1/2 | `python still_hold_qa.py --shot-plan shot_plan.json [--assets-report asset_audit.json] [--media cut.mp4]` or `--beats beats.json --assign assignments.json [--beat-map beat_map.json]` |
| `asset_audit.py` | **VERIFIED** | (`--assets-root` for relative names, `--registry asset_registry.json` to map `pexels:123` / `owner:img_01` refs to conformed files) Resolution after the planned push, aspect, perceptual duplicates, blank/corrupt/missing files, coverage deficit, `research_requests.json`. Exit 0/1/2 | `python asset_audit.py --assets-dir 03_media/conformed --shot-plan shot_plan.json --out-json asset_audit.json --requests-out research_requests.json` |
| `variation_report.py` | **VERIFIED** | Motion / transition / SFX / enrichment variation rules + `edit_report.md` with rationale table and owner feedback block. Exit 0/1/2 | `python variation_report.py --shot-plan shot_plan.json --out-md edit_report.md --out-json variation_log.json` |
| `make_beats.py` | **VERIFIED** | Narrated timeline -> beats (2.5-6 s, one visual per beat; default max lowered from 7.0 to 6.0 on 2026-11-09) | `python make_beats.py --layout layout.json --words words.json --out beats.json` |
| `beats_qa.py` | **VERIFIED** | Beat plan program checks; `--max-still` default lowered from 8.0 to 6.0 on 2026-11-09 and understands assignment `sub` visuals | `python beats_qa.py --beats beats.json --assign assignments.json` |
| `build_full_edit.py` | **VERIFIED (video 19 reference builder)** | 2026-11-09: hold cap overrides the same-idea merge, writes `still_hold_warnings.json`, Ken Burns moves come from the motion library (`motion_log.json`). Not re-run end to end after the patch (needs FilmCraft + `edit_plan.py`); merge logic tested in isolation. **Known divergence:** it still puts a 10-frame dissolve on every V1 cut, which breaks the Toolkit's 85 % hard-cut default (`variation_report.py` would warn `CUT_SHARE`); owner decision pending | `python build_full_edit.py fcproj` |
| `reframe_9x16.py`, `make_variant.py`, `suggest_chapters.py`, `thumb_candidates.py` | **[TO BUILD]** | Specified in `DERIVATIVES.md` | n/a |

### House Presets & Template Tooling (Revision 2026-11-01)
Located in `Videos-Scripts/Video_Pipeline/presets/`. Built and verified in T3b.

| Tool / Script | Status | Purpose & Usage |
|---|---|---|
| `presets/<preset>/<family>/render.ps1` | **VERIFIED** | Renders values JSON -> ProRes 4444 alpha `.mov` + reference PNG into project folder. Call with `-Values <file> -Out <file.mov>`. NEVER pass `-UpdateTemplate` during normal edits. |
| `presets/shorts-vertical/render.ps1` | **VERIFIED** | Root render script for 9:16 vertical keyword pop. Renders into `renders/vertical_keyword_pop.mov`. |
| `presets/documentary-default/check_style.py` | **VERIFIED** | Validates `style.json` schema, 102 leaf keys, typography ratios, color contrasts, and asset references. |
| `presets/documentary-default/verify_render.py` | **VERIFIED** | Frame-by-frame alpha channel, text hold, and safe-margin audit on rendered `.mov` files (`--plate`). |
| `presets/documentary-default/grade/build_grade.py` | **VERIFIED** | Compiles grade parameters into `.cube` 3D LUT (`house-look.cube`) and FilmCraft preset (`house-style.fcpreset`). |
| `presets/documentary-default/grade/measure_grade.py` | **VERIFIED** | Verifies color transform accuracy, contrast curves, and gamut boundaries of compiled LUTs. |
| `presets/documentary-default/sfx/sfx_tool.py` | **VERIFIED** | Audio utility for normalizing, cataloging, and testing SFX hits, whooshes, and paper slides in `sfx.json`. |

---

## 2. Voicebox Voice profiles & Owner Rating Table

Source: `E:\((_atWork_))\Ytube_Channel\.agents\skills\voicebox\SKILL.md`.

| Voice Name | Type | Rating | Engine | Best Used For |
|---|---|---|---|---|
| **Jessica from Ihateediting** | Cloned (`54039424...`) | ⭐ Signature | `qwen` | **Channel Signature Narrator**. Cloned from Video 03 master audio. Default narrator for all documentaries. |
| **Emma (Storyteller)** | Cloned (`fd290dc6...`) | ★★★★★ | `qwen` | High pitched, articulate British voice. Suited for non-dramatic stories. |
| **Tom (Documentary)** | Cloned (`87fd7811...`) | ★★★★☆ | `qwen` | Energetic, American TV documentary style. |
| **Aiden (English)** | Preset (`29cb88dc...`) | ★★★☆☆ | `qwen_custom_voice` | Moderately good American male. Clean and articulate. |
| **Ryan (English)** | Preset (`4c8a347b...`) | ★★★☆☆ | `qwen_custom_voice` | Casual American male narration. |
| **Freeman (Baritone)** | Cloned (`692d3441...`) | ★★★☆☆ | `qwen` | Deep, slow. Good for vintage stories. |
| **Jessica Anne Bogart** | Cloned (`1600e180...`) | ★★★☆☆ | `qwen` | **AVOID**: Heavy, somber, overly dramatic tone. |
| **Jessica Anne Bogart (Friendly)**| Cloned (`a800aea1...`) | ★★★☆☆ | `qwen` | **AVOID**: Warmer interview tone, but unsuitable for show tone. |

---

## 3. Tool Gaps & Boundary Standards

| Proposed Capability | Declared Tool / Target | Real Status | Standard Operating Protocol |
|---|---|---|---|
| **Automated Clipping OCR** | `tesseract` / OCR CLI | `[TO BUILD]` | Direct manual text entry into `06_script_edit_plan/shot_plan.json` under `article.body` sourced from `QUOTE_PROOF.md`. |
| **Spatial Grain & Vignette in Resolve** | Resolve Color Nodes / OpenFX | `[DOCUMENTED-NOT-TESTED]` | The `.cube` LUT carries color only. Grain and vignette must be applied separately in Resolve Studio via dedicated node tree or looping 35mm grain overlay on V4. |
| **Hardware Photosensitivity Cert** | Harding FPA / BT.1702 | `[GUIDELINE SCREEN]` | `flash_scan.py` is a software screen modelled on WCAG 2.3.1; certified broadcast delivery requires post-export QC lab. |

---

## 4. Deterministic Commands & Verification Recipes
*(Working directory: `Videos-Scripts/<NN>_<Slug>/` or repository root for standalone edits)*

### AI Cut Engine & Waveform Snapping *(Revision 2026-11-01)*
```bash
# 1. Transcribe media with Groq Whisper API (cached if output exists)
python ../Video_Pipeline/tools/transcribe_groq.py \
  --input media.mp4 --out words.json --corrections transcript_corrections.json

# 2. Formulate cuts list with waveform audio energy snapping
python ../Video_Pipeline/tools/make_cuts.py \
  --words words.json --keep keep.json --out cuts.json --review cuts_review.md --source media.mp4

# 3. Map overlay anchors from source time to cut-timeline frame
python ../Video_Pipeline/tools/map_to_cut_time.py \
  --cuts cuts.json --words words.json --word-index 4

# 4. Build native FilmCraft timeline
python ../Video_Pipeline/tools/build_cut_filmcraft.py \
  --cuts cuts.json --out project.fcproj --captions --words words.json

# 5. Build DaVinci Resolve Studio timeline (Python 3.13)
python ../Video_Pipeline/tools/build_cut_resolve.py \
  --cuts cuts.json --project-name "Video_01_Cut"
```

### Forensic Code QA Suite *(Revision 2026-11-01)*
```bash
# 1. Auditory cut boundary inspection (exit 1 on FAIL, interior cuts only):
python ../Video_Pipeline/tools/cut_audit.py --media cut_render.mp4 --cuts cuts.json

# 2. Dead air scan (> 0.6s):
python ../Video_Pipeline/tools/dead_air_qa.py --media cut_render.mp4

# 3. Photosensitive flash scan (WCAG 2.3.1 screen):
python ../Video_Pipeline/tools/flash_scan.py --media cut_render.mp4

# 4. Graphic overlay placement and title-safe audit:
python ../Video_Pipeline/tools/graphics_qa.py --input "07_Video_Edit/graphics"
```

### Timing Estimation & Outline Ingestion *(Run 2026-11-01)*
```bash
python ../Video_Pipeline/tools/estimate_timing.py \
  --script 06_script_edit_plan/VoiceOver.md \
  --outline _pipeline/03_hook_outline.md \
  --out 06_script_edit_plan/timing.json \
  --wpm 158
```

### Voicebox Bypass Silent Placeholder Generation *(Run 2026-11-01)*
```bash
python ../Video_Pipeline/tools/make_placeholder_vo.py \
  --timing 06_script_edit_plan/timing.json \
  --out 06_script_edit_plan/take_01.wav
```

### Custom Character Callout Card Generation *(Run 2026-11-01)*
```bash
python ../Video_Pipeline/tools/render_callout.py \
  --name "Sir Patrick Stewart" \
  --role "Chancellor Emeritus | 2004–2015" \
  --subtitle "University of Huddersfield" \
  --position "bottom-left" \
  --illustrative \
  --out "07_Video_Edit/graphics/callout_sample.png"
```

### Custom Geographically Accurate Map Generation *(Run 2026-11-01)*
```bash
python ../Video_Pipeline/tools/render_map.py \
  --title "THE HUDDERSFIELD JOURNEY" \
  --subtitle "Geographic Scale & Early Theatrical Circuit" \
  --points "53.67,-1.69,Mirfield (Birthplace);53.64,-1.78,Huddersfield (University);51.50,-0.12,London (West End)" \
  --illustrative \
  --out "07_Video_Edit/graphics/map_sample.png"
```

### Custom Article Display & Precise Substring Highlight Generation *(Run 2026-11-01)*
```bash
python ../Video_Pipeline/tools/render_article.py \
  --headline "Sir Patrick Stewart Steps Down as Chancellor After 11 Years" \
  --outlet "The Guardian (Archive)" \
  --date "13 July 2015" \
  --body "Sir Patrick Stewart has announced he is standing down as chancellor of the University of Huddersfield after more than a decade in the role. During his tenure, he personally met thousands of graduating students and championed educational access across West Yorkshire." \
  --highlight "personally met thousands of graduating students" \
  --redact "West Yorkshire" \
  --style "marker" \
  --attribution "theguardian.com/stage/2015/jul/13/patrick-stewart-chancellor-huddersfield" \
  --illustrative \
  --out "07_Video_Edit/graphics/article_sample.png"
```

### Stem Loudness Analysis & Report Generation *(Run 2026-11-01)*
```bash
python ../Video_Pipeline/tools/stem_loudness.py \
  --input "07_Video_Edit/dialogue_norm.wav" "07_Video_Edit/ducked_bed.wav" "07_Video_Edit/mixed_audio.wav" \
  --out "07_Video_Edit/stem_loudness.txt"
```

### Graphics Manifest Generation *(Run 2026-11-01)*
```bash
python ../Video_Pipeline/tools/write_graphics_manifest.py \
  --dir "07_Video_Edit/graphics" \
  --out "07_Video_Edit/graphics/graphics_manifest.json"
```

<span style="color: purple;">[AI Agent]</span>
