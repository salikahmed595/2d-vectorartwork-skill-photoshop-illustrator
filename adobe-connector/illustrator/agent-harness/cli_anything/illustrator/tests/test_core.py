"""Unit tests for cli-anything-illustrator with the COM backend replaced by a recorder (no Illustrator needed)."""
import asyncio
import inspect
import json
import re

import pytest
from click.testing import CliRunner

from cli_anything.illustrator import illustrator_cli
from cli_anything.illustrator.core import ops


class Recorder:
    def __init__(self):
        self.calls = []

    def run(self, body, args=None):
        self.calls.append((body, args))
        return {"ok": 1}


@pytest.fixture
def rec(monkeypatch):
    r = Recorder()
    monkeypatch.setattr(ops, "_backend", r)
    return r


def invoke(*args):
    return CliRunner().invoke(illustrator_cli.cli, list(args), obj={})


def test_shape_defaults_black_fill(rec):
    res = invoke("--json", "shape", "rect", "--x", "10", "--y", "20", "--w", "100", "--h", "50", "--name", "Box")
    assert res.exit_code == 0, res.output
    a = rec.calls[0][1]
    # stroke is explicitly 'none' so shapes don't inherit Illustrator's default 1pt black stroke
    assert a["fill"] == [0, 0, 0] and a["stroke"] == "none" and a["name"] == "Box" and a["kind"] == "rect"


def test_paint_none_and_hex(rec):
    invoke("shape", "ellipse", "--x", "0", "--y", "0", "--w", "5", "--h", "5", "--fill", "none", "--stroke", "#ff0000",
           "--stroke-width", "3")
    a = rec.calls[0][1]
    assert a["fill"] == "none" and a["stroke"] == [255, 0, 0] and a["strokeWidth"] == 3


def test_line_gets_stroke_not_fill(rec):
    invoke("shape", "line", "--x", "0", "--y", "0", "--w", "50", "--h", "0")
    a = rec.calls[0][1]
    assert a["fill"] == "none" and a["stroke"] == [0, 0, 0]


def test_path_points_json(rec):
    invoke("path", "--points", "[[0,0],[10,5],[0,10]]", "--closed", "--fill", "#00ff00")
    a = rec.calls[0][1]
    assert a["subs"] == [{"c": True, "a": [[0, 0, 0, 0, 0, 0, False], [10, 5, 10, 5, 10, 5, False], [0, 10, 0, 10, 0, 10, False]]}]
    assert a["fill"] == [0, 255, 0]
    assert "pathPoints.add()" in rec.calls[0][0] and "leftDirection" in rec.calls[0][0]


def test_path_smooth_and_handle_points(rec):
    res = invoke("--json", "path", "--points", '[[0,0],[10,10],{"x":20,"y":0,"corner":true}]', "--smooth", "--name", "Wave")
    assert res.exit_code == 0, res.output
    anchors = rec.calls[0][1]["subs"][0]["a"]
    assert anchors[1][6] is True and anchors[2][4:6] == [20, 0]
    assert rec.calls[0][1]["name"] == "Wave"


def test_path_svg_draws_curves_and_compound_paths(rec):
    res = invoke("--json", "path-svg", "--d", "M0 0 C0 -10 20 -10 20 0 Z M5 -2 H15 V-4 H5 Z", "--fill", "#ff6a1a", "--name", "Ring")
    assert res.exit_code == 0, res.output
    a = rec.calls[0][1]
    assert len(a["subs"]) == 2 and a["subs"][0]["a"][0][4:6] == [0, -10]
    assert a["fill"] == [255, 106, 26] and a["stroke"] == "none" and a["evenodd"] is True and a["name"] == "Ring"
    assert "compoundPathItems.add()" in rec.calls[0][0]


def test_path_svg_defaults_like_svg_black_fill_no_stroke(rec):
    ops.path_svg("M0 0 L10 0 L5 8 Z")
    a = rec.calls[0][1]
    assert a["fill"] == [0, 0, 0] and a["stroke"] == "none"
    ops.path_svg("M0 0 L10 0 L5 8 Z M2 2 L4 2 L3 3 Z", fill_rule="nonzero")
    assert rec.calls[1][1]["evenodd"] is False


@pytest.mark.parametrize("argv,msg", [
    (["path-svg", "--d", "L1 2"], "must start with M"),
    (["path-svg", "--d", "M0 0 L1 2", "--fill-rule", "odd"], "fill_rule"),
    (["path", "--points", '[[0,0],{"x":1}]'], "point 2"),
])
def test_curve_validation_before_illustrator(rec, argv, msg):
    res = invoke("--json", *argv)
    assert res.exit_code != 0, res.output
    assert msg in res.output
    assert rec.calls == []


@pytest.mark.parametrize("argv,msg", [
    (["shape", "rect", "--x", "0", "--y", "0", "--w", "0", "--h", "5"], "w must be a positive"),
    (["shape", "polygon", "--x", "0", "--y", "0", "--w", "5", "--h", "5", "--sides", "2"], "3 or more sides"),
    (["shape", "star", "--x", "0", "--y", "0", "--w", "5", "--h", "5", "--inner-ratio", "1.5"], "inner_ratio"),
    (["path", "--points", "[[0,0]]"], "at least 2 points"),
    (["item", "set", "A", "--scale", "-1"], "scale must be positive"),
    (["doc", "export", "C:/definitely/missing/folder/x.png"], "Folder does not exist"),
])
def test_validation_before_illustrator(rec, argv, msg):
    res = invoke("--json", *argv)
    assert res.exit_code == 1, res.output
    assert msg in json.loads(res.output)["error"]
    assert rec.calls == []


