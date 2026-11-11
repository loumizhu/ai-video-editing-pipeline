# Vcut — Deterministic Video Assembly Pipeline

Vcut is a deterministic, multi-step pipeline that turns your own script (with or without instructions) into a timeline built natively in DaVinci Resolve (default) or FilmCraft, with every title and effect editable there, plus a preview video, for long-form narrated YouTube videos. AI is optional at every step. The plan starts at [AGENTS.md](AGENTS.md) and [Vcut_End_to_End_Pipeline_Architecture.md](Vcut_End_to_End_Pipeline_Architecture.md).

> Status 2026-10-26: the code is a skeleton (runner, CLI, Storyboard) built against the earlier brief-first plan. Script input (`vcut new <id> --script <file>`) is planned, not built yet.

## Quickstart
```bash
# Start the Living Storyboard Web UI & Orchestrator
vcut board

# Or run via CLI
vcut new my_project
vcut run --project my_project
```
