> **OBSOLETE (2026-11-21).** These were prompts for image generators, which the No-AI rule in
> `SKILL.md` forbids. Do not use them to generate images. The section structure (subject, pose,
> camera, light, background depth, palette) is still a useful checklist for the composition lock
> before drawing with `ai_draw.py`.

# Prompt recipes

Build every prompt in the same order so nothing is forgotten. Adapt the wording to the backend:
tag lists for anime SDXL checkpoints, plain sentences for natural-language generators.

## Skeleton
```
[LANE STYLE] [SUBJECT: who, species, age range, build] [FACE/HAIR/EYES] [OUTFIT + MATERIALS]
[POSE + EXPRESSION] [PROP] [CAMERA: framing, angle] [LIGHT: key, rim colour, emissive]
[BACKGROUND: far / mid / foreground] [PARTICLES] [PALETTE: two hues + accent]
[FINISH: clean lineart, cel shading, soft gradients, high detail] square 1:1, centred composition,
empty space at top for title, no text
```

Always end with `no text, no watermark, no signature, no logo` (or the negative-prompt equivalent).
Titles are added later by `finish.py`.

## Negative prompt (tag-style backends)
```
text, watermark, signature, logo, username, jpeg artifacts, lowres, blurry, bad anatomy, bad hands,
extra fingers, fused fingers, missing fingers, extra limbs, asymmetrical eyes, cross-eyed, deformed,
cropped head, out of frame, 3d render, photo, flat lighting, washed out colours
```
Drop `3d render` for lane 7 and `photo` conflicts for lane 9.

## Lane starters
Replace bracketed parts; keep the lighting and background structure.

1. **Cozy fantasy anime**
   `anime illustration, cel shading with soft gradients, [fox-eared girl, long wavy red hair, witch hat],
   [black and orange corset dress], kneeling, gentle smile looking at viewer, hand on a glowing
   jack-o-lantern on stacked books, enchanted forest at dusk, giant twisted trees framing the scene,
   violet mist, glowing mushrooms, falling autumn leaves, purple and orange palette, warm rim light`

2. **Pixel cyberpunk**
   `detailed pixel art, 16-bit style, [masked figure with angular helmet and glowing cyan visor],
   [black trench coat, tactical gear, neon trim], wide power stance facing viewer, ruined city on fire,
   collapsed highway, blue light beams across dark storm sky, embers, navy and orange palette with
   cyan glow, slight chromatic aberration`

3. **Storybook duo**
   `2D cartoon illustration, clean lineart, flat colours with soft shading, two characters full body,
   [silver-haired elf in dark blue armour, flustered, blushing], [blonde ranger with crossbow leaning
   in, teasing smile], cozy fantasy tavern interior, hanging lanterns, potion shelves, wooden beams,
   warm amber light, navy and amber palette`

4. **Neon vector**
   `flat vector illustration, bold shapes, glowing neon outlines, [hooded faceless figure with glowing
   magenta eyes], [long blue coat with luminous swirl patterns], reaching one gloved hand toward the
   viewer, foreshortening, moonlit lake and mountains, teal moon, meteor streaks, blue and violet
   palette with cyan and magenta accents`

5. **Flaming comic**
   `bold comic book illustration, thick ink outlines, mascot logo composition, symmetrical front view,
   [character + vehicle or weapon], engulfed in stylised flames forming a ring, dark red smoke
   background, embers, black and crimson palette with yellow-orange fire`

6. **Kawaii space**
   `bright anime illustration, cute, [girl in white and purple spacesuit, clear helmet, lavender hair,
   blue eyes], floating, waving, open smile, huge full moon directly behind her, colourful nebula,
   sparkling stars, earth in lower corner, white and violet palette`

7. **Mecha close-up**
   `hard-surface mecha illustration, glossy armour, extreme close-up of [helmet design] front view,
   perfectly symmetrical, large reflective compound eyes, crackling lightning, shattered rock debris,
   radial speed lines, crimson and violet palette with blue eyes`
   Design an original helmet unless the client supplies the character and accepts the rights note.

8. **Split-world**
   `anime illustration, [character], dynamic pose with [weapon], background split vertically: left
   [bamboo forest at night, blue, yellow lightning], right [gothic ruins under blood-red sky],
   full moon divided by the split, ground fog in both colours, sparks around the character`

9. **Semi-real couple**
   `semi-realistic anime portrait, soft skin shading, waist-up, [man: features, outfit] and
   [woman: features, outfit] standing close, relaxed smiles, night scene, full moon, city skyline,
   [setting elements for each of the clients' interests], warm practical lights, deep blue palette
   with warm orange accents`
   Game names on signs must be added in finishing, not generated.

## Settings to record in brief.md
Backend and model name, sampler/steps/CFG where applicable, seed, resolution, any LoRA or reference
image used, and the exact final prompt. A piece that cannot be reproduced cannot be revised.

## Revision moves
- Wrong mood -> change palette and light lines only; keep subject lines identical.
- Weak silhouette -> add `backlit, strong rim light, hazy background`; simplify background lines.
- Face fine, hands broken -> inpaint hands at high denoise with `detailed hand, five fingers`.
- Too busy at 64 px -> push camera closer (waist-up or bust) and cut foreground props.
