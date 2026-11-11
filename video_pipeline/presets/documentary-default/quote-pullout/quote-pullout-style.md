# Quote Pullout - style guide (numbers from `../style.json`)

## 1. When
- Verbatim, primary-source-verified quotes only. The example file is a placeholder (`[PLACEHOLDER QUOTE]`); never ship it. Cap: 1 per 5 min, <= 4 per 20 min. Understated tone; no quotation-mark ornament (the floating glyph from earlier versions is deleted).

## 2. Timing
- In 17 frames, 50 px slide + fade, `easeOutCubic`. Hold 5.0 s (`layout.quote_pullout.hold_seconds`). Out 12 frames, `easeInCubic`. Total 149 frames (6.2 s).
- Measured y_min per in-frame: 413, 406, 399, 394, 389, 385, 382, 379, 377, 375, 374, 373, 372.

## 3. Layout (computed)
- Wrapping: greedy word wrap from glyph advances (Georgia-Italic 48 px) against `max_text_width` 1100 px, never wider than safe width - 2 x padding - slack (1600 - 144 - 4 = 1452). Aborts above `max_lines` 6 or if one word is wider than the measure.
- Leading 60 px; attribution (Georgia-Bold 45 px, gold) 40 px below the last line.
- Glass plate: charcoal at 82%, 2 px gold border at 70%, padding 72 px x / 48 px y, centred on (960, 540). Example (3 lines): plate x 388..1532, y 372..708 (1144 x 336).
- Measured at hold frame 74: text bbox [468, 420, 1452, 659]; padding left 80, top 48, right 80, bottom 49.

## 4. Pipeline
`render.ps1 [-Values my.json]` (keys `Quote`, `Attribution`; the builder wraps the text and emits `values.resolved.json` for the render) -> `renders\quote-pullout.mov` + `.png` (t = 2.0 s). Place on V3.
