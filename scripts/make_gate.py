"""Generates gate.svg: an animated terminal that runs Aadi's work through a gate. Pure SMIL animation, no JS, so it plays inside a GitHub README <img>. Base attributes hold the finished frame, because the reduced-motion still is the same markup with its animations stripped."""
import re
from html import escape
from itertools import accumulate
from pathlib import Path
from runpy import run_path

sheet = run_path(str(Path(__file__).with_name("sheets.py")))
W, H = 880, 356
CYCLE = 14.0
BG, FG = "#0d1117", "#e6edf3"
COMMAND = "gate check --owner aadi"
SUMMARY = "7 checked · 1 blocked · every decision recorded"
CLEAR, TYPE_START, ENTER = 1.4, 1.78, 3.4
REVEAL_STEP = .06
SCAN_START, ROW_STEP, SCAN_TIME, STALL = 3.95, .5, .36, 1.0
PUNCH_HOLD, PUNCH_STEP = .9, .028

ROWS = [
    ("reggate", "ALLOW", "insurance binds, checked against the carrier's rules"),
    ("spillway", "402", "payment required before the spend, not after the invoice"),
    ("certified-blind", "FLAG", "what AI filters throw away, and can't prove was safe"),
    ("undo-or-ask", "REFER", "should it ask first, or act and let you undo?"),
    ("openai (prev)", "ALLOW", "evaluated frontier models, on contract"),
    ("corgi (prev)", "ALLOW", "founding GTM + AI lead, YC S24"),
    ("stats-cards", "BLOCK", "0 stars. not putting that on a banner."),
]
PHONE_PUNCHLINE = "0 stars. no banner."

CHIP = {
    "ALLOW": ("#77d892", 'fill="#19392c"'),
    "402": ("#eec66e", 'fill="none" stroke="#d29922" stroke-width="1.5"'),
    "FLAG": ("#f4d27f", 'fill="#4c3a12"'),
    "REFER": ("#9ccbff", 'fill="#16314f"'),
    "BLOCK": ("#ffffff", 'fill="#d5302d"'),
}
SEGMENT = {
    "ALLOW": 'fill="#3fb950"',
    "402": 'fill="none" stroke="#d29922" stroke-width="1.5"',
    "FLAG": 'fill="#d29922"',
    "REFER": 'fill="#58a6ff"',
    "BLOCK": 'fill="#f85149"',
}
DESK = {
    "name": "desk", "prompt": (28, 76, 25), "first": 118, "pitch": 30, "size": 16, "name_x": 52,
    "chip": (228, 61, 23, 17, 15), "why_x": 307, "band": (19, 842, 29, 21), "marker": 3,
}
PHONE = {
    "name": "phone", "prompt": (24, 70, 29), "first": 114, "pitch": 37, "size": 28, "name_x": 24,
    "chip": (318, 112, 32, 25, 26), "why_x": 448, "band": (10, 860, 36, 27), "marker": 5,
}


def gate_anim(attr, frames, discrete=False):
    return sheet["anim"](attr, frames, CYCLE, discrete)


def gate_text(x, y, value, color=FG, size=16, extra=""):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" {extra}>{value}</text>'


def gate_beats():
    starts = [SCAN_START + i * ROW_STEP for i in range(len(ROWS))]
    return [(s, s + (STALL if i == len(ROWS) - 1 else SCAN_TIME)) for i, s in enumerate(starts)]


def gate_keystrokes():
    gaps = [.05 + (.09 if i and COMMAND[i - 1] == " " else 0) for i in range(len(COMMAND))]
    return list(accumulate(gaps, initial=TYPE_START))[:-1]


def gate_typed(char, at):
    return f'<tspan>{gate_anim("display", [(0, "inline"), (CLEAR, "none"), (at, "inline")], True)}{escape(char)}</tspan>'


