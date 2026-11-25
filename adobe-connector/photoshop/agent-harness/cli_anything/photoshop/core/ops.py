"""Photoshop operations. Each function runs one JSX body inside the real Photoshop.

All coordinates and sizes are pixels; origin top-left, y down. Functions return plain
dicts/lists (JSON-ready) and raise AdobeError with a readable message on failure.
"""
from __future__ import annotations

import os
from typing import Any

from cli_anything.photoshop.utils.jsx_backend import AdobeError, JsxBackend, norm_path, parse_color

SETUP = (
    "var __ru=app.preferences.rulerUnits,__tu=app.preferences.typeUnits,__dd=app.displayDialogs;"
    "app.preferences.rulerUnits=Units.PIXELS;app.preferences.typeUnits=TypeUnits.PIXELS;"
    "app.displayDialogs=DialogModes.NO;"
)
TEARDOWN = "app.preferences.rulerUnits=__ru;app.preferences.typeUnits=__tu;app.displayDialogs=__dd;"

LIB = r"""
function __doc(){if(ARGS.doc){for(var i=0;i<app.documents.length;i++){if(app.documents[i].name==ARGS.doc){app.activeDocument=app.documents[i];return app.documents[i];}}__fail('No open document named '+ARGS.doc);}
if(!app.documents.length){__fail('No document is open. Use doc new or doc open first.');}return app.activeDocument;}
function __px(v){return (typeof v=='number')?v:v.as('px');}
function __g(p,k,d){return (p&&p[k]!==undefined&&p[k]!==null)?p[k]:d;}
function __color(rgb){var c=new SolidColor();c.rgb.red=rgb[0];c.rgb.green=rgb[1];c.rgb.blue=rgb[2];return c;}
function __walk(c,pre,out){for(var i=0;i<c.layers.length;i++){var L=c.layers[i];var p=pre?pre+'/'+L.name:L.name;out.push({L:L,path:p});if(L.typename=='LayerSet'){__walk(L,p,out);}}return out;}
function __layer(d,name){var a=__walk(d,'',[]);for(var i=0;i<a.length;i++){if(a[i].path==name){return a[i].L;}}for(var j=0;j<a.length;j++){if(a[j].L.name==name){return a[j].L;}}__fail('No layer named '+name);}
function __target(d){return ARGS.layer?__layer(d,ARGS.layer):d.activeLayer;}
function __linfo(L,path){var b=L.bounds;var o={name:L.name,path:path||L.name,visible:L.visible,
opacity:Math.round(L.opacity),blend:String(L.blendMode).replace('BlendMode.','').toLowerCase(),
bounds:[__px(b[0]),__px(b[1]),__px(b[2]),__px(b[3])]};
if(L.typename=='LayerSet'){o.type='group';o.children=L.layers.length;}else{o.type=String(L.kind).replace('LayerKind.','').toLowerCase();
o.isBackground=L.isBackgroundLayer;if(L.kind==LayerKind.TEXT){o.text=L.textItem.contents;}}return __lam(L,o);}
function __s(s){return stringIDToTypeID(s);}
function __c(s){return charIDToTypeID(s);}
function __amrgb(c){var x=new ActionDescriptor();x.putDouble(__s('red'),c[0]);x.putDouble(__s('grain'),c[1]);x.putDouble(__s('blue'),c[2]);return x;}
function __sel(d){if(ARGS.w===undefined){return false;}var x=ARGS.x,y=ARGS.y,w=ARGS.w,h=ARGS.h;
if(ARGS.shape!='ellipse'){d.selection.select([[x,y],[x+w,y],[x+w,y+h],[x,y+h]]);}
else{var D=new ActionDescriptor(),R=new ActionReference();R.putProperty(__c('Chnl'),__c('fsel'));D.putReference(__c('null'),R);
var E=new ActionDescriptor(),P=__c('#Pxl');E.putUnitDouble(__c('Top '),P,y);E.putUnitDouble(__c('Left'),P,x);E.putUnitDouble(__c('Btom'),P,y+h);E.putUnitDouble(__c('Rght'),P,x+w);
D.putObject(__c('T   '),__c('Elps'),E);D.putBoolean(__c('AntA'),true);executeAction(__c('setd'),D,DialogModes.NO);}
if(ARGS.feather){d.selection.feather(ARGS.feather);}return true;}
function __lam(L,o){try{var r=new ActionReference();r.putIdentifier(__c('Lyr '),L.id);var D=executeActionGet(r);
o.mask=D.hasKey(__s('hasUserMask'))?D.getBoolean(__s('hasUserMask')):false;o.styles=[];
if(D.hasKey(__s('layerEffects'))){var fx=D.getObjectValue(__s('layerEffects'));var seen={};for(var i=0;i<fx.count;i++){var key=fx.getKey(i);var k=typeIDToStringID(key);
var t=fx.getType(key);var on=false;
if(t==DescValueType.OBJECTTYPE){var e1=fx.getObjectValue(key);on=e1.hasKey(__s('enabled'))&&e1.getBoolean(__s('enabled'));}
else if(t==DescValueType.LISTTYPE){var lst=fx.getList(key);for(var j=0;j<lst.count;j++){var e2=lst.getObjectValue(j);if(e2.hasKey(__s('enabled'))&&e2.getBoolean(__s('enabled'))){on=true;}}}
k=k.replace('Multi','');if(on&&!seen[k]){seen[k]=1;o.styles.push(k);}}}}catch(e){}return o;}
function __desel(d){try{d.selection.deselect();}catch(e){}}
function __above(L,A){if(A&&L.id!=A.id){L.move(A,ElementPlacement.PLACEBEFORE);app.activeDocument.activeLayer=L;}}
function __dinfo(d){var p=null;try{p=d.fullName.fsName;}catch(e){}
return {name:d.name,path:p,width:__px(d.width),height:__px(d.height),resolution:d.resolution,
mode:String(d.mode).replace('DocumentMode.','').toLowerCase(),layers:__walk(d,'',[]).length,saved:d.saved};}
"""

_backend: JsxBackend | None = None


def backend() -> JsxBackend:
    global _backend
    if _backend is None:
        # Pinned to Photoshop 2023 (v24), the version installed here: no other version is ever launched (2027 asks for a licence key).
        _backend = JsxBackend(PROGID, "Adobe Photoshop", SETUP, TEARDOWN, required_major=REQUIRED_MAJOR, version_label="2023")
    return _backend


PROGID = "Photoshop.Application.170"
REQUIRED_MAJOR = 24


def app_check() -> dict:
    """Is Photoshop 2023 installed and registered? Reads the registry only; starts nothing."""
    status = backend().check()
    if not status["ok"]:
        raise AdobeError(status["message"])
    return status


def _run(body: str, **args: Any) -> Any:
    return backend().run(LIB + body, {k: v for k, v in args.items() if v is not None})


