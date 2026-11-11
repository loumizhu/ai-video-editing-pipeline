#!/usr/bin/env python
"""FilmCraft NLE cut builder and frame-exact verifier with professional timeline organization.

Builds a fresh FilmCraft project (.fcproj) from cuts.json, placing each segment
back-to-back on V1 and A1 via a single run JSONL, then inspects the active sequence
and verifies clip count, per-clip frames, and total frames against cuts.json.

Professional Organization:
  - 7-Tier NLE Bin Structure: 01_Footage, 02_Audio, 03_B-Roll, 04_Graphics, 05_SFX, 06_Music, 07_Sequences
  - 4V / 4A Multi-track sequence with labeled, color-coded tracks (timeline.setTrack)
  - Color-coded clips by editorial role (edit.label: Forest/Dialogue for primary speech)
  - Timeline markers & chapter points (markers.add, markers.addChapter) with notes
  - Project notes and metadata (project.setNotes)

Exits 0 on exact match, non-zero on any frame drift or mismatch.
Writes build_report.json.

Usage:
  python build_cut_filmcraft.py --cuts cuts.json --out project.fcproj [--report build_report.json] [--captions]
"""
import argparse
from fractions import Fraction
import json
import math
import os
import shutil
import subprocess
import sys

TICKS_PER_SEC = 254016000000
DEFAULT_CLI = r"C:\Program Files\FilmCraft\filmcraft-cli.exe"

STANDARD_BINS = [
    "01_Footage",
    "02_Audio",
    "03_B-Roll",
    "04_Graphics",
    "05_SFX",
    "06_Music",
    "07_Sequences",
]

TRACK_CONFIGS = [
    ("V1", "V1 - Primary / A-Roll", "Forest"),
    ("V2", "V2 - B-Roll / Inserts", "Cerulean"),
    ("V3", "V3 - Graphics / Titles", "Mango"),
    ("V4", "V4 - Overlays / Grain", "Lavender"),
    ("A1", "A1 - Dialogue / Sync", "Forest"),
    ("A2", "A2 - Sound Effects (SFX)", "Rose"),
    ("A3", "A3 - Music Bed", "Violet"),
    ("A4", "A4 - Ambience / Scratch", "Tan"),
]


def find_cli(custom_path=None):
    if custom_path and os.path.exists(custom_path):
        return custom_path
    if shutil.which("filmcraft-cli"):
        return "filmcraft-cli"
    if os.path.exists(DEFAULT_CLI):
        return DEFAULT_CLI
    raise FileNotFoundError("FilmCraft CLI binary not found. Set --cli or add filmcraft-cli to PATH.")


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


