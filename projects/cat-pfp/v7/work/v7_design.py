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
DOC = "cat-pfp-v7.ai"
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

# v7: the outer ear edge now flows into the skull contour at (-306,-90) instead of ending in a step outside it
EAR_L = [(-80, -236), (-150, -322), (-215, -408), (-268, -462, 'c'), (-292, -386), (-306, -282), (-312, -190), (-300, -104),
         (-236, -128), (-160, -180)]
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
        it("Crown shade", path([(-120, -268), (0, -250), (120, -268), (60, -300), (-60, -300)], H), GINGER_SH, opacity=40, blur=8),
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
        # D5: crescent that follows the muzzle's shaded right edge (was a stain-like blob)
        it("Muzzle shade", path([(58, 48, 'c'), (108, 88), (152, 142), (142, 198), (82, 236), (24, 249, 'c'),
                                 (70, 216), (112, 184), (122, 140), (92, 96)], H), CREAM_SH, opacity=80),
        it("Chin shade", path([(-60, 246), (0, 256), (60, 246), (36, 266), (0, 272), (-36, 266)], H), CREAM_SH, opacity=70),
        it("Cheek blush L", ellipse(-210, 118, 52, 26, -8, H), "#ff7f86", opacity=38, blur=12),
        it("Cheek blush R", ellipse(206, 112, 46, 24, 8, H), "#ff7f86", opacity=30, blur=12),
        # v7 face volume (key light upper-left): brow ridge and eye sockets turn under, nose bridge and
        # left cheek plane catch light, muzzle casts a soft shadow onto the chin and the right cheek
        it("Brow shade L", ellipse(-150, -128, 96, 26, -6, H), GINGER_SH, opacity=26, blur=10),
        it("Brow shade R", ellipse(150, -128, 96, 26, 6, H), GINGER_DEEP, opacity=30, blur=10),
        it("Socket shade L", ellipse(-140, 16, 76, 16, 4, H), GINGER_SH, opacity=24, blur=8),
        it("Socket shade R", ellipse(140, 16, 76, 16, -4, H), GINGER_DEEP, opacity=28, blur=8),
        it("Nose bridge light", ellipse(-6, -24, 34, 74, 0, H), GINGER_LT, opacity=60, blur=14),
        it("Cheek plane light", ellipse(-236, 44, 70, 52, -20, H), GINGER_LT, opacity=50, blur=18),
        it("Muzzle side shade R", path([(152, 142), (200, 120), (250, 170), (216, 236), (142, 198)], H), GINGER_SH, opacity=55, blur=10),
        it("Muzzle drop shadow", path([(-120, 228), (0, 262), (120, 228), (100, 260), (0, 284), (-100, 260)], H), "#c98a5a", opacity=45, blur=6),
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
    # v7: no contour across the ear roots - the line starts where each ear's outer edge meets the skull,
    # and fur tufts grow from the head over each ear root so the ears belong to the skull
    left = HEAD[4:16]
    right = HEAD[15:-3]
    items += [
        it("Line L", taper(left, H, 8.5, 0.0, 0.18), LINE),
        it("Line R", taper(right, H, 11, 0.18, 0.0), LINE),
        it("Line crown", taper([(-110, -278), (0, -294), (110, -278)], H, 4.5, 0.4, 0.4), LINE, opacity=70),
    ]
    tufts = [[(-130, -262), (-138, -292), (-132, -318)], [(-178, -236), (-192, -270), (-192, -300)],
             [(-226, -198), (-246, -232), (-252, -262)], [(-268, -150), (-288, -184), (-296, -214)]]
    for i, pts in enumerate(tufts):
        items.append(it(f"Ear root fur L{i}", taper(pts, H, 17, 0.05, 0.95), GINGER))
        items.append(it(f"Ear root fur R{i}", taper(mirror(pts), H, 17, 0.05, 0.95), GINGER_SH))
        items.append(it(f"Ear root fur tip L{i}", taper(pts[1:], H, 5, 0.1, 0.9), GINGER_LT, opacity=70))
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
            it(f"Ear {side} line", taper(outer[1:8], H, 9 if side == "R" else 7.5, 0.15, 0.05), LINE),  # ends on the skull line
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
        it("Iris reflected light", ellipse(px - s * 4, -6, 46, 22, 0, H), "#e4ff9e", opacity=38, blur=7),
        it("Pupil ring", ellipse(px, py + 2, 30, 58, 0, H), "#123a14", opacity=55, blur=4),
        it("Pupil", ellipse(px, py + 2, 21, 50, 0, H), "#060d07"),
        it("Upper lid shadow", path([shape[0], shape[1], shape[2], shape[3], shape[4],
                                     (s * 190, -50), (s * 150, -66), (s * 100, -52)], H), "#08180b", opacity=68),
        it("Magic bounce", path([(px - 44, 2), (px, 12), (px + 44, 2), (px + 30, 10), (px, 18), (px - 30, 10)], H),
           "#8ff8ff", opacity=40, blend="screen", blur=2),  # v7: thin crescent reflection, was a stain-like band
        it("Catchlight big", ellipse(px - 22, -70, 17, 13, -20, H), "#ffffff"),
        it("Catchlight small", ellipse(px + 24, -6, 7, 7, 0, H), "#ffffff", opacity=90),
        it("Catchlight spark", ellipse(px - 42, -40, 4, 4, 0, H), "#e8ffff", opacity=80),
    ]
    lines = [
        it(f"Upper lid {side}", taper([(s * 52, -12), (s * 92, -80), (s * 150, -106), (s * 206, -88), (s * 232, -66)], H, 14, 0.08, 0.3), "#24100a"),
        it(f"Lid flick {side}", taper([(s * 206, -86), (s * 240, -80), (s * 260, -90)], H, 7, 0.1, 0.9), "#24100a"),
        it(f"Lower lid {side}", taper([(s * 80, 12), (s * 134, 24), (s * 196, -8)], H, 4.5, 0.2, 0.3), "#5a2614", opacity=85),
        it(f"Tear duct {side}", ellipse(s * 62, -14, 6, 4, 30, H), "#f08c8c", opacity=80),
        it(f"Wet line {side}", taper([(s * 96, 8), (s * 140, 16), (s * 186, -2)], H, 2.2, 0.3, 0.3), "#fff4e6", opacity=55),
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
            # v7 (skill v3 rule 9): a narrow dark core inside each fold valley gives the fold real depth
            core = [(x + 10, y) for x, y in pts]
            items.append(it(f"Fold core {side}{k}", taper(core if s < 0 else mirror(core), B, w * 0.2, 0.45, 0.05), "#04051a", opacity=80))
        # collar occlusion: the neck ruff casts a soft shadow onto the top of the cloak
        collar = [(x, y + 34) for x, y in (shape[:4] if s < 0 else shape[:4])]
        items.append(it(f"Collar occlusion {side}", taper(collar, B, 46, 0.3, 0.6), "#04051a", opacity=55, blur=12))
        # D3: key light is upper-left, so left ridges are wider, warmer and brighter; right ridges are narrow and cool
        for k, (pts, w) in enumerate([([(-478, 330), (-574, 700), (-626, 1270)], 15), ([(-306, 400), (-354, 800), (-376, 1270)], 11),
                                      ([(-690, 640), (-752, 1000), (-776, 1270)], 9)]):
            if s < 0:
                items.append(it(f"Fold light {side}{k}", taper(pts, B, w * 1.35, 0.4, 0.1), "#5466b8", opacity=92))
                items.append(it(f"Fold spec {side}{k}", taper(pts[:2], B, w * 0.3, 0.3, 0.3), "#93a4ef", opacity=70))
            else:
                items.append(it(f"Fold light {side}{k}", taper(mirror(pts), B, w * 0.6, 0.4, 0.1), "#2e3b80", opacity=70))
        if s > 0:
            items.append(it("Right panel form shade", path([(300, 300), (500, 370), (640, 560), (700, 900), (720, 1270),
                                                            (420, 1270), (380, 900), (330, 560)], B), "#080a26", opacity=45, blur=40))
        for k, (sx, sy, sz) in enumerate([(-560, 520, 16), (-640, 700, 11), (-480, 760, 9), (-700, 940, 14), (-560, 1010, 8),
                                          (-430, 1150, 12), (-720, 1180, 9), (-360, 560, 9)]):
            x, y = B(sx if s < 0 else -sx, sy)
            items.append(it(f"Star stitch {side}{k}", poly([(x, y - sz), (x + sz * .22, y - sz * .22), (x + sz, y), (x + sz * .22, y + sz * .22),
                                                           (x, y + sz), (x - sz * .22, y + sz * .22), (x - sz, y), (x - sz * .22, y - sz * .22)]), GOLD, opacity=92))
        items.append(it(f"Cloak line {side}", taper(shape[:8], B, 10, 0.05, 0.02), "#07081c"))
    return items


def trim_items():
    """Gold front edges of the cloak. Own layer so the upper arm can tuck under the left edge."""
    B = bodyw_xy
    items = []
    for side, pts in (("L", TRIM_L), ("R", mirror(TRIM_L))):
        items += [
            it(f"Trim {side} edge", taper(pts, B, 46, 0, 0), GOLD_DK),
            it(f"Trim {side}", taper(pts, B, 38, 0, 0), lin([["#b9842e", 0], ["#f3cf7c", 50], ["#c99238", 100]], 0)),
            it(f"Trim {side} shine", taper(pts, B, 4, 0.1, 0.1), GOLD_LT, opacity=85),
        ]
        S = sample(pts, B, False, 30)
        # v7 bevel: the band is lit from the upper left, so the edge facing the light is bright and the far edge dark
        Ssm = S[::3] + [S[-1]]
        light_pts, dark_pts = [], []
        for k, (x, y) in enumerate(Ssm):
            ax, ay = Ssm[max(k - 1, 0)]
            bx, by = Ssm[min(k + 1, len(Ssm) - 1)]
            d = math.hypot(bx - ax, by - ay) or 1
            nx, ny = -(by - ay) / d, (bx - ax) / d  # unit normal
            if nx * -1 + ny * -1 < 0:  # point the normal toward the upper left (the key light)
                nx, ny = -nx, -ny
            light_pts.append((x + nx * 13, y + ny * 13))
            dark_pts.append((x - nx * 13, y - ny * 13))
        items.append(it(f"Trim {side} bevel light", taper(light_pts, canvas_xy, 5, 0.1, 0.1), "#fff1c2", opacity=80))
        items.append(it(f"Trim {side} bevel shadow", taper(dark_pts, canvas_xy, 6, 0.1, 0.1), "#6e4512", opacity=85))
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

    def ring(name, r, w, op=100):  # D4: whole circle at ~72% so it no longer competes with the face in greyscale
        items.append(it(name, ellipse(cx, cy, r, r), None, stroke=CYAN, stroke_width=w, opacity=round(op * 0.72)))

    ring("Ring outer", 660, 8)
    ring("Ring outer thin", 634, 2.5, 85)
    ring("Ring band in", 566, 3)
    ring("Ring mid", 526, 6)
    ring("Ring inner", 474, 2, 80)
    ring("Ring core", 250, 3, 70)
    # D7: a designed 8-glyph alphabet (u = along the ring, v = outward), repeated in sequence and aligned to the tangent
    ALPHABET = [
        [[(0, -15), (0, 15)], [(0, -15), (9, -6)], [(0, -3), (9, 6)]],
        [[(-7, -15), (-7, 15)], [(-7, -10), (7, 0), (-7, 10)]],
        [[(0, -15), (8, -4), (0, 7), (-8, -4), (0, -15)], [(0, 7), (0, 15)]],
        [[(-8, 15), (0, -15), (8, 15)], [(-4, 3), (4, 3)]],
        [[(-8, -15), (8, -15)], [(0, -15), (0, 15)], [(-8, 15), (8, 15)]],
        [[(-8, -15), (8, 15)], [(8, -15), (-8, 15)]],
        [[(0, -15), (0, 15)], [(-8, -7), (0, 1), (8, -7)]],
        [[(-7, -15), (-7, 15), (7, 15)], [(-7, 0), (6, -11)]],
    ]
    n_glyph = 48
    for k in range(n_glyph):
        a = 2 * math.pi * (k + 0.5) / n_glyph
        ca, sa = math.cos(a), math.sin(a)
        for j, stroke in enumerate(ALPHABET[k % len(ALPHABET)]):
            P = [(cx + ca * (600 + v) - sa * u, cy + sa * (600 + v) + ca * u) for u, v in stroke]
            d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in P)
            items.append(it(f"Glyph {k}.{j}", d, None, stroke=CYAN, stroke_width=3, opacity=70))
        if k % 4 == 3:  # separator dot every fourth glyph
            b = a + math.pi / n_glyph
            items.append(it(f"Glyph dot {k}", ellipse(cx + math.cos(b) * 600, cy + math.sin(b) * 600, 3.5, 3.5), CYAN_LT, opacity=75))
    for t in range(2):
        pts = []
        for k in range(3):
            a = -math.pi / 2 + k * 2 * math.pi / 3 + (math.pi / 3 if t else 0)
            pts.append((cx + math.cos(a) * 526, cy + math.sin(a) * 526))
        d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f} L {pts[1][0]:.1f} {pts[1][1]:.1f} L {pts[2][0]:.1f} {pts[2][1]:.1f} Z"
        items.append(it(f"Triangle {t}", d, None, stroke=CYAN, stroke_width=3, opacity=60))
    for k in range(6):
        a = -math.pi / 2 + k * math.pi / 3
        x, y = cx + math.cos(a) * 526, cy + math.sin(a) * 526
        items.append(it(f"Node {k}", ellipse(x, y, 30, 30), "#0c1440", stroke=CYAN, stroke_width=4))
        items.append(it(f"Node core {k}", ellipse(x, y, 9, 9), CYAN_LT))
    for k in range(24):
        a = 2 * math.pi * k / 24
        r0, r1 = 474, (504 if k % 2 else 490)
        items.append(it(f"Tick {k}", f"M {cx + math.cos(a) * r0:.1f} {cy + math.sin(a) * r0:.1f} L {cx + math.cos(a) * r1:.1f} {cy + math.sin(a) * r1:.1f}",
                        None, stroke=CYAN, stroke_width=3, opacity=60))
    return items


