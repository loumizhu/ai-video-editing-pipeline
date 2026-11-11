#!/usr/bin/env python
"""DaVinci Resolve Studio NLE cut builder and frame-exact verifier.

Connects directly to DaVinci Resolve Studio via the native scripting API.
Enforces the NLE cut contract:
  - Connection probe (--check) with clear user remediation instructions.
  - Refuses to write into any existing project; requires a fresh, named project.
  - Sets project timelineFrameRate before creating any timeline, asserting return value.
  - Rejects unsupported non-standard frame rates (no str(round()) fallback).
  - Requires fps_num/fps_den in cuts.json (no default), checks them against the source, and rejects segments
    past the source's last frame BEFORE any project is created.
  - Imports source media, asserts the clip's FPS matches planned FPS within 0.005 (23.976 vs 24 differ by 0.024).
  - Creates an empty timeline and uses ONE AppendToTimeline call to assemble segments back-to-back.
  - Reads back timeline items and verifies frame-for-frame on both V1 and A1.
  - Asserts contiguity (GetStart of cut n == GetEnd of cut n-1, starting at 01:00:00:00 = 86400).
  - On failure: deletes created timeline and outputs exact orphan project cleanup command.
  - Supports robust orphan project deletion across non-current projects (--delete-orphan / --delete-project).
  - Defaults build report path to alongside --cuts.
  - Prints reminder about setting Playback frame rate in Project Settings.

Usage:
  python build_cut_resolve.py --check
  python build_cut_resolve.py --cuts cuts.json --project-name zz_test_cut [--report report.json] [--delete-project]
  python build_cut_resolve.py --delete-orphan zz_test_cut
"""
import argparse
from fractions import Fraction
import json
import math
import os
import subprocess
import sys
import time

RESOLVE_API_DIR = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
RESOLVE_LIB_PATH = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"

SUPPORTED_FRAME_RATES = {
    (24000, 1001): "23.976",
    (24, 1): "24",
    (25, 1): "25",
    (30000, 1001): "29.97",
    (30, 1): "30",
    (48, 1): "48",
    (50, 1): "50",
    (60000, 1001): "59.94",
    (60, 1): "60",
}


def connect_resolve():
    """Connect to DaVinci Resolve Studio scripting API."""
    os.environ["RESOLVE_SCRIPT_API"] = RESOLVE_API_DIR
    os.environ["RESOLVE_SCRIPT_LIB"] = RESOLVE_LIB_PATH
    modules_path = os.path.join(RESOLVE_API_DIR, "Modules")
    if modules_path not in sys.path:
        sys.path.append(modules_path)

    try:
        import DaVinciResolveScript as d
        resolve = d.scriptapp("Resolve")
        if resolve:
            return resolve
    except Exception as exc:
        print(f"Resolve scripting import exception: {exc}", file=sys.stderr)

    return None


def print_connection_help():
    msg = (
        "\n"
        "========================================================================================\n"
        "[RESOLVE CONNECTION FAILED]\n"
        "Could not connect to DaVinci Resolve Studio scripting API.\n\n"
        "Required Actions:\n"
        "  1. Ensure DaVinci Resolve Studio (not free edition) is running.\n"
        "     Launch command: Start-Process 'C:\\Program Files\\Blackmagic Design\\DaVinci Resolve\\Resolve.exe'\n"
        "  2. In Resolve, verify external scripting is enabled:\n"
        "     DaVinci Resolve -> Preferences -> System -> General -> 'External scripting using' -> Local or Network.\n"
        "  3. Wait approximately 60 seconds after launch for Resolve's internal ScriptServer loopback socket to bind.\n"
        "  4. Check that Python 3.10-3.13 is installed and matches Resolve architecture.\n"
        "========================================================================================\n"
    )
    print(msg, file=sys.stderr)


