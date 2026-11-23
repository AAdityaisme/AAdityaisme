"""Seam 7, lamps to dawn: the black board thins into night, its calendar lamps lift off as stars, and the sky lightens into the fleet plate's vellum.

The first 3 and last 4 units stay flat so the joins hold at phone scale. Base attributes are the finished frame.
"""
import random

W, H, DUR = 880, 177, 12
BOARD, VELLUM = "#141512", "#f2efe3"
INK, CREAM = "#2e5463", "#fff2cf"
SKY = [(3, BOARD), (34, "#141923"), (54, "#1b2338"), (72, "#2f3550"), (86, "#5c5d74"), (98, "#938c8f"), (108, "#c4b8a9"), (118, "#e4dac6"), (130, "#efe9da"), (H - 4, VELLUM)]
PHONE_SKY = [(3, BOARD), (34, "#12151c"), (92, "#141a28"), (124, "#222b45"), (140, "#6f6878"), (150, "#cdb6a4"), (160, "#ecdfca"), (H - 4, VELLUM)]
LINES = ["Yes, the gate blocked stats cards. He appealed and called this one a departures board.",
         "The numbers are real, private repositories included."]
PHONE_LINES = ["Yes, the gate blocked stats cards.", "He appealed and called this one a departures board.",
               "The numbers are real, private repositories included."]
TIERS = [(78, 0, 0, 1, 5.4), (63, 1, -3, 1, 4.7), (48, 5, -12, .78, 3.5), (33, 13, -26, .56, 2.5), (18, 24, -44, .42, 1.7)]
LAMP_R = 5.4


def s7_lamp_x(col):
    return 452 + (col + .5) * 18


def s7_gradient(id_, stops):
    body = "".join(f'<stop offset="{y / H:.4f}" stop-color="{c}"/>' for y, c in stops)
    return f'<linearGradient id="{id_}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{H}">{body}</linearGradient>'


def s7_defs():
    lamps = "".join(
        f'<radialGradient id="s7lamp{i}" cx=".39" cy=".34" r=".75"><stop stop-color="{core}"/><stop offset=".5" stop-color="{core}"/><stop offset="1" stop-color="{rim}"/></radialGradient>'
        for i, (core, rim) in enumerate([("#9a783d", "#51452a"), ("#d4a33f", "#796331"), ("#ffd571", "#b98a24"), ("#fffae2", "#edb234")], 1))
    return ('<defs>' + s7_gradient("s7sky", SKY) + s7_gradient("s7phone", PHONE_SKY) + lamps +
            f'<linearGradient id="s7rail" gradientUnits="userSpaceOnUse" x1="0" y1="3" x2="0" y2="38"><stop stop-color="#242622"/><stop offset="1" stop-color="#242622" stop-opacity="0"/></linearGradient>'
            f'<linearGradient id="s7railin" gradientUnits="userSpaceOnUse" x1="0" y1="3" x2="0" y2="38"><stop stop-color="#050605"/><stop offset="1" stop-color="#050605" stop-opacity="0"/></linearGradient>'
            f'<linearGradient id="s7railhi" gradientUnits="userSpaceOnUse" x1="0" y1="3" x2="0" y2="38"><stop stop-color="#4d4f48"/><stop offset="1" stop-color="#4d4f48" stop-opacity="0"/></linearGradient>'
            '<radialGradient id="s7halo"><stop stop-color="#ffd65d" stop-opacity=".5"/><stop offset="1" stop-color="#ffc22f" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="s7star"><stop stop-color="#fffdf2"/><stop offset=".3" stop-color="#fff0c0" stop-opacity=".85"/><stop offset="1" stop-color="#ffd65d" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="s7dawn"><stop stop-color="#ffe6c0" stop-opacity=".42"/><stop offset=".55" stop-color="#f6dcc0" stop-opacity=".14"/><stop offset="1" stop-color="#f2dcc0" stop-opacity="0"/></radialGradient>'
            '</defs>')


def s7_rules():
    rows = [(17, "46 7 18 11", .5), (28, "19 12 7 17", .4), (39, "5 18 2 27", .3), (49, "2 31 1 47", .24)]
    return "".join(f'<path d="M0 {y}H{W}" stroke="#34362f" stroke-dasharray="{dash}" opacity="{o}"/>' for y, dash, o in rows)


def s7_field(rng):
    out = []
    for _ in range(46):
        x, y = rng.uniform(8, 430), rng.uniform(12, 70 - rng.uniform(0, 18))
        r = rng.choice([.6, .7, .8, .9, 1.1, 1.3])
        fill = rng.choice(["#fff6dc", "#ffe6a8", "#dfe6ff"])
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" opacity="{rng.uniform(.3, .8):.2f}"/>')
    return "".join(out)


