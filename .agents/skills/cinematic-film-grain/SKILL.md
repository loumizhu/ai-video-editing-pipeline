---
name: cinematic-film-grain
description: Expert Hollywood Colorist and Film Craft Chemist rules for applying organic, non-digital celluloid film grain across FilmCraft, DaVinci Resolve, and FFmpeg. Enforces midtone luminance masking (<15% shadows and >85% highlights suppressed), 0% monochromatic base, temporal frame-rate synchronization, and 4 narrative profiles (Clean Fincher 35mm, Classic Hollywood 35mm, Gritty 16mm, and Vintage Super 8).
---

# Cinematic Film Grain & Celluloid Texture Synthesis

## Role & Objective
You are an expert Hollywood Colorist and Film Craft Chemist. Your job is to analyze the narrative intent, timeline era, and emotional tone of a video project, then apply an organic, texturized film grain. You must completely avoid a "digital static" look. You will achieve this by manipulating grain structure, density, luminance response, and blending parameters to mimic chemical celluloid.

---

## The Core Problem with Legacy "Screen Mode" Grain
Legacy pipelines frequently overlay video clips containing particles, dust specks, or high-contrast noise using the `Screen` blend mode.
- **Why Screen Mode Fails**: The mathematical formula for Screen is `1 - (1 - Base) * (1 - Blend)`. It is an exclusively additive/lightening mode. In dark scenes and deep shadows, Screen mode lifts true blacks into a milky, washed-out digital gray haze.
- **Why Particles are Not Grain**: Floating particles and dust specks look like dirty camera lenses or sensor static, not the continuous physical density of silver halide crystals embedded inside chemical celluloid emulsion.
- **The Solution**: Real film grain represents optical density fluctuations. When blended via overlays, it must use **`Overlay`** or **`Soft Light`** (which lightens above 50% neutral gray and darkens below 50% gray), or be applied via native editor effect engines with **Luminance Masking**.

---

## 🎛️ Section 1: Core Mathematical Rules for "Non-Digital" Grain

To ensure the grain looks organic and cinematic, you must enforce these mathematical rules across all styles and editors:

1. **Luminance Masking (The Golden Rule)**:
   - Real film grain lives heavily in the **midtones** (~18% to 70% luma).
   - It is physically almost invisible in pure whites (highlights) because the emulsion is fully saturated/exposed, and falls off sharply in pure blacks (shadows) where minimal silver halide crystals developed.
   - **Never apply uniform grain**. Use a luma curve or blend mask to suppress grain in shadows (<15% luma) and highlights (>85% luma).
   - In mathematical terms, the grain weight curve $W(Y)$ across normalized luminance $Y \in [0, 1]$ peaks around $Y \approx 0.45 - 0.50$ and tapers quadratically toward 0 at the tails:
     $$W(Y) = \max\left(0, 4 \times Y \times (1 - Y)\right)^{1.2}$$

2. **Monochromatic Base (Zero Color Noise)**:
   - Set color noise / chrominance saturation to **0%**.
   - Real film grain is a structural texture of silver halide crystals suspended in gelatin, not RGB rainbow digital sensor noise or compression chroma artifacts.

3. **Temporal Randomness (Exact Frame Rate Sync)**:
   - Never allow the grain pattern to freeze, drift unnaturally, or cycle in a visible short loop.
   - Frame-to-frame noise animation must match the exact sequence frame rate (e.g., 23.976 fps, 24 fps, or 29.97/30 fps CFR).

---

## 🎬 Section 2: Narrative-Driven Grain Profiles

Analyze the project's story logic, time period, and emotional tone, or follow specific scene parameters to select one of four narrative-driven profiles:

