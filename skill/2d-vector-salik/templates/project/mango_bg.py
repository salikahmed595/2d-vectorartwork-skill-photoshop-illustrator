"""Jungle sunrise scene for the Mango PFP, canvas px (2000x2000). Crisp illustrated depth - value, scale, overlap and
atmospheric colour, never Gaussian blur on scenery (skill rule 12). Imported by mango_design.build()."""
import math
import random

from vec import it, path, taper, ellipse, poly, lin, rad, sample, canvas_xy, leaf_items

W = 2000
SUN = (1450, 990)


def sky_items():
    return [it("Sky", poly([(0, 0), (W, 0), (W, W), (0, W)]),
               lin([["#3a1c5e", 0], ["#7d3270", 20], ["#d4524c", 42], ["#ff8a2e", 58], ["#ffbe48", 70], ["#ffe6a2", 80], ["#ffd27a", 100]]))]


def sun_items():
    sx, sy = SUN
    items = [it("Sun halo", ellipse(sx, sy, 620, 620), rad([["#fff3c0", 0, 85], ["#ffd27a", 35, 45], ["#ff9a3a", 100, 0]]), blend="screen")]
    rr = random.Random(3)
    for k in range(20):
        a = math.radians(k * 18 + rr.uniform(-4, 4))
        da = math.radians(rr.uniform(1.6, 3.4))
        L = rr.uniform(900, 1500)
        items.append(it(f"Ray {k}", poly([(sx, sy), (sx + math.cos(a - da) * L, sy + math.sin(a - da) * L),
                                          (sx + math.cos(a + da) * L, sy + math.sin(a + da) * L)]), "#fff3c0",
                        opacity=rr.choice((10, 14, 18)), blend="screen"))
    items += [it("Sun ring", ellipse(sx, sy, 200, 200), "#ffe9a0", opacity=55),
              it("Sun", ellipse(sx, sy, 168, 168), rad([["#ffffff", 0], ["#fff8d6", 45], ["#ffd65a", 100]])),
              it("Sun shine", ellipse(sx - 50, sy - 56, 46, 30, -30), "#ffffff", opacity=70)]
    return items


def cloud(tag, x, y, w, h, rr):
    n = max(3, int(w / 95))
    x0, x1 = x - w / 2, x + w / 2
    top = [(x0, y, 'c')]
    for i in range(n):
        cx = x0 + w * (i + 0.5) / n
        top.append((cx - w / n * 0.42, y - h * rr.uniform(0.35, 0.55)))
        top.append((cx, y - h * rr.uniform(0.85, 1.25) * (1 - abs(i - (n - 1) / 2) / n)))
    top.append((x1, y, 'c'))
    bottom = [(x1 - w * 0.18, y + h * 0.16), (x0 + w * 0.18, y + h * 0.16)]
    pts = top + bottom
    return [it(f"Cloud {tag}", path(pts), lin([["#ffb27a", 0], ["#e8786c", 55], ["#b84c74", 100]])),
            it(f"Cloud {tag} lit edge", taper([(x0 + w * 0.12, y + h * 0.05), (x, y + h * 0.2), (x1 - w * 0.1, y + h * 0.06)], canvas_xy, 9, 0.2, 0.2),
               "#ffd890", opacity=90),
            it(f"Cloud {tag} top light", taper(top[2:-2], canvas_xy, 5, 0.2, 0.2), "#ffd2a8", opacity=60)]


def cloud_items():
    rr = random.Random(11)
    items = []
    for k, (x, y, w, h) in enumerate([(300, 470, 520, 70), (760, 330, 380, 46), (1260, 560, 600, 76), (1660, 380, 380, 50),
                                      (180, 800, 360, 44), (820, 720, 420, 48), (1760, 760, 460, 56)]):
        items += cloud(k, x, y, w, h, rr)
    return items


