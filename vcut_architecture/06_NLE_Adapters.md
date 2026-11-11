# Step 06: NLE Adapters (DaVinci Resolve · FilmCraft)

## Links
- **Hub:** [[Vcut_End_to_End_Pipeline_Architecture]] · **Decisions:** [[Vcut_Decision_Log#ADR-002 — NLE targets]], [[Vcut_Decision_Log#ADR-021 — One editor: everything native and editable]], [[Vcut_Decision_Log#ADR-004 — Carriers for effects the Resolve API cannot set]]
- **Previous:** [[05_Timeline_Manifest_and_QA]] (`vcut_timeline.json` with **no QA errors**) · **Runs in parallel with:** 05b preview render
- **Next:** [[07_Human_Review_and_Delivery]]
- *Renamed 2026-10-26 from "06 DaVinci Resolve Adapter". Revised 2026-10-27: native build in **one** editor, Resolve by default ([[Vcut_Plan_Review_2026-10-26#Round 3 (2026-10-27)]]).*

---

## Purpose
Turn `vcut_timeline.json` into a timeline **built natively inside the editor the owner chose** (DaVinci Resolve by
default, or FilmCraft). Every title, label, card, transition, look, overlay, keyframe and marker is an object of
that editor, so the whole video is edited in that one program ([[Vcut_Decision_Log#ADR-021 — One editor: everything native and editable]]).

As a backup, 06 also writes an **interchange package** (FCPXML + OTIO + media). It carries cuts, media and markers
to any editor, but not the native titles and effects.

Never touch a timeline a human has already edited.

## Inputs → Outputs
| In | Out |
|---|---|
| `timeline/vcut_timeline.json`, `qa/qa_report.json` (no errors), `assets/asset_registry.json`, `project.yaml` (`editor`), the chosen editor's preset implementations from `libraries/effects/` | `nle/<editor>/` (the native project or build script + `build_report.json`) · `nle/package/` (backup) · readable copy in `06_editor/` |

## How each Vcut object becomes a native editor object
The compiler (05) already resolved every effect to a preset id; 06 looks up that preset's implementation **for the
chosen editor** ([[Vcut_Effects_Library#How a preset reaches the timeline]]) and fills in the values. No video is
rendered for any of these.

| Vcut object | **DaVinci Resolve** (default) | **FilmCraft** |
|---|---|---|
| Media clip at exact frame/track, source in/out | `AppendToTimeline` with `clipInfo` (`recordFrame`, `trackIndex`, `mediaType`) | `timeline.place` (`track`, `time`/`frame`, `sourceIn`, `duration`) ✔ |
| Text, label, lower third, chapter title, quote/article/person card | **Fusion Title template** from the Vcut template set, inserted with `InsertFusionTitleIntoTimeline`; its published fields (text, colour) set through the clip's Fusion comp (`GetFusionCompByIndex`) | **Graphics template** (`.fcgt`) with named controls, placed by `graphics.template.apply` with `values` ✔; extra layers by `graphics.set` |
| Text animation (typed on, pop, slide) | Built into the Fusion title template | The template's own animation, or the **Typewriter** / **Text Animator** transitions on the title clip (to verify how they read) |
| Photo in a card (person card, article) | The photo as its own clip under the title; crop/position as static properties | The photo as its own clip; `Motion`, `Crop` / `Rounded Crop` effects |
| Transition | FCPXML import carries dissolves; scripted transitions only on Studio ≥21.1 | `sequence.applyVideoTransition` with any of its **112** transitions (Cross Dissolve, Dip to Black, Film Dissolve, Light Leak, Flash, Whip, Glitch, VHS Damage…) ✔ |
| Look (archival, old film, sepia) | **Grade from a `.drx` still** (`ApplyGradeFromDRX`) or `SetLUT`; the grade holds Resolve FX (grain, vignette) | **Lumetri Color** (`faded_film`, saturation, look LUT) + **Noise** (`amount`, monochrome) + **Vignette** effects ✔ |
| Film grain (organic celluloid synthesis) | **Resolve FX Film Grain node** (Tone Response midtone curve, 0% sat, profiles 50D/400T/16mm/8mm); or V4 clip with `CompositeMode: Overlay` (Screen banned) | **Noise** effect (`monochrome: true`), or Track V4 continuous grain plate with `Opacity.blend: Overlay` (never Screen) ✔ |
| Light leak, dust texture | Overlay clip on V4 with `CompositeMode` (Screen for leaks, Multiply/Soft Light for dust) | **Light Leaks** effect on the clip ✔, or overlay clip with **Opacity** `blend` |
| Ken Burns / push-in / pan | Transform keyframes are not in the API: carried by FCPXML import (Dynamic Zoom) or a Fusion comp on the clip (`ImportFusionComp`) *(to verify)*; else baked | **Motion** `scale`/`position` keyframes via `effects.setParam … keyframe: true` ✔ |
| Camera shake on a still | Fusion comp or Resolve FX in a grade | **Camera Shake** effect |
| Music ducking | **Fairlight Ducker** in the template project, keyed from the voice; else a baked ducked stem | Volume keyframes from Vcut's envelope, or `essentialSound.generateDucking` (to verify); else baked stem |
| Markers (review notes, chapters) | `Timeline.AddMarker(frameId, colour, name, note, duration, customData)` | `markers.add` (named colours: Rose, Mango, Green, Blue…) ✔ and `markers.addChapter` ✔ |
| Captions | Import the SRT into the timeline (to verify the call) | `captions.import` (SRT/VTT…) |

✔ = run successfully on this workstation on 2026-10-27 (FilmCraft 0.13.0 probe, below). Resolve calls are from the
scripting README installed with Resolve 20.0.1 ("Last Updated: 7 May 2025"), not yet run.

## Targets

### DaVinci Resolve (default editor)
| Mode | Needs | What you get |
|---|---|---|
| **NATIVE BUILD, automatic** | **Resolve Studio** at a **pinned version**; *Preferences → System → General → External scripting using: Local*; the official **`DaVinciResolveScript`** module | The full build sequence below, launched by Vcut, with readback. Autopilot ends with Resolve open on the timeline |
| **NATIVE BUILD, one click** | **Resolve free 20.x** (installed: 20.0.1) | The same build script, installed in *Workspace → Scripts*; the owner clicks it once *(in-app scripting on free ≤21.0 to verify at M0a)*. Free 21.1+ removed scripting, so do not upgrade the free edition past 21.0 if relying on this |
| **IMPORT** (fallback) | Any Resolve | *File → Import → Timeline* of `nle/package/vcut.fcpxml`: cuts, media, dissolves and markers; titles and looks are then missing and listed in the README |

Facts: the README (installed copy, 7 May 2025) lists the calls used above. External scripting is a Studio feature,
and from 21.1 Python scripting is Studio-only (checked 2026-10-12). **This workstation runs Resolve 20.0.1,
apparently the free edition**, so today Resolve is "one click" at best; **full autopilot into Resolve needs Studio
(US$295)**.

**Connector:** the official `DaVinciResolveScript` module, wrapped in a thin Vcut-owned adapter with typed stubs
(AGENTS' strict-type-hints rule), exposing only the calls in the capability matrix. **`pydavinci` is removed**: its
last release (0.2.3) dates from May 2022, its README asks for maintainers, and its `append_to_timeline` cannot pass
the `clipInfo` dicts that exact placement needs.

**Launch:** Resolve must be running for scripts to connect. Vcut spawns `Resolve.exe` (optionally `-nogui`), polls
`scriptapp("Resolve")` until it connects, then runs `GetVersion()` plus a **feature probe**. Features that fail the
probe use their fallback from the matrix and are listed in `build_report.json`.

#### Resolve build sequence
1. **Project from template.** One Resolve project per video (`vcut_<project_id>`), created from the **Vcut template** (`.drp`). The template holds the track layout, the **Fairlight Ducker on the music track keyed from A1/A2**, master bus limiter, render presets and the bins of **Vcut Fusion title templates** and **look stills (`.drx`)** that the effects library points to.
2. **Settings before media.** Set `timelineFrameRate` and resolution **before importing any media**: the timeline rate locks once media is in the pool.
3. **Bins:** `Voice/`, `B-Roll/<chapter>/<slot_id>/` (chosen **+ alternates**), `Photos/`, `Overlays/`, `Music/`, `SFX/`, `Inbox/`.
4. **Import** only new media (dedupe by absolute path / hash). Write provenance to each `MediaPoolItem` with `SetThirdPartyMetadata` (asset_id, licence, source URL).
5. **Base timeline.** If the pinned version cannot script transitions (below Studio 21.1), import `nle/package/vcut.fcpxml` with `MediaPool.ImportTimelineFromFile` to get cuts **and dissolves**, then continue with the API on that timeline. Otherwise create the timeline and place clips with `AppendToTimeline`. Name: `<project_id>_v<NNN>`; existing timelines are **never** modified.
6. **Tracks** via `AddTrack` with explicit layouts. A1 is mono; A2–A5 stereo (`AddTrack('audio')` defaults to mono).
7. **Placement** (when not from FCPXML): `clipInfo` = `{mediaPoolItem, startFrame, endFrame, mediaType, trackIndex, recordFrame}`, `recordFrame = timeline.GetStartFrame() + frame` (verify at M0a); video with `mediaType: 1` so embedded audio never lands on the voice or SFX tracks.
8. **Titles and cards:** for each text/card object, move the playhead to its frame on its track, `InsertFusionTitleIntoTimeline(<template name>)`, set the duration, then set the template's published inputs (text, colour, accent) through the clip's Fusion comp. *(Placement at the playhead and the input names are M0a checks.)*
9. **Looks and overlays:** `ApplyGradeFromDRX` (or `SetLUT`) per clip or per chapter; overlay clips on V4 get `CompositeMode` and `Opacity` with `SetProperty`. Static `ZoomX/Y`, `Pan`, `Tilt` as needed.
10. **Markers:** `Timeline.AddMarker(frameId, color, name, note, duration, customData=marker_id)` (frameId offset from timeline start) and per-clip `TimelineItem.AddMarker(…, customData=clip_id)`. Colour names are Resolve's set (Blue, Cyan, Green, Yellow, Red, …). `SetClipColor` by source type.
11. **Readback diff:** `GetItemListInTrack` / `GetStart` / `GetSourceStartFrame` / `GetMarkers` against the manifest, **0-frame tolerance**. Any mismatch fails the run and lists the offending clips.
12. **Backup:** `Timeline.Export(EXPORT_OTIO)` as an audit copy, `SaveProject`, then `ExportProject` to `.drp` in `nle/resolve/`, since a Resolve project lives in Resolve's database.

### FilmCraft
FilmCraft is an open-source (MIT OR Apache-2.0), Rust, Premiere-style editor from storytold, **alpha**. Installed on
this workstation (checked 2026-10-27): `C:\Program Files\FilmCraft\filmcraft.exe` and `filmcraft-cli.exe`, version
**0.13.0**.

| Mode | Needs | What you get |
|---|---|---|
| **NATIVE BUILD, automatic** (default for FilmCraft) | `filmcraft-cli` 0.13.0 (pinned) | Vcut writes `nle/filmcraft/build.jsonl` (one engine command per line), runs `filmcraft-cli --save-as <project>.fcproj run build.jsonl` headless, reads the sequence back, then opens FilmCraft on the project. Autopilot ends with FilmCraft open on it |
| **IMPORT** (fallback) | FilmCraft | *Import* of `vcut.fcpxml` or `vcut.otio` (the CLI's `file.import` accepts both): cuts and media only |

**What the 2026-10-27 probe showed** (headless, in a scratch folder, demo footage):
- `run script.jsonl` executes commands in order and returns JSON per line; `--save-as` writes a `.fcproj`, which is **plain JSON** (`"format":"filmcraft.project"`, `schema_version` 15). Times are ticks at **254 016 000 000 per second**; most commands also take `seconds=`, `frame=` or `timecode=`. `commands` lists about 700 commands; `describe <id>` gives each one's parameters.
- Worked: new sequence at 1920×1080/25 fps with 4+4 tracks; clip placement at an exact time and duration; two `Motion.scale` keyframes (a push-in); a 15-frame cross dissolve; **Light Leaks**, **Noise** and **Vignette** effects; a text graphic; **exporting a graphics template with a named text control and applying it again with a new value**; a chapter marker; rendering a frame to PNG.
- Failed as expected: a marker with colour `red`. FilmCraft's marker colours are named labels (Violet, Iris, Caribbean, Lavender, Cerulean, Forest, Rose, Mango, Purple, Blue, Teal, Magenta, Tan, Green, Brown, Yellow), so Vcut maps its marker kinds onto those.
- **Interchange loses native objects:** exporting the probe to FCPXML/OTIO reported its text graphic and generated clips as not carried over. That is why FilmCraft is built from commands, not from the package.
- Not yet run: `essentialSound.generateDucking`, `captions.import`, `lumetri.setLook`, `export` to MP4, opening a `.fcproj` in the app, and the bridge mode to a running app (`filmcraft --control <port>` + `filmcraft-cli --bridge`).

FilmCraft-specific rules:
- **Pin the release** (0.13.0) in the reference runtime profile; re-run the M0a probe on every upgrade. The command ids and the `.fcproj` schema are an alpha surface.
- Vcut writes **commands, never the `.fcproj` JSON directly**; the project file is FilmCraft's to own.
- **Readback:** `filmcraft-cli inspect sequence` (JSON: every clip's track, start, source in/out, effects and keyframes) diffed against the manifest with the same 0-frame rule as Resolve.
- Vcut does **not** use FilmCraft's MCP server as an AI-agent bridge; the adapter is deterministic code. (Any MCP use stays read-only, [[Vcut_Decision_Log#ADR-009 — Human gates]].)

### Preview render from the editor
After a successful build, 06 renders `preview/rough_cut.mp4` **from the built timeline**, so the preview shows the
real titles and effects ([[Vcut_Decision_Log#ADR-017 — Preview render]]):
- **FilmCraft:** `filmcraft-cli --project <p>.fcproj export <out>.mp4 --scale 0.5` (H.264, half size; command present in 0.13.0, first run at M0a). Offline media makes it exit 1, which fails the preview, not the build.
- **Resolve Studio:** a render job from the template's preview preset (`AddRenderJob`, `StartRendering`), polled until done.
- **Resolve free:** no scripted render; 05b's FFmpeg approximation is used instead.

## The interchange package (always built)
`{run}/nle/package/`, a backup that works in any editor:

| File | Content |
|---|---|
| `vcut.fcpxml` | **FCPXML 1.10**, written by Vcut's own writer (05): cuts, media, dissolves, markers. Media referenced by **relative** paths into `media/` |
| `vcut.otio` | The same timeline as OTIO, Vcut data under `metadata["vcut"]`. The audit copy |
| `media/` | Hard links to the conformed media, **plus the top-2 alternates per slot** in `media/alternates/<slot_id>/`. Named `<asset_id>.<ext>` (voice units `<unit_id>.wav`), so 07 can match clips in a human-edited export |
| `markers.csv` | Every marker: timecode, kind, name, note |
| `titles.csv` | Every title/card: timecode, preset id, its text values. What a manual import would need to re-create |
| `credits.txt`, `disclosure.json` | From 05 |
| `README_import.md` | Per editor: the import menu path, project settings to set **before** import, and what a manual import leaves out |

The package is **self-contained and movable**: zip it, open it on another machine, relink by folder.

## Opening the result in the editor ("open when done")
The setup form's editor choice (default **DaVinci Resolve**) and **open when done** ([[Vcut_Decision_Log#ADR-018 — Project setup options and autopilot]]) decide what 06 does at the end of the run. Autopilot targets whichever editor was chosen.

| Editor chosen | What happens at the end of the run | Owner action |
|---|---|---|
| Resolve **Studio** | Resolve launched, project `vcut_<project_id>` created from the template, timeline `…_v<NNN>` built natively, Resolve left open on it | None |
| Resolve **free 20.x** (this workstation) | Resolve launched (or brought to front); the Vcut build script is installed under *Workspace → Scripts*; a notification says "Click Workspace → Scripts → Vcut Build" | **One click** *(to verify at M0a)* |
| **FilmCraft** | `filmcraft-cli` builds and saves `06_editor/filmcraft/<project>.fcproj` headlessly, then FilmCraft is opened on it *(the open command to verify at M0a)* | None |
| Any, automation failed | The package and its README are opened in Explorer; the failure is in `STATUS.md` | Import by hand (a minute; titles then listed in `titles.csv`) |

## Capability matrix
**Filled at M0a on the pinned versions. A manifest feature may only be relied on for an editor once its cell is
tested ✔.** "Expected" comes from documentation; "Tested" is filled by the spike. A feature with no native route
in an editor is **left out** of that editor's presets, or baked only if the preset opts in ([[Vcut_Decision_Log#ADR-021 — One editor: everything native and editable]]).

| Manifest feature | Resolve native (exp.) | FilmCraft CLI | Fallback | Tested R / F |
|---|---|---|---|---|
| Cut placement on chosen track/frame | ✔ API / FCPXML | ✔ | — | ☐ / ✔ |
| Source in/out with handles | ✔ | ✔ (`sourceIn`, `duration`) | — | ☐ / ✔ |
| Static scale / position / opacity | ✔ | ✔ (`Motion`, `Opacity`) | — | ☐ / ✔ |
| Ken Burns / animated zoom | FCPXML Dynamic Zoom or Fusion comp | ✔ `Motion` keyframes | baked (opt-in) | ☐ / ✔ |
| Cross dissolve / dip | FCPXML import; API only Studio ≥21.1 | ✔ (112 transitions) | — | ☐ / ✔ |
| Clip fades | Studio ≥21.1 | ? (`Opacity` keyframes) | — | ☐ / ☐ |
| Editable title from a template, text set by Vcut | `InsertFusionTitleIntoTimeline` + Fusion inputs | ✔ `.fcgt` + `values` | `titles.csv` | ☐ / ✔ |
| Title animation (type-on, pop) | inside the template | template or Typewriter/Text Animator transitions | — | ☐ / ☐ |
| Look (LUT, faded film, grain, vignette) | `ApplyGradeFromDRX` / `SetLUT` | ✔ Lumetri, Noise, Vignette | — | ☐ / ✔ (Noise, Vignette) |
| Light leak | overlay clip + `CompositeMode` | ✔ Light Leaks effect | — | ☐ / ✔ |
| Overlay blend modes + opacity | `CompositeMode` (Screen, Add, Overlay, Multiply…) | `Opacity.blend` | — | ☐ / ☐ |
| Clip gain (`gain_db`) | ? | ✔ (`gainDb` on audio clips, seen in readback) | pre-normalised asset | ☐ / ☐ |
| Ducking | Fairlight Ducker via template | volume keyframes / `essentialSound.generateDucking` | baked stem + muted original | ☐ / ☐ |
| Markers with colour + note + id | ✔ `AddMarker` + `customData` | ✔ named colours; chapter markers | `markers.csv` | ☐ / ✔ |
| Captions | ? | `captions.import` | SRT in `07_delivery/` | ☐ / ☐ |
| Mixed source rates | ✔ | ? | conformed in 03d | ☐ / ☐ |
| Build without the owner (autopilot) | Studio: ✔ · free 20.x: one click (?) | ✔ headless | — | ☐ / ✔ |
| Open the built project in the app | Resolve stays open | `filmcraft.exe <project>` (?) | open by hand | ☐ / ☐ |
| Bins, clip colours, provenance metadata | ✔ | `file.newBin` (?) | `media/alternates/` folders | ☐ / ☐ |
| Paths incl. `((_atWork_))` | ? | ✔ (a `((_paren_test_))` folder: import, save, reopen) | — | ☐ / ✔ |

## Re-run & versioning rules
- Each run writes a new timeline/sequence `…_v<NNN+1>` (Resolve) or a new `<project>_v<NNN+1>.fcproj` (FilmCraft), and a new package. A human-touched timeline is never overwritten. Merging human edits back into the manifest is a **non-goal for v1**; 07 only *diffs* them for statistics.
- Media is imported once per editor project; re-runs reuse the existing items.

## LLM vs deterministic code
All code. No AI is involved in building or checking a timeline. Preset implementations are fixed files from the
library; 06 fills in values computed by 05.

## Failure modes
| Failure | Response |
|---|---|
| Resolve not reachable, or free edition detected | Install the one-click script and notify the owner (free), or stop with the package ready. Note it in `STATUS.md` |
| FilmCraft CLI missing, or its version is not the pinned one | Stop the FilmCraft build; package only. A new version must pass the M0a probe first |
| A command fails in `build.jsonl` | Stop at that line (no `--keep-going` in production), keep the partial project renamed `…_FAILED`, report the line and FilmCraft's error |
| Probe shows a missing feature | Use its fallback from the matrix and note it in the build report |
| Readback mismatch | Fail that build, keep the partial timeline renamed `…_FAILED`, list the diffs. The package is unaffected |
| Media offline after import | Fail; the M0a path test should have caught it. The README tells the human to relink by folder |

## Cost & time
$0 per run. Resolve Studio is a one-off US$295, needed only for full autopilot into Resolve. FilmCraft is free.

## Acceptance tests
- The M0a fixture builds natively in **both** pinned editors with every clip online and every cut at its manifest frame (readback diff = 0).
- Every M1 text/card preset arrives as an **editable title** in both editors: changing its text in the editor's inspector needs no other program.
- The fixture's looks, overlays, push-ins and dissolves are native effects/transitions in both editors (no baked clip unless the preset opted in).
- Two consecutive runs produce `…_v001` and `…_v002`; the `v001` timeline is identical before and after the second run.
- Every placed item carries a marker `customData` (Resolve) or a clip name/metadata (FilmCraft) that resolves to a `clip_id`.
- The package still imports by hand after being moved to another folder.
