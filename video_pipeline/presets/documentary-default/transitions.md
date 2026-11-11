# Transitions Vocabulary & NLE Mapping Guide

> **Decision skill:** *when* to use a transition, *which* one, and when NOT to is governed by [video_pipeline/skills/transitions/SKILL.md](../../skills/transitions/SKILL.md) (Stage 06/08/10 agents). This file stays the single source for frame counts, effect IDs, and caps.

## 1. Editorial Rule of Transitions (EDITING_TOOLKIT §2.1 & §4)
> **The Hard Cut Rule:** 85%+ of all cuts in a Publora documentary are **HARD CUTS (0 frames)**.  
> Transitions are never cosmetic eye-candy; every transition must be **narratively motivated** by a change in time, place, perspective, or emotional gravity.

### Anti-Overuse Rule & Density Cap
- **Per-Minute Cap:** Maximum **1 dynamic transition per 60 seconds** of timeline runtime.
- **Per-Video Cap:** Maximum **<=10 dynamic transitions per 10 minutes** of documentary runtime.
- **Default Fallback:** If a transition's narrative motivation is ambiguous, execute a hard cut paired with an audio J-cut (audio leads by 8–18 frames).

---

## 2. Reconciled Transition Vocabulary Mapping Matrix

*Reconciliation Note:* `EDITING_TOOLKIT.md` specifies baseline durations at 30 fps (e.g. 30 frames = 1.00s dip, 15 frames = 0.50s dissolve). In this documentary preset (`fps = 23.976`), frame counts are reconciled to match exact second durations:

| Narrative Beat | Narrative Motivation | FilmCraft ID | DaVinci Resolve Equivalent | Frames @ 23.976 fps | Frames @ 30.0 fps | Duration (s) | Paired SFX Role | Per-Minute Cap |
|---|---|---|---|:---:|:---:|:---:|---|:---:|
| **Standard Beat Cut** | Normal dialogue flow, B-roll progression | *None (Hard Cut)* | *None (Hard Cut)* | **0** | **0** | 0.000s | None | Unlimited |
| **Scene Shift / Time Passage** | Temporal progression, changing interview locations | `cross_dissolve` | `Cross Dissolve` | **12** | **15** | 0.500s | Ambient crossfade / Room tone | 1 / 60s |
| **Act Change / Chapter Shift** | Deep thematic shift, act finale, major milestone | `dip_to_black_legacy` | `Dip to Color Dissolve` (Black) | **24** | **30** | 1.001s | Sub boom (`sfx_sub_boom.wav`) | 1 / 300s (Act only) |
| **Perspective Shift / Reveal** | Revealing new archival evidence or territorial view | `wipe` | `Wipe` (Feathered 30) | **12** | **15** | 0.500s | Soft whoosh (`sfx_whoosh_soft.wav`) | 1 / 120s |
| **Urgent Jump / Shift** | Fast temporal leap, montage pacing shift | `whip_legacy` | `Whip` | **10** | **12** | 0.417s | Quick whoosh (`sfx_whoosh_fast.wav`) | 1 / 180s |
| **Archival Memory / Flashback** | Transitioning into vintage black & white or retro footage | `film_dissolve_legacy` | `Film Dissolve` | **16** | **20** | 0.667s | Subtle film reel / shutter | 1 / 180s |
| **Document / Photo Focus** | Transitioning from wide B-roll to archival still plate | `non_additive_dissolve` | `Non-Additive Dissolve` | **12** | **15** | 0.500s | Paper slide (`sfx_paper_slide.wav`) | 1 / 120s |
| **Audio-Led Scene Bridge** | Audio leads before visual cut | *J-Cut / L-Cut* | *J-Cut / L-Cut* | **12** | **15** | 0.500s | Dialogue / score lead | 2 / 60s |

---

## 2b. Not built: light leak and film burn
`EDITING_TOOLKIT.md` (lines 19, 42, 43, 147: `ovl.light_leak_sweep`, `tr.film_burn`) and earlier drafts of this file listed a light-leak overlay and a film-burn accent on V4. **These assets do not exist in this preset**: no overlay file was rendered, no builder exists, and no licensed footage was sourced. They are removed from the vocabulary above. Add them back only together with a rendered or free-licence overlay file, its licence and a timing row here.

## 2c. Frame counts used across the preset docs (single source: this table)
- Scene shift / perspective / document dissolve: **12 frames** (0.500 s @ 23.976 fps; 15 frames at 30 fps).
- Act change dip to black: **24 frames** (1.001 s; 30 frames at 30 fps).
- README and graphic-family docs refer to this table; there is no 15-frame dissolve at 23.976 fps.

## 3. Automation Recipes

### FilmCraft CLI Execution Syntax
Apply a transition to an edit point via `sequence.applyVideoTransition`:
```powershell
# Cross Dissolve on clip out-edge (0.50s = 12 frames @ 23.976 fps)
filmcraft-cli --project <project.fcproj> --save exec sequence.applyVideoTransition '{"clip": <id>, "effect": "cross_dissolve", "frames": 12, "edge": "out"}'

# Dip to Black at chapter act boundary (1.00s = 24 frames @ 23.976 fps)
filmcraft-cli --project <project.fcproj> --save exec sequence.applyVideoTransition '{"clip": <id>, "effect": "dip_to_black_legacy", "frames": 24, "edge": "in"}'

# Whip transition with parameter control
filmcraft-cli --project <project.fcproj> --save exec sequence.applyVideoTransition '{"clip": <id>, "effect": "whip_legacy", "frames": 10, "edge": "in", "params": {"direction": 0}}'
```

### DaVinci Resolve Studio Recipe (DOCUMENTED-NOT-TESTED)
*Note: In the DaVinci Resolve Studio Python scripting API, Edit timeline transitions cannot be created via `InsertFusionTitleIntoTimeline` (which inserts title generators, not transitions). The verified NLE routes for scripted transition assembly in Resolve are:*

1. **Pre-Rendered Overlay Route (Recommended Dual-NLE Pipeline):**
   Transitions that have no native Resolve equivalent (whips, feathered wipes) can be exported as ProRes 4444 alpha clips (`.mov`) and placed directly on Track V4 (`overlay`). This route is 100% deterministic across both FilmCraft and Resolve.
2. **Timeline XML / FCPXML Ingest:**
   Transitions configured in EDL/XML conform scripts import directly into Resolve's timeline with native transitions (`Cross Dissolve`, `Dip to Color Dissolve`).
3. **UI / Shortcut Route (Manual Finishing):**
   Selecting an edit point in the Edit timeline and executing the standard shortcut (`Cmd+T` / `Ctrl+T`) applies the user's default Video Transition (`Cross Dissolve`).
