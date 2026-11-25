"""Unit tests for cli-anything-photoshop with the COM backend replaced by a recorder (no Photoshop needed)."""
import json

import pytest
from click.testing import CliRunner

from cli_anything.photoshop import photoshop_cli
from cli_anything.photoshop.core import ops
from cli_anything.photoshop.utils.jsx_backend import AdobeError


class Recorder:
    def __init__(self, reply=None):
        self.calls = []
        self.reply = reply if reply is not None else {"ok": 1}

    def run(self, body, args=None):
        self.calls.append((body, args))
        return self.reply


@pytest.fixture
def rec(monkeypatch):
    r = Recorder()
    monkeypatch.setattr(ops, "_backend", r)
    return r


def invoke(*args):
    return CliRunner().invoke(photoshop_cli.cli, list(args), obj={})


def test_doc_new_passes_args(rec):
    res = invoke("--json", "doc", "new", "--width", "800", "--height", "600", "--name", "Poster")
    assert res.exit_code == 0, res.output
    assert json.loads(res.output) == {"ok": True, "result": {"ok": 1}}
    _, args = rec.calls[0]
    assert args == {"width": 800, "height": 600, "resolution": 72, "name": "Poster", "background": "white"}


def test_json_flag_after_subcommand(rec):
    res = invoke("layer", "list", "--json")
    assert json.loads(res.output)["ok"] is True


def test_global_doc_is_injected(rec):
    invoke("--doc", "a.psd", "layer", "list")
    assert rec.calls[0][1] == {"doc": "a.psd"}


def test_human_output(rec):
    rec.reply = {"name": "x.psd", "width": 10}
    res = invoke("doc", "info")
    assert "name: x.psd" in res.output and "width: 10" in res.output


def test_errors_exit_1_with_json(rec, monkeypatch):
    def boom(*a, **k):
        raise AdobeError("No layer named Foo")
    monkeypatch.setattr(rec, "run", boom)
    res = invoke("--json", "layer", "delete", "Foo")
    assert res.exit_code == 1
    assert json.loads(res.output) == {"ok": False, "error": "No layer named Foo"}


@pytest.mark.parametrize("argv,msg", [
    (["doc", "new", "--width", "0", "--height", "5"], "width must be a positive"),
    (["fill", "#ff0000", "--x", "1"], "Give all of x, y, w, h"),
    (["fill", "#ff0000", "--x", "1", "--y", "1", "--w", "-2", "--h", "3"], "positive"),
    (["fill", "red"], "Colour must be hex"),
    (["filter", "apply", "nope"], "Unknown filter"),
    (["doc", "undo", "--steps", "0"], "steps must be 1"),
])
def test_validation_before_photoshop(rec, argv, msg):
    res = invoke("--json", *argv)
    assert res.exit_code == 1
    assert msg in json.loads(res.output)["error"]
    assert rec.calls == []  # never reached Photoshop


def test_save_requires_psd(rec, tmp_path):
    res = invoke("--json", "doc", "save", str(tmp_path / "out.png"))
    assert "use a .psd path" in json.loads(res.output)["error"]


def test_save_refuses_overwrite(rec, tmp_path):
    p = tmp_path / "out.psd"
    p.write_bytes(b"8BPS")
    assert "already exists" in json.loads(invoke("--json", "doc", "save", str(p)).output)["error"]
    assert invoke("--json", "doc", "save", str(p), "--overwrite").exit_code == 0


def test_filter_params_parsed(rec):
    invoke("filter", "apply", "gaussian-blur", "-p", "radius=4.5", "--layer", "Art")
    assert rec.calls[0][1] == {"name": "gaussian-blur", "params": {"radius": 4.5}, "layer": "Art"}


def test_fill_colour_converted(rec):
    invoke("fill", "#00ff80", "--x", "1", "--y", "2", "--w", "3", "--h", "4", "--shape", "ellipse", "--new-layer", "Dot")
    args = rec.calls[0][1]
    assert args["color"] == [0, 255, 128] and args["shape"] == "ellipse" and args["newLayer"] == "Dot"


def test_script_requires_one_source(rec):
    assert invoke("script", "run").exit_code != 0
    invoke("script", "run", "--code", "1+1")
    assert rec.calls[0][1] == {"code": "1+1"}


