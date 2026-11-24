---
name: 2d-pfp
description: Produces premium 2D profile-picture (PFP) illustrations in the Quixotic portfolio style - a single hero character or duo, cinematic themed background, rim-lit glow, optional username title - from brief to finished 2000x2000 master. Use for any "2D PFP", avatar, Discord/Twitch/Kick/YouTube profile picture, gamer or streamer logo-portrait, couple PFP, or "make it like my portfolio" request. No AI image generation: Claude draws the artwork itself inside Adobe Illustrator and Photoshop. Covers style selection, drawing the character part by part, splitting the character into one editable layer per part (eyes, ears, hands, legs...) in layered PSD/AI, title lettering, finishing and QC. Rig-ready VTuber art belongs to vtuber-master; animated PFPs to motion-graphics-production.
---

# 2D PFP - portfolio-grade profile pictures

## What this skill makes
One square illustration that reads at 64 px and holds up at 2000 px: a hero character (or duo), a themed
world behind them, strong colour script, glow, and optionally the client's username as a designed title.
The quality target is the nine pieces in `assets/portfolio/` - open them before every job. They are the
bar for finish, not templates to copy.

## No-AI rule (user, 2026-11-20) - overrides anything else in this skill
The picture is made by Claude **inside Adobe Photoshop and Adobe Illustrator only**. AI must not
generate any part of the image.

Never use, for the artwork or as a base, reference or trace source:
- text-to-image or image-to-image generators (Stable Diffusion, ComfyUI, the local `imagegen` worker,
  hosted image APIs, Adobe Firefly);
- Photoshop Generative Fill / Generative Expand / Neural Filters, or any "AI repaint";
- AI upscalers (Real-ESRGAN and similar).

Allowed:
- Illustrator: paths, shapes, gradients, clipping masks, type - drawn by Claude with
  `scripts/ai_draw.py` or the Illustrator tools - and Image Trace of the **user's own** photo or art;
- Photoshop: layers, masks, fills, gradients, filters, adjustments, layer styles, text,
  Content-Aware Fill;
- Pillow only for bookkeeping (resizing exports, contact sheets, checks) - never to draw the art.

Select Subject is machine-learning selection, not generation: ask the user once per job before using
it; a vector silhouette or a drawn path needs no permission.

If a request cannot be met without AI generation (for example a fully painted multi-character scene),
say so plainly, deliver the closest result that can be drawn, and do not quietly generate.

## Honest capability rule
What Claude draws is clean vector illustration: constructed shapes, gradients, cel shading, glow. It
is not hand-painted brushwork and will not match a painted reference stroke for stroke - say this in
the hand-off instead of overselling. Never claim an image was drawn, exported or checked unless the
file exists and you looked at it.

**Photo trace route.** When the user supplies their own photo or art, it may be cut out and Image
Traced (see the `adobe-custom-artwork` skill). Say plainly that it is a trace of their image.

## Layered delivery rule (user, 2026-11-20)
Every piece ships as an editable layered file with **one layer per character component**: eyes one
layer, ears one layer, legs one layer, hands one layer, and likewise for every other visible part
(head, body, nose & mouth, hair, tail, props...), plus separate layers for scene elements and
lighting. A flat master alone is not a finished delivery. Details, layer lists per character type,
the split method and its checks: `references/layered-components.md`.

## Stage gates
1. **Brief.** Capture: username/title text (exact spelling and case), subject (who, species, outfit,
   props), mood, palette, platform, title yes/no, references. Ask only for what blocks the work; state
   assumptions for the rest.
2. **Style pick.** Choose one lane from `references/style-dna.md` (cozy fantasy anime, pixel cyberpunk,
   storybook duo, neon vector, flaming comic, kawaii space, mecha close-up, split-world, semi-real
   couple). One lane per piece - mixing lanes is the commonest cause of a cheap look.
3. **Composition lock.** Write five lines before prompting: subject scale and pose, camera, light
   source and rim colour, background depth layers (fore/mid/far), title zone. Rules in
   `references/style-dna.md` -> Composition.
