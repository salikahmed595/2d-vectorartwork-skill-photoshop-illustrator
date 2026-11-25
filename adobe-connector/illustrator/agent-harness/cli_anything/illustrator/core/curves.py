"""Curved paths for Illustrator: SVG path data and smooth points become anchors with Bezier handles.

Pure Python (no Illustrator), so it is unit-tested on its own. A subpath is {"c": closed, "a": anchors}; each anchor is
[x, y, in_x, in_y, out_x, out_y, smooth] in artboard points, y down. "in" is the handle towards the previous anchor
(Illustrator's leftDirection), "out" the handle towards the next one (rightDirection). A straight corner has both
handles on the anchor.
"""
from __future__ import annotations

import math
import re
from typing import Any

from cli_anything.illustrator.utils.jsx_backend import AdobeError

MAX_ANCHORS = 20_000
MAX_SUBPATHS = 500
MAX_PATH_DATA = 400_000
_TOKEN = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?|[\s,]+|.")
_ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}
_HELP = "Use SVG path commands M L H V C S Q T A Z with numbers, e.g. 'M10 80 C40 10 65 10 95 80 Z'."


def _corner(x: float, y: float) -> list:
    return [x, y, x, y, x, y, False]


def _is_smooth(a: list) -> bool:
    """Both handles exist and point in opposite directions along one line."""
    ix, iy, ox, oy = a[0] - a[2], a[1] - a[3], a[4] - a[0], a[5] - a[1]
    li, lo = math.hypot(ix, iy), math.hypot(ox, oy)
    if li < 1e-9 or lo < 1e-9:
        return False
    return abs(ix * oy - iy * ox) / (li * lo) < 0.01 and (ix * ox + iy * oy) > 0


def _finish(sub: dict) -> dict:
    for a in sub["a"]:
        a[6] = _is_smooth(a)
    return {"c": sub["c"], "a": sub["a"]}


def _tokens(d: str) -> list[str]:
    out = []
    for m in _TOKEN.finditer(d):
        t = m.group(0)
        if t.strip(" \t\r\n,") == "":
            continue
        if len(t) == 1 and t not in "MmLlHhVvCcSsQqTtAaZz" and not t.isdigit():
            raise AdobeError(f"Unknown text {t!r} in the path data. {_HELP}")
        out.append(t)
    return out


