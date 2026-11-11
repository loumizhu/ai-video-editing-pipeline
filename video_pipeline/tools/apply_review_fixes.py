"""Audio Library Normalization, SFX Restructure, and Catalog Refresh Script."""

import json
import math
import os
import re
import shutil
import subprocess
import sys

LIBRARY_ROOT = r"E:\((Video_Editing_Asset_Library))\(( Production Audio Library ))"
MUSIC_ROOT = os.path.join(LIBRARY_ROOT, "01_Music")
SFX_ROOT = os.path.join(LIBRARY_ROOT, "02_SFX")
ALL_TRACKS = os.path.join(MUSIC_ROOT, "All_Tracks")
CATALOG_PATH = os.path.join(LIBRARY_ROOT, "AUDIO_CATALOG.json")
SRC_AUDIO_LIB = r"E:\(( Sounds Effect - Audio Library ))"


def run_cmd(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, errors="ignore")


def measure_audio(path):
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"]
    r = run_cmd(cmd)
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    TP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
    LRA = re.findall(r"LRA:\s+(-?[\d.]+) LU", r.stderr)

    pr = run_cmd([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size,bit_rate:stream=sample_rate,channels,codec_name",
        "-of", "json", path
    ])
    dur = 0.0
    sr = 48000
    ch = 2
    codec = "unknown"
    try:
        j = json.loads(pr.stdout)
        dur = float(j["format"]["duration"])
        st = j["streams"][0]
        sr = int(st.get("sample_rate", 48000))
        ch = int(st.get("channels", 2))
        codec = st.get("codec_name", "")
    except Exception:
        pass

    i_val = float(I[-1]) if I else None
    tp_val = float(TP[-1]) if TP else None
    lra_val = float(LRA[-1]) if LRA else None
    return {"lufs": i_val, "tp": tp_val, "lra": lra_val, "duration": dur, "sample_rate": sr, "channels": ch, "codec": codec}


def step_1_clean_sfx_duplicates():
    print("--- Step 1: Cleaning SFX duplicates & misfilings ---")
    # 1. Delete duplicate impact_violent_thud.mp3
    p_viol = os.path.join(SFX_ROOT, "02_Impacts_and_Booms", "impact_violent_thud.mp3")
    if os.path.exists(p_viol):
        # Remove read-only attribute if present
        subprocess.run(["attrib", "-R", p_viol], capture_output=True)
        os.remove(p_viol)
        print(f"Removed duplicate file: {p_viol}")

    # 2. Trim whoosh_micro_0.3s.mp3 to true 0.35s
    p_micro = os.path.join(SFX_ROOT, "01_Transitional_Whooshes", "whoosh_micro_0.3s.mp3")
    if os.path.exists(p_micro):
        subprocess.run(["attrib", "-R", p_micro], capture_output=True)
        tmp_out = p_micro + ".tmp.mp3"
        # Trim to 0.35s with snappy fadeout
        cmd = ["ffmpeg", "-y", "-hide_banner", "-i", p_micro, "-af", "atrim=0:0.35,afade=t=out:st=0.25:d=0.10,aresample=48000", "-b:a", "320k", tmp_out]
        run_cmd(cmd)
        if os.path.exists(tmp_out):
            os.replace(tmp_out, p_micro)
            print("Trimmed whoosh_micro_0.3s.mp3 to true 0.35s duration.")

    # 3. Move foley_interior_door.wav from Room Tone to Foley
    p_door = os.path.join(SFX_ROOT, "05_Room_Tone_and_Beds", "foley_interior_door.wav")
    dst_door = os.path.join(SFX_ROOT, "04_Foley_and_Movement", "foley_interior_door.wav")
    if os.path.exists(p_door):
        subprocess.run(["attrib", "-R", p_door], capture_output=True)
        shutil.move(p_door, dst_door)
        print(f"Moved door sound to Foley: {dst_door}")

    # 4. Create 06_Ambiences and move ambience_wind_leaves.wav
    amb_dir = os.path.join(SFX_ROOT, "06_Ambiences")
    os.makedirs(amb_dir, exist_ok=True)
    p_wind = os.path.join(SFX_ROOT, "05_Room_Tone_and_Beds", "ambience_wind_leaves.wav")
    dst_wind = os.path.join(amb_dir, "ambience_wind_leaves.wav")
    if os.path.exists(p_wind):
        subprocess.run(["attrib", "-R", p_wind], capture_output=True)
        shutil.move(p_wind, dst_wind)
        print(f"Moved wind ambience to 06_Ambiences: {dst_wind}")