4. **Draw.** Build the character and the scene in Illustrator with `scripts/ai_draw.py`: one spec
   file, every part on its own layer from the start (body, head, ears, eyes, nose & mouth, whiskers,
   hands, legs...). Take proportions and pose from the user's photo or reference by reading positions
   off a grid; do not trace or copy AI output. Work at the 2000x2000 artboard, so nothing is upscaled.
5. **Review and repair.** Export a PNG after every drawing pass and look at it. At least three passes.
   Fix on: eye asymmetry, lumpy silhouette, parts not meeting, stripes or shading spilling outside
   their part, muddy values, subject cut by the circle crop. Change the spec and redraw the layer;
   never patch with generated pixels. Titles are added in step 8.
6. **Export layers.** `ai_draw.py --export <dir>` writes one PNG per layer plus `manifest.json`.
7. **Layer check.** Parts drawn with `ai_draw.py` are already separate - confirm the layer list
   (`references/layered-components.md`). Only when the character came from Image Trace or a flat
   image, split it: `python scripts/split_parts.py parts.json` (vector) or
   `python scripts/split_parts_raster.py parts.json` (raster); both must print PASS.
   Only make layers for parts that are in frame; list the ones that are not.
8. **Finish.** Preferred: in Photoshop on the layered file, as separate named layers (glow, haze,
   shade, bloom, vignette, grade, title), rim stroke/glow on the character group. Fallback for a
   flat base when Adobe is unavailable: `python scripts/finish.py` - grade, bloom, vignette, optional chromatic split or grain,
   then the title in the preset that matches the lane (`neon`, `fire`, `fantasy`, `impact`).
9. **QC.** Diff the layered file's flat export against the approved image, then `python scripts/qc.py` - size, sharpness, exposure, and circle-crop previews at 256/64 px.
   Read the previews: face and title must survive the 64 px circle.
10. **Deliver.** See Deliverables. Include the layer list. Report status honestly: what was generated, what was checked, what
   still needs a human eye.

## Commands
```
python scripts/finish.py base.png --out out/name --title "USERNAME" --preset neon
python scripts/finish.py base.png --out out/name --preset fantasy --title "name" --font "<fonts-folder>\Abrade-Bold.ttf" --title-y 0.17
python scripts/qc.py out/name_2000.jpg
python scripts/ai_draw.py work/drawing.json --export work/layers   # draw the spec in Illustrator, export every layer
python scripts/split_parts.py work/parts.json     # traced vector character -> one layer per part + proof
python scripts/split_parts_raster.py work/parts.json   # flat raster character -> one PNG per part + proof
```
`split_parts.py` needs Illustrator running with the document open and `cli-anything-illustrator` on PATH.
`finish.py --help` lists every control (bloom, vignette, saturation, chroma, grain, title size, tracking,
position). Both scripts need only Pillow.

## Deliverables
```
output/<client-or-username>/
  brief.md                 # brief, lane, composition lock, final prompt + seed/settings
  candidates/              # every generated candidate, untouched
  <name>_2000.jpg          # master with title
  <name>_2000_clean.jpg    # master without title
  <name>_1080.webp         # platform export
  <name>.psd               # layered: character group with one layer per part, scene, lighting
  <name>.ai / .svg         # when vectors were made: same part layers as the PSD
  parts/                   # one PNG per layer, parts.json, manifest.json, _parts_sheet.png
  qc/                      # circle previews + qc.json
```

## Quality bar (reject if any fails)
- Silhouette reads as one clear shape at 64 px; face or mask is the brightest, sharpest area.
- Palette is two dominant hues plus one accent; glow colour equals the accent.
- Background has three depth layers and is darker/softer than the subject.
- Rim light or glow separates subject from background on at least one side.
- Title: spelled exactly, inside the top or bottom 22%, not touching the face, legible at 256 px.
- No extra fingers, fused props, stray watermarks, signature scribbles or AI text.
- Subject's head and key features sit inside the central circle (platforms crop to a circle).
- Layered file: every visible character part is its own named layer inside one character group;
  hiding a part layer removes that part and nothing else; the flat export matches the approved image.

## Rights
Many requests reference existing characters or game logos. Fan-style commissions are the client's call,
but flag it in the hand-off when a piece uses a recognisable third-party character, logo or wordmark,
and never reproduce a specific artist's signature or watermark.
