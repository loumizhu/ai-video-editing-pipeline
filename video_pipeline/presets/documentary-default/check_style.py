"""Dead-key detector. Runs every consumer of style.json in dry mode with an access-tracking dict and lists leaf keys nobody read.

Consumers: 4 graphic builders (documentary), shorts-vertical builder (merged style), grade/build_grade.py (fcpreset + cube settings),
sfx/sfx_tool.py spec check. Exit 1 if any leaf key is unread (a silent trap: editing it would change nothing).

  python check_style.py [--style style.json]
"""
import argparse
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "grade"))
sys.path.insert(0, os.path.join(HERE, "sfx"))
import _common as C  # noqa: E402


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", default=os.path.join(HERE, "style.json"))
    a = ap.parse_args()
    raw = json.load(open(a.style, encoding="utf-8"))
    leaves = {p for p in C.leaf_paths(raw) if p.split(".")[0] not in C.META_KEYS}
    seen = set()
    import tempfile

    tmp = tempfile.mkdtemp(prefix="zz_test_check_style_")
    for fam in ("lower-third", "chapter-card", "quote-pullout", "keyword-pop"):
        st = C.load_style(a.style, track=True)
        mod = load(os.path.join(HERE, fam, "build.py"), fam.replace("-", "_"))
        values = C.read_values(os.path.join(HERE, fam, fam + ".json.example"), {})
        mod.build(st, values, tmp, None, dry=True)
        seen |= st.seen
    import build_grade as G
    import sfx_tool as S
    st = C.load_style(a.style, track=True)
    G.build_fcpreset(st)
    G.cube_settings(st)
    S.spec_problems(st, json.load(open(os.path.join(HERE, "sfx.json"), encoding="utf-8")))
    seen |= st.seen
    # the shorts variant reads the same keys through its merged style; its own override file must not carry unread keys either
    sh = os.path.join(HERE, "..", "shorts-vertical", "style.json")
    sh_raw = json.load(open(sh, encoding="utf-8"))
    sh_leaves = {p for p in C.leaf_paths(sh_raw) if p.split(".")[0] not in C.META_KEYS}
    sst = C.load_style(sh, track=True)
    sb = load(os.path.join(HERE, "..", "shorts-vertical", "build.py"), "shorts_build")
    sb.build(sst, C.read_values(os.path.join(HERE, "keyword-pop", "keyword-pop.json.example"), {}), tmp, None, dry=True)
    sh_dead = sorted(sh_leaves - sst.seen)
    dead = sorted(leaves - seen)
    print(f"style.json leaf keys: {len(leaves)}, read by a consumer: {len(leaves & seen)}, unread: {len(dead)}")
    for d in dead:
        print("  UNREAD", d)
    print(f"shorts-vertical/style.json override leaf keys: {len(sh_leaves)}, unread: {len(sh_dead)}")
    for d in sh_dead:
        print("  UNREAD", d)
    import shutil

    shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(1 if dead or sh_dead else 0)


if __name__ == "__main__":
    main()
