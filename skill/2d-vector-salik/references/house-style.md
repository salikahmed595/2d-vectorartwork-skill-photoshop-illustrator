# 2d-vector-salik house style - the exact recipe

This is the style of the two reference pieces in `examples/`: **Mango - Jungle Sunrise Gamer**
(`examples/mango-jungle/mango_result.jpg`) and **Cat Mage v7** (`examples/cat-mage-v7/cat_v7_result.jpg`).
Open both result images before starting. To get the same look, start from `templates/project/` (the Mango source),
keep the helper library `vec.py` and the values below, and change only the subject, palette and scene.

Everything is drawn as hand-placed vector paths: Claude writes the coordinates in Python, `ai_draw.py` builds them
in Illustrator, and Photoshop adds the light passes on separate layers. No AI image generation anywhere.

---

## 1. Canvas, coordinates, pose
- Artboard **2000 x 2000 px** (square PFP). A banner is the same method on its own artboard size.
- Each character is drawn in **local coordinates** around its own centre (y down), then placed with one transform:
  ```python
  CX, CY, S = 1000, 1030, 1.15        # placement and scale
  LEAN = math.radians(5)              # lean of the whole figure, pivoting on the feet (local y = 420)
  def M(x, y):
      dx, dy = x, y - 420
      c, s = math.cos(LEAN), math.sin(LEAN)
      x, y = dx*c - dy*s, 420 + dx*s + dy*c
      return (CX + x*S, CY + y*S)
  ```
  The cat uses the same idea with a head transform (`HS = 1.12`, `TILT = -4 deg`) and a body transform.
  Every builder takes the transform as `xf`, so moving or re-posing the character is one number.
- The head/face and the key features sit inside the central circle (platforms crop to a circle).
- The face is the brightest, sharpest area. Light comes from one low key source (sun or moon) plus a warm or cool fill.

## 2. The helper library (`vec.py`)
| Function | Use |
|---|---|
| `path(pts, xf, closed=True)` | Catmull-Rom Bezier through points. A point `(x, y, 'c')` is a hard corner. |
| `taper(pts, xf, w, start, end)` | Filled tapered stroke along a curve: line art, rims, folds, core shadows, brows, lid lines. `start`/`end` = taper length fraction. |
| `ellipse(cx, cy, rx, ry, rot, xf)` | Rotated ellipse (lights, glows, dots, highlights). |
| `poly(pts, xf)` | Straight-edged polygon (sparkles, stars, hard facets). |
| `sample(pts, xf, closed, per)` | Points along the curve (to place leaves, lenticels, particles along a path). |
| `mirror(pts)` | Mirror x for the other side; then nudge a few points so the two sides are not identical. |
| `it(name, d, fill, **kw)` | One spec item. kw: `opacity` (0-100), `blur` (px), `blend`, `stroke`, `stroke_width`. |
| `lin(stops, angle)` / `rad(stops)` | Gradients; stops are `[hex, position 0-100]` or `[hex, pos, opacity]`. |
| `spine`, `leaf_outline`, `leaf_items` | Curved leaf with midrib, veins, two-tone fill, rim, water droplets. |

## 3. Spec and layers
`<name>_design.py` writes `drawing.json`: `{"doc": "<name>.ai", "layers": [ {layer, clear, clip, outline, items}, ... ]}`.
- `layer` is `"Group/Layer"`. Groups, back to front: **Background, Scene, <Character>, Foreground, FX**.
- One layer per character part: Cape / Log (prop) / Contact shadows / Feet / Body / Leaves / Mouth & blush / Eyes / Brows /
  Arms / Controller / Hands / Cape collar (Mango); the cat has Cloak, Body, Head, Ears, Eyes, Nose & mouth, Whiskers, Paws, Staff...
- `clip` = a path that clips every item of the entry (all shading on a part is clipped to that part, so nothing spills out).
- `outline = {"stroke": LINE, "width": 7}` draws the part's outer line on top of its shading.
- Several entries can write into the same layer with `clear: False` (e.g. each eye with its own clip).
- Layer order = draw order. Props that sit in front of a cloth and under the feet go inside the character group.

