# Mango - Jungle Sunrise Gamer (mango-pfp v1) - production report

Date: 2026-11-21. Skill: `2d-vector-salik` (Universal 2D Artwork Studio v3.0). Brief: `brief.md`.
Made only in Adobe Illustrator (every path written as coordinates in `work/mango_char.py` and `work/mango_bg.py`, built by `ai_draw.py`)
and Adobe Photoshop (layer assembly plus light passes). No AI image generation, no Generative Fill/Expand, no stock images.

## References
- Character: `ref/mango-reference.png` (the attached Mango image). Kept: mango body with a green-yellow top fading to orange and red, leaves with water droplets, big dark glossy eyes with two highlights, green brow marks, blush, small smile, peach hands and feet.
- Style reference "Screenshot 2026-10-31 204546.jpg" (Discord banner): **not received** - the attachment came through as the Mango image twice, and the file is not in Downloads, Pictures, Desktop or Documents. The style follows the skill's clean cel-shaded vector standard instead. Send it and the style can be matched in a revision.
- Format: square 2000x2000 PFP (your choice in the size question), not a 17:6 banner.

## 18-point audit (final)

| # | Check | Result | Evidence / note |
|---|---|---|---|
| 1 | Focal point clear | PASS | face is the brightest, sharpest area (greyscale panel, `work/audit_mango.png`) |
| 2 | Composition balanced | PASS | Mango centred and framed by trees; sun right balances the cape left |
| 3 | Silhouette readable | PASS | mango + leaves + streaming cape read as one shape (silhouette panel) |
| 4 | Structure believable | PASS | mango body, leaves grow from one stem |
| 5 | Features placed correctly | PASS | eyes on the lower half like the reference; brows, blush, mouth aligned |
| 6 | Limbs connect | PASS (fixed) | first pass: arms were the body colour and the hands looked detached. Now peach arms come out from under the cape flaps into the hands |
| 7 | Clothing openings / overlaps | PASS (fixed) | cape tied under the chin with a collar and leaf clasp; flaps cover the arm roots. First pass: the cape hung over the log like a tablecloth; now it streams left behind the log |
| 8 | Paths and lines clean | PASS | Catmull-Rom Bezier paths, tapered strokes |
| 9 | Shapes smooth and intentional | PASS | |
| 10 | Shading explains form | PASS | side and base shade away from the fill light, core shadow, gloss, collar occlusion, cape fold cores |
| 11 | Lighting consistent | PASS | low sun right-behind: gold rim on Mango's right edge, trunk and crown rims face the sun, warm fill on the face |
| 12 | Eyes and face polished | PASS | iris glow, orange sunset bounce, lid shadow, two highlights plus a sparkle; half-lidded right eye and raised left brow for the "cool" smirk |
| 13 | Background illustrated, not blurred | PASS | no Gaussian blur on any scenery layer; depth from atmospheric colour (hazy peach far jungle, darker mid and near), scale and overlap |
| 14 | Particles clean | PASS | pollen and fireflies in three size classes with core and halo, glints, wind-blown leaves |
| 15 | Celestial object detailed | PASS (fixed) | first pass: the sun was hidden behind the far jungle; now it's a visible disc with ring, halo and rays. A palm that crossed it was moved |
| 16 | Botanical elements designed | PASS | two-tone leaves with midrib and veins, vines with alternating leaves, swags, ferns with pinnae, five-petal orange flowers |
| 17 | Stylistic consistency | PASS | one cel-vector language throughout |
| 18 | Polished for delivery | PASS | qc.py: no fail or warn; reads in the 64 px circle (`qc/`) |

Defects fixed after the audit: the ground light pool had a hard elliptical edge (now a radial fade), and a "cape shadow" floated in mid-air (removed).
Open notes: none at P0/P1. The pose is "cool" through expression, lean (5 degrees) and the windblown cape; a more dynamic action pose would be a redesign.

## Execution log (all actually run)
1. New Illustrator document `mango-pfp.ai` (2000x2000). Note: the CLI's `--doc` flag was ignored by `doc close` and `doc save`. That briefly closed the already-saved `cat-pfp-v7.ai` and saved two old cat docs under the Mango name. No file on disk was lost. Fixed with a script that targets documents by name.
2. `python mango_design.py` -> `drawing.json` (29 entries, 2,961 items); four drawing and review passes (`work/m_p1`-`m_p4.png`).
3. Saved the .ai, exported the .svg, re-saved the .ai; exported 27 layer PNGs + manifest.
4. Photoshop: `gen_psd_jsx.py` -> `render_psd_mango.jsx` (~45 s per run). Exported the master and saved the PSD (41 layers). Rebuilt twice for the two fixes above.
5. Pillow resize and encode only: 2000 jpg, 1080 webp, 512 png. `qc.py`: no fail, no warn (mean 88.6, centre 152.3, sharpness 29.7 / 32.2).
6. Audit sheets `work/audit_mango.png` and `work/audit_mango_closeups.png` - reviewed.
7. Master uploaded to Creative Cloud `mango-pfp/mango-pfp_master.png` (asset `urn:aaid:sc:AP:9bd12a4a-d2b5-41a5-b10f-87a1db964d2c`).

## Deliverables (`mango-pfp/out/`)
| File | Size | Notes |
|---|---|---|
| mango-pfp.ai | 6.6 MB | editable vectors; groups Background / Scene / Mango / Foreground / FX |
| mango-pfp.svg | 4.3 MB | same vectors |
| mango-pfp.psd | 30.8 MB | 41 layers. Mango group: Cape, Log, Contact shadows, Feet, Body, Leaves, Mouth & blush, Eyes, Brows, Arms, Controller, Hands, Cape collar. Lighting group: Form shade, Warm face fill, Sun rim. Plus Sun bloom, LED glow, grade, vignette, grain |
| mango-pfp_master.png | 3.4 MB | 2000x2000 |
| mango-pfp_2000.jpg / _1080.webp / _512.png | 1.0 MB / 0.18 MB / 0.31 MB | Discord-ready sizes |
| parts/ | 27 PNG + manifest.json | one per layer |
| qc/ | circle 256/64 + qc.json | |
