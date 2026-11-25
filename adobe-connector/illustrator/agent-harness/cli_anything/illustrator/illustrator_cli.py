"""cli-anything-illustrator: agent-friendly CLI for the real Adobe Illustrator (Windows, COM).

Run with no arguments for the REPL, or one-shot:  cli-anything-illustrator --json item list
Coordinates: points from the artboard's top-left, y down.
"""
from __future__ import annotations

import json
import os

import click

from cli_anything.illustrator import __version__
from cli_anything.illustrator.core import ops
from cli_anything.illustrator.utils.cli_common import add_json_to_all, build_mcp, call, ensure_utf8_stdout, run_repl

SKILL_PATH = os.path.join(os.path.dirname(__file__), "skills", "SKILL.md")


@click.group(invoke_without_command=True)
@click.option("--json", "as_json", is_flag=True, help="Machine-readable JSON output.")
@click.option("--doc", default=None, help="Open document to act on, by name (default: the active one).")
@click.version_option(__version__, prog_name="cli-anything-illustrator")
@click.pass_context
def cli(ctx, as_json, doc):
    """Control Adobe Illustrator: documents, layers, shapes, paths, text, trace, export. Units are points, y down."""
    ctx.ensure_object(dict)
    ctx.obj.setdefault("json", False)
    ctx.obj["json"] = ctx.obj["json"] or as_json
    ctx.obj["doc"] = doc
    if ctx.invoked_subcommand is None:
        run_repl(cli, "illustrator", __version__, SKILL_PATH)


def paint_options(f):
    f = click.option("--stroke-width", type=float, default=None)(f)
    f = click.option("--stroke", default=None, help="Hex colour or 'none'.")(f)
    return click.option("--fill", default=None, help="Hex colour or 'none'.")(f)


# ------------------------------------------------------------------ app / doc
@cli.group()
def app():
    """The Illustrator application."""


@app.command("info")
@click.pass_context
def app_info(ctx):
    call(ctx, ops.app_info)


@app.command("check")
@click.pass_context
def app_check(ctx):
    """Is Illustrator 2022 installed and registered? Starts nothing; exit code 1 if not."""
    call(ctx, ops.app_check)


@cli.group()
def doc():
    """Create, open, inspect, save, export and close documents."""


@doc.command("new")
@click.option("--width", type=float, default=612, show_default=True, help="Points (72 = 1 inch).")
@click.option("--height", type=float, default=792, show_default=True)
@click.option("--color-space", type=click.Choice(["rgb", "cmyk"]), default="rgb", show_default=True)
@click.pass_context
def doc_new(ctx, **kw):
    call(ctx, ops.doc_new, **kw)


@doc.command("open")
@click.argument("path")
@click.pass_context
def doc_open(ctx, path):
    """Open .ai, .pdf, .svg, .eps or an image."""
    call(ctx, ops.doc_open, path=path)


@doc.command("info")
@click.pass_context
def doc_info(ctx):
    call(ctx, ops.doc_info)


@doc.command("list")
@click.pass_context
def doc_list(ctx):
    call(ctx, ops.doc_list)


@doc.command("save")
@click.argument("path")
@click.option("--overwrite", is_flag=True)
@click.pass_context
def doc_save(ctx, path, overwrite):
    """Save as editable .ai or .pdf."""
    call(ctx, ops.doc_save, path=path, overwrite=overwrite)


@doc.command("export")
@click.argument("path")
@click.option("--format", "fmt", type=click.Choice(["png", "jpg", "svg"]), default=None, help="Default: from extension.")
@click.option("--scale", type=float, default=1.0, show_default=True)
@click.option("--opaque", is_flag=True, help="PNG with white background instead of transparency.")
@click.option("--quality", type=click.IntRange(0, 100), default=90, show_default=True)
@click.option("--overwrite", is_flag=True)
@click.pass_context
def doc_export(ctx, path, fmt, scale, opaque, quality, overwrite):
    """Export the active artboard (png/jpg/svg)."""
    call(ctx, ops.doc_export, path=path, fmt=fmt, scale=scale, transparent=not opaque, quality=quality, overwrite=overwrite)


@doc.command("close")
@click.option("--save", is_flag=True)
@click.pass_context
def doc_close(ctx, save):
    """Close (discards changes unless --save)."""
    call(ctx, ops.doc_close, save=save)


