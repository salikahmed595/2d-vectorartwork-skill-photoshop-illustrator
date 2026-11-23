"""v7 background: crisp illustrated scenery with no Gaussian blur on drawn shapes (skill v3 rules 12-15).
Imported by v7_design.build(). Every path is hand-placed vector data; depth comes from value, scale and overlap."""
import math
import random

from v7_design import it, path, taper, ellipse, poly, lin, rad, canvas_xy, CYAN

MOON = (1690, 360)


# ---------- stars: designed tiers with intentional spacing ----------
def spaced_points(rr, n, box, min_d, taken, keep_out):
    pts, tries = [], 0
    while len(pts) < n and tries < n * 400:
        tries += 1
        x, y = rr.uniform(box[0], box[2]), rr.uniform(box[1], box[3])
        if keep_out(x, y) or any(math.hypot(x - a, y - b) < min_d for a, b in taken + pts):
            continue
        pts.append((x, y))
    return pts


def sparkle(x, y, s, waist=0.11):
    return poly([(x, y - s), (x + s * waist, y - s * waist), (x + s * .7, y), (x + s * waist, y + s * waist),
                 (x, y + s * 0.85), (x - s * waist, y + s * waist), (x - s * .7, y), (x - s * waist, y - s * waist)])


def star_items():
    rr = random.Random(21)
    items = []
    out = lambda x, y: math.hypot(x - MOON[0], y - MOON[1]) < 250
    taken = []
    sparkles = spaced_points(rr, 14, (60, 40, 1940, 1000), 150, taken, out)
    taken += sparkles
    glows = spaced_points(rr, 26, (30, 30, 1970, 1100), 90, taken, out)
    taken += glows
    dots = spaced_points(rr, 120, (10, 10, 1990, 1150), 42, taken, out)
    for k, (x, y) in enumerate(dots):
        r = rr.choice([1.1, 1.3, 1.5, 1.8])
        items.append(it(f"Star dot {k}", ellipse(x, y, r, r), "#f2f4ff", opacity=rr.randint(50, 90)))
    for k, (x, y) in enumerate(glows):
        items.append(it(f"Glow star halo {k}", ellipse(x, y, 8, 8), "#cfe0ff", opacity=22, blur=3))
        items.append(it(f"Glow star {k}", ellipse(x, y, 2.3, 2.3), "#ffffff"))
    for k, (x, y) in enumerate(sparkles):
        s = rr.uniform(9, 20)
        items.append(it(f"Sparkle {k}", sparkle(x, y, s), "#eef4ff", opacity=92))
        items.append(it(f"Sparkle core {k}", ellipse(x, y, s * 0.16, s * 0.16), "#ffffff"))
    for c, (cx, cy) in enumerate([(230, 700), (1830, 830)]):  # two small cluster accents
        for j, (dx, dy, r) in enumerate([(0, 0, 2.6), (22, -14, 1.6), (-18, 12, 1.4), (34, 10, 1.2), (8, 26, 1.8)]):
            items.append(it(f"Cluster {c}.{j}", ellipse(cx + dx, cy + dy, r, r), "#ffffff", opacity=90))
        items.append(it(f"Cluster sparkle {c}", sparkle(cx, cy, 12, 0.12), "#ffffff"))
    return items


# ---------- moon: limb darkening, maria, craters with rim logic, lit edge ----------
def crescent(cx, cy, r, ang, shift=0.35, n=18):
    a = math.radians(ang)
    ox, oy = cx - math.cos(a) * r * shift, cy - math.sin(a) * r * shift
    ts = [math.radians(-80 + 160 * i / n) for i in range(n + 1)]
    outer = [(cx + math.cos(a + t) * r, cy + math.sin(a + t) * r) for t in ts]
    inner = [(ox + math.cos(a + t) * r, oy + math.sin(a + t) * r) for t in reversed(ts)]
    return "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in outer + inner) + " Z"


def moon_halo_items():
    mx, my = MOON
    return [it("Moon halo", ellipse(mx, my, 420, 420), rad([["#dfe8ff", 0, 24], ["#9a8aff", 45, 9], ["#9a8aff", 100, 0]]), blend="screen"),
            it("Moon ring", ellipse(mx, my, 178, 178), None, stroke="#cfd4ff", stroke_width=2, opacity=30)]


def moon_clip():
    return ellipse(MOON[0], MOON[1], 150, 150)


