"""Zero-Copy Audio Asset Linking & Management Tool for AI Video Editing Pipeline.

Provides production-hardened, zero-copy NTFS directory junctions and hardlinks between
the central library:
  E:\\((Video_Editing_Asset_Library))\\(( Production Audio Library ))
and individual project folders (e.g. Ytube_Channel\\Videos-Scripts\\<Video>\\07_Video_Edit\\Full_Edit_v1\\music).

Key Capabilities:
  1. link: Zero-copy link central library tracks or SFX into a project folder (junction or atomic hardlink).
  2. deduplicate: Audit project folders, identify true byte-for-byte duplicate copies of library tracks,
     and replace them with zero-cost NTFS hardlinks. Dry-run by default; requires --apply.
  3. catalog: Query library tracks by mood, tempo, energy, and story arc.
  4. audit: Check library integrity, hardlink counts, inode sharing, and catalog health.
"""

import argparse
import filecmp
import hashlib
import json
import os
import shutil
import subprocess
import sys

LIBRARY_ROOT = r"E:\((Video_Editing_Asset_Library))\(( Production Audio Library ))"
MUSIC_ROOT = os.path.join(LIBRARY_ROOT, "01_Music")
SFX_ROOT = os.path.join(LIBRARY_ROOT, "02_SFX")
ALL_TRACKS = os.path.join(MUSIC_ROOT, "All_Tracks")
CATALOG_PATH = os.path.join(LIBRARY_ROOT, "AUDIO_CATALOG.json")


def load_catalog():
    if os.path.exists(CATALOG_PATH):
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"music": {}, "sfx": {}}


def is_same_drive(p1, p2):
    return os.path.splitdrive(os.path.abspath(p1))[0].lower() == os.path.splitdrive(os.path.abspath(p2))[0].lower()


def is_same_inode(p1, p2):
    """Check if two file paths point to the exact same NTFS MFT inode."""
    try:
        s1 = os.stat(p1)
        s2 = os.stat(p2)
        return (s1.st_ino, s1.st_dev) == (s2.st_ino, s2.st_dev)
    except Exception:
        return False


def files_are_identical(p1, p2):
    """Verify that two files are identical in content before replacing."""
    if not os.path.exists(p1) or not os.path.exists(p2):
        return False
    if is_same_inode(p1, p2):
        return True
    if os.path.getsize(p1) != os.path.getsize(p2):
        return False
    return filecmp.cmp(p1, p2, shallow=False)


def create_junction(src_dir, dst_junction):
    """Create an NTFS directory junction safely without requiring administrator privileges."""
    src_abs = os.path.abspath(src_dir)
    dst_abs = os.path.abspath(dst_junction)

    if not os.path.isdir(src_abs):
        raise FileNotFoundError(f"Source directory does not exist: {src_abs}")

    if not is_same_drive(src_abs, dst_abs):
        raise ValueError(f"Cross-drive junctions not recommended. Src: {src_abs}, Dst: {dst_abs}")

    if os.path.exists(dst_abs):
        # Python 3.12+ os.path.isjunction
        is_junc = getattr(os.path, "isjunction", None)
        if is_junc and is_junc(dst_abs):
            os.unlink(dst_abs)
        elif os.path.islink(dst_abs):
            os.unlink(dst_abs)
        else:
            raise FileExistsError(
                f"Destination exists and is a real directory (not a junction): {dst_abs}. "
                f"Refusing to delete real user data to create junction."
            )

    cmd = ["cmd", "/c", "mklink", "/J", dst_abs, src_abs]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"Failed to create junction: {r.stderr or r.stdout}")
    return dst_abs