@doc.command("undo")
@click.option("--steps", type=int, default=1, show_default=True)
@click.pass_context
def doc_undo(ctx, steps):
    call(ctx, ops.doc_undo, steps=steps)


# ------------------------------------------------------------------ layers
@cli.group()
def layer():
    """Layers (found by name or 'Parent/Sublayer' path)."""


@layer.command("list")
@click.pass_context
def layer_list(ctx):
    call(ctx, ops.layer_list)


@layer.command("add")
@click.argument("name")
@click.option("--parent", default=None, help="Create as a sublayer of this layer.")
@click.pass_context
def layer_add(ctx, name, parent):
    call(ctx, ops.layer_add, name=name, parent=parent)


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
@click.option("--locked/--unlocked", default=None)
@click.option("--opacity", type=click.FloatRange(0, 100), default=None)
@click.pass_context
def layer_set(ctx, **kw):
    call(ctx, ops.layer_set, **kw)


@layer.command("select")
@click.argument("layer")
@click.pass_context
def layer_select(ctx, layer):
    """Make a layer active (new items go there)."""
    call(ctx, ops.layer_select, layer=layer)


@layer.command("arrange")
@click.argument("layer")
@click.argument("to", type=click.Choice(["front", "back", "forward", "backward"]))
@click.pass_context
def layer_arrange(ctx, layer, to):
    call(ctx, ops.layer_arrange, layer=layer, to=to)


# ------------------------------------------------------------------ drawing
@cli.command("shape")
@click.argument("kind", type=click.Choice(list(ops.SHAPES)))
@click.option("--x", type=float, required=True)
@click.option("--y", type=float, required=True)
@click.option("--w", type=float, required=True)
@click.option("--h", type=float, required=True)
@paint_options
@click.option("--radius", type=float, default=12, show_default=True, help="Corner radius (rounded-rect).")
@click.option("--sides", type=int, default=6, show_default=True, help="polygon")
@click.option("--points", type=int, default=5, show_default=True, help="star")
@click.option("--inner-ratio", type=float, default=0.5, show_default=True, help="star inner/outer radius")
@click.option("--name", default=None, help="Name it so later commands can find it.")
@click.option("--layer", default=None)
@click.pass_context
def shape_cmd(ctx, fill, **kw):
    """Draw rect, rounded-rect, ellipse, polygon, star or line in the box x,y,w,h."""
    call(ctx, ops.shape, fill=fill if fill is not None else "#000000", **kw)


@cli.command("path")
@click.option("--points", "pts", required=True,
              help='JSON list: [x,y] or {"x","y","in":[x,y],"out":[x,y],"corner":true}, e.g. "[[0,0],[100,50],[0,100]]"')
@click.option("--closed", is_flag=True)
@click.option("--smooth", is_flag=True, help="Curve smoothly through the points (corner points stay sharp).")
@paint_options
@click.option("--name", default=None)
@click.option("--layer", default=None)
@click.pass_context
def path_cmd(ctx, pts, closed, smooth, fill, stroke, stroke_width, name, layer):
    """Path through points: straight, smooth, or with your own Bezier handles."""
    try:
        points = json.loads(pts)
    except json.JSONDecodeError as exc:
        raise click.BadParameter(f"--points must be JSON: {exc}")
    call(ctx, ops.path_draw, points=points, closed=closed, smooth=smooth, fill=fill or "none",
         stroke=stroke or "#000000", stroke_width=stroke_width if stroke_width is not None else 1, name=name, layer=layer)


@cli.command("path-svg")
@click.option("--d", "data", required=True, help='SVG path data, e.g. "M10 80 C40 10 65 10 95 80 Z"')
@click.option("--fill-rule", default="evenodd", help="evenodd (inner parts cut holes) or nonzero.")
@paint_options
@click.option("--name", default=None)
@click.option("--layer", default=None)
@click.pass_context
def path_svg_cmd(ctx, data, fill_rule, fill, stroke, stroke_width, name, layer):
    """Curved path from SVG path data (M L H V C S Q T A Z); several M parts make a compound path."""
    call(ctx, ops.path_svg, d=data, fill_rule=fill_rule, fill=fill or "#000000", stroke=stroke or "none",
         stroke_width=stroke_width, name=name, layer=layer)


@cli.group()
def text():
    """Text frames."""


