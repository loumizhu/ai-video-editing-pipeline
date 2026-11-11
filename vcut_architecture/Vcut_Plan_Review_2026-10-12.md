# Vcut — Plan Review (2026-10-12)

> Review of the v1 plan (9 docs, dated 2026-10-05; archived in `_archive/Vcut_plan_v1_2026-10-05.zip`)
> and a record of how the plan was fixed. Current plan: [[Vcut_End_to_End_Pipeline_Architecture]] · [[AGENTS]].

## Verdict
**The v1 plan had the right instincts but was not buildable.**
- *Right:* a voice-led timeline, a multi-pass script chain, an engine-agnostic manifest, and human polish in a real NLE.
- *Not buildable:*
  - it described **two different products**;
  - its two main docs named **different master NLEs**;
  - it defined **one of five** hand-off artifacts;
  - it had **no stage that makes the edit decisions**;
  - its audio step **depended on its own output**;
  - it promised **Resolve API features that do not exist**;
  - its default free tool stack would have exposed a **monetised channel** to copyright, licence and YouTube-policy problems.

It also had no runner, resume, budget, secrets, validation or MVP. v2 fixes all of this in the docs. The
remaining work is **owner decisions** (all ADRs are *Proposed*) and an **M0 capability spike** in Resolve.

## How it was reviewed
- Four independent lenses, each reading all 9 docs:
  1. architecture / data model / orchestration;
  2. NLE integration;
  3. tools, licensing and platform policy;
  4. creative quality and media engineering.
- Each lens was then checked by an **adversarial verifier**, who tried to refute every finding. Tool, licence and policy facts were re-checked against official sources: the local Resolve scripting README, Blackmagic readmes and codec list, the OTIO repo, vendor terms pages, and YouTube Help.
- A **completeness critic** then looked for what no lens raised.
- Result: ~95 findings (6 refuted or downgraded in part, several merged), deduplicated below into **34 tracked items**.

## What v1 got right (kept)
- The voice is the master clock.
- Multi-pass, chunked scripting with hook variants.
- An NLE-agnostic intermediate manifest; the AI never touches Resolve during the creative phase.
- An editable multi-track result with colour-coded AI review markers.
- Separate voice/SFX/music tracks.
- Remotion demoted to a micro-asset generator.
- A free/paid alternative per stage, now re-keyed on licence.
- Kokoro (Apache-2.0) and Pexels as sound free choices.
- Resolve Studio at $295 is correctly priced.

---

## Tracked items (deduplicated)
Severity after verification. **Fixed in** = where v2 resolves it.