def moon_items():
    mx, my = MOON
    R = 150
    items = [it("Moon", ellipse(mx, my, R, R), rad([["#f4ecd6", 0], ["#e6d8b6", 62], ["#c8b48e", 100]]))]
    maria = [[(-70, -60), (-20, -78), (10, -50), (-8, -12), (-56, -4), (-90, -28)],
             [(30, 8), (78, -4), (104, 30), (80, 70), (36, 62), (20, 34)],
             [(-60, 40), (-24, 52), (-30, 92), (-72, 86), (-88, 60)]]
    for k, m in enumerate(maria):
        items.append(it(f"Mare {k}", path([(mx + x, my + y) for x, y in m]), "#cdbb94", opacity=75))
    for k, (dx, dy, r) in enumerate([(-48, -40, 24), (44, 36, 19), (-10, 78, 14), (64, -60, 12), (-86, 28, 10),
                                     (18, -16, 8), (96, 6, 8), (-34, 108, 7), (-104, -6, 6), (40, -100, 9)]):
        x, y = mx + dx, my + dy
        items += [
            it(f"Crater {k}", ellipse(x, y, r, r * 0.9), "#bfac86"),
            it(f"Crater shadow {k}", crescent(x, y, r, 225, 0.4), "#9e8a66", opacity=85),
            it(f"Crater rim light {k}", crescent(x, y, r * 1.08, 45, 0.25), "#fff6e0", opacity=85),
        ]
    items += [
        it("Moon shade", crescent(mx, my, R, 40, 0.22, 30), "#a89878", opacity=40),
        it("Moon lit edge", crescent(mx, my, R, 220, 0.06, 30), "#fffaf0", opacity=80),
    ]
    return items


# ---------- castles: crisp, depth by value and scale, finished detail ----------
def castle_items():
    items = [
        it("Far range", path([(0, 1260), (0, 1000), (180, 880), (330, 960), (520, 840), (700, 980), (860, 920),
                              (1000, 1020), (1160, 900), (1340, 980), (1520, 840), (1700, 940), (1860, 860),
                              (2000, 940), (2000, 1260)]), lin([["#4a3a92", 0], ["#33266e", 100]])),
        it("Far range ridge light", taper([(180, 880), (260, 920), (330, 960)], canvas_xy, 4, 0.3, 0.6), "#7a68c8", opacity=70),
        it("Far range ridge light 2", taper([(1520, 840), (1440, 880), (1360, 960)], canvas_xy, 4, 0.3, 0.6), "#7a68c8", opacity=70),
    ]
    for name, x0, x1, top in (("Wall L", 20, 580, 1180), ("Wall R", 1440, 2000, 1190)):
        pts = [(x0, 1500), (x0, top)]
        x = x0
        while x < x1:
            pts += [(x, top - 16), (min(x + 22, x1), top - 16), (min(x + 22, x1), top), (min(x + 36, x1), top)]
            x += 36
        pts += [(x1, top), (x1, 1500)]
        items.append(it(name, poly(pts), "#2a1f5e"))
        items.append(it(name + " light", poly([(x0, top), (x1, top), (x1, top + 6), (x0, top + 6)]), "#46379a"))
        for k in range(int((x1 - x0) / 70)):
            sx = x0 + 40 + k * 70
            items.append(it(f"{name} slit {k}", poly([(sx - 3, top + 40), (sx + 3, top + 40), (sx + 3, top + 64), (sx - 3, top + 64)]), "#160f38"))
    gx = 300
    items.append(it("Gate", poly([(gx - 34, 1500), (gx - 34, 1290), (gx - 24, 1266), (gx, 1256), (gx + 24, 1266), (gx + 34, 1290), (gx + 34, 1500)]), "#140e34"))
    items.append(it("Gate glow", poly([(gx - 24, 1500), (gx - 24, 1296), (gx, 1272), (gx + 24, 1296), (gx + 24, 1500)]), "#ffcf7a", opacity=35))
    towers = [(70, 70, 1040, 150, 0), (290, 60, 1090, 120, 0), (500, 70, 1120, 130, 0), (1720, 70, 1060, 150, 0), (1930, 70, 1080, 140, 0),
              (170, 90, 960, 190, 1), (380, 110, 1010, 220, 1), (1480, 80, 1100, 140, 1), (1580, 110, 990, 230, 1), (1820, 100, 940, 200, 1)]
    wr = random.Random(4)
    for k, (x, w, top, sp, near) in enumerate(towers):  # far towers first: lighter, simpler (atmospheric value, not blur)
        body, lit, roof, roof_lit = (("#2c2164", "#3a2d7c", "#3a2c7a", "#5a48a8") if near else
                                     ("#3a2d7a", "#463890", "#46378c", "#6553b4"))
        items.append(it(f"Tower {k}", poly([(x - w / 2, 1500), (x - w / 2, top), (x + w / 2, top), (x + w / 2, 1500)]), body))
        items.append(it(f"Tower lit side {k}", poly([(x - w / 2, 1500), (x - w / 2, top), (x - w / 2 + w * 0.3, top), (x - w / 2 + w * 0.3, 1500)]), lit))
        items.append(it(f"Tower band {k}", poly([(x - w / 2 - 6, top), (x + w / 2 + 6, top), (x + w / 2 + 6, top + 12), (x - w / 2 - 6, top + 12)]), roof))
        items.append(it(f"Spire {k}", poly([(x - w / 2 - 10, top + 2), (x, top - sp), (x + w / 2 + 10, top + 2)]), roof))
        items.append(it(f"Spire light {k}", poly([(x, top - sp), (x - w / 2 - 10, top + 2), (x - 6, top + 2)]), roof_lit))
        for j in (0.35, 0.62):  # shingle courses across the cone
            yy = top - sp * (1 - j)
            half = (w / 2 + 10) * j
            items.append(it(f"Shingle {k}.{j}", taper([(x - half, yy + 3), (x, yy - 2), (x + half, yy + 3)], canvas_xy, 2.4, 0.2, 0.2), "#241a52", opacity=70))
        items.append(it(f"Finial {k}", taper([(x, top - sp + 2), (x, top - sp - 22)], canvas_xy, 3, 0.0, 0.3), "#5a48a8"))
        items.append(it(f"Finial ball {k}", ellipse(x, top - sp - 24, 3.5, 3.5), "#ffcf7a" if near else "#8a78d0"))
        if near and sp >= 200:
            fy = top - sp - 22
            items.append(it(f"Flag {k}", path([(x, fy), (x + 30, fy + 4), (x + 22, fy + 10), (x + 34, fy + 16), (x, fy + 14)]), "#6ff6ff", opacity=80))
        for j in range(wr.randint(1, 3) if near else 1):
            wy = top + 40 + j * 70
            col = "#ffcf7a" if wr.random() < 0.6 else CYAN
            arch = [(x - 7, wy + 24), (x - 7, wy + 8), (x - 5, wy + 3), (x, wy), (x + 5, wy + 3), (x + 7, wy + 8), (x + 7, wy + 24)]
            items.append(it(f"Window glow {k}.{j}", ellipse(x, wy + 12, 16, 18), col, opacity=18, blur=4))
            items.append(it(f"Window {k}.{j}", poly(arch), col, opacity=92))
            items.append(it(f"Window sill {k}.{j}", poly([(x - 9, wy + 24), (x + 9, wy + 24), (x + 9, wy + 27), (x - 9, wy + 27)]), "#1c1446"))
    return items


