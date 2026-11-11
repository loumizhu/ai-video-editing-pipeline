# banner-third

**What:** Mixkit "Accented Banner Lower-third" (mixkit.co free template 305) rebuilt as a house EffectCraft family: dark bordered banner plate with an animated accent border frame, holding a high-authority headline and wide-tracked subheading.

**Look:** Dark charcoal solid plate (`#0F1218` at 92% alpha, overridable via `PlateColor`), accented by a gold border (`#D4AF37`, 5 px width, overridable via `AccentColor`). Heading in Montserrat-ExtraBold (92 px ivory), Subhead in Montserrat-Regular (46 px gold_accent, tracked 140). Left-aligned at safe margin (`x=160`), bottom-anchored at safe margin (`y=980`). Plate dimensions derive strictly from text ink measurements with dynamic padding (`pad_x=52`, `pad_y=44`).

**Animation (all `layout.banner_third`):** The entire banner block slides smoothly from off-screen left and decelerates into resting position. Once stopped, the gold accent border lines draw on sequentially (top and bottom bars grow horizontally over 16 frames; left and right edges grow vertically with a 4-frame delay). After holding for the specified duration (default 3.2 s), the full banner slides off to the right (560 px displacement) as it fades out over 12 frames.

**When to use:** Heavyweight investigative or documentary interview contexts, formal subject introductions, institutional affiliations, or multi-part authority stamps.

**Numbers:** Configured in `style.json` -> `layout.banner_third`. Geometry is measured dynamically via `tw()`; max heading and sub widths are capped at 1480 px.

**Render command:**
```bash
python video_pipeline/presets/documentary-default/render_family.py --family banner-third --values <dir>/values.json --out <dir>/graphics/<slot>_banner_third.mov
```
Outputs ProRes 4444 RGBA `.mov`, transparent `.png` still, and editable `.ecproj` in `graphics/_ecproj/`.

**Values schema:**
- `Heading` (string, required): Primary title or name (uppercased automatically).
- `Sub` (string, required): Subheading or role/affiliation (uppercased automatically).
- `AccentColor` (string, optional): Border and subhead color override.
- `PlateColor` (string, optional): Plate solid color override.
- `Hold` (number, optional): Custom hold duration in seconds.
