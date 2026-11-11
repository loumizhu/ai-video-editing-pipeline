"""Graphics testbed: render every title/overlay slot of a plan, lay each over its real footage in a FilmCraft
project, and prove it with FilmCraft-rendered frames + a contact sheet (+ optional preview export).

  python graphics_testbed.py --plan <video>/07_Video_Edit/graphics_test/graphics_test_plan.json [--only S01 S07] [--export]

Plan slot: {"id","family","anchor" (script line),"bg" (file in media_dir or null),"values"} for preset families
(see presets/documentary-default/render_family.py --list) or {"tool": "render_map|render_card|render_callout|render_article", "args": [...]}
for the Pillow still tools.
Outputs (next to the plan): renders/<id>_<family>.mov|.png, renders/_ecproj/*.ecproj (editable), <project>.fcproj,
filmcraft_frames/<id>.png, contact_sheet.png, testbed_report.json [, preview.mp4].
FilmCraft layout: bins 03_B-Roll / 04_Graphics / 07_Sequences; V1 footage, V3 graphics; one green marker per slot.
"""
import argparse
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PRESET = os.path.join(HERE, "..", "presets", "documentary-default")
FC = r"C:\Program Files\FilmCraft\filmcraft-cli.exe"
TPS = 254016000000
TPF = 10594584000  # ticks per frame at 24000/1001
STILL_SECONDS = 4.0
PAD = 0.5


def fc(*args, project=None, save=False):
    cmd = [FC, "--compact"]
    if project:
        cmd += ["--project", project]
    if save:
        cmd += ["--save"]
    r = subprocess.run(cmd + list(args), capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"filmcraft-cli {' '.join(args[:2])} failed: {(r.stderr or r.stdout)[-800:]}")
    return r.stdout


def probe_seconds(path):
    d = json.loads(fc("probe", path))
    v = float(d.get("duration") or d.get("durationSeconds") or 5.0)
    return v / TPS if v > 1e6 else v


def frames(sec):
    return int(round(sec * 24000 / 1001))


