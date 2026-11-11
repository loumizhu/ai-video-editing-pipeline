# Vcut — Decision Log (ADRs)

> **Purpose:** this file is the record of **binding** decisions. Other docs link here; they do not
> re-decide. Each entry shows status **Proposed** (a recommended default the plan is written against,
> waiting for the owner to accept) or **Accepted**. The owner flips a status to Accepted or rewrites it.
> If a doc contradicts an Accepted ADR, the doc is wrong.
>
> Created 2026-10-12 from the plan review ([[Vcut_Plan_Review_2026-10-12]]). **Revised 2026-10-26**
> against the owner's stated goal ([[Vcut_Plan_Review_2026-10-26]]): ADR-001, 002, 004, 006, 009 and 011
> rewritten; ADR-016 and 017 added. **Round 3 (2026-10-27):** ADR-021 added (one editor, everything native);
> ADR-002, 004, 011, 012, 017, 018 and 020 aligned to it. Back to [[AGENTS]].

| ADR | Decision | Status |
|---|---|---|
| ADR-001 | **Several starting points:** brief, script, script with cues/instructions, plus an optional own recording. A provided script skips writing; a brief gets a generated script | Proposed (rev. 2026-10-26 ×2) |
| ADR-002 | Output is a timeline **built natively inside the chosen editor: DaVinci Resolve (default) or FilmCraft**; autopilot targets either; an FCPXML/OTIO package is the backup | Proposed (rev. 2026-10-27) |
| ADR-003 | Single source of truth = **Vcut timeline JSON (own schema)**; OTIO/FCPXML are generated exports | Proposed |
| ADR-004 | Effects reach each editor by its **native route** (API, CLI command, template, FCPXML); baking is a last resort, proven by a capability spike | Proposed (rev. 2026-10-27) |
| ADR-005 | Orchestration = **File-based pipeline manifest (`pipeline.yaml`), deterministic folder handoffs, no database**; AI agents perform targeted tasks only | Proposed |
| ADR-006 | Stack = **hybrid and optional-AI** (licensed stock/music, local where licence + quality allow, AI per role or none) with a **hard per-video budget** | Proposed (rev. 2026-10-26) |
| ADR-007 | **Strict licence allow-list**; per-asset ledger mandatory; **no automated third-party clip harvesting** | Proposed |
| ADR-008 | Narration = **owner's recording, local Qwen3-TTS, Kokoro, or ElevenLabs (paid)**; Edge-TTS is prototype-only | Proposed (rev. 2026-10-26) |
| ADR-009 | Each gate is **reviewed by the owner or passed by the owner's autopilot policy**, set at project setup; AI agents can never approve | Proposed (rev. 2026-10-26 ×2) |
| ADR-010 | Delivery = **1080p, one frame rate per channel, SDR Rec.709** | Proposed |
| ADR-011 | Build order = **M0 interchange spike → M1 script-in slice (3–5 min) → M2 10–15 min + automated builds → M3 45 min+** | Proposed (rev. 2026-10-26) |
| ADR-012 | Titles, labels and cards = **the editor's own title templates** (Resolve Fusion titles, FilmCraft graphics templates), text filled by Vcut | Proposed (rev. 2026-10-27) |
| ADR-013 | Language = **English for v1**; language/locale fields exist from day one | Proposed |
| ADR-014 | AI disclosure is **computed from the ledger** and **confirmed by a human** at G4 | Proposed |
| ADR-015 | Word timing comes from a **timing ladder** (TTS-native → forced alignment → ASR fallback) | Proposed |
| ADR-016 | AI provider is chosen **per role**: `agent` (**default: Antigravity**), `local` (Ollama), `cloud`, `none`; every AI step has a **no-AI fallback** | Proposed (rev. 2026-10-26 ×2) |
| ADR-017 | A **preview MP4** is rendered by the editor itself where it can render headless (FilmCraft, Resolve Studio); else an FFmpeg approximation | Proposed (rev. 2026-10-27) |
| ADR-018 | **Project setup form**: every choice up front (starting point, reviews on/off, **autopilot**, editor, AI, voice, style), saved in `project.yaml` | Proposed (new 2026-10-26) |
| ADR-019 | **Per-video folder**: numbered, human-readable folders (`00_input` … `07_delivery`) over a hidden `.vcut/` system folder | Proposed (new 2026-10-26) |
| ADR-020 | **Documentary effects library**: presets (looks, overlays, motion, transitions, text/label animations with paired SFX, cards), each implemented natively per editor; catalogue in [[Vcut_Effects_Library]] | Proposed (rev. 2026-10-27) |
| ADR-021 | **One editor: everything native and editable.** No separate effects renderer; every object Vcut places is edited in the chosen editor alone | Proposed (new 2026-10-27) |
| ADR-022 | **Still-hold budget, enrichment and pacing presets.** A still run has a soft and hard cap per preset (default 4.5 s / 6.0 s, ceiling 8.0 s); long stills need enrichment events anchored to the narration; beat map drives pacing | Proposed (new 2026-11-09) |

---

