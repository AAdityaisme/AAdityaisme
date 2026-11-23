"""Seam 4, "Lights down": the white page dims, its plot dots defocus and pull through a chrome lens into the dark room.

Edge bands stay flat and static, so row 0 is exactly #ffffff and the last row exactly #1d1424.
"""

L4_H = 177
L4_DUR = 12
L4_PAPER, L4_ROOM = "#ffffff", "#1d1424"
L4_LINE = "Then someone paid him to check the models directly."
L4_BLUE, L4_ORANGE = "#1f77b4", "#ff7f0e"
L4_LIT = {"b": "#8fcbf3", "o": "#ffc58a"}
L4_PULL = (0.45, 0.0, 0.55, 1.0)
L4_DESK_DOTS = [(318, 38, "b"), (345, 25, "b"), (371, 44, "o"), (397, 28, "b"), (424, 23, "b"), (486, 23, "o"),
                (513, 30, "b"), (538, 45, "b"), (561, 26, "o"), (586, 40, "b"), (604, 24, "b")]
L4_PHONE_DOTS = [(120, 40, "b"), (214, 26, "o"), (306, 42, "b"), (388, 25, "b"), (494, 25, "o"), (578, 42, "b"), (668, 27, "b"), (760, 40, "o")]


def l4_hex(color):
    return [int(color[i:i + 2], 16) for i in (1, 3, 5)]


def l4_ramp():
    top, bottom, y0, y1 = l4_hex(L4_PAPER), l4_hex(L4_ROOM), 6, 126
    stops = []
    for i in range(17):
        u = i / 16
        e = u * u * (3 - 2 * u)
        rgb = "".join(f"{min(255, round(a + (b - a) * e + d * 4 * e * (1 - e))):02x}" for a, b, d in zip(top, bottom, (5, -7, 6)))
        stops.append(f'<stop offset="{(y0 + (y1 - y0) * u) / L4_H:.4f}" stop-color="#{rgb}"/>')
    return f'<linearGradient id="l4-room" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{L4_H}">{"".join(stops)}</linearGradient>'


def l4_disc(name, color):
    return (f'<radialGradient id="{name}"><stop offset="0" stop-color="{color}" stop-opacity=".40"/>'
            f'<stop offset=".68" stop-color="{color}" stop-opacity=".50"/><stop offset=".9" stop-color="{color}" stop-opacity=".66"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>')


def l4_defs():
    chrome = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in
                     [(0, "#fbfcfd"), (.2, "#b9bec6"), (.38, "#eef0f3"), (.55, "#6e717b"), (.72, "#c4c7cf"), (1, "#3a3641")])
    return ("<defs>" + l4_ramp() + l4_disc("l4-b", L4_BLUE) + l4_disc("l4-o", L4_ORANGE)
            + l4_disc("l4-lb", L4_LIT["b"]) + l4_disc("l4-lo", L4_LIT["o"])
            + f'<linearGradient id="l4-chrome" x1="0" y1="0" x2=".35" y2="1">{chrome}</linearGradient>'
            + '<linearGradient id="l4-beam" gradientUnits="userSpaceOnUse" x1="0" y1="100" x2="0" y2="170">' + "".join(f'<stop offset="{o}" stop-color="#fff3df" stop-opacity="{a}"/>' for o, a in
                                                      [(0, .58), (.31, .3), (.69, .085), (1, 0)]) + '</linearGradient>'
            + '<radialGradient id="l4-spill"><stop offset="0" stop-color="#fff" stop-opacity=".62"/><stop offset=".55" stop-color="#fff" stop-opacity=".3"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
            + '<radialGradient id="l4-glass" cx=".5" cy=".62" r=".62"><stop offset="0" stop-color="#fff6e6" stop-opacity=".82"/><stop offset=".42" stop-color="#d9c6dc" stop-opacity=".34"/>'
            + '<stop offset="1" stop-color="#1d1424" stop-opacity=".78"/></radialGradient></defs>')


