# source-tag

**What:** Bottom-right citation: coloured truth-tier chip (DOCUMENTED gold, QUOTED ivory, REPORTED slate, ALLEGED/RECONSTRUCTION red) + italic source line.

**When to use:** Whenever narration quotes or relies on a named outlet. Required on every on-screen quote that is not self-attributed.

**Numbers:** `style.json` -> `layout.source_tag` (+ `typography.sizes`, `typography.colors`). Never hard-code values in values JSON except `Hold`.

**Render (never touches committed presets):**
```bash
python Videos-Scripts/Video_Pipeline/presets/documentary-default/render_family.py --family source-tag --values <dir>/values_source_tag.json --out <dir>/graphics/<slot>_source_tag.mov
```
Outputs ProRes 4444 RGBA `.mov` (FilmCraft V3), a transparent `.png` still, and the editable `.ecproj` in `graphics/_ecproj/`.

**Values schema:** see `source-tag.json.example`. Builder: `_families_v2.py::build_source_tag`. Tested 2026-11-07 on video 19 (Child Stars Who Quit Hollywood) in FilmCraft.
