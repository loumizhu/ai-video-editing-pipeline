# person-pin

**What:** Ring on a person + leader line + name/role plate; 1-3 people in one frame. X/Y/Dir/Length per person come from the plan (read off the frame, never guessed from faces).

**When to use:** Naming people inside a shot. For 4+ people or undocumented order use group-legend.

**Numbers:** `style.json` -> `layout.person_pin`.

**Render:** `python render_family.py --family person-pin --values v.json --out graphics/<slot>_person_pin.mov`. Builder: `_families_v3.py::build_person_pin`. Tested 2026-11-07 on video 19 in FilmCraft (`19_Graphics_Showcase_2.fcproj`).