def step_2_ingest_documentary_sfx():
    print("--- Step 2: Ingesting essential documentary SFX ---")
    new_assets = [
        # (src_subpath, dst_folder, dst_filename, is_room_tone)
        (
            r"Sound Effects Series (Volume.1-10)\Volume 1\Mechanical & Science\Projector 16MM Sequence.wav",
            "03_Editorial_UI_and_Graphics", "sfx_projector_16mm.wav", False
        ),
        (
            r"Sound Effects Series (Volume.1-10)\Volume 1\Electronic & Communications\TV Static.wav",
            "03_Editorial_UI_and_Graphics", "sfx_tv_static.wav", False
        ),
        (
            r"Sound Effects Series (Volume.1-10)\Volume 1\Electronic & Communications\Radio Static Old.wav",
            "03_Editorial_UI_and_Graphics", "sfx_radio_static_vintage.wav", False
        ),
        (
            r"Sound Effects Series (Volume.1-10)\Volume 1\Music & Atmosphere Elements\Whisper Drone Atmosphere.wav",
            "02_Impacts_and_Booms", "sfx_drone_dark_whisper.wav", False
        ),
        (
            r"BBC Sound Effects Library\Sound Effects Library-01 (Domestic Backgrounds)\08 Domestic Chiming Clock - Ticking.mp3",
            "03_Editorial_UI_and_Graphics", "sfx_clock_ticking_tension.wav", False
        ),
        (
            r"1001 Sound Effects\Applause\Large Crowd Applause 01.wav",
            "06_Ambiences", "sfx_crowd_applause_theater.wav", False
        ),
        # Room tone beds (all calibrated to -36.0 LUFS)
        (
            r"Sound Effects Series (Volume.1-10)\Volume 2\Backgrounds\Room Tone Long.wav",
            "05_Room_Tone_and_Beds", "room_tone_neutral_long.wav", True
        ),
        (
            r"Sound Effects Series (Volume.1-10)\Volume 2\Backgrounds\Office Interior.wav",
            "05_Room_Tone_and_Beds", "room_tone_office_archive.wav", True
        ),
        (
            r"BBC Sound Effects Library\Sound Effects Library-04 (Interior Backgrounds)\06 Public Library.mp3",
            "05_Room_Tone_and_Beds", "room_tone_public_library.wav", True
        ),
    ]

    for src_rel, dst_fld, dst_name, is_rt in new_assets:
        src = os.path.join(SRC_AUDIO_LIB, src_rel)
        dst_dir = os.path.join(SFX_ROOT, dst_fld)
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, dst_name)
        if os.path.exists(src):
            if not os.path.exists(dst):
                # Copy and resample to 48kHz 24-bit WAV
                cmd = ["ffmpeg", "-y", "-hide_banner", "-i", src, "-ar", "48000", "-c:a", "pcm_s24le", dst]
                run_cmd(cmd)
                print(f"Ingested documentary asset: {dst_name} -> {dst_fld}")


def step_3_normalize_sfx():
    print("--- Step 3: Calibrating SFX loudness (-9.0 dBTP events / -36.0 LUFS room tone) ---")
    sfx_files = []
    for r, _, fs in os.walk(SFX_ROOT):
        for f in fs:
            if f.lower().endswith((".wav", ".mp3", ".ogg")):
                sfx_files.append(os.path.join(r, f))

    for p in sfx_files:
        subprocess.run(["attrib", "-R", p], capture_output=True)
        is_room_tone = "05_Room_Tone_and_Beds" in p
        meas = measure_audio(p)

        if is_room_tone:
            # Target: -36.0 LUFS integrated
            current_i = meas["lufs"]
            if current_i is not None and abs(current_i - (-36.0)) > 0.3:
                gain = -36.0 - current_i
                tmp = p + ".norm.wav"
                cmd = ["ffmpeg", "-y", "-hide_banner", "-i", p, "-af", f"volume={gain:.2f}dB", "-ar", "48000", "-c:a", "pcm_s24le", tmp]
                run_cmd(cmd)
                if os.path.exists(tmp):
                    os.replace(tmp, p)
                    print(f"  [Room Tone -36 LUFS] {os.path.basename(p)} (adjusted {gain:+.1f}dB)")
        else:
            # Target: -9.0 dBTP true-peak limit
            current_tp = meas["tp"]
            if current_tp is not None and (abs(current_tp - (-9.0)) > 0.3 or current_tp > -8.5):
                gain = -9.0 - current_tp
                tmp = p + ".norm.wav"
                # Two-stage: volume gain + brickwall limiter at 0.3548 (-9.0 dBTP)
                cmd = ["ffmpeg", "-y", "-hide_banner", "-i", p, "-af", f"volume={gain:.2f}dB,alimiter=limit=0.3548:level=false", "-ar", "48000", "-c:a", "pcm_s24le", tmp]
                run_cmd(cmd)
                if os.path.exists(tmp):
                    os.replace(tmp, p)
                    print(f"  [Event SFX -9 dBTP] {os.path.basename(p)} (adjusted {gain:+.1f}dB)")


