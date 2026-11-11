# Grade - style guide

> This is the **base look**. Since 2026-11-09 a video's colour script ([COLOR_SCRIPT.md](../../../COLOR_SCRIPT.md)) adds small per-phase offsets on top of it; `tools/color_script.py` writes those looks from this preset (`house-style.fcpreset` is the template) and measures each one through FilmCraft.

## 1. The look (numbers in `../style.json` `grade.*`, applied by FilmCraft Lumetri)
Subtle and photographic: blacks stay where the source has them (no lift, no crush), mild S-curve, soft highlight shoulder, a touch of warmth, light grain, faint vignette. A previous version (shadows +8, blacks -8, contrast +15) measured as a milky fade: p5 9.4 -> 49.9 on the bridge clip. That is gone.

| Param | Value | Effect measured on a gray ramp (FilmCraft output, 8-bit) |
|---|---|---|
| contrast | +10 | S about 128: -1 at levels 4..16, -2 at 32..64, 0 at 128, +2 at 192, +1 at 240 |
| highlights | -6 | 0 below level 64, -1 at 128, -2 at 192, -4 at 240, -5 at 255 |
| shadows | +2 | +2 at levels 4..16, +1 at 32..64, 0 from 128 (ratio gain on luma) |
| whites, blacks, exposure, tint | 0 | inert |
| saturation | 104 | no gray change; LUT-fitted factor 1.0373 about Rec.709 luma |
| temperature | +3 | R minus B = +1.97 levels at gray 128, no change in G |
| noise (grain) | amount 4.5, mono, size 1.0 | spatial; not in the LUT |
| vignette | amount -10, midpoint 70, feather 90, roundness 0 | corner about -9% luma, frame mean about -3% on mid gray; not in the LUT |

Previous vignette (-30 / 45 / 65) darkened the frame mean by 25 levels on flat mid gray (corner 90 vs 128); measured on the bright test frame it dropped the median 111.6 -> 83.3. It is replaced by the values above.

## 2. Files
- `house-style.fcpreset`: FilmCraft preset `HouseStyle_Documentary` (lumetri + noise + vignette), written by `build_grade.py` from `style.json`.
- `house-look.cube`: 3D LUT, `LUT_3D_SIZE 33`, 8 decimals, black corner (0.03, 0, 0.005)/255, same file for FilmCraft (`lumetri.setInputLut`) and Resolve (`item.SetLUT(1, path)`). Colour transform only.
- `calibration_report.json`: how the LUT was fitted and how well it matches.
- `build_grade.py`: the regeneration script. `python build_grade.py` rewrites the three files above (needs FilmCraft installed; takes about 4 s). `--no-calibrate` rewrites only the `.fcpreset`.
- `measure_grade.py`: before / preset / LUT statistics on real frames.

## 3. How the LUT stays float and in parity
FilmCraft's pipeline output is 8-bit (a gray ramp read back through EXR lands on integers), so sampling a LUT from renders would give 1/255 steps (the old cube had 38/255 = 0.149020 steps). `build_grade.py` instead:
1. writes the `.fcpreset` from the numbers;
2. pushes a 256-level gray ramp and 3,000 random colour patches through FilmCraft's own Lumetri (fresh `zz_test_grade_*` project, preset imported and applied in one `run`, EXR float readout) for three sub-presets: per-channel params (exposure, contrast, blacks, whites, temperature, tint), luma-ratio params (highlights, shadows), and everything including saturation;
3. fits smoothing splines to the ramps (noise sigma 0.29 levels), a luma-ratio gain, and the saturation scalar, picks the stage order by held-out error (result: highlights/shadows first, then per-channel), evaluates the model in float on the 33^3 grid.
Probe results that justify the structure: contrast, blacks, exposure, tint, temperature act per channel (per-channel model error 0.05-0.24 levels); highlights and shadows scale RGB by T(luma)/luma (luma-ratio error 0.16-0.21 vs per-channel 0.69-0.73); saturation 104 = luma-based 1.04 (error 0.25).
Validation on 3,000 held-out patches (all colours, including pure primaries): mean abs error 0.41 levels, p99 4.0, max 8.3 (max is on fully saturated primaries near clipping).