def test_every_op_body_uses_known_helpers():
    """Each JSX body only calls helpers defined in LIB (catches typos without Photoshop)."""
    import re
    defined = set(re.findall(r"function (__\w+)", ops.LIB + ops.RETOUCH_LIB)) | {"__fail", "__ser", "__q"}
    import inspect
    src = inspect.getsource(ops)
    used = set(re.findall(r"(__[a-z]\w*)\(", src))
    assert used <= defined | {"__init__"}, used - defined


def test_mcp_tools_build_with_schemas():
    server = photoshop_cli.build_mcp("photoshop", "x", photoshop_cli.MCP_TOOLS)
    import asyncio
    tools = asyncio.run(server.list_tools())
    names = {t.name for t in tools}
    assert {"doc_new", "layer_list", "fill", "doc_export"} <= names
    assert "script_run" not in names  # only with --allow-jsx
    new = next(t for t in tools if t.name == "doc_new")
    schema = getattr(new, "input_schema", None) or new.inputSchema  # mcp 2.x / 1.x
    assert set(schema["required"]) == {"width", "height"}


def test_mcp_errors_reach_the_agent(monkeypatch):
    """mcp 2.x hides plain exception text; AdobeError must arrive as a readable tool error."""
    import asyncio
    rec = Recorder()

    def boom(*a, **k):
        raise AdobeError("No layer named Foo")
    monkeypatch.setattr(rec, "run", boom)
    monkeypatch.setattr(ops, "_backend", rec)
    server = photoshop_cli.build_mcp("photoshop", "x", photoshop_cli.MCP_TOOLS)
    with pytest.raises(Exception, match="No layer named Foo"):
        asyncio.run(server.call_tool("layer_delete", {"layer": "Foo"}))


# ---------------------------------------------------------------- v1.1: masks, adjustments, fill layers, styles
@pytest.mark.parametrize("argv,msg", [
    (["mask", "add", "L", "--x", "1"], "Give all of x, y, w, h"),
    (["adjust", "add", "sepia"], "Unknown adjustment"),
    (["adjust", "add", "curves", "-p", "points=[[0,0]]"], "at least 2 pairs"),
    (["adjust", "add", "curves", "-p", "points=[[0,0],[300,255]]"], "within 0-255"),
    (["fill-layer", "solid"], "needs a colour"),
    (["fill-layer", "gradient", "--stop", "#ff0000"], "at least 2 colour stops"),
    (["fill-layer", "gradient", "--stop", "#ff0000@0", "--stop", "#00ff00@150"], "position 0-100"),
    (["style", "set", "L"], "at least one style"),
    (["style", "set", "L", "--stroke", '{"position":"middle"}'], "outside, inside or center"),
    (["style", "set", "L", "--drop-shadow", '{"color":"blue"}'], "Colour must be hex"),
])
def test_v11_validation(rec, argv, msg):
    res = invoke("--json", *argv)
    assert res.exit_code == 1, res.output
    assert msg in json.loads(res.output)["error"]
    assert rec.calls == []


def test_gradient_stops_spacing_and_sort(rec):
    invoke("fill-layer", "gradient", "--stop", "#000000", "--stop", "#ff0000", "--stop", "#ffffff", "--style", "radial")
    a = rec.calls[0][1]
    assert a["stops"] == [[[0, 0, 0], 0.0], [[255, 0, 0], 50.0], [[255, 255, 255], 100.0]] and a["style"] == "radial"
    rec.calls.clear()
    invoke("fill-layer", "gradient", "--stop", "#ffffff@100", "--stop", "#000000@0")
    assert [s[1] for s in rec.calls[0][1]["stops"]] == [0.0, 100.0]


def test_style_json_options(rec):
    invoke("style", "set", "Logo", "--drop-shadow", "{}", "--stroke", '{"color":"#ffffff","size":4}')
    fx = rec.calls[0][1]["fx"]
    assert fx["drop_shadow"]["color"] == [0, 0, 0] and fx["stroke"] == {"color": [255, 255, 255], "size": 4}
    assert invoke("style", "set", "L", "--stroke", "{bad").exit_code == 2


def test_mask_args(rec):
    invoke("mask", "add", "Photo", "--x", "0", "--y", "0", "--w", "10", "--h", "10", "--shape", "ellipse", "--feather", "3")
    assert rec.calls[0][1] == {"layer": "Photo", "hide": False, "x": 0, "y": 0, "w": 10, "h": 10, "shape": "ellipse", "feather": 3}


