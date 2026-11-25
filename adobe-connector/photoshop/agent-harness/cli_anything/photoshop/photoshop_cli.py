"""cli-anything-photoshop: agent-friendly CLI for the real Adobe Photoshop (Windows, COM).

Run with no arguments for the REPL, or one-shot:  cli-anything-photoshop --json layer list
"""
from __future__ import annotations

import json
import os

import click

from cli_anything.photoshop import __version__
from cli_anything.photoshop.core import ops
from cli_anything.photoshop.utils.cli_common import (
    add_json_to_all, build_mcp, call, ensure_utf8_stdout, parse_params, run_repl,
)

SKILL_PATH = os.path.join(os.path.dirname(__file__), "skills", "SKILL.md")


@click.group(invoke_without_command=True)
@click.option("--json", "as_json", is_flag=True, help="Machine-readable JSON output.")
@click.option("--doc", default=None, help="Open document to act on, by name (default: the active one).")
@click.version_option(__version__, prog_name="cli-anything-photoshop")
@click.pass_context
def cli(ctx, as_json, doc):
    """Control Adobe Photoshop: documents, layers, text, fills, filters, export. Units are pixels."""
    ctx.ensure_object(dict)
    ctx.obj.setdefault("json", False)
    ctx.obj["json"] = ctx.obj["json"] or as_json
    ctx.obj["doc"] = doc
    if ctx.invoked_subcommand is None:
        run_repl(cli, "photoshop", __version__, SKILL_PATH)


# ------------------------------------------------------------------ app
@cli.group()
def app():
    """The Photoshop application."""


@app.command("info")
@click.pass_context
def app_info(ctx):
    """Version, open documents, active document."""
    call(ctx, ops.app_info)


@app.command("check")
@click.pass_context
def app_check(ctx):
    """Is Photoshop 2023 installed and registered? Starts nothing; exit code 1 if not."""
    call(ctx, ops.app_check)


# ------------------------------------------------------------------ doc
@cli.group()
def doc():
    """Create, open, inspect, save, export and close documents."""


@doc.command("new")
@click.option("--width", type=int, required=True)
@click.option("--height", type=int, required=True)
@click.option("--resolution", type=float, default=72, show_default=True)
@click.option("--name", default="Untitled", show_default=True)
@click.option("--background", type=click.Choice(["white", "transparent", "background"]), default="white", show_default=True)
@click.pass_context
def doc_new(ctx, **kw):
    """New RGB document."""
    call(ctx, ops.doc_new, **kw)


@doc.command("open")
@click.argument("path")
@click.pass_context
def doc_open(ctx, path):
    """Open an image or PSD."""
    call(ctx, ops.doc_open, path=path)


@doc.command("info")
@click.pass_context
def doc_info(ctx):
    """Size, resolution, mode, layer count, saved state."""
    call(ctx, ops.doc_info)


@doc.command("list")
@click.pass_context
def doc_list(ctx):
    """All open documents."""
    call(ctx, ops.doc_list)


@doc.command("save")
@click.argument("path")
@click.option("--overwrite", is_flag=True, help="Replace an existing file.")
@click.pass_context
def doc_save(ctx, path, overwrite):
    """Save as layered PSD."""
    call(ctx, ops.doc_save, path=path, overwrite=overwrite)


@doc.command("export")
@click.argument("path")
@click.option("--format", "fmt", type=click.Choice(["png", "jpg", "tif"]), default=None, help="Default: from extension.")
@click.option("--quality", type=click.IntRange(0, 12), default=10, show_default=True, help="JPG quality 0-12.")
@click.option("--overwrite", is_flag=True)
@click.pass_context
def doc_export(ctx, **kw):
    """Export a flattened copy (png/jpg/tif); the open document is unchanged."""
    call(ctx, ops.doc_export, **kw)


@doc.command("close")
@click.option("--save", is_flag=True, help="Save changes before closing.")
@click.pass_context
def doc_close(ctx, save):
    """Close the document (discards changes unless --save)."""
    call(ctx, ops.doc_close, save=save)


@doc.command("resize")
@click.option("--width", type=int, required=True)
@click.option("--height", type=int, default=None, help="Default: keep aspect ratio.")
@click.pass_context
def doc_resize(ctx, **kw):
    """Resample the image (bicubic)."""
    call(ctx, ops.doc_resize, **kw)


