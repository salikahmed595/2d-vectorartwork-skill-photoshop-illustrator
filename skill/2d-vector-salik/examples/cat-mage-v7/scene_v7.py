"""v7 near-frame wisteria and FX particles. Imported by v7_design.build(); every path is hand-placed vector data.
(Background scenery lives in scene_v7_bg.py.)"""
import math
import random

from v7_design import it, path, taper, ellipse, poly, sample, canvas_xy, CYAN, CYAN_LT


def star4(x, y, s, waist=0.16):
    return poly([(x, y - s), (x + s * waist, y - s * waist), (x + s, y), (x + s * waist, y + s * waist),
                 (x, y + s), (x - s * waist, y + s * waist), (x - s, y), (x - s * waist, y - s * waist)])


# ---------- wisteria (v7: real pea-flower florets on a tapered cluster mass, skill v3 rule 16) ----------
BANNER = ["#e8d8fd", "#cdaef5", "#ad88e6", "#8a62cc", "#62409e"]
KEEL = ["#9b72dc", "#7d52c0", "#6340a4", "#4a2a80", "#331a5e"]
# banner petal: broad, slightly notched at the top; keel: small teardrop hanging below it (unit size, local coords)
BANNER_SHAPE = [(0, -0.62, 'c'), (0.55, -1.0), (1.0, -0.45), (0.85, 0.25), (0, 0.5), (-0.85, 0.25), (-1.0, -0.45), (-0.55, -1.0)]
KEEL_SHAPE = [(0, 0.2), (0.45, 0.5), (0.3, 1.0), (0, 1.28, 'c'), (-0.3, 1.0), (-0.45, 0.5)]
BUD_SHAPE = [(0, -0.9), (0.55, -0.2), (0.4, 0.5), (0, 1.0, 'c'), (-0.4, 0.5), (-0.55, -0.2)]


def local(shape, x, y, sz, rot):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return path([(x + (p[0] * c - p[1] * s) * sz, y + (p[0] * s + p[1] * c) * sz) + tuple(p[2:]) for p in shape])


def branch_y(curve, x):
    S = sample(curve, canvas_xy, False, 20)
    return min(S, key=lambda p: abs(p[0] - x))[1]


def raceme(tag, x0, y0, ln, sway, rr, dim=False):
    items = []
    stem_end = (x0 + sway * 0.1, y0 + 26)
    items.append(it(f"Stem {tag}", taper([(x0, y0 - 6), (x0 + 3, y0 + 12), stem_end], canvas_xy, 7, 0.0, 0.3), "#2a1a3a"))
    rach = [stem_end, (stem_end[0] + sway * 0.35, stem_end[1] + ln * 0.5), (stem_end[0] + sway, stem_end[1] + ln)]
    S = sample(rach, canvas_xy, False, 30)
    # cluster mass: a tapered cone behind the florets, so the raceme reads as one cluster, not a bead string
    mass = [S[0], S[int(0.4 * (len(S) - 1))], S[int(0.78 * (len(S) - 1))]]  # stops before the buds so the tip stays light and airy
    items.append(it(f"Cluster mass {tag}", taper(mass, canvas_xy, 54, 0.08, 1.0), "#4a2a80" if not dim else "#331a5e", opacity=85))
    items.append(it(f"Rachis {tag}", taper(rach, canvas_xy, 4, 0.0, 0.9), "#3b2752"))
    rows = max(9, int(ln / 10))
    for i in range(rows):
        t = i / rows
        x, y = S[int(t * (len(S) - 1))]
        tone = min(4, int(t * 4.2) + (1 if dim else 0))
        half = (1 - t) ** 0.9 * 28 + 4
        order = (-1, 1, 0) if i % 2 == 0 else (1, -1, 0)
        for n, side in enumerate(order):
            back = n == 0  # first floret of each row sits behind, a tone darker; the third faces the viewer
            tb = min(4, tone + (1 if back else 0))
            fx = x + side * half * rr.uniform(0.6, 1.0) + (rr.uniform(-4, 4) if side == 0 else 0)
            fy = y + rr.uniform(-3, 3) + (4 if side == 0 else 0)
            rot = side * rr.uniform(15, 40)
            if t > 0.8:  # buds at the tip: small, closed, mid-lilac with a lit tip
                bs = (1 - t) * 16 + 5
                items.append(it(f"Bud {tag}.{i}{side}", local(BUD_SHAPE, fx, fy, bs, rot), BANNER[min(4, tb)]))
                items.append(it(f"Bud hi {tag}.{i}{side}", local(BUD_SHAPE, fx - bs * 0.15, fy - bs * 0.25, bs * 0.45, rot), BANNER[1], opacity=70))
                continue
            sz = (1 - t) * 9 + 6
            items.append(it(f"Keel {tag}.{i}{side}", local(KEEL_SHAPE, fx, fy, sz, rot), KEEL[tb]))
            items.append(it(f"Banner {tag}.{i}{side}", local(BANNER_SHAPE, fx, fy, sz, rot), BANNER[tb]))
            if not back and tone <= 1:
                items.append(it(f"Banner eye {tag}.{i}{side}", ellipse(fx, fy - sz * 0.15, sz * 0.18, sz * 0.14, rot), "#f4e49a", opacity=75))
            if not back and tone <= 2 and rr.random() < 0.5:
                items.append(it(f"Banner hi {tag}.{i}{side}", local(BANNER_SHAPE, fx - side * sz * 0.2, fy - sz * 0.25, sz * 0.38, rot), "#f8f1ff", opacity=80))
    return items


