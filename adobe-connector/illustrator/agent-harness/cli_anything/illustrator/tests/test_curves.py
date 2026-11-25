"""Curved paths: SVG path data and smooth points become anchors with Bezier handles (no Illustrator needed).

An anchor is [x, y, in_x, in_y, out_x, out_y, smooth] in artboard points, y down.
"""
import math

import pytest

from cli_anything.illustrator.core.curves import MAX_ANCHORS, parse_svg_path, points_to_subpath
from cli_anything.illustrator.utils.jsx_backend import AdobeError

approx = pytest.approx


def xy(anchors):
    return [(a[0], a[1]) for a in anchors]


# ---------- SVG path data ----------

def test_straight_lines_have_handles_on_the_anchor():
    [sub] = parse_svg_path("M0 0 L10 0 L10 10 Z")
    assert sub["c"] is True
    assert sub["a"] == [[0, 0, 0, 0, 0, 0, False], [10, 0, 10, 0, 10, 0, False], [10, 10, 10, 10, 10, 10, False]]


def test_cubic_sets_the_out_handle_of_the_start_and_the_in_handle_of_the_end():
    [sub] = parse_svg_path("M0 0 C 0 -10 20 -10 20 0")
    assert sub["c"] is False
    assert sub["a"] == [[0, 0, 0, 0, 0, -10, False], [20, 0, 20, -10, 20, 0, False]]


def test_relative_commands_implicit_repeats_and_closing_onto_the_start():
    [sub] = parse_svg_path("m10 10 l5 0 5 5 h-10 v-5 z")
    # the last point lands on the start, so closing merges it instead of doubling the anchor
    assert sub["c"] is True and xy(sub["a"]) == [(10, 10), (15, 10), (20, 15), (10, 15)]


def test_closing_merge_keeps_the_incoming_handle_of_the_last_curve():
    [sub] = parse_svg_path("M0 0 L10 0 C 10 10 0 10 0 0 Z")
    assert xy(sub["a"]) == [(0, 0), (10, 0)]
    assert sub["a"][0][2:4] == [0, 10]          # in-handle of the first anchor comes from the closing curve
    assert sub["a"][1][4:6] == [10, 10]         # out-handle of (10,0) starts the curve


def test_quadratic_becomes_an_exact_cubic():
    [sub] = parse_svg_path("M0 0 Q 10 10 20 0")
    assert sub["a"][0][4:6] == approx([20 / 3, 20 / 3])
    assert sub["a"][1][2:4] == approx([40 / 3, 20 / 3])


def test_smooth_cubic_reflects_the_previous_control_point():
    [sub] = parse_svg_path("M0 0 C 0 10 10 10 10 0 S 20 -10 20 0")
    mid = sub["a"][1]
    assert mid[:6] == [10, 0, 10, 10, 10, -10] and mid[6] is True
    assert sub["a"][2][2:4] == [20, -10]


def test_smooth_quadratic_reflects_the_previous_control_point():
    [sub] = parse_svg_path("M0 0 Q 5 10 10 0 T 20 0")
    # T's control is (15,-10): out-handle of (10,0) = (10,0) + 2/3 * ((15,-10) - (10,0))
    assert sub["a"][1][4:6] == approx([10 + 10 / 3, -20 / 3])
    assert sub["a"][1][6] is True


def test_arc_is_split_into_quarter_circle_cubics_on_the_circle():
    [sub] = parse_svg_path("M0 0 A 10 10 0 0 1 20 0")
    assert [v for p in xy(sub["a"]) for v in p] == approx([0, 0, 10, -10, 20, 0])
    k = 4 / 3 * math.tan(math.pi / 8) * 10      # standard quarter-circle handle length
    assert sub["a"][0][4:6] == approx([0, -k])
    assert sub["a"][1][2:6] == approx([10 - k, -10, 10 + k, -10])


def test_full_circle_from_two_arcs_is_four_smooth_anchors():
    [sub] = parse_svg_path("M0 10 A10 10 0 1 1 20 10 A10 10 0 1 1 0 10 Z")
    assert sub["c"] is True and len(sub["a"]) == 4
    assert all(a[6] for a in sub["a"])
    for a in sub["a"]:
        assert math.hypot(a[0] - 10, a[1] - 10) == approx(10)


