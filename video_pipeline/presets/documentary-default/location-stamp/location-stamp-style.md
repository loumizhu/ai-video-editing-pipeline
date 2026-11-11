# location-stamp

**What:** Typewriter place + date slug (Courier = evidence voice) on a charcoal plate, gold rule draws first, underscore cursor steps with the typing then blinks.

**When to use:** First frame of a new place or time jump. Pair with sfx_typewriter_clack. Max 1 per scene; never on consecutive shots.

**Numbers:** `style.json` -> `layout.location_stamp` (+ `typography.sizes`, `typography.colors`). Never hard-code values in values JSON except `Hold`.

**Render (never touches committed presets):**
```bash
python Videos-Scripts/Video_Pipeline/presets/documentary-default/render_family.py --family location-stamp --values <dir>/values_location_stamp.json --out <dir>/graphics/<slot>_location_stamp.mov
```
Outputs ProRes 4444 RGBA `.mov` (FilmCraft V3), a transparent `.png` still, and the editable `.ecproj` in `graphics/_ecproj/`.

**Values schema:** see `location-stamp.json.example`. Builder: `_families_v2.py::build_location_stamp`. Tested 2026-11-07 on video 19 (Child Stars Who Quit Hollywood) in FilmCraft.
