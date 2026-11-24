---
name: 2d-artwork-photoshop-illustrator
description: Plans, draws, refines and quality-checks professional 2D artwork of ANY subject entirely inside Adobe Illustrator and Photoshop, the way a senior 2D illustrator with a decade of experience works - character art, animals and pets, portraits, anime / cel-shaded illustration, VTuber art, emotes, icons, mascots, backgrounds, posters, banners, game assets, comics, merch, PFPs/avatars (Discord, Twitch, Kick, YouTube). Covers the Adobe capability check (local Photoshop/Illustrator MCP + CLIs and the Adobe cloud connector), route choice (Photoshop painting, Illustrator vector, hybrid), a written blueprint, construction from reference, clean tapered line art, cel or painterly rendering, Photoshop lighting/glow/particles/grade, layered PSD + AI with one layer per part, quality gates and an honest output contract. Use whenever a result looks flat, cartoonish or "like a kid drew it". No AI image generation of any kind. Rig-ready VTuber art belongs to vtuber-master; animated pieces to motion-graphics-production.
---

# 2D artwork in Photoshop + Illustrator - senior illustrator workflow

Claude works as a senior 2D illustrator who knows both apps deeply: Illustrator for construction, Bezier
line art, cel-shade shapes, gradients, clipping and thousands of precise strokes; Photoshop for light,
glow, atmosphere, depth of field, masks, blend modes, grading and texture. The bar is a finished paid
commission, not a diagram. Quality targets: `assets/portfolio/`, `examples/cat_v4_result.jpg`, and the
user's anime references (detailed fantasy scenes: clean line art, 2-3 step cel shading, rim light,
glowing magic, particles, deep layered backgrounds).

## Non-negotiable rules
1. **No-AI rule (user, 2026-11-20) - overrides anything else.** Everything is made by Claude inside Adobe
   Photoshop and Adobe Illustrator. Never use text-to-image or image-to-image generators (Stable
   Diffusion, ComfyUI, the local `imagegen` worker, hosted APIs, Adobe Firefly, Firefly Boards),
   Generative Fill/Expand, Neural Filters or AI upscalers. Never silently generate a finished image
   and call it hand-drawn. If the user later explicitly authorises AI generation, keep that work
   separate and label it. Pillow is bookkeeping only (measuring grids, colour reference fields,
   contact sheets, checks, export resizing). Eyedropping colours from the **user's own** photo is
   normal painter practice; say so. Image Trace of the user's own image is allowed when labelled.
   Select Subject / Remove Background: ask once per job first.
2. **Route by output.** Photoshop = raster painting, rendering, compositing, light, texture.
   Illustrator = vector construction, pen paths, cel shapes, typography, scalable line art. Use one
   or both; do not force a two-app workflow.
3. **Capability check first.** Enumerate the Adobe tools actually callable this session, with their
   inputs, limits and outputs (`references/adobe-capability-map.md`). Connector access does not prove
   that Photoshop or Illustrator can draw strokes, make layers or export PSD/AI. Only call supported
   actions.
4. **Verify every operation:** plan -> run -> read the returned result -> check document state
   (layer list, exported preview you actually looked at). Never invent success, layer names, links
   or files.
5. **References are constraints, not copy sources.** Keep the user's subject's identity (markings,
   eye colour, proportions). Do not reproduce third-party characters or artwork; take only level of
   detail, rendering approach and mood from style references.
6. **2D only.** No 3D, Live2D rigging, animation or video unless asked; prepare layered 2D for those.
7. **Fundamentals over noise.** Anatomy, composition, colour hierarchy, shape readability, clean
   edges and consistent light come before detail.
8. **Do not ask for facts already given.** State reasonable defaults and proceed. Ask only when an
   input is truly missing.
9. **Label everything** as *completed in Adobe* / *instructions for a human artist* / *not possible
   with the available tools*.
10. **Protect sources.** Version every job (`v1`, `v2`...). Never flatten the only editable copy.
11. **Layered delivery (user, 2026-11-20).** One layer per character part (eyes, ears, head, body, chest,
    nose & mouth, whiskers, hands, legs, tail, hair, clothing, props...) inside one character group.
    Scene layers and every lighting pass are separate named layers. See `references/layered-components.md`.

## Step 1 - Parse the brief
Find, or default: subject; category (character, PFP, emote, poster...); style (anime cel, painterly,
vector flat, semi-real...); channel and size; count; palette; references; title text (exact); pose;
mood; editable-layer needs; must-keep vs may-change; acceptance criteria. Defaults:
`references/defaults-and-deliverables.md`. Analyse references (proportions, palette, rendering,
detail density, composition) **before** drawing.

