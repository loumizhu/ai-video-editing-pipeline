# group-legend

**What:** 'IN THIS PHOTO' band listing names (2 rows max) + caption.

**When to use:** Group photos where left-to-right order is not documented; say so in the caption.

**Numbers:** `style.json` -> `layout.group_legend`.

**Render:** `python render_family.py --family group-legend --values v.json --out graphics/<slot>_group_legend.mov`. Builder: `_families_v3.py::build_group_legend`. Tested 2026-11-07 on video 19 in FilmCraft (`19_Graphics_Showcase_2.fcproj`).
