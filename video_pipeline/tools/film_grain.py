#!/usr/bin/env python3
"""
film_grain.py - Procedural Organic Celluloid Film Grain Synthesis

Implements Hollywood Colorist and Film Craft Chemist rules:
  1. Luminance Masking: Suppress grain in shadows (<15%) and highlights (>85%), peaking in midtones.
  2. Monochromatic Base: 0% chroma noise / saturation. Pure silver halide crystal texture.
  3. Temporal Randomness: Exact frame-rate matching (zero frozen noise loops).
  4. Narrative Profiles:
       - Profile A: Clean Modern Cinema (Fincher 35mm 50D)
       - Profile B: Classic Hollywood (35mm Portra/Eterna)
       - Profile C: Gritty Documentarian (16mm 500T)
       - Profile D: Vintage Archive / Memory Fragment (Super 8mm + Gate Weave)
  5. Execution Pro-Tips: 4K resolution scaling, post-grade / pre-sharpening order, +2% web compression buffer.

Usage:
  python film_grain.py filter --profile classic_35mm [--4k] [--youtube]
  python film_grain.py apply --input clip.mp4 --output clip_grained.mp4 --profile classic_35mm [--youtube]
  python film_grain.py filmcraft --profile classic_35mm --clip-id 12
"""

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRESETS_DIR = os.path.normpath(os.path.join(HERE, "..", "presets", "color"))
PROFILE_JSON = os.path.join(PRESETS_DIR, "film_grain_profiles.json")

PROFILE_ALIASES = {
    "a": "profile_a_clean_modern_cinema",
    "clean": "profile_a_clean_modern_cinema",
    "clean_35mm": "profile_a_clean_modern_cinema",
    "fincher": "profile_a_clean_modern_cinema",
    "b": "profile_b_classic_hollywood",
    "classic": "profile_b_classic_hollywood",
    "classic_35mm": "profile_b_classic_hollywood",
    "hollywood": "profile_b_classic_hollywood",
    "c": "profile_c_gritty_documentarian",
    "gritty": "profile_c_gritty_documentarian",
    "gritty_16mm": "profile_c_gritty_documentarian",
    "16mm": "profile_c_gritty_documentarian",
    "d": "profile_d_vintage_archive",
    "vintage": "profile_d_vintage_archive",
    "vintage_8mm": "profile_d_vintage_archive",
    "8mm": "profile_d_vintage_archive",
    "super8": "profile_d_vintage_archive",
}