def _pos(name: str, value: float) -> float:
    if value is None or value <= 0:
        raise AdobeError(f"{name} must be a positive number, got {value!r}")
    return value


# ---------------------------------------------------------------- app / documents
def app_info() -> dict:
    return _run("var n=[];for(var i=0;i<app.documents.length;i++){n.push(app.documents[i].name);}"
                "return {app:app.name,version:app.version,documents:n,"
                "active:app.documents.length?app.activeDocument.name:null};")


def doc_new(width: int, height: int, resolution: float = 72, name: str = "Untitled",
            background: str = "white") -> dict:
    if background not in ("white", "transparent", "background"):
        raise AdobeError("background must be white, transparent or background")
    return _run("var f={white:DocumentFill.WHITE,transparent:DocumentFill.TRANSPARENT,background:DocumentFill.BACKGROUNDCOLOR}[ARGS.background];"
                "return __dinfo(app.documents.add(ARGS.width,ARGS.height,ARGS.resolution,ARGS.name,NewDocumentMode.RGB,f));",
                width=int(_pos("width", width)), height=int(_pos("height", height)),
                resolution=_pos("resolution", resolution), name=name, background=background)


def doc_open(path: str) -> dict:
    return _run("return __dinfo(app.open(new File(ARGS.path)));", path=norm_path(path, must_exist=True))


def doc_info(doc: str | None = None) -> dict:
    return _run("return __dinfo(__doc());", doc=doc)


def doc_list() -> list:
    return _run("var o=[];for(var i=0;i<app.documents.length;i++){o.push(__dinfo(app.documents[i]));}return o;")


def doc_save(path: str, doc: str | None = None, overwrite: bool = False) -> dict:
    p = norm_path(path, overwrite=overwrite)
    if not p.lower().endswith((".psd", ".psb")):
        raise AdobeError("doc save writes Photoshop files: use a .psd path (use doc export for png/jpg)")
    return _run("var d=__doc();var o=new PhotoshopSaveOptions();o.layers=true;o.embedColorProfile=true;"
                "d.saveAs(new File(ARGS.path),o,false,Extension.LOWERCASE);return __dinfo(d);", path=p, doc=doc)


def doc_export(path: str, fmt: str | None = None, quality: int = 10, doc: str | None = None,
               overwrite: bool = False) -> dict:
    p = norm_path(path, overwrite=overwrite)
    fmt = (fmt or os.path.splitext(p)[1].lstrip(".")).lower().replace("jpeg", "jpg").replace("tiff", "tif")
    if fmt not in ("png", "jpg", "tif"):
        raise AdobeError("export format must be png, jpg or tif")
    if not 0 <= int(quality) <= 12:
        raise AdobeError("jpg quality must be 0-12")
    res = _run("var d=__doc();var o;if(ARGS.fmt=='png'){o=new PNGSaveOptions();o.compression=6;o.interlaced=false;}"
               "else if(ARGS.fmt=='jpg'){o=new JPEGSaveOptions();o.quality=ARGS.quality;o.embedColorProfile=true;o.matte=MatteType.WHITE;}"
               "else{o=new TiffSaveOptions();o.layers=false;}"
               "var f=new File(ARGS.path);d.saveAs(f,o,true,Extension.LOWERCASE);return {path:f.fsName,format:ARGS.fmt};",
               path=p, fmt=fmt, quality=int(quality), doc=doc)
    if not os.path.exists(res["path"]):
        raise AdobeError(f"Photoshop reported success but no file was written: {res['path']}")
    res["bytes"] = os.path.getsize(res["path"])
    return res


def doc_close(save: bool = False, doc: str | None = None) -> dict:
    return _run("var d=__doc();var n=d.name;d.close(ARGS.save?SaveOptions.SAVECHANGES:SaveOptions.DONOTSAVECHANGES);return {closed:n};",
                save=bool(save), doc=doc)


def doc_resize(width: int, height: int | None = None, doc: str | None = None) -> dict:
    return _run("var d=__doc();var w=ARGS.width;var h=ARGS.height||Math.round(w*__px(d.height)/__px(d.width));"
                "d.resizeImage(UnitValue(w,'px'),UnitValue(h,'px'),d.resolution,ResampleMethod.BICUBIC);return __dinfo(d);",
                width=int(_pos("width", width)), height=int(height) if height else None, doc=doc)


def doc_flatten(doc: str | None = None) -> dict:
    return _run("var d=__doc();d.flatten();return __dinfo(d);", doc=doc)


def doc_undo(steps: int = 1, doc: str | None = None) -> dict:
    if steps < 1:
        raise AdobeError("steps must be 1 or more")
    return _run("var d=__doc();var h=d.historyStates;var i=h.length-1-ARGS.steps;if(i<0){__fail('Not that many history steps');}"
                "d.activeHistoryState=h[i];return {state:h[i].name,steps:ARGS.steps};", steps=int(steps), doc=doc)


# ---------------------------------------------------------------- layers
def layer_list(doc: str | None = None) -> dict:
    return _run("var d=__doc();var a=__walk(d,'',[]);var o=[];for(var i=0;i<a.length;i++){o.push(__linfo(a[i].L,a[i].path));}"
                "return {document:d.name,active:d.activeLayer.name,layers:o};", doc=doc)


def layer_add(name: str, group: str | None = None, doc: str | None = None) -> dict:
    return _run("var d=__doc();var P=d;if(ARGS.group){P=__layer(d,ARGS.group);if(P.typename!='LayerSet'){__fail(ARGS.group+' is not a group');}}"
                "var L=P.artLayers.add();L.name=ARGS.name;d.activeLayer=L;return __linfo(L);", name=name, group=group, doc=doc)


def layer_group(name: str, layers: list[str] | None = None, doc: str | None = None) -> dict:
    return _run("var d=__doc();var G=d.layerSets.add();G.name=ARGS.name;var ls=ARGS.layers||[];var L=[];"
                "for(var i=0;i<ls.length;i++){L.push(__layer(d,ls[i]));}"
                "if(L.length){G.move(L[0],ElementPlacement.PLACEBEFORE);}"
                "for(var j=0;j<L.length;j++){if(L[j].isBackgroundLayer){__fail('The Background layer cannot go in a group');}L[j].move(G,ElementPlacement.PLACEATEND);}"
                "d.activeLayer=G;return __linfo(G);", name=name, layers=layers or [], doc=doc)


def layer_rename(layer: str, name: str, doc: str | None = None) -> dict:
    return _run("var d=__doc();var L=__layer(d,ARGS.layer);L.name=ARGS.name;return __linfo(L);", layer=layer, name=name, doc=doc)


def layer_delete(layer: str, doc: str | None = None) -> dict:
    return _run("var d=__doc();var L=__layer(d,ARGS.layer);var n=L.name;L.remove();return {deleted:n};", layer=layer, doc=doc)


