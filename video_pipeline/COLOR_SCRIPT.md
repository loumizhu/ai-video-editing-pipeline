# Colour Script Standard

**Revision 2026-11-09.** Single authority for the story-driven grade: how the colour of a video follows its narration, how phase looks are written, applied per shot and checked. Numbers live in [presets/color/color_rules.json](presets/color/color_rules.json); the tool is [tools/color_script.py](tools/color_script.py) (library `tools/color_lib.py`, self-tests `tools/tests/run_color_selftests.py`, 45 cases). The house grade it builds on is [grade-style.md](presets/documentary-default/grade/grade-style.md).

Before this revision the pipeline had one look for the whole video (`house-style.fcpreset` on every V1 clip) plus a "look bias" table that mapped emotions to colour (grief = desaturate, joy = warm). That table was a universal colour-emotion rule, the exact thing a colour script must not use, and nothing applied it anyway. It is replaced by this standard.

---

## 0. The card (what an agent must remember)

1. **Colour follows story.** Write `story_logic` first: what colour means *in this story* (whose world is warm, what drains it, what comes back). Every phase gives a `reason` tied to a beat. "Blue = sad" is not a reason.
2. **4-8 phases**, by **beat id** (`from_beat` / `to_beat`), never by timecode. Code maps beats to time.
3. **Subtle by default.** A phase is an offset from the house grade within the intensity caps, and its strength on the reference chart stays under **3.0 dE** (subtle). If a viewer can name the filter, it is too strong. Choose one idea per phase: a temperature shift *or* strong split-toning, not both at full.
4. **Shift rarely.** A phase lasts **>= 20 s** (12 s hard floor, montage excepted). Blend 2-6 s at a story drift; cut the colour only when the story cuts (with a `reason`).
5. **Protect the truth.** Archival keeps its look (chroma x0.6, no added grain); black-and-white and toned prints stay neutral; documents never lose contrast; faces get half the chroma; generated graphics are never graded; motifs boost a colour only where it already exists.
6. **Run the gate:** `color_script.py plan` (exit 1 = fix the script), then `color_script.py qa` and look at the strip, the phase sheet and the 70 % over-grade strip.

---

## 1. What we took from the proposed Colour Script System, and what we changed

