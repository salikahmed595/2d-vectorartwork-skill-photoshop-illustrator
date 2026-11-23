"""Build one audit sheet for the 12-point visual audit (bookkeeping only - no drawing, no AI).

    python audit_sheet.py final.png --silhouette cat_alpha.png --vector effects_off.png --out sheet.png

Panels: full (downscaled), greyscale (value check), silhouette-only (alpha filled black on white),
effects-off (vector preview before Photoshop light), 256 px, 64 px circle crop.
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

P = 640


def circle(im, size):
    im = im.resize((size, size), Image.LANCZOS)
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse((0, 0, size - 1, size - 1), fill=255)
    out = Image.new("RGB", (size, size), (24, 24, 28))
    out.paste(im, (0, 0), m)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--silhouette", help="PNG whose alpha is the subject silhouette")
    ap.add_argument("--vector", help="effects-off preview (vector stage)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    im = Image.open(a.image).convert("RGB")
    panels = [("full", im.resize((P, P), Image.LANCZOS)),
              ("greyscale", ImageOps.grayscale(im).convert("RGB").resize((P, P), Image.LANCZOS))]
    if a.silhouette:
        al = Image.open(a.silhouette).convert("RGBA").split()[-1].resize((P, P), Image.LANCZOS)
        sil = Image.new("RGB", (P, P), (255, 255, 255))
        sil.paste((0, 0, 0), (0, 0), al)
        panels.append(("silhouette", sil))
    if a.vector:
        panels.append(("effects-off", Image.open(a.vector).convert("RGB").resize((P, P), Image.LANCZOS)))
    small = Image.new("RGB", (P, P), (24, 24, 28))
    small.paste(im.resize((256, 256), Image.LANCZOS), (40, 40))
    small.paste(circle(im, 64), (40 + 256 + 60, 40 + 96))
    small.paste(circle(im, 128), (40 + 256 + 60 + 90, 40 + 64))
    panels.append(("256 / 64 / 128 circle", small))
    cols = 3
    rows = (len(panels) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * P + (cols + 1) * 10, rows * (P + 30) + 10), (16, 16, 18))
    d = ImageDraw.Draw(sheet)
    for i, (name, pim) in enumerate(panels):
        x, y = 10 + (i % cols) * (P + 10), 10 + (i // cols) * (P + 30)
        sheet.paste(pim, (x, y + 20))
        d.text((x, y + 4), name, fill=(230, 230, 230))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(a.out)
    print(a.out, sheet.size)


if __name__ == "__main__":
    main()
