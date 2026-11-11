"""House graphics as NATIVE FilmCraft graphics (live text + shape layers), fully editable in FilmCraft.

Every family builds one Graphic clip: text layers keep their text/font/size/colour editable, plates are shape layers
PINNED to the text they back (edit the text -> the plate resizes), animation is layer keyframes (opacity / position /
scale) inside the clip's Responsive intro/outro, so trimming a clip keeps its in/out moves.
Portrait panels use real image clips (crop + motion) on their own tracks.

    from fc_native_gfx import build_graphic
    build_graphic(sess, family, values, t_seconds, dur_seconds, track_index, extra_tracks=[...])
"""
from fc_session import FCSession  # noqa: F401  (re-export for callers)

FPS = 24000 / 1001
TPF = 10594584000
IVORY, GOLD, ACC, CHAR, RED, SLATE = "#F3EBDD", "#FFE8B8", "#D4AF37", "#0F1218", "#C9473D", "#9AA0A8"
SERIF, BODY, LABEL, MONO = ("DM Serif Display", "Regular"), ("Spectral", "Medium"), ("Barlow Condensed", "SemiBold"), ("Courier Prime", "Bold")
ITAL, QUOTE, NUM = ("Spectral", "Medium Italic"), ("Spectral", "SemiBold"), ("Barlow Condensed", "ExtraBold")


def tk(sec):
    return int(round(sec * FPS)) * TPF


class G:
    """One native Graphic clip under construction."""

    def __init__(self, s, t, dur, track):
        self.s, self.t, self.dur, self.track, self.clip = s, t, dur, track, None
        self.layers = []  # indices in creation order (shift after arrange; use names)

    def _new(self, cmd, p):
        if self.clip is None:
            p.update({"seconds": self.dur, "track": self.track, "time": tk(self.t)})
        else:
            p["clip"] = self.clip
        r = self.s.run(cmd, p)
        self.clip = r["clip"]
        return r["layer"]

    def text(self, txt, pos, size, font, color, align="left", box=None, tracking=0, caps=False, shadow=True, name=None):
        p = {"text": txt, "position": list(pos), "size": size, "font": font[0], "fontStyle": font[1]}
        if box:
            p["box"] = list(box)
        li = self._new("graphics.newText", p)
        props = {"fill_color": color, "align": align, "tracking": tracking}
        if caps:
            props["caps"] = "all caps"
        if shadow:
            props.update({"shadow": True, "shadow_color": "#000000", "shadow_opacity": 55, "shadow_blur": 18, "shadow_distance": 3, "shadow_angle": 120})
        self.set(li, props)
        if name:
            self.set(li, {"name": name})
        return li

    def shape(self, kind, center, size, fill, opacity=100, stroke=None, radius=0, name=None, shadow=False):
        li = self._new("graphics.newShape", {"shape": kind, "position": list(center), "size": list(size)})
        props = {"fill_color": fill, "opacity": opacity, "corner_radius": radius}
        if fill is None:
            props = {"fill": False, "opacity": opacity}
        if stroke:
            props.update({"stroke": True, "stroke_color": stroke[0], "stroke_width": stroke[1]})
        if shadow:
            props.update({"shadow": True, "shadow_color": "#000000", "shadow_opacity": 60, "shadow_blur": 40, "shadow_distance": 10})
        self.set(li, props)
        if name:
            self.set(li, {"name": name})
        return li

    def set(self, li, props, at=None, kf=False):
        p = {"clip": self.clip, "layer": li, "props": props}
        if at is not None:
            p.update({"time": tk(self.t + at), "keyframe": kf})
        return self.s.run("graphics.set", p)

    def kf(self, li, prop, pairs):
        for off, v in pairs:
            self.s.run("graphics.set", {"clip": self.clip, "layer": li, "props": {prop: v}, "time": tk(self.t + off), "keyframe": True})

    def charstyle(self, li, start, end, style):
        self.s.run("graphics.setCharStyle", {"clip": self.clip, "layer": li, "start": start, "end": end, "style": style})

    def info(self):
        return {l["layer"]: l for l in self.s.run("graphics.list", {"clip": self.clip})["layers"]}

    def bounds(self, *lis):
        inf = self.info()
        xs, ys = [], []
        for li in lis:
            for x, y in inf[li]["quad"]:
                xs.append(x); ys.append(y)
        return min(xs), min(ys), max(xs), max(ys)

    def plate_behind(self, lis, pad=(36, 24), fill=CHAR, opacity=82, stroke=(ACC, 2), pin_to=None, radius=0, shadow=False):
        """Plate sized to the union of `lis` + pad, sent to back, pinned to `pin_to` (default the widest layer).
        Returns the new index map {old_index: new_index} because sending to back shifts indices by one."""
        x0, y0, x1, y1 = self.bounds(*lis)
        x0, y0, x1, y1 = x0 - pad[0], y0 - pad[1], x1 + pad[0], y1 + pad[1]
        li = self.shape("rectangle", ((x0 + x1) / 2, (y0 + y1) / 2), (x1 - x0, y1 - y0), fill, opacity, stroke, radius, name="Plate", shadow=shadow)
        self.s.run("graphics.arrangeLayer", {"clip": self.clip, "layer": li, "to": "back"})
        shift = {k: k + 1 for k in range(li)}
        if pin_to is None:
            inf = self.info()
            pin_to = max(lis, key=lambda k: inf[shift[k]]["quad"][2][0] - inf[shift[k]]["quad"][0][0])
        self.s.run("graphics.pin", {"clip": self.clip, "layer": 0, "to": shift[pin_to], "edges": "all"})
        return shift

    def fade(self, lis, fin=0.45, fout=0.35, rise=0, delay=None):
        delay = delay or {}
        inf = self.info()
        for li in lis:
            d = delay.get(li, 0.0)
            self.kf(li, "opacity", [(d, 0), (d + fin, inf[li].get("opacity", 100) if False else 100), (self.dur - fout, 100), (self.dur - 0.02, 0)])
            if rise:
                x, y = inf[li]["position"]
                self.kf(li, "position", [(d, [x, y + rise]), (d + fin + 0.1, [x, y])])

    def responsive(self, intro=0.8, outro=0.5):
        self.s.run("graphics.setResponsiveTime", {"clip": self.clip, "introSeconds": intro, "outroSeconds": outro})