def crowns(tag, y, amp, r0, r1, col, rr, rim=None, rim_op=70, x0=-120, x1=2120):
    """A canopy line: overlapping round tree crowns over a solid base that runs to the bottom of the canvas."""
    items = [it(f"{tag} mass", poly([(x0, y), (x1, y), (x1, W), (x0, W)]), col)]
    x = x0
    while x < x1:
        r = rr.uniform(r0, r1)
        cy = y - rr.uniform(0.2, 1.0) * amp
        items.append(it(f"{tag} crown {int(x)}", ellipse(x, cy, r, r * 0.82), col))
        if rim:
            # lit on the sun side of each crown
            side = 1 if x < SUN[0] else -1
            arc = [(x + side * math.cos(math.radians(a)) * r * 0.96, cy - math.sin(math.radians(a)) * r * 0.8) for a in (10, 45, 80)]
            items.append(it(f"{tag} rim {int(x)}", taper(arc, canvas_xy, r * 0.12, 0.3, 0.3), rim, opacity=rim_op))
        x += r * rr.uniform(1.0, 1.5)
    return items


def palm(tag, x, y, h, lean, col, rr):
    top = (x + lean, y - h)
    items = [it(f"{tag} trunk", taper([(x, y), (x + lean * 0.3, y - h * 0.5), top], canvas_xy, 16, 0.0, 0.1), col)]
    for k in range(8):
        a = math.radians(-180 + k * 25 + rr.uniform(-6, 6))
        L = rr.uniform(110, 160)
        tip = (top[0] + math.cos(a) * L, top[1] + math.sin(a) * L * 0.6 + 40)
        mid = (top[0] + math.cos(a) * L * 0.55, top[1] + math.sin(a) * L * 0.5 - 14)
        items.append(it(f"{tag} frond {k}", taper([top, mid, tip], canvas_xy, 22, 0.1, 0.6), col))
    return items


def far_jungle_items():
    rr = random.Random(21)
    items = crowns("Far1", 1150, 110, 60, 110, "#e58a68", rr)
    for k, (x, h, lean) in enumerate([(420, 260, -20), (610, 300, 15), (1100, 240, 10), (1890, 280, -18)]):
        items += palm(f"Far palm {k}", x, 1160, h, lean, "#d2765e", rr)
    items += crowns("Far2", 1250, 120, 70, 120, "#bf6458", rr, rim="#ffb27a", rim_op=60)
    for k, (x, h, lean) in enumerate([(260, 330, 16), (860, 300, -12), (1800, 340, 20)]):
        items += palm(f"Mid palm {k}", x, 1270, h, lean, "#a1505a", rr)
    return items


def mist_items():
    items = []
    for k, (y, col, op) in enumerate([(1168, "#ffe0b8", 55), (1262, "#ffd0a8", 50), (1360, "#f4b896", 45)]):
        pts = [(-50, y + 30)] + [(x, y + 14 * math.sin(x / 140 + k * 2) - 10 * math.cos(x / 61 + k)) for x in range(0, 2100, 100)] + \
              [(2050, y + 30), (2050, y + 70, 'c'), (-50, y + 70, 'c')]
        items.append(it(f"Mist band {k}", path(pts), col, opacity=op))
        items.append(it(f"Mist edge {k}", taper([(x, y + 14 * math.sin(x / 140 + k * 2) - 10 * math.cos(x / 61 + k)) for x in range(100, 1900, 150)],
                                                canvas_xy, 4, 0.1, 0.1), "#fff2d8", opacity=60))
    return items


def mid_jungle_items():
    rr = random.Random(31)
    items = crowns("Mid1", 1360, 140, 80, 140, "#6a4a58", rr, rim="#ff9a5a", rim_op=70)
    items += crowns("Mid2", 1470, 150, 90, 160, "#3c4a44", rr, rim="#ff9a4a", rim_op=80)
    return items


