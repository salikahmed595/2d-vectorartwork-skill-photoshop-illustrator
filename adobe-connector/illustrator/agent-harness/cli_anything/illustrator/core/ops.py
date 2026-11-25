"""Illustrator operations. Each function runs one JSX body inside the real Illustrator.

Coordinates are points relative to the active artboard's top-left corner, y DOWN (like SVG
and screens). They are converted to Illustrator's y-up scripting coordinates inside the JSX.
Bounds are returned as [left, top, right, bottom] in the same y-down space.
"""
from __future__ import annotations

import glob
import os
import uuid
from typing import Any

from cli_anything.illustrator.core.curves import parse_svg_path, points_to_subpath
from cli_anything.illustrator.utils.jsx_backend import AdobeError, JsxBackend, norm_path, parse_color

SETUP = (
    "var __cs=app.coordinateSystem,__ui=app.userInteractionLevel;"
    "app.coordinateSystem=CoordinateSystem.ARTBOARDCOORDINATESYSTEM;"
    "app.userInteractionLevel=UserInteractionLevel.DONTDISPLAYALERTS;"
)
TEARDOWN = "app.coordinateSystem=__cs;app.userInteractionLevel=__ui;"

LIB = r"""
function __doc(){if(ARGS.doc){for(var i=0;i<app.documents.length;i++){if(app.documents[i].name==ARGS.doc){app.activeDocument=app.documents[i];return app.documents[i];}}__fail('No open document named '+ARGS.doc);}
if(!app.documents.length){__fail('No document is open. Use doc new or doc open first.');}return app.activeDocument;}
function __g(p,k,d){return (p&&p[k]!==undefined&&p[k]!==null)?p[k]:d;}
function __Y(y){return -y;}
function __r2(v){return Math.round(v*100)/100;}
function __rgb(c){var r=new RGBColor();r.red=c[0];r.green=c[1];r.blue=c[2];return r;}
function __hex(c){if(!c){return null;}if(c.typename=='RGBColor'){var s='#';var v=[c.red,c.green,c.blue];for(var i=0;i<3;i++){var h=Math.round(v[i]).toString(16);s+=(h.length<2?'0':'')+h;}return s;}if(c.typename=='NoColor'){return 'none';}if(c.typename=='GradientColor'){return 'gradient';}return c.typename;}
function __walkL(c,pre,out){for(var i=0;i<c.layers.length;i++){var L=c.layers[i];var p=pre?pre+'/'+L.name:L.name;out.push({L:L,path:p});__walkL(L,p,out);}return out;}
function __layer(d,name){var a=__walkL(d,'',[]);for(var i=0;i<a.length;i++){if(a[i].path==name){return a[i].L;}}for(var j=0;j<a.length;j++){if(a[j].L.name==name){return a[j].L;}}__fail('No layer named '+name);}
function __tlayer(d){if(ARGS.layer){var L=__layer(d,ARGS.layer);}else{var L=d.activeLayer;}if(L.locked){__fail('Layer '+L.name+' is locked');}if(!L.visible){__fail('Layer '+L.name+' is hidden; show it or pass another layer');}return L;}
function __linfo(L,p){return {name:L.name,path:p||L.name,visible:L.visible,locked:L.locked,opacity:__r2(L.opacity),items:L.pageItems.length,sublayers:L.layers.length};}
function __bounds(it){var b=it.geometricBounds;return [__r2(b[0]),__r2(-b[1]),__r2(b[2]),__r2(-b[3])];}
function __iinfo(it){var o={name:it.name,type:it.typename,layer:it.layer.name,bounds:__bounds(it),hidden:it.hidden,opacity:__r2(it.opacity)};
if(it.typename=='PathItem'){o.fill=it.filled?__hex(it.fillColor):'none';o.stroke=it.stroked?__hex(it.strokeColor):'none';if(it.stroked){o.strokeWidth=it.strokeWidth;}o.closed=it.closed;o.points=it.pathPoints.length;}
if(it.typename=='TextFrame'){o.text=it.contents;try{var a=it.textRange.characterAttributes;o.size=a.size;o.font=a.textFont.name;o.fill=__hex(a.fillColor);}catch(e){}}
if(it.typename=='GroupItem'){o.children=it.pageItems.length;}
if(it.typename=='CompoundPathItem'&&it.pathItems.length){var q=it.pathItems[0];o.fill=q.filled?__hex(q.fillColor):'none';o.paths=it.pathItems.length;}return o;}
function __item(d,name){for(var i=0;i<d.pageItems.length;i++){if(d.pageItems[i].name==name){return d.pageItems[i];}}__fail('No item named '+name+' (name items with --name when creating them)');}
function __paint(it){if(it.typename=='TextFrame'){var a=it.textRange.characterAttributes;if(ARGS.fill!==undefined){a.fillColor=(ARGS.fill=='none')?new NoColor():__rgb(ARGS.fill);}if(ARGS.stroke!==undefined){a.strokeColor=(ARGS.stroke=='none')?new NoColor():__rgb(ARGS.stroke);}if(ARGS.strokeWidth!==undefined){a.strokeWeight=ARGS.strokeWidth;}return;}
if(it.typename=='GroupItem'||it.typename=='CompoundPathItem'){var ps=it.pathItems;for(var i=0;i<ps.length;i++){__paint(ps[i]);}return;}
if(it.typename!='PathItem'){if(ARGS.fill!==undefined||ARGS.stroke!==undefined){__fail('Cannot colour a '+it.typename);}return;}
if(ARGS.fill!==undefined){if(ARGS.fill=='none'){it.filled=false;}else{it.filled=true;it.fillColor=__rgb(ARGS.fill);}}
if(ARGS.stroke!==undefined){if(ARGS.stroke=='none'){it.stroked=false;}else{it.stroked=true;it.strokeColor=__rgb(ARGS.stroke);}}
if(ARGS.strokeWidth!==undefined){it.strokeWidth=ARGS.strokeWidth;}}
function __dinfo(d){var p=null;try{if(d.path&&String(d.path)!=''){p=d.fullName.fsName;}}catch(e){}var ab=[];for(var i=0;i<d.artboards.length;i++){var r=d.artboards[i].artboardRect;ab.push({name:d.artboards[i].name,width:__r2(r[2]-r[0]),height:__r2(r[1]-r[3])});}
return {name:d.name,path:p,width:__r2(d.width),height:__r2(d.height),colorSpace:String(d.documentColorSpace).replace('DocumentColorSpace.','').toLowerCase(),artboards:ab,layers:d.layers.length,items:d.pageItems.length,saved:d.saved};}
"""

