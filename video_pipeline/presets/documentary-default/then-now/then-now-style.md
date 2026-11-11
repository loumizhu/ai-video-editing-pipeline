# then-now

**What:** Centered plate: ON SCREEN label + role name, a red strike draws through the role and it dims; IN REAL LIFE label + real-life identity rises in.

**When to use:** The 'where are they now' payoff of each story. Once per subject.

**Numbers:** `style.json` -> `layout.then_now` (+ `typography.sizes`, `typography.colors`). Never hard-code values in values JSON except `Hold`.

**Render (never touches committed presets):**
```bash
python Videos-Scripts/Video_Pipeline/presets/documentary-default/render_family.py --family then-now --values <dir>/values_then_now.json --out <dir>/graphics/<slot>_then_now.mov
```
Outputs ProRes 4444 RGBA `.mov` (FilmCraft V3), a transparent `.png` still, and the editable `.ecproj` in `graphics/_ecproj/`.

**Values schema:** see `then-now.json.example`. Builder: `_families_v2.py::build_then_now`. Tested 2026-11-07 on video 19 (Child Stars Who Quit Hollywood) in FilmCraft.
