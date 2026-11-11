# SFX licences and provenance

Every file is downloaded from the URL in `source_url` (see `sfx.json`); `sfx_tool.py build` re-downloads and re-processes them. No synthesised or generated audio is included.

## Licence terms
- **Mixkit Sound Effects Free License**: terms page https://mixkit.co/license/ (section "Sound Effects Free License", anchor https://mixkit.co/license/#sfxFree). The full terms text is loaded in a pop-up that I could not retrieve automatically, so the "commercial use, no attribution" reading rests on Mixkit's published summary and is **not quoted verbatim here**. Read the pop-up once before the first monetised upload and keep a screenshot in the video folder.
- **Public domain (Wikimedia Commons)**: https://commons.wikimedia.org/wiki/File:Ambient_classroom_mono.ogg (author rcrossley, via PDSounds.org; Commons categories PD-author and PDsounds.org). No attribution required.

## Registry
| File | Source | Asset | Source URL (audio) | Page listing it | Licence |
|---|---|---|---|---|---|
| `sfx_whoosh_soft.wav` | Mixkit | 1492 (Air whoosh) | https://assets.mixkit.co/active_storage/sfx/1492/1492-preview.mp3 | https://mixkit.co/free-sound-effects/whoosh/ | Mixkit Sound Effects Free License |
| `sfx_whoosh_fast.wav` | Mixkit | 1489 (Fast blow whoosh) | https://assets.mixkit.co/active_storage/sfx/1489/1489-preview.mp3 | https://mixkit.co/free-sound-effects/whoosh/ | Mixkit Sound Effects Free License |
| `sfx_sub_boom.wav` | Mixkit | 2902 (Movie impact intro presentation) | https://assets.mixkit.co/active_storage/sfx/2902/2902-preview.mp3 | https://mixkit.co/free-sound-effects/boom/ | Mixkit Sound Effects Free License |
| `sfx_paper_slide.wav` | Mixkit | 1530 (Paper slide) | https://assets.mixkit.co/active_storage/sfx/1530/1530-preview.mp3 | https://mixkit.co/free-sound-effects/paper/ | Mixkit Sound Effects Free License |
| `sfx_paper_stamp.wav` | Mixkit | 2182 (Wood hard hit) | https://assets.mixkit.co/active_storage/sfx/2182/2182-preview.mp3 | https://mixkit.co/free-sound-effects/hit/ | Mixkit Sound Effects Free License |
| `sfx_map_pin.wav` | Mixkit | 1830 (Metal button push) | https://assets.mixkit.co/active_storage/sfx/1830/1830-preview.mp3 | https://mixkit.co/free-sound-effects/button/ | Mixkit Sound Effects Free License |
| `sfx_typewriter_single.wav` | Mixkit | 1125 (Typewriter soft click) | https://assets.mixkit.co/active_storage/sfx/1125/1125-preview.mp3 | https://mixkit.co/free-sound-effects/typewriter/ | Mixkit Sound Effects Free License |
| `sfx_typewriter_clack.wav` | Mixkit | 1119 (Hard typewriter click) | https://assets.mixkit.co/active_storage/sfx/1119/1119-preview.mp3 | https://mixkit.co/free-sound-effects/typewriter/ | Mixkit Sound Effects Free License |
| `sfx_camera_shutter.wav` | Mixkit | 1133 (Camera shutter click) | https://assets.mixkit.co/active_storage/sfx/1133/1133-preview.mp3 | https://mixkit.co/free-sound-effects/camera/ | Mixkit Sound Effects Free License |
| `sfx_room_tone.wav` | Wikimedia Commons | File:Ambient_classroom_mono.ogg (Ambient classroom mono) | https://upload.wikimedia.org/wikipedia/commons/1/10/Ambient_classroom_mono.ogg | https://commons.wikimedia.org/wiki/File:Ambient_classroom_mono.ogg | Public domain (Wikimedia Commons: PD-author / PDSounds.org) |

## Changes from the previous version
- `sfx_paper_stamp.wav` and `sfx_map_pin.wav` were derived from Kenney packs (`impactWood_heavy_000`, `click1`). The pack pages exist and are CC0, but I could not download the packs to confirm the file names, so both files were replaced with Mixkit assets 2182 and 1830, which are listed on the category pages cited above.
- All files were re-processed: 5 ms fades, true-peak normalised to -9.0 dBTP (room tone: -36.0 LUFS integrated). Previous measured loudness is not carried over.
- The Mixkit audio is taken from the preview MP3 URL that the player on each listing page uses (`assets.mixkit.co/active_storage/sfx/<id>/<id>-preview.mp3`, HTTP 200 checked 2026-11-01) and decoded to 48 kHz WAV. I did not compare it with the site's download-button file, so the encoding quality of that file is unverified.

## Known issue
`sfx_room_tone.wav` has faint background voices in the recording. See `sfx.md` section 4.
