"""Seam 1: the gate terminal prints reggate's mint tractor-feed paper. Height 172 keeps reggate's 43-unit fiber tile in phase across the join."""
import math

W, H, DUR = 880, 172, 12
DARK, MINT, INK, RULE = "#0d1117", "#e2edda", "#203b44", "#91a895"
LINES = ("That terminal is a joke Aadi is very proud of.", "I'm the narrator. I'll take it from here.")
FEED_START, FEED_END = 5.4, 6.2
PRINT = ((6.7, 8.5), (8.85, 10.45))
HEAD_IN, HEAD_OUT = 6.3, 11.0
GLYPHS = {
    "T": "#####/..#../..#../..#../..#../..#../..#..", "A": ".###./#...#/#...#/#####/#...#/#...#/#...#",
    "I": ".###./..#../..#../..#../..#../..#../.###.", "a": "...../...../.###./....#/.####/#...#/.####",
    "d": "....#/....#/.##.#/#..##/#...#/#...#/.####", "e": "...../...../.###./#...#/#####/#..../.###.",
    "f": "..##./.#..#/.#.../###../.#.../.#.../.#...", "h": "#..../#..../#.##./##..#/#...#/#...#/#...#",
    "i": "..#../...../.##../..#../..#../..#../.###.", "j": "...#./...../..##./...#./...#./...#./...#./#..#./.##..",
    "k": "#..../#..../#..#./#.#../##.../#.#../#..#.", "l": ".##../..#../..#../..#../..#../..#../.###.",
    "m": "...../...../##.#./#.#.#/#.#.#/#.#.#/#.#.#", "n": "...../...../#.##./##..#/#...#/#...#/#...#",
    "o": "...../...../.###./#...#/#...#/#...#/.###.", "p": "...../...../####./#...#/#...#/#...#/####./#..../#....",
    "r": "...../...../#.##./##..#/#..../#..../#....", "s": "...../...../.####/#..../.###./....#/####.",
    "t": ".#.../.#.../####./.#.../.#.../.#..#/..##.", "u": "...../...../#...#/#...#/#...#/#..##/.##.#",
    "v": "...../...../#...#/#...#/#...#/.#.#./..#..", "y": "...../...../#...#/#...#/#...#/#..##/.##.#/....#/.###.",
    ".": "...../...../...../...../...../.##../.##..", "'": "..#../..#../.#.../...../...../...../.....", " ": "",
}
DESK = {"key": "d", "slot": 64, "edge_end": (-44, 132), "bend": (6, 40, 92, 46), "dot": 2.5, "dot_w": 2.05, "strike": .7, "base": (92, 125),
        "bars": ((72, 105, .62, False), (138, 167, .42, True)), "hole": (2.5, 2.4, 13, 8), "inset": (11, 11), "perf": 13, "head": True}
PHONE = {"key": "p", "slot": 58, "edge_end": (-52, 72), "bend": (4, 12, 58, 20), "dot": 3, "dot_w": 2.6, "strike": .6, "base": (88, 130),
         "bars": ((63, 99, .62, False), (141, 168, .42, True)), "hole": (3.4, 2.2, 19, 12), "inset": (8, 8), "perf": 9, "head": False}


def pf_keys(pairs, eased=()):
    times = ";".join(f"{p[0] / DUR:.4f}" for p in pairs)
    values = ";".join(str(p[1]) for p in pairs)
    splines = ";".join("0.4 0 0.2 1" if i in eased else "0 0 1 1" for i in range(len(pairs) - 1))
    return f'dur="{DUR}s" repeatCount="indefinite" keyTimes="{times}" values="{values}" calcMode="spline" keySplines="{splines}"'


def pf_track(attr, pairs, eased=()):
    return f'<animate attributeName="{attr}" {pf_keys(pairs, eased)}/>'


def pf_move(pairs, eased=()):
    return f'<animateTransform attributeName="transform" type="translate" {pf_keys(pairs, eased)}/>'


def pf_cubic(a, b, c, d, u):
    v = 1 - u
    return tuple(v ** 3 * a[i] + 3 * v * v * u * b[i] + 3 * v * u * u * c[i] + u ** 3 * d[i] for i in (0, 1))


