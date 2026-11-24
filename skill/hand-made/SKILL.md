---
name: hand-made
description: Reference-locked, 100% human-executed manual redrawing workflow for logos, emblems, illustrations and other artwork. Use when a client requires a visually identical hand-drawn recreation without generative AI in the artwork production process.
---

# HAND MADE — Human-Only Reference Redrawing Skill

## Absolute truth and operating boundary

This skill is **a human artist's instruction and quality-assurance checklist**, NOT an automated art-generation skill. An AI assistant **cannot** create, paint, trace, vectorize, retouch, or deliver a finished artwork and honestly certify that the artwork had **0% AI involvement** if the assistant did any of that production work.

When the client specifies **"not even 1% AI"**, use the strictest interpretation: do not use AI at any stage of the commissioned artwork's design, generation, modification, enhancement, or visual verification. The user may use this skill to organize instructions, but should **disclose that AI assisted with the written workflow** if the client's restriction also covers administrative planning. If the client forbids all AI involvement whatsoever, **stop using this AI skill for the job and hand the project directly to a human artist** with a human-authored brief.

No output may be described as "hand-drawn", "100% human-made", or "AI-free" unless verified by the human artist's truthful process record. Never generate deceptive process footage or fake layered source files.

## Mission

Guide an experienced human illustrator/designer to manually recreate each client-provided image with extremely high visual fidelity. Preserve the **exact existing design**: do not redesign, reinterpret, improve, add, remove, or stylize any element without explicit client permission. The brief and reference outrank generic design preferences.

### Non-negotiable constraints

1. **Reference lock:** Every supplied reference is an independent deliverable unless explicitly stated otherwise. Use the exact client's image as the single source of truth for that image. Do not combine references or guess missing content.
2. **No visual changes:** Keep silhouette, proportions, angles, spacing, alignment, pose, features, iconography, ornaments, text wording, font appearance, layout, surface textures, shading, highlights, palette, and background unchanged as closely as humanly possible.
3. **Hand execution:** Every drawn/painted/vector path, brush stroke, gradient, texture, highlight, shadow, and adjustment must be manually created or placed by the human artist. Manual artwork in Adobe Illustrator or Photoshop is allowed if the client approves digital hand-drawing.
4. **No AI artwork tools:** No text-to-image, image-to-image, generative fill, auto-redraw, auto-trace/vectorization, AI inpainting, AI upscaling, AI background removal, AI sharpening/retouching, AI-assisted selection/masking, or AI-controlled drawing agents. Avoid automatic Image Trace even where it is not marketed as AI; this commission specifically calls for a human redraw.
5. **No false provenance:** A manually cleaned-up AI image is not a completely hand-drawn image. Never claim otherwise.
6. **Background lock:** Keep the original background, including transparent, solid color, and/or negative-space regions. Do not replace it or introduce scenery.
7. **Color lock:** Sample the source colors with the normal eyedropper and visually match them; do not recolor. Preserve metallic, glow and shadow treatment through manual drawing.
8. **Typography lock:** Manually reproduce any logo lettering to match the source, including kerning, curves and perspective. Verify every character against the original.
9. **Fidelity over novelty:** No artistic enhancements or 'creative improvements' even if they might look prettier.
10. **No invented specifications:** If a reference file is missing or unreadable, request the exact source; never create an imagined version.

## Inputs the human artist needs

- Full-resolution original reference image(s), each clearly labeled.
- Required working size and export formats (ask client if unspecified).
- Whether digital hand-drawing in Illustrator/Photoshop is acceptable; whether manual tracing over a locked reference layer is acceptable.
- Whether transparency and any lettering must match the reference exactly.

Missing parameters must remain marked **not provided**. Do not make up client approvals.

## Human-only production workflow

### Phase 1 — Reference preservation

- Save the untouched originals to a `references_original/` folder. Do not edit these files.
- One reference image = one distinct artboard/file unless the client says otherwise.
- Visually inspect the whole composition and create a **manual inventory** of elements from top to bottom and foreground to background.
- Record exact text and the number, location and size of all symbols. Record color samples manually.
- Establish a matching-size artboard and consistent reference alignment. Preserve original aspect ratio.

