# photo-annotation

**What:** Ellipse draws around a detail, leader line, label plate (+ optional italic sub). Fails the build if the label cannot sit beside its target.

**When to use:** Pointing at a detail inside a still (ad text, a sign, an object).

**Numbers:** `style.json` -> `layout.photo_annotation`.

**Render:** `python render_family.py --family photo-annotation --values v.json --out graphics/<slot>_photo_annotation.mov`. Builder: `_families_v3.py::build_photo_annotation`. Tested 2026-11-07 on video 19 in FilmCraft (`19_Graphics_Showcase_2.fcproj`).
