# Vcut — Plan Review (2026-10-26)

> Third review of Architecture v2, this time **against the owner's stated goal** rather than against the plan's
> own internal consistency (which the 10-12 and 10-15 reviews covered).
> Back to [[AGENTS]] · Hub: [[Vcut_End_to_End_Pipeline_Architecture]] · Previous: [[Vcut_Plan_Review_2026-10-15]].
> Docs before this review: `_archive/Vcut_plan_v2_pre_script_input_2026-10-26.zip`. Before round 3 (2026-10-27):
> `_archive/Vcut_plan_v2.2_pre_native_effects_2026-10-27.zip`.

## The goal, in the owner's words (2026-10-26)
- **Input:** "I would input a script, either with instruction or not."
- **Process:** a multi-step tool that analyses the script, **researches** it, and finds clips that fit it.
- **AI:** "It might use at some point some AI from my AI agent or not."
- **Output:** "a full file that could fit into **DaVinci Resolve or FilmCraft**. Either way, it would output a video that I can edit and fix."

## Verdict
The plan's engineering core is sound and stays: canonical timeline JSON, LLMs decide by ID while code computes
frames, licence ledger, human gates, resumable runs. But on four points the plan builds a **different product**
from the one the owner described, and on one point (the MCP approval path) an earlier critical finding was never
applied to the docs.

