"""Draws the profile README's animated SMIL SVGs: one sheet per project, each in its own style, plus the split-flap stats board.

Usage: GITHUB_TOKEN=... python3 sheets.py <login> <out_dir> <since YYYY-MM-DD>
Fonts (Barlow, Courier Prime, STIX Two Text; all OFL) are embedded as base64 so the SVGs render the same inside GitHub's <img>.
"""
import base64
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
W = 880
INK, GRID, LINE, FG, DIM = "#0d2b4b", "#143a62", "#3d6e9e", "#eaf3fc", "#a3bfdb"
WATER, SURF, RED = "#2b8fd6", "#8fd3ff", "#ff7b6b"
COND = "'Barlow Condensed','Arial Narrow',sans-serif"
BODY = "Barlow,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
EASE = "0.4 0 0.2 1"


def _keyframes(frames, dur):
    frames = sorted(frames, key=lambda f: f[0])
    if frames[0][0] > 0:
        frames.insert(0, (0, frames[0][1]))
    if frames[-1][0] < dur:
        frames.append((dur, frames[-1][1]))
    return ";".join(f"{t / dur:.4f}" for t, _ in frames), ";".join(str(v) for _, v in frames), len(frames)


def anim(attr, frames, dur, discrete=False, once=False, begin=0):
    times, values, n = _keyframes(frames, dur)
    mode = 'calcMode="discrete"' if discrete else f'calcMode="spline" keySplines="{";".join([EASE] * (n - 1))}"'
    repeat = 'fill="freeze"' if once else 'repeatCount="indefinite"'
    return f'<animate attributeName="{attr}" begin="{begin:g}s" dur="{dur}s" {repeat} keyTimes="{times}" values="{values}" {mode}/>'


def move(frames, dur, begin=0, kind="translate"):
    times, values, n = _keyframes([(t, f"{x} {y}") for t, x, y in frames], dur)
    return (f'<animateTransform attributeName="transform" type="{kind}" begin="{begin:g}s" dur="{dur}s" repeatCount="indefinite" '
            f'keyTimes="{times}" values="{values}" calcMode="spline" keySplines="{";".join([EASE] * (n - 1))}"/>')


def t(x, y, s, fill=DIM, size=16, family=BODY, weight=400, anchor="start", extra=""):
    return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-family="{family}" font-weight="{weight}" text-anchor="{anchor}" {extra}>{s}</text>'


def blink(frames, dur, body, start_on=False, begin=0):
    return f'<g opacity="{1 if start_on else 0}">{anim("opacity", frames, dur, True, begin=begin)}{body}</g>'


BARLOW = [("Barlow", "400", "barlow-400.woff2", "normal"), ("Barlow Condensed", "500", "bc-500.woff2", "normal"), ("Barlow Condensed", "700", "bc-700.woff2", "normal")]
COURIER = [("Courier Prime", "400", "courier-400.woff2", "normal"), ("Courier Prime", "700", "courier-700.woff2", "normal")]
STIX = [("STIX Two Text", "400 700", "stix.woff2", "normal"), ("STIX Two Text", "400", "stix-italic.woff2", "italic")]


def fonts(faces):
    return "".join(
        f"@font-face{{font-family:'{fam}';font-weight:{wt};font-style:{style};src:url(data:font/woff2;base64,"
        f"{base64.b64encode(open(os.path.join(HERE, 'fonts', f), 'rb').read()).decode()}) format('woff2')}}"
        for fam, wt, f, style in faces
    )


def svg(w, h, label, faces, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{label}">'
            f'<style>{fonts(faces)}</style>{body}</svg>\n')


def sheet(title, desc, caption, link, drawing, label, h=300, inlet_extension=""):
    base = h - 44
    style = """<style>
.sw-phone,.sw-plate .still{display:none}
@media (max-width:500px){
  .sw-desktop{display:none}
  .sw-phone{display:inline}
  .sw-section{transform:translate(-342px,-12px) scale(1.40,1.18)}
}
@media (prefers-reduced-motion:reduce){
  .sw-plate .replay{display:none}
  .sw-plate .still{display:inline}
}
</style>"""
    defs = (
        '<defs><pattern id="sw-grid" width="16" height="16" patternUnits="userSpaceOnUse">'
        '<path d="M16 0H0V16" fill="none" stroke="#507d9e" stroke-opacity=".21" stroke-width=".7"/></pattern>'
        '<pattern id="sw-grid-major" width="80" height="80" patternUnits="userSpaceOnUse">'
        '<path d="M80 0H0V80" fill="none" stroke="#507d9e" stroke-opacity=".33" stroke-width=".9"/></pattern>'
        '<pattern id="sw-cut" width="12" height="12" patternUnits="userSpaceOnUse">'
        '<rect width="12" height="12" fill="#2d5270"/><path d="M-3 3L3 -3M0 12L12 0M9 15L15 9" stroke="#93afbe" stroke-width=".85"/>'
        '<path d="m4 5 2 1 1-2" fill="none" stroke="#a9c0ca" stroke-width=".7"/></pattern>'
        '<pattern id="sw-rock" width="73" height="28" patternUnits="userSpaceOnUse">'
        '<rect width="73" height="28" fill="#193d58"/><path d="m-5 11 17-5 11 1 9-3m4 9 18-3 22-6M8 24l9-4m10-7 5 2 11-4m9 14 16-3" fill="none" stroke="#7192a8" stroke-width=".8"/></pattern>'
        f'<clipPath id="sw-frame"><rect x="12" y="12" width="856" height="{h - 24}"/></clipPath></defs>'
    )
    body = [style, defs, '<g class="sw-plate">', f'<rect width="880" height="{h}" fill="{INK}"/>',
            f'<rect width="880" height="{h}" fill="url(#sw-grid)"/><rect width="880" height="{h}" fill="url(#sw-grid-major)"/>',
            '<g class="sw-desktop">',
            f'<path d="M12 {base}H868M251 12V{h - 12}M691 {base}V{h - 12}" fill="none" stroke="#668ba8"/>',
            t(31, 89, title, FG, 65, COND, 700),
            t(33, 125, desc[0], SURF, 15.5),
            ''.join(t(33, 165 + i * 22, line, FG, 17) for i, line in enumerate(desc[1:])),
            t(32, base + 22, link, SURF, 14.5),
            t(269, base + 23, caption, FG, 17, COND, 500),
            t(850, base + 22, 'ILLUSTRATIVE  /  N.T.S.', DIM, 14, COND, 500, 'end'),
            '</g><g clip-path="url(#sw-frame)">', drawing, '</g>',
            f'<path d="M11.5 0V{h}M868.5 0V{h}" stroke="#81a4bc"/>',
            f'<path d="M-4 0H{W + 4}M-4 {h}H{W + 4}" stroke="{INK}" stroke-width="4" vector-effect="non-scaling-stroke" shape-rendering="crispEdges"/>',
            inlet_extension, '</g>']
    return svg(W, h, label, BARLOW, ''.join(body))


def spillway():
    dur = 12
    crest, floor = 129, 253
    hit = 11.4
    coral = '#ff8b7a'
    pale = '#b3cfe1'

    def level(value):
        return round(floor - (floor - crest) * value / 5000, 2)

    def path(d, color, width=1, fill='none', extra=''):
        return f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{width}" {extra}/>'

    def field(x, y, value, size, color=FG, weight=500, anchor='start'):
        return t(x, y, value, color, size, COND, weight, anchor)

    def visible(start, stop, body):
        return blink([(0, 0), (start, 1), (stop, 0)], dur, body)

    def section(content):
        return f'<g class="sw-section">{content}</g>'

    shore = 'M259 116Q279 119 293 135L313 155 327 179 347 195 366 221 388 236 420 250 462 253H625'
    pool = shore + 'V109H259Z'
    resources = f'<defs><clipPath id="sw-pool"><path d="{pool}"/></clipPath></defs>'
    bed = [
        path(shore + 'L688 248 733 244 785 246 808 244 838 236 861 233V266H259Z', 'none', 0, 'url(#sw-rock)'),
        path('M261 109l22 9 19 18 17 18 17 22 17 13 20 26 20 13 29 14 45 3h157', '#527c97', .85),
        path(shore, pale, 1.7),
        path('M266 136l15 7 14 16m3 9 18 14 5 11m6 7 19 19 20 13m-73-77 8 10m40 21 10 9 12 16m14 11 27 14 21 3', '#82a4b7', .85),
        path('M738 246l24-3 23 3 23-2 30-8 23-3m-51 19 13-2 19-6m-26-4 14-4 22-3', '#90afbd', 1),
    ]
    dam = [
        path('M625 129H650C666 129 673 143 678 158Q688 190 714 217C730 233 748 239 767 239H782V250H623Z', FG, 2, 'url(#sw-cut)'),
        path('M628 133h21c14 0 21 13 26 28 8 27 20 47 37 64 16 15 34 20 53 20h12', '#cfdee5', .9),
        path('M624 247h123m-119-74h54m-54 33h69m-69 25h89m-62-56v29m23 4v22', '#a4bcca', .65),
        path('M624 128h28v3h-28z', FG, 1, '#92b1c6'),
        path('M644 247v-11a5 5 0 0 1 10 0v11z', pale, 1, '#153551'),
        path('M620 130v123', pale, 1.2),
    ]
    staff = []
    for i in range(26):
        y = level(i * 200)
        major = i % 5 == 0
        staff.append(path(f'M{610 if major else 616} {y}H623', FG if major else pale, 1.4 if major else .85))
        if major:
            value = f'{i // 5}k' if i else '$0'
            staff.append('<g class="sw-desktop" stroke="#183952" stroke-width="2.3" paint-order="stroke">'
                         + field(605, y + 4, value, 12, pale, 500, 'end') + '</g>')
    dam += [path('M656 129H851', coral, 1, extra='stroke-dasharray="6 4 1 4"'),
            path('M850 125v8', coral, 1.2),
            '<g class="sw-desktop">' + field(851, 122, '$5,000 cap', 18, coral, 500, 'end') + '</g>']
    inlet = [
        path('M265 68H484Q502 68 502 86V100', pale, 18),
        path('M265 68H484Q502 68 502 86V100', '#173853', 14.5),
        path('M263 68H486Q502 68 502 87V106', '#537895', .8, extra='stroke-dasharray="8 3 1 3"'),
        path('M269 57h4v22h-4zm5 0h4v22h-4zm193 0h4v22h-4zm5 0h4v22h-4zm18 41h25v5h-25z', pale, 1, '#365b76'),
        path('M370 57V37h14v20m-17-20h20m-10-1v-6m-10 0h20M367 57h20v4h-20zM366 76h22v4h-22z', pale, 1.4, '#34566e'),
        '<g class="sw-desktop">' + field(269, 46, 'Request inlet', 16, pale)
        + path('M387 38h13l7-8h13', '#71a1c1', .8) + field(424, 34, 'Slide gate', 14, DIM) + '</g>',
    ]
    inlet_extension = ''.join(
        f'<g class="sw-{layout}">' + path(elbow, pale, 18) + path(elbow, '#173853', 14.5)
        + path(elbow, '#537895', .8, extra='stroke-dasharray="8 3 1 3"') + '</g>'
        for layout, elbow in [('desktop', 'M240 0V43Q240 68 265 68'), ('phone', 'M20 0V59Q20 68 29 68')]
    )
    fade = anim('opacity', [(0, 1), (3.4, 1), (3.8, 0), (3.89, 0), (4.29, 1)], dur)
    booked = [(0, 4800), (3.82, 4800), (3.87, 3900), (6.02, 3900), (6.44, 4350),
              (8.55, 4350), (8.97, 4800)]
    levels = [(s, 0, level(value)) for s, value in booked]
    surface = 'M226 0q8-2 16 0t16 0' + 't16 0' * 25
    hatches = 'M291 15h32m46 0h14m42 0h31m52 0h29m40 0h17M329 29h19m54 0h23m102 0h24m41 0h19M363 47h20m80 0h43m50 0h15M408 67h20m63 0h35m52 0h12M448 88h26m39 0h30m41 0h19'

    def water(live):
        lift = move(levels, dur) if live else ''
        scroll = ('<animateTransform attributeName="transform" type="translate" values="0 0;32 0" '
                  'dur="3s" repeatCount="indefinite"/>') if live else ''
        return ('<g>' + (fade if live else '') + '<g clip-path="url(#sw-pool)">'
                + f'<g transform="translate(0 {level(4800)})">' + lift + '<g>' + scroll
                + path(surface + 'V200H226Z', 'none', 0, '#3788b0', 'fill-opacity=".43"')
                + path(surface, SURF, 2) + '</g>' + path(hatches, '#7fb2c9', .85)
                + '</g></g></g>')

    def spending(value):
        desktop = field(412, 188, 'Booked spend', 16, pale) + field(410, 227, value, 42, FG, 700)
        phone = field(196, 244, value + ' of $5,000', 36, FG, 700)
        return section(f'<g class="sw-desktop">{desktop}</g>') + f'<g class="sw-phone">{phone}</g>'

    def verdict(headline, subtitle, phone, phone_detail, color):
        desk = field(548, 64, headline, 40, color, 700) + field(550, 88, subtitle, 19, pale)
        compact = field(840, 77, phone, 60, color, 700, 'end') + field(840, 108, phone_detail, 28, pale, 500, 'end')
        return section(f'<g class="sw-desktop">{desk}</g>') + f'<g class="sw-phone">{compact}</g>'

    refused = verdict('402 refused', '$4,800 + $310 &gt; $5,000', '402', 'refused', coral)
    admissions = [(5.08, 3900), (7.61, 4350)]
    closed = path('M377 33v10', FG, 1.8) + path('M373 42h8v16l-4 2-4-2z', FG, 1, '#547b96')
    blade = path('M373 45h8v13l-4 2-4-2z', coral, 1.3, coral)
    rejected = [(10, 257, 68), (11.34, 370, 68), (11.8, 370, 68), (12, 257, 68)]
    gate = move([(0, 0, 15), (3.5, 0, 15), (3.85, 0, 0), (11.30, 0, 0),
                 (hit, 0, 15), (11.44, 0, 14), (11.51, 0, 15)], dur)
    latched = [(0, 1), (3.65, 0), (hit, 1)]
    steady_gate = '<g transform="translate(0 15)">' + closed + blade + '</g>'
    moving_gate = '<g transform="translate(0 15)">' + gate + closed + blink(latched, dur, blade, True) + '</g>'

    live = [water(True)]
    for start, before in admissions:
        touch = start + .94
        packet = [(start, 266, 68), (start + .54, 483, 68), (start + .66, 499, 76),
                  (start + .76, 502, 96), (touch, 502, level(before))]
        live.append(visible(start, touch, '<g>' + move(packet, dur) + '<circle r="4.7" fill="#a4ddff"/></g>'))
        live.append(f'<g transform="translate(502 {level(before)})"><g opacity="0">'
                    + anim('opacity', [(0, 0), (touch, 0), (touch + .04, 1), (touch + .55, 0)], dur)
                    + move([(0, .15, .2), (touch, .15, .2), (touch + .32, 1, 1), (touch + .56, 1.5, .35)], dur, kind='scale')
                    + path('M-28 -3q11 0 21 6m4-4-5-7m12 11q9-11 19-12m3-3 4-2', SURF, 1.5) + '</g></g>')

    projected = level(5110)
    ghost_rise = move([(0, 0, level(4800)), (10.0, 0, level(4800)), (10.78, 0, projected)], dur)
    spill = 'M624 126H649C672 125 679 139 689 159C703 189 722 220 749 228Q769 237 799 231'
    reveal = anim('width', [(0, 0), (10.47, 0), (11.01, 119), (11.22, 187)], dur)
    live.append('<defs><clipPath id="sw-spill-front"><rect x="622" y="112" width="0" height="138">' + reveal + '</rect></clipPath></defs>')
    ghost = ('<g clip-path="url(#sw-pool)"><g>' + ghost_rise
             + path('M258 0H625v5H258Z', 'none', 0, coral, 'fill-opacity=".18"')
             + path('M258 0H626', coral, 2.1, extra='stroke-dasharray="9 5"') + '</g></g>'
             + '<g clip-path="url(#sw-spill-front)">'
             + path(spill + 'q-27 11-51 0c-31-11-49-42-64-75-9-21-17-31-34-30z', 'none', 0, coral, 'fill-opacity=".18"')
             + path(spill, coral, 2, extra='stroke-dasharray="7 4"')
             + path('M653 128c20 1 26 20 37 41 15 31 32 53 57 63m4 1q18 7 38 2m9-2 6-1m-30-6 4-3m6 1 3-1', coral, 1.15)
             + '</g>' + visible(10.77, hit, '<g class="sw-desktop">'
             + path('M718 202l17-14h10', coral, 1) + field(749, 194, '$5,110', 23, coral, 700) + '</g>'))
    live.append(visible(10, hit, ghost))
    drop = '<g>' + move(rejected, dur) + f'<circle r="5" fill="{coral}"/></g>'
    live.append(visible(10, 11.996, drop))
    live += [moving_gate, visible(hit, 11.63, path('M367 82l-4 5m14-3v6m9-8 4 4', coral, 1.8))]

    scene = [resources, section(''.join(bed + dam + inlet)),
             '<g class="sw-phone">' + field(37, 43, 'Spillway', 32, FG, 700) + '</g>',
             '<g class="replay">', section(''.join(live)), '<g>', fade,
             blink([(0, 1), (3.85, 0), (8.55, 1)], dur, spending('$4,800'), True),
             visible(3.85, 6.02, spending('$3,900')), visible(6.02, 8.55, spending('$4,350')), '</g>',
             blink([(0, 1), (3.4, 0), (hit, 1)], dur, refused, True)]
    ready = section('<g class="sw-desktop">' + field(550, 64, 'Gate open', 31, DIM, 500) + '</g>')
    scene.append(visible(3.82, 5.36, ready))
    for start, end, before in [(5.36, 7.89, 3900), (7.89, 10, 4350)]:
        total = f'${before:,} + $450 = ${before + 450:,}'
        scene.append(visible(start, end, verdict('+$450 admitted', total, '+$450', 'admitted', SURF)))
    scene += [visible(10, hit, verdict('$310 requested', 'Checking the budget cap', '$310', '$5,110 if booked', coral)), '</g>',
              '<g class="still">', section(water(False) + steady_gate), spending('$4,800'), refused, '</g>',
              section(''.join(staff))]
    return sheet('Spillway', ['An open-source LLM gateway.', 'Each team gets a hard',
                 'budget. The request that', 'would go over is refused', 'with a 402.'],
                 'Section A-A   /   Team budget', 'github.com/AAdityaisme/spillway', ''.join(scene),
                 'Spillway. An open-source LLM gateway. Two $450 requests raise booked spend from $3,900 to $4,800. A $310 request projects $5,110 over the dam. HTTP 402 keeps the water below the $5,000 cap.', 318, inlet_extension)


TYPED = "'Courier Prime','Courier New',monospace"
SERIF = "'STIX Two Text','Times New Roman',serif"


def guilloche(w, h, color):
    import math
    curves = []
    for band in range(12):
        phase = math.tau * band / 12
        points = []
        for x in range(0, 65):
            y = 8 + 5.5 * math.sin(math.tau * x / 64 + phase) + 1.4 * math.sin(math.tau * x / 32 - phase)
            points.append(f"{x},{y:.2f}")
        curves.append(f'<polyline points="{" ".join(points)}"/>')
    rings = []
    for band in range(9):
        points = []
        for step in range(321):
            a = math.tau * step / 320
            r = 32 + 5.1 * math.cos(14 * a + band * 0.44) + 2.1 * math.cos(7 * a - band * 0.27)
            points.append(f"{r * math.cos(a):.1f},{r * math.sin(a):.1f}")
        rings.append(f'<polygon points="{" ".join(points)}"/>')
    return (f'<defs><pattern id="rg-braid" width="64" height="16" patternUnits="userSpaceOnUse">'
            f'<g fill="none" stroke="{color}" stroke-width=".55">{"".join(curves)}</g></pattern></defs>'
            f'<g transform="translate(12 9)"><rect width="{w - 24}" height="16" fill="url(#rg-braid)"/></g>'
            f'<g transform="translate(12 {h - 25})"><rect width="{w - 24}" height="16" fill="url(#rg-braid)"/></g>'
            f'<g class="rg-seal" transform="translate(353 68)" fill="none" stroke="{color}" stroke-width=".52">{"".join(rings)}'
            f'<circle r="23"/><circle r="21" stroke-width="1.2"/></g>')


