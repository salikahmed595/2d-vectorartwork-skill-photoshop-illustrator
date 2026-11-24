# Adobe capability map (checked 2026-11-21)

| Need | Tool that does it | Notes |
|---|---|---|
| New PS doc, layers, groups, masks, fills, filters, blend modes, PSD save | `cli-anything-photoshop` (ExtendScript via `script run`), `photoshop` MCP | Full control of the user's Photoshop 25.12 |
| New AI doc, Bezier paths, gradients, clipping, live blur, layers, export | `cli-anything-illustrator`, `scripts/ai_draw.py`, `illustrator` MCP | Full control of Illustrator 28.7 |
| Brush strokes with a tablet | none | Simulated with tapered filled paths / thousands of strand shapes |
| Cloud: tone and colour adjustments | `image_apply_adjustments`, `image_apply_auto_tone` | Non-generative; works on an uploaded PNG |
| Cloud: grain, noise, blur, halftone, tint, colour overlay | `image_apply_effects` | Non-generative |
| Cloud: lens blur / depth blur | `image_apply_lens_blur` | Non-generative |
| Cloud: raster to SVG | `image_vectorize` | Trace; label as trace |
| Cloud: select subject / remove background | `image_select_subject`, `image_remove_background` | ML selection: ask the user once per job |
| Cloud: fonts | `font_search`, `font_recommend`, `font_preview` | For titles |
| Cloud: upload | `asset_initialize_file_upload` -> PUT blocks -> `asset_finalize_file_upload` | Local paths are not readable by the connector |
| Cloud: show result | `asset_preview_file` | |
| Cloud: Express layout from HTML | `export_html_to_express` | Needs an `auth` account |
| Generative (Firefly, Generative Expand, text-to-image) | FORBIDDEN by the No-AI rule | The connector itself says most generation is unavailable |

Order: `adobe_mandatory_init` -> `get_account_type` -> work. Never run Adobe calls in parallel.
