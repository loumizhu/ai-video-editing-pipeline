# line-third

**What:** Mixkit "Simple bottom third" (mixkit.co free template 311) rebuilt as a house EffectCraft family: bold tracked uppercase heading, solid rule under it, wide-tracked light uppercase subheading below. Rendering the example values (`Gemma Lauren / Compositing Supervisor`) gives a 1:1 recreation to compare against the source video.

**Look:** No plate, no glass — text sits directly on footage. Heading Montserrat-ExtraBold (blue `#4993EA`), rule white 8 px, sub Montserrat-Regular (`#F5F7F8`). Bottom-anchored at the safe edge, left at safe margin.

**Animation (all `layout.line_third`):** At `lead_in` the rule snaps in right→left (10 f ease-out). Then the heading reveals in a per-glyph cascade left→right and the subhead right→left simultaneously (30/34 f ease-out along one decelerating front), each with a white caret block riding the reveal front — caret height is derived from the line's real ink height (heading 96 px Montserrat ≈ 67 px tall, sub ≈ 33 px), so the block always matches its text. Hold, then the exit mirrors the entry: heading erased right→left, subhead left→right (30 f ease-in), then the rule retracts (12 f). Typical total ≈ 5.7 s at house 2.5 s hold. (EffectCraft's `Linear Wipe` was probed and is unusable — font/placement-dependent boundary — hence the per-glyph cascade, which reads nearly identically at 23.976 fps.)

**When to use:** Person introductions and "this part of the story" title cards where the glass lower-third looks too heavy — e.g. chapter openers, quick expert cameos.

**Numbers:** `style.json` -> `layout.line_third`. Colors are per-family (`heading_color`, `rule_color`, `sub_color`, `caret_color`) so a shorts variant can swap blue→gold without touching the builder.

**Render (never touches committed presets):**
```bash
python video_pipeline/presets/documentary-default/render_family.py --family line-third --values <dir>/values.json --out <dir>/graphics/<slot>_line_third.mov
```
Outputs ProRes 4444 RGBA `.mov` (FilmCraft V3), a transparent `.png` still, and the editable `.ecproj` in `graphics/_ecproj/`.

**Values schema:** `Heading`, `Sub` (both uppercased by the builder), optional `Hold`. Builder: `_families_v2.py::build_line_third`. Measured from the mixkit 311 preview (24 fps frame-scan): heading cap 68 px @ x 302-971, rule y 830-846 @ x 283-965, sub cap 28 px, reveal ~1.25 s easing out, hold ~1.7 s, exit ~1.3 s; ours upsizes to the 45 px floor.
