# Stage 07: Asset Sourcing, Licensing & Media Conform

## Purpose
Acquire, verify licensing for, and deterministically conform all video, photo, music, and SFX assets to project canvas standards (1080p, constant framerate 30fps, Rec.709) using CLI tools, executing the candidate fallback chain when assets are unavailable.
Reference: [Vcut Step 03: Visuals](../../../../Vcut/03_Shot_Planning_and_Visuals.md#03d--probe--conform), [Vcut Data Contracts §3.4](../../../../Vcut/Vcut_Data_Contracts.md#34-asset_registryjson--licence-and-provenance-ledger), and [Editing Toolkit](../EDITING_TOOLKIT.md).

> *Note: Plain-text project paths (e.g. `03_media/`, `03_media/`, `05_music/`) are relative to working directory `Videos-Scripts/<NN>_<Slug>/`. Markdown links are relative to this stage file.*

## Inputs
- `06_script_edit_plan/shot_plan.json` (visual queries, asset types, slot durations, effect assignments).
- `_pipeline/brief.md` (music direction, thumbnail focal preferences).
- `01_research/QUOTE_PROOF.md` (verified broadcast clips and soundbites).
- [04_editing_production_sop.md](../../../Tips-Playbook/04_editing_production_sop.md) (licensing rules and Fair Use doctrine).

## Outputs
- `03_media/asset_audit.json` / `.md` and `03_media/research_requests.json` (asset audit: resolution after the planned push, aspect, duplicates, missing coverage; Revision 2026-11-09).
- `03_media/raw/*` and `03_media/conformed/*` (conformed 1080p30 MP4 video clips).
- `03_media/scored_clips.wav` (timeline-aligned archival soundbites / quotes at 48kHz).
- `03_media/raw/*` and `03_media/conformed/*` (conformed 1920x1080 PNG stills).
- `05_music/primary_bed.wav` (primary background score track cataloged in manifest, 48kHz).
- `05_music/08_audio_manifest.json` (track metadata, BPM loop calculations, license ledger; cite Video 010).
- `03_media/asset_registry.json` (provenance ledger conforming to Vcut §3.4 schema).
- `_pipeline/BYPASS_LOG.md` (updated if asset candidate fallback triggered).

## Executor
- **Worker / Tool:** `media_search.py` (`internet-media-search` skill) + `yt-dlp` + `ffmpeg` + Pillow + Antigravity.

## Tools
- `python ../Video_Pipeline/tools/asset_audit.py --assets-dir 03_media/conformed --shot-plan 06_script_edit_plan/shot_plan.json --out-json 03_media/asset_audit.json --out-md 03_media/asset_audit.md --requests-out 03_media/research_requests.json` (**VERIFIED; Revision 2026-11-09**; for narrated beat builds use `--beats beats.json --assign assignments.json`).
- `media_search.py` (CLI multi-engine search, Wikimedia, DuckDuckGo, YouTube with `--sections "*MM:SS-MM:SS"` keyframe clipping and curl/SSL fallback).
- `yt-dlp` (`--download-sections` for precise archival segment retrieval).
- `ffmpeg` (conforming to 1080p, CFR 30fps, Rec.709 color; audio sample rate conform to 48kHz).
- Pillow (image resizing, aspect-ratio padding, contact sheet generation).
- `render_article.py` (microfilm / newspaper clipping callout generation for documentary evidence).

## Historical Research Standard: The 5 Pillars of Archival Evidence
> **CRITICAL RULE (LESSONS.md #7):** Audio narration must NEVER run over a black screen or empty video track. Real historical figures and events must **NEVER** be illustrated using synthetic AI-generated images or modern approximations.

Visual research must strictly draw from the **5 Pillars of Archival Evidence**:
1. **Archival Newsreels & Restored 16mm/35mm Footage:** British Movietone, Pathé, Prelinger, AP Archives, Universal Newsreels.
2. **Broadcast Appearances & Oral Histories:** Contemporary TV interviews, Emmy TV Legends, talk show appearances (Mike Wallace, Dick Cavett, Dinah Shore).
3. **Primary Source Documents & Microfilm Scans:** Authentic newspaper microfilm scans, court records, commitment dockets, rendered as sharp callouts with `render_article.py`.
4. **Restored Period Cinema & Theatrical Trailers:** Original studio feature film appearances, trailers, public domain 35mm prints.
5. **Verified Archival Stills:** High-resolution public domain photographs from Library of Congress, Bain Collection, NARA, Wikimedia Commons, animated via subtle 2.5D Ken Burns push/pull.

## Steps
1. **Media Acquisition & Fallback Chain:** Query footage into `03_media/raw/`, stills into `03_media/raw/` using `media_search.py`. If an archival asset is missing, execute candidate fallback chain: (1) First alternate candidate from shot plan → (2) Generated purposeful newspaper article/map graphic (`render_article.py` / `render_map.py`) → (3) Stylized color/grain plate with citation. Never leave slot empty or black.
2. **Video Conforming:** Execute deterministic conform:
   ```bash
   ffmpeg -y -i "03_media/raw/<input>.mp4" -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1" -r 30 -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k "03_media/conformed/<shot_id>.mp4"
   ```
3. **Image Conforming & Clip Prep:** Use Pillow to pad or scale archival stills to 1920x1080 PNG. Prepare CFR 30fps video clips for still slots for consumption by `07_Video_Edit/concat_clips.txt` or NLE timeline.
4. **Music & SFX Sourcing & Stem Alignment:** Ingest score tracks into `05_music/primary_bed.wav`. Compute bar loop lengths (e.g. 3/4 time at 130 BPM = 1.385s per bar). Align `03_media/scored_clips.wav` quotes to narration timeline timecodes (48kHz PCM, padded to master duration). Record metadata in `05_music/08_audio_manifest.json`.
5. **Asset Audit (Revision 2026-11-09):** run `asset_audit.py` after conform. FAIL items (`TOO_SMALL`, `DUPLICATE`/`SIMILAR` used within 20 s, `BLANK`, `CORRUPT`, `MISSING_*`, `COVERAGE_DEFICIT`) go back to acquisition via `research_requests.json` (each request = beat, narration text, reason, shots still needed). Max 2 research rounds, then the fallback chain, ending in a `narration_plate` (never a black slot, never a repeated picture). WARN items (`SOFT_UPSCALE`, `ASPECT_PORTRAIT`) are fixed in the plan: cap the push to `push_slow`, or place the picture on a blurred-fill plate / panel. Feed `asset_audit.json` to `still_hold_qa.py --assets-report` so near-duplicates count as one still run.
6. **Licensing Ledger:** Document source URLs, copyright holders, and Fair Use justifications in `03_media/asset_registry.json` per Vcut §3.4.

## Acceptance Checklist
- [ ] Conformed asset exists for 100% of required shot slots in `conformed/` (zero black screen gaps).
- [ ] Visual assets strictly adhere to the 5 Pillars of Archival Evidence (zero synthetic AI images for historical events/figures).
- [ ] All video assets have constant framerate 30fps (zero variable framerate drift).
- [ ] Score tracks (`primary_bed.wav`) and SFX cataloged in `05_music/08_audio_manifest.json`.
- [ ] `03_media/scored_clips.wav` isolated, conformed to 48kHz, and aligned to narration timeline.
- [ ] No watermarked, corrupted, or unusable low-resolution assets; `asset_audit.py` is PASS (0 `TOO_SMALL`, 0 coverage deficits, no near-duplicates within 20 s).
- [ ] Vcut §3.4 `asset_registry.json` generated with SHA-256 hashes for all files.

## Reviewer
- Claude Sonnet via [code.md](../../../.agents/skills/orchestrate/reviewers/code.md).

## Human Gate
- **No:** Mechanical conform milestone verified by file presence and checksums.

## Failure & Retry
- If download fails or codec corrupted, execute candidate fallback chain, log to `_pipeline/BYPASS_LOG.md`, and proceed. Max 3 passes.

<span style="color: purple;">[AI Agent]</span>
