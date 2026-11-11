#!/usr/bin/env python3
"""render_card.py - Renders custom overlay cards, stamps, numbers, and strips for EDITING_TOOLKIT extras (E1, E2, E5, E8, E9).
Generates broadcast-quality 1920x1080 RGBA PNG overlays (or full-frame cards) with transparent backgrounds.
Zero FilmCraft default presets used. Includes text overlap & bounds self-check and auto-scaling for long strings.
"""

import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont

def get_font(size, bold=False):
    """Loads system font (Georgia, Arial, Trebuchet MS) or fallback."""
    font_names = ["georgiab.ttf" if bold else "georgia.ttf",
                  "arialbd.ttf" if bold else "arial.ttf",
                  "trebucbd.ttf" if bold else "trebuc.ttf"]
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except IOError:
            continue
    try:
        return ImageFont.truetype("arial.ttf", size)
    except IOError:
        return ImageFont.load_default()

def draw_watermark(draw, width, height):
    """Draws subtle illustrative watermark if required."""
    wm_font = get_font(24, bold=True)
    draw.text((width - 340, height - 40), "SAMPLE // ILLUSTRATIVE", font=wm_font, fill=(255, 255, 255, 90))

def check_no_text_overlap(boxes_with_names, bounds=(0, 0, 1920, 1080)):
    """Verifies that none of the text elements overlap each other and all fit within bounds.
    boxes_with_names: list of (name, (x0, y0, x1, y1))
    """
    bx0, by0, bx1, by1 = bounds
    for name, (x0, y0, x1, y1) in boxes_with_names:
        if x0 < bx0 or y0 < by0 or x1 > bx1 or y1 > by1:
            raise ValueError(f"Text bounds violation for '{name}': bbox ({x0},{y0},{x1},{y1}) exceeds bounds {bounds}")

    for i in range(len(boxes_with_names)):
        for j in range(i + 1, len(boxes_with_names)):
            n1, b1 = boxes_with_names[i]
            n2, b2 = boxes_with_names[j]
            overlap_x = max(0, min(b1[2], b2[2]) - max(b1[0], b2[0]))
            overlap_y = max(0, min(b1[3], b2[3]) - max(b1[1], b2[1]))
            if overlap_x > 0 and overlap_y > 0:
                raise ValueError(
                    f"Text overlap detected between '{n1}' and '{n2}': "
                    f"overlap {overlap_x}x{overlap_y} px. "
                    f"Box 1: {b1}, Box 2: {b2}"
                )