_backend: JsxBackend | None = None


def backend() -> JsxBackend:
    global _backend
    if _backend is None:
        # Pinned to Illustrator 2022 (v26), the version the studio uses: no other version is ever launched (2027 asks for a licence key).
        _backend = JsxBackend(PROGID, "Adobe Illustrator", SETUP, TEARDOWN, required_major=REQUIRED_MAJOR, version_label="2022")
    return _backend


PROGID = "Illustrator.Application.26"
REQUIRED_MAJOR = 26


def app_check() -> dict:
    """Is Illustrator 2022 installed and registered? Reads the registry only; starts nothing."""
    status = backend().check()
    if not status["ok"]:
        raise AdobeError(status["message"])
    return status


def _run(body: str, **args: Any) -> Any:
    return backend().run(LIB + body, {k: v for k, v in args.items() if v is not None})


def _paint(value: str | None):
    """None -> leave unchanged; 'none' -> remove paint; hex -> [r,g,b]."""
    if value is None:
        return None
    if str(value).strip().lower() in ("none", "transparent"):
        return "none"
    return parse_color(value)


def _pos(name: str, value: float) -> float:
    if value is None or value <= 0:
        raise AdobeError(f"{name} must be a positive number, got {value!r}")
    return value


# ---------------------------------------------------------------- app / documents
def app_info() -> dict:
    return _run("var n=[];for(var i=0;i<app.documents.length;i++){n.push(app.documents[i].name);}"
                "return {app:app.name,version:app.version,documents:n,active:app.documents.length?app.activeDocument.name:null};")


def doc_new(width: float = 612, height: float = 792, color_space: str = "rgb") -> dict:
    """New document with one artboard (points; 72 pt = 1 inch). Illustrator names it on first save."""
    if color_space not in ("rgb", "cmyk"):
        raise AdobeError("color_space must be rgb or cmyk")
    return _run("var d=app.documents.add(ARGS.cs=='cmyk'?DocumentColorSpace.CMYK:DocumentColorSpace.RGB,ARGS.width,ARGS.height);return __dinfo(d);",
                width=_pos("width", width), height=_pos("height", height), cs=color_space)


def doc_open(path: str) -> dict:
    return _run("return __dinfo(app.open(new File(ARGS.path)));", path=norm_path(path, must_exist=True))


def doc_info(doc: str | None = None) -> dict:
    return _run("return __dinfo(__doc());", doc=doc)


def doc_list() -> list:
    return _run("var o=[];for(var i=0;i<app.documents.length;i++){o.push(__dinfo(app.documents[i]));}return o;")


def doc_save(path: str, doc: str | None = None, overwrite: bool = False) -> dict:
    """Save as editable .ai, or .pdf (keeps Illustrator editing capabilities)."""
    p = norm_path(path, overwrite=overwrite)
    ext = os.path.splitext(p)[1].lower()
    if ext not in (".ai", ".pdf"):
        raise AdobeError("doc save writes .ai or .pdf (use doc export for png/jpg/svg)")
    return _run("var d=__doc();var o;if(ARGS.ext=='.pdf'){o=new PDFSaveOptions();o.preserveEditability=true;}else{o=new IllustratorSaveOptions();o.pdfCompatible=true;}"
                "d.saveAs(new File(ARGS.path),o);return __dinfo(d);", path=p, ext=ext, doc=doc)