def pf_controls(L):
    x, y = L["slot"] + 8, 21
    ex, ey = L["edge_end"]
    b = L["bend"]
    return (x, y), (x - b[0], y + b[1]), (ex + b[2], ey - b[3]), (ex, ey)


def pf_rail(L, inset, mirror):
    a, b, c, d = pf_controls(L)
    points = []
    for step in range(-16, 161):
        u = step / 160
        if u < 0:
            x0, y0 = a
            tx, ty = b[0] - a[0], b[1] - a[1]
            size = math.hypot(tx, ty)
            px, py = x0 + tx / size * u * 400, y0 + ty / size * u * 400
            nx, ny = ty / size, -tx / size
            grow = 0
        else:
            px, py = pf_cubic(a, b, c, d, u)
            qx, qy = pf_cubic(a, b, c, d, min(1, u + .004))
            rx, ry = pf_cubic(a, b, c, d, max(0, u - .004))
            size = math.hypot(qx - rx, qy - ry)
            nx, ny = (qy - ry) / size, -(qx - rx) / size
            grow = u
        depth = inset[0] + inset[1] * grow
        x, y = px + nx * depth, py + ny * depth
        points.append((W - x if mirror else x, y))
    lengths = [0.0]
    for p, q in zip(points, points[1:]):
        lengths.append(lengths[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    return points, lengths


def pf_at(rail, s):
    points, lengths = rail
    s = max(0, min(lengths[-1], s))
    for i in range(1, len(lengths)):
        if lengths[i] >= s:
            span = lengths[i] - lengths[i - 1] or 1
            k = (s - lengths[i - 1]) / span
            return (points[i - 1][0] + (points[i][0] - points[i - 1][0]) * k, points[i - 1][1] + (points[i][1] - points[i - 1][1]) * k)
    return points[-1]


def pf_d(points):
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in points)


def pf_holes(L, mirror, animated):
    r0, r1, p0, p1 = L["hole"]
    rail = pf_rail(L, L["inset"], mirror)
    total = rail[1][-1]
    stations = [0.0]
    while stations[-1] < total:
        stations.append(stations[-1] + p0 + p1 * stations[-1] / total)
    radius = lambda s: round(r0 + r1 * s / total, 2)
    out = []
    for i in range(len(stations) - 2):
        s0, s1 = stations[i], stations[i + 2]
        x, y = pf_at(rail, s0)
        if not animated:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius(s0)}"/>')
            continue
        steps = max(3, int((s1 - s0) / 4))
        path = pf_d([pf_at(rail, s0 + (s1 - s0) * j / steps) for j in range(steps + 1)])
        a, b = FEED_START / DUR, FEED_END / DUR
        out.append(f'<circle r="{radius(s0)}">'
                   + pf_track("r", [(0, radius(s0)), (FEED_START, radius(s0)), (FEED_END, radius(s1)), (DUR, radius(s1))], (1,))
                   + f'<animateMotion path="{path}" dur="{DUR}s" repeatCount="indefinite" keyPoints="0;0;1;1" keyTimes="0;{a:.4f};{b:.4f};1" calcMode="spline" keySplines="0 0 1 1;0.4 0 0.2 1;0 0 1 1"/></circle>')
    return "".join(out)


def pf_perf(L, mirror, animated):
    depth = (L["inset"][0] + L["perf"], L["inset"][1] + L["perf"])
    d = pf_d(pf_rail(L, depth, mirror)[0][::3])
    motion = pf_track("stroke-dashoffset", [(0, 0), (FEED_START, 0), (FEED_END, -30), (DUR, -30)], (1,)) if animated else ""
    return f'<path d="{d}" fill="none" stroke="{RULE}" stroke-width=".9" stroke-dasharray="3 3">{motion}</path>'


