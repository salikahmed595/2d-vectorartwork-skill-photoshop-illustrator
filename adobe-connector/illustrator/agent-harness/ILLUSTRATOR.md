# Illustrator harness notes

Backend: COM `Illustrator.Application` + `DoJavaScript` (ExtendScript). Each call uses ARTBOARDCOORDINATESYSTEM and DONTDISPLAYALERTS, then restores them. Public coordinates are y-down; JSX converts with y -> -y (verified against SVG export in E2E). Pathfinder uses menu commands (Live Pathfinder + Expand); `app.redraw()` between them is required or they silently do nothing.

Not covered by commands: editing multiple artboards, brushes, effects/appearance, gradient meshes; use `script run` (CLI) for those.
