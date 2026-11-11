# Step 03: Shot Planning & Visuals

## Links
- **Hub:** [[Vcut_End_to_End_Pipeline_Architecture]] · **Contracts:** [[Vcut_Data_Contracts#3.3 shot_plan.json]], [[Vcut_Data_Contracts#3.4 asset_registry.json — licence and provenance ledger]]
- **Previous:** [[01_Scriptwriting_Engine]] (03a starts after G2) and [[02_Voice_and_Timing]] (03b needs `timing.json`)
- **Next:** [[04_Music_SFX_and_Ducking]] (04b needs `cut_list.json`) → [[05_Timeline_Manifest_and_QA]]

---

## Purpose
This is the **editor's chair** and the **media research** step. It finds every image, clip and piece of footage
the video needs, turns visual intent plus voice timing into a **shot plan** (which slot starts and ends on which
word, how long shots hold, which licensed asset and which effect preset fill each slot), then downloads,
conforms and trims the media, keeping handles and alternates for the human, **filed by chapter in the video's
folder** ([[Vcut_Decision_Log#ADR-019 — Per-video folder organisation]]). In v1 nothing owned these decisions:
03 "harvested and trimmed" before slot lengths existed, and 05 only assigned tracks.

## Inputs → Outputs
| In | Out |
|---|---|
| `visual_beats[]` (with `effects`, `entity`), `timing.json`, `project.yaml` (`media`, `style`, budget), `channel_profile.yaml` (base layer, library), effects library | `shots/candidates.json`, `shots/shot_plan.json` + contact sheet + cost estimate (G3) |
| `00_input/media/` (owner's own media), `libraries/media/` | `assets/…` + ledger entries, conformed media, `shots/cut_list.json` (with each slot's effect presets and title values); readable copies in `03_media/<NN>_<chapter>/` |

## Media types a documentary needs
| Type (`visual_beats[].type`) | Source, in search order | Notes |
|---|---|---|
| Own media (`own_media`) | `00_input/media/`, then `libraries/media/` | Always searched first; licence note required |
| Stock video (`stock_video`) | Pexels → Pixabay | B-roll of places, objects, processes, moods |
| Photos (`stock_photo`, `commons_image`) | Pexels/Pixabay photos → **Wikimedia Commons** (historic photos, people, places, documents) | Stills get a motion preset (`mot.push_in`…). Commons licence per file in the ledger: CC0/PD ✔; CC-BY ✔ with credit; CC-BY-SA needs a rights decision |
| Person / org card (`person_card`, `org_card`) | `entity` → Wikidata id → Commons image | No licensed photo → silhouette card. Never an AI face of a real person |
| Article (`article_card`, `article_capture`) | A source already in `claims.json` | Card = re-typeset (M1); capture = screenshot with a rights decision (M2) |
| Chart / text card (`chart`, `text_card`) | Claim data / the script | Native title templates in the editor ([[Vcut_Effects_Library]]); charts M2 |
| Map (`map`) | Natural Earth base data (public domain): a still map image + native pin/label template | M3 |
| Archival / news footage (`archival_inbox`) | Owner only, via `00_input/media/` with a rights decision | Never downloaded automatically |
| Generative (`ai_video`) | Cloud, paid tier, capped | Off by default |

## Sub-stages

### 03a — Media research (after G2, in parallel with 02)
- Search the **owner's own media and the channel library first**, then providers in allow-list order: **Pexels** (primary, video and photos), **Pixabay** (low volume, results cached 24 h, never bulk-harvested), **Wikimedia Commons** (images, via its API with a descriptive User-Agent, licence read per file).
- **Entities:** for beats with an `entity`, look up the Wikidata item and its Commons image(s) for person/org cards and place names for location stamps.
  - Requests go through the per-provider rate limiter ([[00_Brief_and_Orchestrator#Run model]]).
  - Search runs the beat's 3–5 queries and fetches **previews only**: thumbnails and Pexels `video_pictures`.
- Post-filter: Pexels `/videos/search` has no duration parameter, so filter on duration, landscape orientation and resolution ≥ delivery.
- Pull top N per query (default 8).
- **Author cues first:** a beat with `source: author_cue` searches the owner's words as given before any expanded queries ([[01_Scriptwriting_Engine#Script input format (Mode S)]]).

### 03b — Shot plan (needs `timing.json`) → **G3**
- **Segmentation.** The AI (`tagging` role) proposes how each beat splits into slots and anchors them to word edges. Code enforces the cadence rules and computes the frames. *With AI `none`:* one slot per beat, split by code wherever the beat exceeds the maximum hold.
- **Cadence rules** are tunable starting values, refined from G4 edit statistics:
  - cut on a word or phrase onset with a −2-frame lead;
  - minimum shot 1.5 s;
  - **maximum hold of one still run** = the pacing preset's hard cap (default 6.0 s, never above 8.0 s), tightened by beat intensity; a still past its soft cap needs enrichment events ([[Vcut_Decision_Log#ADR-022 — Still-hold budget, enrichment and pacing presets]]; replaces "4–8 s by section energy");
  - a visual change at least every N seconds;
  - one pattern interrupt per ~45–60 s (graphic, text card, scale change).
- **Ranking:**
  1. image–text embedding similarity (CLIP/SigLIP class) between the beat description and the previews. This is a **local scoring model run as code**, not an AI role, so it runs even when every AI role is `none` (it fits the 16 GB GPU; if unavailable, provider relevance order is used);
  2. a vision-model yes/no check on the top-k (*matches the beat? visible text/logo/watermark/chyron? quality OK?*) — `vision` role; with `none`, skipped and the slot shown yellow at G3;
  3. reject on `negative_terms`.
  4. Choice among the top candidates: the `tagging` role picks **by id**; with `none`, the top score wins.
- **De-duplication:**
  - never reuse a provider asset id within a video;
  - reject candidates above a perceptual-hash or embedding similarity threshold to anything already used;
  - penalise the same author within a chapter;
  - cap re-use across the channel's recent videos (library ledger).
- **People & brands:** if `context_sentiment` is negative or the line describes wrongdoing, allow only footage with **no identifiable people or brands** (crowds from behind, hands, objects), or flag the slot for a human pick. Pexels and Pixabay licences forbid showing identifiable people in a bad light and implying endorsement, and Pixabay restricts recognisable trademarks.
- **Generative slots:** proposed only where stock fails *and* the beat is conceptual, up to `generative_video_max_pct`. Each is priced individually.
- **Effects per slot** ([[Vcut_Effects_Library]]): owner's `[effect:]` cues → the chosen look's style rules (e.g. Commons/historic photo → `look.old_film` + `mot.push_in`; first mention of a place → `txt.location_stamp`; first mention of a person → `ppl.person_card`; a quoted source → `doc.article_recreated`) → AI `tagging` proposals by preset id. Code applies the density and rotation rules, and records each preset and its values in the slot.
- **Photo/video balance:** `project.yaml` `media.photo_share` (default 0.4 for documentary): stills with motion are a feature of the style, not a fallback.
- **Output:** `shot_plan.json` (top-N ranked candidates, scores and effects per slot), an HTML **contact sheet** (thumbnails, licence, effects preview per slot), and a **cost + ETA estimate** → **G3** (review, or auto under the owner's policy).

### 03c — Fill (only G3-approved slots)
- **Stock:** download the chosen asset **and the top 2 alternates**, as **full source**. Never re-encode to the used range. Write a ledger entry per file, including licence, author, URL and terms snapshot.
- **Titles, cards and effects are not rendered here** ([[Vcut_Decision_Log#ADR-021 — One editor: everything native and editable]]). 03c only records, per slot, the preset ids and their text values (quote and number text from `on_screen_text`; chart data must cite a `claim_id`); 06 builds them as native titles, transitions and effects in the chosen editor ([[Vcut_Decision_Log#ADR-012 — Graphics & titles producer]]).
- **Media for presets:** photos for person/org cards (Commons, owner's library, else the silhouette placeholder), article screenshots (M2, below), and overlay clips from `libraries/effects/overlay_media/` are filed like any other asset, with a ledger entry.
- **Base layer:** the branded **base-layer plate** for V1 is a library clip (made once in the editor and exported), not rendered per video.
- **Generative video:**
  - paid commercial tier only, with `plan_tier_at_generation` recorded;
  - prefer **stylised** prompts;
  - **never photoreal depictions of identifiable real people or real news events**;
  - synthetic flags written to the ledger for disclosure ([[Vcut_Decision_Log#ADR-014 — AI-content disclosure]]).
- **Article captures (M2, opt-in in the setup form):** a headless-browser screenshot of a page **already cited in `claims.json`** (never a URL proposed by an AI), cropped to the headline/excerpt, stored with `rights_decision` pending; under autopilot it is placed with a red marker until the owner decides. Sites whose terms forbid automated access are skipped (re-typeset card instead).
- **Filing:** every placed asset is linked into `03_media/<NN>_<chapter-slug>/` as `<slot_id>_<3-word slug>__<source>.<ext>`, its alternates into `alternates/<slot_id>/`, overlays into `03_media/overlays/` ([[00_Brief_and_Orchestrator#Workspace layout]]).
- **Archival / news / third-party footage:** **only via `00_input/media/`**, with a recorded `rights_decision` (licence, public domain, own footage, or a fair-use rationale signed by the human). *v1's automated yt-dlp keyword harvesting is removed.* YouTube's Terms of Service bar downloading and automated access, broadcasters register footage with Content ID, and "reused content" is not monetisable. Archive.org gives no rights guarantee, so judge each item per jurisdiction. Screen capture of others' content follows the same rule.

### 03d — Probe & conform
`ffprobe` every asset into its ledger `inventory` (container, codecs, exact rate, VFR flag, duration, size, rotation, colour transfer, alpha, audio). Then apply the rules:

| Condition | Action |
|---|---|
| VFR (screen captures, phone/web clips) | Transcode to CFR at the timeline rate |
| WebM or Opus | Re-wrap/transcode to MOV/MP4 with PCM/AAC (Resolve lists no WebM container; Opus only in MOV/MP4) |
| Any audio | 48 kHz / 24-bit PCM WAV |
| HDR (PQ/HLG) | Tone-map to Rec.709, or flag and set Resolve colour management |
| Rate ≠ timeline | Prefer sources at the timeline rate or an exact multiple; else set a per-clip conversion method (nearest / frame blend / optical flow) |
| AI clips at 16 fps (Wan-class) | Frame-interpolate + upscale, or restrict to stylised slots |
| Non-16:9 / vertical | `fit: fill` or `crop` (maps to Resolve `Scaling`), or reject |
| Long-GOP playback poor | Optional DNxHR/ProRes mezzanine |

**Proxies:** none when source ≤ timeline resolution (1080p stock on a 1080p timeline). For 4K sources, use Resolve's own proxies (built in, or the Blackmagic Proxy Generator watch folder, which links them automatically), or external proxies matching name, timecode and rate, written as **.mov** and linked with `LinkProxyMedia` in 06. **The manifest only ever references full-resolution media.**

### 03e — Edit assembly → `cut_list.json`
- `source_in` = the best-scoring preview frame minus lead, not 0.
- **Fit rule:** require `source_duration ≥ slot + 2 × handle` (handle ≥ 1 s). Otherwise:
  1. take the next candidate;
  2. split the slot;
  3. **retime only if source fps ≥ 2× timeline fps** (slowing 24/25 fps footage judders).
- **Transitions** only between adjacent clips, with `alignment` start/center/end checked against handles. B-roll entering over the base layer gets a short **fade**, not a "transition".
- **Stills** get Ken Burns `motion` (start/end rects, eased), built natively in the editor (FilmCraft Motion keyframes; Resolve Dynamic Zoom or Fusion comp) per [[06_NLE_Adapters#Capability matrix]]. The untouched still stays the media; nothing is baked.
- **Coverage invariant:** V1 base layer covers `[0, end of outro]` with zero gaps. V2/V3 cover narration except intentional base-layer moments. No still run holds longer than its preset's hard cap (ADR-022); an unfillable long beat ends in a narration plate, never a repeat or a black slot.

## LLM vs deterministic code
- **LLM:** slot segmentation proposals, choosing between ranked candidates **by id**, generative prompts.
- **Code:** search, rate limiting, ranking scores, dedupe, people/brand rules, frames, fit, conform, coverage.

## Human gate — G3
The contact sheet per slot shows: chosen asset and alternates, score, licence, source and cost. The page also lists the generative slots with their price, and the total estimate. The human can pin, reject or re-query any slot (`overrides.yaml`). **No paid download or generation runs before G3.**

## Failure modes & fallbacks
This is loop **L2**. Every slot has an ordered fallback chain, recorded in the run report:
> re-query with broadened intent → next candidate → `ai_video` (only if approved at G3 and under cap) → `stock_photo` + Ken Burns → text/data card from `on_screen_text` → **visible "UNFILLED" slate + red marker**. The base layer underneath means a slot is never black.

## Cost & time
- Stock: $0, limited by quota. Pexels: 200 requests/h and 20k/month by default; ask Pexels for higher limits.
- Generative: see [[Vcut_End_to_End_Pipeline_Architecture#8. Budget & quotas (per video)]].
- Local generative video does **not** fit this workstation: Wan 2.2 TI2V-5B needs ≥24 GB VRAM, about 9 minutes per 5 s at 720p.

## Tools
Pexels API · Pixabay API (video endpoint; any review UI that shows its results must say they come from Pixabay) · Wikimedia Commons API · CLIP/SigLIP-class embeddings + a vision LLM for QC · FFmpeg/ffprobe · cloud generative video on a commercial tier. No graphics renderer: titles and effects are native in the editor. Details: [[Vcut_Tool_Allowlist#Visuals]].

## Acceptance tests
- 0 uncovered frames on V1; 100% of V2 slots filled or explicitly marked.
- No provider asset id used twice in a video; near-duplicate similarity below threshold.
- Every placed asset has a ledger entry with `commercial_use_ok: true`, and archival assets have a `rights_decision`.
- Every clip has ≥1 s of handle on each side where its source allows.