def _plate_opacity_fade(g, li, top=82, fin=0.4, fout=0.35):
    g.kf(li, "opacity", [(0, 0), (fin, top), (g.dur - fout, top), (g.dur - 0.02, 0)])


# ----------------------------------------------------------------------------------------------- families
def lower_third(g, v):
    n = g.text(v["Name"], (200, 872), 60, SERIF, IVORY, name="Name")
    r = g.text(v["Role"], (202, 930), 44, ITAL, GOLD, name="Role")
    m = g.plate_behind([n, r], pad=(40, 26))
    n, r = m[n], m[r]
    bar = g.shape("rectangle", (166, 900), (5, 120), ACC, name="Accent bar")
    g.s.run("graphics.pin", {"clip": g.clip, "layer": bar, "to": 0, "edges": ["left", "top", "bottom"]})
    _plate_opacity_fade(g, 0)
    g.fade([n, r, bar], rise=14, delay={r: 0.15})
    g.responsive()


def location_stamp(g, v):
    a = g.text(v["Place"].upper(), (200, 930), 52, MONO, IVORY, tracking=40, name="Place")
    b = g.text(v["Date"], (202, 985), 44, MONO, GOLD, name="Date")
    m = g.plate_behind([a, b], pad=(26, 20), opacity=72, stroke=None)
    a, b = m[a], m[b]
    rule = g.shape("rectangle", (270, 860), (140, 3), RED, name="Rule")
    _plate_opacity_fade(g, 0, 72)
    g.fade([a, b, rule], delay={b: 0.3})
    g.kf(rule, "scale_width", [(0, 0), (0.45, 100)])
    g.responsive(1.0, 0.5)


def keyword_pop(g, v):
    k = g.text(v["Keyword"], (960, 540), 130, SERIF, IVORY, align="center", name="Keyword")
    g.set(k, {"shadow_blur": 40, "shadow_opacity": 90, "stroke": True, "stroke_color": CHAR, "stroke_width": 5, "stroke_type": "outer"})
    g.kf(k, "scale", [(0, 30), (0.5, 100), (g.dur - 0.42, 100), (g.dur - 0.02, 85)])
    g.fade([k], fin=0.3, fout=0.4)
    g.responsive(0.6, 0.45)