@doc.command("flatten")
@click.pass_context
def doc_flatten(ctx):
    """Merge all layers."""
    call(ctx, ops.doc_flatten)


@doc.command("undo")
@click.option("--steps", type=int, default=1, show_default=True)
@click.pass_context
def doc_undo(ctx, steps):
    """Go back N steps from the latest history state."""
    call(ctx, ops.doc_undo, steps=steps)


# ------------------------------------------------------------------ layer
@cli.group()
def layer():
    """List and change layers. Layers are found by name or by group path like 'Group/Layer'."""


@layer.command("list")
@click.pass_context
def layer_list(ctx):
    """All layers top to bottom, with type, visibility, opacity, blend and bounds."""
    call(ctx, ops.layer_list)


@layer.command("add")
@click.argument("name")
@click.option("--group", default=None, help="Create it inside this group.")
@click.pass_context
def layer_add(ctx, name, group):
    """New empty pixel layer."""
    call(ctx, ops.layer_add, name=name, group=group)


@layer.command("group")
@click.argument("name")
@click.option("--layer", "layers", multiple=True, help="Layer to move into the group (repeatable).")
@click.pass_context
def layer_group(ctx, name, layers):
    """New group, optionally moving layers into it."""
    call(ctx, ops.layer_group, name=name, layers=list(layers))


@layer.command("rename")
@click.argument("layer")
@click.argument("name")
@click.pass_context
def layer_rename(ctx, layer, name):
    call(ctx, ops.layer_rename, layer=layer, name=name)


@layer.command("delete")
@click.argument("layer")
@click.pass_context
def layer_delete(ctx, layer):
    call(ctx, ops.layer_delete, layer=layer)


@layer.command("set")
@click.argument("layer")
@click.option("--visible/--hidden", default=None)
@click.option("--opacity", type=click.FloatRange(0, 100), default=None)
@click.option("--blend", default=None, help="normal, multiply, screen, overlay, softlight, ...")
@click.pass_context
def layer_set(ctx, **kw):
    """Visibility, opacity, blend mode."""
    call(ctx, ops.layer_set, **kw)


@layer.command("move")
@click.argument("layer")
@click.option("--dx", type=float, default=0)
@click.option("--dy", type=float, default=0)
@click.pass_context
def layer_move(ctx, **kw):
    """Shift a layer by dx, dy pixels."""
    call(ctx, ops.layer_move, **kw)


@layer.command("arrange")
@click.argument("layer")
@click.argument("to", type=click.Choice(["top", "bottom", "up", "down"]))
@click.pass_context
def layer_arrange(ctx, layer, to):
    """Change stacking order within its parent."""
    call(ctx, ops.layer_arrange, layer=layer, to=to)


@layer.command("duplicate")
@click.argument("layer")
@click.option("--name", default=None)
@click.pass_context
def layer_duplicate(ctx, layer, name):
    call(ctx, ops.layer_duplicate, layer=layer, name=name)


@layer.command("transform")
@click.argument("layer", required=False)
@click.option("--scale", type=float, default=None, help="Percent, e.g. 50.")
@click.option("--width", type=float, default=None, help="Fit visible pixels to this width, px.")
@click.option("--height", type=float, default=None, help="Fit visible pixels to this height, px.")
@click.option("--rotate", type=float, default=None, help="Degrees clockwise.")
@click.pass_context
def layer_transform(ctx, **kw):
    """Scale (about the centre) and/or rotate a layer."""
    call(ctx, ops.layer_transform, **kw)


@layer.command("select")
@click.argument("layer")
@click.pass_context
def layer_select(ctx, layer):
    """Make a layer active."""
    call(ctx, ops.layer_select, layer=layer)


# ------------------------------------------------------------------ text / fill / filter / place
@cli.group()
def text():
    """Text layers."""


@text.command("add")
@click.argument("content")
@click.option("--x", type=float, required=True, help="Baseline start, px.")
@click.option("--y", type=float, required=True, help="Baseline, px.")
@click.option("--size", type=float, default=48, show_default=True, help="px")
@click.option("--color", default="#000000", show_default=True)
@click.option("--font", default=None, help="PostScript name, e.g. ArialMT, Arial-BoldMT.")
@click.option("--name", default=None)
@click.pass_context
def text_add(ctx, content, **kw):
    call(ctx, ops.text_add, text=content, **kw)


