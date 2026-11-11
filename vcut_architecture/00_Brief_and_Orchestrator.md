# Step 00: Script, Brief, Channel Profile & Orchestrator

## Links
- **Hub:** [[Vcut_End_to_End_Pipeline_Architecture]] · **Contracts:** [[Vcut_Data_Contracts]] · **Decisions:** [[Vcut_Decision_Log#ADR-005 — Orchestration runtime]]
- **Next step:** [[01_Scriptwriting_Engine]]

---

## Purpose
Define **what the user puts in**, **where everything lives**, and **how the multi-step tool runs, fails,
resumes, spends money and shows its work**. In v1 this whole section was missing: the only input was
"Concept / Prompt", and no runner, layout, cache, retry, budget or secret handling was specified.

---

## Inputs
A new video starts with the **setup form** (Storyboard → *New video*, or `vcut new` with flags), where every
choice is made up front ([[Vcut_Decision_Log#ADR-018 — Project setup options and autopilot]]). The only required
inputs are a **title** and **one starting file**: a script or a brief. Everything else has a default.

### Starting points
Decision: [[Vcut_Decision_Log#ADR-001 — v1 product mode]].

| I have… | Put it in | Vcut then… |
|---|---|---|
| a **script** | `00_input/script.md` (or .txt / .docx) | parses and checks it; **no writing step** |
| a script **with cues** | the same file, with `[visual: …]`, `[effect: …]`, `[sfx: …]`, `[music: …]`, `[pause 2s]` (format: [[01_Scriptwriting_Engine#Script input format (Mode S)]]) and/or `00_input/instructions.md` | uses the cues as given; fills only the gaps |
| a **brief** | the form's brief fields → `00_input/brief.yaml` | researches and writes the script (review optional) |
| my **own narration** | `00_input/recordings/` (one take per chapter, or per paragraph) | aligns it instead of synthesising a voice |
| my **own images/clips** | `00_input/media/` (with a note of their licence) | searches them first, before stock |

Vcut stores every input verbatim and never edits it.

### `project.yaml` — the setup choices
Written by the setup form; the owner may edit it by hand. Fields are defined in
[[Vcut_Data_Contracts#3.10 project.yaml (setup options)]]. Example:
```yaml
schema: vcut.project/1
project_id: 2026-10-26_why-ai-needs-electricity
title: "Why AI needs so much electricity"
start_from: script_with_cues         # brief | script | script_with_cues
own_recording: false
reviews: { G1_outline: review, G2_script: review, G3_media: auto }   # review | auto
autopilot: false                     # true = every gate above auto, result opened in the editor
editor: { target: resolve, open_when_done: true }                  # resolve (default) | filmcraft; one editor per video, autopilot ends in it
ai:   { drafting: antigravity, tagging: antigravity, vision: none } # antigravity | claude_code | claude_desktop | ollama:<model> | cloud:<role> | none
voice: { engine: qwen3_tts, voice_id: "owner_clone", speed: 1.0 } # qwen3_tts | kokoro | elevenlabs | recording
style: { preset: documentary, look: archival, effect_density: medium, text_style: typewriter }
media: { sources: [own, library, pexels, pixabay, wikimedia], article_captures: false, generative: false, photo_share: 0.4 }
length: { target_min: [8, 10] }      # optional when starting from a script
money: { budget_usd: 0, autopilot_spend_limit_usd: 0 }             # 0 = free sources only
output: { captions: true, chapters: true, preview: true }
privacy: cloud_allowed               # cloud_allowed | local_only
```

### `brief.yaml` (brief start only)
```yaml
schema: vcut.brief/2
thesis: "Compute demand is outrunning grid build-out; efficiency gains are being eaten by scale."
angle_and_perspective: |        # REQUIRED: the human's own view (inauthentic-content mitigation)
  I think the real story is local grids, not global totals...
audience: "curious non-engineers"
tone: "measured, investigative"
must_include: ["grid interconnection queues"]
must_avoid: ["stock-market predictions"]
sources_required: ["IEA Electricity 2025 report"]
language: en
locale: en-GB
quality_tier: final             # draft | final
generative_video_max_pct: 10
deadline: 2026-10-30
```
*Moved to `project.yaml` on 2026-10-26: `mode`, `script_file`, target length, budget, privacy (they apply to every starting point).*

### `channel_profile.yaml` (reused across videos)
```yaml
schema: vcut.channel/2
channel_id: my_channel
editor_default: resolve          # ADR-002; pre-fills the setup form (resolve | filmcraft)
editors:                         # pinned versions on this machine (capability matrix columns)
  resolve:   { version: "20.0.1", edition: free }       # free = one-click build; studio = full autopilot
  filmcraft: { version: "0.13.0", cli: "C:/Program Files/FilmCraft/filmcraft-cli.exe" }
ai_defaults:                     # ADR-016; pre-fills the setup form; project.yaml `ai` overrides per video
  drafting: antigravity          # agent apps: antigravity | claude_code | claude_desktop | hermes
  tagging:  antigravity          # or ollama:<model>, cloud:<vendor-model>, none
  vision:   none
voice: { engine: qwen3_tts, voice_id: "owner_clone", speed: 1.0, calibrated_wpm: 158 }   # defaults for the form; calibrated_wpm is measured per voice
style_defaults: { preset: documentary, look: archival, effect_density: medium, text_style: typewriter }   # Vcut_Effects_Library
lexicon:                         # applied to every TTS call; approved at G2
  - { written: "GPU", spoken: "G P U" }
  - { written: "IEA", spoken: "I E A" }
delivery: { width: 1920, height: 1080, rate: "30/1", color: rec709 }
effects: { library: "libraries/effects/", muted_sfx_presets: [] }
brand: { intro: "libraries/brand/intro.mov", outro: "libraries/brand/outro.mov", base_layer: "libraries/brand/plate_loop.mov",
         fonts: ["Inter", "Source Serif 4"], palette: ["#0E1116", "#F2B33D"] }
music: { library: "libraries/music/", moods: ["tense", "curious", "resolved"] }
sfx:   { library: "libraries/sfx/", max_transitional_per_min: 2 }
licence_policy: strict           # see Vcut_Tool_Allowlist
disclosure_default: computed     # ADR-014
```

### `pipeline.yaml` (the pipeline orchestration manifest)
One file orchestrates the run: [`pipeline.yaml`](pipeline.yaml) at the vault root is the default, and a
project may override it. **It is not copied here**, so it cannot drift. Fields are defined in
[[Vcut_Data_Contracts#3.7 pipeline.yaml (the pipeline orchestration manifest)]].

- **Stages** use the canonical ids (01a, 01b, 02, 03a–03e, 04a, 04b, 05, 05b, 06, 07a, 07b). `depends_on` forms a DAG, so 02, 03a and 04a run in parallel after G2, and 05b ∥ 06 after 05. Stages carry `modes` (S = script start, W = brief start); a stage outside the project's starting point is skipped.
- **Gates** G1 (after 01a, brief start only), G2 (after 01b), G3 (after 03b, *before* any paid fill) and G4 (after 07a, before packaging). Each is reviewed or auto-passed per `project.yaml` `reviews` / `autopilot`. Each approval records the hashes of the artifacts it approves.
- **Loops** L1–L4 are the only backward edges, each with `max_rounds`.
- **AI by role** (`role:drafting`, `role:tagging`, `role:vision`), each bound per project in `project.yaml` `ai` (default from `channel_profile.yaml`) to an agent app (default **Antigravity**), an Ollama model, a cloud API or `none` ([[Vcut_Decision_Log#ADR-016 — AI providers and the no-AI path]]).
- *The root `pipeline.yaml` is still `vcut.pipeline/2` (the code reads it); migrating it to `/3` is the first code task ([[Vcut_Plan_Review_2026-10-26#Impact on existing code]]).*
- **Orchestration only.** No tunable values (thresholds, depths, loudness, delivery format, naming); those live in the step docs, Data Contracts and `channel_profile.yaml`.

---

## Workspace layout
Decision: [[Vcut_Decision_Log#ADR-019 — Per-video folder organisation]]. **Every video has its own folder.**
Inside it, numbered folders hold the *current* version of everything under readable names; a system folder,
`.vcut\`, holds the machine's history. The owner only ever writes into `00_input\`.

```
E:\((_atWork_))\Vcut\
├── docs (this vault: *.md), pipeline.yaml
├── libraries\                          # shared by every video of the channel
│   ├── effects\                        # presets by category (Vcut_Effects_Library), each with a resolve\ and a filmcraft\ implementation + overlay_media\
│   ├── sfx\<category>\                 # whoosh, typewriter, paper, camera, stamp_pin… (each file in the ledger)
│   ├── music\<mood>\                   # licensed beds with their licence files
│   ├── brand\                          # intro, outro, base plate, fonts, LUTs
│   ├── media\                          # the owner's reusable images/clips + stock promoted from past videos
│   └── asset_registry.json             # channel ledger + usage history (re-use caps)
└── projects\
    └── 2026-10-26_why-ai-needs-electricity\      # <date created>_<title slug>
        ├── project.yaml                # the setup choices
        ├── STATUS.md                   # human-readable progress: stage, waiting on, spend, links to outputs
        ├── 00_input\                   # ← the ONLY folder the owner writes in
        │   ├── script.md · instructions.md · brief.yaml
        │   ├── recordings\             # own narration
        │   └── media\                  # own images/clips (+ licence notes)
        ├── 01_script\
        │   ├── script_locked.md        # the locked script, readable, with chapter headings
        │   ├── claims.md               # every claim with verdict and sources (readable version of claims.json)
        │   ├── sources\                # fetched pages, for audit
        │   └── data\                   # intake.json · claims.json · script_manifest.json
        ├── 02_voice\
        │   ├── narration_full.wav      # the whole narration in one file, for listening
        │   ├── units\ch01.u001.wav …   # the per-paragraph clips placed on the timeline
        │   └── data\timing.json
        ├── 03_media\
        │   ├── 01_the-problem\         # one folder per chapter, files in timeline order:
        │   │   ├── s0003_server-aisle__pexels-3129957.mp4
        │   │   ├── s0004_substation-photo__commons-81234.jpg
        │   │   └── alternates\s0003\…  # the 2 runner-up candidates per slot
        │   ├── 02_the-grid\ …
        │   ├── overlays\               # overlay clips (dust, scratches, paper…) used in this video
        │   ├── titles.md               # every title/card and its text (they are built natively in the editor)
        │   ├── contact_sheet.html      # every slot with its pick, alternates, licence, cost
        │   └── data\                   # candidates.json · shot_plan.json · cut_list.json
        ├── 04_audio\
        │   ├── music\ · sfx\           # the beds and effects used
        │   ├── music_ducked.wav        # baked ducked bed (+ the un-ducked original in music\)
        │   └── data\                   # shortlist.json · audio_plan.json
        ├── 05_timeline\
        │   ├── preview.mp4             # watchable rough cut, rendered by the editor (FilmCraft, Resolve Studio) or by FFmpeg (not the master)
        │   ├── qa_report.md            # readable QA summary (+ data\qa_report.json)
        │   └── data\                   # vcut_timeline.json · vcut.fcpxml · vcut.otio
        ├── 06_editor\
        │   ├── resolve\                # .drp backup + build report (when the editor is Resolve)
        │   ├── filmcraft\              # <project>_v<NNN>.fcproj + build.jsonl + build report (when the editor is FilmCraft)
        │   └── package\                # backup for a manual import (fcpxml, otio, media links, markers.csv, titles.csv, README_import.md)
        ├── 07_delivery\                # master.mp4 (rendered from the editor), captions, chapters.txt, description.md, credits.txt, upload_checklist.md
        └── .vcut\                      # system folder: the owner never needs to open it
            ├── runs\<run_id>\          # immutable run outputs (ADR-005); the numbered folders link into the newest
            ├── current\                # <stage_id>.json pointers (runner-only)
            ├── assets\                 # content-addressed originals + conformed\ + asset_registry.json
            ├── ledger\ · approvals\ · agent_tasks\ · cache\ · run.lock
            └── overrides.yaml          # G3 pins / rejects / re-queries (written by the Storyboard)
```

- **How the numbered folders stay current:** when a stage completes, the runner rebuilds its folder as **hard links** to the files in `.vcut\` (same NTFS drive: no extra space; otherwise copies). A re-run replaces the links; older versions stay in `.vcut
uns\` until `vcut gc`.
- **Names:** `<slot_id>_<3-word description>__<source>.<ext>`, chapter folders `<NN>_<chapter-slug>`. The `asset_id` is in the ledger and the clip metadata, so nothing depends on the readable name.
- **Editing a numbered folder has no effect** (it is rebuilt). Edits belong in the editor or in `00_input\`.
- **Disk:** about 50–150 GB per 45-min video (originals + conformed + renders); `vcut clean <project>` after G4 removes conformed copies and old runs, keeping inputs, the package media and delivery.

## Run model
1. **File-based Step Forwarding (No Database):** 
   - Orchestration is deterministic Python code executing `pipeline.yaml`.
   - Each stage executes its configured tools (`tool_choice`) and writes the outputs declared in `pipeline.yaml` (per-run under `.vcut/runs/<run_id>/`, shared assets and ledger under `.vcut/`; the numbered folders are then relinked).
   - A stage **waits for the verified output files of every stage in its `depends_on`** before starting; independent branches (02 ∥ 03a ∥ 04a) run concurrently within their resource class.
2. **AI is a pluggable worker, never the orchestrator** ([[Vcut_Decision_Log#ADR-016 — AI providers and the no-AI path]]):
   - AI does not own sequence, state, timing or approvals.
   - Each AI role is bound to an **agent app on this computer** (default **Antigravity**; also Claude Code, Claude Desktop, Hermes), a **local Ollama model**, a **cloud API**, or `none`. The runner calls the bound provider for a discrete task (extract claims, propose beats, choose a candidate by id, draft a chapter) and validates the JSON answer against its schema before use.
   - **Agent task interface:** Vcut writes `.vcut/agent_tasks/<task_id>/task.json` (instructions, allowed inputs as quoted data, the answer's JSON Schema) and waits for `answer.json` in the same folder (timeout, then retry once, then the no-AI fallback). Launch per app ([[Vcut_Decision_Log#ADR-016 — AI providers and the no-AI path]]):
     - **Antigravity:** `antigravity-ide chat -m agent -n -a task.json "<prompt>"` with that task folder as the window's workspace. One window per batch of tasks (all claims of a chapter in one task), not per item, to keep it fast. The window closes when the answer arrives.
     - **Claude Code:** `claude -p` headless, JSON out *(flags to verify at M1)*.
     - **Claude Desktop:** pull mode through `vcut mcp` (`vcut_next_task` / `vcut_submit_answer`); needs an open chat, so not for autopilot.
     - The agent's workspace is only the task folder. It never sees `project.yaml`, `approvals/` or other projects.
   - **`none`:** the stage runs its documented no-AI fallback; what it cannot decide is shown to the human at the next gate (or marked in the editor under autopilot).
3. **Approval Gating:**
   - If a stage declares an `approval`, the runner halts after writing that stage's outputs, **unless `project.yaml` sets that gate to `auto` (or `autopilot: true`) and none of the autopilot stop conditions holds** ([[Vcut_Decision_Log#ADR-009 — Human gates]]); then the runner writes the approval itself, signed `autopilot (policy set by <owner>)`, and carries on.
   - Otherwise the runner waits until the owner approves the gate (writing `approvals/<gate>.json` with the hashes of the gate's `approves` artifacts). Downstream stages refuse to run unless those hashes still match, so an approval survives a new run whose approved content is unchanged.
4. **Pure functions & Item Caching:**
   - Work is per item (line, unit, beat, slot, asset). Each item's output is cached under the hash of its inputs.
   - Re-running recomputes only changed items.
   - **Runs inherit unchanged stages.** A run is one forward pass. A stage whose fingerprint (tools, versions, role→model, params, input hashes) matches `current/<stage_id>.json` is inherited, not copied, and `run_manifest.json` points its paths at the source run. Gate-approved stages re-run only when their *inputs* change, never just because a tool or model was upgraded. Post-gate edits go through `vcut edit`, which starts a new run; completed run folders are immutable ([[Vcut_Decision_Log#ADR-005 — Orchestration runtime]]).
5. **Partial success is valid:** A stage finishes with a list of failed items instead of aborting. Unfillable slots drop to fallback chains and get review markers.
6. **Resource classes:** `network` stages run in parallel. `gpu` stages run sequentially on a single GPU queue (Kokoro, forced alignment, faster-whisper QC, a `local` AI model, NVENC preview encodes, all sharing the 16 GB card). `nle` (Resolve or FilmCraft running) is needed only by an automated build in 06; the interchange package needs no NLE.
7. **Budget:** Before each gate, the orchestrator computes the estimated cost and ETA. Actual spend is tracked per call, and execution halts before exceeding `budget_usd` (or the autopilot spend limit, whichever is lower, under autopilot).
8. **Autopilot run, end to end:** setup form → 01 (write or parse) → G1/G2 auto → 02 ∥ 03a ∥ 04a → 03b → G3 auto (if within budget) → fill, conform, assemble, audio → 05 compile + QA → 05b preview ∥ 06 package → **open in the chosen editor** (full automation or the one-click script, per [[Vcut_Decision_Log#ADR-002 — NLE targets]]) → a desktop notification and `STATUS.md` say it is ready for G4.

---

## Operator workflow

### 0. New video (setup form)
The Storyboard's first page. One screen with every choice from [[Vcut_Decision_Log#ADR-018 — Project setup options and autopilot]], pre-filled from the channel defaults or a saved preset: starting point (and file upload: script, instructions, recording, own media), per-gate review/auto, the **autopilot** checkbox, editor, AI per role, voice, style/look and effect density, media sources, length, budget, outputs. *Create* writes `project.yaml` and `00_input/`, and starts the run.

### 1. The Living Storyboard (Review GUI)
Inspired by OpenMontage's Backlot, Vcut includes a local zero-database review dashboard (`vcut board` or `vcut review <gate>`):
- **Local Observer:** A lightweight Python server that watches the project folder and pushes updates via **Server-Sent Events (SSE)** to a browser UI.
- **Visual Validation at Gates:**
  - **Gate G2 (Script):** Mode S: the owner's script with chapter/unit splits, recognised and unrecognised cues, the instruction mapping, each claim with its verdict and sources, and proposed edits to accept or reject. Mode W adds hook choices and word budgets.
  - **Step 02 (Voice):** Built-in audio unit playback with word-timing sync and WER flags.
  - **Gate G3 (Shot Plan Contact Sheet):** Visual filmstrip of shot slots, candidate takes, licensing tiers, and **exact estimated dollar cost** before paid downloads or video generation occur.
  - **Before G4:** the preview MP4 (05b) with burnt-in review markers, and a button to open the result in the chosen editor.
  - **Effects:** the presets used per chapter, each with its preview, so the owner can swap a preset before the editor build.
- **One-Click Approval (human only):** Approving in the UI writes `approvals/<gate>.json` with the content hash and the operator's name. The board serves its API to its **own origin only** (no `*` CORS) and requires a per-session token, so no other web page or local process can post an approval ([[Vcut_Decision_Log#ADR-009 — Human gates]]).

### 2. MCP Co-Pilot Interface (`vcut mcp`) — read-only
Inspired by OpenChatCut, Vcut exposes a local Model Context Protocol server so an AI assistant (Claude Code, Hermes, …) can follow a project in chat. **It can look and ask; it cannot approve or spend.**
  - `vcut_status()` — stage statuses, pending gates, spend so far.
  - `vcut_review_gate(gate)` — summary data for the gate. Scraped research appears only as quoted data, labelled untrusted.
  - `vcut_request_approval(gate, message)` — notifies the human (board banner / desktop notification). It writes nothing to `approvals/`.
  - There is **no** `vcut_approve` and **no** `vcut_run`. *Removed 2026-10-26 (10-15 review C1): they let an agent pass the cost gate, and injected text in scraped sources could ask it to.* Non-paid stages may later get a `vcut_run_free(stage)` tool that refuses any stage downstream of an unapproved gate.

### 3. CLI Commands
```text
vcut new "<title>" --script <file> [--instructions <file>] [--recording <file|dir>] [--media <dir>]
         [--editor resolve|filmcraft] [--ai antigravity|claude_code|ollama:<model>|cloud|none]
         [--voice qwen3_tts|kokoro|elevenlabs|recording] [--look archival|old_film|clean] [--autopilot]
vcut new "<title>" --brief <file>        # brief start; same options
vcut new … --preset "<saved preset>"     # every option from a saved setup
vcut run [--from <stage>]                # new run: inherit unchanged stages, run the rest (--from forces a re-run)
vcut edit <artifact>                     # copy an artifact into a new run for a post-gate human edit
vcut gc                                  # delete runs nothing points at (kept at least until G4)
vcut status                              # per stage: done / waiting_approval / cost
vcut board [project_id]                  # launch local Living Storyboard web UI (SSE)
vcut review <gate>                       # open specific gate review in Storyboard
vcut approve <gate> [--notes file]       # writes approvals/<gate>.json; interactive terminal only (refuses when stdin is not a TTY)
vcut preview                             # open 05_timeline/preview.mp4
vcut open-editor                         # build/open the result in the chosen editor (06)
vcut clean                               # after G4: drop conformed copies and old runs
vcut mcp                                 # start the MCP server (read-only + agent task pull)
vcut estimate <stage>                    # cost + ETA preview
```

## Run report & telemetry
Every stage appends to `.vcut/runs/<run_id>/run_report.json` (summarised in `STATUS.md`):
- items processed / failed / fell back;
- wall-clock time;
- tokens and API units, with **actual cost**;
- quota remaining per provider.

For every slot it also records the query used, the top candidates with scores, the choice, its licence,
and why the alternatives lost. A Resolve marker or clip note can then link back to that record.

## Secrets & data handling
- Keys come only from the Windows Credential Manager or an untracked `.env`. They are **never written into manifests, logs, review pages or `.drp` exports**. Use one key per vendor and set a **spend limit at the vendor** where offered. Logs redact keys and personal data.
- `privacy: local_only` makes the orchestrator refuse cloud providers for that project. Vendor data-retention and training terms are recorded in [[Vcut_Tool_Allowlist]].
- **Trust boundary (prompt injection):** scraped pages, video descriptions and API metadata are **untrusted data**.
  - Research output is stored as quoted facts with source URLs, and is never fed back as instructions.
  - Downstream LLM passes receive extracted facts, not raw page text.
  - Downloads are only allowed from allow-listed provider APIs. **No free-form URL from an LLM is ever fetched.**
  - Every LLM output that triggers an action is schema-validated by code first.
  - Downloaded media is probed and transcoded in an isolated working folder before it enters the project.

## Reference runtime profile
Observed on this workstation on **2026-10-12**, updated **2026-10-26** and **2026-10-27** (FilmCraft, Resolve README). Confirm before M0.

| Item | Value | Consequence |
|---|---|---|
| OS | Windows 10 Pro 19045 | Paths with `((_atWork_))` must survive FFmpeg, Resolve import and OTIO/FCPXML URLs (M0 test) |
| GPU | NVIDIA RTX 5070 Ti, **16 GB** VRAM | Kokoro, Qwen3-TTS, aligners, faster-whisper and small Ollama models fit (one at a time on the GPU queue). **Local Wan 2.2 (TI2V-5B needs ≥24 GB) and Llama-70B do not**, so generative video stays cloud |
| Python | 3.13.7 system; the project `.venv` was created with 3.12 (seen in `tests/__pycache__`, 2026-10-26) | Pin one version in `pyproject.toml`; check the Resolve scripting module's supported Python at M2 |
| DaVinci Resolve | **20.0.1 (uninstall entry "DaVinci Resolve": apparently the free edition)**; its scripting README ("Last Updated: 7 May 2025") is at `C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\README.txt` | **Default editor.** One-click native build on free (to verify); full autopilot needs Studio. **Do not upgrade the free edition past 21.0** if relying on in-app scripts (21.1 removed Python from free) |
| FilmCraft | **0.13.0** at `C:\Program Files\FilmCraft\` (`filmcraft.exe`, `filmcraft-cli.exe`), checked 2026-10-27; headless build probe passed ([[06_NLE_Adapters#FilmCraft]]) | Alternative editor, full autopilot. Pin 0.13.0; alpha, so re-run the M0a probe on every upgrade |
| EffectCraft | `effectcraft-cli.exe` installed (2026-10-26) | **Not used** in M1–M2 (ADR-021: no separate effects renderer) |
| Ollama (local AI) | Observed 2026-10-26: `gemma4:12b` (7.6 GB), `gemma4:latest` (9.6 GB), `gemma4:26b-a4b-it-qat` (15.6 GB), `qwen3.8:27b` (17.7 GB), `glm-4.7-flash` (19.0 GB) | Only the first two fit in 16 GB VRAM with room to spare; the larger ones spill into system RAM and run slowly. Local AI and Kokoro share the GPU queue. Check each model's licence before `final`-tier use |
| Antigravity | **Antigravity IDE 1.107.0** at `%LOCALAPPDATA%\Programs\Antigravity IDE` (CLI `bin\antigravity-ide.cmd`, with a `chat -m agent` subcommand); also an `antigravity` app folder. The headless `agy` CLI is **not installed** (2026-10-26) | **Default AI agent.** Opens a window per task batch; installing `agy` later would allow headless runs |
| Claude Code | `claude` CLI on PATH (2026-10-26) | Headless agent option (`claude -p`) |
| Hermes | Reachable through the agent-workers MCP (2026-10-26) | Agent option |
| Qwen3-TTS | The owner's local set-up (location to record at M1) | Default local voice; forced alignment for timing (no native timestamps) |
| Disk | *to fill* | Budget about 50–150 GB per 45-min project (originals + conformed + renders); keep originals until G4, then clean up conformed copies |
| Target wall-clock | *to fill after M1* | Measured per 10 min of output |

## Acceptance tests
- Killing the process mid-03c and re-running repeats **no** completed download or paid call.
- Editing one line after G2 re-runs exactly the items the invalidation table predicts.
- With `budget_usd: 1`, the run stops at the first paid call that would exceed it and reports why.
- No key string appears anywhere under `projects/` (grep test).
- `vcut new p --script my.txt` followed by `vcut run` with every AI role `none` reaches G2 with no network AI call.
- An approval POST from another origin, without the session token, or from the MCP server is refused; `vcut approve` with piped stdin is refused.
- **Autopilot:** `vcut new "t" --script s.md --autopilot` with `budget_usd: 0` ends with the timeline built in **Resolve** (one click on free, none on Studio); with `--editor filmcraft` it ends with the project open in FilmCraft and no prompt on the way, unless a stop condition holds. Each auto-approval file names the owner's policy.
- In the built timeline, every title's text can be changed in the editor's inspector, and no clip is a pre-rendered title or effect.
- After every stage, the numbered folders contain only the current outputs, under readable names, and no file in them is a copy where a hard link was possible.
- An agent task whose answer file fails its schema is retried once, then the no-AI fallback runs; a forged `approvals/G3.json` without the runner's HMAC is refused.
