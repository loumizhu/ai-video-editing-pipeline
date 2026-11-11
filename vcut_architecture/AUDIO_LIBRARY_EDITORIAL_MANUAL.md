# Central Production Audio Library: Editorial Manual & Zero-Copy Architecture

Master repository: [`E:\((Video_Editing_Asset_Library))\(( Production Audio Library ))\`](file:///E:/((Video_Editing_Asset_Library))/((%20Production%20Audio%20Library%20))/)

---

## 1. Executive Summary & House Audio Standards

This centralized audio architecture provides **107 production-ready assets** (44 music master tracks across 8 narrative moods + 63 calibrated sound effects across 6 editorial categories) with zero redundant file copying across video essay projects.

### Channel House Loudness Standards (YouTube Long-Form Editorial Recipe)

| Track Layer | Delivery Target | Dynamics & Ducking Rules | Limiter Ceiling |
|---|---|---|---|
| **Voiceover / Dialogue (A1)** | **-16.0 LUFS** integrated | Speech-optimized compressor (2:1 to 3:1 ratio, fast attack 15ms, release 120ms) | **-1.0 dBTP** |
| **Soundbites & Quotes (A2)** | **-16.0 LUFS** integrated | Clean vocal matching; identical level to voiceover | **-1.0 dBTP** |
| **Sound Effects Events (A3)** | **-9.0 dBTP** true peak | Two-pass peak normalized with brickwall limiter; calibrated at 48 kHz | **-9.0 dBTP** |
| **Music Bed Open (A4)** | **-18.0 LUFS** integrated | Full energy during unvoiced scene setting, transitions, and story montages | **-1.0 dBTP** (via `alimiter`) |
| **Music Bed Ducked (A4)** | **-28.0 LUFS** integrated | Two-stage sidechain ducking (-10 dB reduction) triggered by voiceover (k1) and soundbites (k2); releases only on gaps $\ge 1.5$s | **-1.0 dBTP** |
| **Room Tone & Beds (A5)** | **-36.0 LUFS** integrated | Continuous acoustic floor bed preventing dead digital silence between voiceover takes | **-1.0 dBTP** |

> [!IMPORTANT]
> **House Recipe vs EBU R128**: Traditional broadcast EBU R128 specifies -23.0 LUFS integrated for television broadcast. For YouTube and digital streaming, modern standards target **-14 to -16 LUFS** for dialogue to prevent viewer volume cranking. Our house standard sets dialogue at -16.0 LUFS and ducks music to -28.0 LUFS, ensuring perfect vocal intelligibility while maintaining emotional narrative weight.

---

## 2. Zero-Copy Architecture (NTFS Hardlinks & Junctions)

### The Problem
In traditional editing pipelines, each new video project folder copies 60-150 MB of audio files directly into `07_Video_Edit\Full_Edit_v1\music\`. Across 30 video essay projects, this wastes gigabytes of high-speed SSD space.

### The Solution: Zero-Copy NTFS Inodes
Windows NTFS supports directory junctions (`mklink /J`) and hardlinks (`os.link`) on the same volume (drive `E:\`) without administrator privileges:
- **Zero Bytes Added**: A hardlinked track shares the exact Master File Table (MFT) inode (`st_ino`).
- **Master Write Protection**: All 107 master files in `E:\((Video_Editing_Asset_Library))\` are set to read-only (`attrib +R /S`). If an NLE or script attempts an in-place write, Windows forbids it, preventing corruption of the shared master.
- **Project Independence**: Removing a video project later simply decrements the NTFS hardlink counter without deleting the master audio file.

### Safe Automation Tool: `audio_link_tool.py`
Located at: [`video_pipeline/tools/audio_link_tool.py`](file:///E:/((_atWork_))/AI%20video%20editing%20pipeline/video_pipeline/tools/audio_link_tool.py)

```bash
# 1. Zero-copy link specific mood tracks or SFX to a video project:
python video_pipeline/tools/audio_link_tool.py link --project "E:\((_atWork_))\Ytube_Channel\Videos-Scripts\21_Young_Anakin..." --mood "01_Melancholic_Reflective"

# 2. Link sound effects category into project sfx folder:
python video_pipeline/tools/audio_link_tool.py link --project "E:\((_atWork_))\Ytube_Channel\Videos-Scripts\21_Young_Anakin..." --sfx "01_Transitional_Whooshes"

# 3. Deduplicate project audio (dry-run by default; safe byte verification):
python video_pipeline/tools/audio_link_tool.py deduplicate --root "E:\((_atWork_))\Ytube_Channel\Videos-Scripts"
# Apply atomic hardlink replacement:
python video_pipeline/tools/audio_link_tool.py deduplicate --root "E:\((_atWork_))\Ytube_Channel\Videos-Scripts" --apply

# 4. Audit library integrity and verify 100% zero-copy inode synchronization:
python video_pipeline/tools/audio_link_tool.py audit
```

---

## 3. Production Music Taxonomy & Track Catalog (44 Tracks)

Each mood directory in `01_Music\` contains zero-copy NTFS hardlinks pointing directly to the master files in `01_Music\All_Tracks\`.

### 01 Melancholic Reflective
*Quiet sorrow, emotional introspection, tragedy, loss of innocence*

| Track Title | File | Dur | Loudness | Artist & License | Play / Open |
|---|---|---|---|---|---|
| **Anguish** | `Anguish.mp3` | 3m59s | -22.4 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Anguish.mp3) |
| **Bittersweet** | `Bittersweet.mp3` | 3m22s | -16.3 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Bittersweet.mp3) |
| **Loss** | `Loss.mp3` | 2m13s | -33.1 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Loss.mp3) |
| **Private Reflection** | `Private_Reflection.mp3` | 1m30s | -16.7 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Private_Reflection.mp3) |
| **Touching Moments Two - Higher** | `Touching_Moments_Two_-_Higher.mp3` | 2m54s | -28.1 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Touching_Moments_Two_-_Higher.mp3) |

### 02 Tension Investigative Suspense
*Legal battles, contract secrecy, forensic scrutiny, dark mystery*

| Track Title | File | Dur | Loudness | Artist & License | Play / Open |
|---|---|---|---|---|---|
| **Awkward Meeting** | `Awkward_Meeting.mp3` | 1m24s | -24.3 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Awkward_Meeting.mp3) |
| **Comfortable Mystery** | `Comfortable_Mystery.mp3` | 3m56s | -31.3 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Comfortable_Mystery.mp3) |
| **Long Note One** | `Long_Note_One.mp3` | 7m20s | -19.7 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Long_Note_One.mp3) |
| **Long Note Three** | `Long_Note_Three.mp3` | 3m12s | -24.4 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Long_Note_Three.mp3) |
| **Long Note Two** | `Long_Note_Two.mp3` | 7m42s | -25.6 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Long_Note_Two.mp3) |
| **Mesmerize** | `Mesmerize.mp3` | 7m04s | -28.9 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Mesmerize.mp3) |
| **Past the Edge** | `Past_the_Edge.mp3` | 1m18s | -36.5 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Past_the_Edge.mp3) |

### 03 Warm Emotional Hopeful
*Tender beginnings, emotional redemption, protective figures, warmth*

| Track Title | File | Dur | Loudness | Artist & License | Play / Open |
|---|---|---|---|---|---|
| **Background Acoustic (Full 2:10)** | `Background_Acoustic_Full.mp3` | 2m10s | -7.9 LUFS | Envato / Production Library (Envato Elements Commercial) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Background_Acoustic_Full.mp3) |
| **Clean Soul** | `Clean_Soul.mp3` | 5m06s | -25.6 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Clean_Soul.mp3) |
| **Clear Waters** | `Clear_Waters.mp3` | 2m08s | -27.3 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Clear_Waters.mp3) |
| **Heartwarming** | `Heartwarming.mp3` | 1m12s | -17.9 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Heartwarming.mp3) |
| **Lasting Hope** | `Lasting_Hope.mp3` | 2m23s | -17.0 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Lasting_Hope.mp3) |
| **Emotional Cinematic String Bed** | `MUSCStr_Emotional_cinematic_Loop.mp3` | 0m30s | -11.8 LUFS | ElevenLabs AI / House Curated (Owned Commercial Royalty Free) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/MUSCStr_Emotional_cinematic_Loop.mp3) |

### 04 Nostalgic Gentle Memory
*Golden era Hollywood nostalgia, bittersweet vintage reminiscence*

| Track Title | File | Dur | Loudness | Artist & License | Play / Open |
|---|---|---|---|---|---|
| **Dreamy Flashback** | `Dreamy_Flashback.mp3` | 2m06s | -15.4 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Dreamy_Flashback.mp3) |
| **Echoes of Time** | `Echoes_of_Time.mp3` | 4m45s | -15.4 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Echoes_of_Time.mp3) |
| **Gymnopedie No 1** | `Gymnopedie_No_1.mp3` | 3m07s | -20.0 LUFS | Kevin MacLeod (Erik Satie) (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Gymnopedie_No_1.mp3) |

### 05 Wholesome Documentary Pacing
*Neutral biographical exposition, steady narrative flow*

| Track Title | File | Dur | Loudness | Artist & License | Play / Open |
|---|---|---|---|---|---|
| **Clean Soul** | `Clean_Soul.mp3` | 5m06s | -25.6 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Clean_Soul.mp3) |
| **Clear Waters** | `Clear_Waters.mp3` | 2m08s | -27.3 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Clear_Waters.mp3) |
| **Wholesome** | `Wholesome.mp3` | 6m03s | -16.5 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Wholesome.mp3) |

### 06 Dramatic Climax Triumph
*Breakthroughs, monumental revelations, dramatic crescendos*

| Track Title | File | Dur | Loudness | Artist & License | Play / Open |
|---|---|---|---|---|---|
| **Despair and Triumph** | `Despair_and_Triumph.mp3` | 4m45s | -24.0 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Despair_and_Triumph.mp3) |
| **Epic Motivation (Full Orchestral)** | `Epic_Motivation_Full.mp3` | 2m20s | -8.9 LUFS | Envato / Production Library (Envato Elements Commercial) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Epic_Motivation_Full.mp3) |
| **Epic Motivation (Short A)** | `Epic_Motivation_Short_A.mp3` | 1m25s | -9.2 LUFS | Envato / Production Library (Envato Elements Commercial) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Epic_Motivation_Short_A.mp3) |
| **Epic Motivation (Short B)** | `Epic_Motivation_Short_B.mp3` | 1m04s | -8.7 LUFS | Production Library / Luis Ruiz (Envato Elements Commercial) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Epic_Motivation_Short_B.mp3) |
| **Epic Motivation (Short C)** | `Epic_Motivation_Short_C.mp3` | 0m46s | -8.2 LUFS | Production Library / Luis Ruiz (Envato Elements Commercial) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Epic_Motivation_Short_C.mp3) |
| **Epic Motivation (Short D)** | `Epic_Motivation_Short_D.mp3` | 0m28s | -8.4 LUFS | Production Library / Luis Ruiz (Envato Elements Commercial) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Epic_Motivation_Short_D.mp3) |
| **Inspiring Voyage (Full)** | `Inspiring_Voyage_Full.mp3` | 2m18s | -9.5 LUFS | Envato / Production Library (Envato Elements Commercial) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Inspiring_Voyage_Full.mp3) |
| **Inspiring Voyage (Short)** | `Inspiring_Voyage_Short.mp3` | 1m36s | -9.5 LUFS | Envato / Production Library (Envato Elements Commercial) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Inspiring_Voyage_Short.mp3) |
| **Inspiring Voyage (Teaser 30s)** | `Inspiring_Voyage_Teaser.mp3` | 0m50s | -7.7 LUFS | Production Library / Luis Ruiz (Envato Elements Commercial) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Inspiring_Voyage_Teaser.mp3) |
| **Sovereign** | `Sovereign.mp3` | 6m11s | -27.9 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Sovereign.mp3) |
| **The Inspiring (15 Sec Stinger)** | `The_Inspiring_15Sec.mp3` | 0m15s | -8.3 LUFS | Production Library / Luis Ruiz (Envato Elements Commercial) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/The_Inspiring_15Sec.mp3) |
| **The Inspiring (1 Min Edit)** | `The_Inspiring_1Min.mp3` | 1m00s | -11.0 LUFS | Envato / Production Library (Envato Elements Commercial) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/The_Inspiring_1Min.mp3) |
| **The Inspiring (30 Sec Stinger)** | `The_Inspiring_30Sec.mp3` | 0m30s | -8.3 LUFS | Production Library / Luis Ruiz (Envato Elements Commercial) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/The_Inspiring_30Sec.mp3) |
| **The Inspiring (Full)** | `The_Inspiring_Full.mp3` | 2m22s | -10.5 LUFS | Envato / Production Library (Envato Elements Commercial) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/The_Inspiring_Full.mp3) |

### 07 Dark Tragic Downfall
*Menacing doom, heavy corruption, shocking downfall, grim reality*

| Track Title | File | Dur | Loudness | Artist & License | Play / Open |
|---|---|---|---|---|---|
| **Cryptic Sorrow** | `Cryptic_Sorrow.mp3` | 5m36s | -27.6 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Cryptic_Sorrow.mp3) |
| **Darkest Child** | `Darkest_Child.mp3` | 3m58s | -12.6 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Darkest_Child.mp3) |
| **Failing Defense** | `Failing_Defense.mp3` | 1m45s | -12.9 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Failing_Defense.mp3) |
| **Grave Blow** | `Grave_Blow.mp3` | 1m42s | -20.9 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Grave_Blow.mp3) |
| **Sad Trio** | `Sad_Trio.mp3` | 4m11s | -36.4 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Sad_Trio.mp3) |

### 08 Historical Retrospective
*Sweeping period history, archival retrospectives, legacy*

| Track Title | File | Dur | Loudness | Artist & License | Play / Open |
|---|---|---|---|---|---|
| **Echoes of Time** | `Echoes_of_Time.mp3` | 4m45s | -15.4 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Echoes_of_Time.mp3) |
| **Gymnopedie No 1** | `Gymnopedie_No_1.mp3` | 3m07s | -20.0 LUFS | Kevin MacLeod (Erik Satie) (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Gymnopedie_No_1.mp3) |
| **Private Reflection** | `Private_Reflection.mp3` | 1m30s | -16.7 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Private_Reflection.mp3) |
| **Sovereign** | `Sovereign.mp3` | 6m11s | -27.9 LUFS | Kevin MacLeod (CC BY 4.0) | [▶️ Play Track](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/01_Music/All_Tracks/Sovereign.mp3) |

### Envato & Commercial Cut-Down Families
To ensure accurate mood counts, timing variations and cut-downs of single compositional suites are documented as edit packages:
- **Epic Motivation Suite** (Luis Ruiz / Envato Elements): Full (2m20s), Short A (1m25s), Short B (1m05s), Short C (46s), Short D (28s).
- **The Inspiring Suite** (Luis Ruiz / Envato Elements): Full (2m23s), 1Min (60s), 30Sec (31s), 15Sec (15s).
- **Inspiring Voyage Suite** (Envato Elements): Full (2m19s), Short (1m36s), Teaser (51s).
- **Background Acoustic Suite** (Envato Elements): Full (2m10s), Medium (1m43s), Short (1m15s).

> [!NOTE]
> **Licensing Notice**: Tracks licensed under Creative Commons Attribution 4.0 International (CC-BY 4.0) require crediting the composer and source (e.g. `Music: 'Cryptic Sorrow' by Kevin MacLeod (incompetech.com) - CC-BY 4.0`). Tracks from Envato Elements require registering the project URL/channel to clear YouTube Content ID matching.

---

## 4. Sound Effects (SFX) Taxonomy & Delivery Catalog (63 Assets)

All event SFX are pre-normalized to **-9.0 dBTP** true peak at **48 kHz** with true peak limiting (`alimiter`), and Room Tone beds are calibrated to **-36.0 LUFS** integrated.

### 01 Transitional Whooshes
*Whooshes, whips, and transitional risers calibrated for visual cuts and card turns*

| Sound Effect | File | Duration | True Peak | Loudness | 1-Click Preview |
|---|---|---|---|---|---|
| **riser whoosh transition** | `riser_whoosh_transition.mp3` | 2.00s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/01_Transitional_Whooshes/riser_whoosh_transition.mp3) |
| **sfx whoosh fast** | `sfx_whoosh_fast.wav` | 2.32s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/01_Transitional_Whooshes/sfx_whoosh_fast.wav) |
| **sfx whoosh soft** | `sfx_whoosh_soft.wav` | 1.33s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/01_Transitional_Whooshes/sfx_whoosh_soft.wav) |
| **swoosh high energy 01** | `swoosh_high_energy_01.wav` | 1.00s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/01_Transitional_Whooshes/swoosh_high_energy_01.wav) |
| **swoosh high energy 02** | `swoosh_high_energy_02.wav` | 1.22s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/01_Transitional_Whooshes/swoosh_high_energy_02.wav) |
| **whoosh cinematic zoom** | `whoosh_cinematic_zoom.mp3` | 1.00s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/01_Transitional_Whooshes/whoosh_cinematic_zoom.mp3) |
| **whoosh clean air 01** | `whoosh_clean_air_01.mp3` | 1.83s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/01_Transitional_Whooshes/whoosh_clean_air_01.mp3) |
| **whoosh clean air 02** | `whoosh_clean_air_02.mp3` | 0.91s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/01_Transitional_Whooshes/whoosh_clean_air_02.mp3) |
| **whoosh diaporama slide** | `whoosh_diaporama_slide.wav` | 1.16s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/01_Transitional_Whooshes/whoosh_diaporama_slide.wav) |
| **whoosh micro 0.3s** | `whoosh_micro_0.3s.mp3` | 0.35s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/01_Transitional_Whooshes/whoosh_micro_0.3s.mp3) |
| **whoosh soft ambient** | `whoosh_soft_ambient.mp3` | 2.00s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/01_Transitional_Whooshes/whoosh_soft_ambient.mp3) |
| **whoosh sparkler fast** | `whoosh_sparkler_fast.wav` | 40.18s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/01_Transitional_Whooshes/whoosh_sparkler_fast.wav) |

### 02 Impacts and Booms
*Sub-bass hits, dramatic revelations, and cinematic booms for act breaks*

| Sound Effect | File | Duration | True Peak | Loudness | 1-Click Preview |
|---|---|---|---|---|---|
| **impact car body dent** | `impact_car_body_dent.wav` | 25.48s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/02_Impacts_and_Booms/impact_car_body_dent.wav) |
| **impact cinematic bass thud** | `impact_cinematic_bass_thud.mp3` | 2.00s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/02_Impacts_and_Booms/impact_cinematic_bass_thud.mp3) |
| **impact dramatic intro doom** | `impact_dramatic_intro_doom.mp3` | 2.00s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/02_Impacts_and_Booms/impact_dramatic_intro_doom.mp3) |
| **impact metal decay** | `impact_metal_decay.wav` | 1.39s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/02_Impacts_and_Booms/impact_metal_decay.wav) |
| **impact metallic thud** | `impact_metallic_thud.wav` | 1.44s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/02_Impacts_and_Booms/impact_metallic_thud.wav) |
| **impact thunk on wood** | `impact_thunk_on_wood.wav` | 2.14s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/02_Impacts_and_Booms/impact_thunk_on_wood.wav) |
| **impact trailer big powerful** | `impact_trailer_big_powerful.mp3` | 6.79s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/02_Impacts_and_Booms/impact_trailer_big_powerful.mp3) |
| **impact ultra shock revelation** | `impact_ultra_shock_revelation.mp3` | 4.00s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/02_Impacts_and_Booms/impact_ultra_shock_revelation.mp3) |
| **impact wood slam wobble** | `impact_wood_slam_wobble.wav` | 1.65s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/02_Impacts_and_Booms/impact_wood_slam_wobble.wav) |
| **sfx sub boom** | `sfx_sub_boom.wav` | 5.99s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/02_Impacts_and_Booms/sfx_sub_boom.wav) |

### 03 Editorial UI and Graphics
*Typewriter clacks, paper slides, map pins, camera shutters, and vintage static*

| Sound Effect | File | Duration | True Peak | Loudness | 1-Click Preview |
|---|---|---|---|---|---|
| **sfx camera shutter** | `sfx_camera_shutter.wav` | 0.35s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/03_Editorial_UI_and_Graphics/sfx_camera_shutter.wav) |
| **sfx map pin** | `sfx_map_pin.wav` | 0.61s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/03_Editorial_UI_and_Graphics/sfx_map_pin.wav) |
| **sfx paper slide** | `sfx_paper_slide.wav` | 1.09s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/03_Editorial_UI_and_Graphics/sfx_paper_slide.wav) |
| **sfx paper stamp** | `sfx_paper_stamp.wav` | 0.42s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/03_Editorial_UI_and_Graphics/sfx_paper_stamp.wav) |
| **sfx typewriter clack** | `sfx_typewriter_clack.wav` | 0.33s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/03_Editorial_UI_and_Graphics/sfx_typewriter_clack.wav) |
| **sfx typewriter single** | `sfx_typewriter_single.wav` | 0.22s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/03_Editorial_UI_and_Graphics/sfx_typewriter_single.wav) |
| **ui arrows sweetener** | `ui_arrows_sweetener.wav` | 1.26s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/03_Editorial_UI_and_Graphics/ui_arrows_sweetener.wav) |
| **ui click soft** | `ui_click_soft.wav` | 0.04s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/03_Editorial_UI_and_Graphics/ui_click_soft.wav) |
| **ui soft foley swipe** | `ui_soft_foley_swipe.wav` | 3.14s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/03_Editorial_UI_and_Graphics/ui_soft_foley_swipe.wav) |
| **ui subscribe bell** | `ui_subscribe_bell.wav` | 0.70s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/03_Editorial_UI_and_Graphics/ui_subscribe_bell.wav) |

### 04 Foley and Movement
*Footsteps, doors, tape rips, book rustles, and physical document handling*

| Sound Effect | File | Duration | True Peak | Loudness | 1-Click Preview |
|---|---|---|---|---|---|
| **foley bag rummage** | `foley_bag_rummage.wav` | 17.02s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_bag_rummage.wav) |
| **foley bag unzipped** | `foley_bag_unzipped.wav` | 0.58s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_bag_unzipped.wav) |
| **foley book grab shelf** | `foley_book_grab_shelf.wav` | 2.95s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_book_grab_shelf.wav) |
| **foley book pages flutter** | `foley_book_pages_flutter.wav` | 16.57s | -8.8 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_book_pages_flutter.wav) |
| **foley book pages quickly** | `foley_book_pages_quickly.wav` | 20.31s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_book_pages_quickly.wav) |
| **foley boots on wood** | `foley_boots_on_wood.wav` | 26.98s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_boots_on_wood.wav) |
| **foley brass shell drop** | `foley_brass_shell_drop.wav` | 0.67s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_brass_shell_drop.wav) |
| **foley car door close** | `foley_car_door_close.wav` | 3.37s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_car_door_close.wav) |
| **foley computer keyboard** | `foley_computer_keyboard.wav` | 9.76s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_computer_keyboard.wav) |
| **foley folder papers** | `foley_folder_papers.wav` | 5.05s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_folder_papers.wav) |
| **foley footsteps concrete city** | `foley_footsteps_concrete_city.wav` | 86.61s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_footsteps_concrete_city.wav) |
| **foley glass bottle grab** | `foley_glass_bottle_grab.wav` | 3.16s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_glass_bottle_grab.wav) |
| **foley heartbeat stethoscope** | `foley_heartbeat_stethoscope.wav` | 4.74s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_heartbeat_stethoscope.wav) |
| **foley interior door** | `foley_interior_door.wav` | 15.09s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_interior_door.wav) |
| **foley shoveling dirt** | `foley_shoveling_dirt.wav` | 10.15s | -8.8 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_shoveling_dirt.wav) |
| **foley small objects table** | `foley_small_objects_table.wav` | 3.99s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_small_objects_table.wav) |
| **foley soda can open** | `foley_soda_can_open.wav` | 11.10s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_soda_can_open.wav) |
| **foley tape rip** | `foley_tape_rip.wav` | 2.91s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_tape_rip.wav) |
| **foley tearing paper** | `foley_tearing_paper.wav` | 0.90s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_tearing_paper.wav) |
| **foley toolbox rummage** | `foley_toolbox_rummage.wav` | 6.24s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_toolbox_rummage.wav) |
| **foley window blinds open** | `foley_window_blinds_open.wav` | 4.61s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_window_blinds_open.wav) |
| **foley wood chair creak** | `foley_wood_chair_creak.wav` | 16.38s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_wood_chair_creak.wav) |
| **foley wood floor creaks** | `foley_wood_floor_creaks.wav` | 46.26s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_wood_floor_creaks.wav) |
| **foley writing in notebook** | `foley_writing_in_notebook.wav` | 5.83s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_writing_in_notebook.wav) |
| **foley zippo lighter open** | `foley_zippo_lighter_open.wav` | 2.31s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/04_Foley_and_Movement/foley_zippo_lighter_open.wav) |

### 05 Room Tone and Beds
*Continuous acoustic floor beds calibrated to -36.0 LUFS to prevent digital silence*

| Sound Effect | File | Duration | True Peak | Loudness | 1-Click Preview |
|---|---|---|---|---|---|
| **room tone neutral long** | `room_tone_neutral_long.wav` | 150.18s | -17.4 dBTP | -36.0 LUFS | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/05_Room_Tone_and_Beds/room_tone_neutral_long.wav) |
| **room tone office archive** | `room_tone_office_archive.wav` | 128.88s | -8.8 dBTP | -36.0 LUFS | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/05_Room_Tone_and_Beds/room_tone_office_archive.wav) |
| **room tone public library** | `room_tone_public_library.wav` | 216.06s | -1.3 dBTP | -36.0 LUFS | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/05_Room_Tone_and_Beds/room_tone_public_library.wav) |
| **sfx room tone** | `sfx_room_tone.wav` | 65.46s | -15.9 dBTP | -36.0 LUFS | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/05_Room_Tone_and_Beds/sfx_room_tone.wav) |

### 06 Ambiences
*Atmospheric backgrounds including crowd applause and outdoor wind beds*

| Sound Effect | File | Duration | True Peak | Loudness | 1-Click Preview |
|---|---|---|---|---|---|
| **ambience wind leaves** | `ambience_wind_leaves.wav` | 8.96s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/06_Ambiences/ambience_wind_leaves.wav) |
| **sfx crowd applause theater** | `sfx_crowd_applause_theater.wav` | 5.04s | -9.0 dBTP | - | [🔊 Play SFX](file:///E:/((Video_Editing_Asset_Library))/(( Production Audio Library ))/02_SFX/06_Ambiences/sfx_crowd_applause_theater.wav) |
