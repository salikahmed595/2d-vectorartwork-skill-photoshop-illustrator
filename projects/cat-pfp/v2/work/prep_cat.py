"""Lift the painted whiskers off the cat into their own layer and repair the fur underneath.

    <numpy+scipy python> prep_cat.py <work_dir>

Reads  cat-pick-4x.png (3072 px painted cat on a plain background).
Writes whiskers-3072.png (RGBA: only the whiskers / brow hairs), cat-clean.png (RGB: cat without them),
       whisker-check.png (preview: clean cat left, whiskers on magenta right).
Method: white top-hat (image minus its morphological opening) finds thin bright lines; only long, thin
connected pieces inside the hand-drawn whisker zones are kept.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ZONES = [  # 3072 px coordinates
    [(2380, 1180), (3072, 1080), (3072, 1820), (2800, 1820), (2380, 1560)],                             # right whiskers
    [(2050, 1380), (2060, 1560), (1900, 2420), (1540, 2420), (1130, 1760), (1170, 1580), (1700, 1380)],  # left whiskers
    [(1480, 590), (1900, 630), (2010, 960), (1750, 970)],                                               # left brow hairs
    [(2240, 540), (2550, 540), (2470, 940), (2270, 940)],                                               # right brow hairs
]
TOPHAT_MIN, MIN_DIAG, MIN_AREA = 20, 170, 300


def disk(r: int) -> np.ndarray:
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def main() -> None:
    work = Path(sys.argv[1])
    src = Image.open(work / "cat-pick-4x.png").convert("RGB")
    rgb = np.asarray(src, dtype=np.float32)
    lum = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)

    tophat = lum - ndi.grey_opening(lum, footprint=disk(11))
    zone_im = Image.new("L", src.size, 0)
    for poly in ZONES:
        ImageDraw.Draw(zone_im).polygon(poly, fill=255)
    cand = (tophat > TOPHAT_MIN) & (np.asarray(zone_im) > 0)

    labels, n = ndi.label(cand, structure=np.ones((3, 3)))
    keep = np.zeros_like(cand)
    kept = 0
    for i, sl in enumerate(ndi.find_objects(labels), 1):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        comp = labels[sl] == i
        area = int(comp.sum())
        diag = (h * h + w * w) ** 0.5
        if diag >= MIN_DIAG and area >= MIN_AREA and area / diag < 26:      # long and thin
            keep[sl] |= comp
            kept += 1
    print(f"components {n}, kept as whiskers {kept}, pixels {int(keep.sum())}")

    a_w = ndi.gaussian_filter(ndi.binary_dilation(keep, iterations=3).astype(np.float32), 1.5)
    whisk = rgb * 0.55 + np.array([255, 250, 238], dtype=np.float32) * 0.45
    out = np.dstack([whisk, a_w * 255]).clip(0, 255).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(work / "whiskers-3072.png")

    opened = np.dstack([ndi.gaussian_filter(ndi.grey_opening(rgb[..., c], footprint=disk(13)), 2) for c in range(3)])
    a_c = ndi.gaussian_filter(ndi.binary_dilation(keep, iterations=7).astype(np.float32), 3)[..., None]
    clean = (rgb * (1 - a_c) + opened * a_c).clip(0, 255).astype(np.uint8)
    Image.fromarray(clean, "RGB").save(work / "cat-clean.png")

    box = (1000, 450, 3072, 2450)
    left = Image.fromarray(clean).crop(box)
    right = Image.new("RGBA", src.size, (255, 0, 255, 255))
    right.alpha_composite(Image.fromarray(out, "RGBA"))
    sheet = Image.new("RGB", (left.width * 2, left.height))
    sheet.paste(left, (0, 0))
    sheet.paste(right.convert("RGB").crop(box), (left.width, 0))
    sheet.resize((sheet.width // 3, sheet.height // 3), Image.LANCZOS).save(work / "whisker-check.png")


if __name__ == "__main__":
    main()