def s7_edge_fade(col):
    return min(1, (col + 1.5) / 4, (22 - col + .5) / 3)


def s7_sockets(rng):
    cells, lit, loose = [], [], []
    for tier, (y, jitter, drift, keep, r) in enumerate(TIERS):
        for col in range(22):
            if rng.random() > keep:
                continue
            x = s7_lamp_x(col) + rng.uniform(-jitter, jitter) + drift * rng.uniform(.4, 1)
            cy = y + rng.uniform(-jitter * .35, jitter * .35)
            level = rng.choice([0, 1, 2, 2, 3, 3, 4]) if tier < 2 else rng.choice([2, 3, 3, 4])
            fade = s7_edge_fade(col)
            if tier < 2:
                cells.append((round(x, 1), round(cy, 1), level, r, fade))
                if level >= 2 and tier == 0:
                    lit.append((round(x, 1), round(cy, 1), level))
            else:
                loose.append((round(x, 1), round(cy, 1), level, r, fade * (1.05 - tier * .13)))
    return cells, lit, loose


def s7_loose(loose):
    out = []
    for x, y, level, r, o in loose:
        fill = f"url(#s7lamp{level})" if r > 3 else "url(#s7star)"
        size = r if r > 3 else r * 1.7
        out.append(f'<circle cx="{x:g}" cy="{y:g}" r="{size:.2f}" fill="{fill}" opacity="{o:.2f}"/>')
    return "".join(out)


def s7_traveler_times(i):
    lift = 1.7 + i * .36
    return .5 + i * .03, lift, lift + 4.1


def s7_traveler(s, i, x, y, level, sx, sy, sway):
    off, lift, land = s7_traveler_times(i)
    gone = off + .6
    dx, dy = x - sx, y - sy
    path = f"M{dx:.1f} {dy:.1f}C{dx + sway:.1f} {dy * .55:.1f} {dx * .3 - sway * .4:.1f} {dy * .22:.1f} 0 0"
    times = [0, off, gone, gone + .01, lift, land, DUR]
    key_times = ";".join(f"{v / DUR:.4f}" for v in times)
    motion = (f'<animateMotion path="{path}" dur="{DUR}s" repeatCount="indefinite" calcMode="spline" keyTimes="{key_times}" '
              f'keyPoints="1;1;1;0;0;1;1" keySplines="0 0 1 1;0 0 1 1;0 0 1 1;0 0 1 1;.38 .02 .3 1;0 0 1 1"/>')
    scale = s.move([(0, .42, .42), (gone, .42, .42), (gone + .01, 1, 1), (lift, 1, 1), (land, .42, .42), (DUR, .42, .42)], DUR, kind="scale")
    whole = s.anim("opacity", [(0, 1), (off, 1), (gone, 0), (lift - .02, 0), (lift, 1), (DUR, 1)], DUR)
    lamp_on = s.anim("opacity", [(0, 0), (gone + .01, 0), (gone + .02, 1), (lift + 1.4, 1), (land - .5, 0), (DUR, 0)], DUR)
    star_on = s.anim("opacity", [(0, 1), (gone + .01, 1), (gone + .02, 0), (lift + 1.4, 0), (land - .5, 1), (DUR, 1)], DUR)
    socket = s.anim("opacity", [(0, 1), (lift + .1, 1), (lift + .8, 0), (10.5, 0), (11.6, 1), (DUR, 1)], DUR)
    return (f'<circle cx="{x:g}" cy="{y:g}" r="{LAMP_R}" fill="url(#s7lamp{level})">{socket}</circle>'
            f'<g transform="translate({sx:.1f} {sy:.1f})" opacity="1">{motion}{whole}<g>{scale}'
            f'<circle r="{LAMP_R * 1.62:.2f}" fill="url(#s7halo)"/>'
            f'<circle r="{LAMP_R}" fill="url(#s7lamp{level})" opacity="0">{lamp_on}</circle>'
            f'<circle r="{LAMP_R * 1.1:.2f}" fill="url(#s7star)">{star_on}</circle></g></g>')


def s7_targets(rng, lit):
    picks = sorted(rng.sample(lit, min(len(lit), 12)), key=lambda c: c[0])
    out = []
    for i, (x, y, level) in enumerate(picks):
        sx = max(24, min(W - 24, x + rng.uniform(-150, 24)))
        sy = rng.uniform(13, 40)
        out.append((i, x, y, level, sx, sy, rng.uniform(-34, 34)))
    return out