# ---------- scene ----------
def sky_items():
    return [
        it("Sky", poly([(0, 0), (2000, 0), (2000, 2000), (0, 2000)]),
           lin([["#080a24", 0], ["#1a1550", 38], ["#45287c", 70], ["#8a58b6", 100]])),
        it("Horizon haze", ellipse(1000, 1380, 1150, 280), "#c27ad6", opacity=40, blur=70),
        it("Upper haze", ellipse(560, 520, 700, 200, -8), "#3a2a8a", opacity=45, blur=60),
    ]




def upper_arm_items():
    """Upper arm from the elbow up under the left gold trim (the shoulder is hidden by the cloak)."""
    B = body_xy
    stub = [(-128, 890), (-70, 905), (-18, 975), (28, 1080), (10, 1150), (-60, 1160), (-124, 1070)]
    return [
        it("Upper arm", path(stub, B), lin([["#141a44", 0], ["#283472", 100]], 0)),
        it("Upper arm ridge light", taper([(-62, 918), (-22, 978), (16, 1062)], B, 10, 0.3, 0.4), NAVY_LT, opacity=70),
        it("Trim cast shadow", taper([(-98, 880), (-104, 1000), (-110, 1150)], B, 34, 0.1, 0.1), "#04061a", opacity=70, blur=8),
        it("Upper arm line", taper(stub[:5], B, 7, 0.05, 0.1), "#07081c"),
    ]