# ---------- mist: designed vector bands with curl lines (replaces a feathered Photoshop smear) ----------
def mist_items():
    rr = random.Random(12)
    items = []
    for k, (y, amp, col, op) in enumerate([(1390, 26, "#8f70d6", 60), (1600, 32, "#8062c8", 55), (1860, 30, "#7356bc", 60)]):
        top = [(x, y + math.sin(x / 140 + k) * amp + rr.uniform(-8, 8)) for x in range(-40, 2081, 120)]
        shape = [(-40, y + 240)] + top + [(2080, y + 240)]
        items.append(it(f"Mist band {k}", path(shape), lin([[col, 0, 0], [col, 30, op], [col, 100, op * 0.8]])))
        for j in range(5):
            x0 = rr.uniform(40, 1800)
            seg = [(x, y + math.sin(x / 140 + k) * amp + 18) for x in (x0, x0 + 60, x0 + 120, x0 + 180)]
            items.append(it(f"Mist curl {k}.{j}", taper(seg, canvas_xy, 4, 0.3, 0.3), "#cbb4f4", opacity=55))
    return items


# ---------- midground trees: crisp scalloped canopies, lobe definition, floret tassels ----------
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
        items.append(it(f"Branch {name}a", taper([(cx - 2, cy + R * 0.35), (cx - R * 0.25, cy + R * 0.12), (cx - R * 0.4, cy + R * 0.05)], canvas_xy, R * 0.05, 0.0, 0.8), "#22163f"))
        items.append(it(f"Branch {name}b", taper([(cx + 2, cy + R * 0.3), (cx + R * 0.3, cy + R * 0.1), (cx + R * 0.42, cy + R * 0.06)], canvas_xy, R * 0.05, 0.0, 0.8), "#22163f"))
        items.append(it(f"Canopy underside {name}", path(canopy(cx, cy + R * 0.1, R * 0.97, 7, rr)), "#33205f"))
        shape = canopy(cx, cy, R, 7, rr)
        items.append(it(f"Canopy {name}", path(shape), lin([["#5e3ea2", 0], ["#45297f", 100]])))
        items.append(it(f"Canopy light {name}", path(canopy(cx - R * 0.12, cy - R * 0.1, R * 0.7, 5, rr)), "#7353b6", opacity=92))
        items.append(it(f"Canopy top {name}", path(canopy(cx - R * 0.2, cy - R * 0.2, R * 0.38, 4, rr)), "#9274d0", opacity=85))
        for j, p in enumerate(shape):  # a short shade stroke into each valley defines every lobe
            if len(p) > 2:
                items.append(it(f"Lobe line {name}{j}", taper([(p[0], p[1]), (p[0] + (cx - p[0]) * 0.18, p[1] + (cy - p[1]) * 0.25)],
                                                              canvas_xy, 6, 0.1, 0.9), "#3a2270", opacity=80))
        for k in range(9):  # tassels: small hanging floret clusters
            tx = cx + (k - 4) / 4 * R * 0.85 + rr.uniform(-10, 10)
            ty = cy + R * rr.uniform(0.14, 0.3)
            for f in range(rr.randint(3, 5)):
                sz = 7 - f * 1.2
                items.append(it(f"Tassel {name}{k}.{f}", ellipse(tx + rr.uniform(-2, 2), ty + f * 9, sz, sz * 0.8),
                                ["#b392ea", "#9c78dc", "#8460c8", "#6c4cb0", "#5a3d9a"][f]))
    return items
