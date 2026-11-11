import os, json, subprocess, shutil, re

LIBRARY_ROOT = r"E:\((Video_Editing_Asset_Library))\(( Production Audio Library ))"
MUSIC_ROOT = os.path.join(LIBRARY_ROOT, "01_Music")
SFX_ROOT = os.path.join(LIBRARY_ROOT, "02_SFX")
ALL_TRACKS = os.path.join(MUSIC_ROOT, "All_Tracks")
DAVINCI_MEDIA = r"E:\(( Sounds Effect - Audio Library ))\DaVinci_Resolve_Audio_Library\Media Files"
AUDIO_LIB_SRC = r"E:\(( Sounds Effect - Audio Library ))"
CAT_PATH = os.path.join(LIBRARY_ROOT, "AUDIO_CATALOG.json")

with open(CAT_PATH, "r", encoding="utf-8") as f:
    cat = json.load(f)

extra_music = [
    (os.path.join(AUDIO_LIB_SRC, "(( Music Tracks ))", "epic-inspiring-motivate-2025-01-16-08-04-51-utc", "Music by Luis Ruiz- Epic Motivate.mp3"),
     "Epic_Motivate_LuisRuiz.mp3", "Epic Motivate (Luis Ruiz)", ["06_Dramatic_Climax_Triumph"], "Sweeping orchestral trailer motivation bed for major breakthroughs", "Envato Elements Commercial"),
    (os.path.join(AUDIO_LIB_SRC, "(( Music Tracks ))", "inspiring-voyage-2025-01-15-13-32-36-utc", "Teaser.mp3"),
     "Inspiring_Voyage_Teaser.mp3", "Inspiring Voyage (Teaser 30s)", ["06_Dramatic_Climax_Triumph"], "Short triumphant 30s teaser crescendo", "Envato Elements Commercial"),
    (os.path.join(AUDIO_LIB_SRC, "(( Music Tracks ))", "the-inspiring-2025-05-22-04-07-59-utc", "30_SEC.mp3"),
     "The_Inspiring_30Sec.mp3", "The Inspiring (30 Sec Stinger)", ["06_Dramatic_Climax_Triumph"], "Punchy 30-second motivational stinger", "Envato Elements Commercial"),
    (os.path.join(AUDIO_LIB_SRC, "(( Music Tracks ))", "the-inspiring-2025-05-22-04-07-59-utc", "15_SEC.mp3"),
     "The_Inspiring_15Sec.mp3", "The Inspiring (15 Sec Stinger)", ["06_Dramatic_Climax_Triumph"], "Quick 15-second motivational stinger", "Envato Elements Commercial"),
    (os.path.join(AUDIO_LIB_SRC, "(( Music Tracks ))", "motivation-pack", "Epic Short B.mp3"),
     "Epic_Motivation_Short_B.mp3", "Epic Motivation (Short B)", ["06_Dramatic_Climax_Triumph"], "Heavy dramatic brass and percussion accent", "Envato Elements Commercial"),
    (os.path.join(AUDIO_LIB_SRC, "(( Music Tracks ))", "motivation-pack", "Epic Short C.mp3"),
     "Epic_Motivation_Short_C.mp3", "Epic Motivation (Short C)", ["06_Dramatic_Climax_Triumph"], "Uplifting symphonic transition stinger", "Envato Elements Commercial"),
    (os.path.join(AUDIO_LIB_SRC, "(( Music Tracks ))", "motivation-pack", "Epic Short D.mp3"),
     "Epic_Motivation_Short_D.mp3", "Epic Motivation (Short D)", ["06_Dramatic_Climax_Triumph"], "Driving rhythmic orchestral cadence", "Envato Elements Commercial")
]

for src, fname, title, moods, desc, lic in extra_music:
    if os.path.exists(src):
        dst = os.path.join(ALL_TRACKS, fname)
        if not os.path.exists(dst):
            try: os.link(src, dst)
            except: shutil.copy2(src, dst)
        for m in moods:
            md = os.path.join(MUSIC_ROOT, m)
            os.makedirs(md, exist_ok=True)
            dst_m = os.path.join(md, fname)
            if not os.path.exists(dst_m):
                try: os.link(dst, dst_m)
                except: shutil.copy2(dst, dst_m)
        dur_r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dst], capture_output=True, text=True)
        dur = round(float(dur_r.stdout.strip()), 2)
        loud_r = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", dst, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
        m_i = re.findall(r"I:\s+(-?[\d.]+) LUFS", loud_r.stderr)
        m_tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", loud_r.stderr)
        cat["music"][fname] = {
            "title": title,
            "artist": "Production Library / Luis Ruiz",
            "license": lic,
            "credit": f'"{title}" Licensed under Envato Elements Commercial License',
            "moods": moods,
            "story_role": desc,
            "duration_s": dur,
            "lufs_integrated": float(m_i[-1]) if m_i else None,
            "true_peak_dbtp": float(m_tp[-1]) if m_tp else None,
            "path": os.path.relpath(dst, LIBRARY_ROOT)
        }
        print(f"Added Music: {fname}")

