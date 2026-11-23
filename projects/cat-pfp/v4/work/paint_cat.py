"""v4 cat PFP - painterly vector spec for ai_draw.py (no AI generation).

    python paint_cat.py        -> drawing.json (+ colour_field.png for checking)

Method (how a pet-portrait painter works, done with vector strokes):
1. Construction: silhouettes of each part measured off a fine grid of the user's photo (photo coords).
2. Colour reference: colours are eyedropped from the user's photo (median-filtered to drop whiskers,
   blurred inside the cat only so wall colour never leaks in), then pushed in saturation.
3. Block-in: a field of soft blobs per part, clipped to the part and blurred (layer group blur).
4. Render: thousands of tapered fur strokes following each part's growth direction, sorted dark -> light.
5. Details drawn by hand: eyes, nose, mouth, whiskers. Scene: soft sky, moon, hills, bokeh.
Photo -> canvas: X = 1000 + 6.9 (x - 198.5), Y = 960 + 6.9 (y - 71).
"""
from __future__ import annotations

import colorsys
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).parent
SRC = HERE.parents[1] / "inbox" / "cat-source.png"
DOC = "cat-pfp-v4.ai"
W = H = 2000
K, PX, PY, CX, CY = 6.9, 198.5, 71.0, 1000.0, 960.0


def c2p(x, y):
    return ((x - CX) / K + PX, (y - CY) / K + PY)


def p2c(x, y):
    return (CX + K * (x - PX), CY + K * (y - PY))


def poly(pts):
    return [p2c(*p) for p in pts]


# ------------------------------------------------------------------ construction (photo coords)
EAR_L = [(125.8, 35), (138, 37), (152, 39), (166, 42), (162, 52), (152, 62), (144, 70), (139, 58), (132, 46)]
EAR_R = [(221.7, 3.3), (226, 12), (230, 26), (234, 40), (226, 44), (212, 40), (199, 38), (204, 26), (212, 13)]
HEAD = [(147, 47), (160, 41), (176, 37), (192, 35), (208, 35), (222, 37), (234, 41), (240, 52), (246, 66),
        (252, 79), (256, 93), (253, 106), (244, 116), (229, 123), (212, 125), (193, 123), (175, 119),
        (162, 113), (152, 104), (145, 92), (141, 79), (141, 63)]
BODY = [(152, 112), (131, 120), (106, 126), (88, 134), (76, 145), (67, 157), (60, 170), (52, 185), (45, 197),
        (36, 223), (264, 223), (269, 195), (271, 165), (267, 135), (258, 113), (250, 102), (215, 112), (175, 112)]
CHEST = [(203, 113), (226, 112), (248, 104), (260, 116), (266, 138), (270, 165), (268, 195), (263, 223), (214, 223),
         (205, 192), (199, 160), (198, 132)]

NOSE_ORIGIN = (210, 92)


# ------------------------------------------------------------------ colour reference from the photo
def colour_field():
    im = Image.open(SRC).convert("RGB").filter(ImageFilter.MedianFilter(5))
    S = 4
    big = im.resize((im.width * S, im.height * S), Image.BICUBIC)
    mask = Image.new("L", big.size, 0)
    d = ImageDraw.Draw(mask)
    for part in (EAR_L, EAR_R, HEAD, BODY):
        d.polygon([(x * S, y * S) for x, y in part], fill=255)
    d.rectangle((0, 202 * S, 210 * S, 216 * S), fill=0)  # teal blanket under the cat - not fur
    mask = mask.filter(ImageFilter.MinFilter(9))  # pull in from the wall edge
    r = 6
    num = Image.composite(big, Image.new("RGB", big.size), mask).filter(ImageFilter.GaussianBlur(r))
    den = mask.filter(ImageFilter.GaussianBlur(r))
    nb, db = num.load(), den.load()
    out = Image.new("RGB", big.size)
    ob = out.load()
    for y in range(big.height):
        for x in range(big.width):
            a = db[x, y]
            if a > 8:
                c = nb[x, y]
                ob[x, y] = tuple(min(255, int(v * 255 / a)) for v in c)
    valid = den.point(lambda v: 255 if v > 8 else 0)
    for _ in range(40):
        grown = out.filter(ImageFilter.MaxFilter(5))
        out = Image.composite(out, grown, valid)
        valid = valid.filter(ImageFilter.MaxFilter(5))
    return out, S


