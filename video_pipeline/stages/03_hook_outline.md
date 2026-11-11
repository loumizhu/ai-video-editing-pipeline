# Stage 03: Hook & Narrative Architecture

## Purpose
Architect the storytelling backbone: select a single held-back hook engine, land the first hook within 20–40 s, map progressive open loops, plan chapter beats based on the chosen length profile, and tag narrative beats with visual intents.
Reference: [STORYTELLING_WRITING_RULES.md](../../../Tips-Playbook/STORYTELLING_WRITING_RULES.md) and [Editing Toolkit](../EDITING_TOOLKIT.md).

> *Note: Plain-text project paths (e.g. `_pipeline/`, `01_research/`, `03_media/`, `06_script_edit_plan/`) are relative to working directory `Videos-Scripts/<NN>_<Slug>/`. Markdown links are relative to this stage file.*

## Inputs
- `_pipeline/brief.md` (length profile and owner creative direction).
- `_pipeline/01_scout_dossier.md` & `_pipeline/approvals/G1_topic.md` (topic approval).
- `_pipeline/02_dna_report.md` (audience gaps and competitor leaks).
- `01_research/FACT_BASELINE.md` & `01_research/QUOTE_PROOF.md` (verified facts and quotes).
- `03_media/BEST_LINES_SELFCHECK.txt` (eyes and framing proof from Stage 02).
- [STORYTELLING_WRITING_RULES.md](../../../Tips-Playbook/STORYTELLING_WRITING_RULES.md) (§2 Engines & §3 Loops).
- [AGENTS.md](../../../AGENTS.md) (§3 Storytelling Standard).

## Outputs
- `_pipeline/03_hook_outline.md` (hook engine, crucible opening, loop map, chapter breakdown with visual intent notes).
- `06_script_edit_plan/visual_intents.md` (initial visual intent tags per narrative beat; refined in Stage 04, consumed in Stage 06).

## Executor
- **Worker:** Claude Sonnet, effort: medium. (Authorized under `.agents/skills/orchestrate/SKILL.md` §1 for outline drafting; reviewed by Claude Opus under §4).

## Tools
- Markdown editor, word-count/runtime calculator (150 wpm).

## Steps
1. **Length Profile Calibration (Video 010):** Read `length_profile` from `_pipeline/brief.md`:
   - `documentary_long` (Default): 15 min–3 h, ~150 words/min; 45–120 min suits TV/older audiences, ≥5 open loops per 20m, ≥2 active across chapter breaks.
   - `tribute_short` (Opt-in only): 4:30–5:15 runtime (~650–800 words), ≥3 open loops, tight emotional focus.
2. **Hook Engine Selection:** Select ONE engine from `STORYTELLING_WRITING_RULES.md` §2 (e.g. Hidden Contradiction, The Missing 48 Hours, The Documented Lie).
3. **0–60s Crucible Opening:** First hook lands within 20–40 seconds; open ONE core mystery (never multiple stars in the first 60 s). Plant a fresh hook every ~60–90 seconds after that. Strict ban on corpse cold opens and throat-clearing fluff.
4. **Held-Back Reveal:** Anchor the central revelation to land at 85–95% of total runtime.
5. **Progressive Loops:** Ensure new loops open before previous loops close; bridge every chapter break with active narrative tension.
6. **Scene & Quote Grounding:** Anchor beats in physical rooms, concrete dates, documents, and verified quotes from `01_research/QUOTE_PROOF.md`.
7. **Visual Intents Tagging:** Tag narrative beats with visual intents (character introduction callout? map worthy beat? newspaper/article display? transition type?) per [EDITING_TOOLKIT.md](../EDITING_TOOLKIT.md). Write and save tags directly to `06_script_edit_plan/visual_intents.md`; script VO copy remains 100% clean spoken narration.
8. **Eyes & Framing Check (Video 010):** Check `03_media/BEST_LINES_SELFCHECK.txt` contact sheets to confirm who the speaker addressed before attributing dialogue.
9. **Compile Outline:** Save outline to `_pipeline/03_hook_outline.md`.

## Acceptance Checklist
- [ ] Exactly one proven hook engine selected and named.
- [ ] Core mystery introduced in first 60 seconds (no corpse opening, no fluff).
- [ ] Central mystery resolution placed strictly at 85–95% of target runtime.
- [ ] Loop requirements met for profile (≥5 loops for long; ≥3 loops for tribute).
- [ ] Visual intents tagged and saved to `06_script_edit_plan/visual_intents.md` per [EDITING_TOOLKIT.md](../EDITING_TOOLKIT.md).
- [ ] Eyes & framing checked against `BEST_LINES_SELFCHECK.txt` before attributing dialogue.
- [ ] Runtime and word count aligned with `length_profile`.
- [ ] Saved to `_pipeline/03_hook_outline.md`.

## Reviewer
- Claude Opus via [script.md](../../../.agents/skills/orchestrate/reviewers/script.md) (citing `SKILL.md` §4).

## Human Gate
- **Yes — Gate G2 (Hook & Outline Gate):** Human operator inspects narrative engine and signs `_pipeline/approvals/G2_hook_outline.md` before scripting starts.

## Failure & Retry
- If rejected by Opus or operator, rebuild hook engine or re-sequence loops. Max 3 passes.

<span style="color: purple;">[AI Agent]</span>
