"""One renderer for every title/overlay family (v1 template families and v2 project families).

  python render_family.py --family stat-counter --values v.json --out graphics/S11_stat_counter.mov [--frame-at 0.6]
  python render_family.py --list

v2 families: build an editable .ecproj (kept in <out dir>/_ecproj/) -> ProRes 4444 RGBA .mov + transparent .png still.
v1 families (lower-third, chapter-card, keyword-pop, quote-pullout): delegates to <family>/render.ps1 (never -UpdateTemplate).
Prints one JSON line: {"family", "mov", "png", "ecproj", "duration", "box"}.
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _common as C  # noqa: E402
import _families_v2 as V2  # noqa: E402
import _families_v3  # noqa: E402,F401  (registers v3 families into V2.BUILDERS)

V1 = ["lower-third", "chapter-card", "keyword-pop", "quote-pullout"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--family")
    ap.add_argument("--values")
    ap.add_argument("--out")
    ap.add_argument("--style", default=os.path.join(HERE, "style.json"))
    ap.add_argument("--frame-at", type=float, default=0.75, help="still frame position as a fraction of duration (v2)")
    ap.add_argument("--no-mov", action="store_true", help="v2: build project + still only")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        print(json.dumps({"v1_template_families": V1, "v2_project_families": sorted(V2.BUILDERS)}, indent=2))
        return
    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    png = os.path.splitext(out)[0] + ".png"
    if a.family in V1:
        ps = os.path.join(HERE, a.family, "render.ps1")
        subprocess.run(["powershell", "-NoProfile", "-File", ps, "-Values", os.path.abspath(a.values), "-Out", out], check=True)
        print(json.dumps({"family": a.family, "mov": out, "png": png}))
        return
    if a.family not in V2.BUILDERS:
        raise SystemExit(f"unknown family {a.family}; use --list")
    style = C.load_style(a.style)
    with open(a.values, "r", encoding="utf-8") as f:
        values = json.load(f)
    proj_dir = os.path.join(os.path.dirname(out), "_ecproj")
    slot = os.path.splitext(os.path.basename(out))[0]
    jsx, total, box = V2.BUILDERS[a.family](style, values)
    proj = V2.save_project(style, jsx, proj_dir, slot)
    cli = style["toolchain"]["effectcraft_cli"]
    if not a.no_mov:
        subprocess.run([cli, "--project", proj, "render", "--out", out, "--format", "prores", "--prores", "4444",
                        "--channels", "rgba"], check=True, capture_output=True)
    subprocess.run([cli, "--project", proj, "render-frame", "--time", str(round(total * a.frame_at, 3)), "--out", png,
                    "--transparent"], check=True, capture_output=True)
    print(json.dumps({"family": a.family, "mov": out if not a.no_mov else None, "png": png, "ecproj": proj,
                      "duration": round(total, 3), "box": [round(x, 1) for x in list(box.values())[0]]}))


if __name__ == "__main__":
    main()
