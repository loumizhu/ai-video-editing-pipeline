# Stage 07b: Custom Graphic Asset Build & Alpha Overlay Packaging

## Purpose
Render broadcast-quality custom graphics specified in `06_script_edit_plan/shot_plan.json`. Animated graphic families (lower-third, chapter-card, keyword-pop, quote-pullout) originate from the house-style presets (`presets/documentary-default/` or `presets/shorts-vertical/`) rendered via EffectCraft templates into pre-rendered ProRes 4444 `.mov` alpha clips. Purposeful maps, article clippings with marker-sweep highlights, and static document cards are rendered via deterministic Pillow tools. Eliminate NLE default presets entirely. Package all assets into `07_Video_Edit/graphics/` alongside automated QA verification (`graphics_qa.py`), an asset ledger `graphics_manifest.json`, and a visual contact sheet.
Reference: [Editing Toolkit](../EDITING_TOOLKIT.md) and [Vcut Step 05: Timeline Manifest and QA](../../../../Vcut/05_Timeline_Manifest_and_QA.md).

## Families & Testbed (Revision 2026-11-07)
- Full list of on-screen text families, when to use each, density rules and backlog: [GRAPHICS_CATALOG.md](../GRAPHICS_CATALOG.md).
- Render any EffectCraft family (v1 or v2): `python ../Video_Pipeline/presets/documentary-default/render_family.py --family <name> --values <values.json> --out 07_Video_Edit/graphics/<slot>_<family>.mov`.
- Prove a set of graphics in FilmCraft before assembly: `python ../Video_Pipeline/tools/graphics_testbed.py --plan 07_Video_Edit/graphics_test/graphics_test_plan.json --export`.

## Inputs
- `06_script_edit_plan/shot_plan.json` (visual plan with populated `callout`, `map`, `article`, or `extras` fields).
- `01_research/FACT_BASELINE.md` & `01_research/QUOTE_PROOF.md` (verified names, dates, quotes, and primary sources).
- `presets/documentary-default/` (house-style presets: typography, glass plates, palettes, animation timings; Revision 2026-11-01).
- `tools/data/ne_50m_land.geojson` (Natural Earth Public Domain 1:50m land vector dataset).
- `06_script_edit_plan/timing.json` (word-level timestamps for animated highlight sweeps).

## Outputs
- `07_Video_Edit/graphics/<slot>_lower_third.mov` / `.png` (animated face-safe character callouts from house preset).
- `07_Video_Edit/graphics/<slot>_chapter_card.mov` / `.png` (animated act progression cards from house preset).
- `07_Video_Edit/graphics/<slot>_quote_pullout.mov` / `.png` (animated glass quote pull-outs from house preset).
- `07_Video_Edit/graphics/<slot>_keyword_pop.mov` / `.png` (animated kinetic word pops from house preset).
- `07_Video_Edit/graphics/<slot>_map.png` (purposeful cartographic overlays or full frames via `render_map.py`).
- `07_Video_Edit/graphics/<slot>_article.png` (article clipping with synchronized highlight sweep via `render_article.py`).
- `07_Video_Edit/graphics/<slot>_<card>.png` (static date strips, stamps, and counter cards via `render_card.py`).
- `07_Video_Edit/graphics/graphics_manifest.json` (asset ledger with hashes, alpha channel metadata, and licences).
- `07_Video_Edit/graphics/contact_sheet.png` (multi-asset visual validation contact sheet).

## Executor
- **Worker / Tool:** Tool (`EffectCraft` + `python ../Video_Pipeline/tools/render_*.py` + `graphics_qa.py` + `ffmpeg`) + Antigravity (asset packaging).

## Tools
- `EffectCraft CLI` (`0.19.0`; renders animated preset templates to ProRes 4444 `.mov` with alpha; Revision 2026-11-01).
- `powershell -File ../Video_Pipeline/presets/<preset>/<family>/render.ps1` (preset rendering orchestrator; Revision 2026-11-01).
- `python ../Video_Pipeline/tools/graphics_qa.py` (**VERIFIED; Revision 2026-11-01**; audits canvas dimensions and 90% title-safe margin; cap-height floor is guarded by EffectCraft build-time 45px rule).
- `python ../Video_Pipeline/tools/render_callout.py` (custom static character introduction callouts).
- `python ../Video_Pipeline/tools/render_map.py` (purposeful locator, route draw-on maps, and alpha overlay mode).
- `python ../Video_Pipeline/tools/render_article.py` (article display and precise marker-sweep highlight renderer).
- `python ../Video_Pipeline/tools/render_card.py` (date strips, stamps, big stats, keywords, chapter cards).
- `python ../Video_Pipeline/tools/write_graphics_manifest.py` (scans graphics directory, computes hashes and alpha metadata).
- `ffmpeg` (contact sheet generation and video packaging).

