import math
import random


def build(s):
    paper, blue = "#e2edda", "#0d2b4b"
    height = 128
    rng = random.Random(22)

    def shore(x):
        return (21 + 0.043 * x + 5 * math.sin(x / 76) + 3.3 * math.cos(x / 33)
                + 2 * math.sin(x / 13) + 1.2 * math.sin(x / 4.1))

    stops = [(0, paper), (.12, "#dce9d8"), (.23, "#cadfd3"), (.32, "#afcecb"),
             (.38, "#8db6bd"), (.43, "#6298aa"), (.49, "#397996"), (.56, "#245c81"),
             (.66, "#19466a"), (.80, "#123654"), (1, blue)]
    density = ''.join(f'<stop offset="{n}" stop-color="{c}"/>' for n, c in stops)
    wash = []
    for x in range(0, 880, 6):
        y = shore(x)
        slope = (shore(x + 6) - y) / 6
        wash.append(f'<use href="#cy-strip" transform="matrix(1 {slope:.3f} 0 1 {x} {y:.2f})"/>')

    grain = [[], [], []]
    for i in range(700):
        x = rng.uniform(0, 880)
        d = rng.triangular(-13, 37, 8)
        y = shore(x) + d
        length = rng.uniform(.7, 5)
        grain[i % 3].append(f'M{x:.1f} {y:.1f}l{length:.1f} {rng.uniform(-.7,.7):.1f}')
    grains = ''.join(f'<path d="{" ".join(marks)}" stroke="{color}"/>'
                    for marks, color in zip(grain, ["#174d6b", "#e0eee0", "#b9d3cd"]))

    bloom = []
    for i in range(53):
        x = rng.uniform(4, 876)
        y = shore(x) + rng.triangular(-4, 22, 7)
        bloom.append(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{rng.uniform(3,19):.1f}" ry="{rng.uniform(1.5,4.8):.1f}"/>')

    bands = []
    for i in range(7):
        points = []
        for x in range(0, 881, 4):
            u = max(0, min(1, (x - 115) / 550))
            u = u * u * (3 - 2 * u)
            a = math.tau * ((x - 12) / 64 + i / 7)
            curl = 29 + 5.5 * math.sin(a) + 1.4 * math.sin(math.tau * (x - 12) / 32 - i * math.tau / 7)
            y = (i - 1) * 16 * (1 - u) + u * curl
            points.append(f'{x},{y:.1f}')
        detail = ' class="cy-fine"' if i % 2 else ''
        bands.append(f'<polyline{detail} points="{" ".join(points)}"/>')

    css = ('<style>.cy-seam .still,.cy-phone{display:none}'
           '@media(max-width:500px){.cy-fine,.cy-desk{display:none}.cy-phone{display:inline}}'
           '@media(prefers-reduced-motion:reduce){.cy-seam .replay{display:none}.cy-seam .still{display:inline}}</style>')
    defs = (f'<defs><linearGradient id="cy-density" x1="0" y1="-20" x2="0" y2="48" gradientUnits="userSpaceOnUse">{density}</linearGradient>'
            '<g id="cy-strip"><rect y="-20" width="10" height="190"/></g>'
            '<linearGradient id="cy-trace" gradientUnits="userSpaceOnUse" x1="180" x2="715">'
            '<stop stop-color="#7799ab"/><stop offset=".48" stop-color="#719b9f"/><stop offset="1" stop-color="#679278"/></linearGradient>'
            '<linearGradient id="cy-rule" gradientUnits="userSpaceOnUse" x1="260" x2="820">'
            '<stop stop-color="#b3cfe1"/><stop offset=".55" stop-color="#7ba2ad"/><stop offset=".82" stop-color="#6a897e"/><stop offset="1" stop-color="#4e6b59"/></linearGradient>'
            '<linearGradient id="cy-bore" gradientUnits="userSpaceOnUse" x1="295" x2="785">'
            '<stop stop-color="#173853"/><stop offset=".48" stop-color="#3c6c7c"/><stop offset="1" stop-color="#718a7f"/></linearGradient>'
            '<linearGradient id="cy-grid-fade" x2="0" y2="1"><stop stop-color="black"/><stop offset=".24" stop-color="#222"/>'
            '<stop offset=".74" stop-color="white"/></linearGradient>'
            '<mask id="cy-grid-ink"><rect width="880" height="128" fill="url(#cy-grid-fade)"/></mask>'
            '<pattern id="cy-grid" width="16" height="16" patternUnits="userSpaceOnUse"><path d="M16 0H0V16" fill="none" stroke="#507d9e" stroke-opacity=".21" stroke-width=".7"/></pattern>'
            '<pattern id="cy-grid-major" x="0" y="-32" width="80" height="80" patternUnits="userSpaceOnUse"><path d="M80 0H0V80" fill="none" stroke="#507d9e" stroke-opacity=".33" stroke-width=".9"/></pattern>'
            '<linearGradient id="cy-charge" x1="0" y1="-15" x2="0" y2="20" gradientUnits="userSpaceOnUse">'
            '<stop stop-color="black"/><stop offset=".35" stop-color="#707070"/>'
            '<stop offset=".61" stop-color="white"/><stop offset="1" stop-color="black"/></linearGradient>'
            '<radialGradient id="cy-salt"><stop stop-color="#0c4d70" stop-opacity=".27"/>'
            '<stop offset=".66" stop-color="#316d84" stop-opacity=".1"/><stop offset="1" stop-color="#316d84" stop-opacity="0"/></radialGradient>'
            '<linearGradient id="cy-margin" gradientUnits="userSpaceOnUse" x2="0" y2="120"><stop stop-color="#91a895"/>'
            '<stop offset=".28" stop-color="#85a799"/><stop offset=".58" stop-color="#6791a5"/><stop offset="1" stop-color="#81a4bc"/></linearGradient>'
            '<pattern id="cy-stock" width="71" height="43" patternUnits="userSpaceOnUse"><path d="M2 6l3 -.6m17 12 4 1m19 14 3 -.5m10 -26 2 .4m-51 29 4 .2"'
            ' fill="none" stroke="#69795c" opacity=".2" stroke-width=".7"/></pattern>'
            '<g id="cy-windows">' + ''.join(wash) + '</g>'
            '<mask id="cy-wet" x="0" y="-25" width="880" height="180" maskUnits="userSpaceOnUse">'
            '<use href="#cy-windows" fill="url(#cy-charge)"/></mask></defs>')

    def pipe(x):
        elbow = x + 26
        return (f'<path d="M852 47C719 47 599 46 504 43C424 41 369 38 {elbow} 38'
                f'A35 35 0 0 0 {x-9} 73V87H{x+9}V73A17 17 0 0 1 {elbow} 56'
                f'C369 56 424 53 504 51C599 48 719 48 852 48Z" fill="url(#cy-rule)"/>'
                f'<path d="M785 47.5C654 47.4 580 46.8 504 44.6C424 42 369 39.8 {elbow} 39.8'
                f'A33.2 33.2 0 0 0 {x-7.2} 73V87H{x+7.2}V73A18.8 18.8 0 0 1 {elbow} 54.2'
                f'C369 54.2 424 51.5 504 49.4C580 47.9 654 47.7 785 47.5Z" fill="url(#cy-bore)"/>'
                f'<path d="M550 47H{elbow}A26 26 0 0 0 {x} 73V86" fill="none" stroke="#537895" stroke-width=".8" stroke-dasharray="8 3 1 3"/>'
                f'<g fill="none"><path d="M{x} 86V132" stroke="#b3cfe1" stroke-width="18"/>'
                f'<path d="M{x} 86V132" stroke="#173853" stroke-width="14.5"/>'
                f'<path d="M{x} 86V132" stroke="#537895" stroke-width=".8" stroke-dasharray="8 3 1 3" stroke-dashoffset="3"/></g>'
                f'<g fill="#365b76" stroke="#bed4dc"><path d="M{x-11} 85h22v4h-22zm0 6h22v3h-22z"/>'
                f'<path d="M{elbow+43} 36v22h4V36zm6 0v22h3V36z"/></g>')

    charge = (s.move([(0, 0, -14), (1, 0, -14), (6.6, 0, 22), (9.4, 0, 33)], 12)
              + s.anim("opacity", [(0, 0), (1, 0), (2.2, .56), (5.8, .48), (8.7, 0)], 12))
    charge_art = '<rect y="-25" width="880" height="180" fill="#145879" mask="url(#cy-wet)"/>'
    fixed_wash = '<use href="#cy-windows" fill="url(#cy-density)"/>'
    exposure = (f'<g class="replay">{fixed_wash}<g opacity="0">{charge}{charge_art}</g></g>'
                f'<g class="still">{fixed_wash}</g>')
    trace = f'<g fill="none" stroke="url(#cy-trace)" stroke-width=".68" opacity=".74">{"".join(bands)}</g>'
    caption = 'Same idea, applied to the invoice.'

    def lettering(x, y, size):
        return (f'<g transform="translate({x} {y}) skewX(-7)">'
                + s.t(0, 0, caption, '#f0f6f7', size, s.BODY, 400, extra='letter-spacing="1.05"') + '</g>')

    register = ('<path d="M11.5 0V128M868.5 0V128" fill="none" stroke="url(#cy-margin)"/>'
                '<path d="M8 1V19Q8 25 11.5 31M872 1V21Q872 28 868.5 33" fill="none" stroke="#74937e" stroke-width=".8"/>')
    microprint = s.t(615, 43.5, "REGGATE / TAMPER-EVIDENT RECORD", '#537766', 6.7, s.COND, 500,
                     extra='class="cy-fine" letter-spacing="1.25"')
    desktop = pipe(240) + lettering(309, 109, 27)
    phone = pipe(20) + lettering(72, 105, 38)
    top_edge = f'<path d="M-4 0H884" stroke="{paper}" stroke-width="4" vector-effect="non-scaling-stroke" shape-rendering="crispEdges"/>'
    base_edge = f'<path d="M-4 128H884" stroke="{blue}" stroke-width="4" vector-effect="non-scaling-stroke" shape-rendering="crispEdges"/>'
    art = (css + defs + f'<g class="cy-seam"><rect x="-2" y="-2" width="884" height="132" fill="{blue}"/>'
           f'<rect x="-2" y="-2" width="884" height="108" fill="{paper}"/><rect width="880" height="86" fill="url(#cy-stock)"/>'
           + exposure + f'<g fill="url(#cy-salt)">{"".join(bloom)}</g>'
           + f'<g fill="none" stroke-width=".7" opacity=".36">{grains}</g>'
           '<g mask="url(#cy-grid-ink)"><rect width="880" height="128" fill="url(#cy-grid)"/>'
           '<rect width="880" height="128" fill="url(#cy-grid-major)"/></g>'
           + trace + register + microprint + top_edge + base_edge
           + f'<g class="cy-desk">{desktop}</g><g class="cy-phone">{phone}</g></g>')
    return s.svg(880, height, 'Cyanotype. ' + caption, [s.BARLOW[0], s.BARLOW[1]], art)