def create_hardlink(src_file, dst_file):
    """Create an NTFS hardlink atomically with zero data loss risk."""
    src_abs = os.path.abspath(src_file)
    dst_abs = os.path.abspath(dst_file)

    if not os.path.exists(src_abs):
        raise FileNotFoundError(f"Source master file does not exist: {src_abs}")

    if not is_same_drive(src_abs, dst_abs):
        raise ValueError(f"Cannot hardlink across different drives: {src_abs} and {dst_abs}")

    os.makedirs(os.path.dirname(dst_abs), exist_ok=True)

    if os.path.exists(dst_abs):
        if is_same_inode(src_abs, dst_abs):
            return "already_linked"
        # If destination exists and differs, verify content
        if not files_are_identical(src_abs, dst_abs):
            raise FileExistsError(
                f"Destination file exists with differing content: {dst_abs}. "
                f"Refusing to overwrite to prevent project data loss."
            )

    # Atomic link: link to temporary file, then atomic os.replace
    tmp_dst = dst_abs + ".tmp_hlink"
    if os.path.exists(tmp_dst):
        try:
            os.remove(tmp_dst)
        except Exception:
            pass

    os.link(src_abs, tmp_dst)
    os.replace(tmp_dst, dst_abs)
    return "created"


def link_project(project_path, mode="hardlink", mood=None, tracks=None, sfx_category=None):
    """Link central audio into a project folder using zero-copy links."""
    project_abs = os.path.abspath(project_path)

    if sfx_category:
        target_dir = os.path.join(project_abs, "07_Video_Edit", "Full_Edit_v1", "sfx")
        if not os.path.exists(os.path.join(project_abs, "07_Video_Edit")):
            target_dir = project_abs if os.path.basename(project_abs) == "sfx" else os.path.join(project_abs, "sfx")
        print(f"Target Project SFX Directory: {target_dir}")
        os.makedirs(target_dir, exist_ok=True)
        sfx_src = os.path.join(SFX_ROOT, sfx_category)
        if not os.path.exists(sfx_src):
            raise FileNotFoundError(f"SFX category folder not found: {sfx_src}")
        for f in os.listdir(sfx_src):
            if f.lower().endswith((".wav", ".mp3", ".ogg")):
                src = os.path.join(sfx_src, f)
                dst = os.path.join(target_dir, f)
                st = create_hardlink(src, dst)
                print(f"  [{st}] SFX {f}")
        return

    music_dir = os.path.join(project_abs, "07_Video_Edit", "Full_Edit_v1", "music")
    if not os.path.exists(os.path.join(project_abs, "07_Video_Edit")):
        if os.path.basename(project_abs) == "music":
            music_dir = project_abs
        else:
            music_dir = os.path.join(project_abs, "music")

    print(f"Target Project Music Directory: {music_dir}")
    print(f"Mode: {mode}")

    if mode == "junction":
        source_dir = ALL_TRACKS if not mood else os.path.join(MUSIC_ROOT, mood)
        if not os.path.exists(source_dir):
            raise FileNotFoundError(f"Source directory not found: {source_dir}")
        create_junction(source_dir, music_dir)
        print(f"Junction established: {music_dir} -> {source_dir} (0 bytes used)")
        return

    os.makedirs(music_dir, exist_ok=True)
    catalog = load_catalog()
    track_pool = []

    if tracks:
        for t in tracks:
            found = None
            for fname, meta in catalog.get("music", {}).items():
                if t.lower() in [fname.lower(), meta.get("title", "").lower()]:
                    found = fname
                    break
            if found:
                track_pool.append(found)
            else:
                direct_path = os.path.join(ALL_TRACKS, t)
                if os.path.exists(direct_path):
                    track_pool.append(t)
                else:
                    print(f"Warning: Track '{t}' not found in catalog or All_Tracks.")
    elif mood:
        mood_dir = os.path.join(MUSIC_ROOT, mood)
        if os.path.exists(mood_dir):
            track_pool = os.listdir(mood_dir)
    else:
        track_pool = os.listdir(ALL_TRACKS)

    linked_count = 0
    for t in sorted(track_pool):
        src = os.path.join(ALL_TRACKS, t)
        if not os.path.exists(src):
            continue
        dst = os.path.join(music_dir, t)
        status = create_hardlink(src, dst)
        linked_count += 1
        print(f"  [{status}] {t}")

    print(f"Completed! {linked_count} tracks zero-copy linked to {music_dir} (0 bytes used).")