def test_arc_with_zero_radius_is_a_straight_line():
    [sub] = parse_svg_path("M0 0 A 0 5 0 0 1 10 0")
    assert sub["a"][1] == [10, 0, 10, 0, 10, 0, False]


def test_each_moveto_starts_a_new_subpath():
    subs = parse_svg_path("M0 0 H10 V10 H0 Z M3 3 H7 V7 H3 Z")
    assert len(subs) == 2 and all(s["c"] for s in subs)
    assert xy(subs[1]["a"]) == [(3, 3), (7, 3), (7, 7), (3, 7)]


def test_numbers_written_tightly_like_svg_tools_do():
    [sub] = parse_svg_path("M.5.5L-1e1,2.5e0l3-4")
    assert xy(sub["a"]) == [(0.5, 0.5), (-10, 2.5), (-7, -1.5)]


@pytest.mark.parametrize("d,msg", [
    ("", "empty"),
    ("L 1 2", "must start with M"),
    ("M 0 0 X 3 4", "Unknown"),
    ("M 0 0 L 5", "numbers"),
    ("M 0 0 L 5 nan", "Unknown"),
    ("M 0 0", "at least 2 points"),
])
def test_bad_path_data_is_explained(d, msg):
    with pytest.raises(AdobeError, match=msg):
        parse_svg_path(d)


def test_too_many_anchors_is_refused():
    d = "M0 0 " + "l1 0 " * (MAX_ANCHORS + 1)
    with pytest.raises(AdobeError, match="too many"):
        parse_svg_path(d)


# ---------- points ----------

def test_plain_points_stay_straight():
    s = points_to_subpath([[0, 0], [10, 10], [20, 0]], closed=False, smooth=False)
    assert s == {"c": False, "a": [[0, 0, 0, 0, 0, 0, False], [10, 10, 10, 10, 10, 10, False], [20, 0, 20, 0, 20, 0, False]]}


def test_smooth_points_get_catmull_rom_handles():
    s = points_to_subpath([[0, 0], [10, 10], [20, 0]], closed=False, smooth=True)
    mid = s["a"][1]
    assert mid[2:6] == approx([10 - 20 / 6, 10, 10 + 20 / 6, 10]) and mid[6] is True
    assert s["a"][0][2:6] == approx([0, 0, 10 / 6, 10 / 6])     # open ends: no handle outward
    assert s["a"][2][2:6] == approx([20 - 10 / 6, 10 / 6, 20, 0])


def test_corner_points_stay_sharp_inside_a_smooth_path():
    s = points_to_subpath([[0, 0], {"x": 10, "y": 10, "corner": True}, [20, 0]], closed=False, smooth=True)
    assert s["a"][1] == [10, 10, 10, 10, 10, 10, False]


def test_closed_smooth_paths_wrap_around():
    s = points_to_subpath([[0, 0], [10, 0], [10, 10], [0, 10]], closed=True, smooth=True)
    assert s["c"] is True and all(a[6] for a in s["a"])
    # neighbours are (0,10) and (10,0): tangent (10,-10)/6
    assert s["a"][0][2:6] == approx([-10 / 6, 10 / 6, 10 / 6, -10 / 6])


def test_explicit_handles_are_kept():
    s = points_to_subpath([[0, 0], {"x": 10, "y": 10, "in": [5, 10], "out": [15, 10]}], closed=False, smooth=False)
    assert s["a"][1] == [10, 10, 5, 10, 15, 10, True]
    bent = points_to_subpath([[0, 0], {"x": 10, "y": 10, "in": [5, 10], "out": [10, 20]}], closed=False, smooth=False)
    assert bent["a"][1][6] is False


@pytest.mark.parametrize("points,msg", [
    ([[0, 0]], "at least 2 points"),
    ([[0, 0], [1]], "point 2"),
    ([[0, 0], {"x": 1}], "point 2"),
    ([[0, 0], "abc"], "point 2"),
    ([[0, 0], [float("inf"), 1]], "point 2"),
    ([[0, 0], {"x": 1, "y": 1, "in": [1]}], "point 2"),
])
def test_bad_points_are_explained(points, msg):
    with pytest.raises(AdobeError, match=msg):
        points_to_subpath(points, closed=False, smooth=True)