def doc_export(path: str, fmt: str | None = None, scale: float = 1.0, transparent: bool = True,
               quality: int = 90, doc: str | None = None, overwrite: bool = False) -> dict:
    """Export the active artboard to png/jpg/svg. scale 2 = 2x pixels for png/jpg."""
    p = norm_path(path, overwrite=overwrite)
    fmt = (fmt or os.path.splitext(p)[1].lstrip(".")).lower().replace("jpeg", "jpg")
    if fmt not in ("png", "jpg", "svg"):
        raise AdobeError("export format must be png, jpg or svg")
    if not 0 < scale <= 10:
        raise AdobeError("scale must be between 0 and 10")
    before = time_of(p)
    res = _run("var d=__doc();var f=new File(ARGS.path);var o;"
               "if(ARGS.fmt=='png'){o=new ExportOptionsPNG24();o.artBoardClipping=true;o.antiAliasing=true;o.transparency=ARGS.transparent;"
               "o.horizontalScale=ARGS.scale*100;o.verticalScale=ARGS.scale*100;d.exportFile(f,ExportType.PNG24,o);}"
               "else if(ARGS.fmt=='jpg'){o=new ExportOptionsJPEG();o.artBoardClipping=true;o.antiAliasing=true;o.qualitySetting=ARGS.quality;"
               "o.horizontalScale=ARGS.scale*100;o.verticalScale=ARGS.scale*100;d.exportFile(f,ExportType.JPEG,o);}"
               "else{o=new ExportOptionsSVG();o.embedRasterImages=true;o.fontType=SVGFontType.SVGFONT;d.exportFile(f,ExportType.SVG,o);}"
               "return {path:f.fsName,format:ARGS.fmt};",
               path=p, fmt=fmt, scale=float(scale), transparent=bool(transparent), quality=int(quality), doc=doc)
    out = os.path.normpath(res["path"])
    if not os.path.exists(out) or time_of(out) == before:
        # Illustrator sometimes appends an artboard suffix; find the file it really wrote.
        stem, ext = os.path.splitext(out)
        found = [f for f in glob.glob(glob.escape(stem) + "*" + ext) if time_of(f) != before]
        if not found:
            raise AdobeError(f"Illustrator reported success but no file was written: {out}")
        out = max(found, key=os.path.getmtime)
    res["path"] = out
    res["bytes"] = os.path.getsize(out)
    return res


def time_of(path: str) -> float | None:
    return os.path.getmtime(path) if os.path.exists(path) else None


def doc_close(save: bool = False, doc: str | None = None) -> dict:
    return _run("var d=__doc();var n=d.name;d.close(ARGS.save?SaveOptions.SAVECHANGES:SaveOptions.DONOTSAVECHANGES);return {closed:n};",
                save=bool(save), doc=doc)


def doc_undo(steps: int = 1, doc: str | None = None) -> dict:
    if steps < 1:
        raise AdobeError("steps must be 1 or more")
    return _run("__doc();for(var i=0;i<ARGS.steps;i++){app.undo();}return {undone:ARGS.steps};", steps=int(steps), doc=doc)


# ---------------------------------------------------------------- layers
def layer_list(doc: str | None = None) -> dict:
    return _run("var d=__doc();var a=__walkL(d,'',[]);var o=[];for(var i=0;i<a.length;i++){o.push(__linfo(a[i].L,a[i].path));}"
                "return {document:d.name,active:d.activeLayer.name,layers:o};", doc=doc)


def layer_add(name: str, parent: str | None = None, doc: str | None = None) -> dict:
    return _run("var d=__doc();var P=ARGS.parent?__layer(d,ARGS.parent):d;var L=P.layers.add();L.name=ARGS.name;d.activeLayer=L;return __linfo(L);",
                name=name, parent=parent, doc=doc)


def layer_rename(layer: str, name: str, doc: str | None = None) -> dict:
    return _run("var d=__doc();var L=__layer(d,ARGS.layer);L.name=ARGS.name;return __linfo(L);", layer=layer, name=name, doc=doc)


def layer_delete(layer: str, doc: str | None = None) -> dict:
    return _run("var d=__doc();if(d.layers.length<2){__fail('A document needs at least one layer');}var L=__layer(d,ARGS.layer);var n=L.name;L.remove();return {deleted:n};",
                layer=layer, doc=doc)


def layer_set(layer: str, visible: bool | None = None, locked: bool | None = None, opacity: float | None = None,
              doc: str | None = None) -> dict:
    if opacity is not None and not 0 <= opacity <= 100:
        raise AdobeError("opacity must be 0-100")
    return _run("var d=__doc();var L=__layer(d,ARGS.layer);if(ARGS.visible!==undefined){L.visible=ARGS.visible;}"
                "if(ARGS.locked!==undefined){L.locked=ARGS.locked;}if(ARGS.opacity!==undefined){L.opacity=ARGS.opacity;}return __linfo(L);",
                layer=layer, visible=visible, locked=locked, opacity=opacity, doc=doc)


def layer_select(layer: str, doc: str | None = None) -> dict:
    """Make a layer active (new items go there by default)."""
    return _run("var d=__doc();var L=__layer(d,ARGS.layer);d.activeLayer=L;return __linfo(L);", layer=layer, doc=doc)


_Z = {"front": "BRINGTOFRONT", "back": "SENDTOBACK", "forward": "BRINGFORWARD", "backward": "SENDBACKWARD"}


def layer_arrange(layer: str, to: str, doc: str | None = None) -> dict:
    if to not in _Z:
        raise AdobeError("to must be front, back, forward or backward")
    return _run("var d=__doc();var L=__layer(d,ARGS.layer);L.zOrder(ZOrderMethod[ARGS.z]);return __linfo(L);",
                layer=layer, z=_Z[to], doc=doc)


# ---------------------------------------------------------------- drawing
SHAPES = ("rect", "rounded-rect", "ellipse", "polygon", "star", "line")


