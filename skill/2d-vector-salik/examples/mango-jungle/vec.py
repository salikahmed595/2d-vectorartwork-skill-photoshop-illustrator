"""Shared vector helpers (copied from cat-pfp v7_design.py): Catmull-Rom paths, tapered strokes, ellipses, spec items."""
import math


def canvas_xy(x, y):
    return (x, y)


def mirror(pts):
    return [(-p[0], p[1]) + tuple(p[2:]) for p in pts]


# ---------- path builders ----------
def segments(pts, xf, closed=True):
    P = [xf(p[0], p[1]) for p in pts]
    corner = [len(p) > 2 for p in pts]
    n = len(P)

    def tan(i):
        if corner[i] or (not closed and i in (0, n - 1)):
            return (0.0, 0.0)
        a, b = P[(i - 1) % n], P[(i + 1) % n]
        return ((b[0] - a[0]) / 6, (b[1] - a[1]) / 6)

    T = [tan(i) for i in range(n)]
    segs = []
    for i in range(n if closed else n - 1):
        j = (i + 1) % n
        segs.append((P[i], (P[i][0] + T[i][0], P[i][1] + T[i][1]), (P[j][0] - T[j][0], P[j][1] - T[j][1]), P[j]))
    return segs


def path(pts, xf=canvas_xy, closed=True):
    segs = segments(pts, xf, closed)
    d = f"M {segs[0][0][0]:.1f} {segs[0][0][1]:.1f}"
    for _, c1, c2, p in segs:
        d += f" C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p[0]:.1f} {p[1]:.1f}"
    return d + (" Z" if closed else "")


def sample(pts, xf=canvas_xy, closed=False, per=14):
    out = []
    segs = segments(pts, xf, closed)
    for p0, c1, c2, p1 in segs:
        for k in range(per):
            t = k / per
            u = 1 - t
            out.append((u ** 3 * p0[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * p1[0],
                        u ** 3 * p0[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * p1[1]))
    if not closed:
        out.append(segs[-1][3])
    return out


def taper(pts, xf=canvas_xy, w=8.0, start=0.2, end=0.2, per=14):
    """Variable-width brush line as a filled shape: swells in the middle, tapers to points."""
    S = sample(pts, xf, False, per)
    m = len(S)
    L, R = [], []
    for i, (x, y) in enumerate(S):
        a, b = S[max(i - 1, 0)], S[min(i + 1, m - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        t = i / (m - 1)
        f = 1.0
        if start > 0:
            f *= math.sin(math.pi / 2 * min(1.0, t / start))
        if end > 0:
            f *= math.sin(math.pi / 2 * min(1.0, (1 - t) / end))
        ww = max(w * f, 0.35) / 2
        L.append((x + nx * ww, y + ny * ww))
        R.append((x - nx * ww, y - ny * ww))
    pl = L + R[::-1]
    return "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pl) + " Z"


def ellipse(cx, cy, rx, ry, rot=0.0, xf=canvas_xy):
    k = 0.5523
    pts = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))

    def P(u, v):
        x, y = u * rx, v * ry
        return xf(cx + x * c - y * s, cy + x * s + y * c)

    d = ""
    for i in range(4):
        u0, v0 = pts[i]
        u1, v1 = pts[(i + 1) % 4]
        p0 = P(u0, v0)
        c1 = P(u0 - v0 * k, v0 + u0 * k)
        c2 = P(u1 + v1 * k, v1 - u1 * k)
        p1 = P(u1, v1)
        if i == 0:
            d = f"M {p0[0]:.1f} {p0[1]:.1f}"
        d += f" C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p1[0]:.1f} {p1[1]:.1f}"
    return d + " Z"


def poly(pts, xf=canvas_xy):
    P = [xf(*p) for p in pts]
    return "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in P) + " Z"


def it(name, d, fill=None, **kw):
    o = {"name": name, "d": d, "fill": fill}
    o.update(kw)
    return o


def lin(stops, angle=-90):
    return {"type": "linear", "angle": angle, "stops": stops}


def rad(stops):
    return {"type": "radial", "stops": stops}



# ---------- mango-pfp shape builders ----------
def spine(base, ang, length, curl, n=12):
    """Curved centre line: starts at base heading `ang` degrees, turns by `curl` degrees over its length."""
    pts, (x, y) = [base], base
    for k in range(1, n + 1):
        a = math.radians(ang + curl * (k / n) ** 1.3)
        x, y = x + math.cos(a) * length / n, y + math.sin(a) * length / n
        pts.append((x, y))
    return pts


def leaf_outline(sp, width, prof=(0, .5, .9, 1, .85, .55, 0), skew=1.0):
    """Leaf outline around a spine: side A and side B, widths from the profile; returns (outline, sideA_half, sideB_half)."""
    m = len(sp)
    A, B = [], []
    for i, (x, y) in enumerate(sp):
        a, b = sp[max(i - 1, 0)], sp[min(i + 1, m - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        t = i / (m - 1)
        f = t * (len(prof) - 1)
        j = min(int(f), len(prof) - 2)
        w = (prof[j] + (prof[j + 1] - prof[j]) * (f - j)) * width / 2
        A.append((x + nx * w, y + ny * w))
        B.append((x - nx * w * skew, y - ny * w * skew))
    base, tip = sp[0] + ('c',), sp[-1] + ('c',)
    outline = [base] + A[1:-1] + [tip] + B[1:-1][::-1]
    half_a = [base] + A[1:-1] + [tip] + [p for p in sp[1:-1][::-1]]
    half_b = [base] + [p for p in sp[1:-1]] + [tip] + B[1:-1][::-1]
    return outline, half_a, half_b


def leaf_items(tag, base, ang, length, width, curl, xf, light="#64b04c", dark="#2c6c34", line="#163a20",
               rib="#d7ee9e", vein=None, rim=None, lw=5, skew=1.0, veins=5, scale=1.0):
    sp = spine(base, ang, length, curl)
    outline, ha, hb = leaf_outline(sp, width, skew=skew)
    items = [it(f"{tag} base", path(outline, xf), dark),
             it(f"{tag} lit half", path(ha, xf), light)]
    S = sample(sp, xf, False, 6)
    m = len(S)
    for k in range(1, veins + 1):
        i = int(m * (0.12 + 0.75 * k / (veins + 1)))
        x, y = S[i]
        a, b = S[max(i - 2, 0)], S[min(i + 2, m - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        ux, uy = dx / ln, dy / ln
        nx, ny = -uy, ux
        L = width * 0.42 * (1 - 0.5 * k / (veins + 1)) * scale
        for s in (1, -1):
            ex, ey = x + (nx * s * 0.85 + ux * 0.55) * L, y + (ny * s * 0.85 + uy * 0.55) * L
            items.append(it(f"{tag} vein {k}{s}", taper([(x, y), ((x + ex) / 2 + ux * 4, (y + ey) / 2 + uy * 4), (ex, ey)], canvas_xy, 2.6, 0.1, 0.6),
                            vein or line, opacity=55))
    items.append(it(f"{tag} rib", taper(sp, xf, 5, 0.05, 0.5), rib, opacity=85))
    if rim:
        items.append(it(f"{tag} rim", taper(outline[len(outline) // 2:] if rim == "B" else outline[:len(outline) // 2 + 1], xf, 7, 0.2, 0.2), "#ffd27a", opacity=90))
    items.append(it(f"{tag} line", path(outline, xf), None, stroke=line, stroke_width=lw))
    return items
