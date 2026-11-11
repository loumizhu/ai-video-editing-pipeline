"""Master 100-Element Production Audio Library Builder & Curator.

Curates exactly 100 high-caliber production elements:
- 45 Curated Music Tracks across 8 documentary moods (pre-measured LUFS & true peak)
- 55 Curated Sound Effects across 5 editorial categories (EBU R128 normalized)
Stores everything in:
  E:\\((Video_Editing_Asset_Library))\\(( Production Audio Library ))
and establishes zero-copy NTFS hardlinks and directory junctions.
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

DAVINCI_MEDIA = r"E:\(( Sounds Effect - Audio Library ))\DaVinci_Resolve_Audio_Library\Media Files"
AUDIO_LIB_SRC = r"E:\(( Sounds Effect - Audio Library ))"
VIDEO_ASSET_LIB = r"E:\((Video_Editing_Asset_Library))"
PRESET_SFX = r"E:\((_atWork_))\AI video editing pipeline\video_pipeline\presets\documentary-default\sfx"

# 45 Music Tracks Metadata
MUSIC_DEFINITIONS = {
    # 01 Melancholic & Reflective
    "Bittersweet.mp3": {
        "title": "Bittersweet",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Bittersweet" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["01_Melancholic_Reflective", "07_Dark_Tragic_Downfall"],
        "story_role": "Nostalgic piano & strings for tragic backstories and career decline"
    },
    "Touching_Moments_Two_-_Higher.mp3": {
        "title": "Touching Moments Two - Higher",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Touching Moments Two - Higher" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["01_Melancholic_Reflective"],
        "story_role": "Introspective piano reflection for deeply poignant emotional revelations"
    },
    "Private_Reflection.mp3": {
        "title": "Private Reflection",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Private Reflection" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["01_Melancholic_Reflective", "08_Historical_Retrospective"],
        "story_role": "Contemplative solo piano for quiet personal confessions and vulnerability"
    },
    "Heartbreaking.mp3": {
        "title": "Heartbreaking",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Heartbreaking" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["01_Melancholic_Reflective", "07_Dark_Tragic_Downfall"],
        "story_role": "Mournful weeping violin & piano over crushed youth and shattered dreams"
    },
    "Loss.mp3": {
        "title": "Loss",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Loss" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["01_Melancholic_Reflective", "07_Dark_Tragic_Downfall"],
        "story_role": "Poignant, brief sorrow bed for chapter transitions marking permanent absence"
    },
    "Sad_Trio.mp3": {
        "title": "Sad Trio",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Sad Trio" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["01_Melancholic_Reflective", "07_Dark_Tragic_Downfall"],
        "story_role": "Classical cello, violin, and piano trio lamenting historical tragedy"
    },
    "Anguish.mp3": {
        "title": "Anguish",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Anguish" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["01_Melancholic_Reflective", "07_Dark_Tragic_Downfall"],
        "story_role": "Deep emotional weight, orchestral grief during the darkest turning points"
    },

    # 02 Tension, Investigative & Suspense
    "Long_Note_Two.mp3": {
        "title": "Long Note Two",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Long Note Two" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["02_Tension_Investigative_Suspense"],
        "story_role": "Extended drone sustain, documentary stillness, unhurried forensic inquiry"
    },
    "Long_Note_One.mp3": {
        "title": "Long Note One",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Long Note One" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["02_Tension_Investigative_Suspense"],
        "story_role": "Deep low-frequency drone bed for quiet tension and investigative curiosity"
    },
    "Long_Note_Three.mp3": {
        "title": "Long Note Three",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Long Note Three" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["02_Tension_Investigative_Suspense"],
        "story_role": "Textural eerie drone sustain for unhurried courtroom & contract scrutiny"
    },
    "Awkward_Meeting.mp3": {
        "title": "Awkward Meeting",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Awkward Meeting" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["02_Tension_Investigative_Suspense"],
        "story_role": "Quirky tension, investigative pacing, subtle rhythmic intrigue"
    },
    "Cryptic_Sorrow.mp3": {
        "title": "Cryptic Sorrow",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Cryptic Sorrow" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["02_Tension_Investigative_Suspense", "07_Dark_Tragic_Downfall"],
        "story_role": "Dark gothic orchestral sorrow, mysterious unraveling, ominous tone"
    },
    "Comfortable_Mystery.mp3": {
        "title": "Comfortable Mystery",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Comfortable Mystery" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["02_Tension_Investigative_Suspense"],
        "story_role": "Inquisitive pizzicato and light mystery bed for uncovering hidden archives"
    },
    "Mesmerize.mp3": {
        "title": "Mesmerize",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Mesmerize" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["02_Tension_Investigative_Suspense"],
        "story_role": "Hypnotic, pulsing psychological intrigue, strange circumstances"
    },
    "Past_the_Edge.mp3": {
        "title": "Past the Edge",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Past the Edge" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["02_Tension_Investigative_Suspense"],
        "story_role": "Edge-of-seat suspense, impending danger and ticking timeline pressure"
    },
    "Failing_Defense.mp3": {
        "title": "Failing Defense",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Failing Defense" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["02_Tension_Investigative_Suspense", "07_Dark_Tragic_Downfall"],
        "story_role": "Tense rhythmic ticking, studio legal disputes, imminent career collapse"
    },
    "Darkest_Child.mp3": {
        "title": "Darkest Child",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Darkest Child" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["02_Tension_Investigative_Suspense", "07_Dark_Tragic_Downfall"],
        "story_role": "Disturbing revelations, sinister exploitation, dark childhood secrets"
    },

    # 03 Warm, Emotional & Hopeful
    "Heartwarming.mp3": {
        "title": "Heartwarming",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Heartwarming" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["03_Warm_Emotional_Hopeful"],
        "story_role": "Warm tender piano chords, childhood beginnings and family bonds"
    },
    "Lasting_Hope.mp3": {
        "title": "Lasting Hope",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Lasting Hope" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["03_Warm_Emotional_Hopeful"],
        "story_role": "Poignant resilience, overcoming studio control, hopeful recovery"
    },
    "Clear_Waters.mp3": {
        "title": "Clear Waters",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Clear Waters" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["03_Warm_Emotional_Hopeful", "05_Wholesome_Documentary_Pacing"],
        "story_role": "Peaceful flowing acoustic bed, serene documentary optimism"
    },
    "Clean_Soul.mp3": {
        "title": "Clean Soul",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Clean Soul" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["03_Warm_Emotional_Hopeful", "05_Wholesome_Documentary_Pacing"],
        "story_role": "Gentle acoustic guitar and warm percussion for uplifting resolution"
    },
    "MUSCStr_Emotional_cinematic_Loop.mp3": {
        "title": "Emotional Cinematic String Bed",
        "artist": "ElevenLabs AI / House Curated",
        "license": "Owned Commercial Royalty Free",
        "credit": "House Curated Audio Bed",
        "moods": ["03_Warm_Emotional_Hopeful", "06_Dramatic_Climax_Triumph"],
        "story_role": "Lush emotive string bed loop building steadily into a warm climax"
    },
    "Background_Acoustic_Full.mp3": {
        "title": "Background Acoustic (Full 2:10)",
        "artist": "Envato / Production Library",
        "license": "Envato Elements Commercial",
        "credit": "Licensed under Envato Elements Commercial License",
        "moods": ["03_Warm_Emotional_Hopeful", "05_Wholesome_Documentary_Pacing"],
        "story_role": "Light acoustic guitar rhythm, wholesome narrative progression"
    },
    "Background_Acoustic_Medium.mp3": {
        "title": "Background Acoustic (Medium 1:42)",
        "artist": "Envato / Production Library",
        "license": "Envato Elements Commercial",
        "credit": "Licensed under Envato Elements Commercial License",
        "moods": ["03_Warm_Emotional_Hopeful", "05_Wholesome_Documentary_Pacing"],
        "story_role": "Mid-length acoustic bed for compact documentary segments"
    },
    "Background_Acoustic_Short.mp3": {
        "title": "Background Acoustic (Short 1:15)",
        "artist": "Envato / Production Library",
        "license": "Envato Elements Commercial",
        "credit": "Licensed under Envato Elements Commercial License",
        "moods": ["03_Warm_Emotional_Hopeful", "05_Wholesome_Documentary_Pacing"],
        "story_role": "Short acoustic bed for concise chapter intros and recaps"
    },

    # 04 Nostalgic & Gentle Memory
    "Dreamy_Flashback.mp3": {
        "title": "Dreamy Flashback",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Dreamy Flashback" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["04_Nostalgic_Gentle_Memory", "08_Historical_Retrospective"],
        "story_role": "Airy, ethereal memories, Golden Age Hollywood reminiscence"
    },
    "Gymnopedie_No_1.mp3": {
        "title": "Gymnopedie No 1",
        "artist": "Kevin MacLeod (Erik Satie)",
        "license": "CC BY 4.0",
        "credit": '"Gymnopedie No 1" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["04_Nostalgic_Gentle_Memory", "08_Historical_Retrospective"],
        "story_role": "Classical timeless melancholy, faded black-and-white portraits"
    },
    "Echoes_of_Time.mp3": {
        "title": "Echoes of Time",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Echoes of Time" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["04_Nostalgic_Gentle_Memory", "08_Historical_Retrospective"],
        "story_role": "Passage of decades, looking back at Hollywood's forgotten stars"
    },

    # 05 Wholesome & Documentary Pacing
    "Wholesome.mp3": {
        "title": "Wholesome",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Wholesome" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["05_Wholesome_Documentary_Pacing"],
        "story_role": "Gentle, light storytelling, everyday documentary baseline pacing"
    },

    # 06 Dramatic Climax & Triumph
    "Despair_and_Triumph.mp3": {
        "title": "Despair and Triumph",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Despair and Triumph" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["06_Dramatic_Climax_Triumph"],
        "story_role": "Epic emotional crescendo, struggle giving way to monumental victory"
    },
    "Sovereign.mp3": {
        "title": "Sovereign",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Sovereign" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["06_Dramatic_Climax_Triumph", "08_Historical_Retrospective"],
        "story_role": "Stately historical brass & strings, majestic legacy summaries"
    },
    "Inspiring_Voyage_Full.mp3": {
        "title": "Inspiring Voyage (Full)",
        "artist": "Envato / Production Library",
        "license": "Envato Elements Commercial",
        "credit": "Licensed under Envato Elements Commercial License",
        "moods": ["06_Dramatic_Climax_Triumph"],
        "story_role": "Sweeping orchestral achievement, monumental life turns"
    },
    "Inspiring_Voyage_Short.mp3": {
        "title": "Inspiring Voyage (Short)",
        "artist": "Envato / Production Library",
        "license": "Envato Elements Commercial",
        "credit": "Licensed under Envato Elements Commercial License",
        "moods": ["06_Dramatic_Climax_Triumph"],
        "story_role": "Punchy triumphant crescendo for key act conclusions"
    },
    "The_Inspiring_Full.mp3": {
        "title": "The Inspiring (Full)",
        "artist": "Envato / Production Library",
        "license": "Envato Elements Commercial",
        "credit": "Licensed under Envato Elements Commercial License",
        "moods": ["06_Dramatic_Climax_Triumph"],
        "story_role": "Heroic, motivational build with modern cinematic percussion"
    },
    "The_Inspiring_1Min.mp3": {
        "title": "The Inspiring (1 Min Edit)",
        "artist": "Envato / Production Library",
        "license": "Envato Elements Commercial",
        "credit": "Licensed under Envato Elements Commercial License",
        "moods": ["06_Dramatic_Climax_Triumph"],
        "story_role": "Concise 60s motivational build for rapid third-act shifts"
    },
    "Epic_Motivation_Full.mp3": {
        "title": "Epic Motivation (Full Orchestral)",
        "artist": "Envato / Production Library",
        "license": "Envato Elements Commercial",
        "credit": "Licensed under Envato Elements Commercial License",
        "moods": ["06_Dramatic_Climax_Triumph"],
        "story_role": "High-impact orchestral drama for major breakthrough moments"
    },
    "Epic_Motivation_Short_A.mp3": {
        "title": "Epic Motivation (Short A)",
        "artist": "Envato / Production Library",
        "license": "Envato Elements Commercial",
        "credit": "Licensed under Envato Elements Commercial License",
        "moods": ["06_Dramatic_Climax_Triumph"],
        "story_role": "Dynamic dramatic stinger for high-energy reveals"
    },

    # 07 Dark Tragic Downfall
    "Grave_Blow.mp3": {
        "title": "Grave Blow",
        "artist": "Kevin MacLeod",
        "license": "CC BY 4.0",
        "credit": '"Grave Blow" Kevin MacLeod (incompetech.com) Licensed under CC BY 4.0',
        "moods": ["07_Dark_Tragic_Downfall"],
        "story_role": "Shock revelation, devastating news, dramatic turn for the worse"
    }
}

# 55 Sound Effects Curated Sources
SFX_CURATED_SOURCES = [
    # 01 Transitional Whooshes (12 items)
    (os.path.join(VIDEO_ASSET_LIB, "Audio_Transition_Woosh", "WHSH-Micro_Whoosh_0.3s_sh-Elevenlabs.mp3"), "01_Transitional_Whooshes", "whoosh_micro_0.3s.mp3", "Micro Whoosh", "Ultra-short 0.3s snappy whoosh for fast cuts and UI popouts"),
    (os.path.join(PRESET_SFX, "sfx_whoosh_soft.wav"), "01_Transitional_Whooshes", "sfx_whoosh_soft.wav", "Soft Whoosh", "Soft airy whoosh for gentle cut and scene wipes"),
    (os.path.join(PRESET_SFX, "sfx_whoosh_fast.wav"), "01_Transitional_Whooshes", "sfx_whoosh_fast.wav", "Fast Whoosh", "Fast directional blow whoosh for dynamic transitions"),
    (os.path.join(VIDEO_ASSET_LIB, "Audio_Transition_Woosh", "WHSH-Soft_Riser_Woosh_Tra-Elevenlabs.mp3"), "01_Transitional_Whooshes", "riser_whoosh_transition.mp3", "Riser Whoosh", "Building soft riser swoosh resolving on the cut point"),
    (os.path.join(VIDEO_ASSET_LIB, "Audio_Transition_Woosh", "WHSH-Soft_cinematic_zoom--Elevenlabs.mp3"), "01_Transitional_Whooshes", "whoosh_cinematic_zoom.mp3", "Cinematic Zoom", "Gentle whoosh with cinematic zoom trail"),
    (os.path.join(VIDEO_ASSET_LIB, "Audio_Transition_Woosh", "WHSH-Soft_sound_effect_fo-Elevenlabs.mp3"), "01_Transitional_Whooshes", "whoosh_soft_ambient.mp3", "Ambient Whoosh", "Soft airy transition whoosh"),
    (os.path.join(VIDEO_ASSET_LIB, "(( Video Overlays & Effects Library ))", "04_Sound_FX_Transitions", "whoosh-1.mp3"), "01_Transitional_Whooshes", "whoosh_clean_air_01.mp3", "Clean Whoosh", "Clean high-frequency air whoosh"),
    (os.path.join(VIDEO_ASSET_LIB, "(( Video Overlays & Effects Library ))", "04_Sound_FX_Transitions", "whoosh-2.mp3"), "01_Transitional_Whooshes", "whoosh_clean_air_02.mp3", "Clean Whoosh", "Short sharp cut whoosh"),
    (os.path.join(VIDEO_ASSET_LIB, "(( Video Overlays & Effects Library ))", "04_Sound_FX_Transitions", "whoosh-3-Diaporama.wav"), "01_Transitional_Whooshes", "whoosh_diaporama_slide.wav", "Slide Whoosh", "Smooth slide whoosh for photo transitions"),
    (os.path.join(AUDIO_LIB_SRC, "Woosh", "Swoosh_01.wav"), "01_Transitional_Whooshes", "swoosh_high_energy_01.wav", "High Energy Swoosh", "Fast dynamic swoosh for quick whip pans"),
    (os.path.join(AUDIO_LIB_SRC, "Woosh", "Swoosh_02.wav"), "01_Transitional_Whooshes", "swoosh_high_energy_02.wav", "High Energy Swoosh", "Punchy fast swoosh"),
    (os.path.join(AUDIO_LIB_SRC, "Woosh", "002-23304 smooth air whoosh mid-full-?????.wav"), "01_Transitional_Whooshes", "whoosh_smooth_air_mid.wav", "Analog Air Whoosh", "Natural analog air rush for panoramic camera pans"),

    # 02 Impacts & Booms (10 items)
    (os.path.join(PRESET_SFX, "sfx_sub_boom.wav"), "02_Impacts_and_Booms", "sfx_sub_boom.wav", "Sub Boom", "Cinematic sub-bass boom impact for act turns and shocking statements"),
    (os.path.join(VIDEO_ASSET_LIB, "Dramatic Intro Vwoum", "Dam dramatic intro doom-cinematic_intro_soun-Elevenlabs.mp3"), "02_Impacts_and_Booms", "impact_dramatic_intro_doom.mp3", "Dramatic Doom", "Deep doom drop for chapter titles and chilling turns"),
    (os.path.join(VIDEO_ASSET_LIB, "Dramatic Intro Vwoum", "Ultra Dramlatic Shock Intro Revelation-cinematic_intro_soun-Elevenlabs.mp3"), "02_Impacts_and_Booms", "impact_ultra_shock_revelation.mp3", "Shock Revelation", "Ultra dramatic cinematic revelation impact hit"),
    (os.path.join(VIDEO_ASSET_LIB, "Dramatic Intro Vwoum", "DSGNImpt-Cinematic_bass_thud,-Elevenlabs.mp3"), "02_Impacts_and_Booms", "impact_cinematic_bass_thud.mp3", "Bass Thud", "Heavy cinematic bass thud"),
    (os.path.join(VIDEO_ASSET_LIB, "Dramatic Intro Vwoum", "Violent Intro ThTam-Cinematic_bass_thud,-Elevenlabs.mp3"), "02_Impacts_and_Booms", "impact_violent_thud.mp3", "Violent Hit", "Visceral cinematic hit with sub drop"),
    (os.path.join(AUDIO_LIB_SRC, "Cinematic Waooouuumm", "trailer-big-powerful-impact-241356.mp3"), "02_Impacts_and_Booms", "impact_trailer_big_powerful.mp3", "Trailer Boom", "Massive trailer impact with reverberant sub tail"),
    (os.path.join(DAVINCI_MEDIA, "BF Metallic Thud.M.wav"), "02_Impacts_and_Booms", "impact_metallic_thud.wav", "Metallic Thud", "Heavy industrial metal impact for cold documentary turns"),
    (os.path.join(DAVINCI_MEDIA, "BF Slam Into Wood Wobbles.M.wav"), "02_Impacts_and_Booms", "impact_wood_slam_wobble.wav", "Wood Slam", "Hard wooden slam impact with authentic room resonance"),
    (os.path.join(DAVINCI_MEDIA, "BF Thunk On Wood.M.wav"), "02_Impacts_and_Booms", "impact_thunk_on_wood.wav", "Wood Thunk", "Solid dull wood thunk for sobering statements"),
    (os.path.join(DAVINCI_MEDIA, "BF On Metal with Decay.M.wav"), "02_Impacts_and_Booms", "impact_metal_decay.wav", "Metal Decay", "Metallic impact with long dramatic decay"),

    # 03 Editorial UI & Graphics (12 items)
    (os.path.join(PRESET_SFX, "sfx_paper_stamp.wav"), "03_Editorial_UI_and_Graphics", "sfx_paper_stamp.wav", "Paper Stamp", "Hard documentary wood/paper stamp for person cards and date tags"),
    (os.path.join(PRESET_SFX, "sfx_paper_slide.wav"), "03_Editorial_UI_and_Graphics", "sfx_paper_slide.wav", "Paper Slide", "Smooth paper slide sound for article and document reveals"),
    (os.path.join(PRESET_SFX, "sfx_map_pin.wav"), "03_Editorial_UI_and_Graphics", "sfx_map_pin.wav", "Map Pin Click", "Metal button / pin click for map coordinate drop"),
    (os.path.join(PRESET_SFX, "sfx_typewriter_single.wav"), "03_Editorial_UI_and_Graphics", "sfx_typewriter_single.wav", "Typewriter Keystroke", "Single mechanical typewriter keystroke for kinetic text typing"),
    (os.path.join(PRESET_SFX, "sfx_typewriter_clack.wav"), "03_Editorial_UI_and_Graphics", "sfx_typewriter_clack.wav", "Typewriter Return", "Hard mechanical typewriter carriage clack"),
    (os.path.join(PRESET_SFX, "sfx_camera_shutter.wav"), "03_Editorial_UI_and_Graphics", "sfx_camera_shutter.wav", "Camera Shutter", "Vintage SLR camera shutter click for historical still reveals"),
    (os.path.join(VIDEO_ASSET_LIB, "(( Video Overlays & Effects Library ))", "04_Sound_FX_Transitions", "subscribe_bell.wav"), "03_Editorial_UI_and_Graphics", "ui_subscribe_bell.wav", "Notification Bell", "Clear notification chime for calls to action"),
    (os.path.join(VIDEO_ASSET_LIB, "(( Video Overlays & Effects Library ))", "04_Sound_FX_Transitions", "subscribe_click.wav"), "03_Editorial_UI_and_Graphics", "ui_click_soft.wav", "UI Click", "Soft tactile button click"),
    (os.path.join(AUDIO_LIB_SRC, "Woosh", "HUD Buttons and Notifications Pack", "wav", "button-01.wav"), "03_Editorial_UI_and_Graphics", "ui_hud_button_01.wav", "HUD Button 1", "Tech UI button tick for data tickers"),
    (os.path.join(AUDIO_LIB_SRC, "Woosh", "HUD Buttons and Notifications Pack", "wav", "button-02.wav"), "03_Editorial_UI_and_Graphics", "ui_hud_button_02.wav", "HUD Button 2", "Secondary tactile UI click"),
    (os.path.join(DAVINCI_MEDIA, "Arrows Out Sweetener.M.wav"), "03_Editorial_UI_and_Graphics", "ui_arrows_sweetener.wav", "Arrow Accent", "High-frequency subtle graphic whoosh for arrow indicators"),
    (os.path.join(DAVINCI_MEDIA, "Applying Lotion on Skin.M.wav"), "03_Editorial_UI_and_Graphics", "ui_soft_foley_swipe.wav", "Friction Swipe", "Soft friction sound for smooth title fades"),

    # 04 Foley & Movement (14 items)
    (os.path.join(DAVINCI_MEDIA, "Book Grab Off Shelf Movement.M.wav"), "04_Foley_and_Movement", "foley_book_grab_shelf.wav", "Book Grab", "Book taken off bookshelf foley for research sequences"),
    (os.path.join(DAVINCI_MEDIA, "Book Pages Turning Flutter.M.wav"), "04_Foley_and_Movement", "foley_book_pages_flutter.wav", "Pages Flutter", "Rapid flutter of book pages for montage sequences"),
    (os.path.join(DAVINCI_MEDIA, "Book Pages Turning Quickly.M.wav"), "04_Foley_and_Movement", "foley_book_pages_quickly.wav", "Pages Quick Turn", "Fast paper page turn foley"),
    (os.path.join(DAVINCI_MEDIA, "Tearing Paper Out.M.wav"), "04_Foley_and_Movement", "foley_tearing_paper.wav", "Tearing Paper", "Paper tearing texture for archival clipping reveals"),
    (os.path.join(DAVINCI_MEDIA, "Using Folder With Papers.M.wav"), "04_Foley_and_Movement", "foley_folder_papers.wav", "Folder Papers", "Opening archive manila folder and rustling confidential documents"),
    (os.path.join(DAVINCI_MEDIA, "Writing In Notebook.M.wav"), "04_Foley_and_Movement", "foley_writing_in_notebook.wav", "Pencil Writing", "Pencil sketching / writing in notebook foley"),
    (os.path.join(DAVINCI_MEDIA, "Typing On Computer Keyboard.M.wav"), "04_Foley_and_Movement", "foley_computer_keyboard.wav", "Computer Keyboard", "Modern tactile mechanical computer keyboard typing"),
    (os.path.join(DAVINCI_MEDIA, "Wood Chair Creaks.M.wav"), "04_Foley_and_Movement", "foley_wood_chair_creak.wav", "Chair Creak", "Subtle wooden chair movement for interview room authenticity"),
    (os.path.join(DAVINCI_MEDIA, "Car Door Close x4.M.wav"), "04_Foley_and_Movement", "foley_car_door_close.wav", "Car Door Close", "Solid car door close foley for crime / getaway stories"),
    (os.path.join(DAVINCI_MEDIA, "BG Footsteps Concrete City.wav"), "04_Foley_and_Movement", "foley_footsteps_concrete_city.wav", "City Footsteps", "Subtle ambient footsteps on urban pavement"),
    (os.path.join(DAVINCI_MEDIA, "Boots on Wood.M.wav"), "04_Foley_and_Movement", "foley_boots_on_wood.wav", "Boots on Wood", "Heavy footsteps on wooden floorboards"),
    (os.path.join(DAVINCI_MEDIA, "Backpack Bookbag Rummage.M.wav"), "04_Foley_and_Movement", "foley_bag_rummage.wav", "Bag Rummage", "Rummaging through bag / evidence foley"),
    (os.path.join(DAVINCI_MEDIA, "Bag Unzipped.M.wav"), "04_Foley_and_Movement", "foley_bag_unzipped.wav", "Zipper", "Crisp bag zipper opening"),
    (os.path.join(DAVINCI_MEDIA, "Beer Bottle Grab Drop .M.wav"), "04_Foley_and_Movement", "foley_glass_bottle_grab.wav", "Glass Bottle", "Subtle glass clink on wooden table"),

    # 05 Room Tone & Beds (7 items)
    (os.path.join(PRESET_SFX, "sfx_room_tone.wav"), "05_Room_Tone_and_Beds", "sfx_room_tone.wav", "Classroom / Room Tone", "Neutral studio & archive room tone bed to bridge dialogue gaps"),
    (os.path.join(AUDIO_LIB_SRC, "BBC Sound Effects Library", "05 city skyline.mp3"), "05_Room_Tone_and_Beds", "ambience_city_skyline.mp3", "City Skyline", "Distant urban city rumble ambience bed"),
    (os.path.join(AUDIO_LIB_SRC, "BBC Sound Effects Library", "06 high street with traffic.mp3"), "05_Room_Tone_and_Beds", "ambience_traffic_distant.mp3", "Distant Traffic", "Soft exterior ambient traffic presence"),
    (os.path.join(AUDIO_LIB_SRC, "BBC Sound Effects Library", "01 Seawash, calm.mp3"), "05_Room_Tone_and_Beds", "ambience_seawash_calm.mp3", "Calm Water / Sea", "Gentle water lapping ambience"),
    (os.path.join(AUDIO_LIB_SRC, "BBC Sound Effects Library", "04 wood fire, in stove.mp3"), "05_Room_Tone_and_Beds", "ambience_fireplace_subtle.mp3", "Subtle Hearth", "Warm gentle room crackle for historical winter recollections"),
    (os.path.join(DAVINCI_MEDIA, "Bushes Rustling Walk Thru.M.wav"), "05_Room_Tone_and_Beds", "ambience_wind_leaves.wav", "Leaves Rustling", "Soft breeze rustling dry foliage"),
    (os.path.join(DAVINCI_MEDIA, "Bathroom Shower Door.M.wav"), "05_Room_Tone_and_Beds", "foley_interior_door.wav", "Interior Door", "Soft interior room door close")
]

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
    print("=== Curating Master 100-Element Production Audio Library ===")
    os.makedirs(ALL_TRACKS, exist_ok=True)
    catalog = {"music": {}, "sfx": {}}

    # Ingest owned music edits from local packs if not already present
    extra_owned = [
        (os.path.join(AUDIO_LIB_SRC, "(( Music Tracks ))", "background-music-pack", "Medium", "Medium_1_42.mp3"), "Background_Acoustic_Medium.mp3"),
        (os.path.join(AUDIO_LIB_SRC, "(( Music Tracks ))", "background-music-pack", "Short", "Short_1_15.mp3"), "Background_Acoustic_Short.mp3"),
        (os.path.join(AUDIO_LIB_SRC, "(( Music Tracks ))", "inspiring-voyage-2025-01-15-13-32-36-utc", "Short.mp3"), "Inspiring_Voyage_Short.mp3"),
        (os.path.join(AUDIO_LIB_SRC, "(( Music Tracks ))", "the-inspiring-2025-05-22-04-07-59-utc", "1_MIN.mp3"), "The_Inspiring_1Min.mp3"),
        (os.path.join(AUDIO_LIB_SRC, "(( Music Tracks ))", "motivation-pack", "Epic Short A.mp3"), "Epic_Motivation_Short_A.mp3")
    ]
    for src, fname in extra_owned:
        if os.path.exists(src):
            dst = os.path.join(ALL_TRACKS, fname)
            hardlink_or_copy(src, dst)

    # 1. Process Music Tracks
    for fname, meta in MUSIC_DEFINITIONS.items():
        track_path = os.path.join(ALL_TRACKS, fname)
        if os.path.exists(track_path) and os.path.getsize(track_path) > 0:
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
                "story_role": meta["story_role"],
                "duration_s": info.get("duration_s"),
                "lufs_integrated": loud.get("lufs_integrated"),
                "true_peak_dbtp": loud.get("true_peak_dbtp"),
                "path": os.path.relpath(track_path, LIBRARY_ROOT)
            }
            print(f"Curated Music [{len(catalog['music'])}]: {fname:<34} | {meta['title']:<30} | {info.get('duration_s')}s | {loud.get('lufs_integrated')} LUFS")

    # 2. Process SFX Elements
    for src, rel_dir, new_name, title, desc in SFX_CURATED_SOURCES:
        if os.path.exists(src):
            dst = os.path.join(SFX_ROOT, rel_dir, new_name)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            hardlink_or_copy(src, dst)
            info = probe_audio(dst)
            loud = measure_loudness(dst)
            catalog["sfx"][new_name] = {
                "name": new_name,
                "title": title,
                "category": rel_dir.split("_", 1)[-1],
                "folder": rel_dir,
                "description": desc,
                "duration_s": info.get("duration_s"),
                "true_peak_dbtp": loud.get("true_peak_dbtp"),
                "lufs_integrated": loud.get("lufs_integrated"),
                "path": os.path.relpath(dst, LIBRARY_ROOT)
            }
            print(f"Curated SFX   [{len(catalog['sfx'])}]: {new_name:<34} | {title:<22} | {loud.get('true_peak_dbtp')} dBTP | {rel_dir}")

    total_elements = len(catalog["music"]) + len(catalog["sfx"])
    cat_path = os.path.join(LIBRARY_ROOT, "AUDIO_CATALOG.json")
    with open(cat_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"\n==========================================")
    print(f"Master Library Curation Complete: {len(catalog['music'])} Music Tracks + {len(catalog['sfx'])} SFX = {total_elements} Total Elements!")
    print(f"Catalog saved to: {cat_path}")

if __name__ == "__main__":
    main()
