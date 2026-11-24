# Live2D Cubism external API — scope and setup

Official sources:
- https://docs.live2d.com/en/cubism-editor-manual/external-application-integration/
- https://docs.live2d.com/en/cubism-editor-manual/external-application-integration-api/
- https://docs.live2d.com/en/cubism-editor-manual/external-application-integration-api-list/
- https://docs.live2d.com/en/cubism-editor-manual/psd-import/

In Cubism Editor open File > External Application Integration Settings, enable connections, and manually authorize only a trusted local integration. Keep remote connections OFF. Default WebSocket port is 22033. Initial request uses RegisterPlugin with `Type: Request`, `Method: RegisterPlugin`, `Data: {Name: ...}`. Approval is a separate user action. Successful registration/connection does not indicate the bridge can construct meshes, warp deformers, keyforms or physics.

Do not write arbitrary automation commands assuming they exist in the official API. Inspect API function list and supported version at runtime. If deeper editing is necessary, use an explicitly available GUI computer-use tool or human operator to create and verify the rig. Prefer nondestructive backups of Cubism source files.

Use `python scripts/live2d_probe.py` for a passive connection check. The probe prints authorization instructions and does not change character parameters.