def probe_source(source_path):
    """Retrieve width, height, and rational fps from source video."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,avg_frame_rate",
        "-of",
        "json",
        source_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    stream = json.loads(proc.stdout)["streams"][0]
    w = int(stream["width"])
    h = int(stream["height"])
    r_fps = stream.get("r_frame_rate")
    if not r_fps or "/" not in r_fps or r_fps.startswith("0/"):
        raise SystemExit(f"Source '{source_path}' reports no usable r_frame_rate ({r_fps!r}); refusing to guess")
    num, den = map(int, r_fps.split("/"))
    fps_ratio = Fraction(num, den)
    return w, h, fps_ratio, float(fps_ratio)


def main():
    ap = argparse.ArgumentParser(description="Build and verify frame-accurate, professionally organized timeline in FilmCraft.")
    ap.add_argument("--cuts", required=True, help="Input cuts.json")
    ap.add_argument("--out", required=True, help="Output .fcproj project file path")
    ap.add_argument("--report", help="Output build_report.json (default: <stem>_build_report.json)")
    ap.add_argument("--captions", action="store_true", help="Generate captions from transcript on cut timeline")
    ap.add_argument("--words", help="Input words.json (required if --captions is set and not found next to cuts.json)")
    ap.add_argument("--cli", help="Path to filmcraft-cli executable")

    args = ap.parse_args()
    cli = find_cli(args.cli)

    with open(args.cuts, "r", encoding="utf-8") as f:
        cuts_data = json.load(f)

    # Validate cuts.json contract up front (Fix 8)
    try:
        validate_cuts(cuts_data)
    except ValueError as e:
        sys.exit(f"Invalid cuts.json: {e}")

    source_path = cuts_data.get("source")
    if not source_path or not os.path.exists(source_path):
        sys.exit(f"Source file specified in cuts.json not found: {source_path}")

    segments = cuts_data["segments"]
    try:
        planned_fps_ratio = require_fps(cuts_data)
        check_against_source(segments, planned_fps_ratio, source_path)
    except ValueError as e:
        sys.exit(f"Invalid cuts.json: {e}")
    width, height, fps_ratio, fps_float = probe_source(source_path)
    fps_num = planned_fps_ratio.numerator
    fps_den = planned_fps_ratio.denominator

    ticks_per_frame = round(TICKS_PER_SEC * planned_fps_ratio.denominator / planned_fps_ratio.numerator)
    planned_total_frames = sum(s["dur_frames"] for s in segments)

    proj_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(proj_path), exist_ok=True)
    if os.path.exists(proj_path):
        os.remove(proj_path)

    proj_name = os.path.splitext(os.path.basename(proj_path))[0]

    # 1. Create fresh project
    cmd_new = [cli, "--save-as", proj_path, "exec", "file.newProject", f"name={proj_name}"]
    subprocess.run(cmd_new, capture_output=True, text=True, check=True)

    # 1.1 Create 7-tier standard professional bins
    bin_map = {}
    for b_name in STANDARD_BINS:
        cmd_bin = [cli, "--project", proj_path, "--save", "exec", "file.newBin", json.dumps({"name": b_name})]
        proc_bin = subprocess.run(cmd_bin, capture_output=True, text=True, check=True)
        try:
            bin_map[b_name] = json.loads(proc_bin.stdout).get("bin")
        except Exception:
            pass

    # 2. Import media and organize into 01_Footage bin with Forest (Dialogue) label
    cmd_import = [cli, "--project", proj_path, "--save", "import", source_path]
    proc_imp = subprocess.run(cmd_import, capture_output=True, text=True, check=True)
    source_item_id = 1
    try:
        imp_data = json.loads(proc_imp.stdout)
        imp_items = imp_data.get("items", [])
        if imp_items:
            source_item_id = imp_items[0]
            # Move imported footage to 01_Footage bin
            if bin_map.get("01_Footage"):
                subprocess.run(
                    [cli, "--project", proj_path, "--save", "exec", "project.moveToBin", json.dumps({"items": imp_items, "bin": bin_map["01_Footage"]})],
                    capture_output=True,
                    text=True,
                    check=True,
                )
            # Apply Forest (Dialogue role) label to media items
            subprocess.run(
                [cli, "--project", proj_path, "--save", "exec", "edit.label", json.dumps({"label": "Forest", "items": imp_items})],
                capture_output=True,
                text=True,
                check=True,
            )
    except Exception as e:
        print(f"Warning: bin organization for imported media had notice: {e}", file=sys.stderr)

    # 3. Create 4V / 4A multi-track sequence matching source specs
    seq_payload = {
        "name": f"{proj_name}_Seq",
        "width": width,
        "height": height,
        "fps": round(float(planned_fps_ratio), 3),
        "video": 4,
        "audio": 4,
    }
    cmd_seq = [cli, "--project", proj_path, "--save", "exec", "file.newSequence", json.dumps(seq_payload)]
    proc_seq = subprocess.run(cmd_seq, capture_output=True, text=True, check=True)
    try:
        seq_id = json.loads(proc_seq.stdout).get("sequence")
        if seq_id and bin_map.get("07_Sequences"):
            subprocess.run(
                [cli, "--project", proj_path, "--save", "exec", "project.moveToBin", json.dumps({"items": [seq_id], "bin": bin_map["07_Sequences"]})],
                capture_output=True,
                text=True,
                check=True,
            )
    except Exception:
        pass

    # Verify sequence frame_rate equals {num, den} from cuts.json (Fix 7)
    cmd_check_seq = [cli, "--project", proj_path, "inspect", "sequence"]
    proc_check_seq = subprocess.run(cmd_check_seq, capture_output=True, text=True, check=True)
    init_seq_data = json.loads(proc_check_seq.stdout)
    seq_fr = init_seq_data.get("settings", {}).get("frame_rate", {})
    if seq_fr.get("num") != fps_num or seq_fr.get("den") != fps_den:
        sys.exit(
            f"FilmCraft sequence frame rate mismatch! Expected {{num: {fps_num}, den: {fps_den}}}, "
            f"got {seq_fr}"
        )

    # 4. Prepare JSONL script for back-to-back placement, track styling & markers
    jsonl_lines = []

    # 4.1 Track naming and color styling
    for trk, trk_name, trk_label in TRACK_CONFIGS:
        jsonl_lines.append(
            json.dumps({
                "id": "timeline.setTrack",
                "params": {"track": trk, "name": trk_name, "label": trk_label},
            })
        )

    # 4.2 Start marker
    jsonl_lines.append(
        json.dumps({
            "id": "markers.add",
            "params": {
                "target": "program",
                "time": 0,
                "name": "Program Start",
                "comment": f"{proj_name} assembly start",
                "color": "Cyan",
            },
        })
    )

    # Optional: Attach transcript if captions requested
    if args.captions:
        words_file = args.words
        if not words_file:
            cand = os.path.join(os.path.dirname(args.cuts), "words.json")
            if os.path.exists(cand):
                words_file = cand
        if words_file and os.path.exists(words_file):
            w_data = json.load(open(words_file, "r", encoding="utf-8"))
            w_list = w_data.get("words", [])
            fc_words = []
            for w in w_list:
                s_ticks = round(w["start"] * TICKS_PER_SEC)
                e_ticks = round(w["end"] * TICKS_PER_SEC)
                fc_words.append({"text": w["word"], "start": s_ticks, "end": e_ticks, "speaker": 0})
            tr_payload = {
                "id": "transcript.set",
                "params": {
                    "item": source_item_id,
                    "transcript": {"language": w_data.get("language", "en"), "speakers": [{"name": "Speaker"}], "words": fc_words},
                },
            }
            jsonl_lines.append(json.dumps(tr_payload))

    # 4.3 Place segments with markers at each edit / chapter
    current_timeline_ticks = 0
    for idx, seg in enumerate(segments):
        source_in_ticks = seg["start_frame"] * ticks_per_frame
        duration_ticks = (seg["end_frame"] - seg["start_frame"]) * ticks_per_frame

        # Add section / cut marker
        seg_note = seg.get("note") or f"Cut #{idx+1}"
        seg_text = seg.get("text", "")
        is_chapter = (idx == 0) or seg.get("chapter") or seg.get("is_chapter")
        if is_chapter:
            jsonl_lines.append(
                json.dumps({
                    "id": "markers.addChapter",
                    "params": {
                        "time": current_timeline_ticks,
                        "name": f"Chap {idx+1}: {seg_note[:26]}",
                        "comment": seg_text[:80] if seg_text else seg_note,
                        "color": "Cyan",
                    },
                })
            )
        else:
            jsonl_lines.append(
                json.dumps({
                    "id": "markers.add",
                    "params": {
                        "target": "program",
                        "time": current_timeline_ticks,
                        "name": f"Cut {idx+1}: {seg_note[:26]}",
                        "comment": seg_text[:80] if seg_text else seg_note,
                        "color": "Yellow",
                    },
                })
            )

        place_cmd = {
            "id": "timeline.place",
            "params": {
                "item": source_item_id,
                "track": "V1",
                "audioTrack": "A1",
                "time": current_timeline_ticks,
                "sourceIn": source_in_ticks,
                "duration": duration_ticks,
                "insert": False,
                "video": True,
                "audio": True,
            },
        }
        jsonl_lines.append(json.dumps(place_cmd))
        current_timeline_ticks += duration_ticks

    if args.captions:
        # Generate captions on the cut timeline
        jsonl_lines.append(
            json.dumps(
                {
                    "id": "transcript.createCaptions",
                    "params": {"maxChars": 32, "lines": 1, "minSeconds": 0.5, "maxSeconds": 4.0, "gapFrames": 2},
                }
            )
        )
        jsonl_lines.append(
            json.dumps(
                {
                    "id": "captions.setStyle",
                    "params": {
                        "track": "C1",
                        "size": 48.0,
                        "color": "#FFE8B8",
                        "outline": 4.0,
                        "outlineColor": "#000000",
                        "background": False,
                        "align": "center",
                        "anchor": "bottom",
                        "margin": 0.1,
                    },
                }
            )
        )

    jsonl_path = os.path.splitext(proj_path)[0] + "_place.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        f.write("\n".join(jsonl_lines) + "\n")

    # 5. Run placement and parse each line's execution result
    cmd_run = [cli, "--project", proj_path, "--save", "run", jsonl_path]
    proc_run = subprocess.run(cmd_run, capture_output=True, text=True)
    if proc_run.returncode != 0:
        sys.exit(f"FilmCraft run failed:\nStdout: {proc_run.stdout}\nStderr: {proc_run.stderr}")

    caption_count = None
    for line in proc_run.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            line_res = json.loads(line)
            if not line_res.get("ok", True):
                sys.exit(f"FilmCraft run command failed on line {line_res.get('line')}: {line_res}")
            if line_res.get("id") == "transcript.createCaptions":
                caption_count = line_res.get("result", {}).get("captions")
        except json.JSONDecodeError:
            pass

    if args.captions:
        if caption_count is None or caption_count <= 0:
            sys.exit(f"transcript.createCaptions failed or returned 0 captions: count={caption_count}")

        # Clamp any trailing captions that overhang beyond planned_total_frames (Fix 6)
        cmd_list_caps = [cli, "--project", proj_path, "exec", "captions.list"]
        proc_caps = subprocess.run(cmd_list_caps, capture_output=True, text=True, check=True)
        caps_data = json.loads(proc_caps.stdout)
        tracks = caps_data.get("tracks", [])
        if tracks:
            captions_list = tracks[0].get("captions", [])
            max_allowed_ticks = planned_total_frames * ticks_per_frame
            for cap in captions_list:
                cap_id = cap.get("id")
                cap_start = cap.get("start", 0)
                cap_end = cap.get("end", 0)
                if cap_end > max_allowed_ticks:
                    if cap_start >= max_allowed_ticks:
                        # Entirely past end of cut: delete
                        subprocess.run(
                            [cli, "--project", proj_path, "--save", "exec", "captions.delete", json.dumps({"captions": [cap_id]})],
                            check=True,
                        )
                    else:
                        # Overhangs cut end: clamp end frame exactly to planned_total_frames
                        subprocess.run(
                            [cli, "--project", proj_path, "--save", "exec", "captions.setTimes", json.dumps({"caption": cap_id, "endFrame": planned_total_frames})],
                            check=True,
                        )

    # 6. Inspect sequence and verify frame-for-frame
    cmd_inspect = [cli, "--project", proj_path, "inspect", "sequence"]
    proc_inspect = subprocess.run(cmd_inspect, capture_output=True, text=True, check=True)
    seq_data = json.loads(proc_inspect.stdout)

    v_items = seq_data.get("video", [{}])[0].get("items", [])
    a_items = seq_data.get("audio", [{}])[0].get("items", [])
    landed_v_frames = sum(it.get("durationFrames", 0) for it in v_items)
    landed_a_frames = sum(it.get("durationFrames", 0) for it in a_items)
    landed_end_frame = max((it.get("endFrame", 0) for it in v_items), default=0)
    seq_dur_frames = seq_data.get("durationFrames", landed_end_frame)

    mismatches = []
    comparison_table = []

    # Verify V1 clip count
    if len(v_items) != len(segments):
        mismatches.append(f"Video clip count mismatch: planned {len(segments)}, landed {len(v_items)}")

    # Verify A1 clip count (Fix 5)
    if len(a_items) != len(segments):
        mismatches.append(f"Audio A1 clip count mismatch: planned {len(segments)}, landed {len(a_items)}")

    # Verify sequence duration against planned total (Fix 6)
    if seq_dur_frames != planned_total_frames:
        mismatches.append(
            f"Sequence durationFrames ({seq_dur_frames}) != planned total frames ({planned_total_frames})"
        )

    current_frame = 0
    all_placed_clips = []
    for idx, seg in enumerate(segments):
        planned_dur = seg["dur_frames"]
        planned_start = current_frame
        planned_end = planned_start + planned_dur
        current_frame = planned_end

        # Video track verification
        v_item = v_items[idx] if idx < len(v_items) else {}
        landed_v_start = v_item.get("startFrame")
        landed_v_end = v_item.get("endFrame")
        landed_v_dur = v_item.get("durationFrames")
        if "sourceIn" in v_item:
            landed_src_in = round(v_item["sourceIn"] / ticks_per_frame)
        else:
            landed_src_in = v_item.get("sourceInFrames")
        planned_src_in = seg["start_frame"]

        if "clip" in v_item:
            all_placed_clips.append(v_item["clip"])

        v_match = (
            landed_v_start == planned_start
            and landed_v_end == planned_end
            and landed_v_dur == planned_dur
            and landed_src_in == planned_src_in
        )
        if not v_match:
            mismatches.append(
                f"V1 Cut #{idx+1} mismatch: planned [{planned_start}..{planned_end}) dur={planned_dur} srcIn={planned_src_in}, "
                f"landed [{landed_v_start}..{landed_v_end}) dur={landed_v_dur} srcIn={landed_src_in}"
            )

        # Audio track verification (Fix 5)
        a_item = a_items[idx] if idx < len(a_items) else {}
        landed_a_start = a_item.get("startFrame")
        landed_a_end = a_item.get("endFrame")
        landed_a_dur = a_item.get("durationFrames")

        if "clip" in a_item:
            all_placed_clips.append(a_item["clip"])

        a_match = (
            landed_a_start == planned_start
            and landed_a_end == planned_end
            and landed_a_dur == planned_dur
        )
        if not a_match:
            mismatches.append(
                f"A1 Cut #{idx+1} mismatch: planned [{planned_start}..{planned_end}) dur={planned_dur}, "
                f"landed A1 [{landed_a_start}..{landed_a_end}) dur={landed_a_dur}"
            )

        comparison_table.append(
            {
                "cut": idx + 1,
                "planned_frames": planned_dur,
                "landed_v_frames": landed_v_dur,
                "landed_a_frames": landed_a_dur,
                "planned_range": f"[{planned_start}..{planned_end})",
                "landed_v_range": f"[{landed_v_start}..{landed_v_end})",
                "landed_a_range": f"[{landed_a_start}..{landed_a_end})",
                "planned_src_in": planned_src_in,
                "landed_src_in": landed_src_in,
                "video_match": v_match,
                "audio_match": a_match,
            }
        )

    # 6.1 Ensure all landed primary clips explicitly carry Forest (Dialogue) role color
    if all_placed_clips:
        try:
            subprocess.run(
                [cli, "--project", proj_path, "--save", "exec", "edit.label", json.dumps({"label": "Forest", "clips": all_placed_clips})],
                capture_output=True,
                text=True,
                check=True,
            )
        except Exception:
            pass

    # 6.2 Set Project Notes for professional handover
    try:
        notes_txt = (
            f"Project: {proj_name}\n"
            f"Source Media: {source_path}\n"
            f"FPS: {planned_fps_ratio} ({fps_num}/{fps_den})\n"
            f"Segments: {len(segments)} | Total Frames: {planned_total_frames} ({seq_dur_frames})\n"
            f"Organization: 7 Bins (01_Footage..07_Sequences), 4V/4A Tracks, Forest/Dialogue Roles, Timeline Markers."
        )
        subprocess.run(
            [cli, "--project", proj_path, "--save", "exec", "project.setNotes", json.dumps({"notes": notes_txt})],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        pass

    total_match = (
        (landed_v_frames == planned_total_frames)
        and (landed_a_frames == planned_total_frames)
        and (landed_end_frame == planned_total_frames)
        and (seq_dur_frames == planned_total_frames)
        and (len(mismatches) == 0)
    )

    report = {
        "nle": "FilmCraft CLI",
        "cli_path": cli,
        "project": proj_path,
        "source": source_path,
        "fps": str(planned_fps_ratio),
        "fps_num": fps_num,
        "fps_den": fps_den,
        "sequence_frame_rate": seq_fr,
        "planned_clip_count": len(segments),
        "landed_video_clip_count": len(v_items),
        "landed_audio_clip_count": len(a_items),
        "planned_total_frames": planned_total_frames,
        "landed_total_frames": landed_v_frames,
        "landed_audio_total_frames": landed_a_frames,
        "landed_timeline_end_frame": landed_end_frame,
        "sequence_duration_frames": seq_dur_frames,
        "captions": caption_count,
        "organization": {
            "bins": STANDARD_BINS,
            "tracks": [{"track": t[0], "name": t[1], "label": t[2]} for t in TRACK_CONFIGS],
            "clip_color_role": "Forest (Dialogue)",
            "markers_placed": len(segments) + 1,
        },
        "exact_match": total_match,
        "mismatches": mismatches,
        "clips": comparison_table,
    }

    report_path = args.report or os.path.splitext(proj_path)[0] + "_build_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    if not total_match:
        print(f"FAILED: FilmCraft timeline mismatch: {mismatches}", file=sys.stderr)
        sys.exit(1)

    print(
        f"FilmCraft build VERIFIED: {len(v_items)} clips, V1/A1 {landed_v_frames} frames (0 drift) "
        f"[Bins: 7, Tracks: 4V/4A styled, Markers: {len(segments)+1}] -> {proj_path} (report: {report_path})"
    )


if __name__ == "__main__":
    main()