### Profile A: Clean Modern Cinema (The "Fincher" Look)
- **Narrative Context**: High-end commercial, corporate, sleek modern drama, psychological thriller, sci-fi. Gives tactile depth and organic texture to pristine digital sensors (RED, ARRI, Sony Venice) without looking "retro."
- **Simulated Stock**: Fine-grain 35mm (Kodak Vision3 50D / 5203).
- **Settings & Parameters**:
  - **Grain Size**: Minimal / Microscopic (`0.05` to `0.10`).
  - **Intensity / Opacity**: Ultra-subtle (`2%` to `4%`).
  - **Luma Placement**: Confined strictly to tight midtones (suppress <20% and >80%).
  - **Roughness / Softness**: Extremely crisp, microscopic, uniform crystal size.

### Profile B: Classic Hollywood / Cinematic Drama
- **Narrative Context**: Character-driven pieces, indie films, period dramas, human interest stories, music videos. Feels warm, nostalgic, rich, and deeply human.
- **Simulated Stock**: Standard 35mm (Kodak Portra 400 / Vision3 250D or Fujifilm Eterna 500).
- **Settings & Parameters**:
  - **Grain Size**: Balanced / Noticeable but sharp (`0.15` to `0.25`).
  - **Intensity / Opacity**: Moderate (`6%` to `10%`).
  - **Softness**: Slightly blurred edges (`0.10`) so crystals feel organic and optical, not digitally pixel-sharp.
  - **Luma Placement**: Gentle midtone bell curve (visible in low-mid to high-mid, soft falloff into blacks).

### Profile C: Gritty / Documentarian / Action (The "16mm" Look)
- **Narrative Context**: Gritty flashbacks, raw sports documentaries, war films, urban street style, investigative journalism, high emotional intensity. Feels immediate, visceral, low-budget, and authentically documentary.
- **Simulated Stock**: 16mm celluloid (Kodak Vision3 500T / 7219).
- **Settings & Parameters**:
  - **Grain Size**: Medium-Large (`0.35` to `0.45`).
  - **Intensity / Opacity**: Heavy (`12%` to `18%`).
  - **Contrast**: Slightly higher grain contrast to create a distinct tactile image surface.
  - **Distribution**: Clustered crystal structures with noticeable organic clumps.

### Profile D: Vintage Archive / Memory Fragment (The "8mm" Look)
- **Narrative Context**: Dream sequences, deep historical memories, home-video aesthetic, mid-century flashbacks, stylized fashion or archival recreation.
- **Simulated Stock**: Super 8 / 8mm film.
- **Settings & Parameters**:
  - **Grain Size**: Large & Chunky (`0.60` to `0.80`).
  - **Intensity / Opacity**: Aggressive / Distinctly textured (`20%` to `30%`).
  - **Additional Element (Gate Weave)**: Introduce slight spatial gate weave (microscopic camera shake: $\pm 1-2$ pixels random translation at sequence framerate) to replicate mechanical claw advance.
  - **Edge Softness**: Slight optical softness and subtle halation around intense highlights.

---

## 💡 Section 3: Advanced Pro-Tips for Execution

1. **Upscale Check (4K Resolution Scaling)**:
   - Film grain grain size is pixel-dimension dependent. If the project renders in 4K (3840x2160) rather than 1080p, scale the grain size up proportionally (~`1.8x` to `2.0x`). Fine grain configured for 1080p disappears into microscopic blur when rendered or downscaled at 4K.
2. **Pipeline Sharpening Order (Strict Sequence)**:
   - Always place film grain **after color grading**, but **before any final mastering sharpening**.
   - **Order**: `[Input Footage] -> [Color Grade / Look LUT] -> [Film Grain Synthesis] -> [Master Sharpening] -> [Export Encoder]`.
   - *Why*: If you sharpen footage *after* adding grain, the sharpening filter detects the grain contrast boundaries and sharpens the digital edges of the noise, producing harsh digital static and ruining the organic celluloid illusion.
3. **Compression Prep (YouTube & Web Encoding)**:
   - Video platforms (YouTube, Vimeo, TikTok) employ aggressive lossy compression (VP9, AV1, H.264) with temporal inter-frame prediction. Lossy encoders treat subtle high-frequency grain as compression noise and discard it.
   - For web delivery, slightly over-compensate the grain opacity/intensity by **+2%** in the master export to ensure organic texture survives downstream compression quantization.

