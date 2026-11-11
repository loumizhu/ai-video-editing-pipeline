# kinetic-quote

**What:** Word-by-word quote reveal over a 68% scrim: gold hanging quote mark, Georgia Bold 88 px (<= 12 words) or 72 px, balanced line breaks (prefers sentence breaks, no orphans), Emphasis phrase in gold accent, tracked attribution last. Timing: Word_Times (seconds, from words.json) or WPM.

**When to use:** Short, spoken, verified quotes (<= 25 words) when the narrator reads them. For longer quotes use quote-pullout. Feed Word_Times from transcribe_groq words.json for frame-exact sync.

**Numbers:** `style.json` -> `layout.kinetic_quote` (+ `typography.sizes`, `typography.colors`). Never hard-code values in values JSON except `Hold`.

**Render (never touches committed presets):**
```bash
python Videos-Scripts/Video_Pipeline/presets/documentary-default/render_family.py --family kinetic-quote --values <dir>/values_kinetic_quote.json --out <dir>/graphics/<slot>_kinetic_quote.mov
```
Outputs ProRes 4444 RGBA `.mov` (FilmCraft V3), a transparent `.png` still, and the editable `.ecproj` in `graphics/_ecproj/`.

**Values schema:** see `kinetic-quote.json.example`. Builder: `_families_v2.py::build_kinetic_quote`. Tested 2026-11-07 on video 19 (Child Stars Who Quit Hollywood) in FilmCraft.
