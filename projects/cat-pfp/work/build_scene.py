"""Builds the vector night scene (SVG) that Illustrator opens, and crops the hero cutout to its bounds.

Usage: python build_scene.py <work_dir>
Outputs: <work_dir>/scene.svg, <work_dir>/hero-crop.png
"""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

W = H = 2000
MOON = (1050, 790, 590)
CYAN = "#5ff5e6"
PALE = "#c9fff6"
HERO_X, HERO_Y, HERO_W = 30, 440, 1572  # cat placement on the 2000 pt artboard
EYES = {"eyeL": (720, 313, 46, 33), "eyeR": (883, 255, 34, 31)}  # cx, cy, rx, ry in cutout px


def crop_hero(work: Path) -> tuple[int, int]:
    im = Image.open(work / "hero-graded.png").convert("RGBA")
    box = im.getchannel("A").getbbox()
    out = im.crop(box)
    out.save(work / "hero-crop.png")
    s = HERO_W / out.size[0]
    print(f"cat: x={HERO_X} y={HERO_Y} width={HERO_W}")
    for name, (cx, cy, rx, ry) in EYES.items():
        x0, y0, x1, y1 = cx - rx, cy - ry, cx + rx, cy + ry
        eye = im.crop((x0, y0, x1, y1))
        mask = Image.new("L", (eye.width * 4, eye.height * 4), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, mask.width - 1, mask.height - 1), fill=255)
        eye.putalpha(ImageChops.multiply(eye.getchannel("A"), mask.resize(eye.size, Image.LANCZOS)))
        eye = eye.resize((eye.width * 3, eye.height * 3), Image.LANCZOS)
        eye.save(work / f"{name}.png")
        print(f"{name}: x={HERO_X + (x0 - box[0]) * s:.1f} y={HERO_Y + (y0 - box[1]) * s:.1f} width={(x1 - x0) * s:.1f}")
    return out.size