def trunk(tag, x_bot, x_top, w_bot, w_top, col, col_dk, lit_side, rr, moss=True):
    """Tall tree trunk from the canvas bottom to beyond the top, with buttress roots, bark and a sun-side rim."""
    L = [(x_bot - w_bot * 0.9, W + 20, 'c'), (x_bot - w_bot * 0.62, 1880), (x_bot - w_bot * 0.5, 1700), (x_bot + (x_top - x_bot) * 0.35 - w_top * 0.6, 1100),
         (x_top - w_top * 0.5, 500), (x_top - w_top * 0.5, -20, 'c')]
    R = [(x_top + w_top * 0.5, -20, 'c'), (x_top + w_top * 0.5, 500), (x_bot + (x_top - x_bot) * 0.35 + w_top * 0.6, 1100), (x_bot + w_bot * 0.5, 1700),
         (x_bot + w_bot * 0.62, 1880), (x_bot + w_bot * 0.9, W + 20, 'c')]
    shape = L + R
    lit = R if lit_side > 0 else L
    shade_side = L if lit_side > 0 else R
    items = [it(f"{tag}", path(shape), lin([[col, 0], [col_dk, 100]], 0 if lit_side < 0 else 180)),
             it(f"{tag} shade", taper([(p[0] - lit_side * w_top * 0.18, p[1]) for p in shade_side[1:-1]], canvas_xy, w_top * 0.35, 0.05, 0.05), col_dk, opacity=80)]
    for k in range(7):
        f = (k + 0.5) / 7 - 0.5
        pts = [(x_top + f * w_top * 0.8 + rr.uniform(-6, 6), y) for y in range(0, 1800, 200)]
        pts = [(px + (x_bot - x_top) * (py / 1800) ** 1.6 + f * (w_bot - w_top) * (py / 1800) ** 2, py) for px, py in pts]
        items.append(it(f"{tag} bark {k}", taper(pts, canvas_xy, rr.uniform(4, 7), 0.1, 0.1), col_dk, opacity=70))
    rim_w, rim_op = (12, 70) if moss else (7, 45)
    items.append(it(f"{tag} rim", taper([(p[0] - lit_side * rim_w * 0.4, p[1]) for p in lit[1:-1]], canvas_xy, rim_w, 0.05, 0.3), "#ff9a4a", opacity=rim_op))
    if moss:
        items.append(it(f"{tag} rim hot", taper([(p[0] - lit_side * 5, p[1]) for p in lit[2:4]], canvas_xy, 4, 0.2, 0.3), "#ffd890", opacity=70))
        # epiphyte leaf tufts on the shaded side instead of moss blobs
        for k in range(3):
            y = 760 + k * 340
            xm = x_top + (x_bot - x_top) * (y / 1800) ** 1.6 - lit_side * w_top * 0.42
            for j in range(4):
                items += leaf_items(f"{tag} tuft {k}{j}", (xm, y), -lit_side * 0 + (-160 + j * 30 if lit_side > 0 else -20 - j * 30), rr.uniform(70, 100), 34,
                                    rr.uniform(-20, 20), canvas_xy, light="#3f7a3a", dark="#24502c", line="#0c2216", rib="#7ab060", lw=2.5, veins=2)
    return items


def tall_tree_items():
    rr = random.Random(41)
    items = []
    items += trunk("Tree L far", 430, 400, 110, 70, "#6a4650", "#4a2e3c", 1, rr, moss=False)
    items += trunk("Tree R far", 1610, 1640, 110, 72, "#6a4650", "#4a2e3c", -1, rr, moss=False)
    items += trunk("Tree L", 170, 220, 300, 170, "#4a3032", "#22161c", 1, rr)
    items += trunk("Tree R", 1840, 1790, 300, 170, "#4a3032", "#22161c", -1, rr)
    return items


def canopy_items():
    """Big jungle leaves framing the top corners, lit on their lower edges by the low sun."""
    rr = random.Random(51)
    items = [it("Canopy mass L", ellipse(60, 0, 420, 190, 8), "#142a20"), it("Canopy mass R", ellipse(1940, 0, 420, 190, -8), "#142a20")]
    for side, cx in ((-1, 60), (1, 1940)):
        for k in range(12):
            a = math.radians(-10 + k * 16) if side < 0 else math.radians(190 - k * 16)
            bx, by = cx + math.cos(a) * 340, max(-40, math.sin(a) * 160)
            items += leaf_items(f"Canopy edge {'L' if side < 0 else 'R'}{k}", (bx, by), math.degrees(a) + rr.uniform(-12, 12),
                                rr.uniform(150, 220), rr.uniform(70, 95), -side * rr.uniform(5, 25), canvas_xy,
                                light="#24563a", dark="#163a26", line="#0a1e12", rib="#5a8a4a", rim="A" if side < 0 else "B", lw=3, veins=3)
    for side, ox in ((-1, 60), (1, 1940)):
        for k in range(9):
            ang = (90 + side * -1 * (10 + k * 13)) if side < 0 else (90 + (10 + k * 13))
            ang = 90 - (8 + k * 12) if side < 0 else 90 + (8 + k * 12)
            base = (ox + side * -1 * rr.uniform(0, 160) * -1, rr.uniform(-40, 90))
            items += leaf_items(f"Canopy {'L' if side < 0 else 'R'}{k}", base, ang, rr.uniform(260, 380), rr.uniform(110, 150),
                                -side * rr.uniform(10, 30), canvas_xy, light="#2f6a3e", dark="#1b4428", line="#0c2216",
                                rib="#6fa65a", rim="A" if side < 0 else "B", lw=4, veins=4)
    return items


