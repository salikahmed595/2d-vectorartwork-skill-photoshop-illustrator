"""Split a painted (raster) character into one PNG layer per body part and prove the parts rebuild it.

    python split_parts_raster.py parts.json

Config (paths relative to the json file):
{
  "image": "cat-full.png",            RGBA, character already cut out, at final canvas size
  "out_dir": "parts",
  "character": "Cat",
  "start_index": 1,                   first number used in the file names
  "transform": {"scale": 0.534, "dx": -70, "dy": 300},   optional: coordinates below are in source px
  "parts": [                          bottom to top
    {"layer": "Body", "pieces": [{"name": "Body", "polygon": [[x, y], ...]}]},
    {"layer": "Eyes", "fill_under": 8,
     "pieces": [{"name": "Eye L", "ellipse": [cx, cy, rx, ry, degrees]}]}
  ]
}
- Lower parts must reach ~40 px under the part above; upper seams must lie inside the part below.
- "fill_under": N paints soft fur-coloured skin under that part on every layer below it (inset N px), so
  the part can be moved or hidden without a copy of itself showing through.
Writes NN-<character>-<layer>.png, manifest.json, _parts_sheet.png. Exit 1 if the recomposed parts differ
from the input. Needs only Pillow.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat

SS = 3  # supersampling for smooth part edges


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def piece_points(piece: dict, tf: dict) -> list[tuple[float, float]]:
    k, dx, dy = tf.get("scale", 1.0), tf.get("dx", 0.0), tf.get("dy", 0.0)
    if "ellipse" in piece:
        cx, cy, rx, ry, deg = piece["ellipse"]
        a = math.radians(deg)
        pts = [(cx + rx * math.cos(t) * math.cos(a) - ry * math.sin(t) * math.sin(a),
                cy + rx * math.cos(t) * math.sin(a) + ry * math.sin(t) * math.cos(a))
               for t in (2 * math.pi * i / 96 for i in range(96))]
    else:
        pts = piece["polygon"]
    return [(dx + x * k, dy + y * k) for x, y in pts]


def part_mask(part: dict, size: tuple[int, int], tf: dict) -> Image.Image:
    big = Image.new("L", (size[0] * SS, size[1] * SS), 0)
    d = ImageDraw.Draw(big)
    for piece in part["pieces"]:
        d.polygon([(x * SS, y * SS) for x, y in piece_points(piece, tf)], fill=255)
    return big.resize(size, Image.LANCZOS)


def fill_under(rgb: Image.Image, mask: Image.Image, inset: int) -> Image.Image:
    """Replace what is under `mask` (shrunk by `inset`) with a smooth blend of the surrounding colours."""
    inner = mask.point(lambda v: 255 if v > 127 else 0).filter(ImageFilter.MinFilter(2 * inset + 1))
    ring = ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(4 * inset + 1)), mask)
    mean = tuple(int(v) for v in ImageStat.Stat(rgb, ring).mean)
    out = rgb.copy()
    out.paste(mean, mask=inner)
    soft = inner.filter(ImageFilter.GaussianBlur(1.5))
    for radius in (24, 16, 12, 8, 8, 6, 6, 4, 4, 4):
        out.paste(out.filter(ImageFilter.GaussianBlur(radius)), mask=soft)
    return out


def premultiplied(im: Image.Image) -> Image.Image:
    r, g, b, a = im.split()
    return Image.merge("RGBA", [ImageChops.multiply(c, a) for c in (r, g, b)] + [a])


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    cfg_path = Path(sys.argv[1]).resolve()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    out = (cfg_path.parent / cfg["out_dir"]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    src = Image.open(cfg_path.parent / cfg["image"]).convert("RGBA")
    tf = cfg.get("transform", {})
    char, parts = cfg["character"], cfg["parts"]
    masks = [part_mask(p, src.size, tf) for p in parts]

    # layers under a fill_under part are cut from a copy where that part has been painted out
    under = [src.convert("RGB")] * len(parts)
    painted = src.convert("RGB")
    for i in range(len(parts) - 1, -1, -1):
        under[i] = painted
        if parts[i].get("fill_under"):
            painted = fill_under(painted, masks[i], int(parts[i]["fill_under"]))
    alpha = src.getchannel("A")

    manifest = {"character_layer": char, "size": list(src.size), "layers": []}
    comp = Image.new("RGBA", src.size, (0, 0, 0, 0))
    tiles = []
    for n, (part, mask) in enumerate(zip(parts, masks), cfg.get("start_index", 1)):
        layer = under[n - cfg.get("start_index", 1)].copy()
        layer.putalpha(ImageChops.multiply(alpha, mask))
        file = out / f"{n:02d}-{slug(char)}-{slug(part['layer'])}.png"
        layer.save(file)
        comp.alpha_composite(layer)
        tiles.append(layer)
        manifest["layers"].append({"path": f"{char}/{part['layer']}", "file": file.name,
                                   "bbox": layer.getchannel("A").getbbox()})

    diff = ImageChops.difference(premultiplied(src), premultiplied(comp))
    worst = max(band.getextrema()[1] for band in diff.split())
    bad = ImageChops.lighter(Image.merge("RGB", diff.split()[:3]).convert("L"), diff.getchannel("A"))
    bad_pct = 100.0 * sum(bad.histogram()[25:]) / (src.size[0] * src.size[1])
    empty = [l["path"] for l in manifest["layers"] if l["bbox"] is None]
    manifest["check"] = {"max_channel_diff": worst, "pixels_off_by_more_than_24_pct": round(bad_pct, 4),
                         "empty_layers": empty}
    manifest["pass"] = bad_pct <= 0.05 and not empty
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    cell = 420
    sheet = Image.new("RGB", (cell * len(tiles), cell), (255, 0, 255))
    for i, layer in enumerate(tiles):
        tile = Image.new("RGBA", src.size, (255, 0, 255, 255))
        tile.alpha_composite(layer)
        sheet.paste(tile.convert("RGB").resize((cell, cell), Image.LANCZOS), (cell * i, 0))
    sheet.save(out / "_parts_sheet.png")

    print(json.dumps(manifest["check"], indent=2))
    for l in manifest["layers"]:
        print("  ", l["file"], "<-", l["path"], l["bbox"])
    print("PASS" if manifest["pass"] else "FAIL - parts do not rebuild the image (check polygon overlaps)")
    return 0 if manifest["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
