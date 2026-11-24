"""v5 'Moonlit Cat Mage' - anime cel-shaded redraw, drawn as Illustrator paths via ai_draw.py.
No AI generation: every shape below is hand-placed path data. Writes drawing.json next to this file.
Coordinates: head parts are in head-local space (origin between the eyes, tilted 4 deg);
body/cloak parts are relative to (CX, CY); scene parts are canvas px.
"""
import json
import math
import random
from pathlib import Path

HERE = Path(__file__).parent
DOC = "cat-pfp-v5.ai"
CX, CY = 1000, 790
TILT = math.radians(-4)
HS = 1.12
BWX = 0.84

# ---------- palette ----------
GINGER, GINGER_SH, GINGER_DEEP, GINGER_LT = "#f39a4c", "#d4692c", "#b9501d", "#ffc27a"
STRIPE = "#c2501b"
CREAM, CREAM_SH = "#fff3e2", "#efcca8"
LINE = "#3a1608"
NAVY, NAVY_SH, NAVY_LT = "#232d6a", "#131944", "#3c4fa2"
GOLD, GOLD_LT, GOLD_DK = "#e6b65c", "#fff0b8", "#6a4310"
CYAN, CYAN_LT = "#6ff6ff", "#d8ffff"


# ---------- coordinate transforms ----------
def head_xy(x, y):
    px, py = 0.0, 150.0
    dx, dy = (x - px) * HS, (y - py) * HS
    c, s = math.cos(TILT), math.sin(TILT)
    return (CX + px + dx * c - dy * s, CY + py + dx * s + dy * c)


def body_xy(x, y):
    return (CX + x, CY + y)


def bodyw_xy(x, y):
    return (CX + x * BWX, CY + y)


def canvas_xy(x, y):
    return (x, y)


def mirror(pts):
    return [(-p[0], p[1]) + tuple(p[2:]) for p in pts]


# ---------- path builders ----------
def segments(pts, xf, closed=True):
    P = [xf(p[0], p[1]) for p in pts]
    corner = [len(p) > 2 for p in pts]
    n = len(P)

    def tan(i):
        if corner[i] or (not closed and i in (0, n - 1)):
            return (0.0, 0.0)
        a, b = P[(i - 1) % n], P[(i + 1) % n]
        return ((b[0] - a[0]) / 6, (b[1] - a[1]) / 6)

    T = [tan(i) for i in range(n)]
    segs = []
    for i in range(n if closed else n - 1):
        j = (i + 1) % n
        segs.append((P[i], (P[i][0] + T[i][0], P[i][1] + T[i][1]), (P[j][0] - T[j][0], P[j][1] - T[j][1]), P[j]))
    return segs


def path(pts, xf=canvas_xy, closed=True):
    segs = segments(pts, xf, closed)
    d = f"M {segs[0][0][0]:.1f} {segs[0][0][1]:.1f}"
    for _, c1, c2, p in segs:
        d += f" C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p[0]:.1f} {p[1]:.1f}"
    return d + (" Z" if closed else "")


