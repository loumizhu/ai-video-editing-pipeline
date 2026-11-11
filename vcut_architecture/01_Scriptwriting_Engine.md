# Step 01: Script Intake, Research & Scriptwriting

## Links
- **Hub:** [[Vcut_End_to_End_Pipeline_Architecture]] · **Contracts:** [[Vcut_Data_Contracts#3.1 script_manifest.json]], [[Vcut_Data_Contracts#3.9 intake.json (Mode S) and claims verdicts]]
- **Decisions:** [[Vcut_Decision_Log#ADR-001 — v1 product mode]], [[Vcut_Decision_Log#ADR-016 — AI providers and the no-AI path]]
- **Previous:** [[00_Brief_and_Orchestrator]] · **Next:** [[02_Voice_and_Timing]] ∥ [[03_Shot_Planning_and_Visuals]] (candidate search) ∥ [[04_Music_SFX_and_Ducking]] (sourcing)
- *Retitled 2026-10-26 from "Scriptwriting Engine": in v1 the owner brings the script ([[Vcut_Plan_Review_2026-10-26]] R1). The file name is kept so links stay stable.*

---

## Purpose
Produce a **locked, fact-checked script** with separate display and spoken text, and a structured visual plan
anchored to word spans, before any money is spent downstream. The starting point is chosen in the setup form
([[00_Brief_and_Orchestrator#Starting points]]), and every path ends in the same `script_manifest.json`:
- **Script ready (Mode S):** the owner supplies the script, with or without cues and instructions. **The writing step is skipped**: Vcut reads, checks and annotates it, and never rewrites it. With G2 on *Auto*, the run moves straight on to voice and media.
- **Brief only (Mode W, M2):** the owner supplies a brief; Vcut researches and drafts the script. Reviewing the outline (G1) and the script (G2) is optional, per the setup form.
- **Own recording:** with either path, if the owner uploaded narration, the locked script is the text 02 aligns it to. If the recording and the script differ (ad-libs), 02 reports the differences at G2 and the recording wins for timing.

## Inputs → Outputs
| Mode | In | Out |
|---|---|---|
| S | `00_input/script.*` (.txt, .md or .docx), optional `00_input/instructions.md`, `project.yaml`, `channel_profile.yaml` (calibrated WPM, lexicon, moods) | `script/intake.json` (01a) → `research/claims.json` + `research/sources/`, `script/script_manifest.json` (01b, G2) |
| W | `brief.yaml` (thesis, **human angle**, duration, tone, must-include/avoid), `channel_profile.yaml` | `research/claims.json`, `research/sources/`, `script/outline.json` (01a, G1) → `script/script_manifest.json` (01b, G2) |

---

## Script input format (Mode S)
Plain text or Markdown; .docx is converted to text first (headings kept). Nothing is mandatory: a script with no
markup at all is valid and becomes one chapter per blank-line-separated block of roughly 150–400 words.

| Write this | Meaning | Spoken? |
|---|---|---|
| `# The Problem` | Chapter heading (title used for chapter markers and YouTube chapters) | No |
| A blank line | Paragraph break = narration unit boundary + paragraph pause | — |
| `[visual: aerial of a substation at dusk]` | **Author visual cue** for the idea it sits in; it beats any AI or heuristic beat | No |
| `[chart: c-data centres share 2020–2024]` / `[card: "4%"]` | Graphic request; numbers must resolve to a claim | No |
| `[music: tense]` · `[music: off]` | Mood from here to the next music cue | No |
| `[sfx: whoosh]` | Narrative SFX at this word | No |
| `[effect: location stamp "VIENNA, 1914"]` · `[effect: old_film]` · `[effect: person card "Nikola Tesla"]` | An effect preset from [[Vcut_Effects_Library]] by id or name, with its values in quotes; its paired SFX comes with it | No |
| `[image: own/tesla_lab.jpg]` · `[clip: own/storm.mp4]` | Use this file from `00_input/media/` for the idea | No |
| `[pause 2s]` | Extra silence after this point | No |
| `[say: G P U]GPU` | One-off pronunciation for the next word (lexicon entries are global) | Only the respelling |
| `> quoted text` | A quotation; attributed and exempt from the originality rule if sourced | Yes |
| `<!-- note -->` | Comment for the owner; ignored | No |

Any **other** bracketed text is treated as a direction, **never spoken**, and listed at G2 as "unrecognised cue".
This is the guard against the v1 bug where `[B-ROLL: …]` brackets could be read aloud by TTS.

**`instructions.md` (optional, free text)** — e.g. "target 8 minutes, calm tone, use my recorded voice, no music in
chapter 3, avoid showing faces". Vcut maps what it can to structured settings (`target_duration`, voice, mood
overrides, negative terms) **and shows the mapping at G2** so the owner sees what was understood. With AI `none`,
only a small fixed vocabulary is recognised (duration, voice, tone word, "no music", "no faces"); the rest is
shown as "not applied".

---

## Process — Mode S (script-in)

### 01a Intake (code; AI optional)
1. **Read the source verbatim** from `00_input/` and hash it (Vcut never writes there). The hash is in every downstream fingerprint, so editing the script file re-runs exactly what it affects.
2. **Parse:** headings → chapters; paragraphs → units; sentences → lines (`line_id`s issued once, never renumbered, [[Vcut_Data_Contracts#1.2 Stable IDs]]). Cues are stripped into `cues[]` anchored to the word they precede.
3. **Segmentation check.** With AI: propose chapter splits for long unheaded blocks and flag units too long for one TTS call. With `none`: split on headings and paragraphs only; units over ~120 words are split at the nearest sentence end.
4. **Read the instructions** into structured settings (above).
5. **Duration estimate** from word count × the voice's *calibrated* WPM, compared with `target_duration` if one is set. In Mode S the script defines the length; a target is only a check.

### 01b Research, checking and annotation
6. **Claim extraction.** Every number, date, percentage, currency amount, proper name, quote and superlative becomes a candidate claim with its `line_id` and word span. AI adds paraphrased claims ("most of the world's…"); `none` uses regex and capitalisation rules only.
7. **Fact-check research.** For each claim, search through the research interface ([[Vcut_Tool_Allowlist#Research]]) and fetch supporting pages where terms allow. Record per claim: sources, retrieval date, a **verbatim supporting quote from the fetched page** (a search snippet is not verification), and a verdict ∈ `supported · partly · contradicted · not_found`. **Numbers need ≥2 independent sources** for `supported`.
   - With AI, it drafts the verdict from the fetched quotes. With `none`, Vcut attaches the top sources and the **owner sets each verdict at G2**.
   - Fetched text is **untrusted data** ([[00_Brief_and_Orchestrator#Secrets & data handling]]): it is stored as quotes and never passed on as instructions.
   - **The script is not changed.** A claim that fails gets a **proposed edit** (soften, correct, add a source mention), which the owner accepts or rejects at G2.
8. **Visual context research.** For named things the viewer should *see* (a place, a device, an organisation, a chart's data), collect search terms and reference facts so 03 can search for the right footage. This is what "research the script to find which clips fit" means in practice; it never downloads media.
9. **Originality check (code).** Sentence/n-gram overlap between the script and the fetched sources. More than 1–2 consecutive overlapping sentences is flagged unless it is a marked `>` quotation with a source. In Mode S this protects against a pasted passage the owner did not write (YouTube "reused content": readings of material you did not create).
10. **Normalisation (code).** Build `text_spoken` with the locale tables + lexicon + `[say:]` cues, and the `token_map` back to `text_display`. `text_display` is the owner's sentence exactly, minus cues.
11. **Visual beats & SFX intents → G2.** One beat **per idea, not per line**. Author cues become beats first (`source: author_cue`). For the remaining ideas: with AI, type, 3–5 search queries, must-show, negative terms, min/max seconds, fallback chain, `context_sentiment`; with `none`, keyword queries from the sentence's noun phrases (TF-IDF over the script), default type `stock_video`, default fallback chain. Chart and card beats must cite a `claim_id`.

## Process — Mode W (write-from-brief, M2)
1. **Research → claims ledger.** As step 7 above, but driven by the brief's thesis and `sources_required`.
2. **Outline & script bible → G1.** Chapters with goal, mood and **word budget** (target duration × calibrated WPM on the *spoken* form, minus planned pauses), a **promise/payoff map**, a hook concept, a style guide, key terms, a do-not-repeat list. The brief's `angle_and_perspective` must visibly drive the thesis.
3. **Chunked drafting.** One call per chapter, with the bible, the outline, a running "already covered" ledger, the last ~250 words of the previous chapter and the next chapter's summary. A factual specific may only be written by **referencing a `claim_id`**.
4. **Hook pass, against the finished body.** Three variants for the 0–30 s window, promising only items on the payoff map. The human picks one at G2.
5. **Whole-script edit.** One pass over the full text: repetition (backed by an automatic cross-chapter n-gram/embedding check), transitions, callbacks, tone, promises paid.
6. **Claim audit.** Any number, date, name, quote or superlative with no `claim_id`, or whose wording drifted from its claim ("up to 40%" → "40%"), fails.
7. Then steps 9–11 of Mode S.

Mode W needs AI (`drafting` role bound); with `none` it is unavailable.

## LLM vs deterministic code
- **AI (optional in Mode S):** segmentation proposals, instruction mapping, paraphrased-claim extraction, verdict drafting, visual beats. Mode W adds outline, drafting, hooks, edit. Every output is schema-constrained and validated; every Mode S AI step has the `none` fallback above.
- **Code:** parsing, cue stripping, ids, fetching, dedupe, overlap check, extraction regexes, normalisation, duration math, schema validation.

## Human gates
- **G1 Outline (brief start only; Review or Auto per the setup form):** thesis + chapter plan + budgets + promise map.
- **G2 Script lock**, before *any* TTS, download or generation:
  - [ ] Mode S: chapters, units and recognised cues look right; unrecognised cues resolved; instruction mapping confirmed;
  - [ ] Mode W: final text read through; hook variant chosen;
  - [ ] every claim has a verdict; `contradicted` / `not_found` claims fixed in the script or their proposed edit accepted;
  - [ ] lexicon approved (and any respellings proposed by 02 QC);
  - [ ] duration estimate within ±10% of the target, if a target is set;
  - [ ] the script carries the owner's own perspective, not just a summary of sources;
  - [ ] editorial/legal checklist: claims about named living people or organisations reviewed; medical, financial or election topics flagged; YouTube audience setting (made for kids: yes/no) decided.

  An accepted proposed edit changes the script through `vcut edit` (recorded as `human_edit`), never silently.
- **G2 on Auto / autopilot:** the run continues without the page above, except that it **stops** on a `contradicted` claim or an unrecognised cue. `partly` and `not_found` claims and pending proposed edits do not stop it: they become yellow review markers on the line in the editor, and are listed in `01_script/claims.md`. The script text is never changed automatically.

## Failure modes & fallbacks
| Failure | Response |
|---|---|
| Script has no headings | One chapter per block of ~150–400 words; the owner confirms at G2 |
| Claim with <2 sources | Verdict `partly` or `not_found`; propose a softened wording; the owner decides |
| Originality check fails | Flag the span; the owner rewrites it as commentary or marks it as an attributed quote |
| Search provider down | Fall back to the second provider behind the same interface; else continue with claims unchecked and **block G2** until the owner marks them |
| AI provider down or `none` | Use the no-AI fallback for that step; note it on the G2 page |
| Mode W chapter over/under budget | Re-draft that chapter only (bounded to 2 tries) |

## Cost & time
- **Mode S:** $0 with AI `none` or local and SearXNG; a few cents to ~$1 with a cloud `tagging` model and paid search *(est.)*. Seconds to minutes of compute; the owner's G2 review dominates.
- **Mode W:** ≈$1–3 LLM per 45-minute script *(est.: ~0.5M input / 0.1M output tokens at Sonnet-class pricing)*, plus search credits.

## Tools
Role-based AI configuration, **no pinned model names in the docs**; provider per role ∈ `cloud · local · agent · none` ([[Vcut_Decision_Log#ADR-016 — AI providers and the no-AI path]]). Research: Tavily or Perplexity Search/Agent API; self-hosted SearXNG as the free path. .docx conversion: a permissive-licence reader, checked at M1. **"Hemingway Editor API" removed (no public API exists).** Details: [[Vcut_Tool_Allowlist]].

## Acceptance tests
- **Mode S:** for every line, `text_display` equals the owner's source sentence with cues removed (diff = 0), unless an accepted `human_edit` changed it.
- No TTS text contains bracketed tags, comments or markup; every unrecognised cue appears on the G2 page.
- Every number, date, name and quote in `script_manifest.json` has a `claim_id` with a verdict, and each `supported` claim has a quote that supports it.
- A run with every AI role set to `none` produces a valid `script_manifest.json` from a plain-text script with no markup.
- Overlap check: no unattributed run of more than 2 sentences matching a source.
