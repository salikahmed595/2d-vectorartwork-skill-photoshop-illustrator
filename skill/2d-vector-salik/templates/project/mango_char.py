"""Mango character, drawn as vector paths for ai_draw.py. Local coords: origin at the body centre, y down.
Every shape is hand-placed path data (no AI generation). Imported by mango_design.build()."""
import math
import random

from vec import it, path, taper, ellipse, poly, lin, rad, sample, mirror, canvas_xy, leaf_items

CX, CY, S = 1000, 1030, 1.15
LEAN = math.radians(5)  # whole figure leans into the wind, pivoting on the feet


def M(x, y):
    dx, dy = x, y - 420
    c, s = math.cos(LEAN), math.sin(LEAN)
    x, y = dx * c - dy * s, 420 + dx * s + dy * c
    return (CX + x * S, CY + y * S)


LINE = "#4a1c0c"
PEACH, PEACH_SH, PEACH_LT = "#ffa48c", "#e8706c", "#ffd2c0"
CAPE, CAPE_SH, CAPE_DEEP, CAPE_LT, CAPE_IN = "#b6e36b", "#86c34e", "#4f8f35", "#e6fbb0", "#5f9c3e"
GOLD, GOLD_LT, GOLD_DK = "#f2c14e", "#fff0b8", "#6a4310"

# ---------- body: mango silhouette with a slight lean of the tip to the right ----------
BODY = [(30, -388), (130, -366), (222, -292), (284, -176), (312, -36), (308, 110), (272, 240), (196, 338), (76, 386),
        (-58, 390), (-180, 348), (-264, 262), (-304, 130), (-302, -12), (-266, -148), (-200, -262), (-104, -350)]


def body_clip():
    return path(BODY, M)


def body_items():
    rr = random.Random(7)
    items = [
        it("Skin", path(BODY, M), lin([["#cfdc4c", 0], ["#ffd640", 26], ["#ffa22c", 52], ["#ff7a2a", 76], ["#ee503a", 100]])),
        # form: fill light from the upper left, so the right side and the base turn away into shade
        it("Side shade", path([(150, -350), (250, -246), (304, -96), (310, 80), (276, 236), (196, 338), (80, 388), (150, 306),
                               (214, 190), (236, 40), (226, -110), (196, -246)], M), "#e0582a", opacity=55),
        it("Base shade", ellipse(-10, 400, 300, 80, 0, M), "#d0502a", opacity=38),
        it("Core shadow", taper([(170, -300), (236, -120), (246, 60), (214, 230), (140, 340)], M, 26, 0.3, 0.3), "#c94a2a", opacity=40),
        it("Top light", ellipse(-110, -170, 150, 200, -18, M), "#fff4ac", opacity=55, blur=30),
        it("Cheek glow", ellipse(0, 140, 230, 120, 0, M), "#ffb45a", opacity=35, blur=24),
    ]
    # lenticels: the small pale dots on a real mango skin, kept off the face
    for k in range(46):
        x, y = rr.uniform(-280, 280), rr.uniform(-340, 360)
        if (x / 300) ** 2 + (y / 380) ** 2 > 0.82 or (abs(x) < 240 and 10 < y < 270):
            continue
        r = rr.uniform(2.4, 4.6)
        items.append(it(f"Lenticel {k}", ellipse(x, y, r, r * 0.8, 0, M), "#fff1b0" if y < 60 else "#ffc27a", opacity=60))
    items += [
        it("Gloss", path([(-214, -150), (-196, -236), (-140, -308), (-96, -326), (-130, -270), (-170, -200), (-188, -136)], M), "#fffbe0", opacity=88),
        it("Gloss dot", ellipse(-176, -92, 13, 17, -10, M), "#fffbe0", opacity=88),
        # back light: the low sun sits behind Mango, so both edges catch a warm rim (stronger on the sun side, right)
        it("Rim R", taper(BODY[1:9], M, 22, 0.15, 0.15), "#ffe58a", opacity=92),
        it("Rim L", taper(BODY[10:16], M, 12, 0.2, 0.2), "#ffd27a", opacity=70),
        it("Collar occlusion", taper([(-300, 150), (-150, 192), (0, 204), (150, 190), (300, 146)], M, 34, 0.1, 0.1), "#b8452a", opacity=38, blur=8),
    ]
    return items


