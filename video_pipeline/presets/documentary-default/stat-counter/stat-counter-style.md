# stat-counter

**What:** Big Montserrat ExtraBold number that counts up (easeOutCubic, 1.6 s) over a 55% scrim, gold hairline, tracked label, optional italic context line. Format comma|plain (years), Prefix/Suffix, Decimals.

**When to use:** When a number IS the beat (5,000 boys, $4M box office, 1985 -> 2023 year jump). Max 1 per 2 minutes. Keep 'about/roughly' honesty in Context.

**Numbers:** `style.json` -> `layout.stat_counter` (+ `typography.sizes`, `typography.colors`). Never hard-code values in values JSON except `Hold`.

**Render (never touches committed presets):**
```bash
python Videos-Scripts/Video_Pipeline/presets/documentary-default/render_family.py --family stat-counter --values <dir>/values_stat_counter.json --out <dir>/graphics/<slot>_stat_counter.mov
```
Outputs ProRes 4444 RGBA `.mov` (FilmCraft V3), a transparent `.png` still, and the editable `.ecproj` in `graphics/_ecproj/`.

**Values schema:** see `stat-counter.json.example`. Builder: `_families_v2.py::build_stat_counter`. Tested 2026-11-07 on video 19 (Child Stars Who Quit Hollywood) in FilmCraft.
