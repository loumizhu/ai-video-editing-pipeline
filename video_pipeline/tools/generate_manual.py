"""Generate the comprehensive AUDIO_LIBRARY_EDITORIAL_MANUAL.md from AUDIO_CATALOG.json."""

import json
import os

LIBRARY_ROOT = r"E:\((Video_Editing_Asset_Library))\(( Production Audio Library ))"
CATALOG_PATH = os.path.join(LIBRARY_ROOT, "AUDIO_CATALOG.json")
MANUAL_PATH = r"E:\((_atWork_))\AI video editing pipeline\vcut_architecture\AUDIO_LIBRARY_EDITORIAL_MANUAL.md"
CENTRAL_MANUAL_PATH = os.path.join(r"E:\((Video_Editing_Asset_Library))", "AUDIO_LIBRARY_EDITORIAL_MANUAL.md")

cat = json.load(open(CATALOG_PATH, encoding="utf-8"))
music = cat["music"]
sfx = cat["sfx"]

lines = []
lines.append("# Central Production Audio Library: Editorial Manual & Zero-Copy Architecture")
lines.append("")
lines.append("Master repository: [`E:\\((Video_Editing_Asset_Library))\\(( Production Audio Library ))\\`](file:///E:/((Video_Editing_Asset_Library))/((%20Production%20Audio%20Library%20))/)")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 1. Executive Summary & House Audio Standards")
lines.append("")
lines.append("This centralized audio architecture provides **107 production-ready assets** (44 music master tracks across 8 narrative moods + 63 calibrated sound effects across 6 editorial categories) with zero redundant file copying across video essay projects.")
lines.append("")
lines.append("### Channel House Loudness Standards (YouTube Long-Form Editorial Recipe)")
lines.append("")
lines.append("| Track Layer | Delivery Target | Dynamics & Ducking Rules | Limiter Ceiling |")
lines.append("|---|---|---|---|")
lines.append("| **Voiceover / Dialogue (A1)** | **-16.0 LUFS** integrated | Speech-optimized compressor (2:1 to 3:1 ratio, fast attack 15ms, release 120ms) | **-1.0 dBTP** |")
lines.append("| **Soundbites & Quotes (A2)** | **-16.0 LUFS** integrated | Clean vocal matching; identical level to voiceover | **-1.0 dBTP** |")
lines.append("| **Sound Effects Events (A3)** | **-9.0 dBTP** true peak | Two-pass peak normalized with brickwall limiter; calibrated at 48 kHz | **-9.0 dBTP** |")
lines.append("| **Music Bed Open (A4)** | **-18.0 LUFS** integrated | Full energy during unvoiced scene setting, transitions, and story montages | **-1.0 dBTP** (via `alimiter`) |")
lines.append("| **Music Bed Ducked (A4)** | **-28.0 LUFS** integrated | Two-stage sidechain ducking (-10 dB reduction) triggered by voiceover (k1) and soundbites (k2); releases only on gaps $\\ge 1.5$s | **-1.0 dBTP** |")
lines.append("| **Room Tone & Beds (A5)** | **-36.0 LUFS** integrated | Continuous acoustic floor bed preventing dead digital silence between voiceover takes | **-1.0 dBTP** |")
lines.append("")
lines.append("> [!IMPORTANT]")
lines.append("> **House Recipe vs EBU R128**: Traditional broadcast EBU R128 specifies -23.0 LUFS integrated for television broadcast. For YouTube and digital streaming, modern standards target **-14 to -16 LUFS** for dialogue to prevent viewer volume cranking. Our house standard sets dialogue at -16.0 LUFS and ducks music to -28.0 LUFS, ensuring perfect vocal intelligibility while maintaining emotional narrative weight.")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 2. Zero-Copy Architecture (NTFS Hardlinks & Junctions)")
lines.append("")
lines.append("### The Problem")
lines.append("In traditional editing pipelines, each new video project folder copies 60-150 MB of audio files directly into `07_Video_Edit\\Full_Edit_v1\\music\\`. Across 30 video essay projects, this wastes gigabytes of high-speed SSD space.")
lines.append("")
lines.append("### The Solution: Zero-Copy NTFS Inodes")
lines.append("Windows NTFS supports directory junctions (`mklink /J`) and hardlinks (`os.link`) on the same volume (drive `E:\\`) without administrator privileges:")
lines.append("- **Zero Bytes Added**: A hardlinked track shares the exact Master File Table (MFT) inode (`st_ino`).")
lines.append("- **Master Write Protection**: All 107 master files in `E:\\((Video_Editing_Asset_Library))\\` are set to read-only (`attrib +R /S`). If an NLE or script attempts an in-place write, Windows forbids it, preventing corruption of the shared master.")
lines.append("- **Project Independence**: Removing a video project later simply decrements the NTFS hardlink counter without deleting the master audio file.")
lines.append("")
lines.append("### Safe Automation Tool: `audio_link_tool.py`")
lines.append("Located at: [`video_pipeline/tools/audio_link_tool.py`](file:///E:/((_atWork_))/AI%20video%20editing%20pipeline/video_pipeline/tools/audio_link_tool.py)")
lines.append("")
lines.append("```bash")
lines.append("# 1. Zero-copy link specific mood tracks or SFX to a video project:")
lines.append("python video_pipeline/tools/audio_link_tool.py link --project \"E:\\((_atWork_))\\Ytube_Channel\\Videos-Scripts\\21_Young_Anakin...\" --mood \"01_Melancholic_Reflective\"")
lines.append("")
lines.append("# 2. Link sound effects category into project sfx folder:")
lines.append("python video_pipeline/tools/audio_link_tool.py link --project \"E:\\((_atWork_))\\Ytube_Channel\\Videos-Scripts\\21_Young_Anakin...\" --sfx \"01_Transitional_Whooshes\"")
lines.append("")
lines.append("# 3. Deduplicate project audio (dry-run by default; safe byte verification):")
lines.append("python video_pipeline/tools/audio_link_tool.py deduplicate --root \"E:\\((_atWork_))\\Ytube_Channel\\Videos-Scripts\"")
lines.append("# Apply atomic hardlink replacement:")
lines.append("python video_pipeline/tools/audio_link_tool.py deduplicate --root \"E:\\((_atWork_))\\Ytube_Channel\\Videos-Scripts\" --apply")
lines.append("")
lines.append("# 4. Audit library integrity and verify 100% zero-copy inode synchronization:")
lines.append("python video_pipeline/tools/audio_link_tool.py audit")
lines.append("```")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 3. Production Music Taxonomy & Track Catalog (44 Tracks)")
lines.append("")
lines.append("Each mood directory in `01_Music\\` contains zero-copy NTFS hardlinks pointing directly to the master files in `01_Music\\All_Tracks\\`.")
lines.append("")

