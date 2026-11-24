"""Mechanical QC for a finished PFP. Writes circle-crop previews and qc.json next to the image
(in a qc/ folder) and exits 1 if a hard check fails. It cannot judge anatomy, likeness or taste -
look at the previews yourself.

    python qc.py out/name_2000.jpg
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageStat


def circle(img: Image.Image, size: int) -> Image.Image:
    im = img.resize((size, size), Image.LANCZOS).convert("RGBA")
    big = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(big).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    im.putalpha(big.resize((size, size), Image.LANCZOS))
    return im


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    img = Image.open(path).convert("RGB")
    w, h = img.size
    grey = img.convert("L")
    centre = grey.crop((w // 4, h // 4, 3 * w // 4, 3 * h // 4))

    def sharp(im: Image.Image) -> float:
        return round(ImageStat.Stat(im.filter(ImageFilter.FIND_EDGES)).stddev[0], 1)

    hist = grey.histogram()
    total = w * h
    sat = ImageStat.Stat(img.convert("HSV").split()[1]).mean[0]
    r = {
        "file": str(path),
        "size": [w, h],
        "mean_brightness": round(ImageStat.Stat(grey).mean[0], 1),
        "centre_brightness": round(ImageStat.Stat(centre).mean[0], 1),
        "mean_saturation": round(sat, 1),
        "clipped_white_pct": round(100 * sum(hist[250:]) / total, 2),
        "crushed_black_pct": round(100 * sum(hist[:6]) / total, 2),
        "sharpness_full": sharp(grey),
        "sharpness_centre": sharp(centre),
    }
    fails, warns = [], []
    if w != h:
        fails.append("not square")
    if min(w, h) < 1080:
        fails.append("smaller than 1080 px")
    elif min(w, h) < 2000:
        warns.append("below the 2000 px master size")
    if r["clipped_white_pct"] > 4:
        warns.append("more than 4% blown highlights - reduce bloom")
    if r["crushed_black_pct"] > 35:
        warns.append("more than 35% pure black - lift shadows or reduce vignette")
    if r["centre_brightness"] < r["mean_brightness"]:
        warns.append("subject area is darker than the frame average - check separation")
    if r["sharpness_centre"] < 8:
        warns.append("centre looks soft - check upscale")
    if r["mean_saturation"] < 60:
        warns.append("low saturation for this style")
    r["fail"], r["warn"] = fails, warns

    qdir = path.parent / "qc"
    qdir.mkdir(exist_ok=True)
    for s in (256, 64):
        circle(img, s).save(qdir / f"{path.stem}_circle{s}.png")
    sheet = Image.new("RGB", (256 + 64 + 60, 296), (24, 24, 28))
    sheet.paste(circle(img, 256), (20, 20), circle(img, 256))
    sheet.paste(circle(img, 64), (296, 116), circle(img, 64))
    sheet.save(qdir / f"{path.stem}_circle_sheet.png")
    (qdir / f"{path.stem}_qc.json").write_text(json.dumps(r, indent=2), encoding="utf-8")

    print(json.dumps(r, indent=2))
    print(f"previews: {qdir}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
