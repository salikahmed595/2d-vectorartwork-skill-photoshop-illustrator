"""E2E tests against the REAL Adobe Photoshop (Windows). They open Photoshop, build documents,
export files and check the pixels/bytes. Skipped unless Photoshop is registered for COM.

Artifacts: <repo>/artifacts/e2e/photoshop/  (kept for manual inspection)
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

from cli_anything.photoshop.core import ops
from cli_anything.photoshop.utils.jsx_backend import AdobeError

PIL = pytest.importorskip("PIL.Image")
REPO = pathlib.Path(__file__).resolve().parents[5]
OUT = REPO / "artifacts" / "e2e" / "photoshop"


def _photoshop_registered() -> bool:
    if sys.platform != "win32":
        return False
    import winreg
    try:
        winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"Photoshop.Application\CLSID")
        return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(not _photoshop_registered(), reason="Adobe Photoshop not installed")


def _resolve_cli():
    exe = shutil.which("cli-anything-photoshop") or str(pathlib.Path(sys.executable).parent / "cli-anything-photoshop.exe")
    assert os.path.exists(exe), "install the package: pip install -e photoshop/agent-harness"
    return exe


@pytest.fixture(scope="module")
def doc():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    info = ops.doc_new(400, 300, name="e2e-ps", background="white")
    yield info
    for d in ops.doc_list():
        if d["name"].startswith("e2e-"):
            ops.doc_close(save=False, doc=d["name"])


def px(path, xy):
    with PIL.open(path) as im:
        return im.convert("RGB").getpixel(xy)


def close_to(a, b, tol=12):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def test_build_layered_document(doc):
    assert doc["width"] == 400 and doc["height"] == 300 and doc["mode"] == "rgb"
    ops.layer_add("Red box")
    ops.fill("#ff0000", 50, 50, 100, 80)
    ops.fill("#0000ff", 200, 100, 80, 80, shape="ellipse", new_layer="Blue dot")
    t = ops.text_add("Hello", 20, 280, size=32, color="#00aa00", name="Title")
    assert t["type"] == "text" and t["text"] == "Hello"
    g = ops.layer_group("Shapes", ["Red box", "Blue dot"])
    assert g["type"] == "group" and g["children"] == 2
    s = ops.layer_set("Shapes/Blue dot", opacity=50, blend="multiply")
    assert s["opacity"] == 50 and s["blend"] == "multiply"

    layers = {L["path"]: L for L in ops.layer_list()["layers"]}
    assert ["Title", "Shapes", "Shapes/Red box", "Shapes/Blue dot", "Background"] == list(layers)
    assert layers["Shapes/Red box"]["bounds"] == [50, 50, 150, 130]
    assert layers["Background"]["isBackground"] is True


def test_filter_and_arrange(doc):
    ops.filter_apply("gaussian-blur", {"radius": 2}, layer="Shapes/Red box")
    b = next(L for L in ops.layer_list()["layers"] if L["path"] == "Shapes/Red box")["bounds"]
    assert b[0] < 50 and b[2] > 150  # blur spreads the edges
    ops.layer_arrange("Title", "bottom")
    order = [L["path"] for L in ops.layer_list()["layers"] if "/" not in L["path"]]
    assert order == ["Shapes", "Title", "Background"]
    ops.layer_arrange("Title", "top")
    assert ops.layer_list()["layers"][0]["name"] == "Title"


def test_export_png_pixels(doc):
    r = ops.doc_export(str(OUT / "e2e.png"))
    assert r["bytes"] > 0
    raw = (OUT / "e2e.png").read_bytes()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    with PIL.open(OUT / "e2e.png") as im:
        assert im.size == (400, 300)
    assert close_to(px(OUT / "e2e.png", (100, 90)), (255, 0, 0))        # red box centre
    assert close_to(px(OUT / "e2e.png", (240, 140)), (128, 128, 255), 20)  # 50% multiply blue over white
    assert close_to(px(OUT / "e2e.png", (380, 20)), (255, 255, 255))    # untouched background
    with pytest.raises(AdobeError, match="already exists"):
        ops.doc_export(str(OUT / "e2e.png"))
    ops.doc_export(str(OUT / "e2e.jpg"), quality=8)
    assert (OUT / "e2e.jpg").read_bytes()[:3] == b"\xff\xd8\xff"


def test_save_psd_and_reopen(doc):
    ops.doc_save(str(OUT / "e2e-ps.psd"))
    assert (OUT / "e2e-ps.psd").read_bytes()[:4] == b"8BPS"
    before = [L["path"] for L in ops.layer_list()["layers"]]
    ops.doc_close(doc="e2e-ps.psd")
    reopened = ops.doc_open(str(OUT / "e2e-ps.psd"))
    assert reopened["name"] == "e2e-ps.psd" and reopened["saved"] is True
    assert [L["path"] for L in ops.layer_list()["layers"]] == before
    t = ops.text_edit("Title", text="Edited", color="#ff00ff")
    assert t["text"] == "Edited"


def test_place_resize_undo(doc):
    ops.doc_new(800, 600, name="e2e-place")
    L = ops.place(str(OUT / "e2e.png"), name="Placed", x=10, y=20)
    assert L["name"] == "Placed" and L["bounds"][:2] == [10, 20]
    assert ops.layer_move("Placed", 5, 5)["bounds"][:2] == [15, 25]
    ops.doc_undo(1)
    assert next(x for x in ops.layer_list()["layers"] if x["name"] == "Placed")["bounds"][:2] == [10, 20]
    r = ops.doc_resize(400)
    assert (r["width"], r["height"]) == (400, 300)
    ops.doc_flatten()
    assert ops.doc_info()["layers"] == 1


def test_errors_are_readable(doc):
    with pytest.raises(AdobeError, match="No layer named Nope"):
        ops.layer_delete("Nope")
    with pytest.raises(AdobeError, match="No open document named"):
        ops.doc_info(doc="missing.psd")
    with pytest.raises(AdobeError, match="not a text layer"):
        ops.text_edit("Background", text="x")


def test_script_escape_hatch(doc):
    assert ops.script_run("app.activeDocument.layers.length + 1") >= 2
    with pytest.raises(AdobeError):
        ops.script_run("throw new Error('custom failure')")


def test_installed_cli_subprocess(doc):
    exe = _resolve_cli()
    p = subprocess.run([exe, "--json", "--doc", "e2e-ps.psd", "layer", "list"], capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stderr
    data = json.loads(p.stdout)
    assert data["ok"] and data["result"]["document"] == "e2e-ps.psd"
    p = subprocess.run([exe, "--json", "layer", "delete", "Nope"], capture_output=True, text=True, timeout=120)
    assert p.returncode == 1 and json.loads(p.stdout)["ok"] is False
    print(f"\nArtifacts: {OUT}")


# ---------------------------------------------------------------- v1.1 features, checked by pixels
def test_fill_layers_masks_styles_adjustments(doc):
    ops.doc_new(400, 300, name="e2e-fx", background="white")
    g = ops.fill_layer_add("gradient", stops=["#000000", "#ffffff"], style="linear", angle=0, name="Grad")
    assert g["type"] == "gradientfill"
    s = ops.fill_layer_add("solid", color="#00ff00", name="Green")
    assert s["type"] == "solidfill" and s["mask"] is True
    m = ops.mask_add("Green", hide=True, x=0, y=0, w=200, h=300)  # replaces the default mask; left half hidden
    assert m["mask"] is True
    ops.fill("#ff0000", 250, 50, 100, 100, new_layer="Box")
    st = ops.style_set("Box", stroke={"color": "#0000ff", "size": 6, "position": "outside"}, drop_shadow={"distance": 0, "size": 0, "opacity": 0})
    assert set(st["styles"]) == {"frameFX", "dropShadow"}
    a = ops.adjust_add("hue-saturation", {"saturation": -100}, name="Desat")  # greyscale everything below
    assert a["type"] == "huesaturation"
    ops.layer_set("Desat", visible=False)
    p = OUT / "fx.png"
    ops.doc_export(str(p))
    assert close_to(px(p, (5, 150)), (0, 0, 0), 20)          # gradient starts black on the left (Green hidden here)
    assert close_to(px(p, (195, 150)), (124, 124, 124), 30)  # mid-grey near the middle
    assert close_to(px(p, (220, 20)), (0, 255, 0))           # green on the right half
    assert close_to(px(p, (300, 100)), (255, 0, 0))          # red box
    assert close_to(px(p, (247, 100)), (0, 0, 255))          # blue outside stroke
    ops.layer_set("Desat", visible=True)
    ops.doc_export(str(OUT / "fx-desat.png"))
    r, g2, b = px(OUT / "fx-desat.png", (300, 100))
    assert abs(r - g2) < 12 and abs(g2 - b) < 12             # red box turned grey
    for kind, params in [("brightness-contrast", {"brightness": 10}), ("vibrance", {"vibrance": 20}),
                         ("curves", {"points": [[0, 0], [128, 160], [255, 255]]}), ("levels", {"black": 10, "white": 245}),
                         ("black-white", {}), ("invert", {})]:
        assert ops.adjust_add(kind, params, name=kind)["name"] == kind
    ops.layer_set("invert", visible=True)
    for n in ("Desat", "brightness-contrast", "vibrance", "curves", "levels", "black-white"):
        ops.layer_set(n, visible=False)
    ops.doc_export(str(OUT / "fx-invert.png"))
    assert close_to(px(OUT / "fx-invert.png", (300, 100)), (0, 255, 255))  # red inverted to cyan
    assert ops.style_clear("Box")["styles"] == []
    assert ops.mask_delete("Green")["mask"] is False
    ops.doc_save(str(OUT / "e2e-fx.psd"))
    assert (OUT / "e2e-fx.psd").read_bytes()[:4] == b"8BPS"


def test_mask_errors(doc):
    with pytest.raises(AdobeError, match="Background layer cannot have a mask"):
        ops.mask_add("Background", doc="e2e-fx.psd")
    with pytest.raises(AdobeError, match="has no layer mask"):
        ops.mask_delete("Box", doc="e2e-fx.psd")


def test_adjustment_after_group_is_top_level(doc):
    """Regression: after layer_group, new adjustment layers must not land inside the group."""
    ops.doc_new(100, 100, name="e2e-order")
    ops.layer_add("A")
    ops.layer_group("G", ["A"])
    ops.adjust_add("vibrance", {"vibrance": 10}, name="V")
    ops.fill_layer_add("solid", color="#123456", name="C", above="Background")
    top = [L["path"] for L in ops.layer_list()["layers"] if "/" not in L["path"]]
    assert top == ["V", "G", "C", "Background"]


def test_retouch_tools_change_pixels(doc):
    """Content-aware remove, soft fill, dodge/burn, skin smooth, sharpen, layer-from-box on a synthetic image."""
    ops.doc_new(300, 200, name="e2e-retouch")
    ops.fill("#808080", layer="Background")
    ops.fill("#ff0000", 140, 90, 20, 20, shape="ellipse", layer="Background")      # the "blemish"
    r = ops.remove([[140, 90, 20, 20]], layer="Background")
    assert r["name"] == "Retouch" and r["spots"] == 1
    ops.doc_export(str(OUT / "retouch-remove.png"))
    assert close_to(px(OUT / "retouch-remove.png", (150, 100)), (128, 128, 128), tol=20)   # red spot gone
    ops.layer_set("Retouch", visible=False)
    ops.doc_export(str(OUT / "retouch-original.png"))
    assert close_to(px(OUT / "retouch-original.png", (150, 100)), (255, 0, 0))            # original untouched
    ops.layer_set("Retouch", visible=True)
    s = ops.fill("#ffffff", 10, 10, 60, 60, new_layer="Soft", feather=10, opacity=50)
    ops.doc_export(str(OUT / "retouch-soft.png"))
    c = px(OUT / "retouch-soft.png", (40, 40))
    assert 170 < c[0] < 215 and close_to(c, (c[0], c[0], c[0]), 3)                       # ~50% white over grey
    edge = px(OUT / "retouch-soft.png", (12, 40))[0]
    assert 128 <= edge < c[0]                                                             # feathered edge
    ops.layer_set("Soft", visible=False)
    db = ops.dodge_burn([{"x": 200, "y": 20, "w": 60, "h": 60, "mode": "dodge", "strength": 60},
                         {"x": 200, "y": 120, "w": 60, "h": 60, "mode": "burn", "strength": 60}])
    assert db["blend"] == "overlay" and db["strokes"] == 2
    ops.doc_export(str(OUT / "retouch-db.png"))
    assert px(OUT / "retouch-db.png", (230, 50))[0] > 150 and px(OUT / "retouch-db.png", (230, 150))[0] < 105
    assert px(OUT / "retouch-db.png", (100, 150))[0] in range(120, 137)                 # neutral elsewhere
    sk = ops.skin_smooth([[20, 120, 60, 60]], layer="Retouch")
    assert sk["mask"] is True and sk["opacity"] == 60
    sh = ops.sharpen(layer="Retouch", strength=50)
    assert sh["blend"] == "overlay" and sh["opacity"] == 50
    fb = ops.layer_from_box("Piece", 0, 0, 50, 40, layer="Retouch")
    assert fb["bounds"] == [0, 0, 50, 40]
    tf = ops.layer_transform("Piece", height=80)
    assert tf["bounds"] == [-25, -20, 75, 60]                                            # 2x about the centre
    ops.doc_close(save=False)


HUNTER = pathlib.Path.home() / "Documents" / "PhotoCraft-Work" / "hunter-original.jpg"


@pytest.mark.skipif(not HUNTER.exists(), reason="sample character image missing")
def test_cutout_select_subject_on_character(doc):
    shutil.copy(HUNTER, OUT / "e2e-hunter.jpg")
    ops.doc_open(str(OUT / "e2e-hunter.jpg"))
    c = ops.cutout(layer="Background", mode="layer", name="Hero")
    l, t, r, b = c["subjectBounds"]
    assert c["name"] == "Hero" and (r - l) > 700 and (b - t) > 1800           # whole figure incl. crossbow
    ops.layer_set("Background", visible=False)
    ops.doc_export(str(OUT / "hunter-cutout.png"))
    with PIL.open(OUT / "hunter-cutout.png") as im:
        assert im.mode == "RGBA" and im.getpixel((5, 5))[3] == 0              # background transparent
        assert im.getpixel((550, 600))[3] == 255                              # body opaque
    m = ops.cutout(layer="Background", mode="mask")
    assert m["mask"] is True and m["isBackground"] is False
    ops.doc_close(save=False)
