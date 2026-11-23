# Cat PFP v4 - painterly rebuild (2026-11-21)

Why v4: the user judged v3 "like a kid drew it". v3 had a thick outline, flat fills, saw-tooth fur,
blob stripes, toy eyes and a sharp background. v4 is rebuilt with a professional painter's workflow,
still with no AI generation.

## Method
1. **Construction.** Part outlines (ears, head, body, chest) and landmarks (eyes, nose, mouth) were read off
   4-6x measuring grids of `inbox/cat-source.png` (`work/grid-head.png`, `work/grid-body.png`).
   Photo -> canvas: X = 1000 + 6.9(x - 198.5), Y = 960 + 6.9(y - 71).
2. **Colour reference.** Colours were eyedropped from the user's photo, as a painter would. The photo was
   median-filtered to drop whiskers, then blurred inside the cat outline only, so no wall colour leaks in.
   Blanket and wall zones are clamped. Saturation was pushed by 25%. Check image: `work/colour_field.png`.
3. **Block-in (Illustrator).** About 2,900 soft colour blobs, clipped per part, with a group Gaussian blur of 15-24 px.
4. **Render (Illustrator).** About 14,000 tapered fur strokes, each following the part's growth direction:
   radial from the nose on the face, down and back on the body, base to tip on the ears. They are sorted dark to
   light, and turned outward at the outline so the edge breaks like real fur. Tabby markings come from the
   stroke colours.
5. **Details.** Eyes have a radial iris, 70 fibres, a limbal ring, lid shadow, catchlight, bounce light and a
   tear duct. The nose has nostrils and highlights. Mouth, follicle dots, 18 whiskers and brow hairs are drawn.
6. **Review passes.** `work/p1-p3.png`:
   - p1 looked like scratchy straw.
   - p2 had softer value spread and opacity but was too soft.
   - p3 is balanced. It also has thinner eye rims, a rounded chest edge, and no blanket colour leak.
7. **Photoshop.** Built by `work/render_psd.jsx`:
   - Depth-of-field blur on the far layers.
   - A Lighting group masked to the cat: Form shade, Contact shadow, Key light (warm soft light), and a
     Moon rim (the silhouette minus a shifted copy, blurred, screen).
   - Moon glow, ground fade, vignette and grain.
   - Fixes applied after review: the cheek shade was moved inside the face (it was darkening the block-in
     fringe), and the Sky layer was blurred 60 px to remove a hard gradient edge.

## Layers (`out/cat-pfp-v4.psd`, top to bottom)
Grain, Vignette, Ground fade, Moon glow,
**Lighting** {Form shade, Contact shadow, Key light, Moon rim},
**Cat** {Whiskers, Eyes, Nose & mouth, Head, Ears, Chest fur, Body},
Bokeh,
**Background art** {Hills, Clouds, Moon, Stars, Sky}.
`out/cat-pfp-v4.ai` holds the editable vectors: Cat parts, Background art and Bokeh, without the PS lighting.
Legs, paws and tail are not in frame.

## Checks run
- `qc.py` on `_2000_clean.jpg`: no fails, no warnings. The circle previews at 256/64 px were viewed, and the face reads.
- The PSD layer list was read back after saving (list above).
- Not run: a per-layer hide test, and a recomposite diff of the v4 layer PNGs against the AI artboard.

## Honest limits
- This is scripted vector strokes plus Photoshop lighting, not human freehand brushwork. Up close the fur
  strokes are regular in shape.
- The colours follow the user's photo (eyedropped). Shapes, strokes, eyes, nose, whiskers and the scene are drawn.
- The `.ai` file is heavy (about 45 MB, 17.5k items).