# ---------- leaves and stem (identity: leaves with water droplets) ----------
def leaf_group_items():
    items = [it("Stem", taper([(26, -372), (34, -410), (52, -446)], M, 26, 0.0, 0.25), "#7a4a22"),
             it("Stem light", taper([(22, -380), (30, -410), (44, -440)], M, 7, 0.1, 0.3), "#c08a4a")]
    items += leaf_items("Leaf back", (18, -404), -150, 270, 100, -30, M, light="#4f9a42", dark="#24602e", rim="A", scale=S)
    items += leaf_items("Leaf big", (44, -410), -28, 340, 120, 32, M, rim="A", scale=S)
    items += leaf_items("Leaf top", (34, -418), -98, 200, 74, 22, M, light="#76c056", rim="B", scale=S)
    for k, (x, y, r) in enumerate([(150, -488, 13), (230, -470, 9), (-120, -470, 11), (40, -560, 8)]):
        items += [it(f"Droplet {k}", ellipse(x, y, r, r, 0, M), "#e4f7ff", opacity=50, stroke="#2a6a3a", stroke_width=2),
                  it(f"Droplet {k} shine", ellipse(x - r * .35, y - r * .35, r * .32, r * .32, 0, M), "#ffffff")]
    return items


# ---------- face ----------
def eye_shape(cx, cy, rx, ry, lid, slope):
    top = lambda x: cy - ry * (1 - lid) + slope * (x - cx)
    pts = []
    for k in range(36):
        a = 2 * math.pi * k / 36
        x, y = cx + math.cos(a) * rx, cy + math.sin(a) * ry
        pts.append((x, max(y, top(x))))
    return pts, top


EYES = {"L": (-100, 78, 50, 62, 0.12, 0.10), "R": (98, 76, 50, 62, 0.30, -0.16)}  # right eye half-lidded: the cool smirk


def eye_items(side):
    cx, cy, rx, ry, lid, slope = EYES[side]
    pts, top = eye_shape(cx, cy, rx, ry, lid, slope)
    clip = path(pts, M)
    inner = [
        it(f"Eye {side} base", path(pts, M), rad([["#5a3424", 0], ["#2a1610", 60], ["#120806", 100]])),
        it(f"Eye {side} iris glow", ellipse(cx + 2, cy + 30, 40, 26, 0, M), "#8a4a22", opacity=70),
        it(f"Eye {side} sunset bounce", taper([(cx - 36, cy + 34), (cx, cy + 54), (cx + 36, cy + 34)], M, 12, 0.2, 0.2), "#ff9a3a", opacity=80),
        it(f"Eye {side} lid shadow", taper([(cx - rx, top(cx - rx) + 6), (cx, top(cx) + 10), (cx + rx, top(cx + rx) + 6)], M, 22, 0.1, 0.1), "#000000", opacity=40),
        it(f"Eye {side} shine big", ellipse(cx - 17, cy - 12, 17, 21, -15, M), "#ffffff"),
        it(f"Eye {side} shine small", ellipse(cx + 20, cy + 24, 8, 8, 0, M), "#ffffff", opacity=95),
        it(f"Eye {side} spark", poly([(cx + 22, cy - 34), (cx + 25, cy - 25), (cx + 34, cy - 22), (cx + 25, cy - 19), (cx + 22, cy - 10),
                                       (cx + 19, cy - 19), (cx + 10, cy - 22), (cx + 19, cy - 25)], M), "#fff6d0", opacity=90),
    ]
    s = -1 if side == "L" else 1
    lines = [
        it(f"Eye {side} outline", path(pts, M), None, stroke="#1a0a06", stroke_width=4),
        it(f"Eye {side} lid line", taper([(cx - rx - 6 * -s, top(cx - rx) + 2), (cx, top(cx) - 2), (cx + rx + 4, top(cx + rx) + 1),
                                          (cx + s * (rx + 16), top(cx + s * rx) - 10)], M, 11, 0.05, 0.45), "#1a0a06"),
    ]
    return clip, inner, lines


