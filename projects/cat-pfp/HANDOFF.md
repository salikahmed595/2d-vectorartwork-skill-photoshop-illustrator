# 2D PFP - cat job handoff (continue in a new session)

Written 2026-11-21 at the end of the first session. Give this file to the new session first.

## Starter prompt for the new session
> Read `HANDOFF.md` in this folder. The `2d-pfp` skill is in `skill/2d-pfp` (install it to
> `C:\Users\salik\.claude\skills\2d-pfp` if it is not there). Continue the v3 cat redraw from
> "Next steps", following the No-AI rule and the one-layer-per-part rule.

## What is in this zip
```
HANDOFF.md                     this file
skill/2d-pfp/                  the skill, as updated in session 1
  SKILL.md                     No-AI rule, layered delivery rule, stage gates 1-10, commands
  references/                  layered-components.md, backends.md, style-dna.md, prompt-recipes.md
  scripts/                     ai_draw.py, split_parts.py, split_parts_raster.py, finish.py, qc.py
  assets/portfolio/            the quality-bar portfolio pieces
cat-pfp/
  inbox/cat-source.png         the user's orange tabby photo (472x216) - the only source image
  out/                         v1 deliverable (layered PSD + AI + SVG + exports + qc); out/brief.md = v1 build record
  work/                        v1 working files (scene generator, layer PNGs, parts.json)
```
Not included on purpose:
- `cat-pfp/v2/` - made with Stable Diffusion + Real-ESRGAN before the No-AI rule. **Rejected. Do not
  use or deliver it.** It is still on disk at `C:\Users\salik\Documents\Adobe-Work\cat-pfp\v2`
  (renaming it failed with "access denied", probably a locked file; delete it when unlocked).
- `cat-pfp/v3/` - created but empty (`v3\work`, nothing drawn yet).
- The raw chat transcript (28.7 MB jsonl) - this file summarises it.

**Restore paths:** the scripts and briefs assume the original locations:
`C:\Users\salik\.claude\skills\2d-pfp\` and `C:\Users\salik\Documents\Adobe-Work\cat-pfp\`.

## Standing rules from the user
1. **No AI image generation, ever** (added 2026-11-20). Everything is drawn by Claude inside
   **Adobe Photoshop and Adobe Illustrator**. No SD/ComfyUI/imagegen worker/hosted APIs/Firefly,
   no Generative Fill/Expand/Neural Filters, no AI upscalers. Pillow only for bookkeeping
   (resize, contact sheets, checks). Select Subject: ask once per job first. Image Trace of the
   user's own photo is allowed (say it is a trace).
2. **One layer per character component**: eyes, ears, whiskers ("moustache"), nose & mouth, head,
   body, chest fur, legs, hands, tail... each its own named layer inside one character group;
   scene and lighting on separate layers. Rim stroke/glow on the group.
3. Quality target: detailed, "human-like" illustration like the HANGMAN303 painted banner the user
   showed. Be honest: vector construction will not match painted brushwork stroke for stroke.
4. Global: never claim a test/export/check that was not run; no git commits/pushes without
   permission; no AI co-author trailers; keep the user's email private.

## Status
| Item | Status |
|---|---|
| v1 neon-vector cat PFP (Image Trace of the photo + vector eyes + vector night scene) | **Delivered**, qc.py: no fails/warnings |
| v1 split into one layer per part (Eyes, Nose & mouth, Ears, Head, Body) in PSD and AI | **Delivered**, recomposite diff 0.005% = PASS |
| Skill: layered delivery rule + `split_parts.py` / `split_parts_raster.py` | Done |
| Skill: No-AI rule, stage gates rewritten for drawing, `ai_draw.py` drawing tool | Done; `ai_draw.py` verified 2026-11-21 (draw, --preview, --export all worked first run) |
| v2 SD painted cat | **Rejected** (AI) |
| v3 cat redrawn by hand in Illustrator, every part a layer, + scene | **Delivered 2026-11-21** - see `v3/out/brief.md`; qc.py no fails/warnings |
| Skill reference clean-up (backends / prompt-recipes / layered-components) | Done 2026-11-21 |
| v4 painterly rebuild (user: v3 looked childish) - fur strokes, painted eyes, PS lighting/DOF | **Delivered 2026-11-21** - see `v4/out/brief.md` |
| New skill `2d-artwork-photoshop-illustrator` (copy of 2d-pfp + pro painter workflow) | Installed in `~/.claude/skills/2d-artwork-photoshop-illustrator` |

### v1 layer structure (`out/cat-pfp.psd`, top to bottom)
Final vibrance, Final contrast, Vignette (multiply 38), Bloom (screen 26), Fireflies (outer glow),
Foreground, Ground shade, **Cat** group (pale-cyan stroke + cyan outer glow) {Eyes, Nose & mouth,
Ears, Head, Body}, Horizon haze, Moon glow, **Background art** group {Mountains, Clouds, Moon,
Meteors, Sparkles, Stars, Sky}, Background.
`out/cat-pfp.ai` has the same structure as Illustrator layers.

## Next steps (v3)
1. Write `v3\work\cat_design.py` - generates `drawing.json` for `ai_draw.py` (design below).
2. In Illustrator: new 2000x2000 doc, save as `v3\out\cat-pfp-drawn.ai` (the spec finds the doc by
   name `cat-pfp-drawn.ai`).
3. `cd C:\Users\salik\.claude\skills\2d-pfp\scripts` and run
   `python ai_draw.py <v3>\work\drawing.json --preview <v3>\work\preview1.png`. Fix ExtendScript
   errors (the tool is untested).
4. At least 3 review passes against `inbox/cat-source.png`: eyes, silhouette, stripes, proportions.
5. Add the scene: reuse v1's vector scene (`work/build_scene.py` -> `work/scene.svg`; Claude-made
   vector, not AI) or draw Background/{Sky, Stars, Moon, Clouds, Mountains}, Foreground, Fireflies.
6. `ai_draw.py ... --export v3\work\layers`, assemble the layered PSD in Photoshop
   (Cat group {Body, Chest fur, Ears, Head, Nose & mouth, Eyes, Whiskers} + scene + lighting).
7. Export master / `_2000_clean.jpg` / `_1080.webp`, run `qc.py`, write `v3\out\brief.md`.
8. Skill clean-up still owed:
   - `references/backends.md`: mark Routes A/B/C and the imagegen worker as **forbidden**.
   - `references/prompt-recipes.md`: mark obsolete (AI prompting) or replace with drawing recipes.
   - `references/layered-components.md`: drop the "raster renders from an image backend / NOT
     VERIFIED / layered-character-psd" wording; document `ai_draw.py` and `split_parts_raster.py`.

### Planned v3 cat design (for `cat_design.py`)
- Doc `cat-pfp-drawn.ai`; head transform `{"scale":1.0,"rotate":-14,"translate":[1095,960]}`
  (head parts in local coords around 0,0; rotate is degrees, clockwise +).
- Colours: INK `#4a1d07`, CREAM `#fff1d6`, CREAM_HI `#fff8ea`, STRIPE `#c2551a`,
  STRIPE_DK `#8f3a10`; eye greens `#f0ffa8 #a6e64e #3fa83e #1c7434`; lids `#2b1206`.