@text.command("edit")
@click.argument("layer")
@click.option("--content", "text", default=None)
@click.option("--size", type=float, default=None)
@click.option("--color", default=None)
@click.option("--font", default=None)
@click.pass_context
def text_edit(ctx, **kw):
    call(ctx, ops.text_edit, **kw)


@cli.command("fill")
@click.argument("color")
@click.option("--x", type=float)
@click.option("--y", type=float)
@click.option("--w", type=float)
@click.option("--h", type=float)
@click.option("--shape", type=click.Choice(["rect", "ellipse"]), default="rect", show_default=True)
@click.option("--layer", default=None, help="Pixel layer to fill (default: active).")
@click.option("--new-layer", default=None, help="Create a new layer with this name and fill it.")
@click.option("--feather", type=float, default=None, help="Soft edge, px (box only).")
@click.option("--opacity", type=click.FloatRange(0.1, 100), default=100, show_default=True, help="Paint opacity %.")
@click.pass_context
def fill_cmd(ctx, color, **kw):
    """Fill a box (x y w h) or the whole layer with a hex colour."""
    call(ctx, ops.fill, color=color, **kw)


# ---------------------------------------------------------------- cutout & retouch
def _json_boxes(values, what):
    import json as _j
    out = []
    for v in values:
        try:
            out.append(_j.loads(v))
        except ValueError:
            raise click.BadParameter(f"{what} must be JSON like [x,y,w,h], got {v!r}")
    return out


@cli.command("cutout")
@click.argument("layer", required=False)
@click.option("--mode", type=click.Choice(["mask", "layer"]), default="mask", show_default=True,
              help="mask = hide background with a layer mask; layer = copy subject to a new layer.")
@click.option("--name", default=None, help="Name of the new layer (mode=layer).")
@click.option("--expand", type=float, default=0, show_default=True, help="Grow the selection, px.")
@click.option("--feather", type=float, default=0, show_default=True, help="Soften the edge, px.")
@click.pass_context
def cutout_cmd(ctx, **kw):
    """Select Subject (Photoshop AI) and cut the subject out."""
    call(ctx, ops.cutout, **kw)


@cli.command("remove")
@click.option("--spot", "spots", multiple=True, required=True, help="Area to remove as JSON [x,y,w,h] (repeatable).")
@click.option("--layer", default=None, help="Source pixel layer (default: active).")
@click.option("--new-layer", default="Retouch", show_default=True, help="Work on a copy with this name.")
@click.option("--in-place", is_flag=True, help="Edit the layer itself instead of a copy.")
@click.option("--shape", type=click.Choice(["rect", "ellipse"]), default="ellipse", show_default=True)
@click.option("--expand", type=float, default=4, show_default=True)
@click.pass_context
def remove_cmd(ctx, spots, layer, new_layer, in_place, shape, expand):
    """Content-Aware Fill over spots (blemishes, dust, small objects)."""
    call(ctx, ops.remove, spots=_json_boxes(spots, "--spot"), layer=layer,
         new_layer=None if in_place else new_layer, shape=shape, expand=expand)


@layer.command("from-box")
@click.argument("name")
@click.option("--x", type=float, required=True)
@click.option("--y", type=float, required=True)
@click.option("--w", type=float, required=True)
@click.option("--h", type=float, required=True)
@click.option("--shape", type=click.Choice(["rect", "ellipse"]), default="rect", show_default=True)
@click.option("--feather", type=float, default=0, show_default=True)
@click.option("--cut", is_flag=True, help="Cut instead of copy.")
@click.option("--layer", default=None, help="Source layer (default: active).")
@click.pass_context
def layer_from_box(ctx, **kw):
    """Copy (or cut) a region onto its own new layer."""
    call(ctx, ops.layer_from_box, **kw)


@cli.group()
def retouch():
    """Non-destructive retouching layers."""


@retouch.command("skin")
@click.option("--area", "areas", multiple=True, required=True, help="Ellipse to smooth as JSON [x,y,w,h] (repeatable).")
@click.option("--layer", default=None)
@click.option("--radius", type=float, default=8, show_default=True)
@click.option("--threshold", type=int, default=12, show_default=True)
@click.option("--strength", type=float, default=60, show_default=True, help="Layer opacity %.")
@click.option("--feather", type=float, default=12, show_default=True)
@click.option("--name", default="Skin smooth", show_default=True)
@click.pass_context
def retouch_skin(ctx, areas, **kw):
    """Surface-blur skin smoothing masked to the given areas."""
    call(ctx, ops.skin_smooth, areas=_json_boxes(areas, "--area"), **kw)


