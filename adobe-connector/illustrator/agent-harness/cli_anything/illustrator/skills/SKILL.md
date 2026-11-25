---
name: cli-anything-illustrator
description: Drive the user's real Adobe Illustrator (Windows) from an agent - create/open documents, draw rectangles, ellipses, stars, polygons, lines, straight or smooth paths and real Bezier curves from SVG path data, add text, edit/move/group/arrange items, linear/radial gradients, Pathfinder (unite, minus front, intersect, exclude, divide), symbols, manage layers, place and Image Trace pictures, play Actions, save .ai/.pdf and export PNG/JPG/SVG - through the `cli-anything-illustrator` CLI or the `illustrator` MCP server. Use whenever the user asks to make or edit vector art, logos, icons or layouts in Illustrator.
---

# Illustrator via cli-anything-illustrator

Two ways in, same operations:
- **MCP** (Claude): tools `mcp__illustrator__*` - e.g. `doc_new`, `shape`, `path_draw`, `path_svg`, `text_add`, `item_list`, `doc_export`.
- **CLI** (any agent / script): `<repo>\adobe-connector\.venv\Scripts\cli-anything-illustrator.exe` (`<repo>` = where you cloned this repository)
  Always pass `--json`; output is `{"ok": true, "result": ...}` or `{"ok": false, "error": "..."}` (exit code 1).

Units are **points** (72 pt = 1 in), origin = **top-left of the active artboard, y down** (same as
SVG). Bounds are `[left, top, right, bottom]`. Paths must be **absolute**.
**Name every item you create** (`--name`) - items are edited by name later.

## Workflow
1. `app info` (first call launches Illustrator).
2. `doc new --width 1000 --height 1000` or `doc open C:\path\file.ai`.
3. Draw: `shape`, `path-svg` (curves), `path`, `text add`, `place`, `trace image`. Organise: `layer add`, `item group`.
4. Check: `item list` and `doc export C:\...\check.png`, then look at the PNG.
5. Save: `doc save C:\...\file.ai` (editable). Export SVG/PNG for delivery.
6. `doc close` discards unsaved changes unless `--save`.

## Commands
| Command | Notes |
|---|---|
| `doc new [--width 612 --height 792] [--color-space rgb\|cmyk]` | named on first save |
| `doc open` / `doc info` / `doc list` / `doc undo [--steps]` / `doc close [--save]` | |
| `doc save PATH.ai\|.pdf [--overwrite]` | |
| `doc export PATH.png\|.jpg\|.svg [--scale 2] [--opaque] [--quality]` | active artboard |
| `shape rect\|rounded-rect\|ellipse\|polygon\|star\|line --x --y --w --h [--fill #hex\|none] [--stroke #hex] [--stroke-width] [--radius] [--sides] [--points] [--inner-ratio] [--name] [--layer]` | default: black fill, no stroke; line = stroke |
| `path-svg --d "M10 80 C40 10 65 10 95 80 Z" [--fill #hex] [--stroke] [--stroke-width] [--fill-rule evenodd\|nonzero] [--name]` | **real Bezier curves** from SVG path data (M L H V C S Q T A Z, absolute or relative, y down). Several `M` parts = one compound path; inner parts cut holes. Default: black fill, no stroke |
| `path --points "[[x,y],...]" [--closed] [--smooth] [--fill] [--stroke] [--stroke-width] [--name]` | straight segments; `--smooth` curves through the points; a point can be `{"x","y","in":[x,y],"out":[x,y]}` (own handles) or `{"x","y","corner":true}` (stays sharp) |
| `text add "Text" --x --y [--size 24] [--color] [--font ArialMT] [--name]` | x,y = top-left |
| `text edit ITEM [--content] [--size] [--color] [--font]` | |
| `item list [--layer L]` | name, type, bounds, fill/stroke |
| `item set ITEM [--fill] [--stroke] [--opacity] [--hidden] [--rename] [--x --y \| --dx --dy] [--rotate deg] [--scale 1.5] [--width] [--height]` | groups: colours every path inside |
| `item delete` / `item duplicate ITEM [--dx --dy --name]` / `item group A B [--name]` / `item arrange ITEM front\|back\|forward\|backward` | |
| `layer list` / `layer add NAME [--parent P]` / `layer rename` / `layer delete` / `layer select` / `layer arrange` | |
| `layer set L [--visible/--hidden] [--locked/--unlocked] [--opacity]` | |
| `place PATH [--x --y] [--width] [--embed] [--name]` | |
| `trace presets` / `trace image PATH [--preset "..."] [--width] [--no-expand] [--name]` | raster to vector paths |
| `trace image ... [--mode color\|gray\|bw] [--colors 2-30] [--noise 1-100] [--path-fidelity 0-100] [--corner-fidelity] [--threshold 1-255] [--method abutting\|overlapping] [--ignore-white] [--snap-lines] [--drop-background]` | options override the preset; result has `trace.paths/colors/droppedBackground` |
| `item gradient ITEM --stop #a --stop "#b@60" --stop #c [--kind linear\|radial] [--angle deg]` | paths, groups, compound paths, text |
| `pathfinder unite\|minus-front\|intersect\|exclude\|divide A B [...] [--name]` | replaces the inputs with the expanded result (single shapes come back ungrouped) |
| `symbol create ITEM NAME [--remove-original]` / `symbol list` / `symbol place NAME [--x --y] [--scale] [--name]` | reusable art |
| `action play NAME --set SET` / `script run --code "JSX"` | escape hatches (`script run` is CLI-only) |

## Gotchas
- Organic shapes (flames, feathers, hair, leaves, petals, swooshes, lettering) should be **curves**, not polygons:
  write them as SVG path data with `C`/`Q`/`A` and draw with `path-svg`, or give `path --smooth` a few points and mark
  sharp tips with `"corner": true`. Check the exported PNG: angular edges mean straight segments slipped in.
- You can't draw on a locked or hidden layer - the error says which; `layer select` another.
- Rotation is counter-clockwise in degrees.
- Text font = PostScript name; an unknown font gives "Font not found".
- If a call hangs, a dialog is probably open in Illustrator - ask the user to close it.
- MCP paths are limited to the `--allowed-root` folders (`install.ps1` registers your user folder). Raw scripts (`script_run`) are **off** in the
  MCP server; the CLI still has `script run` for anything no command covers.
- `minus-front`: the bottom item is cut by the ones above it (create the base shape first).
- Trace a **cut-out PNG** with `--drop-background` (else a white box comes along). Thousands of paths = photo-like;
  lower `--colors` / raise `--noise` for flat art. Thin details (strings, wires) may break up at low colour counts.
- The CLI lives in the connector venv, `<repo>\adobe-connector\.venv\Scripts\`; add that folder to PATH to type just `cli-anything-illustrator`.
