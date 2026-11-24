"""Draw a vector illustration inside Adobe Illustrator from a spec file - no AI generation involved.
Claude writes the spec (paths, colours, gradients); Illustrator creates every path on its own layer.

    python ai_draw.py drawing.json                  draw / redraw the layers in the spec
    python ai_draw.py drawing.json --export dir     ...then export every leaf layer to dir + manifest.json
    python ai_draw.py drawing.json --preview p.png  ...then export the whole artboard to one PNG

Illustrator must be running with the document open; needs cli-anything-illustrator on PATH.

Spec (coordinates are artboard px, origin top-left, y down):
{
  "doc": "name.ai",
  "layers": [                                drawn in this order; a new layer goes above its siblings
    {"layer": "Cat/Head",                    'Parent/Sub' path, created when missing
     "clear": true,                          delete what the layer holds first
     "transform": {"scale": 1, "rotate": -14, "translate": [1095, 960]},
                                             items are in local coords: scale, rotate (clockwise +), move
     "clip": "M ... Z",                      optional silhouette; every item is clipped to it
     "outline": {"stroke": "#4a1d07", "width": 5},      optional: stroke the silhouette on top
     "items": [                              bottom to top; one sub-path per item
       {"name": "Base", "d": "M 0 0 C 10 0 20 10 20 20 L 0 20 Z", "fill": "#f08a24"},
       {"name": "Glow", "d": "...", "fill": {"type": "radial", "stops": [["#ffffff", 0, 80], ["#ffffff", 100, 0]]},
        "blend": "screen", "opacity": 70, "blur": 12},
       {"name": "Line", "d": "M 0 0 Q 50 -20 100 0", "fill": null, "stroke": "#ffffff", "stroke_width": 4}
     ]}
  ]
}
Path data: SVG commands M L H V C S Q Z (upper = absolute, lower = relative).
Gradient: {"type": "linear"|"radial", "angle": degrees, "stops": [[hex, position 0-100, opacity 0-100], ...]}.
  Linear angle: 0 = left to right, 90 = bottom to top, -90 = top to bottom.
Blend: normal, multiply, screen, overlay, softlight. Blur: Gaussian blur radius in px (live effect).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

from PIL import Image

from split_parts import JSX_SHOW, cli, jsx, slug

JSX_DRAW = """
(function () {
  __HEAD__
  var log = [];
  function rgb(hex) {
    var c = new RGBColor();
    c.red = parseInt(hex.substr(1, 2), 16); c.green = parseInt(hex.substr(3, 2), 16); c.blue = parseInt(hex.substr(5, 2), 16);
    return c;
  }
  function findLayer(path) {
    var names = path.split('/'), coll = doc.layers, lay = null;
    for (var i = 0; i < names.length; i++) {
      var hit = null;
      for (var k = 0; k < coll.length; k++) if (coll[k].name == names[i]) { hit = coll[k]; break; }
      if (!hit) { hit = coll.add(); hit.name = names[i]; }
      lay = hit; coll = lay.layers;
    }
    return lay;
  }
  function mkPath(container, sub, name) {
    var p = container.pathItems.add();
    for (var i = 0; i < sub.pts.length; i++) {
      var q = sub.pts[i], pp = p.pathPoints.add();
      pp.anchor = pt(q.a); pp.leftDirection = pt(q.l); pp.rightDirection = pt(q.r);
      pp.pointType = PointType.CORNER;
    }
    p.closed = sub.closed; p.name = name;
    return p;
  }
  function gradient(spec, p) {
    var g = doc.gradients.add();
    g.type = spec.type == 'radial' ? GradientType.RADIAL : GradientType.LINEAR;
    while (g.gradientStops.length < spec.stops.length) g.gradientStops.add();
    for (var i = 0; i < spec.stops.length; i++) {
      var s = g.gradientStops[i];
      s.rampPoint = spec.stops[i][1]; s.midPoint = 50; s.color = rgb(spec.stops[i][0]);
      s.opacity = spec.stops[i].length > 2 ? spec.stops[i][2] : 100;
    }
    var gc = new GradientColor(); gc.gradient = g;
    p.fillColor = gc;
    if (spec.type != 'radial' && spec.angle) p.rotate(spec.angle, false, false, true, false, Transformation.CENTER);
  }
  var BLEND = {multiply: BlendModes.MULTIPLY, screen: BlendModes.SCREEN, overlay: BlendModes.OVERLAY,
               softlight: BlendModes.SOFTLIGHT, normal: BlendModes.NORMAL};
  function paint(p, it) {
    if (it.fill && typeof it.fill == 'object') { p.filled = true; gradient(it.fill, p); }
    else if (it.fill) { p.filled = true; p.fillColor = rgb(it.fill); }
    else p.filled = false;
    if (it.stroke) {
      p.stroked = true; p.strokeColor = rgb(it.stroke); p.strokeWidth = it.stroke_width || 1;
      p.strokeCap = it.cap == 'butt' ? StrokeCap.BUTTENDCAP : StrokeCap.ROUNDENDCAP; p.strokeJoin = StrokeJoin.ROUNDENDJOIN;
    } else p.stroked = false;
    if (it.opacity != null) p.opacity = it.opacity;
    if (it.blend && BLEND[it.blend]) p.blendingMode = BLEND[it.blend];
    if (it.blur) {
      try { p.applyEffect('<LiveEffect name="Adobe PSL Gaussian Blur"><Dict data="R blur ' + it.blur + '"/></LiveEffect>'); }
      catch (e) { log.push('blur failed on ' + it.name); }
    }
  }
  for (var n = 0; n < cfg.layers.length; n++) {
    var spec = cfg.layers[n], lay = findLayer(spec.layer);
    lay.visible = true; lay.locked = false;
    if (spec.clear) { for (var r = lay.pageItems.length - 1; r >= 0; r--) { try { lay.pageItems[r].remove(); } catch (e) {} } }
    var target = lay;
    if (spec.clip) { target = lay.groupItems.add(); target.name = spec.leaf + ' art'; }
    for (var i = 0; i < spec.items.length; i++) paint(mkPath(target, spec.items[i].sub, spec.items[i].name), spec.items[i]);
    if (spec.clip) {
      var c = mkPath(target, spec.clip, spec.leaf + ' clip'); c.filled = false; c.stroked = false;
      c.move(target, ElementPlacement.PLACEATBEGINNING); c.clipping = true; target.clipped = true;
      if (spec.outline) {
        var o = mkPath(lay, spec.clip, spec.leaf + ' outline');
        o.filled = false; o.stroked = true; o.strokeColor = rgb(spec.outline.stroke); o.strokeWidth = spec.outline.width;
        o.strokeJoin = StrokeJoin.ROUNDENDJOIN;
      }
    }
    log.push(spec.layer + ':' + spec.items.length);
  }
  return log.join(' ');
})();
"""

TOKEN = re.compile(r"[MLHVCSQZmlhvcsqz]|-?\d*\.?\d+(?:[eE]-?\d+)?")


def parse_path(d: str) -> dict:
    """SVG path data -> {'closed': bool, 'pts': [{'a','l','r'}]} for the first sub-path."""
    toks = TOKEN.findall(d)
    pts: list[dict] = []
    closed, i, cmd = False, 0, ""
    cur, prev_c2 = (0.0, 0.0), None

    def num() -> float:
        nonlocal i
        i += 1
        return float(toks[i - 1])

    while i < len(toks):
        if toks[i].isalpha():
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                closed = True
                break
        rel, c = cmd.islower(), cmd.upper()
        ox, oy = cur if rel else (0.0, 0.0)
        if c == "M":
            if pts:
                raise ValueError("one sub-path per item: " + d[:60])
            cur = (ox + num(), oy + num())
            pts.append({"a": cur, "l": cur, "r": cur})
            cmd, prev_c2 = ("l" if rel else "L"), None
        elif c in "LHV":
            x = ox + num() if c in "LH" else cur[0]
            y = oy + num() if c in "LV" else cur[1]
            cur = (x, y)
            pts.append({"a": cur, "l": cur, "r": cur})
            prev_c2 = None
        elif c in "CS":
            if c == "C":
                c1 = (ox + num(), oy + num())
            else:
                c1 = (2 * cur[0] - prev_c2[0], 2 * cur[1] - prev_c2[1]) if prev_c2 else cur
            c2 = (ox + num(), oy + num())
            end = (ox + num(), oy + num())
            pts[-1]["r"] = c1
            pts.append({"a": end, "l": c2, "r": end})
            cur, prev_c2 = end, c2
        elif c == "Q":
            q = (ox + num(), oy + num())
            end = (ox + num(), oy + num())
            pts[-1]["r"] = (cur[0] + 2 / 3 * (q[0] - cur[0]), cur[1] + 2 / 3 * (q[1] - cur[1]))
            pts.append({"a": end, "l": (end[0] + 2 / 3 * (q[0] - end[0]), end[1] + 2 / 3 * (q[1] - end[1])), "r": end})
            cur, prev_c2 = end, None
        else:
            raise ValueError(f"unsupported path command {cmd!r}")
    if closed and len(pts) > 2 and math.dist(pts[0]["a"], pts[-1]["a"]) < 0.01:
        pts[0]["l"] = pts[-1]["l"]
        pts.pop()
    return {"closed": closed, "pts": pts}


def transformed(sub: dict, tf: dict | None) -> dict:
    if not tf:
        return sub
    k, a = tf.get("scale", 1.0), math.radians(tf.get("rotate", 0.0))
    tx, ty = tf.get("translate", [0.0, 0.0])
    ca, sa = math.cos(a), math.sin(a)

    def f(p):
        x, y = p[0] * k, p[1] * k
        return (tx + x * ca - y * sa, ty + x * sa + y * ca)

    return {"closed": sub["closed"], "pts": [{key: f(q[key]) for key in ("a", "l", "r")} for q in sub["pts"]]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--export", help="folder for one PNG per leaf layer + manifest.json")
    ap.add_argument("--preview", help="PNG of the whole artboard after drawing")
    ap.add_argument("--only", nargs="*", help="draw only these layer paths from the spec")
    a = ap.parse_args()
    spec_path = Path(a.spec).resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    doc = spec["doc"]
    layers = []
    for lay in spec["layers"]:
        if a.only and lay["layer"] not in a.only:
            continue
        tf = lay.get("transform")
        out = {"layer": lay["layer"], "leaf": lay["layer"].split("/")[-1], "clear": lay.get("clear", False),
               "outline": lay.get("outline"), "items": []}
        if lay.get("clip"):
            out["clip"] = transformed(parse_path(lay["clip"]), tf)
        for it in lay["items"]:
            item = {k: v for k, v in it.items() if k != "d"}
            item["sub"] = transformed(parse_path(it["d"]), tf)
            out["items"].append(item)
        layers.append(out)
    tmp = spec_path.parent / "_draw.jsx"
    print(jsx(JSX_DRAW, {"doc": doc, "layers": layers}, tmp))

    if a.preview:
        jsx(JSX_SHOW, {"doc": doc, "path": []}, tmp)
        cli("--doc", doc, "doc", "export", str(Path(a.preview).resolve()), "--opaque", "--overwrite")
    if a.export:
        out_dir = Path(a.export).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        leaves = [l["path"] for l in cli("--doc", doc, "layer", "list")["layers"] if not l.get("sublayers")][::-1]
        manifest = {"doc": doc, "layers": []}
        for n, path in enumerate(leaves, 1):
            file = out_dir / f"{n:02d}-{slug(path)}.png"
            jsx(JSX_SHOW, {"doc": doc, "path": path.split("/")}, tmp)
            cli("--doc", doc, "doc", "export", str(file), "--overwrite")
            im = Image.open(file).convert("RGBA")
            manifest["size"] = list(im.size)
            manifest["layers"].append({"path": path, "file": file.name, "bbox": im.getchannel("A").getbbox()})
        jsx(JSX_SHOW, {"doc": doc, "path": []}, tmp)
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        for l in manifest["layers"]:
            print("  ", l["file"], "<-", l["path"], l["bbox"])
    tmp.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
