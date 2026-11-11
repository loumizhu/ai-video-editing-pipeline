# Stage 06: Visual Pacing Subdivision & Shot Planning

## Purpose
Translate locked voiceover timing (`timing.json` or estimated fallback) into a continuous, gapless sequence of visual shot slots in `06_script_edit_plan/shot_plan.json`. Enforce documentary visual pacing (3.5–4.5s standard cuts; 5.0–6.0s for text cards/quotes), map visual slots directly to canonical Vcut §3.3 track roles, assign motion/look presets from `Vcut_Effects_Library.md`, and specify custom graphic overlays (callouts, maps, articles, engagement extras) adhering strictly to [EDITING_TOOLKIT.md](../EDITING_TOOLKIT.md).
Reference: [Vcut Step 03: Shot Planning and Visuals](../../../../Vcut/03_Shot_Planning_and_Visuals.md) and [Vcut Data Contracts §3.3](../../../../Vcut/Vcut_Data_Contracts.md#33-shot_planjson).

> **Pacing standard (Revision 2026-11-09):** the cadence below is the `documentary_standard` preset. The authoritative still-hold caps, enrichment ladder, beat map, pacing presets and motion library are in [PACING_AND_ENRICHMENT.md](../PACING_AND_ENRICHMENT.md). A still run never exceeds its hard cap (6.0 s default); a 12 s still is a Stage 06 failure.

## Inputs
- `Videos-Scripts/_style_memory/style_memory.md` (channel taste rules; record applied rule ids in the plan header as `style_memory_rules_applied`).
- `_pipeline/brief.md` field `pacing_preset` (default `documentary_standard`).
- `06_script_edit_plan/timing.json` (canonical timing manifest with word-level timestamps).
- `_pipeline/03_hook_outline.md` (chapter structure and emotional open loops).
- `06_script_edit_plan/visual_intents.md` (scene-by-scene visual targets).
- `01_research/QUOTE_PROOF.md` & `03_media/BEST_LINES_SELFCHECK.txt` (quote and framing proof).
- [EDITING_TOOLKIT.md](../EDITING_TOOLKIT.md) (transitions, callouts, maps, effects catalog, rhythm rules).

## Outputs
- `06_script_edit_plan/color_script.json` (Stage 06b: story logic + 4-8 colour phases by beat id; template `templates/color_script.example.json`; standard [COLOR_SCRIPT.md](../COLOR_SCRIPT.md)) and `06_script_edit_plan/color/color_plan.md` (phase cards, gate result).
- `06_script_edit_plan/beat_map.json` (Stage 06a: emotion, intensity, function, info_type, anchor_phrase, priority per beat; template `templates/beat_map.example.json`).
- `06_script_edit_plan/qa_still_hold.json` / `.md` and `06_script_edit_plan/edit_report.md` (+ `variation_log.json`) from the Stage 06 gate.
- `06_script_edit_plan/shot_plan.json` (structured shot slots conforming to Vcut §3.3 + toolkit extensions).
- `06_script_edit_plan/NAMING_REVERENCE_CHECK.txt` (extended with grep proof on text card lines).

## Executor
- **Worker:** Antigravity (Gemini Flash medium), effort: medium.

## Tools
- `python ../Video_Pipeline/tools/still_hold_qa.py --shot-plan 06_script_edit_plan/shot_plan.json [--beat-map 06_script_edit_plan/beat_map.json] --out-json 06_script_edit_plan/qa_still_hold.json --out-md 06_script_edit_plan/qa_still_hold.md` (**VERIFIED; Revision 2026-11-09**; exit 1 on any still run over its cap).
- `python ../Video_Pipeline/tools/variation_report.py --shot-plan 06_script_edit_plan/shot_plan.json --out-json 06_script_edit_plan/variation_log.json --out-md 06_script_edit_plan/edit_report.md` (**VERIFIED; Revision 2026-11-09**; motion / transition / SFX / enrichment variation + rationale report).
- `pacing_lib.pick_motion` (motion library selection; `tools/pacing_lib.py`).
- `[TO BUILD]` JSON schema validator checking slot continuity and toolkit field presence.
- `[TO BUILD]` Grep script scanning `callout.name`, `line_1_text` for formal naming compliance.

## Pipeline Field to Vcut §3.3 Schema & Toolkit Downstream Mapping
| Pipeline Field | Vcut Target Field | Mapping Logic & Schema Placement |
|---|---|---|
| `slot_id` | `slot_id` (§3.3) | Unique slot ID (`s0001`, `s0002`...). |
| `start_ms` / `end_ms` | `anchor_in` / `anchor_out` (§3.3) | Anchored to `timing.json` line IDs and word boundaries. |
| `duration_ms` | `min_frames` / `max_frames` (§3.3) | 30fps: 3,500–4,500ms = 105–135 frames; **Cards/Articles:** 5,000–6,000ms = 150–180 frames. |
| `visual_type` | `track_role` (§3.3) | Canonical Vcut track role: `broll` (footage/stills) or `graphics` (custom overlay). |
| `candidate_assets` | `candidates[].asset_ref` (§3.3) | Array of candidate references (`pexels:<id>`, `owner:<id>`) with `score` and `qc`. |
| `selected_asset` | `chosen` (§3.3) | Selected asset reference string (e.g. `"pexels:3129957"` or `"owner:img_01"`). |
| `motion` | `motion` (§3.5) | `{ "preset": "mot.push_in", "carrier": "native", "start_rect": [0,0,1,1], "end_rect": [0.05,0.05,0.9,0.9] }`. |
| `effects` | `effects[]` (§3.5) | Exact preset names from `Vcut_Effects_Library.md` (`[{ "preset": "look.archival" }]`). |
| `transitions` | `transitions[]` (§3.5) | Transition preset (`tr.cross_dissolve`, `tr.dip_black`, `tr.whip_pan`, or `pipeline_ext.*`), duration, alignment. |
| `callout` | `pipeline_ext.callout` | Custom character callout object (`name`, `role`, `subtitle`, `position`, `hold_duration_s`). |
| `map` | `pipeline_ext.map` | Purposeful map object (`type`, `title`, `subtitle`, `points`, `alpha_overlay`, `duration_s`). Types: `route_draw`, `locator_zoom`, `distance_line`, `multi_pin_cluster`, `comparison_inset`, `hidden_connection`. |
| `article` | `pipeline_ext.article` | Article highlight object (`headline`, `outlet`, `date`, `body`, `quote`, `style`, `redact`, `attribution`, `duration_s`). Note: `body` contains full text from `01_research/QUOTE_PROOF.md` (see [Toolkit §2.5](../EDITING_TOOLKIT.md#25-article-display--text-highlighting)); `quote` feeds `--highlight` in `render_article.py`; `attribution` feeds `--attribution`. |
| `media_type` | `pipeline_ext.media_type` | `image` \| `video` \| `plate` (full-frame graphic). Unknown media is treated as a still (conservative). |
| `asset_group` | `pipeline_ext.asset_group` | Same-idea group id; stills sharing it count as ONE still run for the hold cap. |
| `beat` / `beat_id` | `pipeline_ext.beat` | `{ "emotion", "intensity" }` copied from `beat_map.json` (drives caps, motion, transitions). |
| `anchor_phrase` | `pipeline_ext.anchor_phrase` | The narration words the picture must show (search query + QA of picture vs words). |
| `preset` | `pipeline_ext.preset` | Optional per-slot pacing preset override (needs `rationale`). |
| `motion.move` | `pipeline_ext.motion.move` | Motion library id (`push_slow`, `detail_crop`, ...), plus `target_rect` when required. |
| `enrichments[]` | `pipeline_ext.enrichments` | `[{ "type": "photo_annotation", "at_ms": 18500, "anchor_word": "phone", "rationale": "..." }]`; types from `enrichment_catalog.json`. Tier A/B count as events inside a still run. |
| `transition_in` / `sfx` | `pipeline_ext.transition_in` / `.sfx` | Transition type entering the slot; SFX file ids (variation tracking). |
| `rationale` | `pipeline_ext.rationale` | One sentence tying a major choice to the line (required for dynamic transitions, plates, tier C/D, intensity >= 4, preset overrides). |
| `still_hold_waiver` | `pipeline_ext.still_hold_waiver` | **Owner only.** Reason string; agents never write it. |
| `extras` | `pipeline_ext.extras` | Array of engagement objects E1–E10 matching [Toolkit §3](../EDITING_TOOLKIT.md#3-additional-engagement-ideas-61-to-610): `date_strip` (`date`), `stamp` (`word`, `color`), `split_screen` (`left_ref`, `right_ref`), `soundbite_card` (`speaker`, `quote`), `big_number` (`number`, `label`, `citation`), `spotlight` (`target_rect`), `photo_stack` (`photos`), `keyword_pop` (`word`), `chapter_title` (`title`, `subtitle`), `texture_bed` (`preset`, `opacity`). |

## Steps
1. **Verification & Ingestion:** Ingest `timing.json` (real or estimated) and `06_script_edit_plan/visual_intents.md`.
1b. **Stage 06a Beat Map:** rate every beat (`beats.json` from `make_beats.py`, max 6.0 s) for `emotion` (calm / tension / grief / joy / neutral), `intensity` 1-5, `function`, `info_type`, `anchor_phrase`, `priority` per [PACING_AND_ENRICHMENT.md section 4](../PACING_AND_ENRICHMENT.md#4-beat-map-emotion-intensity-function). AI rates by beat id; code maps ids to times. Worker: Argon-class; reviewer: Sonnet.
1c. **Stage 06b Colour Script (Revision 2026-11-09):** from the beat map, the outline's turning points and the picture set, write `story_logic` (what colour means in this story, never a universal rule) and 4-8 phases by beat id per [COLOR_SCRIPT.md](../COLOR_SCRIPT.md) (subtle by default, each phase >= 20 s, colour hard cut only on a story cut with a reason). Gate: `python ../Video_Pipeline/tools/color_script.py plan --script 06_script_edit_plan/color_script.json --shot-plan 06_script_edit_plan/shot_plan.json --beat-map 06_script_edit_plan/beat_map.json --out-dir 06_script_edit_plan/color` (re-run after step 7; pictures are checked at Stage 07/08). Worker: Argon-class; reviewer: Sonnet.
2. **Pacing Subdivision:** Segment timeline per the chosen preset (documentary_standard: 3.5–4.5s; 5.0–6.0s for text/quote cards; 4.5–5.5s for articles), scaled by beat intensity. **Every beat longer than the soft cap gets a second distinct visual (`sub`) or a plate; never one still across a long beat.**
3. **Effect Assignment:** Pick a move from the motion library for every still (`pick_motion`: emotion, intensity, subject, cooldown; no 3rd identical move in a row), record it in `motion`. No per-slot look preset: the grade comes from the colour script (a slot may carry `grade_adjust` with a reason, or `"archival": false` for modern material).
3b. **Enrichment Assignment:** for each still that must hold past the soft cap, choose tier A/B events from what the line says (narration-to-method table, PACING_AND_ENRICHMENT.md section 3.2), anchored to the spoken word (`at_ms`); write a `rationale` for each major choice. Cut first, enrich second, decorate never.
4. **Custom Graphics Specification:** Populate `callout`, `map`, `article`, `enrichments` or `extras` fields adhering to [EDITING_TOOLKIT.md](../EDITING_TOOLKIT.md) rules.
5. **Eyes & Framing Check:** Verify `eyes_check_ref` contact sheet in `03_media/` confirms speaker target.
6. **Naming Reverence Grep:** Grep `callout.name` and text card lines for formal names, appending to `NAMING_REVERENCE_CHECK.txt`.
7. **Schema Output:** Validate and save to `06_script_edit_plan/shot_plan.json`.
8. **Pacing Gate:** run `still_hold_qa.py` and `variation_report.py` (commands above). Exit 1 returns to step 2 with the report; max 3 passes.

## Acceptance Checklist
- [ ] 100% of voiceover timeline covered with contiguous shot slots (zero gaps).
- [ ] Visual pacing follows the chosen preset (documentary_standard: 3.5–4.5s per shot, 5.0–6.0s for text cards) and **`still_hold_qa.py` is PASS: no still run over its hard cap (6.0 s default), none over the soft cap (4.5 s) without enrichment events** (Revision 2026-11-09).
- [ ] `color_script.json` present; `color_script.py plan` exit 0 (story logic stated, 4-8 phases tiling every beat, subtle budget, no shift < 12 s, cut shifts have a reason) (Revision 2026-11-09).
- [ ] `beat_map.json` present for 100% of beats; intensity 5 on <= 20 % of beats; >= 3 distinct intensity levels per chapter.
- [ ] `variation_report.py` is PASS (no 3rd identical motion in a row, no 3 identical dynamic transitions, enrichment caps respected); every major choice has a `rationale`.
- [ ] Every slot carries an effect assignment from `Vcut_Effects_Library.md`.
- [ ] Zero FilmCraft default title/lower-third presets; all graphics mapped to custom tool pipeline.
- [ ] Naming reverence verified via grep in `NAMING_REVERENCE_CHECK.txt`.
- [ ] Output saved to `06_script_edit_plan/shot_plan.json` conforming to Vcut §3.3 + toolkit extensions.

## Reviewer
- Claude Sonnet via [code.md](../../../.agents/skills/orchestrate/reviewers/code.md) (beat map: judge the ratings against the rubric, not the code).

## Human Gate
- **No:** Schema-validated autonomous milestone; feeds directly into asset and graphics generation.

## Failure & Retry
- If slot duration exceeds bounds or fields invalid, re-subdivide slots and validate. Max 3 passes.

<span style="color: purple;">[AI Agent]</span>
