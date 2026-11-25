# cli-anything-illustrator

Agent CLI + MCP server for the real Adobe Illustrator on Windows. Requires Illustrator installed
(COM ProgID `Illustrator.Application`) and Python 3.10+.

```powershell
pip install -e illustrator/agent-harness          # from the repo root, inside the venv
cli-anything-illustrator --help                   # commands
cli-anything-illustrator                          # REPL
cli-anything-illustrator mcp --allowed-root C:\Users\me --allow-jsx    # MCP stdio server
pytest cli_anything/illustrator/tests             # unit + E2E (E2E opens Illustrator)
```
Agent usage: `skills/SKILL.md`. Tests: `tests/TEST.md`.
