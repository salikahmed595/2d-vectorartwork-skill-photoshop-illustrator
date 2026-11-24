# Layered components - one layer per character part

Standing rule (user, 2026-11-20): every delivered PFP ships as an editable layered file in which
**each character component is its own layer** - eyes one layer, ears one layer, legs one layer, hands
one layer, and the same for every other part - so an editor can move, recolour, hide or repaint one
part without touching the rest. A flat master alone is not a finished delivery.

## Which layers
Make a layer for every part that is **visible** in the piece. Never invent a hidden limb to fill the
list; say in the hand-off which parts are not in frame.

| Character | Part layers, bottom to top |
|---|---|
| Humanoid | Legs, Feet/Shoes, Body/Torso (clothes), Arms, Hands, Neck, Head/Face, Ears, Hair back, Nose & mouth, Eyes, Brows, Hair front, Hat/Headwear, Props |
| Animal / mascot | Tail, Back legs, Body, Front legs/Paws, Head, Ears, Nose & mouth, Eyes, Whiskers (only if drawn as separate strokes), Accessories |
| Mecha / helmet | Body plates, Head shell, Visor/Eyes, Antennae/Horns, Emissive lights, Weapons |
| Duo / couple | One parent group per character, each with its own part layers |

Rules:
- Left and right of a pair share **one** layer (`Ears`, `Eyes`, `Hands`, `Legs`) with a named piece
  each (`Ear L`, `Ear R`), unless the user asks for them apart.
- Plain names, no numbers or abbreviations: `Eyes`, `Nose & mouth`, `Body`.
- The character is one parent layer/group named after the character (`Cat`, `Hunter`), parts inside.
- Scene elements get their own layers too: `Sky`, `Stars`, `Moon`, `Clouds`, `Mountains`,
  `Foreground`, particles, title. Lighting layers (glow, haze, shade, bloom, vignette, grade) stay
  separate and named for what they do.
- Rim stroke and glow go on the **character group**, not on the parts, so they follow any part that
  is moved.

## How (traced / vector character in Illustrator) - verified on the cat job, 2026-11-20
1. Export the character layer alone and draw a 100 px grid over it. Read part positions off the grid.
2. Write `parts.json` (schema below). One polygon per piece, canvas pixels, y down.
3. `python scripts/split_parts.py parts.json` - builds the layers, exports every layer, checks that
   the parts rebuild the original, writes `manifest.json` and `_parts_sheet.png`.
4. Look at `_parts_sheet.png`: each tile must hold only its part.
5. Save the `.ai`. Assemble the PSD from the exported PNGs (below).

Polygon rules that keep seams invisible:
- Parts are listed bottom to top. A lower part extends about 40 px **under** the part above it.
- The edge of an upper part that crosses the character sits on the natural seam (ear base, jaw line,
  wrist) and must fall inside the part below.
- Polygons may spill outside the silhouette; only edges crossing the character matter.
- A part already built as its own group (hand-drawn eyes, a prop) is passed as `"group"`, no polygon.

```json
{
  "doc": "name.ai",
  "out_dir": "parts",
  "erase": [{"bbox": [150, 1840, 900, 1950], "min_luma": 235}],
  "stack": [
    {"layer": "Background", "group": "BG", "explode": true},
    {"layer": "Cat", "source_group": "Cat", "parts": [
      {"layer": "Body", "pieces": [{"name": "Body", "polygon": [[-50, 1165], [720, 1165], [1750, 2050], [-50, 2050]]}]},
      {"layer": "Ears", "pieces": [{"name": "Ear L", "polygon": [[540, 620], [812, 712], [702, 915]]},
                                   {"name": "Ear R", "polygon": [[1125, 420], [1345, 728], [1128, 642]]}]},
      {"layer": "Eyes", "group": "Eyes"}
    ]},
    {"layer": "Foreground", "group": "FG"}
  ]
}
```
`stack` is bottom to top. `erase` is optional (removes light leftover shapes fully inside a box).
A full worked example: `Documents\Adobe-Work\cat-pfp\out\parts\parts.json`.

## PSD assembly (Photoshop CLI)
1. `doc new` at master size, then `place <png> --name <leaf> --x <bbox x> --y <bbox y> --rasterize`
   for every entry of `manifest.json`, bottom to top. Rasterized so the editor can paint on each part.
2. Group: `layer group <Character> --layer ...`, then check `layer list`.
3. Lighting layers, then `style set <Character> --stroke ... --outer-glow ...` on the group.
4. Export a flat PNG and diff it against the approved master before overwriting anything.

Observed behaviour (this PC, Photoshop 25.12 / Illustrator 28.7.1):
- `layer group` keeps the group in place but **reverses** the order of the layers given. Pass them
  top to bottom, or fix with `layer arrange <Group/Layer> top` from the bottom part upward.
- `fill --new-layer` and `place` after a group exists land at the **top** of the stack. Move them with
  `layer arrange ... up/down/top` and re-read `layer list`.
- `style set` works on a group.
- The default white layer is called `Background`; name the scene group `Background art`.
- Illustrator `doc export file.svg` renames the open document to the `.svg`. Save the `.ai` first,
  export the SVG last, then close it and reopen the `.ai`.
- Image Trace leaves the cut-off edge of a cropped subject and stray light shapes (blanket, floor);
  remove them with `erase` or hide them behind the foreground.

## Verification (required before delivery)
- `split_parts.py` prints PASS: under 0.05% of pixels differ by more than 24 levels, no empty layer.
- Flat export of the layered PSD vs the approved master: report max difference and % of pixels over 8.
- Reopen the saved `.ai` and list layers - the part layers must be there.
- Put the layer list in `brief.md` and in the hand-off.

## Limits to state honestly
- Parts cut from a single flat image have nothing behind them: move an ear far and the head shows
  only the ~40 px underlap. Say so; offer to paint in the hidden area if the editor needs big moves.
- Details baked into the art (whiskers across fur, hair strands over a face) stay in the layer they
  cross. Do not claim a `Whiskers` or `Hair front` layer unless it was built as separate shapes.
- Routes and their status:
  - Drawn with `scripts/ai_draw.py` (the normal route): every part is its own layer from the start;
    `--export dir` writes one PNG per leaf layer + `manifest.json`. Verified on the v3 cat: layer
    recomposite vs the artboard export differed on 0.010% of pixels (>15 levels), only where a
    multiply shadow blends across layers.
  - Image Trace of the user's photo: split with `split_parts.py` (verified on v1).
  - A flat raster of the user's own art: `split_parts_raster.py` cuts along polygons into one PNG
    per part and checks the recomposite; check its output the same way and report what was checked.
- Blend-mode items (multiply shadows, screen lights) inside one part layer blend with the layers
  below in Illustrator but with nothing when that layer is exported alone; keep them subtle or
  expect small recomposite differences.