def gate_command(layout):
    x, y, size = layout["prompt"]
    tokens = ['<tspan fill="#79bbff">$</tspan> ']
    for i, (char, at) in enumerate(zip(COMMAND, gate_keystrokes())):
        show = gate_anim("display", [(0, "inline"), (CLEAR, "none"), (at, "inline")], True)
        style = 'font-weight="700"' if i < 10 else 'fill="#aabad0"' if i < 19 else ""
        tokens.append(f"<tspan {style}>{show}{escape(char)}</tspan>")
    cursor = gate_anim("display", [(0, "none"), (CLEAR, "inline"), (CLEAR + .2, "none"), (TYPE_START - .04, "inline"), (ENTER, "none")], True)
    tokens.append(f'<tspan fill="#79bbff" display="none">{cursor}▍</tspan>')
    return gate_text(x, y, "".join(tokens), size=size, extra='xml:space="preserve"')


def gate_punchline(text, land):
    prefix, payoff = text.split(". ", 1)
    typed = f" {payoff}"
    tokens = [f"<tspan>{escape(prefix)}.</tspan>"]
    tokens += [gate_typed(char, land + PUNCH_HOLD + j * PUNCH_STEP) for j, char in enumerate(typed)]
    end = land + PUNCH_HOLD + len(typed) * PUNCH_STEP
    cursor = gate_anim("display", [(0, "none"), (land, "inline"), (land + .42, "none"), (land + .66, "inline"), (end + .14, "none")], True)
    tokens.append(f'<tspan fill="#ffb3aa" display="none">{cursor}▍</tspan>')
    return "".join(tokens)


def gate_row(index, data, beat, layout):
    name, verdict, why = data
    start, land = beat
    phone = layout["name"] == "phone"
    blocked = verdict == "BLOCK"
    y = layout["first"] + index * layout["pitch"]
    chip_x, chip_w, chip_h, chip_rise, chip_size = layout["chip"]
    band_x, band_w, band_h, band_rise = layout["band"]
    band_y = y - band_rise
    arrive = ENTER + .08 + index * REVEAL_STEP
    shown = gate_anim("opacity", [(0, 1), (CLEAR, 0), (arrive, 1)], True)
    landed = gate_anim("opacity", [(0, 1), (CLEAR, 0), (land, 1)], True)
    waiting = gate_anim("display", [(0, "none"), (arrive, "inline"), (land, "none")], True)
    scan = gate_anim("opacity", [(0, 0), (start, 0), (start + .08, 1), (land, 1), (land + .2, 0)])
    color, chip = CHIP[verdict]
    row = [f"<g>{shown}"]
    row.append(f'<g opacity="0">{scan}<rect x="{band_x}" y="{band_y}" width="{band_w}" height="{band_h}" fill="#16263a"/>'
               f'<rect x="{band_x + 1}" y="{band_y + 1}" width="{layout["marker"]}" height="{band_h - 2}" fill="#79bbff"/></g>')
    if blocked:
        bell = gate_anim("opacity", [(0, 0), (land, 0), (land + .03, .55), (land + .5, 0)])
        row.append(f'<g>{landed}<rect x="{band_x}" y="{band_y}" width="{band_w}" height="{band_h}" fill="#2a1a1f"/>'
                   f'<rect x="{band_x + 1}" y="{band_y + 1}" width="{layout["marker"]}" height="{band_h - 2}" fill="#f85149"/></g>'
                   f'<rect x="{band_x}" y="{band_y}" width="{band_w}" height="{band_h}" fill="#f85149" opacity="0">{bell}</rect>')
    if not phone:
        top = y - 23 if index == 0 else y - 4 - layout["pitch"]
        row.append(f'<path d="M30 {top}V{y - 4}h12" fill="none" stroke="#435363"/>')
    row.append(gate_text(layout["name_x"], y, escape(name), size=layout["size"], extra='font-weight="600"'))
    row.append(gate_text(chip_x + chip_w / 2, y, f"{waiting}····", "#5d6d7e", chip_size, 'text-anchor="middle" display="none"'))
    row.append(f"<g>{landed}")
    row.append(f'<rect x="{chip_x + .75}" y="{y - chip_rise + .75}" width="{chip_w - 1.5}" height="{chip_h - 1.5}" rx="2" {chip}/>')
    row.append(gate_text(chip_x + chip_w / 2, y, verdict, color, chip_size, 'font-weight="700" text-anchor="middle"'))
    if blocked:
        line = gate_punchline(PHONE_PUNCHLINE if phone else why, land)
        row.append(gate_text(layout["why_x"], y, line, "#ffe0db", layout["size"], 'xml:space="preserve"'))
    elif not phone:
        fit = 'textLength="541" lengthAdjust="spacingAndGlyphs"' if name == "spillway" else ""
        row.append(gate_text(layout["why_x"], y, escape(why), "#b7c5d4", layout["size"], fit))
    row.append("</g></g>")
    return "".join(row)