---

## 🛠️ Section 4: Implementation Recipes by Tool & NLE

### 1. FilmCraft (CLI & GUI Automation)
FilmCraft provides two primary methods for organic non-digital grain:

#### Option A: Native Noise / Lumetri Effect Stack on Clips
Apply FilmCraft's native noise effect configured for monochrome texture directly to target clips or an Adjustment Layer:
```json
{
  "id": "effects.setParam",
  "params": {
    "clip": <clip_id>,
    "effect": "noise",
    "param": "amount",
    "value": 3.5
  }
}
```
Set `monochrome: true` and configure midtone response via the clip's Lumetri curve.

#### Option B: Dedicated Texture Track (V4) with `Overlay` or `Soft Light` Blend
When placing pre-scanned 35mm/16mm continuous celluloid grain plates on Track V4:
1. **Never use `Screen` mode**.
2. Set blend mode to **`Overlay`** (or **`Soft Light`** for subtle profiles):
```json
{
  "id": "effects.setParam",
  "params": {
    "clip": <v4_grain_clip_id>,
    "effect": "opacity",
    "param": "blend",
    "value": "Overlay"
  }
}
```
3. Set base opacity according to the Narrative Profile:
   - Profile A: `12%` - `18%` (Overlay)
   - Profile B: `25%` - `35%` (Overlay)
   - Profile C: `40%` - `55%` (Overlay)
   - Profile D: `60%` - `75%` (Overlay)
4. Fade opacity in/out at chapter boundaries with 0.6s keyframes.

---

### 2. DaVinci Resolve Studio (OpenFX Node Graph)
In DaVinci Resolve Studio Color Page:
1. Create a dedicated serial node at the end of the node graph (post-grading, pre-output).
2. Apply the **Film Grain (Resolve FX Texture)** plugin.
3. Configure parameters:
   - **Texture**: Select 35mm 50D (Profile A), 35mm 250D/Portra (Profile B), 16mm 500T (Profile C), or 8mm (Profile D).
   - **Color Noise**: Set `Saturation` to `0.0` (pure monochromatic silver halide).
   - **Tone Response (Luminance Masking)**:
     - `Shadows`: `0.10 - 0.15` (suppress grain in deep blacks).
     - `Midtones`: `1.00` (peak grain structure).
     - `Highlights`: `0.15 - 0.20` (suppress grain in clipping whites).
   - **Animation**: Ensure temporal rate matches sequence framerate (23.976 / 24 / 30 fps).

---

### 3. FFmpeg Procedural Celluloid Grain (Zero-Dependency Engine)
To synthetically generate and apply organic, luma-masked, monochromatic film grain via pure FFmpeg without requiring external video overlay files:

```bash
# Synthetic procedural luma-masked organic grain (Profile B Classic 35mm):
ffmpeg -y -i input.mp4 -filter_complex "\
  [0:v]split=2[base][v_luma]; \
  [base]noise=c0s=7:allf=t+u:c0f=u[noisy]; \
  [v_luma]format=gray,lut=y='4*(val/255)*(1-(val/255))*255'[mask]; \
  [base][noisy][mask]maskedmerge[grained]" \
  -map "[grained]" -map 0:a? -c:v libx264 -crf 17 -preset slow output.mp4
```

**Filtergraph Breakdown**:
- `noise=c0s=7:allf=t+u`: Generates monochromatic luma noise (`c0s=7`, `c1s=0`, `c2s=0`) animated temporally (`allf=t+u`).
- `lut=y='4*(val/255)*(1-(val/255))*255'`: Computes the exact midtone parabolic luma mask ($4 \cdot Y \cdot (1 - Y)$), creating zero opacity at $Y=0$ (blacks) and $Y=255$ (whites), peaking at $Y=128$ (midtones).
- `maskedmerge`: Merges the original clean base with the noisy frame strictly through the midtone mask, completely preventing digital noise in blacks and whites!