def reggate():
    w, h, dur = W, 300, 12
    paper, ink, green, line = "#e2edda", "#203b44", "#4e6b59", "#91a895"
    stock, slip_ink, serial = "#faf7e9", "#244640", "#99483a"
    pen, check = "#b3261e", "#1f7a50"
    manila, manila_back, folder_ink = "#f1e8cf", "#e7dcbc", "#203b44"
    sx, sy, sw, sh = 429, 33, 407, 230
    value_x, char_w, row_gap = 158, 10.2, 28
    slips = [
        {"num": "7C2E", "where": "Restaurant, CO", "limit": "$500,000", "cap": None, "verdict": "ALLOWED", "reason": "No rule fires",
         "color": "#226649", "tilt": -3, "lands": 6.4, "hold": 2.0, "thud": 1, "seed": 11, "mark": "check",
         "shape": [(-108, -25), (108, -25), (108, 25), (-108, 25)], "glyph": [[(-93, -4), (-87, 3), (-75, -11)]]},
        {"num": "A91D", "where": "Roofing,\u00a0 CO", "limit": "$500,000", "cap": None, "verdict": "REFERRED", "reason": "High-hazard class",
         "color": "#895013", "tilt": 2, "lands": 10.4, "hold": 2.0, "thud": 1, "seed": 23, "mark": "where",
         "shape": [(-108, -25), (99, -25), (109, 0), (99, 25), (-108, 25)], "glyph": [[(-94, 4), (-94, -4), (-77, -4)], [(-83, -10), (-77, -4), (-83, 2)]]},
        {"num": "3F08", "where": "Roofing,\u00a0 CO", "limit": "$2,000,000", "cap": "$1,000,000", "verdict": "BLOCKED", "reason": "Over limit",
         "color": "#9b3d36", "tilt": -5, "lands": 2.4, "hold": 2.6, "thud": 2, "seed": 37, "mark": "limit",
         "shape": [(-97, -25), (97, -25), (108, -14), (108, 14), (97, 25), (-97, 25), (-108, 14), (-108, -14)],
         "glyph": [[(-92, -11), (-78, 3)], [(-78, -11), (-92, 3)]]},
    ]
    for i, slip in enumerate(slips):
        prev = slips[i - 1]
        slip["start"] = round((prev["lands"] + prev["hold"]) % dur, 3)
        slip["land"] = round((slip["lands"] - slip["start"]) % dur, 3)
        slip["leave"] = round(slip["land"] + slip["hold"], 3)
        slip["begin"] = round(slip["start"] - dur, 3)

    def typed(x, y, value, size, color=ink, weight=400, anchor="start", extra=""):
        return t(x, y, value, color, size, TYPED, weight, anchor, extra)

    def strokes(slip, x, y, cw, glyph_h, gap):
        if slip["mark"] == "check":
            cx = x + cw * len(slip["limit"]) + glyph_h * .8
            cy = y - glyph_h * .32
            k = glyph_h / 17
            return check, [(rg_rough([(cx - 7 * k, cy), (cx - 1.5 * k, cy + 6 * k), (cx + 10 * k, cy - 10 * k)], slip["seed"] + 9, .25 * k, 3, False), 3.1)]
        value = "Roofing," if slip["mark"] == "where" else slip["limit"]
        row = y - gap if slip["mark"] == "where" else y
        cx = x + cw * len(value) / 2
        cy = row - glyph_h * .33
        rx, ry = cw * len(value) / 2 + glyph_h * .41, glyph_h * .86
        return pen, [(rg_loop(cx, cy, rx, ry, slip["seed"] + 5), 2.5), (rg_loop(cx + .6, cy - .5, rx + 1.2, ry + .8, slip["seed"] + 6), .9)]

    def sheet_base(slip):
        fibers = "M34 92l3 -.6m92 41 4 1m104 -77 3 -.5m60 62 2 .4m-212 62 4 .2m118 23 3 -.4m76 -160 2 .5m-310 44 3 .3"
        body = [f'<rect x="1.5" y="3" width="{sw}" height="{sh}" fill="{ink}" opacity=".12"/>'
                f'<rect width="{sw}" height="{sh}" fill="{stock}" stroke="{line}"/>'
                f'<path d="{fibers}" fill="none" stroke="#69795c" opacity=".25" stroke-width=".7"/>'
                f'<path d="M17 1V229" stroke="{line}" stroke-dasharray="2 3"/>']
        body.extend(f'<circle cx="8" cy="{y}" r="3.2" fill="#dae0cb" stroke="#aebba6" stroke-width=".75"/>' for y in range(16, 229, 25))
        body.extend([typed(30, 25, "Decision record", 23, slip_ink, 700),
                     typed(388, 24, "N&#186; " + slip["num"], 18, serial, 700, "end"),
                     typed(31, 42, "CHECKED BEFORE BIND", 10.5, green, 700),
                     typed(388, 42, "TAMPER-EVIDENT", 10.5, green, 700, "end"),
                     f'<path d="M30 49H389m-359 3h359" stroke="{green}"/>'])
        labels = ("Bind", "Policy limit", "Carrier limit" if slip["cap"] else "")
        for j, label in enumerate(labels):
            y = 77 + j * row_gap
            body.append(f'<path d="M30 {y + 6}H389" stroke="{line}" stroke-dasharray="1.4 2.2"/>')
            if label:
                body.append(typed(31, y, label, 14, green))
        body.extend([typed(31, 163, "DISPOSITION", 10.5, green, 700),
                     f'<path d="M30 219H389" stroke="{line}"/>',
                     typed(31, 226, "REGGATE / TAMPER-EVIDENT RECORD   " * 3, 5.8, green, extra='textLength="357" lengthAdjust="spacing"')])
        return "".join(body)

    def values(slip):
        return [v for v in (slip["where"], slip["limit"], slip["cap"]) if v]

    def finished(slip):
        color, marks = strokes(slip, value_x, 77 + row_gap, char_w, 17, row_gap)
        rows = "".join(typed(value_x, 77 + row_gap * j, v, 17, slip_ink, 700) for j, v in enumerate(values(slip)))
        return (sheet_base(slip) + rows + rg_ink(marks, color) +
                f'<g transform="translate(238 184) rotate({slip["tilt"]})">{rg_stamp(slip, stock)}</g>')

    def desk(i, slip):
        b, land, leave = slip["begin"], slip["land"], slip["leave"]
        rows = values(slip)
        gap = (land - .95) / len(rows)
        parts = [sheet_base(slip)]
        for j, value in enumerate(rows):
            y = 77 + row_gap * j
            start = .5 + j * gap
            frames = [(0, 0)] + [(round(start + k * .012, 3), round((char_w * k + 2) if k < len(value) else char_w * len(value) + 2, 2)) for k in range(1, len(value) + 1)]
            clip = f"rg-type-{i}-{j}"
            parts.append(f'<clipPath id="{clip}"><rect x="{value_x}" y="{y - 17}" width="0" height="23">{anim("width", frames, dur, True, begin=b)}</rect></clipPath>'
                         f'<g clip-path="url(#{clip})">{typed(value_x, y, value, 17, slip_ink, 700)}</g>')
        color, marks = strokes(slip, value_x, 77 + row_gap, char_w, 17, row_gap)
        ink_on = round(land - .4, 3)
        parts.append(f'<g opacity="0">{anim("opacity", [(0, 0), (ink_on, 1)], dur, True, begin=b)}'
                     f'{rg_ink(marks, color, [(0, 1), (ink_on, 1), (round(land - .12, 3), 0)], dur, b)}</g>')
        impact = [(0, 1.15, 1.15), (round(land - .05, 3), 1.15, 1.15), (land, .965, .955), (round(land + .11, 3), 1, 1)]
        parts.append(f'<g transform="translate(238 184) rotate({slip["tilt"]})"><g opacity="0">'
                     f'{anim("opacity", [(0, 0), (round(land - .05, 3), 1)], dur, True, begin=b)}'
                     f'<g>{move(impact, dur, b, "scale")}{rg_stamp(slip, stock)}</g></g></g>')
        thud = [(0, 0, 0), (land, 0, 0), (round(land + .05, 3), 0, slip["thud"]), (round(land + .21, 3), 0, 0)]
        return (f'<g opacity="0">{anim("opacity", [(0, 1), (leave, 0)], dur, True, begin=b)}'
                f'<g transform="translate({sx} {sy})"><g>{move(thud, dur, b)}{"".join(parts)}</g></g></g>')

    def flight(slip):
        b, leave = slip["begin"], slip["leave"]
        gone = round(leave + .45, 3)
        travel = rg_motion("translate", [(0, "0 0"), (leave, "0 0"), (gone, "-173 196")], dur, b)
        tilt = rg_motion("rotate", [(0, "0 203 115"), (leave, "0 203 115"), (gone, "-4 203 115")], dur, b)
        shrink = rg_motion("scale", [(0, "1 1"), (round(leave + .28, 3), "1 1"), (round(leave + .42, 3), ".33 .33")], dur, b, ".2 .6 .4 1")
        return (f'<g opacity="0">{anim("opacity", [(0, 0), (leave, 1), (round(gone + .02, 3), 0)], dur, True, begin=b)}'
                f'<g transform="translate({sx} {sy})"><g>{travel}<g>{tilt}<g>{shrink}{finished(slip)}</g></g></g></g></g>')

    def folder_front():
        return (f'<path d="M242 226h57l6 3 93 -3 -5 42 -146 1z" fill="{manila}" stroke="{folder_ink}" stroke-width="1.15" stroke-linejoin="round"/>'
                f'<path d="M250 262l139 -1" stroke="{folder_ink}" stroke-width=".6" opacity=".5"/>'
                + typed(320, 250, "EXAM FILE", 15, ink, 700, "middle"))

    def phone_lines(slip):
        first, second = (slip["limit"], "limit " + slip["cap"]) if slip["cap"] else (slip["where"], slip["limit"])
        return typed(412, 84, first, 34, slip_ink, 700) + typed(412, 142, second, 34, slip_ink, 700)

    def phone_marks(slip):
        return strokes(slip, 412, 84 if slip["cap"] else 142, 20.4, 34, 58)

    def phone_slip(slip):
        b, land, leave = slip["begin"], slip["land"], slip["leave"]
        color, marks = phone_marks(slip)
        lines = phone_lines(slip)
        ink_on = round(land - .4, 3)
        impact = [(0, 1.6, 1.6), (round(land - .05, 3), 1.6, 1.6), (land, 1.36, 1.34), (round(land + .11, 3), 1.4, 1.4)]
        return (f'<g opacity="0">{anim("opacity", [(0, 1), (leave, 0)], dur, True, begin=b)}{lines}'
                f'<g opacity="0">{anim("opacity", [(0, 0), (ink_on, 1)], dur, True, begin=b)}'
                f'{rg_ink(marks, color, [(0, 1), (ink_on, 1), (round(land - .12, 3), 0)], dur, b)}</g>'
                f'<g transform="translate(612 208) rotate({slip["tilt"]})"><g opacity="0">'
                f'{anim("opacity", [(0, 0), (round(land - .05, 3), 1)], dur, True, begin=b)}'
                f'<g>{move(impact, dur, b, "scale")}{rg_stamp(slip, stock, False)}</g></g></g></g>')

    def phone_still(slip):
        color, marks = phone_marks(slip)
        return (phone_lines(slip) + rg_ink(marks, color) +
                f'<g transform="translate(612 208) rotate({slip["tilt"]}) scale(1.4)">{rg_stamp(slip, stock, False)}</g>')

    css = ('<style>.still,.rg-phone{display:none}'
           '@media (prefers-reduced-motion:reduce){.replay{display:none}.still{display:inline}}'
           '@media (max-width:500px){.rg-desk,.rg-seal{display:none}.rg-phone{display:inline}}</style>')
    defs = ('<defs><pattern id="rg-fiber" width="71" height="43" patternUnits="userSpaceOnUse">'
            '<path d="M2 6l3 -.6m17 12 4 1m19 14 3 -.5m10 -26 2 .4m-51 29 4 .2" fill="none" stroke="#69795c" opacity=".20" stroke-width=".7"/>'
            '</pattern><clipPath id="rg-pocket"><path d="M12 12H868V275H400V266H12z"/></clipPath></defs>')
    ground = [css, defs, f'<rect width="{w}" height="{h}" fill="{paper}"/>', guilloche(w, h, "#86a78d"),
              f'<path d="M8 0V{h}M872 0V{h}" stroke="{green}" stroke-width="1.4"/>'
              f'<path d="M12 25H868M12 275H868M12 9V291M868 9V291" fill="none" stroke="{line}" stroke-width=".8"/>',
              '<rect width="880" height="300" fill="url(#rg-fiber)"/>']
    copy = ["Checks every insurance policy against", "the carrier's rules before it's bound,",
            "returns allow, refer or block, and", "keeps a tamper-evident record of why."]
    left = [typed(353, 75, "RG", 22, green, 700, "middle"), typed(34, 92, "reggate", 57, ink, 700)]
    left += [typed(37, 124 + 20 * j, row, 15.2) for j, row in enumerate(copy)]
    left += [typed(37, 234, "reggate.cloud", 19, ink, 700), f'<path d="M37 238H183" stroke="{ink}"/>',
             typed(37, 260, "SYNTHETIC DEMO", 13, green, 700)]
    folder_back = (f'<path d="M249 269l-3 -62h18l6 -8h53l6 7h72l-4 63z" fill="{manila_back}" stroke="{folder_ink}" stroke-width="1.15" stroke-linejoin="round"/>'
                   f'<path d="M256 210l134 -3 1 40 -133 3z" fill="{stock}" stroke="{line}"/>')
    under = "".join(f'<rect x="{sx + d}" y="{sy + d}" width="{sw}" height="{sh}" fill="{stock}" stroke="{line}"/>' for d in (7, 4))
    filed_at = sorted(round((s["lands"] + s["hold"] + .45) % dur, 3) for s in slips)
    tuck = [(0, 0, 0)]
    for at in filed_at:
        tuck += [(at, 0, 0), (round(at + .07, 3), 0, 1.6), (round(at + .22, 3), 0, 0)]
    replay = ("".join(desk(i, s) for i, s in enumerate(slips)) +
              f'<g clip-path="url(#rg-pocket)">{"".join(flight(s) for s in slips)}</g>'
              f'<g>{move(tuck, dur)}{folder_front()}</g>')
    still = (f'<g transform="translate({sx} {sy})">{finished(slips[1])}</g>' + folder_front())
    phone_ground = (typed(34, 138, "reggate", 74, ink, 700) + typed(37, 190, "SYNTHETIC DEMO", 28, green, 700) +
                    f'<rect x="372" y="38" width="478" height="224" fill="{stock}" stroke="{line}"/>')
    body = "".join(ground) + (
        f'<g class="rg-desk">{"".join(left)}{folder_back}{under}<g class="replay">{replay}</g><g class="still">{still}</g></g>'
        f'<g class="rg-phone">{phone_ground}<g class="replay">{"".join(phone_slip(s) for s in slips)}</g>'
        f'<g class="still">{phone_still(slips[1])}</g></g>'
        f'<path d="M-4 0H{w + 4}M-4 {h}H{w + 4}" stroke="{paper}" stroke-width="4" vector-effect="non-scaling-stroke" shape-rendering="crispEdges"/>')
    return svg(w, h, "reggate: synthetic demo. Insurance binds are checked against the carrier's rules and stamped allowed, referred or blocked, then filed.",
               COURIER, body)