def render_stamp(text="CONFIRMED", color="red", illustrative=False):
    """Renders angled document stamp (E2)."""
    img = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
    color_map = {
        "red": ((220, 50, 50, 230), (220, 50, 50, 40)),
        "green": ((40, 180, 80, 230), (40, 180, 80, 40)),
        "amber": ((230, 160, 30, 230), (230, 160, 30, 40))
    }
    fg_col, bg_col = color_map.get(color.lower(), color_map["red"])
    
    stamp_size = 52
    font = get_font(stamp_size, bold=True)
    tb = font.getbbox(text)
    tw = tb[2] - tb[0]
    if tw > 600:
        stamp_size = max(18, int(stamp_size * 600 / tw))
        font = get_font(stamp_size, bold=True)
        tb = font.getbbox(text)
        tw = tb[2] - tb[0]
    th = tb[3] - tb[1]
    
    pad_x, pad_y = 36, 18
    pw = tw + pad_x * 2
    ph = th + pad_y * 2
    
    plate = Image.new('RGBA', (pw + 20, ph + 20), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(plate)
    pdraw.rectangle([10, 10, pw + 10, ph + 10], fill=bg_col, outline=fg_col, width=5)
    pdraw.rectangle([16, 16, pw + 4, ph + 4], outline=fg_col, width=2)
    
    gx = 10 + pad_x
    gy = 10 + pad_y
    pdraw.text((gx - tb[0], gy - tb[1]), text, font=font, fill=fg_col)
    box_t = ("stamp_text", (gx, gy, gx + tw, gy + th))
    
    check_no_text_overlap([box_t], (10, 10, pw + 10, ph + 10))
    
    rotated = plate.rotate(12, resample=Image.BICUBIC, expand=True)
    paste_x = min(1350, 1920 - rotated.width - 40)
    img.paste(rotated, (paste_x, 220), rotated)
    
    draw = ImageDraw.Draw(img)
    if illustrative:
        draw_watermark(draw, 1920, 1080)
    return img

def render_date_strip(date_text="14 MARCH 1974", illustrative=False):
    """Renders sleek timeline date strip (E1)."""
    img = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    date_size = 26
    font = get_font(date_size, bold=True)
    db = font.getbbox(date_text)
    dw = db[2] - db[0]
    if dw > 650:
        date_size = max(14, int(date_size * 650 / dw))
        font = get_font(date_size, bold=True)
        db = font.getbbox(date_text)
        dw = db[2] - db[0]
    dh = db[3] - db[1]

    sub_font = get_font(14, bold=False)
    sub_text = "CHRONOLOGICAL ARCHIVE"
    sb = sub_font.getbbox(sub_text)
    sw = sb[2] - sb[0]
    sh = sb[3] - sb[1]
    
    pad_x = 24
    pad_top = 14
    gap = 8
    pad_bottom = 14
    
    bw = max(dw, sw) + pad_x * 2
    bh = pad_top + dh + gap + sh + pad_bottom
    bx0, by0 = 80, 80
    
    draw.rounded_rectangle([bx0, by0, bx0 + bw, by0 + bh], radius=6, fill=(12, 16, 24, 230), outline=(212, 175, 55, 220), width=1)
    
    gx_d = bx0 + pad_x
    gy_d = by0 + pad_top
    draw.text((gx_d - db[0], gy_d - db[1]), date_text, font=font, fill=(245, 242, 235, 255))
    box_d = ("date", (gx_d, gy_d, gx_d + dw, gy_d + dh))
    
    gx_s = bx0 + pad_x
    gy_s = gy_d + dh + gap
    draw.text((gx_s - sb[0], gy_s - sb[1]), sub_text, font=sub_font, fill=(212, 175, 55, 200))
    box_s = ("sub", (gx_s, gy_s, gx_s + sw, gy_s + sh))
    
    draw.line([bx0 + bw, by0 + bh // 2, bx0 + bw + 60, by0 + bh // 2], fill=(212, 175, 55, 180), width=2)
    draw.ellipse([bx0 + bw + 60 - 4, by0 + bh // 2 - 4, bx0 + bw + 60 + 4, by0 + bh // 2 + 4], fill=(255, 235, 130, 255))
    
    check_no_text_overlap([box_d, box_s], (bx0, by0, bx0 + bw, by0 + bh))
    
    if illustrative:
        draw_watermark(draw, 1920, 1080)
    return img

def render_big_number(number="2,400+", label="STUDENTS CONFERRED", citation="UNIVERSITY ARCHIVE", illustrative=False):
    """Renders scale surprise metric counter card (E5).
    Positions label and citation strictly below glyph bounding boxes to guarantee zero text overlap.
    """
    img = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    num_size = 110
    num_font = get_font(num_size, bold=True)
    nb = num_font.getbbox(number)
    nw = nb[2] - nb[0]
    if nw > 1500:
        num_size = max(30, int(num_size * 1500 / nw))
        num_font = get_font(num_size, bold=True)
        nb = num_font.getbbox(number)
        nw = nb[2] - nb[0]
    nh = nb[3] - nb[1]
    
    lbl_size = 24
    lbl_font = get_font(lbl_size, bold=True)
    lb = lbl_font.getbbox(label)
    lw = lb[2] - lb[0]
    if lw > 1500:
        lbl_size = max(12, int(lbl_size * 1500 / lw))
        lbl_font = get_font(lbl_size, bold=True)
        lb = lbl_font.getbbox(label)
        lw = lb[2] - lb[0]
    lh = lb[3] - lb[1]
    
    cite_size = 14
    cite_font = get_font(cite_size, bold=False)
    cite_text = f"SOURCE: {citation}"
    cb = cite_font.getbbox(cite_text)
    cw = cb[2] - cb[0]
    if cw > 1500:
        cite_size = max(10, int(cite_size * 1500 / cw))
        cite_font = get_font(cite_size, bold=False)
        cb = cite_font.getbbox(cite_text)
        cw = cb[2] - cb[0]
    ch = cb[3] - cb[1]
    
    pad_x = 40
    pad_top = 24
    gap1 = 20
    gap2 = 14
    pad_bottom = 24
    
    content_w = max(nw, lw, cw)
    pw = content_w + pad_x * 2
    ph = pad_top + nh + gap1 + lh + gap2 + ch + pad_bottom
    
    cx0 = 120
    if cx0 + pw > 1920 - 40:
        cx0 = max(40, (1920 - pw) // 2)
    cy0 = min(680, 1080 - ph - 60)
    
    draw.rounded_rectangle([cx0, cy0, cx0 + pw, cy0 + ph], radius=10, fill=(10, 14, 22, 235), outline=(212, 175, 55, 240), width=2)
    
    gx_n = cx0 + pad_x
    gy_n = cy0 + pad_top
    draw.text((gx_n - nb[0], gy_n - nb[1]), number, font=num_font, fill=(255, 235, 130, 255))
    box_n = ("number", (gx_n, gy_n, gx_n + nw, gy_n + nh))
    
    gx_l = cx0 + pad_x
    gy_l = gy_n + nh + gap1
    draw.text((gx_l - lb[0], gy_l - lb[1]), label, font=lbl_font, fill=(245, 242, 235, 255))
    box_l = ("label", (gx_l, gy_l, gx_l + lw, gy_l + lh))
    
    gx_c = cx0 + pad_x
    gy_c = gy_l + lh + gap2
    draw.text((gx_c - cb[0], gy_c - cb[1]), cite_text, font=cite_font, fill=(160, 180, 210, 200))
    box_c = ("citation", (gx_c, gy_c, gx_c + cw, gy_c + ch))
    
    check_no_text_overlap([box_n, box_l, box_c], (cx0, cy0, cx0 + pw, cy0 + ph))
    
    if illustrative:
        draw_watermark(draw, 1920, 1080)
    return img

def render_keyword(word="SOVEREIGNTY", illustrative=False):
    """Renders dramatic single kinetic keyword pop (E8)."""
    img = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    word_size = 72
    font = get_font(word_size, bold=True)
    wb = font.getbbox(word)
    tw = wb[2] - wb[0]
    if tw > 1600:
        word_size = max(20, int(word_size * 1600 / tw))
        font = get_font(word_size, bold=True)
        wb = font.getbbox(word)
        tw = wb[2] - wb[0]
    th = wb[3] - wb[1]
    
    pad_x, pad_y = 40, 20
    cw = tw + pad_x * 2
    ch = th + pad_y * 2
    
    cx0 = (1920 - cw) // 2
    cy0 = (1080 - ch) // 2
    
    draw.rectangle([cx0, cy0, cx0 + cw, cy0 + ch], fill=(15, 18, 24, 235), outline=(212, 175, 55, 220), width=3)
    
    gx_w = cx0 + pad_x
    gy_w = cy0 + pad_y
    draw.text((gx_w - wb[0], gy_w - wb[1]), word, font=font, fill=(255, 240, 140, 255))
    box_w = ("keyword", (gx_w, gy_w, gx_w + tw, gy_w + th))
    
    check_no_text_overlap([box_w], (cx0, cy0, cx0 + cw, cy0 + ch))
    
    if illustrative:
        draw_watermark(draw, 1920, 1080)
    return img

def render_chapter_card(title="CHAPTER 01", subtitle="THE EARLY YEARS", illustrative=False):
    """Renders full-frame or lower chapter transition card (E9)."""
    img = Image.new('RGBA', (1920, 1080), (10, 12, 16, 255))
    draw = ImageDraw.Draw(img)
    
    chap_size = 32
    chap_font = get_font(chap_size, bold=True)
    tb = chap_font.getbbox(title)
    tw = tb[2] - tb[0]
    if tw > 1700:
        chap_size = max(14, int(chap_size * 1700 / tw))
        chap_font = get_font(chap_size, bold=True)
        tb = chap_font.getbbox(title)
        tw = tb[2] - tb[0]
    th = tb[3] - tb[1]
    
    title_size = 68
    title_font = get_font(title_size, bold=True)
    sb = title_font.getbbox(subtitle)
    sw = sb[2] - sb[0]
    if sw > 1700:
        title_size = max(18, int(title_size * 1700 / sw))
        title_font = get_font(title_size, bold=True)
        sb = title_font.getbbox(subtitle)
        sw = sb[2] - sb[0]
    sh = sb[3] - sb[1]
    
    draw.rectangle([60, 60, 1860, 1020], outline=(212, 175, 55, 120), width=2)
    draw.rectangle([70, 70, 1850, 1010], outline=(212, 175, 55, 60), width=1)
    
    gap = 24
    line_gap = 24
    total_h = th + gap + sh + line_gap + 2
    
    gy_t = (1080 - total_h) // 2
    gx_t = (1920 - tw) // 2
    draw.text((gx_t - tb[0], gy_t - tb[1]), title, font=chap_font, fill=(212, 175, 55, 240))
    box_t = ("title", (gx_t, gy_t, gx_t + tw, gy_t + th))
    
    gy_s = gy_t + th + gap
    gx_s = (1920 - sw) // 2
    draw.text((gx_s - sb[0], gy_s - sb[1]), subtitle, font=title_font, fill=(245, 242, 235, 255))
    box_s = ("subtitle", (gx_s, gy_s, gx_s + sw, gy_s + sh))
    
    line_y = gy_s + sh + line_gap
    draw.line([960 - 150, line_y, 960 + 150, line_y], fill=(212, 175, 55, 220), width=2)
    
    check_no_text_overlap([box_t, box_s], (70, 70, 1850, 1010))
    
    if illustrative:
        draw_watermark(draw, 1920, 1080)
    return img

def main():
    parser = argparse.ArgumentParser(description="Render custom cards and overlay elements")
    parser.add_argument('--type', required=True, choices=['stamp', 'date_strip', 'big_number', 'keyword', 'chapter_card'], help="Card type to render")
    parser.add_argument('--text', default=None, help="Primary text")
    parser.add_argument('--date', default=None, help="Date text alias for date_strip")
    parser.add_argument('--word', default=None, help="Word alias for stamp/keyword")
    parser.add_argument('--number', default=None, help="Number alias for big_number")
    parser.add_argument('--title', default=None, help="Title alias for chapter_card")
    parser.add_argument('--subtitle', default="", help="Secondary text/label")
    parser.add_argument('--citation', default="", help="Citation line")
    parser.add_argument('--color', default="red", help="Color theme (red, green, amber)")
    parser.add_argument('--illustrative', action='store_true', default=False, help="Add illustrative watermark")
    parser.add_argument('--out', required=True, help="Output PNG path")
    args = parser.parse_args()

    primary_text = args.text or args.date or args.word or args.number or args.title or "CONFIRMED"

    if args.type == 'stamp':
        img = render_stamp(text=primary_text, color=args.color, illustrative=args.illustrative)
    elif args.type == 'date_strip':
        img = render_date_strip(date_text=primary_text, illustrative=args.illustrative)
    elif args.type == 'big_number':
        lbl = args.subtitle if args.subtitle else "DOCUMENTED RECORD"
        cite = args.citation if args.citation else "HISTORICAL ARCHIVE"
        img = render_big_number(number=primary_text, label=lbl, citation=cite, illustrative=args.illustrative)
    elif args.type == 'keyword':
        img = render_keyword(word=primary_text, illustrative=args.illustrative)
    elif args.type == 'chapter_card':
        sub = args.subtitle if args.subtitle else "SECTION OVERVIEW"
        img = render_chapter_card(title=primary_text, subtitle=sub, illustrative=args.illustrative)

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    img.save(args.out, 'PNG')
    print(f"Rendered {args.type} card to {args.out} (1920x1080)")

if __name__ == '__main__':
    main()
