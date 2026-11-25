"""Shared CLI plumbing for the Adobe harnesses: JSON/human output, error handling,
REPL (default when no subcommand is given) and the MCP stdio server.

Shared by cli-anything-photoshop and cli-anything-illustrator; keep the copies identical.
"""
from __future__ import annotations

import inspect
import json
import os
import shlex
import sys
from typing import Any, Callable

import click

from .jsx_backend import AdobeError

ROOTS_ENV = "CLI_ANYTHING_ADOBE_ROOTS"


# ------------------------------------------------------------------ output
def _human(data: Any, indent: int = 0) -> str:
    pad = "  " * indent
    if isinstance(data, dict):
        lines = []
        for k, v in data.items():
            if isinstance(v, (dict, list)) and v:
                lines.append(f"{pad}{k}:")
                lines.append(_human(v, indent + 1))
            else:
                lines.append(f"{pad}{k}: {v}")
        return "\n".join(lines)
    if isinstance(data, list):
        if not data:
            return f"{pad}(none)"
        out = []
        for item in data:
            if isinstance(item, dict):
                head = item.get("path") or item.get("name") or ""
                rest = {k: v for k, v in item.items() if k not in ("path",) and v not in (None, "")}
                out.append(f"{pad}- {head}  " + "  ".join(f"{k}={v}" for k, v in rest.items() if k != "name"))
            else:
                out.append(f"{pad}- {item}")
        return "\n".join(out)
    return f"{pad}{data}"


def emit(ctx: click.Context, data: Any) -> None:
    if ctx.find_root().obj.get("json"):
        click.echo(json.dumps({"ok": True, "result": data}, ensure_ascii=False))
    else:
        click.echo(_human(data))


def fail(ctx: click.Context, message: str) -> None:
    if ctx.find_root().obj.get("json"):
        click.echo(json.dumps({"ok": False, "error": message}, ensure_ascii=False))
    else:
        click.echo(f"Error: {message}", err=True)
    ctx.exit(1)


def call(ctx: click.Context, fn: Callable, **kwargs: Any) -> None:
    """Run an op, injecting the global --doc target where the op accepts one."""
    root = ctx.find_root().obj
    if "doc" in inspect.signature(fn).parameters and kwargs.get("doc") is None:
        kwargs["doc"] = root.get("doc")
    try:
        emit(ctx, fn(**kwargs))
    except AdobeError as exc:
        fail(ctx, str(exc))


def json_option(f: Callable) -> Callable:
    """Per-command --json (same effect as the global flag) so it works in any position."""
    def _cb(ctx: click.Context, _param, value):
        if value:
            ctx.find_root().obj["json"] = True
        return value
    return click.option("--json", "json_flag", is_flag=True, expose_value=False, callback=_cb,
                        is_eager=True, help="Machine-readable JSON output.")(f)


def add_json_to_all(group: click.Group) -> None:
    for cmd in group.commands.values():
        if isinstance(cmd, click.Group):
            add_json_to_all(cmd)
        elif not any(p.name == "json_flag" for p in cmd.params):
            json_option(cmd)


def parse_params(pairs: tuple[str, ...]) -> dict:
    """key=value pairs -> dict, values parsed as JSON when possible (numbers, true/false)."""
    out = {}
    for pair in pairs:
        if "=" not in pair:
            raise click.BadParameter(f"expected key=value, got {pair!r}")
        k, v = pair.split("=", 1)
        try:
            out[k.strip()] = json.loads(v)
        except json.JSONDecodeError:
            out[k.strip()] = v
    return out


# ------------------------------------------------------------------ REPL
def run_repl(cli: click.Group, app_name: str, version: str, skill_path: str) -> None:
    try:
        from .repl_skin import ReplSkin
        skin = ReplSkin(app_name, version=version, skill_path=skill_path)
    except Exception:  # skin is cosmetic; never block the REPL on it
        skin = None
    if skin:
        skin.print_banner()
        session = skin.create_prompt_session()
    else:
        click.echo(f"cli-anything-{app_name} {version} - type 'help' or 'exit'")
        session = None
    while True:
        try:
            line = skin.get_input(session) if skin else input(f"{app_name}> ")
        except (EOFError, KeyboardInterrupt):
            break
        line = (line or "").strip()
        if not line:
            continue
        if line in ("exit", "quit"):
            break
        if line == "help":
            line = "--help"
        try:
            cli.main(args=shlex.split(line, posix=True), prog_name=f"cli-anything-{app_name}",
                     standalone_mode=False, obj={})
        except click.exceptions.Exit:
            pass
        except click.ClickException as exc:
            exc.show()
        except SystemExit:
            pass
    if skin:
        skin.print_goodbye()


# ------------------------------------------------------------------ MCP
def build_mcp(server_name: str, instructions: str, tools: list[tuple[Callable, str]],
              allowed_roots: tuple[str, ...] = ()):
    """FastMCP server exposing each op as a tool; schemas come from the op's type hints."""
    try:  # mcp >= 2
        from mcp.server.mcpserver import MCPServer as Server
    except ImportError:  # mcp 1.x
        from mcp.server.fastmcp import FastMCP as Server

    if allowed_roots:
        os.environ[ROOTS_ENV] = os.pathsep.join(os.path.abspath(r) for r in allowed_roots)
    server = Server(server_name, instructions=instructions)
    for fn, description in tools:
        doc = inspect.getdoc(fn)
        server.add_tool(_readable_errors(fn), name=fn.__name__, description=description + (f"\n{doc}" if doc else ""))
    return server


def _readable_errors(fn: Callable) -> Callable:
    """Re-raise AdobeError as the SDK's ToolError so the agent sees the message
    (mcp 2.x hides the text of any other exception)."""
    try:
        from mcp.server.mcpserver.exceptions import ToolError
    except ImportError:
        from mcp.server.fastmcp.exceptions import ToolError
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except AdobeError as exc:
            raise ToolError(str(exc)) from exc
    return wrapper


def ensure_utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