@retouch.command("dodge-burn")
@click.option("--stroke", "strokes", multiple=True, required=True,
              help='JSON {"x","y","w","h","mode":"dodge|burn","strength":20,"feather":px} (repeatable).')
@click.option("--name", default="Dodge & Burn", show_default=True)
@click.pass_context
def retouch_dodge_burn(ctx, strokes, name):
    """Soft dodge/burn dabs on a 50% grey Overlay layer."""
    call(ctx, ops.dodge_burn, strokes=_json_boxes(strokes, "--stroke"), name=name)


@retouch.command("sharpen")
@click.option("--layer", default=None)
@click.option("--radius", type=float, default=2, show_default=True)
@click.option("--strength", type=float, default=100, show_default=True)
@click.option("--name", default="Sharpen", show_default=True)
@click.pass_context
def retouch_sharpen(ctx, **kw):
    """High-pass sharpen layer (Overlay)."""
    call(ctx, ops.sharpen, **kw)


@cli.group("filter")
def filter_grp():
    """Pixel filters and adjustments."""


@filter_grp.command("list")
@click.pass_context
def filter_list(ctx):
    """Available filters and their parameters."""
    from cli_anything.photoshop.utils.cli_common import emit
    emit(ctx, ops.FILTERS)


@filter_grp.command("apply")
@click.argument("name")
@click.option("--param", "-p", multiple=True, help="key=value, e.g. -p radius=4")
@click.option("--layer", default=None)
@click.pass_context
def filter_apply(ctx, name, param, layer):
    call(ctx, ops.filter_apply, name=name, params=parse_params(param), layer=layer)


@cli.command("place")
@click.argument("path")
@click.option("--name", default=None)
@click.option("--x", type=float, default=None, help="Left edge of the visible pixels, px.")
@click.option("--y", type=float, default=None, help="Top edge of the visible pixels, px.")
@click.option("--rasterize", is_flag=True, help="Turn the smart object into pixels.")
@click.pass_context
def place_cmd(ctx, path, **kw):
    """Place an image file as a new layer."""
    call(ctx, ops.place, path=path, **kw)


@cli.group()
def mask():
    """Layer masks."""


def _box_options(f):
    for opt in reversed([
        click.option("--x", type=float), click.option("--y", type=float),
        click.option("--w", type=float), click.option("--h", type=float),
        click.option("--shape", type=click.Choice(["rect", "ellipse"]), default="rect", show_default=True),
        click.option("--feather", type=float, default=None, help="Soft edge, px."),
    ]):
        f = opt(f)
    return f


@mask.command("add")
@click.argument("layer", required=False)
@click.option("--hide", is_flag=True, help="Hide the box (or hide everything when no box).")
@_box_options
@click.pass_context
def mask_add(ctx, **kw):
    """Add a mask: with a box only that area shows (or is hidden with --hide). Replaces an existing mask."""
    call(ctx, ops.mask_add, **kw)


@mask.command("delete")
@click.argument("layer", required=False)
@click.option("--apply", is_flag=True, help="Bake the mask into the pixels first.")
@click.pass_context
def mask_delete(ctx, layer, apply):
    call(ctx, ops.mask_delete, layer=layer, apply=apply)


@cli.group()
def adjust():
    """Adjustment layers (non-destructive)."""


@adjust.command("list")
@click.pass_context
def adjust_list(ctx):
    from cli_anything.photoshop.utils.cli_common import emit
    emit(ctx, ops.ADJUSTMENTS)


@adjust.command("add")
@click.argument("kind")
@click.option("--param", "-p", multiple=True, help='key=value, e.g. -p saturation=20 or -p points="[[0,0],[128,150],[255,255]]"')
@click.option("--name", default=None)
@click.option("--clip", is_flag=True, help="Clip to the layer below only.")
@click.option("--above", default=None, help="Create it above this layer (default: the active layer).")
@click.pass_context
def adjust_add(ctx, kind, param, name, clip, above):
    """Add an adjustment layer."""
    call(ctx, ops.adjust_add, kind=kind, params=parse_params(param), name=name, clip=clip, above=above)


