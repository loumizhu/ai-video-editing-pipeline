#!/usr/bin/env python3
"""render_article.py - Custom Article Display & Precise Text Highlighting Renderer
Generates documentary-grade article/press clipping cards with mathematically exact substring highlights
(marker sweep, bounding box, underline, dim-rest), optional redaction bars, and animated frame sweeps.
Zero FilmCraft default presets.
"""

import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def get_font(size, bold=False, italic=False, serif=True):
    """Loads system fonts or fallback."""
    font_names = []
    if serif:
        if bold and italic:
            font_names = ["georgiaz.ttf", "timesbi.ttf"]
        elif bold:
            font_names = ["georgiab.ttf", "timesbd.ttf"]
        elif italic:
            font_names = ["georgiai.ttf", "timesi.ttf"]
        else:
            font_names = ["georgia.ttf", "times.ttf"]
    else:
        if bold and italic:
            font_names = ["arialbi.ttf", "segoeuiz.ttf"]
        elif bold:
            font_names = ["arialbd.ttf", "segoeuib.ttf"]
        elif italic:
            font_names = ["ariali.ttf", "segoeuii.ttf"]
        else:
            font_names = ["arial.ttf", "segoeui.ttf"]

    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except IOError:
            continue
    try:
        return ImageFont.truetype("arial.ttf", size)
    except IOError:
        return ImageFont.load_default()

def wrap_text_with_spans(text, font, max_width):
    """Wraps text into lines while tracking exact (start_char, end_char) slice indices."""
    words = text.split(' ')
    lines = []
    curr_words = []
    curr_start = 0
    pos = 0

    for w in words:
        cand = " ".join(curr_words + [w]) if curr_words else w
        w_len = font.getlength(cand)
        if w_len <= max_width:
            curr_words.append(w)
        else:
            if curr_words:
                line_str = " ".join(curr_words)
                lines.append({
                    "text": line_str,
                    "start": curr_start,
                    "end": curr_start + len(line_str)
                })
                curr_start += len(line_str) + 1  # account for space
            curr_words = [w]

    if curr_words:
        line_str = " ".join(curr_words)
        lines.append({
            "text": line_str,
            "start": curr_start,
            "end": curr_start + len(line_str)
        })

    return lines