def s7_twinkles(s, rng):
    out, rest = [], []
    for i in range(7):
        x, y = rng.uniform(40, 840), rng.uniform(13, 40)
        low = 2.5 + i * 1.1
        tw = s.anim("opacity", [(0, .95), (low, .95), (low + .8, .25), (low + 1.6, .95), (DUR, .95)], DUR)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.3" fill="url(#s7star)">{tw}</circle>')
        rest.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.3" fill="url(#s7star)" opacity=".95"/>')
    return "".join(out), "".join(rest)


def s7_etch():
    return ('<g fill="none" stroke="#8ab5b2" stroke-width=".6" opacity=".48">'
            '<path d="M812 137q22-2 44 0"/>'
            '<path d="M548 156q44-3 88 0m30-1q52-3 104 1m24 0q24-2 50 0"/>'
            '<path d="M592 167q58-2 116 0m28 0q44-2 88 0"/>'
            '</g>')


def s7_phone_stars(s):
    spots = [(668, 26, 2.6), (712, 44, 1.6), (752, 20, 3), (796, 40, 1.8), (836, 24, 2.4), (858, 48, 1.4), (694, 14, 1.2), (818, 12, 1.2)]
    live, rest = [], []
    for i, (x, y, r) in enumerate(spots):
        low = 1.5 + i * 1.2
        tw = s.anim("opacity", [(0, 1), (low, 1), (low + .9, .35), (low + 1.8, 1), (DUR, 1)], DUR)
        live.append(f'<circle cx="{x}" cy="{y}" r="{r * 2.2:.1f}" fill="url(#s7star)">{tw}</circle>')
        rest.append(f'<circle cx="{x}" cy="{y}" r="{r * 2.2:.1f}" fill="url(#s7star)"/>')
    return "".join(live), "".join(rest)


def build(s):
    rng = random.Random(77)
    cells, lit, loose = s7_sockets(rng)
    targets = s7_targets(rng, lit)
    moving = {(x, y) for _, x, y, _, _, _, _ in targets}
    sockets = "".join(
        f'<circle cx="{x:g}" cy="{y:g}" r="{r}" fill="{f"url(#s7lamp{level})" if level else "#262823"}" opacity="{fade:.2f}"/>'
        for x, y, level, r, fade in cells if (x, y) not in moving)
    dark_sockets = "".join(f'<circle cx="{x:g}" cy="{y:g}" r="{LAMP_R}" fill="#262823"/>' for x, y in sorted(moving))
    travelers = "".join(s7_traveler(s, i, x, y, level, sx, sy, sway) for i, x, y, level, sx, sy, sway in targets)
    still = "".join(
        f'<circle cx="{x:g}" cy="{y:g}" r="{LAMP_R}" fill="url(#s7lamp{level})"/>'
        f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{LAMP_R * 1.62 * .42:.2f}" fill="url(#s7halo)"/>'
        f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{LAMP_R * 1.1 * .42:.2f}" fill="url(#s7star)"/>'
        for _, x, y, level, sx, sy, _ in targets)
    field = s7_field(rng)
    phone_live, phone_rest = s7_phone_stars(s)
    twinkling, twinkle_rest = s7_twinkles(s, rng)
    style = ('<style>.still,.s7-phone{display:none}'
             '@media(prefers-reduced-motion:reduce){.replay{display:none}.still{display:inline}}'
             '@media(max-width:500px){.s7-desk{display:none}.s7-phone{display:inline}}</style>')
    desk_text = "".join(s.t(28, 142 + 24 * i, line, INK, 22, s.SERIF) for i, line in enumerate(LINES))
    phone_text = "".join(s.t(28, 40 + 41 * i, line, CREAM, 35, s.SERIF) for i, line in enumerate(PHONE_LINES))
    body = (style + s7_defs() +
            f'<g class="s7-desk"><rect width="{W}" height="{H}" fill="url(#s7sky)"/>'
            '<ellipse cx="682" cy="116" rx="360" ry="46" fill="url(#s7dawn)"/>'
            f'{s7_rules()}{field}{s7_loose(loose)}{s7_etch()}{sockets}{dark_sockets}'
            f'<g class="replay">{twinkling}{travelers}</g><g class="still">{twinkle_rest}{still}</g>{desk_text}</g>'
            f'<g class="s7-phone"><rect width="{W}" height="{H}" fill="url(#s7phone)"/>'
            f'<g class="replay">{phone_live}</g><g class="still">{phone_rest}</g>{phone_text}</g>'
            f'<rect x="-2" y="-2" width="{W + 4}" height="5" fill="{BOARD}"/><rect x="-2" y="{H - 4}" width="{W + 4}" height="6" fill="{VELLUM}"/>')
    label = " ".join(LINES) + " The black board dissolves into a night sky, its yellow lamps drift up as stars, and the horizon lightens into pale dawn."
    return s.svg(W, H, label, s.STIX[:1], body)
