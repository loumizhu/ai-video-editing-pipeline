# Lower Third - style guide (all numbers from `../style.json`, measured on `renders/`)

## 1. When
- Introduce a speaker or subject at first meaningful appearance, or on re-introduction after >= 10 min.
- Never on crowds or generic B-roll. Formal name ("Sir Patrick Stewart, OBE").
- Cap: 1 per named subject + at most 1 return; <= 4 per 10 min.

## 2. Timing (`animation.*`, `layout.lower_third.hold_seconds`)
- In: 17 frames (0.709 s @ 23.976) slide up 50 px (`animation.slide_px`) + fade, `easeOutCubic` baked 1 key/frame.
- Hold: 3.5 s. Out: 12 frames (0.500 s), `easeInCubic`. Total 4.71 s = 113 frames.
- Measured in-animation y_min per frame (px): 852, 845, 838, 833, 828, 824, 821, 818, 816, 814, 813, 812, 811, then flat. Steps 7, 7, 5, 5, 4, 3, 3, 2, 2, 1, 1, 1, 0 (shrinking = ease-out).

## 3. Plate (sized from the text, never fixed)
`build.py` measures both lines with the real font (`typography.measure_files`, ink box) and builds:
- width = `text_offset_x` 43 + widest ink line + `measure_slack_px` 4 + `pad_right` 44
- height = `pad_y` 28 + name ink + `line_gap` 14 + role ink + `pad_y` 28
- left edge = `canvas.safe_margin_x` 160, bottom edge = 1080 - `canvas.safe_margin_bottom` 100 = 980. The build aborts if the plate leaves the safe rect (x 160..1760, y 100..980).
- Example ("Sir Patrick Stewart, OBE" / "Chancellor Emeritus | University of Huddersfield"): plate x 160..1315, y 811..980 (1155 x 169). Measured padding text-to-plate: left 44, top 28, right 55, bottom 28 px (`verify_render.py`, hold frame 60).
- Plate: charcoal `#0F1218` at 82% (`layout.glass.plate_alpha`), gold `#D4AF37` 2 px border at 70% (`layout.lower_third.border_px`, `layout.glass.border_alpha`), 5 px gold accent bar inset 10 px / 14 px.
- Text comes from a values JSON; `render.ps1` rebuilds the template from that JSON on every run, so the plate always fits the text.

## 4. Typography and deviations from `tools\render_callout.py` / LESSONS
| Item | render_callout.py | This preset | Reason |
|---|---|---|---|
| Face | Georgia Bold / Georgia Italic (first in its stack) | Georgia-Bold / Georgia-Italic | same |
| Name / role size | 52 / 32 px | 56 / 48 px | LESSONS "no text < 45 px" (the 32 px role breaks it). These are font sizes; cap heights are 39 px and 33 px. |
| Colours | Ivory #F3EBDD, Gold #FFE8B8, plate (15,18,24) at 210/255 = 82% | same | same |
| Border / bar | 2 px gold at 180/255 = 71% / 5 px bar | 2 px at 70% / 5 px bar | same |
| Corner radius | 12 px | 0 px | EffectCraft solids are rectangles. A shape-layer route was not tried. |
| Position | margin 100 px | x 160 (`safe_margin_x`), bottom 100 | one safe-area definition for the whole preset |
| LESSONS feathered wipe (`linear_wipe_legacy`, 270 deg, feather 30) | n/a | not baked | It is a FilmCraft clip effect, not an EffectCraft property. The preset uses slide 50 px + fade instead. Add the wipe on the V3 clip in FilmCraft if wanted. |
| LESSONS 72 px / 56 px sizes (Video 010 overlay) | n/a | 56 / 48 px | Plate height for the example is 169 px (15.6% of frame height) at 56/48 and 193 px (17.9%) at 72/56, width 1155 vs 1323 px. 56/48 keeps the plate smaller while passing the 45 px floor. This is a taste call, not a technical limit: 72/56 also fits the safe rect. Change `typography.sizes.name_primary` / `role_secondary` to restore it. |

## 5. Pipeline
- Build + render: `powershell -NoProfile -File render.ps1 [-Values my.json]` (keys `Name`, `Role`). Output `renders\lower-third.mov` (ProRes 4444, `yuva444p12le`) and `.png` (t = 2.0 s). Place on V3.
- Check: `python ..\verify_render.py --mov renders\lower-third.mov --plate` and `python ..\..\..\tools\graphics_qa.py --input renders\lower-third.mov`.
