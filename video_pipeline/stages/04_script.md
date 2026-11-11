# Stage 04: Scriptwriting & Pre-Flight Verification

## Purpose
Produce an emotionally resonant, factually rigorous documentary script with café-friend narration, sensory scene anchors, adjective discipline, truth tiers, and 100% adherence to all 17 points of the §10 Pre-Flight Checklist. Prepare visual intent cues for Stage 06 while keeping narration copy pure.
Reference: [STORYTELLING_WRITING_RULES.md](../../../Tips-Playbook/STORYTELLING_WRITING_RULES.md) and [Editing Toolkit](../EDITING_TOOLKIT.md).

> *Note: Plain-text project paths (e.g. `_pipeline/`, `01_research/`, `06_script_edit_plan/`) are relative to working directory `Videos-Scripts/<NN>_<Slug>/`. Markdown links are relative to this stage file.*

## Inputs
- `_pipeline/brief.md` (length profile and strict naming boundaries).
- `_pipeline/02_dna_report.md` (audience gaps and friction points).
- `_pipeline/03_hook_outline.md` & `_pipeline/approvals/G2_hook_outline.md` (approved narrative architecture).
- `01_research/FACT_BASELINE.md` & `01_research/QUOTE_PROOF.md` (verified facts and quotes).
- `03_media/BEST_LINES_SELFCHECK.txt` (framing verification).
- [STORYTELLING_WRITING_RULES.md](../../../Tips-Playbook/STORYTELLING_WRITING_RULES.md) & [AGENTS.md](../../../AGENTS.md) (§3 Storytelling).

## Outputs
- `06_script_edit_plan/Video_<NN>_Script_Draft_1.md` (working draft by Antigravity).
- `_pipeline/04_review_notes.md` (Sonnet review findings and line audit).
- `06_script_edit_plan/Video_<NN>_Script_Draft_2.md` (final script by Claude Opus).
- `_pipeline/04_opus_rating.md` (Claude Opus separate quality rating: 1–10).
- `06_script_edit_plan/visual_intents.md` (updated and refined visual intent cues for Stage 06 shot planning).
- `06_script_edit_plan/PREFLIGHT_01.md` (full verification of all 17 points of §10).
- `06_script_edit_plan/NAMING_REVERENCE_CHECK.txt` (grep check proof for formal names & exclusions).
- Superseded drafts archived to `old/`.

## Executor & Multi-Agent Script Chain
- **Draft Writer:** Antigravity (Gemini Flash medium). Permitted under `SKILL.md` §1 for draft generation.
- **Auditor / Reviewer:** Claude Sonnet, evaluating against [reviewers/script.md](../../../.agents/skills/orchestrate/reviewers/script.md) and outputting `_pipeline/04_review_notes.md`.
- **Final Script & Rating:** Claude Opus ingests `_pipeline/04_review_notes.md`, writes `Draft_2` incorporating review findings, completes pre-flight verification, and delivers a separate final rating (1–10) in `_pipeline/04_opus_rating.md`.

## Tools
- Markdown editor, word counter, regex script for sensational adjective scanning.
- `[TO BUILD]` Grep script for formal name compliance (`NAMING_REVERENCE_CHECK.txt`).

## Steps
1. **Verification:** Confirm `_pipeline/approvals/G2_hook_outline.md` matches `03_hook_outline.md`.
2. **Drafting (Antigravity):** Draft script adhering to café-friend tone, sensory anchors, and length profile word count (~2,250+ words for long, ~150 words/min of target runtime; 650–800 words for tribute).
3. **Adjective Discipline:** Ban sensational adjectives (*predatory, shocking, horrific, sickening*). Let dates, numbers, and primary quotes carry emotional weight.
4. **Truth Tiers:** Tag every factual statement: `[documented]`, `[reported]`, `[alleged]`, `[speculative]`.
5. **Visual Intents Separation:** Maintain 100% spoken narration purity in script body. Identify visual intents (character callouts, map-worthy beats, articles, transitions) mapped to [EDITING_TOOLKIT.md](../EDITING_TOOLKIT.md); append and refine tags in `06_script_edit_plan/visual_intents.md` so Stage 06 receives a closed chain.
6. **Review Audit (Claude Sonnet):** Audit draft against storytelling rules and quote provenance, saving findings to `_pipeline/04_review_notes.md`.
7. **Final Polish & Separate Rating (Claude Opus):** Ingest `_pipeline/04_review_notes.md` from disk, write `Video_<NN>_Script_Draft_2.md`, and record separate 1–10 quality rating in `_pipeline/04_opus_rating.md`.
8. **Pre-Flight Verification:** Complete and sign **all 17 points of §10 Pre-Flight Checklist** in `06_script_edit_plan/PREFLIGHT_01.md`.
9. **Naming Check (Video 010):** Execute grep script confirming zero occurrences of casual nicknames or excluded topics; output `NAMING_REVERENCE_CHECK.txt`.

## Acceptance Checklist
- [ ] Word count matches length profile (~150 words/min of target runtime for long; 650–800 for tribute).
- [ ] Zero sensational judgment adjectives; truth tiers explicitly annotated.
- [ ] All quotes verified in `01_research/QUOTE_PROOF.md`.
- [ ] Visual intents tagged and updated in `06_script_edit_plan/visual_intents.md` per [EDITING_TOOLKIT.md](../EDITING_TOOLKIT.md).
- [ ] `_pipeline/04_review_notes.md` and Opus rating (≥8/10) recorded.
- [ ] **All 17 points of §10 Pre-Flight Checklist** passed in `PREFLIGHT_01.md`.
- [ ] `NAMING_REVERENCE_CHECK.txt` confirms strict naming reverence.
- [ ] Numbered draft naming (`Draft_1`, `Draft_2`... never "FINAL").

## Reviewer & Rater
- Claude Sonnet reviews draft; Claude Opus provides final script and rating.

## Human Gate
- **Yes — Gate G3 (Script Gate):** Human operator inspects `Video_<NN>_Script_Draft_2.md` and Opus rating, then signs `_pipeline/approvals/G3_script.md`.

## Failure & Retry
- If rejected by reviewer or operator, increment draft number (Draft 3), archive previous to `old/`, and revise. Max 3 passes.

<span style="color: purple;">[AI Agent]</span>