def pf_dots(text, x0, base, pitch, strike):
    out, cx, cy = [], 0.0, 0.0
    for n, ch in enumerate(text):
        rows = GLYPHS[ch].split("/") if GLYPHS[ch] else []
        for r, row in enumerate(rows):
            for c, cell in enumerate(row):
                if cell != "#":
                    continue
                x, y = round(x0 + (n * 6 + c) * pitch, 1), round(base + (r - 6) * pitch, 1)
                out.append(f"m{round(x - cx, 1):g} {round(y - cy, 1):g}h{strike:g}")
                cx, cy = round(x + strike, 1), y
    return "".join(out)


def pf_width(text, pitch):
    return (len(text) * 6 - 1) * pitch


def pf_paper_d(L):
    a, b, c, d = pf_controls(L)
    return (f"M{a[0]} {a[1]}C{b[0]} {b[1]} {c[0]} {c[1]} {d[0]} {d[1]}V{H + 4}H{W - d[0]}V{d[1]}"
            f"C{W - c[0]} {c[1]} {W - b[0]} {b[1]} {W - a[0]} {a[1]}Z")


def pf_head():
    return ('<g><rect x="-9" y="-23" width="18" height="31" rx="2" fill="#1b232c" stroke="#3a4653"/>'
            '<rect x="-9" y="-9" width="18" height="6" fill="#0d1117"/>'
            '<path d="M-5 -16h10M-5 -13h10" stroke="#566575" stroke-width="1"/>'
            '<rect x="-2" y="-3" width="4" height="9" fill="#79bbff" opacity=".85"/></g>')