extra_sfx = [
    (os.path.join(DAVINCI_MEDIA, "Tape Ripping.M.wav"), "04_Foley_and_Movement", "foley_tape_rip.wav", "Tape Rip", "Adhesive packing tape ripping foley for evidence / unboxing"),
    (os.path.join(DAVINCI_MEDIA, "Tool Box Rummage.M.wav"), "04_Foley_and_Movement", "foley_toolbox_rummage.wav", "Toolbox Rummage", "Metal tools clinking in toolbox foley"),
    (os.path.join(DAVINCI_MEDIA, "Window Blinds Loud.M.wav"), "04_Foley_and_Movement", "foley_window_blinds_open.wav", "Window Blinds", "Venetian window blinds opening foley for detective lighting"),
    (os.path.join(DAVINCI_MEDIA, "Zippo Lighter Open Light.M.wav"), "04_Foley_and_Movement", "foley_zippo_lighter_open.wav", "Zippo Lighter", "Classic metal Zippo lighter flick and ignite foley"),
    (os.path.join(DAVINCI_MEDIA, "Bullet Shells Drop 1.M.wav"), "04_Foley_and_Movement", "foley_brass_shell_drop.wav", "Brass Shell Drop", "Brass bullet cartridge falling onto concrete surface"),
    (os.path.join(DAVINCI_MEDIA, "Soda Can Open Pour.M.wav"), "04_Foley_and_Movement", "foley_soda_can_open.wav", "Soda Can Open", "Crisp aluminum can tab pop foley"),
    (os.path.join(DAVINCI_MEDIA, "Sparkler Fast Whoosh.M.wav"), "01_Transitional_Whooshes", "whoosh_sparkler_fast.wav", "Sparkler Whoosh", "Airy sizzle whoosh for dynamic wipes"),
    (os.path.join(DAVINCI_MEDIA, "Wood Floor Creaks and Ground.M.wav"), "04_Foley_and_Movement", "foley_wood_floor_creaks.wav", "Floorboard Creak", "Old historical floorboard creak foley"),
    (os.path.join(DAVINCI_MEDIA, "Stethoscope.M.wav"), "04_Foley_and_Movement", "foley_heartbeat_stethoscope.wav", "Stethoscope Heartbeat", "Medical stethoscope heartbeat pulse for tension peaks"),
    (os.path.join(DAVINCI_MEDIA, "Car Banging.M.wav"), "02_Impacts_and_Booms", "impact_car_body_dent.wav", "Car Impact Thud", "Heavy metallic vehicle impact thud"),
    (os.path.join(DAVINCI_MEDIA, "Shoveling Dirt.M.wav"), "04_Foley_and_Movement", "foley_shoveling_dirt.wav", "Shoveling Dirt", "Shovel cutting through soil foley for historical archaeology / buried secrets"),
    (os.path.join(DAVINCI_MEDIA, "Beads Moving Around On Table.M.wav"), "04_Foley_and_Movement", "foley_small_objects_table.wav", "Small Objects Scatter", "Small wooden/plastic beads shifting on table surface")
]

for src, rel_dir, fname, title, desc in extra_sfx:
    if os.path.exists(src):
        dst = os.path.join(SFX_ROOT, rel_dir, fname)
        if not os.path.exists(dst):
            try: os.link(src, dst)
            except: shutil.copy2(src, dst)
        dur_r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dst], capture_output=True, text=True)
        dur = round(float(dur_r.stdout.strip()), 2)
        loud_r = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", dst, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
        m_tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", loud_r.stderr)
        cat["sfx"][fname] = {
            "name": fname,
            "title": title,
            "category": rel_dir.split("_", 1)[-1],
            "folder": rel_dir,
            "description": desc,
            "duration_s": dur,
            "true_peak_dbtp": float(m_tp[-1]) if m_tp else None,
            "path": os.path.relpath(dst, LIBRARY_ROOT)
        }
        print(f"Added SFX: {fname}")

with open(CAT_PATH, "w", encoding="utf-8") as f:
    json.dump(cat, f, indent=2, ensure_ascii=False)

print(f"TOTAL ELEMENTS: {len(cat['music'])} Music + {len(cat['sfx'])} SFX = {len(cat['music']) + len(cat['sfx'])} Total Assets!")