def layer_set(layer: str, visible: bool | None = None, opacity: float | None = None, blend: str | None = None,
              doc: str | None = None) -> dict:
    if opacity is not None and not 0 <= opacity <= 100:
        raise AdobeError("opacity must be 0-100")
    return _run("var d=__doc();var L=__layer(d,ARGS.layer);if(ARGS.visible!==undefined){L.visible=ARGS.visible;}"
                "if(ARGS.opacity!==undefined){L.opacity=ARGS.opacity;}"
                "if(ARGS.blend){var b=BlendMode[ARGS.blend.toUpperCase().replace(/[^A-Z]/g,'')];if(!b){__fail('Unknown blend mode '+ARGS.blend);}L.blendMode=b;}"
                "return __linfo(L);", layer=layer, visible=visible, opacity=opacity, blend=blend, doc=doc)


def layer_move(layer: str, dx: float, dy: float, doc: str | None = None) -> dict:
    return _run("var d=__doc();var L=__layer(d,ARGS.layer);L.translate(ARGS.dx,ARGS.dy);return __linfo(L);",
                layer=layer, dx=dx, dy=dy, doc=doc)


def layer_arrange(layer: str, to: str, doc: str | None = None) -> dict:
    if to not in ("top", "bottom", "up", "down"):
        raise AdobeError("to must be top, bottom, up or down")
    return _run("var d=__doc();var L=__layer(d,ARGS.layer);var S=L.parent.layers;var i=0;for(;i<S.length;i++){if(S[i]==L){break;}}"
                "var last=S.length-1;if(S[last].isBackgroundLayer){last--;}"
                "if(ARGS.to=='top'&&i>0){L.move(S[0],ElementPlacement.PLACEBEFORE);}"
                "else if(ARGS.to=='bottom'&&i<last){L.move(S[last],ElementPlacement.PLACEAFTER);}"
                "else if(ARGS.to=='up'&&i>0){L.move(S[i-1],ElementPlacement.PLACEBEFORE);}"
                "else if(ARGS.to=='down'&&i<last){L.move(S[i+1],ElementPlacement.PLACEAFTER);}"
                "return __linfo(L);", layer=layer, to=to, doc=doc)


def layer_duplicate(layer: str, name: str | None = None, doc: str | None = None) -> dict:
    return _run("var d=__doc();var L=__layer(d,ARGS.layer).duplicate();if(ARGS.name){L.name=ARGS.name;}return __linfo(L);",
                layer=layer, name=name, doc=doc)


def layer_select(layer: str, doc: str | None = None) -> dict:
    return _run("var d=__doc();var L=__layer(d,ARGS.layer);d.activeLayer=L;return __linfo(L);", layer=layer, doc=doc)


# ---------------------------------------------------------------- content
def text_add(text: str, x: float, y: float, size: float = 48, color: str = "#000000", font: str | None = None,
             name: str | None = None, doc: str | None = None) -> dict:
    """Add a text layer. (x, y) is the baseline start of the first line. font = PostScript name."""
    return _run("var d=__doc();var L=d.artLayers.add();L.kind=LayerKind.TEXT;var t=L.textItem;t.contents=ARGS.text;"
                "t.size=new UnitValue(ARGS.size,'px');if(ARGS.font){t.font=ARGS.font;}if(ARGS.color){t.color=__color(ARGS.color);}"
                "t.position=[new UnitValue(ARGS.x,'px'),new UnitValue(ARGS.y,'px')];if(ARGS.name){L.name=ARGS.name;}return __linfo(L);",
                text=text, x=x, y=y, size=_pos("size", size), color=parse_color(color), font=font, name=name, doc=doc)


def text_edit(layer: str, text: str | None = None, size: float | None = None, color: str | None = None,
              font: str | None = None, doc: str | None = None) -> dict:
    return _run("var d=__doc();var L=__layer(d,ARGS.layer);if(L.typename!='ArtLayer'||L.kind!=LayerKind.TEXT){__fail(L.name+' is not a text layer');}"
                "var t=L.textItem;if(ARGS.text!==undefined){t.contents=ARGS.text;}if(ARGS.size){t.size=new UnitValue(ARGS.size,'px');}"
                "if(ARGS.font){t.font=ARGS.font;}if(ARGS.color){t.color=__color(ARGS.color);}return __linfo(L);",
                layer=layer, text=text, size=size, color=parse_color(color), font=font, doc=doc)


def fill(color: str, x: float | None = None, y: float | None = None, w: float | None = None, h: float | None = None,
         shape: str = "rect", layer: str | None = None, new_layer: str | None = None, feather: float | None = None,
         opacity: float = 100, doc: str | None = None) -> dict:
    """Fill a rectangle / ellipse (or the whole layer when no box is given) with a solid colour.
    feather (px) softens the edge and opacity (1-100) makes it a partial dab, so a feathered ellipse at
    low opacity works like a soft brush stamp (dodge/burn, shading, glows)."""
    box = [x, y, w, h]
    if any(v is not None for v in box) and any(v is None for v in box):
        raise AdobeError("Give all of x, y, w, h (or none of them to fill the whole layer)")
    if w is not None and (w <= 0 or h <= 0):
        raise AdobeError("w and h must be positive")
    if shape not in ("rect", "ellipse"):
        raise AdobeError("shape must be rect or ellipse")
    if not 0 < opacity <= 100:
        raise AdobeError("opacity must be 1-100")
    rgb = parse_color(color)
    if rgb is None:
        raise AdobeError("fill needs a colour")
    return _run("var d=__doc();var L;if(ARGS.newLayer){L=d.artLayers.add();L.name=ARGS.newLayer;}else{L=__target(d);}"
                "if(L.typename!='ArtLayer'||L.kind!=LayerKind.NORMAL){__fail('Can only fill a normal pixel layer: '+L.name);}"
                "d.activeLayer=L;__desel(d);try{if(!__sel(d)){d.selection.selectAll();}"
                "d.selection.fill(__color(ARGS.color),ColorBlendMode.NORMAL,ARGS.opacity,false);}finally{__desel(d);}return __linfo(L);",
                color=rgb, x=x, y=y, w=w, h=h, shape=shape, layer=layer, newLayer=new_layer, feather=feather,
                opacity=float(opacity), doc=doc)


FILTERS = {
    "gaussian-blur": "radius (px, default 2)",
    "motion-blur": "angle (deg, default 0), radius (px, default 10)",
    "sharpen": "no parameters",
    "unsharp-mask": "amount (%, 50), radius (px, 1), threshold (0)",
    "add-noise": "amount (%, 5), monochromatic (false)",
    "desaturate": "no parameters",
    "invert": "no parameters",
    "brightness-contrast": "brightness (-150..150, 0), contrast (-50..100, 0)",
    "auto-contrast": "no parameters",
    "posterize": "levels (2..255, 4)",
}