def vine(tag, x, y0, length, sway, rr, col="#2c4a26", leaf_col=("#4f8a3a", "#2f6030"), w=7):
    pts = [(x, y0), (x + sway * 0.4, y0 + length * 0.4), (x + sway, y0 + length * 0.75), (x + sway * 0.8, y0 + length)]
    items = [it(f"{tag}", taper(pts, canvas_xy, w, 0.0, 0.6), col)]
    S = sample(pts, canvas_xy, False, 30)
    for k, i in enumerate(range(6, len(S) - 2, 7)):
        x1, y1 = S[i]
        s = 1 if k % 2 else -1
        a = math.radians(90 + s * rr.uniform(35, 60))
        L = rr.uniform(26, 38) * (1 - 0.4 * i / len(S))
        tip = (x1 + math.cos(a) * L * s * -1 + s * L * 0.6, y1 + math.sin(a) * L)
        mid = ((x1 + tip[0]) / 2, (y1 + tip[1]) / 2)
        nx, ny = -(tip[1] - y1) / L * 0.38 * L, (tip[0] - x1) / L * 0.38 * L
        items.append(it(f"{tag} leaf {k}", path([(x1, y1, 'c'), (mid[0] + nx, mid[1] + ny), tip + ('c',), (mid[0] - nx, mid[1] - ny)]),
                        leaf_col[k % 2]))
        items.append(it(f"{tag} leaf rib {k}", taper([(x1, y1), tip], canvas_xy, 1.6, 0.1, 0.4), "#9ac46a", opacity=70))
    return items


def swag(tag, a, b, dip, rr):
    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + dip)
    pts = [a, ((a[0] + m[0]) / 2, m[1] - dip * 0.15), m, ((m[0] + b[0]) / 2, m[1] - dip * 0.15), b]
    items = [it(f"{tag}", taper(pts, canvas_xy, 9, 0.05, 0.05), "#2c4a26"),
             it(f"{tag} lit", taper([(x, y - 3) for x, y in pts], canvas_xy, 3, 0.1, 0.1), "#ffb060", opacity=70)]
    return items


def vines_back_items():
    rr = random.Random(61)
    items = []
    items += swag("Swag L", (150, 230), (560, 170), 150, rr)
    items += swag("Swag R", (1440, 170), (1850, 240), 150, rr)
    for k, (x, y0, ln, sw) in enumerate([(300, 150, 700, 20), (470, 120, 520, -14), (560, 170, 360, 10),
                                         (1450, 170, 420, -10), (1560, 120, 640, 16), (1700, 150, 900, -20)]):
        items += vine(f"Vine back {k}", x, y0, ln, sw, rr)
    return items


def vines_front_items():
    rr = random.Random(71)
    items = []
    for k, (x, y0, ln, sw) in enumerate([(90, 80, 1250, 24), (240, 60, 520, -10), (1910, 80, 1150, -24), (1770, 60, 600, 12)]):
        items += vine(f"Vine front {k}", x, y0, ln, sw, rr, col="#1c3418", leaf_col=("#2f6a34", "#1c4424"), w=10)
    return items