## ADR-001 — v1 product mode
- **Context:** the original plan described two products: a *raw-footage editor* (AGENTS overview, Brainstorming doc) and a *prompt-to-video generator* (steps 01–06). They have different inputs, stage graphs and QA. The manifest's `host_camera.mp4` had no producer.
- **Options:** (a) script-to-video from a brief; (b) raw-footage editor; (c) both in v1.
- **Decision (proposed 2026-10-12):** (a). Narration is either TTS **or the owner recording the locked script** (same contract). **Mode B: Recorded footage** (interviews, podcasts) is a later front end. It must output the **same contracts** (narration audio + line-keyed timing), so every stage from Shot Planning onward is shared.
- **Revision (2026-10-26, owner's goal, round 2):** there are **several starting points**, chosen in the project setup form ([[Vcut_Decision_Log#ADR-018 — Project setup options and autopilot]]). Each one skips the steps whose output the owner already has, and all of them produce the **same** `script_manifest.json`, so everything after it is shared:

  | Starting point | What the owner provides | What Vcut does before G2 |
  |---|---|---|
  | **Brief** (Mode W) | `brief.yaml` or a few lines in the setup form | Research → outline (G1, optional review) → draft → edit → claims → visual beats |
  | **Script** (Mode S) | The script, no markup | Intake → fact-check → visual beats and SFX chosen by AI or heuristics |
  | **Script + cues** (Mode S) | The script with `[visual: …]`, `[sfx: …]`, `[music: …]`, `[effect: …]` cues and/or `instructions.md` | Intake → fact-check → the owner's cues are used as given; AI/heuristics fill only the ideas without a cue |
  | **+ Own recording** (any of the above) | Narration audio, uploaded at setup | Stage 02 aligns the recording instead of synthesising a voice |

  - **If the owner has a script, writing is skipped entirely**: 01a intake parses it, 01b checks it, and the run moves on. **Vcut never rewrites the owner's words**; it may only *propose* edits (a failing claim, a TTS respelling), which the owner accepts or rejects at G2, or which autopilot leaves as markers.
  - **If the owner has only a brief**, Vcut writes the script. Reviewing it (G1 outline, G2 script) is the owner's choice per project.
  - Mode W moves from M3 to **M2**, since the owner wants it available early.
- **Consequences:** V1 is a *base layer* (branded motion plate), not A-roll. Ingest, silence cutting, diarisation and false-start removal are out of scope for v1. The `angle_and_perspective` requirement moves from the brief to the G2 checklist ("the script carries the owner's own view"), because in Mode S the script itself is the perspective.

## ADR-002 — NLE targets
- **Options:** Resolve Studio only · Resolve free (file import only) · Blender VSE · NLE-agnostic multi-adapter.
- **Decision (proposed 2026-10-12, superseded):** DaVinci Resolve Studio as the only master NLE.
- **Revision (2026-10-26, owner's goal):** the owner finishes in **DaVinci Resolve or FilmCraft**. So:
  1. **The always-produced output is an interchange package** (`{run}/nle/package/`): `vcut.fcpxml` (**FCPXML 1.10**, the version both Resolve and FilmCraft are documented to read), `vcut.otio`, the conformed media it links (relative paths), the credits and a one-page import README. This alone is a complete, editable deliverable for Resolve free, Resolve Studio and FilmCraft.
  2. **Automated builds are optional adapters**, each behind the same interface and capability matrix ([[06_NLE_Adapters]]): **Resolve Studio API** (bins with alternates, markers with notes, clip colours, readback) and **FilmCraft headless** (`filmcraft-cli`, its MCP server or JSON control channel). FilmCraft is **alpha**, so its adapter waits for the M0 import test.
  3. Each run picks its targets from `channel_profile.yaml` `nle.targets`. The package is built whatever the targets are.
  *(Points 1–3 are superseded by Round 3 below: one editor per video, built natively; the package is a backup.)*
- **Round 2 (2026-10-26): the result must land *inside* the chosen editor.** The owner picks the editor in the setup form, and with autopilot on, the run ends with the timeline open in it. How far that can be automated depends on the editor, so the plan states it plainly:

  | Editor | Automation level | How |
  |---|---|---|
  | **DaVinci Resolve Studio** | **Full** | External scripting: Vcut launches Resolve, creates the project from the template, builds the timeline natively (titles, grades, overlays, markers, bins), and leaves it open |
  | **DaVinci Resolve free 20.x** (installed) | **One click** *(to verify at M0a)* | External scripting is Studio-only. Vcut installs its build script in Resolve's *Workspace → Scripts* menu; the owner clicks it once. This path ends if the free edition is upgraded to 21.1+, which removed scripting from free |
  | **FilmCraft** (installed, 0.13.0) | **Full** *(headless build tested 2026-10-27; opening the app on the project to verify)* | `filmcraft-cli` runs a Vcut-written command script headless, saves a `.fcproj`, then FilmCraft is opened on it |

  So **full autopilot into Resolve needs Studio (US$295)**; FilmCraft gives it for free.
  - Pin one version per target on the reference machine ([[00_Brief_and_Orchestrator#Reference runtime profile]]). Blender VSE stays deferred. Premiere/FCP are not targets, though the backup FCPXML/OTIO may work there.
- **Round 3 (2026-10-27, owner):** "in the autopilot mode the user can choose between DaVinci Resolve or FilmCraft. The default for now is DaVinci Resolve." So:
  - The setup form's editor choice is **one** editor per video, **default DaVinci Resolve**; FilmCraft is the alternative. Autopilot ends inside whichever was chosen.
  - The timeline is **built natively in that editor** (Resolve API/script, FilmCraft CLI commands), so titles and effects arrive as editor objects ([[Vcut_Decision_Log#ADR-021 — One editor: everything native and editable]]). The FCPXML/OTIO package is demoted to a **backup** for manual import: interchange carries cuts, media and markers, not native titles.
- **Facts behind it:**
  - Resolve (verified 2026-10-12): external scripting is a Studio feature; from **21.1 Python scripting is Studio-only**. The workstation has **Resolve 20.0.1, apparently the free edition**. The scripting README installed with it ("Last Updated: 7 May 2025", read 2026-10-27) lists `InsertFusionTitleIntoTimeline`, `GetFusionCompByIndex`, `ImportFusionComp`, `ApplyGradeFromDRX`, `SetLUT`, the `CompositeMode` and `DynamicZoomEase` clip properties, `AddMarker` and `ImportTimelineFromFile` (AAF/EDL/XML/FCPXML/DRT/ADL/OTIO), and **no transition call**.
  - FilmCraft (verified 2026-10-27 on this workstation): `C:\Program Files\FilmCraft\filmcraft.exe` and `filmcraft-cli.exe`, **0.13.0**, MIT OR Apache-2.0, alpha. The CLI runs about 700 engine commands headless (`run script.jsonl`, `--save-as p.fcproj`), and its `file.import` accepts FCPXML and OTIO. Probe results: [[06_NLE_Adapters#FilmCraft]]. Its GitHub README (checked 2026-10-26) says Windows gets "far less testing than macOS".

## ADR-003 — Canonical timeline artifact
- **Options:** own versioned schema (OTIO/FCPXML derived) · OTIO canonical with Vcut fields in metadata · both hand-maintained (the original plan).
- **Decision (proposed):** `timeline/vcut_timeline.json` (schema `vcut.timeline/1`, defined only in [[Vcut_Data_Contracts]]) is the **only** source of truth. OTIO and FCPXML are generated one-way by a deterministic compiler. They are never hand-edited and never read back as input. The one exception is the post-build **readback diff** (see [[06_NLE_Adapters]]).
- **Why:** OTIO 0.18 has no standard schema for volume, ducking, transforms or keyframes, and its FCPXML adapter is a community plugin outside the official bundle. Vcut needs licence, anchor, alternate and review data that OTIO only holds as opaque metadata.

## ADR-004 — Carriers for effects the Resolve API cannot set
- **Scope widened (2026-10-26):** the same question now applies to every target in [[Vcut_Decision_Log#ADR-002 — NLE targets]]. The rule is: **a manifest feature reaches an NLE through the interchange file if the M0 spike shows that NLE keeps it; otherwise through baked media.** Baked media is the carrier that works everywhere (ducked music stem + muted original, pre-rendered Ken Burns), so it is the default for FilmCraft until its column of the matrix is tested. Resolve-specific carriers (template project, Fairlight Ducker, API post-pass) are below.
- **Facts (official Resolve scripting README v20 and the 21.1 readme):** the API places clips at exact frames on chosen tracks and sets markers, bins, clip colours, *static* transform/opacity and render jobs. It has **no** call for audio volume or volume keyframes, Fairlight automation/ducking, or animated transforms (Ken Burns). **Transitions and fades are only scriptable from Studio 21.1.**
- **Decision (proposed):** per effect:
  - **Ducking:** a Fairlight **Ducker** on the music track, keyed from the voice, pre-configured in a **Vcut template project** (or applied as a Fairlight preset). Fallback: a baked ducked stem, with the un-ducked bed on a muted track.
  - **Ken Burns / zoom:** pre-render into the clip (baked, with handles), or carry it via FCPXML import, which Resolve maps to an editable Dynamic Zoom.
  - **Dissolves:** API on Studio ≥21.1, else FCPXML.
  - **Markers, bins, colours:** always an API post-pass.
- **Gate:** the **M0 capability spike** fills the matrix in [[06_NLE_Adapters#Capability matrix]] on the pinned version before any manifest field is relied on.
- **Revision (2026-10-27, ADR-021):** the order of preference is now **native route first** (API call or CLI command, an editor template, FCPXML import into Resolve for dissolves and Dynamic Zoom), and **baked media only as a last resort**, opted into per preset and flagged in the editor. For FilmCraft the native routes are CLI commands (Motion keyframes, 112 transitions, Light Leaks/Noise/Vignette effects, graphics templates), so its default is no longer "baked". Ducking keeps the baked stem as its fallback in both editors.

## ADR-005 — Orchestration runtime
- **Decision (proposed):** file-based orchestration via a declarative pipeline manifest (`pipeline.yaml`), deterministic step runner, pure file folder handoffs, and content-hash caching. **No database (no SQLite/PostgreSQL)**.
  - Each stage declares its dependencies (`depends_on`, forming a DAG with parallel branches), tools (`tool_choice`, LLMs by role), input/output artifacts and an optional human gate (`approval`). Bounded `loops` are the only backward edges. Schema: [[Vcut_Data_Contracts#3.7 pipeline.yaml (the pipeline orchestration manifest)]].
  - A stage waits for the verified outputs of every stage it depends on before executing.
  - **No autonomous agent owns sequencing, timecodes, or workflow control.** AI models/agents are invoked strictly as specialized execution units for specific tasks (e.g. text generation, script drafting).
  - No workflow server (Prefect/Temporal) in v1.
- **Shared ledger writes (added 2026-10-15, review item B2):** the asset ledger is the only file several stages write. 04a can still be running when 03c and 03d start, and 05 adds `usage` records. Decision: a **single writer with append-only fragments**, still with no database.
  1. **Stages never write `asset_registry.json` directly.** Each writer stage (03c, 03d, 04a, 05) appends records to its own fragment, `{run}/ledger/<stage_id>.jsonl`. A record is either a new entry or a field patch keyed by `asset_id` (for example 03d adding `inventory`, or 05 adding a `usage` row).
  2. **Only the runner merges.** When a writer stage completes, the runner merges its fragment into `{project}/assets/asset_registry.json`. It takes an exclusive lock file (`asset_registry.json.lock`), writes to a temp file and renames it atomically. Stages that start afterwards read the merged file. A stage never reads another stage's unmerged fragment. **Reads are scoped:** a stage reads only the entries whose `asset_id`s its own inputs reference, and its cache key hashes those entries, not the whole file. Otherwise 03d could see 04a's audio entries or not, depending on timing, and give a different cache key for the same work.
  3. **Merges are idempotent.** `asset_id` is content-addressed, so the same file sourced twice gives the same id and merges into one entry; replaying a fragment changes nothing. Fields set from different sources (`usage`, `inventory`) merge as a union. A **conflicting licence or `commercial_use_ok`** for one `asset_id` is a merge error and blocks the stage, rather than letting the last writer win.
  4. **The channel library ledger** (`libraries/asset_registry.json`) is written only by the runner, under the same lock-and-rename rule. That happens when a human adds files to the library, and after **G4**, when the final video's usage is recorded for the channel re-use caps. Projects only read it during a run.
  - **Why not SQLite** (the research synthesis suggested it): OpenChatCut moved to SQLite because many agent edits and a GUI were changing live project state at once. Vcut has one operator, one runner process and hundreds to low thousands of ledger entries. A single writer removes the race, and the ledger stays a human-readable, diffable JSON audit record, which matters for licence disputes.
  - **Revisit when** more than one runner process must write the same project, or the ledger passes about 10k entries or merges become slow. Then move the ledger and cache, not the artifacts, to SQLite behind the same merge interface.
- **Runs and inheritance (added 2026-10-15, review item B1):** a run is **one forward pass** over the DAG. Each new pass reuses every stage output that would come out the same.
  1. **Starting a run.** `vcut run` creates the next `run_id` and takes the project lock (`projects/<id>/run.lock`), so one run is active per project. Loops L1, L2 and L4 also start a new run from their target stage; L3 is internal to 02.
  2. **Stage fingerprint.** For each stage, in DAG order, the runner computes a fingerprint over: stage id and `stage_version`; resolved `tool_choice` with tool versions and the model each role is bound to; params and prompt hashes; and the sha256 of every input artifact as resolved *in this run*.
  3. **Inherit or run.** If the fingerprint equals `current/<stage_id>.json`'s fingerprint, and that run's outputs still match their recorded hashes, the stage is **inherited**. Nothing is copied: the new run's `run_manifest.json` records that stage → source `run_id`, and `{run}/…` paths for that stage resolve into the source run's folder. Otherwise the stage runs. Inside a re-run stage, unchanged **items** (units, slots, assets) come from the item cache (`{project}/cache/items/`), so only changed items cost time or money.
  4. **Gates pin approved stages.** For a stage whose outputs a gate has approved (01a, 01b, 03b), a change in **tools, versions or role→model binding alone** does not re-run it: the runner keeps the approved output and warns. Only a change in its **input artifacts** re-runs it. That stops a model upgrade from silently rewriting a locked script. `vcut run --from <stage>` forces a re-run from that stage on purpose.
  5. **Advancing `current/`.** `current/<stage_id>.json` (one file per stage, so parallel stages never share a file) is written by the runner only, with an atomic rename. It points at the newest run in which that stage **completed**. It records the run, fingerprint and output hashes. A failed or partial stage never advances its pointer.
  6. **Runs are immutable once their stages complete.** A human change after a gate (say, rewording a line after G2) is made with `vcut edit <artifact>`. It opens a copy of the artifact in a new run; downstream stages then re-run or inherit by fingerprint as usual. The changed artifact is recorded with `produced_by.stage: human_edit`, and its new hash requires re-approval. If a completed run folder is edited in place, its hashes no longer verify and the runner refuses to inherit from it.
  7. **Retention.** `vcut gc` deletes run folders that no `current/` pointer, approval file or `run_manifest.json` of a kept run refers to. Runs are kept at least until G4.
- **Entry modes (added 2026-10-26, ADR-001):** a stage may declare `modes: [S]`, `[W]` or both (default both). The runner reads the project's mode from `brief.yaml` (`mode: script | brief`), skips stages not in that mode (`status: skipped`), and drops a `depends_on` edge to a skipped stage. One `pipeline.yaml` therefore serves both modes, and no stage needs an `if`.

## ADR-006 — Cost / stack policy
- **Decision (proposed):** hybrid. Pexels as the primary stock source. Licensed music library. Kokoro (local) for draft voice; owner voice or ElevenLabs paid for final. Generative video capped (≤10% of shots by default, cloud, paid commercial tier). Every project carries a **hard budget cap**, and the run stops before exceeding it. Two quality tiers: `draft` and `final`.
- **AI is optional (revised 2026-10-26):** the earlier "cloud LLM, because a 70B local model does not fit" is replaced by [[Vcut_Decision_Log#ADR-016 — AI providers and the no-AI path]]: each role is bound to a cloud model, a local Ollama model, the owner's agent, or nothing.
- **Zero-cost path:** Mode S + AI `none` or `local` + Kokoro + Pexels + local music/SFX library + the interchange package costs **$0 per video** in third-party fees. This is the M1 configuration.

## ADR-007 — Licence & source policy
- **Decision (proposed):** strict allow-list ([[Vcut_Tool_Allowlist]]). Every asset has a ledger entry, and the validator refuses to place an asset without `commercial_use_ok: true`. **Banned:** non-commercial licences (CC-BY-NC, MusicGen weights, ElevenLabs free tier, Luma Free/Lite …), Freesound Sampling+, and **automated download of third-party video (yt-dlp, screen capture of others' content)**. Archival or news footage enters only through the manual `00_input/media/` with a human rights decision recorded. Credits are generated from the ledger.

## ADR-008 — Narration voice
- **Decision (proposed):** monetised releases use (a) the owner's recorded voice or (b) ElevenLabs on a paid plan, with a library voice or the owner's **own** verified clone. Kokoro-82M (Apache-2.0) is the free voice for `draft`, and for `final` if quality is accepted. Edge-TTS is prototype-only: it uses an unofficial endpoint with no commercial licence.
- **Revision (2026-10-26):** the owner has a **local Qwen3-TTS** set-up, which becomes the **default local engine**, chosen in the setup form alongside Kokoro, ElevenLabs and "upload my recording". Facts (GitHub `QwenLM/Qwen3-TTS` README, 2026-10-26): code Apache-2.0; **the weights' licence is not stated on the README** (secondary sources say Apache-2.0), so confirm it on the Hugging Face model card before `final`-tier use; 0.6B and 1.7B models; 10 languages incl. English; voice cloning from a short reference clip; **no word timestamps**, so its timing comes from forced alignment (rung 2 of ADR-015). Cloning is limited to the owner's own voice, as for ElevenLabs.
- **Own recording** is uploaded at setup (`00_input/recordings/`), not in a later step.

## ADR-009 — Human gates
- **Decision (proposed, revised 2026-10-26):**
  - **Gates:** **G1 Outline** (brief start only) · **G2 Script lock** · **G3 Shot plan + cost** (media chosen) · **G4 Final review in the editor** (Resolve or FilmCraft). For a video under 10 minutes with no paid fill, G3 may be merged into G2's page, but it is still recorded as its own approval file.
  - **Living Storyboard (review GUI):** a local, zero-database browser dashboard (Backlot pattern) watching `projects/<id>/` via Server-Sent Events. It renders the parsed script with claims, the voice units, the contact sheet and the preview MP4.
  - **The owner decides how each gate passes, at setup** (round 2, 2026-10-26). Per gate, the setup form offers *Review* (wait for me) or *Auto* (pass it for me). The **autopilot** checkbox sets every gate before the editor to *Auto*, so a brief or script goes all the way to a timeline inside Resolve or FilmCraft with no stop.
  - **An approval file is written only by:** (a) a click in the Storyboard, served to its own origin only with a per-session token; (b) `vcut approve <gate>` on an interactive terminal; or (c) **the runner applying the owner's autopilot policy** from `project.yaml`. It records who: the operator's name, or `autopilot (policy set by <owner> at <time>)`, never a default.
  - **Autopilot still stops** (and waits for the owner) when: the cost estimate at G3 exceeds `budget_usd` or the autopilot spend limit; QA has errors after loop L4; a claim is `contradicted` (Mode S/W); or nothing usable was found for more than 20% of slots. Assets that need a human rights decision (archival, article captures, CC-BY-SA photos) are **placed with a red marker**, never silently cleared.
  - **G4 is always the owner**, in the editor: autopilot ends with the timeline open, not with a published video.
  - Only the owner, through the setup form or `project.yaml`, can turn autopilot on. AI agents cannot change the policy or write approvals.
  - **MCP co-pilot and the `agent` provider are read-only** ([[Vcut_Decision_Log#ADR-016 — AI providers and the no-AI path]]): `vcut_status`, `vcut_review_gate` (summary) and `vcut_request_approval` (which only notifies the human), plus `vcut_next_task` / `vcut_submit_answer` for pull-mode agents (an answer is only a validated JSON file in its task folder). There is **no** MCP tool that approves a gate, changes the autopilot policy or starts a paid stage. *Why:* the 10-15 review (C1) found that `vcut_approve` let an agent pass the cost gate, and that scraped research text in `vcut_review_gate` could ask it to.
  - Downstream stages refuse to run without gate approval records in `approvals/` whose hashes match.

## ADR-010 — Delivery format
- **Decision (proposed):** 1920×1080, one frame rate per channel (default **30/1**; 25/1 for PAL-region channels), SDR Rec.709, 48 kHz audio. Every source is conformed to that. 4K is revisited only when the stock and generative tiers deliver 4K consistently. (The original "Final 4K Render" contradicted the 1080p manifest.)

## ADR-011 — Build order (MVP)
- **Decision (proposed, revised 2026-10-26):**
  - **M0a — native-build spike (2–3 days):** a hand-made 60 s fixture (clips, a push-in, a dissolve, a look, a light leak, two title templates, markers) → built natively in **Resolve (installed free 20.0.1, via the Scripts menu) and FilmCraft 0.13.0 (CLI)** → fill the capability matrix for both. Check the `((_atWork_))` path in both. *Moved first because its result decides which manifest fields can exist (10-15 review, D2). FilmCraft's part was partly done on 2026-10-27 ([[06_NLE_Adapters#FilmCraft]]).*
  - **M0b — contracts:** schemas, validator, quantiser, compiler and exporters for only the fields the spike marks ✔; FFmpeg preview render of the fixture.
  - **M1 — script-in slice (3–5 min):** setup form → the owner's script (with or without cues) → intake → fact-check → Qwen3-TTS, Kokoro or own recording → Pexels photos/video + Wikimedia images → no generative → **a starter set of ~20 effect presets, native in both editors** ([[Vcut_Effects_Library]]) → ducking (template Ducker or baked stem) → native build in the chosen editor (**Resolve by default**; one click on free Resolve, full on Studio or FilmCraft, per ADR-002) + preview → G4. **Must also run with AI `none`; default AI is Antigravity.** Autopilot works end to end.
  - **M2 — 10–15 min + brief start:** **Mode W (write-from-brief)**, alternates, full SFX, per-line regeneration, the full effects library, article captures, the rest of the effects library as native presets, full automation into Resolve Studio (if bought).
  - **M3 — 45 min+:** generative video under caps, resumable long runs, maps, and **opt-in pre-rendered presets** for effects no editor has natively (parallax, animated maps), per ADR-021.
- Acceptance criteria: [[Vcut_End_to_End_Pipeline_Architecture#9. Roadmap]].

## ADR-012 — Graphics & titles producer
- **Decision (proposed, revised 2026-10-27 by ADR-021):**
  - **Text, labels, lower thirds, chapter titles, quote cards, article cards, person cards:** the **editor's own title templates**, made once per preset and stored in the effects library: **Resolve Fusion Title templates** (published inputs for text, colour, accent) and **FilmCraft graphics templates** (`.fcgt`, named controls). Vcut fills the values at build time; the owner edits the text in the editor's inspector. Photos in cards are separate clips under the title, so they can be swapped in the editor.
  - **Charts:** M2, built from native shapes and text where the editor allows (FilmCraft `graphics.newShape`, Fusion templates in Resolve); otherwise a still image rendered from claim data (an ordinary image clip, flagged "baked").
  - **Superseded:** Python- or EffectCraft-rendered alpha clips (ProRes 4444 / PNG) for text and cards, and the `values.json` + `vcut rerender` loop. They needed a second program to change a word. Resolve does not import WebM, so the original `intro_title.webm` example stays invalid.
  - **Remotion:** not used in M1–M2 (no step renders graphics outside the editor); revisit only for M3 opt-in pre-renders, with its licence check.

## ADR-013 — Language
- **Decision (proposed):** English only in v1. `language` and `locale` exist in the brief and channel profile from day one. Speech rate is a per-voice calibration, not a fixed 140–160 WPM. Dubbing and multi-language audio tracks are out of scope.

## ADR-014 — AI-content disclosure
- **Decision (proposed):** 05 computes `disclosure_required` from the ledger. It is true when any photoreal synthetic visual depicts a real place, event or person or is presented as real, when a synthetic voice is presented as a real person, or when AI music is the **main focus**. A ducked bed alone does not count, and narrating with your own cloned voice is exempt. A human confirms it at G4. Rules per YouTube Help "Disclosing use of altered or synthetic content".

## ADR-015 — Timing source
- **Decision (proposed):** synthesise per **unit** (a paragraph or short beat; strict per-sentence synthesis breaks prosody on context-free engines). Unit boundaries are exact by construction. Word timing inside a unit comes from:
  1. TTS-native timing: ElevenLabs `with-timestamps`; Kokoro token timestamps (English only); Edge-TTS `boundary="WordBoundary"`, prototype only.
  2. **Forced alignment of the known text** for human narration (WhisperX/wav2vec2, MFA, or ctc-forced-aligner with a *commercially licensed* model — its default MMS model is CC-BY-NC).
  3. faster-whisper is used **only as a QC pass** (word-error rate against the script). It is a transcriber, not a forced aligner, and does no diarisation.
- Precision requirement: cuts ±1 frame, captions ±2 frames. "Millisecond-exact" is removed.

## ADR-016 — AI providers and the no-AI path
- **Context (2026-10-26):** the owner "might use some AI from my AI agent or not". The plan bound every judgement step to a cloud LLM. The workstation already runs Ollama (five local models, see [[00_Brief_and_Orchestrator#Reference runtime profile]]) and a Hermes agent.
- **Decision (proposed):** every AI role in `pipeline.yaml` (`drafting`, `tagging`, `vision`) is bound to one provider, chosen in the setup form:
  - `agent` — **default: Antigravity** (owner's choice, 2026-10-26). An AI app installed on this computer does the task. Vcut writes a **task file** (instructions + the allowed inputs + the JSON Schema of the answer) and waits for one JSON answer file. Per app:
    - **Antigravity IDE** (installed, v1.107.0, checked 2026-10-26): `antigravity-ide chat -m agent -n -a <task.json> "<prompt>"` opens an agent session in a new window on the task folder; the agent writes `<task>.answer.json`. It needs the app's window, not a headless run. A separate headless CLI, `agy -p --output-format json`, is described by third-party sources but is **not installed and not verified**; if adopted, it replaces the window.
    - **Claude Code** (CLI on PATH here): `claude -p` with JSON output, headless *(flags to verify at M1)*.
    - **Claude Desktop** and other chat apps: no command to send them a task. They connect to Vcut's MCP server as clients and **pull** tasks (`vcut_next_task`, `vcut_submit_answer`); that needs a chat session open, so it suits review-mode runs, not autopilot.
    - Hermes, through the agent-workers MCP.
    In every case the agent's workspace is **confined to the task folder** (`.vcut/agent_tasks/<task_id>/`), its answer is schema-validated like any LLM output, scraped text reaches it only as quoted data, and it gets no tool or folder access that writes approvals, changes `project.yaml`, starts stages or fetches URLs for Vcut. Approval files carry an HMAC made with a key the runner keeps in Windows Credential Manager, so a file written by anything else is refused. *(Residual risk: an agent running as the same Windows user with unrestricted shell access could still reach that key; run agents in their confined mode.)*
  - `local`: an Ollama model on this machine (required when `privacy: local_only`);
  - `cloud`: a vendor API from [[Vcut_Tool_Allowlist#AI providers (roles: drafting, tagging, vision)]];
  - `none`: no AI. The step runs its **deterministic fallback**, and anything the fallback cannot decide is left for the human at the next gate (or marked in the editor under autopilot).
- **Every AI step must name its no-AI fallback** in its step doc. Summary:

  | Step | With AI | With `none` |
  |---|---|---|
  | 01a segmentation (Mode S) | Proposes chapter/unit splits | Splits on `#` headings and paragraphs; one unit per paragraph |
  | 01b claim extraction | Finds claims, incl. paraphrased ones | Regex for numbers, dates, %, currency, quotes, capitalised names |
  | 01b fact-check research | Synthesises search results into verdicts | Runs the searches, attaches top sources; the **human** marks each claim at G2 |
  | 01b visual beats | Intent, 3–5 queries, negatives per idea | Author cues first; else noun-phrase keywords per sentence (TF-IDF over the script) as queries |
  | 03b segmentation & choice | Proposes slots; picks among top candidates by id | Cadence rules alone; top embedding score wins |
  | 03b vision QC | Yes/no on text/logo/match | Skipped; slots flagged yellow for G3 |
  | 04a moods | Labels chapter moods | Author `[music: …]` cue, else the channel default mood |
- **Consequences:** the quality of beats and claim checking rises with AI, but **a full run never requires it**. Fingerprints include the provider and model per role (ADR-005), so switching from `none` to `local` re-runs only the affected unpinned stages.

## ADR-017 — Preview render
- **Context (2026-10-26):** the owner expects "a video that I can edit and fix". Before this, the first watchable output was an NLE timeline at stage 06.
- **Decision (proposed):** stage **05b** renders `{run}/preview/rough_cut.mp4` directly from `vcut_timeline.json` with FFmpeg (NVENC where available): 1080p or 720p, the carriers marked "baked" applied, review markers burnt in as small captions, chapter titles as plain text. It is **deterministic, needs no NLE, and is not the master**: the master is rendered from the NLE after G4 (07a).
- **Revision (2026-10-27, ADR-021):** with titles and effects now native to the editor, an FFmpeg preview can only approximate them. So the preview is rendered **by the editor, after 06 builds the timeline**, where it can render without the owner: **FilmCraft** `filmcraft-cli export <out>.mp4 --scale 0.5` (command present in 0.13.0; to run at M0a) and **Resolve Studio** render job (`AddRenderJob`/`StartRendering`). On **free Resolve** the FFmpeg preview above is kept and labelled "approximate: titles and effects simplified".
- **Why not make it the master:** an FFmpeg filter graph cannot give the human the editable multi-track timeline, alternates and markers that the goal requires. The preview is for checking pace and coverage, and for watching the result on a machine without Resolve or FilmCraft.

## ADR-018 — Project setup options and autopilot
- **Context (2026-10-26, round 2):** "at the beginning, I should have all of the choices possible", including one checkbox that automates everything from the brief or script to a timeline inside the editor.
- **Decision (proposed):** a new video starts with a **setup form** (Storyboard page "New video", or `vcut new` with flags). Every choice is made there and saved in `project.yaml` ([[Vcut_Data_Contracts#3.10 project.yaml (setup options)]]); every field has a default, so the form can be submitted with only a title and a file.

  | Group | Choices (default in bold) |
  |---|---|
  | Starting point | **Script** · Script + cues/instructions · Brief (Vcut writes the script) — plus "I have my own narration recording" (upload) |
  | Reviews | Per gate: **Review** or Auto — G1 outline (brief only), G2 script, G3 media & cost. G4 is always the owner, in the editor |
  | Autopilot | ☐ **Off** / ☑ On = every gate above set to Auto, and the result opened in the editor |
  | Editor | **DaVinci Resolve** · FilmCraft (one per video; autopilot ends in it) — and "open it when done" (☑) |
  | AI | Per role: **Antigravity** · Claude Code · Claude Desktop (pull) · Ollama model · cloud API · none |
  | Voice | **Qwen3-TTS (local)** · Kokoro · ElevenLabs · my recording — voice id, speed |
  | Style | **Documentary** preset: look (clean / archival / old film), effect density (low / **medium** / high), text-label style, music mood default — from [[Vcut_Effects_Library]] |
  | Media | Sources allowed (**Pexels, Pixabay, Wikimedia Commons**, my library, article captures ☐, generative ☐), photo vs video balance |
  | Length & money | Target length (optional for a script), `budget_usd` (**0** = free sources only), autopilot spend limit |
  | Output | Resolution/frame rate (from the channel), captions ☑, chapters ☑, preview MP4 ☑ |
- **Channel defaults:** the form is pre-filled from `channel_profile.yaml`, so a recurring format is one click. The owner can save a filled form as a named preset ("Documentary – autopilot – FilmCraft").
- **Changing options later** starts a new run from the first affected stage (ADR-005 fingerprints), e.g. switching the editor re-runs only 05/06.
- **Risk stated plainly:** autopilot from a brief to a finished timeline is the kind of mass-produced content YouTube's "inauthentic content" policy targets, if used at volume without the owner's own input. Vcut keeps G4 (the owner, in the editor) and never publishes; the owner's own script and recording are the strongest mitigation ([[AGENTS#Platform constraints]]).

## ADR-019 — Per-video folder organisation
- **Context (2026-10-26, round 2):** "each video has its own folder and subfolders and organisation". The v2 layout stored media under hash names (`a_3f9c2e81b0d4.mp4`) and outputs under opaque run ids (`runs/r0007/`), which is right for the machine and unreadable for a person.
- **Decision (proposed): two layers in each video's folder.**
  1. **Readable folders**, numbered in pipeline order, holding the **current** version of everything with meaningful names: `00_input`, `01_script`, `02_voice`, `03_media` (by chapter, then slot), `04_audio`, `05_timeline`, `06_editor`, `07_delivery`, plus a `STATUS.md` progress page. File names say what they are: `03_media/02_the-grid/s0017_substation-aerial__pexels-3129957.mp4`.
  2. **`.vcut/`**, the system folder: immutable runs, content-addressed originals, cache, ledger fragments, approvals, agent tasks. The runner owns it; the owner never needs to open it.
  - The readable folders are rebuilt by the runner whenever a stage completes, as **hard links** into `.vcut/` (no extra disk space on the same NTFS drive; copies if the drive cannot link). Older versions stay in `.vcut/runs/` until `vcut gc`.
  - **The owner writes only into `00_input/`** (script, instructions, recordings, own images and clips). Anything else is regenerated; edits belong in the editor.
  - Project folders are named `<YYYY-MM-DD>_<slug>` (date created + title slug), so they sort by date.
  - Full tree: [[00_Brief_and_Orchestrator#Workspace layout]]. Path rules: [[Vcut_Data_Contracts#1.4 Paths]].
- **Why not drop runs:** run immutability and inheritance (ADR-005) are what make re-runs cheap and resumable. The readable layer gives the organisation without losing that.

## ADR-020 — Documentary effects library
- **Context (2026-10-26, round 2):** the channel is faceless documentary. It needs ready-made effects: light leaks, old-film looks, animated text and labels **with their sound effects**, article screenshots with a highlight, person cards, and similar.
- **Decision (proposed):**
  - A channel-level **effects library** (`libraries/effects/`), one folder per preset with a `preset.yaml` (id, category, parameters, carrier, paired SFX, default duration, preview clip). The catalogue and the starter list are in [[Vcut_Effects_Library]]; the preset schema is in [[Vcut_Data_Contracts#3.11 Effect presets]].
  - **Who chooses:** the owner's `[effect: …]` cues first; then style rules from the chosen look (e.g. every archival photo gets "old photo" + slow push-in); then the AI `tagging` role proposes by **preset id** per beat; with AI `none`, style rules only. Code checks density limits and places the preset's native implementation for the chosen editor.
  - **Carriers (revised 2026-10-27, ADR-021):** every preset has **one implementation per editor**, all native: (1) **title template** (text, labels, cards); (2) **editor transition**; (3) **effect stack on the clip** (looks, light leaks, grain, vignette, push-in keyframes); (4) **overlay clip** with the editor's blend mode (dust, scratches, paper textures). A preset with no native implementation in an editor is **not offered** for that editor; pre-rendering is an M3 opt-in.
  - **No separate renderer.** The EffectCraft-CLI renderer, the `values.json` files and `vcut rerender` proposed on 2026-10-26 are withdrawn. Overlay texture clips (dust, scratches) are ordinary media in the library: generated once procedurally by Vcut (no licence risk) or bought packs with a ledger entry.
  - **Paired SFX:** every text/label/card preset names its SFX (typewriter, whoosh, camera shutter, paper slide, stamp…), placed by 04b with the same sync rules and density budget as other SFX.

## ADR-021 — One editor: everything native and editable
- **Context (2026-10-27, owner):** "For now we don't need effect graphs for these simple effects like labels or … transitions. I want to be able to edit the video in one single software." The 2026-10-26 plan rendered text, cards and some looks outside the editor (EffectCraft or Python alpha clips, baked motion), so changing a word meant editing a values file and re-rendering.
- **Decision (proposed):**
  - **Every object Vcut places is a native object of the chosen editor** (ADR-002: Resolve by default, or FilmCraft): clips, title templates with their text, transitions, effects and their keyframes, overlay clips with blend modes, markers, captions, ducking. The owner changes any of it in that editor alone, with no other program and no re-render.
  - **Presets are implemented once per editor** and stored in the library ([[Vcut_Effects_Library#How a preset reaches the timeline]]): a Resolve Fusion title / `.drx` grade / transition name, and a FilmCraft `.fcgt` template / effect stack / transition id. The templates are built by hand once (owner or developer), then only filled with values by code.
  - **What is not native is not done** in M1–M2: a preset without an implementation for the chosen editor is not offered for it. From M3, a preset may opt into pre-rendering (parallax, animated maps); its clip is then marked "baked" in the editor and its untouched original is kept in the alternates bin.
  - **No effects renderer in M1–M2:** EffectCraft, `values.json` and `vcut rerender` are withdrawn (ADR-012, ADR-020).
  - Effects remain **LLM-chosen by preset id, code-placed**: the AI never writes an editor command, a keyframe time or a template value that is a time.
- **Why:** it is what the owner asked for; it removes a render step, a second app and a licence question (EffectCraft) from M1; and both editors have the native routes. FilmCraft 0.13.0 ran them headless on 2026-10-27 (templates with named controls, 112 transitions, Light Leaks/Noise/Vignette, Motion keyframes). Resolve's API lists Fusion titles, DRX grades, LUTs and composite modes.
- **Consequences:**
  - The preview MP4 is rendered by the editor where possible (ADR-017).
  - The FCPXML/OTIO package becomes a backup: interchange does not carry native titles (FilmCraft's own FCPXML/OTIO export reported its text graphic as not carried, 2026-10-27).
  - Each preset costs one implementation per editor. M1's ~20 presets are built for both editors; a preset may ship for one editor first, and the catalogue shows which.
  - Resolve's routes are documented but **not yet run**; transitions on Resolve below Studio 21.1 still need the FCPXML import step. M0a tests both editors.

## ADR-022 — Still-hold budget, enrichment and pacing presets
- **Context (2026-11-09, owner):** narration was good but a single still sometimes stayed on screen about 12 s. Root cause found in the pipeline's builder: shot count followed image count, same-idea merging extended holds without limit, and the caps in force (`~10 s`, `<= 8 s`, Vcut 03b "4-8 s by section energy") were checked per beat, not per picture run.
- **Decision (proposed):**
  - **A still run** (one picture, or several of the same idea, ended only by a distinct shot) has a **soft cap and a hard cap per pacing preset**: `documentary_standard` 4.5 s / 6.0 s, `slow_reflective` 6.5 s / 8.0 s, `tense_fast` 3.5 s / 4.5 s, `shorts_vertical` 3.0 s / 4.0 s; tightened x0.85 / x0.70 on intensity 4 / 5 beats; **absolute ceiling 8.0 s**. Between soft and hard cap a still needs **enrichment events** so no event-free stretch exceeds the preset gap (3.5 s default). The cap overrides the same-idea merge. A picture is shown once per video (owner rule of 2026-11-08, kept); fixes are new shots or plates, never repeats.
  - **Enrichment** is chosen by what the line says (person, place, number, date, quote, document, object...), anchored to a spoken word, from a tiered catalogue (A in-frame camera, B overlay, C plate, D cutaway; sound never counts). Cut first, enrich second, decorate never.
  - **Beat map** (emotion, intensity 1-5, function, info_type, anchor_phrase, priority) is rated by AI **by beat id**; code maps beats to times (principle 3 unchanged). It drives caps, shot length, motion, transitions, music and look.
  - **Variation, asset audit and edit report** are deterministic QA with exit codes; the feedback loop writes a bounded style memory that can never relax a hard cap, a licence rule or a truth tier.
- **Why:** an unenforced adjective ("never hold an unmoving frame") did not stop the failure; numbers, a QA exit code and a way to fix the failure (the fix order) do.
- **Consequences:**
  - Supersedes 03b "maximum hold depends on section energy (e.g. 4-8 s)". Section energy now enters through beat intensity and the preset, never above the ceiling.
  - `shot_plan.json` gains optional fields (`media_type`, `asset_group`, `beat`, `anchor_phrase`, `enrichments[]`, `transition_in`, `sfx`, `rationale`, `still_hold_waiver`): see [[Vcut_Data_Contracts#3.3 shot_plan.json]]. The waiver is owner-only.
  - Implementation in the AI Video Editing Pipeline: `video_pipeline/PACING_AND_ENRICHMENT.md`, `presets/pacing/*.json`, `tools/still_hold_qa.py`, `asset_audit.py`, `variation_report.py`.
