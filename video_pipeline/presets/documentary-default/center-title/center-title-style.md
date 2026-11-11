# center-title

**What:** Mixkit "Center-aligned simple animated title" (mixkit.co free template 196) rebuilt as a house EffectCraft family: centered chapter/act title card featuring a wide-tracked kicker with an animated drawing underline, a bold centered title with soft settling overshoot, and an accented subtitle.

**Look:** Optically centered layout at `y=540` (screen center). Kicker in Montserrat-Bold (46 px ivory, tracked 260), animated 3 px white underline matching kicker ink width, Title in Montserrat-ExtraBold (112 px ivory), Subhead in Montserrat-Regular (48 px gold, tracked 80). Clean, text-on-footage presentation without a heavy scrim box.

**Animation (all `layout.center_title`):** Three-tiered cascade entry:
1. Kicker rises upward 20 px and fades in (14 frames).
2. The white underline draws horizontally left-to-right beneath the kicker (10 frames) once the kicker settles.
3. Main title rises with an overshoot settling curve (`type_pop`, 20 frames).
4. Subhead rises upward 22 px and fades in (14 frames).
After holding for the specified duration (default 3.0 s), the card exits in reverse sequence (subhead leaves first, followed by title, then kicker/underline, rising upward 18 px as they fade).

**When to use:** Major chapter introductions, act breaks, historical event cards, episodic title reveals, or archival scene transitions.

**Numbers:** Configured via `style.json` -> `layout.center_title`. Widths and center alignments are optically computed from actual glyph ink bounding boxes (`tw()`). Max title width is capped at 1300 px.

**Render command:**
```bash
python video_pipeline/presets/documentary-default/render_family.py --family center-title --values <dir>/values.json --out <dir>/graphics/<slot>_center_title.mov
```
Outputs ProRes 4444 RGBA `.mov`, transparent `.png` still, and editable `.ecproj` in `graphics/_ecproj/`.

**Values schema:**
- `Kicker` (string, required): Chapter or category prefix (e.g. "Chapter Two", uppercased automatically).
- `Title` (string, required): Primary episode or event title (e.g. "The City That Burned").
- `Sub` (string, required): Date, location, or secondary context (e.g. "October 8, 1871").
- `AccentColor` (string, optional): Color override for subtitle.
- `Hold` (number, optional): Custom hold duration in seconds.