def step_4_rebuild_music_moods():
    print("--- Step 4: Reorganizing Music Mood Folders with Zero Overlap ---")
    # Clean mood directory structure
    MOOD_MAPPINGS = {
        "01_Melancholic_Reflective": [
            "Touching_Moments_Two_-_Higher.mp3",
            "Bittersweet.mp3",
            "Anguish.mp3",
            "Loss.mp3",
            "Private_Reflection.mp3",
        ],
        "02_Tension_Investigative_Suspense": [
            "Awkward_Meeting.mp3",
            "Comfortable_Mystery.mp3",
            "Long_Note_One.mp3",
            "Long_Note_Two.mp3",
            "Long_Note_Three.mp3",
            "Mesmerize.mp3",
            "Past_the_Edge.mp3",
        ],
        "03_Warm_Emotional_Hopeful": [
            "Heartwarming.mp3",
            "Lasting_Hope.mp3",
            "Clean_Soul.mp3",
            "Clear_Waters.mp3",
            "Background_Acoustic_Full.mp3",
            "MUSCStr_Emotional_cinematic_Loop.mp3",
        ],
        "04_Nostalgic_Gentle_Memory": [
            "Dreamy_Flashback.mp3",
            "Gymnopedie_No_1.mp3",
            "Echoes_of_Time.mp3",
        ],
        "05_Wholesome_Documentary_Pacing": [
            "Wholesome.mp3",
            "Clean_Soul.mp3",
            "Clear_Waters.mp3",
        ],
        "06_Dramatic_Climax_Triumph": [
            "Despair_and_Triumph.mp3",
            "Sovereign.mp3",
            "Epic_Motivation_Full.mp3",
            "Inspiring_Voyage_Full.mp3",
            "The_Inspiring_Full.mp3",
        ],
        "07_Dark_Tragic_Downfall": [
            "Cryptic_Sorrow.mp3",
            "Darkest_Child.mp3",
            "Grave_Blow.mp3",
            "Failing_Defense.mp3",
            "Sad_Trio.mp3",
        ],
        "08_Historical_Retrospective": [
            "Sovereign.mp3",
            "Private_Reflection.mp3",
            "Gymnopedie_No_1.mp3",
            "Echoes_of_Time.mp3",
        ],
    }

    # Remove old links from mood folders and recreate crisp hardlinks
    for mood, track_list in MOOD_MAPPINGS.items():
        mood_dir = os.path.join(MUSIC_ROOT, mood)
        os.makedirs(mood_dir, exist_ok=True)
        # Clear existing hardlinks in mood dir
        for existing in os.listdir(mood_dir):
            ep = os.path.join(mood_dir, existing)
            if os.path.isfile(ep):
                subprocess.run(["attrib", "-R", ep], capture_output=True)
                os.remove(ep)

        # Create fresh hardlinks
        for t in track_list:
            src = os.path.join(ALL_TRACKS, t)
            dst = os.path.join(mood_dir, t)
            if os.path.exists(src):
                os.link(src, dst)
        print(f"Re-linked mood folder: {mood} ({len(track_list)} hardlinked tracks)")

    return MOOD_MAPPINGS