def shape(kind: str, x: float, y: float, w: float, h: float, fill: str | None = "#000000", stroke: str | None = None,
          stroke_width: float | None = None, radius: float = 12, sides: int = 6, points: int = 5,
          inner_ratio: float = 0.5, name: str | None = None, layer: str | None = None, doc: str | None = None) -> dict:
    """Draw a shape in the box (x, y, w, h). polygon/star fit the box; line goes from (x,y) to (x+w,y+h)."""
    if kind not in SHAPES:
        raise AdobeError(f"kind must be one of {', '.join(SHAPES)}")
    if kind != "line":
        _pos("w", w), _pos("h", h)
    if kind == "polygon" and sides < 3:
        raise AdobeError("polygon needs 3 or more sides")
    if kind == "star" and (points < 3 or not 0 < inner_ratio < 1):
        raise AdobeError("star needs points >= 3 and 0 < inner_ratio < 1")
    if kind == "line" and fill == "#000000":
        fill, stroke = "none", stroke or "#000000"
    if stroke is None:
        stroke = "none"  # don't inherit Illustrator's default 1pt black stroke
    return _run("var d=__doc();var L=__tlayer(d);var P=L.pathItems;var x=ARGS.x,y=ARGS.y,w=ARGS.w,h=ARGS.h,k=ARGS.kind,it;"
                "var cx=x+w/2,cy=__Y(y+h/2),r=Math.min(Math.abs(w),Math.abs(h))/2;"
                "if(k=='rect'){it=P.rectangle(__Y(y),x,w,h);}"
                "else if(k=='rounded-rect'){it=P.roundedRectangle(__Y(y),x,w,h,ARGS.radius,ARGS.radius);}"
                "else if(k=='ellipse'){it=P.ellipse(__Y(y),x,w,h);}"
                "else if(k=='polygon'){it=P.polygon(cx,cy,r,ARGS.sides);}"
                "else if(k=='star'){it=P.star(cx,cy,r,r*ARGS.inner,ARGS.points);}"
                "else{it=P.add();it.setEntirePath([[x,__Y(y)],[x+w,__Y(y+h)]]);it.filled=false;}"
                "__paint(it);if(ARGS.name){it.name=ARGS.name;}return __iinfo(it);",
                kind=kind, x=x, y=y, w=w, h=h, fill=_paint(fill), stroke=_paint(stroke), strokeWidth=stroke_width,
                radius=radius, sides=int(sides), points=int(points), inner=inner_ratio, name=name, layer=layer, doc=doc)


# Draws subpaths of Bezier anchors [x, y, inX, inY, outX, outY, smooth] (from core/curves.py).
# Several subpaths become one compound path, so inner shapes can cut holes.
_DRAW_SUBPATHS = (
    "var d=__doc();var L=__tlayer(d);var S=ARGS.subs,it=null,host=L.pathItems;"
    "if(S.length>1){it=L.compoundPathItems.add();host=it.pathItems;}"
    "for(var s=0;s<S.length;s++){var p=host.add();var A=S[s].a;"
    "for(var i=0;i<A.length;i++){var a=A[i];var q=p.pathPoints.add();q.anchor=[a[0],__Y(a[1])];"
    "q.leftDirection=[a[2],__Y(a[3])];q.rightDirection=[a[4],__Y(a[5])];q.pointType=a[6]?PointType.SMOOTH:PointType.CORNER;}"
    "p.closed=S[s].c;p.filled=false;p.stroked=false;if(S.length>1){p.evenodd=ARGS.evenodd;}if(!it){it=p;}}"
    "__paint(it);if(ARGS.name){it.name=ARGS.name;}return __iinfo(it);"
)


def path_draw(points: list[list[float] | dict[str, Any]], closed: bool = False, smooth: bool = False,
              fill: str | None = "none", stroke: str | None = "#000000", stroke_width: float | None = 1,
              name: str | None = None, layer: str | None = None, doc: str | None = None) -> dict:
    """Draw a path through points (at least 2). A point is [x, y], or {"x", "y", "in": [x, y], "out": [x, y],
    "corner": true} with its own Bezier handles ("in" towards the previous point, "out" towards the next).
    smooth=true curves smoothly through every point that has no handles of its own; "corner": true keeps a point
    sharp (e.g. a flame tip). Without smooth or handles, segments are straight."""
    sub = points_to_subpath(points, closed=closed, smooth=smooth)
    return _run(_DRAW_SUBPATHS, subs=[sub], evenodd=True, fill=_paint(fill), stroke=_paint(stroke),
                strokeWidth=stroke_width, name=name, layer=layer, doc=doc)


def path_svg(d: str, fill: str | None = "#000000", stroke: str | None = "none", stroke_width: float | None = None,
             fill_rule: str = "evenodd", name: str | None = None, layer: str | None = None,
             doc: str | None = None) -> dict:
    """Draw SVG path data as one editable Illustrator path with real Bezier curves: M L H V C S Q T A Z, absolute or
    relative, in artboard points (y down, like SVG). Several M parts make one compound path; with
    fill_rule 'evenodd' (default) an inner part cuts a hole, 'nonzero' follows path direction like SVG's default."""
    if fill_rule not in ("evenodd", "nonzero"):
        raise AdobeError("fill_rule must be 'evenodd' or 'nonzero'")
    subs = parse_svg_path(d)
    return _run(_DRAW_SUBPATHS, subs=subs, evenodd=fill_rule == "evenodd", fill=_paint(fill), stroke=_paint(stroke),
                strokeWidth=stroke_width, name=name, layer=layer, doc=doc)


