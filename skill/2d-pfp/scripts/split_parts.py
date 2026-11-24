"""Split a character into one Illustrator layer per body part, export every layer, and prove the split
did not change the picture.

    python split_parts.py parts.json

What it does (Illustrator must be running with the document open; uses the cli-anything-illustrator CLI):
1. Optional clean-up: removes light leftover shapes (e.g. a traced blanket) inside given boxes.
2. Exports the untouched character as `_reference.png`.
3. Rebuilds the document as real layers, bottom to top, from `stack` in the config:
   - a scene group becomes a layer (`explode: true` turns each child into its own sublayer);
   - the character becomes a parent layer with one sublayer per part. A part is either an existing
     group (e.g. hand-built eyes) or one or more polygon pieces. Each piece is a clip group holding a
     copy of the character art, pruned to the shapes that touch the polygon.
4. Exports every leaf layer alone to `out_dir` (`NN-name.png`) and writes `manifest.json`.
5. Re-composites the character part PNGs and compares them with `_reference.png`. Exit 1 if they differ.
6. Writes `_parts_sheet.png` (each character part over magenta) - look at it.

Rules for polygons (canvas px = artboard points, origin top-left, y down):
- List parts bottom to top. Lower parts must extend ~40 px UNDER the part above them, and the edge
  of an upper part that crosses the character must lie inside the part below. That hides seams.
- Polygons may spill outside the silhouette freely; only edges that cross the character matter.
- Make layers only for parts that are visible. Never invent hidden limbs.

The script does not save the document. Save it yourself (`cli-anything-illustrator doc save ...`).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops

CLI = "cli-anything-illustrator"

JSX_HEAD = """
var cfg = __CFG__;
var doc = app.documents.getByName(cfg.doc);
app.activeDocument = doc;
var ab = doc.artboards[doc.artboards.getActiveArtboardIndex()].artboardRect;
var L = ab[0], T = ab[1];
function pt(p) { return [L + p[0], T - p[1]]; }
function topGroup(name) { return doc.groupItems.getByName(name); }
"""

JSX_ERASE = """
(function () {
  __HEAD__
  var src = topGroup(cfg.source_group), n = 0;
  function luma(c) { return c.typename == 'RGBColor' ? 0.299 * c.red + 0.587 * c.green + 0.114 * c.blue : -1; }
  for (var e = 0; e < cfg.erase.length; e++) {
    var l = L + cfg.erase[e].bbox[0], t = T - cfg.erase[e].bbox[1], r = L + cfg.erase[e].bbox[2], b = T - cfg.erase[e].bbox[3];
    var colls = [src.pathItems, src.compoundPathItems];
    for (var c = 0; c < 2; c++) {
      for (var i = colls[c].length - 1; i >= 0; i--) {
        var it = colls[c][i], gb = it.geometricBounds;
        if (gb[0] < l || gb[2] > r || gb[1] > t || gb[3] < b) continue;
        var p = c == 0 ? it : it.pathItems[0];
        if (p.filled && luma(p.fillColor) >= cfg.erase[e].min_luma) { it.remove(); n++; }
      }
    }
  }
  return 'erased ' + n;
})();
"""

JSX_KEEP_ONLY = """
(function () {
  __HEAD__
  var keep = cfg.keep, n = 0;
  for (var i = 0; i < doc.layers.length; i++) {
    var items = doc.layers[i].pageItems;
    for (var k = 0; k < items.length; k++) {
      var it = items[k];
      if (it.parent.typename != 'Layer') continue;
      var show = !keep;
      if (keep) { for (var q = 0; q < keep.length; q++) if (keep[q] == it.name) show = true; }
      it.hidden = !show; n++;
    }
  }
  return 'ok ' + n;
})();
"""

JSX_SPLIT = """
(function () {
  __HEAD__
  var old = [], log = [];
  for (var i = 0; i < doc.layers.length; i++) old.push(doc.layers[i]);
  function prune(coll, l, t, r, b) {
    var n = 0;
    for (var i = coll.length - 1; i >= 0; i--) {
      var gb = coll[i].geometricBounds;
      if (gb[2] < l || gb[0] > r || gb[3] > t || gb[1] < b) { coll[i].remove(); n++; }
    }
    return n;
  }
  function addPiece(sub, src, piece) {
    var g = sub.groupItems.add(); g.name = piece.name;
    var art = src.duplicate(g, ElementPlacement.PLACEATEND); art.name = piece.name + ' art';
    var pts = [], l = 1e9, t = -1e9, r = -1e9, b = 1e9;
    for (var i = 0; i < piece.polygon.length; i++) {
      var q = pt(piece.polygon[i]); pts.push(q);
      if (q[0] < l) l = q[0]; if (q[0] > r) r = q[0]; if (q[1] > t) t = q[1]; if (q[1] < b) b = q[1];
    }
    var removed = prune(art.pathItems, l, t, r, b) + prune(art.compoundPathItems, l, t, r, b);
    var clip = g.pathItems.add(); clip.setEntirePath(pts); clip.closed = true;
    clip.filled = false; clip.stroked = false; clip.name = piece.name + ' clip';
    clip.move(g, ElementPlacement.PLACEATBEGINNING);
    clip.clipping = true; g.clipped = true;
    log.push(piece.name + ' kept ' + art.pageItems.length + ' pruned ' + removed);
  }
  for (var s = 0; s < cfg.stack.length; s++) {
    var e = cfg.stack[s];
    var lay = doc.layers.add(); lay.name = e.layer;
    if (e.parts) {
      var src = topGroup(e.source_group);
      for (var p = 0; p < e.parts.length; p++) {
        var part = e.parts[p];
        var sub = lay.layers.add(); sub.name = part.layer;
        if (part.group) { topGroup(part.group).move(sub, ElementPlacement.PLACEATBEGINNING); }
        else { for (var k = 0; k < part.pieces.length; k++) addPiece(sub, src, part.pieces[k]); }
      }
      src.remove();
    } else if (e.explode) {
      var grp = topGroup(e.group), kids = [];
      for (var c = grp.pageItems.length - 1; c >= 0; c--) {
        var kid = grp.pageItems[c];
        if (kid.parent.typename == 'GroupItem' && kid.parent.name == grp.name) kids.push(kid);
      }
      for (var c2 = 0; c2 < kids.length; c2++) {
        var sl = lay.layers.add(); sl.name = kids[c2].name ? kids[c2].name : (e.layer + ' ' + (c2 + 1));
        kids[c2].move(sl, ElementPlacement.PLACEATBEGINNING);
      }
      grp.remove();
      log.push(e.layer + ' exploded ' + kids.length);
    } else {
      topGroup(e.group).move(lay, ElementPlacement.PLACEATBEGINNING);
    }
  }
  for (var o = 0; o < old.length; o++) {
    try { if (old[o].pageItems.length === 0 && old[o].layers.length === 0) old[o].remove(); } catch (err) {}
  }
  return log.join('; ');
})();
"""

JSX_SHOW = """
(function () {
  __HEAD__
  var path = cfg.path;
  function all(ls, v) { for (var i = 0; i < ls.length; i++) { ls[i].visible = v; all(ls[i].layers, v); } }
  function only(ls, d) {
    for (var i = 0; i < ls.length; i++) {
      var m = ls[i].name == path[d];
      ls[i].visible = m;
      if (m) { if (d + 1 < path.length) only(ls[i].layers, d + 1); else all(ls[i].layers, true); }
    }
  }
  if (path.length) only(doc.layers, 0); else all(doc.layers, true);
  return 'ok';
})();
"""


def cli(*args: str) -> object:
    exe = shutil.which(CLI)
    if not exe:
        raise SystemExit(f"{CLI} is not on PATH")
    proc = subprocess.run([exe, "--json", *args], capture_output=True, text=True, encoding="utf-8")
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise SystemExit(f"{CLI} {' '.join(args[:3])} gave no JSON:\n{proc.stdout[-400:]}\n{proc.stderr[-400:]}")
    if not data.get("ok"):
        raise SystemExit(f"{CLI} {' '.join(args[:3])} failed: {data.get('error')}")
    return data["result"]


def jsx(template: str, cfg: dict, tmp: Path) -> str:
    code = template.replace("__HEAD__", JSX_HEAD).replace("__CFG__", json.dumps(cfg))
    tmp.write_text(code, encoding="utf-8")
    return str(cli("script", "run", "--file", str(tmp)))


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


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
    tmp = out / "_run.jsx"
    doc = cfg["doc"]
    chars = [e for e in cfg["stack"] if e.get("parts")]
    if len(chars) != 1:
        raise SystemExit("stack needs exactly one character entry (the one with 'parts')")
    char = chars[0]
    keep = [char["source_group"]] + [p["group"] for p in char["parts"] if p.get("group")]

    if cfg.get("erase"):
        print(jsx(JSX_ERASE, {"doc": doc, "source_group": char["source_group"], "erase": cfg["erase"]}, tmp))

    jsx(JSX_KEEP_ONLY, {"doc": doc, "keep": keep}, tmp)
    cli("--doc", doc, "doc", "export", str(out / "_reference.png"), "--overwrite")
    jsx(JSX_KEEP_ONLY, {"doc": doc, "keep": None}, tmp)

    print(jsx(JSX_SPLIT, {"doc": doc, "stack": cfg["stack"]}, tmp))

    layers = cli("--doc", doc, "layer", "list")["layers"]
    leaves = [l["path"] for l in layers if not l.get("sublayers")][::-1]  # bottom to top
    manifest = {"doc": doc, "character_layer": char["layer"], "layers": []}
    for n, path in enumerate(leaves, 1):
        file = out / f"{n:02d}-{slug(path)}.png"
        jsx(JSX_SHOW, {"doc": doc, "path": path.split("/")}, tmp)
        cli("--doc", doc, "doc", "export", str(file), "--overwrite")
        im = Image.open(file).convert("RGBA")
        manifest["size"] = list(im.size)
        manifest["layers"].append({"path": path, "file": file.name, "bbox": im.getchannel("A").getbbox()})
    jsx(JSX_SHOW, {"doc": doc, "path": []}, tmp)
    tmp.unlink(missing_ok=True)

    # ---- proof: the parts put back together must equal the untouched character
    ref = Image.open(out / "_reference.png").convert("RGBA")
    comp = Image.new("RGBA", ref.size, (0, 0, 0, 0))
    parts = [l for l in manifest["layers"] if l["path"].startswith(char["layer"] + "/")]
    for l in parts:
        comp.alpha_composite(Image.open(out / l["file"]).convert("RGBA"))
    diff = ImageChops.difference(premultiplied(ref), premultiplied(comp))
    worst = max(band.getextrema()[1] for band in diff.split())
    mask = Image.merge("RGB", diff.split()[:3]).convert("L").point(lambda v: 255 if v > 24 else 0)
    alpha_bad = diff.getchannel("A").point(lambda v: 255 if v > 24 else 0)
    bad = ImageChops.lighter(mask, alpha_bad)
    bad_pct = 100.0 * bad.histogram()[255] / (ref.size[0] * ref.size[1])
    empty = [l["path"] for l in manifest["layers"] if l["bbox"] is None]
    manifest["check"] = {"max_channel_diff": worst, "pixels_off_by_more_than_24_pct": round(bad_pct, 4), "empty_layers": empty}
    manifest["pass"] = bad_pct <= 0.05 and not empty
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # ---- contact sheet of the character parts
    cell = 420
    sheet = Image.new("RGB", (cell * len(parts), cell), (255, 0, 255))
    for i, l in enumerate(parts):
        tile = Image.new("RGBA", ref.size, (255, 0, 255, 255))
        tile.alpha_composite(Image.open(out / l["file"]).convert("RGBA"))
        sheet.paste(tile.convert("RGB").resize((cell, cell), Image.LANCZOS), (cell * i, 0))
    sheet.save(out / "_parts_sheet.png")

    print(json.dumps(manifest["check"], indent=2))
    print("layers, bottom to top:")
    for l in manifest["layers"]:
        print("  ", l["file"], "<-", l["path"], l["bbox"])
    print("PASS" if manifest["pass"] else "FAIL - parts do not rebuild the reference (check polygon overlaps)")
    return 0 if manifest["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
