# Sound Design & SFX Catalogue Guide

## 1. Role of sound design
SFX anchor abstract graphics (dates, numbers, quotes, maps) in physical reality. They never compete with the voiceover.
If an SFX transient collides with a voiceover consonant, duck the SFX by 4 dB or move its onset by 4 to 6 frames.

## 2. Loudness spec (single source: `style.json` `audio.*`; identical in `sfx.json` `loudness_spec`)
| Class | Files | Metric | Target | Tolerance |
|---|---|---|---|---|
| Event | 9 files (everything except room tone) | true peak, EBU R128 `peak=true`, dBTP | -9.0 dBTP | +/-1.5 dB (-10.5 .. -7.5) |
| Bed | `sfx_room_tone.wav` | integrated loudness, LUFS | -36.0 LUFS | +/-1.5 LU |

- Why peak for events: the events last 0.26 to 6.0 s and most of that is a 5 to 100 ms transient. Integrated LUFS of such a file is set by the silence around the transient: the shortest ones read -70 LUFS (below the 0.4 s ebur128 window) and the click-type ones need a limiter to reach -20 LUFS. The previous "-20 LUFS +/-3" spec could not be met without distorting them, and 6 of 10 files missed it (measured -24.1 to -29.4).
- Why -9.0 dBTP: the dialogue master ceiling is `audio.master_true_peak_max_dbtp` = -1.8 dBTP and dialogue sits at `audio.dialogue_target_lufs` = -16.0 LUFS; an event peak 5 dB or more under the master ceiling (`audio.sfx_vs_master_peak_margin_db` = 5.0) keeps it under VO peaks. The spec ceiling is -7.5 dBTP, which is 5.7 dB under -1.8.
- Integrated LUFS and momentary max are recorded in `sfx.json` for information. They are not gated.
- Fades: 5.0 ms in and out (`audio.fade_ms`); sample 0 is 0 in all files. Format 48 kHz, 16-bit PCM WAV, stereo (mono sources duplicated).
- Check: `python sfx\sfx_tool.py verify` re-measures every file with ffmpeg and exits 1 if any file is outside the spec, if sfx.json disagrees with style.json, or if a URL field is empty. Rebuild: `python sfx\sfx_tool.py build` (downloads from the URLs in sfx.json).

## 3. Track routing
- Timeline: Track A3 (`sfx`). Dialogue A1 at -16.0 LUFS. Music A4 ducked -24.0 dB under speech, -28.0 dB under archival sync (see `music.md`).

## 4. Catalogue (measured with `sfx_tool.py verify`)
| Role | File | Trigger | Paired visual | Spec | Measured (gated) | Integrated LUFS (info) | Length |
|---|---|---|---|---|---|---|---|
| `whoosh_soft` | `sfx/sfx_whoosh_soft.wav` | Smooth scene transition, soft card reveal | Cross Dissolve, Soft Wipe, Lower Third | true peak -9.0 +/-1.5 dBTP | **-9.0 dBTP** | -21.4 | 1.33 s |
| `whoosh_fast` | `sfx/sfx_whoosh_fast.wav` | High-velocity time jump, rapid montage | Whip, rapid zoom | true peak -9.0 +/-1.5 dBTP | **-9.0 dBTP** | -25.5 | 2.32 s |
| `sub_boom` | `sfx/sfx_sub_boom.wav` | Chapter milestone, act finale | Chapter Card, Dip to Black | true peak -9.0 +/-1.5 dBTP | **-9.0 dBTP** | -18.8 | 5.99 s |
| `paper_slide` | `sfx/sfx_paper_slide.wav` | Archival document reveal, photo-stack slide | Document plate, photo stack | true peak -9.0 +/-1.5 dBTP | **-9.0 dBTP** | -32.9 | 1.09 s |
| `paper_stamp` | `sfx/sfx_paper_stamp.wav` | Verified archival badge, fact confirmation | Verification seal, document stamp | true peak -9.0 +/-1.5 dBTP | **-9.0 dBTP** | -27.2 | 0.42 s |
| `map_pin` | `sfx/sfx_map_pin.wav` | Route waypoint or map marker | Map, location pin | true peak -9.0 +/-1.5 dBTP | **-9.0 dBTP** | -29.8 | 0.61 s |
| `typewriter_single` | `sfx/sfx_typewriter_single.wav` | Single metric or keyword | Keyword Pop | true peak -9.0 +/-1.5 dBTP | **-9.0 dBTP** | n/a (<0.4 s) | 0.22 s |
| `typewriter_clack` | `sfx/sfx_typewriter_clack.wav` | Attribution or secondary line reveal | Quote Pullout attribution | true peak -9.0 +/-1.5 dBTP | **-9.0 dBTP** | n/a (<0.4 s) | 0.33 s |
| `camera_shutter` | `sfx/sfx_camera_shutter.wav` | Introducing a historical still | Archival still, photo callout | true peak -9.0 +/-1.5 dBTP | **-9.0 dBTP** | n/a (<0.4 s) | 0.35 s |
| `room_tone` | `sfx/sfx_room_tone.wav` | Bridging audio gaps across archival cuts | J-cut / L-cut, scene silence | integrated -36.0 +/-1.5 LUFS | **-36.0 LUFS** (TP -15.9 dBTP) | -36.0 | 65.46 s |

*Deprecation notice (2026-11-03)*: `sfx_whoosh_soft.wav` and `sfx_whoosh_fast.wav` are deprecated in favour of the curated smooth whoosh library at `E:\((Video_Editing_Asset_Library))\(( Video Overlays & Effects Library ))\04_Sound_FX_Transitions\Smooth_Whooshes\` (see `CATALOG.md` there); retained for backwards compatibility until pipeline T4b wires the new library in.

Room tone note: the source recording is a school computer classroom. It contains faint background voices (the Commons description says "very few distinct words"). Use it only under dialogue, never alone in silence, and never under a scene where a listener could parse the voices.

## 5. Density caps
- At most 3 distinct SFX events per 60 s.
- No SFX on consecutive words or bullets.
- Pivotal reveal: no SFX and no music (silence).
