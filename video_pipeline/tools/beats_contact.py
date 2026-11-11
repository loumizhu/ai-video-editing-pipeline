"""Contact sheets of a beat plan: the real frame each beat will show (video: middle of its window), labelled
with the beat id and the words spoken, so a reviewer can judge picture-vs-words at a glance.

    python beats_contact.py --beats beats.json --assign assignments.json --out sheet_prefix [--per 20]
"""
import argparse, json, os, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont


def frame(x, b, tmp):
    out = os.path.join(tmp, b["id"] + ".jpg")
    if x.get("kind") == "video":
        t = float(x.get("src_in") or 0) + b["dur"] / 2
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", x["file"], "-frames:v", "1", "-vf", "scale=480:270", out])
    else:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", x["file"], "-vf", "scale=480:270", out])
    return out if os.path.exists(out) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--beats", required=True); ap.add_argument("--assign", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--per", type=int, default=20)
    a = ap.parse_args()
    beats = {b["id"]: b for b in json.load(open(a.beats, encoding="utf-8"))}
    asg = json.load(open(a.assign, encoding="utf-8"))
    tmp = tempfile.mkdtemp()
    try:
        font = ImageFont.truetype("arial.ttf", 15)
    except Exception:
        font = ImageFont.load_default()
    for k in range(0, len(asg), a.per):
        part = asg[k:k + a.per]
        cols = 4; rows = (len(part) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 480, rows * 340), (20, 20, 24))
        d = ImageDraw.Draw(sheet)
        for i, x in enumerate(part):
            b = beats[x["beat"]]
            f = frame(x, b, tmp)
            ox, oy = (i % cols) * 480, (i // cols) * 340
            if f:
                sheet.paste(Image.open(f).convert("RGB").resize((480, 270)), (ox, oy))
            tag = f"{b['id']} {'VID' if x.get('kind') == 'video' else 'IMG'} {os.path.basename(x['file'])[:28]}"
            d.text((ox + 4, oy + 272), tag, fill=(255, 210, 90), font=font)
            words = b["text"]
            d.text((ox + 4, oy + 292), words[:62], fill=(230, 230, 230), font=font)
            d.text((ox + 4, oy + 312), words[62:124], fill=(230, 230, 230), font=font)
        p = f"{a.out}_{k // a.per + 1}.jpg"
        sheet.save(p, quality=85)
        print(p)


if __name__ == "__main__":
    main()