def neck_ruff_items():
    """D2: fur ruff under the jaw spilling over the collar, plus contact shadow, so the head sits on the body."""
    H = head_xy
    # irregular tufts (tip x, tip y, lean): no two the same length, so it reads as fur, not a lace collar
    tufts = [(-196, 298, -10), (-138, 318, -6), (-84, 306, -2), (-30, 326, 0), (24, 314, 3), (78, 324, 5), (132, 302, 8), (186, 290, 10)]
    pts = [(-226, 236)]
    for k, (x, y, lean) in enumerate(tufts):
        nx = tufts[k + 1][0] if k + 1 < len(tufts) else 226
        pts.append((x + lean, y, 'c'))
        pts.append(((x + nx) / 2, 274 + (k % 3) * 6))  # rounded valley between tufts
    pts[-1] = (226, 236)
    ruff = [(-220, 190)] + pts + [(220, 190), (0, 220)]
    items = [
        it("Ruff contact shadow", ellipse(0, 318, 190, 22, 0, H), "#4a2414", opacity=26, blur=10),
        it("Neck ruff", path(ruff, H), lin([[GINGER, 0], [CREAM, 32], [CREAM, 68], [GINGER_SH, 100]], 0)),
        it("Ruff shade", path([(-220, 200), (-100, 262), (0, 272), (100, 262), (220, 200), (220, 228), (100, 284), (0, 294),
                               (-100, 284), (-220, 228)], H), CREAM_SH, opacity=70, blur=6),
    ]
    for k, (x, y, lean) in enumerate(tufts):
        col = CREAM_SH if abs(x) < 150 else GINGER_DEEP
        items.append(it(f"Ruff flick {k}", taper([(x + lean * 0.3, y - 48), (x + lean * 0.7, y - 22), (x + lean, y - 2)], H, 5, 0.6, 0.1),
                        col, opacity=80))
    items.append(it("Ruff line", taper(pts, H, 3.5, 0.05, 0.05), "#8a5a34", opacity=60))
    return items