def leaf_spray(tag, x0, y0, ang, ln):
    items = []
    a = math.radians(ang)
    tip = (x0 + math.cos(a) * ln, y0 + math.sin(a) * ln)
    mid = ((x0 + tip[0]) / 2 + math.sin(a) * 10, (y0 + tip[1]) / 2 - math.cos(a) * 10)
    spine = [(x0, y0), mid, tip]
    items.append(it(f"Leaf stem {tag}", taper(spine, canvas_xy, 4, 0.0, 0.8), "#1b2a30"))
    S = sample(spine, canvas_xy, False, 20)
    pairs = 5
    for k in range(pairs):
        i = int((0.25 + 0.7 * k / pairs) * (len(S) - 1))
        x, y = S[i]
        nx, ny = S[min(i + 1, len(S) - 1)], S[i - 1]
        base = math.atan2(nx[1] - ny[1], nx[0] - ny[0])
        L = 34 * (1 - 0.3 * k / pairs)
        for side in (-1, 1):
            b = base + side * math.radians(50)
            lt = (x + math.cos(b) * L, y + math.sin(b) * L)
            col = "#2f4a52" if side < 0 else "#22363f"
            items.append(it(f"Leaflet {tag}.{k}{side}", taper([(x, y), ((x + lt[0]) / 2, (y + lt[1]) / 2), lt], canvas_xy, 13, 0.5, 0.6), col))
            items.append(it(f"Leaflet rib {tag}.{k}{side}", taper([(x, y), lt], canvas_xy, 1.4, 0.1, 0.4), "#456770", opacity=70))
    items.append(it(f"Leaflet end {tag}", taper([tip, (tip[0] + math.cos(a) * 30, tip[1] + math.sin(a) * 30)], canvas_xy, 13, 0.5, 0.6), "#2f4a52"))
    return items


def wisteria_items():
    rr = random.Random(77)
    items = []
    bl = [(-40, 26), (140, 66), (300, 40), (460, 92), (610, 64), (720, 112)]
    br = [(2040, 34), (1920, 74), (1790, 46)]
    for tag, curve in (("L", bl), ("R", br)):
        items.append(it(f"Branch {tag}", taper(curve, canvas_xy, 30, 0.0, 0.7), "#1c0f26"))
        items.append(it(f"Branch {tag} light", taper(curve, canvas_xy, 6, 0.1, 0.7), "#3a2850", opacity=80))
    curve = lambda tag: bl if tag[0] == "L" else br
    for tag, x, ln, sway in (("Lb0", 200, 240, 14), ("Lb1", 520, 220, -10), ("Lb2", 380, 300, 6), ("Rb0", 1880, 180, 8)):  # back, dimmer
        items += raceme(tag, x, branch_y(curve(tag), x), ln, sway, rr, dim=True)
    for tag, x, ang, ln in (("L0", 120, 120, 150), ("L1", 380, 60, 130), ("L2", 600, 130, 140), ("L3", 250, 95, 110),
                            ("L4", 680, 70, 100), ("R0", 1850, 70, 120), ("R1", 1990, 110, 110)):
        items += leaf_spray(tag, x, branch_y(curve(tag), x), ang, ln)
    for tag, x, ln, sway in (("L0", 70, 400, -12), ("L1", 300, 330, 10), ("L2", 430, 450, -6), ("L3", 590, 210, -8), ("R0", 1960, 300, -10)):
        items += raceme(tag, x, branch_y(curve(tag), x), ln, sway, rr)
    return items