@cli.command("fill-layer")
@click.argument("kind", type=click.Choice(["solid", "gradient"]))
@click.option("--color", default=None, help="solid: hex colour.")
@click.option("--stop", "stops", multiple=True, help="gradient: '#hex' or '#hex@position' (0-100), repeat 2+ times.")
@click.option("--style", type=click.Choice(["linear", "radial"]), default="linear", show_default=True)
@click.option("--angle", type=float, default=90, show_default=True)
@click.option("--name", default=None)
@click.option("--above", default=None, help="Create it above this layer (default: the active layer).")
@click.pass_context
def fill_layer_cmd(ctx, kind, color, stops, style, angle, name, above):
    """Editable solid-colour or gradient fill layer."""
    parsed = [[s.split("@")[0], float(s.split("@")[1])] if "@" in s else s for s in stops] or None
    call(ctx, ops.fill_layer_add, kind=kind, color=color, stops=parsed, style=style, angle=angle, name=name, above=above)


@cli.group()
def style():
    """Layer styles: drop shadow, stroke, outer glow, colour overlay."""


@style.command("list")
@click.pass_context
def style_list(ctx):
    from cli_anything.photoshop.utils.cli_common import emit
    emit(ctx, ops.STYLE_KEYS)


@style.command("set")
@click.argument("layer", required=False)
@click.option("--drop-shadow", "drop_shadow", default=None, help='JSON options, e.g. \'{"distance":10,"size":8}\' or {}')
@click.option("--stroke", default=None, help='JSON, e.g. \'{"color":"#ffffff","size":4}\'')
@click.option("--outer-glow", "outer_glow", default=None, help="JSON options")
@click.option("--color-overlay", "color_overlay", default=None, help='JSON, e.g. \'{"color":"#ff0000"}\'')
@click.pass_context
def style_set(ctx, layer, **opts):
    """Set styles (replaces the layer's current styles)."""
    parsed = {}
    for k, v in opts.items():
        if v is not None:
            try:
                parsed[k] = json.loads(v)
            except json.JSONDecodeError as exc:
                raise click.BadParameter(f"--{k.replace('_', '-')} must be JSON: {exc}")
    call(ctx, ops.style_set, layer=layer, **parsed)


@style.command("clear")
@click.argument("layer", required=False)
@click.pass_context
def style_clear(ctx, layer):
    call(ctx, ops.style_clear, layer=layer)


@cli.group()
def action():
    """Photoshop Actions."""


@action.command("play")
@click.argument("action_name")
@click.option("--set", "action_set", required=True, help="Action set name.")
@click.pass_context
def action_play(ctx, action_name, action_set):
    call(ctx, ops.action_play, action=action_name, action_set=action_set)


@cli.group()
def script():
    """Run raw ExtendScript (escape hatch for anything not covered)."""


@script.command("run")
@click.option("--code", default=None, help="JSX code; the last expression's value is returned.")
@click.option("--file", "path", type=click.Path(exists=True, dir_okay=False), default=None)
@click.pass_context
def script_run(ctx, code, path):
    if bool(code) == bool(path):
        raise click.UsageError("give exactly one of --code or --file")
    if path:
        with open(path, encoding="utf-8") as fh:
            code = fh.read()
    call(ctx, ops.script_run, code=code)


# ------------------------------------------------------------------ repl / mcp
@cli.command()
def repl():
    """Interactive shell (default when no command is given)."""
    run_repl(cli, "photoshop", __version__, SKILL_PATH)


