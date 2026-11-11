# On-Screen Text & Graphics Catalog (documentary-default)

Revision 2026-11-09. Every on-screen text family the pipeline can produce, when to use it, and its build status.
Tested on video 19 (*Child Stars Who Quit Hollywood*, `Quit_Hollywood_VoiceOver_06.md`) in FilmCraft:
`Videos-Scripts/19_Child_Stars_Who_Quit_Hollywood_And_Never_Came_Back/07_Video_Edit/graphics_test/`.

## 1. Type system: one voice per job (v3.2, 2026-11-07)
| Voice | Font (OFL, `presets/documentary-default/fonts/`) | Used for |
|---|---|---|
| Display | DM Serif Display | names, titles, then/now names, mastheads |
| Editorial | Spectral SemiBold / Medium / Medium Italic | quotes, article body, roles, context lines |
| Data | Barlow Condensed SemiBold / ExtraBold (tracked caps) | labels, tags, counters, years, keyword pops |
| Evidence | Courier Prime Bold | place/date stamps |

Install once per machine: `powershell -File presets/documentary-default/install_fonts.ps1`.

Palette: ivory `#F3EBDD`, gold `#FFE8B8`, gold accent `#D4AF37`, charcoal `#0F1218`, signal red `#C9473D`, slate `#9AA0A8`.
Floor: no text under 45 px. Safe area x 160..1760, y 100..980. Motion: in 17 f easeOutCubic, out 12 f easeInCubic.

