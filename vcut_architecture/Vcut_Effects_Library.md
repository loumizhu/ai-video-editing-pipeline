# Vcut — Documentary Effects Library

## Links
- **Hub:** [[Vcut_End_to_End_Pipeline_Architecture]] · **Decisions:** [[Vcut_Decision_Log#ADR-020 — Documentary effects library]], [[Vcut_Decision_Log#ADR-021 — One editor: everything native and editable]] · **Schema:** [[Vcut_Data_Contracts#3.11 Effect presets]]
- **Used by:** [[03_Shot_Planning_and_Visuals]] (03b picks presets per slot) · [[04_Music_SFX_and_Ducking]] (04b places the paired SFX) · [[05_Timeline_Manifest_and_QA]] (density checks) · [[06_NLE_Adapters]] (builds each preset natively in the chosen editor)
- *Revised 2026-10-27: every preset is native to the editor; no separate effects renderer.*

---

## Purpose
A faceless documentary channel lives on its visual grammar: stills that move, archival looks, light and
texture, and on-screen text that lands with a sound. This library is the **ready-to-use catalogue** of those
effects. Each entry is a **preset**: a named, parameterised effect with a paired sound and **one native
implementation per editor**. Vcut applies it automatically, and the owner changes it **in the editor alone**
(DaVinci Resolve by default, or FilmCraft): edit the text in the inspector, swap the transition, tweak the
grain, delete the overlay.

## How a preset reaches the timeline
Nothing is pre-rendered. 06 builds each preset from its implementation for the chosen editor
([[06_NLE_Adapters#How each Vcut object becomes a native editor object]]):

| Kind | DaVinci Resolve | FilmCraft | Edited in the editor by… |
|---|---|---|---|
| **Title template** (text, labels, cards) | Fusion Title template with published inputs (text, colour, accent) | Graphics template `.fcgt` with named controls (text, colour, slider, font, position) | Typing in the inspector; the template's animation stays intact |
| **Transition** | Dissolves through FCPXML import; other transitions on Studio ≥21.1 or by hand | Any of FilmCraft's 112 transitions (`sequence.applyVideoTransition`) | Changing or trimming the transition |
| **Effect stack on a clip** (looks, light leak, grain, vignette, push-in) | A grade from a `.drx` still (may include Resolve FX) or a LUT; push-in via Dynamic Zoom (FCPXML) or a Fusion comp *(to verify)* | Lumetri Color, Noise, Vignette, Light Leaks, Camera Shake…; Motion keyframes | Changing parameters or keyframes |
| **Overlay clip** (dust, scratches, paper, burns) | A library clip on V4 with `CompositeMode` (Screen, Add, Overlay, Multiply) | A library clip with `Opacity` blend mode | Moving, trimming, deleting, changing opacity |

The **template files are made once by hand** (owner or developer) in each editor and saved into the library; code
only fills in their values and timings. A preset that has **no implementation for the chosen editor is not
offered** for it. Pre-rendering is an M3 opt-in for effects no editor has natively (marked *M3 opt-in* below).

**Who picks a preset, in order:** the owner's `[effect: <preset id or name>]` cue in the script → the style rules of
the chosen look (setup form) → the AI `tagging` role, choosing **by preset id** for each beat → with AI `none`, style
rules only. Code then applies the density limits below, computes every frame, and places the paired SFX.

## Density and variety rules (defaults, tuned from G4 edit stats)
- **Text/label presets:** at most 4 per minute; never two within 3 s; never over a key line the owner marked.
- **Looks:** one look per chapter (consistent texture); accent overlays (light leak sweep, film burn) at most 1 per 45 s.
- **Transition effects** beyond cut/dissolve: at most 1 per 60 s, and only at section changes.
- **Rotation:** each preset family has 2–4 variants (colour, direction, timing); the same variant is not reused within 3 minutes. This also keeps videos from looking templated, which YouTube's "inauthentic content" rule penalises.
- **Paired SFX** follow the SFX budget and sync rules in [[04_Music_SFX_and_Ducking#SFX placement (one authority, a budget, real sync)]]; a preset's SFX can be muted per channel. The sync points come from the preset's declared **event offsets** (e.g. "text fully on at +8 frames", "one key per 2 frames per character"), because the template's animation timing is fixed.

---

## Catalogue
**Phase:** **M1** = starter set (20 presets, built first in both editors) · M2 · M3. **SFX** = the paired sound
(category from the SFX library below). **R** = DaVinci Resolve, **F** = FilmCraft. Effect and transition names in
the F column are from FilmCraft 0.13.0's own lists (checked 2026-10-27); R routes are from Resolve's scripting
README and are tested at M0a.

### 1. Looks (applied to a clip, a chapter or the whole video)
| Preset id | What it looks like | R | F | Best for | Phase |
|---|---|---|---|---|---|
| `look.clean` | Neutral Rec.709, light contrast | `.drx` grade (or none) | Lumetri Color, basic | Modern stock footage | **M1** |
| `look.archival` | Slightly desaturated, soft contrast, fine grain, light vignette | `.drx` grade | Lumetri (saturation, faded film) + Noise + Vignette | Mixing old and new material so it feels like one film | **M1** |
| `look.old_film` | Sepia or B&W, heavy grain, dust and scratches, flicker, vignette | `.drx` grade + dust overlay clip | Tint or Black & White + Noise + Vignette + dust overlay clip | Early 20th-century stories, flashbacks | **M1** |
| `look.vhs` | Chroma bleed, scan lines, noise, date stamp option | `.drx` grade + scan-line overlay | RGB Split + Noise + scan-line overlay | 1980s–90s era segments | M2 |
| `look.cold_investigative` | Teal-blue shadows, low saturation | `.drx` grade | Lumetri | Crime, tech, investigations | M2 |
| `look.warm_nostalgic` | Warm highlights, lifted blacks, soft bloom | `.drx` grade | Lumetri + Glow | Personal or human-interest chapters | M2 |
| `look.newsprint` | Halftone dots, paper colour, ink spread | — | — | Photos framed as press coverage | M3 opt-in |

### 2. Overlays & Texture Synthesis (Celluloid & Light)
| Preset id | What it does | R | F | SFX | Phase |
|---|---|---|---|---|---|
| `ovl.light_leak_sweep` | Warm light moving across the frame (the "light moving around" effect); warm/cool variants | Overlay clip, Screen | **Light Leaks** effect (colours, intensity, direction, speed) | soft whoosh (optional) | **M1** |
| `grain.clean_35mm` *(Profile A)* | Clean modern cinema (Fincher look): microscopic 35mm 50D grain (size 0.08, 2-4% opacity), tight midtone luma mask | Resolve OFX 35mm 50D node (sat 0, midtones 1.0) | FilmCraft native **Noise** (1.5, monochrome) or V4 plate (Overlay 15%) | — | **M1** |
| `grain.classic_35mm` *(Profile B)* | Classic Hollywood: balanced 35mm Portra/Eterna grain (size 0.20, 6-10% opacity, 0.1 softness), gentle midtones | Resolve OFX 35mm 400T node (sat 0, midtones 1.0) | FilmCraft native **Noise** (3.0, monochrome) or V4 plate (Overlay 30%) | — | **M1** |
| `grain.gritty_16mm` *(Profile C)* | Gritty documentarian: tactile 16mm 500T grain (size 0.40, 12-18% opacity, high contrast texture) | Resolve OFX 16mm 500T node (sat 0, midtones 1.0) | FilmCraft native **Noise** (5.0, monochrome) or V4 plate (Overlay 48%) | — | **M1** |
| `grain.vintage_8mm` *(Profile D)* | Vintage archive / memory fragment: chunky Super 8 grain (size 0.70, 20-30% opacity) + ±1px gate weave | Resolve OFX 8mm node + Camera Shake | FilmCraft native **Noise** (8.0, monochrome) or V4 plate (Overlay 65%) | projector loop | **M1** |
| `ovl.film_grain` *(Alias)* | Continuous grain default (maps to `grain.classic_35mm`, Overlay blend; Screen mode banned) | In `.drx` grade / OFX | **Noise** (amount, monochrome) or V4 plate (Overlay) | — | **M1** |
| `ovl.dust_scratches` | Specks, hairs, vertical scratches (placed on V3, Opacity blend) | Overlay clip, Multiply/Soft Light | Overlay clip, Opacity blend | projector loop (very low, optional) | **M1** |
| `ovl.vignette` | Static or slowly breathing dark edges | In the `.drx` grade | **Vignette** | — | **M1** |
| `ovl.film_burn` | Burn-out flash, usually at a section change | Overlay clip | Overlay clip | flame flare / impact | M2 |
| `ovl.projector_flicker` | Brightness flicker + soft gate light | Overlay clip | Lumetri exposure keyframes | projector loop | M2 |
| `ovl.paper_texture` | Paper or canvas grain over graphics | Overlay clip, Multiply | Overlay clip, Multiply | — | M2 |
| `ovl.lens_flare_sweep` | Anamorphic streak crossing the frame | Overlay clip | **Lens Flare**, keyframed position | shimmer | M2 |
| `ovl.haze_smoke` · `ovl.bokeh_drift` | Drifting haze; out-of-focus light spots | Overlay clip | Overlay clip | — | M3 |

### 3. Motion on photos and clips
| Preset id | What it does | R | F | SFX | Phase |
|---|---|---|---|---|---|
| `mot.push_in` / `mot.pull_out` | Slow Ken Burns zoom toward or away from a point of interest | Dynamic Zoom (FCPXML) or Fusion comp *(to verify)* | **Motion** scale/position keyframes (tested) | — | **M1** |
| `mot.pan` | Slow pan across a wide photo or document | as above | Motion position keyframes | — | **M1** |
| `mot.photo_drop` | Photo with a print border drops onto the frame, settles with a small bounce | Fusion comp on the photo clip | Motion keyframes + Stroke + Drop Shadow | paper slap | M2 |
| `mot.photo_stack` | Several photos shuffle on top of each other | Fusion comp | Motion keyframes on stacked clips | paper slides | M2 |
| `mot.focus_pull` | Starts blurred, pulls sharp onto the subject | Fusion comp | Gaussian Blur keyframes | — | M2 |
| `mot.handheld` | Subtle camera shake on a still to make it feel filmed | Fusion comp | **Camera Shake** | — | M2 |
| `mot.zoom_punch` | Quick zoom on a detail for emphasis | Fusion comp | Motion keyframes | impact / hit | M2 |
| `mot.magnifier` | A loupe circle enlarges a detail of a photo or document | Fusion comp | **Magnify** | glass ting | M3 |
| `mot.parallax_25d` | Photo split into depth layers moving at different speeds (needs a depth model) | — | — | soft whoosh | M3 opt-in |

### 4. Transitions
| Preset id | What it does | R | F | SFX | Phase |
|---|---|---|---|---|---|
| `tr.cross_dissolve` | Standard dissolve | FCPXML dissolve (API on Studio ≥21.1) | **Cross Dissolve** (tested) | — | **M1** |
| `tr.dip_black` | Fade through black (chapter ends) | FCPXML (to verify) | **Dip to Black** | low boom (optional) | **M1** |
| `tr.flash_white` | Camera-flash cut | White overlay clip | **Flash** / Dip to White | camera shutter | M2 |
| `tr.light_leak` | Cut hidden under a bright light leak | Overlay clip over the cut | **Light Leak** | whoosh | M2 |
| `tr.film_burn` | Cut hidden under a film burn | Overlay clip over the cut | Overlay clip over the cut | flame flare | M2 |
| `tr.whip_pan` | Fast motion-blur slide to the next shot | by hand / Studio ≥21.1 | **Whip** | hard whoosh | M2 |
| `tr.glitch` | Short digital break-up (tech topics, sparingly) | Overlay clip | **Glitch** | glitch | M3 |
| `tr.ink_wipe` | Ink or paint spreads to reveal the next shot | Overlay matte clip | Track Matte Key + matte clip | brush swish | M3 |

### 5. Text and labels (each with its sound)
Every row is a **title template**: a Fusion Title in Resolve and a `.fcgt` graphics template in FilmCraft, with the
animation built into the template (FilmCraft can also use its **Typewriter** and **Text Animator** transitions on
the title clip). The text fields are filled by Vcut and edited in the inspector.

| Preset id | What appears | Template fields | SFX | Phase |
|---|---|---|---|---|
| `txt.lower_third` | Name + role bar for a person or source | name, role | soft whoosh | **M1** |
| `txt.location_stamp` | "VIENNA, AUSTRIA" typed letter by letter, bottom left | place | typewriter keys + carriage return | **M1** |
| `txt.date_stamp` | "14 MARCH 2011" typed or ticked in | date | typewriter or clock tick | **M1** |
| `txt.chapter_title` | Full-screen chapter number + title | number, title | deep boom or riser into hit | **M1** |
| `txt.keyword_pop` | One key word or figure pops on screen beside the subject | word, side | pop / click | **M1** |
| `txt.quote_card` | A quotation with attribution over a dimmed background | quote, speaker, source | paper slide / soft whoosh | **M1** |
| `txt.big_number` | Number counts up to a value ("$4.2 billion"), claim-cited | value, unit, label | ticking + ding | M2 |
| `txt.underline_draw` | A line draws under a word on screen | word | pen scratch | M2 |
| `txt.stamp` | "CONFIRMED", "CLASSIFIED", "DENIED" stamped at an angle | word, colour | stamp thud | M2 |
| `txt.redaction_reveal` | Black bars slide off to reveal hidden words | text | marker / slide | M2 |
| `txt.list_build` | Bullet list builds line by line (recaps) | up to 5 lines | click per line | M2 |
| `txt.archival_subtitle` | Subtitles for speech in archival audio | — (caption track) | — | M2 |

### 6. Documents, articles and evidence
| Preset id | What it shows | How (both editors) | SFX | Rights | Phase |
|---|---|---|---|---|---|
| `doc.article_recreated` | Vcut **re-types** the headline and excerpt as a clean "article card" with outlet name and date; a highlighter sweeps over one sentence | Title template (headline, excerpt, outlet, date, highlight span) | paper slide + highlighter squeak | Lower risk: short quotation with attribution, no copy of the page design | **M1** |
| `doc.article_highlight` | **Screenshot of an article**: the page slides in, the camera pushes onto a sentence, a highlighter sweeps over it, the rest dims, source shown | Screenshot as an image clip + push-in (motion preset) + highlighter title template on top + source label | paper slide + highlighter squeak | Only pages already cited in `claims.json`; crop to the excerpt; source on screen; **rights decision required** — under autopilot it is placed with a red marker | M2 |
| `doc.document_pan` | Scan of a report or letter, slow pan + highlight of one line | Scan clip + `mot.pan` + highlighter template | paper flip + highlighter | Public-domain or owned documents; otherwise rights decision | M2 |
| `doc.post_card` | A social post re-created as a card (name, handle, date, text), not a screenshot | Title template | notification click | Short quote + attribution; no profile photo unless licensed | M2 |
| `doc.evidence_board` | Photos pinned on a board, red string drawn between them | Photo clips + board image + line templates | pin push + string twang | Per photo | M3 |

### 7. People and organisations
| Preset id | What it shows | How (both editors) | SFX | Rights | Phase |
|---|---|---|---|---|---|
| `ppl.person_card` | Card with photo, name, role, years; slides in beside the narration | Title template (name, role, years) + the **photo as its own clip** under it (R: static crop/position; F: Motion + Rounded Crop + Drop Shadow), so the photo can be swapped in the editor | soft whoosh | Photo from Wikimedia Commons (licence + credit in the ledger) or the owner's library; **silhouette placeholder** if none. Never an AI-generated face of a real person | **M1** |
| `ppl.cast_grid` | Several person cards in a grid ("the key players"), one highlighted at a time | Several photo clips + templates; highlight by opacity keyframes | click per card | Same as above | M2 |
| `ppl.relationship_web` | Cards connected by labelled lines (who funded whom) | Photo clips + line/label templates | line draw | Same as above | M3 |
| `org.org_card` | Organisation name, logo, founding year, one fact | Logo clip + title template | soft whoosh | Logos for identification only, never implying endorsement | M2 |

### 8. Data, time and place
| Preset id | What it shows | How | SFX | Phase |
|---|---|---|---|---|
| `data.bar_chart` / `data.line_chart` | Chart from claim-cited data, bars or line building in | Title template with value sliders (R: Fusion inputs; F: slider controls), filled from claim data | soft build | M2 |
| `data.percent_ring` | A ring fills to a percentage | Title template with a slider | tick + ding | M2 |
| `time.timeline_bar` | Horizontal timeline; events appear as the narration reaches them | Title template per event, placed at the narration's frames | click per event | M2 |
| `cmp.split_screen` | Two images side by side with labels (before/after, then/now) | Two clips with crop/position + label templates | soft whoosh | M2 |
| `map.location_pin` | Map zooms to a place, pin drops, label appears | Map still (Natural Earth, public domain) as a clip + push-in + pin/label template | pin drop | M3 |
| `map.route_draw` | A route or border draws across a map | — | pen / line draw | M3 opt-in |

---

## SFX library categories (for the paired sounds)
`libraries/sfx/<category>/`, every file with a ledger entry ([[04_Music_SFX_and_Ducking]]); built once from CC0 and owned packs.

| Category | Examples |
|---|---|
| `whoosh` | soft, hard, reverse, airy |
| `riser_hit` | risers 1–4 s, boom, deep hit, sub drop |
| `typewriter` | single key, word burst, carriage return, bell |
| `paper` | slide, flip, slap, crumple, page turn |
| `pen_marker` | highlighter squeak, pen scratch, underline |
| `camera` | shutter, flash pop, film advance |
| `click_pop` | UI click, pop, tick, ding, notification |
| `stamp_pin` | rubber stamp, pin push, string twang |
| `film` | projector loop, reel start, flame flare |
| `glitch` | digital glitch, static burst, tape stop |
| `clock` | tick, clock chime |
| `ambience` | room tone, city, wind (beds under quiet moments) |

## Library folder layout
```
libraries\effects\
├── catalog.yaml                     # index of all presets (generated from the preset folders)
├── looks\look.old_film\
│   ├── preset.yaml                  # id, fields, variants, paired SFX, event offsets, density class, editors
│   ├── preview.mp4                  # what it looks like (rendered once, in either editor)
│   ├── resolve\                     # look_old_film.drx · notes
│   └── filmcraft\                   # effects.jsonl (the effect-stack commands, values as {placeholders})
├── text\txt.location_stamp\
│   ├── preset.yaml · preview.mp4
│   ├── resolve\                     # vcut_location_stamp.setting (Fusion Title template)
│   └── filmcraft\                   # vcut_location_stamp.fcgt (graphics template)
├── overlays\  motion\  transitions\  documents\  people\  data\
└── overlay_media\                   # dust, scratches, paper, burns, light-leak clips (procedural or licensed),
                                     # each with a ledger entry
```
Resolve templates are also loaded into the Vcut template project's bins; FilmCraft templates are applied by path
(`graphics.template.apply`) or installed once (`graphics.template.install`).

## Acceptance tests
- Every M1 preset exists for **both** editors, has a preview clip, and builds in the M0a fixture with no baked clip.
- Changing the text of any M1 text/card preset is done in the editor's inspector and survives a save and reopen; no other program is opened.
- A 5-minute M1 video respects every density rule above, and no preset variant repeats within 3 minutes.
- Every placed text/label preset has its paired SFX within ±1 frame of the preset's declared event offset (unless the channel muted it).
- No `doc.article_highlight` or `ppl.person_card` photo is placed without a ledger entry; under autopilot, each one that needs a rights decision carries a red marker.
