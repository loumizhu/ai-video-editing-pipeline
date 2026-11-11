# article-highlight

**What:** Paper clipping on a tilted, slowly pushing card: outlet, meta line, verbatim body, marker sweep across the exact Highlight substring, footer.

**When to use:** Showing the source text of a quote. Body must be verbatim; no invented headlines; footer says it is typeset.

**Numbers:** `style.json` -> `layout.article_highlight`.

**Render:** `python render_family.py --family article-highlight --values v.json --out graphics/<slot>_article_highlight.mov`. Builder: `_families_v3.py::build_article_highlight`. Tested 2026-11-07 on video 19 in FilmCraft (`19_Graphics_Showcase_2.fcproj`).