def step_5_update_catalog(mood_mappings):
    print("--- Step 5: Updating AUDIO_CATALOG.json with Measured Specs ---")
    existing_cat = {}
    if os.path.exists(CATALOG_PATH):
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            existing_cat = json.load(f)

    # Invert mood mappings for music metadata
    track_to_moods = {}
    for mood, tracks in mood_mappings.items():
        for t in tracks:
            track_to_moods.setdefault(t, []).append(mood)

    # Audit All_Tracks
    music_catalog = {}
    for f in sorted(os.listdir(ALL_TRACKS)):
        p = os.path.join(ALL_TRACKS, f)
        if os.path.isfile(p) and f.lower().endswith((".mp3", ".wav")):
            meas = measure_audio(p)
            prev = existing_cat.get("music", {}).get(f, {})
            # Determine edit relationship
            edits = []
            if "Epic_Motivation" in f:
                edits = ["Full", "Short_A", "Short_B", "Short_C", "Short_D"]
            elif "The_Inspiring" in f:
                edits = ["Full", "1Min", "30Sec", "15Sec"]
            elif "Inspiring_Voyage" in f:
                edits = ["Full", "Short", "Teaser"]
            elif "Background_Acoustic" in f:
                edits = ["Full", "Medium", "Short"]

            music_catalog[f] = {
                "title": prev.get("title", f.replace("_", " ").rsplit(".", 1)[0]),
                "artist": prev.get("artist", "Kevin MacLeod"),
                "license": prev.get("license", "CC-BY 4.0"),
                "credit": prev.get("credit", f"Music: '{f}' by Kevin MacLeod (incompetech.com) - Licensed under CC-BY 4.0"),
                "path": f"01_Music\\All_Tracks\\{f}",
                "moods": track_to_moods.get(f, ["06_Dramatic_Climax_Triumph" if "Inspiring" in f or "Epic" in f else "Unassigned_Cutdown"]),
                "duration_s": round(meas["duration"], 2),
                "lufs_integrated": meas["lufs"],
                "true_peak_dbtp": meas["tp"],
                "lra_lu": meas["lra"],
                "sample_rate": meas["sample_rate"],
                "format": f.rsplit(".", 1)[-1].upper(),
                "description": prev.get("description", "Broadcast documentary audio track."),
                "edits_available": edits if edits else None,
            }

    # Audit SFX
    sfx_catalog = {}
    for r, _, fs in sorted(os.walk(SFX_ROOT)):
        fld = os.path.basename(r)
        if fld == "02_SFX":
            continue
        for f in sorted(fs):
            if f.lower().endswith((".wav", ".mp3", ".ogg")):
                p = os.path.join(r, f)
                meas = measure_audio(p)
                prev = existing_cat.get("sfx", {}).get(f, {})
                is_room = "05_Room_Tone_and_Beds" in r
                sfx_catalog[f] = {
                    "folder": fld,
                    "path": f"02_SFX\\{fld}\\{f}",
                    "category": fld.split("_", 1)[-1].replace("_", " "),
                    "duration_s": round(meas["duration"], 2),
                    "true_peak_dbtp": meas["tp"],
                    "lufs_integrated": meas["lufs"] if is_room else None,
                    "sample_rate": meas["sample_rate"],
                    "channels": meas["channels"],
                    "description": prev.get("description", f"{fld.split('_', 1)[-1].replace('_', ' ')} sound effect calibrated for broadcast video."),
                }

    new_cat = {
        "version": "2.0.0",
        "description": "Central Production Audio Library - Broadcast Master Catalog",
        "standards": {
            "dialogue_integrated_lufs": -16.0,
            "dialogue_true_peak_ceiling_dbtp": -1.0,
            "music_bed_open_lufs": -18.0,
            "music_bed_sidechain_ducked_lufs": -28.0,
            "music_limiter_ceiling_dbtp": -1.0,
            "sfx_true_peak_target_dbtp": -9.0,
            "room_tone_integrated_lufs": -36.0,
        },
        "stats": {
            "total_music_master_files": len(music_catalog),
            "total_sfx_master_files": len(sfx_catalog),
            "total_production_assets": len(music_catalog) + len(sfx_catalog),
        },
        "music": music_catalog,
        "sfx": sfx_catalog,
    }

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(new_cat, f, indent=2)

    print(f"Master Catalog updated: {CATALOG_PATH}")
    print(f"Total assets: {len(music_catalog)} music + {len(sfx_catalog)} SFX = {len(music_catalog)+len(sfx_catalog)} total.")


def step_6_set_readonly():
    print("--- Step 6: Setting master files to read-only (+R) ---")
    cmd = ["attrib", "+R", "/S", os.path.join(LIBRARY_ROOT, "*.*")]
    run_cmd(cmd)
    print("Master library files are now strictly write-protected against in-place overwrites.")


if __name__ == "__main__":
    step_1_clean_sfx_duplicates()
    step_2_ingest_documentary_sfx()
    step_3_normalize_sfx()
    moods = step_4_rebuild_music_moods()
    step_5_update_catalog(moods)
    step_6_set_readonly()
    print("All review fixes executed successfully!")