def text_add(text: str, x: float, y: float, size: float = 24, color: str = "#000000", font: str | None = None,
             name: str | None = None, layer: str | None = None, doc: str | None = None) -> dict:
    """Point text whose bounding box top-left is at (x, y). font = PostScript name (e.g. ArialMT)."""
    return _run("var d=__doc();var L=__tlayer(d);var t=L.textFrames.add();t.contents=ARGS.text;var a=t.textRange.characterAttributes;"
                "a.size=ARGS.size;if(ARGS.fill&&ARGS.fill!='none'){a.fillColor=__rgb(ARGS.fill);}"
                "if(ARGS.font){try{a.textFont=app.textFonts.getByName(ARGS.font);}catch(e){__fail('Font not found: '+ARGS.font);}}"
                "t.position=[ARGS.x,__Y(ARGS.y)];if(ARGS.name){t.name=ARGS.name;}return __iinfo(t);",
                text=text, x=x, y=y, size=_pos("size", size), fill=_paint(color), font=font, name=name, layer=layer, doc=doc)


def text_edit(item: str, text: str | None = None, size: float | None = None, color: str | None = None,
              font: str | None = None, doc: str | None = None) -> dict:
    return _run("var d=__doc();var t=__item(d,ARGS.item);if(t.typename!='TextFrame'){__fail(ARGS.item+' is not text');}"
                "if(ARGS.text!==undefined){t.contents=ARGS.text;}var a=t.textRange.characterAttributes;if(ARGS.size){a.size=ARGS.size;}"
                "if(ARGS.fill){a.fillColor=(ARGS.fill=='none')?new NoColor():__rgb(ARGS.fill);}"
                "if(ARGS.font){try{a.textFont=app.textFonts.getByName(ARGS.font);}catch(e){__fail('Font not found: '+ARGS.font);}}return __iinfo(t);",
                item=item, text=text, size=size, fill=_paint(color), font=font, doc=doc)


# ---------------------------------------------------------------- items
def item_list(layer: str | None = None, doc: str | None = None) -> dict:
    """Top-level items of every layer (or one layer), front to back."""
    return _run("var d=__doc();var a=ARGS.layer?[{L:__layer(d,ARGS.layer),path:ARGS.layer}]:__walkL(d,'',[]);var o=[];"
                "for(var i=0;i<a.length;i++){var it=a[i].L.pageItems;for(var j=0;j<it.length;j++){var n=__iinfo(it[j]);n.layer=a[i].path;o.push(n);}}"
                "return {document:d.name,count:o.length,items:o};", layer=layer, doc=doc)


def item_set(item: str, fill: str | None = None, stroke: str | None = None, stroke_width: float | None = None,
             opacity: float | None = None, hidden: bool | None = None, rename: str | None = None,
             x: float | None = None, y: float | None = None, dx: float | None = None, dy: float | None = None,
             rotate: float | None = None, scale: float | None = None, width: float | None = None,
             height: float | None = None, doc: str | None = None) -> dict:
    """Change paint, opacity, visibility, name, position (x,y = new top-left, or dx,dy), rotation (deg, counter-clockwise), scale or size."""
    if opacity is not None and not 0 <= opacity <= 100:
        raise AdobeError("opacity must be 0-100")
    if scale is not None and scale <= 0:
        raise AdobeError("scale must be positive")
    return _run("var d=__doc();var it=__item(d,ARGS.item);__paint(it);if(ARGS.opacity!==undefined){it.opacity=ARGS.opacity;}"
                "if(ARGS.hidden!==undefined){it.hidden=ARGS.hidden;}if(ARGS.rename){it.name=ARGS.rename;}"
                "if(ARGS.scale){it.resize(ARGS.scale*100,ARGS.scale*100);}if(ARGS.width){it.width=ARGS.width;}if(ARGS.height){it.height=ARGS.height;}"
                "if(ARGS.rotate){it.rotate(ARGS.rotate);}"
                "if(ARGS.x!==undefined||ARGS.y!==undefined){var b=it.geometricBounds;var nx=__g(ARGS,'x',b[0]),ny=(ARGS.y!==undefined)?__Y(ARGS.y):b[1];it.translate(nx-b[0],ny-b[1]);}"
                "if(ARGS.dx||ARGS.dy){it.translate(__g(ARGS,'dx',0),-__g(ARGS,'dy',0));}return __iinfo(it);",
                item=item, fill=_paint(fill), stroke=_paint(stroke), strokeWidth=stroke_width, opacity=opacity,
                hidden=hidden, rename=rename, x=x, y=y, dx=dx, dy=dy, rotate=rotate, scale=scale, width=width,
                height=height, doc=doc)


def item_delete(item: str, doc: str | None = None) -> dict:
    return _run("var d=__doc();var it=__item(d,ARGS.item);it.remove();return {deleted:ARGS.item};", item=item, doc=doc)


def item_duplicate(item: str, name: str | None = None, dx: float = 0, dy: float = 0, doc: str | None = None) -> dict:
    return _run("var d=__doc();var it=__item(d,ARGS.item).duplicate();it.translate(ARGS.dx,-ARGS.dy);if(ARGS.name){it.name=ARGS.name;}return __iinfo(it);",
                item=item, name=name, dx=dx, dy=dy, doc=doc)


