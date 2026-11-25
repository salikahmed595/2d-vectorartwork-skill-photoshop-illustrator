---
name: cli-anything-photoshop
description: Drive the user's real Adobe Photoshop (Windows) from an agent - create/open documents, add and edit pixel/text layers and groups, fill boxes and ellipses, apply filters, add layer masks, adjustment layers (curves, levels, hue/saturation...), solid/gradient fill layers and layer styles (drop shadow, stroke, glow, colour overlay), Select Subject cutouts, retouching (Content-Aware spot removal, skin smoothing, dodge & burn, high-pass sharpen), scale/rotate layers, place images, play Actions, save layered PSD and export PNG/JPG/TIF - through the `cli-anything-photoshop` CLI or the `photoshop` MCP server. Use whenever the user asks to make, edit, retouch, compose or export something in Photoshop.
---

# Photoshop via cli-anything-photoshop

Two ways in, same operations:
- **MCP** (Claude): tools `mcp__photoshop__*` - e.g. `doc_new`, `layer_list`, `fill`, `text_add`, `doc_export`.
- **CLI** (any agent / script): `<repo>\adobe-connector\.venv\Scripts\cli-anything-photoshop.exe` (`<repo>` = where you cloned this repository)
  Always pass `--json`; output is `{"ok": true, "result": ...}` or `{"ok": false, "error": "..."}` (exit code 1).

Units are **pixels**, origin **top-left**, y down. Paths must be **absolute**. Layers are found by
name or by group path `Group/Layer`. Commands act on the active document unless `--doc NAME` is given.

## Workflow
1. `app info` - is Photoshop up, what is open (first call launches Photoshop, ~45 s).
2. `doc new --width 1080 --height 1080 --name Post` or `doc open C:\path\file.psd`.
3. Build: `layer add`, `fill`, `text add`, `place`, `filter apply`, `layer group`, `layer set`.
4. Check: `layer list` (names, bounds, opacity) and `doc export C:\...\check.png`, then look at the PNG.
5. Save: `doc save C:\...\file.psd` (layered). `export` never changes the open document.
6. `doc close` discards unsaved changes unless `--save`. Never close a document the user opened
   themselves without asking.

## Commands
| Command | Notes |
|---|---|
| `app info` | version, open docs |
| `doc new --width --height [--resolution 72] [--name] [--background white\|transparent\|background]` | RGB |
| `doc open PATH` / `doc info` / `doc list` | |
| `doc save PATH.psd [--overwrite]` | refuses to overwrite by default |
| `doc export PATH.png\|.jpg\|.tif [--quality 0-12] [--overwrite]` | flattened copy |
| `doc resize --width [--height]` / `doc flatten` / `doc undo [--steps N]` / `doc close [--save]` | |
| `layer list` | top to bottom; bounds = [left, top, right, bottom] |
| `layer add NAME [--group G]` / `layer group NAME --layer A --layer B` | |
| `layer rename L NEW` / `layer delete L` / `layer duplicate L [--name]` / `layer select L` | |
| `layer set L [--visible/--hidden] [--opacity 0-100] [--blend multiply]` | |
| `layer move L --dx --dy` / `layer arrange L top\|bottom\|up\|down` | |
| `layer transform [L] [--scale % \| --width px \| --height px] [--rotate deg]` | about the centre, keeps aspect |
| `layer from-box NAME --x --y --w --h [--shape ellipse] [--feather] [--cut] [--layer L]` | region to its own layer |
| `text add "Text" --x --y [--size 48] [--color #hex] [--font ArialMT] [--name]` | x,y = baseline start |
| `text edit L [--content] [--size] [--color] [--font]` | |
| `fill #hex [--x --y --w --h] [--shape rect\|ellipse] [--layer L \| --new-layer NAME] [--feather px] [--opacity %]` | no box = whole layer; feather+opacity = soft paint |
| `filter list` / `filter apply NAME -p key=value [--layer L]` | gaussian-blur, motion-blur, sharpen, unsharp-mask, add-noise, desaturate, invert, brightness-contrast, auto-contrast, posterize |
| `place PATH [--x --y] [--name] [--rasterize]` | smart object layer; x,y = top-left of its **visible** pixels |
| `fill-layer solid --color #hex` / `fill-layer gradient --stop #a --stop "#b@60" --stop #c [--style linear\|radial] [--angle 90] [--name] [--above L]` | editable fill layers |
| `adjust list` / `adjust add KIND -p key=value [--name] [--clip] [--above L]` | brightness-contrast, hue-saturation, vibrance, curves (`-p "points=[[0,0],[128,150],[255,255]]"`), levels, black-white, invert |
| `mask add [L] [--x --y --w --h] [--shape rect\|ellipse] [--feather px] [--hide]` | box = only that area shows; replaces an existing mask |
| `mask delete [L] [--apply]` | |
| `style list` / `style set [L] --drop-shadow '{...}' --stroke '{"color":"#fff","size":4}' --outer-glow '{...}' --color-overlay '{...}'` | JSON options, `{}` = defaults; **replaces** the layer's styles |
| `style clear [L]` | |
| `cutout [L] [--mode mask\|layer] [--name] [--expand px] [--feather px]` | Select Subject (Photoshop AI); returns `subjectBounds`. Run once, on the original layer |
| `remove --spot "[x,y,w,h]" ... [--layer L] [--in-place] [--shape rect\|ellipse]` | Content-Aware Fill; works on a copy "Retouch" |
| `retouch skin --area "[x,y,w,h]" ... [--strength 60] [--radius 8]` | Surface Blur copy masked to ellipses |
| `retouch dodge-burn --stroke '{"x":..,"y":..,"w":..,"h":..,"mode":"dodge","strength":20}' ...` | 50% grey Overlay layer "Dodge & Burn" |
| `retouch sharpen [--layer L] [--radius 2] [--strength 100]` | High Pass, Overlay |
| `action play NAME --set SET` | recorded Actions |
| `script run --code "JSX"` / `--file x.jsx` | CLI-only escape hatch; last expression is returned |

`layer list` also reports `mask` (true/false) and `styles` (enabled effects) for every layer.
New adjustment/fill layers go directly above `--above` (or the active layer), never inside a group.

## Gotchas
- Fonts use PostScript names (`ArialMT`, `Arial-BoldMT`, `Montserrat-Bold`).
- `fill` and filters need a normal pixel layer, not text or a group.
- Opacity is reported as whole percent (Photoshop stores 255 steps).
- Placing a big image may be scaled to fit the canvas (Photoshop preference).
- If a call hangs, a dialog is probably open in Photoshop - ask the user to close it.
- MCP file paths are limited to the `--allowed-root` folders (`install.ps1` registers your user folder).
- Raw scripts (`script_run`) are **off** in the MCP server. The CLI still has `script run` for
  things no command covers; prefer the commands, and say when you fall back to a script.
- The CLI lives in the connector venv, `<repo>\adobe-connector\.venv\Scripts\`; add that folder to PATH to type just `cli-anything-photoshop`.