def brow_items():
    return [it("Brow L", taper([(-158, -6), (-112, -32), (-60, -24)], M, 17, 0.25, 0.35), "#3f8a3a"),   # raised: the confident side
            it("Brow R", taper([(56, 18), (100, 6), (148, -12)], M, 17, 0.35, 0.25), "#3f8a3a")]     # low and level over the half-lid


def mouth_items():
    mouth = [(-36, 150), (0, 160), (42, 144, 'c'), (34, 168), (6, 184), (-20, 174)]
    return [
        it("Blush L", ellipse(-178, 150, 50, 27, -6, M), "#ff5470", opacity=42),
        it("Blush R", ellipse(176, 146, 50, 27, 6, M), "#ff5470", opacity=42),
        *[it(f"Blush tick {k}", taper([(x, 138), (x - 8, 158)], M, 4, 0.2, 0.2), "#ffe0d0", opacity=80)
          for k, x in enumerate((-196, -178, -160, 158, 176, 194))],
        it("Mouth", path(mouth, M), "#5a1612"),
        it("Tongue", ellipse(8, 176, 15, 7, -10, M), "#ff7a7a"),
        it("Smirk line", taper([(-48, 146), (-20, 156), (8, 158), (40, 142), (54, 128)], M, 7, 0.2, 0.25), "#2a0c06"),
    ]


# ---------- cape (behind the body), front collar and clasp ----------
# wind from the right: the cape streams out to the left, its tip flipping to show the lining
CAPE_PTS = [(-282, 186), (-340, 170), (-420, 166), (-490, 194), (-560, 184), (-640, 212), (-736, 248, 'c'), (-668, 300), (-640, 352),
            (-604, 404, 'c'), (-520, 398), (-440, 428), (-360, 418), (-280, 450), (0, 460), (250, 440), (320, 430, 'c'), (352, 370),
            (372, 300), (350, 230), (292, 186)]


def cape_items():
    items = [it("Cape", path(CAPE_PTS, M), lin([["#c6ee7e", 0], ["#a6dc5e", 55], ["#86c34e", 100]], -90))]
    # lining flip at the windblown tip shows the darker inner side
    items.append(it("Cape lining flip", path([(-736, 248, 'c'), (-668, 300), (-640, 352), (-690, 316), (-716, 282)], M), CAPE_IN))
    for k, (pts, w) in enumerate([([(-300, 232), (-380, 252), (-460, 242), (-550, 262), (-650, 262)], 46),
                                  ([(-300, 284), (-370, 316), (-450, 320), (-520, 352), (-590, 372)], 40),
                                  ([(-290, 334), (-340, 372), (-410, 384), (-480, 410)], 32), ([(300, 222), (336, 300), (346, 360), (326, 424)], 38)]):
        items.append(it(f"Fold shade {k}", taper(pts, M, w, 0.35, 0.05), CAPE_SH, opacity=90))
        items.append(it(f"Fold core {k}", taper([(x + 6, y) for x, y in pts], M, w * 0.22, 0.45, 0.05), CAPE_DEEP, opacity=85))
    for k, (pts, w) in enumerate([([(-320, 206), (-400, 214), (-480, 206), (-570, 224), (-670, 236)], 14),
                                  ([(-310, 258), (-390, 282), (-470, 286), (-560, 312), (-610, 328)], 10)]):
        items.append(it(f"Fold light {k}", taper(pts, M, w, 0.4, 0.1), CAPE_LT, opacity=85))
    items.append(it("Cape rim", taper(CAPE_PTS[0:7], M, 10, 0.1, 0.3), "#fff0a0", opacity=90))
    items.append(it("Cape rim R", taper(CAPE_PTS[16:21], M, 12, 0.1, 0.1), "#fff0a0", opacity=90))
    items.append(it("Cape line", path(CAPE_PTS, M), None, stroke="#2a4a1a", stroke_width=6))
    return items