def deduplicate_projects(root_dir, apply=False):
    """Find duplicated audio files across video projects and replace them with zero-cost NTFS hardlinks.
    
    Dry run by default. Use --apply to execute link replacements safely.
    """
    print(f"=== Audio Deduplication & Space Reclamation ===")
    print(f"Root: {root_dir}")
    print(f"Mode: {'APPLY (replacing duplicates with hardlinks)' if apply else 'DRY RUN (scan only; use --apply to execute)'}\n")

    library_files = {}
    for root, _, files in os.walk(LIBRARY_ROOT):
        for f in files:
            if f.lower().endswith((".mp3", ".wav", ".aac", ".ogg", ".flac", ".m4a")):
                full_p = os.path.join(root, f)
                library_files[f.lower()] = full_p

    total_files_scanned = 0
    total_duplicates = 0
    bytes_reclaimed = 0
    already_linked_count = 0

    for root, dirs, files in os.walk(root_dir):
        if os.path.basename(root).lower() in ["music", "sfx", "audio"]:
            for f in files:
                if f.lower().endswith((".mp3", ".wav", ".aac", ".ogg", ".flac")):
                    total_files_scanned += 1
                    project_file = os.path.join(root, f)
                    lib_match = library_files.get(f.lower())

                    if lib_match and os.path.exists(lib_match):
                        if is_same_inode(project_file, lib_match):
                            already_linked_count += 1
                            continue

                        # Strict byte-level content verification
                        if files_are_identical(lib_match, project_file):
                            sz_proj = os.path.getsize(project_file)
                            total_duplicates += 1
                            bytes_reclaimed += sz_proj
                            rel_p = os.path.relpath(project_file, root_dir)
                            print(f"[DUPLICATE VERIFIED] {rel_p} ({sz_proj / (1024*1024):.2f} MB)")
                            if apply:
                                # Safe atomic link
                                tmp_dst = project_file + ".tmp_dedup"
                                os.link(lib_match, tmp_dst)
                                os.replace(tmp_dst, project_file)
                                print(f"  -> Atomically replaced with zero-cost hardlink to central library!")
                        else:
                            rel_p = os.path.relpath(project_file, root_dir)
                            print(f"[SKIPPED - CONTENT DIFFERS] {rel_p} shares name with library but differs in bytes.")

    mb_saved = bytes_reclaimed / (1024 * 1024)
    print(f"\nSummary:")
    print(f"  Files Scanned: {total_files_scanned}")
    print(f"  Already Zero-Cost Linked: {already_linked_count}")
    print(f"  Duplicates Identified: {total_duplicates}")
    print(f"  Disk Space {'Reclaimed' if apply else 'Reclaimable'}: {mb_saved:.2f} MB ({bytes_reclaimed:,} bytes)")


def audit_library():
    """Verify library integrity, NTFS inode synchronization, and catalog completeness."""
    print(f"=== Central Production Audio Library Audit ===")
    print(f"Library Root: {LIBRARY_ROOT}\n")

    catalog = load_catalog()
    music_cat = catalog.get("music", {})
    sfx_cat = catalog.get("sfx", {})

    print(f"Catalog counts: {len(music_cat)} music entries, {len(sfx_cat)} SFX entries.\n")

    all_tracks_files = {}
    if os.path.exists(ALL_TRACKS):
        for f in os.listdir(ALL_TRACKS):
            p = os.path.join(ALL_TRACKS, f)
            if os.path.isfile(p):
                st = os.stat(p)
                all_tracks_files[f.lower()] = (p, st.st_ino, st.st_nlink)

    print(f"All_Tracks master count: {len(all_tracks_files)}")

    # Verify mood folders are hardlinks to All_Tracks
    broken_links = 0
    unmatched_inodes = 0
    for mood_dir in os.listdir(MUSIC_ROOT):
        p_mood = os.path.join(MUSIC_ROOT, mood_dir)
        if os.path.isdir(p_mood) and mood_dir.lower() != "all_tracks":
            for f in os.listdir(p_mood):
                pf = os.path.join(p_mood, f)
                if os.path.isfile(pf):
                    st = os.stat(pf)
                    master = all_tracks_files.get(f.lower())
                    if not master:
                        print(f"[ORPHAN] {pf} is in mood '{mood_dir}' but not in All_Tracks!")
                        broken_links += 1
                    elif master[1] != st.st_ino:
                        print(f"[INODE MISMATCH] {pf} is a duplicate copy, not a hardlink to All_Tracks!")
                        unmatched_inodes += 1

    print(f"\nIntegrity Check Results:")
    print(f"  Broken / Orphan Links: {broken_links}")
    print(f"  Unmatched Inodes in Moods: {unmatched_inodes}")
    print(f"  Status: {'PASSED - 100% Zero-Copy Integrity' if broken_links == 0 and unmatched_inodes == 0 else 'ACTION REQUIRED'}")


