# Tests: cli-anything-illustrator (v1.2.0)

## Coverage
- **test_core.py** (unit, no Adobe needed): CLI to op argument mapping, `--json` in either position,
  `--doc` injection, validation before the app is touched, overwrite protection, JSX helper typos,
  MCP tool schemas, readable MCP errors.
- **test_full_e2e.py** (real Adobe Illustrator): builds real documents, exports files, checks magic
  bytes, pixel colours and geometry, save + reopen round trip, readable errors, the installed
  `cli-anything-illustrator` executable via subprocess; v1.1: gradients and all 5 Pathfinder operations verified by exported pixels and geometry; symbols create/place.
- Shared backend (`/tests/test_shared.py`, 28 tests): the JSX wrapper is executed in Node.js;
  covers JSON round trip, error capture, injection through arguments, path roots.
- MCP stdio smoke: `/tests/mcp_smoke.py` (handshake, tool calls, outside-root refusal) and
  `/artifacts/registered_check.py` (servers as registered expose no `script_run`).

## Last run: 2026-11-19, Windows 11, Python 3.12
Full suite: 128 passed, 0 failed, 0 skipped in 5 min 22 s (`artifacts/test-run.txt`). v1.2 adds cutout (Select Subject), content-aware remove, skin smoothing, dodge & burn, high-pass sharpen, soft fill, layer transform / from-box (Photoshop) and Image Trace options + drop-background (Illustrator), all pixel- or count-checked in the real apps. The per-test list below is from v1.1.

```
illustrator/agent-harness/cli_anything/illustrator/tests/test_core.py::test_shape_defaults_black_fill PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_core.py::test_paint_none_and_hex PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_core.py::test_line_gets_stroke_not_fill PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_core.py::test_path_points_json PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_core.py::test_validation_before_illustrator[argv2-inner_ratio] PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_core.py::test_bad_points_json_is_usage_error PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_core.py::test_save_only_ai_or_pdf PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_core.py::test_item_group_order PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_core.py::test_every_op_body_uses_known_helpers PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_core.py::test_mcp_tools_build_with_schemas PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_core.py::test_gradient_args PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_core.py::test_pathfinder_args PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_core.py::test_symbol_args PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_full_e2e.py::test_draw_everything PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_full_e2e.py::test_svg_geometry_matches_y_down PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_full_e2e.py::test_png_export_pixels PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_full_e2e.py::test_edit_items PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_full_e2e.py::test_layers PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_full_e2e.py::test_save_ai_and_reopen PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_full_e2e.py::test_place_and_trace PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_full_e2e.py::test_errors_and_undo PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_full_e2e.py::test_installed_cli_subprocess PASSED
illustrator/agent-harness/cli_anything/illustrator/tests/test_full_e2e.py::test_gradients_symbols_pathfinder PASSED
```