| Proposal | Verdict | What changed and why |
|---|---|---|
| Colour follows story, every grade traceable to a beat | **ADOPT** | Enforced: `story_logic` (>= 40 chars) and a per-phase `reason` are required (FAIL `SCHEMA`). |
| Contrast between states; restrained range; save big shifts | **ADOPT, measured** | "Restrained" is a number: per-intensity caps per parameter plus a dE budget on a reference chart (neutral ramp, skin, soft primaries, sepia). Maxing every cap at once exceeds the budget on purpose. |
| Subtle beats strong ("if a viewer can name the filter, too strong") | **ADOPT, measured** | Subtle budget 3.0 dE, moderate 5.0, bold 7.0. FAIL `TOO_STRONG`. The 30 % over-grade test is rendered (`strip_overgrade.png`). |
| One look per beat/phase, change between | **ADOPT** | One look per phase; shots inside a phase differ only by protection and cast correction (logged per shot). |
| Preserve authenticity; documents legible | **ADOPT, enforced** | Protection multipliers; `TEXT_CONTRAST` FAIL if a look lowers luma RMS contrast on a document by > 3 %; sepia/cyanotype prints are detected and never "corrected". |
| No universal colour-emotion rules | **ADOPT; it exposed our own bug** | Our `pacing_presets.json` "look_bias" (grief = saturation -10..-20 %, joy = warm highlights) was exactly such a rule. Removed; emotion and intensity now only inform *when* the colour moves, the story decides *which way*. `UNIVERSAL_RULE` WARN on phase reasons. |
| Phases with a "time": "00:00:30-00:03:10" field | **CHANGED** | Phases are given by beat id. An AI-written timecode is FAIL `TIMECODE` (Vcut principle 3: the AI never writes a timecode; code maps beats to time). Phases must tile the beat list with no gap or overlap (`TILING`). |
| Temperature -100..+100 "relative" | **CHANGED** | Abstract scales get interpreted differently by every agent. Units are FilmCraft Lumetri units, each measured on a gray ramp (temperature +10 = R +2 / B -2 levels at mid-gray). The card keys of the proposal (`temp`, `sat`, `blacks_lift`, `shadow_tone`...) are accepted as aliases. |
| Shadow/highlight tint as hex only | **CHANGED** | A hex gives the hue; `split_levels` gives the strength (largest channel shift in 8-bit levels). Without a strength the same hex means anything from invisible to garish. |
| Base look + memory look | **ADOPT** | Base = the house grade (`style.json grade.*`); `base_look` offsets apply to every phase. A memory/flashback look is a normal phase; a return to it is `callback_of` (checked: must stay within 1.0 dE of the phase it echoes unless `callback_variation` says why it differs). |
| Motifs | **ADOPT, bounded** | Implemented as Lumetri's HSL qualifier: a saturation boost on the motif's hue only (subtle max +10 %), so it can only strengthen a colour that is already in the picture. It never paints colour on. Strength per phase (`per_phase`) lets a motif fade with the story. Off on B&W. |
| Colour script strip (image + data) | **ADOPT** | `strip.png` (graded mean per shot, plus a "look direction" row with the deviation amplified x3 so the arc is visible), `strip.json`, `phase_sheet.png` (squint test), `strip_overgrade.png` (70 % test), `color_plan.md` (phase cards). With `--video` a third row samples the rendered cut. |
| Normalize every image first | **ADOPT, conservative** | Cast correction only on near-neutral pixels (min 5 % of the picture, so a sunset or forest is not "corrected"), half strength, capped; never on B&W or toned prints. **Exposure is never auto-corrected**: `NEIGHBOR_JUMP` names the outlier and the agent sets `grade_adjust` with a reason. |
| Protect skin | **ADOPT** | Shots whose `subject` is portrait/person/face (or a detected face when OpenCV is installed) get chroma x0.5 and saturation held to -8..+4; QA `SKIN` FAIL on > 6 deg hue shift or > 15 % chroma change vs the house grade. |
| Avoid clipping, check scopes | **ADOPT** | QA `CLIPPING`: FAIL when a look adds > 1 % clipped pixels vs the house grade, WARN > 0.3 %. |
| Transitions 2-6 s, hard cut on story cuts, callbacks | **ADOPT, adapted to the NLE** | FilmCraft has no per-clip look keyframes in our build path, so a blend is **stepped at the cuts**: shots starting inside the blend window get the interpolated look (quantised to 0.25). With 3.5-4.5 s shots a 4 s blend = 1-2 intermediate shots, which reads as a drift. A colour hard cut needs `transition_in.reason` (FAIL `CUT_NO_REASON`). |
| Never shift more than once per ~20 s | **ADOPT** | Phase < 20 s WARN, < 12 s FAIL, unless `montage: true`. |
| Pair with music, pacing, text | **ADOPT as advice** | Each phase card carries `music` (read by stage 04/08); pace pairing in `color_rules.json pairing`; on-screen text stays house ivory, the phase `accent` may colour a keyword only at >= 3:1 against the charcoal plate (`ACCENT_TEXT` WARN). |
| QC: strip, neighbour, squint, skin/text, over-grade, authenticity, consistency, display | **6 of 8 automated** | Automated: strip, neighbour (`NEIGHBOR_JUMP`), squint sheet + `NO_IDENTITY` (adjacent phases < 1 dE apart), skin, text, clipping, over-grade strip, callback consistency, `FLICKER` (temperature alternating phase after phase). **Human:** archival authenticity and the phone + monitor display check (stage 10 checklist). |
| Options with defaults | **ADOPT** | `options` in the script: intensity subtle / era faithful_archival / arc gradual / bw neutral / motifs on / output video + strip + cards. Recorded in `brief.md`. |
| (missing) | **ADDED** | Measured looks: `--measure` pushes a 17^3 patch grid through FilmCraft's own Lumetri for every look and writes a `.cube` (exact preview for QA, and the same look for Resolve). The analytic preview used without FilmCraft is within **0.82 dE** mean (max 1.32) of FilmCraft on the reference chart. |
| (missing) | **ADDED** | Generated plates and house graphics are never graded: their colours are the brand palette. |