@text.command("add")
@click.argument("content")
@click.option("--x", type=float, required=True, help="Top-left x, pt.")
@click.option("--y", type=float, required=True, help="Top-left y, pt (down).")
@click.option("--size", type=float, default=24, show_default=True)
@click.option("--color", default="#000000", show_default=True)
@click.option("--font", default=None, help="PostScript name, e.g. ArialMT, Arial-BoldMT.")
@click.option("--name", default=None)
@click.option("--layer", default=None)
@click.pass_context
def text_add(ctx, content, **kw):
    call(ctx, ops.text_add, text=content, **kw)


@text.command("edit")
@click.argument("item")
@click.option("--content", "text", default=None)
@click.option("--size", type=float, default=None)
@click.option("--color", default=None)
@click.option("--font", default=None)
@click.pass_context
def text_edit(ctx, **kw):
    call(ctx, ops.text_edit, **kw)


# ------------------------------------------------------------------ items
@cli.group()
def item():
    """Page items (shapes, paths, text, groups, placed images), found by name."""


@item.command("list")
@click.option("--layer", default=None)
@click.pass_context
def item_list(ctx, layer):
    call(ctx, ops.item_list, layer=layer)


@item.command("set")
@click.argument("item_name")
@paint_options
@click.option("--opacity", type=click.FloatRange(0, 100), default=None)
@click.option("--hidden/--shown", default=None)
@click.option("--rename", default=None)
@click.option("--x", type=float, default=None, help="New left.")
@click.option("--y", type=float, default=None, help="New top.")
@click.option("--dx", type=float, default=None)
@click.option("--dy", type=float, default=None)
@click.option("--rotate", type=float, default=None, help="Degrees, counter-clockwise.")
@click.option("--scale", type=float, default=None, help="1.5 = 150%")
@click.option("--width", type=float, default=None)
@click.option("--height", type=float, default=None)
@click.pass_context
def item_set(ctx, item_name, **kw):
    """Change paint, opacity, visibility, name, position, rotation or size."""
    call(ctx, ops.item_set, item=item_name, **kw)


@item.command("delete")
@click.argument("item_name")
@click.pass_context
def item_delete(ctx, item_name):
    call(ctx, ops.item_delete, item=item_name)


@item.command("duplicate")
@click.argument("item_name")
@click.option("--name", default=None)
@click.option("--dx", type=float, default=0)
@click.option("--dy", type=float, default=0)
@click.pass_context
def item_duplicate(ctx, item_name, **kw):
    call(ctx, ops.item_duplicate, item=item_name, **kw)


@item.command("group")
@click.argument("items", nargs=-1, required=True)
@click.option("--name", default=None)
@click.pass_context
def item_group(ctx, items, name):
    call(ctx, ops.item_group, items=list(items), name=name)


@item.command("arrange")
@click.argument("item_name")
@click.argument("to", type=click.Choice(["front", "back", "forward", "backward"]))
@click.pass_context
def item_arrange(ctx, item_name, to):
    call(ctx, ops.item_arrange, item=item_name, to=to)


@item.command("gradient")
@click.argument("item_name")
@click.option("--stop", "stops", multiple=True, required=True, help="'#hex' or '#hex@position' (0-100), repeat 2+ times.")
@click.option("--kind", type=click.Choice(["linear", "radial"]), default="linear", show_default=True)
@click.option("--angle", type=float, default=0, show_default=True, help="Linear gradient angle, degrees.")
@click.pass_context
def item_gradient(ctx, item_name, stops, kind, angle):
    """Fill an item (path, group, compound path, text) with a gradient."""
    parsed = [[s.split("@")[0], float(s.split("@")[1])] if "@" in s else s for s in stops]
    call(ctx, ops.item_gradient, item=item_name, stops=parsed, kind=kind, angle=angle)


@cli.group()
def symbol():
    """Reusable symbols."""


@symbol.command("create")
@click.argument("item_name")
@click.argument("name")
@click.option("--remove-original", is_flag=True, help="Delete the source item after making the symbol.")
@click.pass_context
def symbol_create(ctx, item_name, name, remove_original):
    call(ctx, ops.symbol_create, item=item_name, name=name, keep_original=not remove_original)


@symbol.command("list")
@click.pass_context
def symbol_list(ctx):
    call(ctx, ops.symbol_list)


