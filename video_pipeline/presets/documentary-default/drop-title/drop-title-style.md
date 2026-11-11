# drop-title

**What:** Mixkit "Drop Text Title" (mixkit.co free template 240) rebuilt as a house EffectCraft family: bold upper-third section/step title that drops down with overshoot, settling onto its line before an accent rule and optional tag pop in below.

**Look:** Upper-third positioning centered around `y=360`, left-aligned at safe margin (`x=160`). Heading in Montserrat-ExtraBold (108 px ivory, tracked 10). Accent rule (6 px thick) matching the heading's ink width minus a 140 px notch, popping in with a gold accent. Optional tag label below in Montserrat-Bold (46 px gold, tracked 80).

**Animation (all `layout.drop_title`):**
1. Heading drops 150 px from above, accelerates into an overshoot (28 px past resting baseline over 9 frames), squashes slightly (4% vertical compression), and springs back onto the resting baseline over 7 frames. Opacity fades in over 5 frames.
2. Once the heading settles, the accent rule scales out from its left anchor (`anchor_left=True`) with a back-eased pop over 10 frames.
3. If a tag is present, it rises 14 px into position alongside the rule.
4. After holding (default 3.0 s), the heading is plucked upward (26 px rise) as the entire card fades out cleanly over 12 frames.

**When to use:** Section breaks, step markers, numbered procedural points ("Step 3"), vlog chapter markers, or fast tutorial milestone cards.

**Numbers:** Configured via `style.json` -> `layout.drop_title`. Ink boundaries and rule length are dynamically calculated via `tw()`; max heading and tag widths are capped at 1300 px.

**Render command:**
```bash
python video_pipeline/presets/documentary-default/render_family.py --family drop-title --values <dir>/values.json --out <dir>/graphics/<slot>_drop_title.mov
```
Outputs ProRes 4444 RGBA `.mov`, transparent `.png` still, and editable `.ecproj` in `graphics/_ecproj/`.

**Values schema:**
- `Heading` (string, required): Step or section title (e.g. "Step 3", uppercased automatically).
- `Tag` (string, optional): Contextual description or subtitle (e.g. "Adjacency Pass").
- `AccentColor` (string, optional): Accent color override for rule and tag.
- `Hold` (number, optional): Custom hold duration in seconds.
