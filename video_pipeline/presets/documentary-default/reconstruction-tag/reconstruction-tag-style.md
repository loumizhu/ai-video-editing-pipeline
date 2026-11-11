# reconstruction-tag

**What:** Corner bug (top-left) that labels dramatized footage for the whole reconstructed passage. Red rule + slow-blinking tally square + RECONSTRUCTION in tracked Montserrat.

**When to use:** Every dramatized/reconstructed scene (truth-tier rule, AGENTS.md section 3.5). Hold = length of the reconstruction (hook: about 27 s).

**Numbers:** `style.json` -> `layout.reconstruction_tag` (+ `typography.sizes`, `typography.colors`). Never hard-code values in values JSON except `Hold`.

**Render (never touches committed presets):**
```bash
python Videos-Scripts/Video_Pipeline/presets/documentary-default/render_family.py --family reconstruction-tag --values <dir>/values_reconstruction_tag.json --out <dir>/graphics/<slot>_reconstruction_tag.mov
```
Outputs ProRes 4444 RGBA `.mov` (FilmCraft V3), a transparent `.png` still, and the editable `.ecproj` in `graphics/_ecproj/`.

**Values schema:** see `reconstruction-tag.json.example`. Builder: `_families_v2.py::build_reconstruction_tag`. Tested 2026-11-07 on video 19 (Child Stars Who Quit Hollywood) in FilmCraft.
