# Vcut — Plan Review (2026-10-15)

> Follow-up review of Architecture v2 ([[Vcut_Plan_Review_2026-10-12]]), including the changes made late on
> 2026-10-12: `pipeline.yaml`, the Living Storyboard, the MCP co-pilot, "no database" (ADR-005) and `research/`.
> Back to [[AGENTS]] · Hub: [[Vcut_End_to_End_Pipeline_Architecture]].
>
> **Status 2026-10-26** ([[Vcut_Plan_Review_2026-10-26]]): **C1 applied to the docs** (ADR-009, 00: MCP read-only, human-only approvals). C2 is moot: the Storyboard was built on 2026-10-15 and stays in M1. **D2 applied** (M0a spike first). **D1 and D3 still open.** "0 lines of code" is no longer true: `src/vcut`, `tests/` and `web/` hold a skeleton.

## Verdict
**The v2 plan is strong, and the stage docs (01–07), Data Contracts and Tool Allow-list are close to buildable.**
The regressions come from the **late additions**. `pipeline.yaml` was written without the canonical stage
table and contradicts it in ways that would break the plan's two core promises:
- *no money spent before the human gate*;
- *one source of truth for every parameter*.

The other risk is process, not design: about 2,300 lines of plan, **0 lines of code**, and **all 15 ADRs still
*Proposed***. The next useful step is the Resolve capability spike, not more documents.

---

## A. `pipeline.yaml` contradicts the canonical plan (fix before M0)

> **Status 2026-10-15: A1–A9 and B3 fixed.** `pipeline.yaml` is now `vcut.pipeline/2`: a DAG of the
> canonical stages with gates G1–G4, loops L1–L4, LLM roles and no tunables. Contracts §2/§3.7, ADR-005 and
> 00 were updated to match. The previous files are in `_archive/Vcut_pipeline_pre_dag_2026-10-15.zip`.
> Approvals now bind to content hashes, which covers part of B1. **B2 settled** in ADR-005 (shared ledger
> writes): per-stage append-only fragments, a runner-only merge, idempotent merges keyed by content-addressed
> ids, and scoped reads. **B1 settled** in ADR-005 (runs and inheritance): a run is one forward pass; stages are
> inherited by fingerprint through `current/<stage_id>.json` and `run_manifest.json`; gate-approved stages are
> pinned against tool or model drift; completed runs are immutable. **Section B is closed.**

