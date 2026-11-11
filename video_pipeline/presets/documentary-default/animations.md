# Timeline Animations & Motion Recipes

## 1. Ken Burns Effect on Archival Stills

### Mathematical Parameter Contract
- **Duration:** 4.0s to 7.0s (spanning the exact duration of the archival still clip).
- **Start Scale:** `100.0%`.
- **End Scale:** `115.0%` (standard drift) to `125.0%` (dramatic push). Hard limit: **<=130.0%** to prevent bitmap softening.
- **Position Displacement:**
  - Delta X: `+/- 40 px` to `80 px`.
  - Delta Y: `+/- 30 px` to `60 px`.
  - Focal Target: Anchor translates from center `[960, 540]` toward the subject's eyeline (e.g. `[920, 480]` or `[1000, 490]`).
- **Easing:** Real `Bezier` / `easeOut` curve with `in_influence = 0.65`, `out_influence = 0.65`, `speed = 0.0`.
- **Direction Rules:**
  - Forward push (scale 100% -> 120%): Intimacy, confession, investigative revelation.
  - Backward pull (scale 120% -> 100%): Contextualization, historical aftermath, solitude.

### When NOT to Use
1. Never apply Ken Burns to talking-head footage where natural host motion already exists.
2. Never apply to graphic cards (lower-thirds, quote cards) which execute independent floating animations.
3. Never use opposing pan directions back-to-back across a cut (e.g., pan left followed immediately by pan right causes visual whiplash).

### FilmCraft Implementation Syntax
```powershell
# Set keyframes on clip motion:
# Scale keyframe 1 at clip start (t0):
filmcraft-cli --project <proj.fcproj> --save exec effects.setParam '{"clip": <id>, "effect": "motion", "param": "scale", "value": 100.0, "time": <t0>, "keyframe": true}'
# Scale keyframe 2 at clip end (t1):
filmcraft-cli --project <proj.fcproj> --save exec effects.setParam '{"clip": <id>, "effect": "motion", "param": "scale", "value": 120.0, "time": <t1>, "keyframe": true}'
# Set Bezier interpolation:
filmcraft-cli --project <proj.fcproj> --save exec effects.setInterpolation '{"clip": <id>, "effect": "motion", "param": "scale", "mediaTime": <t0>, "interpolation": "easeOut"}'
```

---

## 2. Focal Zoom / The Punch-In

### Mathematical Parameter Contract
- **Scale Jump:** `100.0%` -> `120.0%` (standard) or `125.0%` (strong emphasis).
- **Transition Duration:** **0 frames** (Hard cut punch-in) or **4 frames** (Whip zoom with motion blur).
- **Anchor Offset:** Shift anchor coordinates directly to speaker's eyes (`[960, 540]` -> `[910, 450]`).
- **Trigger Rule:** Motivated on the second sentence or turning clause of a primary statement.
- **Density Cap:** Maximum **1 punch-in per 30 seconds** of talking head.

### When NOT to Use
1. Never punch in while an animated lower third or quote card is on-screen.
2. Never punch in twice in under 15 seconds.
3. Never punch in on an awkward facial transition or blink.

---

## 3. Photo Stack Multi-Plate Presentation

### Mathematical Parameter Contract
When presenting multiple related archival documents or photographs simultaneously:
- **Base Canvas:** Track V2, V3, V4.
- **Plate 1 (Background Left):**
  - Rotation: `-4.5 deg`.
  - Scale: `85.0%`.
  - Position: `[820, 560]`.
  - Drop Shadow: Opacity `40%`, Distance `12 px`, Blur `15 px`.
  - Entrance: Frame `0` (t = 0.00s).
- **Plate 2 (Background Right):**
  - Rotation: `+3.2 deg`.
  - Scale: `88.0%`.
  - Position: `[1100, 550]`.
  - Drop Shadow: Opacity `45%`, Distance `14 px`, Blur `18 px`.
  - Entrance: Frame `6` (t = 0.25s).
- **Plate 3 (Hero Foreground):**
  - Rotation: `0.0 deg`.
  - Scale: `94.0%`.
  - Position: `[960, 520]`.
  - Drop Shadow: Opacity `55%`, Distance `20 px`, Blur `25 px`.
  - Entrance: Frame `12` (t = 0.50s) with Bezier easeOut.

### When NOT to Use
1. Never use for a single portrait.
2. Never stack more than 3 plates (causes visual clutter and illegibility).