def ground_items():
    rr = random.Random(81)
    items = [it("Ground", path([(-40, 1700), (300, 1660), (700, 1672), (1000, 1660), (1300, 1670), (1700, 1656), (2040, 1700),
                                (2040, 2040, 'c'), (-40, 2040, 'c')]), lin([["#2c3a2a", 0], ["#141c16", 100]]))]
    for k in range(60):
        x = rr.uniform(0, 2000)
        y = 1680 + rr.uniform(-10, 40)
        h = rr.uniform(30, 70)
        lean = rr.uniform(-16, 16)
        items.append(it(f"Grass {k}", taper([(x, y), (x + lean * 0.5, y - h * 0.6), (x + lean, y - h)], canvas_xy, rr.uniform(5, 8), 0.0, 0.8),
                        rr.choice(("#2a4a2a", "#3a5a30", "#1e3a22"))))
        if rr.random() < 0.35:
            items.append(it(f"Grass {k} rim", taper([(x + 2, y - h * 0.3), (x + lean + 1, y - h)], canvas_xy, 2, 0.1, 0.6), "#ffb060", opacity=70))
    return items


LOG_Y, LOG_X0, LOG_X1, LOG_R = 1612, 600, 1390, 78


def log_items():
    rr = random.Random(91)
    y, x0, x1, r = LOG_Y, LOG_X0, LOG_X1, LOG_R
    body = [(x0, y - r), (1000, y - r - 4), (x1, y - r), (x1, y + r), (1000, y + r + 4), (x0, y + r)]
    items = [it("Log shadow", ellipse(1000, y + r + 18, 470, 30), "#0c120e", opacity=60),
             it("Log", poly(body), lin([["#b0703a", 0], ["#8a5028", 35], ["#5a3018", 80], ["#3a1e10", 100]]))]
    for k in range(9):
        yy = y - r * 0.7 + k * r * 0.18
        pts = [(x, yy + 4 * math.sin(x / 50 + k)) for x in range(int(x0) + 20, int(x1) - 20, 90)]
        items.append(it(f"Bark groove {k}", taper(pts, canvas_xy, rr.uniform(3, 6), 0.1, 0.1), "#3e2010", opacity=80))
    items += [it("Log top light", taper([(x0 + 10, y - r + 6), (1000, y - r + 2), (x1 - 10, y - r + 6)], canvas_xy, 12, 0.05, 0.05), "#ffc070", opacity=85),
              it("Knot", ellipse(820, y + 10, 22, 14), "#3e2010"), it("Knot ring", ellipse(820, y + 10, 30, 20), None, stroke="#5a3018", stroke_width=4),
              it("Log line", poly(body), None, stroke="#24120a", stroke_width=6)]
    # cut end facing the viewer on the right, with growth rings
    items += [it("Log end", ellipse(x1, y, 36, r), lin([["#f0c48a", 0], ["#d29a5a", 100]], 0)),
              *[it(f"Ring {k}", ellipse(x1 + 2, y, 36 * f, r * f), None, stroke="#a8703a", stroke_width=2.5) for k, f in enumerate((0.75, 0.5, 0.26))],
              it("Log end line", ellipse(x1, y, 36, r), None, stroke="#24120a", stroke_width=5),
              it("Log end rim", taper([(x1 + 30, y - r * 0.7), (x1 + 36, y), (x1 + 30, y + r * 0.6)], canvas_xy, 7, 0.2, 0.2), "#ffe0a0", opacity=90)]
    # moss on top and a small sprout
    for k, (mx, mw) in enumerate([(660, 90), (900, 70), (1140, 110), (1300, 60)]):
        items.append(it(f"Moss {k}", path([(mx - mw, y - r + 8), (mx - mw * 0.6, y - r - 12), (mx, y - r - 16), (mx + mw * 0.6, y - r - 10),
                                           (mx + mw, y - r + 8), (mx + mw * 0.4, y - r + 22), (mx - mw * 0.4, y - r + 20)]), "#5a9a3a"))
        items.append(it(f"Moss {k} light", taper([(mx - mw * 0.6, y - r - 8), (mx, y - r - 13), (mx + mw * 0.5, y - r - 7)], canvas_xy, 5, 0.2, 0.2), "#a8d870"))
    items += [it("Sprout stem", taper([(680, y - r - 4), (676, y - r - 50), (690, y - r - 86)], canvas_xy, 6, 0.0, 0.3), "#4a8a34")]
    items += leaf_items("Sprout leaf L", (688, y - r - 80), -150, 54, 26, -10, canvas_xy, lw=2.5, veins=2)
    items += leaf_items("Sprout leaf R", (690, y - r - 84), -40, 58, 28, 14, canvas_xy, lw=2.5, veins=2, rim="A")
    return items


