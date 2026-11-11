# Keyword Pop - style guide (numbers from `../style.json`)

## 1. When
- One verified number, date or name spoken in the VO. Never adjectives. Cap: 1 per 60 s, <= 6 per 10 min.

## 2. Timing (`layout.keyword_pop.*`)
- In 12 frames: scale 30% -> overshoot -> 100%, `easeOutBack` (`animation.easing.overshoot_c1` 1.70158) baked 1 key/frame, opacity `easeOutCubic`. Hold 2.5 s. Out 10 frames: scale 100% -> 85% (`out_scale_pct`) + fade, `easeInCubic`. Total 82 frames.
- Measured ink width per in-frame (px): 0, 162, 219, 260, 288, 307, 316, 319 (peak, frame 8), 317, 312, 306, 300, 298 (rest). Overshoot +7.0% over rest, then settles. Vertical variant: 210, 284, 334, 364, 379, 382 (peak, frame 7), 377, 369, 361, 358 (rest), +6.7%.
- Scale pivots on the ink centre (anchor point set from font metrics), so the word grows around `center_x` / `center_y`, not from its baseline.

## 3. Layout and type
- Centre (960, 500) at 100% scale. Peak scale 1.07 is checked against the safe rect at build time (abort if outside x 160..1760, y 100..980). Measured union bbox over all 82 frames: [801, 452, 1120, 548].
- Arial-BoldMT 100 px, gold #FFE8B8. Arial because Georgia figures are old-style. Cap height 72 px.
- No plate. Gold on pale footage loses contrast (see `renders\composite_reference.png`). Use over mid or dark footage, or add a darkening layer in the NLE.

## 4. Pipeline
`render.ps1 [-Values my.json]` (key `Keyword`) -> `renders\keyword-pop.mov` + `.png` (t = 1.0 s). Place on V3.
