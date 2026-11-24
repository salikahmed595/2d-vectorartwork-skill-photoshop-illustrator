# Baseline rig-ready layer manifest (adapt to actual character)

Recommended ordering is *conceptual*; verify exact z-order visually in Cubism. Each layer should be a visually complete RGBA object, not just a masked crop from composite.

- backmost: tail_back, back_hair_far_L/R, back_hair_main, accessories_behind
- body: torso_skin, neck, ear_L/R if appropriate, upper_arm_L/R, forearm_L/R, hand_L/R and finger groups if independent movement required
- face base: face_base, nose_shading, cheeks, blush_L/R, ears and ear_inner_L/R
- eye L and R separately: sclera, iris, pupil, iris_reflections, eye_highlights, upper_lash, lower_lash, eyelid_upper, eyelid_lower, eyebrow, closed_eye variants if needed
- mouth: lip_line, upper_lip, inner_mouth, tongue, upper_teeth, lower_teeth, closed_mouth variant
- hair mid: side_hair_L/R, side_lock_L/R, bangs_L/C/R, crown, flyaways on separately animated clumps
- outfit: underlayer, collar, neckline, chest garments, sleeves_L/R, cuff_L/R, jacket panels, bows, belts, fasteners, skirt front/back sections, accessories, pendant
- foreground: arms/hands/front-hair and accessories where their visual z-order demands

Coverage requirements:
1. Fill behind visible fragments (hair behind eyes, neck behind chin, shoulder underneath sleeve) based on anticipated movement.
2. Keep 15–40 px of extra overlap at a 4K working canvas as a *starting heuristic*, adjusted per expected rotation and region.
3. Use descriptive stable layer names, avoid numeric-only names.
4. Keep line and fill merged per final animation object when required by Cubism importer; do not mistake Photoshop adjustment layers for artwork texture layers.
5. Preserve full-resolution sources before destructive edits.
6. Verify both open and closed eyes, mouth phoneme shapes and exaggerated head turns.
