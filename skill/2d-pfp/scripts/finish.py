"""Finish a base PFP render: square crop, upscale, grade, bloom, vignette, optional
chromatic split / grain, designed title, and exports. Requires Pillow only.

    python finish.py base.png --out out/name --title "USERNAME" --preset neon
"""
from __future__ import annotations

import argparse
import os
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

WINFONTS = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"

# fill = vertical gradient (top, bottom); tracking is a fraction of font size.
PRESETS = {
    "neon": dict(font="bahnschrift.ttf", fill=((120, 235, 255), (40, 160, 215)), stroke=(8, 40, 70),
                 stroke_w=0.03, glow=(60, 220, 255), tracking=0.45, upper=True, shear=0.0, size=0.085),
    "fire": dict(font="impact.ttf", fill=((255, 240, 90), (255, 120, 10)), stroke=(90, 10, 0),
                 stroke_w=0.07, glow=(255, 110, 0), tracking=0.04, upper=True, shear=0.22, size=0.12),
    "fantasy": dict(font="georgiab.ttf", fill=((255, 190, 90), (200, 95, 20)), stroke=(60, 25, 5),
                    stroke_w=0.05, glow=(255, 170, 80), tracking=0.03, upper=False, shear=0.0, size=0.11),
    "impact": dict(font="impact.ttf", fill=((255, 60, 60), (150, 0, 10)), stroke=(10, 0, 0),
                   stroke_w=0.08, glow=(255, 30, 30), tracking=0.05, upper=True, shear=0.18, size=0.12),
}


def square_crop(img: Image.Image) -> Image.Image:
    w, h = img.size
    s = min(w, h)
    left, top = (w - s) // 2, (h - s) // 2
    return img.crop((left, top, left + s, top + s))


def bloom(img: Image.Image, strength: float, threshold: int = 170) -> Image.Image:
    if strength <= 0:
        return img
    span = 255 - threshold
    hi = img.point(lambda v: 0 if v < threshold else int((v - threshold) * 255 / span))
    hi = hi.filter(ImageFilter.GaussianBlur(img.width * 0.018))
    hi = ImageEnhance.Brightness(hi).enhance(strength)
    return ImageChops.screen(img, hi)


def vignette(img: Image.Image, strength: float) -> Image.Image:
    if strength <= 0:
        return img
    mask = Image.radial_gradient("L").resize(img.size, Image.BICUBIC)  # 0 centre -> 255 edge
    mask = mask.point(lambda v: int(max(0, v - 110) / 145 * 255 * strength))
    return Image.composite(Image.new("RGB", img.size, (0, 0, 0)), img, mask)


def chroma_split(img: Image.Image, px: int) -> Image.Image:
    if px <= 0:
        return img
    r, g, b = img.split()
    return Image.merge("RGB", (ImageChops.offset(r, px, 0), g, ImageChops.offset(b, -px, 0)))


def grain(img: Image.Image, amount: float, seed: int = 7) -> Image.Image:
    if amount <= 0:
        return img
    rnd = random.Random(seed)
    small = Image.frombytes("L", (256, 256), bytes(rnd.getrandbits(8) for _ in range(256 * 256)))
    noise = small.resize(img.size, Image.NEAREST).filter(ImageFilter.GaussianBlur(0.6))
    noise = Image.merge("RGB", (noise, noise, noise))
    return Image.blend(img, ImageChops.overlay(img, noise), amount)


def resolve_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    for cand in (Path(name), WINFONTS / name):
        if cand.is_file():
            return ImageFont.truetype(str(cand), size)
    raise SystemExit(f"Font not found: {name}")


def text_mask(text: str, font: ImageFont.FreeTypeFont, tracking: float, stroke: int) -> Image.Image:
    """White-on-black mask of the text with letter spacing; stroke>0 fattens it."""
    gap = int(font.size * tracking)
    widths = [font.getlength(ch) for ch in text]
    pad = stroke + int(font.size * 0.3)
    w = int(sum(widths) + gap * (len(text) - 1)) + pad * 2
    asc, desc = font.getmetrics()
    h = asc + desc + pad * 2
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    x = float(pad)
    for ch, cw in zip(text, widths):
        d.text((x, pad), ch, font=font, fill=255, stroke_width=stroke, stroke_fill=255)
        x += cw + gap
    return mask


def gradient(size: tuple[int, int], top: tuple, bottom: tuple) -> Image.Image:
    col = Image.new("RGB", (1, 256))
    col.putdata([tuple(int(top[i] + (bottom[i] - top[i]) * y / 255) for i in range(3)) for y in range(256)])
    return col.resize(size, Image.BILINEAR)


