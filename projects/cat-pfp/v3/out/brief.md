# Cat PFP v3 - build record (2026-11-21)

## Brief
- Subject: the user's orange tabby (`inbox/cat-source.png`, 472x216), head tilted, green eyes, cream muzzle and chest.
- Rules: No AI image generation (drawn by Claude in Illustrator + Photoshop); one layer per character part.
- No title text was requested, so there is no titled master. Only the clean master exists.

## Lane and composition lock
- Lane: clean vector illustration, cel shading with soft gradients, night scene. Palette: navy/violet + orange; accent cyan rim and green eyes.
- Subject: head and shoulders, head at canvas centre (eye midpoint 1000,960), tilted 17.5° like the photo.
- Camera: eye level, close. Light: moon top right; cyan rim on the Cat group; warm face light.
- Depth: sky + stars (far), moon, clouds, two mountain ranges (mid), fireflies (front).
- Title zone: none.

## How it was made
- Landmarks (eyes, nose, ear tips, cheeks, body edge) were read off a grid of the photo (`work/src-grid.png`) and mapped
  photo -> canvas as X = 1000 + 6.9(x - 198.5), Y = 960 + 6.9(y - 71).
- `work/cat_design.py` writes `work/drawing.json` (13 layers, 193 path items). `ai_draw.py` drew it into
  `out/cat-pfp-drawn.ai`. Nothing was traced; everything is drawn with paths and gradients.
- There were 3 review passes (`work/preview1-3.png`). Pass 1 -> 2: the flat white chest slab became a narrower,
  warmer panel; the saw-tooth back fur was softened; the left ear was turned upright; the muzzle glow was reduced;
  the fireflies were moved off the cat. Pass 2 -> 3: the chest was narrowed further and given a gradient, and the
  chin was toned down.
- Photoshop: the layer PNGs from `ai_draw.py --export` were stacked by `work/build_psd.jsx`. Lighting was then added
  as separate layers.

## Layers (`out/cat-pfp-v3.psd`, top to bottom)
Final vibrance (vibrance +12), Vignette (multiply 22), Face light (screen 22),
Fireflies,
**Cat** group (stroke 2 px #c8f6ff + outer glow #7fe8ff) {Whiskers, Eyes, Nose & mouth, Head, Ears, Chest fur, Body},
**Background art** group {Mountains, Clouds, Moon, Stars, Sky}.
`out/cat-pfp-drawn.ai` has the same Cat / Background art / Fireflies layers. It has no PS lighting layers.
Not in frame, so there are no layers for them: legs, paws, tail.

## Checks run
- Layer PNG recomposite vs Illustrator artboard export: 0.010% of pixels differ by >15 levels. All of them are in the
  chin-shadow area, where a multiply item blends across layers.
- PSD flat export vs the approved flat check (`work/psd-flat.png`): identical (no differing pixels).
- Master PNG vs `_2000_clean.jpg`: max 25 levels, 0.33% of pixels >8 (JPEG compression).
- `qc.py` on `_2000_clean.jpg`: no fails, no warnings. Circle previews at 256/64 px were viewed, and the face reads at both.
- The saved `.ai` was reopened and its layers listed: all part layers are present.

## Honest limits
- This is constructed vector art, not painted brushwork. It does not reach the painted HANGMAN303 banner's
  level of fur detail.
- Parts drawn under other parts (ear bases under the head, body under the head) exist only as far as they were drawn.
  Large moves will show edges.
- Whiskers are their own layer and cross the body. The Cat group's rim stroke also outlines the whisker tips (kept thin).
- Hiding individual PSD layers was not separately tested. Each layer comes from its own per-layer export.

## Files
`out/cat-pfp-v3.psd`, `out/cat-pfp-drawn.ai`, `out/cat-pfp-v3_master.png`, `out/cat-pfp-v3_2000_clean.jpg`,
`out/cat-pfp-v3_1080.webp`, `out/parts/` (one PNG per layer + manifest.json), `out/qc/`.