def collar_items():
    band_top = [(-300, 168), (-150, 200), (0, 210), (150, 198), (300, 164)]
    band_bot = [(300, 196), (150, 232), (0, 242), (-150, 232), (-300, 198)]
    items = [
        # cape front edges drape over the arm roots, so the arms visibly come out from under the cape
        it("Cape flap L", path([(-300, 170), (-334, 220), (-334, 300, 'c'), (-292, 286), (-262, 226)], M), CAPE),
        it("Cape flap L shade", taper([(-318, 200), (-318, 290)], M, 12, 0.2, 0.2), CAPE_SH),
        it("Cape flap R", path([(300, 166), (336, 216), (340, 296, 'c'), (298, 282), (264, 222)], M), CAPE_SH),
        it("Cape flap R rim", taper([(320, 186), (342, 240), (340, 292)], M, 8, 0.2, 0.2), "#fff0a0", opacity=90),
        it("Cape flap lines L", path([(-300, 170), (-334, 220), (-334, 300, 'c'), (-292, 286), (-262, 226)], M), None, stroke="#2a4a1a", stroke_width=5),
        it("Cape flap lines R", path([(300, 166), (336, 216), (340, 296, 'c'), (298, 282), (264, 222)], M), None, stroke="#2a4a1a", stroke_width=5),
        it("Collar", path(band_top + band_bot, M), lin([["#d4f590", 0], ["#9ad256", 100]], -90)),
        it("Collar bevel", taper(band_top, M, 6, 0.1, 0.1), "#f4ffd0", opacity=85),
        it("Collar under", taper(band_bot, M, 6, 0.1, 0.1), "#5f9c3e", opacity=90),
        it("Collar line", path(band_top + band_bot, M), None, stroke="#2a4a1a", stroke_width=5),
    ]
    # gold leaf clasp with an orange gem
    clasp = [(0, 196, 'c'), (26, 210), (34, 226), (0, 250, 'c'), (-34, 226), (-26, 210)]
    items += [it("Clasp", path(clasp, M), lin([["#fff0b8", 0], ["#f2c14e", 50], ["#b07a1e", 100]], -90)),
              it("Clasp line", path(clasp, M), None, stroke=GOLD_DK, stroke_width=4),
              it("Clasp gem", ellipse(0, 224, 11, 11, 0, M), rad([["#fff2c0", 0], ["#ff9a2a", 45], ["#c24a10", 100]])),
              it("Clasp gem shine", ellipse(-4, 220, 3.5, 3.5, 0, M), "#ffffff")]
    return items


# ---------- arms, controller, hands, feet ----------
def arm_items():
    items = []
    for side, pts in (("L", [(-292, 196), (-262, 262), (-196, 318), (-150, 336)]), ("R", [(292, 192), (266, 256), (204, 310), (156, 326)])):
        items += [it(f"Arm {side} line", taper(pts, M, 54, 0.0, 0.0), LINE),
                  it(f"Arm {side}", taper(pts, M, 43, 0.0, 0.0), PEACH),
                  it(f"Arm {side} shade", taper([(x + 3, y + 8) for x, y in pts], M, 17, 0.1, 0.1), PEACH_SH, opacity=85),
                  it(f"Arm {side} light", taper([(x - 3, y - 9) for x, y in pts[1:]], M, 8, 0.2, 0.3), PEACH_LT, opacity=85),
                  it(f"Arm {side} occlusion", ellipse(pts[1][0], pts[1][1] - 18, 30, 14, 40 if side == "L" else -40, M), "#3a120a", opacity=35)]
    return items


CT_X, CT_Y, CT_R, CT_S = 0, 300, -6, 0.86


def C(x, y):
    c, s = math.cos(math.radians(CT_R)), math.sin(math.radians(CT_R))
    x, y = x * CT_S, y * CT_S
    return M(CT_X + x * c - y * s, CT_Y + x * s + y * c)


CTRL = [(-150, -42), (-60, -52), (0, -46), (60, -52), (150, -42), (186, 6), (198, 66), (176, 98, 'c'), (128, 84), (92, 42),
        (-92, 42), (-128, 84), (-176, 98, 'c'), (-198, 66), (-186, 6)]