@symbol.command("place")
@click.argument("symbol_name")
@click.option("--x", type=float, default=0)
@click.option("--y", type=float, default=0)
@click.option("--scale", type=float, default=None)
@click.option("--name", default=None)
@click.option("--layer", default=None)
@click.pass_context
def symbol_place(ctx, symbol_name, **kw):
    """Place an instance with its top-left at x, y."""
    call(ctx, ops.symbol_place, symbol=symbol_name, **kw)


@cli.command("pathfinder")
@click.argument("op", type=click.Choice(list(ops.PATHFINDER)))
@click.argument("items", nargs=-1, required=True)
@click.option("--name", default=None, help="Name for the result.")
@click.pass_context
def pathfinder_cmd(ctx, op, items, name):
    """Combine named items: unite, minus-front, intersect, exclude, divide."""
    call(ctx, ops.pathfinder, op=op, items=list(items), name=name)


@cli.command("place")
@click.argument("path")
@click.option("--x", type=float, default=0)
@click.option("--y", type=float, default=0)
@click.option("--width", type=float, default=None)
@click.option("--name", default=None)
@click.option("--embed", is_flag=True)
@click.option("--layer", default=None)
@click.pass_context
def place_cmd(ctx, path, **kw):
    """Place an image or vector file."""
    call(ctx, ops.place, path=path, **kw)