def l4_cross(fraction):
    x1, y1, x2, y2 = L4_PULL
    lo, hi = 0.0, 1.0
    for _ in range(40):
        s = (lo + hi) / 2
        y = 3 * (1 - s) ** 2 * s * y1 + 3 * (1 - s) * s * s * y2 + s ** 3
        lo, hi = (s, hi) if y < fraction else (lo, s)
    return 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s * s * x2 + s ** 3


def l4_track(attr, keys, transform=False):
    keys = [(0, keys[0][1], None)] * (keys[0][0] > 0) + list(keys)
    if keys[-1][0] < L4_DUR:
        keys.append((L4_DUR, keys[-1][1], None))
    times = ";".join(f"{k[0] / L4_DUR:.5f}" for k in keys)
    values = ";".join(str(k[1]) for k in keys)
    splines = ";".join(" ".join(f"{v:g}" for v in (k[2] or (0, 0, 1, 1))) for k in keys[:-1])
    head = f'<animateTransform attributeName="transform" type="translate"' if transform else f'<animate attributeName="{attr}"'
    return f'{head} dur="{L4_DUR}s" repeatCount="indefinite" calcMode="spline" keyTimes="{times}" values="{values}" keySplines="{splines}"/>'


def l4_dot(i, x, y, kind, cx, cy, grow):
    r0 = (4.7 if kind == "o" else 3.8) * grow
    big = min((13 + (i * 7) % 7) * grow, y - 8)
    k = .85
    ex, ey = round(cx + k * (cx - x), 1), round(cy + k * (cy - y), 1)
    soft = (.45, 0, .55, 1)
    d0, d1 = 1.15 + i * .05, 2.55 + i * .05
    p0, p1 = 2.75 + i * .13, 6.0 + i * .13
    pc = round(p0 + (p1 - p0) * l4_cross(1 / (1 + k)), 3)
    off = 8.85
    back = round(9.35 + i * .07, 3)
    color, lit = f"url(#l4-{kind})", f"url(#l4-l{kind})"
    solid = L4_ORANGE if kind == "o" else L4_BLUE
    move = l4_track("transform", [(0, f"{x} {y}", None), (p0, f"{x} {y}", L4_PULL), (p1, f"{ex} {ey}", None), (off, f"{ex} {ey}", None),
                                  (off + .01, f"{x} {y}", None)], True)
    sharp = l4_track("opacity", [(0, 1, None), (d0, 1, soft), (d0 + .7, 0, None), (back, 0, soft), (back + .6, 1, None)])
    blur_r = l4_track("r", [(0, r0, None), (d0, r0, soft), (d1, round(big, 1), None), (p0, round(big, 1), soft), (pc, round(3 * grow, 1), None)])
    blur_o = l4_track("opacity", [(0, 0, None), (d0, 0, soft), (d0 + .6, 1, None), (round(pc - .1, 3), 1, soft), (round(pc + .04, 3), 0, None)])
    lit_r = l4_track("r", [(0, round(3 * grow, 1), None), (pc, round(3 * grow, 1), soft), (p1, round(big * .62, 1), None)])
    lit_o = l4_track("opacity", [(0, 0, None), (round(pc - .04, 3), 0, soft), (round(pc + .14, 3), 1, None), (p1, 1, soft), (round(p1 + 1.05, 3), 0, None)])
    return (f'<g transform="translate({x} {y})">{move}'
            f'<circle r="{r0}" fill="{color}" opacity="0">{blur_r}{blur_o}</circle>'
            f'<circle r="{round(3 * grow, 1)}" fill="{lit}" opacity="0">{lit_r}{lit_o}</circle>'
            f'<circle r="{r0}" fill="{solid}">{sharp}</circle></g>')


