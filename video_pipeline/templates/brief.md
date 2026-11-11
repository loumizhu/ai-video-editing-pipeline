# Kick-Off Project Brief Template

Source: Adapted from Video 010 (`USER_BRIEFING_CHECKLIST.md`).
The orchestrator reads this brief at Stage 01. If any owner field is blank, the orchestrator asks the owner ONCE upfront and never interrupts mid-run.

---

## 1. What You Decide (User Upfront Input)

Fill these 7 core decisions before triggering Stage 01:

1. **Subject & Life Scope:**
   - **Full Name:** [e.g. Sir Patrick Stewart / Walt Disney]
   - **Life Dates / Active Era:** [e.g. 1940–2026 / 1923–1966]
   - **Tone / Orientation:** [e.g. Reverent tribute / Cinematic retrospective / Investigative corporate profile]
   - **Length Profile:** [`documentary_long` (Default: 15 min–3 h, ~150 words/min; 45–120 min suits TV/older audiences) | `tribute_short` (Opt-in: 4:30–5:15, 650–800 words)]

2. **The Hook Engine (0:00–0:60):**
   - **Opening Core Question / Mystery:** [e.g. "Without this one man, Star Trek would have died in 1987."]
   - **Cold Open Anchor:** [Lead voice, quote, or specific primary document; ban corpse cold opens]

3. **The Held-Back Revelation (85–95% Mark):**
   - **Core Hidden Truth:** [The unsung mentor, hidden contract, or decisive revelation held back until 85–95% runtime]

4. **Must-Have Characters & Key Roles:**
   - **Key Co-Stars / Figures:** [e.g. Hugh Jackman, Ian McKellen, Gene Roddenberry]

4b. **Pacing & Style (optional; defaults apply):**
   - **Pacing Preset:** [`documentary_standard` (default) | `slow_reflective` | `tense_fast`; the hook chapter defaults to `tense_fast`; see `PACING_AND_ENRICHMENT.md` section 5]
   - **Colour Script (Revision 2026-11-09; `COLOR_SCRIPT.md`):** intensity [`subtle` (default) | `moderate` | `bold`] · era [`faithful_archival` (default) | `light_tone_only` | `unified_stylized`] · arc [`gradual` (default) | `sharp`] · B&W [`neutral` (default) | `warm_toned` | `cool_toned` | `per_phase`] · motifs [on (default) | off] · output [video + strip + phase cards (default) | video only]
   - **Style Memory:** loaded automatically from `Videos-Scripts/_style_memory/style_memory.md` (taste rules from earlier videos).

5. **Score & Audio Vibe:**
   - **Music Direction:** [e.g. Solo acoustic piano in 3/4 time, gentle orchestral swell, melancholic yet uplifting]
   - **Voice Profile:** [Default: "Jessica from Ihateediting" (Signature) | "Emma (Storyteller)" | "Tom (Documentary)"]
   - **Voice Delivery Line (`--instruct`):** ["warm, calm, engaging storytelling tone"]

6. **Thumbnail Direction:**
   - **Focal Subject & Angle:** [e.g. Subject alone with mystery book vs. Subject with key co-star; focal subject ≥40% canvas]
   - **Text Overlay (≤4 words):** [e.g. "HIS SECRET TEACHER" — must not repeat words from title]

7. **Strict Boundaries (Exclusions & Naming Reverence):**
   - **Formal Name Rule:** [e.g. Always "Cecil" or "Cecil Dormand", never casual nickname "Cec"]
   - **Exclusions:** [e.g. No tabloid rumors, no medical speculation, no unverified fan theories]

---

## 2. What Agents Discover & Verify Automatically (Do Not Research Manually)

- Competitor outlier spikes, view velocity, and target RPM calculations (Stage 01).
- Live breaking fact checks and official memorial statements (`01_research/FACT_BASELINE.md`).
- Primary broadcast quotes and timestamped proof (`01_research/QUOTE_PROOF.md`).
- Audience comments and friction points from top 5 competitor videos (`02_reference_videos/`).
- Whisper word-level timestamps and timing alignment (`06_script_edit_plan/timing.json`).
- EBU R128 audio loudness normalization (-16 LUFS, -24 dB / -28 dB music ducking, ceiling <-1.5 dBTP).
- 1080p conformed visuals, soft-feathered typography wipes, and 120px thumbnail readability tests.
- Turnkey YouTube metadata, chapter timestamps, and upload packaging (`09_upload/`).

---

## 3. Quick Copy-Paste Brief Form

```markdown
- **Subject:** [Full Name] ([Years])
- **Tone:** [Reverent / Retrospective / Investigative]
- **Length Profile:** [documentary_long | tribute_short]
- **Target Runtime:** [15 min–3 h (default) | ~4:30–5:15 (tribute)]
- **Hook Idea:** [Core opening question or primary quote]
- **Held-Back Revelation:** [The hidden turning point or unsung person]
- **Must-Have Co-Stars / Figures:** [Figure A, Figure B]
- **Pacing Preset:** [documentary_standard | slow_reflective | tense_fast]
- **Music Style:** [Style, tempo, instrumentation]
- **Voice Profile:** ["Jessica from Ihateediting"]
- **Thumbnail Preferences:** [Subject + Mystery element; text overlay ≤4 words]
- **Strict Exclusions:** [Formal name rules, banned topics]
```

<span style="color: purple;">[AI Agent]</span>