def certified_blind():
    ink, grey, blue, orange, slash = "#202325", "#575c60", "#1f77b4", "#ff7f0e", "#b16a2b"
    rule, paper, band_fill, ghost_blue = "#c7cacf", "#ffffff", "#f1f3f5", "#9ea5ad"
    dur, fade0, fade1, reset_t, plot0 = 12, 1.95, 2.35, 2.36, 2.42
    left, right, top, bottom = 306, 604, 66, 202
    low, high = 0.04, 0.49
    italic = 'font-style="italic"'
    stroke_dash = 'stroke-width="1.2" stroke-dasharray="5 4"'
    stroke_slash = 'stroke-width="1.25"'
    bot_cls = 'class="cb-b-label-bot"'
    tau_cls = 'class="cb-tau-lbl"'

    def label(x, y, words, size=16, color=ink, weight=400, style="", anchor="start", extra=""):
        return t(x, y, words, color, size, SERIF, weight, anchor, f"{style} {extra}".strip())

    def line(x1, y1, x2, y2, color, style=""):
        return f'<path d="M{x1} {y1} L{x2} {y2}" fill="none" stroke="{color}" {style}/>'

    def ordinate(score):
        return round(bottom - (bottom - top) * score, 2)

    def panel(x, letter, title):
        return label(x, 37, letter, 18, weight=650) + label(x + 29, 37, title, 18)

    def remap_x(old_x):
        return round(left + (old_x - 348) * (right - left) / 248.0, 1)

    raw_blues = [(360, .65), (368, .84), (377, .35), (375, .77), (390, .96), (395, .63),
                 (404, .79), (412, .55), (420, .89), (424, .67), (441, .83), (448, .70),
                 (458, .59), (469, .93), (476, .72), (484, .83), (492, .59), (493, .72),
                 (510, .73), (522, .88), (535, .64), (545, .94), (552, .78), (565, .58),
                 (574, .83), (587, .68), (438, .28)]
    raw_slice = [(465, .11), (490, .20), (476, .28), (512, .36), (494, .44), (520, .61)]
    blues = [(remap_x(x), s) for x, s in raw_blues]
    slice_points = [(remap_x(x), s) for x, s in raw_slice]

    steps = [
        (3.70, low, 4.15, 0.155),
        (4.48, 0.155, 4.93, 0.24),
        (5.26, 0.24, 5.71, 0.32),
        (6.04, 0.32, 6.49, 0.40),
        (7.19, 0.40, 7.74, high),
    ]
    tau_frames = [(0, high), (fade1, high), (reset_t, low), (steps[0][0], low)]
    for t0, s0, t1, s1 in steps:
        tau_frames.append((t1, s1))
        if t1 < steps[-1][2]:
            nxt = [st[0] for st in steps if st[0] > t1][0]
            tau_frames.append((nxt, s1))
    tau_frames.append((dur, high))

    y_frames = [(tm, ordinate(sc)) for tm, sc in tau_frames]
    h_frames = [(tm, round(bottom - ordinate(sc), 2)) for tm, sc in tau_frames]
    tr_frames = [(tm, 0, ordinate(sc)) for tm, sc in tau_frames]

    all_pts = sorted([(x, s, "b") for x, s in blues] + [(x, s, "o") for x, s in slice_points], key=lambda item: item[0])
    plot_rank = {(item[0], item[1], item[2]): idx for idx, item in enumerate(all_pts)}

    def orange_ghost(x, y, r=4.7):
        d = round(r * 0.72, 2)
        return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fafbfc" stroke="{slash}" stroke-width="1.25"/>'
                f'<path d="M{round(x - d, 2)} {round(y + d, 2)} L{round(x + d, 2)} {round(y - d, 2)}" '
                f'fill="none" stroke="{slash}" stroke-width="1.25"/>')

    def blue_ghost(x, y, r=3.8):
        return f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{ghost_blue}" stroke-width="1.15"/>'

    def live_or_ghost(x, score, kind, is_still):
        y = ordinate(score)
        is_orange = kind == "o"
        r = 4.7 if is_orange else 3.8
        color = orange if is_orange else blue
        solid = f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>'
        if is_still:
            if score < high:
                return orange_ghost(x, y, r) if is_orange else blue_ghost(x, y, r)
            return solid
        p_t = round(plot0 + plot_rank[(x, score, kind)] * 0.020, 3)
        outer_op = anim("opacity", [(0, 1), (fade0, 1), (fade1, 0), (p_t, 0), (round(p_t + 0.08, 3), 1), (dur, 1)], dur)
        if score >= high:
            return f'<g>{outer_op}{solid}</g>'
        tc = cb_cross_time(steps, score)
        live_part = f'<g opacity="0">{anim("opacity", [(0, 0), (reset_t, 1), (tc, 0)], dur, True)}{solid}</g>'
        ghost_shape = orange_ghost(x, y, r) if is_orange else blue_ghost(x, y, r)
        ghost_part = f'<g>{anim("opacity", [(0, 1), (reset_t, 0), (tc, 1)], dur, True)}{ghost_shape}</g>'
        return f'<g>{outer_op}{live_part}{ghost_part}</g>'

    slice_cross = [cb_cross_time(steps, s) for _, s in slice_points if s < high]
    passes_dip = [(0, 1)]
    for tc in slice_cross:
        passes_dip.extend([(round(tc - 0.005, 3), 1), (round(tc + 0.075, 3), 0.4), (round(tc + 0.145, 3), 0.4), (round(tc + 0.25, 3), 1)])
    passes_dip.append((dur, 1))

    band_fade = anim("opacity", [(0, 1), (fade0, 1), (fade1, 0), (3.15, 0), (3.45, 1), (dur, 1)], dur)
    excl_fade = anim("opacity", [(0, 1), (fade0, 1), (fade1, 0), (5.15, 0), (5.45, 1), (dur, 1)], dur)
    panel_b_fade = anim("opacity", [(0, 1), (fade0, 1), (fade1, 0), (2.78, 0), (3.10, 1), (dur, 1)], dur)

    y_high = ordinate(high)
    plot_replay = [
        f'<g>{band_fade}<rect x="{left + 1}" y="{y_high}" width="{right - left - 1}" height="{round(bottom - y_high, 2)}" fill="{band_fill}">',
        anim("y", y_frames, dur), anim("height", h_frames, dur), '</rect></g>',
    ]
    plot_replay.extend(live_or_ghost(x, s, "b", False) for x, s in blues)
    plot_replay.append('<g id="cb-slice">')
    plot_replay.extend(live_or_ghost(x, s, "o", False) for x, s in slice_points)
    plot_replay.append('</g>')
    plot_replay.append(f'<g class="cb-desk-only">{excl_fade}{label(left + 10, bottom - 10, "Discarded", 14, grey, style=italic)}</g>')
    plot_replay.append(
        f'<g>{band_fade}<g transform="translate(0 {y_high})">{move(tr_frames, dur)}'
        f'{line(left, 0, right, 0, ink, stroke_dash)}'
        f'{label(right + 7, 5, "τ", 18, style=italic, extra=tau_cls)}</g></g>'
    )

    plot_still = [
        f'<rect x="{left + 1}" y="{y_high}" width="{right - left - 1}" height="{round(bottom - y_high, 2)}" fill="{band_fill}"/>',
    ]
    plot_still.extend(live_or_ghost(x, s, "b", True) for x, s in blues)
    plot_still.extend(live_or_ghost(x, s, "o", True) for x, s in slice_points)
    plot_still.append(f'<g class="cb-desk-only">{label(left + 10, bottom - 10, "Discarded", 14, grey, style=italic)}</g>')
    plot_still.append(
        f'<g transform="translate(0 {y_high})">'
        f'{line(left, 0, right, 0, ink, stroke_dash)}'
        f'{label(right + 7, 5, "τ", 18, style=italic, extra=tau_cls)}</g>'
    )

    counts = [(0, len(slice_cross)), (reset_t, 0)] + [(tc, i) for i, tc in enumerate(slice_cross, 1)]
    b_top_replay = (
        f'<g>{panel_b_fade}'
        f'<text x="0" y="59" fill="{blue}" font-size="26" font-family="{SERIF}" font-style="italic">'
        f'{anim("opacity", passes_dip, dur)}Passes</text></g>'
    )
    b_top_still = label(0, 59, "Passes", 26, blue, style=italic)

    b_count_replay = [f'<g>{panel_b_fade}']
    for i in range(len(slice_cross) + 1):
        b_count_replay.append(blink([(when, int(cnt == i)) for when, cnt in counts], dur,
                                    label(0, 62, f"{i} of {len(slice_points)}", 32), i == len(slice_cross)))
    b_count_replay.append('</g>')

    b_dots_replay = []
    b_dots_still = []
    for i, (_, score) in enumerate(slice_points):
        cx = 7 + i * 25
        cy = 87
        stagger_t = round(2.74 + i * 0.032, 3)
        dot_fade = anim("opacity", [(0, 1), (fade0, 1), (fade1, 0), (stagger_t, 0), (round(stagger_t + 0.09, 3), 1), (dur, 1)], dur)
        solid_dot = f'<circle cx="{cx}" cy="{cy}" r="6" fill="{orange}"/>'
        slashed_dot = (f'<circle cx="{cx}" cy="{cy}" r="6" fill="{paper}" stroke="{slash}" stroke-width="1.25"/>'
                       f'{line(round(cx - 4.3, 2), round(cy + 4.3, 2), round(cx + 4.3, 2), round(cy - 4.3, 2), slash, stroke_slash)}')
        if score < high:
            tc = cb_cross_time(steps, score)
            b_dots_replay.append(
                f'<g>{dot_fade}'
                f'<g opacity="0">{anim("opacity", [(0, 0), (reset_t, 1), (tc, 0)], dur, True)}{solid_dot}</g>'
                f'<g>{anim("opacity", [(0, 1), (reset_t, 0), (tc, 1)], dur, True)}{slashed_dot}</g></g>'
            )
            b_dots_still.append(slashed_dot)
        else:
            b_dots_replay.append(f'<g>{dot_fade}{solid_dot}</g>')
            b_dots_still.append(solid_dot)

    desc_lines = [
        (114, "A filter that throws data away for"),
        (133, "good can be poisoned to remove"),
        (152, "most of one slice while its aggregate"),
        (171, "certification still passes."),
        (197, "A small labeled probe, committed"),
        (216, "before the discard, can detect it."),
    ]

    axes_grid = []
    for score in (0, 0.5, 1):
        y = ordinate(score)
        if score:
            axes_grid.append(line(left, y, right, y, "#e5e7e8"))
        axes_grid.append(f'<g class="cb-desk-only">{line(left - 4, y, left, y, ink)}'
                         f'{label(left - 8, y + 4, f"{score:g}", 13, grey, anchor="end")}</g>')

    css = (
        ".still{display:none}"
        "@media(prefers-reduced-motion:reduce){.replay{display:none}.still{display:inline}}"
        "@media(max-width:500px){"
        ".cb-desk-only{display:none}"
        ".cb-title{transform:translate(-5px,-56px) scale(1.33)}"
        ".cb-plot{transform:translate(-413px,-17px) scale(1.44)}"
        ".cb-tau-lbl{font-size:19px}"
        ".cb-b-top{transform:translate(534px,34px) scale(1.69)}"
        ".cb-b-bot{transform:translate(534px,147px) scale(1.38)}"
        ".cb-b-label-bot{font-size:19.6px}"
        "}"
    )

    body = [
        f'<rect width="{W}" height="300" fill="{paper}"/>',
        f'<defs><linearGradient id="cb-rim" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="300"><stop offset=".78" stop-color="{rule}"/><stop offset=".985" stop-color="{rule}" stop-opacity="0"/></linearGradient></defs><path d="M.5 0V300M879.5 0V300" stroke="url(#cb-rim)"/>',
        f'<g class="cb-desk-only">{label(26, 39, "Under review", 15, grey, style=italic)}</g>',
        f'<g class="cb-title">{label(25, 84, "Certified Blind", 33, weight=600)}</g>',
        '<g class="cb-desk-only">' + "".join(label(26, y, text, 14) for y, text in desc_lines) + '</g>',
        f'<g class="cb-desk-only">{panel(280, "(a)", "Threshold filter")}{panel(648, "(b)", "After filtering")}</g>',
        '<g class="cb-plot">',
        "".join(axes_grid),
        line(left, top, left, bottom, ink),
        line(left, bottom, right, bottom, ink),
        f'<g class="cb-desk-only">{label(left, 58, "Filter score", 14, grey, style=italic)}'
        f'{label(right, 221, "Input", 14, grey, style=italic, anchor="end")}',
        f'<circle cx="{left + 4}" cy="234" r="4" fill="{blue}"/>{label(left + 15, 239, "Other data", 14.5)}',
        f'<circle cx="{left + 109}" cy="234" r="4" fill="{orange}"/>{label(left + 120, 239, "One slice", 14.5)}</g>',
        '<g class="replay">' + "".join(plot_replay) + '</g>',
        '<g class="still">' + "".join(plot_still) + '</g>',
        '</g>',
        f'<g class="cb-desk-only">{line(648, 56, 854, 56, ink)}</g>',
        f'<g class="cb-b-top" transform="translate(648 56)">'
        f'{label(0, 26, "Aggregate check", 16)}'
        f'<g class="replay">{b_top_replay}</g>'
        f'<g class="still">{b_top_still}</g></g>',
        f'<g class="cb-b-bot" transform="translate(648 132)">'
        f'{line(0, 0, 206, 0, rule)}'
        f'{label(0, 26, "Slice actually lost", 16, extra=bot_cls)}'
        f'<g class="replay">{"".join(b_count_replay)}{"".join(b_dots_replay)}</g>'
        f'<g class="still">{label(0, 62, f"{len(slice_cross)} of {len(slice_points)}", 32)}{"".join(b_dots_still)}</g></g>',
        f'<g class="cb-desk-only">{line(280, 254, 854, 254, rule)}'
        f'{label(280, 278, "Fig. 1.", 15, weight=650)}'
        f'{label(326, 278, "Illustrative data. The aggregate check sees only the points that clear τ.", 15)}</g>',
        f'<path d="M-4 0H{W + 4}M-4 300H{W + 4}" stroke="{paper}" stroke-width="4" vector-effect="non-scaling-stroke" shape-rendering="crispEdges"/>',
    ]
    aria = "Certified Blind. Illustrative filter: five of six orange points are discarded as the threshold rises, leaving ghosts below the threshold while the aggregate check passes throughout."
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="300" viewBox="0 0 {W} 300" role="img" aria-label="{aria}">'
            f'<style>{fonts(STIX)}{css}</style>{"".join(body)}</svg>\n')


QUERY = """query($login:String!,$from:DateTime!){user(login:$login){contributionsCollection(from:$from){
totalCommitContributions totalRepositoriesWithContributedCommits
commitContributionsByRepository(maxRepositories:1){repository{name} contributions{totalCount}}
contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}"""


