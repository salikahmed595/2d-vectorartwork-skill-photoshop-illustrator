---
name: adobe-custom-artwork
description: Turns an image the user uploads into custom finished artwork by driving their real Photoshop and Illustrator together through the `photoshop` / `illustrator` MCP servers or the cli-anything CLIs - Select Subject cutouts, retouching (spot removal, skin smoothing, dodge & burn, sharpening), Image Trace to vector with colour/detail control, then posters, stickers, logos, thumbnails and PFP-style compositions delivered as layered PSD + AI/SVG + PNG. Use when the user says "I'll upload an image, make artwork from it", "use my Photoshop and Illustrator", "cut this out and put it on a poster", "vectorize my character", "retouch this photo", "make a sticker / logo / poster from this picture".
---

# Custom artwork from an uploaded image (Photoshop + Illustrator)

Claude does not paint pixels by hand. It **directs** the user's Photoshop and Illustrator: Photoshop's own
AI (Select Subject, Content-Aware Fill) plus filters, masks, adjustments, styles and text; Illustrator's
Image Trace, shapes, gradients, Pathfinder and type. Everything stays editable (layers, vectors).

Tools (same operations either way - see the `cli-anything-photoshop` and `cli-anything-illustrator` skills):
- MCP: `mcp__photoshop__*`, `mcp__illustrator__*`
- CLI: `cli-anything-photoshop --json ...`, `cli-anything-illustrator --json ...` (in `<repo>\adobe-connector\.venv\Scripts\`)

## 1. Intake
- Work folder: `%USERPROFILE%\Documents\Adobe-Work\<job>\` with `inbox\`, `work\`, `out\`.
- An image pasted into chat may have **no file path**. Ask the user to drop the file into
  `%USERPROFILE%\Documents\Adobe-Work\inbox\` (or give its path). Copy it into the job folder - never edit the original.
- Paths outside the `--allowed-root` folders (your user folder, as `install.ps1` registers them) are refused by the MCP servers (by design).

## 2. Look, then plan (before touching the apps)
Look at the image and write a short plan the user can correct:
- subject (person / character / product / logo), background (plain / busy), style (photo / illustration / flat).
- deliverable: size and format (e.g. poster 1080x1350, YouTube thumb 1280x720, PFP 2000x2000, sticker, logo).
- recipe from the table below, the colours, any text (exact words - ask; never invent names or slogans).
Ask only what changes the result (text, size, style). Otherwise pick sensible defaults and say so.

## 3. Recipes
| Goal | Steps |
|---|---|
| **Cut out** | PS `doc_open` -> `cutout` (layer=Background, mode=layer, name=Hero) -> hide Background -> `doc_export` PNG (transparent) |
| **Retouch photo** | `remove` spots `[[x,y,w,h]]` (Content-Aware, on a "Retouch" copy) -> `skin_smooth` areas (cheeks/forehead ellipses) -> `dodge_burn` strokes -> `sharpen` -> `adjust_add` curves/vibrance |
| **Poster / thumbnail** | PS `doc_new` -> `fill_layer_add` gradient -> soft glow (`fill` ellipse + gaussian-blur, screen) -> `place` Hero PNG -> `style_set` (outer glow / stroke) -> `text_add` + `style_set` drop shadow -> `adjust_add` curves on top |
| **Vector / flat art** | Cut out first -> IL `doc_new` -> `trace` Hero PNG (colors 4-12, noise 10-40, `snap_lines`) -> recolour with `item_set` / `item_gradient` -> `doc_save` .ai + `doc_export` .svg/.png |
| **Sticker** | vector or cutout -> PS `style_set` stroke `{"color":"#ffffff","size":18}` + drop shadow on a transparent doc |
| **Logo / badge** | IL shapes + `pathfinder` + `item_gradient` + `text_add`; optional traced silhouette (`trace` mode=bw, threshold) |
| **Split into parts** | `layer_from_box` for regions (face, prop), or the `layered-character-psd` skill for a full part split |

Ready-made pipeline: `<repo>\adobe-connector\examples\custom_artwork.ps1 -Image <path> -Title "<text>"`
(cutout -> Illustrator vector -> Photoshop poster; prints the output paths).

## 4. Review loop (mandatory)
After each stage: `doc_export` a PNG, **look at it**, fix what is wrong, then go on. Check: cutout edges
(missing props/hair? halo?), text spelling and contrast, nothing off-canvas, layer names meaningful.
Show the user the preview before final delivery when the brief was open-ended.

## 5. Deliver
`out\` gets: layered `.psd`, `.ai` + `.svg` when vectors were made, and a full-size `.png`
(plus `.jpg` for social if asked). Report the layer list and paths. Never overwrite a user file
(`overwrite` only for files you created in this job).

## Gotchas (observed while testing)
- Run `cutout` **once, on the original photo layer**. Running Select Subject again on an already
  cut-out layer dropped the crossbow from the hunter. Check `subjectBounds`; fix misses with `mask_add` / `layer_from_box`.
- `remove` works on a copy called "Retouch" - later retouch steps should target `layer="Retouch"`.
- Image Trace: give `colors` for flat art (it loads a limited-colour palette first); `noise` higher = fewer
  specks; result reports `trace.colors` / `trace.paths` - huge counts (thousands) mean "photo-like", lower them.
- Photoshop `place` may scale big images to fit the canvas; read the returned bounds and `layer_move` to position.
- Coordinates: Photoshop pixels, Illustrator points; both top-left origin, y down.
- If a call hangs, a dialog is open in the app - ask the user to close it.
- **Generative Fill / Firefly** (text-to-image) is *not* wired: it uses the user's Adobe credits.
  Ask before trying it; otherwise compose from the uploaded image + shapes, gradients, type.
- What this cannot do: hand-paint new detailed illustration from nothing. Say so plainly and offer
  the closest composable result (cutout + styling, vector restyle, layout, type).