def chapter_card(g, v):
    c = g.text(v["Chapter"], (960, 480), 54, LABEL, GOLD, align="center", tracking=200, name="Chapter")
    t = g.text(v["Title"], (960, 600), 68, SERIF, IVORY, align="center", name="Title")
    m = g.plate_behind([c, t], pad=(96, 56), opacity=72, stroke=None, pin_to=t)
    c, t = m[c], m[t]
    hl = g.shape("rectangle", (960, 522), (160, 3), ACC, name="Hairline")
    _plate_opacity_fade(g, 0, 72, 0.6, 0.6)
    g.fade([c, hl, t], fin=0.6, fout=0.6, rise=10, delay={hl: 0.2, t: 0.35})
    g.kf(hl, "scale_width", [(0.2, 0), (0.8, 100)])
    g.responsive(1.2, 0.7)


def quote_pullout(g, v):
    body = v["Quote"] + "\n— " + v["Attribution"].upper()
    q = g.text(body, (410, 380), 46, QUOTE, IVORY, box=(1100, 420), name="Quote + attribution")
    g.set(q, {"leading": 14})
    g.charstyle(q, len(v["Quote"]) + 1, len(body), {"font": LABEL[0], "fontStyle": LABEL[1], "size": 40, "color": GOLD, "tracking": 120})
    m = g.plate_behind([q], pad=(70, 46), pin_to=q)
    q = m[q]
    _plate_opacity_fade(g, 0)
    g.fade([q], fin=0.6, rise=12)
    g.responsive(1.0, 0.5)


def kinetic_quote(g, v):
    scrim = g.shape("rectangle", (960, 540), (1920, 1080), CHAR, 68, name="Scrim")
    mark = g.text("“", (300, 400), 200, SERIF, ACC, name="Quote mark")
    body = v["Quote"] + "\n\u2014 " + v["Attribution"].upper()
    q = g.text(body, (330, 380), 76, QUOTE, IVORY, box=(1300, 520), name="Quote + attribution")
    emph = v.get("Emphasis") or ""
    i = v["Quote"].find(emph) if emph else -1
    if i >= 0:
        g.charstyle(q, i, i + len(v["Emphasis"]), {"color": GOLD})
    g.charstyle(q, len(v["Quote"]) + 1, len(body), {"font": LABEL[0], "fontStyle": LABEL[1], "size": 40, "color": GOLD, "tracking": 150})
    a = None
    g.kf(scrim, "opacity", [(0, 0), (0.4, 68), (g.dur - 0.4, 68), (g.dur - 0.02, 0)])
    g.fade([mark, q], fin=0.7, rise=14, delay={q: 0.25})
    g.responsive(1.6, 0.5)


def reconstruction_tag(g, v):
    t = g.text(v["Label"], (214, 150), 30, LABEL, IVORY, tracking=140, shadow=False, name="Label")
    m = g.plate_behind([t], pad=(26, 16), opacity=82, stroke=None, pin_to=t)
    t = m[t]
    dot = g.shape("ellipse", (190, 139), (16, 16), RED, name="Dot")
    _plate_opacity_fade(g, 0)
    g.fade([t], fin=0.4)
    pairs, x = [(0, 0), (0.4, 100)], 0.4
    while x + 1.6 < g.dur - 0.5:
        pairs += [(x + 0.8, 55), (x + 1.6, 100)]
        x += 1.6
    pairs += [(g.dur - 0.35, 100), (g.dur - 0.02, 0)]
    g.kf(dot, "opacity", pairs)
    g.responsive(0.5, 0.4)


TIERS = {"DOCUMENTED": (ACC, CHAR), "QUOTED": (IVORY, CHAR), "REPORTED": (SLATE, CHAR), "ALLEGED": (RED, IVORY), "RECONSTRUCTION": (RED, IVORY)}


def source_tag(g, v):
    bg, fg = TIERS.get(v["Tier"], (IVORY, CHAR))
    src = g.text(v["Source"], (1760, 985), 40, ITAL, IVORY, align="right", name="Source")
    x0, y0, x1, y1 = g.bounds(src)
    tier = g.text(v["Tier"], (x0 - 34, 980), 30, LABEL, fg, align="right", tracking=100, shadow=False, name="Tier")
    m = g.plate_behind([src, tier], pad=(20, 16), opacity=82, stroke=None, pin_to=src)
    src, tier = m[src], m[tier]
    tx0, ty0, tx1, ty1 = g.bounds(tier)
    chip = g.shape("rectangle", ((tx0 + tx1) / 2, (ty0 + ty1) / 2), (tx1 - tx0 + 28, ty1 - ty0 + 14), bg, name="Tier chip")
    g.s.run("graphics.arrangeLayer", {"clip": g.clip, "layer": chip, "to": 1})
    g.s.run("graphics.pin", {"clip": g.clip, "layer": 1, "to": tier + 1, "edges": "all"})
    _plate_opacity_fade(g, 0)
    g.fade([1, tier + 1, src + 1], rise=0)
    g.responsive(0.6, 0.4)