def _arc(x1, y1, rx, ry, phi_deg, large, sweep, x2, y2):
    """SVG elliptical arc as cubic segments [(c1, c2, end), ...] (SVG spec, implementation notes F.6.5)."""
    if abs(x1 - x2) < 1e-12 and abs(y1 - y2) < 1e-12:
        return []
    rx, ry = abs(rx), abs(ry)
    if rx == 0 or ry == 0:
        return [((x1, y1), (x2, y2), (x2, y2))]
    phi = math.radians(phi_deg % 360)
    c, s = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p, y1p = c * dx + s * dy, -s * dx + c * dy
    lam = x1p ** 2 / rx ** 2 + y1p ** 2 / ry ** 2
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    coef = math.sqrt(max(0.0, num / den)) if den else 0.0
    if large == sweep:
        coef = -coef
    cxp, cyp = coef * rx * y1p / ry, -coef * ry * x1p / rx
    cx, cy = c * cxp - s * cyp + (x1 + x2) / 2, s * cxp + c * cyp + (y1 + y2) / 2

    def angle(ux, uy, vx, vy):
        return math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)

    ux, uy = (x1p - cxp) / rx, (y1p - cyp) / ry
    t1 = angle(1, 0, ux, uy)
    dt = angle(ux, uy, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dt > 0:
        dt -= 2 * math.pi
    elif sweep and dt < 0:
        dt += 2 * math.pi
    n = max(1, math.ceil(abs(dt) / (math.pi / 2) - 1e-9))
    step = dt / n
    k = 4 / 3 * math.tan(step / 4)

    def point(t):
        return (cx + rx * math.cos(t) * c - ry * math.sin(t) * s, cy + rx * math.cos(t) * s + ry * math.sin(t) * c)

    def deriv(t):
        return (-rx * math.sin(t) * c - ry * math.cos(t) * s, -rx * math.sin(t) * s + ry * math.cos(t) * c)

    segs = []
    for j in range(n):
        ta, tb = t1 + j * step, t1 + (j + 1) * step
        pa, pb, da, db = point(ta), point(tb), deriv(ta), deriv(tb)
        end = (x2, y2) if j == n - 1 else pb
        segs.append(((pa[0] + k * da[0], pa[1] + k * da[1]), (pb[0] - k * db[0], pb[1] - k * db[1]), end))
    return segs


class _Builder:
    """Collects subpaths while the SVG commands are read."""

    def __init__(self):
        self.subs: list[dict] = []
        self.cur: dict | None = None
        self.total = 0

    def add(self, x: float, y: float) -> list:
        self.total += 1
        if self.total > MAX_ANCHORS:
            raise AdobeError(f"The path has too many anchors (max {MAX_ANCHORS}).")
        a = _corner(x, y)
        self.cur["a"].append(a)
        return a

    def flush(self):
        if self.cur is not None and len(self.cur["a"]) > 1:
            self.subs.append(_finish(self.cur))
            if len(self.subs) > MAX_SUBPATHS:
                raise AdobeError(f"The path has too many parts (max {MAX_SUBPATHS}).")
        self.cur = None

    def begin(self, x: float, y: float):
        self.flush()
        self.cur = {"c": False, "a": []}
        self.add(x, y)

    def close(self):
        if self.cur is None:
            return
        a = self.cur["a"]
        if len(a) > 1 and abs(a[0][0] - a[-1][0]) < 1e-9 and abs(a[0][1] - a[-1][1]) < 1e-9:
            a[0][2], a[0][3] = a[-1][2], a[-1][3]   # the closing curve's in-handle moves to the start anchor
            a.pop()
            self.total -= 1
        self.cur["c"] = True
        self.flush()


def parse_svg_path(d: str) -> list[dict]:
    """SVG path data -> subpaths of anchors. Each M starts a new subpath (several make a compound path)."""
    if not isinstance(d, str) or not d.strip():
        raise AdobeError(f"The path data is empty. {_HELP}")
    if len(d) > MAX_PATH_DATA:
        raise AdobeError(f"The path data is too long (max {MAX_PATH_DATA} characters).")
    toks = _tokens(d)
    b = _Builder()
    x = y = sx = sy = 0.0
    cmd: str | None = None
    prev = ""            # previous command (upper case), for S/T reflection
    ctrl = (0.0, 0.0)    # last control point of a cubic (C/S) or quadratic (Q/T)
    i = 0

    def take(n: int, arc: bool) -> list[float]:
        nonlocal i
        vals: list[float] = []
        while len(vals) < n:
            if i >= len(toks) or toks[i].isalpha():
                raise AdobeError(f"{cmd} needs {n} numbers. {_HELP}")
            t = toks[i]
            if arc and len(vals) in (3, 4) and t[0] in "01" and len(t) > 1:
                toks[i] = t[1:]   # compact arc flags such as "011" mean 0, 1, 1...
                t = t[0]
            else:
                i += 1
            v = float(t)
            if not math.isfinite(v):
                raise AdobeError(f"{cmd} needs finite numbers. {_HELP}")
            vals.append(v)
        return vals

    while i < len(toks):
        if toks[i].isalpha():
            cmd = toks[i]
            i += 1
        elif cmd is None:
            raise AdobeError(f"The path data must start with M. {_HELP}")
        elif cmd in "Zz":
            raise AdobeError(f"Z takes no numbers; start the next part with M. {_HELP}")
        up, rel = cmd.upper(), cmd.islower()
        if prev == "" and up != "M":
            raise AdobeError(f"The path data must start with M. {_HELP}")
        if up == "Z":
            b.close()
            x, y, prev = sx, sy, "Z"
            continue
        if b.cur is None and up != "M":
            b.begin(x, y)   # drawing on after Z starts a new part at the last start point
        ox, oy = (x, y) if rel else (0.0, 0.0)
        v = take(_ARGS[up], up == "A")

        if up == "M":
            x, y = ox + v[0], oy + v[1]
            sx, sy = x, y
            b.begin(x, y)
            cmd = "l" if rel else "L"   # more pairs after M are lines
        elif up == "L":
            x, y = ox + v[0], oy + v[1]
            b.add(x, y)
        elif up == "H":
            x = ox + v[0]
            b.add(x, y)
        elif up == "V":
            y = oy + v[0]
            b.add(x, y)
        elif up in "CS":
            if up == "C":
                x1, y1, x2, y2, nx, ny = ox + v[0], oy + v[1], ox + v[2], oy + v[3], ox + v[4], oy + v[5]
            else:
                x1, y1 = (2 * x - ctrl[0], 2 * y - ctrl[1]) if prev in ("C", "S") else (x, y)
                x2, y2, nx, ny = ox + v[0], oy + v[1], ox + v[2], oy + v[3]
            b.cur["a"][-1][4:6] = [x1, y1]
            b.add(nx, ny)[2:4] = [x2, y2]
            ctrl, x, y = (x2, y2), nx, ny
        elif up in "QT":
            if up == "Q":
                qx, qy, nx, ny = ox + v[0], oy + v[1], ox + v[2], oy + v[3]
            else:
                qx, qy = (2 * x - ctrl[0], 2 * y - ctrl[1]) if prev in ("Q", "T") else (x, y)
                nx, ny = ox + v[0], oy + v[1]
            b.cur["a"][-1][4:6] = [x + 2 / 3 * (qx - x), y + 2 / 3 * (qy - y)]
            b.add(nx, ny)[2:4] = [nx + 2 / 3 * (qx - nx), ny + 2 / 3 * (qy - ny)]
            ctrl, x, y = (qx, qy), nx, ny
        elif up == "A":
            nx, ny = ox + v[5], oy + v[6]
            for c1, c2, end in _arc(x, y, v[0], v[1], v[2], v[3] != 0, v[4] != 0, nx, ny):
                b.cur["a"][-1][4:6] = [c1[0], c1[1]]
                b.add(end[0], end[1])[2:4] = [c2[0], c2[1]]
            x, y = nx, ny
        prev = up

    b.flush()
    if not b.subs:
        raise AdobeError("A path needs at least 2 points.")
    return b.subs


def _xy(v: Any) -> tuple[float, float]:
    if isinstance(v, (list, tuple)) and len(v) == 2 and all(isinstance(n, (int, float)) and not isinstance(n, bool) for n in v):
        x, y = float(v[0]), float(v[1])
        if math.isfinite(x) and math.isfinite(y):
            return x, y
    raise ValueError


def points_to_subpath(points: list, closed: bool, smooth: bool) -> dict:
    """Points -> one subpath. A point is [x, y] or {"x", "y", "in": [x, y], "out": [x, y], "corner": bool}.
    smooth=True gives every point without its own handles a smooth curve through its neighbours (Catmull-Rom);
    "corner": true keeps that point sharp."""
    if not isinstance(points, (list, tuple)) or len(points) < 2:
        raise AdobeError("A path needs at least 2 points.")
    if len(points) > MAX_ANCHORS:
        raise AdobeError(f"The path has too many anchors (max {MAX_ANCHORS}).")
    anchors, fixed = [], []
    for n, p in enumerate(points, 1):
        try:
            if isinstance(p, dict):
                a = _corner(*_xy([p.get("x"), p.get("y")]))
                if p.get("in") is not None:
                    a[2:4] = list(_xy(p["in"]))
                if p.get("out") is not None:
                    a[4:6] = list(_xy(p["out"]))
                fixed.append(bool(p.get("corner")) or p.get("in") is not None or p.get("out") is not None)
            else:
                a = _corner(*_xy(p))
                fixed.append(False)
        except (ValueError, TypeError):
            raise AdobeError(f'point {n}: give [x, y] or {{"x": .., "y": .., "in": [x, y], "out": [x, y], "corner": true}}') from None
        anchors.append(a)

    if smooth:
        last = len(anchors) - 1
        for k, a in enumerate(anchors):
            if fixed[k]:
                continue
            has_prev, has_next = closed or k > 0, closed or k < last
            pa = anchors[(k - 1) % len(anchors)] if has_prev else a
            na = anchors[(k + 1) % len(anchors)] if has_next else a
            tx, ty = (na[0] - pa[0]) / 6, (na[1] - pa[1]) / 6
            if has_prev:
                a[2:4] = [a[0] - tx, a[1] - ty]
            if has_next:
                a[4:6] = [a[0] + tx, a[1] + ty]
    return _finish({"c": bool(closed), "a": anchors})