def render_slot(slot, rdir):
    os.makedirs(rdir, exist_ok=True)
    base = os.path.join(rdir, f"{slot['id']}_{slot['family']}")
    if slot.get("tool"):
        png = base + ".png"
        subprocess.run([sys.executable, os.path.join(HERE, slot["tool"] + ".py")] + slot["args"] + ["--out", png], check=True,
                       capture_output=True)
        return {"png": png, "mov": None, "duration": STILL_SECONDS}
    vp = os.path.join(rdir, "_values", slot["id"] + ".json")
    os.makedirs(os.path.dirname(vp), exist_ok=True)
    with open(vp, "w", encoding="utf-8") as f:
        json.dump(slot["values"], f, ensure_ascii=False, indent=2)
    r = subprocess.run([sys.executable, os.path.join(PRESET, "render_family.py"), "--family", slot["family"], "--values", vp,
                        "--out", base + ".mov"], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"{slot['id']} {slot['family']} failed: {(r.stderr or r.stdout)[-800:]}")
    info = json.loads([ln for ln in r.stdout.splitlines() if ln.startswith("{")][-1])
    if not info.get("duration"):
        info["duration"] = probe_seconds(base + ".mov")
    info["mov"] = base + ".mov"
    return info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--skip-render", action="store_true", help="reuse renders/")
    ap.add_argument("--export", action="store_true", help="also export preview.mp4 from FilmCraft")
    a = ap.parse_args()
    plan_path = os.path.abspath(a.plan)
    root = os.path.dirname(plan_path)
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)
    media = os.path.normpath(os.path.join(root, plan["media_dir"]))
    rdir = os.path.join(root, plan.get("renders_dir", "renders"))
    slots = [s for s in plan["slots"] if not a.only or s["id"] in a.only]

    # 1. render
    for s in slots:
        if a.skip_render and os.path.exists(os.path.join(rdir, f"{s['id']}_{s['family']}.png")):
            mov = os.path.join(rdir, f"{s['id']}_{s['family']}.mov")
            s["_r"] = {"png": os.path.join(rdir, f"{s['id']}_{s['family']}.png"), "mov": mov if os.path.exists(mov) else None}
            s["_r"]["duration"] = probe_seconds(mov) if s["_r"]["mov"] else STILL_SECONDS
        else:
            s["_r"] = render_slot(s, rdir)
        print(s["id"], s["family"], "rendered", round(float(s["_r"]["duration"]), 2), "s", flush=True)

    # 2. FilmCraft project
    proj = os.path.join(root, plan["project"] + ".fcproj")
    if os.path.exists(proj):
        os.remove(proj)
    subprocess.run([FC, "--save-as", proj, "exec", "file.newProject", json.dumps({"name": plan["project"]})], check=True,
                   capture_output=True)
    files, index = [], {}
    for s in slots:
        for key, path in (("bg", os.path.join(media, s["bg"]) if s.get("bg") else None), ("gfx", s["_r"]["mov"] or s["_r"]["png"])):
            if path and path not in index:
                index[path] = len(files)
                files.append(path)
    out = json.loads(fc("import", *files, project=proj, save=True))
    ids = out["items"]
    if len(ids) != len(files):
        raise SystemExit(f"import returned {len(ids)} ids for {len(files)} files: {out.get('errors')}")
    item = {p: ids[i] for p, i in index.items()}

    lines = [{"id": "file.newSequence", "params": {"name": plan["project"] + "_Seq", "width": 1920, "height": 1080, "fps": 23.976,
                                                    "video": 4, "audio": 4}}]
    for t, n, lab in (("V1", "V1 - Primary / Footage", "Forest"), ("V2", "V2 - B-Roll / Inserts", "Cerulean"),
                      ("V3", "V3 - Graphics / Titles", "Mango"), ("V4", "V4 - Overlays / Grain", "Lavender")):
        lines.append({"id": "timeline.setTrack", "params": {"track": t, "name": n, "label": lab}})
    t_cursor = 0
    report = []
    for s in slots:
        dur_f = frames(float(s["_r"]["duration"]))
        pad_f = frames(PAD)
        slot_f = dur_f + 2 * pad_f
        bg = os.path.join(media, s["bg"]) if s.get("bg") else None
        if bg:
            lines.append({"id": "timeline.place", "params": {"item": item[bg], "track": "V1", "time": t_cursor * TPF, "insert": False,
                                                             "duration": slot_f * TPF, "video": True, "audio": False}})
        g = s["_r"]["mov"] or s["_r"]["png"]
        lines.append({"id": "timeline.place", "params": {"item": item[g], "track": "V3", "time": (t_cursor + pad_f) * TPF,
                                                         "insert": False, "duration": dur_f * TPF, "video": True, "audio": False}})
        lines.append({"id": "markers.add", "params": {"target": "program", "time": (t_cursor + pad_f) * TPF,
                                                      "name": f"{s['id']} {s['family']}", "comment": s.get("anchor", ""),
                                                      "color": "Green"}})
        check_t = (t_cursor + pad_f + int(dur_f * 0.75)) / (24000 / 1001)
        report.append({"id": s["id"], "family": s["family"], "anchor": s.get("anchor"), "start_s": round(t_cursor / (24000 / 1001), 3),
                       "duration_s": round(dur_f / (24000 / 1001), 3), "check_s": round(check_t, 3), "graphic": g, "bg": s.get("bg")})
        t_cursor += slot_f
    jl = os.path.join(root, "_filmcraft_build.jsonl")
    with open(jl, "w", encoding="utf-8") as f:
        f.write("\n".join(json.dumps(x) for x in lines) + "\n")
    fc("run", jl, project=proj, save=True)

    # bins (after the sequence exists so its id is known)
    insp = json.loads(fc("inspect", "project", project=proj))
    seq_ids = [n["id"] for n in insp.get("items", insp.get("project", {}).get("items", [])) if n.get("kind") == "sequence"] if isinstance(insp, dict) else []
    bl = []
    bl.append({"id": "file.newBin", "params": {"name": "03_B-Roll"}})
    bl.append({"id": "file.newBin", "params": {"name": "04_Graphics"}})
    bl.append({"id": "file.newBin", "params": {"name": "07_Sequences"}})
    jb = os.path.join(root, "_filmcraft_bins.jsonl")
    with open(jb, "w", encoding="utf-8") as f:
        f.write("\n".join(json.dumps(x) for x in bl) + "\n")
    res = fc("run", jb, project=proj, save=True)
    bins = [json.loads(ln).get("result", json.loads(ln)).get("bin") for ln in res.splitlines() if ln.strip().startswith("{") and "bin" in ln]
    if len(bins) == 3:
        moves = []
        broll = [item[p] for p in files if not p.startswith(rdir)]
        gfx = [item[p] for p in files if p.startswith(rdir)]
        if broll:
            moves.append({"id": "project.moveToBin", "params": {"items": broll, "bin": bins[0]}})
        if gfx:
            moves.append({"id": "project.moveToBin", "params": {"items": gfx, "bin": bins[1]}})
        if seq_ids:
            moves.append({"id": "project.moveToBin", "params": {"items": seq_ids, "bin": bins[2]}})
        if moves:
            with open(jb, "w", encoding="utf-8") as f:
                f.write("\n".join(json.dumps(x) for x in moves) + "\n")
            fc("run", jb, project=proj, save=True)
    for p in (jl, jb):
        os.remove(p)

    # 3. FilmCraft frames + contact sheet
    fdir = os.path.join(root, "filmcraft_frames")
    os.makedirs(fdir, exist_ok=True)
    cells = []
    font = ImageFont.truetype("arialbd.ttf", 22)
    for r in report:
        png = os.path.join(fdir, f"{r['id']}_{r['family']}.png")
        fc("render", "--seconds", str(r["check_s"]), "--out", png, project=proj)
        r["filmcraft_frame"] = png
        im = Image.open(png).convert("RGB").resize((640, 360))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 640, 30], fill=(0, 0, 0))
        d.text((8, 4), f"{r['id']}  {r['family']}", fill=(255, 214, 90), font=font)
        cells.append(im)
        print(r["id"], "frame ok", flush=True)
    cols = 4
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new("RGB", (640 * cols, 360 * rows), (20, 20, 20))
    for i, c in enumerate(cells):
        sheet.paste(c, ((i % cols) * 640, (i // cols) * 360))
    sheet.save(os.path.join(root, plan.get("sheet_name", "contact_sheet.png")))
    if a.export:
        fc("export", os.path.join(root, plan.get("preview_name", "preview.mp4")), "--format", "h264", "--no-audio", project=proj)
    with open(os.path.join(root, plan.get("report_name", "testbed_report.json")), "w", encoding="utf-8") as f:
        json.dump({"project": proj, "sequence_seconds": round(t_cursor / (24000 / 1001), 2), "slots": report}, f, indent=2)
    print("DONE", proj, round(t_cursor / (24000 / 1001), 1), "s")


if __name__ == "__main__":
    main()