@cli.group(invoke_without_command=True)
@click.pass_context
def trace(ctx):
    """Image Trace: 'trace image PATH' or 'trace presets'."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@trace.command("presets")
@click.pass_context
def trace_presets(ctx):
    call(ctx, ops.trace_presets)


@trace.command("image")
@click.argument("path")
@click.option("--preset", default=None, help="See 'trace presets'.")
@click.option("--x", type=float, default=0)
@click.option("--y", type=float, default=0)
@click.option("--width", type=float, default=None)
@click.option("--no-expand", is_flag=True, help="Keep it as a live trace object.")
@click.option("--name", default=None)
@click.option("--layer", default=None)
@click.option("--mode", type=click.Choice(["color", "gray", "bw"]), default=None)
@click.option("--colors", type=int, default=None, help="2-30 colours (colour mode).")
@click.option("--path-fidelity", type=float, default=None, help="0-100: higher follows the pixels more closely.")
@click.option("--corner-fidelity", type=float, default=None, help="0-100: higher keeps sharper corners.")
@click.option("--noise", type=float, default=None, help="1-100 px: shapes smaller than this are dropped.")
@click.option("--threshold", type=float, default=None, help="1-255 (bw mode).")
@click.option("--method", type=click.Choice(["abutting", "overlapping"]), default=None)
@click.option("--ignore-white/--keep-white", default=None, help="Drop white areas (clean backgrounds).")
@click.option("--snap-lines/--no-snap-lines", default=None, help="Snap near-straight curves to lines.")
@click.option("--drop-background", is_flag=True, help="Delete the shape(s) covering the whole image (traced background).")
@click.pass_context
def trace_image(ctx, path, no_expand, **kw):
    call(ctx, ops.trace, path=path, expand=not no_expand, **kw)


@cli.group()
def action():
    """Illustrator Actions."""


@action.command("play")
@click.argument("action_name")
@click.option("--set", "action_set", required=True)
@click.pass_context
def action_play(ctx, action_name, action_set):
    call(ctx, ops.action_play, action=action_name, action_set=action_set)


@cli.group()
def script():
    """Run raw ExtendScript (escape hatch)."""


@script.command("run")
@click.option("--code", default=None)
@click.option("--file", "path", type=click.Path(exists=True, dir_okay=False), default=None)
@click.pass_context
def script_run(ctx, code, path):
    if bool(code) == bool(path):
        raise click.UsageError("give exactly one of --code or --file")
    if path:
        with open(path, encoding="utf-8") as fh:
            code = fh.read()
    call(ctx, ops.script_run, code=code)


@cli.command()
def repl():
    """Interactive shell (default when no command is given)."""
    run_repl(cli, "illustrator", __version__, SKILL_PATH)


MCP_TOOLS = [
    (ops.app_check, "Check that Illustrator 2022 (the only version used) is installed, without starting it."),
    (ops.app_info, "Illustrator version, open documents and the active one."),
    (ops.doc_new, "Create a document with one artboard (points; 612x792 = US Letter)."),
    (ops.doc_open, "Open .ai/.pdf/.svg/.eps or an image by absolute path."),
    (ops.doc_info, "Document info: size, artboards, layer and item counts."),
    (ops.doc_list, "Info about every open document."),
    (ops.doc_save, "Save as editable .ai or .pdf. overwrite=true replaces an existing file."),
    (ops.doc_export, "Export the active artboard to png/jpg/svg (scale for png/jpg)."),
    (ops.doc_close, "Close; save=true saves first, otherwise changes are discarded."),
    (ops.doc_undo, "Undo N steps."),
    (ops.layer_list, "All layers and sublayers with visibility, lock, opacity and item counts."),
    (ops.layer_add, "Add a layer (or sublayer with parent); it becomes active."),
    (ops.layer_rename, "Rename a layer."),
    (ops.layer_delete, "Delete a layer and its contents."),
    (ops.layer_set, "Set visible, locked, opacity (0-100)."),
    (ops.layer_select, "Make a layer active."),
    (ops.layer_arrange, "Move a layer front/back/forward/backward."),
    (ops.shape, "Draw rect|rounded-rect|ellipse|polygon|star|line in box x,y,w,h (points, y down). fill/stroke hex or 'none'. Give name to edit later."),
    (ops.path_draw, "Draw a path through points: straight segments, smooth=true for curves through the points, or per-point Bezier handles. closed for a shape."),
    (ops.path_svg, "Draw real Bezier curves from SVG path data (M L H V C S Q T A Z), e.g. 'M10 80 C40 10 65 10 95 80 Z'. Best for organic shapes: flames, feathers, hair, leaves, lettering. Several M parts make one compound path (inner parts cut holes)."),
    (ops.text_add, "Add point text with top-left at x,y."),
    (ops.text_edit, "Change a text item's content, size, colour or font."),
    (ops.item_list, "List top-level items per layer: name, type, bounds [l,t,r,b], paint."),
    (ops.item_set, "Edit a named item: fill, stroke, opacity, hidden, rename, move, rotate, scale, size."),
    (ops.item_delete, "Delete a named item."),
    (ops.item_duplicate, "Duplicate a named item, offset by dx,dy."),
    (ops.item_group, "Group named items into one group."),
    (ops.item_arrange, "Move an item front/back/forward/backward."),
    (ops.place, "Place an image or vector file at x,y (width scales proportionally)."),
    (ops.trace_presets, "List Image Trace presets."),
    (ops.trace, "Place a raster image and Image Trace it into editable vector paths. Options (override preset): mode color|gray|bw, colors 2-30, path_fidelity, corner_fidelity 0-100, noise 1-100 px, threshold 1-255, method abutting|overlapping, ignore_white, snap_lines, drop_background (removes the traced full-image background shape)."),
    (ops.item_gradient, "Fill a named item with a linear or radial gradient."),
    (ops.symbol_create, "Make a named item into a reusable symbol."),
    (ops.symbol_list, "List the document's symbols."),
    (ops.symbol_place, "Place a symbol instance at x,y (optional scale)."),
    (ops.pathfinder, "Pathfinder on named items: unite, minus-front, intersect, exclude, divide (expanded result)."),
    (ops.action_play, "Play a recorded Illustrator Action."),
]

INSTRUCTIONS = (
    "Controls the user's real Adobe Illustrator on Windows. Coordinates are points from the active artboard's "
    "top-left, y down. Start with app_info or doc_new/doc_open; name items when you create them so you can edit "
    "them later; check with item_list and doc_export to a PNG you can look at. Paths must be absolute. "
    "Save with doc_save (.ai)."
)


@cli.command()
@click.option("--allowed-root", multiple=True, help="Only allow file paths under these folders (repeatable).")
@click.option("--allow-jsx", is_flag=True, help="Also expose script_run (arbitrary ExtendScript).")
def mcp(allowed_root, allow_jsx):
    """Run as an MCP stdio server."""
    tools = list(MCP_TOOLS)
    if allow_jsx:
        tools.append((ops.script_run, "Run raw ExtendScript in Illustrator for anything the other tools miss; "
                                      "returns the last expression's value."))
    build_mcp("illustrator", INSTRUCTIONS, tools, allowed_root).run("stdio")


add_json_to_all(cli)


def main():
    ensure_utf8_stdout()
    cli(obj={})


if __name__ == "__main__":
    main()