## Steps
1. **Manifest Parsing:** Parse `06_script_edit_plan/shot_plan.json` for slots requesting custom graphics (`callout`, `map`, `article`, `extras`) **and every entry of `enrichments[]`** (Revision 2026-11-09). Build each enrichment with the tool named in `presets/pacing/enrichment_catalog.json` (photo-annotation, spotlight, keyword-pop, stat-counter, location-stamp, date strip, narration plate...). Each enrichment is timed from its `at_ms` (the spoken word), leaves with its sentence, and a `narration_plate` text is verbatim narration or a verified fact only.
2. **Animated Preset Families Build (Revision 2026-11-01):** *(Working directory: Videos-Scripts/<NN>_<Slug>/)*. For standard graphics (lower-thirds, chapter cards, quote pull-outs, kinetic keyword pops), build via the house presets (`../Video_Pipeline/presets/documentary-default/` or `../Video_Pipeline/presets/shorts-vertical/`):
   - Write project-specific values JSON (e.g. `07_Video_Edit/graphics/values_<family>.json`) following the schema in `../Video_Pipeline/presets/documentary-default/<family>/<family>.json.example`.
   - Render animated ProRes 4444 alpha `.mov` directly into the project graphics folder:
     ```powershell
     powershell -NoProfile -File "../Video_Pipeline/presets/documentary-default/<family>/render.ps1" -Values "07_Video_Edit/graphics/values_<family>.json" -Out "07_Video_Edit/graphics/<family>.mov"
     ```
     *(Note: NEVER pass `-UpdateTemplate` during video production. Modifying committed presets is strictly restricted to `bake-preset` on explicit owner approval).*
3. **Purposeful Maps Build:** For each `map` slot, verify the "geography is the point" trigger, resolve waypoints from `FACT_BASELINE.md`, and execute `render_map.py` with real Natural Earth vector cartography (`--alpha-overlay` if placed over footage).
4. **Article & Highlight Build:** For each `article` slot, match quoted passage to `QUOTE_PROOF.md`, apply redactions for private data (`--redact`), and execute `render_article.py` with exact substring highlight sweep (feeding `quote` to `--highlight`, `body` from `QUOTE_PROOF.md`, and `attribution` to `--attribution`).
5. **Additional Engagement Assets & Fallbacks:** Render timeline bars, date stamps, and quote cards via `python ../Video_Pipeline/tools/render_card.py` or `render_callout.py` according to [EDITING_TOOLKIT.md](../EDITING_TOOLKIT.md) specs.
6. **Automated Graphics QA Verification (Revision 2026-11-01):** Inspect all rendered overlay graphics for canvas bounds and 90% title-safe margins:
   ```bash
   python ../Video_Pipeline/tools/graphics_qa.py --input "07_Video_Edit/graphics" --out-json "07_Video_Edit/graphics/qa_graphics.json" --out-md "07_Video_Edit/graphics/qa_graphics.md"
   python ../Video_Pipeline/presets/documentary-default/verify_render.py --mov "07_Video_Edit/graphics/<family>.mov" --plate --out-json "07_Video_Edit/graphics/qa_verify.json"
   ```
7. **Compile Manifest & Contact Sheet:** Generate `graphics_manifest.json` and visual contact sheet *(Working directory: Videos-Scripts/<NN>_<Slug>/)*:
   ```bash
   python ../Video_Pipeline/tools/write_graphics_manifest.py --dir "07_Video_Edit/graphics" --out "07_Video_Edit/graphics/graphics_manifest.json"
   ffmpeg -y -i "07_Video_Edit/graphics/s0001_callout.png" -i "07_Video_Edit/graphics/s0002_map.png" -i "07_Video_Edit/graphics/s0003_article.png" -filter_complex "[0:v]scale=640:360[v0]; [1:v]scale=640:360[v1]; [2:v]scale=640:360[v2]; [v0][v1][v2]hstack=inputs=3[out]" -map "[out]" "07_Video_Edit/graphics/contact_sheet.png"
   ```

## Acceptance Checklist
- [ ] 100% of custom graphics specified in `shot_plan.json` rendered to `07_Video_Edit/graphics/`.
- [ ] Zero built-in NLE default title or lower-third presets used; animated families sourced from house presets without mutating committed templates (Revision 2026-11-01).
- [ ] Character callouts use verified formal names (Video 010: "Cecil", not "Cec").
- [ ] Maps triggered only for geographic narrative beats; Natural Earth attribution present.
- [ ] Articles display outlet, date, source attribution, and exact substring highlights.
- [ ] `graphics_qa.py` verification passes (0 safe-margin violations; 45px cap-height floor enforced at template build; Revision 2026-11-01).
- [ ] `graphics_manifest.json` and visual `contact_sheet.png` generated and verified.

## Reviewer
- Claude Sonnet via [code.md](../../../.agents/skills/orchestrate/reviewers/code.md).

## Human Gate
- **No:** Autonomous asset generation milestone verified by contact sheet and checksums.

## Failure & Retry
- If a custom script fails, apply the bypass fallback (simpler Pillow renderer -> flagged placeholder plate), log to `_pipeline/BYPASS_LOG.md`, and proceed to Stage 08. Max 3 passes.