def filter_apply(name: str, params: dict | None = None, layer: str | None = None, doc: str | None = None) -> dict:
    if name not in FILTERS:
        raise AdobeError(f"Unknown filter {name!r}. Available: {', '.join(FILTERS)}")
    return _run("var d=__doc();var L=__target(d);if(L.typename!='ArtLayer'){__fail('Filters need a pixel layer, not a group');}"
                "d.activeLayer=L;var p=ARGS.params||{};var n=ARGS.name;"
                "if(n=='gaussian-blur'){L.applyGaussianBlur(__g(p,'radius',2));}"
                "else if(n=='motion-blur'){L.applyMotionBlur(__g(p,'angle',0),__g(p,'radius',10));}"
                "else if(n=='sharpen'){L.applySharpen();}"
                "else if(n=='unsharp-mask'){L.applyUnSharpMask(__g(p,'amount',50),__g(p,'radius',1),__g(p,'threshold',0));}"
                "else if(n=='add-noise'){L.applyAddNoise(__g(p,'amount',5),NoiseDistribution.GAUSSIAN,!!__g(p,'monochromatic',false));}"
                "else if(n=='desaturate'){L.desaturate();}else if(n=='invert'){L.invert();}"
                "else if(n=='brightness-contrast'){L.adjustBrightnessContrast(__g(p,'brightness',0),__g(p,'contrast',0));}"
                "else if(n=='auto-contrast'){L.autoContrast();}else if(n=='posterize'){L.posterize(__g(p,'levels',4));}"
                "return __linfo(L);", name=name, params=params or {}, layer=layer, doc=doc)


def place(path: str, name: str | None = None, x: float | None = None, y: float | None = None,
          rasterize: bool = False, doc: str | None = None) -> dict:
    """Place an image file as a new (smart object) layer. x,y = where the top-left of its VISIBLE pixels goes
    (transparent margins are not counted, same as layer bounds)."""
    return _run("var d=__doc();var D=new ActionDescriptor();D.putPath(charIDToTypeID('null'),new File(ARGS.path));"
                "D.putEnumerated(charIDToTypeID('FTcs'),charIDToTypeID('QCSt'),charIDToTypeID('Qcsa'));"
                "executeAction(charIDToTypeID('Plc '),D,DialogModes.NO);var L=d.activeLayer;if(ARGS.name){L.name=ARGS.name;}"
                "if(ARGS.x!==undefined||ARGS.y!==undefined){var b=L.bounds;L.translate(__g(ARGS,'x',__px(b[0]))-__px(b[0]),__g(ARGS,'y',__px(b[1]))-__px(b[1]));}"
                "if(ARGS.rasterize){L.rasterize(RasterizeType.ENTIRELAYER);}return __linfo(L);",
                path=norm_path(path, must_exist=True), name=name, x=x, y=y, rasterize=bool(rasterize), doc=doc)


def layer_transform(layer: str | None = None, scale: float | None = None, width: float | None = None,
                    height: float | None = None, rotate: float | None = None, doc: str | None = None) -> dict:
    """Scale a layer about its centre (scale %, or fit its visible pixels to width or height px, keeping
    aspect) and/or rotate it (degrees, clockwise). Smart objects keep full quality when scaled."""
    given = [v for v in (scale, width, height) if v is not None]
    if len(given) > 1:
        raise AdobeError("Give only one of scale, width, height")
    if any(v <= 0 for v in given):
        raise AdobeError("scale, width and height must be positive")
    if not given and rotate is None:
        raise AdobeError("Nothing to do: give scale, width, height or rotate")
    return _run("var d=__doc();var L=__target(d);var b=L.bounds;var w=__px(b[2])-__px(b[0]),h=__px(b[3])-__px(b[1]);"
                "if(w<=0||h<=0){__fail(L.name+' is empty');}var pct=ARGS.scale;"
                "if(ARGS.width){pct=100*ARGS.width/w;}if(ARGS.height){pct=100*ARGS.height/h;}"
                "if(pct){L.resize(pct,pct,AnchorPosition.MIDDLECENTER);}if(ARGS.rotate){L.rotate(ARGS.rotate,AnchorPosition.MIDDLECENTER);}"
                "return __linfo(L);", layer=layer, scale=scale, width=width, height=height, rotate=rotate, doc=doc)


# ---------------------------------------------------------------- masks
def _box(x, y, w, h):
    box = [x, y, w, h]
    if any(v is not None for v in box) and any(v is None for v in box):
        raise AdobeError("Give all of x, y, w, h (or none of them)")
    if w is not None and (w <= 0 or h <= 0):
        raise AdobeError("w and h must be positive")


def mask_add(layer: str | None = None, hide: bool = False, x: float | None = None, y: float | None = None,
             w: float | None = None, h: float | None = None, shape: str = "rect", feather: float | None = None,
             doc: str | None = None) -> dict:
    """Add a layer mask. With a box (x,y,w,h, rect|ellipse, optional feather px) only that area shows
    (hide=true: that area is hidden). Without a box the mask reveals all (hide=true: hides all)."""
    _box(x, y, w, h)
    if shape not in ("rect", "ellipse"):
        raise AdobeError("shape must be rect or ellipse")
    return _run("var d=__doc();var L=__target(d);if(L.typename=='ArtLayer'&&L.isBackgroundLayer){__fail('The Background layer cannot have a mask; add a layer first');}"
                "d.activeLayer=L;__desel(d);if(__linfo(L).mask){var X=new ActionDescriptor();var XR=new ActionReference();"
                "XR.putEnumerated(__c('Chnl'),__c('Chnl'),__c('Msk '));X.putReference(__c('null'),XR);executeAction(__c('Dlt '),X,DialogModes.NO);}"
                "try{var has=__sel(d);var m=has?(ARGS.hide?'HdSl':'RvlS'):(ARGS.hide?'HdAl':'RvlA');"
                "var D=new ActionDescriptor();D.putClass(__c('Nw  '),__c('Chnl'));var R=new ActionReference();"
                "R.putEnumerated(__c('Chnl'),__c('Chnl'),__c('Msk '));D.putReference(__c('At  '),R);"
                "D.putEnumerated(__c('Usng'),__c('UsrM'),__c(m));executeAction(__c('Mk  '),D,DialogModes.NO);}finally{__desel(d);}return __linfo(L);",
                layer=layer, hide=bool(hide), x=x, y=y, w=w, h=h, shape=shape, feather=feather, doc=doc)