| # | Sev | Item | Source findings | Fixed in |
|---|---|---|---|---|
| 1 | **critical** | Two products in one plan (raw-footage editor vs script-to-video); manifest V1 `host_camera.mp4` has no producer | A1, A2, D21, critic | ADR-001; [[AGENTS]]; Brainstorming banner; V1 = base layer |
| 2 | **critical** | No stage owns edit decisions (slots, cadence, cut timing, candidate choice); no coverage guarantee or fallback | A3, D1, D17 | [[03_Shot_Planning_and_Visuals]] 03b/03e; fallback chain; `COVERAGE_V1` |
| 3 | **critical** | Resolve adapter promised keyframed levels, ducking, zoom animation and transitions the API cannot set | A6, B1, DX2 | ADR-004; [[06_NLE_Adapters#Capability matrix]]; template project |
| 4 | **critical** | No licence/provenance ledger; non-commercial or unusable sources in the default stack (MusicGen CC-BY-NC, Freesound unfiltered, Pixabay "audio API", FMA API, premium libraries via bots) | A8, C4–C7, C12, DX1 | ADR-007; [[Vcut_Tool_Allowlist]]; ledger in [[Vcut_Data_Contracts]]; `LICENCE` rule |
| 5 | **critical** | Automated yt-dlp keyword harvesting of news/interview clips (YouTube ToS, Content ID, reused content); Archive.org mislabelled | C1 | Removed; `inbox/` + `rights_decision` |
| 6 | **critical** | YouTube "inauthentic content" (renamed 15 Jul 2025) and "reused content" risk unaddressed; scraped text could be narrated near-verbatim | C2, CX1, A14 | Human angle in brief + G2; originality check (01); anti-template rules; [[AGENTS#Platform constraints]] |
| 7 | major | Audio step circular / false-parallel (SFX needs cut points from 05; ducking needs voice) | A4, A10 | 04a/04b split; canonical stage table |
| 8 | major | Only 1 of 5 artifacts defined; no stable IDs linking line ↔ audio ↔ slot ↔ asset ↔ clip; bare relative paths | A5, AX4 | [[Vcut_Data_Contracts]] |
| 9 | major | Float seconds, ambiguous `fps: 30`, no source rates, no `source_out`, no sample rate | A12, B6 | Integer frames at a rational rate, quantiser, per-source rates |
| 10 | major | JSON and OTIO both "the" blueprint; OTIO oversold (no volume/transform schema; FCPXML adapter outside the official bundle) | A13, B7, B11, C18 | ADR-003; Vcut's own FCPXML writer |
| 11 | major | Orchestration absent: runner, layout, caching, resume, retries, rate limits, budget, secrets, GPU contention | A7, AX3, critic | [[00_Brief_and_Orchestrator]] |
| 12 | major | Only human checkpoint after all paid generation; hook variants never selected | A14, D7 | ADR-009, gates G1–G4 |
| 13 | major | "The AI agent" writes timecodes and the manifest | A16 | LLM-vs-code table; 05 is pure code |
| 14 | major | Feed-forward only: no loop for duration overrun, sourcing misses, TTS defects | A17, D5 | Loops L1–L4 |
| 15 | major | Single 45-min voice clip + absolute times → every change rebuilds everything; human edits could be overwritten | A15, B10 | Anchors, per-unit A1 clips, versioned timelines, readback |
| 16 | major | Harvest-time trimming removes handles; no alternates for "swap a B-roll" | A18, B5, D16 | Full-source download, handle rule, alternates bins |
| 17 | major | Graphics/titles have no producing stage; `.webm` alpha overlay won't import into Resolve | A20, BX1, B2 | 03c graphics; ProRes 4444 / PNG seq.; ADR-012 |
| 18 | major | No automated validation before Resolve | A21 | [[05_Timeline_Manifest_and_QA#Validation rules]] |
| 19 | major | No MVP: v1 scoped at 10–60 min; milestones targeted the out-of-scope mode and Blender | A19 | ADR-011, roadmap M0–M3 |
| 20 | major | faster-whisper called "forced alignment", "millisecond-exact" | A11, C15, D8 | ADR-015 timing ladder; faster-whisper = QC only |
| 21 | major | Long-form TTS consistency: no display/spoken layers, lexicon, prosody continuity, pause control or audio format policy | D9 | [[02_Voice_and_Timing]] |
| 22 | major | Script chain: hook before body (and 3 conflicting orders), no shared state across chunks, no claim ledger, free-text visual tags, "Hemingway API" | D2–D4, D6, AX1, C21 | [[01_Scriptwriting_Engine]] |
| 23 | major | Loudness and ducking: −14 LUFS on the voice stem, no final-mix measurement, 3 conflicting duck depths, pumping | A22, D10–D12 | 02 dialogue reference; 04 ducking model; [[07_Human_Review_and_Delivery#Mix & loudness QC]] |
| 24 | major | Music: one finite track over the whole timeline; no fitting or transitions | AX2, D14 | 04b music fitting |
| 25 | major | SFX: two competing sources, no density budget, no sync point | D13 | 04b SFX rules |
| 26 | major | Stock: keyword-only relevance, no de-duplication, no text/logo QC, identifiable-people licence limits ignored | D15, C8 | 03b ranking, dedupe, people & brands rule |
| 27 | major | No media conform (VFR, mixed rates, 24 kHz/MP3 audio, WebM/Opus, HDR); 1080p vs "4K render"; proxies never linked | B4, B12, A23, B14, D18 | 03d conform; ADR-010 |
| 28 | major | Embedded/sync audio has no track; it would land on the SFX/voice tracks | B8 | A2 `sync` track, `mediaType` rules |
| 29 | major | pydavinci; Studio/free/headless misstated; no version pin. **Local finding:** installed Resolve is 20.0.1, apparently free | B3, B9, A24, C18 | 06 Requirements & modes; ADR-002 |
| 30 | major | Outdated or mis-described tools and no cost model (Edge-TTS, ElevenLabs tiers, Wan 2.1, Runway Gen-3, Claude 3.5, GPT-4o, Llama-70B local, DDG API, Perplexity, Suno/Udio, Remotion, Adobe Enhance) | C9–C11, C13, C14, C16, C17, C19, C20 | [[Vcut_Tool_Allowlist]]; budget table |
| 31 | major | No AI-content disclosure handling | C3 | ADR-014; ledger synthetic flags |
| 32 | major | No captions, YouTube-valid chapters, description, credits or packaging; chapter and review markers mixed | D19, D20, BX2 | [[07_Human_Review_and_Delivery]] |
| 33 | major | Critic additions: no input contract; no operator workflow; no item-level caching; no run versioning; language unscoped; no hardware profile; secrets and privacy; prompt-injection trust boundary; voice/likeness consent; no observability; no success metrics; no doc structure discipline | critic | 00; ADR-013; 02 voice policy; Architecture §10; AGENTS docs discipline |
| 34 | minor | Doc hygiene: duplicate "3." in AGENTS, stale tree, section gaps, missing Step 07 doc, drifting file names, marker colours unspecified | A25, B13, B15 | All docs rewritten to one template |

### Verification adjustments worth knowing
- **Downgraded critical → major:**
  - A1 alone: the critic argues it should stay critical, as root cause of #1/#2; kept critical in the merged item #1.
  - B2 WebM: a one-line fix.
  - C3 disclosure: penalties apply to *consistent* non-disclosure; a ducked AI bed alone does not trigger it.
  - C5 Freesound: v1 did *intend* CC0; the defect is no enforced filter.
- **Corrected by verifiers:**
  - The edge-tts default boundary is SentenceBoundary.
  - Kokoro's token timestamps are in the *official* pipeline (English only).
  - MusicGen *can* extend past 30 s natively, but its weights are non-commercial regardless.
  - Pexels attribution is an API-app guideline, not a licence condition on the video.
  - Pixabay "full API access" applies to images only.
  - A Freesound SFX placement is not one download each (reuse).
  - Strict per-sentence TTS breaks prosody, so v2 synthesises per **unit**.
- **Contested:** Perplexity's endpoint retirement date (pages inconsistent); WebM evidence for current Resolve (the codec list for v20 has no WebM; newer versions unconfirmed).

---

## Factual corrections (v1 claim → reality, checked 2026-10-12)
| v1 said | Reality | Source |
|---|---|---|
| faster-whisper does "Forced Word-Level Alignment", "millisecond-exact" | Transcription with heuristic cross-attention/DTW word times; takes no reference text; no diarisation | faster-whisper `transcribe.py`; WhisperX README |
| Resolve API sets "keyframed audio levels", "ducking parameters" | No volume, keyframe or ducking API; transitions and fades scriptable only from Studio 21.1 | Resolve scripting README v20; 21.1 readme |
| `pydavinci` = native API | Unofficial wrapper, last release 0.2.3 (May 2022), "needs maintainers" | PyPI, GitHub |
| Headless Resolve "requires an active desktop display session" | `-nogui` headless is documented; the real limits are Studio-only scripting (all Python since 21.1) | README v20; 21.1 readme |
| Overlay `intro_title.webm` | Resolve's codec list has no WebM container and no VP9 alpha | Resolve 20 codec list |
| `.otio` "loaded directly" into Blender, Resolve, Premiere, FCP | Resolve native; Premiere recent versions; FCP needs FCPXML; Blender add-ons only. No volume/transform schema in OTIO | OTIO docs; Adobe notes (snippet) |
| Freesound = "CC0" | CC0, CC-BY, **CC-BY-NC**, Sampling+; OAuth2 for originals; 500 originals/day | Freesound FAQ, API docs |
| "Pixabay Audio" via API | API serves images and videos only | Pixabay API docs |
| MusicGen = free / open source | Code MIT, **weights CC-BY-NC 4.0** | audiocraft README |
| Free Music Archive API | No current API documentation found | — |
| Suno API / Udio | No public Suno self-serve API; Udio downloads disabled since Oct 2025 *(secondary)* | Suno help; DMN |
| Edge-TTS = free Microsoft neural voices | Unofficial endpoint; no commercial licence found; breaks on token rotation | edge-tts repo |
| Claude 3.5 Sonnet / GPT-4o | Retired 28 Oct 2025 / legacy | Anthropic and OpenAI deprecation pages |
| Llama 3.3 70B local | ≈43 GB; does not fit this 16 GB GPU | Ollama |
| Wan 2.1 local; Runway Gen-3 | Wan 2.2 is the current open-weights release (≥24 GB VRAM); Runway at Gen-4.x *(secondary)* | Wan2.2 README |
| CogVideoX local B-roll | 720×480, 8 fps, 6 s; commercial use needs registration | HF model card |
| DuckDuckGo Search API | Only the Instant Answer API (not full results) | DDG API page |
| Hemingway Editor API | None found; readability, not duration | — |
| Adobe Podcast Enhance (pipeline stage) | No public API | — |
| Whisper Cloud API | `whisper-1` deprecated 26 Aug 2026, shutdown 26 Feb 2027 | OpenAI deprecations |
| Remotion = free / open source | Source-available; Company License above 3 employees | Remotion LICENSE.md |
| Archive.org = "Paid / Commercial" | Free; **no copyright guarantee** per item | archive.org rights help |
| yt-dlp automated keyword download | YouTube ToS bar downloading and automated access | YouTube Terms |
| Pexels/Pixabay "automated REST downloads" | Pexels 200/h, 20k/month; Pixabay 100/60 s, 24 h cache, no mass downloads; identifiable-people limits | Pexels and Pixabay docs |
| Voice stem → −14 LUFS | −14 LUFS is a programme-level reference *(secondary)*; dialogue stem ≈ −18 LUFS (AES TD1008) | TD1008 summary |
| Blender proxies 25/50/100% | 25/50/75/100% | Blender manual |

---

## What changed in the vault
| v1 file | v2 |
|---|---|
| `AGENTS.md` | Rewritten: scope, 7 principles (renumbered), platform constraints, docs discipline |
| `Vcut_End_to_End_Pipeline_Architecture.md` | Rewritten as the hub: doc map, **canonical stage table**, one stage graph with gates and loops, LLM-vs-code table, budget, roadmap, success metrics, risks |
| `Vcut_LongForm_Pipeline_Brainstorming.md` | Kept as **archived exploration** (Mode B background), with a banner and inline corrections |
| `01_Scriptwriting_Engine.md` | Rewritten (9-step chain, claims, originality, structured visual beats, G1/G2) |
| `02_Voice_and_Speech_Synthesis.md` | → **`02_Voice_and_Timing.md`** |
| `03_Visual_and_B-Roll_Harvesting.md` | → **`03_Shot_Planning_and_Visuals.md`** (adds the missing edit-decision stage) |
| `04_Audio_and_SFX_Mastering.md` | → **`04_Music_SFX_and_Ducking.md`** (it never mastered anything) |
| `05_Vcut_JSON_and_OTIO_Blueprint.md` | → **`05_Timeline_Manifest_and_QA.md`** (JSON canonical, OTIO/FCPXML exports, validation) |
| `06_NLE_Adapters.md` | Rewritten (modes, build sequence, capability matrix, readback, versioning) |
| — | **New:** `00_Brief_and_Orchestrator.md`, `07_Human_Review_and_Delivery.md`, `Vcut_Decision_Log.md`, `Vcut_Data_Contracts.md`, `Vcut_Tool_Allowlist.md`, this review |

---

## Open items

### Owner decisions (decide first; all ADRs are *Proposed*)
1. **ADR-001:** is v1 really script-to-video, with recorded footage deferred?
2. **ADR-002:** buy **Resolve Studio** ($295), or accept FREE mode (manual FCPXML import; no bins, markers, readback). The installed 20.0.1 appears to be free. **Don't upgrade free past 21.0** if you plan to use in-app scripts.
3. **ADR-006:** the default per-video budget cap and the generative-video share.
4. **ADR-007:** confirm the strict licence policy, including no automated third-party clips.
5. **ADR-008:** narrator: your own voice, ElevenLabs paid, or Kokoro.

### M0 spikes (prove before relying on the manifest fields)
- Fill the capability matrix on the pinned Resolve version: ducker via template/preset, FCPXML Ken Burns and keyframes, OTIO markers, 21.1 transition/fade method names, clip gain.
- `recordFrame` absolute vs offset; `AddTrack` layouts; import with the `((_atWork_))` path.
- Python version supported by the `DaVinciResolveScript` module vs the installed Python 3.13.
- Licences of forced-alignment models (WhisperX/wav2vec2, MFA), and of DeepFilterNet weights if used.

### Facts still unverified (re-check before depending on them)
- Cloud generative-video prices.
- Tavily pricing.
- Perplexity endpoint timeline.
- Premiere's minimum OTIO version.
- Pixabay Content ID "shield" process.
- Udio status.
- DeepSeek V4 licence.
- Epidemic Creator-plan channel limit.
- Resolve's full marker colour list (secondary sources).
- Whether this machine's Resolve is free or Studio.
