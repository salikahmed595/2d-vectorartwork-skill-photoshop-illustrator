"""MCP integration smoke test: start each server over stdio exactly as Claude does, list tools,
call real tools (opens the Adobe apps), and check a path outside --allowed-root is refused.

Run:  .venv\\Scripts\\python.exe tests\\mcp_smoke.py
"""
import asyncio
import json
import pathlib
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = pathlib.Path(sys.executable).parent
WORK = ROOT / "artifacts"


def is_err(result):
    return getattr(result, "is_error", None) if hasattr(result, "is_error") else result.isError


def text_of(result):
    return "".join(getattr(c, "text", "") for c in result.content)


async def check(app: str, calls: list[tuple[str, dict]]):
    params = StdioServerParameters(command=str(SCRIPTS / f"cli-anything-{app}.exe"),
                                   args=["mcp", "--allow-jsx", "--allowed-root", str(WORK)])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = (await s.list_tools()).tools
            print(f"[{app}] {len(tools)} tools; script_run exposed: {any(t.name == 'script_run' for t in tools)}")
            for name, args in calls:
                res = await s.call_tool(name, args)
                print(f"[{app}] {name} -> error={is_err(res)} {text_of(res)[:160]}")
            res = await s.call_tool("doc_open", {"path": "C:/Windows/win.ini"})
            assert is_err(res) and "outside the allowed" in text_of(res), text_of(res)
            print(f"[{app}] outside-root path refused: OK")


async def main():
    await check("photoshop", [("app_info", {}), ("script_run", {"code": "app.name"})])
    await check("illustrator", [("app_info", {}), ("script_run", {"code": "app.name"})])


asyncio.run(main())
