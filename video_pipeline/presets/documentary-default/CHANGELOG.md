# Documentary Default Preset — Taste Changelog & Bake History

All modifications to this preset folder are governed by the `bake-preset` loop (`.agents/skills/bake-preset/SKILL.md`). Every change requires explicit human approval, documented motivation ("why"), and exact before/after parameter values.

---

## [2026-11-10] Version 3.4.0 - Title Family Expansion (Mixkit 312, 305, 196, 240) & line-third Caret Fix

### Why
Expand our title and graphic overlay library with 4 proven, versatile title card styles (Mixkit 312, 305, 196, 240) implemented entirely as instruction-based EffectCraft builders rather than static or manually edited Premiere templates. Also resolves the `line-third` caret height bug.

### Caret Height Fix (`line-third`)
- Heading caret height calibrated to 67 px (exact cap height match) and sub caret to 32 px (sub ink height match).
- Added sub caret 34-frame sweep gate, hold-after-max timing, and blank string validation.

### 4 New Title Families Added
1. `bold-third` (Mixkit 312): Stamped bold heading with animated clearance line sweep + fast snap exit. Ideal for quick cameos and punchy talking-head name stamps.
2. `banner-third` (Mixkit 305): Heavyweight bordered dark banner plate with drawing gold accent border lines, headline + wide-tracked subhead. Ideal for formal investigative interviews and institutional affiliations.
3. `center-title` (Mixkit 196): Centered chapter/act title card with wide-tracked kicker, animated drawing underline, bold title with settling overshoot curve, and accented subhead. Ideal for chapter breaks and historical scene cards.
4. `drop-title` (Mixkit 240): Upper-third step/section stamp with dropping overshoot heading, popping accent rule, and optional tag label. Ideal for procedural steps, tutorials, and section milestones.

### Architecture & Standards
- Self-contained modular architecture in `_families_titles.py`, registered directly into `_families_v2.BUILDERS`.
- Geometry strictly measured from real font metrics via `tw()`; zero hardcoded text widths; enforces 45 px minimum font floor and safe area boundaries.
- Per-family folders created under `presets/documentary-default/` (`bold-third`, `banner-third`, `center-title`, `drop-title`), each with `-style.md` and `.json.example`.
- Verified in FilmCraft testbed (`titles_fc_example.fcproj`) over real footage with all frame checks passing.

### Approved by: pending owner review.

---

## [2026-11-09] Version 3.3.0 - New family `line-third` (Mixkit 311 adaptation)