| # | Sev | Finding | Where | Fix |
|---|---|---|---|---|
| A1 | **critical** | **G3 sits after fill.** Stage `03_shots` outputs `cut_list.json` and `assets/` and *then* halts at G3. So paid downloads and generation run **before** the cost gate. The canonical table puts G3 between 03b (plan) and 03c (fill) | `pipeline.yaml` 03_shots | Split 03 into `03ab_plan` (G3) and `03ce_fill_assemble`. The same goes for 04a/04b |
| A2 | **critical** | **The runner is linear and has no loops.** L1 (chapter off budget → 01), L2 (unfillable → re-plan) and L4 (QA error → owning stage) cannot be expressed. Nor can the parallel branches (02 ∥ 03a ∥ 04a) | whole file vs Architecture §3–4 | Add `depends_on: [stage_ids]` (a DAG) plus a `loops:` section. Or say plainly that loops are manual re-runs in v1 |
| A3 | major | **G1 and stage 07 are missing.** There is no G1 outline gate. G4 is attached to `06_resolve`, but nothing after it produces the delivery package | `pipeline.yaml` | Add a G1 checkpoint inside 01 and a `07_delivery` stage gated on G4 |
| A4 | major | **The model name is pinned: `claude-3-7-sonnet`.** It breaks the "role-based, never pin names" rule (01 Tools, Allow-list). It is also an old generation that the Allow-list doesn't list (check Anthropic's deprecation page) | 01_script `tool_choice` | Use roles: `scriptwriter: role:drafting`, `claims_extractor: role:tagging`. Resolve the role to a model in one config file |
| A5 | major | **The parameters conflict with the stage docs.** This brings back the "three duck depths" class of bug that the 10-12 review fixed (item #23) | see the table below | Delete these options from `pipeline.yaml`, or make the docs reference them. Each value should have exactly **one** home |
| A6 | major | **Paths differ from Data Contracts.** Contracts use `research/claims.json`, `script/…`, `voice/…`, `shots/…`, `timeline/…`, `qa/…` and a project-level, content-addressed `assets/`. `pipeline.yaml` uses `runs/<run>/01_script/…` and puts `assets/` **inside the run's 03 folder**. That breaks cross-run asset reuse and the "no re-download on re-run" acceptance test | `pipeline.yaml`, 00 layout, Contracts §2 | Pick one layout; Contracts is the authority. Keep `assets/` and the ledger at project level |
| A7 | major | **Artifacts are missing from the I/O lists.** No stage outputs `asset_registry.json`, which 05's `LICENCE` and `FILES` rules need. 05 doesn't take `script_manifest.json` (chapters) or `brief.yaml` (budget) as inputs. The 03a `candidates.json` and 04a shortlist aren't modelled | `pipeline.yaml` | Generate the I/O lists from the Contracts catalogue, not by hand |
| A8 | minor | **Naming doesn't match 06.** `project_name: {project_id}` and `timeline_name: vcut_{run_id}`, while 06 specifies `vcut_<project_id>` and `<project_id>_v<NNN>` (versioned, never overwritten) | 06_resolve options | Follow 06 |
| A9 | minor | **Tool choices the Allow-list doesn't cover.** `generative_provider: fal_kling` (fal is not listed, and M1 has no generative video). `aligner: ctc_forced_aligner` is the default, although its default model is CC-BY-NC (◐), and the ladder starts with TTS-native timing. `whisper_timestamped` isn't listed | 02, 03 `tool_choice` | Defaults are `tts_native` with no generative provider; add vendors to the Allow-list before using them |

**Conflicting values (A5):**

| Parameter | `pipeline.yaml` | Stage docs / Contracts |
|---|---|---|
| Ducking depth | `ducking_depth_db: -18` | `depth_db: 10.0`, a positive value relative to the open level (Contracts §3.5, 04) |
| Loudness in 04 | `target_loudness_lufs: -14` | 04 "never masters"; −14 LUFS is set only at the final mix (07) |
| WER threshold | `0.10` | "e.g. WER > 5%" (02 step 6) |
| Duration tolerance | `word_budget_tolerance_pct: 5` | ±10 % at G2 and ±5 % in L1 (01, 02) |

## B. Orchestration model: under-specified since "no database"

| # | Sev | Finding | Fix |
|---|---|---|---|
| B1 | major | **Run semantics are undefined.** Every stage reads only *its own* `run_id`'s earlier folders. So when one line is edited after G2, nothing says how run `r0008` gets 01's output without re-running it. The `current/` pointers, item cache and invalidation table (Contracts §4) assume cross-run reuse that the folder model doesn't describe. It is also unclear whether a G2 approval hash survives a new run | Specify how runs are created: a new run inherits `current/` stage outputs by hash. Approvals bind to the **content hash**, not to `run_id` |
| B2 | major | **The ledger is shared mutable state.** 03a and 04a run in parallel, and both write ledger entries to `asset_registry.json`, which is *cross-project*. The research synthesis (Idea 3) recommends SQLite for exactly this, which contradicts ADR-005 "no database", and nobody resolved it | Decide in ADR-005. Either use a single-writer ledger (stages write per-stage fragments that the runner merges), or allow SQLite **only** for the cache and ledger and keep artifacts as files |
| B3 | minor | **The approval enum is defined twice.** ADR-005 says `approval: required \| optional \| none`; the Contracts schema says `required: boolean` | Use one; Contracts wins |

## C. Human gates: the MCP co-pilot can bypass them

| # | Sev | Finding | Fix |
|---|---|---|---|
| C1 | **critical** | **`vcut_approve(gate)` lets an AI agent approve G1–G4.** That defeats principle 1 ("the human decides") and the cost gate. It is also a prompt-injection path: `vcut_review_gate` puts scraped research and media metadata into the agent's context, and that text can ask the agent to approve. `vcut_run(stage)` can likewise start paid stages | MCP gets **read-only** tools plus `request_approval`. Approvals are written only by the Storyboard click or the `vcut approve` CLI on a TTY, and record `approved_by` as a human. Paid stages refuse MCP-initiated runs unless the matching gate file exists |
| C2 | major | **The GUI and MCP aren't in the roadmap.** ADR-009 now bundles an SSE dashboard and an MCP server into the gates, but M0–M3 never schedule them. M1 needs only G2 and G4 | M1: use static HTML pages generated per gate (the contact sheet already exists in 03b) plus `vcut approve`. Move the SSE Storyboard to M2 and MCP to M2/M3 |

## D. Process and repo

| # | Sev | Finding | Fix |
|---|---|---|---|
| D1 | **critical** | **No ADR is accepted.** Four are blocking: ADR-001 (scope), ADR-002 (Resolve Studio vs free; the installed 20.0.1 is apparently free), ADR-006 (budget) and ADR-008 (voice). M0's design depends on ADR-002 | Decide these four this week. Flip them to Accepted or rewrite them |
| D2 | major | **The M0 milestone is too big and in the wrong order.** It holds the schemas for about 17 artifacts, a validator, a quantiser, OTIO and FCPXML writers, and the Resolve spike. But the spike result decides which manifest fields can exist (ADR-004) | **M0a (1–2 days):** a Resolve spike with a hand-built 60 s fixture that fills the capability matrix and checks Python 3.13 compatibility and the `((_atWork_))` path. **M0b:** schemas and compiler for only the fields marked ✔ |
| D3 | major | **There is no version control.** `E:\((_atWork_))\Vcut` is not a git repository; history lives in three zip files. There is already a `.gitignore` | `git init`, then commit. The zip-before-restructure rule in AGENTS can then go |
| D4 | minor | **The doc map is stale.** The AGENTS workspace tree and the Architecture §1 doc map leave out `pipeline.yaml` and `research/`. 00 re-states the whole `pipeline.yaml` inline (a second copy that will drift) | List them; have 00 link to `pipeline.yaml` instead of copying it |
| D5 | minor | **Research quality.** `research/README.md` uses `file:///e:/…` links, which break off this machine. "Both suffer severe degradation >50–100 tool calls" generalises from one issue. The "48 kHz sub-sample sync" claim isn't in any stage doc. Both repos are **AGPL-3.0**: borrow patterns, never code | Use relative links; mark the generalisations *(unverified)*; add an AGPL note |

---

## E. Note on the "SaaS blueprint" prompt
The generic prompt ("SaaS that *fully automates* YouTube videos … publishing") **conflicts with the decisions
already made here**, so don't feed it to a model as the project brief:
- **SaaS and multi-tenant vs local and single-operator.** Resolve Studio is a per-seat desktop app that needs a running GUI session. GPU work is local, and the cost model is per video.
- **"Fully automates publishing" vs "never auto-publishes".** The four human gates are also the mitigation for YouTube's "inauthentic content" rule, which bars mass-produced or templated videos ([[AGENTS#Platform constraints]]).
- **Its sections are already covered.** The vision is in Architecture §2, metrics in §10, MVP in ADR-011, stack in the Allow-list, risks in §11 and privacy in 00 Secrets. Only the **business sections** (personas, pricing, acquisition) are genuinely missing. They matter only if Vcut is meant to become a product for other people, and that would be a new ADR-000 to decide before any SaaS architecture work.

## Recommended order
1. Decide ADR-001/002/006/008 (D1). If Vcut might become a SaaS, decide that first (E).
2. `git init` (D3).
3. Rewrite `pipeline.yaml` against the canonical stage table: split 03 and 04, add a DAG and gates G1 and 07, use roles instead of model names, and remove the duplicated parameters (A1–A9).
4. Make MCP read-only for approvals (C1); defer the Storyboard and MCP to M2 (C2).
5. Write the run and ledger semantics into ADR-005 (B1–B3).
6. Run the M0a Resolve spike (D2).
