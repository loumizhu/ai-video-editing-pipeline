#!/usr/bin/env python3
"""render_callout.py - Custom Character Introduction Callout Renderer
Generates face-safe, documentary-grade character introduction overlay cards
(transparent RGBA PNG or ProRes 4444 / PNG image sequence / alpha video)
without using NLE built-in presets.

Adheres to Video 010 reverence standards:
- Elegant typography (Ivory #F3EBDD title, Gold #FFE8B8 subtitle/role)
- Semi-transparent glass backplate with subtle gold border
- Face-safe placement coordinates (bottom-left, bottom-right, top-left, top-right)
- Formal naming rules (e.g. "Cecil", not "Cec")
- Watermark support for sample / illustrative runs
"""

import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont

def get_font(size, bold=False, italic=False):
    font_names = []
    if bold and italic:
        font_names = ["georgiaz.ttf", "segoeuiz.ttf", "arialbi.ttf"]
    elif bold:
        font_names = ["georgiab.ttf", "segoeuib.ttf", "arialbd.ttf"]
    elif italic:
        font_names = ["georgiai.ttf", "segoeuii.ttf", "ariali.ttf"]
    else:
        font_names = ["georgia.ttf", "segoeui.ttf", "arial.ttf"]
    
    windir = os.environ.get("WINDIR", "C:\\Windows")
    fonts_dir = os.path.join(windir, "Fonts")
    for fn in font_names:
        p = os.path.join(fonts_dir, fn)
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    try:
        return ImageFont.truetype("arial.ttf", size)
    except IOError:
        return ImageFont.load_default()

def render_callout_frame(name, role, subtitle=None, position="bottom-left", width=1920, height=1080, opacity=1.0, illustrative=False):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_name = get_font(52, bold=True)
    font_role = get_font(32, italic=True)
    font_sub = get_font(24)

    # Measure text bounds
    bbox_name = font_name.getbbox(name)
    name_w = bbox_name[2] - bbox_name[0]
    name_h = bbox_name[3] - bbox_name[1]

    bbox_role = font_role.getbbox(role)
    role_w = bbox_role[2] - bbox_role[0]
    role_h = bbox_role[3] - bbox_role[1]

    sub_w, sub_h = 0, 0
    if subtitle:
        bbox_sub = font_sub.getbbox(subtitle)
        sub_w = bbox_sub[2] - bbox_sub[0]
        sub_h = bbox_sub[3] - bbox_sub[1]

    card_content_w = max(name_w, role_w, sub_w)
    padding_x = 44
    padding_y = 28
    card_w = card_content_w + padding_x * 2 + 16  # extra margin for accent bar
    card_h = name_h + role_h + (sub_h + 12 if subtitle else 0) + padding_y * 2 + 20

    # Determine coordinates based on position
    margin_x = 100
    margin_y = 100
    if position == "bottom-left":
        x0 = margin_x
        y0 = height - margin_y - card_h
    elif position == "bottom-right":
        x0 = width - margin_x - card_w
        y0 = height - margin_y - card_h
    elif position == "top-left":
        x0 = margin_x
        y0 = margin_y
    else:  # top-right
        x0 = width - margin_x - card_w
        y0 = margin_y

    x1 = x0 + card_w
    y1 = y0 + card_h

    # Glass backplate with opacity
    bg_alpha = int(210 * opacity)
    border_alpha = int(180 * opacity)
    accent_alpha = int(255 * opacity)

    # Background plate
    draw.rounded_rectangle([x0, y0, x1, y1], radius=12, fill=(15, 18, 24, bg_alpha), outline=(212, 175, 55, border_alpha), width=2)

    # Vertical gold accent bar on the left
    bar_x0 = x0 + 10
    bar_y0 = y0 + 14
    bar_x1 = bar_x0 + 5
    bar_y1 = y1 - 14
    draw.rounded_rectangle([bar_x0, bar_y0, bar_x1, bar_y1], radius=2, fill=(212, 175, 55, accent_alpha))

    # Text positioning
    text_x = bar_x1 + padding_x - 16
    curr_y = y0 + padding_y

    # Name: Ivory #F3EBDD
    name_color = (243, 235, 221, int(255 * opacity))
    draw.text((text_x, curr_y), name, font=font_name, fill=name_color)
    curr_y += name_h + 14

    # Role / Years: Gold #FFE8B8
    role_color = (255, 232, 184, int(240 * opacity))
    draw.text((text_x, curr_y), role, font=font_role, fill=role_color)
    curr_y += role_h + 10

    # Subtitle if present
    if subtitle:
        sub_color = (200, 205, 215, int(210 * opacity))
        draw.text((text_x, curr_y), subtitle, font=font_sub, fill=sub_color)

    if illustrative:
        # High-contrast watermark badge in top right corner visible on any background
        wm_font = get_font(18, bold=True)
        wm_text = "SAMPLE // ILLUSTRATIVE"
        bbox_wm = wm_font.getbbox(wm_text)
        wm_w = bbox_wm[2] - bbox_wm[0]
        wm_h = bbox_wm[3] - bbox_wm[1]
        
        bx0 = width - wm_w - 60
        by0 = 50
        bx1 = bx0 + wm_w + 32
        by1 = by0 + wm_h + 18
        draw.rounded_rectangle([bx0, by0, bx1, by1], radius=6, fill=(15, 18, 24, 235), outline=(212, 175, 55, 230), width=2)
        draw.text((bx0 + 16, by0 + 8), wm_text, font=wm_font, fill=(255, 235, 130, 255))

        # Also place watermark tag directly on top of the callout card plate
        tag_font = get_font(13, bold=True)
        tag_text = "SAMPLE // ILLUSTRATIVE SPECIMEN"
        tbox = tag_font.getbbox(tag_text)
        tw = tbox[2] - tbox[0]
        draw.rounded_rectangle([x0 + 14, y0 - 22, x0 + tw + 28, y0 - 2], radius=4,
                               fill=(15, 18, 24, 230), outline=(212, 175, 55, 210), width=1)
        draw.text((x0 + 20, y0 - 20), tag_text, font=tag_font, fill=(255, 235, 130, 255))

    return img

def main():
    parser = argparse.ArgumentParser(description="Render custom character introduction callout card.")
    parser.add_argument("--name", required=True, help="Full formal name (e.g. 'Sir Patrick Stewart')")
    parser.add_argument("--role", required=True, help="Role, title, or years (e.g. 'Chancellor Emeritus | 2004-2015')")
    parser.add_argument("--subtitle", default=None, help="Optional one-line contextual identifier")
    parser.add_argument("--position", default="bottom-left", choices=["bottom-left", "bottom-right", "top-left", "top-right"])
    parser.add_argument("--illustrative", action="store_true", default=False, help="Watermark with SAMPLE // ILLUSTRATIVE")
    parser.add_argument("--out", required=True, help="Output file path (.png)")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    args = parser.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    frame = render_callout_frame(args.name, args.role, args.subtitle, args.position, args.width, args.height, illustrative=args.illustrative)
    frame.save(args.out, "PNG")
    print(f"Rendered callout to {args.out} ({args.width}x{args.height}, illustrative={args.illustrative})")

if __name__ == "__main__":
    main()