| # | Sev | Gap between plan and goal | Change made |
|---|---|---|---|
| **R1** | **critical** | **Wrong entry point.** The plan's only input is a `brief.yaml` with a thesis, and Vcut writes the script. The owner brings **their own script**, with or without instructions. Nothing in the plan parses a script, keeps the owner's wording, or handles directions written inside it | **Two entry modes** ([[Vcut_Decision_Log#ADR-001 — v1 product mode]]): **Mode S, script-in** (v1 default) and **Mode W, write-from-brief** (kept, later). New stage **01a intake** parses the script, strips inline cues into structured hints, and never rewrites the owner's words. In Mode S, "research" means **fact-checking the script and gathering visual context**, not drafting. See [[01_Scriptwriting_Engine]] |
| **R2** | **critical** | **Resolve-only, and Studio-only for anything automated.** ADR-002 makes Resolve Studio (US$295) the master NLE and treats FCPXML import as a degraded "FREE mode". The owner wants Resolve **or FilmCraft** | **NLE-neutral output** ([[Vcut_Decision_Log#ADR-002 — NLE targets]]). The always-produced deliverable is an **interchange package**: FCPXML 1.10 + OTIO + linked media + a README. It imports into Resolve (free or Studio) **and** FilmCraft (FCPXML 1.9–1.11, OTIO, EDL, AAF per its README, checked 2026-10-26). Automated builds become optional adapters: Resolve Studio API, FilmCraft headless CLI/MCP. 06 is now [[06_NLE_Adapters]] |
| **R3** | major | **No watchable video without an NLE.** The plan's first viewable output is a Resolve timeline at stage 06. The owner expects "a video" | New stage **05b preview render** ([[Vcut_Decision_Log#ADR-017 — Preview render]]): FFmpeg renders a rough-cut MP4 straight from `vcut_timeline.json`, with burnt-in review markers. It is a check, not the master: the master is still rendered from the NLE after G4 |
| **R4** | major | **AI is assumed, always cloud.** Every judgement step is "LLM, role-based, cloud". The owner may use **their own agent**, or **no AI at all**. The workstation already runs Ollama with five local models (listed in [[00_Brief_and_Orchestrator#Reference runtime profile]]) and a Hermes agent | **Pluggable AI per role** ([[Vcut_Decision_Log#ADR-016 — AI providers and the no-AI path]]): provider ∈ `cloud · local · agent · none`. Every LLM step now names its **no-AI fallback** (heuristics + the human at the gate), so a run with `none` everywhere still produces a timeline |
| **R5** | **critical** | **C1 from 10-15 was never applied.** 00 still lists MCP tools `vcut_approve(gate)` and `vcut_run(stage)`, and ADR-009 still names MCP as a gate interface. An AI agent could approve G2/G3 and spend money; scraped text could tell it to | ADR-009 and 00 rewritten: MCP and the agent provider are **read-only plus `request_approval`**. Approvals come only from a human click in the Storyboard or `vcut approve` on a TTY |
| R6 | major | **The roadmap front-loads the hardest dependency.** M0 needs Resolve Studio for the API spike before anything else, and M1 needs the cloud LLM and Studio | Milestones re-cut ([[Vcut_Decision_Log#ADR-011 — Build order (MVP)]]): **M1 = script in → interchange package + preview MP4**, runnable with no AI, Kokoro, Pexels, Resolve free or FilmCraft. Studio API and FilmCraft automation move to M2 |
| R7 | minor | **Stale status lines.** The 10-15 review says "0 lines of code"; `src/vcut` now holds a runner, CLI, FastAPI board and tests, and `web/` a front end. The AGENTS workspace tree lists neither, nor `pipeline.yaml`, `research/` or the 10-15 review | AGENTS tree updated. Code impact listed below |

## What did not change
- `vcut_timeline.json` is still the one source of truth; FCPXML/OTIO are generated, never edited.
- No LLM writes a timecode. Licence ledger, the strict allow-list, no automated third-party video harvesting.
- G2 (script lock) still blocks all paid TTS, downloads and generation; G3 still blocks paid fill.
- Resolve Studio stays the **recommended** finishing tool when automation and the Fairlight Ducker are wanted.
- YouTube constraints: in Mode S the owner's own script is the strongest "inauthentic content" mitigation; the originality check still runs because a pasted script can be someone else's text.

## Open decisions for the owner
These block M0/M1. Every ADR is still **Proposed**; flip to Accepted or rewrite.
1. **ADR-001:** confirm Mode S (your own script) is v1 and Mode W (Vcut writes the script) is later.
2. **ADR-002:** which NLE do you finish in first: Resolve (free, via FCPXML import) or FilmCraft? Both get the same package; the answer decides which import the M0 spike tests first.
3. **ADR-016:** for M1, which AI provider per role: `none`, `local` (Ollama), `agent` (Hermes) or `cloud`? The plan works with `none`; it is better with at least `tagging` bound.
4. **ADR-008:** narration for M1: Kokoro (free, local), ElevenLabs (paid) or your own recorded voice.
5. **Script format:** is plain text / Markdown with `#` chapter headings and `[visual: …]` cues acceptable (see [[01_Scriptwriting_Engine#Script input format (Mode S)]])? If your scripts already use a format, say which.

## Impact on existing code
Not fixed now: the owner asked for planning only.
The skeleton in `src/vcut` and `web/` was written against `vcut.pipeline/2`. `pipeline.yaml` was **left
unchanged** for that reason (the runner and tests read it); its header now says it is pending v3.
At the next code step:
- **pipeline.yaml → `vcut.pipeline/3`** per [[Vcut_Data_Contracts#3.7 pipeline.yaml (the pipeline orchestration manifest)]]: add `01a_intake` (Mode S), the stage `modes` filter, `05b_preview`, rename `06_resolve` → `06_nle_build`, provider enum on roles. Tests that assert `stages[0] == "01a_research_outline"` will need updating.
- `core/models.py` `StageConfig.resource` adds `nle`; the `resolve` value goes. `web/src/api/client.ts` mirrors it.
- **Security, high:** `api/server.py` serves approval and run endpoints with `allow_origins=["*"]` and a default `approved_by="human_operator"`. Any web page open in the same browser could POST an approval to the local board. Restrict CORS to the board's own origin, require a per-session token, and reject approvals that do not come from the board UI or a TTY (ADR-009).
- `approve_gate` must record the real operator name and refuse calls from the MCP or agent path.

## Recommended order
1. Answer the five open decisions above.
2. `git init` and commit (still open from 10-15, D3); the zip archives can then stop.
3. **M0 spike (2–3 days):** one hand-made 60 s fixture → FCPXML 1.10 + OTIO → import into **Resolve free and FilmCraft** → fill both columns of the capability matrix in [[06_NLE_Adapters#Capability matrix]]. Test the `((_atWork_))` path in both.
4. Migrate `pipeline.yaml` and the runner to v3; fix the board's CORS/approval path.
5. M1 vertical slice: your own 3–5 min script, end to end, no paid services.

## Round 2 — the owner's clarifications (same day)
Docs before round 2: `_archive/Vcut_plan_v2.1_pre_autopilot_effects_2026-10-26.zip`.

| Owner said | Plan change |
|---|---|
| "The starting point could be a brief, or the script itself, or the script with instructions and visual/SFX instructions… if I have a script, that step is good to go" | ADR-001: four starting points (brief · script · script + cues · + own recording). A provided script skips writing entirely; a brief gets a generated script, reviewed or not. New cues: `[effect: …]`, `[image: …]`, `[clip: …]` ([[01_Scriptwriting_Engine#Script input format (Mode S)]]). Brief start moved up to M2 |
| "At the beginning I should have all of the choices… a checkbox that automates everything until it outputs inside the video editor" | **ADR-018**: one setup form with every option, saved in `project.yaml`; per-gate Review/Auto; **autopilot** = all Auto + open in the editor. ADR-009 rewritten: the owner's autopilot policy can pass G1–G3; G4 stays the owner; stop conditions (budget, contradicted claim, unfilled slots) |
| "Output inside the video editor, Resolve or FilmCraft" | ADR-002 + [[06_NLE_Adapters#Opening the result in the editor ("open when done")]]: Resolve Studio = full automation; Resolve free = one click (to verify); FilmCraft = full once its CLI import is verified. **Full autopilot into Resolve needs Studio** |
| "I don't understand why you say no video unless you open an editor" | That described the *old* plan, which had no watchable output before the editor; the fix (ADR-017, preview MP4) stays. Both now exist: a preview MP4 **and** the timeline opened in the editor |
| "There should be a step where you research all of the media… images, videos, clips, footage" | It existed as 03a "candidate search"; now named **media research** and widened: own media first, stock video **and photos**, **Wikimedia Commons**, entity lookup for person/org cards, article captures (M2), maps (M3) ([[03_Shot_Planning_and_Visuals#Media types a documentary needs]]) |
| "Each video has its own folder and subfolders and organisation" | **ADR-019**: `projects/<date>_<slug>/` with readable `00_input … 07_delivery` folders (media filed by chapter, readable names) over a `.vcut/` system folder; the owner writes only in `00_input` ([[00_Brief_and_Orchestrator#Workspace layout]]) |
| "AI: cloud, local Ollama, or what I have installed like Claude Desktop or Antigravity… Antigravity as the default" | ADR-016: **Antigravity default**, via a task-file interface and `antigravity-ide chat -m agent` (checked locally, v1.107.0; it runs in a window, no verified headless mode). Claude Code headless; Claude Desktop pull-only via MCP; Ollama; cloud; none. Agent workspaces confined; approvals HMAC-signed |
| "Voice: my local Qwen TTS, Kokoro, ElevenLabs, or my own recording, uploaded at the first step" | ADR-008: **Qwen3-TTS default local voice** (code Apache-2.0; weights licence to confirm; timing by forced alignment). Recording uploaded at setup into `00_input/recordings/` |
| "Faceless documentary… effects like light moving around, old effect… labels and text with their sound effect… article screenshot with highlight… person cards" | **ADR-020** + new [[Vcut_Effects_Library]]: ~60 presets in 8 families (looks, overlays, motion, transitions, text with paired SFX, documents/articles, people/orgs, data/maps), ~20 in M1; density and rotation rules; EffectCraft CLI (installed) proposed as the template renderer |

**New open decisions from round 2**
1. **Resolve Studio or not?** Full autopilot into Resolve needs it (US$295). Without it: one click in free Resolve (if the M0a test confirms), or FilmCraft.
2. ~~**Install FilmCraft?** It is not on this machine~~ *Answered in round 3: FilmCraft 0.13.0 was already installed in `C:\Program Files\FilmCraft\`.*
3. **Article screenshots:** keep the re-typeset card as the default, with real screenshots opt-in per video (proposed), or the reverse?
4. **Qwen3-TTS:** where is your set-up installed, and which voice/reference clip should be the channel default?

**More code impact** (on top of the list above): `vcut new` takes a title and files instead of an id; the project folder layout changes (`projects/ai_video_essay_001` uses the old layout); approvals move to `.vcut/approvals/` with an HMAC; the Storyboard needs the setup form page.

## Round 3 (2026-10-27)
The owner: FilmCraft is installed at `C:\Program Files\FilmCraft\filmcraft.exe`; "in the autopilot mode the user
can choose between DaVinci Resolve or FilmCraft. The default for now is DaVinci Resolve"; "for now we don't need
effect graphs for these simple effects like labels or … transitions. I want to be able to edit the video in one
single software."

| Owner's statement | Plan change |
|---|---|
| "FilmCraft … is installed" | Confirmed: **0.13.0**, `filmcraft.exe` + `filmcraft-cli.exe` (files dated 2026-10-25). *Round 2 said "not installed" because it looked only in `%LOCALAPPDATA%\Programs`; that was wrong.* A headless probe in a scratch folder built a sequence with placement, Motion keyframes, a dissolve, Light Leaks/Noise/Vignette, a text graphic, a graphics template re-applied with a new value, a chapter marker and a frame render ([[06_NLE_Adapters#FilmCraft]]). FilmCraft's FCPXML/OTIO export drops its own text graphics, so FilmCraft is built from **CLI commands**, not from the package |
| "Choose between Resolve or FilmCraft; default Resolve" | ADR-002 / ADR-018: **one editor per video, default DaVinci Resolve**; autopilot ends inside whichever was chosen. Full autopilot into Resolve still needs **Studio**; free Resolve is one click (to verify); FilmCraft is full today |
| "No effect graphs for simple effects … edit the video in one single software" | New **ADR-021**: every title, label, card, transition, look, overlay and push-in is a **native object of the chosen editor**, filled in by Vcut from per-editor preset implementations (Resolve Fusion title templates, `.drx` grades, composite modes; FilmCraft `.fcgt` templates, its effects and 112 transitions). **EffectCraft, `values.json` and `vcut rerender` are withdrawn**; ADR-012 and ADR-020 revised; the [[Vcut_Effects_Library]] now lists the Resolve and FilmCraft implementation of each preset (20 in M1). Effects with no native route (parallax, newsprint, animated route maps) wait for an M3 opt-in pre-render |
| (consequence) | The preview MP4 is rendered **by the editor** where it can run headless (FilmCraft CLI `export`, Resolve Studio render job); FFmpeg stays as an approximation on free Resolve (ADR-017). Ducking prefers native (Resolve Ducker, FilmCraft volume keyframes), with the baked stem as fallback. The FCPXML/OTIO package is a backup only, with a `titles.csv` |

Also checked: the Resolve scripting README installed with 20.0.1 ("Last Updated: 7 May 2025") lists the calls the
native Resolve build needs: `InsertFusionTitleIntoTimeline`, `GetFusionCompByIndex`, `ImportFusionComp`,
`ApplyGradeFromDRX`, `SetLUT`, the `CompositeMode` property and `AddMarker`. It has no transition call, so dissolves on
Resolve below Studio 21.1 still come in through an FCPXML import step. None of the Resolve calls has been run yet.

**Open decisions after round 3**
1. **Resolve Studio or not?** Resolve is now the default editor, so this decides whether the default autopilot stops at one click (free) or not at all (Studio, US$295).
2. **Who builds the preset templates?** About 20 per editor for M1, made by hand once in Resolve (Fusion titles, `.drx` looks) and in FilmCraft (`.fcgt`). Proposed order: Resolve first, FilmCraft second.
3. **Article screenshots** and **Qwen3-TTS location/voice**: still open from round 2.

**Code impact of round 3:** the adapter layer becomes `resolve_build` (script for Studio or the Scripts menu) and `filmcraft_build` (writes `build.jsonl`, runs `filmcraft-cli`, reads back with `inspect sequence`); the timeline schema gains `title` clips and `effects[]`; `vcut.effect/2` preset files; no renderer module.

## Sources checked for this review (2026-10-26)
- FilmCraft README, `github.com/storytold/filmcraft`: MIT OR Apache-2.0; alpha; Windows x64 installers; imports/exports FCP7 XML, FCPXML 1.9–1.11, OTIO (`metadata.filmcraft`), CMX 3600 EDL, AAF, OMF 2.0; `filmcraft-cli` (650+ commands), headless MCP server (`filmcraft-cli -- mcp`), JSON-lines TCP control channel; exports H.264 MP4, ProRes 422 HQ, DNxHR MXF, PNG sequence, WAV. The README notes that "Windows and Linux get far less testing than macOS".
- Local Ollama model list (`ollama list` through the agent-workers MCP), this workstation.
- Round 2: `antigravity-ide --help` / `chat --help` (Antigravity IDE 1.107.0); `effectcraft-cli --help`; PATH lookups (`agy` absent, `claude` and `ollama` present); `%LOCALAPPDATA%\Programs` listing (no FilmCraft); Qwen3-TTS README `github.com/QwenLM/Qwen3-TTS`; third-party pages on the `agy` CLI (computingforgeeks cheat sheet, glama.ai MCP listings), treated as unverified.
