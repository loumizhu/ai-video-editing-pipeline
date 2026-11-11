# AI Video Editing Pipeline

A unified, modular, multi-agent AI video editing pipeline tailored for documentary, historical narrative, and faceless YouTube productions.

---

## 1. Quickstart for Collaborators & Friends

This repository contains deterministic tools, templates, house style presets, and agent production stage workflows for end-to-end documentary video creation.

### Prerequisites

1. **Python 3.10+**: Ensure Python is installed and available on your system path.
2. **FFmpeg & FFprobe**: Required for audio/video mastering, confections, and waveform cuts.
   - *Windows*: `winget install Gyan.FFmpeg` (or download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/))
   - *macOS*: `brew install ffmpeg`
   - *Linux*: `sudo apt-get install ffmpeg`
3. *(Optional)* **Groq API Key**: For ultra-fast `whisper-large-v3` word-level ASR transcription (`transcribe_groq.py`).
4. *(Optional)* **NLE Editor**:
   - **FilmCraft CLI / App** (default native pipeline target)
   - **DaVinci Resolve Studio 19/20** (via Python scripting API)

### Installation

Clone the repository and install Python dependencies:

```bash
# Clone the repository
git clone https://github.com/loumizhu/ai-video-editing-pipeline.git
cd ai-video-editing-pipeline

# Install required dependencies
pip install -r requirements.txt

# (Optional) Set up your environment variables
cp .env.example .env
```

### Preflight Setup Verification

Run the built-in diagnostic inspector to verify all system dependencies, tools, and API keys:

```bash
python video_pipeline/tools/check_setup.py
```

### Run Self-Tests

Verify color maths, pacing logic, cut boundaries, flash hazards, and dead-air detection:

```bash
python -m unittest discover -s video_pipeline/tools/tests
```

---

## 2. Directory Structure

```text
ai-video-editing-pipeline/
├── README.md                     # Master architecture, policies & quickstart
├── requirements.txt              # Pinned Python package dependencies
├── .env.example                  # Environment configuration template
├── .agents/                      # Multi-agent skill definitions (video-editor, etc.)
├── video_pipeline/               # End-to-end production pipeline specifications
│   ├── 00_ORCHESTRATOR.md        # Pipeline orchestrator, multi-model routing & gates
│   ├── EDITING_TOOLKIT.md        # Tool contracts, FFmpeg, FilmCraft & DaVinci commands
│   ├── PACING_AND_ENRICHMENT.md  # Still-hold caps, enrichment ladder, beat map, presets
│   ├── COLOR_SCRIPT.md           # Story-driven color phases, looks & skin protection
│   ├── DERIVATIVES.md            # Alternate cuts, Shorts/Reels, auto-chapters, thumbnails
│   ├── LESSONS.md                # Empirical operational learnings & edge cases
│   ├── TOOLS.md                  # CLI tool interfaces and parameters
│   ├── gates/                    # Human approval gates (G1: Brief to G4: Final Master)
│   ├── stages/                   # 10 modular production stages (01_scout to 10_qa_delivery)
│   ├── templates/                # Standard project templates and data schemas
│   ├── presets/                  # House style presets (documentary-default & shorts-vertical)
│   └── tools/                    # Deterministic keeper scripts for cuts, audio, and QA
├── vcut_architecture/           # Low-level Vcut data contracts & NLE adapters
└── sops/                        # Visual direction, audio priority & editing SOPs
```

---

## 3. Core Production Stages (10-Stage Pipeline)

| Stage | Name | Key Deliverables & Objective | Primary Model / Worker |
| :--- | :--- | :--- | :--- |
| **01** | `01_scout.md` | Competitor outliers, hook engines, audience angle | Antigravity / Claude Opus |
| **02** | `02_dna.md` | Reverse-engineered packaging, audience comments | Antigravity |
| **03** | `03_hook_outline.md` | Single held-back mystery hook, 3-act narrative spine | Claude Opus |
| **04** | `04_script.md` | 15 min - 3 h production script, scene sensory grounding | Claude Opus |
| **05** | `05_voiceover.md` | Voicebox TTS / studio VO WAV, word-level timestamps | Voicebox / Antigravity |
| **06** | `06_shot_plan.md` | Beat map (06a), frame-accurate shot list (visuals, duration, motion, enrichment, rationale); **no still past its hold cap** | Antigravity |
| **07** | `07_assets.md` | Multi-engine search, archival acquisition, conform to 1080p30, asset audit | Antigravity / `media_search.py` |
| **07b**| `07b_graphics_build.md` | Kinetic typography, chapter cards, microfilm scans | FilmCraft / Motion Graphics |
| **08** | `08_assembly.md` | NLE timeline build (7 bins, 4V/4A tracks), 0-drift cuts | FilmCraft / DaVinci Resolve |
| **09** | `09_packaging.md` | 5 title clusters, 1080p Smart Object thumbnails | PhotoCraft / Claude Sonnet Audit |
| **10** | `10_qa_delivery.md` | LUFS mastering (-14 LUFS), 5 QA scripts (incl. still-hold), export, style-memory update | FFmpeg / Claude Sonnet QA |

---

## 4. Pacing Rule in One Line

A single still image never stays on screen longer than **6.0 s** (documentary standard; 4.5 s without enrichment events; slow preset 8.0 s absolute ceiling). Fix a long hold by cutting to a distinct shot or a full-frame plate, then by enrichment tied to the spoken words; never by repeating a picture. Details and the ten-tip verdict: [video_pipeline/PACING_AND_ENRICHMENT.md](video_pipeline/PACING_AND_ENRICHMENT.md).

---

## 5. Asset Research & YouTube Copyright Protocol

YouTube operates aggressive automated ContentID matching (fingerprinting audio and video against commercial studios and distributors). To ensure zero claims, strikes, or demonetization, the pipeline mandates strict risk categorization:

### Risk Tiers
1. **Tier 1 (Safe / 0 Risk - Primary Visual Foundation)**:
   - **Archival Stills & High-Res Press Photos**: Promotional studio stills, behind-the-scenes set photos, Library of Congress, Wikimedia Commons, Bain collection. Images do NOT trigger video/audio ContentID fingerprinting.
   - **Public Domain & Government Archives**: Pre-1978 newsreels, National Archives (NARA), NASA, Prelinger vintage films from Internet Archive.
   - **Royalty-Free Commercial B-Roll**: Pexels, Pixabay (CC0 / commercial license).
   - **Primary Document Callouts**: Sharp microfilm scans and newspaper archives rendered via `render_article.py`.
2. **Tier 2 (Low Risk / Fair Use - Editorial & Transformative)**:
   - **Archival Broadcast Interviews & News Clips**: Contemporary TV appearances, talk shows, news coverage.
   - **Mandatory Transformative Rule**: Mute or strip original background soundtrack/score; keep video clips short (under 4–7 seconds per cut); overlay custom voiceover and ducked score.
3. **Tier 3 (High Risk - Strictly Prohibited)**:
   - Direct raw rips of studio feature film footage with original sync audio/dialogue/score.
   - Uncut commercial music tracks.

---

## 6. Multi-Agent Orchestration Standard

In accordance with `vcut_architecture/AGENTS.md`:
- **Executor / Workhorse**: **Antigravity** (handling coding, media search, downloading, conform, and asset registry generation).
- **Strict Reviewer**: **Claude Sonnet** conducting strict quality, licensing, and compliance audits with a maximum of 4 iteration passes.
- **Planner / Arbitrator**: **Claude Opus** for high-level creative direction and narrative arbitration.