# ---------- D6: designed particles: size classes, clusters, glints, notched petals, bokeh ----------
PETAL = [(0, -12, 'c'), (4.5, -4), (5, 5), (1.5, 10), (0, 8.5, 'c'), (-1.5, 10), (-5, 5), (-4.5, -4)]  # slender, small tip notch


def petal_path(x, y, sc, rot):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return path([(x + (p[0] * c - p[1] * s) * sc, y + (p[0] * s + p[1] * c) * sc) + tuple(p[2:]) for p in PETAL])


def blocked(x, y):  # keep the face and ears clear
    return 560 < x < 1440 and 260 < y < 1180


def particle_items():
    rr = random.Random(101)
    items = []
    n = 0

    def spark(x, y, cls):
        nonlocal n
        if cls == 0:
            r = rr.uniform(1.4, 2.2)
            items.append(it(f"Spark s{n}", ellipse(x, y, r, r), CYAN_LT, opacity=75))
        else:
            r = rr.uniform(2.6, 3.6) if cls == 1 else rr.uniform(4.5, 6)
            items.append(it(f"Spark halo {n}", ellipse(x, y, r * 3.2, r * 3.2), CYAN, opacity=28, blend="screen", blur=5))
            items.append(it(f"Spark {n}", ellipse(x, y, r, r), CYAN_LT))
            if cls == 2:
                items.append(it(f"Glint {n}", star4(x, y, r * 4.5), "#e8ffff", opacity=90))
        n += 1

    def cls_pick():
        v = rr.random()
        return 0 if v < 0.55 else (1 if v < 0.88 else 2)

    for (cx, cy), sig, keep, cnt in (((670, 1430), 120, 90, 18), ((1000, 1230), 100, 80, 8)):  # orb, amulet clusters
        made = 0
        while made < cnt:
            x, y = rr.gauss(cx, sig), rr.gauss(cy, sig)
            if math.hypot(x - cx, y - cy) < keep or blocked(x, y):
                continue
            spark(x, y, cls_pick())
            made += 1
    made = 0
    while made < 22:  # along the magic circle rim
        a = rr.uniform(0, 2 * math.pi)
        r = 660 + rr.gauss(0, 26)
        x, y = 1000 + math.cos(a) * r, 760 + math.sin(a) * r
        if blocked(x, y) or not 0 < x < 2000:
            continue
        spark(x, y, cls_pick())
        made += 1
    made = 0
    while made < 12:  # sparse ambient
        x, y = rr.uniform(80, 1920), rr.uniform(150, 1900)
        if blocked(x, y) or (420 < x < 1580 and y > 1100):
            continue
        spark(x, y, 0)
        made += 1
    made = 0
    while made < 20:  # petals drift from the wisteria (top-left) down to the right
        t = rr.random()
        x = rr.uniform(60, 760) + t * 900
        y = 160 + t * 1650 + rr.uniform(-120, 120)
        if blocked(x, y):
            continue
        fg = made < 2
        if fg:  # out-of-focus foreground petals stay at the frame edges
            x, y = (160, 1500) if made == 0 else (1830, 1150)
        sc = rr.uniform(2.2, 2.6) if fg else rr.uniform(0.9, 1.5)
        rot = rr.uniform(0, 360)
        items.append(it(f"Petal drift {made}", petal_path(x, y, sc, rot), rr.choice(["#c9a2ff", "#b88cf2", "#d8b8ff"]),
                        opacity=85 if fg else 95, blur=3 if fg else 0))
        if not fg:
            items.append(it(f"Petal drift hi {made}", petal_path(x - sc * 1.5, y - sc * 1.5, sc * 0.5, rot), "#f4e8ff", opacity=80))
        made += 1
    for k, (x, y, r, col) in enumerate([(120, 1840, 60, CYAN), (300, 1950, 44, "#b894ec"), (1880, 1800, 70, "#b894ec"),
                                        (1750, 1960, 40, CYAN)]):
        items.append(it(f"Bokeh {k}", ellipse(x, y, r, r), col, opacity=14, blur=6))
    return items