def sample(pts, xf=canvas_xy, closed=False, per=14):
    out = []
    segs = segments(pts, xf, closed)
    for p0, c1, c2, p1 in segs:
        for k in range(per):
            t = k / per
            u = 1 - t
            out.append((u ** 3 * p0[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * p1[0],
                        u ** 3 * p0[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * p1[1]))
    if not closed:
        out.append(segs[-1][3])
    return out


def taper(pts, xf=canvas_xy, w=8.0, start=0.2, end=0.2, per=14):
    """Variable-width brush line as a filled shape: swells in the middle, tapers to points."""
    S = sample(pts, xf, False, per)
    m = len(S)
    L, R = [], []
    for i, (x, y) in enumerate(S):
        a, b = S[max(i - 1, 0)], S[min(i + 1, m - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        t = i / (m - 1)
        f = 1.0
        if start > 0:
            f *= math.sin(math.pi / 2 * min(1.0, t / start))
        if end > 0:
            f *= math.sin(math.pi / 2 * min(1.0, (1 - t) / end))
        ww = max(w * f, 0.35) / 2
        L.append((x + nx * ww, y + ny * ww))
        R.append((x - nx * ww, y - ny * ww))
    pl = L + R[::-1]
    return "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pl) + " Z"


def ellipse(cx, cy, rx, ry, rot=0.0, xf=canvas_xy):
    k = 0.5523
    pts = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))

    def P(u, v):
        x, y = u * rx, v * ry
        return xf(cx + x * c - y * s, cy + x * s + y * c)

    d = ""
    for i in range(4):
        u0, v0 = pts[i]
        u1, v1 = pts[(i + 1) % 4]
        p0 = P(u0, v0)
        c1 = P(u0 - v0 * k, v0 + u0 * k)
        c2 = P(u1 + v1 * k, v1 - u1 * k)
        p1 = P(u1, v1)
        if i == 0:
            d = f"M {p0[0]:.1f} {p0[1]:.1f}"
        d += f" C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p1[0]:.1f} {p1[1]:.1f}"
    return d + " Z"


def poly(pts, xf=canvas_xy):
    P = [xf(*p) for p in pts]
    return "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in P) + " Z"


def it(name, d, fill=None, **kw):
    o = {"name": name, "d": d, "fill": fill}
    o.update(kw)
    return o


def lin(stops, angle=-90):
    return {"type": "linear", "angle": angle, "stops": stops}


def rad(stops):
    return {"type": "radial", "stops": stops}


# ---------- character shapes (head-local) ----------
rng = random.Random(55)
HL = [(0, -292), (-95, -282), (-190, -238), (-262, -164), (-306, -80), (-322, -12),
      (-374, 28, 'c'), (-330, 52, 'c'), (-392, 112, 'c'), (-322, 122, 'c'), (-354, 190, 'c'), (-272, 182, 'c'),
      (-262, 214), (-190, 244), (-100, 266)]
HR = [(p[0] + (rng.uniform(-7, 7) if len(p) > 2 else 0), p[1] + (rng.uniform(-6, 6) if len(p) > 2 else 0)) + tuple(p[2:])
      for p in mirror(HL[1:])][::-1]
HEAD = HL + [(0, 276)] + HR

EAR_L = [(-80, -236), (-150, -322), (-215, -408), (-268, -462, 'c'), (-292, -386), (-310, -270), (-328, -150), (-260, -150)]
EAR_L_IN = [(-140, -236), (-192, -322), (-252, -420, 'c'), (-270, -330), (-288, -215), (-222, -198)]
EAR_R = [(p[0] + (8 if p[1] < -440 else 0), p[1]) + tuple(p[2:]) for p in mirror(EAR_L)]
EAR_R_IN = [(p[0] + (6 if p[1] < -400 else 0), p[1]) + tuple(p[2:]) for p in mirror(EAR_L_IN)]

MUZZLE = [(0, 22), (-50, 44), (-108, 88), (-152, 142), (-142, 198), (-82, 236), (0, 250),
          (82, 236), (142, 198), (152, 142), (108, 88), (50, 44)]

EYE_L = [(-58, -16, 'c'), (-92, -78), (-150, -102), (-202, -86), (-222, -66, 'c'), (-196, -12), (-134, 18), (-86, 8)]
EYE_R = mirror(EYE_L)


def head_items():
    H = head_xy
    items = [
        it("Head base", path(HEAD, H), GINGER),
        it("Forehead light", ellipse(-70, -150, 230, 140, -10, H), GINGER_LT, opacity=70, blur=34),
        it("Right side shade", path([(140, -268), (262, -190), (340, -60), (410, 120), (330, 268), (180, 262),
                                     (232, 160), (262, 40), (246, -60), (196, -160)], H), GINGER_SH),
        it("Left jaw shade", path([(-340, 96), (-250, 168), (-176, 238), (-262, 262), (-380, 210)], H), GINGER_SH),
        it("Under-ear shade L", ellipse(-200, -230, 90, 40, 30, H), GINGER_SH, opacity=45, blur=10),
        it("Under-ear shade R", ellipse(200, -230, 90, 40, -30, H), GINGER_DEEP, opacity=40, blur=10),
        it("Shade locks", path([(246, -60, 'c'), (212, -20, 'c'), (262, 10, 'c'), (226, 60, 'c'), (270, 90, 'c'), (232, 150, 'c'),
                                (180, 262, 'c'), (330, 268), (410, 120), (340, -60)], H), GINGER_SH),
        it("Crown shade", path([(-120, -268), (0, -250), (120, -268), (60, -300), (-60, -300)], H), GINGER_SH, opacity=80),
    ]
    stripes = [
        ([(0, -272), (2, -216), (0, -164)], 26), ([(-56, -268), (-50, -214), (-36, -172)], 21),
        ([(56, -268), (50, -214), (36, -172)], 21), ([(-112, -258), (-100, -220), (-80, -190)], 15),
        ([(112, -258), (100, -220), (80, -190)], 15),
        ([(-334, -24), (-272, -2), (-206, 8)], 21), ([(-350, 58), (-288, 70), (-222, 76)], 18),
        ([(-334, 140), (-284, 142), (-240, 134)], 13),
        ([(334, -24), (272, -2), (206, 8)], 21), ([(350, 58), (288, 70), (222, 76)], 18),
        ([(334, 140), (284, 142), (240, 134)], 13),
        ([(-150, -112), (-185, -128), (-226, -122)], 9), ([(150, -112), (185, -128), (226, -122)], 9),
    ]
    for i, (pts, w) in enumerate(stripes):
        items.append(it(f"Stripe {i}", taper(pts, H, w, start=0, end=0.9), STRIPE))
    items += [
        it("Muzzle", path(MUZZLE, H), CREAM),
        it("Muzzle shade", path([(70, 150), (118, 140), (150, 170), (136, 204), (96, 228), (84, 190)], H), CREAM_SH, opacity=75),
        it("Chin shade", path([(-60, 246), (0, 256), (60, 246), (36, 266), (0, 272), (-36, 266)], H), CREAM_SH, opacity=70),
        it("Cheek blush L", ellipse(-210, 118, 52, 26, -8, H), "#ff7f86", opacity=38, blur=12),
        it("Cheek blush R", ellipse(206, 112, 46, 24, 8, H), "#ff7f86", opacity=30, blur=12),
    ]
    for i, pts in enumerate([[(-40, -250), (-70, -200), (-90, -150)], [(-120, -236), (-150, -190), (-160, -150)],
                             [(-230, -150), (-250, -110), (-252, -70)], [(-280, -60), (-292, -20), (-286, 10)],
                             [(20, -250), (30, -210), (26, -170)]]):
        items.append(it(f"Light lock {i}", taper(pts, H, 13, 0.05, 0.9), GINGER_LT, opacity=85))
    for i, pts in enumerate([[(-330, 20), (-300, 40), (-262, 44)], [(-345, 100), (-310, 112), (-270, 112)],
                             [(-320, 170), (-290, 176), (-258, 168)], [(330, 20), (300, 40), (262, 44)],
                             [(345, 100), (310, 112), (270, 112)]]):
        items.append(it(f"Cheek lock {i}", taper(pts, H, 16, 0.05, 0.9), "#ffd3a0" if pts[0][0] < 0 else GINGER, opacity=80))
    for i, (x, y) in enumerate([(-62, 148), (-84, 158), (-106, 150), (-74, 176), (-98, 182),
                                (62, 148), (84, 158), (106, 150), (74, 176), (98, 182)]):
        items.append(it(f"Whisker dot {i}", ellipse(x, y, 3.2, 3.2, 0, H), "#b98c6c"))
    for i, pts in enumerate([[(-300, -40), (-280, -30), (-262, -32)], [(-318, 40), (-298, 46), (-280, 44)],
                             [(-300, 110), (-282, 112), (-262, 106)], [(300, -36), (282, -28), (264, -30)],
                             [(312, 44), (292, 50), (276, 48)], [(-40, 210), (-30, 232), (-20, 244)],
                             [(40, 210), (30, 232), (20, 244)]]):
        items.append(it(f"Fur flick {i}", taper(pts, H, 5, 0.1, 0.8), GINGER_DEEP if abs(pts[0][0]) > 100 else CREAM_SH))
    # line art: outer contour in broken, tapered strokes (heavier on the shaded right and underside)
    left = HEAD[1:16]
    right = HEAD[15:] + [HEAD[0]]
    items += [
        it("Line L", taper(left, H, 8.5, 0.12, 0.18), LINE),
        it("Line R", taper(right, H, 11, 0.18, 0.12), LINE),
        it("Line crown", taper([(-95, -282), (0, -294), (95, -282)], H, 5, 0.3, 0.3), LINE, opacity=80),
    ]
    return items


def ear_items():
    H = head_xy
    items = []
    for side, outer, inner in (("L", EAR_L, EAR_L_IN), ("R", EAR_R, EAR_R_IN)):
        s = -1 if side == "L" else 1
        items += [
            it(f"Ear {side}", path(outer, H), GINGER if side == "L" else GINGER_SH),
            it(f"Ear {side} rim light", taper(outer[1:5], H, 10, 0.3, 0.3), GINGER_LT, opacity=70),
            it(f"Ear {side} inner", path(inner, H), lin([["#c8616c", 0], ["#f29aa0", 55], ["#ffc1bd", 100]], 90)),
            it(f"Ear {side} inner shade", path([(s * 140, -236), (s * 200, -300), (s * 280, -240), (s * 222, -198)], H),
               "#a94f5c", opacity=70),
        ]
        for k, (x0, y0, x1, y1) in enumerate([(230, -205, 250, -340), (200, -210, 214, -318), (262, -214, 274, -300),
                                              (180, -214, 196, -290)]):
            mid = (s * (x0 + x1) / 2 - s * 6, (y0 + y1) / 2)
            items.append(it(f"Ear {side} tuft {k}", taper([(s * x0, y0), mid, (s * x1, y1)], H, 7, 0.05, 0.9), CREAM, opacity=92))
        items += [
            it(f"Ear {side} line", taper(outer[1:7], H, 9 if side == "R" else 7.5, 0.15, 0.2), LINE),
            it(f"Ear {side} inner line", taper(inner[1:5], H, 3.5, 0.2, 0.2), "#7a2f2a", opacity=80),
        ]
    return items


def eye_items(side):
    H = head_xy
    s = -1 if side == "L" else 1
    shape = EYE_L if side == "L" else EYE_R
    px, py = s * 136, -40
    clip = path(shape, H)
    inner = [
        it("Sclera dark", path(shape, H), "#122a16"),
        it("Iris", ellipse(px - s * 2, -42, 68, 68, 0, H),
           lin([["#163a1c", 0], ["#3c8c33", 38], ["#8fdc55", 74], ["#e2ff98", 100]])),
        it("Iris ring", ellipse(px, -38, 40, 44, 0, H), "#c6f77c", opacity=40, blur=6),
    ]
    for k in range(32):
        a = 2 * math.pi * k / 32 + 0.08
        r0, r1 = 26, 60 + (k % 3) * 3
        inner.append(it(f"Fibre {k}", taper([(px + math.cos(a) * r0, py + math.sin(a) * r0 * 1.1),
                                             (px + math.cos(a) * r1, py + math.sin(a) * r1)], H, 2.6, 0.3, 0.6),
                        "#f0ffc2" if k % 2 else "#2b6a2a", opacity=30))
    inner += [
        it("Limbal ring", ellipse(px - s * 2, -42, 66, 66, 0, H), None, stroke="#0d2210", stroke_width=7),
        it("Pupil", ellipse(px, py + 2, 21, 50, 0, H), "#060d07"),
        it("Upper lid shadow", path([shape[0], shape[1], shape[2], shape[3], shape[4],
                                     (s * 190, -50), (s * 150, -66), (s * 100, -52)], H), "#08180b", opacity=68),
        it("Magic bounce", ellipse(px - s * 4, 4, 52, 15, 0, H), "#8ff8ff", opacity=55, blend="screen", blur=4),
        it("Catchlight big", ellipse(px - 22, -70, 17, 13, -20, H), "#ffffff"),
        it("Catchlight small", ellipse(px + 24, -6, 7, 7, 0, H), "#ffffff", opacity=90),
        it("Catchlight spark", ellipse(px - 42, -40, 4, 4, 0, H), "#e8ffff", opacity=80),
    ]
    lines = [
        it(f"Upper lid {side}", taper([(s * 52, -12), (s * 92, -80), (s * 150, -106), (s * 206, -88), (s * 232, -66)], H, 14, 0.08, 0.3), "#24100a"),
        it(f"Lid flick {side}", taper([(s * 206, -86), (s * 240, -80), (s * 260, -90)], H, 7, 0.1, 0.9), "#24100a"),
        it(f"Lower lid {side}", taper([(s * 80, 12), (s * 134, 24), (s * 196, -8)], H, 4.5, 0.2, 0.3), "#5a2614", opacity=85),
        it(f"Tear duct {side}", ellipse(s * 62, -14, 6, 4, 30, H), "#f08c8c", opacity=80),
    ]
    return clip, inner, lines


def nose_mouth_items():
    H = head_xy
    nose = [(-36, 74), (0, 70), (36, 74), (22, 96), (0, 114, 'c'), (-22, 96)]
    return [
        it("Nose", path(nose, H), lin([["#ffb4b8", 0], ["#e97a86", 100]])),
        it("Nose shade", path([(6, 96), (30, 78), (22, 98), (0, 114, 'c')], H), "#c95a6a", opacity=70),
        it("Nose shine", ellipse(-10, 80, 10, 5, -8, H), "#ffffff", opacity=75),
        it("Nose line", taper([(-34, 76), (-20, 98), (0, 116), (20, 98), (34, 76)], H, 4, 0.3, 0.3), "#7a2a2a", opacity=85),
        it("Philtrum", taper([(0, 114), (0, 134)], H, 5, 0.1, 0.4), LINE),
        it("Mouth L", taper([(0, 133), (-18, 152), (-46, 146)], H, 6, 0.15, 0.6), LINE),
        it("Mouth R", taper([(0, 133), (18, 152), (46, 146)], H, 6, 0.15, 0.6), LINE),
        it("Mouth inner", path([(-14, 148), (0, 140), (14, 148), (0, 160)], H), "#d16a74", opacity=60),
    ]


def whisker_items():
    H = head_xy
    items = []
    base = [[(-96, 140), (-290, 96), (-480, 72)], [(-102, 156), (-310, 142), (-510, 154)],
            [(-100, 172), (-296, 196), (-488, 240)], [(-92, 186), (-262, 238), (-424, 306)],
            [(-150, -118), (-166, -150), (-172, -184)], [(-170, -112), (-200, -140), (-222, -164)]]
    for i, pts in enumerate(base + [mirror(p) for p in base]):
        items.append(it(f"Whisker {i}", taper(pts, H, 5 if i % 6 < 4 else 3.4, 0.02, 1.0), "#fffaf0", opacity=88))
    return items


# ---------- body / cloak (body-local) ----------
B = body_xy
COWL = [(-560, 480), (-530, 320), (-470, 200), (-360, 122), (-200, 92), (0, 86), (200, 92), (360, 122),
        (470, 200), (530, 320), (560, 480), (300, 390), (0, 340), (-300, 390)]
CHEST = [(-210, 214), (-150, 288), (-100, 344), (-62, 392, 'c'), (-46, 362, 'c'), (-22, 424, 'c'), (0, 396, 'c'),
         (22, 424, 'c'), (46, 362, 'c'), (62, 392, 'c'), (100, 344), (150, 288), (210, 214), (0, 196)]
CLOAK_L = [(-206, 226), (-330, 248), (-482, 300), (-612, 402), (-712, 562), (-782, 800), (-832, 1100),
           (-860, 1270, 'c'), (-158, 1270, 'c'), (-124, 800), (-78, 582), (0, 442, 'c'), (-92, 360), (-160, 292)]
CLOAK_R = mirror(CLOAK_L)
TRIM_L = [(-212, 222), (-160, 292), (-90, 364), (-8, 440), (-78, 582), (-122, 800), (-154, 1270)]


def cowl_items():
    B = bodyw_xy
    return [
        it("Cowl", path(COWL, B), lin([["#34408c", 0], ["#1b2258", 100]])),
        it("Cowl inner", path([(-400, 364), (-366, 250), (-252, 176), (0, 160), (252, 176), (366, 250), (400, 364), (0, 322)], B), "#0b0e30"),
        it("Cowl fold L", taper([(-500, 260), (-440, 330), (-420, 420)], B, 26, 0.3, 0.6), NAVY_SH),
        it("Cowl fold R", taper([(500, 260), (440, 330), (420, 420)], B, 26, 0.3, 0.6), NAVY_SH),
        it("Cowl edge gold L", taper([(-540, 340), (-480, 206), (-366, 130), (-210, 100)], B, 10, 0.1, 0.4), GOLD),
        it("Cowl edge gold R", taper([(540, 340), (480, 206), (366, 130), (210, 100)], B, 10, 0.1, 0.4), GOLD),
        it("Cowl line", taper(COWL[:11], B, 9, 0.05, 0.05), "#090a22"),
    ]


def chest_items():
    items = [
        it("Chest fluff", path(CHEST, B), lin([["#e3bb94", 0], ["#fff3e2", 45], ["#fff6ea", 100]])),
        it("Chest under-chin", ellipse(0, 236, 190, 46, 0, B), "#d9ad84", opacity=60, blur=10),
    ]
    for i, pts in enumerate([[(-120, 300), (-100, 330), (-84, 356)], [(-60, 280), (-46, 320), (-40, 350)],
                             [(60, 280), (46, 320), (40, 350)], [(120, 300), (100, 330), (84, 356)],
                             [(0, 300), (4, 340), (0, 372)]]):
        items.append(it(f"Fluff flick {i}", taper(pts, B, 5, 0.1, 0.8), CREAM_SH))
    items.append(it("Chest line", taper(CHEST[1:13], B, 5, 0.1, 0.1), "#8a5a34", opacity=70))
    return items


def cloak_items():
    B = bodyw_xy
    robe = [(0, 432), (-84, 584), (-128, 800), (-164, 1270), (164, 1270), (128, 800), (84, 584)]
    items = [it("Robe", path(robe, B), lin([["#2b3c7e", 0], ["#3a54a6", 100]], 0))]
    for k, y in enumerate(range(620, 1260, 82)):
        items.append(it(f"Robe rune {k}", path([(0, y - 22), (14, y), (0, y + 22), (-14, y)], B), CYAN, opacity=75))
        items.append(it(f"Robe dot {k}", ellipse(0, y + 41, 4, 4, 0, B), GOLD))
    for side, shape in (("L", CLOAK_L), ("R", CLOAK_R)):
        s = -1 if side == "L" else 1
        items.append(it(f"Cloak {side}", path(shape, B), lin([["#1a2152", 0], ["#283373", 100]], 0 if side == "L" else 180)))
        for k, (pts, w) in enumerate([([(-430, 330), (-520, 700), (-570, 1270)], 64), ([(-262, 420), (-300, 800), (-326, 1270)], 52),
                                      ([(-640, 600), (-700, 1000), (-726, 1270)], 44)]):
            items.append(it(f"Fold shade {side}{k}", taper(pts if s < 0 else mirror(pts), B, w, 0.35, 0.02), NAVY_SH, opacity=90))
        for k, (pts, w) in enumerate([([(-478, 330), (-574, 700), (-626, 1270)], 15), ([(-306, 400), (-354, 800), (-376, 1270)], 11),
                                      ([(-690, 640), (-752, 1000), (-776, 1270)], 9)]):
            items.append(it(f"Fold light {side}{k}", taper(pts if s < 0 else mirror(pts), B, w, 0.4, 0.1), NAVY_LT, opacity=85))
        for k, (sx, sy, sz) in enumerate([(-560, 520, 16), (-640, 700, 11), (-480, 760, 9), (-700, 940, 14), (-560, 1010, 8),
                                          (-430, 1150, 12), (-720, 1180, 9), (-360, 560, 9)]):
            x, y = B(sx if s < 0 else -sx, sy)
            items.append(it(f"Star stitch {side}{k}", poly([(x, y - sz), (x + sz * .22, y - sz * .22), (x + sz, y), (x + sz * .22, y + sz * .22),
                                                           (x, y + sz), (x - sz * .22, y + sz * .22), (x - sz, y), (x - sz * .22, y - sz * .22)]), GOLD, opacity=92))
        items.append(it(f"Cloak line {side}", taper(shape[:8], B, 10, 0.05, 0.02), "#07081c"))
    for side, pts in (("L", TRIM_L), ("R", mirror(TRIM_L))):
        items += [
            it(f"Trim {side} edge", taper(pts, B, 46, 0, 0), GOLD_DK),
            it(f"Trim {side}", taper(pts, B, 38, 0, 0), lin([["#b9842e", 0], ["#f3cf7c", 50], ["#c99238", 100]], 0)),
            it(f"Trim {side} shine", taper(pts, B, 4, 0.1, 0.1), GOLD_LT, opacity=85),
        ]
        S = sample(pts, B, False, 30)
        for k in range(6, len(S) - 6, 14):
            x, y = S[k]
            items.append(it(f"Trim {side} rune {k}", poly([(x, y - 9), (x + 7, y), (x, y + 9), (x - 7, y)]), "#2a6f8a"))
            items.append(it(f"Trim {side} rune glow {k}", ellipse(x, y, 3, 3), CYAN))
    return items


def amulet_items():
    items = []
    for side in (-1, 1):
        S = sample([(side * 50, 404), (side * 118, 330), (side * 182, 254), (side * 226, 206)], B, False, 20)
        for k in range(0, len(S), 4):
            x, y = S[k]
            items.append(it(f"Chain {side} {k}", ellipse(x, y, 7, 4.5, 40 * side), None, stroke=GOLD, stroke_width=3))
    items += [
        it("Amulet glow", ellipse(0, 440, 230, 230, 0, B), rad([[CYAN, 0, 70], [CYAN, 100, 0]]), blend="screen"),
        it("Amulet rim", ellipse(0, 440, 68, 68, 0, B), GOLD_DK),
        it("Amulet ring", ellipse(0, 440, 62, 62, 0, B), lin([["#fff0b8", 0], ["#d9a547", 55], ["#8a5a18", 100]])),
        it("Amulet seat", ellipse(0, 440, 48, 48, 0, B), "#2a1a08"),
        it("Gem", ellipse(0, 440, 43, 43, 0, B), rad([["#ffffff", 0], ["#b8fdff", 22], ["#3fd2ef", 62], ["#0d4f82", 100]])),
        it("Gem facet", poly([(-26, 418), (0, 404), (18, 420), (-6, 432)], B), "#ffffff", opacity=55),
        it("Gem spark", ellipse(-16, 418, 7, 7, 0, B), "#ffffff"),
    ]
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        items.append(it(f"Prong {k}", ellipse(math.cos(a) * 64, 440 + math.sin(a) * 64, 8, 8, 0, B), GOLD))
    return items


# ---------- magic circle ----------
def rune_circle_items():
    cx, cy = 1000, 760
    rr = random.Random(9)
    items = []

    def ring(name, r, w, op=100):
        items.append(it(name, ellipse(cx, cy, r, r), None, stroke=CYAN, stroke_width=w, opacity=op))

    ring("Ring outer", 660, 8)
    ring("Ring outer thin", 634, 2.5, 85)
    ring("Ring band in", 566, 3)
    ring("Ring mid", 526, 6)
    ring("Ring inner", 474, 2, 80)
    ring("Ring core", 250, 3, 70)
    for k in range(56):
        a = 2 * math.pi * k / 56
        ca, sa = math.cos(a), math.sin(a)
        for j in range(rr.randint(2, 3)):
            u0, v0, u1, v1 = rr.uniform(-11, 11), rr.uniform(-20, 20), rr.uniform(-11, 11), rr.uniform(-20, 20)
            r0, r1 = 600 + v0, 600 + v1
            p0 = (cx + ca * r0 - sa * u0, cy + sa * r0 + ca * u0)
            p1 = (cx + ca * r1 - sa * u1, cy + sa * r1 + ca * u1)
            items.append(it(f"Glyph {k}.{j}", f"M {p0[0]:.1f} {p0[1]:.1f} L {p1[0]:.1f} {p1[1]:.1f}", None,
                            stroke=CYAN, stroke_width=3.2, opacity=90))
    for t in range(2):
        pts = []
        for k in range(3):
            a = -math.pi / 2 + k * 2 * math.pi / 3 + (math.pi / 3 if t else 0)
            pts.append((cx + math.cos(a) * 526, cy + math.sin(a) * 526))
        d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f} L {pts[1][0]:.1f} {pts[1][1]:.1f} L {pts[2][0]:.1f} {pts[2][1]:.1f} Z"
        items.append(it(f"Triangle {t}", d, None, stroke=CYAN, stroke_width=3, opacity=80))
    for k in range(6):
        a = -math.pi / 2 + k * math.pi / 3
        x, y = cx + math.cos(a) * 526, cy + math.sin(a) * 526
        items.append(it(f"Node {k}", ellipse(x, y, 30, 30), "#0c1440", stroke=CYAN, stroke_width=4))
        items.append(it(f"Node core {k}", ellipse(x, y, 9, 9), CYAN_LT))
    for k in range(24):
        a = 2 * math.pi * k / 24
        r0, r1 = 474, (504 if k % 2 else 490)
        items.append(it(f"Tick {k}", f"M {cx + math.cos(a) * r0:.1f} {cy + math.sin(a) * r0:.1f} L {cx + math.cos(a) * r1:.1f} {cy + math.sin(a) * r1:.1f}",
                        None, stroke=CYAN, stroke_width=3, opacity=80))
    return items


# ---------- scene ----------
def sky_items():
    return [
        it("Sky", poly([(0, 0), (2000, 0), (2000, 2000), (0, 2000)]),
           lin([["#080a24", 0], ["#1a1550", 38], ["#45287c", 70], ["#8a58b6", 100]])),
        it("Horizon haze", ellipse(1000, 1380, 1150, 280), "#c27ad6", opacity=40, blur=70),
        it("Upper haze", ellipse(560, 520, 700, 200, -8), "#3a2a8a", opacity=45, blur=60),
    ]


def star_items():
    rr = random.Random(21)
    items = []
    for k in range(170):
        x, y = rr.uniform(0, 2000), rr.uniform(0, 1150)
        r = rr.choice([1.4, 1.8, 2.2, 2.8, 3.6])
        items.append(it(f"Star {k}", ellipse(x, y, r, r), "#ffffff", opacity=rr.randint(45, 100)))
    for k in range(14):
        x, y = rr.uniform(60, 1940), rr.uniform(40, 900)
        s = rr.uniform(10, 22)
        items.append(it(f"Sparkle {k}", poly([(x, y - s), (x + s * .18, y - s * .18), (x + s, y), (x + s * .18, y + s * .18),
                                              (x, y + s), (x - s * .18, y + s * .18), (x - s, y), (x - s * .18, y - s * .18)]),
                        "#e8f4ff", opacity=90))
    return items


def moon_items():
    mx, my = 1690, 360
    return [
        it("Moon halo", ellipse(mx, my, 430, 430), rad([["#dfe8ff", 0, 45], ["#9a8aff", 45, 18], ["#9a8aff", 100, 0]]), blend="screen"),
        it("Moon", ellipse(mx, my, 150, 150), rad([["#fffcf2", 0], ["#fbf0d6", 70], ["#ecdcb8", 100]])),
        it("Crater 1", ellipse(mx - 40, my - 30, 34, 26, 15), "#e2cfa6", opacity=55),
        it("Crater 2", ellipse(mx + 50, my + 30, 24, 20), "#e2cfa6", opacity=50),
        it("Crater 3", ellipse(mx - 10, my + 70, 18, 14), "#e2cfa6", opacity=45),
        it("Crater 4", ellipse(mx + 60, my - 60, 14, 12), "#e2cfa6", opacity=45),
    ]


def castle_items():
    items = [
        it("Mountains", path([(0, 1300), (0, 1020), (180, 900), (330, 980), (520, 860), (700, 1000), (860, 940),
                              (1000, 1040), (1160, 920), (1340, 1000), (1520, 860), (1700, 960), (1860, 880),
                              (2000, 960), (2000, 1300)]), "#2c2066", opacity=90),
        it("Wall L", poly([(20, 1180), (580, 1180), (580, 1500), (20, 1500)]), "#2a1f5e"),
        it("Wall R", poly([(1440, 1190), (2000, 1190), (2000, 1500), (1440, 1500)]), "#2a1f5e"),
    ]
    towers = [(70, 70, 1040, 150), (170, 90, 960, 190), (290, 60, 1090, 120), (380, 110, 1010, 220), (500, 70, 1120, 130),
              (1480, 80, 1100, 140), (1580, 110, 990, 230), (1720, 70, 1060, 150), (1820, 100, 940, 200), (1930, 70, 1080, 140)]
    wr = random.Random(4)
    for k, (x, w, top, sp) in enumerate(towers):
        items.append(it(f"Tower {k}", poly([(x - w / 2, 1500), (x - w / 2, top), (x + w / 2, top), (x + w / 2, 1500)]), "#30246a"))
        items.append(it(f"Spire {k}", poly([(x - w / 2 - 10, top + 2), (x, top - sp), (x + w / 2 + 10, top + 2)]), "#3a2c7a"))
        items.append(it(f"Spire light {k}", poly([(x, top - sp), (x + w / 2 + 10, top + 2), (x + 6, top + 2)]), "#4b3a96"))
        for j in range(wr.randint(1, 3)):
            wy = top + 40 + j * 70
            col = "#ffcf7a" if wr.random() < 0.5 else CYAN
            items.append(it(f"Window {k}.{j}", poly([(x - 7, wy), (x + 7, wy), (x + 7, wy + 20), (x - 7, wy + 20)]), col, opacity=90))
    return items


def mid_tree_items():
    rr = random.Random(33)
    items = []
    for side, x0, x1 in (("L", -80, 520), ("R", 1480, 2080)):
        for k in range(34):
            x, y = rr.uniform(x0, x1), rr.uniform(1260, 1900)
            r = rr.uniform(70, 150)
            col = rr.choice(["#4e3290", "#603ea4", "#7650b8", "#8e68cc"])
            items.append(it(f"Bloom {side}{k}", ellipse(x, y, r, r * 0.8), col, opacity=95))
        for k in range(18):
            x, y = rr.uniform(x0, x1), rr.uniform(1240, 1700)
            items.append(it(f"Bloom light {side}{k}", ellipse(x, y, rr.uniform(30, 70), rr.uniform(20, 45)), "#b894ec", opacity=70))
    items.append(it("Tree base shade", poly([(0, 1700), (2000, 1700), (2000, 2000), (0, 2000)]), "#1a1240", opacity=55, blur=40))
    return items


def wisteria_items():
    """Hanging wisteria racemes framing the top-left (big) and the top-right edge (small)."""
    rr = random.Random(77)
    items = []
    groups = [("L", 1, 0, [(40, 50, 430), (130, 66, 520), (225, 58, 380), (320, 44, 470), (420, 60, 330), (520, 80, 400), (610, 60, 280)]),
              ("R", -1, 2000, [(40, 40, 300), (120, 56, 220)])]
    for side, s, ox, anchors in groups:
        reach = anchors[-1][0] + 40
        branch = [(ox - s * 20, 36), (ox + s * reach * 0.3, 64), (ox + s * reach * 0.6, 36), (ox + s * reach * 0.85, 84), (ox + s * reach, 56)]
        items.append(it(f"Branch {side}", taper(branch, canvas_xy, 28, 0.0, 0.6), "#1c0f26"))
        for a, (ax, ay, ln) in enumerate(anchors):
            x0 = ox + s * ax
            sway = rr.uniform(-18, 18)
            rows = int(ln / 9)
            for k in range(rows):
                t = k / rows
                y = ay + t * ln
                half = (1 - t) ** 0.9 * 40 + 5
                cx = x0 + sway * t * t
                for j in range(3 if t < 0.8 else 2):
                    x = cx + rr.uniform(-half, half)
                    tone = min(4, int(t * 4.6 + rr.uniform(-0.6, 0.6)))
                    dark = ["#2c1452", "#4a2486", "#7346b8", "#a57ce0", "#e4ccff"][max(0, tone)]
                    sz = (1 - t) * 6 + 7
                    items.append(it(f"Petal {side}{a}.{k}.{j}", ellipse(x, y, sz * 1.2, sz * 0.8, rr.uniform(-30, 30)), dark, opacity=96))
                    if tone >= 2 and rr.random() < 0.5:
                        items.append(it(f"Petal hi {side}{a}.{k}.{j}", ellipse(x - 2, y - 2, sz * 0.5, sz * 0.35, -20), "#f4e8ff", opacity=80))
        for k in range(len(anchors) * 2):
            lx = ox + s * rr.uniform(0, reach)
            ly = rr.uniform(40, 110)
            ang = rr.uniform(40, 140)
            L = rr.uniform(50, 80)
            tip = (lx + math.cos(math.radians(ang)) * L, ly + math.sin(math.radians(ang)) * L)
            items.append(it(f"Leaf {side}{k}", taper([(lx, ly), ((lx + tip[0]) / 2 + 6, (ly + tip[1]) / 2), tip], canvas_xy, 16, 0.2, 0.7),
                            rr.choice(["#1d1a3a", "#232548"]), opacity=97))
    return items


def paw_items():
    """Raised paw (viewer's left) holding a floating rune orb."""
    B = body_xy
    px, py = -330, 905
    items = [
        it("Sleeve", path([(-452, 1000), (-440, 930), (-362, 900), (-290, 902), (-220, 936), (-180, 990), (-110, 1090), (-60, 1180),
                           (-70, 1272, 'c'), (-262, 1272, 'c'), (-300, 1150), (-400, 1060)], B), lin([["#2c3880", 0], ["#18204f", 100]], 0)),
        it("Sleeve fold 1", taper([(-400, 950), (-330, 1050), (-250, 1160)], B, 26, 0.3, 0.5), NAVY_SH),
        it("Sleeve fold 2", taper([(-250, 960), (-190, 1060), (-140, 1170)], B, 18, 0.3, 0.5), NAVY_SH),
        it("Sleeve light", taper([(-430, 920), (-390, 1010), (-330, 1090)], B, 10, 0.3, 0.3), NAVY_LT, opacity=85),
        it("Sleeve line", taper([(-452, 1000), (-400, 1060), (-300, 1150), (-262, 1272)], B, 9, 0.1, 0.05), "#07081c"),
        it("Palm", path([(-440, 902), (-454, 842), (-440, 800), (-428, 780), (-404, 762), (-382, 778, 'c'), (-360, 752), (-330, 770, 'c'), (-300, 752), (-278, 778, 'c'), (-256, 762), (-232, 780), (-220, 800), (-206, 842), (-220, 902), (-330, 914)], B), CREAM),
        it("Palm shade", path([(-440, 902), (-454, 842), (-430, 868), (-330, 880), (-230, 868), (-206, 842), (-220, 902), (-330, 914)], B), CREAM_SH),
        it("Palm side L", path([(-454, 842), (-440, 902), (-410, 908), (-436, 860)], B), GINGER),
        it("Palm side R", path([(-206, 842), (-220, 902), (-250, 908), (-224, 860)], B), GINGER_SH),
        it("Main pad", path([(-376, 842), (-360, 812), (-330, 804), (-300, 812), (-284, 842), (-306, 860), (-330, 852), (-354, 860)], B),
           lin([["#ffb8bc", 0], ["#e8808c", 100]])),
        it("Toe pad 1", ellipse(-404, 790, 17, 14, -20, B), "#f6a0a8"),
        it("Toe pad 2", ellipse(-360, 778, 18, 15, -6, B), "#f6a0a8"),
        it("Toe pad 3", ellipse(-300, 778, 18, 15, 6, B), "#f6a0a8"),
        it("Toe pad 4", ellipse(-256, 790, 17, 14, 20, B), "#f6a0a8"),
        it("Pad shine", ellipse(-342, 818, 10, 5, -10, B), "#ffffff", opacity=70),
        it("Palm line", taper([(-440, 902), (-454, 842), (-440, 800), (-428, 780), (-404, 762), (-382, 778, 'c'), (-360, 752), (-330, 770, 'c'), (-300, 752), (-278, 778, 'c'), (-256, 762), (-232, 780), (-220, 800), (-206, 842), (-220, 902), (-330, 914)][:15], B, 7, 0.08, 0.08), LINE),
        it("Cuff edge", taper([(-456, 924), (-362, 904), (-290, 906), (-206, 926)], B, 36, 0, 0), GOLD_DK),
        it("Cuff", taper([(-456, 924), (-362, 904), (-290, 906), (-206, 926)], B, 28, 0, 0), lin([["#b9842e", 0], ["#f3cf7c", 50], ["#c99238", 100]], 0)),
        it("Cuff shine", taper([(-444, 916), (-362, 898), (-290, 900), (-218, 918)], B, 3, 0.1, 0.1), GOLD_LT, opacity=85),
        it("Pad glow", ellipse(-330, 790, 120, 40, 0, B), "#9ff8ff", opacity=35, blend="screen", blur=14),
        it("Orb glow", ellipse(-330, 650, 230, 230, 0, B), rad([[CYAN, 0, 75], [CYAN, 100, 0]]), blend="screen"),
        it("Orb", ellipse(-330, 650, 74, 74, 0, B), rad([["#ffffff", 0], ["#c8feff", 25], ["#4ad9f2", 65], ["#123f7a", 100]])),
        it("Orb inner rune", ellipse(-330, 650, 40, 40, 0, B), None, stroke="#ffffff", stroke_width=2.5, opacity=70),
        it("Orb shine", ellipse(-356, 612, 20, 12, -30, B), "#ffffff", opacity=90),
        it("Orb ring 1", ellipse(-330, 650, 120, 30, -18, B), None, stroke=CYAN, stroke_width=4, opacity=90),
        it("Orb ring 2", ellipse(-330, 650, 106, 26, 24, B), None, stroke=CYAN_LT, stroke_width=2.5, opacity=75),
    ]
    for k in range(10):
        a = 2 * math.pi * k / 10
        items.append(it(f"Orb mote {k}", ellipse(-330 + math.cos(a) * 150, 640 + math.sin(a) * 60 - 20, 4, 4, 0, B), CYAN_LT, opacity=85))
    return items


def particle_items():
    rr = random.Random(101)
    items = []
    n = 0
    while n < 46:
        x, y = rr.uniform(80, 1920), rr.uniform(200, 1900)
        if (560 < x < 1440 and 300 < y < 1150) or (420 < x < 1580 and y > 1100):  # keep face and cloak clear
            continue
        r = rr.uniform(1.6, 4.2)
        items.append(it(f"Spark halo {n}", ellipse(x, y, r * 3, r * 3), CYAN, opacity=30, blend="screen", blur=5))
        items.append(it(f"Spark {n}", ellipse(x, y, r, r), CYAN_LT))
        n += 1
    for k in range(36):
        x, y = rr.uniform(60, 1940), rr.uniform(150, 1950)
        if 600 < x < 1400 and 300 < y < 1150:
            continue
        items.append(it(f"Petal drift {k}", ellipse(x, y, rr.uniform(8, 15), rr.uniform(5, 8), rr.uniform(0, 180)),
                        rr.choice(["#e6c6ff", "#c9a2ff", "#f6e6ff"]), opacity=90, blur=rr.choice([0, 0, 0, 3])))
    return items


def build():
    L = []

    def add(layer, items, clear=True, **kw):
        e = {"layer": layer, "clear": clear, "items": items}
        e.update(kw)
        L.append(e)

    add("Background art/Sky", sky_items())
    add("Background art/Stars", star_items())
    add("Background art/Moon", moon_items())
    add("Background art/Far castle", castle_items())
    add("Background art/Mid trees", mid_tree_items())
    add("Magic/Rune circle", rune_circle_items())
    add("Cat/Cowl", cowl_items())
    add("Cat/Chest fluff", chest_items())
    add("Cat/Cloak", cloak_items())
    add("Cat/Amulet", amulet_items())
    add("Cat/Paw & orb", paw_items())
    add("Cat/Ears", ear_items())
    head = head_items()
    add("Cat/Head", head[:-3], clip=path(HEAD, head_xy))
    add("Cat/Head", head[-3:], clear=False)
    cl, il, ll = eye_items("L")
    cr, ir, lr = eye_items("R")
    add("Cat/Eyes", il, clip=cl)
    add("Cat/Eyes", ir, clear=False, clip=cr)
    add("Cat/Eyes", ll + lr, clear=False)
    add("Cat/Nose & mouth", nose_mouth_items())
    add("Cat/Whiskers", whisker_items())
    add("Near frame/Wisteria", wisteria_items())
    add("FX/Particles", particle_items())
    spec = {"doc": DOC, "layers": L}
    out = HERE / "drawing.json"
    out.write_text(json.dumps(spec), encoding="utf-8")
    n = sum(len(e["items"]) for e in L)
    print(f"wrote {out.name}: {len(L)} entries, {n} items, {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    build()