def build_title(text: str, canvas: int, p: dict, font_path: str | None, size: float | None,
                tracking: float | None) -> Image.Image:
    if p["upper"]:
        text = text.upper()
    track = p["tracking"] if tracking is None else tracking
    px = int(canvas * (size or p["size"]))
    max_w = canvas * 0.9
    while True:  # shrink to fit 90% of the canvas width
        font = resolve_font(font_path or p["font"], px)
        stroke = max(1, int(px * p["stroke_w"]))
        fill_m = text_mask(text, font, track, 0)
        if fill_m.width + 2 * stroke <= max_w or px <= 12:
            break
        px = int(px * 0.94)
    stroke_m = text_mask(text, font, track, stroke)
    # same padding rule in both masks -> centre the fill inside the stroke mask
    off = ((stroke_m.width - fill_m.width) // 2, (stroke_m.height - fill_m.height) // 2)
    fill_full = Image.new("L", stroke_m.size, 0)
    fill_full.paste(fill_m, off)

    margin = int(px * 0.6)
    size_px = (stroke_m.width + margin * 2, stroke_m.height + margin * 2)
    layer = Image.new("RGBA", size_px, (0, 0, 0, 0))

    def place(mask: Image.Image) -> Image.Image:
        full = Image.new("L", size_px, 0)
        full.paste(mask, (margin, margin))
        return full

    sm, fm = place(stroke_m), place(fill_full)
    glow_m = sm.filter(ImageFilter.GaussianBlur(px * 0.16)).point(lambda v: min(255, int(v * 1.6)))
    layer = Image.alpha_composite(layer, Image.merge("RGBA", (*Image.new("RGB", size_px, p["glow"]).split(), glow_m)))
    shadow = ImageChops.offset(sm, 0, max(2, px // 14)).filter(ImageFilter.GaussianBlur(px * 0.04))
    layer = Image.alpha_composite(layer, Image.merge("RGBA", (*Image.new("RGB", size_px, (0, 0, 0)).split(),
                                                              shadow.point(lambda v: int(v * 0.7)))))
    layer = Image.alpha_composite(layer, Image.merge("RGBA", (*Image.new("RGB", size_px, p["stroke"]).split(), sm)))
    box = fm.getbbox() or (0, 0, *size_px)
    grad = Image.new("RGB", size_px, p["fill"][0])
    grad.paste(gradient((size_px[0], box[3] - box[1]), *p["fill"]), (0, box[1]))
    layer = Image.alpha_composite(layer, Image.merge("RGBA", (*grad.split(), fm)))
    # thin top highlight for a bevelled look
    hi = ImageChops.subtract(fm, ImageChops.offset(fm, 0, max(1, px // 30)))
    layer = Image.alpha_composite(layer, Image.merge("RGBA", (*Image.new("RGB", size_px, (255, 255, 255)).split(),
                                                              hi.point(lambda v: int(v * 0.45)))))
    if p["shear"]:
        s = p["shear"]
        extra = int(abs(s) * layer.height)
        wide = Image.new("RGBA", (layer.width + extra, layer.height), (0, 0, 0, 0))
        wide.paste(layer, (extra, 0))
        layer = wide.transform(wide.size, Image.AFFINE, (1, s, 0, 0, 1, 0), Image.BICUBIC)
    return layer


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base", help="base render (any size; centre-cropped to square)")
    ap.add_argument("--out", required=True, help="output path prefix, e.g. out/username")
    ap.add_argument("--size", type=int, default=2000, help="master size in px (default 2000)")
    ap.add_argument("--title", default="", help="title text; omit for no title")
    ap.add_argument("--preset", choices=sorted(PRESETS), default="neon")
    ap.add_argument("--font", help="font file path or Windows font file name (overrides preset)")
    ap.add_argument("--title-size", type=float, help="title height as fraction of canvas")
    ap.add_argument("--title-y", type=float, default=0.13, help="title centre, fraction of height (0.13 top, 0.87 bottom)")
    ap.add_argument("--tracking", type=float, help="letter spacing as fraction of font size")
    ap.add_argument("--contrast", type=float, default=1.06)
    ap.add_argument("--saturation", type=float, default=1.10)
    ap.add_argument("--bloom", type=float, default=0.55, help="0 disables")
    ap.add_argument("--vignette", type=float, default=0.45, help="0 disables")
    ap.add_argument("--sharpen", type=int, default=60, help="unsharp percent, 0 disables")
    ap.add_argument("--chroma", type=int, default=0, help="chromatic split in px at master size")
    ap.add_argument("--grain", type=float, default=0.0, help="0-0.3")
    a = ap.parse_args()

    img = square_crop(Image.open(a.base).convert("RGB"))
    src = img.width
    if src != a.size:
        img = img.resize((a.size, a.size), Image.LANCZOS)
    if a.sharpen:
        img = img.filter(ImageFilter.UnsharpMask(radius=a.size / 900, percent=a.sharpen, threshold=3))
    img = ImageEnhance.Contrast(img).enhance(a.contrast)
    img = ImageEnhance.Color(img).enhance(a.saturation)
    img = bloom(img, a.bloom)
    img = chroma_split(img, a.chroma)
    img = vignette(img, a.vignette)
    img = grain(img, a.grain)

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    written = []

    def save(im: Image.Image, suffix: str) -> None:
        j = out.with_name(f"{out.name}_{a.size}{suffix}.jpg")
        im.save(j, quality=95, subsampling=0)
        written.append(j)

    save(img, "_clean")
    final = img
    if a.title:
        t = build_title(a.title, a.size, PRESETS[a.preset], a.font, a.title_size, a.tracking)
        final = img.convert("RGBA")
        final.alpha_composite(t, ((a.size - t.width) // 2, int(a.size * a.title_y) - t.height // 2))
        final = final.convert("RGB")
        save(final, "")
    w = out.with_name(f"{out.name}_1080.webp")
    final.resize((1080, 1080), Image.LANCZOS).save(w, quality=92, method=6)
    written.append(w)

    if src < a.size:
        print(f"note: base was {src}px, upscaled x{a.size / src:.2f} with Lanczos - inspect face and hands at 100%")
    for p in written:
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