## 4. Measured on real footage (Video 010 archival frames; proof frames in `renders/` and `files/T3b_proofs/p3/grade/`)
Rec.709 luma of the 8-bit render. "preset" = full `.fcpreset` (lumetri + grain + vignette), "lumetri" = same preset without grain/vignette, "LUT" = `house-look.cube` through `lumetri.setInputLut`.

| Frame | | p5 | p50 | p95 | < 8/255 |
|---|---|:-:|:-:|:-:|:-:|
| Archival bridge | before | 9.50 | 35.34 | 168.51 | 2.48% |
| | preset | 8.56 | 34.30 | 165.39 | 4.24% |
| | lumetri | 10.34 | 35.10 | 168.90 | 1.56% |
| | LUT | 10.34 | 34.89 | 168.89 | 2.00% |
| Bright scene | before | 30.58 | 111.63 | 175.53 | 0.55% |
| | preset | 29.19 | 106.31 | 172.76 | 0.70% |
| | lumetri | 29.75 | 110.85 | 175.97 | 0.43% |
| | LUT | 29.73 | 110.86 | 175.97 | 0.45% |
| Dark scene | before | 3.72 | 17.20 | 30.28 | 18.70% |
| | preset | 4.16 | 16.85 | 32.19 | 16.98% |
| | lumetri | 5.29 | 17.20 | 30.25 | 16.58% |
| | LUT | 4.65 | 17.20 | 30.04 | 16.59% |

- Black point: p5 shift of the full preset is -0.94, -1.39, +0.44 levels (limit +/-3). No lift, no crush (share below 8/255 changes by +1.76, +0.15 and -1.72 points).
- LUT vs the Lumetri colour transform (mean absolute luma difference): **0.134, 0.129, 0.113 levels** (limit 2). This is the parity that matters for "same look in both NLEs".
- LUT vs the full preset: 3.12, 4.20, 2.56 levels. This does NOT meet a "< 2 levels" reading of parity and cannot: the difference is the grain and vignette, which are spatial effects a LUT cannot carry (with grain 0 the bright frame still differs by 3.1 from the vignette alone; with grain 0 the bridge frame differs by 1.45). In Resolve add grain and vignette separately (Fusion/OFX) if the full look is wanted.
- Remaining limitation: the fit is least accurate on fully saturated primaries (max 8.3 levels); natural footage shows 0.11-0.13.

## 5. Recipes
FilmCraft preset (same-`run` rule: `presets.apply` only works in the run that imported the preset):
```
{"id": "presets.import", "params": {"path": "E:/((_atWork_))/Ytube_Channel/Videos-Scripts/Video_Pipeline/presets/documentary-default/grade/house-style.fcpreset"}}
{"id": "presets.apply", "params": {"preset": "HouseStyle_Documentary", "clips": [<clip ids>]}}
```
Run with `filmcraft-cli --project p.fcproj --save run apply.jsonl` (`--save` keeps the applied effects; the preset name does not survive the run).
FilmCraft LUT: `filmcraft-cli --project p.fcproj --save exec lumetri.setInputLut '{"clip": <id>, "path": ".../grade/house-look.cube"}'`.
Resolve (DOCUMENTED-NOT-TESTED here; `SetLUT` is a real API call):
```python
for item in timeline.GetItemListInTrack("video", 1):
    item.SetLUT(1, r"E:\((_atWork_))\Ytube_Channel\Videos-Scripts\Video_Pipeline\presets\documentary-default\grade\house-look.cube")
```

## 6. After editing `grade.*`
`python build_grade.py`, then `python measure_grade.py --frames <3 frames> --out-dir <proof dir>` and check: p5 shift within +/-3 levels, LUT vs lumetri < 2 levels, `calibration_report.json` held-out mean < 1 level. Look at the strip (before / preset / cube) before approving.