FIELD, FS = colour_field()
FIELD.save(HERE / "colour_field.png")


def pick(cx, cy):
    """Colour under canvas point, from the photo reference, stylised."""
    x, y = c2p(cx, cy)
    x = min(max(x, 0), 471.9)
    y = min(max(y, 0), 215.9)
    if x < 210:
        y = min(y, 199.0)  # below this is the blanket
    x = min(x, 261.0)      # right of this is wall
    r, g, b = FIELD.getpixel((int(x * FS), int(y * FS)))
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    s = min(1.0, s * 1.25 + 0.04)
    l = min(0.97, l * 1.02)
    return h, l, s


def hexc(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h % 1.0, min(max(l, 0), 1), min(max(s, 0), 1))
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


# ------------------------------------------------------------------ geometry
def f(v):
    return f"{v:.1f}"


def smooth_closed(pts):
    m = len(pts)
    d = f"M {f(pts[0][0])} {f(pts[0][1])}"
    for i in range(m):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C {f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p2[0])} {f(p2[1])}"
    return d + " Z"


def ell(cx, cy, rx, ry, rot=0.0):
    k = 0.5523
    base = [(rx, 0), (rx, k * ry), (k * rx, ry), (0, ry), (-k * rx, ry), (-rx, k * ry), (-rx, 0), (-rx, -k * ry),
            (-k * rx, -ry), (0, -ry), (k * rx, -ry), (rx, -k * ry)]
    a = math.radians(rot)
    P = [(cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)) for x, y in base]
    d = f"M {f(P[0][0])} {f(P[0][1])}"
    for i in range(4):
        q = P[3 * i + 1: 3 * i + 4] if i < 3 else [P[10], P[11], P[0]]
        d += " C " + " ".join(f"{f(x)} {f(y)}" for x, y in q)
    return d + " Z"


def strand(x0, y0, ang, length, width, bend):
    """Tapered fur stroke: base (x0,y0) of `width`, tip at `length` along `ang` (radians), bowed by bend."""
    dx, dy = math.cos(ang), math.sin(ang)
    nx, ny = -dy, dx
    x1, y1 = x0 + dx * length, y0 + dy * length
    mx, my = x0 + dx * length * 0.5 + nx * bend, y0 + dy * length * 0.5 + ny * bend
    h = width / 2
    return (f"M {f(x0 + nx * h)} {f(y0 + ny * h)} Q {f(mx + nx * h * 0.6)} {f(my + ny * h * 0.6)} {f(x1)} {f(y1)} "
            f"Q {f(mx - nx * h * 0.6)} {f(my - ny * h * 0.6)} {f(x0 - nx * h)} {f(y0 - ny * h)} Z")


