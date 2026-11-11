# Chapter Card - style guide (numbers from `../style.json`)

## 1. When
- Major act or chapter change only. Cap: 1 per chapter, <= 4 per 20 min.

## 2. Timing
- In 17 frames (0.709 s): 50 px slide up + fade, `easeOutCubic`. Hold 4.0 s (`layout.chapter_card.hold_seconds`). Out 12 frames, `easeInCubic`. Total 125 frames (5.21 s).
- Measured y_min per in-frame: 454, 446, 440, 434, 429, 425, 422, 419, 417, 415, 414, 413, 412 (steps 8, 6, 6, 5, 4, 3, 3, 2, 2, 1, 1, 1).

## 3. Layout (computed, centred on `layout.chapter_card.center_y` 540)
- Stack: chapter label (Arial-BoldMT 48 px, gold #FFE8B8, tracking 20) / 24 px / hairline 160 x 3 px gold #D4AF37 at 90% / 32 px / title (Georgia-Bold 68 px, ivory #F3EBDD, wrapped to <= 3 lines at the safe width minus padding, leading 80 px).
- Scrim plate behind everything: charcoal at 72% (`plate_alpha`), padding 96 px x / 56 px y, no border. Example: plate x 316..1604, y 412..668.
- The build aborts if the plate leaves the safe rect (x 160..1760, y 100..980). Title wrapping comes from glyph advances (`_common.wrap`), not a character count.
- The label uses Arial because Georgia figures are old-style (the "01" renders at x-height); lining figures are needed for chapter numbers and stats.

## 4. Measured (hold frame 62)
- Plate bbox [316, 412, 1604, 668]; text bbox [415, 469, 1505, 612]; padding left 99, top 57, right 99, bottom 56 px. All frames inside the safe rect, no edge contact (`verify_render.py` PASS).
- Cap heights (H): label 35 px, title 47 px. Font sizes 48 / 68 >= 45 px floor.

## 5. Pipeline
`render.ps1 [-Values my.json]` (keys `Chapter`, `Title`) -> `renders\chapter-card.mov` + `.png` (t = 2.0 s). Place on V3.
