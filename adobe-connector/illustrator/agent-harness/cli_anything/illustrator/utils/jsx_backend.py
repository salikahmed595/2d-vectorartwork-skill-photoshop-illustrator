"""Backend: drives a real Adobe app (Photoshop / Illustrator) on Windows through COM.

Every operation is an ExtendScript (JSX) body that reads its inputs from ``ARGS`` and
returns a plain value. Inputs are serialised with ``json.dumps`` (valid ES3 literal syntax,
ASCII-escaped), so file paths or text can never break out into code. Results come back as
a JSON string built by a small ES3 serialiser (ExtendScript has no native JSON).

This file is shared by cli-anything-photoshop and cli-anything-illustrator; keep the
copies identical (tests check this).
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

PRELUDE = r"""
function __q(s){s=String(s);var o='"';for(var i=0;i<s.length;i++){var c=s.charAt(i),n=s.charCodeAt(i);
if(c=='"'||c=='\\'){o+='\\'+c;}else if(n<32||n>126){var h=n.toString(16);while(h.length<4){h='0'+h;}o+='\\u'+h;}else{o+=c;}}return o+'"';}
function __ser(v){if(v===null||v===undefined){return 'null';}var t=typeof v;
if(t=='number'){return isFinite(v)?String(v):'null';}if(t=='boolean'){return v?'true':'false';}if(t=='string'){return __q(v);}
if(v instanceof Array){var a=[];for(var i=0;i<v.length;i++){a.push(__ser(v[i]));}return '['+a.join(',')+']';}
if(t=='object'){var p=[];for(var k in v){if(v.hasOwnProperty(k)){p.push(__q(k)+':'+__ser(v[k]));}}return '{'+p.join(',')+'}';}
return __q(String(v));}
function __fail(msg){throw new Error(msg);}
"""


class AdobeError(RuntimeError):
    """Raised when the Adobe app reports an error or cannot be reached."""


def js_literal(value: Any) -> str:
    """Encode a Python value as an ES3 literal. ASCII-only, so it is injection-safe."""
    return json.dumps(value, ensure_ascii=True)


def build_script(body: str, args: dict | None, setup: str = "", teardown: str = "") -> str:
    """Wrap a JSX body so it always returns '{"ok":true,"result":...}' or an error object."""
    return (
        PRELUDE
        + "var ARGS = " + js_literal(args or {}) + ";\n"
        + "(function(){var __r;try{" + setup + "\n"
        + "__r='{\"ok\":true,\"result\":'+__ser((function(){" + body + "\n})())+'}';"
        + "}catch(e){__r='{\"ok\":false,\"error\":'+__q(e.message||String(e))+',\"line\":'+__ser(e.line||null)+'}';}"
        + "try{" + teardown + "}catch(e2){}return __r;})();"
    )


def parse_result(raw: Any) -> Any:
    """Turn the string returned by DoJavaScript into a Python value or raise AdobeError."""
    if raw is None or raw == "":
        raise AdobeError("The Adobe app returned nothing (a modal dialog may be open in the app).")
    try:
        data = json.loads(str(raw))
    except json.JSONDecodeError as exc:
        raise AdobeError(f"Unreadable reply from the Adobe app: {str(raw)[:200]!r}") from exc
    if not isinstance(data, dict) or "ok" not in data:
        raise AdobeError(f"Unexpected reply shape: {str(raw)[:200]!r}")
    if not data["ok"]:
        line = data.get("line")
        raise AdobeError(data.get("error", "unknown error") + (f" (script line {line})" if line else ""))
    return data.get("result")


def exe_from_command(command: str) -> str:
    """'"C:\\x y\\App.exe" /Automation' or 'C:\\x y\\App.exe /Automation' -> 'C:\\x y\\App.exe'."""
    cmd = command.strip()
    if cmd.startswith('"'):
        end = cmd.find('"', 1)
        return cmd[1:end] if end > 0 else cmd[1:]
    i = cmd.lower().find(".exe")
    return cmd[:i + 4] if i >= 0 else cmd


def _reg_default(path: str) -> str | None:
    import winreg
    for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, path, 0, winreg.KEY_READ | view) as key:
                value, _ = winreg.QueryValueEx(key, "")
                if value:
                    return str(value)
        except OSError:
            continue
    return None


def com_server(progid: str) -> tuple[str, str] | None:
    """(CLSID, exe) that COM would start for this ProgID, read from the registry. Starts nothing."""
    clsid = _reg_default(progid + "\\CLSID")
    if not clsid:
        return None
    command = _reg_default("CLSID\\" + clsid + "\\LocalServer32")
    return (clsid, exe_from_command(command)) if command else None


def file_major(path: str) -> int | None:
    """Major file version of an .exe (Photoshop 2024 -> 25, Illustrator 2024 -> 28)."""
    try:
        import win32api
        info = win32api.GetFileVersionInfo(path, "\\")
        return int(info["FileVersionMS"]) >> 16
    except Exception:
        return None


BUSY_TRIES = 10
BUSY_WAIT_S = 2.0


def _major_of(version: Any) -> int | None:
    try:
        return int(str(version).strip().split(".")[0])
    except ValueError:
        return None


def _dispatch(clsid: str):
    import win32com.client
    return win32com.client.Dispatch(clsid)


class JsxBackend:
    """Attach to (or launch) the app by COM and run JSX bodies.

    With ``required_major`` set, only that release is ever used: the registry is checked before
    anything starts (so a different, unlicensed version is never launched) and the running app's
    version is checked again after connecting.
    """

    def __init__(self, progid: str, app_label: str, setup: str = "", teardown: str = "",
                 required_major: int | None = None, version_label: str = ""):
        self.progid = progid
        self.app_label = app_label
        self.setup = setup
        self.teardown = teardown
        self.required_major = required_major
        self.version_label = version_label
        self._app = None

    @property
    def wanted(self) -> str:
        return f"{self.app_label} {self.version_label}".strip()

    def _install_hint(self) -> str:
        return (f"Install {self.wanted} (version {self.required_major}.x), open it once, then try again. "
                "Other versions are not used.") if self.required_major else f"Install {self.app_label} and open it once."

    def check(self) -> dict:
        """Is the required version installed and registered for automation? Starts nothing."""
        status = {"ok": False, "app": self.wanted, "progid": self.progid, "clsid": None, "exe": None,
                  "major": None, "message": ""}
        if sys.platform != "win32":
            status["message"] = f"{self.app_label} automation needs Windows (COM)."
            return status
        found = com_server(self.progid)
        if not found or not os.path.isfile(found[1]):
            status["message"] = f"{self.wanted} is not installed on this computer. {self._install_hint()}"
            return status
        status["clsid"], status["exe"] = found
        status["major"] = file_major(found[1])
        if self.required_major and status["major"] != self.required_major:
            status["message"] = (f"This connector only works with {self.wanted}, but its automation entry "
                                 f"points to {found[1]} (version {status['major']}). {self._install_hint()}")
            return status
        status["ok"] = True
        status["message"] = f"{self.wanted} found at {found[1]}."
        return status

    def _connect(self):
        status = self.check()
        if not status["ok"]:
            raise AdobeError(status["message"])
        try:
            import pythoncom  # pywin32
        except ImportError as exc:
            raise AdobeError("pywin32 is missing. Install it with: pip install pywin32") from exc
        pythoncom.CoInitialize()  # safe to call repeatedly / from worker threads
        try:
            app = _dispatch(status["clsid"])  # the exact class checked above, not whatever the ProgID says now
        except Exception as exc:  # pywintypes.com_error
            raise AdobeError(
                f"Could not start or reach {self.wanted} through COM ({self.progid}). "
                f"{self._install_hint()} Details: {exc}"
            ) from exc
        if self.required_major:
            # A busy app (running a script, or showing a dialog) can answer with no version for a while.
            # The exe was already checked above, so wait for it instead of calling it the wrong version.
            running = None
            for attempt in range(BUSY_TRIES):
                try:
                    running = app.Version
                except Exception:  # pywintypes.com_error: call rejected while busy
                    running = None
                if running is not None:
                    break
                if attempt < BUSY_TRIES - 1:
                    time.sleep(BUSY_WAIT_S)
            if running is None:
                raise AdobeError(f"{self.wanted} is busy or showing a dialog, so it did not answer. "
                                 f"Close any open dialog in it, wait for it to finish, then try again.")
            if _major_of(running) != self.required_major:
                raise AdobeError(f"This connector only works with {self.wanted}, but the app that answered "
                                 f"is version {running}. Close it and open {self.wanted}.")
        return app

    def app(self):
        if self._app is None:
            self._app = self._connect()
        return self._app

    def run(self, body: str, args: dict | None = None) -> Any:
        script = build_script(body, args, self.setup, self.teardown)
        try:
            raw = self.app().DoJavaScript(script)
        except AdobeError:
            raise
        except Exception as exc:
            self._app = None  # app may have been closed; reconnect next time
            raise AdobeError(f"{self.app_label} did not run the script: {exc}") from exc
        return parse_result(raw)


def norm_path(path: str, must_exist: bool = False, overwrite: bool = True,
              allowed_roots: list[str] | None = None) -> str:
    """Absolute, forward-slash path for ExtendScript File(); enforce roots / existence."""
    if not path or not str(path).strip():
        raise AdobeError("A file path is required.")
    full = os.path.abspath(os.path.expandvars(os.path.expanduser(str(path))))
    roots = allowed_roots if allowed_roots is not None else _env_roots()
    if roots:
        ok = any(os.path.normcase(full).startswith(os.path.normcase(os.path.abspath(r)).rstrip("\\/") + os.sep)
                 for r in roots)
        if not ok:
            raise AdobeError(f"Path is outside the allowed folders: {full}")
    if must_exist and not os.path.exists(full):
        raise AdobeError(f"File not found: {full}")
    if not must_exist:
        parent = os.path.dirname(full)
        if not os.path.isdir(parent):
            raise AdobeError(f"Folder does not exist: {parent}")
        if not overwrite and os.path.exists(full):
            raise AdobeError(f"File already exists (pass overwrite to replace it): {full}")
    return full.replace("\\", "/")


def _env_roots() -> list[str]:
    raw = os.environ.get("CLI_ANYTHING_ADOBE_ROOTS", "")
    return [r for r in raw.split(os.pathsep) if r.strip()]


def parse_color(value: str | None) -> list[int] | None:
    """'#ff8800' / 'ff8800' / '#f80' -> [255,136,0]; 'none' or None -> None."""
    if value is None:
        return None
    v = str(value).strip().lower()
    if v in ("", "none", "transparent"):
        return None
    if v.startswith("#"):
        v = v[1:]
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    if len(v) != 6 or any(c not in "0123456789abcdef" for c in v):
        raise AdobeError(f"Colour must be hex like #ff8800 or 'none', got {value!r}")
    return [int(v[i:i + 2], 16) for i in (0, 2, 4)]
