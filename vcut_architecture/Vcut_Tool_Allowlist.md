# Vcut — Tool Allow-list (dated)

> **Sorted by what matters, not price:** may the output go into a **monetised** YouTube video, and
> do the terms **allow automation**? v1's "Free / Open-Source vs Paid" columns mixed open licences,
> API-terms services, source-available software and non-commercial models, which caused most of the legal
> findings in [[Vcut_Plan_Review_2026-10-12]]. Policy: [[Vcut_Decision_Log#ADR-007 — Licence & source policy]].
>
> **Every row is dated.** Vendors drift (model retirements, API migrations, licence changes), so re-verify
> before each milestone. *(unverified)* marks a fact taken from secondary sources only.

**Status legend:** ✔ production · ◐ draft/prototype or restricted use · ⏸ manual only (the owner puts files in `00_input/media/` or `libraries/`, with a licence note) · ✘ excluded

---

## Research
| Tool | Status | Licence / terms | Automation | Notes (verified 2026-10-12) |
|---|---|---|---|---|
| Tavily | ✔ | Commercial API | ✔ | Acquired by Nebius (closed 19 Feb 2026). Pricing ≈$0.008/credit *(unverified)* |
| Perplexity Search API / Agent API | ✔ | Commercial API | ✔ | Sonar chat-completions is migrating to the Agent API (staff post gives 27 Sep 2026; Perplexity's own pages are inconsistent). Pin the endpoint at implementation |
| SearXNG (self-hosted) | ◐ | AGPL, self-hosted metasearch | ✔ | JSON output must be enabled (HTML only by default); upstream engines may block. Best-effort free path |
| DuckDuckGo "Search API" | ✘ | — | — | Only the Instant Answer API exists, not full web results; `ddgs` is unofficial scraping |
| Hemingway Editor API | ✘ | — | — | No public API found; it measures readability, not spoken duration |

## AI providers (roles: drafting, tagging, vision)
Each role binds to `cloud`, `local`, `agent` or `none` ([[Vcut_Decision_Log#ADR-016 — AI providers and the no-AI path]]). `none` is always allowed.

| Tool | Status | Notes |
|---|---|---|
| Current frontier API model (`cloud`) | ✔ | e.g. as of 2026-10: Claude Sonnet 5.5 ($2 / $10 per MTok in/out) for drafting; Haiku 5.5 ($0.10 / $0.50) for tagging. Configure by role; never pin names in docs |
| Ollama local models (`local`) | ◐ per model | Installed 2026-10-26: `gemma4:12b` 7.6 GB, `gemma4:latest` 9.6 GB, `gemma4:26b-a4b-it-qat` 15.6 GB, `qwen3.8:27b` 17.7 GB, `glm-4.7-flash` 19.0 GB (`ollama list`). **Licence of each model's weights to be checked before `final`-tier use** (unverified). Only models ≤ ~10 GB leave room on the 16 GB GPU for Kokoro/aligners. Good fit for `tagging`; `drafting` (Mode W) quality untested |
| **Antigravity IDE** (`agent`, **default**) | ✔ M1, window mode | Installed: **v1.107.0** (`%LOCALAPPDATA%\Programs\Antigravity IDE`, CLI `bin\antigravity-ide.cmd`). Checked 2026-10-26 from its `--help`: `chat [prompt] -m ask\|edit\|agent -a <file> -n/-r` opens a chat session **in a window**, and `--add-mcp` registers an MCP server. No stdout answer, so Vcut uses the task-file interface. The model behind it and its data terms: record in the vendor table |
| Antigravity CLI `agy` (headless) | ? not installed | Third-party sources (a CLI cheat sheet, community MCP bridges) describe `agy -p "<prompt>" --output-format json` and report piped stdout going silent. **Unverified; no official doc found.** Would allow headless autopilot if adopted |
| Claude Code (`agent`) | ◐ | `claude` CLI on PATH here (2026-10-26). Headless `-p` mode with JSON output *(flags to verify at M1)* |
| Claude Desktop (`agent`, pull) | ◐ | No command to send it a task; connects to `vcut mcp` as a client and pulls tasks. Review-mode runs only |
| Hermes (`agent`) | ◐ | Reachable on this workstation through the agent-workers MCP (2026-10-26) |
| *All agent apps* | — | Used only through the confined task interface ([[00_Brief_and_Orchestrator#Run model]]). Whatever model the agent uses inherits that model's terms and data handling; record them in the vendor table below |
| Claude 3.5 Sonnet | ✘ | Retired 28 Oct 2025; requests fail |
| GPT-4o | ✘ | Legacy (snapshot `gpt-4o-2024-05-13` shuts down 23 Oct 2026) |
| DeepSeek V4 (API or open weights) | ? | Released Apr 2026; MIT weights for Flash per secondary sources *(unverified)* |
| Llama 3.3 70B local | ✘ (this machine) | ≈43 GB at Q4; does not fit the 16 GB GPU |

## Voice & timing
| Tool | Status | Licence / terms | Notes |
|---|---|---|---|
| Owner's recorded voice | ✔ | Own | Best inauthentic-content mitigation. Forced-align the known text |
| **Qwen3-TTS** (local, default) | ✔ draft · ◐ final until the weights licence is confirmed | Code **Apache-2.0** (GitHub `QwenLM/Qwen3-TTS` README, 2026-10-26); weights licence **not stated on the README** (secondary sources: Apache-2.0) — check the Hugging Face model card | Released Jan 2026; 0.6B / 1.7B; 10 languages incl. English; streaming; voice clone from a short reference clip (owner's own voice only); **no word timestamps** → forced alignment; output sample rate not stated → resample to 48 kHz. VRAM 4–8 GB *(secondary, unverified)* |
| Kokoro-82M | ✔ (draft; final if quality accepted) | Apache-2.0 weights | 24 kHz output; v1.0 has 8 languages, 54 voices; token timestamps **English only** |
| ElevenLabs (paid plan) | ✔ | Commercial on all paid plans except Beta Services | Free plan: non-commercial + attribution. `/with-timestamps` gives character alignment. Professional Voice Clone = **own voice only**. PCM 44.1 kHz needs Pro+. Credits/month: Starter 30k · Creator 121k · Pro 600k |
| Azure AI Speech | ? | Licensed Microsoft service | The legitimate route to Microsoft neural voices *(pricing unverified)* |
| Edge-TTS | ◐ prototype only | Unofficial use of Edge read-aloud; GPL-3.0 wrapper | No commercial licence found; breaks when its rotating token goes stale (HTTP 403); custom SSML blocked; 24 kHz MP3 |
| WhisperX / Montreal Forced Aligner | ✔ | Check code + model licences at M0 | Forced alignment of known text (human-voice path; fallback) |
| ctc-forced-aligner | ◐ | Default MMS model **CC-BY-NC** | Only with a commercially licensed model |
| faster-whisper | ✔ QC only | MIT | Transcription with heuristic word times; **not** a forced aligner; no diarisation |
| OpenAI `whisper-1` | ✘ | — | Deprecated 26 Aug 2026, shutdown 26 Feb 2027 (`gpt-4o-transcribe` the same date) |
| DeepFilterNet | ◐ human voice only | Code MIT/Apache-2.0; **weights licence unstated** | 48 kHz WAV input only. Useless on clean TTS |
| Adobe Podcast Enhance | ⏸ | Web tool | No public API |

## Visuals
| Tool | Status | Licence / terms | Automation | Notes |
|---|---|---|---|---|
| Pexels API | ✔ primary | Free commercial use; attribution not required by the licence (the API guidelines ask for a credit) | ✔ 200 req/h, 20k/month (raise on request) | No identifiable people in a bad light; no implied endorsement. Search has no duration filter |
| Pixabay API (video) | ✔ low volume | Content licence; restrictions on recognisable people and trademarks | ✔ 100 req/60 s; **cache 24 h; no mass downloads; "real human requests"** | Show "Pixabay" next to results in any review UI |
| Storyblocks | ⏸ | Subscription | Contracted API only (client agreement priced by libraries and MAU) | Manual in v1 |
| Envato Elements | ⏸ | Subscription | **Bots and mass download prohibited** | Manual only |
| Artlist / Artgrid footage | ⏸ | Subscription | No public footage API found | Manual only |
| Wikimedia Commons API (images) | ✔ search + download, licence per file (from M1) | Per file: PD/CC0 ✔; CC-BY ✔ with credit; **CC-BY-SA** ◐ needs a rights decision; anything else ✘ | ✔ with a descriptive User-Agent and polite rate *(API etiquette to re-check at M1)* | Read the licence from the file's metadata; **no copyright guarantee**, so the ledger keeps the page URL and licence text. Person photos for cards |
| Archive.org / other archives | ⏸ | Per item; **no copyright guarantee** | — | `00_input/media/` + human `rights_decision` per item, per jurisdiction |
| Article captures (headless browser, e.g. Playwright) | ◐ M2, opt-in | The page's own copyright; short excerpt with attribution; **rights decision** per capture | Only pages already cited in `claims.json`; skip sites whose terms forbid automated access | Re-typeset article card is the default |
| Natural Earth (map data) | ✔ M3 | Public domain | ✔ | Base maps for `map.*` presets, rendered locally |
| EffectCraft CLI | ⏸ not used in M1–M2 | **EffectCraft's own licence not yet checked** | ✔ headless | Installed here (2026-10-26). Withdrawn as the effects renderer on 2026-10-27: titles and effects are native in the editor ([[Vcut_Decision_Log#ADR-021 — One editor: everything native and editable]]). Candidate only for M3 opt-in pre-renders |
| yt-dlp / screen capture of third-party video | ✘ | YouTube ToS bar downloading and automated access; Content ID; "reused content" | — | Allowed only for the owner's **own** uploads |
| Cloud generative video (Runway Gen-4.x, Kling 3.x, Luma Ray3.x …) | ✔ ≤ cap, paid tier | Commercial use only on paid tiers (Luma Free/Lite personal-use: official; others: secondary) | ✔ | ≈$0.05–0.58/s *(unverified)*. Stylised prompts; no photoreal real people or events; disclosure flags |
| Wan 2.2 (local) | ✘ (this machine) | Apache-2.0 | — | TI2V-5B needs ≥24 GB VRAM (~9 min per 5 s at 720p); A14B needs 80 GB. Wan 2.1 superseded, 16 fps |
| CogVideoX-5b | ✘ | Commercial use needs registration | — | 720×480, 8 fps, 6 s only |
| Matplotlib / Pillow / NumPy | ✔ | Permissive | ✔ | Library tooling only: generating overlay texture clips once, contact-sheet thumbnails. Not used for titles or cards (native in the editor) |
| Blender | ✔ | GPL; output is yours | ✔ | Optional for 3D graphics |
| Remotion | ⏸ not used in M1–M2 | Source-available: free for individuals, non-profits and companies ≤3 people; otherwise paid Company License | ✔ | Only a candidate for M3 opt-in pre-renders (ADR-021) |

## Audio
| Tool | Status | Licence / terms | Notes |
|---|---|---|---|
| Curated local SFX library (CC0 + owned packs) | ✔ | Per file in the ledger | Built once, reused |
| Freesound API | ✔ CC0 (+ CC-BY with credit) | Mixed: CC0 / CC-BY / **CC-BY-NC** / **Sampling+** | Filter at query time. OAuth2 for originals; 60/min, 2,000/day; originals 30/min, 500/day. Commercial API use "negotiated case by case with UPF": **ask first** |
| Pixabay Music / SFX | ⏸ | Pixabay licence; some tracks in Content ID *(third-party reports)* | The API has **no audio endpoint**. Keep the certificate |
| Epidemic Sound | ⏸ (plan) | Subscription; plan must match legal entity | Partner API needs an agreement; the free API tier (50 lifetime downloads) is not publishable |
| Artlist music | ⏸ | Subscription | Enterprise API via account manager *(unverified)* |
| Boom Library | ⏸ | Per-user perpetual packs | No API found |
| Suno | ⏸ paid plan | Commercial rights only for songs made while subscribed | Pro 20 / Premier 60 downloads a month (official). No public self-serve API |
| MusicGen | ✘ | **Weights CC-BY-NC 4.0** | Non-commercial; not usable in monetised video |
| Udio | ✘ | — | Downloads disabled since Oct 2025 *(secondary reports)* |
| Free Music Archive "API" | ✘ | — | No current API documentation found |
| FFmpeg / librosa | ✔ | LGPL/GPL builds / ISC | Measuring, resampling, baked stems, beat detection |

## NLE & interchange
| Tool | Status | Notes |
|---|---|---|
| DaVinci Resolve Studio | ✔ (pin version) | **Default editor** (owner, 2026-10-27). US$295 one-off. **Python scripting is Studio-only from 21.1.** 21.1 adds scripted transitions, fades and audio normalise. Its native MCP server is for interactive use, not the build path. Needed for full autopilot into Resolve |
| DaVinci Resolve free | ◐ one-click native build (to verify at M0a); ✔ IMPORT fallback | Installed here: 20.0.1. The Vcut build script runs from *Workspace → Scripts* (in-app scripting, free ≤21.0); manual FCPXML import as fallback ([[06_NLE_Adapters#Targets]]). Scripting README (local, "Last Updated: 7 May 2025", read 2026-10-27) lists `InsertFusionTitleIntoTimeline`, `GetFusionCompByIndex`, `ImportFusionComp`, `ApplyGradeFromDRX`, `SetLUT`, the `CompositeMode` / `DynamicZoomEase` properties, `AddMarker`, `ImportTimelineFromFile`; no transition call |
| FilmCraft (storytold) | ◐ alpha; **alternative editor, full autopilot** | **Installed here 2026-10-27: 0.13.0** at `C:\Program Files\FilmCraft\` (`filmcraft.exe`, `filmcraft-cli.exe`; file version 0.13.0, copyright "MIT OR Apache-2.0"). From the README (2026-10-26): MIT OR Apache-2.0; macOS/Windows/Linux (+ browser via WebAssembly); Windows x64/arm64/x86 MSI or portable ZIP, "far less testing than macOS"; imports/exports FCP7 XML, **FCPXML 1.9–1.11**, **OTIO** (`metadata.filmcraft`), CMX 3600 EDL, AAF, OMF 2.0; `filmcraft-cli` (650+ commands), headless MCP server, JSON-lines TCP control channel; exports H.264 MP4, ProRes 422 HQ, DNxHR/ProRes MXF, PNG sequences, WAV; H.265 via hardware encoders only; no AV1. Pin **0.13.0** |
| FilmCraft CLI (`filmcraft-cli` 0.13.0) | ✔ headless build (probe 2026-10-27) | The FilmCraft adapter's only interface: `run build.jsonl --save-as p.fcproj`, `inspect sequence` for readback, `export` for the preview. About 700 commands (`commands`, `describe <id>`); ticks = 254 016 000 000 per second. Probe passed: placement, Motion keyframes, cross dissolve, Light Leaks/Noise/Vignette, text graphic, graphics template export + apply with a named control, chapter marker, frame render, a `((…))` path. CLI/JSON commands only, never UI automation |
| `DaVinciResolveScript` (official) | ✔ | The only connector |
| pydavinci | ✘ | Last release 0.2.3 (May 2022), needs maintainers, cannot pass `clipInfo` dicts |
| OpenTimelineIO | ✔ export / archive / readback | Apache-2.0. Core adapters are only `.otio/.otioz/.otiod`; the OpenTimelineIO-Plugins bundle has aaf, ale, burnins, cmx3600, fcp (FCP7 XML), maya, svg, xges — **no FCPXML** |
| otio-fcpx-xml-adapter | ◐ | Community; last release 1.0.0 (Jul 2023). Vcut writes its own FCPXML instead |
| Blender VSE | ✘ v1 | No native OTIO import (add-ons only) |
| Premiere Pro / Final Cut Pro | out of scope | Premiere imports OTIO in recent versions (minimum version unconfirmed: 25.6 vs 26.0); FCP needs FCPXML conversion |

## Script intake
| Tool | Status | Notes |
|---|---|---|
| Plain text / Markdown parser | ✔ | Own code; no dependency needed |
| .docx reader (e.g. python-docx) | ? | Licence and maintenance to verify at M1 before use; until then, ask the owner to save as .txt/.md |

## Vendor data handling (fill before M1)
For each cloud vendor, record: data retention period, whether inputs are used for training (and the opt-out), region. Projects with `privacy: local_only` may use only local tools ([[00_Brief_and_Orchestrator#Secrets & data handling]]).

| Vendor | Retention | Training on inputs | Opt-out | Checked |
|---|---|---|---|---|
| LLM provider | | | | |
| ElevenLabs | | | | |
| Search provider | | | | |
| Generative video provider | | | | |
| Owner's agent (`agent` provider) and the model behind it | | | | |

---

## Primary sources used (2026-10-12)
- Resolve: local scripting README v20 (`C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\README.txt`) · 21.1 readme `blackmagicdesign.com/support/content/readme/baf7c071c0524fbf8ccc961925c9f443` · Resolve 20 codec list `documents.blackmagicdesign.com/SupportNotes/DaVinci_Resolve_20_Supported_Codec_List.pdf`
- OTIO: `opentimelineio.readthedocs.io` · `pypi.org/pypi/OpenTimelineIO-Plugins/json` · `pypi.org/pypi/otio-fcpx-xml-adapter/json`
- pydavinci: `pypi.org/project/pydavinci` · `github.com/pedrolabonia/pydavinci`
- YouTube: monetisation policies `support.google.com/youtube/answer/1311392` · synthetic disclosure `…/answer/14328491` · chapters `…/answer/9884579` · Terms `youtube.com/static?template=terms`
- Freesound `freesound.org/help/faq/`, `freesound.org/docs/api/overview.html`, `freesound.org/help/tos_api/` · Pexels `pexels.com/api/documentation/`, `pexels.com/license/` · Pixabay `pixabay.com/api/docs/`, `pixabay.com/service/license-summary/`
- Kokoro `huggingface.co/hexgrad/Kokoro-82M` · edge-tts `github.com/rany2/edge-tts` · ElevenLabs `help.elevenlabs.io/hc/en-us/articles/13313564601361`, `elevenlabs.io/pricing` · faster-whisper `github.com/SYSTRAN/faster-whisper` · WhisperX `github.com/m-bain/whisperX` · ctc-forced-aligner `github.com/MahmoudAshraf97/ctc-forced-aligner` · DeepFilterNet `github.com/Rikorose/DeepFilterNet`
- Wan 2.2 `github.com/Wan-Video/Wan2.2` · CogVideoX `huggingface.co/THUDM/CogVideoX-5b` · Luma `lumalabs.ai/learning-hub/licensing` · audiocraft/MusicGen `github.com/facebookresearch/audiocraft` · Suno `help.suno.com/en/articles/13614785` · Remotion `github.com/remotion-dev/remotion/blob/main/LICENSE.md`
- Storyblocks `storyblocks.com/business-solutions/api` · Envato `help.elements.envato.com/hc/en-us/articles/360000621743` · Epidemic `developers.epidemicsound.com/docs/`
- FilmCraft (2026-10-26): `github.com/storytold/filmcraft` README · Ollama models: `ollama list` on this workstation (2026-10-26)
- Local checks (2026-10-27): `C:\Program Files\FilmCraft\filmcraft.exe` file version; `filmcraft-cli --version`, `--help`, `commands`, `describe`, `effects.list` and a headless build probe in a scratch folder · Resolve scripting README at `C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\README.txt` ("Last Updated: 7 May 2025")
- Local checks (2026-10-26): `antigravity-ide --help` and `chat --help` (v1.107.0), `effectcraft-cli --help`, PATH lookup for `agy`, `claude`, `ollama` · Qwen3-TTS: `github.com/QwenLM/Qwen3-TTS` README · Antigravity `agy` CLI: third-party only (computingforgeeks cheat sheet, glama.ai MCP bridge listings), unverified
- Anthropic deprecations `platform.claude.com/docs/en/about-claude/model-deprecations` · OpenAI deprecations `developers.openai.com/api/docs/deprecations` · Nebius/Tavily `nebius.com/newsroom/…`