def paw_items():
    """Raised paw (viewer's left) holding a floating rune orb."""
    B = body_xy
    px, py = -330, 905
    # D1 fix: forearm runs from the elbow (in front of the robe, at the cloak opening) up-left to the cuff.
    # The upper arm is on its own layer under the gold trim, so the arm reads as one jointed limb.
    SLV = [(-206, 918), (-150, 958), (-84, 1008), (-24, 1058), (22, 1104), (38, 1150), (14, 1190), (-60, 1200),
           (-150, 1186), (-250, 1166), (-350, 1134), (-430, 1078), (-470, 1004), (-458, 934)]
    items = [
        it("Forearm cast shadow", path([(x + 16, y + 26) for x, y in SLV], B), "#04061a", opacity=55, blur=14),
        it("Elbow contact shadow", ellipse(-14, 1204, 96, 26, 0, B), "#04061a", opacity=65, blur=12),
        it("Sleeve", path(SLV, B), lin([["#34459c", 0], ["#222d6c", 45], ["#141a46", 100]])),
        it("Sleeve underside", taper([(-464, 980), (-420, 1068), (-330, 1130), (-200, 1172), (-60, 1196)], B, 58, 0.2, 0.3), NAVY_SH, opacity=85),
        it("Bell fold 1", taper([(-420, 962), (-402, 1040), (-352, 1110)], B, 18, 0.3, 0.5), NAVY_SH),
        it("Bell fold 2", taper([(-330, 952), (-302, 1040), (-262, 1128)], B, 14, 0.3, 0.5), NAVY_SH),
        it("Elbow fold 1", taper([(-130, 1040), (-150, 1092), (-148, 1150)], B, 12, 0.3, 0.4), NAVY_SH, opacity=85),
        it("Elbow fold 2", taper([(-70, 1062), (-90, 1112), (-80, 1162)], B, 14, 0.3, 0.4), NAVY_SH),
        it("Elbow fold 3", taper([(-18, 1092), (-36, 1132), (-28, 1176)], B, 10, 0.3, 0.4), NAVY_SH),
        it("Elbow fold light", taper([(-58, 1066), (-76, 1112)], B, 6, 0.3, 0.5), NAVY_LT, opacity=60),
        it("Bell edge light", taper([(-446, 958), (-436, 1024)], B, 8, 0.3, 0.5), "#5b6fc4", opacity=70),
        it("Forearm ridge light", taper([(-200, 934), (-130, 984), (-60, 1036), (2, 1086)], B, 16, 0.2, 0.5), "#5b6fc4", opacity=85),
        it("Forearm ridge spec", taper([(-180, 944), (-110, 994), (-50, 1040)], B, 4, 0.3, 0.3), "#9fb0ff", opacity=70),
        it("Orb bounce on sleeve", taper([(-236, 926), (-168, 962)], B, 6, 0.3, 0.3), CYAN, opacity=45, blend="screen"),
        it("Sleeve line", taper(SLV[:14], B, 8, 0.05, 0.05), "#07081c"),
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


def build():
    from scene_v7 import wisteria_items, particle_items  # v6 decorative pass, v7 wisteria
    from scene_v7_bg import star_items, moon_items, moon_halo_items, moon_clip, castle_items, mist_items, mid_tree_items  # v7 crisp background
    L = []

    def add(layer, items, clear=True, **kw):
        e = {"layer": layer, "clear": clear, "items": items}
        e.update(kw)
        L.append(e)

    add("Background art/Sky", sky_items())
    add("Background art/Stars", star_items())
    add("Background art/Moon", moon_halo_items())
    add("Background art/Moon", moon_items(), clear=False, clip=moon_clip())
    add("Background art/Far castle", castle_items())
    add("Background art/Mist", mist_items())
    add("Background art/Mid trees", mid_tree_items())
    add("Magic/Rune circle", rune_circle_items())
    add("Cat/Cowl", cowl_items())
    add("Cat/Chest fluff", chest_items())
    add("Cat/Cloak", cloak_items())
    add("Cat/Upper arm", upper_arm_items())
    add("Cat/Cloak trim", trim_items())
    add("Cat/Amulet", amulet_items())
    add("Cat/Neck ruff", neck_ruff_items())
    add("Cat/Paw & orb", paw_items())
    add("Cat/Ears", ear_items())
    head = head_items()
    over = [h for h in head if h["name"].startswith(("Line ", "Ear root fur"))]  # outside the head clip
    add("Cat/Head", [h for h in head if h not in over], clip=path(HEAD, head_xy))
    add("Cat/Head", over, clear=False)
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