def story_tracker(g, v):
    items, act, prev = v["Items"], v["Active"], v.get("Previous")
    head = f"{act + 1:02d}/{len(items):02d}   "
    txt = head + "   ".join(x.upper() for x in items)
    t = g.text(txt, (1760, 150), 32, LABEL, SLATE, align="right", tracking=120, shadow=False, name="Tracker")
    g.charstyle(t, 0, len(head), {"color": ACC})
    pos = len(head)
    for k, x in enumerate(items):
        col = IVORY if k == act else (SLATE if prev is None or k != prev else "#C9C2B6")
        st = {"color": col}
        if k == act:
            st["underline"] = True
        g.charstyle(t, pos, pos + len(x), st)
        pos += len(x) + 3
    m = g.plate_behind([t], pad=(28, 18), opacity=82, stroke=None, pin_to=t)
    _plate_opacity_fade(g, 0)
    g.fade([m[t]])
    g.responsive(0.6, 0.4)


def stat_counter(g, v):
    scrim = g.shape("rectangle", (960, 540), (1920, 1080), CHAR, 55, name="Scrim")
    n = g.text(f"{v['To']:,}", (960, 560), 250, NUM, IVORY, align="center", name="Number")
    rule = g.shape("rectangle", (960, 610), (160, 3), ACC, name="Rule")
    lab = g.text(v["Label"].upper(), (960, 690), 56, LABEL, GOLD, align="center", tracking=180, name="Label")
    ctx = g.text(v["Context"], (960, 750), 44, ITAL, IVORY, align="center", name="Context")
    g.kf(scrim, "opacity", [(0, 0), (0.4, 55), (g.dur - 0.35, 55), (g.dur - 0.02, 0)])
    g.kf(n, "scale", [(0, 70), (0.8, 100)])
    g.fade([n, rule, lab, ctx], delay={rule: 0.4, lab: 0.55, ctx: 0.7})
    g.kf(rule, "scale_width", [(0.4, 0), (0.9, 100)])
    g.responsive(1.4, 0.4)


def timeline_strip(g, v):
    ev = v["Events"]
    n = len(ev)
    xs = [960 + (i - (n - 1) / 2) * 540 for i in range(n)]
    line = g.shape("rectangle", (960, 880), (540 * (n - 1) + 40, 3), SLATE, name="Line")
    ys, ls, ds = [], [], []
    for i, e in enumerate(ev):
        ds.append(g.shape("ellipse", (xs[i], 880), (20, 20), RED if i == v.get("Active") else ACC, name=f"Dot {e['Year']}"))
        ys.append(g.text(e["Year"], (xs[i], 850), 60, NUM, GOLD if i != v.get("Active") else IVORY, align="center", name=f"Year {e['Year']}"))
        ls.append(g.text(e["Label"], (xs[i], 945), 36, BODY, IVORY, align="center", name=f"Label {e['Year']}"))
    m = g.plate_behind([line] + ys + ls, pad=(40, 30), opacity=78, stroke=None, pin_to=line)
    _plate_opacity_fade(g, 0, 78)
    g.fade([m[line]])
    for i in range(n):
        g.fade([m[ds[i]], m[ys[i]], m[ls[i]]], delay={m[ds[i]]: 0.3 + i * 0.55, m[ys[i]]: 0.35 + i * 0.55, m[ls[i]]: 0.45 + i * 0.55})
    g.responsive(0.4 + n * 0.6, 0.4)