---

## 2. Workflow (Stage 06b, after the beat map)

1. **Read** `beat_map.json` (emotion, intensity, function per beat), the outline's chapters and turning points, and the picture set (archival? colour or B&W? documents?).
2. **Write `story_logic`**: two to five sentences on what colour means in this story. Derive it from the material (the colour of the archive itself, a place, an object, a period), not from colour psychology.
3. **Define phases** (`06_script_edit_plan/color_script.json`, template [templates/color_script.example.json](templates/color_script.example.json)): one per chapter plus special states (turning point, loss, climax, resolution) only where they last >= 20 s. Fill the card: `intent`, `reason`, `palette` (3-5 hex, for the strip and graphics), offsets, split tones + `split_levels`, `grain`, `vignette`, optional `accent`, `motif`, `music`, `transition_in`, `callback_of`.
4. **Plan and gate:** `python tools/color_script.py plan --script color_script.json --beats beats.json --assign assignments.json --beat-map beat_map.json --assets-root <media> --out-dir 06_script_edit_plan/color --measure` (shot-plan builds: `--shot-plan shot_plan.json`). Exit 1 returns to step 3.
5. **Look:** `python tools/color_script.py qa --assign-file 06_script_edit_plan/color/color_assign.json --out-dir 06_script_edit_plan/color`. Open `strip.png`, `phase_sheet.png`, `strip_overgrade.png`. Fix every FAIL; answer every `NEIGHBOR_JUMP` with a story reason or a `grade_adjust` on the outlier (`{"exposure": 0.2, "reason": "underexposed print"}`, capped at 0.4 / 10 / 8).
6. **Build:** `build_full_edit.py` reads `Source/color/color_assign.json` (verdict PASS only) and imports + applies one preset per look in its single pass-2 run (FilmCraft same-run rule). Unmatched clips fall back to the house look; ungraded plates get nothing.
7. **After the render:** `color_script.py qa ... --video <cut.mp4>` adds the rendered row and `RENDER_DRIFT` (a planned look that did not land).

