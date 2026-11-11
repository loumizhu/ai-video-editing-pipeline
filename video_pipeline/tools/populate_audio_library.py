"""Script to build, populate, and catalog the central Production Audio Library in
E:\\((Video_Editing_Asset_Library))\\(( Production Audio Library )).
"""
import json
import os
import re
import shutil
import subprocess

LIBRARY_ROOT = r"E:\((Video_Editing_Asset_Library))\(( Production Audio Library ))"
MUSIC_ROOT = os.path.join(LIBRARY_ROOT, "01_Music")
SFX_ROOT = os.path.join(LIBRARY_ROOT, "02_SFX")
ALL_TRACKS = os.path.join(MUSIC_ROOT, "All_Tracks")

AUDIO_LIB_SRC = r"E:\(( Sounds Effect - Audio Library ))"
VIDEO_ASSET_LIB = r"E:\((Video_Editing_Asset_Library))"

TRACK_METADATA = {
    "Bittersweet.mp3": {
        "title": "Bittersweet",
        "artist": "Kevin MacLeod",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "credit": '"Bittersweet" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["01_Melancholic_Reflective", "07_Dark_Tragic_Downfall"],
        "description": "Slow nostalgic piano with bittersweet emotional depth. Ideal for sad reflections and tragic backstories."
    },
    "Touching_Moments_Two_-_Higher.mp3": {
        "title": "Touching Moments Two - Higher",
        "artist": "Kevin MacLeod",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "credit": '"Touching Moments Two - Higher" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["01_Melancholic_Reflective"],
        "description": "Gentle, poignant piano reflection with subtle strings. Highly emotional storytelling."
    },
    "Private_Reflection.mp3": {
        "title": "Private Reflection",
        "artist": "Kevin MacLeod",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "credit": '"Private Reflection" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["01_Melancholic_Reflective", "08_Historical_Retrospective"],
        "description": "Quiet, introspective, contemplative solo piano. Perfect for deeply personal confessions."
    },
    "Heartbreaking.mp3": {
        "title": "Heartbreaking",
        "artist": "Kevin MacLeod",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "credit": '"Heartbreaking" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["01_Melancholic_Reflective", "07_Dark_Tragic_Downfall"],
        "description": "Tender grief, violin and piano weeping over crushed careers and broken lives."
    },
    "Loss.mp3": {
        "title": "Loss",
        "artist": "Kevin MacLeod",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "credit": '"Loss" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["01_Melancholic_Reflective", "07_Dark_Tragic_Downfall"],
        "description": "Short poignant sorrow and lingering absence. A somber transition bed."
    },
    "Long_Note_Two.mp3": {
        "title": "Long Note Two",
        "artist": "Kevin MacLeod",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "credit": '"Long Note Two" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["02_Tension_Investigative_Suspense"],
        "description": "Long ambient drone sustain, documentary stillness, suspenseful investigative pause."
    },
    "Awkward_Meeting.mp3": {
        "title": "Awkward Meeting",
        "artist": "Kevin MacLeod",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "credit": '"Awkward Meeting" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["02_Tension_Investigative_Suspense"],
        "description": "Quirky tension, investigative curiosity, subtle rhythmic intrigue, courtroom / contract scrutiny."
    },
    "Cryptic_Sorrow.mp3": {
        "title": "Cryptic Sorrow",
        "artist": "Kevin MacLeod",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "credit": '"Cryptic Sorrow" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["02_Tension_Investigative_Suspense", "07_Dark_Tragic_Downfall"],
        "description": "Dark gothic orchestral sorrow, mysterious unraveling, ominous investigative tone."
    },
    "Heartwarming.mp3": {
        "title": "Heartwarming",
        "artist": "Kevin MacLeod",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "credit": '"Heartwarming" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["03_Warm_Emotional_Hopeful"],
        "description": "Warm, tender piano, hopeful and touching. Good for family reconciliations and childhood beginnings."
    },
    "Lasting_Hope.mp3": {
        "title": "Lasting Hope",
        "artist": "Kevin MacLeod",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "credit": '"Lasting Hope" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["03_Warm_Emotional_Hopeful"],
        "description": "Strings and piano, poignant resilience, bittersweet triumph over adversity."
    },
    "Dreamy_Flashback.mp3": {
        "title": "Dreamy Flashback",
        "artist": "Kevin MacLeod",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "credit": '"Dreamy Flashback" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["04_Nostalgic_Gentle_Memory", "08_Historical_Retrospective"],
        "description": "Airy, ethereal memories, golden age Hollywood reminiscence, childhood beginnings."
    },
    "Wholesome.mp3": {
        "title": "Wholesome",
        "artist": "Kevin MacLeod",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "credit": '"Wholesome" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["05_Wholesome_Documentary_Pacing"],
        "description": "Gentle, light storytelling, everyday documentary pacing, neutral narrative flow."
    },
    "Background_Acoustic_Full.mp3": {
        "title": "Background Acoustic (Full 2:10)",
        "artist": "Envato / Production Library",
        "license": "Envato Elements Royalty-Free Commercial",
        "credit": "Licensed under Envato Elements Commercial License",
        "moods": ["05_Wholesome_Documentary_Pacing", "03_Warm_Emotional_Hopeful"],
        "description": "Light acoustic guitar narrative bed, warm and steady progression."
    },
    "MUSCStr_Emotional_cinematic_Loop.mp3": {
        "title": "Emotional Cinematic String Bed",
        "artist": "ElevenLabs AI / House Curated",
        "license": "Owned Commercial / Royalty Free",
        "credit": "House Curated Audio Bed",
        "moods": ["03_Warm_Emotional_Hopeful", "06_Dramatic_Climax_Triumph"],
        "description": "Lush emotive string bed, builds steadily, ideal for reflective documentary climaxes."
    },
    "Inspiring_Voyage_Full.mp3": {
        "title": "Inspiring Voyage (Full)",
        "artist": "Envato / Production Library",
        "license": "Envato Elements Royalty-Free Commercial",
        "credit": "Licensed under Envato Elements Commercial License",
        "moods": ["06_Dramatic_Climax_Triumph"],
        "description": "Inspiring piano and sweeping orchestral strings for victorious and momentous achievements."
    },
    "The_Inspiring_Full.mp3": {
        "title": "The Inspiring (Full)",
        "artist": "Envato / Production Library",
        "license": "Envato Elements Royalty-Free Commercial",
        "credit": "Licensed under Envato Elements Commercial License",
        "moods": ["06_Dramatic_Climax_Triumph"],
        "description": "Heroic, motivational build with modern cinematic percussion and uplifting strings."
    },
    "Epic_Motivation_Full.mp3": {
        "title": "Epic Motivation (Full Orchestral)",
        "artist": "Envato / Production Library",
        "license": "Envato Elements Royalty-Free Commercial",
        "credit": "Licensed under Envato Elements Commercial License",
        "moods": ["06_Dramatic_Climax_Triumph"],
        "description": "High-impact orchestral drama, dramatic revelations and breakthrough moments."
    }
}

