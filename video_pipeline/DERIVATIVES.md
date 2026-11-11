# Derivatives: Alternate Cuts, Shorts / Reels, Chapters, Thumbnails

**Revision 2026-11-09.** All derivatives are built from the same **scene map** (`shot_plan.json` or `beats.json` + `assignments.json`, plus `beat_map.json`). Nothing here re-researches assets. Every derivative runs the same QA (`still_hold_qa`, `variation_report`) with its own preset. Authority for caps and presets: [PACING_AND_ENRICHMENT.md](PACING_AND_ENRICHMENT.md).

Tool status legend (repo convention): **VERIFIED** = built and self-tested; **[TO BUILD]** = specified here, not yet written. Until built, the agent performs the step by hand following the spec and the QA tools still gate the result.

---

## 1. Alternate cuts (opt-in; owner asks for them)

| Variant | What changes | What cannot change | Needs |
|---|---|---|---|
| **Faster** | preset `tense_fast` (or one step faster), shot lengths x0.7, more tier A events, fewer dissolves | narration audio and its timing | new `shot_plan` timings only |
| **Slower** | preset `slow_reflective`, longer shots, dissolves allowed | narration audio, the 8.0 s ceiling | new `shot_plan` timings only |
| **Shorter** | drops low-`priority` beats | must keep every `function: hook / turn / reveal / payoff` beat | **a narration cut list**: `keep.json` -> `make_cuts.py` -> `cuts.json`, then re-map graphics with `map_to_cut_time.py` |

Rules:
1. A faster or slower edit with fixed narration is a **visual-rhythm** change only. Do not promise a shorter video from it.
2. Variants share the asset pool; each gets its own folder `07_Video_Edit/Export/alt_<name>/` with its own `shot_plan_<name>.json`, QA reports and edit report.
3. Generate only on request: each variant multiplies QA time and owner review.
4. Orchestration tool `make_variant.py` **[TO BUILD]**: input scene map + preset (+ `--target-s` for shorter) -> variant shot plan. Until then: re-run Stage 06 with the other preset and reuse Stage 07 assets.

---

## 2. Shorts / Reels (9:16), post-G4

Preset: `shorts_vertical` (shots 1.5-3.0 s, hard cap 4.0 s) + visual preset `presets/shorts-vertical/` (1080x1920, safe window x 90..990, y 300..1450).

1. **Pick the beats:** hook beat + highest-`priority` beats, 20-60 s total. Re-voice nothing: build the narration cut with `make_cuts.py`; Shorts need a clean first-second hook (a `function: hook` beat, or the strongest `turn`).
2. **Re-crop every shot, never just trim the frame.** Per shot, set a `focus_rect` (normalized `[x, y, w, h]` of what matters, faces included) in the shot plan. The 9:16 window is the full height with width = height x 9/16, centred on the focus, clamped to the image. A shot with a face and no `focus_rect` is a defect (face-safe rule). Moves for Shorts come from the motion library with intensity 2-5; `punch_in` and `detail_crop` are the staples.
3. **Tighten pacing:** every still obeys the `shorts_vertical` caps; a tier A/B event at least every 2.0 s on longer stills; kinetic keyword on roughly every second shot (house family `keyword-pop` in `shorts-vertical`).
4. **Captions burned in** (word-timed, from `words.json`), inside the safe window; no title or graphic outside it (`graphics_qa.py --width 1080 --height 1920`).
5. QA: `still_hold_qa.py --preset shorts_vertical`, `variation_report.py --preset shorts_vertical`, `graphics_qa.py`, `dead_air_qa.py` (Shorts allow 0.4 s), `flash_scan.py`.
6. Truth, licensing and naming rules are inherited unchanged; a clip that is only licensed for the long form is not reused without checking the ledger. Never auto-publish.
7. Tool `reframe_9x16.py` **[TO BUILD]**: scene map + `focus_rect`s -> `shorts_shot_plan.json` with `motion.start_rect/end_rect` already converted to 9:16 windows (`pacing_lib.rect_to_scale_pos` handles the keyframe maths), warning on shots without a focus.

---

## 3. Auto-chaptering and thumbnail candidates (inputs to Stage 09)

### Chapters
- Source: `03_hook_outline.md` chapters (authoritative titles) refined by the beat map: a chapter starts at the beat whose `function` is `turn` or `reveal` nearest the outline boundary.
- YouTube constraints (verify against current Help before publishing): first chapter at `0:00`, at least 3 chapters, each at least 10 s, ascending timestamps.
- Output `09_upload/chapters.txt` and the `chapters` field of `metadata.json`. Titles: plain, curiosity-led, no sensational adjectives (editorial standard), formal names.
- Tool `suggest_chapters.py` **[TO BUILD]**: outline + `timing.json` + `beat_map.json` -> `chapters.txt` with the validity checks above.

### Thumbnail candidates
- Candidate frames come from the **highest-intensity beats** with a clear subject, sharp, not mid-dissolve, not under a full-screen text card, and with space for <= 4 words of text.
- Selection checks: sharpness (Laplacian variance), contrast, non-blank, subject present (vision check by the agent), **subject flag** (owner-checked packaging rule: the thumbnail stays on the real subject).
- Candidates are inputs to the existing Stage 09 process (5 title clusters, 4 distinct plates, 0.5 s friction test, 120 px legibility); they never replace it.
- Tool `thumb_candidates.py` **[TO BUILD]**: master + `beat_map.json` -> 12 candidate frames + `thumb_contact_sheet.png` + scores.

<span style="color: purple;">[AI Agent]</span>