def l4_lens(cx, cy, scale):
    return (f'<g transform="translate({cx} {cy}) scale({scale})">'
            '<circle r="25" fill="url(#l4-glass)"/>'
            '<circle r="30.5" fill="none" stroke="url(#l4-chrome)" stroke-width="11"/>'
            '<circle r="34.6" fill="none" stroke="#2c2733" stroke-opacity=".62" stroke-width="2.6" stroke-dasharray="1.1 2.5"/>'
            '<circle r="36" fill="none" stroke="#25202b" stroke-opacity=".6" stroke-width=".8"/>'
            '<circle r="25" fill="none" stroke="#17111c" stroke-width="1.1"/>'
            '<path d="M-15.5 -11.5A19.5 19.5 0 0 1 3 -19" fill="none" stroke="#fff" stroke-opacity=".82" stroke-width="2" stroke-linecap="round"/>'
            '</g>')


def l4_cone(tag, cx, cy, reach, lens):
    apex = cy + 25 * lens
    drop = 170 - apex
    length = (reach * reach + drop * drop) ** .5
    stops = "".join(f'<stop offset="{o}" stop-color="#fff" stop-opacity="{a}"/>' for o, a in [(0, 0), (.25, .12), (.55, .5), (.8, .85), (1, 1)])
    parts = []
    for side, sign in (("a", -1), ("b", 1)):
        x2, y2 = round(cx + sign * 22 * drop / length, 2), round(apex + 22 * reach / length, 2)
        parts.append(f'<linearGradient id="l4-e{side}{tag}" gradientUnits="userSpaceOnUse" x1="{cx}" y1="{apex}" x2="{x2}" y2="{y2}">{stops}</linearGradient>'
                     f'<mask id="l4-m{side}{tag}" maskUnits="userSpaceOnUse" x="0" y="0" width="880" height="{L4_H}"><rect width="880" height="{L4_H}" fill="url(#l4-e{side}{tag})"/></mask>')
    return f'<defs>{"".join(parts)}</defs>'


def l4_beam(tag, cy, lens):
    apex = cy + 25 * lens
    return (f'<g mask="url(#l4-ma{tag})"><g mask="url(#l4-mb{tag})">'
            f'<rect y="{apex}" width="880" height="{170 - apex}" fill="url(#l4-beam)"/></g></g>')


def l4_scene(s, tag, cx, cy, dots, grow, lens, reach, size, base):
    lift = l4_track("opacity", [(0, 0, None), (2.3, 0, L4_PULL), (4.2, .6, None), (7.8, .6, L4_PULL), (10.2, 0, None)])
    live = "".join(l4_dot(i, x, y, k, cx, cy, grow) for i, (x, y, k) in enumerate(dots))
    fixed = "".join(f'<circle cx="{x}" cy="{y}" r="{(4.7 if k == "o" else 3.8) * grow}" fill="{L4_ORANGE if k == "o" else L4_BLUE}"/>' for x, y, k in dots)
    words = s.t(cx, base, L4_LINE, "#f8efe0", size, s.SERIF, 400, "middle", 'font-style="italic"')
    return (f'<ellipse cx="{cx}" cy="10" rx="560" ry="66" fill="url(#l4-spill)"/>' + l4_cone(tag, cx, cy, reach, lens) + l4_beam(tag, cy, lens)
            + f'<g class="replay"><g opacity="0">{lift}{l4_beam(tag, cy, lens)}</g>{live}</g><g class="still">{fixed}</g>'
            + l4_lens(cx, cy, lens) + words)


def build(s):
    css = ("<style>.still,.l4-p{display:none}"
           "@media (prefers-reduced-motion:reduce){.replay{display:none}.still{display:inline}}"
           "@media (max-width:500px){.l4-d{display:none}.l4-p{display:inline}}</style>")
    body = (css + l4_defs()
            + f'<rect x="-4" y="-4" width="888" height="{L4_H + 8}" fill="url(#l4-room)"/>'
            + '<g class="l4-d">' + l4_scene(s, "d", 455, 76, L4_DESK_DOTS, 1, 1, 320, 23, 158) + "</g>"
            + '<g class="l4-p">' + l4_scene(s, "p", 440, 70, L4_PHONE_DOTS, 1.5, 1.15, 420, 33, 159) + "</g>")
    label = "A white page dims into a dark room as plot dots blur into soft circles and pass through a round chrome lens. Then someone paid him to check the models directly."
    return s.svg(880, L4_H, label, s.STIX[1:], body)
