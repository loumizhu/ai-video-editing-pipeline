# timeline-strip

**What:** Bottom band: gold line draws across 2-5 events; diamond dots pop in sequence, year above (Montserrat), balanced 2-line italic label below. Active event in gold.

**When to use:** Recaps of a life arc or a multi-decade jump. Labels <= 5 words. Use '|' in a label for a manual break.

**Numbers:** `style.json` -> `layout.timeline_strip` (+ `typography.sizes`, `typography.colors`). Never hard-code values in values JSON except `Hold`.

**Render (never touches committed presets):**
```bash
python Videos-Scripts/Video_Pipeline/presets/documentary-default/render_family.py --family timeline-strip --values <dir>/values_timeline_strip.json --out <dir>/graphics/<slot>_timeline_strip.mov
```
Outputs ProRes 4444 RGBA `.mov` (FilmCraft V3), a transparent `.png` still, and the editable `.ecproj` in `graphics/_ecproj/`.

**Values schema:** see `timeline-strip.json.example`. Builder: `_families_v2.py::build_timeline_strip`. Tested 2026-11-07 on video 19 (Child Stars Who Quit Hollywood) in FilmCraft.
