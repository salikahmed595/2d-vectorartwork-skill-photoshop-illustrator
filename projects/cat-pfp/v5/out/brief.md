# Cat PFP v5 - "Moonlit Cat Mage" (2026-11-21)

Why v5: the user rejected v4 ("this design sucks"). They asked for a full redraw at the level of detail of
their three anime fantasy references, using the connected Adobe connector. The blueprint is in `../work/blueprint.md`.

## Art direction
- **Subject:** the user's ginger tabby, keeping its green eyes, white muzzle and chest, pink nose and tabby
  stripes. It is redrawn as an anime cel-shaded mage: navy cloak with gold rune trim, a cyan crystal amulet,
  and a raised paw (toe beans up) holding a floating rune orb.
- **Scene:** a cyan rune circle behind the head; a violet night sky with stars and the moon top right;
  castle spires far off; wisteria trees in the midground; hanging wisteria framing the top left; cyan
  sparks and petals.
- **Light:** warm key light from the front left, cyan magic rim light from behind, a cool moon rim, and a
  cyan under-light from the amulet and the orb.
- **Format:** 2000x2000 sRGB.

## How it was made (no AI generation anywhere)
1. **Illustrator.**
   - `work/v5_design.py` writes about 2,370 hand-placed paths as an ai_draw spec.
   - Line art is drawn as tapered filled strokes: thick in the middle, pointed at the ends, and heavier on the shaded side.
   - Cel shading uses base, shadow and deep tones, plus fur-lock highlights. Eyes have a gradient iris, 32 fibres,
     a limbal ring, lid shadow, two catchlights and a cyan bounce.
2. **Review passes.** Previews are in `work/p1.png` to `p4.png`.
   - p1: small, flat head; tent-like cloak; confetti wisteria; too many bubbles.
   - p2: bigger head, narrower cloak, raceme wisteria, paw and orb added. The paw read as a fist.
   - p3 and p4: palm-up paw with pads, star embroidery instead of hooks, shading blotches toned down.
3. **Photoshop** (`work/render_psd.jsx`).
   - Depth of field on the far layers.
   - Rune glow and bloom.
   - A Lighting group masked to the cat silhouette: Form shade, Contact shadow, Key light, Magic under-light,
     Rune rim (silhouette edge band) and Moon rim.
   - Magic glow, colour grade, vignette and grain.
   - Preview `work/ps1.png` showed a ghost band from the moon-rim offset and a cyan wash on the cloak.
     `work/ps2.png` has both fixed and is the master.
4. **Adobe cloud connector** (signed-in account).
   - Capability check: the connector has no drawing tools and its generative features are unavailable, which the
     No-AI rule forbids anyway.
   - The master was uploaded to Creative Cloud as `cat-pfp/cat-pfp-v5_master.png`.
   - A non-generative `image_apply_adjustments` pass (contrast +12, vibrance +14, darks -10) produced
     `cat-pfp-v5_connector-grade.png`.

## Deliverables (`out/`)
- `cat-pfp-v5.psd`: layered, 39 layers, saved and reported by Photoshop.
- `cat-pfp-v5.ai`: editable vectors.
- `cat-pfp-v5_master.png`, `_2000_clean.jpg`, `_1080.webp`: local Photoshop grade.
- `cat-pfp-v5_connector-grade.png` and `_2000.jpg`: the same art after the Adobe connector tone pass. It is slightly punchier.
- `parts/`: one PNG per layer, plus `manifest.json`.
- `qc/`: circle crops at 256 and 64 px, and the QC json.

## Layers (PSD, top to bottom)

| Group or layer | Contents |
|---|---|
| Magic glow | |
| Colour grade | |
| Vignette | |
| Grain | |
| FX | Particles |
| Near frame | Wisteria |
| Lighting | Form shade, Contact shadow, Key light, Magic under-light, Rune rim, Moon rim |
| Cat | Paw & orb, Whiskers, Nose & mouth, Eyes, Head, Ears, Amulet, Cloak, Chest fluff, Cowl |
| Magic | Rune glow, Rune bloom, Rune circle, Circle halo |
| Background art | Ground mist, Mid trees, Far castle, Moon glow, Moon, Stars, Sky |

Legs and tail are not in frame.

## Checks run
- `qc.py` on the master and on the connector grade: no fails, no warnings. I viewed the 256 and 64 px circle
  crops, and the face and orb read at 64 px.
- I read back the Photoshop layer list after the build.
- **Not run:**
  - a per-layer hide test;
  - a pixel diff between the PSD recomposite and the AI artboard.

  The master PNG is exported from the PSD itself.

## Honest limits
- This is hand-placed vector path work plus Photoshop light. It is not human tablet brushwork.
- Up close, the fur is stylised cel locks rather than painted strands.
- The mid-ground trees are blurred blobs, not drawn foliage.
- The references set the level of detail and the mood only. No character, layout or artwork from them was copied.