### Phase 2 — Manual structural mapping

- Add the original as a locked, non-exporting reference layer in Photoshop or Illustrator.
- Human manually draws guide lines for center, symmetry, margins, silhouettes, and object boundaries.
- Human manually draws every path or brush stroke using pen, pencil, brush, shape, or bezier tools; no automatic tracing or AI.
- Compare alignment at multiple zoom levels. If the reference is asymmetrical, retain that asymmetry.

### Phase 3 — Manual detail recreation

- Draw large base forms first, then secondary shapes, then micro-details.
- Recreate line weights and edge quality manually.
- Rebuild light, dark, texture, wear and depth manually with ordinary non-AI drawing tools.
- Recreate exact color relationships and all original highlight / shadow directions.
- Hand-draw any typography and ornamentation to match the reference.
- Do not introduce stylistic changes during cleanup.

### Phase 4 — Manual verification (by human)

- Human artist compares reference and redrawing side by side at fit-to-screen and 100% zoom.
- Check silhouette; layout; margins; proportions; symmetry/asymmetry; count of objects; wording; color; background; shading; edges; texture; and tiny details.
- Use a **manual** transparency overlay or difference layer in conventional software, if client permits, to identify mismatches. No AI analysis or generation.
- Correct each discrepancy manually. Do not claim pixel-perfect identity; an independently hand-drawn recreation will usually have small differences.

### Phase 5 — Evidence and deliverables

- Save layered source file (.AI or .PSD as appropriate), plus client-approved PNG/SVG/PDF exports. SVG must be authored manually, not auto-traced.
- Preserve real work-in-progress versions, hand-drawn layers, and truthful screen recordings/timelapses **only if actually recorded**.
- Document the software and tools used, who drew the work, and the dates/hours if tracked. Never fabricate screenshots, timelines, strokes, or provenance records.
- Human artist signs an accurate completion declaration only after personally checking how the work was created.
- Request client approval with a reference-versus-redraw comparison. Any requested change beyond faithful reproduction needs separate approval.

## Fidelity checklist (human artist signs off)

- [ ] Each reference matched to its own deliverable
- [ ] All objects present; none added or removed
- [ ] Shape, pose, silhouettes and overall composition preserved
- [ ] Exact wording and logo lettering preserved
- [ ] Relative sizing, centering, spacing and angles preserved
- [ ] Original color theme and background preserved
- [ ] Original light, texture, material effects and visual style carefully matched
- [ ] All artwork drawn/painted manually by the human artist
- [ ] No generative AI or automatic trace/vectorization used on the artwork
- [ ] Layered editable source retained with authentic work history
- [ ] Human review completed; any deviations disclosed

## Example job — MACHINE CORPS emblem (reference provided in this conversation)

The provided reference shows a dark metal shield-like crest with a central menacing skull, glowing green eye sockets and forehead ring, large metallic wings on both sides, two crossed blades below the skull, **five stars across the top**, and curved **"MACHINE CORPS"** lettering along the bottom. The background outside the emblem is solid black. Keep the reference's grayscale/dark gunmetal metallic rendering and green glow. Preserve exact placement, shapes, surface details, text, lighting, and spacing, including any small asymmetries in the reference. **Do not reinterpret as a different skull, emblem, crest, wing set, sword layout, lettering style, or background.**

The client's text mentions **two reference logos**. Only one logo reference is available in this conversation. **Do not invent or complete the second logo** without receiving that exact image.

## Response contract when the skill is invoked

1. Say: "This is a human-only manual redrawing workflow. I can prepare a faithful production brief and review checklist, but I will not generate or modify the artwork under a no-AI-art requirement."
2. Reproduce a source-locked element inventory for each supplied reference. Explicitly mark missing references.
3. Give a concise step-by-step assignment for a human illustrator and a fidelity checklist. Prioritize identical reproduction above enhancements.
4. Do not output generated artwork or claim the commission is complete.
5. Never promise that AI-generated images, AI-produced vector code, or a simulated hand-drawn appearance satisfy a truly human-only client requirement.
