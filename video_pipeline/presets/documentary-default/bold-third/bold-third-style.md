# bold-third

**What:** Mixkit "Bold Lower-third" (mixkit.co free template 312) rebuilt as a house EffectCraft family: high-impact bold uppercase heading with a slam landing and an animated clearance line sweeping underneath, followed by a snappy exit.

**Look:** No plate, no background box — text sits directly over footage. Heading in Montserrat-ExtraBold (104 px, tracked 10), clearance rule in white (6 px thick) extending 20 px past the last glyph. Default accent color is `gold_accent` (`#D4AF37`), overridable via `values.AccentColor`. Bottom-anchored at safe area bottom (`y=980`), left-aligned at safe margin (`x=160`).

**Animation (all `layout.bold_third`):** At `lead_in` (0.25 s), the heading slams in (scale 128% -> 100% with `type_pop` easeOutBack, drop 18 px) while opacity fades in rapidly over 5 frames. Simultaneously, the clearance line sweeps out from left to right under the heading (11 frames). Once settled, it holds for the specified duration (default 3.4 s). On exit, the heading shrinks (100% -> 96%) and fades out quickly over 6 frames, while the clearance line retracts smoothly over 10 frames.

**When to use:** Fast expert cameos, punchy subject identifications, talking-head name tags, or video passages where a glass lower-third or boxed plate is too heavy or formal.

**Numbers:** Configured via `style.json` -> `layout.bold_third`. Geometry is measured dynamically from font ink via `tw()`; max heading width is capped at 1400 px.

**Render command:**
```bash
python video_pipeline/presets/documentary-default/render_family.py --family bold-third --values <dir>/values.json --out <dir>/graphics/<slot>_bold_third.mov
```
Outputs ProRes 4444 RGBA `.mov` for FilmCraft V3, a transparent `.png` still, and an editable `.ecproj` in `graphics/_ecproj/`.

**Values schema:**
- `Heading` (string, required): Person name or label (uppercased automatically).
- `AccentColor` (string, optional): Hex color (`#RRGGBB`) or palette key.
- `Hold` (number, optional): Custom hold duration in seconds.