def item_group(items: list[str], name: str | None = None, doc: str | None = None) -> dict:
    """Group the named items (they move to the first item's layer)."""
    if not items:
        raise AdobeError("Give at least one item to group")
    return _run("var d=__doc();var f=__item(d,ARGS.items[0]);var g=f.layer.groupItems.add();"
                "for(var i=ARGS.items.length-1;i>=0;i--){__item(d,ARGS.items[i]).move(g,ElementPlacement.PLACEATBEGINNING);}"
                "if(ARGS.name){g.name=ARGS.name;}return __iinfo(g);", items=list(items), name=name, doc=doc)


def item_arrange(item: str, to: str, doc: str | None = None) -> dict:
    if to not in _Z:
        raise AdobeError("to must be front, back, forward or backward")
    return _run("var d=__doc();var it=__item(d,ARGS.item);it.zOrder(ZOrderMethod[ARGS.z]);return __iinfo(it);",
                item=item, z=_Z[to], doc=doc)


def place(path: str, x: float = 0, y: float = 0, width: float | None = None, name: str | None = None,
          embed: bool = False, layer: str | None = None, doc: str | None = None) -> dict:
    """Place an image/vector file with its top-left at (x, y); width scales it proportionally.
    An SVG comes in as editable vector paths (a group), not a linked image."""
    return _run("var d=__doc();var L=__tlayer(d);var f=new File(ARGS.path);var p;"
                "if(ARGS.svg){p=L.groupItems.createFromFile(f);}else{p=L.placedItems.add();p.file=f;}"
                "if(ARGS.width){var r=p.height/p.width;p.width=ARGS.width;p.height=ARGS.width*r;}"
                "var b=p.geometricBounds;p.translate(ARGS.x-b[0],__Y(ARGS.y)-b[1]);if(ARGS.name){p.name=ARGS.name;}"
                "var info=__iinfo(p);if(ARGS.embed){p.embed();info.embedded=true;}return info;",
                path=norm_path(path, must_exist=True), x=x, y=y, width=width, name=name,
                embed=bool(embed) and not str(path).lower().endswith(".svg"), svg=str(path).lower().endswith(".svg"),
                layer=layer, doc=doc)


def trace_presets() -> list:
    """Image Trace preset names available in this Illustrator."""
    return _run("var o=[];var l=app.tracingPresetsList;for(var i=0;i<l.length;i++){o.push(l[i]);}return o;")


TRACE_MODES = {"color": "TRACINGMODECOLOR", "gray": "TRACINGMODEGRAY", "bw": "TRACINGMODEBLACKANDWHITE"}
TRACE_METHODS = {"abutting": "TRACINGMETHODABUTTING", "overlapping": "TRACINGMETHODOVERLAPPING"}


def _trace_opts(mode, colors, path_fidelity, corner_fidelity, noise, threshold, method, ignore_white, snap_lines) -> dict:
    o = {}
    if mode is not None:
        if mode not in TRACE_MODES:
            raise AdobeError("mode must be color, gray or bw")
        o["mode"] = TRACE_MODES[mode]
    if colors is not None:
        if not 2 <= int(colors) <= 30:
            raise AdobeError("colors must be 2-30")
        o["colors"] = int(colors)
    for key, val, lo, hi in (("pathFidelity", path_fidelity, 0, 100), ("cornerFidelity", corner_fidelity, 0, 100),
                             ("noiseFidelity", noise, 1, 100), ("threshold", threshold, 1, 255)):
        if val is not None:
            if not lo <= float(val) <= hi:
                raise AdobeError(f"{key} must be {lo}-{hi}")
            o[key] = float(val)
    if method is not None:
        if method not in TRACE_METHODS:
            raise AdobeError("method must be abutting or overlapping")
        o["method"] = TRACE_METHODS[method]
    if ignore_white is not None:
        o["ignoreWhite"] = bool(ignore_white)
    if snap_lines is not None:
        o["snapCurveToLines"] = bool(snap_lines)
    return o


def _wait_retrace(tag: str, opts: dict, doc: str | None, timeout: float = 30.0) -> None:
    import time
    want_colors = opts.get("colors") or (2 if opts.get("mode") == "TRACINGMODEBLACKANDWHITE" else None)
    last, same, start = None, 0, time.time()
    time.sleep(0.5)
    while time.time() - start < timeout:
        st = _run("app.redraw();var t=__doc().pageItems.getByName(ARGS.tag);"
                  "return [t.tracing.pathCount,t.tracing.usedColorCount];", tag=tag, doc=doc)
        if want_colors and 0 < st[1] <= want_colors:
            return
        same = same + 1 if st == last else 0
        if not want_colors and same >= 2 and st[0] > 0:
            return
        last = st
        time.sleep(0.5)


