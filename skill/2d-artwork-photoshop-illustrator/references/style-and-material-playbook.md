# Style and material playbook

## Anime / cel-shaded illustration (the user's reference level)
- Line art: dark warm tone of the local colour (fur: #3a1a0c, cloth: deep navy), tapered both ends,
  6-9 px outer contour at 2000 px, 2-4 px interior lines; break the line where light hits.
- Cel: base, shadow (hue shifted toward the ambient colour, ~25% darker), deep shadow in occlusions.
  Hard edges on shadows, soft airbrush only for bounce light and blush.
- Rim light: thin bright line of the glow colour on the edge facing the second light source.
- Eyes: largest contrast in the image. Gradient iris (dark top, light bottom), slit pupil, 2 catchlights.
- Magic: rune circle = concentric rings + glyph segments, screen-blended cyan with layered blurs (4, 16, 60 px).
- Particles: 60-200 dots and petals, sizes 2-14 px, some blurred (depth), on-palette.
- Background: painted shapes in 3 depths: far silhouettes (light, cool, blurred),
  mid (trees, buildings), near frame (dark branches or blossoms across a corner).

## Painterly fur
Block-in blobs + group blur, then thousands of tapered strands along a flow field (see `examples/cat_painterly_spec.py`).

## Fabric
Cloth folds radiate from tension points (shoulders, clasp). Each fold = shadow shape + thin highlight on the ridge.
Embroidered trim: repeated gold motifs along a path, with a darker under-line and a 1 px highlight.

## Metal / gems
Hard specular hits, dark reflected horizon line, glow on gems (core white -> accent -> transparent).

## Emotes / stickers
Thick readable silhouette, 1 expression, white sticker border optional, test at 28 px.

## Pixel art
Fixed grid, nearest-neighbour scaling, limited palette, no anti-aliased brushes.

## Brand / merch
Vector-first, spot-friendly colours, outlined-text export copy, keep live text in the master.

## Environments
Perspective grid first; foreground / midground / background; atmospheric perspective; one focal light.
