# Documentary House Style Preset ("taste layer")

Our equivalent of Jason Cooperson's `presets/youtube/default/` folder (FORENSIC_REPORT §2, §3 P1). Style values, animated templates and editing rules are files the agent follows; owner corrections are baked back in with the bake loop (`.agents/skills/bake-preset/SKILL.md`).

## 1. Read order for an agent
1. `style.json`: single source of every number (canvas, safe area, fonts, sizes, colours, layout, animation, grade, audio). 102 leaf keys, every one read by a script (`python check_style.py` -> "unread: 0").
2. `<family>/<family>-style.md`: when to use, caps, timing, measured geometry. Families: `lower-third`, `chapter-card`, `keyword-pop`, `quote-pullout`.
3. `transitions.md`: transition vocabulary, frames, caps (single source for frame counts).
4. `animations.md`, `creative-moves.md`: Ken Burns, focal zoom, photo stack, 12 fps stepped option, grain/glow. (Glow numbers in `creative-moves.md` are not wired to `style.json` and not rendered.)
5. `sfx.md`, `sfx.json`, `sfx/LICENSES.md`, `music.md`: audio roles, licences, loudness spec, ducking.
6. `grade/grade-style.md`: the look, how it is built (`grade/build_grade.py`) and measured.

## 2. Safe area (one definition)
`canvas.safe_margin_x` 160, `safe_margin_top` 100, `safe_margin_bottom` 100 -> graphics (plates included) stay inside x 160..1760, y 100..980 once their in-animation has settled. Builders abort if a computed box leaves it. The `shorts-vertical` override uses 90 / 300 / 470 -> x 90..990, y 300..1450. `tools\graphics_qa.py` uses a looser 90% title-safe rectangle (x 96..1824, y 54..1026); passing it is necessary, not sufficient. `verify_render.py` checks the stricter safe rect on every frame.

## 3. How each graphic is produced
`powershell -NoProfile -File <family>\render.ps1 [-Values my.json] [-Out file.mov] [-UpdateTemplate]`
- `build.py` reads `style.json`, measures the text with the real font, sizes plates and wraps lines, writes the EffectCraft project/template (temp folder unless `-UpdateTemplate`), then `effectcraft-cli render --format prores --prores 4444 --channels rgba` -> `.mov` and `render-frame` -> `.png`.
- Because plates depend on the text, never render a committed `.ectemplate` with different text; always go through `render.ps1`.
- Frame-by-frame check: `python verify_render.py --mov <file> [--plate]`; one-frame check: `python ..\..\tools\graphics_qa.py --input <file>`.
- FilmCraft cannot import `.ectemplate`: the `.mov` goes on V3. Resolve: same `.mov` on a video track above the picture.

## 4. FilmCraft vs DaVinci Resolve
| | FilmCraft | Resolve Studio |
|---|---|---|
| Driver | `filmcraft-cli` (headless) | scripting API, needs the GUI session (DOCUMENTED-NOT-TESTED here) |
| Graphics | ProRes 4444 `.mov` on V3 | same `.mov` on V3/V4 |
| Grade | Colour-script looks `CS_<phase>_<hash>.fcpreset` when the video has a PASSing `color_assign.json` ([COLOR_SCRIPT.md](../../COLOR_SCRIPT.md)); otherwise `house-style.fcpreset` (same-`run` import + apply) or `lumetri.setInputLut` with `house-look.cube` | `item.SetLUT(1, "house-look.cube")` (colour only; grain and vignette are added separately) |
| Transitions | `sequence.applyVideoTransition` | native transitions, FCPXML conform, or pre-rendered overlay |
| Ducking | `essentialSound.generateDucking` or FFmpeg sidechain | Fairlight dynamics or FFmpeg sidechain |

## 5. Numbers that other docs repeat (check these before editing them)
- Frames: in 17 (0.709 s), out 12 (0.500 s) at 23.976 fps; cross dissolve **12 frames**, dip to black 24 frames (see `transitions.md`).
- SFX: events true peak -9.0 +/-1.5 dBTP, room tone -36.0 +/-1.5 LUFS integrated (`sfx.md`). Dialogue -16.0 LUFS, master ceiling -1.8 dBTP.
- Grade: contrast +10, highlights -6, shadows +2, saturation 104, temperature +3, grain 4.5, vignette -10 / 70 / 90.
- Not built: light-leak and film-burn overlays (see `transitions.md` section 2b).

## 6. Tools in this folder
| Script | Purpose |
|---|---|
| `check_style.py` | lists `style.json` keys nothing reads |
| `verify_render.py` | per-frame alpha, safe-rect, edge, easing and text-in-plate check of a `.mov` |
| `grade/build_grade.py` | rebuilds `house-style.fcpreset` + `house-look.cube` + `calibration_report.json` from `grade.*` |
| `grade/measure_grade.py` | before/preset/LUT luma statistics on real frames through FilmCraft |
| `sfx/sfx_tool.py` (build, verify) | rebuilds / checks the SFX files against `audio.*` |

## 7. Bake loop
After every edit session: list owner changes -> map each to a `style.json` key or a doc -> show the diff -> on approval apply and add a dated `CHANGELOG.md` entry (why, before -> after) -> regenerate (`build_grade.py` if `grade.*` changed, `sfx_tool.py build` if `audio.*` changed) -> re-render every affected family in 16:9 and 9:16, run `verify_render.py` + `graphics_qa.py`, and look at the frames. Never change a value silently.