def mask_delete(layer: str | None = None, apply: bool = False, doc: str | None = None) -> dict:
    """Remove a layer's mask; apply=true bakes it into the pixels first."""
    return _run("var d=__doc();var L=__target(d);d.activeLayer=L;var o=__linfo(L);if(!o.mask){__fail(L.name+' has no layer mask');}"
                "var D=new ActionDescriptor();var R=new ActionReference();R.putEnumerated(__c('Chnl'),__c('Chnl'),__c('Msk '));"
                "D.putReference(__c('null'),R);D.putBoolean(__c('Aply'),ARGS.apply);executeAction(__c('Dlt '),D,DialogModes.NO);return __linfo(L);",
                layer=layer, apply=bool(apply), doc=doc)


# ---------------------------------------------------------------- adjustment & fill layers
ADJUSTMENTS = {
    "brightness-contrast": "brightness (-150..150, 0), contrast (-50..100, 0)",
    "hue-saturation": "hue (-180..180, 0), saturation (-100..100, 0), lightness (-100..100, 0), colorize (false)",
    "vibrance": "vibrance (-100..100, 0), saturation (-100..100, 0)",
    "curves": "points [[in,out],...] 0-255 (default [[0,0],[255,255]])",
    "levels": "black (0), white (255), gamma (1.0)",
    "black-white": "no parameters",
    "invert": "no parameters",
}


def adjust_add(kind: str, params: dict | None = None, name: str | None = None, clip: bool = False,
               above: str | None = None, doc: str | None = None) -> dict:
    """Add an adjustment layer above `above` (default: the active layer); clip=true affects only the layer below."""
    if kind not in ADJUSTMENTS:
        raise AdobeError(f"Unknown adjustment {kind!r}. Available: {', '.join(ADJUSTMENTS)}")
    p = params or {}
    if kind == "curves":
        pts = p.get("points", [[0, 0], [255, 255]])
        if len(pts) < 2 or any(len(q) != 2 or not all(0 <= v <= 255 for v in q) for q in pts):
            raise AdobeError("curves points must be at least 2 pairs [in,out] within 0-255")
    return _run("var d=__doc();__desel(d);var A=ARGS.above?__layer(d,ARGS.above):d.activeLayer;d.activeLayer=A;var p=ARGS.params||{};var k=ARGS.kind;var t=new ActionDescriptor();var cls;"
                "if(k=='brightness-contrast'){cls='brightnessEvent';t.putInteger(__s('brightness'),__g(p,'brightness',0));t.putInteger(__s('center'),__g(p,'contrast',0));t.putBoolean(__s('useLegacy'),false);}"
                "else if(k=='hue-saturation'){cls='hueSaturation';t.putBoolean(__s('colorize'),!!__g(p,'colorize',false));var a=new ActionDescriptor();"
                "a.putInteger(__s('hue'),__g(p,'hue',0));a.putInteger(__s('saturation'),__g(p,'saturation',0));a.putInteger(__s('lightness'),__g(p,'lightness',0));"
                "var l=new ActionList();l.putObject(__s('hueSatAdjustmentV2'),a);t.putList(__s('adjustment'),l);}"
                "else if(k=='vibrance'){cls='vibrance';t.putInteger(__s('vibrance'),__g(p,'vibrance',0));t.putInteger(__s('saturation'),__g(p,'saturation',0));}"
                "else if(k=='curves'||k=='levels'){cls=k;var ch=new ActionReference();ch.putEnumerated(__s('channel'),__s('channel'),__s('composite'));"
                "var ca=new ActionDescriptor();ca.putReference(__s('channel'),ch);"
                "if(k=='curves'){var pl=new ActionList();var pts=__g(p,'points',[[0,0],[255,255]]);for(var i=0;i<pts.length;i++){var q=new ActionDescriptor();"
                "q.putDouble(__s('horizontal'),pts[i][0]);q.putDouble(__s('vertical'),pts[i][1]);pl.putObject(__s('paint'),q);}ca.putList(__s('curve'),pl);}"
                "else{var il=new ActionList();il.putInteger(__g(p,'black',0));il.putInteger(__g(p,'white',255));ca.putList(__s('input'),il);ca.putDouble(__s('gamma'),__g(p,'gamma',1));}"
                "var al=new ActionList();al.putObject(__s(k+'Adjustment'),ca);t.putList(__s('adjustment'),al);}"
                "else if(k=='black-white'){cls='blackAndWhite';}else{cls='invert';}"
                "var D=new ActionDescriptor();var R=new ActionReference();R.putClass(__s('adjustmentLayer'));D.putReference(__c('null'),R);"
                "var U=new ActionDescriptor();if(ARGS.clip){U.putBoolean(__s('group'),true);}U.putObject(__c('Type'),__s(cls),t);"
                "D.putObject(__c('Usng'),__s('adjustmentLayer'),U);executeAction(__c('Mk  '),D,DialogModes.NO);"
                "var L=d.activeLayer;__above(L,A);if(ARGS.name){L.name=ARGS.name;}return __linfo(L);",
                kind=kind, params=p, name=name, clip=bool(clip), above=above, doc=doc)


def fill_layer_add(kind: str, color: str | None = None, stops: list | None = None, style: str = "linear",
                   angle: float = 90, name: str | None = None, above: str | None = None, doc: str | None = None) -> dict:
    """Add a fill layer: kind=solid (color) or gradient (stops = ['#hex', ...] or [['#hex', pos 0-100], ...],
    style linear|radial, angle in degrees). Fill layers are editable and resolution-independent."""
    if kind not in ("solid", "gradient"):
        raise AdobeError("kind must be solid or gradient")
    if style not in ("linear", "radial"):
        raise AdobeError("style must be linear or radial")
    rgb, gstops = None, None
    if kind == "solid":
        rgb = parse_color(color)
        if rgb is None:
            raise AdobeError("solid fill needs a colour")
    else:
        gstops = _stops(stops)
    return _run("var d=__doc();__desel(d);var A=ARGS.above?__layer(d,ARGS.above):d.activeLayer;d.activeLayer=A;var t=new ActionDescriptor();var cls;"
                "if(ARGS.kind=='solid'){cls='solidColorLayer';t.putObject(__s('color'),__s('RGBColor'),__amrgb(ARGS.rgb));}"
                "else{cls='gradientLayer';t.putEnumerated(__s('type'),__s('gradientType'),__s(ARGS.style));t.putUnitDouble(__s('angle'),__s('angleUnit'),ARGS.angle);"
                "var g=new ActionDescriptor();g.putString(__s('name'),'Custom');g.putEnumerated(__s('gradientForm'),__s('gradientForm'),__s('customStops'));"
                "g.putDouble(__s('interfaceIconFrameDimmed'),4096);var cl=new ActionList();for(var i=0;i<ARGS.stops.length;i++){var s=new ActionDescriptor();"
                "s.putObject(__s('color'),__s('RGBColor'),__amrgb(ARGS.stops[i][0]));s.putEnumerated(__s('type'),__s('colorStopType'),__s('userStop'));"
                "s.putInteger(__s('location'),Math.round(ARGS.stops[i][1]*40.96));s.putInteger(__s('midpoint'),50);cl.putObject(__s('colorStop'),s);}"
                "g.putList(__s('colors'),cl);var tl=new ActionList();for(var j=0;j<2;j++){var o=new ActionDescriptor();o.putUnitDouble(__s('opacity'),__s('percentUnit'),100);"
                "o.putInteger(__s('location'),j*4096);o.putInteger(__s('midpoint'),50);tl.putObject(__s('transferSpec'),o);}g.putList(__s('transparency'),tl);"
                "t.putObject(__s('gradient'),__s('gradientClassEvent'),g);}"
                "var D=new ActionDescriptor();var R=new ActionReference();R.putClass(__s('contentLayer'));D.putReference(__c('null'),R);"
                "var U=new ActionDescriptor();U.putObject(__c('Type'),__s(cls),t);D.putObject(__c('Usng'),__s('contentLayer'),U);"
                "executeAction(__c('Mk  '),D,DialogModes.NO);var L=d.activeLayer;__above(L,A);if(ARGS.name){L.name=ARGS.name;}return __linfo(L);",
                kind=kind, rgb=rgb, stops=gstops, style=style, angle=float(angle), name=name, above=above, doc=doc)


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