def sparkle(x: float, y: float, s: float) -> str:
    pts = []
    for i in range(8):
        r = s if i % 2 == 0 else s * 0.16
        a = math.pi / 4 * i - math.pi / 2
        pts.append(f"{x + r * math.cos(a):.1f},{y + r * math.sin(a):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{PALE}"/>'


def meteor(hx: float, hy: float, length: float, deg: float = -32) -> str:
    a = math.radians(deg)
    tx, ty = hx + length * math.cos(a), hy + length * math.sin(a)
    nx, ny = -math.sin(a) * 6, math.cos(a) * 6
    return (
        f'<polygon points="{hx + nx:.1f},{hy + ny:.1f} {hx - nx:.1f},{hy - ny:.1f} {tx:.1f},{ty:.1f}" '
        f'fill="{CYAN}" opacity="0.85"/><circle cx="{hx}" cy="{hy}" r="8" fill="#ffffff"/>'
    )


def blade(bx: float, by: float, h: float, lean: float, w: float, closed: bool = True) -> str:
    tx, ty = bx + lean, by - h
    cx, cy = bx + lean * 0.15, by - h * 0.6
    d = f"M {bx - w:.1f} {by:.1f} Q {cx - w * 0.4:.1f} {cy:.1f} {tx:.1f} {ty:.1f} Q {cx + w:.1f} {cy:.1f} {bx + w:.1f} {by:.1f}"
    return d + (" Z" if closed else "")


def build(work: Path) -> None:
    rnd = random.Random(20261120)
    mx, my, mr = MOON
    bg, fg, fx = [], [], []

    # ---- sky + stars
    bg.append(f'<rect id="Sky" x="0" y="0" width="{W}" height="{H}" fill="url(#sky)"/>')
    stars = []
    while len(stars) < 90:
        x, y = rnd.uniform(20, W - 20), rnd.uniform(20, 1180)
        if math.hypot(x - mx, y - my) < mr + 40:
            continue
        r = rnd.choice([2, 2.5, 3, 3, 4, 5])
        stars.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{rnd.choice([PALE, "#ffffff", "#a9c8ff"])}" opacity="{rnd.choice([0.55, 0.75, 0.95])}"/>')
    bg.append('<g id="Stars">' + "".join(stars) + "</g>")
    spark = [(170, 150, 30), (640, 110, 22), (1240, 90, 26), (1900, 640, 24), (120, 930, 20), (330, 620, 16), (1820, 980, 18)]
    bg.append('<g id="Sparkles">' + "".join(sparkle(*s) for s in spark) + "</g>")
    bg.append('<g id="Meteors">' + meteor(1500, 215, 260) + meteor(1705, 330, 210) + meteor(1330, 120, 170) + "</g>")

    # ---- moon
    craters = [(-210, -250, 95), (190, -330, 60), (330, -90, 120), (-330, 60, 70), (60, -130, 45), (-80, 300, 110), (300, 260, 55)]
    moon = [f'<circle id="MoonDisc" cx="{mx}" cy="{my}" r="{mr}" fill="url(#moon)"/>']
    moon += [f'<circle cx="{mx + dx}" cy="{my + dy}" r="{r}" fill="#1f9fb4" opacity="0.16"/>' for dx, dy, r in craters]
    bg.append('<g id="Moon">' + "".join(moon) + "</g>")

    # ---- stylised clouds with glowing top edges
    clouds = [
        ("M -60 330 C 140 240 380 232 560 296 C 700 345 820 328 930 366 C 760 410 560 428 380 404 C 220 384 80 404 -60 440 Z",
         "M -60 330 C 140 240 380 232 560 296 C 700 345 820 328 930 366"),
        ("M 1250 500 C 1440 418 1700 404 2060 462 L 2060 570 C 1800 548 1520 578 1250 500 Z",
         "M 1250 500 C 1440 418 1700 404 2060 462"),
        ("M -60 1010 C 80 960 240 962 400 1004 C 300 1040 120 1052 -60 1076 Z",
         "M -60 1010 C 80 960 240 962 400 1004"),
    ]
    cl = []
    for body, edge in clouds:
        cl.append(f'<path d="{body}" fill="#2b2096" opacity="0.9"/>')
        cl.append(f'<path d="{edge}" fill="none" stroke="{CYAN}" stroke-width="6" stroke-linecap="round" opacity="0.9"/>')
    bg.append('<g id="Clouds">' + "".join(cl) + "</g>")

    # ---- mountains: far range with lit facets, near range with a neon ridge line
    far = "M 0 1380 L 140 1210 L 260 1300 L 420 1120 L 560 1260 L 720 1180 L 900 1330 L 1100 1240 L 1300 1330 L 1480 1160 L 1620 1270 L 1780 1090 L 2000 1280 L 2000 2000 L 0 2000 Z"
    facets = [
        "420,1120 560,1260 480,1330 440,1210", "140,1210 260,1300 190,1350 160,1270",
        "1780,1090 1620,1270 1710,1330 1765,1190", "1480,1160 1300,1330 1400,1360 1462,1250",
        "720,1180 900,1330 800,1350 735,1260",
    ]
    near_pts = "0 1560 L 180 1400 L 330 1500 L 520 1360 L 700 1520 L 900 1450 L 1100 1540 L 1320 1440 L 1500 1500 L 1680 1340 L 1840 1460 L 2000 1380"
    bg.append(
        '<g id="Mountains">'
        f'<path d="{far}" fill="#2c1d7c"/>'
        + "".join(f'<polygon points="{p}" fill="#4a36b4" opacity="0.9"/>' for p in facets)
        + f'<path d="M {near_pts} L 2000 2000 L 0 2000 Z" fill="#170f4a"/>'
        + f'<path d="M {near_pts}" fill="none" stroke="{CYAN}" stroke-width="4" stroke-linejoin="round" opacity="0.6"/>'
        + "</g>"
    )

    # ---- foreground: rocks, ground mound, grass (darkest layer, cyan rim)
    dark, rock = "#06051a", "#0c0a30"
    fg.append(f'<path d="M -20 1720 L 80 1570 L 225 1535 L 335 1640 L 410 1790 L -20 1830 Z" fill="{rock}"/>')
    fg.append('<polygon points="80,1570 225,1535 250,1640 130,1670" fill="#1b1668"/>')
    fg.append(f'<path d="M 80 1570 L 225 1535 L 335 1640" fill="none" stroke="{CYAN}" stroke-width="4" stroke-linejoin="round" opacity="0.75"/>')
    fg.append(f'<path d="M 2020 1650 L 1905 1485 L 1765 1470 L 1665 1600 L 1600 1810 L 2020 1840 Z" fill="{rock}"/>')
    fg.append('<polygon points="1905,1485 1765,1470 1740,1590 1860,1620" fill="#1b1668"/>')
    fg.append(f'<path d="M 1905 1485 L 1765 1470 L 1665 1600" fill="none" stroke="{CYAN}" stroke-width="4" stroke-linejoin="round" opacity="0.75"/>')
    blades, lit = [], []
    for cx0, base, n in [(470, 1800, 9), (640, 1850, 6), (1380, 1860, 6), (1540, 1820, 9), (160, 1700, 5), (1850, 1690, 5)]:
        for _ in range(n):
            args = (cx0 + rnd.uniform(-70, 70), base + 60, rnd.uniform(170, 310), rnd.uniform(-70, 70), rnd.uniform(9, 16))
            blades.append(blade(*args))
            if rnd.random() < 0.4:
                lit.append(blade(*args, closed=False))
    fg.append(f'<path id="Grass" d="{" ".join(blades)}" fill="{dark}"/>')
    fg.append(f'<path id="GrassRim" d="{" ".join(lit)}" fill="none" stroke="{CYAN}" stroke-width="2.5" opacity="0.5"/>')
    top = "M -20 1690 C 120 1650 260 1690 380 1740 C 560 1815 760 1850 1000 1855 C 1250 1860 1450 1835 1620 1770 C 1760 1715 1880 1650 2020 1632"
    fg.append(f'<path id="Ground" d="{top} L 2020 2020 L -20 2020 Z" fill="{dark}"/>')
    fg.append(f'<path id="GroundRim" d="{top}" fill="none" stroke="{CYAN}" stroke-width="4" stroke-linecap="round" opacity="0.55"/>')

    # ---- fireflies (glow added in Photoshop)
    for _ in range(34):
        side = rnd.random()
        x = rnd.uniform(40, 520) if side < 0.4 else rnd.uniform(1480, 1960) if side < 0.8 else rnd.uniform(520, 1480)
        y = rnd.uniform(1180, 1900) if side < 0.8 else rnd.uniform(1700, 1930)
        fx.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.choice([4, 5, 6, 8, 10])}" fill="{rnd.choice([PALE, CYAN, "#ffffff"])}"/>')

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="#060520"/><stop offset="0.34" stop-color="#150f4c"/>
<stop offset="0.6" stop-color="#3a1d88"/><stop offset="0.72" stop-color="#5b2ba6"/><stop offset="1" stop-color="#120c38"/>
</linearGradient>
<radialGradient id="moon" cx="0.42" cy="0.38" r="0.7">
<stop offset="0" stop-color="#effffb"/><stop offset="0.45" stop-color="#8df3e6"/><stop offset="1" stop-color="#2fbccb"/>
</radialGradient>
</defs>
<g id="BG">{"".join(bg)}</g>
<g id="FG">{"".join(fg)}</g>
<g id="FX">{"".join(fx)}</g>
</svg>'''
    (work / "scene.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    work_dir = Path(sys.argv[1])
    print("hero-crop size:", crop_hero(work_dir))
    build(work_dir)
    print("wrote", work_dir / "scene.svg")