mood_names = [
    ("01_Melancholic_Reflective", "Quiet sorrow, emotional introspection, tragedy, loss of innocence"),
    ("02_Tension_Investigative_Suspense", "Legal battles, contract secrecy, forensic scrutiny, dark mystery"),
    ("03_Warm_Emotional_Hopeful", "Tender beginnings, emotional redemption, protective figures, warmth"),
    ("04_Nostalgic_Gentle_Memory", "Golden era Hollywood nostalgia, bittersweet vintage reminiscence"),
    ("05_Wholesome_Documentary_Pacing", "Neutral biographical exposition, steady narrative flow"),
    ("06_Dramatic_Climax_Triumph", "Breakthroughs, monumental revelations, dramatic crescendos"),
    ("07_Dark_Tragic_Downfall", "Menacing doom, heavy corruption, shocking downfall, grim reality"),
    ("08_Historical_Retrospective", "Sweeping period history, archival retrospectives, legacy"),
]

for m_key, m_desc in mood_names:
    lines.append(f"### {m_key.replace('_', ' ')}")
    lines.append(f"*{m_desc}*")
    lines.append("")
    lines.append("| Track Title | File | Dur | Loudness | Artist & License | Play / Open |")
    lines.append("|---|---|---|---|---|---|")
    for fn, d in sorted(music.items()):
        if m_key in d.get("moods", []):
            title = d.get("title", fn)
            dur = f"{int(d.get('duration_s', 0)//60)}m{int(d.get('duration_s', 0)%60):02d}s"
            lufs = f"{d.get('lufs_integrated')} LUFS"
            art = f"{d.get('artist')} ({d.get('license')})"
            full_path = f"E:\\((Video_Editing_Asset_Library))\\(( Production Audio Library ))\\{d['path']}"
            file_url = f"file:///{full_path.replace(chr(92), '/')}"
            lines.append(f"| **{title}** | `{fn}` | {dur} | {lufs} | {art} | [▶️ Play Track]({file_url}) |")
    lines.append("")

