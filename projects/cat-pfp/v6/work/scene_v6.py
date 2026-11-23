"""v6 decorative pass (defects D6, D8, D9, D10). Imported by v6_design.build(); every path is hand-placed vector data."""
import math
import random

from v6_design import it, path, taper, ellipse, poly, lin, sample, canvas_xy, CYAN, CYAN_LT


def star4(x, y, s, waist=0.16):
    return poly([(x, y - s), (x + s * waist, y - s * waist), (x + s, y), (x + s * waist, y + s * waist),
                 (x, y + s), (x - s * waist, y + s * waist), (x - s, y), (x - s * waist, y - s * waist)])


# ---------- D10: castles with crenellations and arched windows ----------
def castle_items():
    items = [
        it("Mountains", path([(0, 1300), (0, 1020), (180, 900), (330, 980), (520, 860), (700, 1000), (860, 940),
                              (1000, 1040), (1160, 920), (1340, 1000), (1520, 860), (1700, 960), (1860, 880),
                              (2000, 960), (2000, 1300)]), "#2c2066", opacity=90),
    ]
    for name, x0, x1, top in (("Wall L", 20, 580, 1180), ("Wall R", 1440, 2000, 1190)):
        pts = [(x0, 1500), (x0, top)]
        x = x0
        while x < x1:  # merlons 22 px wide, 16 px tall, gaps 14 px
            pts += [(x, top - 16), (min(x + 22, x1), top - 16), (min(x + 22, x1), top), (min(x + 36, x1), top)]
            x += 36
        pts += [(x1, top), (x1, 1500)]
        items.append(it(name, poly(pts), "#2a1f5e"))
        items.append(it(name + " light", poly([(x0, top), (x1, top), (x1, top + 6), (x0, top + 6)]), "#3d2f80"))
    towers = [(70, 70, 1040, 150), (170, 90, 960, 190), (290, 60, 1090, 120), (380, 110, 1010, 220), (500, 70, 1120, 130),
              (1480, 80, 1100, 140), (1580, 110, 990, 230), (1720, 70, 1060, 150), (1820, 100, 940, 200), (1930, 70, 1080, 140)]
    wr = random.Random(4)
    for k, (x, w, top, sp) in enumerate(towers):
        items.append(it(f"Tower {k}", poly([(x - w / 2, 1500), (x - w / 2, top), (x + w / 2, top), (x + w / 2, 1500)]), "#30246a"))
        items.append(it(f"Tower lit side {k}", poly([(x - w / 2, 1500), (x - w / 2, top), (x - w / 2 + w * 0.3, top), (x - w / 2 + w * 0.3, 1500)]), "#382b78"))
        items.append(it(f"Tower band {k}", poly([(x - w / 2 - 6, top), (x + w / 2 + 6, top), (x + w / 2 + 6, top + 12), (x - w / 2 - 6, top + 12)]), "#3f3186"))
        items.append(it(f"Spire {k}", poly([(x - w / 2 - 10, top + 2), (x, top - sp), (x + w / 2 + 10, top + 2)]), "#3a2c7a"))
        items.append(it(f"Spire light {k}", poly([(x, top - sp), (x - w / 2 - 10, top + 2), (x - 6, top + 2)]), "#4b3a96"))
        for j in range(wr.randint(1, 3)):
            wy = top + 40 + j * 70
            col = "#ffcf7a" if wr.random() < 0.6 else CYAN
            arch = [(x - 7, wy + 24), (x - 7, wy + 8), (x - 5, wy + 3), (x, wy), (x + 5, wy + 3), (x + 7, wy + 8), (x + 7, wy + 24)]
            items.append(it(f"Window {k}.{j}", poly(arch), col, opacity=90))
            items.append(it(f"Window sill {k}.{j}", poly([(x - 9, wy + 24), (x + 9, wy + 24), (x + 9, wy + 27), (x - 9, wy + 27)]), "#241a52"))
    return items


# ---------- D9: scalloped blossom canopies with hanging tassels ----------
def canopy(cx, cy, R, bumps, rr, flat=0.72):
    pts = []
    for k in range(bumps):
        a = math.pi + math.pi * (k + 0.5) / bumps
        r = R * rr.uniform(0.93, 1.05)
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r * flat))
        if k < bumps - 1:
            b = math.pi + math.pi * (k + 1) / bumps
            pts.append((cx + math.cos(b) * R * 0.86, cy + math.sin(b) * R * 0.86 * flat, 'c'))
    pts += [(cx + R * 1.02, cy + R * 0.1), (cx + R * 0.55, cy + R * 0.3), (cx, cy + R * 0.22), (cx - R * 0.55, cy + R * 0.32), (cx - R * 1.02, cy + R * 0.1)]
    return pts