## 2. Built families
| # | Family | Engine | What it is | Use it when | Video 19 test |
|---|---|---|---|---|---|
| 1 | `lower-third` | EffectCraft v1 | Glass name plate + gold bar | First on-screen appearance of a person | Peter Ostrum, Jeff Cohen, Danny Lloyd |
| 2 | `chapter-card` | EffectCraft v1 | Centered act card | Act/story breaks | PART 02 · A FACE IN THE CROWD |
| 3 | `keyword-pop` | EffectCraft v1 | One word, pop scale | Single-word peak line | "NO." |
| 4 | `quote-pullout` | EffectCraft v1 | Static glass quote, up to 6 lines | Long quotes (> 25 words) | Jeff Cohen "four fat kids", Peter Ostrum AVMA quote |
| 5 | `reconstruction-tag` | EffectCraft v2 | Corner tally bug | Every dramatized passage | Hook cold open |
| 6 | `location-stamp` | EffectCraft v2 | Typewriter place + date | New place / time jump | Munich, Cleveland, Lowville |
| 7 | `stat-counter` | EffectCraft v2 | Count-up number + label | A number is the beat; year jumps | 5,000 boys · $4,000,000 · 1985→2023 · 35+ years |
| 8 | `timeline-strip` | EffectCraft v2 | 2–5 event band | Life-arc recaps | Jeff 1985/2002/2023 · Peter 1970/71/84/35+ |
| 9 | `then-now` | EffectCraft v2 | Role struck through → real life | "Where are they now" payoff | Chunk → Entertainment Lawyer, etc. |
| 10 | `source-tag` | EffectCraft v2 | Truth-tier chip + source | Any quoted/reported claim | REPORTED · The Hollywood Reporter; QUOTED · The Guardian |
| 11 | `credit-line` | EffectCraft v2 | End-credit pastiche | A real credit is the punchline | Doctor Sleep: Spectator, Danny Lloyd |
| 12 | `story-tracker` | EffectCraft v2 | NN/NN chip row, sliding underline | Story hand-offs | JEFF → DANNY → PETER |
| 13 | `kinetic-quote` | EffectCraft v2 | Word-by-word quote, emphasis in gold | Short spoken quotes (≤ 25 words) | "Acting gave me up." · "kind of boring." · "really enjoyed" |
| 14a | `person-pin` | EffectCraft v3 | Ring + leader + name plate on 1-3 people in one frame | Naming people inside a shot | Peter Ostrum |
| 14b | `people-panel` | EffectCraft v3 | 1-3 cropped portraits with names/roles | Introducing/comparing 2-3 people | Kubrick + Flanagan; Wilder + Donner + Kubrick |
| 14c | `group-legend` | EffectCraft v3 | "In this photo" names band | Group photos without documented order | 2011 Wonka child-cast reunion (alphabetical) |
| 14d | `article-highlight` | EffectCraft v3 | Paper clipping, marker sweep on the exact quote | Showing a source text | Peter Ostrum to the AVMA |
| 14e | `photo-annotation` | EffectCraft v3 | Ellipse draw-on + label | Pointing at a detail in a still | "First run" on the 1971 Allentown ad |
| 14 | `render_map` | Pillow still | Natural Earth route / locator map | Geography is the point | Cleveland → Munich |
| 15 | `render_article` | Pillow still | Clipping with marker highlight | Showing a source text | AVMA quote (illustrative layout) |
| 16 | `render_card` | Pillow still | Stamp / date strip / big number | Static emphasis | DECLINED stamp |
| 17 | `render_callout` | Pillow still | Static name callout | Fallback when EffectCraft is down | Ke Huy Quan |
| 18 | `line-third` | EffectCraft v2 | Bottom third: bold blue name caps over a white rule, wide-tracked sub below, per-glyph cascade reveal (heading left→right, sub right→left) with a white caret block riding the front; exit mirrors the reveal, rule retracts | Person/subject ident when we want the Mixkit 311 beat instead of the glass plate (heading #4993EA kept faithful; swap to gold in `layout.line_third` for house palette) | Gemma Lauren · Dr. Amara Okafor over footage (FilmCraft pass, 2026-11-09) |
| 19 | `bold-third` | EffectCraft v2 | Stamped bold heading with animated clearance line sweep + fast snap exit (Mixkit 312 adaptation) | Quick expert cameos, punchy talking-head name tags | Gemma Lauren (FilmCraft testbed pass, 2026-11-10) |
| 20 | `banner-third` | EffectCraft v2 | Heavyweight bordered dark banner plate with drawing gold accent border lines, headline + wide-tracked sub (Mixkit 305 adaptation) | Investigative/documentary formal subject idents | Dr. Amara Okafor (FilmCraft testbed pass, 2026-11-10) |
| 21 | `center-title` | EffectCraft v2 | Centered chapter/act card: wide-tracked kicker with drawing underline, bold title with settling overshoot, subhead (Mixkit 196 adaptation) | Chapter breaks, act intros, historical cards | Chapter Two: The City That Burned (FilmCraft testbed pass, 2026-11-10) |
| 22 | `drop-title` | EffectCraft v2 | Upper-third step/section stamp: dropping overshoot heading, popping accent rule + tag label (Mixkit 240 adaptation) | Procedural steps, section milestones, tutorial stamps | Step 3: Adjacency Pass (FilmCraft testbed pass, 2026-11-10) |


One command renders any EffectCraft family: `presets/documentary-default/render_family.py --family <name> --values v.json --out x.mov` (`--list` shows all).
One command tests a whole plan in FilmCraft: `tools/graphics_testbed.py --plan graphics_test_plan.json [--export]` → renders, `.fcproj` (V1 footage, V3 graphics, slot markers, bins), FilmCraft-rendered frames, `contact_sheet.png`, `preview.mp4`.

## 3. Density rules (per 10 minutes of runtime)
- People: 1 person = lower-third (or person-pin when pointing matters); 2-3 people = people-panel or person-pin; group without documented order = group-legend. Never assign a name to a face from a guess.
- Persistent identity: 1 lower-third per new person; 1 then-now per subject; 1 story-tracker per hand-off.
- Emphasis: max 3 kinetic quotes, 3 stat counters, 2 keyword pops. Never two full-frame scrim families back-to-back.
- Credibility: a source-tag on every quoted outlet; a reconstruction-tag on every dramatization.
- Never stack two families in the same screen corner at once (lower-third bottom-left, source-tag bottom-right, story-tracker top-right, reconstruction-tag top-left).

## 4. Known defects (fix next)
| Item | Defect | Fix |
|---|---|---|
| `render_map` | Title clipped at the top edge; city labels and footer far below the 45 px floor | Port to EffectCraft v2 (`map-route` family) with draw-on route |
| `render_card --type stamp` | Stamp renders tiny and cropped at the top-right edge (S26 "DECLINED" unreadable) | Rebuild as v2 `stamp` family, centered, 45 px+ |
| `render_article` / `render_card` / `render_callout` | Static Pillow, no motion, own styling | Rebuild as v2 families or retire `render_callout` (lower-third covers it) |
| `03_media/conformed` stills | Portrait images are pillarboxed with a smeared blur fill (visible behind S02, S10, S11, S28, S30) | Replace blur-fill with a Ken Burns crop or a darkened, desaturated blur at ≤ 35% brightness |
| `kinetic-quote` sync | Uses 150 WPM estimate until real VO exists | Feed `Word_Times` from `words.json` (transcribe_groq) |

## 5. Backlog: families worth adding (priority order)
1. **Burned-in captions / word-highlight subtitles**: required for Shorts cut-downs and silent autoplay; drive from `words.json`.
3. **Polaroid / photo-stack card**: archival photos dropped as framed prints with captions and date; matches the 1970 Polaroid beat.
4. **Split comparison**: two images side by side with a wipe and labels (1971 vs today).
5. **Screenshot highlight**: marker sweep over a REAL article screenshot (boxes from the plan); complements the typeset `article-highlight`.
6. **Map route (v2)**: animated route draw with legible labels; replaces Pillow `render_map`.
7. **Interview frame (picture-in-picture)**: framed archival interview clip with name strip and source tag while narration continues.
8. **Social-post card**: only with a real, archived post (Mike Flanagan's outreach to Danny Lloyd). Never synthesize a post.
9. **End screen / subscribe**: YouTube end-screen safe layout (last 20 s), house style.