def trace(path: str, preset: str | None = None, x: float = 0, y: float = 0, width: float | None = None,
          expand: bool = True, name: str | None = None, layer: str | None = None,
          mode: str | None = None, colors: int | None = None, path_fidelity: float | None = None,
          corner_fidelity: float | None = None, noise: float | None = None, threshold: float | None = None,
          method: str | None = None, ignore_white: bool | None = None, snap_lines: bool | None = None,
          drop_background: bool = False, doc: str | None = None) -> dict:
    """Place a raster image and Image Trace it into vector paths (expand=true gives editable paths).
    Options override the preset: mode color|gray|bw, colors 2-30, path_fidelity/corner_fidelity 0-100,
    noise 1-100 (px; higher drops specks), threshold 1-255 (bw), method abutting|overlapping, ignore_white, snap_lines.
    drop_background=true deletes the shape(s) covering ~the whole image (the fill Image Trace makes for a
    transparent or flat background) while keeping light colours inside the subject."""
    opts = _trace_opts(mode, colors, path_fidelity, corner_fidelity, noise, threshold, method, ignore_white, snap_lines)
    tag = "__trace_" + uuid.uuid4().hex[:10]
    # Call 1: place, trace, set options. Illustrator only re-traces with new options between script calls,
    # and the colour limit only applies in a limited-palette state, so a limited preset is loaded first.
    _run("var d=__doc();var L=__tlayer(d);var p=L.placedItems.add();p.file=new File(ARGS.path);"
         "if(ARGS.width){var r=p.height/p.width;p.width=ARGS.width;p.height=ARGS.width*r;}"
         "var b=p.geometricBounds;p.translate(ARGS.x-b[0],__Y(ARGS.y)-b[1]);"
         "var t=p.trace();t.name=ARGS.tag;var o=t.tracing.tracingOptions;var Q=ARGS.opts;"
         "if(ARGS.preset){o.loadFromPreset(ARGS.preset);}else if(Q.colors){try{o.loadFromPreset('6 Colors');}catch(e){}}"
         "if(Q.mode){o.tracingMode=TracingModeType[Q.mode];}"
         "if(Q.colors){o.tracingColors=Q.colors;}"
         "var K=['pathFidelity','cornerFidelity','noiseFidelity','threshold','ignoreWhite','snapCurveToLines'];"
         "for(var i=0;i<K.length;i++){if(Q[K[i]]!==undefined){o[K[i]]=Q[K[i]];}}"
         "if(Q.method){o.tracingMethod=TracingMethodType[Q.method];}return 1;",
         path=norm_path(path, must_exist=True), preset=preset, x=x, y=y, width=width, opts=opts, tag=tag, layer=layer, doc=doc)
    # Illustrator re-traces asynchronously: poll until the result reflects the options (or is stable).
    if opts or preset:
        _wait_retrace(tag, opts, doc)
    # Call 2: expand and report.
    return _run("var d=__doc();app.redraw();var t=d.pageItems.getByName(ARGS.tag);var o=t.tracing.tracingOptions;"
                "var stats={paths:t.tracing.pathCount,colors:t.tracing.usedColorCount,mode:String(o.tracingMode).replace('TracingModeType.TRACINGMODE','').toLowerCase()};"
                "var out=t;if(ARGS.expand){out=t.tracing.expandTracing();}out.name=ARGS.name||'';var dropped=0;"
                "if(ARGS.drop&&out.typename=='GroupItem'){var G=out.geometricBounds,ga=(G[2]-G[0])*(G[1]-G[3]);"
                "for(var i=out.pageItems.length-1;i>=0;i--){var it=out.pageItems[i],B=it.geometricBounds;"
                "if((B[2]-B[0])*(B[1]-B[3])>=0.9*ga){it.remove();dropped++;}}}"
                "var info=__iinfo(out);stats.droppedBackground=dropped;info.trace=stats;if(out.typename=='GroupItem'){info.paths=out.pathItems.length;}return info;",
                tag=tag, expand=bool(expand), name=name, drop=bool(drop_background), doc=doc)


# ---------------------------------------------------------------- gradients
def _stops(stops: list | None) -> list:
    """['#a', '#b'] or [['#a', 0], ['#b', 100]] -> [[[r,g,b], pos], ...] sorted by position."""
    if not stops or len(stops) < 2:
        raise AdobeError("A gradient needs at least 2 colour stops")
    out = []
    for i, s in enumerate(stops):
        if isinstance(s, (list, tuple)):
            if len(s) != 2:
                raise AdobeError(f"Stop {i} must be ['#hex', position]")
            colour, pos = s
        else:
            colour, pos = s, round(100 * i / (len(stops) - 1), 2)
        rgb = parse_color(colour)
        if rgb is None or not 0 <= float(pos) <= 100:
            raise AdobeError(f"Stop {i}: need a hex colour and a position 0-100")
        out.append([rgb, float(pos)])
    return sorted(out, key=lambda s: s[1])


def item_gradient(item: str, stops: list, kind: str = "linear", angle: float = 0, doc: str | None = None) -> dict:
    """Fill a named item (path, group, compound path or text) with a gradient.
    stops = ['#hex', ...] (evenly spaced) or [['#hex', position 0-100], ...]; angle in degrees (linear)."""
    if kind not in ("linear", "radial"):
        raise AdobeError("kind must be linear or radial")
    return _run("var d=__doc();var it=__item(d,ARGS.item);var g=d.gradients.add();"
                "g.type=(ARGS.kind=='radial')?GradientType.RADIAL:GradientType.LINEAR;var S=ARGS.stops;"
                "while(g.gradientStops.length<S.length){g.gradientStops.add();}"
                "while(g.gradientStops.length>S.length){g.gradientStops[g.gradientStops.length-1].remove();}"
                "for(var i=0;i<S.length;i++){var st=g.gradientStops[i];st.rampPoint=S[i][1];st.midPoint=50;st.color=__rgb(S[i][0]);}"
                "var gc=new GradientColor();gc.gradient=g;"
                "function gf(x){if(x.typename=='TextFrame'){x.textRange.characterAttributes.fillColor=gc;return;}"
                "if(x.typename=='GroupItem'||x.typename=='CompoundPathItem'){for(var j=0;j<x.pathItems.length;j++){gf(x.pathItems[j]);}return;}"
                "if(x.typename!='PathItem'){__fail('Cannot fill a '+x.typename+' with a gradient');}"
                "x.filled=true;x.fillColor=gc;if(ARGS.angle){x.rotate(ARGS.angle,false,false,true,false,Transformation.CENTER);}}"
                "gf(it);var o=__iinfo(it);o.gradient={kind:ARGS.kind,stops:S.length,name:g.name};return o;",
                item=item, stops=_stops(stops), kind=kind, angle=float(angle), doc=doc)