def render_article_display(headline, outlet, date, body, highlight_text,
                           style="marker", redact_text=None, source_attribution=None,
                           highlight_progress=1.0, illustrative=False, out_path="article.png",
                           width=1920, height=1080):
    """Renders article plate with exact character substring highlight and redaction."""
    # Base cinematic background
    img = Image.new("RGBA", (width, height), (13, 17, 23, 255))
    draw = ImageDraw.Draw(img)

    # Validate target highlight text
    if highlight_text and highlight_text not in body:
        raise ValueError(f"Highlight target substring '{highlight_text}' not found in body text.")

    # Dimensions of paper plate
    paper_w = 1320
    paper_h = 780
    px0 = (width - paper_w) // 2
    py0 = (height - paper_h) // 2 + 10
    px1 = px0 + paper_w
    py1 = py0 + paper_h

    # Drop shadow
    shadow_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow_img)
    sdraw.rounded_rectangle([px0 - 15, py0 - 10, px1 + 15, py1 + 25], radius=16, fill=(0, 0, 0, 180))
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(16))
    img.paste(shadow_img, (0, 0), shadow_img)
    draw = ImageDraw.Draw(img)

    # Archival paper background
    draw.rounded_rectangle([px0, py0, px1, py1], radius=8, fill=(245, 242, 235, 255), outline=(190, 185, 170, 255), width=2)

    # Fonts
    font_outlet = get_font(34, bold=True, serif=True)
    font_date = get_font(20, italic=True, serif=False)
    font_head = get_font(40, bold=True, serif=True)
    font_body = get_font(24, serif=True)
    font_attr = get_font(18, serif=False)

    margin_x = 70
    curr_y = py0 + 40
    max_text_w = paper_w - margin_x * 2

    # Masthead Header: Outlet & Date
    draw.text((px0 + margin_x, curr_y), outlet.upper(), font=font_outlet, fill=(25, 30, 40, 255))
    date_w = font_date.getlength(date)
    draw.text((px1 - margin_x - date_w, curr_y + 10), date, font=font_date, fill=(90, 95, 105, 255))
    curr_y += 52

    # Divider rule
    draw.line([px0 + margin_x, curr_y, px1 - margin_x, curr_y], fill=(180, 175, 160, 255), width=2)
    curr_y += 24

    # Headline wrapping
    head_lines = wrap_text_with_spans(headline, font_head, max_text_w)
    for hl in head_lines:
        draw.text((px0 + margin_x, curr_y), hl["text"], font=font_head, fill=(15, 20, 28, 255))
        curr_y += 48
    curr_y += 12

    # Gold accent divider
    draw.line([px0 + margin_x, curr_y, px0 + margin_x + 180, curr_y], fill=(212, 175, 55, 255), width=3)
    curr_y += 32

    # Wrap body lines and track exact character spans
    wrapped_lines = wrap_text_with_spans(body, font_body, max_text_w)
    
    # Calculate highlight span [hl_start, hl_end]
    hl_start = body.find(highlight_text) if highlight_text else -1
    hl_end = hl_start + len(highlight_text) if hl_start != -1 else -1

    # Calculate redaction span [rd_start, rd_end]
    rd_start = body.find(redact_text) if redact_text else -1
    rd_end = rd_start + len(redact_text) if rd_start != -1 else -1

    # Total characters in highlight to scale progress
    total_hl_chars = len(highlight_text) if highlight_text else 1
    chars_to_highlight = int(total_hl_chars * max(0.0, min(1.0, highlight_progress)))

    # Track how many characters have been highlighted across earlier lines
    hl_chars_drawn = 0

    # Draw highlights first so text sits cleanly on top
    for line in wrapped_lines:
        line_start = line["start"]
        line_end = line["end"]
        line_str = line["text"]
        line_h = 32

        # Check if line intersects highlight span
        if hl_start != -1 and not (line_end <= hl_start or line_start >= hl_end):
            span_start = max(hl_start, line_start)
            span_end = min(hl_end, line_end)
            
            # How many characters of the highlight fall into this line
            line_hl_len = span_end - span_start
            # Remaining characters allowed by progress
            allowed_on_line = max(0, min(line_hl_len, chars_to_highlight - hl_chars_drawn))
            hl_chars_drawn += line_hl_len

            if allowed_on_line > 0:
                # Text prefix before highlight on this line
                prefix_str = line_str[:span_start - line_start]
                hl_sub_str = line_str[span_start - line_start : span_start - line_start + allowed_on_line]
                
                hx0 = px0 + margin_x + font_body.getlength(prefix_str)
                hw = font_body.getlength(hl_sub_str)
                hx1 = hx0 + hw
                hy0 = curr_y - 3
                hy1 = curr_y + line_h + 3

                if style == "marker":
                    # Semi-transparent yellow highlighter #FFEE55 with soft alpha
                    hl_overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
                    hldraw = ImageDraw.Draw(hl_overlay)
                    hldraw.rounded_rectangle([hx0 - 2, hy0, hx1 + 2, hy1], radius=3, fill=(255, 235, 59, 180))
                    img.paste(hl_overlay, (0, 0), hl_overlay)
                    draw = ImageDraw.Draw(img)
                elif style == "box":
                    draw.rounded_rectangle([hx0 - 3, hy0 - 1, hx1 + 3, hy1 + 1], radius=3, outline=(212, 175, 55, 230), width=2)
                elif style == "underline":
                    draw.line([hx0, hy1, hx1, hy1], fill=(212, 175, 55, 255), width=3)

        curr_y += line_h + 10

    # Now render body text and redactions
    curr_y = py0 + 40 + 52 + 24 + len(head_lines)*48 + 12 + 32
    for line in wrapped_lines:
        line_start = line["start"]
        line_end = line["end"]
        line_str = line["text"]
        line_h = 32

        # Render text
        text_color = (25, 30, 40, 255)
        draw.text((px0 + margin_x, curr_y), line_str, font=font_body, fill=text_color)

        # Check for redaction span
        if rd_start != -1 and not (line_end <= rd_start or line_start >= rd_end):
            r_span_start = max(rd_start, line_start)
            r_span_end = min(rd_end, line_end)
            prefix_str = line_str[:r_span_start - line_start]
            rd_sub_str = line_str[r_span_start - line_start : r_span_end - line_start]
            
            rx0 = px0 + margin_x + font_body.getlength(prefix_str)
            rw = font_body.getlength(rd_sub_str)
            rx1 = rx0 + rw
            ry0 = curr_y - 2
            ry1 = curr_y + line_h + 2
            # Solid black redaction bar
            draw.rectangle([rx0 - 2, ry0, rx1 + 2, ry1], fill=(15, 18, 24, 255))

        curr_y += line_h + 10

    # Source Attribution banner at bottom
    if source_attribution:
        attr_text = f"SOURCE VERIFICATION: {source_attribution}"
        draw.text((px0 + margin_x, py1 - 45), attr_text, font=font_attr, fill=(110, 115, 125, 255))

    # Watermark if illustrative
    if illustrative:
        wm_font = get_font(22, bold=True)
        draw.text((px1 - margin_x - 300, py1 - 45), "SAMPLE // ILLUSTRATIVE", font=wm_font, fill=(180, 50, 50, 200))

    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    img.save(out_path, "PNG")
    print(f"Rendered article display to {out_path} ({width}x{height})")

