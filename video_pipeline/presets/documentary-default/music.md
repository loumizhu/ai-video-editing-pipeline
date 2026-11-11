# Music Bed Pacing, Ducking & Licensing Guide

## 1. Editorial Vision & Music Philosophy
Music in Publora documentaries serves as emotional architecture rather than continuous sonic wallpaper. The score mirrors the dramatic structure of the script, building tension during investigative discoveries, settling into understated contemplation during historical reflections, and stepping aside during critical revelations.

---

## 2. Dynamic Ducking & Acoustic Level Rules (Source: `stages/08_assembly.md`)

### Loudness & Headroom Targets
- **Master Dialogue Stem (`A1`):** Integrated **-16.0 LUFS** (ITU-R BS.1770-4), True Peak capped strictly at **-1.8 dBTP** (ensuring final mix ceiling < -1.5 dBTP).
- **Archival Sync Soundbites (`A2`):** Normalized to **-16.0 LUFS**.
- **Music Bed Track (`A4`):**
  - **Ducked under Speech:** Ducked by **-24.0 dB** relative to dialogue.
  - **Ducked under Archival Clips:** Ducked by **-28.0 dB** relative to archival sync dialogue.
  - **Unducked Full Level (Transitions & Montages):** **-14.0 dB** to **-16.0 dBFS**.
  - **Attack Time:** `100 ms` (smooth, non-pumping onset).
  - **Release Time:** `600 ms` (gentle acoustic swell following spoken sentences).

### Two-Level Sidechain Compression Filtergraph (FFmpeg Recipe)
```bash
ffmpeg -y -i dialogue_norm.wav -i scored_clips.wav -i primary_bed.wav \
  -filter_complex "[0:a]asplit=2[key][d0]; [d0]pan=stereo|c0=c0|c1=c0[dlg]; \
    [2:a][key]sidechaincompress=threshold=0.0265:ratio=20:attack=100:release=600:makeup=1[bd1]; \
    [bd1][1:a]sidechaincompress=threshold=0.010:ratio=20:attack=100:release=600:makeup=1[md]; \
    [md]asplit=2[m_stem][m_mix]; \
    [dlg][1:a][m_mix]amix=inputs=3:duration=first:dropout_transition=0:normalize=0[mix_raw]" \
  -map "[m_stem]" ducked_bed.wav -map "[mix_raw]" mixed_audio.wav
```

### Native NLE Implementation
- **FilmCraft:** Ingest `primary_bed.wav` onto Track A4. Execute `essentialSound.generateDucking '{"clips": [<music_clip_ids>]}'`.
- **DaVinci Resolve (Fairlight):** Sidechain ducking configured via Fairlight Dynamics palette (Compressor sidechain source: Bus 1 / Dialogue).

---

## 3. Music Onset Alignment to Chapter Starts & Visual Cuts
- **The Audio-First Principle (J-Cut Bridge):** At chapter cards and major act shifts, the music cue must lead the visual transition. Swell the music bed **8 to 16 frames** (0.33s to 0.67s) BEFORE the chapter card (`chapter-card`) appears on Track V3.
- **Beat Snapping:** Major narrative cut points must snap to rhythmic downbeats or melodic phrase boundaries (using onset detection timestamps from `tools/music-onset.py`).
- **Silence as Punctuation:** Before a shocking revelation or turning point, cut the music bed abruptly **12 frames** before the line is spoken. Allow the revelation to hang in dry silence before re-introducing the score underneath.

---

## 4. Free Music Sources & Licensing Standards
Every music track utilized in this pipeline must be 100% free of licensing fees, royalty demands, and Content ID strike risks.

### Verified Free-License Providers
1. **Scott Buckley (https://scottbuckley.com.au/):**
   - License: Creative Commons Attribution 4.0 International (CC-BY 4.0).
   - Proven in Production: Scott Buckley's "Childhood" piano score was calibrated for Video 010.
   - Requirement: Verbatim attribution credit in video description.
2. **Musopen (https://musopen.org/):**
   - License: Public Domain (CC0) / CC-BY.
   - Repertoire: Classical orchestral recordings, solo piano, chamber music.
3. **Free Music Archive (FMA) (https://freemusicarchive.org/):**
   - License: Filter strictly by `CC-BY` or `CC0 Public Domain`.
4. **Incompetech / Kevin MacLeod (https://incompetech.com/):**
   - License: Creative Commons Attribution 4.0 (CC-BY 4.0).

### Asset Registry Mandate
No music file may be placed on the timeline without a corresponding entry in `03_media/asset_registry.json` recording:
```json
{
  "file": "primary_bed.wav",
  "track_name": "Childhood",
  "composer": "Scott Buckley",
  "license": "CC-BY 4.0",
  "license_url": "https://creativecommons.org/licenses/by/4.0/",
  "attribution_text": "\"Childhood\" by Scott Buckley (released under CC-BY 4.0) www.scottbuckley.com.au"
}
```
