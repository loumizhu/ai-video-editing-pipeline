# shorts-vertical (1080 x 1920) - override preset

## 1. What is in this folder
| File | Role |
|---|---|
| `style.json` | overrides only (10 leaf keys) plus `"base_preset": "documentary-default"` |
| `build.py` | loads `style.json`, deep-merges it over `..\documentary-default\style.json` (`_common.load_style`), then calls the documentary `keyword-pop` builder with the merged style |
| `render.ps1` | the one command: values JSON -> ProRes 4444 alpha `.mov` + `.png` |
| `renders\` | `vertical_keyword_pop.mov` (80 frames), `.png` (t = 1.0 s), `composite_reference.png` (with the safe window drawn) |

Everything not overridden (colours, fonts, easing, slide, grade, audio, frame rate 23.976) is inherited. Only the **keyword-pop** family is built and proven vertical. The other three families would inherit their 16:9 layout constants (e.g. `chapter_card.center_y` 540, `quote_pullout.center_y` 540), so they need their own overrides before use; their builders do compute plate geometry from `canvas.*`, but nothing was rendered or verified at 1080 x 1920.

## 2. Overrides (all read by the builder; `python ..\documentary-default\check_style.py` -> "shorts-vertical ... unread: 0")
| Key | Documentary | Vertical |
|---|---|---|
| `canvas.width` / `height` | 1920 / 1080 | 1080 / 1920 |
| `canvas.safe_margin_x` | 160 | 90 |
| `canvas.safe_margin_top` / `bottom` | 100 / 100 | 300 / 470 |
| `typography.sizes.keyword_pop` | 100 | 120 |
| `layout.keyword_pop.center_x` / `center_y` | 960 / 500 | 540 / 875 |
| `layout.keyword_pop.in_frames` / `out_frames` | 12 / 10 | 10 / 10 |

## 3. Safe area (single definition)
Content window x 90..990, y 300..1450 (top 300 px clear of the search/header UI, bottom 470 px clear of handle/caption/audio UI, 90 px sides). `center_y` 875 is the centre of that window ((300 + 1450) / 2). The documentary rule of 45 px minimum font size applies unchanged.

## 4. Render and verify
```powershell
powershell -NoProfile -File render.ps1                      # default values: ..\documentary-default\keyword-pop\keyword-pop.json.example
powershell -NoProfile -File render.ps1 -Values my.json -Out D:\out\kw.mov
python ..\documentary-default\verify_render.py --mov renders\vertical_keyword_pop.mov --style style.json
python ..\..\..\tools\graphics_qa.py --input renders\vertical_keyword_pop.mov --width 1080 --height 1920
```
Do not run `..\documentary-default\keyword-pop\build.py --style .\style.json`: it does not merge `base_preset`. Use `build.py` in this folder (which `render.ps1` calls).

## 5. Measured result (frames of `renders\vertical_keyword_pop.mov`)
- `ffprobe`: 1080x1920, `yuva444p12le`, 80 frames.
- Alpha bbox over all 80 frames: x 349..731, y 817..931 (inside x 90..990, y 300..1450); no frame touches a canvas edge; 0 safe-rect violations.
- Rest frame (`.png`): bbox [361, 821, 719, 928], size 358 x 107 px, centre (540, 874.5).
- Overshoot: ink width per in-frame 210, 284, 334, 364, 379, 382 (peak, frame 7), 377, 369, 361, 358 (rest) = +6.7%.
- `graphics_qa.py` on `.mov` and `.png`: PASS (estimated cap height 66 px).