def main():
    parser = argparse.ArgumentParser(description="Render custom article highlight display.")
    parser.add_argument("--headline", required=True, help="Article headline")
    parser.add_argument("--outlet", required=True, help="Publication/outlet name (e.g. 'The Guardian')")
    parser.add_argument("--date", required=True, help="Publication date string")
    parser.add_argument("--body", required=True, help="Body text passage containing the quote")
    parser.add_argument("--highlight", required=True, help="Exact substring or quote to highlight")
    parser.add_argument("--style", default="marker", choices=["marker", "box", "underline", "dim-rest"])
    parser.add_argument("--redact", default=None, help="Substring to redact with solid black bar")
    parser.add_argument("--progress", type=float, default=1.0, help="Highlight sweep progress (0.0 to 1.0)")
    parser.add_argument("--frames", type=int, default=0, help="If > 0, outputs animated frame sequence to directory")
    parser.add_argument("--illustrative", action="store_true", default=False, help="Watermark with SAMPLE // ILLUSTRATIVE")
    parser.add_argument("--attribution", default=None, help="Archive or URL attribution note")
    parser.add_argument("--out", required=True, help="Output PNG path or directory if frames > 0")
    args = parser.parse_args()

    if args.frames > 0:
        os.makedirs(args.out, exist_ok=True)
        print(f"Rendering {args.frames} animated article highlight frames to {args.out}...")
        for frame_idx in range(args.frames):
            prog = (frame_idx + 1) / args.frames
            frame_path = os.path.join(args.out, f"frame_{frame_idx:04d}.png")
            render_article_display(
                headline=args.headline, outlet=args.outlet, date=args.date,
                body=args.body, highlight_text=args.highlight, style=args.style,
                redact_text=args.redact, source_attribution=args.attribution,
                highlight_progress=prog, illustrative=args.illustrative,
                out_path=frame_path
            )
        print(f"Finished rendering {args.frames} frames.")
    else:
        render_article_display(
            headline=args.headline, outlet=args.outlet, date=args.date,
            body=args.body, highlight_text=args.highlight, style=args.style,
            redact_text=args.redact, source_attribution=args.attribution,
            highlight_progress=args.progress, illustrative=args.illustrative,
            out_path=args.out
        )

if __name__ == "__main__":
    main()