# ---------------------------------------------------------------- symbols
def symbol_create(item: str, name: str, keep_original: bool = True, doc: str | None = None) -> dict:
    """Turn a named item into a reusable symbol called `name`."""
    return _run("var d=__doc();for(var i=0;i<d.symbols.length;i++){if(d.symbols[i].name==ARGS.name){__fail('A symbol named '+ARGS.name+' already exists');}}"
                "var it=__item(d,ARGS.item);var s=d.symbols.add(it);s.name=ARGS.name;if(!ARGS.keep){it.remove();}"
                "return {symbol:s.name,count:d.symbols.length};", item=item, name=name, keep=bool(keep_original), doc=doc)


def symbol_list(doc: str | None = None) -> list:
    """Symbols in the document."""
    return _run("var d=__doc();var o=[];for(var i=0;i<d.symbols.length;i++){o.push(d.symbols[i].name);}return o;", doc=doc)


def symbol_place(symbol: str, x: float = 0, y: float = 0, name: str | None = None, scale: float | None = None,
                 layer: str | None = None, doc: str | None = None) -> dict:
    """Place an instance of a symbol with its top-left at (x, y); scale 0.5 = half size."""
    if scale is not None and scale <= 0:
        raise AdobeError("scale must be positive")
    return _run("var d=__doc();var L=__tlayer(d);var S=null;for(var i=0;i<d.symbols.length;i++){if(d.symbols[i].name==ARGS.symbol){S=d.symbols[i];}}"
                "if(!S){__fail('No symbol named '+ARGS.symbol);}var si=L.symbolItems.add(S);if(ARGS.scale){si.resize(ARGS.scale*100,ARGS.scale*100);}"
                "var b=si.geometricBounds;si.translate(ARGS.x-b[0],__Y(ARGS.y)-b[1]);if(ARGS.name){si.name=ARGS.name;}return __iinfo(si);",
                symbol=symbol, x=x, y=y, name=name, scale=scale, layer=layer, doc=doc)


# ---------------------------------------------------------------- pathfinder
PATHFINDER = {"unite": "Live Pathfinder Add", "minus-front": "Live Pathfinder Subtract",
              "intersect": "Live Pathfinder Intersect", "exclude": "Live Pathfinder Exclude",
              "divide": "Live Pathfinder Divide"}


def pathfinder(op: str, items: list[str], name: str | None = None, doc: str | None = None) -> dict:
    """Combine named items with Pathfinder: unite, minus-front (top items cut the bottom one), intersect,
    exclude or divide. The originals are replaced by the expanded result (named `name`)."""
    if op not in PATHFINDER:
        raise AdobeError(f"op must be one of {', '.join(PATHFINDER)}")
    if not items or len(items) < 2:
        raise AdobeError("Pathfinder needs at least 2 items")
    return _run("var d=__doc();d.selection=null;var its=[];for(var i=0;i<ARGS.items.length;i++){var it=__item(d,ARGS.items[i]);"
                "if(it.locked||it.hidden||it.layer.locked||!it.layer.visible){__fail(ARGS.items[i]+' is locked or hidden');}its.push(it);}"
                "for(var j=0;j<its.length;j++){its[j].selected=true;}app.redraw();"  # menu commands need a redraw to see the selection
                "app.executeMenuCommand('group');app.redraw();app.executeMenuCommand(ARGS.cmd);app.redraw();"
                "app.executeMenuCommand('expandStyle');app.redraw();"
                "var sel=d.selection;if(!sel||!sel.length){__fail('Pathfinder produced nothing (do the shapes overlap?)');}"
                "var r=sel[0];if(r.typename=='GroupItem'&&r.pageItems.length==1){var c=r.pageItems[0];c.move(r,ElementPlacement.PLACEBEFORE);r.remove();r=c;}"
                "if(r.typename=='GroupItem'&&r.pageItems.length==0){__fail('Pathfinder produced nothing (do the shapes overlap?)');}"
                "if(ARGS.name){r.name=ARGS.name;}d.selection=null;var o=__iinfo(r);o.op=ARGS.op;return o;",
                items=list(items), cmd=PATHFINDER[op], op=op, name=name, doc=doc)


def action_play(action: str, action_set: str) -> dict:
    return _run("app.doScript(ARGS.action,ARGS.set);return {played:ARGS.action,set:ARGS.set};", action=action, set=action_set)


def script_run(code: str) -> Any:
    """Run arbitrary JSX in Illustrator (intentional escape hatch); the last expression's value is returned."""
    if not code or not code.strip():
        raise AdobeError("No script code given")
    return _run("var __v=eval(ARGS.code);return (__v===undefined)?null:__v;", code=code)