def pf_scene(L):
    k = L["key"]
    sx = L["slot"]
    pitch = L["dot"]
    paper = pf_paper_d(L)
    x = [round(440 - pf_width(line, pitch) / 2, 1) for line in LINES]
    widths = [round(pf_width(line, pitch) + pitch, 1) for line in LINES]
    dots = [pf_dots(line, x[i], L["base"][i], pitch, L["strike"]) for i, line in enumerate(LINES)]
    fade_fill = f"url(#pf-{k}-fade)"
    bars = "".join(f'<rect y="{a}" width="{W}" height="{b - a}" fill="{fade_fill if fade else "#c9dcbf"}" opacity="{o}"/>' for a, b, o, fade in L["bars"])
    last = L["bars"][-1]
    defs = (f'<defs><clipPath id="pf-{k}-paper"><path d="{paper}"/></clipPath>'
            f'<clipPath id="pf-{k}-head"><rect y="21" width="{W}" height="{H}"/></clipPath>'
            f'<linearGradient id="pf-{k}-shade" gradientUnits="userSpaceOnUse" x1="0" y1="21" x2="0" y2="37">'
            f'<stop offset="0" stop-color="{DARK}" stop-opacity=".34"/><stop offset="1" stop-color="{DARK}" stop-opacity="0"/></linearGradient>'
            f'<linearGradient id="pf-{k}-fade" gradientUnits="userSpaceOnUse" x1="0" y1="{last[0]}" x2="0" y2="{last[1]}">'
            '<stop offset="0" stop-color="#c9dcbf"/><stop offset="1" stop-color="#c9dcbf" stop-opacity="0"/></linearGradient>'
            + "".join(f'<path id="pf-{k}-l{i}" d="{d}" fill="none" stroke="{INK}" stroke-width="{L["dot_w"]}" stroke-linecap="round"/>' for i, d in enumerate(dots))
            + "".join(f'<clipPath id="pf-{k}-c{i}"><rect x="{x[i] - 2}" y="{L["base"][i] - 24}" width="{widths[i] + 2}" height="36">'
                      + pf_track("width", [(0, widths[i] + 2), (FEED_END, widths[i] + 2), (FEED_END + .02, 0), (PRINT[i][0], 0), (PRINT[i][1], widths[i] + 2), (DUR, widths[i] + 2)])
                      + '</rect></clipPath>' for i in range(2))
            + '</defs>')
    machine = (f'<rect x="{sx - 14}" y="7" width="{W - 2 * sx + 28}" height="23" rx="3" fill="#151b23" stroke="#2c3743"/>'
               f'<path d="M{sx - 13} 8.5H{W - sx + 13}" stroke="#222b35"/>'
               f'<rect x="{sx}" y="14" width="{W - 2 * sx}" height="10" rx="1.5" fill="#04060a"/>')
    edge = (f'<path d="{paper}" fill="none" stroke="#04060a" stroke-opacity=".5" stroke-width="4"/>'
            f'<path d="{paper}" fill="{MINT}"/>')
    sheet = (f'<g clip-path="url(#pf-{k}-paper)">{bars}<rect width="{W}" height="{H}" fill="url(#pf-fiber)"/>'
             f'<rect y="21" width="{W}" height="16" fill="url(#pf-{k}-shade)"/></g>')
    throat = f'<rect x="{sx}" y="14" width="{W - 2 * sx}" height="7" rx="1.5" fill="#04060a"/><path d="M{sx} 21.5H{W - sx}" stroke="#39444f" stroke-width=".8"/>'

    def perforation(animated):
        holes = f'<g fill="{DARK}" stroke="#aebba6" stroke-width=".7">{pf_holes(L, False, animated)}{pf_holes(L, True, animated)}</g>'
        return f'<g clip-path="url(#pf-{k}-paper)">{pf_perf(L, False, animated)}{pf_perf(L, True, animated)}{holes}</g>'

    still = perforation(False) + "".join(f'<use href="#pf-{k}-l{i}"/>' for i in range(2))
    printed = "".join(
        f'<g>{pf_move([(0, "0 0"), (FEED_START, "0 0"), (FEED_END, "0 30"), (FEED_END + .03, "0 0"), (DUR, "0 0")], (1,))}'
        + pf_track("opacity", [(0, 1), (FEED_START, 1), (FEED_END, 0), (FEED_END + .03, 1), (DUR, 1)])
        + f'<g clip-path="url(#pf-{k}-c{i})"><use href="#pf-{k}-l{i}"/></g></g>' for i in range(2))
    head = ""
    if L["head"]:
        top = -14
        y0, y1 = L["base"]
        x0, x1 = x[0], x[1]
        end0, end1 = round(x0 + widths[0], 1), round(x1 + widths[1], 1)
        path = [(0, f"{x0} {top}"), (HEAD_IN, f"{x0} {top}"), (PRINT[0][0], f"{x0} {y0}"), (PRINT[0][1], f"{end0} {y0}"), (PRINT[1][0], f"{x1} {y1}"),
                (PRINT[1][1], f"{end1} {y1}"), (HEAD_OUT, f"{end1} {top}"), (HEAD_OUT + .01, f"{x0} {top}"), (DUR, f"{x0} {top}")]
        head = f'<g clip-path="url(#pf-{k}-head)"><g transform="translate({x0} {top})">{pf_move(path, (1, 3, 5))}{pf_head()}</g></g>'
    led = (f'<circle cx="{W - sx + 7}" cy="19" r="2" fill="#3fb950" opacity=".45">'
           + pf_track("opacity", [(0, .45), (HEAD_IN, .45), (HEAD_IN + .1, 1), (HEAD_OUT, 1), (HEAD_OUT + .2, .45), (DUR, .45)]) + '</circle>')
    return (f'<g class="{k}">{defs}{machine}{edge}{sheet}{throat}'
            f'<g class="replay">{perforation(True)}{printed}{head}{led}</g>'
            f'<g class="still">{still}<circle cx="{W - sx + 7}" cy="19" r="2" fill="#3fb950" opacity=".45"/></g></g>')


def build(s):
    style = ("<style>.still,.p{display:none}@media (max-width:500px){.d{display:none}.p{display:inline}}"
             "@media (prefers-reduced-motion:reduce){.replay{display:none}.still{display:inline}}</style>")
    fiber = ('<defs><pattern id="pf-fiber" width="71" height="43" patternUnits="userSpaceOnUse">'
             '<path d="M2 6l3 -.6m17 12 4 1m19 14 3 -.5m10 -26 2 .4m-51 29 4 .2" fill="none" stroke="#69795c" opacity=".20" stroke-width=".7"/></pattern></defs>')
    body = f'{style}{fiber}<rect width="{W}" height="{H}" fill="{DARK}"/>{pf_scene(DESK)}{pf_scene(PHONE)}'
    label = " ".join(LINES)
    return s.svg(W, H, label, [], body)
