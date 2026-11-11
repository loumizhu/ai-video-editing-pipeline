#!/usr/bin/env python3
"""estimate_timing.py - Generates estimated timing.json at calibrated narration WPM (default 158 WPM).
Used when Voicebox/TTS is offline or owner records later.
Emits the canonical Vcut §3.2 schema (vcut.timing/1):
  - start_s / end_s on lines and chapters
  - line_id (e.g. ch01.l001) and chapter_id (e.g. ch01)
  - list-shaped qc entries with wer, status, re_time_required
  - list-shaped units with offset_samples and duration_samples (48kHz)
  - list-shaped words with line_id, word index, start_s, end_s, source
Preserves multi-chapter structures from:
  1. Stage 03 hook outline (--outline <file>)
  2. Per-chapter spoken files directory (--chapters-dir <dir>)
  3. Chapter markers file or comma-separated list (--chapters <spec>)
  4. Script internal headings or section dividers (---)
"""

import argparse
import glob
import json
import math
import os
import re
import sys

def parse_outline_chapters(outline_path):
    """Parses chapter titles from a Stage 03 outline markdown file."""
    if not os.path.exists(outline_path):
        return []
    with open(outline_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    chapters = []
    for line in content.splitlines():
        line_clean = line.strip()
        m = re.match(r'^(?:#{1,3}\s+|\-\s+|\*\*)?(?:Chapter\s+(\d+|[IVXLCDM]+)[:\-\s]*|Act\s+(\d+|[IVXLCDM]+)[:\-\s]*|\bPart\s+(\d+)[:\-\s]*|\b(\d+)\.\s+)(.*?)(?:\*\*|\(.*\)|$)', line_clean, re.I)
        if m:
            title = m.group(5).strip(' *-_#[]')
            if not title:
                title = f"Chapter {len(chapters)+1}"
            # Exclude generic stage doc sections
            if not any(kw in title.lower() for kw in ['purpose', 'inputs', 'outputs', 'steps', 'checklist', 'tools', 'review', 'gate', 'failure']):
                chapters.append(title)
        elif re.match(r'^##\s+(?:Chapter|Beat|Scene)\s*(.*?)$', line_clean, re.I):
            title = re.sub(r'^##\s+', '', line_clean).strip(' *-_#[]')
            if title and not any(kw in title.lower() for kw in ['purpose', 'inputs', 'outputs', 'steps', 'checklist', 'tools', 'review', 'gate', 'failure']):
                chapters.append(title)

    return chapters

def parse_spoken_lines(text):
    """Sanitizes text and extracts spoken narration lines and words."""
    lines = []
    for line in text.splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue
        # Skip technical directives, comments, metadata headers, and visual cues
        if line_clean.startswith('---') or line_clean.startswith('```') or re.match(r'^#{1,6}\s', line_clean):
            continue
        if re.match(r'^\s*\[(?:SFX|VISUAL|SHOT|NOTE|B-ROLL|MUSIC|AUDIO).*?\]\s*$', line_clean, re.I):
            continue
        # Strip inline bracketed cues and markdown formatting
        spoken = re.sub(r'\[.*?\]', '', line_clean).strip()
        spoken = re.sub(r'[*_`#]', '', spoken).strip()
        if not spoken:
            continue
        words = [w for w in re.split(r'\s+', spoken) if w]
        if words:
            lines.append({"text": spoken, "words": words})
    return lines

def load_from_chapters_dir(chapters_dir):
    """Loads chapter spoken text from 06_script_edit_plan/chapters/chapter_<N>.md."""
    pattern = os.path.join(chapters_dir, 'chapter_*.md')
    files = sorted(glob.glob(pattern))
    if not files:
        files = sorted(glob.glob(os.path.join(chapters_dir, '*.md')))
    if not files:
        return None

    parsed_chapters = []
    for fpath in files:
        basename = os.path.splitext(os.path.basename(fpath))[0]
        title = basename.replace('_', ' ').title()
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
        lines = parse_spoken_lines(text)
        if lines:
            parsed_chapters.append({"title": title, "lines": lines})
    return parsed_chapters

def partition_script_into_chapters(script_path, outline_path=None, chapters_spec=None):
    """Parses script and partitions it into structured chapters."""
    with open(script_path, 'r', encoding='utf-8', errors='replace') as f:
        raw_text = f.read()

    # Determine chapter titles
    chapter_titles = []
    if outline_path and os.path.exists(outline_path):
        chapter_titles = parse_outline_chapters(outline_path)
    elif chapters_spec:
        if os.path.exists(chapters_spec):
            with open(chapters_spec, 'r', encoding='utf-8') as cf:
                chapter_titles = [ln.strip() for ln in cf.read().splitlines() if ln.strip()]
        else:
            chapter_titles = [c.strip() for c in chapters_spec.split(',') if c.strip()]

    # Check if script has explicit chapter headings or '---' dividers
    sections = []
    current_title = None
    current_lines = []

    raw_lines = raw_text.splitlines()
    for line in raw_lines:
        line_clean = line.strip()
        m_chap = re.match(r'^(?:#{1,3}\s+|\bChapter\s+\d+[:\-\s]*)(.*?)$', line_clean, re.I)
        is_divider = line_clean == '---'
        
        if (m_chap and any(kw in line_clean.lower() for kw in ['chapter', 'act', 'part'])) or is_divider:
            if current_lines:
                sections.append({"title": current_title or f"Chapter {len(sections)+1}", "lines": current_lines})
                current_lines = []
            if m_chap:
                current_title = m_chap.group(1).strip(' *-_#[]') or f"Chapter {len(sections)+1}"
            else:
                current_title = None
            continue

        if not line_clean or line_clean.startswith('```') or re.match(r'^\s*\[(?:SFX|VISUAL|SHOT|NOTE|B-ROLL).*?\]\s*$', line_clean, re.I):
            continue

        spoken = re.sub(r'\[.*?\]', '', line_clean).strip()
        spoken = re.sub(r'[*_`#]', '', spoken).strip()
        if spoken:
            words = [w for w in re.split(r'\s+', spoken) if w]
            if words:
                current_lines.append({"text": spoken, "words": words})

    if current_lines:
        sections.append({"title": current_title or f"Chapter {len(sections)+1}", "lines": current_lines})

    # If script had internal sections with multiple chapters, use them
    if len(sections) > 1:
        for i, sec in enumerate(sections):
            if i < len(chapter_titles):
                sec["title"] = chapter_titles[i]
        return sections

    # Otherwise, script was narration-only without headers
    all_lines = sections[0]["lines"] if sections else parse_spoken_lines(raw_text)
    if not all_lines:
        return []

    # If chapter titles exist from outline or --chapters, distribute lines across them
    if chapter_titles and len(chapter_titles) > 1:
        num_chaps = len(chapter_titles)
        lines_per_chap = math.ceil(len(all_lines) / num_chaps)
        structured = []
        for i, title in enumerate(chapter_titles):
            chap_lines = all_lines[i * lines_per_chap : (i + 1) * lines_per_chap]
            if chap_lines:
                structured.append({"title": title, "lines": chap_lines})
        return structured

    # Fallback to single chapter
    return [{"title": "Introduction", "lines": all_lines}]

def generate_vcut_timing(chapters_data, wpm=158, sample_rate=48000):
    """Generates canonical Vcut §3.2 timing data."""
    sec_per_word = 60.0 / wpm
    pause_between_lines = 0.40
    pause_between_chapters = 1.20

    current_time_s = 0.0
    units_list = []
    lines_list = []
    words_list = []
    chapters_list = []
    qc_list = []

    for c_idx, chap in enumerate(chapters_data):
        chap_id = f"ch{c_idx+1:02d}"
        chap_start_s = round(current_time_s, 3)
        chap_lines = chap["lines"]

        for l_idx, line in enumerate(chap_lines):
            line_id = f"{chap_id}.l{l_idx+1:03d}"
            line_start_s = round(current_time_s, 3)
            line_words = line["words"]

            for w_idx, w_text in enumerate(line_words):
                w_start = round(current_time_s, 3)
                w_end = round(current_time_s + sec_per_word, 3)
                current_time_s += sec_per_word
                words_list.append({
                    "line_id": line_id,
                    "word": w_idx,
                    "text": w_text,
                    "start_s": w_start,
                    "end_s": w_end,
                    "source": "estimated_wpm"
                })

            line_end_s = round(current_time_s, 3)
            current_time_s += pause_between_lines

            lines_list.append({
                "line_id": line_id,
                "chapter_id": chap_id,
                "text": line["text"],
                "start_s": line_start_s,
                "end_s": line_end_s
            })

        chap_end_s = round(current_time_s - pause_between_lines, 3)
        current_time_s += pause_between_chapters

        dur_s = round(chap_end_s - chap_start_s, 3)
        budget_s = round(dur_s * 1.15, 1)

        chapters_list.append({
            "chapter_id": chap_id,
            "title": chap["title"],
            "start_s": chap_start_s,
            "end_s": chap_end_s,
            "budget_s": budget_s
        })

        unit_id = f"{chap_id}.u001"
        offset_samples = int(round(chap_start_s * sample_rate))
        dur_samples = int(round(dur_s * sample_rate))

        units_list.append({
            "unit_id": unit_id,
            "chapter_id": chap_id,
            "file": f"06_script_edit_plan/chapters/chapter_{c_idx+1:02d}.wav",
            "sha256": "",
            "offset_samples": offset_samples,
            "duration_samples": dur_samples,
            "source": "estimated_placeholder"
        })

        qc_list.append({
            "unit_id": unit_id,
            "wer": 0.0,
            "status": "pending_owner_recording",
            "re_time_required": True,
            "requires_gate_g3b_approval": True
        })

    total_duration_s = round(current_time_s - pause_between_chapters, 3)

    return {
        "schema": "vcut.timing/1",
        "sample_rate": sample_rate,
        "estimated": True,
        "status": "pending_owner_recording",
        "requires_gate_g3b_approval": True,
        "calibrated_wpm": wpm,
        "total_duration_s": total_duration_s,
        "total_duration_seconds": total_duration_s,
        "units": units_list,
        "lines": lines_list,
        "words": words_list,
        "chapters": chapters_list,
        "qc": qc_list
    }

def main():
    parser = argparse.ArgumentParser(description="Estimate narration timing matching canonical Vcut §3.2 schema")
    parser.add_argument('--script', help="Path to VoiceOver.md or narration text")
    parser.add_argument('--outline', help="Path to Stage 03 outline markdown file (e.g. 03_hook_outline.md)")
    parser.add_argument('--chapters-dir', help="Path to directory containing per-chapter markdown files (e.g. chapters/)")
    parser.add_argument('--chapters', help="Comma-separated chapter names or path to chapters text file")
    parser.add_argument('--out', required=True, help="Output path for timing.json")
    parser.add_argument('--wpm', type=int, default=158, help="Calibrated words per minute (default 158)")
    parser.add_argument('--sample-rate', type=int, default=48000, help="Audio sample rate (default 48000 Hz)")
    args = parser.parse_args()

    chapters_data = None
    if args.chapters_dir and os.path.exists(args.chapters_dir):
        chapters_data = load_from_chapters_dir(args.chapters_dir)

    if not chapters_data:
        if not args.script or not os.path.exists(args.script):
            print("Error: must provide an existing --script file or valid --chapters-dir", file=sys.stderr)
            sys.exit(1)
        chapters_data = partition_script_into_chapters(args.script, outline_path=args.outline, chapters_spec=args.chapters)

    if not chapters_data:
        print("Error: no spoken content could be parsed", file=sys.stderr)
        sys.exit(1)

    timing_data = generate_vcut_timing(chapters_data, wpm=args.wpm, sample_rate=args.sample_rate)

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(timing_data, f, indent=2, ensure_ascii=False)

    print("Estimated timing generated successfully (canonical Vcut §3.2):")
    print(f"  Schema: {timing_data['schema']}")
    print(f"  WPM: {args.wpm}")
    print(f"  Total Duration: {timing_data['total_duration_s']} s")
    print(f"  Chapters: {len(timing_data['chapters'])}")
    print(f"  Lines: {len(timing_data['lines'])}")
    print(f"  Words: {len(timing_data['words'])}")
    print(f"  QC Entries: {len(timing_data['qc'])}")
    print(f"  Output: {args.out}")

if __name__ == '__main__':
    main()