## 4. Line work
- Line colour is a **dark, warm, saturated version of the local colour, never black**: Mango `#4a1c0c`, cat `#3a1608`,
  cape `#2a4a1a`, eye lines `#1a0a06`, leaf lines `#163a20`.
- Outer silhouette 6-7 px; inner features 4 px; detail lines are tapered fills (`taper`) at 8-17 px, tapering 0.2-0.45.
- Lid lines end in a small outward flick.

## 5. Cel shading stack (every form, in this order, clipped to the part)
1. **Base gradient** - top light to bottom warm/dark, e.g. Mango skin `lin(#cfdc4c 0, #ffd640 26, #ffa22c 52, #ff7a2a 76, #ee503a 100)`.
2. **Side shade** - crescent on the side away from the fill light, darker hue-shifted colour, opacity 55.
3. **Base shade** - flat ellipse at the bottom, opacity 38.
4. **Core shadow** - `taper` along the turning edge, width ~26, opacity 40.
5. **Soft top light** - ellipse, pale warm (`#fff4ac`), opacity 55, `blur` 30 - blur is allowed only *inside the clip*.
6. **Cheek / bounce glow** - opacity 35, blur 24.
7. **Texture** - small seeded marks kept off the face (lenticels, fur tufts, stripes) at opacity ~60.
8. **Crisp gloss** - hard-edged highlight shape + one gloss dot, `#fffbe0`, opacity 88.
9. **Rim lights** - `taper` along the silhouette points: key side 22 px at 92 % (`#ffe58a`), opposite side 12 px at 70 %.
10. **Occlusion** - tapered dark band under every overlap (collar, ruff, arm roots), opacity 38, blur 8.

Shadows are hue-shifted (toward red/purple), not grey. Light side wider and warmer, shadow side narrow and cooler.
Never mirror highlights on both sides.

## 6. Eyes
Clipped to the eye shape (`eye_shape(cx, cy, rx, ry, lid, slope)`):
radial base `#5a3424 -> #2a1610 -> #120806`; iris glow (lower half, `#8a4a22`, 70 %); a coloured **bounce** from the
environment along the bottom (sunset `#ff9a3a` / magic cyan); lid shadow (black, 40 %, 22 px taper under the top lid);
**two white highlights** (big upper-left 17x21, small lower-right 8x8) plus a **4-point sparkle**.
Outside the clip: 4 px outline and a tapered lid line with a flick.
Attitude comes from asymmetry: one eye half-lidded (`lid` 0.30 vs 0.12), brows at different heights.

## 7. Cloth (cape, cloak, robe)
Base gradient -> **fold shade** tapers (width 32-46, opacity 90) -> **fold core** inside each fold (22 % width, 85 %) ->
**fold light** tapers on the ridges (10-14 px) -> **lining flip** where the edge turns (darker inner colour) ->
rim on the light side -> 6 px line. Cloth edges and flaps **cover limb roots**, so limbs come out from under them.
Cloth moves with the wind (streaming, not hanging like a tablecloth).

## 8. Background (drawn, never blurred)
Depth from **value, colour temperature, scale, overlap and detail** - Gaussian blur on scenery is forbidden.
Back to front:
- **Sky** gradient + **celestial object** with disc, ring, halo and rays (sun) or craters and glow (moon); keep it visible.
- **Clouds** as layered crisp shapes with a lit edge.
- **Far crowns** (`crowns(tag, y, amp, r0, r1, col, rr, rim)`) in hazy, light, low-contrast colour; palms/silhouettes.
- **Mist bands** between depth planes.
- **Mid crowns** darker and more saturated.
- **Tall trunks** (`trunk(...)`) with bark lines, a rim on the side facing the light, moss only as designed shapes.
- **Canopy** leaf clusters at the top edge (never a hard cut line), **vines** with alternating leaves, **swags**.
- **Ground** with ferns (pinnae), five-petal flowers, a radial light pool (soft fade, no hard ellipse edge).
- **Contact shadows** only under things that touch the ground.
- **Foreground** leaves/vines at the frame edges, darker, overlapping the character slightly.
- **Particles**: three size classes, each with a core and a halo, clustered toward the light; glints (`star4`); wind-blown leaves.

