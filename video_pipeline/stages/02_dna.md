# Stage 02: Competitor DNA & Audience Gaps

## Purpose
Deconstruct the top 5 competitor videos (<4 months old) to extract transcripts and top 250 comments, isolating audience pain points, unmet curiosities, and verified quote baselines.

> *Note: Plain-text project paths (e.g. `_pipeline/`, `01_research/`, `02_reference_videos/`) are relative to working directory `Videos-Scripts/<NN>_<Slug>/`. Markdown links are relative to this stage file.*

## Inputs
- `_pipeline/01_scout_dossier.md` (competitor URLs/IDs).
- `01_research/FACT_BASELINE.md` (verified factual baseline).
- `_pipeline/approvals/G1_topic.md` (verified G1 human approval).
- [AGENTS.md](../../../AGENTS.md) (§1 Storage & §2 DNA).

## Outputs
- `_pipeline/02_dna_report.md` (synthesis of audience gaps, retention leaks, narrative opportunities).
- `_pipeline/02_sources.md` (relative pointers to competitor archives in `Channel Niche & Audience/`).
- `02_reference_videos/` (local repository of reference video clips, transcripts, and comment summaries).
- `01_research/QUOTE_PROOF.md` (quote provenance table: source archive, timestamp, verbatim text, verification method; cite Video 010).
- `03_media/BEST_LINES_SELFCHECK.txt` (contact sheet proof for eyes & framing check).

## Executor
- **Worker:** Antigravity (Gemini Flash medium), effort: medium.

## Tools
- `yt-dlp` (`--write-comments`, `--write-auto-subs`, `--sub-lang en`, `--cookies-from-browser firefox`).
- `ffmpeg` (frame contact sheets for eyes & framing check).
- Python (comment sorting, text parsing, SHA-256 calculation).

## Steps
1. **Verification:** Confirm `_pipeline/approvals/G1_topic.md` SHA-256 matches `01_scout_dossier.md`.
2. **Competitor Archiving (AGENTS.md §1):** Download and archive competitor assets directly into `Channel Niche & Audience/<Niche_Folder>/<Video_Title>_[<Video_ID>]/` (`.mp4`, `metadata.json`, `comments_top250.json`, `transcripts/`, `audio/`, forensic report). Record pointers in `_pipeline/02_sources.md` and save reference transcripts/summaries to `02_reference_videos/`.
3. **Friction Analysis:** Parse top 250 comments for recurring audience friction ("Why didn't they mention...", "The real reason was...").
4. **Quote Provenance Rule (Video 010):** Extract candidate quotes exclusively from raw broadcast clips, talk show archives, or signed statements (banning automated-voiceover channels or unverified compilations). Log in `01_research/QUOTE_PROOF.md`.
5. **Eyes & Framing Check (Video 010):** Run `ffmpeg` to generate a 3x3 contact sheet around quote timestamps to verify who the speaker is actually addressing before attributing dialogue (e.g. Jackman-to-McKellen check). Save proof to `03_media/BEST_LINES_SELFCHECK.txt`.
6. **Synthesize Report:** Output actionable creative opportunities in `_pipeline/02_dna_report.md`.

## Acceptance Checklist
- [ ] Competitor data saved to `Channel Niche & Audience/` and cataloged in `_pipeline/02_sources.md`.
- [ ] Reference transcripts and comment summaries saved to `02_reference_videos/`.
- [ ] ≥5 distinct audience pain points/unmet curiosities cited with verbatim quotes.
- [ ] `01_research/QUOTE_PROOF.md` lists all quotes with broadcast sources and timestamps.
- [ ] Framing check contact sheets generated in `03_media/` for ambiguous dialogue (`BEST_LINES_SELFCHECK.txt`).
- [ ] Synthesis report written to `_pipeline/02_dna_report.md`.

## Reviewer
- Claude Sonnet via [research.md](../../../.agents/skills/orchestrate/reviewers/research.md).

## Human Gate
- **No:** Research synthesis milestone; reviewer approval advances pipeline to Stage 03.

## Failure & Retry
- If comments lack depth, analyze 2 additional niche videos or historical forum threads. Max 3 passes.

<span style="color: purple;">[AI Agent]</span>
