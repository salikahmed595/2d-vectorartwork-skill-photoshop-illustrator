# VTuber Master Claude Code skill

## Windows installation
1. Extract this archive.
2. Copy the entire `vtuber-master` directory into `%USERPROFILE%\\.claude\\skills\\` (create directory if absent). Final file should be `%USERPROFILE%\\.claude\\skills\\vtuber-master\\SKILL.md`.
3. In Claude Code enter `/vtuber-master Create an original high-end VTuber character with a full-body neutral view and animation-ready layered PSD handoff`.
4. Connect your preferred supported image generation/drawing tool separately; the skill does not include image-generation credentials or direct control of desktop apps.
5. Open Live2D Cubism Editor locally, use File > External Application Integration Settings, turn on local integration and grant permission to your trusted bridge app.
6. Optional: `py -m pip install websockets psd-tools` and `py scripts\\live2d_probe.py` from the skill directory.

## Reality check
- The attached sample images are **style references**, not source rig assets.
- The bridge probe is read-only apart from registering itself. It does not rig a character.
- The user still needs an actual artwork generation/editing engine, a PSD composition step, and Cubism rigging (often manual or desktop-automated under supervision).
- Never report an exported `.moc3` until it has actually been exported from Cubism and tested.