# ---------------------------------------------------------------- layer styles
STYLE_KEYS = {
    "drop_shadow": "color (#000000), opacity (75), angle (120), distance (8), spread (0), size (10), blend (multiply)",
    "stroke": "color (#000000), size (3), position (outside|inside|center), opacity (100)",
    "outer_glow": "color (#ffffbe), opacity (75), spread (0), size (16), blend (screen)",
    "color_overlay": "color (#ff0000), opacity (100), blend (normal)",
}


def style_set(layer: str | None = None, drop_shadow: dict | None = None, stroke: dict | None = None,
              outer_glow: dict | None = None, color_overlay: dict | None = None, doc: str | None = None) -> dict:
    """Set layer styles (replaces the layer's current styles). Pass {} to use defaults, e.g. stroke={"size": 4}."""
    given = {k: v for k, v in (("drop_shadow", drop_shadow), ("stroke", stroke), ("outer_glow", outer_glow),
                               ("color_overlay", color_overlay)) if v is not None}
    if not given:
        raise AdobeError("Give at least one style: " + ", ".join(STYLE_KEYS))
    defaults = {"drop_shadow": "#000000", "stroke": "#000000", "outer_glow": "#ffffbe", "color_overlay": "#ff0000"}
    fx = {}
    for key, opts in given.items():
        if not isinstance(opts, dict):
            raise AdobeError(f"{key} must be an object of options")
        o = dict(opts)
        o["color"] = parse_color(o.get("color", defaults[key]))
        if o["color"] is None:
            raise AdobeError(f"{key} needs a colour")
        if key == "stroke" and o.get("position", "outside") not in ("outside", "inside", "center"):
            raise AdobeError("stroke position must be outside, inside or center")
        fx[key] = o
    return _run("var d=__doc();var L=__target(d);if(L.typename=='ArtLayer'&&L.isBackgroundLayer){__fail('The Background layer cannot have styles');}"
                "d.activeLayer=L;var F=new ActionDescriptor();F.putUnitDouble(__s('scale'),__s('percentUnit'),100);var P=__s('percentUnit'),X=__s('pixelsUnit');"
                "function bm(n){return __s(n=='softlight'?'softLight':n);}"
                "var o=ARGS.fx.drop_shadow;if(o){var s=new ActionDescriptor();s.putBoolean(__s('enabled'),true);s.putEnumerated(__s('mode'),__s('blendMode'),bm(__g(o,'blend','multiply')));"
                "s.putObject(__s('color'),__s('RGBColor'),__amrgb(o.color));s.putUnitDouble(__s('opacity'),P,__g(o,'opacity',75));s.putBoolean(__s('useGlobalAngle'),false);"
                "s.putUnitDouble(__s('localLightingAngle'),__s('angleUnit'),__g(o,'angle',120));s.putUnitDouble(__s('distance'),X,__g(o,'distance',8));"
                "s.putUnitDouble(__s('chokeMatte'),X,__g(o,'spread',0));s.putUnitDouble(__s('blur'),X,__g(o,'size',10));F.putObject(__s('dropShadow'),__s('dropShadow'),s);}"
                "o=ARGS.fx.stroke;if(o){var s2=new ActionDescriptor();s2.putBoolean(__s('enabled'),true);var pos={outside:'outsetFrame',inside:'insetFrame',center:'centeredFrame'}[__g(o,'position','outside')];"
                "s2.putEnumerated(__s('style'),__s('frameStyle'),__s(pos));s2.putEnumerated(__s('paintType'),__s('frameFill'),__s('solidColor'));"
                "s2.putEnumerated(__s('mode'),__s('blendMode'),__s('normal'));s2.putUnitDouble(__s('opacity'),P,__g(o,'opacity',100));"
                "s2.putUnitDouble(__s('size'),X,__g(o,'size',3));s2.putObject(__s('color'),__s('RGBColor'),__amrgb(o.color));F.putObject(__s('frameFX'),__s('frameFX'),s2);}"
                "o=ARGS.fx.outer_glow;if(o){var s3=new ActionDescriptor();s3.putBoolean(__s('enabled'),true);s3.putEnumerated(__s('mode'),__s('blendMode'),bm(__g(o,'blend','screen')));"
                "s3.putObject(__s('color'),__s('RGBColor'),__amrgb(o.color));s3.putUnitDouble(__s('opacity'),P,__g(o,'opacity',75));"
                "s3.putEnumerated(__s('glowTechnique'),__s('matteTechnique'),__s('softMatte'));s3.putUnitDouble(__s('chokeMatte'),X,__g(o,'spread',0));"
                "s3.putUnitDouble(__s('blur'),X,__g(o,'size',16));F.putObject(__s('outerGlow'),__s('outerGlow'),s3);}"
                "o=ARGS.fx.color_overlay;if(o){var s4=new ActionDescriptor();s4.putBoolean(__s('enabled'),true);s4.putEnumerated(__s('mode'),__s('blendMode'),bm(__g(o,'blend','normal')));"
                "s4.putUnitDouble(__s('opacity'),P,__g(o,'opacity',100));s4.putObject(__s('color'),__s('RGBColor'),__amrgb(o.color));F.putObject(__s('solidFill'),__s('solidFill'),s4);}"
                "var R=new ActionReference();R.putProperty(__c('Prpr'),__s('layerEffects'));R.putEnumerated(__c('Lyr '),__c('Ordn'),__c('Trgt'));"
                "var D=new ActionDescriptor();D.putReference(__c('null'),R);D.putObject(__s('to'),__s('layerEffects'),F);executeAction(__c('setd'),D,DialogModes.NO);"
                "return __linfo(L);", layer=layer, fx=fx, doc=doc)


