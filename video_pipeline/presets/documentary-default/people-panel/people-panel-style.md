# people-panel

**What:** Full-frame card: 1-3 portraits cropped on a focus point (FX/FY in source pixels, Zoom), gold rule, name + role under each, optional tracked title.

**When to use:** Comparing or introducing 2-3 people at once.

**Numbers:** `style.json` -> `layout.people_panel`.

**Render:** `python render_family.py --family people-panel --values v.json --out graphics/<slot>_people_panel.mov`. Builder: `_families_v3.py::build_people_panel`. Tested 2026-11-07 on video 19 in FilmCraft (`19_Graphics_Showcase_2.fcproj`).