## 9. Palettes
**Mango (orange sunrise jungle):** skin `#cfdc4c / #ffd640 / #ffa22c / #ff7a2a / #ee503a`; shades `#e0582a #d0502a #c94a2a`;
peach limbs `#ffa48c / #e8706c / #ffd2c0`; cape `#b6e36b / #86c34e / #4f8f35 / #e6fbb0`, lining `#5f9c3e`;
gold `#f2c14e / #fff0b8 / #6a4310`; brows `#3f8a3a`; sun bloom `#ffcf7a`; rim `#ffe58a / #ffd27a`.
**Cat mage (night, navy and gold):** ginger `#f39a4c / #d4692c / #b9501d / #ffc27a`, stripes `#c2501b`;
cream `#fff3e2 / #efcca8`; navy `#232d6a / #131944 / #3c4fa2`; gold `#e6b65c / #fff0b8 / #6a4310`; magic cyan `#6ff6ff / #d8ffff`.
Rule: two dominant hues + one accent; the glow colour equals the accent.

## 10. Photoshop pass (`gen_psd_jsx.py` -> `render_psd_<name>.jsx`)
Layers from the Illustrator export are placed in their groups, then these are added as separate named layers:

| Layer | Blend | Opacity | Recipe |
|---|---|---|---|
| Sun bloom | Screen | 45 | ellipse r 430 on the light source, feather 240, `#ffcf7a`, under the scenery in front of it |
| Lighting / Form shade | Multiply | 40 | ellipse on the shadow side, feather 220, `#5a2040` |
| Lighting / Warm face fill | Soft Light | 55 | ellipse on the face, feather 220, `#ffe0a8` |
| Lighting / Sun rim | Screen | 85 | character alpha filled `#ffd27a`, minus the alpha offset `translate(-12, 7)` (toward the light), blur 2.5 |
| (prop) LED glow | Screen | 60 | small ellipse, feather 30, accent colour |
| Colour grade | Soft Light | 16 | flat warm fill `#ff8a3a` |
| Vignette | Multiply | 40 | `#1a0c20` minus a centred circle r 1060, feather 300 |
| Grain | Overlay | 12 | 50 % grey + Add Noise 3 % gaussian mono |

The three Lighting layers are masked to the character's merged alpha. Blur is used only on light layers.

## 11. Pipeline
```
python <name>_design.py                                   # -> drawing.json
python <skill>/scripts/ai_draw.py drawing.json --preview p1.png      # draw in Illustrator + preview
python <skill>/scripts/ai_draw.py drawing.json --only "Mango/Eyes" --preview p2.png   # redraw one layer
cli-anything-illustrator --json doc save <out>/<name>.ai
cli-anything-illustrator --json doc export <out>/<name>.svg  (then re-save the .ai: SVG export renames the doc)
python <skill>/scripts/ai_draw.py drawing.json --export layers      # one PNG per layer + manifest.json
python gen_psd_jsx.py                                     # -> render_psd_<name>.jsx
cli-anything-photoshop --json script run --file render_psd_<name>.jsx
python <skill>/scripts/qc.py <out>/<name>_2000.jpg        # size, sharpness, exposure, circle previews
python <skill>/scripts/audit_sheet.py <master> --silhouette <alpha> --out audit.png
```
Review at least three drawing passes (look at every preview), make 100 % close-up crops of face, hands and props,
then run the 18-point audit and write `revision-report.md` with what was actually run.

## 12. Gotchas (learned the hard way)
- The Illustrator CLI ignores `--doc` for `doc close` / `doc save`: it acts on the **active** document. Target documents
  by name with a small JSX (`app.documents.getByName(...)`).
- Photoshop scratch disk fills up: close your own already-saved PSDs before a new render (the generated JSX does this).
- `layers/manifest.json` uses the key `path` (`"Group/Layer"`) for each layer.
- In Python on Windows use `C:\...` paths, not `/c/...`.
- Defects seen before and how they were fixed: sun hidden behind the jungle (raise it / lower the crowns); cape looked
  like a tablecloth (make it stream, put the prop in front); limbs the same colour as the body (give limbs their own
  colour); a red base shade read as a second mouth (lower and soften it); neon trunk rims (cut opacity, warm the colour);
  blob moss; a hard canopy edge; an empty ground; fronds crossing the sun; a hard light-pool edge; a floating shadow.