def test_bad_points_json_is_usage_error(rec):
    assert invoke("path", "--points", "nope").exit_code == 2


def test_save_only_ai_or_pdf(rec, tmp_path):
    res = invoke("--json", "doc", "save", str(tmp_path / "x.svg"))
    assert ".ai or .pdf" in json.loads(res.output)["error"]
    assert invoke("--json", "doc", "save", str(tmp_path / "x.ai")).exit_code == 0
    assert rec.calls[0][1]["ext"] == ".ai"


def test_item_group_order(rec):
    invoke("item", "group", "A", "B", "C", "--name", "G")
    assert rec.calls[0][1] == {"items": ["A", "B", "C"], "name": "G"}


def test_every_op_body_uses_known_helpers():
    defined = set(re.findall(r"function (__\w+)", ops.LIB)) | {"__fail", "__ser", "__q"}
    used = set(re.findall(r"(__[a-z]\w*)\(", inspect.getsource(ops)))
    assert used <= defined | {"__init__"}, used - defined


def test_mcp_tools_build_with_schemas():
    server = illustrator_cli.build_mcp("illustrator", "x", illustrator_cli.MCP_TOOLS)
    tools = asyncio.run(server.list_tools())
    names = {t.name for t in tools}
    assert {"shape", "path_draw", "path_svg", "text_add", "trace", "doc_export"} <= names
    assert "script_run" not in names
    shape = next(t for t in tools if t.name == "shape")
    schema = getattr(shape, "input_schema", None) or shape.inputSchema  # mcp 2.x / 1.x
    assert set(schema["required"]) == {"kind", "x", "y", "w", "h"}


# ---------------------------------------------------------------- v1.1: gradients, symbols, pathfinder
@pytest.mark.parametrize("argv,msg", [
    (["item", "gradient", "A", "--stop", "#ff0000"], "at least 2 colour stops"),
    (["item", "gradient", "A", "--stop", "#ff0000@0", "--stop", "nope@50"], "Colour must be hex"),
    (["pathfinder", "unite", "A"], "at least 2 items"),
    (["symbol", "place", "S", "--scale", "0"], "scale must be positive"),
])
def test_v11_validation(rec, argv, msg):
    res = invoke("--json", *argv)
    assert res.exit_code == 1, res.output
    assert msg in json.loads(res.output)["error"]
    assert rec.calls == []


def test_gradient_args(rec):
    invoke("item", "gradient", "A", "--stop", "#ff0000", "--stop", "#0000ff@100", "--kind", "radial", "--angle", "45")
    a = rec.calls[0][1]
    assert a["stops"] == [[[255, 0, 0], 0.0], [[0, 0, 255], 100.0]] and a["kind"] == "radial" and a["angle"] == 45


def test_pathfinder_args(rec):
    invoke("pathfinder", "minus-front", "Base", "Hole", "--name", "Donut")
    a = rec.calls[0][1]
    assert a["items"] == ["Base", "Hole"] and a["cmd"] == "Live Pathfinder Subtract" and a["name"] == "Donut"
    assert invoke("pathfinder", "smush", "A", "B").exit_code == 2


def test_symbol_args(rec):
    invoke("symbol", "create", "Star", "StarSym", "--remove-original")
    assert rec.calls[0][1] == {"item": "Star", "name": "StarSym", "keep": False}


# ---------------------------------------------------------------- v1.2 trace options
@pytest.mark.parametrize("argv,msg", [
    (["--colors", "1"], "colors must be 2-30"),
    (["--path-fidelity", "120"], "pathFidelity must be 0-100"),
    (["--noise", "0"], "noiseFidelity must be 1-100"),
    (["--mode", "sepia"], "Invalid value"),
])
def test_trace_option_validation(rec, tmp_path, argv, msg):
    img = tmp_path / "a.png"
    img.write_bytes(b"x")
    res = invoke("--json", "trace", "image", str(img), *argv)
    assert res.exit_code != 0 and msg in res.output and rec.calls == []


def test_trace_options_passed(rec, tmp_path):
    img = tmp_path / "a.png"
    img.write_bytes(b"x")
    invoke("trace", "image", str(img), "--mode", "bw", "--threshold", "100", "--noise", "8", "--ignore-white",
           "--method", "abutting", "--colors", "6")
    o = rec.calls[0][1]["opts"]
    assert rec.calls[1][1]["tag"] == rec.calls[0][1]["tag"]  # call 2 finds the same trace
    assert o == {"mode": "TRACINGMODEBLACKANDWHITE", "threshold": 100.0, "noiseFidelity": 8.0, "ignoreWhite": True,
                 "method": "TRACINGMETHODABUTTING", "colors": 6}
    invoke("trace", "image", str(img))
    assert rec.calls[2][1]["opts"] == {}


def test_place_imports_svg_as_editable_vectors(rec, tmp_path):
    svg = tmp_path / "lucide-heart.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M2 2h20v20z"/></svg>')
    png = tmp_path / "photo.png"
    png.write_bytes(b"PNG")
    ops.place(str(svg), x=10, y=20, width=48, name="Heart")
    body, args = rec.calls[-1]
    assert "groupItems.createFromFile" in body and args["svg"] is True and args["name"] == "Heart"
    ops.place(str(png))
    assert rec.calls[-1][1]["svg"] is False


def test_pinned_to_illustrator_2022():
    """The studio uses Illustrator 2022 (v26, COM entry Illustrator.Application.26), never 2023 or any other version."""
    ops._backend = None
    b = ops.backend()
    assert (ops.PROGID, ops.REQUIRED_MAJOR, b.version_label) == ("Illustrator.Application.26", 26, "2022")
    assert b.wanted == "Adobe Illustrator 2022"
    ops._backend = None
