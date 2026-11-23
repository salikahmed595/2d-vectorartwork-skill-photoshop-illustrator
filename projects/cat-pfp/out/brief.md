# cat-pfp - brief and build record (2026-11-20)

## Brief
- Source: user-pasted photo of an orange tabby (472x216 px), copied to `inbox\cat-source.png`. Original untouched.
- Request: "make a artwork using the skill and adobe photoshop and illustrator".
- Assumptions (not asked, easy to change): 2000x2000 PFP, no title (no username was given - none invented),
  night / moon mood.

## Lane
4 - Neon vector. Indigo-violet world + orange subject, cyan accent (moon, rim line, glow, fireflies).

## Composition lock
1. Subject: cat bust, 75% of frame height, head tilted, looking at viewer. Head inside the central 70% circle.
2. Camera: straight-on, eye-line at about 43-48% of height.
3. Light: big teal moon directly behind the head; cyan rim line + outer glow on the silhouette; green-cyan eyes.
4. Depth: far = sky, stars, meteors, moon, clouds, two mountain ranges; mid = cat; fore = dark ground, rocks, grass, fireflies.
5. Title zone: top band kept low-detail (stars only). No title placed.

## Backend and settings (reproducible)
No image generator was used. The picture is the user's photo, restyled:
- Photoshop 25.12: resample 4x (1888x864) -> Select Subject mask -> Vibrance +45/+12 -> Tone curve
  [[0,0],[64,50],[128,128],[200,208],[255,248]] -> Hue/Sat on each eye (masked ellipses) -> Hue/Sat global +24.
  Saved as `work\cat-cutout.psd`.
- `work\build_scene.py` (seed 20261120) writes `scene.svg` (sky, stars, moon, clouds, mountains, foreground, fireflies).
- Illustrator 28.7.1: open `scene.svg`; Image Trace of the cutout - color, 16 colours, noise 26, path fidelity 45,
  corner fidelity 35, abutting, background dropped (1573 paths); placed x=30 y=440 width=1572. Eyes rebuilt as vector
  shapes (radial-gradient iris, pupil, glint). Saved `out\cat-pfp.ai`, `out\cat-pfp.svg`.
- Photoshop composite `out\cat-pfp.psd` (top to bottom): Final vibrance, Final contrast, Vignette (multiply 38),
  Bloom (screen 26, blur 42), Fireflies (outer glow), Foreground, Ground shade, Cat (4 px pale-cyan stroke + cyan outer
  glow), Horizon haze, Moon glow, BG vector, Background.

## Layer structure (added 2026-11-20, user request: one layer per character component)
Built with `2d-pfp\scripts\split_parts.py` from `parts\parts.json`. Same parts in `cat-pfp.ai` and `cat-pfp.psd`.

PSD, top to bottom:
```
Final vibrance / Final contrast / Vignette / Bloom        lighting and grade
Fireflies                                                  outer glow
Foreground                                                 ground, rocks, grass
Ground shade
Cat (group: pale-cyan stroke + cyan outer glow)
  Eyes            both eyes, hand-built vector irises, pupils, glints
  Nose & mouth    nose, mouth, whisker pads
  Ears            Ear L + Ear R
  Head
  Body
Horizon haze / Moon glow
Background art (group): Mountains, Clouds, Moon, Meteors, Sparkles, Stars, Sky
Background                                                 plain white base
```
Illustrator layers: Fireflies, Foreground, Cat (Eyes, Nose & mouth, Ears, Head, Body), Background (7 sublayers).
Each cat part is a clip group holding its own copy of the traced shapes.

Checks run: parts recomposed vs the unsplit cat - 0.005% of pixels differ by more than 24 levels (max 64),
no empty layer. Layered PSD flat export vs the previous master - max difference 33, 0.005% of pixels over 8.
Saved `.ai` reopened and its 16 layers listed.

Not in frame, so no layer: legs, paws, tail. Whiskers are baked into the Head and Body fur, not separate.
Each lower part reaches about 40 px under the part above it; beyond that there is nothing behind a moved part.
The Head layer still holds the original traced eyes under the Eyes layer. A white traced blanket shape was removed.

## Candidates (`candidates\`)
- c1 - 14 colours, cat too large, eyes lost their green, highlights blown. Rejected.
- c2 - 12 colours, smaller cat, traced eyes left white patches and muddy colour. Rejected.
- c3 - 16 colours, warmer grade, vector eyes. Selected.

## QC (`qc\`)
`qc.py` on `cat-pfp_2000_clean.jpg`: no fails, no warnings. 2000x2000, clipped white 0.27%, crushed black 6.76%.
Circle previews at 256 and 64 px looked at: head and both eyes inside the circle, eyes readable at 64 px.

## Status
- VERIFIED: files exist, sizes, QC numbers, circle previews, eyes and silhouette inspected at full size.
- NOT MADE: titled master (`_2000.jpg`) - no username supplied.
- NEEDS A HUMAN EYE: the cat is a posterised trace of a low-resolution photo, not a hand-drawn character, so fur
  detail is blocky at 100%. It does not match the hand-illustrated finish of the portfolio pieces.