MCP_TOOLS = [
    (ops.app_check, "Check that Photoshop 2023 (the only version used) is installed, without starting it."),
    (ops.app_info, "Photoshop version, open documents and the active one."),
    (ops.doc_new, "Create a new RGB document (pixels). background: white|transparent|background."),
    (ops.doc_open, "Open an image or PSD by absolute path."),
    (ops.doc_info, "Info about a document (default: active)."),
    (ops.doc_list, "Info about every open document."),
    (ops.doc_save, "Save the document as layered .psd. overwrite=true replaces an existing file."),
    (ops.doc_export, "Export a flattened copy to png/jpg/tif (format from extension if not given)."),
    (ops.doc_close, "Close a document; save=true saves first, otherwise changes are discarded."),
    (ops.doc_resize, "Resample the image to width (and height, or keep aspect)."),
    (ops.doc_flatten, "Flatten all layers."),
    (ops.doc_undo, "Step back N history states from the latest."),
    (ops.layer_list, "All layers top-to-bottom with path, type, visibility, opacity, blend, bounds [l,t,r,b]."),
    (ops.layer_add, "Add an empty pixel layer (optionally inside a group)."),
    (ops.layer_group, "Create a group and move the named layers into it."),
    (ops.layer_rename, "Rename a layer (find by name or 'Group/Layer' path)."),
    (ops.layer_delete, "Delete a layer or group."),
    (ops.layer_set, "Set visible, opacity (0-100) and/or blend mode of a layer."),
    (ops.layer_move, "Translate a layer by dx, dy pixels."),
    (ops.layer_arrange, "Move a layer to top/bottom/up/down within its parent."),
    (ops.layer_duplicate, "Duplicate a layer, optionally naming the copy."),
    (ops.layer_select, "Make a layer active."),
    (ops.layer_transform, "Scale a layer about its centre (scale %, or fit to width/height px) and/or rotate (degrees clockwise)."),
    (ops.text_add, "Add a text layer. color is hex like #ff8800."),
    (ops.text_edit, "Change text, size, colour or font of a text layer."),
    (ops.fill, "Fill a rect/ellipse box (x,y,w,h) or a whole pixel layer with a hex colour; feather (px) and opacity (%) for soft paint."),
    (ops.cutout, "Select Subject (Photoshop AI) on a layer; mode=mask hides the background with a mask, mode=layer copies the subject to a new layer. Returns subjectBounds."),
    (ops.remove, "Content-Aware Fill over spots [[x,y,w,h],...] to remove blemishes/dust/small objects, on a copy layer 'Retouch' (new_layer=null edits in place)."),
    (ops.layer_from_box, "Copy (or cut=true) a rect/ellipse region of a layer onto a new named layer."),
    (ops.skin_smooth, "Skin smoothing: Surface Blur copy masked to ellipse areas [[x,y,w,h],...] at strength %."),
    (ops.dodge_burn, "Dodge/burn on a 50% grey Overlay layer. strokes=[{x,y,w,h,mode:'dodge'|'burn',strength,feather}]."),
    (ops.sharpen, "High-pass sharpen: Overlay High Pass copy of a layer (radius px, strength %)."),
    (ops.filter_apply, "Apply a filter to a pixel layer. Filters: " + "; ".join(f"{k}: {v}" for k, v in ops.FILTERS.items())),
    (ops.place, "Place an image file as a new layer at optional top-left x,y."),
    (ops.mask_add, "Add a layer mask (box shows only that area; hide=true hides it). Replaces an existing mask."),
    (ops.mask_delete, "Delete a layer mask; apply=true bakes it into the pixels."),
    (ops.adjust_add, "Add an adjustment layer. Kinds: " + "; ".join(f"{k}: {v}" for k, v in ops.ADJUSTMENTS.items())),
    (ops.fill_layer_add, "Add an editable solid or gradient fill layer."),
    (ops.style_set, "Set layer styles (replaces existing). Options: " + "; ".join(f"{k}: {v}" for k, v in ops.STYLE_KEYS.items())),
    (ops.style_clear, "Remove all layer styles from a layer."),
    (ops.action_play, "Play a recorded Photoshop Action from an action set."),
]

INSTRUCTIONS = (
    "Controls the user's real Adobe Photoshop on Windows. Units are pixels, origin top-left. "
    "Start with app_info or doc_new/doc_open; check with layer_list and doc_export to a PNG you can look at. "
    "Paths must be absolute. Layers are addressed by name or 'Group/Layer'. "
    "Save with doc_save(.psd); export never changes the open document."
)


@cli.command()
@click.option("--allowed-root", multiple=True, help="Only allow file paths under these folders (repeatable).")
@click.option("--allow-jsx", is_flag=True, help="Also expose script_run (arbitrary ExtendScript).")
def mcp(allowed_root, allow_jsx):
    """Run as an MCP stdio server."""
    tools = list(MCP_TOOLS)
    if allow_jsx:
        tools.append((ops.script_run, "Run raw ExtendScript in Photoshop for anything the other tools miss; "
                                      "returns the last expression's value (plain objects/arrays/strings/numbers)."))
    build_mcp("photoshop", INSTRUCTIONS, tools, allowed_root).run("stdio")


add_json_to_all(cli)


def main():
    ensure_utf8_stdout()
    cli(obj={})


if __name__ == "__main__":
    main()
