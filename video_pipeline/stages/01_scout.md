# Stage 01: Scout & Topic Validation

## Purpose
Identify and mathematically validate a high-retention, high-RPM video topic centered on a household-name star or franchise, establishing live fact baselines before writing.

> *Note: Plain-text project paths (e.g. `_pipeline/`, `01_research/`) are relative to working directory `Videos-Scripts/<NN>_<Slug>/`. Markdown links are relative to this stage file.*

## Inputs
- `_pipeline/brief.md` (kick-off project brief; prompts owner upfront if blank).
- [AGENTS.md](../../../AGENTS.md) (§1 Storage & §2 Validation Standards).
- [MASTER_PROCESS_CHECKLIST.md](../../../Tips-Playbook/MASTER_PROCESS_CHECKLIST.md) (Phase 1 Scout).

## Outputs
- `_pipeline/01_scout_dossier.md` (validation metrics, competitor URLs, outlier ratios, RPM estimate).
- `01_research/FACT_BASELINE.md` (live verified facts: dates, official statements, charities; cite Video 010).

## Executor
- **Worker:** Antigravity (Gemini Flash medium), effort: medium.

## Tools
- `yt-dlp` (metadata extraction with `--cookies-from-browser firefox` and Node EJS).
- Web Search / Brave Browser automation (for primary fact verification).
- Python (computing outlier spike ratios and SHA-256 checksums).

## Steps
1. **Step 0 — Live Fact Check (Video 010):** Run an immediate fact baseline check on birth/death dates, spouse/spokesperson statements, official memorial charities, and breaking news before drafting anything. Save to `01_research/FACT_BASELINE.md`. Never trust second-hand titles.
2. **Star / Franchise Anchor:** Verify the subject is a household-name cultural icon or titan.
3. **Proof of Concept Check:** Confirm ≥2 independent competitor videos with 100k+ views on the exact premise in the last 4 months (Lemino Playbook).
4. **Outlier Rule Check (Andrew's Playbook):** Identify at least one channel with <50k subscribers achieving a ≥5x view spike vs the same-age performance of their last 20 uploads.
5. **RPM Tiering:** Confirm US/Tier-1 audience alignment ($10–$15 Hollywood/Nostalgia; $12–$18 Corporate).
6. **Dossier Compilation:** Record validation findings in `_pipeline/01_scout_dossier.md`.

## Acceptance Checklist
- [ ] Topic explicitly centers on a household-name star or franchise.
- [ ] `01_research/FACT_BASELINE.md` completed with primary dates and statements verified.
- [ ] ≥2 independent competitor videos (100k+ views, <4 months old) documented.
- [ ] Outlier channel (<50k subs, ≥5x view spike) identified with links and view counts.
- [ ] Target RPM confirmed between $10 and $18.
- [ ] Output saved to `_pipeline/01_scout_dossier.md`.

## Reviewer
- Claude Sonnet via [research.md](../../../.agents/skills/orchestrate/reviewers/research.md).

## Human Gate
- **Yes — Gate G1 (Topic Gate):** Human operator inspects `01_scout_dossier.md` and signs `_pipeline/approvals/G1_topic.md`.

## Failure & Retry
- If rejected by reviewer or human, propose 2 alternative star-centered angles. Max 3 passes. Deadlocks escalate to Claude Opus.

<span style="color: purple;">[AI Agent]</span>
