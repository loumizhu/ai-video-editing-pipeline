# Stage 08: Timeline Assembly, Native Scripting & Multitrack Mix

## Purpose
Assemble the complete native documentary timeline exclusively in **FilmCraft** via headless CLI automation (`filmcraft-cli`) or the FilmCraft desktop application. Traditional third-party NLEs (Adobe Premiere Pro, DaVinci Resolve Studio) are **not** used. Adhere to canonical Vcut §3.5 4-Video / 5-Audio track layout at CFR. Execute frame-exact verification against the cut plan (mandatory: zero frame drift). Execute dynamic sidechain ducking, measure master and stem loudness, and output locked preview media. If headless automation fails, execute the technical bypass (interchange package + FFmpeg preview) so production advances to Packaging.
Reference: [Editing Toolkit](../EDITING_TOOLKIT.md), [STANDARD_FOLDER_STRUCTURE.md](../templates/STANDARD_FOLDER_STRUCTURE.md), [Vcut Step 05: Timeline Manifest and QA](../../../../Vcut/05_Timeline_Manifest_and_QA.md), and [Vcut Data Contracts §3.5](../../../../Vcut/Vcut_Data_Contracts.md#35-vcut_timelinejson--canonical).

> *Note: Plain-text project paths (e.g. `07_Video_Edit/Source/`, `07_Video_Edit/Export/`, `03_media/`) are relative to working directory `Videos-Scripts/<NN>_<Slug>/`. Markdown links are relative to this stage file.*
> *Owner Mandate: No third-party NLE. Do not use built-in NLE title/text presets anywhere. All graphics are custom overlay assets on V3/V4.*

## Inputs
- `03_media/_cuts/*.mp4` (CFR conformed visual footage).
- `03_media/conformed/*.png` (stage 07 conformed visual stills, 25–35% of runtime).
- `07_Video_Edit/Source/graphics/*` (custom rendered overlay PNGs and alpha video clips).
- `06_script_edit_plan/take_01.wav` (master normalized voiceover or calibrated placeholder).
- `03_media/scored_clips.wav` (archival speech sync soundbites).
- `05_music/primary_bed.wav` (selected un-ducked music bed).
- `06_script_edit_plan/shot_plan.json` & `timing.json` (visual-audio alignment schedule).
- `06_script_edit_plan/cuts.json` (frame-accurate cut list if cut engine was invoked).

## Outputs
- `07_Video_Edit/Source/<slug>.fcproj` (native FilmCraft project file).
- `07_Video_Edit/Source/<stem>_build_report.json` (frame-for-frame verification report: clip count, durations, zero drift; Revision 2026-11-01).
- `07_Video_Edit/Source/stems/dialogue_norm.wav` (dialogue stem normalized to -16 LUFS, TP -1.8 dBTP).
- `07_Video_Edit/Source/stems/ducked_bed.wav` (ducked music bed: -24 dB relative to speech / -28 dB relative to scored clips).
- `07_Video_Edit/Source/stems/mixed_audio.wav` (master stereo mix: dialogue + sync + ducked music).
- `07_Video_Edit/Source/stems/stem_loudness.txt` (forensic stem loudness verification report).
- `07_Video_Edit/Source/vcut_timeline.json` (canonical multitrack timeline conforming to Vcut §3.5).
- `07_Video_Edit/Export/preview_rough_cut.mp4` (H.264 preview render with full 3-layer audio mix).
- `07_Video_Edit/Export/loudness_readout.txt` (integrated loudness, LRA, and true peak readout).
- `_pipeline/BYPASS_LOG.md` (updated if scripting fallback triggered).

## Executor
- **Worker / Tool:** Tool (`ffmpeg` + `filmcraft-cli` + `build_cut_filmcraft.py` + `stem_loudness.py`) + Antigravity (timeline builder).

## Tools
- `ffmpeg` (two-level dynamic sidechain ducking, loudnorm, ebur128 with peak=true, multitrack rendering).
- `python ../Video_Pipeline/tools/stem_loudness.py` (stem loudness analysis and pass/review reporting).
- `filmcraft-cli` (`0.15.0`; verified commands: `file.newProject`, `file.newSequence`, `import`, `exec timeline.place`, `sequence.applyVideoTransition`, `inspect sequence`).
- `python ../Video_Pipeline/tools/build_cut_filmcraft.py` (**VERIFIED; Revision 2026-11-01**; builds native `.fcproj` with captions from transcript and verifies 0 frame drift).
- `python ../Video_Pipeline/tools/render_cut_ffmpeg.py` (**VERIFIED; Revision 2026-11-01**; single-filtergraph preview render verifying frame counts and A/V sync within 1.5 frames).

## Audio Mix & Two-Level Sidechain Ducking Recipe *(Working directory: Videos-Scripts/<NN>_<Slug>/)*
The FFmpeg two-level sidechain recipe below serves as the reference standard and default for documentary voiceover. *(Note on FilmCraft native ducking: `essentialSound.generateDucking` applies a fixed -15 dB attenuation under speech with 0.8s release, but applies **no attack ramp**, causing an abrupt drop at speech onset. The FFmpeg recipe below provides professional documentary mastering with 100ms attack, 600ms release, -24 dB dialogue bed, and -28 dB under scored soundbites).*
```bash
# Ensure destination folders exist
mkdir -p "07_Video_Edit/Source/stems" "07_Video_Edit/Export"

# 1. Normalize dialogue stem to -16 LUFS (capped at TP -1.8 dBTP to guarantee mix ceiling < -1.5 dBTP)
ffmpeg -y -i "06_script_edit_plan/take_01.wav" -af "loudnorm=I=-16:TP=-1.8:LRA=11:print_format=summary" -ar 48000 "07_Video_Edit/Source/stems/dialogue_norm.wav"

# 2. Two-level sidechain ducking; dialogue is mono, duplicated to stereo. amix normalize=0 avoids level halving.
ffmpeg -y -i "07_Video_Edit/Source/stems/dialogue_norm.wav" -i "03_media/scored_clips.wav" -i "05_music/primary_bed.wav" \
  -filter_complex "[0:a]asplit=2[key][d0]; [d0]pan=stereo|c0=c0|c1=c0[dlg]; \
    [2:a][key]sidechaincompress=threshold=0.0265:ratio=20:attack=100:release=600:makeup=1[bd1]; \
    [bd1][1:a]sidechaincompress=threshold=0.010:ratio=20:attack=100:release=600:makeup=1[md]; \
    [md]asplit=2[m_stem][m_mix]; \
    [dlg][1:a][m_mix]amix=inputs=3:duration=first:dropout_transition=0:normalize=0[mix_raw]" \
  -map "[m_stem]" "07_Video_Edit/Source/stems/ducked_bed.wav" -map "[mix_raw]" "07_Video_Edit/Source/stems/mixed_audio.wav"

# 3. Stem loudness and mix readout with true peak
python ../Video_Pipeline/tools/stem_loudness.py --input "07_Video_Edit/Source/stems/dialogue_norm.wav" "07_Video_Edit/Source/stems/ducked_bed.wav" "07_Video_Edit/Source/stems/mixed_audio.wav" --out "07_Video_Edit/Source/stems/stem_loudness.txt"
ffmpeg -y -i "07_Video_Edit/Source/stems/mixed_audio.wav" -af "ebur128=framelog=verbose:peak=true" -f null - 2> "07_Video_Edit/Export/loudness_readout.txt"
```

## FilmCraft Timeline Build Protocol
Build fresh native timeline inside FilmCraft via deterministic CLI adapter:
```powershell
# Automated builder (generates project, places V1/A1, verifies frame-exact match):
python ../Video_Pipeline/tools/build_cut_filmcraft.py --cuts "06_script_edit_plan/cuts.json" --out "07_Video_Edit/Source/<slug>.fcproj" --captions --words "06_script_edit_plan/words.json"

# Direct CLI syntax reference (ticks = seconds * 254016000000; Revision 2026-11-01):
# 1. Create fresh FilmCraft project file in Source/
& "C:\Program Files\FilmCraft\filmcraft-cli.exe" --save-as "07_Video_Edit/Source/<slug>.fcproj" exec file.newProject '{"name": "<slug>"}'

# 2. Create canonical sequence with 4 video tracks and 5 audio tracks (Vcut §3.5)
& "C:\Program Files\FilmCraft\filmcraft-cli.exe" --project "07_Video_Edit/Source/<slug>.fcproj" --save exec file.newSequence `
  '{"name": "Main_Sequence", "width": 1920, "height": 1080, "fps": 23.976, "video": 4, "audio": 5}'

# 3. Import media via expanded file paths
& "C:\Program Files\FilmCraft\filmcraft-cli.exe" --project "07_Video_Edit/Source/<slug>.fcproj" --save import $import_files

# 4. Place clips natively across V1..V4 and A1..A5 using ticks
& "C:\Program Files\FilmCraft\filmcraft-cli.exe" --project "07_Video_Edit/Source/<slug>.fcproj" --save exec timeline.place `
  '{"item": <item_id>, "track": "V3", "time": <start_ticks>, "duration": <dur_ticks>, "insert": false}'
```

*Fallback Chain (Bypass):* If FilmCraft CLI automation fails, generate FCPXML/OTIO interchange package into `07_Video_Edit/Source/` + FFmpeg rough cut preview into `07_Video_Edit/Export/preview_rough_cut.mp4`, log to `_pipeline/BYPASS_LOG.md`, and advance to Stage 09.

## Colour Script: per-shot looks (Revision 2026-11-09)
Before the timeline build, with the conformed pictures in place ([COLOR_SCRIPT.md](../COLOR_SCRIPT.md)):
```bash
# Per-shot looks (phase + blend + protection + cast correction), one FilmCraft preset per look, measured .cube per look:
python ../Video_Pipeline/tools/color_script.py plan --script "06_script_edit_plan/color_script.json" --shot-plan "06_script_edit_plan/shot_plan.json" --beat-map "06_script_edit_plan/beat_map.json" --assets-root "03_media" --out-dir "06_script_edit_plan/color" --measure
# Strip, phase sheet, 70 % over-grade strip, text / skin / clipping checks:
python ../Video_Pipeline/tools/color_script.py qa --assign-file "06_script_edit_plan/color/color_assign.json" --out-dir "06_script_edit_plan/color"
# After the preview render: the rendered strip row + RENDER_DRIFT
python ../Video_Pipeline/tools/color_script.py qa --assign-file "06_script_edit_plan/color/color_assign.json" --video "07_Video_Edit/Export/preview_rough_cut.mp4" --out-dir "07_Video_Edit/Export/color_qa"
```
Narrated beat builds: `--beats beats.json --assign assignments.json` instead of `--shot-plan`, and copy `color/` into `Source/` so `build_full_edit.py` finds `Source/color/color_assign.json` (it applies the looks only when the plan verdict is PASS; unmatched clips get the house look, generated plates get no grade). Resolve: `item.SetLUT(1, <look>.cube)` per clip, grain and vignette added separately.

## Organic Film Grain Synthesis & Texture Bed (Revision 2026-11-09)
Apply organic celluloid grain per narrative profile ([EDITING_TOOLKIT.md \S2.6](../EDITING_TOOLKIT.md#26-organic-celluloid-film-grain-synthesis-moving-beyond-screen-overlays) & [`film_grain_profiles.json`](../presets/color/film_grain_profiles.json)).
**Golden Rule:** Suppress grain in deep shadows (<15%) and bright whites (>85%); 0% chroma noise; strict pipeline order `[Grade] -> [Grain] -> [Master Sharpening]`.
- **FilmCraft CLI / Project:**
  - *Option 1 (Clip / Master Effect Stack):* Apply native `noise` effect (`monochrome: true`, amount 1.5–5.0 depending on Profile A–D).
  - *Option 2 (Track V4 Texture Bed):* Continuous celluloid loop placed on V4 with `Opacity.blend: "Overlay"` (never `Screen`), opacity 15–35%.
- **FFmpeg Procedural Filter (Preview / Export):**
  ```bash
  python ../Video_Pipeline/tools/film_grain.py apply --input "07_Video_Edit/Export/preview_rough_cut.mp4" --output "07_Video_Edit/Export/preview_rough_cut_grained.mp4" --profile classic_35mm --youtube
  ```
- **DaVinci Resolve Studio:** Color Page terminal serial node with OpenFX *Film Grain* (35mm 50D/400T/16mm, Saturation 0.0, Tone Response Midtones 1.0).

## Pacing Verification (Revision 2026-11-09)
```bash
# Still-hold budget on the plan that was built, plus a heuristic scene-change scan of the rendered preview:
python ../Video_Pipeline/tools/still_hold_qa.py --shot-plan "06_script_edit_plan/shot_plan.json" --assets-report "03_media/asset_audit.json" --media "07_Video_Edit/Export/preview_rough_cut.mp4" --out-json "07_Video_Edit/Export/qa_still_hold.json" --out-md "07_Video_Edit/Export/qa_still_hold.md"
# Variation log and the edit report with rationale (owner reads section 5, fills section 6):
python ../Video_Pipeline/tools/variation_report.py --shot-plan "06_script_edit_plan/shot_plan.json" --out-json "07_Video_Edit/Export/variation_log.json" --out-md "07_Video_Edit/Export/edit_report.md"
```
Narrated beat builds use `--beats beats.json --assign assignments.json [--beat-map beat_map.json]` instead of `--shot-plan`. Builders pick Ken Burns moves from the motion library and write `motion_log.json`; `build_full_edit.py` refuses a same-idea merge that would exceed the hard cap and writes `still_hold_warnings.json`. Builders never stop (bypass policy); the QA exit code decides. Optional alternate cuts: [DERIVATIVES.md](../DERIVATIVES.md).

## Acceptance Checklist
- [ ] `color_script.py plan` and `qa` PASS on the conformed pictures; `strip.png`, `phase_sheet.png` and `strip_overgrade.png` looked at; every `NEIGHBOR_JUMP` answered (story reason or `grade_adjust`) (Revision 2026-11-09).
- [ ] Organic celluloid film grain applied per narrative profile (`grain.clean_35mm`, `grain.classic_35mm`, `grain.gritty_16mm`, or `grain.vintage_8mm`) with midtone luma masking, 0% chroma noise, and post-grade/pre-sharpening order; Screen blend mode banned for grain.
- [ ] `still_hold_qa.py` PASS (or each long hold carries an owner waiver) and `variation_report.py` PASS; `edit_report.md` written.
- [ ] Timeline conforms to canonical Vcut §3.5 schema (`vcut_timeline.json`).
- [ ] Dialogue normalized to -16 LUFS; music ducked to -24 dB (speech) and -28 dB (scored clips). *(Exemption: If `voice_status: pending_owner_recording`, dialogue loudness and ducking items are marked DEFERRED to re-time; preview only; open bed level check only -24 to -28 LUFS).*
- [ ] Native FilmCraft timeline generated (`07_Video_Edit/Source/<slug>.fcproj`) with tracks V1–V4 and A1–A5.
- [ ] Zero third-party NLE dependency; pure FilmCraft + deterministic CLI tooling.
- [ ] Frame-exact verification passed with zero drift documented in build report (Revision 2026-11-01).
- [ ] Zero built-in NLE default title/lower-third presets; all graphics placed as custom overlay assets on V3/V4.
- [ ] Proofs `stem_loudness.txt` and `loudness_readout.txt` (with `peak=true`) generated and verified.
- [ ] `07_Video_Edit/Export/preview_rough_cut.mp4` rendered with audio and visual tracks locked.

## Reviewer
- Claude Sonnet via [code.md](../../../.agents/skills/orchestrate/reviewers/code.md).

## Human Gate
- **No:** Direct precursor to Packaging (Stage 09) and Final QA (Stage 10).

## Failure & Retry
- If FilmCraft automation fails, apply interchange package fallback, log to `BYPASS_LOG.md`, and re-render preview. Max 3 passes.

<span style="color: purple;">[AI Agent]</span>