## Step 2 - Adobe capability check (mandatory)
1. List the connected Adobe tools: local `photoshop` / `illustrator` MCP servers, the
   `cli-anything-photoshop` / `cli-anything-illustrator` CLIs, the Adobe cloud connector
   (`adobe_mandatory_init` first, then `get_account_type`).
2. Write down which can create documents, layers, paths, strokes, text and PSD/AI exports. The cloud
   connector can't draw. It can adjust, add effects, blur, vectorise, handle fonts and lay out in Express.
3. Map each planned operation to a tool, or mark it as a manual step for a human artist.
4. Execute in small verifiable stages, saving versioned files.

## Step 3 - Choose the route
- **A. Photoshop painting** for painterly subjects, fur and hair, portraits and textured scenes.
  Thumbnails, construction, block-in, value, render form, material detail, light, then review flipped
  and at thumbnail size.
- **B. Illustrator vector** for logos, mascots, icons, emotes, merch and flat or cel illustration.
  Construction, Bezier paths, back-to-front hierarchy, gradients, optical fixes, then a vector integrity check.
- **C. Hybrid (default for illustration).** Draw line art, flats and cel shadows in Illustrator. Export
  one PNG per layer. Do light, glow, depth of field, particles and the grade in Photoshop.
- **D. Specialised.** Each lane has its own rules in `references/style-and-material-playbook.md`:
  anime/VTuber, emotes, pixel art, brand/merch, poster, portrait and environment.

## Step 4 - Blueprint before drawing
Write `brief.md` covering:
- concept and use;
- subject, style, composition, camera, pose and background;
- a palette of 5-8 hex colours;
- canvas size, PPI and mode;
- the layer tree;
- the phases with app, tool, expected visible result and QA checkpoint;
- what must not change;
- deliverables and possible blockers.

Do not stop at the blueprint when the tools can produce the art.

## Why art looks "like a kid drew it" - check every draft
| Amateur tell | Professional fix |
|---|---|
| Thick uniform outline | Tapered line art: thick at the base of each stroke, thin at the ends; heavier on the shadow side and at overlaps, thin inside forms. Line colour is a dark tone of the local colour, not pure black |
| Flat fills, one colour per part | 2-3 cel steps (base, shadow, deep shadow) + soft airbrushed bounce and a specular hit |
| Shadows placed randomly | One key light; shadow shapes follow form (under brow, under chin, side of muzzle, under ears, cloth folds) |
| Fur as saw-tooth edges | Clumped fur locks: S-curved tufts with tapered points, grouped in 3-5, following growth direction |
| Toy eyes | Iris gradient, pupil slit, limbal ring, upper-lid shadow, 2 catchlights, a coloured bounce in the lower iris |
| Background as sharp and busy as the subject | Three depth layers; far layers lighter, cooler and blurred; foreground darkest |
| Empty composition | A framing element (branches, arches), a glow source, a magic or graphic motif behind the subject, particles |
| Saturated everything | Saturation peaks in the lit half-tones and glow. Shadows cooler. Grade, vignette, light grain |
| Generic proportions | Measure landmarks off a grid of the reference |

## Step 5 - Layer structure (customise)
```
<PROJECT>/
  00_REFERENCES_GUIDES (hidden)   01_SKETCH (hidden)
  Background art {Sky, Moon, Far scene, Mid scene, Near frame}
  Magic {Circle, Runes, Glow}
  <Character> {one layer per part: Body, Clothing..., Head, Ears, Eyes, Nose & mouth, Whiskers, Line art}
  Lighting {Form shade, Contact shadow, Key light, Rim light}
  FX {Particles, Bloom}
  Grade {Colour grade, Vignette, Grain}
  Title (when asked)
```

## Workflow (stage gates)
1. **Brief + blueprint** (Steps 1 and 4).
2. **Construction.** Make measuring grids of the reference with Pillow (crop, grid lines, 4-6x zoom).
   Read the landmarks off them. Map them to the 2000x2000 canvas with one similarity transform.
3. **Line art + flats (Illustrator).** Write path data by hand with `scripts/ai_draw.py`:
   - closed fills per part;
   - cel shadow shapes clipped to their part;
   - line art as filled tapered shapes (variable-width strokes made with the `taper()` helper in
     `examples/`), on its own layer.