def then_now(g, v):
    l1 = g.text(v["Then_Label"].upper(), (960, 420), 36, LABEL, SLATE, align="center", tracking=160, name="Then label")
    t1 = g.text(v["Then"], (960, 510), 84, SERIF, IVORY, align="center", name="Then")
    l2 = g.text(v["Now_Label"].upper(), (960, 610), 36, LABEL, GOLD, align="center", tracking=160, name="Now label")
    t2 = g.text(v["Now"], (960, 700), 84, SERIF, IVORY, align="center", name="Now")
    m = g.plate_behind([l1, t1, l2, t2], pad=(90, 52), pin_to=t2)
    l1, t1, l2, t2 = m[l1], m[t1], m[l2], m[t2]
    x0, y0, x1, y1 = g.bounds(t1)
    strike = g.shape("rectangle", ((x0 + x1) / 2, (y0 + y1) / 2 + 8), (x1 - x0 + 20, 6), RED, name="Strike")
    _plate_opacity_fade(g, 0)
    g.fade([l1, t1], rise=10)
    g.kf(t1, "opacity", [(1.2, 100), (1.5, 62)])
    g.fade([strike], delay={strike: 1.2}, fin=0.05)
    g.kf(strike, "scale_width", [(1.2, 0), (1.6, 100)])
    g.fade([l2, t2], rise=10, delay={l2: 1.55, t2: 1.7})
    g.responsive(2.4, 0.4)


def credit_line(g, v):
    bg = g.shape("rectangle", (960, 540), (1920, 1080), "#000000", 88, name="Backdrop")
    ti = g.text(v["Title"].upper(), (960, 470), 34, LABEL, SLATE, align="center", tracking=260, shadow=False, name="Title")
    ro = g.text(v["Role"], (930, 575), 52, ITAL, GOLD, align="right", shadow=False, name="Role")
    nm = g.text(v["Name"].upper(), (990, 575), 56, SERIF, IVORY, align="left", tracking=80, shadow=False, name="Name")
    g.kf(bg, "opacity", [(0, 0), (0.4, 88), (g.dur - 0.4, 88), (g.dur - 0.02, 0)])
    g.fade([ti, ro, nm], delay={ti: 0.3, ro: 0.6, nm: 0.75}, fin=0.6)
    g.responsive(1.4, 0.5)


def article_highlight(g, v):
    paper = g.shape("rectangle", (960, 540), (1180, 640), IVORY, name="Paper", shadow=True)
    ms = g.text(v["Outlet"], (440, 330), 52, SERIF, CHAR, shadow=False, name="Masthead")
    me = g.text(v["Meta"].upper(), (442, 380), 30, LABEL, "#5A606B", tracking=80, shadow=False, name="Meta")
    rule = g.shape("rectangle", (960, 405), (1080, 2), CHAR, name="Rule")
    hi = v["Highlight"]
    pre = v["Body"].replace(hi, "").strip()
    b1 = g.text(pre, (440, 430), 42, BODY, CHAR, box=(1060, 200), shadow=False, name="Body")
    x0, y0, x1, y1 = g.bounds(b1)
    b2 = g.text(hi, (440, y1 + 22), 42, QUOTE, CHAR, box=(1060, 120), shadow=False, name="Highlighted sentence")
    g.set(b2, {"background": True, "background_color": "#F2C94C", "background_opacity": 85, "background_size": 6})
    ft = g.text(v.get("Footer", ""), (440, 840), 28, ITAL, "#5A606B", shadow=False, name="Footer")
    for li in (paper, ms, me, rule, b1, b2, ft):
        g.set(li, {"rotation": -1.2})
    g.fade([paper, ms, me, rule, b1, ft], fin=0.5)
    g.fade([b2], delay={b2: 1.0})
    g.kf(paper, "position", [(0, [960, 600]), (0.6, [960, 540])])
    g.responsive(1.6, 0.4)


def photo_annotation(g, v):
    cx, cy = v["X"] + v["W"] / 2, v["Y"] + v["H"] / 2
    ring = g.shape("ellipse", (cx, cy), (v["W"], v["H"]), None, stroke=(GOLD, 7), name="Ring")
    g.set(ring, {"shadow": True, "shadow_opacity": 80, "shadow_blur": 12, "shadow_distance": 2})
    lx = v["X"] - v.get("Length", 50)
    lead = g.shape("rectangle", (lx + v.get("Length", 50) / 2, cy), (v.get("Length", 50), 3), GOLD, name="Leader")
    lab = g.text(v["Label"].upper(), (lx - 20, cy - 4), 44, LABEL, IVORY, align="right", tracking=60, name="Label")
    sub = g.text(v.get("Sub", ""), (lx - 20, cy + 40), 36, ITAL, GOLD, align="right", name="Sub")
    m = g.plate_behind([lab, sub], pad=(22, 14), stroke=None, pin_to=lab)
    _plate_opacity_fade(g, 0)
    g.fade([m[ring]], fin=0.35)
    g.kf(m[ring], "scale", [(0, 130), (0.45, 100)])
    g.fade([m[lead], m[lab], m[sub]], delay={m[lead]: 0.35, m[lab]: 0.45, m[sub]: 0.6})
    g.responsive(1.2, 0.4)