def style_clear(layer: str | None = None, doc: str | None = None) -> dict:
    """Remove all layer styles from a layer."""
    return _run("var d=__doc();var L=__target(d);d.activeLayer=L;var D=new ActionDescriptor();var R=new ActionReference();"
                "R.putEnumerated(__c('Lyr '),__c('Ordn'),__c('Trgt'));D.putReference(__c('null'),R);"
                "executeAction(__s('disableLayerStyle'),D,DialogModes.NO);return __linfo(L);", layer=layer, doc=doc)


# ---------------------------------------------------------------- cutout & retouching
RETOUCH_LIB = r"""
function __ell(a,add){var D=new ActionDescriptor(),R=new ActionReference();R.putProperty(__c('Chnl'),__c('fsel'));D.putReference(__c('null'),R);
var E=new ActionDescriptor(),P=__c('#Pxl');E.putUnitDouble(__c('Top '),P,a[1]);E.putUnitDouble(__c('Left'),P,a[0]);E.putUnitDouble(__c('Btom'),P,a[1]+a[3]);E.putUnitDouble(__c('Rght'),P,a[0]+a[2]);
D.putObject(__c('T   '),__c('Elps'),E);D.putBoolean(__c('AntA'),true);executeAction(__c(add?'AddT':'setd'),D,DialogModes.NO);}
function __rect(d,a,add){d.selection.select([[a[0],a[1]],[a[0]+a[2],a[1]],[a[0]+a[2],a[1]+a[3]],[a[0],a[1]+a[3]]],add?SelectionType.EXTEND:SelectionType.REPLACE);}
function __selmany(d,areas,shape){for(var i=0;i<areas.length;i++){if(shape=='rect'){__rect(d,areas[i],i>0);}else{__ell(areas[i],i>0);}}}
function __hassel(d){try{d.selection.bounds;return true;}catch(e){return false;}}
function __pixel(d,L,newName){if(L.typename!='ArtLayer'){__fail(L.name+' is a group; pick a pixel layer');}
if(newName){var N=L.duplicate();N.name=newName;d.activeLayer=N;L=N;}
if(L.kind==LayerKind.SMARTOBJECT){L.rasterize(RasterizeType.ENTIRELAYER);}
if(L.kind!=LayerKind.NORMAL){__fail(L.name+' is not a pixel layer');}d.activeLayer=L;return L;}
function __mkmask(m){var D=new ActionDescriptor();D.putClass(__c('Nw  '),__c('Chnl'));var R=new ActionReference();
R.putEnumerated(__c('Chnl'),__c('Chnl'),__c('Msk '));D.putReference(__c('At  '),R);D.putEnumerated(__c('Usng'),__c('UsrM'),__c(m));executeAction(__c('Mk  '),D,DialogModes.NO);}
"""


def _areas(areas, name="areas") -> list:
    out = []
    for i, a in enumerate(areas or []):
        if not isinstance(a, (list, tuple)) or len(a) != 4:
            raise AdobeError(f"{name}[{i}] must be [x, y, w, h]")
        x, y, w, h = (float(v) for v in a)
        if w <= 0 or h <= 0:
            raise AdobeError(f"{name}[{i}]: w and h must be positive")
        out.append([x, y, w, h])
    if not out:
        raise AdobeError(f"Give at least one {name[:-1]} as [x, y, w, h]")
    return out


def _rrun(body: str, **args):
    return _run(RETOUCH_LIB + body, **args)


def cutout(layer: str | None = None, mode: str = "mask", name: str | None = None, expand: float = 0,
           feather: float = 0, doc: str | None = None) -> dict:
    """Select Subject (Photoshop's AI) on a layer, then mode=mask hides the background with a layer mask
    (non-destructive), or mode=layer copies the subject onto a new layer called `name`."""
    if mode not in ("mask", "layer"):
        raise AdobeError("mode must be mask or layer")
    if expand < 0 or feather < 0:
        raise AdobeError("expand and feather must be 0 or more")
    return _rrun("var d=__doc();var L=__target(d);if(L.typename!='ArtLayer'){__fail('Pick a pixel or smart-object layer, not a group');}"
                 "if(ARGS.mode=='mask'&&L.isBackgroundLayer){L.isBackgroundLayer=false;}d.activeLayer=L;__desel(d);"
                 "try{var D=new ActionDescriptor();D.putBoolean(__s('sampleAllLayers'),false);executeAction(__s('autoCutout'),D,DialogModes.NO);"
                 "if(!__hassel(d)){__fail('Select Subject found no subject');}"
                 "if(ARGS.expand){d.selection.expand(ARGS.expand);}if(ARGS.feather){d.selection.feather(ARGS.feather);}"
                 "var b=d.selection.bounds;var box=[__px(b[0]),__px(b[1]),__px(b[2]),__px(b[3])];"
                 "if(ARGS.mode=='mask'){if(__linfo(L).mask){var X=new ActionDescriptor(),XR=new ActionReference();XR.putEnumerated(__c('Chnl'),__c('Chnl'),__c('Msk '));"
                 "X.putReference(__c('null'),XR);executeAction(__c('Dlt '),X,DialogModes.NO);}__mkmask('RvlS');var o=__linfo(L);}"
                 "else{executeAction(__c('CpTL'),undefined,DialogModes.NO);var N=d.activeLayer;N.name=ARGS.name||(L.name+' cutout');var o=__linfo(N);}"
                 "o.subjectBounds=box;return o;}finally{__desel(d);}",
                 layer=layer, mode=mode, name=name, expand=float(expand), feather=float(feather), doc=doc)


def remove(spots: list, layer: str | None = None, new_layer: str | None = "Retouch", shape: str = "ellipse",
           expand: float = 4, doc: str | None = None) -> dict:
    """Content-Aware Fill over each spot [x, y, w, h] (blemishes, dust, stray hairs, small objects).
    Works on a copy of the layer named `new_layer` (default 'Retouch') so the original is untouched;
    new_layer=None edits the layer itself."""
    if shape not in ("rect", "ellipse"):
        raise AdobeError("shape must be rect or ellipse")
    return _rrun("var d=__doc();var L=__pixel(d,__target(d),ARGS.newLayer);__desel(d);"
                 "try{for(var i=0;i<ARGS.spots.length;i++){__selmany(d,[ARGS.spots[i]],ARGS.shape);if(ARGS.expand){d.selection.expand(ARGS.expand);}"
                 "var D=new ActionDescriptor();D.putEnumerated(__c('Usng'),__c('FlCn'),__s('contentAware'));"
                 "D.putBoolean(__s('contentAwareColorAdaptationFill'),true);D.putUnitDouble(__c('Opct'),__c('#Prc'),100);"
                 "D.putEnumerated(__c('Md  '),__c('BlnM'),__c('Nrml'));executeAction(__c('Fl  '),D,DialogModes.NO);__desel(d);}}"
                 "finally{__desel(d);}var o=__linfo(L);o.spots=ARGS.spots.length;return o;",
                 spots=_areas(spots, "spots"), layer=layer, newLayer=new_layer, shape=shape, expand=float(expand), doc=doc)