- Helpers: `ell(cx,cy,rx,ry)` Bezier ellipse (K=0.5523); `crescent(x0,y0,x1,y1,bend,width)`
  tapered Q-curve stripe; `taper(p0,c1,c2,p3,half)` tapered whisker polygon; `lin(angle,*stops)`,
  `rad(*stops)` gradient fills.
- Layers, bottom to top:
  - **Cat/Body** - clip `M 790 1150 C 640 1230 430 1310 290 1440 C 150 1575 60 1760 -30 1990
    L -30 2060 L 1660 2060 L 1650 1950 C 1630 1680 1570 1380 1430 1140 Z`, ink outline 7;
    gradient `#9a3d10 -> #d96f1a -> #f08d28 -> #f9aa42`, back shade (multiply 35), 7 back stripes,
    shoulder light (screen 35), head shadow (multiply 55).
  - **Cat/Chest fur** - zig-zag fur edge from (930,1270) to (1648,2060); cream gradient -90,
    chin shadow (multiply 60), 6 fur tufts.
  - **Cat/Ears** (head coords) - Ear L / Ear R, ink stroke 7, pink inner gradients, 3 cream tufts each.
  - **Cat/Head** (head coords, clip with jagged cheek fur, outline 7) - orange base gradient,
    side shade, lower-face light, cream muzzle ellipse, brow lights, 5 forehead + 4 cheek stripes,
    top light (screen 70).
  - **Cat/Nose & mouth** - chin, whisker pads L/R, pink-gradient nose (ink stroke 3), shine,
    mouth lines (ink 5), 8 whisker dots.
  - **Cat/Eyes** - almond lids, radial green irises, lid shadow (multiply 55), slit pupils
    `ell(-130,-6,15,40)` and `ell(162,-4,12,36)`, glints.
  - **Cat/Whiskers** - 6 whiskers + 4 brow hairs, `taper` polygons in `#fffaf0`.