def delete_project_cleanly(pm, project_name):
    """Safely close and delete a test project, whether current or non-current (Fix 9)."""
    curr = pm.GetCurrentProject()
    if curr and curr.GetName() == project_name:
        pm.CloseProject(curr)
        time.sleep(0.5)
    else:
        # Load, save, close sequence releases internal database locks
        proj = pm.LoadProject(project_name)
        if proj:
            pm.SaveProject()
            pm.CloseProject(proj)
            time.sleep(0.5)

    for attempt in range(5):
        if pm.DeleteProject(project_name):
            return True
        time.sleep(0.5)
    return False


def validate_cuts(cuts_data):
    """Validate internal cuts.json consistency (Fix 8)."""
    segments = cuts_data.get("segments", [])
    if not segments:
        raise ValueError("No segments in cuts.json to place.")
    for idx, seg in enumerate(segments):
        sf = seg.get("start_frame")
        ef = seg.get("end_frame")
        df = seg.get("dur_frames")
        if sf is None or ef is None or df is None:
            raise ValueError(f"Segment #{idx+1} missing frame boundary fields (start_frame, end_frame, dur_frames)")
        if df != (ef - sf):
            raise ValueError(
                f"Segment #{idx+1} internal inconsistency: dur_frames ({df}) != end_frame ({ef}) - start_frame ({sf})"
            )
        if df <= 0:
            raise ValueError(f"Segment #{idx+1} has non-positive duration: {df} frames")
        if idx > 0:
            prev_ef = segments[idx - 1]["end_frame"]
            if sf < prev_ef:
                raise ValueError(
                    f"Segment #{idx+1} source start_frame ({sf}) is before previous segment end_frame ({prev_ef}) (non-monotonic/overlapping source order)"
                )


def require_fps(cuts_data):
    """fps_num/fps_den are mandatory in cuts.json: a silent default corrupts every frame position."""
    fn, fd = cuts_data.get("fps_num"), cuts_data.get("fps_den")
    if not isinstance(fn, int) or not isinstance(fd, int) or fn <= 0 or fd <= 0:
        raise ValueError(f"cuts.json has no valid fps_num/fps_den (got {fn!r}/{fd!r}); refusing to guess a frame rate")
    return Fraction(fn, fd)


def probe_source_frames(source_path):
    """ffprobe the source video. Returns (frame_count, fps Fraction). No default fps: raises if unreadable."""
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate,nb_frames,duration", "-show_entries", "format=duration",
        "-of", "json", source_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise ValueError(f"ffprobe failed for '{source_path}': {proc.stderr.strip()}")
    data = json.loads(proc.stdout)
    streams = data.get("streams") or []
    if not streams:
        raise ValueError(f"No video stream in '{source_path}'")
    st = streams[0]
    rate = st.get("r_frame_rate")
    if not rate or "/" not in rate or rate.startswith("0/"):
        raise ValueError(f"Source '{source_path}' reports no usable r_frame_rate ({rate!r})")
    num, den = map(int, rate.split("/"))
    fps = Fraction(num, den)
    nb = st.get("nb_frames")
    if nb and nb != "N/A":
        frames = int(nb)
    else:
        dur = float(st.get("duration") or data.get("format", {}).get("duration") or 0.0)
        frames = math.floor(dur * fps)
    return frames, fps


def check_against_source(segments, fps, source_path):
    """Reject a cut list whose frame rate differs from the source or whose segments run past the source's last frame."""
    frames, src_fps = probe_source_frames(source_path)
    if src_fps != fps:
        raise ValueError(f"cuts.json fps {fps} != source fps {src_fps} ({source_path})")
    for idx, seg in enumerate(segments):
        if seg["end_frame"] > frames:
            raise ValueError(
                f"Segment #{idx+1} end_frame {seg['end_frame']} is past the source's {frames} frames "
                f"(valid exclusive end <= {frames})"
            )
    return frames