def layer_from_box(name: str, x: float, y: float, w: float, h: float, shape: str = "rect", feather: float = 0,
                   cut: bool = False, layer: str | None = None, doc: str | None = None) -> dict:
    """Copy (or cut) a region of a layer onto a new layer called `name` - e.g. split a face, prop or sky
    into its own editable layer."""
    if shape not in ("rect", "ellipse"):
        raise AdobeError("shape must be rect or ellipse")
    box = _areas([[x, y, w, h]], "boxs")[0]
    return _rrun("var d=__doc();var L=__pixel(d,__target(d),null);if(ARGS.cut&&L.isBackgroundLayer){__fail('Cannot cut from the Background layer; copy instead');}"
                 "__desel(d);try{__selmany(d,[ARGS.box],ARGS.shape);if(ARGS.feather){d.selection.feather(ARGS.feather);}"
                 "executeAction(__c(ARGS.cut?'CtTL':'CpTL'),undefined,DialogModes.NO);}finally{__desel(d);}"
                 "var N=d.activeLayer;N.name=ARGS.name;return __linfo(N);",
                 name=name, box=box, shape=shape, feather=float(feather), cut=bool(cut), layer=layer, doc=doc)


def skin_smooth(areas: list, layer: str | None = None, radius: float = 8, threshold: int = 12,
                strength: float = 60, feather: float = 12, name: str = "Skin smooth", doc: str | None = None) -> dict:
    """Smooth skin only inside the given areas [x, y, w, h] (ellipses, e.g. cheeks, forehead): a Surface
    Blur copy of the layer, masked to those areas, at `strength` % opacity. Edges and texture outside stay sharp."""
    if not 1 <= radius <= 100 or not 2 <= threshold <= 255 or not 0 < strength <= 100:
        raise AdobeError("radius 1-100, threshold 2-255, strength 1-100")
    return _rrun("var d=__doc();var L=__pixel(d,__target(d),ARGS.name);__desel(d);"
                 "var D=new ActionDescriptor();D.putUnitDouble(__s('radius'),__s('pixelsUnit'),ARGS.radius);D.putInteger(__s('threshold'),ARGS.threshold);"
                 "executeAction(__s('surfaceBlur'),D,DialogModes.NO);"
                 "try{__selmany(d,ARGS.areas,'ellipse');if(ARGS.feather){d.selection.feather(ARGS.feather);}__mkmask('RvlS');}finally{__desel(d);}"
                 "L.opacity=ARGS.strength;return __linfo(L);",
                 areas=_areas(areas), layer=layer, radius=float(radius), threshold=int(threshold), strength=float(strength),
                 feather=float(feather), name=name, doc=doc)


def dodge_burn(strokes: list, name: str = "Dodge & Burn", doc: str | None = None) -> dict:
    """Non-destructive dodge (lighten) and burn (darken) on a 50%-grey Overlay layer (created if missing).
    strokes = [{"x","y","w","h","mode":"dodge"|"burn","strength":1-100,"feather":px}, ...] - soft ellipse dabs."""
    clean = []
    for i, s in enumerate(strokes or []):
        if not isinstance(s, dict):
            raise AdobeError(f"strokes[{i}] must be an object")
        try:
            box = [s["x"], s["y"], s["w"], s["h"]]
        except KeyError as exc:
            raise AdobeError(f"strokes[{i}] needs x, y, w and h") from exc
        x, y, w, h = _areas([box], "strokes")[0]
        mode = s.get("mode", "dodge")
        if mode not in ("dodge", "burn"):
            raise AdobeError(f"strokes[{i}].mode must be dodge or burn")
        strength = float(s.get("strength", 20))
        if not 0 < strength <= 100:
            raise AdobeError(f"strokes[{i}].strength must be 1-100")
        clean.append({"a": [x, y, w, h], "white": mode == "dodge", "op": strength,
                      "f": float(s.get("feather", max(2.0, min(w, h) / 3)))})
    if not clean:
        raise AdobeError("Give at least one stroke")
    return _rrun("var d=__doc();var L=null;try{L=__layer(d,ARGS.name);}catch(e){}"
                 "if(!L){var A=d.activeLayer;L=d.artLayers.add();L.name=ARGS.name;__desel(d);d.selection.selectAll();"
                 "var g=new SolidColor();g.rgb.red=128;g.rgb.green=128;g.rgb.blue=128;d.selection.fill(g);__desel(d);L.blendMode=BlendMode.OVERLAY;}"
                 "d.activeLayer=L;try{for(var i=0;i<ARGS.st.length;i++){var s=ARGS.st[i];__ell(s.a,false);d.selection.feather(s.f);"
                 "var c=new SolidColor();var v=s.white?255:0;c.rgb.red=v;c.rgb.green=v;c.rgb.blue=v;d.selection.fill(c,ColorBlendMode.NORMAL,s.op,false);__desel(d);}}"
                 "finally{__desel(d);}var o=__linfo(L);o.strokes=ARGS.st.length;return o;",
                 name=name, st=clean, doc=doc)


def sharpen(layer: str | None = None, radius: float = 2, strength: float = 100, name: str = "Sharpen",
            doc: str | None = None) -> dict:
    """High-pass sharpen: a High Pass copy of the layer in Overlay mode at `strength` % (non-destructive)."""
    if not 0.1 <= radius <= 100 or not 0 < strength <= 100:
        raise AdobeError("radius 0.1-100, strength 1-100")
    return _rrun("var d=__doc();var L=__pixel(d,__target(d),ARGS.name);var D=new ActionDescriptor();"
                 "D.putUnitDouble(__s('radius'),__s('pixelsUnit'),ARGS.radius);executeAction(__s('highPass'),D,DialogModes.NO);"
                 "L.blendMode=BlendMode.OVERLAY;L.opacity=ARGS.strength;return __linfo(L);",
                 layer=layer, radius=float(radius), strength=float(strength), name=name, doc=doc)


def action_play(action: str, action_set: str) -> dict:
    return _run("app.doAction(ARGS.action,ARGS.set);return {played:ARGS.action,set:ARGS.set};", action=action, set=action_set)


def script_run(code: str) -> Any:
    """Run arbitrary JSX in Photoshop; the value of the last expression is returned."""
    if not code or not code.strip():
        raise AdobeError("No script code given")
    return _run("var __v=eval(ARGS.code);return (__v===undefined)?null:__v;", code=code)
