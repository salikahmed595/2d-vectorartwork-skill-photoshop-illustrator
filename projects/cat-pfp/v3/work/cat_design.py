"""v3 cat PFP - hand-built vector spec for ai_draw.py (no AI generation).

    python cat_design.py            -> writes drawing.json next to this file

Proportions come from landmarks read off a grid of inbox/cat-source.png:
photo -> canvas is X = 1000 + 6.9 (x - 198.5), Y = 960 + 6.9 (y - 71);
head parts are drawn in head-local coords (eye midpoint = 0,0, head upright) and placed with HEAD_TF
(the photo head is tilted 17.5 deg counter-clockwise).
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

DOC = "cat-pfp-drawn.ai"
W = H = 2000
HEAD_TF = {"scale": 1.0, "rotate": -17.5, "translate": [1000, 960]}

INK = "#4a1d07"
CREAM, CREAM_HI = "#fff1d6", "#fff8ea"
STRIPE, STRIPE_DK = "#c2551a", "#8f3a10"
LID = "#2b1206"
SKY = ["#0b1030", "#1b2257", "#3b3474", "#6a4a86"]


# ---------------------------------------------------------------- geometry helpers
def f(v: float) -> str:
    return f"{v:.1f}"


def ell(cx, cy, rx, ry):
    k = 0.5523
    return (f"M {f(cx+rx)} {f(cy)} C {f(cx+rx)} {f(cy+k*ry)} {f(cx+k*rx)} {f(cy+ry)} {f(cx)} {f(cy+ry)} "
            f"C {f(cx-k*rx)} {f(cy+ry)} {f(cx-rx)} {f(cy+k*ry)} {f(cx-rx)} {f(cy)} "
            f"C {f(cx-rx)} {f(cy-k*ry)} {f(cx-k*rx)} {f(cy-ry)} {f(cx)} {f(cy-ry)} "
            f"C {f(cx+k*rx)} {f(cy-ry)} {f(cx+rx)} {f(cy-k*ry)} {f(cx+rx)} {f(cy)} Z")


def rect(x0, y0, x1, y1):
    return f"M {x0} {y0} L {x1} {y0} L {x1} {y1} L {x0} {y1} Z"


def rot(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a))


def nodes_path(nodes, closed=True):
    """nodes: list of (x, y) or (x, y, {'corner': bool, 'rot': deg}). Smooth nodes use Catmull-Rom
    handles; corner nodes aim their handles at the neighbours, turned by 'rot' (fur sweep)."""
    pts = [(n[0], n[1], n[2] if len(n) > 2 else {}) for n in nodes]
    m = len(pts)

    def P(i):
        if closed:
            return pts[i % m]
        return pts[max(0, min(m - 1, i))]

    def handles(i):
        x, y, o = P(i)
        px, py, _ = P(i - 1)
        nx, ny, _ = P(i + 1)
        if o.get("corner"):
            r = o.get("rot", 0)
            hi = rot(((px - x) / 3, (py - y) / 3), -r)
            ho = rot(((nx - x) / 3, (ny - y) / 3), r)
            return (x + hi[0], y + hi[1]), (x + ho[0], y + ho[1])
        t = o.get("t", 1.0)
        tx, ty = (nx - px) / 6 * t, (ny - py) / 6 * t
        return (x - tx, y - ty), (x + tx, y + ty)

    hs = [handles(i) for i in range(m)]
    d = f"M {f(pts[0][0])} {f(pts[0][1])}"
    last = m if closed else m - 1
    for i in range(last):
        j = (i + 1) % m
        d += (f" C {f(hs[i][1][0])} {f(hs[i][1][1])} {f(hs[j][0][0])} {f(hs[j][0][1])} "
              f"{f(pts[j][0])} {f(pts[j][1])}")
    return d + (" Z" if closed else "")


def sample(anchors, per=24):
    """Dense polyline along a smooth closed Catmull-Rom curve through anchors."""
    out = []
    m = len(anchors)
    for i in range(m):
        p0, p1, p2, p3 = (anchors[(i + k) % m] for k in (-1, 0, 1, 2))
        for s in range(per):
            t = s / per
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[c]) + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                    + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    return out


def furry(anchors, tufts, seed=1, step=70):
    """Closed outline through anchors; inside each tuft range (u0, u1, amp, sweep) in 0..1 of the
    perimeter, the edge breaks into pointed fur tufts pushed outward by ~amp."""
    rng = random.Random(seed)
    poly = sample(anchors)
    n = len(poly)
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    sign = 1 if area > 0 else -1  # y-down: area>0 means clockwise on screen -> outward normal = (dy, -dx)
    seg = [math.dist(poly[i], poly[(i + 1) % n]) for i in range(n)]
    total = sum(seg)
    cum = [0.0]
    for s in seg[:-1]:
        cum.append(cum[-1] + s)

    def at(u):
        L = (u % 1.0) * total
        i = max(k for k in range(n) if cum[k] <= L)
        j = (i + 1) % n
        t = (L - cum[i]) / seg[i] if seg[i] else 0
        x = poly[i][0] + (poly[j][0] - poly[i][0]) * t
        y = poly[i][1] + (poly[j][1] - poly[i][1]) * t
        dx, dy = poly[j][0] - poly[i][0], poly[j][1] - poly[i][1]
        ln = math.hypot(dx, dy) or 1
        tx, ty = dx / ln, dy / ln
        nx, ny = (ty, -tx) if sign > 0 else (-ty, tx)
        return (x, y), (tx, ty), (nx, ny)

    def in_tuft(u):
        for t in tufts:
            if t[0] <= u <= t[1]:
                return t
        return None

    nodes = []
    du = step / total
    u = 0.0
    while u < 1.0 - du * 0.5:
        t = in_tuft(u)
        p, tg, nm = at(u)
        if not t:
            nodes.append((p[0], p[1]))
            u += du
            continue
        amp, sweep = t[2], t[3]
        w = du * rng.uniform(0.55, 0.9)
        nodes.append((p[0] - nm[0] * amp * 0.15, p[1] - nm[1] * amp * 0.15, {"corner": True, "rot": sweep * 0.5}))
        p2, tg2, nm2 = at(u + w * 0.5)
        a = amp * rng.uniform(0.6, 1.25)
        sw = a * 0.45 * (1 if sweep >= 0 else -1)
        nodes.append((p2[0] + nm2[0] * a + tg2[0] * sw, p2[1] + nm2[1] * a + tg2[1] * sw,
                      {"corner": True, "rot": sweep}))
        u += w
    return nodes_path(nodes)


def crescent(x0, y0, x1, y1, bend, width):
    """Tapered stripe from (x0,y0) to (x1,y1), bowed sideways by `bend`, max thickness `width`."""
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy) or 1
    nx, ny = -dy / ln, dx / ln
    c1 = (mx + nx * (bend + width), my + ny * (bend + width))
    c2 = (mx + nx * (bend - width), my + ny * (bend - width))
    return (f"M {f(x0)} {f(y0)} Q {f(c1[0])} {f(c1[1])} {f(x1)} {f(y1)} "
            f"Q {f(c2[0])} {f(c2[1])} {f(x0)} {f(y0)} Z")


def taper(x0, y0, x1, y1, bend, half):
    """Whisker: wide at (x0,y0), sharp at (x1,y1), bowed by `bend`."""
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy) or 1
    nx, ny = -dy / ln, dx / ln
    b1 = (x0 + nx * half, y0 + ny * half)
    b2 = (x0 - nx * half, y0 - ny * half)
    c1 = (mx + nx * (bend + half * 0.5), my + ny * (bend + half * 0.5))
    c2 = (mx + nx * (bend - half * 0.5), my + ny * (bend - half * 0.5))
    return (f"M {f(b1[0])} {f(b1[1])} Q {f(c1[0])} {f(c1[1])} {f(x1)} {f(y1)} "
            f"Q {f(c2[0])} {f(c2[1])} {f(b2[0])} {f(b2[1])} Z")


def lin(angle, *stops):
    return {"type": "linear", "angle": angle, "stops": [list(s) if len(s) == 3 else [s[0], s[1], 100] for s in stops]}


def rad(*stops):
    return {"type": "radial", "stops": [list(s) if len(s) == 3 else [s[0], s[1], 100] for s in stops]}


def item(name, d, fill=None, **kw):
    it = {"name": name, "d": d, "fill": fill}
    it.update(kw)
    return it


def photo(x, y):
    return (1000 + 6.9 * (x - 198.5), 960 + 6.9 * (y - 71))


# ---------------------------------------------------------------- scene
def scene_layers():
    rng = random.Random(7)
    L = []
    L.append({"layer": "Background art/Sky", "clear": True, "items": [
        item("Sky", rect(0, 0, W, H), lin(-90, (SKY[0], 0), (SKY[1], 45), (SKY[2], 75), (SKY[3], 100))),
        item("Sky glow", ell(1450, 700, 1100, 800), rad(("#8a6bd1", 0, 45), ("#8a6bd1", 100, 0))),
    ]})
    stars = []
    for i in range(70):
        x, y = rng.uniform(20, 1980), rng.uniform(20, 1150)
        r = rng.choice([2.5, 3, 3.5, 4, 5, 6.5])
        stars.append(item(f"Star {i+1}", ell(x, y, r, r), "#fff7e0", opacity=rng.randint(45, 100)))
    for i, (x, y, s) in enumerate([(260, 220, 26), (1780, 980, 20), (640, 120, 18), (1340, 160, 22)]):
        d = (f"M {x} {y-s} Q {x+s*0.15} {y-s*0.15} {x+s} {y} Q {x+s*0.15} {y+s*0.15} {x} {y+s} "
             f"Q {x-s*0.15} {y+s*0.15} {x-s} {y} Q {x-s*0.15} {y-s*0.15} {x} {y-s} Z")
        stars.append(item(f"Sparkle {i+1}", d, "#ffffff"))
    L.append({"layer": "Background art/Stars", "clear": True, "items": stars})
    mx, my, mr = 1600, 400, 135
    L.append({"layer": "Background art/Moon", "clear": True, "items": [
        item("Moon halo", ell(mx, my, mr * 2.6, mr * 2.6), rad(("#cfe8ff", 0, 55), ("#cfe8ff", 100, 0))),
        item("Moon", ell(mx, my, mr, mr), rad(("#fffdf2", 0), ("#f3e7c4", 100))),
        item("Crater 1", ell(mx - 40, my - 30, 26, 22), "#e6d6ab", opacity=70),
        item("Crater 2", ell(mx + 45, my + 35, 18, 16), "#e6d6ab", opacity=70),
        item("Crater 3", ell(mx + 20, my - 60, 12, 10), "#e6d6ab", opacity=70),
    ]})
    clouds = []
    for i, (cx, cy, w) in enumerate([(380, 700, 420), (1650, 640, 380), (1050, 300, 300)]):
        d = nodes_path([(cx - w, cy + 40), (cx - w * 0.7, cy - 10), (cx - w * 0.35, cy - 50), (cx, cy - 30),
                        (cx + w * 0.4, cy - 60), (cx + w * 0.75, cy - 5), (cx + w, cy + 40)])
        clouds.append(item(f"Cloud {i+1}", d, lin(-90, ("#b9a6e8", 0, 55), ("#5c4f9c", 100, 10)), blur=6))
    L.append({"layer": "Background art/Clouds", "clear": True, "items": clouds})
    far = [(0, 1240), (180, 1060), (330, 1140), (520, 960), (700, 1100), (900, 1010), (1100, 1120),
           (1320, 990), (1520, 1100), (1720, 1000), (2000, 1150)]
    near = [(0, 1420), (240, 1280), (460, 1380), (700, 1250), (1000, 1360), (1300, 1260), (1600, 1370),
            (1820, 1290), (2000, 1340)]

    def ridge(pts):
        return "M " + " L ".join(f"{x} {y}" for x, y in pts) + f" L {W} {H} L 0 {H} Z"

    L.append({"layer": "Background art/Mountains", "clear": True, "items": [
        item("Far range", ridge(far), lin(-90, ("#3a3a7a", 0), ("#1d1f4a", 100))),
        item("Near range", ridge(near), lin(-90, ("#262659", 0), ("#11122e", 100))),
    ]})
    return L


# ---------------------------------------------------------------- cat
HEAD_ANCHORS = [(0, -278), (180, -262), (330, -150), (382, 20), (392, 170), (300, 300), (150, 348),
                (10, 352), (-150, 330), (-300, 255), (-415, 120), (-420, -40), (-330, -190), (-180, -265)]
# fraction ranges of the perimeter that are cheek / jaw fur (starts at the crown, runs clockwise)
HEAD_TUFTS = [(0.20, 0.33, 40, 18), (0.60, 0.80, 44, -18)]


def body_clip():
    return [(1000, 1080), (1240, 1090), photo(250, 100), photo(258, 118), photo(264, 150), photo(262, 200),
            (1470, 2060), (-60, 2060), photo(48, 216), photo(60, 175), photo(85, 145), photo(120, 125),
            photo(155, 113), (820, 1150)]


def cat_layers():
    L = []
    bc = body_clip()
    body_d = furry(bc, [(0.62, 0.95, 28, -22), (0.15, 0.40, 22, 20)], seed=3, step=120)
    stripes = []
    for i, (x0, y0, x1, y1, b, w) in enumerate([
            (840, 1170, 700, 1420, 30, 26), (650, 1260, 470, 1540, 40, 30), (470, 1360, 260, 1680, 50, 34),
            (300, 1480, 100, 1820, 50, 34), (160, 1620, -20, 1960, 40, 30), (760, 1460, 600, 1780, 30, 22),
            (560, 1620, 380, 1960, 30, 24), (960, 1560, 860, 1900, 20, 20)]):
        stripes.append(item(f"Back stripe {i+1}", crescent(x0, y0, x1, y1, b, w), STRIPE_DK, opacity=80,
                            blend="multiply", blur=4))
    L.append({"layer": "Cat/Body", "clear": True, "clip": body_d, "outline": {"stroke": INK, "width": 7},
              "items": [
                  item("Body base", rect(-100, 1000, 1600, 2100),
                       lin(20, ("#9a3d10", 0), ("#d96f1a", 40), ("#f08d28", 75), ("#f9aa42", 100))),
                  item("Back shade", ell(150, 1900, 650, 500), rad((STRIPE_DK, 0, 70), (STRIPE_DK, 100, 0)),
                       blend="multiply", opacity=60),
                  *stripes,
                  item("Shoulder light", ell(1250, 1350, 300, 380), rad(("#ffd08a", 0, 70), ("#ffd08a", 100, 0)),
                       blend="screen", opacity=55),
                  item("Head shadow", ell(980, 1230, 520, 170), rad(("#5a2008", 0, 80), ("#5a2008", 100, 0)),
                       blend="multiply", opacity=70),
              ]})
    chest = furry([(1090, 1250), (1260, 1215), (1380, 1290), (1400, 2080), (1210, 2080), (1150, 1760),
                   (1090, 1500)], [(0.58, 0.99, 34, -24)], seed=5, step=85)
    tufts = []
    for i, (x0, y0, x1, y1, b) in enumerate([(1200, 1310, 1160, 1430, -14), (1310, 1330, 1280, 1460, 12),
                                              (1180, 1520, 1150, 1650, -16), (1290, 1570, 1260, 1710, 14),
                                              (1360, 1480, 1345, 1610, 10), (1230, 1780, 1210, 1910, -14)]):
        tufts.append(item(f"Fur tuft {i+1}", crescent(x0, y0, x1, y1, b, 10), CREAM_HI, opacity=90))
    L.append({"layer": "Cat/Chest fur", "clear": True, "clip": body_d, "items": [
        item("Chest", chest, lin(-90, (CREAM_HI, 0), ("#f6d29c", 40), ("#e99a4c", 100)), opacity=92),
        item("Chin shadow", ell(1120, 1220, 330, 120), rad(("#b86a2c", 0, 75), ("#b86a2c", 100, 0)),
             blend="multiply", opacity=70),
        *tufts,
    ]})

    # ears (head-local)
    ears = []
    for side, (bo, tip, bi) in (("L", ((-392, -110), (-365, -460), (-150, -262))),
                                ("R", ((90, -278), (282, -420), (352, -60)))):
        out = nodes_path([bo, ((bo[0] + tip[0]) / 2 - (20 if side == "L" else -10), (bo[1] + tip[1]) / 2),
                          (tip[0], tip[1], {"corner": True}),
                          ((tip[0] + bi[0]) / 2 + (25 if side == "L" else -20), (tip[1] + bi[1]) / 2 - 15), bi,
                          ((bo[0] + bi[0]) / 2, (bo[1] + bi[1]) / 2 + 60)])
        ears.append(item(f"Ear {side}", out, lin(-90, ("#e07a22", 0), ("#b8521a", 100)), stroke=INK, stroke_width=7))
        cx, cy = (bo[0] + tip[0] + bi[0]) / 3, (bo[1] + tip[1] + bi[1]) / 3 + 15

        def inset(p, k=0.62):
            return (cx + (p[0] - cx) * k, cy + (p[1] - cy) * k)
        ti, boi, bii = inset(tip, 0.78), inset(bo), inset(bi)
        inner = nodes_path([boi, (ti[0], ti[1], {"corner": True}), bii,
                            ((boi[0] + bii[0]) / 2, (boi[1] + bii[1]) / 2 + 40)])
        ears.append(item(f"Ear {side} inner", inner, lin(-90, ("#f6b6a6", 0), ("#c96a6a", 100))))
        for k in range(3):
            sx = boi[0] + (bii[0] - boi[0]) * (0.3 + 0.2 * k)
            sy = boi[1] + (bii[1] - boi[1]) * (0.3 + 0.2 * k) + 20
            ears.append(item(f"Ear {side} tuft {k+1}", crescent(sx, sy, sx + (ti[0] - sx) * 0.6, sy + (ti[1] - sy) * 0.6,
                                                                  8 * (1 if k % 2 else -1), 9), CREAM_HI, opacity=85))
    L.append({"layer": "Cat/Ears", "clear": True, "transform": HEAD_TF, "items": ears})

    head_d = furry(HEAD_ANCHORS, HEAD_TUFTS, seed=11, step=60)
    fore = [(-95, -100, -120, -255, 10, 16), (-35, -95, -45, -275, 4, 17), (30, -95, 40, -275, -4, 17),
            (95, -100, 125, -255, -10, 16), (-170, -150, -230, -250, 12, 12)]
    cheek = [(-240, 40, -420, 20, -14, 15), (-250, 95, -420, 115, 10, 13), (230, 40, 400, 20, 14, 14),
             (245, 95, 400, 120, -10, 12)]
    L.append({"layer": "Cat/Head", "clear": True, "transform": HEAD_TF, "clip": head_d,
              "outline": {"stroke": INK, "width": 7}, "items": [
                  item("Head base", ell(0, 40, 470, 420), lin(-90, ("#f6a03a", 0), ("#e9842a", 50), ("#c8601c", 100))),
                  item("Side shade", ell(-420, 60, 190, 360), rad(("#8f3a10", 0, 70), ("#8f3a10", 100, 0)),
                       blend="multiply", opacity=55),
                  item("Lower face light", ell(30, 225, 260, 140), rad((CREAM, 0, 45), (CREAM, 100, 0))),
                  item("Muzzle", ell(35, 212, 150, 92), rad((CREAM_HI, 0), (CREAM, 75), (CREAM, 100, 0))),
                  item("Brow light L", ell(-150, -70, 90, 40), rad((CREAM_HI, 0, 45), (CREAM_HI, 100, 0))),
                  item("Brow light R", ell(150, -78, 90, 40), rad((CREAM_HI, 0, 45), (CREAM_HI, 100, 0))),
                  *[item(f"Forehead stripe {i+1}", crescent(*s), STRIPE, opacity=85) for i, s in enumerate(fore)],
                  *[item(f"Cheek stripe {i+1}", crescent(*s), STRIPE, opacity=80) for i, s in enumerate(cheek)],
                  item("Top light", ell(-40, -230, 260, 90), rad(("#ffd9a0", 0, 70), ("#ffd9a0", 100, 0)),
                       blend="screen", opacity=70),
              ]})

    nm = [
        item("Chin", ell(30, 288, 72, 34), rad((CREAM, 0), ("#f3d2a6", 100))),
        item("Whisker pad L", ell(-10, 215, 62, 44), rad((CREAM_HI, 0), (CREAM, 100, 70))),
        item("Whisker pad R", ell(80, 212, 62, 44), rad((CREAM_HI, 0), (CREAM, 100, 70))),
        item("Nose", nodes_path([(-2, 128), (70, 128), (40, 170, {"corner": True}), (34, 174), (28, 170, {"corner": True})]),
             lin(-90, ("#f7a6a0", 0), ("#d77272", 100)), stroke=INK, stroke_width=3),
        item("Nose shine", ell(24, 138, 12, 6), "#ffffff", opacity=80),
        item("Mouth", "M 34 176 L 34 198 Q 30 218 -12 222", stroke=INK, stroke_width=5),
        item("Mouth R", "M 34 198 Q 42 216 84 216", stroke=INK, stroke_width=5),
    ]
    for i, (x, y) in enumerate([(-35, 205), (-15, 225), (-45, 228), (5, 240), (75, 202), (100, 218), (70, 228), (110, 236)]):
        nm.append(item(f"Whisker dot {i+1}", ell(x, y, 4, 4), "#b8703a"))
    L.append({"layer": "Cat/Nose & mouth", "clear": True, "transform": HEAD_TF, "items": nm})

    eyes = []
    for side, (cx, cy), px in (("L", (-149, 4), 10), ("R", (149, -4), 8)):
        lid = nodes_path([(cx - 78, cy + 4, {"corner": True, "rot": 12}), (cx - 20, cy - 58), (cx + 40, cy - 52),
                          (cx + 76, cy - 6, {"corner": True, "rot": -12}), (cx + 30, cy + 50), (cx - 30, cy + 50)])
        eyes.append(item(f"Lid {side}", lid, LID))
        eyes.append(item(f"Iris {side}", ell(cx, cy, 58, 50),
                         rad(("#f0ffa8", 0), ("#a6e64e", 45), ("#3fa83e", 80), ("#1c7434", 100))))
        eyes.append(item(f"Lid shadow {side}", ell(cx, cy - 46, 64, 26), rad(("#2b1206", 0, 85), ("#2b1206", 100, 0)),
                         blend="multiply", opacity=65))
        eyes.append(item(f"Pupil {side}", ell(cx + px, cy, 16, 40), "#120804"))
        eyes.append(item(f"Glint {side}", ell(cx + px + 22, cy - 22, 12, 10), "#ffffff"))
        eyes.append(item(f"Glint small {side}", ell(cx + px - 20, cy + 24, 5, 5), "#ffffff", opacity=80))
    L.append({"layer": "Cat/Eyes", "clear": True, "transform": HEAD_TF, "items": eyes})

    wh = []
    for i, (x0, y0, x1, y1, b) in enumerate([(-40, 210, -620, 120, -30), (-40, 222, -640, 250, -20),
                                              (-35, 235, -560, 360, 10), (105, 205, 660, 90, 30),
                                              (105, 218, 700, 230, 20), (100, 232, 620, 360, -10)]):
        wh.append(item(f"Whisker {i+1}", taper(x0, y0, x1, y1, b, 3.2), "#fffaf0", opacity=92))
    for i, (x0, y0, x1, y1, b) in enumerate([(-170, -62, -260, -190, -10), (-130, -66, -180, -200, -8),
                                              (130, -70, 170, -205, 8), (170, -66, 250, -190, 10)]):
        wh.append(item(f"Brow hair {i+1}", taper(x0, y0, x1, y1, b, 2.4), "#fffaf0", opacity=85))
    L.append({"layer": "Cat/Whiskers", "clear": True, "transform": HEAD_TF, "items": wh})
    return L


def fx_layers():
    rng = random.Random(21)
    flies = []
    for i in range(40):
        x, y = rng.uniform(80, 1920), rng.uniform(900, 1950)
        if not (x > 1520 or (x < 430 and y < 1250)):
            continue
        r = rng.uniform(5, 9)
        flies.append(item(f"Firefly glow {i+1}", ell(x, y, r * 5, r * 5), rad(("#d8ff8a", 0, 70), ("#d8ff8a", 100, 0))))
        flies.append(item(f"Firefly {i+1}", ell(x, y, r, r), "#f6ffd0"))
    return [{"layer": "Fireflies", "clear": True, "items": flies}]


def main():
    spec = {"doc": DOC, "layers": scene_layers() + cat_layers() + fx_layers()}
    out = Path(__file__).with_name("drawing.json")
    out.write_text(json.dumps(spec, indent=1), encoding="utf-8")
    n = sum(len(l["items"]) for l in spec["layers"])
    print(f"wrote {out} - {len(spec['layers'])} layers, {n} items")


if __name__ == "__main__":
    main()
