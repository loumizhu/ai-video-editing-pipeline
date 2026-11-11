---
name: bake-preset
description: After every edit session, turn the owner's corrections into approved changes to the house-style preset (presets/documentary-default, presets/shorts-vertical), regenerate grade/SFX artifacts, re-render the graphic families and verify them frame by frame. Use after a video edit, when the owner asks to change a font, timing, colour, grade or loudness value, or says "remember this for next time".
---

# Bake Preset

Root: `E:\((_atWork_))\Ytube_Channel\Videos-Scripts\Video_Pipeline` (below `$VP`). Preset: `$VP\presets\documentary-default` (`$D`), vertical: `$VP\presets\shorts-vertical` (`$V`).
Never touch the preset without owner approval (step 5). Notion is not used. Scratch goes in `temp_can_del_later\`.

## Step 1: list what the owner changed or asked for
One line per item, in the owner's words ("lower third stays 1 s longer", "grain too strong", "SFX too loud under VO").

## Step 2: map each item to a file and key
| Item | File / key |
|---|---|
| Colours, fonts, sizes | `$D\style.json` -> `typography.colors.*`, `typography.font_primary/secondary/numeric`, `typography.sizes.*` |
| Safe area | `canvas.safe_margin_x`, `safe_margin_top`, `safe_margin_bottom` (vertical: `$V\style.json`) |
| Position, padding, wrap width, hold time per family | `layout.lower_third.*`, `layout.chapter_card.*`, `layout.keyword_pop.*`, `layout.quote_pullout.*` (hold = `hold_seconds`), plate look `layout.glass.*` |
| In/out frames, slide distance, easing | `animation.in_frames`, `out_frames`, `slide_px`, `animation.easing.type_in/type_out/type_pop/overshoot_c1` (keyword-pop frames: `layout.keyword_pop.in_frames/out_frames`) |
| Grade, grain, vignette | `grade.lumetri.*`, `grade.noise.*`, `grade.vignette.*`, `grade.cube.size` |
| SFX / room tone level | `audio.sfx_peak_target_dbtp`, `sfx_peak_tolerance_db`, `room_tone_target_lufs`, `room_tone_tolerance_lu`, `fade_ms` |
| Transitions, density caps, frame counts | `$D\transitions.md` (single source for frame counts) |
| Ken Burns, glow, texture | `$D\animations.md`, `$D\creative-moves.md` |
| SFX files and licences | `$D\sfx.json`, `$D\sfx\LICENSES.md`, `$D\sfx.md` |
| Music ducking | `$D\music.md` (source `stages\08_assembly.md`) |
If an item has no home, say so and propose a new key plus the script that will read it. A key nothing reads is a bug (`check_style.py` fails).

## Step 3: show the owner the diff, change nothing yet
```
File: presets/documentary-default/style.json
Key:  layout.lower_third.hold_seconds
Before: 3.5 (84 frames @ 23.976)   After: 4.5 (108 frames)
Why:  owner said the role line is read too fast
Affects: lower-third renders; shorts-vertical unaffected
```

## Step 4: on explicit approval, apply and regenerate
1. Edit the key (JSON stays valid, one key per approved item).
2. `python $D\check_style.py` -> must print `unread: 0` for both files.
3. If `grade.*` changed: `python $D\grade\build_grade.py` (rewrites `house-style.fcpreset`, `house-look.cube`, `calibration_report.json`; needs FilmCraft; about 4 s). Check `calibration_report.json` held-out mean error < 1 level.
4. If `audio.*` changed: `python $D\sfx\sfx_tool.py build` then `python $D\sfx\sfx_tool.py verify` (must end `RESULT: PASS`). Update the numbers quoted in `sfx.md`.
5. Add a dated entry to `$D\CHANGELOG.md` using the template there: why, file, key, before -> after, renders updated, approved by.
6. Update any doc that repeats the value (README section 5, the family `-style.md`).

## Step 5: no silent edits
Every value change needs a shown diff, an owner "yes" and a CHANGELOG entry. Unapproved or one-off tweaks stay in the video's own folder.

## Step 6: re-render, verify with numbers, then look at the frames
For every affected family (all four if `animation.*`, `canvas.*`, `typography.*` or `layout.glass.*` changed), in a fresh shell:
```
powershell -NoProfile -File $D\<family>\render.ps1 -UpdateTemplate
python $D\verify_render.py --mov $D\<family>\renders\<family>.mov --plate --out-json <scratch>\v_<family>.json   # omit --plate for keyword-pop
python $VP\tools\graphics_qa.py --input $D\<family>\renders\<family>.mov --out-json <scratch>\qa.json --out-md <scratch>\qa.md
python $VP\tools\graphics_qa.py --input $D\<family>\renders\<family>.png
```
`<family>` = `lower-third`, `chapter-card`, `quote-pullout`, `keyword-pop`. Vertical:
```
powershell -NoProfile -File $V\render.ps1 -UpdateTemplate
python $D\verify_render.py --mov $V\renders\vertical_keyword_pop.mov --style $V\style.json
python $VP\tools\graphics_qa.py --input $V\renders\vertical_keyword_pop.mov --width 1080 --height 1920
```
Pass means: `verify_render.py` verdict PASS (alpha pix_fmt, 0 safe-rect violations, 0 edge touches, text padding >= 24 px, in-animation steps shrinking) and `graphics_qa.py` PASS. Note: for plate families `graphics_qa.py` measures the plate, not the glyphs; the glyph rule is the 45 px font-size floor enforced at build time.
Grade changes: `python $D\grade\measure_grade.py --frames <bridge.png> <bright.png> <dark.png> --out-dir <scratch>` -> p5 shift within +/-3 levels, LUT vs lumetri mean diff < 2.

**View the frames.** Composite each new hold frame (take it from the frame folder with `verify_render.py --keep-frames <dir>`, or the `.png`) over one bright and one dark real frame and open the images. Check: text inside the plate, nothing clipped, contrast readable on the bright frame, the in-animation frames (1, 4, 8, 12, 17) move and fade. For grade changes open a before / preset / cube strip. Report what you saw per image. Replace `renders\composite_reference.png` only after the owner approves what you saw.

Finish by deleting `__pycache__` and scratch folders you created, then report: diff applied, commands run, numbers, image paths.