def map_resolve_rate(fps_ratio):
    """Map rational fps to Resolve supported rate string, or raise ValueError (Fix 10)."""
    fps_float = float(fps_ratio)
    for (num, den), rate_str in SUPPORTED_FRAME_RATES.items():
        if abs(fps_float - (float(num) / float(den))) < 0.005:
            return rate_str
    raise ValueError(
        f"Unsupported fps {fps_ratio} ({fps_float:.4f}). DaVinci Resolve requires standard frame rates: "
        f"{list(SUPPORTED_FRAME_RATES.values())}"
    )


def main():
    ap = argparse.ArgumentParser(description="DaVinci Resolve Studio cut builder and frame verifier.")
    ap.add_argument("--check", action="store_true", help="Probe Resolve connection and exit")
    ap.add_argument("--cuts", help="Input cuts.json")
    ap.add_argument("--project-name", help="Name for NEW Resolve project (refuses existing projects)")
    ap.add_argument("--timeline-name", default="Cut_Timeline", help="Timeline name (default: Cut_Timeline)")
    ap.add_argument("--report", help="Output build report JSON (default: alongside --cuts)")
    ap.add_argument("--media", help="Optional override for source video path")
    ap.add_argument("--delete-project", action="store_true", help="Delete the test project after successful verification")
    ap.add_argument("--delete-orphan", help="Safely delete a named orphan project and exit")

    args = ap.parse_args()

    resolve = connect_resolve()
    if not resolve:
        print_connection_help()
        sys.exit(1)

    pm = resolve.GetProjectManager()
    product_name = resolve.GetProductName()
    version_str = resolve.GetVersionString()

    if args.check:
        print(f"CONNECTED: {product_name} {version_str} (Scripting API verified)")
        return

    if args.delete_orphan:
        ok = delete_project_cleanly(pm, args.delete_orphan)
        if ok:
            print(f"Orphan project '{args.delete_orphan}' cleanly deleted from Resolve.")
            return
        else:
            sys.exit(f"Failed to delete orphan project '{args.delete_orphan}' from Resolve.")

    if not args.cuts or not args.project_name:
        ap.error("--cuts and --project-name are required unless --check or --delete-orphan is specified.")

    existing_projects = pm.GetProjectListInCurrentFolder() or []
    if args.project_name in existing_projects:
        sys.exit(
            f"ERROR: Project '{args.project_name}' already exists! "
            f"Per safety rules, build_cut_resolve.py refuses to write into existing projects. "
            f"Choose a new project name or delete with: python build_cut_resolve.py --delete-orphan {args.project_name}"
        )

    with open(args.cuts, "r", encoding="utf-8") as f:
        cuts_data = json.load(f)

    # Validate cuts.json contract up front (Fix 8)
    try:
        validate_cuts(cuts_data)
    except ValueError as e:
        sys.exit(f"Invalid cuts.json: {e}")

    source_path = os.path.abspath(args.media or cuts_data.get("source"))
    if not os.path.exists(source_path):
        sys.exit(f"Source media not found: {source_path}")

    segments = cuts_data["segments"]
    try:
        fps_ratio = require_fps(cuts_data)
        check_against_source(segments, fps_ratio, source_path)
    except ValueError as e:
        sys.exit(f"Invalid cuts.json: {e}")

    # Rate setting mapping with strict validation (Fix 10)
    try:
        rate_setting = map_resolve_rate(fps_ratio)
    except ValueError as e:
        sys.exit(f"Frame rate error: {e}")

    # 1. Create fresh project
    proj = pm.CreateProject(args.project_name)
    if not proj:
        sys.exit(f"Failed to create project '{args.project_name}' in Resolve.")

    timeline = None
    mp = None
    created_timeline = False

    try:
        # 2. Set timeline frame rate before creating any timeline (Fix 10: assert return value)
        set_ok = proj.SetSetting("timelineFrameRate", rate_setting)
        if not set_ok:
            raise RuntimeError(f"proj.SetSetting('timelineFrameRate', '{rate_setting}') returned False!")

        # 3. Import media into Media Pool
        mp = proj.GetMediaPool()
        items = mp.ImportMedia([source_path])
        if not items:
            raise RuntimeError(f"Failed to import media '{source_path}' into Resolve Media Pool.")
        clip = items[0]

        # Fix 10: Assert clip FPS read-back matches expected rate
        clip_fps = str(clip.GetClipProperty("FPS"))
        clip_fps_float = float(clip_fps) if clip_fps else 0.0
        if abs(clip_fps_float - float(fps_ratio)) > 0.005:
            raise RuntimeError(
                f"Imported clip FPS ({clip_fps}) does not match cuts.json FPS {fps_ratio} ({float(fps_ratio):.3f})"
            )

        # 4. Create empty timeline
        timeline = mp.CreateEmptyTimeline(args.timeline_name)
        if not timeline:
            raise RuntimeError("Failed to create empty timeline in Resolve.")
        created_timeline = True

        # 5. Build ONE AppendToTimeline list
        clip_infos = []
        for seg in segments:
            clip_infos.append(
                {
                    "mediaPoolItem": clip,
                    "startFrame": seg["start_frame"],
                    "endFrame": seg["end_frame"],
                }
            )

        append_result = mp.AppendToTimeline(clip_infos)
        if not append_result:
            raise RuntimeError("MediaPool.AppendToTimeline returned no items.")

        # 6. Read back and verify frame for frame on V1 and A1 (Fix 10)
        v_items = timeline.GetItemListInTrack("video", 1) or []
        a_items = timeline.GetItemListInTrack("audio", 1) or []

        planned_total_frames = sum(s["dur_frames"] for s in segments)
        landed_v_frames = sum(it.GetDuration() for it in v_items)
        landed_a_frames = sum(it.GetDuration() for it in a_items)

        mismatches = []
        comparison_table = []

        if len(v_items) != len(segments):
            mismatches.append(f"V1 clip count mismatch: planned {len(segments)}, landed {len(v_items)}")
        if len(a_items) != len(segments):
            mismatches.append(f"A1 clip count mismatch: planned {len(segments)}, landed {len(a_items)}")

        # Verification of clips and contiguity (Fix 10)
        # In Resolve default timeline timecode starts at 01:00:00:00 = 86400 frames
        RESOLVE_TIMELINE_START_FRAME = 86400
        prev_end_frame = RESOLVE_TIMELINE_START_FRAME

        for idx, seg in enumerate(segments):
            planned_dur = seg["dur_frames"]
            planned_src_in = seg["start_frame"]

            v_item = v_items[idx] if idx < len(v_items) else None
            a_item = a_items[idx] if idx < len(a_items) else None

            v_dur = v_item.GetDuration() if v_item else None
            v_src_in = v_item.GetLeftOffset() if v_item else None
            v_start = v_item.GetStart() if v_item else None
            v_end = v_item.GetEnd() if v_item else None

            a_dur = a_item.GetDuration() if a_item else None
            a_start = a_item.GetStart() if a_item else None
            a_end = a_item.GetEnd() if a_item else None

            # Video match
            v_match = (v_dur == planned_dur) and (v_src_in == planned_src_in)
            # Audio match (Fix 10)
            a_match = (a_dur == planned_dur) and (a_start == v_start) and (a_end == v_end)

            # Contiguity match (Fix 10): GetStart of cut n == GetEnd of cut n-1 (first at 86400)
            if idx == 0:
                contiguity_match = (v_start == RESOLVE_TIMELINE_START_FRAME)
                if not contiguity_match:
                    mismatches.append(
                        f"First cut does not start at 01:00:00:00 (86400): landed start is {v_start}"
                    )
            else:
                contiguity_match = (v_start == prev_end_frame)
                if not contiguity_match:
                    mismatches.append(
                        f"Contiguity broken at Cut #{idx+1}: GetStart ({v_start}) != previous GetEnd ({prev_end_frame})"
                    )

            if not v_match:
                mismatches.append(
                    f"V1 Cut #{idx+1} mismatch: planned dur={planned_dur} srcIn={planned_src_in}, "
                    f"landed dur={v_dur} srcIn={v_src_in}"
                )
            if not a_match:
                mismatches.append(
                    f"A1 Cut #{idx+1} mismatch: planned dur={planned_dur}, landed dur={a_dur}"
                )

            comparison_table.append(
                {
                    "cut": idx + 1,
                    "planned_frames": planned_dur,
                    "landed_v_frames": v_dur,
                    "landed_a_frames": a_dur,
                    "planned_src_in": planned_src_in,
                    "landed_src_in": v_src_in,
                    "timeline_start": v_start,
                    "timeline_end": v_end,
                    "v_match": v_match,
                    "a_match": a_match,
                    "contiguous": contiguity_match,
                }
            )
            if v_end is not None:
                prev_end_frame = v_end

        exact_match = (
            (len(mismatches) == 0)
            and (landed_v_frames == planned_total_frames)
            and (landed_a_frames == planned_total_frames)
        )

        report = {
            "nle": "DaVinci Resolve Studio",
            "resolve_version": f"{product_name} {version_str}",
            "project_name": args.project_name,
            "timeline_name": args.timeline_name,
            "source": source_path,
            "clip_fps": clip_fps,
            "timeline_frame_rate_setting": rate_setting,
            "planned_clip_count": len(segments),
            "landed_v_clip_count": len(v_items),
            "landed_a_clip_count": len(a_items),
            "planned_total_frames": planned_total_frames,
            "landed_v_total_frames": landed_v_frames,
            "landed_a_total_frames": landed_a_frames,
            "exact_match": exact_match,
            "mismatches": mismatches,
            "clips": comparison_table,
            "playback_fps_reminder": "Playback frame rate cannot be set by scripting; set it manually in Project Settings to match timeline frame rate.",
        }

        # Fix 11: Default report path alongside --cuts
        default_report = os.path.splitext(os.path.abspath(args.cuts))[0] + "_resolve_build_report.json"
        report_path = args.report or default_report
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        if not exact_match:
            # Delete failed timeline (Fix 9)
            if created_timeline and timeline and mp:
                mp.DeleteTimelines([timeline])
            print(f"FAILED: DaVinci Resolve timeline mismatch: {mismatches}", file=sys.stderr)
            print(
                f"CLEANUP ADVICE: An orphan project '{args.project_name}' was created.\n"
                f"To remove it cleanly, run: python build_cut_resolve.py --delete-orphan {args.project_name}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Save project
        pm.SaveProject()

        print(
            f"DaVinci Resolve build VERIFIED: {len(v_items)} clips, V1/A1 {landed_v_frames} frames (0 drift) "
            f"in project '{args.project_name}' (report: {report_path})"
        )
        print("REMINDER: Verify Playback frame rate in DaVinci Resolve Project Settings matches your timeline frame rate.")

    except Exception as exc:
        # Delete timeline on failure (Fix 9)
        if created_timeline and timeline and mp:
            try:
                mp.DeleteTimelines([timeline])
            except Exception:
                pass
        print(f"Exception during Resolve build: {exc}", file=sys.stderr)
        print(
            f"CLEANUP ADVICE: An orphan project '{args.project_name}' was created.\n"
            f"To remove it cleanly, run: python build_cut_resolve.py --delete-orphan {args.project_name}",
            file=sys.stderr,
        )
        sys.exit(1)

    finally:
        if args.delete_project:
            del_ok = delete_project_cleanly(pm, args.project_name)
            print(f"Deleted test project '{args.project_name}': {del_ok}")


if __name__ == "__main__":
    main()