def contact_items():
    from mango_char import M
    return [it("Foot contact L", ellipse(*M(-116, 438), 82, 12), "#1a0c06", opacity=55),
            it("Foot contact R", ellipse(*M(128, 434), 82, 12), "#1a0c06", opacity=55)]


def foreground_items():
    rr = random.Random(101)
    items = []
    for k, (base, ang, ln, wd, curl) in enumerate([((-60, 2060), -60, 520, 210, 20), ((-80, 1900), -30, 460, 180, 26), ((60, 2080), -88, 420, 170, -14),
                                                   ((-40, 1760), -8, 380, 150, 30), ((260, 2090), -110, 300, 130, -18)]):
        items += leaf_items(f"FG leaf L{k}", base, ang, ln, wd, curl, canvas_xy, light="#245a34", dark="#143a22", line="#081a10",
                            rib="#4f8a4a", rim="A", lw=5, veins=6)
    for k, (base, ang, ln, wd, curl) in enumerate([((2060, 2060), -120, 520, 210, -20), ((2080, 1900), -150, 460, 180, -26), ((1940, 2080), -92, 420, 170, 14),
                                                   ((2040, 1760), -172, 380, 150, -30), ((1740, 2090), -70, 300, 130, 18)]):
        items += leaf_items(f"FG leaf R{k}", base, ang, ln, wd, curl, canvas_xy, light="#245a34", dark="#143a22", line="#081a10",
                            rib="#4f8a4a", rim="B", lw=5, veins=6)
    return items


def star4(x, y, s, waist=0.18):
    return poly([(x, y - s), (x + s * waist, y - s * waist), (x + s, y), (x + s * waist, y + s * waist),
                 (x, y + s), (x - s * waist, y + s * waist), (x - s, y), (x - s * waist, y - s * waist)])


def particle_items():
    """Pollen and fireflies: three size classes, clustered around the sun and the hero, with a core and a halo."""
    rr = random.Random(111)
    items = []
    pts = []
    while len(pts) < 70:
        if rr.random() < 0.5:
            a, d = rr.uniform(0, 2 * math.pi), rr.uniform(220, 650)
            x, y = SUN[0] + math.cos(a) * d, SUN[1] + math.sin(a) * d * 0.8
        else:
            x, y = rr.uniform(120, 1880), rr.uniform(300, 1600)
        if 560 < x < 1420 and 420 < y < 1580:  # keep the character readable
            continue
        if all(math.hypot(x - px, y - py) > 60 for px, py in pts):
            pts.append((x, y))
    for k, (x, y) in enumerate(pts):
        v = rr.random()
        if v < 0.55:
            r = rr.uniform(1.8, 2.8)
            items.append(it(f"Pollen {k}", ellipse(x, y, r, r), "#fff2c0", opacity=80))
        else:
            r = rr.uniform(3, 4.5) if v < 0.9 else rr.uniform(5, 7)
            items.append(it(f"Firefly halo {k}", ellipse(x, y, r * 3.4, r * 3.4), "#ffc24a", opacity=30, blend="screen"))
            items.append(it(f"Firefly {k}", ellipse(x, y, r, r), "#fff6d0"))
            if v >= 0.9:
                items.append(it(f"Glint {k}", star4(x, y, r * 4.2), "#fffbe8", opacity=90))
    # a few leaves blowing left with the wind that lifts the cape
    for k, (x, y, rot, s) in enumerate([(380, 980, -30, 1.0), (300, 1240, 20, 0.8), (1580, 820, -50, 0.9), (1700, 1320, 10, 0.7), (520, 640, 40, 0.7)]):
        c, si = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        shp = [(0, -22 * s, 'c'), (10 * s, 0), (0, 22 * s, 'c'), (-10 * s, 0)]
        P = [(x + p[0] * c - p[1] * si, y + p[0] * si + p[1] * c) + tuple(p[2:]) for p in shp]
        items.append(it(f"Blown leaf {k}", path(P), "#5a9a3a"))
        items.append(it(f"Blown leaf {k} rib", taper([P[0][:2], P[2][:2]], canvas_xy, 1.5, 0.1, 0.1), "#b8e080"))
    return items