lines.append("### Envato & Commercial Cut-Down Families")
lines.append("To ensure accurate mood counts, timing variations and cut-downs of single compositional suites are documented as edit packages:")
lines.append("- **Epic Motivation Suite** (Luis Ruiz / Envato Elements): Full (2m20s), Short A (1m25s), Short B (1m05s), Short C (46s), Short D (28s).")
lines.append("- **The Inspiring Suite** (Luis Ruiz / Envato Elements): Full (2m23s), 1Min (60s), 30Sec (31s), 15Sec (15s).")
lines.append("- **Inspiring Voyage Suite** (Envato Elements): Full (2m19s), Short (1m36s), Teaser (51s).")
lines.append("- **Background Acoustic Suite** (Envato Elements): Full (2m10s), Medium (1m43s), Short (1m15s).")
lines.append("")
lines.append("> [!NOTE]")
lines.append("> **Licensing Notice**: Tracks licensed under Creative Commons Attribution 4.0 International (CC-BY 4.0) require crediting the composer and source (e.g. `Music: 'Cryptic Sorrow' by Kevin MacLeod (incompetech.com) - CC-BY 4.0`). Tracks from Envato Elements require registering the project URL/channel to clear YouTube Content ID matching.")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 4. Sound Effects (SFX) Taxonomy & Delivery Catalog (63 Assets)")
lines.append("")
lines.append("All event SFX are pre-normalized to **-9.0 dBTP** true peak at **48 kHz** with true peak limiting (`alimiter`), and Room Tone beds are calibrated to **-36.0 LUFS** integrated.")
lines.append("")

sfx_folders = [
    ("01_Transitional_Whooshes", "Whooshes, whips, and transitional risers calibrated for visual cuts and card turns"),
    ("02_Impacts_and_Booms", "Sub-bass hits, dramatic revelations, and cinematic booms for act breaks"),
    ("03_Editorial_UI_and_Graphics", "Typewriter clacks, paper slides, map pins, camera shutters, and vintage static"),
    ("04_Foley_and_Movement", "Footsteps, doors, tape rips, book rustles, and physical document handling"),
    ("05_Room_Tone_and_Beds", "Continuous acoustic floor beds calibrated to -36.0 LUFS to prevent digital silence"),
    ("06_Ambiences", "Atmospheric backgrounds including crowd applause and outdoor wind beds"),
]

for s_fld, s_desc in sfx_folders:
    lines.append(f"### {s_fld.replace('_', ' ')}")
    lines.append(f"*{s_desc}*")
    lines.append("")
    lines.append("| Sound Effect | File | Duration | True Peak | Loudness | 1-Click Preview |")
    lines.append("|---|---|---|---|---|---|")
    for fn, d in sorted(sfx.items()):
        if d.get("folder") == s_fld:
            dur = f"{d.get('duration_s', 0):.2f}s"
            tp = f"{d.get('true_peak_dbtp')} dBTP"
            lufs = f"{d.get('lufs_integrated')} LUFS" if d.get('lufs_integrated') is not None else "-"
            full_path = f"E:\\((Video_Editing_Asset_Library))\\(( Production Audio Library ))\\{d['path']}"
            file_url = f"file:///{full_path.replace(chr(92), '/')}"
            lines.append(f"| **{fn.rsplit('.', 1)[0].replace('_', ' ')}** | `{fn}` | {dur} | {tp} | {lufs} | [🔊 Play SFX]({file_url}) |")
    lines.append("")

content = "\n".join(lines)
open(MANUAL_PATH, "w", encoding="utf-8").write(content)
open(CENTRAL_MANUAL_PATH, "w", encoding="utf-8").write(content)
print(f"Generated {MANUAL_PATH} ({len(lines)} lines)")
print(f"Copied to {CENTRAL_MANUAL_PATH}")
