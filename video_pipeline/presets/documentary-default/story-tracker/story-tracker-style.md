# story-tracker

**What:** Top-right chip row 'NN/NN  JEFF  DANNY  PETER': done items ivory 70%, upcoming 40%, active gold; gold underline slides from the previous item to the active one.

**When to use:** At each story hand-off in multi-subject videos (3 stars per 15-25 min). Not in the hook.

**Numbers:** `style.json` -> `layout.story_tracker` (+ `typography.sizes`, `typography.colors`). Never hard-code values in values JSON except `Hold`.

**Render (never touches committed presets):**
```bash
python Videos-Scripts/Video_Pipeline/presets/documentary-default/render_family.py --family story-tracker --values <dir>/values_story_tracker.json --out <dir>/graphics/<slot>_story_tracker.mov
```
Outputs ProRes 4444 RGBA `.mov` (FilmCraft V3), a transparent `.png` still, and the editable `.ecproj` in `graphics/_ecproj/`.

**Values schema:** see `story-tracker.json.example`. Builder: `_families_v2.py::build_story_tracker`. Tested 2026-11-07 on video 19 (Child Stars Who Quit Hollywood) in FilmCraft.