def load_profiles():
    if not os.path.exists(PROFILE_JSON):
        raise FileNotFoundError(f"Missing film grain preset file: {PROFILE_JSON}")
    with open(PROFILE_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_profile_key(name):
    clean = name.strip().lower()
    if clean in PROFILE_ALIASES:
        return PROFILE_ALIASES[clean]
    data = load_profiles()
    if clean in data.get("profiles", {}):
        return clean
    for k, v in data.get("profiles", {}).items():
        if v.get("id") == clean or clean in v.get("name", "").lower():
            return k
    raise ValueError(f"Unknown grain profile '{name}'. Choose from: clean_35mm (A), classic_35mm (B), gritty_16mm (C), vintage_8mm (D)")


def build_ffmpeg_filtergraph(profile_key, is_4k=False, youtube=False):
    data = load_profiles()
    prof = data["profiles"][profile_key]
    settings = prof["settings"]
    rules = data.get("rules", {})
    tips = rules.get("execution_pro_tips", {})

    intensity = settings["intensity_percent"]
    grain_size = settings["grain_size"]
    weave = settings.get("gate_weave_px", 0.0)

    if youtube:
        buffer = tips.get("web_compression_buffer_percent", 2.0)
        intensity += buffer

    if is_4k:
        multiplier = tips.get("upscale_4k_multiplier", 1.85)
        grain_size *= multiplier
        intensity *= 1.15

    # Derive FFmpeg monochromatic noise strength (c0s) based on intensity
    # Standard mapping: c0s roughly 0.8 * intensity_percent
    c0s = max(2, int(round(intensity * 0.9)))

    # Midtone luminance mask formula:
    # 4 * (Y/255) * (1 - Y/255) peaks at Y=128 (val 255), drops to 0 at Y=0 and Y=255.
    # Exponent 1.2 tightens midtones and suppresses deep shadows / specular highlights.
    luma_lut = "255*pow(max(0, 4*(val/255)*(1-(val/255))), 1.2)"

    filter_chains = []
    # Split input into base video and luma analysis branch
    filter_chains.append("[0:v]split=2[grain_base][v_luma]")

    # Branch 1: Monochromatic noise on luma only (c0s = strength, c1s=0, c2s=0)
    filter_chains.append(f"[grain_base]noise=c0s={c0s}:c1s=0:c2s=0:allf=t+u:c0f=u[noisy]")

    # Branch 2: Quadratic midtone mask
    filter_chains.append(f"[v_luma]format=gray,lut=y='{luma_lut}'[mask]")

    # Merge: base with noisy strictly through mask
    if weave > 0.0:
        # Replicate subtle gate weave (microscopic camera shake)
        filter_chains.append(f"[grain_base][noisy][mask]maskedmerge[grained_pre]")
        filter_chains.append(f"[grained_pre]crop=in_w-4:in_h-4:2:2,pad=in_w+4:in_h+4:2+1*sin(2*PI*n/4):2+1*cos(2*PI*n/3)[grained]")
    else:
        filter_chains.append("[grain_base][noisy][mask]maskedmerge[grained]")

    return "; ".join(filter_chains)


def generate_filmcraft_commands(profile_key, clip_id=None, track="V4", overlay=False):
    data = load_profiles()
    prof = data["profiles"][profile_key]
    fc_info = prof.get("filmcraft", {})

    if overlay:
        return [
            {
                "id": "effects.setParam",
                "params": {
                    "clip": clip_id or "<v4_grain_clip_id>",
                    "effect": "opacity",
                    "param": "blend",
                    "value": fc_info.get("v4_overlay_mode", "Overlay"),
                },
            },
            {
                "id": "effects.setParam",
                "params": {
                    "clip": clip_id or "<v4_grain_clip_id>",
                    "effect": "opacity",
                    "param": "opacity",
                    "value": fc_info.get("v4_overlay_opacity", 30.0),
                },
            },
        ]
    else:
        return [
            {
                "id": "effects.apply",
                "params": {
                    "clip": clip_id or "<target_clip_id>",
                    "effect": "noise",
                },
            },
            {
                "id": "effects.setParam",
                "params": {
                    "clip": clip_id or "<target_clip_id>",
                    "effect": "noise",
                    "param": "amount",
                    "value": fc_info.get("native_noise_amount", 3.0),
                },
            },
            {
                "id": "effects.setParam",
                "params": {
                    "clip": clip_id or "<target_clip_id>",
                    "effect": "noise",
                    "param": "monochrome",
                    "value": True,
                },
            },
        ]


def main():
    parser = argparse.ArgumentParser(description="Procedural Organic Celluloid Film Grain Synthesis")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: filter
    p_filter = subparsers.add_parser("filter", help="Output FFmpeg filtergraph string")
    p_filter.add_argument("--profile", required=True, help="Profile: clean_35mm, classic_35mm, gritty_16mm, vintage_8mm")
    p_filter.add_argument("--4k", dest="is_4k", action="store_true", help="Scale grain for 4K canvas (3840x2160)")
    p_filter.add_argument("--youtube", action="store_true", help="Add +2% intensity buffer for YouTube compression prep")

    # Subcommand: apply
    p_apply = subparsers.add_parser("apply", help="Execute FFmpeg render with organic celluloid grain")
    p_apply.add_argument("--input", "-i", required=True, help="Input video file")
    p_apply.add_argument("--output", "-o", required=True, help="Output video file")
    p_apply.add_argument("--profile", required=True, help="Profile: clean_35mm, classic_35mm, gritty_16mm, vintage_8mm")
    p_apply.add_argument("--4k", dest="is_4k", action="store_true", help="Scale grain for 4K canvas")
    p_apply.add_argument("--youtube", action="store_true", help="Add +2% buffer for YouTube compression")
    p_apply.add_argument("--crf", default="17", help="H.264 CRF quality level (default 17)")

    # Subcommand: filmcraft
    p_fc = subparsers.add_parser("filmcraft", help="Output FilmCraft JSON commands for native grain")
    p_fc.add_argument("--profile", required=True, help="Profile: clean_35mm, classic_35mm, gritty_16mm, vintage_8mm")
    p_fc.add_argument("--clip-id", help="Target clip ID")
    p_fc.add_argument("--overlay", action="store_true", help="Generate V4 Overlay blend mode commands instead of clip noise")

    args = parser.parse_args()

    try:
        prof_key = resolve_profile_key(args.profile)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

    if args.command == "filter":
        fg = build_ffmpeg_filtergraph(prof_key, is_4k=args.is_4k, youtube=args.youtube)
        print(fg)

    elif args.command == "apply":
        fg = build_ffmpeg_filtergraph(prof_key, is_4k=args.is_4k, youtube=args.youtube)
        cmd = [
            "ffmpeg", "-y", "-hide_banner",
            "-i", args.input,
            "-filter_complex", fg,
            "-map", "[grained]",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-crf", str(args.crf),
            "-preset", "slow",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            args.output,
        ]
        print(f"Executing: {' '.join(cmd)}")
        res = subprocess.run(cmd)
        sys.exit(res.returncode)

    elif args.command == "filmcraft":
        cmds = generate_filmcraft_commands(prof_key, clip_id=args.clip_id, overlay=args.overlay)
        print(json.dumps(cmds, indent=2))


if __name__ == "__main__":
    main()
