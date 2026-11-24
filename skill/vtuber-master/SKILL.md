---
name: vtuber-master
description: Create high-end VTuber character art and rig-ready layer specifications from references; validate layered PSDs and coordinate safe local Live2D Cubism integration.
---

# VTuber Master — professional character art to Live2D pipeline

## Mission
Produce original, polished anime VTuber character designs with consistency and a technically honest, verifiable Live2D production handoff. Study the supplied reference images for finish, not for copying character identities, watermarks, or trademarked properties. Never promise pixel-identical output from stochastic generation.

## Mandatory stage gates
1. **Design brief:** Extract physical features, palette, outfits, rendering cues, pose, expressions, delivery format. Build a locked `character_bible.md` with turnaround specifications and stable visual landmarks. Obtain user approval only when genuinely needed; otherwise proceed with explicit assumptions.
2. **Art generation:** Use an actually available image generation or drawing tool. Produce a full body *neutral/front view*, not merely glamour poses, plus expression and pose sheets. If no image tool is connected, output the precise generation prompts and mark renders as NOT GENERATED. Never claim Claude text alone rendered images.
3. **Consistency QC:** Inspect face proportions, eye color, hair topology, accessory locations, costume details and body proportions across views. Reject major drift. Preserve a fixed seed where supported but never treat seed as a guarantee.
4. **Separation:** Generate or draw each physically independently moving part in its own RGBA layer, with missing occluded surfaces inpainted/drawn, smooth alpha, overlap margins and correct draw order. A flat-image auto-segmentation result is only a rough starting point: do not label it finished. Record exceptions in `separation_issues.md`.
5. **Layered PSD:** Build a real layered RGB PSD with named groups/parts; PNGs alongside it are useful. Validate with `scripts/validate_psd.py`. A PSD merely containing a single composite layer fails.
6. **Cubism import:** When local access is present, guide/operate PSD import in Live2D Cubism Editor. Confirm ArtMeshes, then rig deformation/parameter keyforms, clipping, expressions, physics and model export. If only the official external integration API is available, it is NOT sufficient to auto-rig a model from scratch. Use GUI control only with explicit desktop tool access, permission and verification. No fabricated `.cmo3`, `.moc3` or `.model3.json` files.
7. **Live2D connection:** Read `references/live2d-integration.md`; optionally run `scripts/live2d_probe.py` locally. This probe connects and registers an integration; it does not modify the model and does not constitute a rigging engine.
8. **QC and packaging:** Check neutral pose, ± head movement, blink, mouth shapes, hair physics, sleeve and skirt deformation, meshes, z-order and visual artifacts. Deliver a transparent status table identifying what exists and what remains.

## Input
- Character brief, including desired degree of originality, references in `assets/`, output canvas sizes and image generation backend.
- Optional existing art/PSD and installed Cubism Editor.
- Never ask user for secrets in chat; store API keys in environment variables, never in reports or version control.

## Styling target — reference grounded
See `references/style-guide.md`. Target elegant high-detail anime aesthetics: fine line-weight variation; elaborate highlight/shadow treatment; hair with readable clumps and thin flyaways; expressive layered irises; thoughtfully rendered knitted, leather, metallic and translucent materials; anatomy and accessories consistent across turnarounds. Ensure animation-friendly baseline where eyes/mouth are clearly visible.

## Minimum layers
See `references/layer-manifest.md` for complete starting manifest. Eyes have distinct white, iris, pupil, highlights, upper/lower lashes, eyebrow, lid and occlusion pieces where appropriate; mouth has lip/outline, open cavity, tongue, teeth; hair subdivides by motion and depth; arms/hands independently segmented; torso/costume and joints need hidden-overlap fill. Numbers of layers vary; never assert a fixed number guarantees quality.

## Deliverable status tags
Use `PLANNED`, `GENERATED`, `LAYERED`, `IMPORTED`, `RIGGED`, `TESTED`, `EXPORTED`. Never advance a status without a corresponding artifact/test. Differentiating concept PNG from PSD from Cubism source from runtime export is mandatory.

## Commands
- `/vtuber-master [character description]` triggers this skill in Claude Code.
- `python scripts/validate_psd.py path/to/model.psd` inspects layer tree (requires `psd-tools`).
- `python scripts/live2d_probe.py` tests the local Cubism external integration (requires `websockets`).

## Required output directory
```
output/<character-name>/
  character_bible.md
  previews/                 # fullbody, expression, angle previews
  separated_layers/         # individual transparent layered artwork
  source/model.psd           # only if genuinely built
  live2d/                    # only after genuine Cubism work/export
  reports/qc.md
  reports/separation_issues.md
```

## Quality bar
Treat exact identity consistency, organic anatomy, anti-aliasing, no missing pixels during head turns, riggability and auditability as separate metrics. Require human art/rig review for commercial premium-grade deliverables; do not claim perfect automation.