def list_catalog(mood_filter=None):
    """Print the library catalog categorized by narrative moods."""
    cat = load_catalog()
    music = cat.get("music", {})
    sfx = cat.get("sfx", {})

    print(f"=== Central Production Audio Library Catalog ===")
    print(f"Location: {LIBRARY_ROOT}\n")

    print(f"--- MUSIC TRACKS ({len(music)} Available) ---")
    by_mood = {}
    for fname, data in sorted(music.items()):
        moods = data.get("moods", ["Uncategorized"])
        for m in moods:
            by_mood.setdefault(m, []).append((fname, data))

    for m, track_list in sorted(by_mood.items()):
        if mood_filter and mood_filter.lower() not in m.lower():
            continue
        print(f"\n[MOOD: {m}] ({len(track_list)} tracks)")
        for fname, d in track_list:
            dur = f"{int(d.get('duration_s', 0)//60)}m{int(d.get('duration_s', 0)%60):02d}s"
            lufs = f"{d.get('lufs_integrated')} LUFS" if d.get('lufs_integrated') is not None else "N/A"
            print(f"  - {d.get('title', fname):<30} | {fname:<32} | {dur:<6} | {lufs:<10} | {d.get('artist')}")

    print(f"\n--- SOUND EFFECTS ({len(sfx)} Available) ---")
    by_folder = {}
    for fname, data in sorted(sfx.items()):
        fld = data.get("folder", "General")
        by_folder.setdefault(fld, []).append((fname, data))

    for fld, sfx_list in sorted(by_folder.items()):
        print(f"\n[CATEGORY: {fld}] ({len(sfx_list)} items)")
        for fname, d in sfx_list:
            tp = f"{d.get('true_peak_dbtp')} dBTP" if d.get('true_peak_dbtp') is not None else "N/A"
            dur = f"{d.get('duration_s', 0):.2f}s"
            print(f"  - {fname:<32} | {dur:<6} | {tp:<10} | {d.get('description', '')}")


def main():
    parser = argparse.ArgumentParser(description="Zero-Copy Audio Asset Linking & Management Tool")
    subparsers = parser.add_subparsers(dest="command")

    # link
    p_link = subparsers.add_parser("link", help="Link audio tracks or SFX into a project folder")
    p_link.add_argument("--project", "-p", required=True, help="Target project directory")
    p_link.add_argument("--mode", "-m", choices=["hardlink", "junction"], default="hardlink", help="Link mode")
    p_link.add_argument("--mood", help="Filter music by specific narrative mood")
    p_link.add_argument("--sfx", help="Link a specific SFX category into project sfx folder")
    p_link.add_argument("--tracks", "-t", nargs="+", help="Specific track names or titles to link")

    # deduplicate
    p_dedup = subparsers.add_parser("deduplicate", help="Audit and replace duplicate project files with hardlinks")
    p_dedup.add_argument("--root", "-r", default=".", help="Root directory of projects (default: current working directory)")
    p_dedup.add_argument("--apply", action="store_true", help="Execute hardlink replacement (default is dry run)")

    # audit
    subparsers.add_parser("audit", help="Audit library zero-copy integrity and catalog health")

    # catalog
    p_cat = subparsers.add_parser("catalog", help="List audio catalog")
    p_cat.add_argument("--mood", help="Filter catalog by mood")

    args = parser.parse_args()
    if args.command == "link":
        link_project(args.project, mode=args.mode, mood=args.mood, tracks=args.tracks, sfx_category=args.sfx)
    elif args.command == "deduplicate":
        deduplicate_projects(args.root, apply=args.apply)
    elif args.command == "audit":
        audit_library()
    elif args.command == "catalog":
        list_catalog(args.mood)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
