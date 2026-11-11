# Stage 09: Packaging, CTR Optimization & Integrity Verification

## Purpose
Engineer high-CTR packaging assets: 5-title cluster, turnkey YouTube metadata with manual mid-rolls, captions SRT, and 4 pre-sized thumbnails (1280x720). Enforce 0.5s friction test, 120px mobile legibility, and shock-forward packaging that stays on the real subject (owner-checked).
Reference: [Packaging Playbook](../../../Tips-Playbook/02_packaging_ctr_playbook.md) and [AGENTS.md §2](../../../AGENTS.md).

> *Note: Plain-text project paths (e.g. `08_thumbnail/`, `09_upload/`, `06_script_edit_plan/`) are relative to working directory `Videos-Scripts/<NN>_<Slug>/`. Markdown links are relative to this stage file.*

## Inputs
- `_pipeline/brief.md` (thumbnail preferences, exclusions, formal names).
- `_pipeline/01_scout_dossier.md` (competitor packaging benchmarks).
- `_pipeline/03_hook_outline.md` (central mystery engine).
- `06_script_edit_plan/Video_<NN>_Script_Draft_2.md` (verified factual coverage).
- `06_script_edit_plan/timing.json` (caption timestamps).
- `07_Video_Edit/preview_rough_cut.mp4` (verified scene timestamps for mid-rolls).

## Outputs
- `08_thumbnail/thumbnail_brief.md` (composition, contrast, text rules).
- `08_thumbnail/thumb_v1.png` .. `thumb_v4.png` (1280x720 design plates; cite Video 010).
- `08_thumbnail/thumb_120px_test.png` (mechanical 120px scale render).
- `09_upload/captions.srt` (subtitle captions derived from `words.srt` or `timing.json`).
- `09_upload/metadata.json` (turnkey YouTube release metadata).
- `09_upload/thumb_1.png` .. `thumb_4.png` (4 final 1280x720 variants ready for A/B testing).
- `09_upload/upload_checklist.md` (pre-flight upload verification checklist).
- `06_script_edit_plan/NAMING_REVERENCE_CHECK.txt` (extended with grep proof on metadata).

## Executor
- **Worker:** Antigravity (metadata, composition, scripts) + Grok (5-title cluster brainstorming), effort: medium.

## Tools
- Chapter and thumbnail candidates (Revision 2026-11-09): spec in [DERIVATIVES.md section 3](../DERIVATIVES.md#3-auto-chaptering-and-thumbnail-candidates-inputs-to-stage-09); `suggest_chapters.py` and `thumb_candidates.py` are `[TO BUILD]`. Until built the agent derives chapters from `03_hook_outline.md` + `beat_map.json` (turn / reveal beats) and picks thumbnail candidate frames from the highest-intensity beats by hand.
- Python + Pillow (image resizing, contrast check, mechanical 120px thumbnail downsampling).
- `transcribe_groq.py` (VERIFIED; generates `words.srt` directly from transcribed VO) / `build_cut_filmcraft.py --captions` (VERIFIED; generates cut-timeline captions).
- `[TO BUILD]` Estimated-timing captions generator converting unaligned `timing.json` to `captions.srt` when real VO is bypassed.
- `[TO BUILD]` Background removal script for subject cutout extraction.
- `[TO BUILD]` Grep script scanning `metadata.json` for formal naming compliance.

## Minimal `metadata.json` Schema Fields
- `primary_title`: Selected high-curiosity title shock-forward, on the real subject.
- `title_cluster`: 5 thematic variants exploring distinct psychological angles.
- `description`: Café-friend video synopsis, primary sources, memorial/charity citations.
- `tags`: Targeted search tags (specific proper nouns, no keyword stuffing).
- `chapters`: Timestamped chapter markers (`00:00 - Introduction`).
- `manual_mid_rolls`: Specific timestamps (every 90–120s placed immediately prior to reveal beats).

## Steps
1. **Title Cluster:** Brainstorm 5 distinct thematic titles with Grok. Select the strongest, most visceral hook.
2. **Subject Flag (AGENTS.md §2):** Note any title/thumbnail element that is not about the video's real subject for the owner to review. Packaging is owner-checked: shock-forward is fine as long as it is about the video's real subject. Agents flag concerns; they never block.
2b. **Chapters & Thumbnail Candidates:** build `chapters` from the outline chapters snapped to the nearest `turn` / `reveal` beat (first at `0:00`, at least 3, each at least 10 s, plain curiosity-led titles, formal names). Pull 8-12 candidate frames from intensity >= 4 beats (sharp, not mid-dissolve, not under a full-screen card, room for <= 4 words) as raw material for step 6; they never replace the 0.5 s friction test or the subject flag.
3. **Mid-Roll Insertion:** Identify retention peaks and mark manual ad breaks every 90–120s right before mystery reveals.
4. **Caption SRT Generation:** Copy verified `words.srt` (from `transcribe_groq.py`) into `09_upload/captions.srt` (or generate via `build_cut_filmcraft.py --captions`). If bypassed, use estimated-timing generator.
5. **Naming Reverence Grep:** Grep `metadata.json` (title, description, tags) for formal naming compliance, appending results to `06_script_edit_plan/NAMING_REVERENCE_CHECK.txt`.
6. **Thumbnail Briefing & Cutouts:** Architect 2–4 concepts (focal subject ≥40% canvas, text overlay ≤4 non-repeating words). Extract cutouts and generate 1280x720 plates in `08_thumbnail/`.
7. **Mechanical 120px & 0.5s Friction Test:**
   - **Deterministic Tool (Pillow):** Downsample thumbnail to 120px width (`thumb_120px_test.png`).
   - **Agent / Operator Judgment:** Evaluate visual clarity and readability at 0.5s glance.
8. **Consolidate Upload Package:** Copy 4 approved thumbnails, `captions.srt`, `metadata.json`, and `upload_checklist.md` into `09_upload/`.

## Acceptance Checklist
- [ ] Packaging Integrity: subject flags (if any) listed for owner review.
- [ ] 5-title cluster formulated; 1 primary title chosen.
- [ ] `chapters` valid (starts `0:00`, >= 3 chapters, each >= 10 s) and aligned to outline chapters / beat-map turns.
- [ ] Thumbnail text overlay ≤4 words with zero words repeated from title.
- [ ] Pillow generated 120px scale test; verified ultra-readable at 120px mobile width.
- [ ] Captions generated and saved to `09_upload/captions.srt`.
- [ ] Naming reverence check appended to `NAMING_REVERENCE_CHECK.txt`.
- [ ] Turnkey files placed in `09_upload/` (`metadata.json`, 4 thumbnails, `upload_checklist.md`, `captions.srt`).

## Reviewer
- Claude Sonnet via [packaging.md](../../../.agents/skills/orchestrate/reviewers/packaging.md).

## Human Gate
- **No:** Direct input to Stage 10 for Final Cut Gate (G4).

## Failure & Retry
- If text repeats title words or 120px readability fails, redesign plates. Max 3 passes.

<span style="color: purple;">[AI Agent]</span>
