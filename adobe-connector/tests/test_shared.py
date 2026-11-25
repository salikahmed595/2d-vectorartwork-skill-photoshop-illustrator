"""Unit tests for the shared backend (no Adobe app needed).

The JSX wrapper is executed for real in Node.js (ES3-compatible subset) with a stub ``app``,
so serialisation, error capture and injection-safety are checked on actual script output.
"""
import filecmp
import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "_shared"))
import jsx_backend as jb  # noqa: E402

NODE = shutil.which("node")


def run_in_node(script: str):
    if not NODE:
        pytest.skip("node not installed")
    proc = subprocess.run([NODE, "-e", "var app={};process.stdout.write(String(eval(" + json.dumps(script) + ")))"],
                          capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


# ---------------------------------------------------------------- build_script / parse_result
def test_round_trip_types():
    out = run_in_node(jb.build_script("return {s:ARGS.s,n:3.5,b:true,z:null,a:[1,'x',{k:false}],inf:1/0};",
                                      {"s": "héllo \"q\" \\ \n ✓"}))
    assert jb.parse_result(out) == {"s": "héllo \"q\" \\ \n ✓", "n": 3.5, "b": True, "z": None,
                                    "a": [1, "x", {"k": False}], "inf": None}


def test_errors_are_captured_with_message():
    out = run_in_node(jb.build_script("__fail('No layer named X');", {}))
    with pytest.raises(jb.AdobeError, match="No layer named X"):
        jb.parse_result(out)


def test_undefined_result_is_null():
    assert jb.parse_result(run_in_node(jb.build_script("return undefined;", {}))) is None


def test_injection_through_args_is_inert():
    evil = "'); throw new Error('pwned'); ('"
    evil2 = "</script>\"}; app.hacked=1; //"
    out = run_in_node(jb.build_script("return [ARGS.a, ARGS.b, app.hacked===undefined];", {"a": evil, "b": evil2}))
    assert jb.parse_result(out) == [evil, evil2, True]


def test_setup_and_teardown_run_even_on_error():
    s = jb.build_script("__fail('boom');", {}, setup="app.x=1;", teardown="app.x=2;")
    proc_script = s + ";app.x"
    if not NODE:
        pytest.skip("node not installed")
    r = subprocess.run([NODE, "-e", "var app={};var r=eval(" + json.dumps(s) + ");process.stdout.write(r+'|'+app.x)"],
                       capture_output=True, text=True, timeout=30)
    reply, x = r.stdout.rsplit("|", 1)
    assert x == "2"
    with pytest.raises(jb.AdobeError, match="boom"):
        jb.parse_result(reply)
    assert proc_script  # keep linters quiet


def test_js_literal_is_ascii():
    lit = jb.js_literal({"t": "  ✓ \x00"})
    assert lit.isascii()


@pytest.mark.parametrize("raw", [None, "", "not json", "[1,2]"])
def test_parse_result_rejects_bad_replies(raw):
    with pytest.raises(jb.AdobeError):
        jb.parse_result(raw)


# ---------------------------------------------------------------- colours / paths
@pytest.mark.parametrize("value,expected", [("#ff8800", [255, 136, 0]), ("FF8800", [255, 136, 0]),
                                            ("#f80", [255, 136, 0]), ("none", None), (None, None)])
def test_parse_color(value, expected):
    assert jb.parse_color(value) == expected


@pytest.mark.parametrize("bad", ["#12345", "red", "#gggggg", "12"])
def test_parse_color_rejects(bad):
    with pytest.raises(jb.AdobeError):
        jb.parse_color(bad)


def test_norm_path_rules(tmp_path):
    f = tmp_path / "a.png"
    f.write_bytes(b"x")
    assert jb.norm_path(str(f), must_exist=True, allowed_roots=[]) == str(f).replace("\\", "/")
    with pytest.raises(jb.AdobeError, match="not found"):
        jb.norm_path(str(tmp_path / "missing.png"), must_exist=True, allowed_roots=[])
    with pytest.raises(jb.AdobeError, match="already exists"):
        jb.norm_path(str(f), overwrite=False, allowed_roots=[])
    with pytest.raises(jb.AdobeError, match="Folder does not exist"):
        jb.norm_path(str(tmp_path / "nope" / "x.png"), allowed_roots=[])
    with pytest.raises(jb.AdobeError, match="required"):
        jb.norm_path("  ", allowed_roots=[])


def test_allowed_roots(tmp_path):
    inside = tmp_path / "work"
    inside.mkdir()
    jb.norm_path(str(inside / "x.png"), allowed_roots=[str(inside)])
    with pytest.raises(jb.AdobeError, match="outside the allowed"):
        jb.norm_path(str(tmp_path / "x.png"), allowed_roots=[str(inside)])
    with pytest.raises(jb.AdobeError, match="outside the allowed"):  # prefix trick: work2 is not inside work
        (tmp_path / "work2").mkdir()
        jb.norm_path(str(tmp_path / "work2" / "x.png"), allowed_roots=[str(inside)])
    with pytest.raises(jb.AdobeError, match="outside the allowed"):
        jb.norm_path(str(inside / ".." / "x.png"), allowed_roots=[str(inside)])


def test_roots_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("CLI_ANYTHING_ADOBE_ROOTS", str(tmp_path / "only"))
    (tmp_path / "only").mkdir()
    with pytest.raises(jb.AdobeError, match="outside the allowed"):
        jb.norm_path(str(tmp_path / "x.png"))


# ---------------------------------------------------------------- copies stay in sync
@pytest.mark.parametrize("app", ["photoshop", "illustrator"])
@pytest.mark.parametrize("name", ["jsx_backend.py", "cli_common.py", "repl_skin.py"])
def test_shared_copies_identical(app, name):
    copy = ROOT / app / "agent-harness" / "cli_anything" / app / "utils" / name
    assert filecmp.cmp(ROOT / "_shared" / name, copy, shallow=False), f"run sync_shared.py ({copy})"


def test_cli_anything_namespace_has_no_init():
    for app in ("photoshop", "illustrator"):
        assert not os.path.exists(ROOT / app / "agent-harness" / "cli_anything" / "__init__.py")


# ---------------------------------------------------------------- version pin (2024 only)
class FakeApp:
    def __init__(self, version):
        self.Version = version


def pinned(monkeypatch, exe="D:/softwares/Adobe Photoshop 2024/Photoshop.exe", major=25, app_version="25.12.0"):
    monkeypatch.setattr(jb.sys, "platform", "win32")
    monkeypatch.setattr(jb, "com_server", lambda progid: None if exe is None else ("{CLSID-2024}", exe))
    monkeypatch.setattr(jb, "file_major", lambda path: major)
    real_isfile = os.path.isfile
    monkeypatch.setattr(jb.os.path, "isfile", lambda path: path == exe or real_isfile(path))  # never depend on what is installed
    made = []
    monkeypatch.setattr(jb, "_dispatch", lambda clsid: made.append(clsid) or FakeApp(app_version))
    return made, jb.JsxBackend("Photoshop.Application.180", "Adobe Photoshop", required_major=25, version_label="2024")


def test_check_ok_for_2024(monkeypatch):
    _, b = pinned(monkeypatch)
    st = b.check()
    assert st["ok"] and st["major"] == 25 and st["exe"].endswith("Photoshop.exe")


def test_check_not_installed_says_install_2024(monkeypatch):
    made, b = pinned(monkeypatch, exe=None)
    st = b.check()
    assert not st["ok"] and "Install Adobe Photoshop 2024" in st["message"]
    with pytest.raises(jb.AdobeError, match="Install Adobe Photoshop 2024"):
        b.app()
    assert made == []  # nothing was launched


def test_registration_pointing_at_2027_is_refused_without_launching(monkeypatch):
    made, b = pinned(monkeypatch, exe="C:/Program Files/Adobe/Adobe Photoshop 2027/Photoshop.exe", major=28)
    with pytest.raises(jb.AdobeError, match="only works with Adobe Photoshop 2024"):
        b.app()
    assert made == []


def test_running_app_with_wrong_version_is_rejected(monkeypatch):
    made, b = pinned(monkeypatch, app_version="28.0.0")
    with pytest.raises(jb.AdobeError, match="only works with Adobe Photoshop 2024"):
        b.app()
    assert made == ["{CLSID-2024}"]


class BusyApp:
    """Reports no version (busy / showing a dialog) a few times, then answers."""
    def __init__(self, nones, version="25.12.0"):
        self.nones, self.version = nones, version

    @property
    def Version(self):
        if self.nones > 0:
            self.nones -= 1
            return None
        return self.version


def test_busy_app_is_waited_for_not_called_the_wrong_version(monkeypatch):
    made, b = pinned(monkeypatch)
    monkeypatch.setattr(jb, "_dispatch", lambda clsid: made.append(clsid) or BusyApp(3))
    waits = []
    monkeypatch.setattr(jb.time, "sleep", waits.append)
    assert b.app().Version == "25.12.0"
    assert len(waits) == 3


def test_app_that_stays_busy_says_busy(monkeypatch):
    made, b = pinned(monkeypatch)
    monkeypatch.setattr(jb, "_dispatch", lambda clsid: made.append(clsid) or BusyApp(99))
    monkeypatch.setattr(jb.time, "sleep", lambda s: None)
    with pytest.raises(jb.AdobeError, match="is busy or showing a dialog") as e:
        b.app()
    assert "only works with" not in str(e.value)


def test_connect_dispatches_the_checked_clsid(monkeypatch):
    made, b = pinned(monkeypatch)
    assert b.app().Version == "25.12.0" and made == ["{CLSID-2024}"]


@pytest.mark.parametrize("raw,exe", [
    ('"C:\\Program Files\\Adobe\\Adobe Photoshop 2024\\Photoshop.exe" /Automation', "C:\\Program Files\\Adobe\\Adobe Photoshop 2024\\Photoshop.exe"),
    ("D:\\softwares\\Adobe Photoshop 2024\\Photoshop.exe /Automation", "D:\\softwares\\Adobe Photoshop 2024\\Photoshop.exe"),
    ("D:\\x\\Illustrator.EXE", "D:\\x\\Illustrator.EXE"),
])
def test_exe_from_server_command(raw, exe):
    assert jb.exe_from_command(raw) == exe
