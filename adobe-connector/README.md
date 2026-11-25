# Adobe CLI-Anything: Photoshop + Illustrator for agents

Two agent-friendly CLIs, each also an MCP server, built on the
[CLI-Anything](https://github.com/HKUDS/CLI-Anything) harness method (Apache-2.0; `repl_skin.py` is copied from it).
They drive the **real** Adobe Photoshop and Illustrator on a Windows PC through COM + ExtendScript;
nothing is re-implemented.

| | CLI (in `adobe-connector\.venv\Scripts\`) | MCP server (registered with Claude Code) |
|---|---|---|
| Photoshop | `cli-anything-photoshop` | `photoshop`: tools `mcp__photoshop__*` (40) |
| Illustrator | `cli-anything-illustrator` | `illustrator`: tools `mcp__illustrator__*` (35) |

Agent instructions: `photoshop/.../skills/SKILL.md` and `illustrator/.../skills/SKILL.md`.

## Install
Run the repo-root installer: `powershell -ExecutionPolicy Bypass -File .\install.ps1`. It creates `.venv` here,
installs both harnesses with `pip install -e`, runs `app check` for both apps (and stops with an install message
if Photoshop 2023 or Illustrator 2022 is missing), then registers the `photoshop` / `illustrator` MCP servers with
`claude mcp add --scope user` unless they are already registered. Running it again does not register them twice.

## What they cover
- **Photoshop:** documents, pixel/text layers, groups, fills, 10 filters, placing images, layer masks,
  7 adjustment-layer types, solid/gradient fill layers, layer styles (drop shadow, stroke, outer glow,
  colour overlay), Select Subject cutout, Content-Aware spot removal, skin smoothing, dodge & burn,
  high-pass sharpen, soft (feathered) fills, layer scale/rotate, region-to-layer, Actions, layered PSD,
  PNG/JPG/TIF export.
- **Illustrator:** shapes, straight/smooth paths and real Bezier curves from SVG path data, text, item edit/group/arrange, layers, linear/radial gradients,
  Pathfinder (unite, minus front, intersect, exclude, divide), symbols, place + Image Trace (mode, colours,
  noise, fidelity, threshold, drop background), Actions,
  .ai/.pdf save, PNG/JPG/SVG export.

## Quick use
```powershell
$env:PATH = "$PWD\.venv\Scripts;$env:PATH"    # once per terminal, from adobe-connector\
cli-anything-photoshop --json doc new --width 800 --height 600 --name Demo
cli-anything-photoshop --json fill-layer gradient --stop "#0b0a1f" --stop "#ff3d6e"
cli-anything-photoshop --json text add "Hello" --x 40 --y 120 --size 64 --color "#ffffff"
cli-anything-photoshop --json doc export "$env:USERPROFILE\Documents\demo.png"
cli-anything-photoshop            # no arguments = interactive REPL
```
Every command takes `--json` and prints `{"ok":true,"result":...}` or `{"ok":false,"error":"..."}` with exit code 1.
Example agent pipelines (CLI only):
- `examples\build_demo.ps1`: logo in Illustrator, poster in Photoshop.
- `examples\custom_artwork.ps1 -Image C:\path\photo.jpg -Title "TEXT"`: your image -> Select Subject cutout ->
  Illustrator flat vector -> Photoshop poster (layered PSD, AI, SVG, PNG in `Documents\Adobe-Work\<job>\out`).

Workflow skill for agents: `skills\adobe-custom-artwork\SKILL.md`.

## Which Adobe version
The tools work **only with Photoshop 2023 (v24) and Illustrator 2022 (v26)** (COM ProgIDs
`Photoshop.Application.170` and `Illustrator.Application.26`). Any other version (e.g. 2027, which asks
for a licence key) is never opened: before starting anything the connector reads which program the
COM entry would launch and checks its file version, then checks the running app's version again.
If the pinned version is missing, every tool answers "Install Adobe Photoshop 2023 …" (or Illustrator 2022) instead of opening another version.

Check without starting anything: `cli-anything-photoshop --json app check` / `cli-anything-illustrator --json app check`
(exit code 1 + install message if the pinned version is not there). `install.ps1` and the studio app both run this check; the
studio app also registers a missing MCP server itself when `cli-anything-*` is on PATH.

## How it works
`core/ops.py` holds one function per operation; each runs a small JSX body in the app via
`DoJavaScript`. The CLI (Click) and the MCP server (`mcp` SDK) both call those same functions.
Arguments are passed as JSON data, never pasted into code, so a path or text cannot inject script.

## Safety
- Saving/exporting refuses to overwrite an existing file unless `--overwrite` / `overwrite=true`.
- MCP servers only accept file paths under `--allowed-root` (`install.ps1` registers your user folder; to add
  another folder, `claude mcp remove <name> -s user` and add it again with a second `--allowed-root`).
- `script_run` (raw ExtendScript) is exposed to MCP only with `--allow-jsx`, which is **off** in the
  registered servers. The CLI keeps `script run` as a local escape hatch. Register a server with `--allow-jsx`
  to give MCP agents raw scripting (not path-limited).
- `doc close` discards unsaved changes unless `--save`.

## Develop / test
```powershell
cd adobe-connector                               # from the repo root, after install.ps1
.venv\Scripts\python.exe -m pip install pytest pillow     # test-only dependencies
.venv\Scripts\python.exe sync_shared.py          # after editing _shared/
# unit tests (no Adobe app needed):
.venv\Scripts\python.exe -m pytest tests photoshop\agent-harness\cli_anything\photoshop\tests\test_core.py illustrator\agent-harness\cli_anything\illustrator\tests\test_core.py
# everything, including E2E (opens both apps):
.venv\Scripts\python.exe -m pytest tests photoshop\agent-harness illustrator\agent-harness
.venv\Scripts\python.exe tests\mcp_smoke.py      # MCP over stdio, opens both apps
```
E2E tests open the real apps and write to `artifacts\e2e\`. Results: `*/agent-harness/cli_anything/*/tests/TEST.md`.
