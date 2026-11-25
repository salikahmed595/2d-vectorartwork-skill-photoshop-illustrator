# Photoshop harness notes

Backend: COM `Photoshop.Application` + `DoJavaScript` (ExtendScript). Each call sets pixel units and DialogModes.NO, then restores the user's preferences. Masks, adjustment layers, fill layers, layer styles, place and elliptical selections use Action Manager descriptors. Operations clear any selection before and after (in `finally`) so a failed call cannot leak a selection into the next one. New adjustment/fill layers are moved directly above their anchor because Photoshop otherwise nests them inside an active group.

Not covered by commands: smart filters, channels, paths/vector masks, multiple style instances; use `script run` (CLI) for those.