def inside(pt, pts):
    x, y = pt
    c = False
    for i in range(len(pts)):
        x1, y1 = pts[i - 1]
        x2, y2 = pts[i]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def bbox(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def edge_dist(pt, pts):
    best, bn = 1e9, (0, 0)
    for i in range(len(pts)):
        ax, ay = pts[i - 1]
        bx, by = pts[i]
        vx, vy = bx - ax, by - ay
        t = max(0, min(1, ((pt[0] - ax) * vx + (pt[1] - ay) * vy) / ((vx * vx + vy * vy) or 1)))
        qx, qy = ax + vx * t, ay + vy * t
        dd = math.hypot(pt[0] - qx, pt[1] - qy)
        if dd < best:
            best, bn = dd, (pt[0] - qx, pt[1] - qy)
    return best, bn


def item(name, d, fill=None, **kw):
    it = {"name": name, "d": d, "fill": fill}
    it.update(kw)
    return it


# ------------------------------------------------------------------ painting passes
def underpaint(name, pts, spacing, rng):
    x0, y0, x1, y1 = bbox(pts)
    items = []
    y = y0 - spacing
    i = 0
    row = 0
    while y < y1 + spacing:
        x = x0 - spacing + (spacing / 2 if row % 2 else 0)
        while x < x1 + spacing:
            jx, jy = x + rng.uniform(-0.3, 0.3) * spacing, y + rng.uniform(-0.3, 0.3) * spacing
            dist, _ = edge_dist((jx, jy), pts)
            if inside((jx, jy), pts) or dist < spacing * 1.2:
                h, l, s = pick(jx, jy)
                i += 1
                items.append(item(f"{name} paint {i}", ell(jx, jy, spacing * 0.95, spacing * 0.8, rng.uniform(0, 180)),
                                  hexc(h, l, s)))
            x += spacing
        y += spacing * 0.85
        row += 1
    return items


def fur(name, pts, flow, count, length, width, rng, edge_out=0.0, light=1.0, sat=1.0, min_l=0.0):
    """Strokes seeded inside pts. flow(x, y) -> angle. length/width: (min, max) canvas px.
    edge_out: near the outline, turn strokes outward by this fraction (breaks the silhouette)."""
    x0, y0, x1, y1 = bbox(pts)
    strokes = []
    tries = 0
    while len(strokes) < count and tries < count * 20:
        tries += 1
        p = (rng.uniform(x0, x1), rng.uniform(y0, y1))
        if not inside(p, pts):
            continue
        ang = flow(*p)
        L = rng.uniform(*length)
        if edge_out:
            dist, (nx, ny) = edge_dist(p, pts)
            if dist < L * 0.9 and dist > 0:
                a2 = math.atan2(-ny, -nx)
                tx, ty = p[0] + math.cos(a2) * 6, p[1] + math.sin(a2) * 6
                if inside((tx, ty), pts):
                    a2 += math.pi
                mix = edge_out * (1 - dist / (L * 0.9))
                da = math.atan2(math.sin(a2 - ang), math.cos(a2 - ang))
                ang += da * mix
                L *= 1 + 0.5 * mix
        ang += rng.gauss(0, 0.12)
        h, l, s = pick(*p)
        r = rng.random()
        if r < 0.18:
            l *= rng.uniform(0.7, 0.85)        # darker under-fur
        elif r > 0.9:
            l = min(0.94, l * rng.uniform(1.06, 1.16) + 0.02)  # sparse highlight hairs
        else:
            l *= rng.uniform(0.93, 1.05)
        l = max(min_l, l * light)
        wdt = rng.uniform(*width)
        bend = rng.gauss(0, L * 0.12)
        strokes.append((l, item(f"{name} {len(strokes)+1}", strand(p[0], p[1], ang, L, wdt, bend),
                                hexc(h + rng.gauss(0, 0.006), l, s * sat), opacity=rng.randint(70, 96))))
    strokes.sort(key=lambda t: t[0])
    return [s for _, s in strokes]


def radial_flow(ox, oy, down=0.0, twist=0.0):
    def fl(x, y):
        vx, vy = x - ox, y - oy
        n = math.hypot(vx, vy) or 1
        vx, vy = vx / n, vy / n + down
        return math.atan2(vy, vx) + twist
    return fl


def toward(tx, ty):
    def fl(x, y):
        return math.atan2(ty - y, tx - x)
    return fl


# ------------------------------------------------------------------ eyes, nose, whiskers
def eye(side, cx, cy, w, h, tilt, pup, rng):
    items = []
    a = math.radians(tilt)

    def R(x, y):
        return (cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a))

    def P(pts):
        return smooth_closed([R(*p) for p in pts])
    rw, rh = w / 2, h / 2
    socket = [(-rw * 1.1, rh * 0.12), (-rw * 0.6, -rh * 1.1), (rw * 0.4, -rh * 1.13), (rw * 1.08, -rh * 0.15),
              (rw * 0.55, rh * 1.06), (-rw * 0.5, rh * 1.03)]
    items.append(item(f"Eye socket shade {side}", P([(x * 1.25, y * 1.35) for x, y in socket]),
                      {"type": "radial", "stops": [["#3a1a08", 0, 70], ["#3a1a08", 100, 0]]}, blend="multiply", opacity=60))
    items.append(item(f"Lid rim {side}", P(socket), "#2e1609"))
    iris = [(-rw, 0), (-rw * 0.7, -rh * 0.92), (0, -rh * 1.02), (rw * 0.75, -rh * 0.88), (rw, 0),
            (rw * 0.7, rh * 0.9), (0, rh * 1.0), (-rw * 0.72, rh * 0.88)]
    items.append(item(f"Iris {side}", P([(x * 0.93, y * 0.93) for x, y in iris]),
                      {"type": "radial", "stops": [["#f1f0a6", 0, 100], ["#c9d77e", 30, 100], ["#8fae6a", 62, 100],
                                                   ["#58704b", 88, 100], ["#2b3524", 100, 100]]}))
    for k in range(70):
        t = k / 70 * 2 * math.pi + rng.uniform(-0.03, 0.03)
        r0, r1 = rng.uniform(0.25, 0.4), rng.uniform(0.7, 0.92)
        x0, y0 = R(math.cos(t) * rw * r0, math.sin(t) * rh * r0)
        x1, y1 = R(math.cos(t) * rw * r1, math.sin(t) * rh * r1)
        ang = math.atan2(y1 - y0, x1 - x0)
        col = rng.choice(["#fbf6c8", "#e8eb9c", "#6f8a52", "#46593a"])
        items.append(item(f"Iris fibre {side} {k+1}", strand(x0, y0, ang, math.hypot(x1 - x0, y1 - y0), rng.uniform(1.4, 2.6),
                                                             rng.gauss(0, 1.5)), col, opacity=rng.randint(35, 70)))
    items.append(item(f"Limbal ring {side}", P([(x * 0.93, y * 0.93) for x, y in iris]), None,
                      stroke="#1f2a1a", stroke_width=max(3, w * 0.035), opacity=85))
    px, py, prx, pry = pup
    items.append(item(f"Pupil {side}", ell(*R(px, py), prx, pry, tilt), "#0a0604"))
    items.append(item(f"Upper lid shadow {side}", P([(-rw * 1.05, -rh * 0.25), (-rw * 0.5, -rh * 1.05), (rw * 0.45, -rh * 1.1),
                                                      (rw * 1.05, -rh * 0.35), (rw * 0.4, -rh * 0.55), (-rw * 0.4, -rh * 0.5)]),
                      {"type": "linear", "angle": -90, "stops": [["#140904", 0, 85], ["#140904", 100, 0]]},
                      blend="multiply", opacity=75))
    gx, gy = R(rw * 0.28, -rh * 0.42)
    items.append(item(f"Catchlight {side}", ell(gx, gy, w * 0.11, h * 0.09, tilt - 20), "#ffffff", opacity=95))
    gx2, gy2 = R(-rw * 0.35, rh * 0.45)
    items.append(item(f"Bounce light {side}", ell(gx2, gy2, w * 0.13, h * 0.05, tilt + 15), "#f7ffd8", opacity=45))
    ix, iy = R(-rw * 1.14 if side == "L" else rw * 1.1, rh * 0.25)
    items.append(item(f"Tear duct {side}", ell(ix, iy, w * 0.05, h * 0.07, tilt), "#6b2f24", opacity=80))
    return items