## `ai_draw.py` spec format (what `drawing.json` must look like)
```json
{"doc": "cat-pfp-drawn.ai",
 "layers": [
  {"layer": "Cat/Eyes", "clear": true,
   "transform": {"scale": 1, "rotate": -14, "translate": [1095, 960]},
   "clip": "M ... Z",
   "outline": {"stroke": "#4a1d07", "width": 7},
   "items": [{"name": "Iris L", "d": "M ... Z",
              "fill": {"type": "radial", "stops": [["#f0ffa8", 0, 100], ["#1c7434", 100, 100]]},
              "stroke": null, "stroke_width": 0, "opacity": 100, "blend": "multiply", "blur": 0}]}
 ]}
```
- `d` supports M L H V C S Q Z (absolute and relative), one sub-path per item. Coordinates are
  canvas px, y down.
- Fill is a hex colour, a gradient object (`linear` with `angle`, or `radial`), or null.
- Usage: `python ai_draw.py drawing.json [--export dir] [--preview p.png] [--only "Cat/Eyes" ...]`.
  Run it from the `scripts` folder: it imports `split_parts`.

## Tool notes learned the hard way
- Photoshop 25.12.0 and Illustrator 28.7.1. The `cli-anything-photoshop --json` /
  `cli-anything-illustrator --json` CLIs are more reliable than the MCP. ExtendScript runs via
  `script run --file x.jsx`.
- Never call Adobe MCP tools in parallel ("CoInitialize has not been called"). The MCP can
  disconnect mid-job; switch to the CLI when that happens.
- Photoshop CLI quirks:
  - `layer group` reverses the order of the layers. Fix with `layer arrange <path> top`, starting
    from the bottom part.
  - `place` and `fill --new-layer` land on top of the stack.
  - `style set` works on groups.
  - Name the scene group `Background art`, because `Background` is taken.
- Select Subject: `mode=layer` returned a rectangle; `mode=mask` worked.
- Illustrator: `doc export x.svg` renames the open document. Save the .ai first, export the SVG
  last, then reopen the .ai.
- `qc.py` takes only an image path (no `--help`); it writes `qc/` next to the image.
- A local hook ("Fact-Forcing Gate") blocks the first Write/Edit/PowerShell of each new file or
  session. State the facts it asks for and retry.

| 2026-11-21 | v5 delivered | Full anime cel-shaded redraw, "Moonlit Cat Mage". Built from Illustrator paths (`v5/work/v5_design.py`) plus Photoshop light (`v5/work/render_psd.jsx`). Outputs are in `v5/out/`: PSD (39 layers), AI, master, 2000 jpg, 1080 webp, parts, qc, brief. The Adobe cloud connector (signed-in account) uploaded the master to CC `cat-pfp/` and made a non-generative tone variant, `cat-pfp-v5_connector-grade.png`. No AI generation. |
| 2026-11-21 | Skill merged | The user's `2d-vector-salik` SKILL.md is merged into `~/.claude/skills/2d-artwork-photoshop-illustrator` (any subject, capability check, routes, blueprint, gates, output contract). New references: adobe-capability-map, defaults-and-deliverables, style-and-material-playbook. The old SKILL.md is backed up in the session scratchpad. |
| 2026-11-21 | v6 delivered | Refine pass with `universal-2d-vector-art-studio` (full 12-point audit). Fixed P0 arm attachment (new Upper arm / Cloak trim / forearm layers), P1 neck join (Neck ruff layer), cloak light direction, ring and moon values; redrew particles, rune glyphs, wisteria, mid trees, castles. Report: `v6/out/revision-report.md`. Specs: `v6/work/v6_design.py` and `scene_v6.py`; PS script `v6/work/render_psd_v6.jsx`. Outputs in `v6/out/`: AI, SVG, PSD (41 layers), master, 2000 jpg, 1080 webp, parts (21), qc. Master uploaded to CC `cat-pfp/`. No AI generation; Openverse not used (stock raster is not allowed as drawn art). |
| 2026-11-21 | v7 delivered | Redraw with `2d-vector-salik` (user's skill v3.0, 18-point audit). Fixed P1 ears-to-skull join and P1 blurred background (all background blurs removed; vector Mist layer); face volume, eye depth, designed star classes, detailed moon, pea-flower wisteria, cape fold cores + trim bevel. Report: `v7/out/revision-report.md`. Specs: `v7/work/v7_design.py`, `scene_v7.py`, `scene_v7_bg.py`; PS script `v7/work/render_psd_v7.jsx`. Outputs in `v7/out/`: AI, SVG, PSD (41 layers), master, 2000 jpg, 1080 webp, parts (22), qc. Master uploaded to CC `cat-pfp/`. Photoshop scratch disk: C: has ~3 GB free; close old docs before big scripts. No AI generation. |
