# Creative Editorial Moves & Taste Layer Recipes

## 1. 12 FPS Stepped Motion Graphics ("Tactile / Stop-Motion Look")

### Concept & Narrative Motivation
Modern vector graphics can look clinical or synthetic when rendered at 60 fps or ultra-smooth 24 fps interpolation. Stepping motion-graphics frame rates down to **12.0 fps** introduces a tactile, printed-page, tactile editorial feel characteristic of high-end investigative video essays (e.g., Vox, Johnny Harris, NYT Visual Investigations).

### Parameter Contract
- **Step Frame Rate:** `12.0 fps` (holding each visual sample for 2 frames of a 24 fps timeline).
- **Application Target:**
  - Animated route maps (`render_map.py` route draws).
  - Document highlighter underlines.
  - Diagram arrows and archival stamp annotations.
- **Implementation:**
  - In EffectCraft: Add `posterizeTime(12)` expression to property transforms or apply `posterize_time` effect.
  - In FilmCraft: Apply `time_remap` effect or pre-render animated asset at 12 fps with `yuva444p12le` ProRes 4444.

### When NOT to Use
1. Never apply 12 fps stepped timing to live human talking-head video or organic camera pans (results in jarring judder).
2. Never apply to slow Ken Burns drifting stills.
3. Never apply to scrolling end-credits.

---

## 2. Master Glow & Grain Texture Layer (Track V4)

### Parameter Contract (Source of Truth: `style.json`)
The master texture pass unifies disparate archival footage formats (4:3 SD video, 35mm scans, modern 4K digital) under a consistent photographic texture.

1. **Film Grain (`noise` effect):**
   - Amount: `4.5%` (`Float(4.5)`).
   - Monochromatic: `color = false` (avoids digital RGB chroma noise).
   - Grain Size: `1.0`.
   - Blend: Soft overlay atop midtones.
2. **Highlight Bloom / Optical Glow (NOT built, not in `style.json`, not rendered; numbers are a starting point only):**
   - Threshold: `82.0%` (only peak whites and light sources bloom).
   - Radius: `45 px`.
   - Intensity: `0.18`.
   - Blend Mode: `Screen` or `Add` with layer opacity at `22.0%`.
3. **Peripheral Shading (`vignette` effect):**
   - Amount: `-10.0` (`grade.vignette`; measured corner about -9% luma; the earlier -30 darkened the frame mean by 25 levels on flat gray).
   - Feather: `90.0%`.
   - Midpoint: `70.0%`.
   - Roundness: `0.0` (oval 16:9 matching screen aspect ratio).

### When NOT to Use
1. Never apply heavy grain or bloom over fine monospaced computer code or dense financial spreadsheets where character legibility is paramount.
2. Never increase grain above 6.0% (triggers YouTube compression macro-blocking).

---

## 3. Document Highlighter & Redaction Reveal

### Parameter Contract
- **Highlighter Stroke:** Gold `#FFE8B8` or Warm Accent `#D4AF37`.
- **Blend Mode:** `Multiply` on Track V3 (translucent ink showing archival text underneath).
- **Opacity:** `78.0%`.
- **Wipe In:** Horizontal wipe from left to right over **14 frames** (0.584s) synchronized with the voiceover reading the exact words.
- **Paired SFX:** Soft marker slide / dry felt-tip draw (`sfx_paper_slide.wav`).

### When NOT to Use
1. Never highlight more than 2 sentences per document page.
2. Never highlight text faster than normal speaking cadence (150–160 WPM).

---

## 4. Behind-Text Subject Separation

### Parameter Contract
- **Layer Architecture:**
  - V1: Background plate / environmental plate.
  - V2: Roto-isolated subject mask (host or historical figure).
  - V3: Title card or keyword graphic (`keyword-pop` or `chapter-card`).
- **Depth Hierarchy:** Graphic is rendered at V2.5 (behind subject silhouette, in front of background plate).
- **Subject Edge Feather:** `3.5 px` to eliminate cutout halos.
- **Subject Contrast Boost:** `+5.0%` to lift foreground off the background graphic.

### When NOT to Use
1. Never place text behind the subject if the text cannot be 100% read (if the subject covers more than 30% of any word, bring the text to V3 foreground).
2. Never use with complex hair edges without high-fidelity alpha rotoscoping.