def whiskers(rng):
    items = []
    L_root = [p2c(203, 98), p2c(204, 101), p2c(202, 104), p2c(205, 103), p2c(201, 100)]
    R_root = [p2c(218, 97), p2c(219, 100), p2c(217, 103), p2c(220, 102)]
    n = 0
    for roots, base_ang, spread, length in ((L_root, 160, 50, (430, 700)), (R_root, 8, 40, (380, 560))):
        for k in range(9):
            x0, y0 = rng.choice(roots)
            x0 += rng.uniform(-10, 10)
            y0 += rng.uniform(-8, 8)
            ang = math.radians(base_ang + (k / 8 - 0.5) * spread + rng.uniform(-4, 4))
            L = rng.uniform(*length)
            n += 1
            bend = L * rng.uniform(0.06, 0.12) * (1 if base_ang > 90 else -1)
            items.append(item(f"Whisker {n}", strand(x0, y0, ang, L, rng.uniform(3.0, 4.6), bend), "#fffaf0",
                              opacity=rng.randint(70, 95)))
    for k in range(7):
        side = -1 if k < 4 else 1
        x0, y0 = (p2c(176 + k * 2, 66) if side < 0 else p2c(214 + k, 54))
        ang = math.radians(-115 + rng.uniform(-15, 15) if side < 0 else -80 + rng.uniform(-15, 15))
        n += 1
        items.append(item(f"Brow hair {k+1}", strand(x0, y0, ang, rng.uniform(110, 170), 2.6, rng.uniform(-14, 14)),
                          "#fff6e8", opacity=80))
    return items