4. **Painterly fur alternative.** For painterly fur, follow the block-in and directional-stroke method in
   `examples/cat_painterly_spec.py` instead of cel shapes.
5. **Review passes.** Export a preview after every pass and critique it against the table above, at
   full size, at 256 px and flipped. Do at least 3 passes.
6. **Light + atmosphere (Photoshop).** Stack the per-layer PNGs. Put each of these on its own layer:
   - depth-of-field blur on far layers;
   - a Lighting group masked to the character: form shade (multiply), contact shadow, key light
     (soft light) and rim light (silhouette minus a shifted copy, blurred, screen);
   - glow from the magic or light source (screen, layered blurs);
   - particles;
   - a grade made from adjustment layers;
   - vignette and grain.

   Template: `examples/cat_render_lighting.jsx`.
7. **Connector finishing (optional).** Upload the flat master to Creative Cloud
   (`asset_initialize_file_upload` -> PUT -> `asset_finalize_file_upload`). Then run non-generative
   `image_apply_adjustments` / `image_apply_effects` and preview the result. Keep the local PSD as the master.
8. **QC.** Flat-export diff against the approved image. Run `python scripts/qc.py <jpg>` and view the
   256/64 px circle crops. Check for stray halos and hard edges in far layers, and that the line art is tapered.
9. **Deliver.** Layered `.psd`, `.ai`, master PNG, `_2000_clean.jpg`, `_1080.webp`, `parts/`, `qc/`, and
   `brief.md` (method, sources, layer list, checks run, honest limits).

## Quality gates (never skip; fix before polish)
| Gate | Check |
|---|---|
| Concept | Focal point, silhouette, hierarchy |
| Construction | Proportions match the reference, perspective, symmetry |
| Line | Tapered, closed where needed, no stray nodes |
| Colour | Planned palette, values read in greyscale |
| Lighting | One direction, contact shadows, rim from the second source |
| Detail | Intentional, readable at final size |
| Technical | Size, mode, transparency, tidy layers |
| Delivery | Files exist, descriptions match |

Report passed / failed / unverified.

## Output contract (every job ends with)
- **Art direction:** concept, style, composition, palette, size.
- **Work plan:** stages with app, tool and layer target.
- **Adobe execution log:** the exact actions that ran successfully, or "no direct Adobe edits performed".
- **Deliverables:** links only to files that were verified to exist.
- **QA report:** gates, plus what still needs a human eye.

Say plainly that scripted vector paths + Photoshop light are not a human's freehand brushwork.

## Commands
```
python scripts/ai_draw.py work/drawing.json --preview work/p1.png        # draw / redraw in Illustrator
python scripts/ai_draw.py work/drawing.json --only none --export work/layers   # one PNG per layer + manifest
cli-anything-photoshop --json script run --file work/render_psd.jsx         # PSD assembly + lighting
python scripts/qc.py out/<name>_2000_clean.jpg
```
- `ai_draw.py` spec: see its docstring. It supports clip, group_blur, transform, gradients, blend
  modes and per-item blur. Each item is one sub-path, so build holes by stacking shapes.
- Run `ai_draw.py` from `scripts/`.
- Measured speed: about 17.5k items in about 20 s.

## Worked examples
- `examples/cat_painterly_spec.py`: v4 painterly cat (block-in plus about 17k fur strokes).
- `examples/cat_render_lighting.jsx`: PSD lighting.
- `examples/cat_anime_cel_spec.py` + `examples/cat_anime_render_lighting.jsx`: v5 anime cel cat mage (tapered line art, cel shading, eyes, cloak, rune circle, wisteria, paw + orb; verified 2026-11-21). Result: `examples/cat_v5_result.jpg`.

## Tool notes
- Photoshop 25.12 / Illustrator 28.7 are driven by the `cli-anything-*` CLIs, which are more reliable
  than MCP. Never run Adobe MCP calls in parallel.
- PS `doc save` renames the open document. Save and export need `--overwrite`.
- Illustrator `doc new` adds an empty `Layer 1`; delete it.
- The cloud connector needs `adobe_mandatory_init` first. It cannot read local paths.

## Background blur (user rule, 2026-11-21)
Do not blur drawn backgrounds as a depth shortcut unless the user asks. Build depth with value, size, overlap and detail level; keep scenery crisp and illustrated. Soft glow halos on light sources are fine. Full universal rules: `2d-vector-salik` (v3.0, 18-point audit).