### 2.1 Phase card fields
| Field | Unit / values | Notes |
|---|---|---|
| `id`, `name`, `from_beat`, `to_beat` | beat ids | tile the whole beat list |
| `intent`, `reason` | one line each | reason ties the look to the story logic and a beat |
| `temp` / `temperature`, `tint` | Lumetri units | +10 temp = R +2 / B -2 levels at mid-gray; +10 tint = G -2 |
| `sat` / `saturation` | % of the house saturation | -10 = 10 % less |
| `contrast`, `blacks` / `blacks_lift`, `fade` | Lumetri units | blacks +10 = +4 levels at level 16; fade +20 = +5 at 16 and -6 at 240 (lifted, soft) |
| `shadow_tone`, `highlight_tone`, `split_levels` | hex + levels | hue from the hex, strength from `split_levels` |
| `grain`, `vignette` | added to house noise / vignette | maps to narrative profiles (Clean 35mm, Classic 35mm, Gritty 16mm, Vintage 8mm; see [EDITING_TOOLKIT.md §2.6](EDITING_TOOLKIT.md#26-organic-celluloid-film-grain-synthesis-moving-beyond-screen-overlays)); archival: no added grain |
| `accent`, `palette`, `music` | hex / text | for graphics and the sound mix |
| `motif` | motif id | motif strength per phase in `motifs[].per_phase` (0-1) |
| `transition_in` | `{"type": "blend", "seconds": 2-6}` or `{"type": "cut", "reason": "..."}` | none on the first phase |
| `callback_of`, `callback_variation` | phase id, reason | echo of an earlier palette |
| `montage` | true | allows a phase under 12 s (owner-approved montage only) |

### 2.2 Intensity caps (`color_rules.json intensity_caps`)
| | temp | tint | sat % | contrast | blacks | fade | split levels | grain | vignette | motif sat | dE budget |
|---|---|---|---|---|---|---|---|---|---|---|---|
| subtle (default) | 8 | 5 | 12 | 8 | 6 | 8 | 4 | 1.5 | 6 | 110 | 3.0 |
| moderate | 14 | 8 | 20 | 14 | 10 | 14 | 7 | 3.0 | 12 | 120 | 5.0 |
| bold | 22 | 12 | 30 | 20 | 14 | 20 | 10 | 5.0 | 18 | 130 | 7.0 |

### 2.3 Per-shot protection (multipliers on the phase offsets; the smallest wins)
| Role | How it is found | Effect |
|---|---|---|
| generated graphic | plate (map, card...) | not graded |
| face | `subject` portrait/person/face/people/crowd, or OpenCV face | chroma x0.5, saturation -8..+4 |
| document | `reading: true` or `subject` document/text/newspaper/letter/map | chroma x0.3, contrast >= house, no lift, no fade, saturation -10..0 |
| archival (default for every picture; `"archival": false` for modern material) | era option | faithful: chroma x0.6, no added grain; light tone only: chroma x0.4, contrast/sat x0.5 |
| B&W / toned print | mean chroma < 4, or one hue only (sepia, cyanotype) | neutral: no colour offsets, no motif, no cast correction; `warm_toned` / `cool_toned` = fixed +/-4 temperature |

---

## 3. Gate codes

`plan` FAIL: `SCHEMA`, `TIMECODE`, `BEAT_UNKNOWN`, `TILING`, `PHASE_COUNT` (< 3 or > 10), `SHIFT_TOO_SOON` (< 12 s), `CUT_NO_REASON`, `CALLBACK_REF`, `MOTIF_REF`, `TOO_STRONG`, `NO_PRESET_TEMPLATE`.
`plan` WARN: `CLAMPED`, `PHASE_COUNT` (outside 4-8), `SHIFT_TOO_SOON` (12-20 s), `NO_IDENTITY`, `CALLBACK_DRIFT`, `FLICKER`, `UNIVERSAL_RULE`, `ACCENT_TEXT`, `NO_IMAGE`, `ADJUST_NO_REASON`, `NO_FACE_DETECT`, `NO_MEASURE`.
`qa` FAIL: `TEXT_CONTRAST`, `CLIPPING` (> 1 %), `SKIN`. `qa` WARN: `CLIPPING` (> 0.3 %), `NEIGHBOR_JUMP`, `RENDER_DRIFT`.

Human checks left at stage 10: does the strip's shape match the story's shape; archival authenticity; the master on a phone at low brightness and on a monitor (subtle looks can vanish or turn muddy).

---

## 4. Limits (known, stated)

- Blends are stepped at cuts, not keyframed inside a shot. Within a single long shot the look does not move.
- The analytic preview ignores grain and approximates the vignette; with `--measure` the colour transform is FilmCraft's own (8-bit readout, about +/-0.5 level).
- Face detection needs `opencv-python`; on this machine the installed `cv2` has no cascade classifier, so the `subject` field is what protects faces until it is installed.
- `NEIGHBOR_JUMP` is a heuristic on medians and neutral pixels; two pictures may differ for a good reason. It warns, it does not fail.
- The colour script does not pick the music. It hands each phase's `music` note to the mix.