def line(a, b, c):
    return "M %s %s Q %s %s %s %s" % (*map(f, p2c(*a)), *map(f, p2c(*b)), *map(f, p2c(*c)))


def nose_mouth():
    nose = poly([(201.5, 86.2), (207, 85.6), (214.5, 87.6), (213, 90.2), (210.3, 94.2), (208.4, 93.4), (204.5, 89.6)])
    items = [
        item("Muzzle shadow", ell(*p2c(209, 99), 120, 70, -17), {"type": "radial", "stops": [["#a8603a", 0, 40], ["#a8603a", 100, 0]]},
             blend="multiply"),
        item("Nose leather", smooth_closed(nose), {"type": "linear", "angle": -90, "stops": [["#f4b0a3", 0], ["#d98378", 60], ["#b85f58", 100]]}),
        item("Nostril L", ell(*p2c(205.6, 89.6), 9, 5, 40), "#5a2420", opacity=85),
        item("Nostril R", ell(*p2c(212.4, 90.4), 8, 5, -30), "#5a2420", opacity=85),
        item("Nose bridge light", ell(*p2c(207.4, 87.2), 22, 7, -8), "#ffe6dc", opacity=80),
        item("Nose tip shine", ell(*p2c(209.8, 92.4), 6, 4, 0), "#ffffff", opacity=70),
        item("Philtrum", line((210.3, 94.4), (210.8, 97), (211, 99.6)), None, stroke="#4a1f14", stroke_width=3.5, opacity=85),
        item("Lip L", line((211, 99.6), (208, 102.4), (203.5, 101.8)), None, stroke="#4a1f14", stroke_width=4, opacity=85),
        item("Lip R", line((211, 99.6), (214, 101.6), (218, 100.4)), None, stroke="#4a1f14", stroke_width=4, opacity=85),
    ]
    rng = random.Random(9)
    for i in range(18):
        side = -1 if i < 9 else 1
        x = (202 if side < 0 else 214) + (i % 3) * 2.2 + rng.uniform(-0.5, 0.5)
        y = 97 + (i // 3 % 3) * 2.1 + rng.uniform(-0.4, 0.4)
        items.append(item(f"Whisker follicle {i+1}", ell(*p2c(x, y), 3.6, 3.2), "#8a5236", opacity=70))
    return items


# ------------------------------------------------------------------ scene
def scene(rng):
    L = []
    sky = [["#0a0f2c", 0], ["#18225a", 40], ["#3a3580", 70], ["#7b5aa0", 100]]
    L.append({"layer": "Background art/Sky", "clear": True, "items": [
        item("Sky", "M 0 0 L 2000 0 L 2000 2000 L 0 2000 Z", {"type": "linear", "angle": -90, "stops": sky}),
        item("Horizon warmth", ell(400, 1500, 1300, 600), {"type": "radial", "stops": [["#c77aa0", 0, 55], ["#c77aa0", 100, 0]]}),
        item("Moon wash", ell(1560, 420, 900, 700), {"type": "radial", "stops": [["#9fb8ff", 0, 45], ["#9fb8ff", 100, 0]]})]})
    stars = []
    for i in range(140):
        x, y = rng.uniform(0, 2000), rng.uniform(0, 1100)
        r = rng.choice([1.6, 2, 2.4, 3, 3.6, 4.4])
        stars.append(item(f"Star {i+1}", ell(x, y, r, r), rng.choice(["#ffffff", "#fff4d6", "#d6e4ff"]), opacity=rng.randint(40, 100)))
    L.append({"layer": "Background art/Stars", "clear": True, "items": stars})
    mx, my, mr = 1560, 420, 150
    moon = [item("Moon halo", ell(mx, my, mr * 3.4, mr * 3.4), {"type": "radial", "stops": [["#e9f0ff", 0, 60], ["#bcd0ff", 30, 25], ["#bcd0ff", 100, 0]]}),
            item("Moon", ell(mx, my, mr, mr), {"type": "radial", "stops": [["#fffef6", 0], ["#f6efd8", 70], ["#e3d8b8", 100]]})]
    for i in range(9):
        a, r = rng.uniform(0, 6.28), rng.uniform(0, mr * 0.75)
        cr = rng.uniform(20, 48)
        moon.append(item(f"Maria {i+1}", ell(mx + math.cos(a) * r, my + math.sin(a) * r, cr, cr * rng.uniform(0.7, 1)),
                         {"type": "radial", "stops": [["#c9bb94", 0, 55], ["#c9bb94", 100, 0]]}))
    L.append({"layer": "Background art/Moon", "clear": True, "items": moon})
    clouds = []
    for i, (cx, cy, w, h) in enumerate([(300, 760, 520, 90), (1700, 720, 480, 80), (1000, 330, 380, 60), (700, 560, 300, 50),
                                        (1500, 980, 420, 70)]):
        for j in range(7):
            ox, oy = rng.uniform(-w, w) * 0.8, rng.uniform(-h, h) * 0.5
            clouds.append(item(f"Cloud {i+1}.{j+1}", ell(cx + ox, cy + oy, w * rng.uniform(0.35, 0.6), h * rng.uniform(0.6, 1.1)),
                               {"type": "radial", "stops": [["#b7a6e6", 0, 45], ["#6e5aa8", 100, 0]]}))
    L.append({"layer": "Background art/Clouds", "clear": True, "items": clouds})

    def ridge(pts, name, top, bot):
        d = smooth_closed(pts + [(2200, 2200), (-200, 2200)])
        return item(name, d, {"type": "linear", "angle": -90, "stops": [[top, 0], [bot, 100]]})
    L.append({"layer": "Background art/Hills", "clear": True, "items": [
        ridge([(-200, 1180), (250, 1040), (600, 1120), (950, 1010), (1350, 1100), (1750, 990), (2200, 1120)], "Far hills", "#4a3f86", "#231d4d"),
        ridge([(-200, 1400), (300, 1290), (700, 1370), (1150, 1280), (1600, 1380), (2200, 1300)], "Near hills", "#2b2560", "#120f2e")]})
    bokeh = []
    for i in range(26):
        x, y = rng.uniform(0, 2000), rng.uniform(800, 2000)
        if 300 < x < 1500 and y < 1500:
            continue
        r = rng.uniform(18, 70)
        col = rng.choice(["#ffd27a", "#ffe9a8", "#c9ff9a", "#9fe9ff"])
        bokeh.append(item(f"Bokeh {i+1}", ell(x, y, r, r), {"type": "radial", "stops": [[col, 0, 55], [col, 80, 35], [col, 100, 0]]}))
    L.append({"layer": "Bokeh", "clear": True, "items": bokeh})
    return L


# ------------------------------------------------------------------ assemble
def main():
    rng = random.Random(42)
    head, body, chest = poly(HEAD), poly(BODY), poly(CHEST)
    earl, earr = poly(EAR_L), poly(EAR_R)
    nose = p2c(*NOSE_ORIGIN)
    layers = scene(rng)

    layers.append({"layer": "Cat/Body", "clear": True, "clip": smooth_closed(body), "group_blur": 22,
                   "items": underpaint("Body", body, 38, rng)})
    layers.append({"layer": "Cat/Body", "items": fur("Body fur", body, radial_flow(*p2c(205, 95), down=0.9), 4200,
                                                    (28, 58), (3.2, 5.2), rng, edge_out=0.8)})
    layers.append({"layer": "Cat/Chest fur", "clear": True, "clip": smooth_closed(chest), "group_blur": 24,
                   "items": underpaint("Chest", chest, 34, rng)})
    layers.append({"layer": "Cat/Chest fur", "items": fur("Chest fur", chest, radial_flow(*p2c(228, 100), down=1.6), 1900,
                                                         (30, 64), (3, 5), rng, edge_out=1.0)})
    layers.append({"layer": "Cat/Ears", "clear": True, "clip": smooth_closed(earl), "group_blur": 8,
                   "items": underpaint("Ear L", earl, 20, rng)})
    layers.append({"layer": "Cat/Ears", "clip": smooth_closed(earr), "group_blur": 8, "items": underpaint("Ear R", earr, 20, rng)})
    for nm, pts, tip in (("Ear L", earl, p2c(125.8, 35)), ("Ear R", earr, p2c(221.7, 3.3))):
        layers.append({"layer": "Cat/Ears", "items": fur(nm + " fur", pts, toward(*tip), 420, (16, 34), (2.6, 4), rng, edge_out=0.35)
                       + fur(nm + " tufts", pts, toward(*tip), 60, (50, 95), (3, 4.5), rng, light=1.25, min_l=0.82, sat=0.5)})
    layers.append({"layer": "Cat/Head", "clear": True, "clip": smooth_closed(head), "group_blur": 15,
                   "items": underpaint("Head", head, 22, rng)})
    layers.append({"layer": "Cat/Head", "items": fur("Head fur", head, radial_flow(*nose, down=0.15), 6500,
                                                    (12, 28), (2.0, 3.4), rng, edge_out=0.9)})
    cheeks = poly([(141, 80), (150, 100), (160, 114), (176, 120), (170, 104), (156, 90), (147, 78)])
    cheek_r = poly([(244, 76), (255, 92), (252, 108), (240, 118), (236, 100)])
    layers.append({"layer": "Cat/Head", "items": fur("Cheek ruff L", cheeks, radial_flow(*nose, down=0.35), 420, (30, 60), (2.6, 4), rng, edge_out=1.0)
                   + fur("Cheek ruff R", cheek_r, radial_flow(*nose, down=0.3), 260, (28, 54), (2.6, 4), rng, edge_out=1.0)})
    layers.append({"layer": "Cat/Nose & mouth", "clear": True, "items": nose_mouth()})
    erng = random.Random(5)
    eyes = eye("L", *p2c(178.4, 77.4), 128, 92, -16, (3, 0, 14, 31), erng) + eye("R", *p2c(220.3, 63.6), 96, 88, -18, (-4, 0, 11, 29), erng)
    layers.append({"layer": "Cat/Eyes", "clear": True, "items": eyes})
    layers.append({"layer": "Cat/Whiskers", "clear": True, "items": whiskers(random.Random(3))})

    spec = {"doc": DOC, "layers": layers}
    out = HERE / "drawing.json"
    out.write_text(json.dumps(spec), encoding="utf-8")
    n = sum(len(l["items"]) for l in layers)
    print(f"wrote {out.name}: {len(layers)} layer entries, {n} items, {out.stat().st_size//1024} KB")


if __name__ == "__main__":
    main()
