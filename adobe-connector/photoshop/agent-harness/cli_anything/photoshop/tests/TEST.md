# Tests: cli-anything-photoshop (v1.2.0)

## Coverage
- **test_core.py** (unit, no Adobe needed): CLI to op argument mapping, `--json` in either position,
  `--doc` injection, validation before the app is touched, overwrite protection, JSX helper typos,
  MCP tool schemas, readable MCP errors.
- **test_full_e2e.py** (real Adobe Photoshop): builds real documents, exports files, checks magic
  bytes, pixel colours and geometry, save + reopen round trip, readable errors, the installed
  `cli-anything-photoshop` executable via subprocess; v1.1: fill layers, masks, layer styles and all 7 adjustment types verified by exported pixels; layer-order regression after grouping.
- Shared backend (`/tests/test_shared.py`, 28 tests): the JSX wrapper is executed in Node.js;
  covers JSON round trip, error capture, injection through arguments, path roots.
- MCP stdio smoke: `/tests/mcp_smoke.py` (handshake, tool calls, outside-root refusal) and
  `/artifacts/registered_check.py` (servers as registered expose no `script_run`).

## Last run: 2026-11-19, Windows 11, Python 3.12
Full suite: 128 passed, 0 failed, 0 skipped in 5 min 22 s (`artifacts/test-run.txt`). v1.2 adds cutout (Select Subject), content-aware remove, skin smoothing, dodge & burn, high-pass sharpen, soft fill, layer transform / from-box (Photoshop) and Image Trace options + drop-background (Illustrator), all pixel- or count-checked in the real apps. The per-test list below is from v1.1.

```
photoshop/agent-harness/cli_anything/photoshop/tests/test_core.py::test_doc_new_passes_args PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_core.py::test_json_flag_after_subcommand PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_core.py::test_global_doc_is_injected PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_core.py::test_human_output PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_core.py::test_errors_exit_1_with_json PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_core.py::test_validation_before_photoshop[argv2-positive] PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_core.py::test_save_requires_psd PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_core.py::test_save_refuses_overwrite PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_core.py::test_filter_params_parsed PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_core.py::test_fill_colour_converted PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_core.py::test_script_requires_one_source PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_core.py::test_every_op_body_uses_known_helpers PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_core.py::test_mcp_tools_build_with_schemas PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_core.py::test_mcp_errors_reach_the_agent PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_core.py::test_gradient_stops_spacing_and_sort PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_core.py::test_style_json_options PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_core.py::test_mask_args PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_full_e2e.py::test_build_layered_document PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_full_e2e.py::test_filter_and_arrange PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_full_e2e.py::test_export_png_pixels PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_full_e2e.py::test_save_psd_and_reopen PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_full_e2e.py::test_place_resize_undo PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_full_e2e.py::test_errors_are_readable PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_full_e2e.py::test_script_escape_hatch PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_full_e2e.py::test_installed_cli_subprocess PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_full_e2e.py::test_fill_layers_masks_styles_adjustments PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_full_e2e.py::test_mask_errors PASSED
photoshop/agent-harness/cli_anything/photoshop/tests/test_full_e2e.py::test_adjustment_after_group_is_top_level PASSED
```