def fern(tag, x, y, size, rr, col=("#2f5a30", "#1f4224"), rim=True):
    items = []
    for f in range(5):
        ang = -90 + (f - 2) * 28 + rr.uniform(-8, 8)
        sp_pts = [(x, y)]
        a = math.radians(ang)
        L = size * rr.uniform(0.8, 1.1)
        curl = (f - 2) * 18
        px, py = x, y
        for k in range(1, 9):
            aa = math.radians(ang + curl * (k / 8) ** 1.5)
            px, py = px + math.cos(aa) * L / 8, py + math.sin(aa) * L / 8
            sp_pts.append((px, py))
        items.append(it(f"{tag} frond {f}", taper(sp_pts, canvas_xy, 4, 0.0, 0.5), col[1]))
        S = sample(sp_pts, canvas_xy, False, 4)
        for i in range(3, len(S) - 2, 3):
            sx, sy = S[i]
            dx, dy = S[i + 1][0] - S[i - 1][0], S[i + 1][1] - S[i - 1][1]
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            l = size * 0.16 * (1 - i / len(S) * 0.7)
            for s in (1, -1):
                tip = (sx + nx * s * l + dx / ln * l * 0.5, sy + ny * s * l + dy / ln * l * 0.5)
                items.append(it(f"{tag} pinna {f}.{i}{s}", taper([(sx, sy), tip], canvas_xy, l * 0.45, 0.2, 0.7), col[0 if s > 0 else 1]))
        if rim:
            items.append(it(f"{tag} rim {f}", taper(sp_pts[2:], canvas_xy, 2.5, 0.1, 0.5), "#ffb060", opacity=60))
    return items


def flower(tag, x, y, r, rr):
    items = []
    for k in range(5):
        a = math.radians(k * 72 + rr.uniform(-6, 6) - 90)
        tip = (x + math.cos(a) * r, y + math.sin(a) * r)
        mid = (x + math.cos(a) * r * 0.55, y + math.sin(a) * r * 0.55)
        nx, ny = -math.sin(a) * r * 0.34, math.cos(a) * r * 0.34
        items.append(it(f"{tag} petal {k}", path([(x, y, 'c'), (mid[0] + nx, mid[1] + ny), tip, (mid[0] - nx, mid[1] - ny)]),
                        lin([["#ffb03a", 0], ["#ff6a1f", 100]])))
        items.append(it(f"{tag} petal vein {k}", taper([(x, y), mid], canvas_xy, 1.6, 0.1, 0.5), "#c2400e", opacity=60))
    items += [it(f"{tag} centre", ellipse(x, y, r * 0.22, r * 0.22), "#ffe46a"),
              it(f"{tag} centre dot", ellipse(x - r * 0.05, y - r * 0.06, r * 0.08, r * 0.08), "#fff8d0")]
    return items


def ground_detail_items():
    rr = random.Random(121)
    items = [it("Ground light pool", ellipse(1050, 1700, 640, 90), rad([["#ffb060", 0, 70], ["#ff9a4a", 60, 25], ["#ff9a4a", 100, 0]]), opacity=40, blend="screen")]
    for k, (x, y, s) in enumerate([(360, 1790, 280), (560, 1880, 230), (1500, 1800, 280), (1700, 1880, 240), (760, 1990, 240), (1260, 1990, 240),
                                   (1010, 2040, 300), (230, 2010, 260), (1800, 2020, 260)]):
        items += fern(f"Fern {k}", x, y, s, rr)
    for k, (x, y, r) in enumerate([(470, 1712, 34), (560, 1760, 28), (1530, 1716, 34), (1610, 1770, 27), (880, 1850, 32), (1150, 1872, 30),
                                   (300, 1860, 30), (1720, 1870, 30)]):
        items.append(it(f"Flower stem {k}", taper([(x, y + 60), (x + 4, y + 30), (x, y)], canvas_xy, 4, 0.0, 0.2), "#2f5a30"))
        items += flower(f"Flower {k}", x, y, r, rr)
    return items