def group_legend(g, v):
    hd = g.text("IN THIS PHOTO", (200, 900), 32, LABEL, ACC, tracking=180, shadow=False, name="Heading")
    nm = g.text("  ·  ".join(v["Names"]), (200, 960), 44, SERIF, IVORY, name="Names")
    cp = g.text(v.get("Caption", ""), (200, 1005), 30, ITAL, SLATE, shadow=False, name="Caption")
    m = g.plate_behind([hd, nm, cp], pad=(40, 24), opacity=82, stroke=None, pin_to=nm)
    _plate_opacity_fade(g, 0)
    g.fade([m[hd], m[nm], m[cp]], rise=10, delay={m[nm]: 0.2, m[cp]: 0.4})
    g.responsive(1.0, 0.4)


def people_panel(g, v, portrait_place=None):
    """Backdrop + title + names on the graphic; portraits are real image clips placed by `portrait_place(i, path, center, size)`."""
    bg = g.shape("rectangle", (960, 540), (1920, 1080), CHAR, 96, name="Backdrop")
    ti = g.text(v["Title"].upper(), (960, 150), 40, LABEL, ACC, align="center", tracking=220, shadow=False, name="Title")
    n = len(v["Panels"])
    xs = [960 + (i - (n - 1) / 2) * 520 for i in range(n)]
    lis = []
    for i, p in enumerate(v["Panels"]):
        fr = g.shape("rectangle", (xs[i], 500), (452, 532), None, stroke=(ACC, 2), name=f"Frame {i + 1}")
        nm = g.text(p["Name"], (xs[i], 840), 56, SERIF, IVORY, align="center", shadow=False, name=f"Name {i + 1}")
        ro = g.text(p["Role"].upper(), (xs[i], 895), 34, LABEL, GOLD, align="center", tracking=120, shadow=False, name=f"Role {i + 1}")
        lis.append((fr, nm, ro))
        if portrait_place:
            portrait_place(i, p["Image"], (xs[i], 500), (440, 520))
    g.kf(bg, "opacity", [(0, 0), (0.4, 96), (g.dur - 0.4, 96), (g.dur - 0.02, 0)])
    g.fade([ti], fin=0.5)
    for i, (fr, nm, ro) in enumerate(lis):
        g.fade([fr, nm, ro], rise=10, delay={fr: 0.3 + i * 0.3, nm: 0.4 + i * 0.3, ro: 0.5 + i * 0.3})
    g.responsive(1.5, 0.4)


FAMILIES = {"lower-third": lower_third, "location-stamp": location_stamp, "keyword-pop": keyword_pop, "chapter-card": chapter_card,
            "quote-pullout": quote_pullout, "kinetic-quote": kinetic_quote, "reconstruction-tag": reconstruction_tag,
            "source-tag": source_tag, "story-tracker": story_tracker, "stat-counter": stat_counter, "timeline-strip": timeline_strip,
            "then-now": then_now, "credit-line": credit_line, "article-highlight": article_highlight,
            "photo-annotation": photo_annotation, "group-legend": group_legend, "people-panel": people_panel}

DEFAULT_DUR = {"lower-third": 4.7, "location-stamp": 6.0, "keyword-pop": 3.4, "chapter-card": 5.2, "quote-pullout": 6.2, "kinetic-quote": 6.8,
               "reconstruction-tag": 6.2, "source-tag": 5.2, "story-tracker": 4.5, "stat-counter": 5.0, "timeline-strip": 6.0, "then-now": 6.1,
               "credit-line": 5.2, "article-highlight": 5.7, "photo-annotation": 5.5, "group-legend": 7.1, "people-panel": 6.3}


def build_graphic(s, family, values, t, dur, track, portrait_place=None):
    g = G(s, t, dur, track)
    if family == "people-panel":
        people_panel(g, values, portrait_place)
    else:
        FAMILIES[family](g, values)
    s.run("clip.rename", {"clip": g.clip, "name": f"{family}: " + str(values.get("Name") or values.get("Title") or values.get("Quote")
                                                                         or values.get("Place") or values.get("Keyword") or values.get("Label")
                                                                         or values.get("Source") or values.get("Then") or values.get("Outlet") or "")[:60]})
    return g.clip
