# Revision report - cat-pfp v5 -> v6

Mode: **Refine**, following the skill `universal-2d-vector-art-studio` v2.0.

Order of work:
1. Structural defects (P0/P1) were fixed first.
2. Decorative defects (P2/P3) came second.
3. Photoshop light was rebuilt last.

"Drawn" here means Claude wrote every path's coordinates by hand in a spec. The spec files are:
- `v6/work/v6_design.py`, for the character and the cloak;
- `v6/work/scene_v6.py`, for the scene and particles.

Adobe Illustrator built the paths through `ai_draw.py`. It is not human brushwork. No AI image generation, Firefly, Generative Fill or auto-trace was used.

## Defect log
| ID | Audit # | Sev | Location | Symptom | Root cause | Operation (tool) | Expected change | Result (view checked) |
|---|---|---|---|---|---|---|---|---|
| D1 | 3 Attachments | P0 | Raised arm, lower left | Sleeve rose as a column from the canvas bottom; no shoulder or elbow | The arm was one closed sleeve shape with no joint | Rebuilt the arm as 3 layers in Illustrator. **Upper arm** tucks under the gold edge. **Cloak trim** is its own layer, drawn over the upper arm. **Paw & orb** carries a forearm from an elbow at the cloak opening to the cuff, with a ridge light, elbow folds, a forearm cast shadow and an elbow contact shadow | Arm reads as a jointed limb coming out of the cloak opening | PASS: effects-off and 100% crop |
| D2 | 3, 8 | P1 | Jaw / collar | Head looked pasted onto the cloak | No overlap or shadow where the head meets the body | New layer **Neck ruff**: 8 irregular fur tufts, a shade under the jaw and a warm contact shadow. The first version read as a lace collar and was redrawn | Head sits into the body | PASS (P3 note below) |
| D3 | 9 Light | P1 | Cloak folds | Fold highlights were mirrored, though the key light comes from the left | Left and right folds were drawn as mirror copies | Left ridges now ×1.35 width, a warmer colour (#5466b8) and a specular line. Right ridges are ×0.6, cool, at 70% opacity. Added a right-panel form shade | Light direction is consistent | PASS: greyscale |
| D4 | 7, 10 | P1 | Rune ring, moon | In greyscale, the ring and moon nearly matched the face | Full-opacity strokes, heavy bloom and a near-white moon | Ring strokes at 72% in Illustrator. Ticks and triangles at 60. Moon fill darker, halo 45→26. In Photoshop: rune glow 100→70, bloom 80→50, moon glow 45→28, circle halo 40→30 | The face is the brightest area | PASS with note: the moon is still the second-brightest shape (intended) |
| D5 | 5, 7 | P2 | Muzzle, right side | Shade was a stain-like blob | The shape didn't follow the form | Replaced with a crescent that follows the muzzle edge | Reads as the muzzle turning away | PASS: 100% |
| D6 | 11 | P2 | Particles | Petals were plain ovals; sparks were uniform and evenly spread | A single random generator | Rewrote the particles (see the list after this table) | Particles look designed | PASS. The first redraw made a heart-like petal and bubble-like bokeh; both fixed in review pass 2 |
| D7 | 11 | P2 | Rune ring | Glyphs were random scratches | Random line segments | Designed 8-glyph alphabet, 48 glyphs in sequence, aligned to the ring's tangent, with a separator dot every 4 | Reads as an inscription | PASS: 100% |
| D8 | 12 Botanical | P2 | Wisteria | Racemes had no stems; florets were generic ellipses; the left side was a dense wall; leaves floated | Floret scatter with no structure | Redrew the wisteria (see the list after this table) | Readable clusters attached to the branch | PASS. One raceme overlapped the left ear tip in pass 1; moved and shortened |
| D9 | 10 | P2 | Midground | Trees were random translucent blobs | Ellipse scatter | 8 trees with scalloped canopies in 3 tones, trunks and hanging tassels. Photoshop depth blur reduced from 16 to 9 | Reads as blossom trees at depth | PASS. The tassels first read as icicles; softened in pass 2 |
| D10 | 10 | P3 | Far castle | Walls and windows were plain rectangles | Primitive shapes | Crenellated walls, tower bands, a lit side on each tower, and arched windows with sills | More believable silhouette | PASS (soft under depth blur, as intended) |
| D11 | 8 | P2 | Right cloak edge | Dark halo spilled past the cloak edge onto the background (found in the after-audit silhouette view) | The blurred form shade sat too close to the edge | Moved the shade path inward | No spill | PASS, measured on the cloak layer alpha: 15,419 → 494 soft pixels; the edge now stops at x=1712, against x=1753 before |

**D6 particle rewrite:**
- Sparks come in 3 size classes: small core; medium core and halo; large with a 4-point glint.
- They cluster around the orb, the amulet and the ring rim, with a few ambient ones.
- 20 slender notched petals drift from the wisteria.
- 2 out-of-focus foreground petals sit at the frame edges.
- 4 soft bokeh discs.

**D8 wisteria redraw:**
- Branches have a light edge.
- Each raceme has a stem and a tapered rachis.
- Florets are two-tone (a light banner and a darker keel), shrinking toward the bud tip, with a back row a tone darker.
- 4 pinnate leaf sprays attach to the branch.
- There are fewer racemes (5 front, 4 back), of varied length.

Kept as intentional stylisation: eyelash flicks, cel-shaded lines, cream muzzle, palette.

## 12-point scorecard
| # | Check | Before (v5) | After (v6) | View | Note |
|---|---|---|---|---|---|
| 1 | Identity | PASS | PASS | full | Ginger tabby, green eyes, white muzzle and chest, pink nose |
| 2 | Anatomy and proportion | FAIL (arm) | PASS | effects-off, 100% | Elbow, forearm and wrist read in order |
| 3 | Attachments and roots | FAIL (P0 arm, P1 head) | PASS | 100% crops | Upper arm under the trim, forearm over it; ruff joins the head to the body; racemes hang from stems |
| 4 | Silhouette | PASS | PASS | silhouette | Ears, cheek fluff and cloak read; the arm is inside the body mass |
| 5 | Facial features | ACCEPTED-WITH-NOTE (muzzle stain) | PASS | 100% | |
| 6 | Line and path quality | PASS | PASS | 100% | Tapered contour lines; arm line weight matches the cloak |
| 7 | Form values | FAIL (ring and moon competed) | ACCEPTED-WITH-NOTE | greyscale | Face brightest; moon second, intended as the backlight |
| 8 | Contact and ambient shadow | FAIL | PASS | full, silhouette | Forearm, elbow, trim, ruff contact shadows; the D11 spill fixed |
| 9 | Highlights, rim, light direction | FAIL (mirrored folds) | PASS | greyscale | Key light upper-left, orb cyan from lower-left, moon rim from upper-right |
| 10 | Background depth, focal separation | ACCEPTED-WITH-NOTE | PASS | full, 256 px | Far castle blur 6, mid trees 9, mist; subject sharpest |
| 11 | Particles, glow, magic geometry | FAIL | PASS | 100% | |
| 12 | Botanical detail | FAIL | PASS | 100% | |

P3 notes left open:
- The neck-ruff tufts are still fairly regular in rhythm.
- A light band of chest fluff shows below the ruff's contact shadow.

Neither affects readability at 64 or 256 px.

## Execution log
**Executed in Adobe** (each step was checked by looking at the exported preview, or by reading the CLI's JSON result):

- **Illustrator** (local, through `cli-anything-illustrator` and `ai_draw.py`):
  - Saved a versioned copy, `cat-pfp-v6.ai`; the v5 files were not touched.
  - Deleted and rebuilt the Cat sublayers in back-to-front order, adding 3 new part layers.
  - Drew 2,243 paths.
  - Ran 5 preview passes (`v6_p1`–`v6_p5`).
  - Saved the .ai, exported the .svg, and exported one PNG per layer.
- **Photoshop** (local, through `cli-anything-photoshop`):
  - `render_psd_v6.jsx` built the 41-layer PSD: 13 Cat part layers plus scene groups, a Lighting group with 5 masked passes, glow, grade, vignette and grain.
  - Exported the master PNG and saved the PSD. It was rebuilt once after the D11 fix.
- **Adobe cloud connector** (your signed-in account): uploaded the master to Creative Cloud as `cat-pfp/cat-pfp-v6_master.png` (asset `urn:aaid:sc:AP:68fb67e5-aca8-421b-a80e-a476f395d42e`). Non-generative.

**Bookkeeping only (Pillow):**
- JPG and WebP resizes.
- Silhouette alpha union.
- Audit sheets.
- Alpha-spill measurement.
- `qc.py`: no fails, no warnings; mean brightness 77.1, centre 125.0.

**Instructions-only:** none.

**Blocked or not used:**
- Generative connector tools are forbidden by the standing rule.
- Openverse stock images were not used. The skill forbids stock raster passed off as drawn art.

## Deliverables (verified paths, `v6/out/`)
- `cat-pfp-v6.ai`: editable vector, layers Background art / Magic / Cat (13 parts) / Near frame / FX.
- `cat-pfp-v6.svg`: 14.1 MB.
- `cat-pfp-v6.psd`: 41 layers.
- `cat-pfp-v6_master.png`, `cat-pfp-v6_2000_clean.jpg`, `cat-pfp-v6_1080.webp`.
- `parts/`: 21 layer PNGs plus `manifest.json`.
- `qc/`: circle previews and `qc.json`.
- Audit views:
  - `v6/work/audit_v5.png` (before);
  - `v6/work/audit_v6.png` (after);
  - `v6/work/audit_v6_closeups.png`.