def gql(query, variables, token):
    req = urllib.request.Request("https://api.github.com/graphql", data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if "errors" in body:
        raise SystemExit(f"GraphQL error: {body['errors']}")
    return body["data"]


def merged_prs(login, since, token):
    q = urllib.parse.quote(f"is:pr author:{login} is:merged created:>={since}")
    req = urllib.request.Request(f"https://api.github.com/search/issues?q={q}&per_page=1", headers={"Authorization": f"bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["total_count"]


TILE_W = 36


def flap_tile(x, y, final, lands, dur, seed):
    from xml.sax.saxutils import escape

    half = TILE_W / 2
    origin = f'transform="translate({x:g} {y + 20:g})"'
    seam = '<path d="M0 0H36" stroke="#050605" stroke-width="1.6"/><path d="M0 0H3M33 0H36" stroke="#6d6e60"/>'
    base = (f'<g {origin}><rect y="-20" width="36" height="20" rx="2" fill="url(#flapTop)"/><rect width="36" height="20" rx="2" fill="url(#flapBottom)"/>'
            f'<text x="{half:g}" y="12.5">{escape(final)}</text>{seam}</g>')
    if not lands:
        return base, ""
    drum = STATS_DRUMS[0] if final.isdigit() else STATS_DRUMS[1]
    prior = 3 + seed % 4
    at = drum.find(final)
    strip = final + "".join(drum[(at - prior + k) % len(drum)] for k in range(prior))
    xs = " ".join(f"{half:g}" for _ in strip)
    ys = " ".join(f"{12.5 + 60 * k:g}" for k in range(len(strip)))
    glyphs = f'<text x="{xs}" y="{ys}">{escape(strip)}</text>'
    current, upcoming, fold, unfold, show = [(0, 0)], [(0, 0)], [(0, 1)], [(0, 0)], [(0, 0)]
    for land in lands:
        begin = round(land - (prior + 1) * STATS_FLIP, 3)
        show += [(begin, 1), (land, 0)]
        for j, target in enumerate(list(range(1, prior + 1)) + [0]):
            flip = round(begin + j * STATS_FLIP, 3)
            mid, end = round(flip + STATS_FLIP / 2, 3), round(flip + STATS_FLIP, 3)
            upcoming.append((flip, target))
            current.append((end, target))
            fold += [(flip, 1), (mid, 0), (end, 0), (end, 1)]
            unfold += [(mid, 0), (end, 1), (end, 0)]
    now = f'<g>{stats_track(current, dur, "translate", True)}{glyphs}</g>'
    next_up = f'<g>{stats_track(upcoming, dur, "translate", True)}{glyphs}</g>'
    overlay = (f'<g {origin} opacity="0">{stats_track(show, dur, "opacity")}'
               f'<g clip-path="url(#flapUpper)"><rect y="-20" width="36" height="20" fill="url(#flapTop)"/>{next_up}</g>'
               f'<g clip-path="url(#flapLower)"><rect width="36" height="20" fill="url(#flapBottom)"/>{now}</g>'
               f'<g>{stats_track(fold, dur, "scale")}<g clip-path="url(#flapUpper)"><rect y="-20" width="36" height="20" fill="#2f302b"/>{now}</g></g>'
               f'<g>{stats_track(unfold, dur, "scale")}<g clip-path="url(#flapLower)"><rect width="36" height="20" fill="#121311"/>{next_up}</g></g>'
               f'{seam}</g>')
    return base, overlay


def lamp_grid(days, start, x0, y0, width, dur):
    if not days:
        return ""
    sunday = start - timedelta((start.weekday() + 1) % 7)
    columns = (days[-1][0] - sunday).days // 7 + 1
    step = min(18, width / columns)
    radius = min(5.4, step * 0.34)
    active = sorted(n for _, n in days if n)
    cuts = [active[len(active) * q // 4] for q in (1, 2, 3)] if active else []
    months = {}
    lamps = []
    for day, n in days:
        col = (day - sunday).days // 7
        x = x0 + (col + 0.5) * step
        y = y0 + (day.weekday() + 1) % 7 * 15
        level = 1 + sum(n > c for c in cuts) if n else 0
        fill = f"url(#lamp{level})" if level else "#262823"
        if level == 4:
            lamps.append(f'<circle cx="{x:g}" cy="{y}" r="{radius * 1.62:g}" fill="url(#lampHalo)"/>')
        lamps.append(f'<circle cx="{x:g}" cy="{y}" r="{radius:g}" fill="{fill}"/>')
        months.setdefault((day.year, day.month), (x - radius, day.strftime("%b").upper()))
    last = -100
    for x, name in months.values():
        if x - last >= 29:
            lamps.append(t(round(x, 1), y0 - 13, name, "#b9b7a5", 15, COND, 500))
            last = x
    return "".join(lamps)


def bests(days, with_dates=False):
    weeks = {}
    for day, n in days:
        sunday = day - timedelta((day.weekday() + 1) % 7)
        weeks[sunday] = weeks.get(sunday, 0) + n
    active = sum(n > 0 for _, n in days)
    peak_day, peak = max(days, key=lambda item: item[1], default=(None, 0))
    peak_sunday, week = max(weeks.items(), key=lambda item: item[1], default=(None, 0))
    result = peak, week, round(sum(weeks.values()) / active) if active else 0
    if with_dates:
        return result, (peak_day if peak else None, peak_sunday if week else None, active)
    return result


def fetch_stats(login, since, token):
    cc = gql(QUERY, {"login": login, "from": f"{since}T00:00:00Z"}, token)["user"]["contributionsCollection"]
    return {"since": since, "as_of": date.today().isoformat(), "merged_prs": merged_prs(login, since, token), "collection": cc}


def flow_record(stats):
    from xml.sax.saxutils import escape

    cc = stats["collection"]
    start, end = date.fromisoformat(stats["since"]), date.fromisoformat(stats["as_of"])
    calendar = cc["contributionCalendar"]
    days = sorted((date.fromisoformat(d["date"]), d["contributionCount"]) for wk in calendar["weeks"] for d in wk["contributionDays"])
    days = [(day, n) for day, n in days if start <= day <= end]
    total = sum(n for _, n in days)
    assert total == calendar["totalContributions"], "calendar days do not add up to the reported total"
    (peak, week, per_day), (peak_day, peak_sunday, active_days) = bests(days, with_dates=True)
    week_span = ""
    if peak_sunday:
        first, last = max(peak_sunday, start), min(peak_sunday + timedelta(days=6), end)
        week_span = f"{first:%b} {first.day}-{last.day}" if first.month == last.month else f"{first:%b} {first.day}-{last:%b} {last.day}"
    rows = [("Contributions", total), ("Commits", cc["totalCommitContributions"]),
            ("Merged PRs", stats["merged_prs"]), ("Repositories", cc["totalRepositoriesWithContributedCommits"])]
    repos = cc["commitContributionsByRepository"]
    top_repo = max(repos, key=lambda repo: repo["contributions"]["totalCount"]) if repos else None
    name = top_repo["repository"]["name"].upper() if top_repo else "NONE"
    count = top_repo["contributions"]["totalCount"] if top_repo else 0
    dur, h = 14, 340
    amber, cream, pale, rule, board = "#ffcd52", "#fff2cf", "#b9b7a5", "#34362f", "#0d0e0c"
    tracked = 'letter-spacing="1.1"'
    as_of = f"{end:%b} {end.day} {end.year}".upper()
    style = ('<style>.st-phone{display:none}@media(prefers-reduced-motion:reduce){.replay{display:none}}'
             '@media(max-width:500px){.st-cal,.st-rec,.st-colhead{display:none}.st-phone{display:inline}'
             '.st-lab{font-size:30px}.st-hd,.st-unit{font-size:27px}}</style>')
    out = [style, '<defs><clipPath id="flapUpper"><rect y="-20" width="36" height="20"/></clipPath>'
           '<clipPath id="flapLower"><rect width="36" height="20"/></clipPath>'
           '<clipPath id="stCalClip"><rect x="437" y="72" width="427" height="140"/></clipPath>'
           f'<linearGradient id="stSweep"><stop stop-color="{board}" stop-opacity="0"/><stop offset=".5" stop-color="{board}" stop-opacity=".82"/><stop offset="1" stop-color="{board}" stop-opacity="0"/></linearGradient>']
    for id_, top, bottom in [("flapTop", "#2a2b27", "#212220"), ("flapBottom", "#1a1b19", "#20211e"), ("caseMetal", "#51534b", "#242622")]:
        out.append(f'<linearGradient id="{id_}" x2="0" y2="1"><stop stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>')
    for i, (core, rim) in enumerate([("#9a783d", "#51452a"), ("#d4a33f", "#796331"),
                                     ("#ffd571", "#b98a24"), ("#fffae2", "#edb234")], 1):
        out.append(f'<radialGradient id="lamp{i}" cx=".39" cy=".34" r=".75"><stop stop-color="{core}"/><stop offset=".5" stop-color="{core}"/><stop offset="1" stop-color="{rim}"/></radialGradient>')
    out.extend(['<radialGradient id="lampHalo"><stop stop-color="#ffd65d" stop-opacity=".48"/><stop offset="1" stop-color="#ffc22f" stop-opacity="0"/></radialGradient></defs>',
                f'<rect width="{W}" height="{h}" fill="url(#caseMetal)"/>',
                f'<path d="M1 0V{h}M879 0V{h}" stroke="#77786e"/>',
                f'<rect x="8" y="-1" width="864" height="{h + 2}" fill="{board}" stroke="#050605" stroke-width="2"/>',
                f'<path d="M30 39 46 23M33 23H46V36" fill="none" stroke="{amber}" stroke-width="4.5"/>',
                t(60, 40, "SHIPPED", amber, 32, COND, 700, extra=tracked),
                t(186, 39, f"SINCE {start:%b} {start.day} {start.year}".upper(), amber, 20, COND, 500, extra=f'class="st-hd" {tracked}'),
                t(852, 39, f'<tspan font-weight="500">AS OF</tspan> {as_of}', amber, 20, COND, 700, "end", 'class="st-hd"'),
                f'<path d="M16 49H864M16 267H864M436 49V267" stroke="{rule}"/>',
                '<g class="st-colhead">',
                t(28, 65, "SERVICE", pale, 15, COND, 500, extra=tracked),
                t(423, 65, "TOTAL", pale, 15, COND, 500, "end", tracked),
                t(452, 65, "DAILY CONTRIBUTIONS", pale, 15, COND, 500, extra=tracked),
                f'<path d="M16 71H436" stroke="{rule}"/></g>'])
    slots = max(len(str(number)) for _, number in rows)
    still, replay = [], []

    def place(x, y, ch, lands, seed):
        base, overlay = flap_tile(x, y, ch, lands, dur, seed)
        still.append(base)
        replay.append(overlay)

    for r, (label, number) in enumerate(rows):
        top = 71 + 49 * r
        if r:
            out.append(f'<path d="M16 {top}H436" stroke="{rule}"/>')
        out.append(t(28, top + 33, label, cream, 25, COND, 500, extra='class="st-lab"'))
        value = str(number)
        left = 423 - STATS_PITCH * slots + 3
        for slot in range(slots - len(value)):
            place(left + STATS_PITCH * slot, top + 4, "", [], slot)
        for k, ch in enumerate(value):
            column = slots - len(value) + k
            place(left + STATS_PITCH * column, top + 4, ch, [round(1.55 + 0.55 * r + 0.09 * column, 3)], r * 3 + k)
    out.extend(['<g class="st-cal">', lamp_grid(days, start, 452, 104, 400, dur),
                f'<path d="M436 213H864" stroke="{rule}"/></g>'])
    records = [(452, "Best day", peak, f"{peak_day:%b} {peak_day.day}" if peak_day else ""),
               (590, "Best week", week, week_span), (728, "Per active day", per_day, f"{active_days} days")]
    out.append('<g class="st-rec">')
    for x, label, value, detail in records:
        out.extend([t(x, 233, label, pale, 16, COND, 500),
                    t(x, 259, f'{value:,}<tspan dx="6" fill="{pale}" font-size="15" font-weight="500">{escape(detail)}</tspan>', cream, 24, COND, 700)])
    out.append('</g><g class="st-phone">')
    for i, (x, label, value, detail) in enumerate(records):
        out.extend([t(456, 124 + 54 * i, label, cream, 30, COND, 500),
                    t(852, 124 + 54 * i, f'<tspan fill="{pale}" font-size="27" font-weight="500">{escape(detail)}</tspan><tspan dx="10">{value:,}</tspan>', cream, 30, COND, 700, "end")])
    out.append('</g>')
    out.append(t(28, 308, "Busiest repo", cream, 25, COND, 500, extra='class="st-lab"'))
    value = str(count)
    count_left = 760 - STATS_PITCH * len(value) + 3
    for k, ch in enumerate(value):
        place(count_left + STATS_PITCH * k, 280, ch, [round(3.75 + 0.09 * k, 3), round(9.75 + 0.09 * k, 3)], k + 2)
    name_right = count_left - 12
    if len(name) <= 10:
        name_left = name_right - STATS_PITCH * len(name) + 3
        for k, ch in enumerate(name):
            place(name_left + STATS_PITCH * k, 280, ch, [round(4.2 + 0.09 * k, 3), round(10.2 + 0.09 * k, 3)], k)
    else:
        fit = 'textLength="382" lengthAdjust="spacingAndGlyphs"' if len(name) > 23 else ""
        out.append(t(name_right, 310, escape(name), cream, 29, COND, 700, "end", fit))
    out.append(t(852, 308, "commits", pale, 21, COND, 500, "end", 'class="st-unit"'))
    faces = f'font-family="{COND}" font-weight="700" font-size="35" fill="{cream}" text-anchor="middle"'
    out.append(f'<g class="still" {faces}>{"".join(still)}</g><g class="replay" {faces}>{"".join(replay)}</g>')
    sweep_at = move([(0, 380, 0), (5.3, 380, 0), (7.7, 900, 0)], dur)
    sweep_on = anim("opacity", [(0, 0), (5.3, 0), (5.31, 1), (7.69, 1), (7.7, 0)], dur, True)
    out.append(f'<g class="replay st-cal" clip-path="url(#stCalClip)"><rect width="120" y="92" height="118" fill="url(#stSweep)" opacity="0">{sweep_at}{sweep_on}</rect></g>')
    for x, y in [(12, 13), (868, 13), (12, h - 13), (868, h - 13)]:
        out.append(f'<circle cx="{x}" cy="{y}" r="3" fill="#74766b" stroke="#141511"/><path d="M{x-1.6} {y+1.2}l3.2 -2.4" stroke="#22241f"/>')
    out.append(f'<defs><linearGradient id="board-foot" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#141512" stop-opacity="0"/><stop offset="1" stop-color="#141512"/></linearGradient></defs><rect x="-4" y="{h - 22}" width="{W + 8}" height="22" fill="url(#board-foot)"/>')
    out.append(f'<path d="M-4 0H{W + 4}M-4 {h}H{W + 4}" stroke="#141512" stroke-width="2" vector-effect="non-scaling-stroke" shape-rendering="crispEdges"/>')
    desc = ", ".join(f"{label} {number:,}" for label, number in rows)
    label = f"Shipped since {start:%B} {start.day} {start.year}, as of {end:%B} {end.day} {end.year}. {desc}. Busiest repo {name}, {count:,} commits. Best day {peak}, best week {week}, per active day {per_day}."
    return svg(W, h, escape(label, {'"': "&quot;"}), BARLOW[1:], "".join(out))


def rg_rough(points, seed, amp=.42, step=6, closed=True):
    import math
    import random
    rng = random.Random(seed)
    path = points + points[:1] if closed else points
    out = []
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        out.extend((x0 + (x1 - x0) * k / n + rng.uniform(-amp, amp), y0 + (y1 - y0) * k / n + rng.uniform(-amp, amp)) for k in range(n))
    if not closed:
        out.append(path[-1])
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in out) + ("Z" if closed else "")

def rg_flecks(seed, color, count=58):
    import random
    rng = random.Random(seed)
    strokes = "".join(f"M{rng.uniform(-106, 106):.1f} {rng.uniform(-24, 24):.1f}l{rng.uniform(.5, 2.6):.1f} {rng.uniform(-.8, .8):.1f}" for _ in range(count))
    return f'<path d="{strokes}" fill="none" stroke="{color}" stroke-width="1.05" stroke-linecap="round"/>'

def rg_loop(cx, cy, rx, ry, seed):
    import math
    import random
    rng = random.Random(seed)
    phase = rng.uniform(0, math.tau)
    points = []
    for k in range(65):
        a = -2.55 + math.tau * 1.1 * k / 64
        wobble = (1 + .045 * math.sin(3 * a + phase) + rng.uniform(-.008, .008)) * (1 + .055 * k / 64)
        points.append((cx + rx * wobble * math.cos(a), cy + ry * wobble * math.sin(a)))
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in points)

def rg_ink(strokes, color, frames=None, dur=12, begin=0):
    paths = []
    for d, width in strokes:
        if frames is None:
            paths.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')
        else:
            paths.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round" '
                         f'pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1">{anim("stroke-dashoffset", frames, dur, begin=begin)}</path>')
    return "".join(paths)

def rg_stamp(slip, paper, reason=True):
    color, seed = slip["color"], slip["seed"]
    verdict_y = 2 if reason else 11
    verdict = t(17, verdict_y, slip["verdict"], color, 30, TYPED, 700, "middle")
    note = t(17, 18, slip["reason"], color, 14, TYPED, 700, "middle") if reason else ""
    glyphs = "".join(f'<path d="{rg_rough(g, seed + 3 + n, .22, 4, False)}" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="square"/>'
                     for n, g in enumerate(slip["glyph"]))
    return (f'<path d="{rg_rough(slip["shape"], seed)}" fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round"/>'
            f'<path d="{rg_rough(slip["shape"], seed + 1, .75, 9)}" fill="none" stroke="{color}" stroke-width=".8" opacity=".6"/>'
            f'{glyphs}<path d="{rg_rough([(-65, -20), (-65, 19)], seed + 2, .3, 5, False)}" fill="none" stroke="{color}" stroke-width="1.3"/>'
            f'{verdict}{note}{rg_flecks(seed, paper)}')

def rg_motion(kind, frames, dur, begin, spline=".55 .05 .9 .5"):
    times, values, n = _keyframes(frames, dur)
    return (f'<animateTransform attributeName="transform" type="{kind}" begin="{begin:g}s" dur="{dur}s" repeatCount="indefinite" '
            f'keyTimes="{times}" values="{values}" calcMode="spline" keySplines="{";".join([spline] * (n - 1))}"/>')

def cb_cubic(u, p1, p2):
    v = 1.0 - u
    return 3.0 * v * v * u * p1 + 3.0 * v * u * u * p2 + u * u * u

def cb_ease_inv(frac):
    lo, hi = 0.0, 1.0
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        if cb_cubic(mid, 0.0, 1.0) < frac:
            lo = mid
        else:
            hi = mid
    return cb_cubic(0.5 * (lo + hi), 0.4, 0.2)

def cb_cross_time(steps, score):
    for t0, s0, t1, s1 in steps:
        if s0 <= score <= s1 and s1 > s0:
            return round(t0 + (t1 - t0) * cb_ease_inv((score - s0) / (s1 - s0)), 3)
    return 0.0

STATS_PITCH = 39

STATS_FLIP = 0.07

STATS_DRUMS = ("0123456789", "ABCDEFGHIJKLMNOPQRSTUVWXYZ-._0123456789")

def stats_track(frames, dur, kind, discrete=False):
    kept = [frames[0]]
    for frame in frames[1:]:
        if frame != kept[-1]:
            kept.append(frame)
    if kept[-1][0] < dur:
        kept.append((dur, kept[-1][1]))
    times = ";".join(f"{at / dur:.5f}" for at, _ in kept)
    if kind == "opacity":
        values = ";".join(str(v) for _, v in kept)
        return f'<animate attributeName="opacity" dur="{dur}s" repeatCount="indefinite" keyTimes="{times}" values="{values}" calcMode="discrete"/>'
    values = ";".join(f"0 {-60 * v}" if kind == "translate" else f"1 {v}" for _, v in kept)
    mode = "discrete" if discrete else "linear"
    return f'<animateTransform attributeName="transform" type="{kind}" dur="{dur}s" repeatCount="indefinite" keyTimes="{times}" values="{values}" calcMode="{mode}"/>'

UNDO_SPLINES = {"line": "0 0 1 1", "out": "0.3 0.354 0.4 1", "in": "0.5 0 0.9 0.841", "both": EASE, "stop": "0.3 0.9 0.6 1", "start": "0.4 0 0.8 0.4"}

UNDO_TAPE = [(0, 1.75, "out"), (1.05, 2.6, "line"), (1.25, 2.6, "both"), (1.95, 2.0, "line"), (2.75, 2.0, "both"), (3.85, 2.56, "line"),
             (8.4, 2.56, "in"), (9.1, 2.98, "line"), (12, 5.75, None)]

UNDO_PLATTER = [(0, 0, "line"), (2.8, 336, "stop"), (3.4, 360, "line"), (5.95, 360, "start"), (6.55, 384, "line"), (12, 1080, None)]

UNDO_ACTIONS = ["edit file", "move meeting", "send invite", "delete account"]

UNDO_INK, UNDO_CREAM, UNDO_LAMP = "#2f2a24", "#f4ead6", "#e8502a"

def undo_track(kind, frames):
    times = ";".join(f"{f[0] / 12:.4f}" for f in frames)
    values = ";".join(str(f[1]) for f in frames)
    splines = ";".join(UNDO_SPLINES[f[2]] for f in frames[:-1])
    return (f'<animateTransform attributeName="transform" type="{kind}" dur="12s" repeatCount="indefinite" '
            f'keyTimes="{times}" values="{values}" calcMode="spline" keySplines="{splines}"/>')

def undo_spin(degrees):
    return undo_track("rotate", [(f[0], f"{(f[1] - 1.75) * degrees:.1f}", f[2]) for f in UNDO_TAPE])

def undo_polar(cx, cy, radius, degrees):
    import math
    rad = math.radians(degrees)
    return f"{cx + radius * math.cos(rad):.1f} {cy + radius * math.sin(rad):.1f}"

def undo_grain():
    import math
    import random
    rng = random.Random(11)
    dark, light = [], []
    for i in range(50):
        y = 2 + i * 6.1 + rng.uniform(-2, 2)
        amp, freq, phase = rng.uniform(1.5, 5), rng.uniform(.004, .009), rng.uniform(0, 6.3)
        pts = [(x, y + amp * math.sin(x * freq + phase)) for x in range(-40, 1000, 160)]
        mids = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in zip(pts, pts[1:])]
        d = f"M{mids[0][0]:.0f} {mids[0][1]:.1f}" + "".join(f"Q{p[0]} {p[1]:.1f} {m[0]:.0f} {m[1]:.1f}" for p, m in zip(pts[1:], mids[1:]))
        (light if i % 3 == 0 else dark).append(d)
    return (f'<path d="{"".join(dark)}" fill="none" stroke="#2e1a0d" stroke-width=".9" opacity=".5"/>'
            f'<path d="{"".join(light)}" fill="none" stroke="#a87a50" stroke-width=".8" opacity=".32"/>')

def undo_reel(cx, cy, radius, pack, degrees):
    windows = ""
    for k in range(3):
        a = 90 + k * 120
        inner, outer = radius * .3, radius * .84
        windows += (f"M{undo_polar(0, 0, inner, a - 40)}L{undo_polar(0, 0, outer, a - 46)}A{outer:.1f} {outer:.1f} 0 0 1 {undo_polar(0, 0, outer, a + 46)}"
                    f"L{undo_polar(0, 0, inner, a + 40)}A{inner:.1f} {inner:.1f} 0 0 0 {undo_polar(0, 0, inner, a - 40)}Z")
    flange = f"M{-radius} 0A{radius} {radius} 0 1 1 {radius} 0A{radius} {radius} 0 1 1 {-radius} 0Z{windows}"
    rings = "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#5b3f29" stroke-width=".7"/>' for r in range(pack - 18, pack, 5))
    base = (f'<circle cx="{cx}" cy="{cy + 2}" r="{radius + 1}" fill="#6f6c64" opacity=".55"/><circle cx="{cx}" cy="{cy}" r="{radius}" fill="#1d1a17"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{pack}" fill="#3e2918"/>{rings}')
    notches = "".join(f'<path d="M-2.4 -13h4.8v6h-4.8z" fill="#efeee8" transform="rotate({k * 120})"/>' for k in range(3))
    rotor = (f'<g transform="translate({cx} {cy})"><g>{undo_spin(degrees)}<path d="{flange}" fill="#cfcdc5" fill-rule="evenodd" stroke="#77736a" stroke-width=".8"/>'
             f'<circle r="15" fill="#34302b" stroke="#928e84"/>{notches}<circle r="3" fill="#a9a59b"/></g></g>')
    sheen = (f'<path d="M{cx} {cy}L{undo_polar(cx, cy, radius - 1, 205)}A{radius - 1} {radius - 1} 0 0 1 {undo_polar(cx, cy, radius - 1, 250)}Z" fill="#fff" opacity=".2"/>'
             f'<path d="M{cx} {cy}L{undo_polar(cx, cy, radius - 1, 25)}A{radius - 1} {radius - 1} 0 0 1 {undo_polar(cx, cy, radius - 1, 58)}Z" fill="#fff" opacity=".12"/>')
    return base, rotor, sheen

def undo_meter(x, y, name, frames):
    w, h = 118, 60
    px, py = x + w / 2, y + h + 13
    ticks = ""
    for k in range(13):
        a = -90 - 42 + k * 7
        color, width = ("#c43d22", 1.8) if k >= 9 else (UNDO_INK, 1.2 if k % 3 == 0 else .7)
        ticks += f'<path d="M{undo_polar(px, py, 56 if k % 3 == 0 else 59, a)}L{undo_polar(px, py, 64, a)}" stroke="{color}" stroke-width="{width}"/>'
    arc = f'<path d="M{undo_polar(px, py, 64, -132)}A64 64 0 0 1 {undo_polar(px, py, 64, -69)}" fill="none" stroke="{UNDO_INK}" stroke-width=".8"/>'
    red = f'<path d="M{undo_polar(px, py, 64, -69)}A64 64 0 0 1 {undo_polar(px, py, 64, -48)}" fill="none" stroke="#c43d22" stroke-width="2.6"/>'
    face = (f'<rect x="{x - 2}" y="{y - 2}" width="{w + 4}" height="{h + 4}" rx="3" fill="#6e6a61"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="url(#undo-face)"/>{arc}{red}{ticks}'
            + t(x + w - 8, y + h - 7, name, UNDO_INK, 15, COND, 700, "end", 'class="undo-fine" letter-spacing="1"'))
    needle = (f'<g clip-path="url(#undo-meter-{name})"><g transform="translate({px} {py})"><g transform="rotate({frames[0][1]})">{undo_track("rotate", frames)}'
              f'<path d="M-.7 0L0 -66L.7 0Z" fill="#1f1b17" stroke="#1f1b17" stroke-width=".5"/></g></g></g>')
    clip = f'<clipPath id="undo-meter-{name}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath>'
    glass = f'<path d="M{x} {y}H{x + w}V{y + 15}Q{x + w / 2} {y + 26} {x} {y + 15}Z" fill="#fff" opacity=".24"/>'
    return clip, face, needle, glass

def undo_label(i):
    x = 465 + (1.75 - i) * 120
    name = UNDO_ACTIONS[i % 4]
    hot = i % 4 == 3
    paper = (f'<rect x="{x - 53:g}" y="203" width="106" height="24" rx="1.5" fill="{"#c8452c" if hot else "#efe4cb"}" stroke="{"#8e2c18" if hot else "#b9a988"}" stroke-width=".7"/>'
             + t(x, 220, name, "#fff5e6" if hot else "#33261a", 17, COND, 700, "middle", 'class="undo-fine"'))
    if i != 2:
        return paper
    slash = f'<path d="M{x - 45:g} 224L{x + 44:g} 206M{x - 42:g} 207L{x + 46:g} 225" fill="none" stroke="#d92f18" stroke-width="2.6" stroke-linecap="round"/>'
    mark = f'<g opacity="0">{anim("opacity", [(0, 0), (.42, 0), (.6, 1), (2.72, 1), (2.73, 0)], 12)}{slash}</g>'
    lift = (f'<g>{move([(0, 0, 0), (2.22, 0, 0), (2.72, 0, -24), (2.74, 0, 0)], 12)}'
            f'<g>{anim("opacity", [(0, 1), (2.3, 1), (2.72, 0), (11.8, 0), (11.81, 1)], 12)}{paper}{mark}</g></g>')
    patch = (f'<g opacity="0">{anim("opacity", [(0, 0), (2.34, 0), (2.6, 1), (11.8, 1), (11.81, 0)], 12)}'
             f'<rect x="{x - 53:g}" y="204" width="106" height="22" rx="1.5" fill="none" stroke="#b9a988" stroke-opacity=".55" stroke-dasharray="4 3"/>'
             f'<path d="M{x - 6:g} 203L{x + 8:g} 227H{x + 1:g}L{x - 13:g} 203Z" fill="#efe9db" stroke="#a9a08e" stroke-width=".5"/></g>')
    return lift + patch

def undo_lathe():
    cx, cy = 764, 112
    dots = "".join(f"M{undo_polar(0, 0, 85, k * 10)}h1.8v3h-1.8z" for k in range(36))
    radii = [round(72 * .93 ** k, 2) for k in range(-1, 11)]
    rings = "".join(f'<circle r="{r}" fill="none" stroke="{"#57504a" if k % 3 else "#6e655d"}" stroke-width=".75"/>' for k, r in enumerate(radii))
    base = (f'<circle cx="{cx}" cy="{cy + 3}" r="92" fill="#6f6c64" opacity=".5"/><circle cx="{cx}" cy="{cy}" r="91" fill="url(#undo-platter)" stroke="#7d796f"/>'
            f'<circle cx="{cx}" cy="{cy}" r="80" fill="#191614" stroke="#0c0a09"/>')
    title = t(0, -9, "NO UNDO", "#5a2415", 15, COND, 700, "middle", 'class="undo-fine" letter-spacing=".6"')
    spin = (f'<g transform="translate({cx} {cy})"><g>{undo_track("rotate", UNDO_PLATTER)}<path d="{dots}" fill="#47443e"/>'
            f'<circle r="32" fill="#e9c98c" stroke="#a97f43"/><circle r="27" fill="none" stroke="#a97f43" stroke-width=".7"/>{title}'
            '<circle r="2.6" fill="#2a2622"/><path d="M-17 11h34M-11 16h22" stroke="#a97f43" stroke-width="1"/></g></g>')
    grooves = (f'<g clip-path="url(#undo-cut)"><g transform="translate({cx} {cy})"><g>'
               f'{move([(0, 1, 1), (6.35, 1, 1), (8.35, .93, .93), (12, .93, .93)], 12, kind="scale")}{rings}</g></g></g>')
    glint = (f'<circle cx="{cx}" cy="{cy}" r="72" fill="none" stroke="#e8a765" stroke-width="1.6" opacity=".55">'
             f'{anim("opacity", [(0, .55), (2.9, 0), (6.3, 0), (6.5, .95), (8.2, .95), (9.3, .55), (12, .55)], 12)}</circle>')
    arm = (f'<g transform="translate(846 40)"><g transform="rotate(-8.3)">'
           + undo_track("rotate", [(0, -8.3, "line"), (6.08, -8.3, "both"), (6.34, -12.3, "line"), (8.36, -12.3, "both"), (8.72, -8.3, "line"), (12, -8.3, None)])
           + '<rect x="-122" y="-2.6" width="126" height="5.2" rx="2" fill="#d8d6ce" stroke="#57534b" stroke-width=".7"/>'
             '<path d="M-146 -7h30l5 4v6l-5 4h-30z" fill="#35312c" stroke="#a9a59b" stroke-width=".8"/><path d="M-146 0h-3" stroke="#e8a765" stroke-width="2"/>'
             '<rect x="-136" y="-3" width="15" height="6" fill="#b5462a"/></g></g>'
             '<circle cx="846" cy="40" r="11" fill="#c9c7bf" stroke="#57534b"/><circle cx="846" cy="40" r="4.5" fill="#35312c"/>')
    sheen = (f'<path d="M{cx} {cy}L{undo_polar(cx, cy, 79, 200)}A79 79 0 0 1 {undo_polar(cx, cy, 79, 238)}Z" fill="#fff" opacity=".1"/>'
             f'<path d="M{cx} {cy}L{undo_polar(cx, cy, 79, 20)}A79 79 0 0 1 {undo_polar(cx, cy, 79, 58)}Z" fill="#fff" opacity=".08"/>')
    return base, grooves + spin + glint, sheen, arm

def undo_lamp():
    base = ('<rect x="670" y="224" width="122" height="48" rx="3" fill="#57534b"/><rect x="673" y="227" width="116" height="42" rx="2" fill="#46251a"/>'
            + t(731, 257, "ASK FIRST", "#d8a98a", 27, COND, 700, "middle", 'letter-spacing=".6"'))
    lit = ('<rect x="656" y="212" width="150" height="72" rx="20" fill="url(#undo-halo)"/><rect x="673" y="227" width="116" height="42" rx="2" fill="url(#undo-glass)"/>'
           + t(731, 257, "ASK FIRST", "#fff8e8", 27, COND, 700, "middle", 'letter-spacing=".6"'))
    live = f'<g opacity="0">{anim("opacity", [(0, 0), (4.34, 0), (4.46, 1), (5.9, 1), (6.4, 0)], 12)}{lit}</g>'
    return base, live

def undo_scene():
    frames_undo = [(0, -30, "both"), (.5, -24, "both"), (1.05, -30, "both"), (1.3, -30, "both"), (1.62, 16, "both"), (2.05, 9, "both"), (2.75, -30, "both"),
                   (3.3, -24, "both"), (3.95, -34, "line"), (8.6, -34, "both"), (9.4, -26, "both"), (10.2, -31, "both"), (11.1, -24, "both"), (12, -30, None)]
    frames_ask = [(0, -30, "both"), (.6, -25, "both"), (1.25, -32, "both"), (2.75, -32, "both"), (3.3, -25, "both"), (3.95, -34, "both"), (4.42, 20, "both"), (5, 14, "both"),
                  (5.72, 19, "both"), (6.35, -34, "line"), (8.6, -34, "both"), (9.5, -25, "both"), (10.3, -31, "both"), (11.2, -25, "both"), (12, -30, None)]
    clip_u, face_u, needle_u, glass_u = undo_meter(398, 24, "UNDO", frames_undo)
    clip_a, face_a, needle_a, glass_a = undo_meter(398, 92, "ASK", frames_ask)
    supply = undo_reel(326, 88, 62, 52, 180)
    takeup = undo_reel(590, 88, 62, 40, 120)
    plat_base, plat_spin, plat_sheen, arm = undo_lathe()
    lamp_base, lamp_live = undo_lamp()
    wide = "".join(t(26, 104 + i * 22, s, UNDO_CREAM, 16) for i, s in enumerate(
        ["When an AI agent acts for you,", "should it ask first, or act", "and let you undo it? A study", "of which one actually catches", "more mistakes."]))
    plate = ('<rect x="24" y="238" width="216" height="36" rx="2" fill="url(#undo-brass)" stroke="#7d5f2b"/><path d="M26 240H238" stroke="#fff3c9" stroke-opacity=".7"/>'
             + "".join(f'<circle cx="{x}" cy="256" r="3" fill="#a07f3f" stroke="#5e4619" stroke-width=".7"/><path d="M{x - 2} 257.2l4 -2.4" stroke="#4a3613"/>' for x in (33, 231))
             + t(132, 262, "Study design. No results yet.", "#33250f", 18, COND, 700, "middle"))
    phone = ("".join(t(26, 112 + i * 34, s, UNDO_CREAM, 29, COND, 500) for i, s in enumerate(["should it ask first,", "or act and let you", "undo it?"]))
             + t(26, 240, "Study design.", "#f0cf8d", 28, COND, 700) + t(26, 272, "No results yet.", "#f0cf8d", 28, COND, 700))
    style = ('<style>.still,.undo-phone{display:none}@media (prefers-reduced-motion:reduce){.replay{display:none}.still{display:inline}}'
             '@media (max-width:500px){.undo-wide,.undo-fine{display:none}.undo-phone{display:inline}}</style>')
    defs = ('<defs><linearGradient id="undo-wood" x2="1" y2=".08"><stop stop-color="#74492a"/><stop offset=".34" stop-color="#5d3a20"/><stop offset=".62" stop-color="#6e4628"/><stop offset="1" stop-color="#4e2f1a"/></linearGradient>'
            '<linearGradient id="undo-alu" x2="0" y2="1"><stop stop-color="#ecebe5"/><stop offset=".42" stop-color="#d4d2ca"/><stop offset=".62" stop-color="#e2e0d9"/><stop offset="1" stop-color="#c2c0b7"/></linearGradient>'
            '<pattern id="undo-brush" width="240" height="5" patternUnits="userSpaceOnUse"><path d="M0 .5H150M60 2.5H240M0 4H96" stroke="#fff" stroke-opacity=".42" stroke-width=".6"/><path d="M90 1.5H240M0 3.2H130" stroke="#55524a" stroke-opacity=".14" stroke-width=".6"/></pattern>'
            '<linearGradient id="undo-face" x2="0" y2="1"><stop stop-color="#fbf1da"/><stop offset="1" stop-color="#ecd9ae"/></linearGradient>'
            '<linearGradient id="undo-brass" x2="1" y2="1"><stop stop-color="#e6c677"/><stop offset=".5" stop-color="#c9a24f"/><stop offset="1" stop-color="#dcb965"/></linearGradient>'
            '<radialGradient id="undo-platter"><stop offset=".8" stop-color="#b9b6ad"/><stop offset=".93" stop-color="#e7e5de"/><stop offset="1" stop-color="#a5a299"/></radialGradient>'
            f'<linearGradient id="undo-glass" x2="0" y2="1"><stop stop-color="#ff7a45"/><stop offset="1" stop-color="{UNDO_LAMP}"/></linearGradient>'
            f'<radialGradient id="undo-halo"><stop offset=".45" stop-color="{UNDO_LAMP}" stop-opacity=".55"/><stop offset="1" stop-color="{UNDO_LAMP}" stop-opacity="0"/></radialGradient>'
            f'<clipPath id="undo-tape"><rect x="296" y="156" width="338" height="80"/></clipPath><clipPath id="undo-cut"><circle cx="764" cy="112" r="72.4"/></clipPath>{clip_u}{clip_a}</defs>')
    screws = "".join(f'<circle cx="{x}" cy="{y}" r="3.4" fill="#a7a49b" stroke="#57534b" stroke-width=".7"/><path d="M{x - 2.3} {y + 1.2}l4.6 -2.4" stroke="#3a372f"/>' for x, y in [(272, 24), (856, 276), (272, 276)])
    tape_run = ('<path d="M274 88L275 212" fill="none" stroke="#2c1b0f" stroke-width="2.6"/><path d="M630 88L655 212" fill="none" stroke="#2c1b0f" stroke-width="2.6"/>'
                '<rect x="288" y="201" width="354" height="28" fill="#33200f"/><path d="M288 201.5H642M288 228.5H642" stroke="#6a4a2c" stroke-width=".8"/>')
    keys = ('<rect x="288" y="238" width="140" height="38" rx="3" fill="#7c786e"/>'
            '<rect x="291" y="241" width="66" height="32" rx="2" fill="#f0e8d6" stroke="#8f8878"/><path d="M304 251v12l-8 -6zM314 251v12l-8 -6z" fill="#3a332b"/>'
            + t(320, 263, "UNDO", UNDO_INK, 15, COND, 700, extra='class="undo-fine"')
            + '<rect x="360" y="241" width="32" height="32" rx="2" fill="#f0e8d6" stroke="#8f8878"/><path d="M371 250v14l11 -7z" fill="#3a332b"/>'
              '<rect x="395" y="241" width="30" height="32" rx="2" fill="#f0e8d6" stroke="#8f8878"/><rect x="404" y="251" width="12" height="12" fill="#3a332b"/>')
    rewind = (f'<g opacity="0">{anim("opacity", [(0, 0), (1.2, 0), (1.3, 1), (1.92, 1), (2.05, 0)], 12)}'
              '<rect x="291" y="242" width="66" height="32" rx="2" fill="#f2b75a" stroke="#a8742a"/><path d="M304 252v12l-8 -6zM314 252v12l-8 -6z" fill="#3a2410"/>'
              + t(320, 264, "UNDO", "#2d1c08", 15, COND, 700, extra='class="undo-fine"') + '</g>')
    head = ('<rect x="437" y="233" width="56" height="43" rx="3" fill="#2a2622" stroke="#6c685f"/><rect x="461" y="233" width="8" height="6" fill="#c9c7bf"/>'
            + t(465, 262, "HEAD", "#efe7d6", 15, COND, 700, "middle", 'class="undo-fine" letter-spacing="1"'))
    cord = '<path d="M493 252H670" fill="none" stroke="#7b4a24" stroke-width="3" stroke-linecap="round"/><path d="M493 251.4H670" fill="none" stroke="#d99a5e" stroke-width=".8"/>'
    pulse = (f'<path d="M493 252H670" fill="none" stroke="#ffd9a0" stroke-width="3.4" stroke-linecap="round" stroke-dasharray="26 400" stroke-dashoffset="26" opacity="0">'
             f'{anim("stroke-dashoffset", [(0, 26), (3.88, 26), (4.36, -177), (12, -177)], 12)}{anim("opacity", [(0, 0), (3.86, 0), (3.9, 1), (4.34, 1), (4.42, 0)], 12)}</path>')
    blade = (f'<g transform="translate(446 174)">{move([(0, 446, 174), (1.98, 446, 174), (2.12, 446, 186), (2.24, 446, 186), (2.46, 446, 174)], 12)}'
             '<path d="M0 0H38V13L19 20L0 13Z" fill="#dfddd6" stroke="#57534b" stroke-width=".8"/><path d="M0 13L19 20L38 13" fill="none" stroke="#fff" stroke-width="1"/>'
             '<rect x="14" y="3" width="10" height="5" rx="2.5" fill="#57534b"/></g>')
    splice = t(465, 170, "SPLICE", "#4a463e", 15, COND, 700, "middle", 'class="undo-fine" letter-spacing="1.4"')
    labels = "".join(undo_label(i) for i in range(8))
    strip = f'<g clip-path="url(#undo-tape)"><g>{undo_track("translate", [(f[0], f"{(f[1] - 1.75) * 120:.1f} 0", f[2]) for f in UNDO_TAPE])}{labels}</g></g>'
    rollers = "".join(f'<circle cx="{x}" cy="215" r="13" fill="#d8d6ce" stroke="#57534b"/><circle cx="{x}" cy="215" r="4" fill="#47433c"/>' for x in (288, 642))
    playline = '<path d="M465 197V233" stroke="#d92f18" stroke-width="1.4"/><path d="M460 195h10l-5 6z" fill="#d92f18"/>'
    key_well = '<rect x="800" y="224" width="58" height="48" rx="3" fill="#57534b"/>'
    key = (f'<g>{move([(0, 0, 0), (5.66, 0, 0), (5.78, 0, 2.5), (6.02, 0, 2.5), (6.2, 0, 0)], 12)}<rect x="803" y="227" width="52" height="40" rx="2" fill="#f4ecdb" stroke="#8f8878"/>'
           + t(829, 252, "APPROVE", UNDO_INK, 15, COND, 700, "middle", 'class="undo-fine"') + '</g>')
    finger = (f'<g transform="translate(829 322)">{move([(0, 829, 322), (4.92, 829, 322), (5.62, 829, 255), (5.78, 829, 259), (6.06, 829, 259), (6.72, 829, 322)], 12)}'
              '<path d="M-11 84V11Q-11 0 0 0Q11 0 11 11V84Z" fill="#b57f58" stroke="#6f4729" stroke-width="1"/><path d="M-6.5 11Q-6.5 4 0 4Q6.5 4 6.5 11V17Q0 20 -6.5 17Z" fill="#e7c6aa" stroke="#8d6242" stroke-width=".6"/>'
              '<path d="M-7 36q7 2.5 14 0M-7 40q7 2.5 14 0" fill="none" stroke="#7d5234" stroke-width=".7"/></g>')
    chassis = "".join(['<rect width="880" height="300" fill="url(#undo-wood)"/>', undo_grain(),
                       '<path d="M.75 0V300M879.25 0V300" stroke="#2b1809" stroke-width="1.5"/>',
                       t(25, 66, "Undo or ask", "#2a1608", 44, "'STIX Two Text',serif", 400, extra='font-style="italic"'),
                       t(24, 64.5, "Undo or ask", "#fbf0dc", 44, "'STIX Two Text',serif", 400, extra='font-style="italic"'),
                       f'<g class="undo-wide">{wide}{plate}</g><g class="undo-phone">{phone}</g>',
                       '<rect x="260" y="13" width="608" height="275" rx="7" fill="#2b1809" opacity=".65"/>',
                       '<rect x="262" y="14" width="604" height="272" rx="6" fill="url(#undo-alu)" stroke="#8a867b"/><rect x="262" y="14" width="604" height="272" rx="6" fill="url(#undo-brush)"/>',
                       '<path d="M263 15.5H865" stroke="#fff" stroke-opacity=".85"/>', screws, supply[0], takeup[0], face_u, face_a, plat_base, tape_run, keys, cord, head, lamp_base, key_well, splice])
    moving = "".join([supply[1], takeup[1], needle_u, needle_a, plat_spin, blade, strip, rewind, pulse, key, lamp_live, arm, '<clipPath id="undo-finger-well"><rect width="880" height="286"/></clipPath><g clip-path="url(#undo-finger-well)">', finger, "</g>"])
    top = "".join([supply[2], takeup[2], glass_u, glass_a, plat_sheen, rollers, playline])
    still = re.sub(r"<animate\w*\b[^>]*/>", "", moving).replace('<g opacity="0"><rect x="656"', '<g><rect x="656"')
    edges = ('<defs><linearGradient id="undo-seal-t" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4a2e17"/><stop offset="1" stop-color="#4a2e17" stop-opacity="0"/></linearGradient>'
             '<linearGradient id="undo-seal-b" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#4a2e17"/><stop offset="1" stop-color="#4a2e17" stop-opacity="0"/></linearGradient></defs>'
             '<rect x="-4" y="0" width="888" height="12" fill="url(#undo-seal-t)"/><rect x="-4" y="288" width="888" height="12" fill="url(#undo-seal-b)"/>'
             '<path d="M-4 0H884M-4 300H884" stroke="#4a2e17" stroke-width="2" vector-effect="non-scaling-stroke" shape-rendering="crispEdges"/>')
    return style + defs + chassis + f'<g class="replay">{moving}</g><g class="still">{still}</g>' + top + edges

def undo_or_ask():
    label = "Undo or ask. When an AI agent acts for you, should it ask first, or act and let you undo it? A study of which one actually catches more mistakes. Study design. No results yet."
    return svg(W, 300, label, BARLOW + [STIX[1]], undo_scene())

def fleet_move(frames, dur, begin=0, kind="translate"):
    return move(frames, dur, begin, kind)

def fleet_rotate(frames, dur, cx=0, cy=0, begin=0):
    times, values, n = _keyframes([(s, f"{ang:g} {cx:g} {cy:g}") for s, ang in frames], dur)
    splines = ";".join([EASE] * (n - 1))
    return (f'<animateTransform attributeName="transform" type="rotate" begin="{begin:g}s" dur="{dur}s" '
            f'repeatCount="indefinite" keyTimes="{times}" values="{values}" calcMode="spline" keySplines="{splines}"/>')

def fleet_defs(w, h):
    return (
        '<defs>'
        f'<clipPath id="fl-plate"><rect width="{w}" height="{h}"/></clipPath>'
        f'<clipPath id="fl-water-clip"><rect y="39" width="{w}" height="{h - 39}"/></clipPath>'
        '<linearGradient id="fl-sky" x2="0" y2="1">'
        '<stop offset="0" stop-color="#f5f0e3"/>'
        '<stop offset=".52" stop-color="#e3efe8"/>'
        '<stop offset="1" stop-color="#a8e0d8"/>'
        '</linearGradient>'
        '<linearGradient id="fl-sea" x2="0" y2="1">'
        '<stop offset="0" stop-color="#48d8cc"/>'
        '<stop offset=".16" stop-color="#21b5b9"/>'
        '<stop offset=".36" stop-color="#147fa0"/>'
        '<stop offset=".60" stop-color="#10497d"/>'
        '<stop offset=".83" stop-color="#0b2454"/>'
        '<stop offset="1" stop-color="#061030"/>'
        '</linearGradient>'
        '<linearGradient id="fl-ray" x2="0" y2="1">'
        '<stop offset="0" stop-color="#f2fffe" stop-opacity=".38"/>'
        '<stop offset=".42" stop-color="#7ef0e4" stop-opacity=".16"/>'
        '<stop offset="1" stop-color="#29b4be" stop-opacity="0"/>'
        '</linearGradient>'
        '<radialGradient id="fl-left-veil" cx=".20" cy=".64" r=".52" fx=".14" fy=".68">'
        '<stop offset="0" stop-color="#061738" stop-opacity=".64"/>'
        '<stop offset=".50" stop-color="#082047" stop-opacity=".44"/>'
        '<stop offset=".80" stop-color="#0b2e5a" stop-opacity=".16"/>'
        '<stop offset="1" stop-color="#0c315e" stop-opacity="0"/>'
        '</radialGradient>'
        '<radialGradient id="fl-left-veil-phone" cx=".26" cy=".62" r=".56" fx=".18" fy=".66">'
        '<stop offset="0" stop-color="#051432" stop-opacity=".78"/>'
        '<stop offset=".58" stop-color="#081f45" stop-opacity=".56"/>'
        '<stop offset=".84" stop-color="#0b2c57" stop-opacity=".20"/>'
        '<stop offset="1" stop-color="#0c315e" stop-opacity="0"/>'
        '</radialGradient>'
        '<linearGradient id="fl-wave-a" x2="0" y2="1">'
        '<stop offset="0" stop-color="#87efe4" stop-opacity=".76"/>'
        '<stop offset="1" stop-color="#25b2b8" stop-opacity=".10"/>'
        '</linearGradient>'
        '<linearGradient id="fl-wave-b" x2="0" y2="1">'
        '<stop offset="0" stop-color="#4fd9ce" stop-opacity=".92"/>'
        '<stop offset=".55" stop-color="#1ca0af" stop-opacity=".52"/>'
        '<stop offset="1" stop-color="#14799b" stop-opacity="0"/>'
        '</linearGradient>'
        '<linearGradient id="fl-buoy-red" x1=".15" y1=".08" x2=".88" y2=".92">'
        '<stop offset="0" stop-color="#ff7a6a"/>'
        '<stop offset=".38" stop-color="#db352b"/>'
        '<stop offset=".78" stop-color="#ab201a"/>'
        '<stop offset="1" stop-color="#6e1414"/>'
        '</linearGradient>'
        '<linearGradient id="fl-buoy-sub" x2="0" y2="1">'
        '<stop offset="0" stop-color="#962426"/>'
        '<stop offset="1" stop-color="#35183a"/>'
        '</linearGradient>'
        '<radialGradient id="fl-answer-halo">'
        '<stop offset="0" stop-color="#ffffff" stop-opacity=".98"/>'
        '<stop offset=".32" stop-color="#b4fcf4" stop-opacity=".68"/>'
        '<stop offset=".68" stop-color="#5ae3d8" stop-opacity=".22"/>'
        '<stop offset="1" stop-color="#38c6c2" stop-opacity="0"/>'
        '</radialGradient>'
        '<linearGradient id="fl-answer-beam" x2="0" y2="1">'
        '<stop offset="0" stop-color="#eafffd" stop-opacity=".74"/>'
        '<stop offset=".52" stop-color="#86f5ea" stop-opacity=".30"/>'
        '<stop offset="1" stop-color="#48d2c8" stop-opacity="0"/>'
        '</linearGradient>'
        '<linearGradient id="fl-scribe-body" x1=".05" y1=".15" x2=".95" y2=".85">'
        '<stop offset="0" stop-color="#fff9ef"/>'
        '<stop offset=".42" stop-color="#f4b7a3"/>'
        '<stop offset=".78" stop-color="#d95c57"/>'
        '<stop offset="1" stop-color="#a8363c"/>'
        '</linearGradient>'
        '<linearGradient id="fl-scribe-fin" x2="1" y2="1">'
        '<stop offset="0" stop-color="#b6faf0" stop-opacity=".95"/>'
        '<stop offset=".6" stop-color="#5fd2c8" stop-opacity=".82"/>'
        '<stop offset="1" stop-color="#339aa6" stop-opacity=".70"/>'
        '</linearGradient>'
        '<linearGradient id="fl-moth-wing" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#ebfcf8" stop-opacity=".92"/>'
        '<stop offset=".45" stop-color="#7be6d8" stop-opacity=".86"/>'
        '<stop offset="1" stop-color="#228fa3" stop-opacity=".72"/>'
        '</linearGradient>'
        '<linearGradient id="fl-medusa-out" x2="0" y2="1">'
        '<stop offset="0" stop-color="#f7e3f0" stop-opacity=".90"/>'
        '<stop offset=".5" stop-color="#c6b1e6" stop-opacity=".72"/>'
        '<stop offset="1" stop-color="#7cc7dc" stop-opacity=".38"/>'
        '</linearGradient>'
        '<radialGradient id="fl-medusa-core" cx=".5" cy=".4" r=".55">'
        '<stop offset="0" stop-color="#e8fffc" stop-opacity=".92"/>'
        '<stop offset=".6" stop-color="#99e9ec" stop-opacity=".42"/>'
        '<stop offset="1" stop-color="#99e9ec" stop-opacity="0"/>'
        '</radialGradient>'
        '<linearGradient id="fl-shell" x1=".12" y1=".1" x2=".88" y2=".92">'
        '<stop offset="0" stop-color="#f7efe0"/>'
        '<stop offset=".45" stop-color="#c6d8d2"/>'
        '<stop offset=".78" stop-color="#7aa2ad"/>'
        '<stop offset="1" stop-color="#3c6078"/>'
        '</linearGradient>'
        '<linearGradient id="fl-rock-far" x2="0" y2="1">'
        '<stop offset="0" stop-color="#1a3b6e"/>'
        '<stop offset="1" stop-color="#091536"/>'
        '</linearGradient>'
        '<linearGradient id="fl-rock-near" x2="0" y2="1">'
        '<stop offset="0" stop-color="#204775"/>'
        '<stop offset=".48" stop-color="#0f254f"/>'
        '<stop offset="1" stop-color="#07102a"/>'
        '</linearGradient>'
        '<radialGradient id="fl-node-glow">'
        '<stop offset="0" stop-color="#d4fffa" stop-opacity=".95"/>'
        '<stop offset=".45" stop-color="#6ce8dd" stop-opacity=".40"/>'
        '<stop offset="1" stop-color="#30b8c0" stop-opacity="0"/>'
        '</radialGradient>'
        '<pattern id="fl-grain" width="52" height="26" patternUnits="userSpaceOnUse">'
        '<path d="M2 5h10m14 3h11m-20 7h15m11 4h7M4 21h9" fill="none" stroke="#ffffff" stroke-opacity=".06" stroke-width=".55"/>'
        '<circle cx="15" cy="4" r=".55" fill="#d8faf5" fill-opacity=".09"/>'
        '<circle cx="40" cy="15" r=".6" fill="#061229" fill-opacity=".11"/>'
        '<circle cx="25" cy="22" r=".5" fill="#d8faf5" fill-opacity=".07"/>'
        '</pattern>'
        '</defs>'
    )

def fleet_backdrop(w, h):
    rays = [
        "M472 40L432 154 478 156 510 40Z",
        "M554 40L508 166 558 168 594 40Z",
        "M642 40L596 172 650 174 690 40Z",
        "M732 40L696 162 746 162 776 40Z",
        "M816 40L788 144 828 144 852 40Z",
        "M152 40L122 110 158 112 186 40Z",
        "M286 40L256 116 292 116 318 40Z",
    ]
    wash = (
        '<path d="M360 48Q520 42 690 52T880 48V84Q710 92 530 82T360 88Z" fill="#46dbd0" opacity=".20"/>'
        '<path d="M0 82Q185 66 380 90T750 82Q825 78 880 88V144Q680 130 460 146T0 138Z" fill="#0d4375" opacity=".28"/>'
        '<path d="M0 122Q215 108 435 128T880 122V204H0Z" fill="#091d48" opacity=".34"/>'
        '<path d="M510 144Q645 128 780 146L880 140V204H510Z" fill="#132559" opacity=".26"/>'
    )
    sky_lines = (
        '<g fill="none" stroke="#8ab5b2" stroke-width=".6" opacity=".48">'
        '<path d="M88 19q44-4 88 0m98-4q56-3 110 1m144-2q44-4 88 0m136 5q38-3 76 0"/>'
        '<path d="M18 33h844" stroke="#6aa5a6" stroke-width=".55" stroke-dasharray="20 8 6 10"/>'
        '</g>'
    )
    depth_etch = (
        '<g fill="none" stroke="#9cf0e8" stroke-width=".55" opacity=".18">'
        '<path d="M408 68q52-3 104 1m64-2q60-4 120 0m54 2q44-2 88 1"/>'
        '<path d="M432 99q62-2 124 1m88 2q52-3 104 0"/>'
        '<path d="M454 132q56-2 112 1m86-1q56-3 112 0" stroke="#85b9e0" opacity=".78"/>'
        '<path d="M490 158q48-2 96 1m76-1q52-2 104 0" stroke="#759fd0" opacity=".68"/>'
        '</g>'
    )
    return (
        f'<rect width="{w}" height="46" fill="url(#fl-sky)"/>'
        f'{sky_lines}'
        f'<rect y="39" width="{w}" height="{h - 39}" fill="url(#fl-sea)"/>'
        f'{wash}'
        + "".join(f'<path d="{d}" fill="url(#fl-ray)"/>' for d in rays)
        + f'{depth_etch}'
        + f'<rect class="fleet-wash-desk" y="40" width="{w}" height="{h - 40}" fill="url(#fl-left-veil)"/>'
        + f'<rect class="fleet-wash-phone" y="40" width="{w}" height="{h - 40}" fill="url(#fl-left-veil-phone)"/>'
        + f'<rect width="{w}" height="{h}" fill="url(#fl-grain)"/>'
    )

def fleet_seabed(dur, animate=True):
    far = (
        'M0 177Q64 167 142 175T292 180Q372 183 444 174T598 168Q664 166 728 176T880 164V204H0Z'
    )
    near = (
        'M0 186Q78 179 164 187T346 189Q436 185 516 178T672 183Q754 187 816 174L880 170V204H0Z'
    )
    hachures = (
        '<g fill="none" stroke="#5b90b4" stroke-width=".68" opacity=".46">'
        '<path d="M38 185l-6 14m13-14l-6 15m13-14l-5 14m88-10l-4 13m12-12l-5 13m13-12l-4 12m94-11l-4 12m12-12l-4 12"/>'
        '<path d="M454 183l-6 16m12-18l-6 18m12-19l-5 18m12-17l-5 17m12-16l-4 16m12-15l-4 15"/>'
        '<path d="M572 178l-5 18m12-18l-4 18m12-17l-4 18m12-16l-3 16m12-15l-3 15"/>'
        '<path d="M754 182l-5 16m12-18l-5 18m12-20l-5 19m12-20l-4 19m12-20l-4 19m12-18l-4 18m12-18l-4 18"/>'
        '</g>'
    )
    def kelp(x, y, scale, color, phase, sway=3.0):
        rot = fleet_rotate([(0, -sway), (dur / 2, sway), (dur, -sway)], dur, x, y, begin=-phase) if animate else ""
        return (
            f'<g>{rot}<g transform="translate({x} {y}) scale({scale})">'
            f'<path d="M0 0Q-6 -14 2 -28Q8 -40 1 -52" fill="none" stroke="{color}" stroke-width="2.1" stroke-linecap="round"/>'
            f'<path d="M-2 -14Q-13 -19 -14 -27Q-5 -26 -1 -19Z" fill="{color}"/>'
            f'<path d="M2 -25Q13 -31 15 -39Q5 -37 1 -30Z" fill="{color}"/>'
            f'<path d="M1 -38Q-9 -44 -9 -52Q-1 -49 2 -42Z" fill="{color}"/>'
            '</g></g>'
        )
    fans = (
        '<g fill="none" stroke-linecap="round">'
        '<g stroke="#c25962" stroke-width="1.2" opacity=".84">'
        '<path d="M518 180q-5-14-14-23m14 23q1-16 0-28m0 28q8-12 16-20m-23-5q-6-4-11-9m15-3q-2-7-6-11m9 13q5-7 11-11"/>'
        '<path d="M513 168q-6-2-10-6m15-4q4-4 9-5" stroke-width=".85"/>'
        '</g>'
        '<g stroke="#4295a2" stroke-width="1.15" opacity=".86">'
        '<path d="M742 183q-5-14-14-24m14 24q0-16 2-28m-2 28q8-13 17-20m-23-4q-5-5-8-12m14-2q1-7-2-13m6 15q6-6 13-10"/>'
        '</g>'
        '<g stroke="#7b63a3" stroke-width="1.05" opacity=".72">'
        '<path d="M416 185q-4-11-11-18m11 18q2-13 4-21m-4 21q6-10 13-15"/>'
        '</g>'
        '<g stroke="#b85460" stroke-width="1" opacity=".76">'
        '<path d="M234 186q-4-10-10-16m10 16q1-12 3-18m-3 18q6-8 11-12"/>'
        '</g>'
        '</g>'
    )
    nodes = [
        (534, 176, 2.3, 0), (544, 174, 1.9, 2), (618, 177, 2.4, 1),
        (627, 179, 1.9, 3.5), (656, 179, 2.1, 4.2), (804, 176, 2.2, 5),
    ]
    node_svg = []
    for nx, ny, nr, ph in nodes:
        pulse = anim("opacity", [(0, .52), (dur / 2, 1), (dur, .52)], dur, begin=-ph) if animate else ""
        node_svg.append(
            f'<g><circle cx="{nx}" cy="{ny}" r="{nr * 3.5:.1f}" fill="url(#fl-node-glow)">{pulse}</circle>'
            f'<circle cx="{nx}" cy="{ny}" r="{nr:.1f}" fill="#d0fff8" stroke="#16425b" stroke-width=".6"/></g>'
        )
    return (
        f'<path d="{far}" fill="url(#fl-rock-far)"/>'
        + kelp(436, 183, .74, "#1b586d", 1.2, 2.6)
        + kelp(724, 184, .88, "#1c6276", 3.4, 3.0)
        + kelp(854, 172, .95, "#1a556a", 0.6, 2.8)
        + kelp(52, 185, .60, "#174a66", 4.5, 2.2)
        + kelp(314, 187, .54, "#174662", 2.1, 2.2)
        + f'<path d="{near}" fill="url(#fl-rock-near)" stroke="#356891" stroke-width=".85"/>'
        + hachures + fans + "".join(node_svg)
    )

def fleet_waves_back(dur, animate=True):
    seg_a = "M-96 41.5" + "".join("q16 -4.2 32 0t32 0" for _ in range(17))
    seg_b = "M-96 44.5" + "".join("q12 3.3 24 0t24 0" for _ in range(23))
    shift_a = (
        '<animateTransform attributeName="transform" type="translate" values="0 0;64 0" dur="6s" repeatCount="indefinite"/>'
        if animate else ""
    )
    shift_b = (
        '<animateTransform attributeName="transform" type="translate" values="0 0;-48 0" dur="6s" repeatCount="indefinite"/>'
        if animate else ""
    )
    return (
        '<g clip-path="url(#fl-plate)">'
        f'<g>{shift_a}<path d="{seg_a}V74H-96Z" fill="url(#fl-wave-a)"/>'
        f'<path d="{seg_a}" fill="none" stroke="#eefdfa" stroke-width="1.4" opacity=".84"/></g>'
        f'<g>{shift_b}<path d="{seg_b}V76H-96Z" fill="url(#fl-wave-b)"/></g>'
        '</g>'
    )

def fleet_waves_front(dur, animate=True):
    seg_b = "M-96 44.5" + "".join("q12 3.3 24 0t24 0" for _ in range(23))
    foam = "".join(
        f'M{x} 42.2q7-2.2 15-.4m22 1.8q6-1.5 11 .2'
        for x in range(-40, 920, 96)
    )
    shift_b = (
        '<animateTransform attributeName="transform" type="translate" values="0 0;-48 0" dur="6s" repeatCount="indefinite"/>'
        if animate else ""
    )
    return (
        '<g clip-path="url(#fl-plate)">'
        f'<g>{shift_b}'
        f'<path d="{seg_b}" fill="none" stroke="#cbf8f3" stroke-width="1.15" opacity=".78"/>'
        f'<path d="{foam}" fill="none" stroke="#ffffff" stroke-width="1.25" stroke-linecap="round" opacity=".76"/>'
        '</g></g>'
    )

def fleet_buoy(dur, animate=True):
    bx, by = 682, 42
    chain_pts = [(682, 60), (683, 73), (685, 86), (687, 100), (690, 113),
                 (693, 127), (696, 140), (699, 154), (702, 167), (705, 180)]
    links = ['<path d="M682 57Q690 119 706 183" fill="none" stroke="#18344d" stroke-width="1.25" opacity=".68"/>']
    for i, (cx, cy) in enumerate(chain_pts):
        ang = 7 if i > 2 else 3
        if i % 2 == 0:
            links.append(f'<ellipse cx="{cx}" cy="{cy}" rx="2.2" ry="4.3" transform="rotate({ang} {cx} {cy})" fill="none" stroke="#5282a3" stroke-width="1" opacity=".78"/>')
        else:
            links.append(f'<path d="M{cx} {cy - 3.6}L{cx + .5} {cy + 3.6}" stroke="#72a3c0" stroke-width="1.15" opacity=".74"/>')
    anchor = (
        '<g transform="translate(706 183)">'
        '<path d="M-10 2l4.5-8.5h11l4.5 8.5z" fill="#1b3454" stroke="#5685a6" stroke-width=".95"/>'
        '<path d="M-5 -2h10" stroke="#3c6788" stroke-width=".7"/>'
        '<circle cx="0" cy="-6.5" r="2.3" fill="none" stroke="#76a6c4" stroke-width=".95"/>'
        '</g>'
    )
    rock_frames = [
        (0, -5.2), (0.65, 3.0), (1.35, -1.8), (2.2, 1.2), (4.2, -1.4),
        (6.4, 1.5), (8.6, -1.3), (10.50, 0.8), (10.82, -11.5),
        (11.16, 8.2), (11.54, -6.8), (12, -5.2),
    ]
    bob_frames = [
        (0, 0, .4), (1.6, 0, -1.2), (3.4, 0, 1.1), (5.5, 0, -.9),
        (7.6, 0, 1.0), (9.6, 0, -.9), (10.60, 0, -.4), (10.85, 0, 2.2),
        (11.35, 0, -1.2), (12, 0, .4),
    ]
    clapper_frames = [
        (0, 14), (0.55, -10), (1.15, 6), (1.8, 0), (10.50, 0),
        (10.80, -26), (11.12, 24), (11.45, -19), (11.75, 16), (12, 14),
    ]
    rock = fleet_rotate(rock_frames, dur, bx, by) if animate else f'transform="rotate(-5.2 {bx} {by})"'
    bob = fleet_move(bob_frames, dur) if animate else ""
    clapper = fleet_rotate(clapper_frames, dur, 0, -19) if animate else 'transform="rotate(14 0 -19)"'
    chime_op = (
        anim("opacity", [(0, .82), (.5, .42), (1.15, 0), (10.60, 0), (10.86, 1), (11.45, .88), (12, .82)], dur)
        if animate else ""
    )
    chime_sc = (
        move([(0, 1.06, 1.06), (1.0, 1.28, 1.28), (10.60, .70, .70), (11.18, 1.02, 1.02), (12, 1.06, 1.06)], dur, kind="scale")
        if animate else ""
    )
    ripple_op = (
        anim("opacity", [(0, .82), (.75, .32), (1.55, 0), (10.64, 0), (10.90, .95), (12, .82)], dur)
        if animate else ""
    )
    ripple_sc = (
        move([(0, 1.08, 1), (1.50, 1.72, 1.15), (10.64, .52, .85), (11.38, .96, 1), (12, 1.08, 1)], dur, kind="scale")
        if animate else ""
    )
    ans_op = (
        anim("opacity", [(0, .96), (1.45, .84), (2.25, 0), (11.18, 0), (11.62, .94), (12, .96)], dur)
        if animate else ""
    )
    ans_arc1 = (
        move([(0, -8, 13), (1.6, -20, 22), (2.25, -24, 25), (11.2, -2, 6), (12, -8, 13)], dur)
        if animate else 'transform="translate(-8 13)"'
    )
    ans_arc2 = (
        move([(0, -16, 19), (1.6, -29, 28), (2.25, -32, 31), (11.2, -7, 11), (12, -16, 19)], dur)
        if animate else 'transform="translate(-16 19)"'
    )
    ans_arc3 = (
        move([(0, -24, 25), (1.6, -36, 34), (2.25, -38, 36), (11.2, -12, 15), (12, -24, 25)], dur)
        if animate else 'transform="translate(-24 25)"'
    )
    buoy_art = (
        f'<g transform="translate({bx} {by})">'
        '<path d="M-9.5 7L-5 19H5L9.5 7Z" fill="url(#fl-buoy-sub)" stroke="#1a243d" stroke-width=".9"/>'
        '<path d="M-19 5C-19 -5 -11 -10.5 0 -10.5C11 -10.5 19 -5 19 5C14 9.5 -14 9.5 -19 5Z" fill="url(#fl-buoy-red)" stroke="#231a2a" stroke-width="1.05"/>'
        '<path d="M-18 2.4C-8.5 5.6 8.5 5.6 18 2.4L16.6 5.8C7.5 8.6 -7.5 8.6 -16.6 5.8Z" fill="#f8f3e8" opacity=".95"/>'
        '<path d="M-12 -4.8C-7 -7.8 2.5 -8.2 8.5 -6" fill="none" stroke="#ffbdb2" stroke-width="1.35" stroke-linecap="round" opacity=".78"/>'
        '<path d="M-10.5 -8L-4.5 -27H4.5L10.5 -8M-7.2 -15.5H7.2M-5.2 -21.5H5.2M-7.2 -15.5L5.2 -21.5M7.2 -15.5L-5.2 -21.5" fill="none" stroke="#1e3242" stroke-width="1.3" stroke-linejoin="round"/>'
        '<g>' + (clapper if animate else f'<g {clapper}>')
        + '<path d="M0 -19.5V-11.5" stroke="#223647" stroke-width="1.2"/>'
        + '<circle cx="0" cy="-11" r="1.6" fill="#dc3a30" stroke="#1b2d3d" stroke-width=".6"/>'
        + ('' if animate else '</g>') + '</g>'
        '<path d="M-5 -20.2C-5 -22.8 5 -22.8 5 -20.2L6.5 -13.8H-6.5Z" fill="#f7f1e3" stroke="#1e3242" stroke-width="1"/>'
        '<path d="M-5.1 -15.5H5.1" stroke="#d1382e" stroke-width="1.3"/>'
        '<circle cx="0" cy="-28.6" r="3.0" fill="#fffdf8" stroke="#22384b" stroke-width=".95"/>'
        '<path d="M-2.4 -31.2L0 -33.6L2.4 -31.2" fill="none" stroke="#22384b" stroke-width=".9"/>'
        '</g>'
    )
    buoy_wrap = (
        f'<g>{bob}<g>{rock}{buoy_art}</g></g>'
        if animate else f'<g {rock}>{buoy_art}</g>'
    )
    chime_group = (
        f'<g transform="translate({bx} {by - 18})"><g opacity="0.82">{chime_op}'
        f'<g>{chime_sc}'
        '<g fill="none" stroke-linecap="round">'
        '<path d="M-14 -5.5a12.5 12.5 0 0 0 0 11M14 -5.5a12.5 12.5 0 0 1 0 11" stroke="#d4392f" stroke-width="1.5"/>'
        '<path d="M-20 -9a19 19 0 0 0 0 18M20 -9a19 19 0 0 1 0 18" stroke="#ca4238" stroke-width="1.15" opacity=".80"/>'
        '<path d="M-26 -12.5a25 25 0 0 0 0 25M26 -12.5a25 25 0 0 1 0 25" stroke="#2a4c5e" stroke-width=".8" stroke-dasharray="3 2.5" opacity=".64"/>'
        '</g></g></g></g>'
    )
    ripples = (
        f'<g transform="translate({bx} {by + 4})"><g opacity="0.82">{ripple_op}'
        f'<g>{ripple_sc}'
        '<ellipse rx="28" ry="3.6" fill="none" stroke="#f0fdfa" stroke-width="1.35" opacity=".92"/>'
        '<ellipse rx="42" ry="4.9" fill="none" stroke="#baf5ee" stroke-width=".9" stroke-dasharray="9 4" opacity=".68"/>'
        '</g></g></g>'
    )
    answer = (
        f'<g opacity="0.96">{ans_op}'
        f'<circle cx="{bx}" cy="{by - 28.6}" r="22" fill="url(#fl-answer-halo)"/>'
        f'<path d="M{bx - 8} {by + 7}L{bx - 52} {by + 40}L{bx - 24} {by + 46}L{bx + 8} {by + 11}Z" fill="url(#fl-answer-beam)"/>'
        f'<g transform="translate({bx} {by + 8})">'
        + (f'<g>{ans_arc1}' if animate else f'<g {ans_arc1}>')
        + '<path d="M-8 -5a10 10 0 0 0 11 10" fill="none" stroke="#f2fffd" stroke-width="1.6" stroke-linecap="round" opacity=".92"/>'
        + '<circle cx="-3" cy="2" r="2.1" fill="#ffffff" opacity=".96"/></g>'
        + (f'<g>{ans_arc2}' if animate else f'<g {ans_arc2}>')
        + '<path d="M-11 -6a14 14 0 0 0 15 13" fill="none" stroke="#a6faf0" stroke-width="1.35" stroke-linecap="round" opacity=".88"/>'
        + '<circle cx="-3" cy="2" r="1.5" fill="#e8fffd" opacity=".92"/></g>'
        + (f'<g>{ans_arc3}' if animate else f'<g {ans_arc3}>')
        + '<path d="M-13 -7a17 17 0 0 0 18 15" fill="none" stroke="#76ebe0" stroke-width="1.1" stroke-dasharray="4 3" stroke-linecap="round" opacity=".78"/></g>'
        '</g></g>'
    )
    return "".join(links) + anchor + answer + ripples + buoy_wrap + chime_group

def fleet_hero_creature(dur, animate=True):
    pos_frames = [
        (0, 638, 72), (0.90, 642, 69), (1.85, 646, 72),
        (2.85, 696, 90), (3.85, 722, 122), (4.85, 696, 144),
        (5.95, 638, 146), (7.10, 568, 140), (8.15, 544, 118),
        (9.35, 580, 88), (10.45, 646, 64), (10.80, 660, 59),
        (11.30, 642, 69), (12, 638, 72),
    ]
    ang_frames = [
        (0, -30), (0.90, -26), (1.85, -8),
        (2.85, 38), (3.85, 98), (4.85, 152),
        (5.95, 178), (7.10, 198), (8.15, 258),
        (9.35, 312), (10.45, 334), (10.80, 338),
        (11.30, 330), (12, 330),
    ]
    fin_anim = (
        move([(0, 1, 1), (.75, 1, .84), (1.5, 1, 1)], 1.5, kind="scale")
        if animate else ""
    )
    tail_rot = (
        fleet_rotate([(0, -6), (1, 7), (2, -6)], 2, -18, 0)
        if animate else ""
    )
    crown_glow = (
        anim("opacity", [(0, .92), (1.6, .75), (2.3, 0), (11.2, 0), (11.65, .92), (12, .92)], dur)
        if animate else ""
    )
    art = (
        '<g>'
        '<g>' + tail_rot
        + '<path d="M-16 -2.5C-26 -8 -34 -3 -41 -7.5" fill="none" stroke="#f6c7b8" stroke-width="1.85" stroke-linecap="round"/>'
        + '<path d="M-17 0C-27 1 -35 5 -43 2" fill="none" stroke="#8df2e3" stroke-width="1.55" stroke-linecap="round"/>'
        + '<path d="M-16 3.5C-25 9 -33 11 -40 9.5" fill="none" stroke="#e4877d" stroke-width="1.35" stroke-linecap="round"/>'
        + '</g>'
        '<g>' + fin_anim
        + '<path d="M-14 -5.5C-8 -18 7 -19 14 -7.5C6 -9 -5 -8 -14 -5.5Z" fill="url(#fl-scribe-fin)" stroke="#163b4e" stroke-width=".82"/>'
        + '<path d="M-14 5.5C-8 18 7 19 14 7.5C6 9 -5 8 -14 5.5Z" fill="url(#fl-scribe-fin)" stroke="#163b4e" stroke-width=".82"/>'
        + '<path d="M-8 -13L-3 -7.5M-1 -14.5L3 -7.5M5 -12.5L8 -7.5M-8 13L-3 7.5M-1 14.5L3 7.5M5 12.5L8 7.5" stroke="#1e5f70" stroke-width=".6" opacity=".74"/>'
        + '</g>'
        '<path d="M-18 0C-15 -9 -2 -11 11 -7.5C19 -5.5 24.5 -2.2 27 0C24.5 2.2 19 5.5 11 7.5C-2 11 -15 9 -18 0Z" fill="url(#fl-scribe-body)" stroke="#172844" stroke-width="1.05"/>'
        '<path d="M-12 -3C-3 -6 9 -5 18 -2M-12 3C-3 6 9 5 18 2" fill="none" stroke="#b53d42" stroke-width=".8" opacity=".62"/>'
        '<path d="M-10 -5.5v11m4.5-12v13m4.5-12.5v12m4.5-11v10m4.5-8.5v7" stroke="#9e3e45" stroke-width=".55" opacity=".48"/>'
        '<circle cx="6" cy="0" r="1.45" fill="#9cf7ea" stroke="#1b4d60" stroke-width=".45"/>'
        '<circle cx=".5" cy="0" r="1.2" fill="#9cf7ea" opacity=".88"/>'
        '<circle cx="-5" cy="0" r="1.0" fill="#9cf7ea" opacity=".80"/>'
        '<circle cx="17.5" cy="0" r="2.65" fill="#10213d" stroke="#fff8ee" stroke-width=".75"/>'
        '<circle cx="18.3" cy="-.8" r=".9" fill="#ffffff"/>'
        '<path d="M25 -2.5Q29.5 -5 33 -3M25 2.5Q29.5 5 33 3" fill="none" stroke="#faece0" stroke-width=".95" stroke-linecap="round"/>'
        f'<circle cx="24" cy="0" r="10.5" fill="url(#fl-answer-halo)" opacity="0.92">{crown_glow}</circle>'
        '</g>'
    )
    bubbles = []
    for bx, by, r, start in [(662, 58, 2.3, 10.72), (668, 61, 1.6, 10.92), (656, 64, 1.4, 11.15), (698, 94, 1.8, 3.0), (720, 124, 1.5, 4.0)]:
        if animate:
            bop = anim("opacity", [(0, 0), (start, 0), (start + .12, .88), (start + 1.1, 0)], dur)
            bmv = move([(0, 0, 0), (start, 0, 0), (start + 1.1, 4, -22)], dur)
            bubbles.append(f'<g opacity="0">{bop}<g>{bmv}<circle cx="{bx}" cy="{by}" r="{r}" fill="#e8fffc" fill-opacity=".42" stroke="#dcfcf8" stroke-width=".8"/></g></g>')
        elif start > 10:
            bubbles.append(f'<circle cx="{bx + 2}" cy="{by - 10}" r="{r}" fill="#e8fffc" fill-opacity=".38" stroke="#dcfcf8" stroke-width=".8"/>')
    if animate:
        return (
            "".join(bubbles)
            + f'<g>{fleet_move(pos_frames, dur)}<g>{fleet_rotate(ang_frames, dur)}{art}</g></g>'
        )
    return "".join(bubbles) + f'<g transform="translate(638 72) rotate(-30)">{art}</g>'

def fleet_depth_creatures(dur, animate=True):
    moth_pos = [(0, 774, 84), (3, 798, 80), (6, 822, 86), (9, 796, 91), (12, 774, 84)]
    moth_mv = fleet_move(moth_pos, dur) if animate else ""
    moth_wing = move([(0, 1, 1), (1.5, 1, .82), (3, 1, 1)], 3, kind="scale") if animate else ""
    moth_art = (
        '<g>'
        '<g>' + moth_wing
        + '<path d="M-8 -2C-16 -18 2 -23 13 -11C17 -7 12 -2 5 -2Z" fill="url(#fl-moth-wing)" stroke="#12475d" stroke-width=".85"/>'
        + '<path d="M-6 2C-14 17 3 21 13 10C16 6 12 2 5 2Z" fill="url(#fl-moth-wing)" stroke="#12475d" stroke-width=".85"/>'
        + '<path d="M-4 -14L2 -3M2 -16L5 -3M7 -12L8 -3M-3 13L2 3M3 15L5 3M7 11L8 3" stroke="#186075" stroke-width=".6" opacity=".72"/>'
        + '<circle cx="1" cy="-10" r="1.4" fill="#e67e74" opacity=".88"/><circle cx="2" cy="9" r="1.25" fill="#e67e74" opacity=".84"/>'
        + '</g>'
        '<path d="M-16 0Q-25 -5 -33 -3M-16 0Q-26 4 -35 3" fill="none" stroke="#9cf2e6" stroke-width="1.15" stroke-linecap="round"/>'
        '<path d="M-18 0C-12 -3.5 0 -4.5 14 -3C19 -2 23 -.8 25 0C23 .8 19 2 14 3C0 4.5 -12 3.5 -18 0Z" fill="#2c9cab" stroke="#0f394d" stroke-width=".85"/>'
        '<path d="M-10 0H12" stroke="#c8faf2" stroke-width=".75" stroke-dasharray="3 2"/>'
        '<circle cx="17.5" cy="-.3" r="1.5" fill="#0d233d"/><circle cx="18" cy="-.8" r=".5" fill="#ffffff"/>'
        '<path d="M23 -1.5Q27 -4 29 -2.5M23 1.5Q27 4 29 2.5" fill="none" stroke="#defaf4" stroke-width=".8" stroke-linecap="round"/>'
        '</g>'
    )
    moth = (
        f'<g>{moth_mv}{moth_art}</g>'
        if animate else f'<g transform="translate(774 84)">{moth_art}</g>'
    )
    def medusa(x, y, scale, cls, phase):
        mv = fleet_move([(0, x, y), (3, x + 5, y - 6), (6, x + 2, y + 3), (9, x - 4, y - 3), (12, x, y)], dur, begin=-phase) if animate else ""
        pulse = move([(0, 1, 1), (1.5, 1.09, .91), (3, .94, 1.06), (4.5, 1.08, .92), (6, 1, 1)], 6, begin=-phase, kind="scale") if animate else ""
        body = (
            f'<g transform="scale({scale})">'
            '<path d="M-14 3C-14 -10 -7 -16 0 -16C7 -16 14 -10 14 3C10 5.5 6 1.8 2 4C-1 1.8 -5 5.5 -9 3.5C-11 4.5 -13 4 -14 3Z" fill="url(#fl-medusa-out)" stroke="#233764" stroke-width=".85"/>'
            '<ellipse cx="0" cy="-6" rx="7" ry="6.5" fill="url(#fl-medusa-core)"/>'
            '<path d="M-8 -13C-5 -7 -5 -1 -7 3M-3 -15.5C-2 -8 -2 -1 -3 3.5M3 -15.5C2 -8 2 -1 3 3.5M8 -13C5 -7 5 -1 7 3" fill="none" stroke="#ffffff" stroke-width=".6" opacity=".56"/>'
            '<path d="M-10 2.5Q-6 1 -2 2.8T6 2.8T11 2.2" fill="none" stroke="#f8e8f3" stroke-width=".8" opacity=".75"/>'
            '<path d="M-9 4Q-13 13 -9 22M-4 4Q-1 15 -5 27M0 4Q4 15 1 28M5 4Q9 14 5 25M9 4Q12 12 9 20" fill="none" stroke="#d8c8ee" stroke-width=".95" stroke-linecap="round" opacity=".80"/>'
            '<path d="M-2 4Q0 12 -2 21M2 4Q4 11 2 20" fill="none" stroke="#9cf5ec" stroke-width=".8" stroke-linecap="round" opacity=".72"/>'
            '</g>'
        )
        if animate:
            return f'<g class="{cls}">{mv}<g>{pulse}{body}</g></g>'
        return f'<g class="{cls}" transform="translate({x} {y})">{body}</g>'

    def shell_walker(x, y, scale, phase, flip=1):
        mv = fleet_move([(0, x, y), (6, x + 12 * flip, y + 1), (12, x, y)], dur, begin=-phase) if animate else ""
        body = (
            f'<g transform="scale({scale * flip} {scale})">'
            '<path d="M-10 5.5l-3.5 5.5m7-4.5l-1.2 5.5m5.5-5.5l2.2 5.5m5.5-5.5l4.5 4.5" stroke="#b0c4d4" stroke-width="1.2" stroke-linecap="round"/>'
            '<path d="M8.5 2C13 .8 16.5 2 17.8 4.4C15.5 6.8 11 6.8 7.5 5.6Z" fill="#e09c99" stroke="#182a4c" stroke-width=".8"/>'
            '<path d="M16.5 2Q21 -1.5 24.5 1M16.5 4.4Q22 3.2 24.5 5.6" fill="none" stroke="#f2cfc9" stroke-width=".9" stroke-linecap="round"/>'
            '<circle cx="14.2" cy="3" r="1.15" fill="#101f3b"/><circle cx="14.6" cy="2.6" r=".38" fill="#ffffff"/>'
            '<path d="M-12.5 4.5C-13.5 -6.5 -4.5 -14.5 4.5 -12.5C11.5 -10.5 13.5 -2 9 4.5C3.5 7 -5.5 7 -12.5 4.5Z" fill="url(#fl-shell)" stroke="#162c4a" stroke-width="1"/>'
            '<path d="M-7 2.5C-8 -4.5 -2.5 -9 3.5 -8C7 -6.8 8 -2.2 4.5 1.2C2.2 3.2 -2.2 2.4 -2.2 -1C-2.2 -3.2 1.2 -4.2 2.2 -2" fill="none" stroke="#294e69" stroke-width=".85"/>'
            '<path d="M-10.5 -1l4.5-2.2m-2.2-5.8l3.5 1.2m4.5-4.5l1.2 3.5m5.8 0l-2.2 2.5m-12 5.5l3.5-1" stroke="#3c6782" stroke-width=".65" opacity=".78"/>'
            '</g>'
        )
        if animate:
            return f'<g>{mv}{body}</g>'
        return f'<g transform="translate({x} {y})">{body}</g>'

    motes_data = [
        (110, 56, 1.1, 0), (240, 52, 1.0, 2.4), (390, 64, 1.2, 4.8), (470, 140, 1.1, 1.2),
        (518, 78, 1.2, 3.6), (594, 98, 1.0, 6.0), (632, 134, 1.1, 8.4), (722, 70, 1.2, 2.0),
        (746, 120, 1.0, 5.2), (836, 110, 1.1, 7.6), (854, 66, 1.0, 9.8), (496, 162, 1.0, 4.0),
    ]
    motes = []
    for mx, my, mr, ph in motes_data:
        if animate:
            mm = fleet_move([(0, 0, 0), (6, 6, -5), (12, 0, 0)], dur, begin=-ph)
            mo = anim("opacity", [(0, .28), (6, .78), (12, .28)], dur, begin=-ph)
            motes.append(f'<g>{mm}<circle cx="{mx}" cy="{my}" r="{mr}" fill="#d6fcf7" opacity=".5">{mo}</circle></g>')
        else:
            motes.append(f'<circle cx="{mx}" cy="{my}" r="{mr}" fill="#d6fcf7" opacity=".48"/>')
    return (
        "".join(motes)
        + moth
        + medusa(464, 98, .96, "fleet-mid-left", 1.2)
        + medusa(800, 130, .84, "fleet-mid-right", 4.6)
        + shell_walker(576, 175, 1.06, 0.8, 1)
        + shell_walker(824, 166, .82, 5.0, -1)
    )

def fleet_text_and_chrome(w, h):
    desk_lines = [
        "Most of the typing behind these numbers is done",
        "by AI agents. He runs them from one control room.",
        "When one needs a decision, it comes up and asks.",
    ]
    phone_lines = [
        "Most of the typing behind these numbers",
        "is done by AI agents. He runs them from",
        "one control room. When one needs a",
        "decision, it comes up and asks.",
    ]
    shadow_ink = 'fill="#05132c" opacity=".62"'
    desk = [
        '<g class="fleet-text-desk">',
        f'<text x="28" y="88.5" font-size="38" font-family="{SERIF}" font-weight="600" {shadow_ink}>The fleet</text>',
        t(28, 87, "The fleet", "#fcfaf2", 38, SERIF, 600),
    ]
    for i, line in enumerate(desk_lines):
        y = 117 + i * 22
        desk.append(f'<text x="28" y="{y + 1.2:.1f}" font-size="16.2" font-family="{SERIF}" {shadow_ink}>{line}</text>')
        desk.append(t(28, y, line, "#ecf7f4", 16.2, SERIF, 400))
    desk.append('</g>')

    phone = [
        '<g class="fleet-text-phone">',
        f'<text x="22" y="74.5" font-size="40" font-family="{SERIF}" font-weight="600" {shadow_ink}>The fleet</text>',
        t(22, 73, "The fleet", "#fcfaf2", 40, SERIF, 600),
    ]
    for i, line in enumerate(phone_lines):
        y = 103 + i * 27
        phone.append(f'<text x="22" y="{y + 1.4:.1f}" font-size="25" font-family="{SERIF}" {shadow_ink}>{line}</text>')
        phone.append(t(22, y, line, "#f0f9f7", 25, SERIF, 400))
    phone.append('</g>')

    ticks = "".join(
        f'<path d="M{w - 14} {y}H{w - 8}" stroke="#c6efea" stroke-width=".7" opacity=".46"/>'
        for y in (62, 88, 114, 140, 166)
    )
    corners = (
        f'<path d="M7.5 {h - 14}V{h - 7.5}H14M{w - 14} {h - 7.5}H{w - 7.5}V{h - 14}" '
        'fill="none" stroke="#2f5a6a" stroke-width="1.15" opacity=".55"/>'
    )
    chrome = (
        f'<defs><linearGradient id="fleet-rim" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{h}"><stop offset="{10 / h:.3f}" stop-color="#1c3a52" stop-opacity="0"/><stop offset="{44 / h:.3f}" stop-color="#1c3a52"/></linearGradient></defs><rect x=".5" y="-1" width="{w - 1}" height="{h + .5}" fill="none" stroke="url(#fleet-rim)" stroke-width="1"/>'
        '<g class="fleet-plate-chrome">'
        f'<rect x="7.5" y="-1" width="{w - 15}" height="{h - 6.5}" fill="none" stroke="#dff2ee" stroke-opacity=".38" stroke-width=".85"/>'
        f'<rect x="10" y="-1" width="{w - 20}" height="{h - 9}" fill="none" stroke="#2c596a" stroke-opacity=".30" stroke-width=".55"/>'
        f'{corners}{ticks}'
        + t(20, 24, "TAB. PELAGICA", "#2e5463", 11, SERIF, 600, extra='letter-spacing="1.8"')
        + t(w - 20, 24, "Sectio maris, ad vivum", "#2e5463", 12, SERIF, 400, "end", 'font-style="italic"')
        + '</g>'
    )
    return "".join(desk) + "".join(phone) + chrome

def fleet():
    w, h, dur = W, 204, 12
    style = (
        '<style>'
        '.still{display:none}'
        '.fleet-text-phone,.fleet-wash-phone{display:none}'
        '@media(prefers-reduced-motion:reduce){.replay{display:none}.still{display:inline}}'
        '@media(max-width:500px){'
        '.fleet-text-desk,.fleet-wash-desk,.fleet-plate-chrome,.fleet-mid-left{display:none}'
        '.fleet-text-phone,.fleet-wash-phone{display:inline}'
        '}'
        '</style>'
    )
    def scene(animate):
        return (
            fleet_waves_back(dur, animate)
            + fleet_seabed(dur, animate)
            + fleet_depth_creatures(dur, animate)
            + fleet_hero_creature(dur, animate)
            + fleet_buoy(dur, animate)
            + fleet_waves_front(dur, animate)
        )
    body = (
        style
        + fleet_defs(w, h)
        + f'<g clip-path="url(#fl-plate)">'
        + fleet_backdrop(w, h)
        + f'<g class="replay">{scene(True)}</g>'
        + f'<g class="still">{scene(False)}</g>'
        + fleet_text_and_chrome(w, h)
        + '</g>'
        + f'<path d="M-4 0H{w + 4}" stroke="#f2efe3" stroke-width="4" vector-effect="non-scaling-stroke" shape-rendering="crispEdges"/>'
    )
    label = (
        "The fleet. Most of the typing behind these numbers is done by AI agents. "
        "He runs them from one control room. When one needs a decision, it comes up and asks. "
        "A painted sea cross-section where creatures work at different depths while one rises to ring a red buoy and dives again."
    )
    return svg(w, h, label, STIX, body)


def oai_finishes():
    finishes = {
        "chrome": ("16%", "0%", "75%", "100%", [
            (0, "#f8e3c9"), (.12, "#8b7584"), (.25, "#494659"), (.34, "#a3a4b2"),
            (.45, "#f7f0e2"), (.49, "#d4cfca"), (.51, "#665f72"), (.71, "#282637"),
            (.82, "#514659"), (.92, "#b7a5a7"), (1, "#574955")]),
        "bezel": ("8%", "4%", "92%", "98%", [
            (0, "#fff1d5"), (.17, "#d2b9ae"), (.32, "#4f4657"), (.46, "#302d40"),
            (.59, "#898693"), (.69, "#d6d1ce"), (.86, "#655567"), (1, "#302838")]),
        "enamel": ("0%", "0%", "100%", "91%", [
            (0, "#b5a0a6"), (.14, "#6b6172"), (.3, "#484454"), (.52, "#282736"),
            (.79, "#171825"), (1, "#443846")]),
        "spindle": ("0%", "0%", "0%", "100%", [
            (0, "#2b2432"), (.16, "#907e89"), (.32, "#fce9cf"), (.43, "#c3b5b5"),
            (.52, "#706879"), (.83, "#403849"), (1, "#1d192a")]),
        "box": ("0%", "6%", "100%", "94%", [
            (0, "#a79187"), (.15, "#493841"), (.47, "#68545c"), (.78, "#2e2532"), (1, "#87746d")]),
        "glass": ("0%", "0%", "80%", "100%", [
            (0, "#798494"), (.22, "#435268"), (.42, "#263144"), (.6, "#131b2c"),
            (.75, "#292636"), (.94, "#69516b"), (1, "#242332")]),
    }
    gradients = []
    for name, (x1, y1, x2, y2, stops) in finishes.items():
        colors = "".join(f'<stop offset="{p}" stop-color="{c}"/>' for p, c in stops)
        gradients.append(f'<linearGradient id="oai-{name}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{colors}</linearGradient>')
    return '<defs>' + ''.join(gradients) + """
<radialGradient id="oai-room" cx="53%" cy="48%" r="54%">
  <stop stop-color="#74606b"/><stop offset=".29" stop-color="#58414f"/>
  <stop offset=".65" stop-color="#362538"/><stop offset="1" stop-color="#1d1424"/>
</radialGradient>
<radialGradient id="oai-light" cx="50%" cy="47%" r="73%">
  <stop stop-color="#fff7da"/><stop offset=".67" stop-color="#f4e6c9"/>
  <stop offset=".91" stop-color="#e8d7bc"/><stop offset="1" stop-color="#ddc7aa"/>
</radialGradient>
<radialGradient id="oai-aura">
  <stop stop-color="#ffe5bd" stop-opacity=".39"/><stop offset=".57" stop-color="#efceba" stop-opacity=".15"/>
  <stop offset="1" stop-color="#edccb5" stop-opacity="0"/>
</radialGradient>
<linearGradient id="oai-seal" x2="0%" y2="100%">
  <stop stop-color="#1d1424"/><stop offset=".09" stop-color="#1d1424" stop-opacity="0"/>
  <stop offset=".91" stop-color="#1d1424" stop-opacity="0"/><stop offset="1" stop-color="#1d1424"/>
</linearGradient>
<pattern id="oai-grip" patternUnits="userSpaceOnUse" width="3.4" height="4"><path d="M.4 0v4" stroke="#211c2c" stroke-width="1"/><path d="M1.5 0v4" stroke="#f1dbca" stroke-opacity=".52" stroke-width=".55"/></pattern>
<pattern id="oai-skin" patternUnits="userSpaceOnUse" width="6" height="5"><path d="M1 2h1m2 2h.5" stroke="#c3aeb9" stroke-width=".6" stroke-opacity=".22"/></pattern>
<clipPath id="oai-port"><circle r="21"/></clipPath>
</defs>"""

def oai_optotypes():
    glyphs = {
        "B": "M0 0h3.85L5 1v.95l-.75.57.75.65V4L3.85 5H0zM1.2 1v1h2.35l.25-.22v-.56L3.55 1zM1.2 3v1h2.35l.25-.22v-.55L3.52 3z",
        "E": "M0 0h5v1H1.1v1h3.1v1H1.1v1H5v1H0z",
        "T": "M0 0h5v1H3.05v4h-1.1V1H0z",
        "R": "M0 0h4l1 .92v1.34l-.95.86h-.64L5.1 5H3.67L1.98 3.12h-.85V5H0zM1.13 1v1.12h2.49l.28-.25v-.63L3.62 1z",
        "O": "M1.05 0h2.9L5 1.04v2.92L3.95 5h-2.9L0 3.96V1.04zM1.13 1.43v2.14l.43.43h1.88l.43-.43V1.43L3.44 1H1.56z",
        "W": "M0 0h1.04l.45 3.15.6-2.06h.82l.6 2.06L3.96 0H5l-.85 5H3.1l-.6-2.09L1.9 5H.85z",
        "S": "M1 0h4v1H1.47l-.32.3v.42l.3.28h2.63l.92.89v1.22L4.04 5H0V4h3.6l.28-.25v-.47L3.55 3H.96L0 2.06V.95z",
    }
    rows = []
    for word, y, size in [("B", 24, 10.3), ("ET", 91, 6.15), ("TER", 135, 4.45), ("OR", 171, 3.25), ("WORSE", 195, 2.45)]:
        width = (8 * len(word) - 3) * size
        letters = ''.join(f'<path transform="translate({i * 8})" d="{glyphs[letter]}"/>' for i, letter in enumerate(word))
        rows.append(f'<g transform="translate({(144 - width) / 2:.3f} {y}) scale({size})">{letters}</g>')
    return ''.join(rows)

def oai_chart():
    sharp = [(0, 1), (3.47, 1), (3.55, 0), (8.91, 0), (9.0, 1)]
    soft = [(at, 1 - opacity) for at, opacity in sharp]
    ink = '<rect width="144" height="232" mask="url(#oai-type)" fill="#2c2330"/>'
    spread = [(-3.8, .35), (-1.9, .75), (0, 1), (1.9, .75), (3.8, .35)]
    ghosts = ''.join(f'<g transform="translate({x} {y})" opacity="{.137 * wx * wy:.3f}">{ink}</g>'
                     for x, wx in spread for y, wy in spread)
    return (f'<defs><mask id="oai-type" maskUnits="userSpaceOnUse" x="0" y="0" width="144" height="232">'
            f'<g fill="white" fill-rule="evenodd">{oai_optotypes()}</g></mask></defs>'
            '<g class="oai-chart"><g transform="matrix(1 .03 0 1 0 0)">'
            '<ellipse cx="73" cy="110" rx="187" ry="152" fill="url(#oai-aura)"/>'
            '<rect x="9" y="7" width="151" height="240" rx="4" fill="#201925" opacity=".46"/>'
            '<path d="M-6 -5l8-4 148 1 5 4v236l-8 6H-6z" fill="url(#oai-box)" stroke="#302632" stroke-width="2"/>'
            '<rect x="-5" y="-5" width="154" height="242" rx="2" fill="#66575e" stroke="#bfa99a" stroke-width="1"/>'
            '<rect x="-1" y="-1" width="146" height="234" rx="2" fill="url(#oai-light)" stroke="#453843" stroke-width="2"/>'
            '<path d="M3 2h138M2 3v226" stroke="#fff5da" fill="none" opacity=".75"/>'
            '<path d="M30 163h84" stroke="#bb5b55" stroke-width="2.1"/>'
            '<path d="M38 217h68" stroke="#637b86" stroke-width="1.8"/>'
            '<g class="replay">'
            f'<g opacity="0">{anim("opacity", soft, 12)}{ghosts}</g>'
            f'<g>{anim("opacity", sharp, 12)}{ink}</g></g>'
            f'<g class="still">{ink}</g></g></g>')

def oai_turn(reverse):
    angles = [(0, 0), (3.22, 0), (3.53, 36), (3.63, 34),
              (8.68, 34), (8.98, -2), (9.08, 0)]
    times, values, n = _keyframes([(at, -a if reverse else a) for at, a in angles], 12)
    splines = ';'.join([EASE] * (n - 1))
    return (f'<animateTransform attributeName="transform" type="rotate" dur="12s" repeatCount="indefinite" '
            f'keyTimes="{times}" values="{values}" calcMode="spline" keySplines="{splines}"/>')

def oai_wheel(radius, reverse=False):
    marks = []
    for i in range(36):
        length = 3.7 if i % 3 == 0 else 2.4
        color = "#c5afac" if i % 3 == 0 else "#827783"
        marks.append(f'<path transform="rotate({i * 10})" d="M0 {-radius + 2.1}v{length}" stroke="{color}" stroke-width="1.15"/>')
    engraving = (''.join(marks) + f'<path d="M-.1 {-radius + 1.9}v5.6" stroke="#ffb397" stroke-width="2.8"/>')
    return (f'<circle r="{radius + 1.4}" fill="#24212c" stroke="url(#oai-bezel)" stroke-width="2.6"/>'
            f'<g class="replay">{oai_turn(reverse)}{engraving}</g><g class="still">{engraving}</g>')

def oai_screw(x, y, r=2.2):
    return (f'<g transform="translate({x} {y})"><circle r="{r}" fill="url(#oai-bezel)" stroke="#2a2431" stroke-width=".7"/>'
            f'<path d="M{-r * .55:.2f} {r * .32:.2f}l{r * 1.1:.2f} {-r * .64:.2f}" stroke="#3d3241" stroke-width=".85"/></g>')

def oai_optic(reverse=False):
    shell = ('M-51 -11C-52 -27 -44 -41 -31 -49L-24 -64Q-19 -75 -5 -75H11'
             'Q24 -74 31 -61L38 -40Q42 -33 54 -26Q62 -19 58 -8L52 10'
             'Q60 29 50 52Q41 78 16 83Q-11 89 -30 72Q-40 64 -44 49L-53 19Q-58 4 -51 -11Z')
    focus = [(0, 0, 0), (3.26, 0, 0), (3.57, 21, 0), (8.71, 21, 0), (9, 0, 0)]
    reflection = ('<path d="M-41 -16l28 -12 22 8-35 16z" fill="#f7dcbe" opacity=".57"/>'
                  '<path d="M-28 7L17 -14l2 2L-26 11z" fill="#b1b9ce" opacity=".28"/>'
                  '<path d="M8 20l25 -12 11 4-24 15z" fill="#bb809b" opacity=".58"/>')
    if reverse:
        reflection = f'<g transform="scale(-1 1)">{reflection}</g>'
    switch = '<path d="M-10 5L8 -9q2.5 -1 4 2l1 3L-5 10q-4 3 -6 -1z" fill="url(#oai-bezel)" stroke="#171622" stroke-width=".9"/>'
    optic = (f'<path d="{shell}" transform="translate(3 3)" fill="#18141e" stroke="#1b1820" stroke-width="4"/>'
             f'<path d="{shell}" fill="url(#oai-chrome)" stroke="#372e3d" stroke-width="1.1"/>'
             f'<path d="{shell}" transform="translate(0 1.2) scale(.946 .958)" fill="url(#oai-enamel)" stroke="#b9a6aa"/>'
             f'<path d="{shell}" transform="translate(0 1.2) scale(.928 .944)" fill="url(#oai-skin)"/>'
             '<path d="M-48 -7Q-52 -26 -31 -43M-35 58Q-23 83 3 80" fill="none" stroke="#ddc6bc" stroke-width="1.25" opacity=".7"/>'
             '<g transform="translate(3 -51)"><circle r="22" fill="url(#oai-bezel)" stroke="#302a39" stroke-width="1.4"/>'
             '<circle r="17.5" fill="#272433" stroke="#958894"/><circle r="14.5" fill="url(#oai-enamel)" stroke="#171825"/>'
             f'<g class="replay">{oai_turn(reverse)}{switch}</g><g class="still">{switch}</g></g>'
             '<g transform="translate(0 12)">' + oai_wheel(42, reverse) +
             '<circle r="34.3" fill="url(#oai-chrome)" stroke="#161623" stroke-width="1.3"/>'
             '<circle r="29.5" fill="url(#oai-enamel)" stroke="#ede2d1" stroke-width=".8"/>'
             '<circle r="25.4" fill="#110e1d" stroke="#69606d" stroke-width="2"/>'
             '<circle r="21.5" fill="url(#oai-glass)" stroke="#080e19"/>'
             '<g clip-path="url(#oai-port)"><g class="replay"><g>' + move(focus, 12) + reflection +
             '</g></g><g class="still">' + reflection + '</g></g>'
             '<path d="M-19 7A20 20 0 0 1 -6 -19M10 17Q15 15 18 9" fill="none" stroke="#b1a8bc" stroke-opacity=".63" stroke-width="1.1"/></g>'
             '<path d="M4 -34l-3 4-3 -4z" fill="#f1d8bf"/>'
             '<g transform="translate(-48 38) rotate(-18)"><path d="M-12 -5h17v10h-17z" fill="url(#oai-spindle)" stroke="#28212f"/>'
             '<rect x="-18" y="-11" width="12" height="22" rx="3" fill="url(#oai-bezel)" stroke="#292330"/>'
             '<path d="M-15 -9v18m3 -18v18m3 -18v18" stroke="#47404f" stroke-width="1.25"/></g>'
             '<g transform="translate(8 66)"><circle r="7.8" fill="url(#oai-bezel)" stroke="#211d2a"/>'
             '<circle r="5" fill="#272332" stroke="#827886"/><path d="M-3 -.4h6" stroke="#bca699" stroke-width="1.2"/></g>' +
             ''.join(oai_screw(x, y) for x, y in [(-34, -32), (38, -23), (-27, 57), (34, 53)]))
    return optic

def oai_instrument():
    ribs = '<path d="M-5 -4v8m3-8v8m3-8v8m3-8v8" fill="none" stroke="#36303f" stroke-width="1.3"/>'
    return ('<g class="oai-machine"><g transform="rotate(-7)">'
             '<path d="M-8 -71v-24q0 -11 11 -11h64q14 0 24 -10l26 -24q12 -12 33 -12h107" fill="none" stroke="#191621" stroke-width="16" stroke-linecap="round"/>'
             '<path d="M-8 -73v-22q0 -11 11 -11h64q14 0 24 -10l26 -24q12 -12 33 -12h107" fill="none" stroke="url(#oai-bezel)" stroke-width="12"/>'
             '<path d="M-11 -93q0 -15 14 -16h64q14 0 23 -9l25 -24q14 -13 36 -13h106" fill="none" stroke="#d0bbbd" stroke-opacity=".75" stroke-width="1.6"/>'
             '<g transform="translate(67 -106)"><circle r="12.5" fill="url(#oai-bezel)" stroke="#372b3b"/><circle r="7" fill="url(#oai-enamel)"/>'
             + oai_screw(0, 0, 4.1) + '</g>'
             '<path d="M-108 -44h216v14h-216z" fill="url(#oai-spindle)" stroke="#312635"/>'
             '<path d="M-32 -50h63v38q-4 10 -15 11h-32q-12 -1 -15 -12z" fill="url(#oai-chrome)" stroke="#211a28" stroke-width="1.5"/>'
             '<rect x="-19" y="-28" width="38" height="27" rx="7" fill="url(#oai-enamel)" stroke="#241e29"/>'
             '<rect x="-122" y="-55" width="245" height="9" rx="3" fill="url(#oai-spindle)" stroke="#332a37"/>'
             + ''.join(f'<g transform="translate({x} -50)">{ribs}</g>' for x in (-119, 118)) +
             '<g transform="translate(68 1) scale(-.94 .94)">' + oai_optic(True) + '</g>'
             '<g transform="translate(-65 0)">' + oai_optic() + '</g>'
             '<path d="M-70 -86h42l12 -7h33l12 7h40q8 0 8 8t-8 9H26l-12 8h-29l-13 -8h-42q-9 0 -9 -8t9 -9z" fill="url(#oai-chrome)" stroke="#352c38" stroke-width="1.8"/>'
             '<path d="M-67 -81h41m52 0h41" stroke="#fff0da" stroke-width="2" stroke-linecap="round"/>'
             + oai_screw(-66, -76, 3.1) + oai_screw(65, -76, 3.1) +
             '<rect x="-19" y="-97" width="38" height="16" rx="3" fill="url(#oai-spindle)" stroke="#2e2632"/>'
             '<rect x="-18" y="-95" width="36" height="12" rx="2" fill="url(#oai-grip)"/>'
             '<rect x="-29" y="-74" width="59" height="22" rx="6" fill="url(#oai-bezel)" stroke="#302634"/>'
             '<rect x="-25" y="-70" width="51" height="13" rx="3" fill="#262130" stroke="#8f828b"/>'
             '<path d="M-19 -66v3m5-4v4m5-3v3m5-4v4m5-3v3m5-4v4m5-3v3m5-4v4m5-3v3" fill="none" stroke="#d0c2ba" stroke-width="1"/>'
             '<path d="M0 -68v9" stroke="#e8a490" stroke-width="1.9"/>'
             '</g></g>')

def openai_card():
    title = "OpenAI"
    role = "AI Evaluation Specialist, contract, 2026"
    copy = "Evaluated frontier models. Which mostly means asking the oldest question in optometry."
    style = """<style>
.oai-plate .still,.oai-phone{display:none}
.oai-chart{transform:translate(408px,38px) scale(.96)}
.oai-machine{transform:translate(693px,169px) scale(1.13)}
@media(max-width:500px){
  .oai-desktop{display:none}.oai-phone{display:inline}
  .oai-chart{transform:translate(512px,42px) scale(.77)}
  .oai-machine{transform:translate(753px,183px) scale(.85)}
}
@media(prefers-reduced-motion:reduce){
  .oai-plate .replay{display:none}.oai-plate .still{display:inline}
}
</style>"""
    desktop = (t(36, 107, title, "#f8eadc", 79, SERIF, 450, extra='letter-spacing="-3.8"') +
               t(39, 143, role, "#d4b7bb", 18.5) +
               t(39, 194, "Evaluated frontier models.", "#f6e7da", 23.5, SERIF) +
               t(39, 227, "Which mostly means asking the", "#f0d8cf", 23.5, SERIF, extra='font-style="italic"') +
               t(39, 254, "oldest question in optometry.", "#f0d8cf", 23.5, SERIF, extra='font-style="italic"'))
    phone = (t(28, 86, title, "#f8eadc", 77, SERIF, 450, extra='letter-spacing="-3.4"') +
             t(30, 125, role, "#dfc5c8", 27) +
             t(30, 180, "Evaluated frontier models.", "#f6e7da", 32, SERIF) +
             t(30, 224, "Which mostly means asking the", "#f0d8cf", 32, SERIF, extra='font-style="italic"') +
             t(30, 261, "oldest question in optometry.", "#f0d8cf", 32, SERIF, extra='font-style="italic"'))
    body = (style + oai_finishes() + '<g class="oai-plate">'
            '<rect x="-3" y="-3" width="886" height="316" fill="#1d1424"/>'
            '<rect width="880" height="310" fill="url(#oai-room)"/>'
            '<g class="oai-desktop" fill="none"><path d="M320 259L880 233" stroke="#251c2b" opacity=".52"/><path d="M320 260L880 234" stroke="#876775" opacity=".17"/></g>'
            + oai_chart() + oai_instrument() + '<rect width="880" height="310" fill="url(#oai-seal)"/>'
            f'<g class="oai-desktop">{desktop}</g><g class="oai-phone">{phone}</g>'
            '<path d="M-3 -3h886v8H-3zM-3 305h886v8H-3z" fill="#1d1424"/></g>')
    return svg(W, 310, f"{title}. {role}. {copy} Better, or worse?", STIX + [BARLOW[0]], body)


if __name__ == "__main__":
    login, out_dir, since = sys.argv[1], sys.argv[2], sys.argv[3]
    sheets = {"sheet-reggate.svg": reggate(), "sheet-spillway.svg": spillway(), "sheet-certified-blind.svg": certified_blind(), "sheet-openai.svg": openai_card(), "sheet-undo.svg": undo_or_ask(),
              "sheet-fleet.svg": fleet(), "sheet-flow-record.svg": flow_record(fetch_stats(login, since, os.environ["GITHUB_TOKEN"]))}
    for name, svg in sheets.items():
        assert not re.search(r'[ ;"]nan[ ;"]', svg), name
        open(os.path.join(out_dir, name), "w").write(svg)
