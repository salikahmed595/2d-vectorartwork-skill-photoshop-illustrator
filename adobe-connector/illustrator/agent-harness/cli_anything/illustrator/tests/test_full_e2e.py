"""E2E tests against the REAL Adobe Illustrator (Windows). They open Illustrator, draw, export
and check the bytes/pixels/SVG geometry. Skipped unless Illustrator is registered for COM.

Artifacts: <repo>/artifacts/e2e/illustrator/  (kept for manual inspection)
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

from cli_anything.illustrator.core import ops
from cli_anything.illustrator.utils.jsx_backend import AdobeError

PIL = pytest.importorskip("PIL.Image")
REPO = pathlib.Path(__file__).resolve().parents[5]
OUT = REPO / "artifacts" / "e2e" / "illustrator"
PS_PNG = REPO / "artifacts" / "e2e" / "photoshop" / "e2e.png"


def _registered() -> bool:
    if sys.platform != "win32":
        return False
    import winreg
    try:
        winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"Illustrator.Application\CLSID")
        return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(not _registered(), reason="Adobe Illustrator not installed")


@pytest.fixture(scope="module")
def doc():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    info = ops.doc_new(400, 300)
    yield info
    for d in ops.doc_list():
        if d["name"] == info["name"] or d["name"].startswith("e2e-"):
            ops.doc_close(save=False, doc=d["name"])


def items():
    return {i["name"]: i for i in ops.item_list()["items"] if i["name"]}


def close_to(a, b, tol=12):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def test_draw_everything(doc):
    assert doc["artboards"][0]["width"] == 400 and doc["artboards"][0]["height"] == 300
    r = ops.shape("rect", 50, 40, 100, 60, fill="#ff0000", name="R")
    assert r["bounds"] == [50, 40, 150, 100] and r["fill"] == "#ff0000" and r["stroke"] == "none"
    ops.shape("ellipse", 200, 40, 80, 80, fill="#0000ff", stroke="#000000", stroke_width=4, name="E")
    ops.shape("rounded-rect", 300, 150, 80, 50, fill="#00ff00", radius=10, name="RR")
    ops.shape("star", 50, 150, 100, 100, fill="#ffcc00", points=5, name="S")
    ops.shape("polygon", 170, 150, 100, 100, fill="#9900ff", sides=6, name="P")
    ops.shape("line", 10, 290, 380, 0, stroke="#333333", stroke_width=2, name="L")
    p = ops.path_draw([[300, 220], [390, 220], [345, 290]], closed=True, fill="#ff00ff", stroke="none", name="Tri")
    assert p["closed"] is True and p["points"] == 3 and p["bounds"] == [300, 220, 390, 290]
    t = ops.text_add("Hi AI", 20, 5, size=24, color="#008800", name="T")
    assert t["text"] == "Hi AI" and t["size"] == 24
    assert abs(t["bounds"][0] - 20) < 1 and abs(t["bounds"][1] - 5) < 1
    got = items()
    assert {"R", "E", "RR", "S", "P", "L", "Tri", "T"} <= set(got)
    assert got["E"]["strokeWidth"] == 4 and got["L"]["fill"] == "none"


def test_svg_geometry_matches_y_down(doc):
    r = ops.doc_export(str(OUT / "e2e.svg"))
    root = ET.parse(r["path"]).getroot()
    ns = "{http://www.w3.org/2000/svg}"
    rects = [e for e in root.iter(ns + "rect")]
    red = [e for e in rects if float(e.get("width", 0)) == 100 and float(e.get("height", 0)) == 60]
    assert red, "red rect not in SVG"
    assert float(red[0].get("x")) == 50 and float(red[0].get("y")) == 40


def test_png_export_pixels(doc):
    r = ops.doc_export(str(OUT / "e2e.png"), transparent=False)
    assert (OUT / "e2e.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n" and r["bytes"] > 0
    with PIL.open(r["path"]) as im:
        im = im.convert("RGB")
        assert im.size == (400, 300)
        assert close_to(im.getpixel((100, 70)), (255, 0, 0))
        assert close_to(im.getpixel((240, 80)), (0, 0, 255))
        assert close_to(im.getpixel((395, 5)), (255, 255, 255))
    r2 = ops.doc_export(str(OUT / "e2e@2x.png"), scale=2)
    with PIL.open(r2["path"]) as im:
        assert im.size == (800, 600)


def test_edit_items(doc):
    m = ops.item_set("R", fill="#00aaff", x=200, y=150)
    assert m["bounds"] == [200, 150, 300, 210] and m["fill"] == "#00aaff"
    assert ops.item_set("R", dx=10, dy=-10)["bounds"] == [210, 140, 310, 200]
    assert ops.item_set("R", opacity=40, rename="Box")["name"] == "Box"
    d = ops.item_duplicate("Box", name="Box2", dx=0, dy=20)
    assert d["bounds"] == [210, 160, 310, 220]
    g = ops.item_group(["Box", "Box2"], name="Boxes")
    assert g["type"] == "GroupItem" and g["children"] == 2
    ops.item_set("Boxes", fill="#123456")
    ops.item_arrange("Boxes", "back")
    ops.item_delete("S")
    assert "S" not in items()
    e = ops.text_edit("T", text="Edited", size=30)
    assert e["text"] == "Edited" and e["size"] == 30


def test_layers(doc):
    ops.layer_add("Top")
    ops.layer_add("Inner", parent="Top")
    ops.shape("rect", 0, 0, 10, 10, name="OnInner", layer="Top/Inner")
    paths = [L["path"] for L in ops.layer_list()["layers"]]
    assert "Top" in paths and "Top/Inner" in paths
    assert items()["OnInner"]["layer"] == "Top/Inner"
    ops.layer_set("Top", locked=True)
    with pytest.raises(AdobeError, match="locked"):
        ops.shape("rect", 0, 0, 5, 5, layer="Top")
    ops.layer_set("Top", locked=False, visible=False)
    with pytest.raises(AdobeError, match="hidden"):
        ops.shape("rect", 0, 0, 5, 5, layer="Top")
    ops.layer_select("Layer 1")
    assert next(L for L in ops.layer_list()["layers"] if L["path"] == "Top")["visible"] is False


def test_save_ai_and_reopen(doc):
    count = ops.doc_info()["items"]
    ops.doc_save(str(OUT / "e2e-ai.ai"))
    assert (OUT / "e2e-ai.ai").read_bytes()[:4] == b"%PDF"  # .ai with PDF compatibility
    ops.doc_close(doc="e2e-ai.ai")
    again = ops.doc_open(str(OUT / "e2e-ai.ai"))
    assert again["name"] == "e2e-ai.ai" and again["items"] == count
    ops.layer_select("Layer 1")  # the reopened file restores 'Top' (hidden) as the active layer


def test_place_and_trace(doc):
    if not PS_PNG.exists():
        pytest.skip("run the Photoshop E2E first (it makes the image to trace)")
    presets = ops.trace_presets()
    assert len(presets) > 3
    pl = ops.place(str(PS_PNG), x=0, y=0, width=200, name="Img")
    assert pl["bounds"][0] == 0 and abs(pl["bounds"][2] - 200) < 0.5
    tr = ops.trace(str(PS_PNG), preset=next((p for p in presets if "6" in p), None), x=0, y=0, width=200, name="Traced")
    assert tr["type"] == "GroupItem" and tr["paths"] > 0


def test_errors_and_undo(doc):
    with pytest.raises(AdobeError, match="No item named Nope"):
        ops.item_delete("Nope")
    with pytest.raises(AdobeError, match="Font not found"):
        ops.text_add("x", 0, 0, font="NoSuchFont-Regular")
    n = ops.doc_info()["items"]
    ops.shape("rect", 0, 0, 5, 5, name="Temp")
    ops.doc_undo(1)
    assert ops.doc_info()["items"] == n


def test_installed_cli_subprocess(doc):
    exe = shutil.which("cli-anything-illustrator") or str(pathlib.Path(sys.executable).parent / "cli-anything-illustrator.exe")
    assert os.path.exists(exe)
    p = subprocess.run([exe, "--json", "item", "list"], capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stderr
    assert json.loads(p.stdout)["result"]["count"] > 0
    p = subprocess.run([exe, "--json", "item", "delete", "Nope"], capture_output=True, text=True, timeout=120)
    assert p.returncode == 1 and "No item named" in json.loads(p.stdout)["error"]
    print(f"\nArtifacts: {OUT}")


# ---------------------------------------------------------------- v1.1 features, checked by pixels
def test_gradients_symbols_pathfinder(doc):
    ops.doc_new(400, 300)
    ops.shape("rect", 0, 0, 400, 60, name="Band")
    g = ops.item_gradient("Band", ["#ff0000", ["#0000ff", 100]])
    assert g["fill"] == "gradient" and g["gradient"]["stops"] == 2
    ops.shape("ellipse", 20, 100, 80, 80, fill="#ff8800", name="A")
    ops.shape("rect", 60, 100, 80, 80, fill="#ff8800", name="B")
    u = ops.pathfinder("unite", ["A", "B"], name="AB")
    assert u["type"] == "PathItem" and u["bounds"] == [20, 100, 140, 180]
    ops.shape("rect", 200, 100, 80, 80, fill="#00aa00", name="Base")
    ops.shape("ellipse", 220, 120, 40, 40, fill="#000000", name="Hole")
    m = ops.pathfinder("minus-front", ["Base", "Hole"], name="Donut")
    assert m["type"] == "CompoundPathItem" and m["bounds"] == [200, 100, 280, 180]
    names = {i["name"] for i in ops.item_list()["items"]}
    assert {"AB", "Donut"} <= names and not {"A", "B", "Base", "Hole"} & names
    ops.shape("star", 0, 0, 40, 40, fill="#ffcc00", name="Star")
    ops.symbol_create("Star", "E2EStar", keep_original=False)
    assert "E2EStar" in ops.symbol_list()
    with pytest.raises(AdobeError, match="already exists"):
        ops.shape("rect", 0, 0, 5, 5, name="X") and ops.symbol_create("X", "E2EStar")
    si = ops.symbol_place("E2EStar", x=320, y=200, scale=1.5, name="S1")
    assert si["type"] == "SymbolItem" and abs(si["bounds"][0] - 320) < 0.5 and abs(si["bounds"][1] - 200) < 0.5
    with pytest.raises(AdobeError, match="No symbol named"):
        ops.symbol_place("Nope")
    r = ops.doc_export(str(OUT / "v11.png"), transparent=False)
    with PIL.open(r["path"]) as im:
        im = im.convert("RGB")
        left, right = im.getpixel((5, 30)), im.getpixel((395, 30))
        assert left[0] > 200 and left[2] < 60 and right[2] > 200 and right[0] < 60  # red -> blue gradient
        assert close_to(im.getpixel((100, 140)), (255, 136, 0))   # united shape filled
        assert close_to(im.getpixel((240, 140)), (255, 255, 255))  # hole punched through
        assert close_to(im.getpixel((205, 105)), (0, 170, 0))      # donut body


HUNTER = pathlib.Path.home() / "Documents" / "PhotoCraft-Work" / "hunter-original.jpg"


@pytest.mark.skipif(not HUNTER.exists(), reason="sample character image missing")
def test_trace_options_change_result(doc):
    """Colour limit, noise and mode really change the trace (Illustrator re-traces between calls)."""
    ops.doc_new(400, 720)
    six = ops.trace(str(HUNTER), width=400, colors=6, name="Six")
    assert six["trace"]["colors"] == 6 and six["type"] == "GroupItem"
    ops.item_delete("Six")
    three = ops.trace(str(HUNTER), width=400, colors=3, noise=60, name="Three")
    assert three["trace"]["colors"] == 3 and three["trace"]["paths"] < six["trace"]["paths"]
    ops.item_delete("Three")
    bw = ops.trace(str(HUNTER), width=400, mode="bw", threshold=90, expand=False, name="Live")
    assert bw["trace"]["mode"] == "blackandwhite" and bw["trace"]["colors"] <= 2
    ops.item_delete("Live")
    pre = ops.trace(str(HUNTER), width=400, preset="16 Colors", name="Sixteen")
    assert pre["trace"]["colors"] == 16
    ops.item_delete("Sixteen")
    nobg = ops.trace(str(HUNTER), width=400, colors=6, drop_background=True, name="NoBg")
    assert nobg["trace"]["droppedBackground"] >= 1
    ops.doc_close(save=False)


def test_curves_are_real_bezier_curves(doc):
    """path_svg and smooth path_draw make true curves: pixels a straight-segment version would miss are filled."""
    made = ops.doc_new(400, 300)
    try:
        dome = ops.path_svg("M220 280 A50 50 0 0 1 320 280 Z", fill="#ff0000", name="Dome")
        assert dome["type"] == "PathItem" and dome["points"] == 3 and dome["closed"] is True
        assert close_to(dome["bounds"], [220, 230, 320, 280], tol=1)
        ring = ops.path_svg("M250 100 A50 50 0 1 1 350 100 A50 50 0 1 1 250 100 Z "
                            "M280 100 A20 20 0 1 1 320 100 A20 20 0 1 1 280 100 Z", fill="#0000ff", name="Ring")
        assert ring["type"] == "CompoundPathItem" and ring["paths"] == 2
        blob = ops.path_draw([[30, 220], [90, 160], [150, 220], [90, 280]], closed=True, smooth=True,
                             fill="#00aa00", stroke="none", name="Blob")
        assert blob["points"] == 4
        wave = ops.path_draw([[10, 20], {"x": 60, "y": 20, "in": [40, 0], "out": [80, 40]}, [110, 20]],
                             stroke="#000000", stroke_width=3, name="Wave")
        assert wave["points"] == 3 and wave["fill"] == "none"

        r = ops.doc_export(str(OUT / "curves.png"), transparent=False, overwrite=True)
        with PIL.open(r["path"]) as im:
            im = im.convert("RGB")
            assert close_to(im.getpixel((235, 250)), (255, 0, 0))     # inside the arc, outside the straight triangle
            assert close_to(im.getpixel((270, 285)), (255, 255, 255))  # below the dome's flat base
            assert close_to(im.getpixel((300, 65)), (0, 0, 255))      # ring body
            assert close_to(im.getpixel((300, 100)), (255, 255, 255))  # hole cut by the inner circle
            assert close_to(im.getpixel((56, 186)), (0, 170, 0))      # bulges past the straight diamond
            assert close_to(im.getpixel((90, 220)), (0, 170, 0))
    finally:
        ops.doc_close(save=False, doc=made["name"])