def mid_tree_items():
    rr = random.Random(33)
    items = []
    trees = [("L3", 160, 1930, 300), ("L2", 20, 1640, 280), ("L1", 330, 1640, 210), ("L0", 150, 1330, 230),
             ("R3", 1850, 1930, 300), ("R2", 1990, 1640, 280), ("R1", 1680, 1640, 210), ("R0", 1850, 1320, 230)]
    for name, cx, cy, R in trees:
        items.append(it(f"Trunk {name}", taper([(cx + 10, cy + R * 0.9), (cx - 6, cy + R * 0.4), (cx, cy)], canvas_xy, R * 0.16, 0.0, 0.5), "#22163f"))
        items.append(it(f"Canopy {name}", path(canopy(cx, cy, R, 7, rr)), lin([["#5a3a9c", 0], ["#3e2578", 100]])))
        items.append(it(f"Canopy light {name}", path(canopy(cx - R * 0.12, cy - R * 0.1, R * 0.7, 5, rr)), "#6f4fb2", opacity=90))
        items.append(it(f"Canopy top {name}", path(canopy(cx - R * 0.2, cy - R * 0.2, R * 0.38, 4, rr)), "#8a68c8", opacity=80))
        for k in range(9):  # tassels hang from the canopy's lower edge
            tx = cx + (k - 4) / 4 * R * 0.85 + rr.uniform(-10, 10)
            ty = cy + R * rr.uniform(0.12, 0.3)
            ln = rr.uniform(18, 40)
            items.append(it(f"Tassel {name}{k}", taper([(tx, ty), (tx + 2, ty + ln * 0.5), (tx - 1, ty + ln)], canvas_xy, 14, 0.35, 0.7),
                            rr.choice(["#7a58c0", "#8c66cc", "#6c4cb0"]), opacity=80))
    items.append(it("Tree base shade", poly([(0, 1700), (2000, 1700), (2000, 2000), (0, 2000)]), "#1a1240", opacity=45, blur=40))
    return items


# ---------- D8: wisteria racemes with stems, rachis, two-tone florets, pinnate leaves ----------
BANNER = ["#e2cffc", "#c7a6f2", "#a882e2", "#8259c8", "#5c3998"]
KEEL = ["#9b72dc", "#7d52c0", "#6340a4", "#4a2a80", "#331a5e"]


def branch_y(curve, x):
    S = sample(curve, canvas_xy, False, 20)
    return min(S, key=lambda p: abs(p[0] - x))[1]


def raceme(tag, x0, y0, ln, sway, rr, dim=False):
    items = []
    stem_end = (x0 + sway * 0.1, y0 + 26)
    items.append(it(f"Stem {tag}", taper([(x0, y0 - 6), (x0 + 3, y0 + 12), stem_end], canvas_xy, 7, 0.0, 0.3), "#2a1a3a"))
    rach = [stem_end, (stem_end[0] + sway * 0.35, stem_end[1] + ln * 0.5), (stem_end[0] + sway, stem_end[1] + ln)]
    items.append(it(f"Rachis {tag}", taper(rach, canvas_xy, 4, 0.0, 0.9), "#3b2752"))
    S = sample(rach, canvas_xy, False, 30)
    rows = max(8, int(ln / 11))
    for i in range(rows):
        t = i / rows
        x, y = S[int(t * (len(S) - 1))]
        tone = min(4, int(t * 5) + (1 if dim else 0))
        sz = (1 - t) * 10 + 5
        half = (1 - t) ** 0.8 * 32 + 5
        order = (-1, 1) if i % 2 == 0 else (1, -1)
        for n, side in enumerate(order):
            back = n == 0  # first floret of each row sits behind the rachis, a tone darker
            tb = min(4, tone + (1 if back else 0))
            fx = x + side * half * rr.uniform(0.55, 1.0)
            fy = y + rr.uniform(-3, 3)
            rot = side * rr.uniform(10, 35)
            items.append(it(f"Keel {tag}.{i}{side}", ellipse(fx + side * 2, fy + sz * 0.55, sz * 0.6, sz * 0.45, rot), KEEL[tb]))
            items.append(it(f"Banner {tag}.{i}{side}", ellipse(fx, fy, sz * 1.05, sz * 0.8, rot), BANNER[tb]))
            if not back and tone <= 2 and rr.random() < 0.6:
                items.append(it(f"Banner hi {tag}.{i}{side}", ellipse(fx - side * sz * 0.25, fy - sz * 0.25, sz * 0.38, sz * 0.24, rot), "#f6eeff", opacity=85))
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
    for tag, x, ang, ln in (("L0", 120, 120, 150), ("L1", 380, 60, 130), ("L2", 600, 130, 140), ("R0", 1850, 70, 120)):
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
