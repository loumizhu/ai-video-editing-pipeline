#!/usr/bin/env python3
"""write_graphics_manifest.py - Generates graphics_manifest.json for Stage 07b.
Scans graphics directory, computes SHA-256 hashes, file sizes, image dimensions,
transparent overlay classification, and licence metadata from ledger/registry.
Rules:
  - is_transparent_overlay is TRUE only for assets designed as overlays (callouts, cards, stamps,
    date strips, keywords, and map overlays), and FALSE for full-frame plates (articles, map stills).
  - Licence metadata defaults to 'owner-supplied / see asset_registry' (never 'Proprietary')
    or 'Public Domain / Natural Earth vector data' for maps, or is read from asset_registry.json.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from PIL import Image

def sha256_file(filepath):
    """Computes hex SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def inspect_image(filepath, graphic_type, filename):
    """Inspects image dimensions, alpha channel, and classifies transparent overlay vs full plate."""
    try:
        with Image.open(filepath) as img:
            width, height = img.size
            mode = img.mode
            has_alpha = False
            transparent_pixel_pct = 0.0

            if mode in ('RGBA', 'LA') or (mode == 'P' and 'transparency' in img.info):
                has_alpha = True
                rgba_img = img.convert('RGBA')
                alpha_channel = rgba_img.split()[3]
                # Measure percentage of transparent/translucent pixels (< 128 alpha)
                histogram = alpha_channel.histogram()
                trans_pixels = sum(histogram[:128])
                total_pixels = width * height
                transparent_pixel_pct = round((trans_pixels / total_pixels) * 100.0, 1)

            # Designed overlay classification:
            # Overlays: callouts, cards (stamps, date strips, numbers, keywords), and explicit map overlays
            # Full-frame plates: articles, map stills, video frames
            fn_lower = filename.lower()
            is_designed_overlay = False

            if graphic_type in ('callout', 'card'):
                is_designed_overlay = True
            elif 'overlay' in fn_lower or 'alpha' in fn_lower:
                is_designed_overlay = True
            elif graphic_type == 'map' and ('overlay' in fn_lower or 'alpha' in fn_lower):
                is_designed_overlay = True
            elif graphic_type == 'article':
                is_designed_overlay = False
            elif 'still' in fn_lower or 'plate' in fn_lower:
                is_designed_overlay = False

            # Overlay requires both intended role AND actual non-zero transparency
            is_transparent_overlay = is_designed_overlay and has_alpha and (transparent_pixel_pct >= 5.0)

            return {
                "width": width,
                "height": height,
                "mode": mode,
                "has_alpha": has_alpha,
                "transparent_pixel_pct": transparent_pixel_pct,
                "is_transparent_overlay": is_transparent_overlay,
                "target_layer": "V3/V4" if is_transparent_overlay else "V1/V2"
            }
    except Exception as e:
        return {
            "error": str(e)
        }

def load_registry(registry_path):
    """Loads asset registry or ledger if provided."""
    if not registry_path or not os.path.exists(registry_path):
        return {}
    try:
        with open(registry_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Map by asset_id and by relative path / filename
        lookup = {}
        assets = data.get("assets", data if isinstance(data, list) else [])
        for entry in assets:
            if isinstance(entry, dict):
                if "asset_id" in entry:
                    lookup[entry["asset_id"]] = entry
                if "path" in entry:
                    lookup[os.path.basename(entry["path"])] = entry
        return lookup
    except Exception:
        return {}

def build_manifest(graphics_dir, output_path=None, video_slug="unknown", registry_path=None):
    """Scans graphics directory and generates manifest structure."""
    if not os.path.exists(graphics_dir):
        print(f"Error: directory {graphics_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    registry = load_registry(registry_path)
    assets = []
    allowed_exts = ('.png', '.jpg', '.jpeg', '.webp', '.mp4', '.mov')

    for root, _, files in os.walk(graphics_dir):
        for f in sorted(files):
            if f == 'graphics_manifest.json' or f == 'contact_sheet.png':
                continue
            ext = os.path.splitext(f)[1].lower()
            if ext not in allowed_exts:
                continue

            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, graphics_dir).replace('\\', '/')
            filesize = os.path.getsize(full_path)
            file_hash = sha256_file(full_path)

            m_slot = re.match(r'^(s\d+)', f, re.I)
            slot_id = m_slot.group(1).lower() if m_slot else None

            fn_lower = f.lower()
            if "callout" in fn_lower:
                graphic_type = "callout"
            elif "map" in fn_lower:
                graphic_type = "map"
            elif "article" in fn_lower:
                graphic_type = "article"
            elif any(k in fn_lower for k in ("card", "stamp", "date_strip", "big_number", "keyword")):
                graphic_type = "card"
            else:
                graphic_type = "custom_graphic"

            # Resolve licence from registry or sound default
            reg_entry = registry.get(slot_id) or registry.get(f)
            if reg_entry and "licence" in reg_entry:
                licence = reg_entry["licence"]
                if isinstance(licence, dict):
                    licence = licence.get("id", "owner-supplied / see asset_registry")
            elif graphic_type == "map":
                licence = "Public Domain / Natural Earth vector data"
            else:
                licence = "owner-supplied / see asset_registry"

            info = {
                "filename": f,
                "relative_path": rel_path,
                "slot_id": slot_id,
                "graphic_type": graphic_type,
                "size_bytes": filesize,
                "sha256": file_hash,
                "provenance": "pipeline_custom_render",
                "licence": licence
            }

            if ext in ('.png', '.jpg', '.jpeg', '.webp'):
                img_info = inspect_image(full_path, graphic_type, f)
                info.update(img_info)
                if graphic_type == "map":
                    info["cartography_source"] = "Natural Earth 1:50m Vector Data (Public Domain)"

            assets.append(info)

    manifest = {
        "schema": "vcut.graphics_manifest/1",
        "video_slug": video_slug,
        "graphics_count": len(assets),
        "target_track": "V3/V4",
        "assets": assets
    }

    if output_path:
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as mf:
            json.dump(manifest, mf, indent=2)

    return manifest

def main():
    parser = argparse.ArgumentParser(description="Generate graphics_manifest.json with transparent overlay detection")
    parser.add_argument('--dir', required=True, help="Path to 07_Video_Edit/graphics directory")
    parser.add_argument('--out', default=None, help="Output graphics_manifest.json path")
    parser.add_argument('--registry', default=None, help="Optional path to asset_registry.json")
    parser.add_argument('--slug', default="video_pipeline", help="Project video slug")
    args = parser.parse_args()

    manifest = build_manifest(args.dir, output_path=args.out, video_slug=args.slug, registry_path=args.registry)
    print(f"Graphics manifest generated: {len(manifest['assets'])} assets cataloged.")
    for a in manifest['assets'][:5]:
        print(f"  {a['filename']}: {a['graphic_type']} | overlay={a.get('is_transparent_overlay')} | licence={a['licence']}")

if __name__ == '__main__':
    main()
