# credit-line

**What:** Full-frame black end-credit pastiche: tracked film title, then 'Role ...... NAME' split on the centre gutter, slow upward crawl.

**When to use:** Only for a REAL credit (verify against the film's credits). Not for invented roles.

**Numbers:** `style.json` -> `layout.credit_line` (+ `typography.sizes`, `typography.colors`). Never hard-code values in values JSON except `Hold`.

**Render (never touches committed presets):**
```bash
python Videos-Scripts/Video_Pipeline/presets/documentary-default/render_family.py --family credit-line --values <dir>/values_credit_line.json --out <dir>/graphics/<slot>_credit_line.mov
```
Outputs ProRes 4444 RGBA `.mov` (FilmCraft V3), a transparent `.png` still, and the editable `.ecproj` in `graphics/_ecproj/`.

**Values schema:** see `credit-line.json.example`. Builder: `_families_v2.py::build_credit_line`. Tested 2026-11-07 on video 19 (Child Stars Who Quit Hollywood) in FilmCraft.