### Why
We wanted house access to the Mixkit "Simple bottom third" beat (https://mixkit.co/free-premiere-pro-templates/simple-bottom-third-311/) as a preset family instead of editing the template in Premiere. Measured the 1080p preview frame-by-frame (colors, geometry, in/hold/exit timing at 24 fps) and translated it into an instruction-only builder, `_families_v2.build_line_third`.

### Source measurements kept faithful
- Heading #4993EA caps ~68 px equivalent (ours 96 px Montserrat-ExtraBold ≈ 67 px cap), rule white 8 px thick with 24 px project to the right (`rule_project_px`), sub near-white #F5F7F8 wide-tracked below the rule.
- Left flush at safe area x 160, bottom flush at safe bottom 980. Reveal: heading left→right and sub right→left, both decelerating (house `type_in` easeOutCubic), ~1.25 s + 34 f sub; white caret block (66×58 heading / 110×30 sub) rides the reveal front. Exit mirrors reveal; rule draws in 10 f after `lead_in` 0.25 s and retracts 12 f right→left at the end. Total ≈ 5.75 s with 2.5 s hold (`values.Hold` overrides).

### Before → after
- None → `line-third` in `BUILDERS` (`_families_v2.py`), `layout.line_third` in `style.json`, example values + docs `line-third/line-third.json.example`, `line-third/line-third-style.md`.
- Mechanism: first attempt used EffectCraft `Linear Wipe` keyed per frame; probes proved its boundary semantics are font/placement-dependent and unreliable (static-value probes hid half the comp, the same mapping read per-frame rendered the text untouched). → Replaced with a verified primitive: per-glyph cascade (one layer per character, opacity ramps staggered along the same virtual front), caret fronts unchanged. `glyph_frames`/`glyph_out_frames` (6/6) added to `layout.line_third`. Reveal/exit front timing, geometry, and colors are identical to the original wipe design.
- Fonts: `Montserrat-Regular.otf` added to `typography.measure_files` (heading already used Montserrat-ExtraBold). Deliberate deviation from the one-type-voice table: Montserrat matches the Mixkit geometric sans read; the family is opt-in, not a replacement for `lower-third`.
- `tools/graphics_testbed.py`: plan slots with `"bg": null` crashed in the bins step (`project.moveToBin` with an empty `items` list). → Empty item groups are now skipped.

### Verification
- `render_family.py --family line-third` → 5.753 s ProRes 4444 RGBA, block [160, 843, 1027, 980]; per-frame alpha/color analysis of entry (0.5/0.75/1.0 s: blue ink grows left→right, missing region collapses toward the last glyph), hold (1.75–4.0 s stable, rule full 0.667–5.25 s), exit (4.3–5.5 s: heading erased right→left, sub left→right, reverse of entry, carets riding; rule retracts right→left).
- Direction audit caught the sub reversed on first render (entered left-first / exited right-first). → `cascade()` now places each character by the sweep position `(cx - front0)/(front1 - front0)` for entry and the mirrored expression for exit; re-verified numerically (entry x-min shrinks 362→54 = right→left reveal; exit x-min grows 276→746 = left→right erase).
- FilmCraft testbed (temp project, black bg, 2 slots: "Gemma Lauren"/"Compositing Supervisor" and edge case "Dr. Amara Okafor"/"Marine Biologist | Lagos") → both FilmCraft-rendered frames correct at the 75 %-duration check.
- FilmCraft example over footage (16 s of documentary b-roll on V1, both slots on V3): entry/hold/exit frames rendered by FilmCraft at 1.1/5.2/8.15/11.3 s all correct; `preview.mp4` exported.

### Known gaps
- `check_style.py` does not read v2 layout keys and currently crashes on the unrelated missing `presets/shorts-vertical` preset, so dead-key checking did not gate this change.
- Template's exact pixel mask wipe approximated by per-glyph fades (6 f); at 23.976 fps with 1.25 s sweeps the read is near-identical, but not pixel-faithful.

### Approved by: pending owner review.

---

## [2026-11-01] Version 3.0.0 - Rebuild after review (T3b pass 3)

### Why
The 2.0.0 files failed review: lower-third plate did not cover its text, chapter-card and quote-pullout had no scrim, the grade lifted blacks by +40 levels while the docs said the opposite, 6 of 10 SFX missed the stated loudness, ~35 `style.json` keys were dead, and the docs and report contradicted the renders.

### Before -> after (all measured; see `files/T3b_proofs/p3/`)
- Lower-third plate: fixed 780 x 136 px, text overflowed by 290 px -> sized from font metrics: 1155 x 169 px for the example, inside x 160..1760 / y 100..980.
- Chapter card / quote pullout: no plate -> glass plate (72% / 82% charcoal), visible 3 px hairline at 90%, floating quote glyph deleted, wrapping from glyph advances (was `max_chars` 44).
- Fonts: Arial -> Georgia Bold/Italic (matches `toolsender_callout.py`), Arial Bold kept for figures (keyword, chapter label). Keyword size 84 -> 100.
- Grade: contrast 15 -> 10, highlights -10 -> -6, shadows 8 -> 2, blacks -8 -> 0, saturation 105 -> 104, temperature 4 -> 3, exposure 0.05 -> 0 (the old preset file said 0.0, `style.json` said 0.05), tint 1 -> 0. Vignette -30/45/65 -> -10/70/90. p5 luma shift 9.4 -> 49.9 (old) vs -0.94 / -1.39 / +0.44 (new).
- LUT: 8-bit-quantised, black corner 38/255 -> float (8 decimals), black corner 0.03/255, regenerable with `grade/build_grade.py`.
- SFX: spec "-20 LUFS +/-3" (6 files failed) -> events true peak -9.0 +/-1.5 dBTP, room tone -36.0 +/-1.5 LUFS; all 10 pass `sfx/sfx_tool.py verify`. Kenney stamp/pin (file names unverifiable) -> Mixkit 2182 / 1830.
- `style.json`: 35 dead keys removed or wired (`check_style.py`: 0 unread), every builder literal moved in (frames, scale, tracking, plate geometry, leading), safe area now one definition (`safe_margin_x/top/bottom`).
- Docs: README cross-dissolve 15 -> 12 frames (matches `transitions.md`), SFX ceiling -3.5 -> spec above; light-leak/film-burn rows removed (assets never existed).
- Approved by: pending owner review.

---

## [2026-11-01] Version 1.0.0 — Initial Calibrated Baseline (Video 010 Production & Forensic Audit)

### Context & Motivation
Established our channel's initial house-style taste layer, encoding proven editorial parameters from Video 010 (Sir Patrick Stewart Hommage) and structural lessons from Jason Cooperson's AI video editing system. Eliminates ad-hoc improvisation and enforces strict brand aesthetics across FilmCraft and DaVinci Resolve timelines.

### Initial Calibrated Values Baked
- **Typography & Brand Hierarchy:**
  - `typography.colors.ivory`: `#F3EBDD` (`[0.9529, 0.9215, 0.8666]`)
  - `typography.colors.gold`: `#FFE8B8` (`[1.0, 0.9098, 0.7215]`)
  - `typography.colors.charcoal`: `#0F1218`
  - Font sizes: Hero Title 72px Bold, Lower-Third Name 56px, Role 48px, Keyword Pop 84px, Quote Body 48px, Author 45px (hard rule: no font < 45px).
- **Motion & Easing:**
  - In/Out duration: 12 frames (0.5005s @ 23.976 fps).
  - Fade duration: 0.70s.
  - Easing: Real Bezier curves (`KeyframeInterpolationType.BEZIER`, `KeyframeEase(0.0, 0.75)`).
  - Keyword pop: Calibrated scale overshoot (30% -> 112% crest at frame 8 -> 100% rest at frame 12).
- **Safe Margins & Text Alignment:**
  - Safe margin X: 160px (action safe: 96px, title safe: 192px).
  - Left-justified text (`ParagraphJustification.LEFT_JUSTIFY`) on lower-thirds, eliminating left-edge clipping observed in early audit passes.
- **Color Grading & Texture:**
  - Lumetri: Contrast +15.0, Shadows +8.0, Highlights -10.0, Blacks -8.0, Saturation 105.0%, Temperature +4.0.
  - Film Grain (`noise`): 4.5% monochromatic noise (`Float(4.5)`).
  - Vignette: -30.0% oval shading, feather 65.0%, midpoint 45.0%.
  - 3D LUT: Generated `house-look.cube` for dual-NLE parity.
- **Audio Mix Targets:**
  - Dialogue target: -16.0 LUFS, True Peak <= -1.8 dBTP.
  - Music ducking: -24.0 dB (speech), -28.0 dB (archival sync clips).
  - Master mix ceiling: < -1.5 dBTP.
  - SFX starter library: 10 CC0 audio files normalized to -24 to -18 LUFS with true peak <= -3.0 dBTP.

---

## Bake Entry Template (for future edit sessions)

```markdown
### [YYYY-MM-DD] <Video_ID / Title> — Post-Edit Bake
- **Motivation / Why:** <Concrete explanation of what the owner requested or what friction occurred during review>
- **Preset File(s) Affected:** `<preset_file_path>`
- **Parameter Diff:**
  - Path: `<parameter_json_path>`
  - Before: `<old_value>`
  - After:  `<new_value>`
- **Renders Updated:** `<family>/renders/<image>.png` re-verified.
- **Approved By:** <Channel Owner / Lead Editor>
```

## 2026-11-07 (3.1.0): title & overlay families v2
- Added 9 EffectCraft families: reconstruction-tag, location-stamp, stat-counter, timeline-strip, then-now, source-tag, credit-line, story-tracker, kinetic-quote (`_families_v2.py`, one folder each with style md + values example).
- Added `render_family.py` (one renderer for v1 + v2 families; keeps editable `.ecproj`).
- style.json: new fonts (Montserrat Bold/ExtraBold = data voice, Courier New Bold = evidence voice), colours signal_red + slate, sizes and `layout.*` blocks for the new families. Existing values unchanged. Backup: `style.json.bak_2026-11-07`.
- Why: video 19 needed reconstruction labelling, truth-tier citations, counters and then/now payoffs that the 4 v1 families could not express.

## 2026-11-07 (3.2.0): new type system + people/evidence families
- Fonts (OFL, shipped in ./fonts, installed per user via install_fonts.ps1): DM Serif Display = names/titles; Spectral SemiBold/Medium/MediumItalic = quotes, body, roles; Barlow Condensed SemiBold/ExtraBold = labels, tags, numbers; Courier Prime Bold = stamps. Replaces Georgia/Montserrat/Arial/Courier New. Owner asked for "better, more appropriate fonts".
- Sizes retuned for the condensed/display faces (tag 48, stat number 250, keyword pop 130, name 60...). Trackings lowered for Barlow.
- New families: person-pin, people-panel, group-legend, article-highlight, photo-annotation (`_families_v3.py`).
- `_common.font_for` now looks in ./fonts first.
