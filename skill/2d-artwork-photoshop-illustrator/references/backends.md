# Backends - what can actually make the picture

Machine inventory checked 2026-11-17. Re-check before relying on it (`nvidia-smi`, look for the
folders named below); delete or update lines that are no longer true.

## Verified on this machine
- GPU: NVIDIA GTX 1660 SUPER, 6 GB VRAM. CPU: Ryzen 5 2600. RAM: 32 GB.
- Disk: C: about 7 GB free (do not install anything large there). D: about 330 GB free.
- Python 3.12 with Pillow 12.3; `uv`; Node; Git.
- Blender 5.2 (`C:\Program Files\Blender Foundation\Blender 5.2\`), not on PATH.
- Live2D Cubism 5.3, VTube Studio, Figma desktop.
- Fonts: Windows set (Impact, Bahnschrift, Georgia, Arial Black, Gabriola) and
  `<fonts-folder>\` (Abrade-Bold, Avatar Airbender, ChillingSabrina, Munake).

## Team's normal tools (user, 2026-11-17)
The team usually makes these pieces in Adobe Photoshop and Illustrator. Prefer that route once the
apps are installed: layered PSD master, Illustrator for vector titles/lettering, both scriptable
(JSX via COM or `-r script.jsx`) so Claude can build layers, titles and exports. `finish.py` is the
fallback when Adobe is unavailable.

## Adobe route (verified 2026-11-20 on the cat-pfp job)
- Photoshop 25.12.0 and Illustrator 28.7.1 are installed and were running. Both are driven through
  the `photoshop` / `illustrator` MCP servers or the `cli-anything-photoshop` / `cli-anything-illustrator`
  CLIs (same operations; `script run --file x.jsx` is the escape hatch).
- Work folder: `%USERPROFILE%\Documents\Adobe-Work\<job>\` (`inbox`, `work`, `out`).
- MCP calls must go **one at a time**: two Adobe calls in one batch fail with "CoInitialize has not
  been called". If the MCP link drops mid-job ("Object is not connected to server"), switch to the
  CLI - it starts a fresh connection each call and can be batched in one shell command.
- New characters and scenes are drawn by Claude in Illustrator with `scripts/ai_draw.py` (spec of
  paths, gradients and blend modes; one layer per part). Verified 2026-11-21 on the v3 cat
  (`cat-pfp/v3/work/cat_design.py` -> `drawing.json`, 193 items, ~10 s per full redraw).
- Layer split and PSD assembly notes: `layered-components.md`.

## Not present on this machine
- No Krita, GIMP, Clip Studio, Affinity, Aseprite, Inkscape.
- No ComfyUI, Stable Diffusion WebUI, Forge, Fooocus or InvokeAI; Ollama has no models.
- No image-generation API key in the environment.

## Forbidden by the No-AI rule (user, 2026-11-20)
Do not use any of these for artwork, bases, references or trace sources, even if installed later:
- the `imagegen` worker in `<local-path>\workers\imagegen\`
  (Stable Diffusion 1.5 / DreamShaper / ControlNet);
- former Route A (ComfyUI / any local Stable Diffusion), Route B (user-supplied AI renders as a
  base) and Route C (hosted image APIs, Adobe Firefly);
- Photoshop Generative Fill / Expand, Neural Filters, AI upscalers (Real-ESRGAN and similar).
The user's own photos and hand-made art are fine as trace sources (say it is a trace).

## Supporting tools (not generators)
- `scripts/finish.py` / `scripts/qc.py` - finishing and checks, Pillow only.
- Blender 5.2 - optional compositing, 3D blockouts for hard poses or symmetrical vehicles/helmets
  to use as a pose/depth guide. Not a substitute for the illustration.
- Figma - title lettering experiments or client presentation boards.
