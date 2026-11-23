# v5 blueprint - "Moonlit Cat Mage" (2026-11-21)

**Concept.** The user's ginger tabby (green eyes, white muzzle and chest) redrawn as an anime cel-shaded
fantasy mage portrait, for a 2000x2000 PFP. The level of detail follows the user's three references:
clean tapered line art, 2-3 cel steps, rim light, glowing magic, particles and a deep layered night scene.
No character or art is copied from the references.

**Composition.**
- Bust, front view, head tilted 4 degrees.
- Eye-line at 39% of the height. The head sits inside the central circle.
- Navy mage cloak with the hood down as a cowl, gold rune trim, and a cyan crystal amulet at the clasp.
- A large cyan rune circle sits behind the head.
- Background: violet night sky, moon top right, castle spires far away, wisteria trees in the midground,
  and hanging wisteria framing the top corners.
- Cyan sparks and petals float around the cat.

**Light.**
- Warm key light from the front left.
- Cyan magic rim light from behind, on both edges.
- Cool moon rim on the right shoulder.
- The amulet throws a cyan under-light on the chin.

**Palette.**

| Role | Hex |
|---|---|
| Night navy | #0d0f2e |
| Violet | #4a2b80 |
| Wisteria | #b68fe0 |
| Ginger | #f29545 |
| Cream | #fff1dc |
| Cloak navy | #222b63 |
| Gold | #e8b85a |
| Glow cyan | #6ff6ff |
| Eye green | #7fd04a |

**Route.** Hybrid.
- Illustrator (`v5_design.py` -> `ai_draw.py`) for line art, flats and cel shadows, one layer per part.
- Photoshop (`render_psd.jsx`) for depth of field, the Lighting group, glow, bloom, grade, vignette and grain.
- Adobe cloud connector (non-generative) for a final tone check and preview of the flat master.

**Layers.** These are drawn in this order, from the bottom up:

| Group | Layers |
|---|---|
| Background art | Sky, Stars, Moon, Far castle, Mid trees |
| Magic | Rune circle |
| Cat | Cowl, Chest fluff, Cloak, Amulet, Ears, Head, Eyes, Nose & mouth, Whiskers |
| Near frame | Wisteria |
| FX | Particles |

The Photoshop Lighting, Glow and Grade layers go on top.

**Must keep.** The cat's identity: ginger tabby markings, green eyes, white muzzle and chest, pink nose.

**Gates.** Concept, construction, line, colour, lighting, detail, technical and delivery. Do at least 3 review passes.