def gate_footer(beats):
    land = beats[-1][1]
    done = land + PUNCH_HOLD + len(ROWS[-1][2].split(". ", 1)[1]) * PUNCH_STEP + .34
    arrive = ENTER + .08 + len(ROWS) * REVEAL_STEP
    shown = gate_anim("opacity", [(0, 1), (CLEAR, 0), (arrive, 1)], True)
    finished = gate_anim("opacity", [(0, 1), (CLEAR, 0), (done, 1)], True)
    live = gate_anim("opacity", [(0, 0), (arrive, 1), (done, 0)], True)
    parts = [f'<g>{shown}<path d="M28 310.5h824" stroke="#33404d" stroke-dasharray="4 4"/>']
    parts.append(gate_text(28, 337, f"{finished}{SUMMARY}", "#b5c3d1", 15))
    parts.append(gate_text(28, 337, f"{live}checking records…", "#8abef5", 15, 'opacity="0"'))
    for index, ((_, verdict, _), (_, row_land)) in enumerate(zip(ROWS, beats)):
        x = 856 - 20 * len(ROWS) + index * 20
        lit = gate_anim("opacity", [(0, 1), (CLEAR, 0), (row_land, 1)], True)
        parts.append(f'<rect x="{x}" y="327" width="16" height="8" fill="#34404d"/>'
                     f'<g>{lit}<rect x="{x}" y="327" width="16" height="8" fill="{BG}"/>'
                     f'<rect x="{x + .75}" y="327.75" width="14.5" height="6.5" {SEGMENT[verdict]}/></g>')
    parts.append("</g>")
    return "".join(parts)


def gate_layer(layout):
    beats = gate_beats()
    rows = "".join(gate_row(i, entry, beat, layout) for i, (entry, beat) in enumerate(zip(ROWS, beats)))
    footer = gate_footer(beats) if layout["name"] == "desk" else ""
    return f'<g class="{layout["name"]}">{gate_command(layout)}{rows}{footer}</g>'


def build():
    faces = sheet["fonts"](sheet["COURIER"])
    transcript = gate_layer(DESK) + gate_layer(PHONE)
    still = re.sub(r"<animate [^>]*/>", "", transcript)
    title = gate_text(440, 22, "aadi@gate", "#74838f", 13, 'class="title" text-anchor="middle"')
    phone_title = gate_text(440, 26, "aadi@gate", "#8a98a6", 27, 'class="phone" text-anchor="middle"')
    label = ", ".join(f"{name.split(' ')[0]} {verdict}" for name, verdict, _ in ROWS)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="aadi@gate: {label}">
<style>{faces}text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,'Courier Prime',monospace}}.still,.phone{{display:none}}@media(max-width:500px){{.desk,.title{{display:none}}.phone{{display:inline}}}}@media(prefers-reduced-motion:reduce){{.replay{{display:none}}.still{{display:inline}}}}</style>
<defs><linearGradient id="gate-rim" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{H}"><stop offset="{(H - 44) / H:.3f}" stop-color="#2c3743"/><stop offset="{(H - 4) / H:.3f}" stop-color="#2c3743" stop-opacity="0"/></linearGradient></defs><rect y="12" width="880" height="{H - 12}" fill="{BG}"/><rect x=".5" y=".5" width="879" height="{H + 10}" rx="10" fill="{BG}" stroke="url(#gate-rim)"/>
<path d="M-4 {H}H{W + 4}" stroke="{BG}" stroke-width="4" vector-effect="non-scaling-stroke" shape-rendering="crispEdges"/>
<path d="M1 11Q1 1 11 1H869Q879 1 879 11V34H1Z" fill="#131920"/>
<path d="M1 34.5h878" stroke="#242d37"/>{title}{phone_title}
<g class="replay">{transcript}</g><g class="still">{still}</g>
</svg>
"""


if __name__ == "__main__":
    import sys
    Path(sys.argv[1]).write_text(build())