# ---------------------------------------------------------------- v1.2 cutout & retouch
@pytest.mark.parametrize("argv,msg", [
    (["cutout", "--mode", "erase"], "Invalid value"),
    (["cutout", "--expand", "-1"], "expand and feather"),
    (["remove", "--spot", "[1,2,3]"], "must be [x, y, w, h]"),
    (["remove", "--spot", "nope"], "JSON"),
    (["remove", "--spot", "[0,0,0,5]"], "positive"),
    (["retouch", "skin", "--area", "[0,0,10,10]", "--radius", "0"], "radius 1-100"),
    (["retouch", "dodge-burn", "--stroke", '{"x":1,"y":1,"w":5}'], "needs x, y, w and h"),
    (["retouch", "dodge-burn", "--stroke", '{"x":1,"y":1,"w":5,"h":5,"mode":"blur"}'], "dodge or burn"),
    (["retouch", "sharpen", "--strength", "0"], "strength 1-100"),
    (["fill", "#ff0000", "--opacity", "0"], "Invalid value"),
])
def test_v12_validation(rec, argv, msg):
    res = invoke("--json", *argv)
    assert res.exit_code != 0
    assert msg in res.output
    assert rec.calls == []


def test_remove_args_and_in_place(rec):
    invoke("remove", "--spot", "[10,20,30,40]", "--spot", "[1,1,2,2]")
    a = rec.calls[0][1]
    assert a["spots"] == [[10, 20, 30, 40], [1, 1, 2, 2]] and a["newLayer"] == "Retouch" and a["shape"] == "ellipse"
    invoke("remove", "--spot", "[10,20,30,40]", "--in-place")
    assert "newLayer" not in rec.calls[1][1]


def test_dodge_burn_defaults(rec):
    invoke("retouch", "dodge-burn", "--stroke", '{"x":0,"y":0,"w":30,"h":60,"mode":"burn"}')
    st = rec.calls[0][1]["st"][0]
    assert st == {"a": [0, 0, 30, 60], "white": False, "op": 20.0, "f": 10.0}


def test_cutout_and_from_box_args(rec):
    invoke("cutout", "Photo", "--mode", "layer", "--name", "Hero", "--feather", "1")
    assert rec.calls[0][1] == {"layer": "Photo", "mode": "layer", "name": "Hero", "expand": 0.0, "feather": 1.0}
    invoke("layer", "from-box", "Face", "--x", "1", "--y", "2", "--w", "3", "--h", "4", "--shape", "ellipse", "--cut")
    a = rec.calls[1][1]
    assert a["box"] == [1, 2, 3, 4] and a["cut"] is True and a["name"] == "Face"


def test_fill_soft_args(rec):
    invoke("fill", "#ffffff", "--x", "0", "--y", "0", "--w", "5", "--h", "5", "--feather", "3", "--opacity", "40")
    a = rec.calls[0][1]
    assert a["feather"] == 3 and a["opacity"] == 40


def test_mcp_has_retouch_tools():
    import asyncio
    names = {t.name for t in asyncio.run(photoshop_cli.build_mcp("photoshop", "x", photoshop_cli.MCP_TOOLS).list_tools())}
    assert {"cutout", "remove", "layer_from_box", "skin_smooth", "dodge_burn", "sharpen"} <= names


def test_layer_transform(rec):
    invoke("layer", "transform", "Hero", "--height", "1200")
    assert rec.calls[0][1] == {"layer": "Hero", "height": 1200.0}
    for argv, msg in ((["--scale", "50", "--width", "10"], "only one"), ([], "Nothing to do"), (["--scale", "-5"], "positive")):
        res = invoke("--json", "layer", "transform", "Hero", *argv)
        assert res.exit_code != 0 and msg in res.output


def test_pinned_to_photoshop_2023():
    """This computer has Photoshop 2023 (v24, COM entry Photoshop.Application.170); 2024 is not installed."""
    ops._backend = None
    b = ops.backend()
    assert (ops.PROGID, ops.REQUIRED_MAJOR, b.version_label) == ("Photoshop.Application.170", 24, "2023")
    assert b.wanted == "Adobe Photoshop 2023"
    ops._backend = None