def controller_items():
    items = [it("Pad body", path(CTRL, C), lin([["#4a4e68", 0], ["#2a2c3c", 60], ["#1a1b26", 100]], -90)),
             it("Pad top light", taper([(-150, -34), (-60, -44), (0, -38), (60, -44), (150, -34)], C, 10, 0.1, 0.1), "#7c82a8", opacity=85),
             it("Pad rim", taper([(150, -42), (186, 6), (198, 66), (176, 98)], C, 9, 0.2, 0.2), "#ffb460", opacity=85),
             it("Pad line", path(CTRL, C), None, stroke="#0e0c14", stroke_width=6)]
    # d-pad
    for k, (w, h) in enumerate([(14, 40), (40, 14)]):
        items.append(it(f"Dpad {k}", poly([(-110 - w / 2, -h / 2 - 2), (-110 + w / 2, -h / 2 - 2), (-110 + w / 2, h / 2 - 2), (-110 - w / 2, h / 2 - 2)], C), "#101018"))
    items.append(it("Dpad shine", poly([(-117, -22), (-103, -22), (-103, -16), (-117, -16)], C), "#5a5f7d"))
    for k, (x, y, col) in enumerate([(110, -22, "#ff8a1f"), (132, 0, "#7ad14c"), (110, 22, "#2ec5d8"), (88, 0, "#ffd43f")]):
        items += [it(f"Button {k}", ellipse(x, y, 11, 11, 0, C), col, stroke="#0e0c14", stroke_width=2.5),
                  it(f"Button {k} shine", ellipse(x - 3, y - 4, 3.6, 3, 0, C), "#ffffff", opacity=85)]
    for k, x in enumerate((-46, 46)):
        items += [it(f"Stick {k} well", ellipse(x, 28, 23, 23, 0, C), "#0c0c12"),
                  it(f"Stick {k}", ellipse(x, 26, 16, 16, 0, C), rad([["#5a5f7d", 0], ["#2a2c3c", 100]])),
                  it(f"Stick {k} shine", ellipse(x - 5, 21, 5, 4, 0, C), "#9aa0c8", opacity=80)]
    items += [it("LED glow", ellipse(0, -22, 38, 14, 0, C), "#ff9a2a", opacity=55, blend="screen", blur=6),
              it("LED", poly([(-22, -26), (22, -26), (22, -18), (-22, -18)], C), "#ffc46a"),
              it("Home", ellipse(0, 4, 9, 9, 0, C), "#ff8a1f", stroke="#0e0c14", stroke_width=2)]
    return items


def hand_items():
    items = []
    for side, (x, y, rot) in (("L", (-160, 346, 24)), ("R", (160, 338, -24))):
        s = -1 if side == "L" else 1
        items += [it(f"Hand {side}", ellipse(x, y, 44, 36, rot, M), lin([["#ffc2ae", 0], [PEACH, 55], [PEACH_SH, 100]], -90),
                     stroke=LINE, stroke_width=5),
                  it(f"Thumb {side}", ellipse(x - s * 26, y - 30, 17, 13, -s * 30, M), PEACH, stroke=LINE, stroke_width=4),
                  it(f"Hand {side} light", ellipse(x - 8, y - 14, 15, 8, rot, M), PEACH_LT, opacity=85),
                  it(f"Finger {side}", taper([(x + s * 8, y + 4), (x + s * 18, y + 18)], M, 4, 0.2, 0.2), "#c0504c", opacity=80)]
    return items


def feet_items():
    items = []
    for side, (x, y, rot) in (("L", (-116, 410, -6)), ("R", (128, 406, 8))):
        items += [it(f"Foot {side}", ellipse(x, y, 64, 34, rot, M), lin([[PEACH, 0], [PEACH_SH, 100]], -90), stroke=LINE, stroke_width=5),
                  it(f"Foot {side} light", ellipse(x - 14, y - 6, 26, 9, rot, M), PEACH_LT, opacity=80)]
        for k in (-1, 1):
            items.append(it(f"Toe {side}{k}", taper([(x + k * 20, y + 10), (x + k * 22, y + 28)], M, 4, 0.2, 0.2), "#b8484a", opacity=85))
    return items