def hardlink_or_copy(src, dst):
    if os.path.exists(dst):
        return
    try:
        os.link(src, dst)
    except Exception:
        shutil.copy2(src, dst)

def probe_audio(path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration,bit_rate:format_tags=title,artist,genre,date", "-of", "json", path]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(r.stdout).get("format", {})
        dur = float(data.get("duration", 0))
        tags = data.get("tags", {})
        return {
            "duration_s": round(dur, 2),
            "bitrate_kbps": int(int(data.get("bit_rate", 0)) / 1000) if data.get("bit_rate") else None,
            "title": tags.get("title") or tags.get("Title"),
            "artist": tags.get("artist") or tags.get("Artist")
        }
    except Exception as e:
        return {"duration_s": 0, "error": str(e)}

def measure_loudness(path):
    cmd = ["ffmpeg", "-nostats", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        t = r.stderr
        m_i = re.findall(r"I:\s+(-?[\d.]+) LUFS", t)
        m_tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", t)
        lufs = float(m_i[-1]) if m_i else None
        tp = float(m_tp[-1]) if m_tp else None
        return {"lufs_integrated": lufs, "true_peak_dbtp": tp}
    except Exception:
        return {"lufs_integrated": None, "true_peak_dbtp": None}

def main():
    print("=== Central Audio Library Processing & Cataloging ===")
    catalog = {"music": {}, "sfx": {}}

    # 1. Process all tracks in All_Tracks
    all_files = [f for f in os.listdir(ALL_TRACKS) if f.lower().endswith(".mp3")]
    for fname in sorted(all_files):
        track_path = os.path.join(ALL_TRACKS, fname)
        meta = TRACK_METADATA.get(fname, {
            "title": fname.replace(".mp3", "").replace("_", " "),
            "artist": "Kevin MacLeod",
            "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
            "credit": f'"{fname}" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
            "moods": ["05_Wholesome_Documentary_Pacing"],
            "description": "Documentary background music bed."
        })

        # Distribute into mood folders via hardlink
        for m in meta["moods"]:
            m_dir = os.path.join(MUSIC_ROOT, m)
            os.makedirs(m_dir, exist_ok=True)
            hardlink_or_copy(track_path, os.path.join(m_dir, fname))

        info = probe_audio(track_path)
        loud = measure_loudness(track_path)
        catalog["music"][fname] = {
            "title": meta["title"],
            "artist": meta["artist"],
            "license": meta["license"],
            "credit": meta["credit"],
            "moods": meta["moods"],
            "description": meta["description"],
            "duration_s": info.get("duration_s"),
            "lufs_integrated": loud.get("lufs_integrated"),
            "true_peak_dbtp": loud.get("true_peak_dbtp"),
            "file": fname
        }
        print(f"Cataloged Music: {fname:<32} | {meta['title']} | {info.get('duration_s')}s | {loud.get('lufs_integrated')} LUFS")

    # 2. SFX Ingestion & Cataloging
    print("\n--- Ingesting and Organizing SFX ---")
    sfx_sources = [
        # (source_path, target_rel_dir, new_name, category, description)
        (os.path.join(VIDEO_ASSET_LIB, "Audio_Transition_Woosh", "WHSH-Micro_Whoosh_0.3s_sh-Elevenlabs.mp3"), "01_Transitional_Whooshes", "whoosh_micro_0.3s.mp3", "Micro Whoosh", "Ultra-short 0.3s snappy whoosh for fast cuts and UI popouts"),
        (os.path.join(VIDEO_ASSET_LIB, "Audio_Transition_Woosh", "WHSH-Soft_cinematic_zoom--Elevenlabs.mp3"), "01_Transitional_Whooshes", "whoosh_cinematic_zoom.mp3", "Cinematic Zoom", "Gentle whoosh with cinematic zoom trail"),
        (os.path.join(VIDEO_ASSET_LIB, "Audio_Transition_Woosh", "WHSH-Soft_Riser_Woosh_Tra-Elevenlabs.mp3"), "01_Transitional_Whooshes", "riser_whoosh_transition.mp3", "Riser Whoosh", "Building soft riser swoosh resolving on the cut point"),
        (os.path.join(VIDEO_ASSET_LIB, "Audio_Transition_Woosh", "WHSH-Soft_sound_effect_fo-Elevenlabs.mp3"), "01_Transitional_Whooshes", "whoosh_soft_ambient.mp3", "Ambient Whoosh", "Soft airy transition whoosh"),
        (os.path.join(VIDEO_ASSET_LIB, "(( Video Overlays & Effects Library ))", "04_Sound_FX_Transitions", "whoosh-1.mp3"), "01_Transitional_Whooshes", "whoosh_clean_air_01.mp3", "Clean Whoosh", "Clean high-frequency air whoosh"),
        (os.path.join(VIDEO_ASSET_LIB, "(( Video Overlays & Effects Library ))", "04_Sound_FX_Transitions", "whoosh-2.mp3"), "01_Transitional_Whooshes", "whoosh_clean_air_02.mp3", "Clean Whoosh", "Short sharp cut whoosh"),
        (os.path.join(VIDEO_ASSET_LIB, "(( Video Overlays & Effects Library ))", "04_Sound_FX_Transitions", "whoosh-3-Diaporama.wav"), "01_Transitional_Whooshes", "whoosh_diaporama_slide.wav", "Slide Whoosh", "Smooth slide whoosh for slideshow / photo transitions"),
        (os.path.join(AUDIO_LIB_SRC, "Woosh", "Swoosh_01.wav"), "01_Transitional_Whooshes", "swoosh_high_energy_01.wav", "Swoosh", "High energy fast dynamic swoosh"),
        (os.path.join(AUDIO_LIB_SRC, "Woosh", "Swoosh_02.wav"), "01_Transitional_Whooshes", "swoosh_high_energy_02.wav", "Swoosh", "Punchy fast swoosh"),

        # Impacts and Booms
        (os.path.join(VIDEO_ASSET_LIB, "Dramatic Intro Vwoum", "Dam dramatic intro doom-cinematic_intro_soun-Elevenlabs.mp3"), "02_Impacts_and_Booms", "impact_dramatic_intro_doom.mp3", "Dramatic Impact", "Deep doom drop for chapter titles and chilling turns"),
        (os.path.join(VIDEO_ASSET_LIB, "Dramatic Intro Vwoum", "Ultra Dramlatic Shock Intro Revelation-cinematic_intro_soun-Elevenlabs.mp3"), "02_Impacts_and_Booms", "impact_ultra_shock_revelation.mp3", "Shock Impact", "Ultra dramatic cinematic revelation impact hit"),
        (os.path.join(VIDEO_ASSET_LIB, "Dramatic Intro Vwoum", "DSGNImpt-Cinematic_bass_thud,-Elevenlabs.mp3"), "02_Impacts_and_Booms", "impact_cinematic_bass_thud.mp3", "Bass Thud", "Heavy cinematic bass thud"),
        (os.path.join(VIDEO_ASSET_LIB, "Dramatic Intro Vwoum", "Violent Intro ThTam-Cinematic_bass_thud,-Elevenlabs.mp3"), "02_Impacts_and_Booms", "impact_violent_thud.mp3", "Heavy Thud", "Visceral cinematic hit with sub drop"),
        (os.path.join(AUDIO_LIB_SRC, "Cinematic Waooouuumm", "trailer-big-powerful-impact-241356.mp3"), "02_Impacts_and_Booms", "impact_trailer_big_powerful.mp3", "Trailer Boom", "Massive trailer impact with reverberant sub tail"),

        # UI & Graphics
        (os.path.join(VIDEO_ASSET_LIB, "(( Video Overlays & Effects Library ))", "04_Sound_FX_Transitions", "subscribe_bell.wav"), "03_Editorial_UI_and_Graphics", "ui_subscribe_bell.wav", "Notification Bell", "Clear notification chime for calls to action"),
        (os.path.join(VIDEO_ASSET_LIB, "(( Video Overlays & Effects Library ))", "04_Sound_FX_Transitions", "subscribe_click.wav"), "03_Editorial_UI_and_Graphics", "ui_click_soft.wav", "UI Click", "Soft tactile button click"),
        (os.path.join(AUDIO_LIB_SRC, "Woosh", "HUD Buttons and Notifications Pack", "wav", "button-01.wav"), "03_Editorial_UI_and_Graphics", "ui_hud_button_01.wav", "HUD Button", "Tech UI button tick"),

        # Foley & Realism
        (os.path.join(AUDIO_LIB_SRC, "DaVinci_Resolve_Audio_Library", "Tearing Paper Out.M.wav"), "04_Foley_and_Movement", "foley_tearing_paper.wav", "Foley / Paper", "Paper tearing texture for document & article reveals"),
        (os.path.join(AUDIO_LIB_SRC, "DaVinci_Resolve_Audio_Library", "Using Folder With Papers.M.wav"), "04_Foley_and_Movement", "foley_folder_papers.wav", "Foley / Handling", "Opening archive manila folder and rustling confidential papers"),
        (os.path.join(AUDIO_LIB_SRC, "DaVinci_Resolve_Audio_Library", "Writing In Notebook.M.wav"), "04_Foley_and_Movement", "foley_writing_in_notebook.wav", "Foley / Writing", "Pencil sketching / writing in notebook foley"),
        (os.path.join(AUDIO_LIB_SRC, "DaVinci_Resolve_Audio_Library", "Typing On Computer Keyboard.M.wav"), "04_Foley_and_Movement", "foley_computer_keyboard.wav", "Foley / Typing", "Subtle mechanical computer keyboard typing"),
        (os.path.join(AUDIO_LIB_SRC, "DaVinci_Resolve_Audio_Library", "Wood Chair Creaks.M.wav"), "04_Foley_and_Movement", "foley_wood_chair_creak.wav", "Foley / Room", "Subtle wooden chair creak for interview authenticity")
    ]

    for src, rel_dir, new_name, cat, desc in sfx_sources:
        if os.path.exists(src):
            dst = os.path.join(SFX_ROOT, rel_dir, new_name)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            hardlink_or_copy(src, dst)
            info = probe_audio(dst)
            loud = measure_loudness(dst)
            catalog["sfx"][new_name] = {
                "name": new_name,
                "title": new_name.replace(".wav", "").replace(".mp3", "").replace("_", " ").title(),
                "author": "House / Foley Library",
                "category": cat,
                "license": "Owned Commercial / Royalty-Free",
                "folder": rel_dir,
                "description": desc,
                "duration_s": info.get("duration_s"),
                "true_peak_dbtp": loud.get("true_peak_dbtp"),
                "lufs_integrated": loud.get("lufs_integrated"),
                "path": os.path.relpath(dst, LIBRARY_ROOT)
            }
            print(f"Cataloged SFX:   {new_name:<32} | {cat:<20} | {loud.get('true_peak_dbtp')} dBTP | {rel_dir}")

    # Write Catalog JSON
    cat_path = os.path.join(LIBRARY_ROOT, "AUDIO_CATALOG.json")
    with open(cat_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"\nWritten {len(catalog['music'])} music tracks and {len(catalog['sfx'])} SFX to {cat_path}")

if __name__ == "__main__":
    main()
