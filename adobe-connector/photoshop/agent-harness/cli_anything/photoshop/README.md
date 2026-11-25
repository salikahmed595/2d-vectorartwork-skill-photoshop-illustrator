# cli-anything-photoshop

Agent CLI + MCP server for the real Adobe Photoshop on Windows. Requires Photoshop installed
(COM ProgID `Photoshop.Application`) and Python 3.10+.

```powershell
pip install -e photoshop/agent-harness          # from the repo root, inside the venv
cli-anything-photoshop --help                   # commands
cli-anything-photoshop                          # REPL
cli-anything-photoshop mcp --allowed-root C:\Users\me --allow-jsx    # MCP stdio server
pytest cli_anything/photoshop/tests             # unit + E2E (E2E opens Photoshop)
```
Agent usage: `skills/SKILL.md`. Tests: `tests/TEST.md`.
