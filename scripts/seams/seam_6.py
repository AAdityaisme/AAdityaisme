import math
import random
from xml.sax.saxutils import escape

W = 880
H = 176
DUR = 12
TOP_EDGE = "#4a2e17"
BOT_EDGE = "#141512"
FLAP_WORD = "EVIDENCE"
FLAP_DRUM = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
SPLINE = "0.42 0 0.2 1"


def s6_grain():
    rng = random.Random(61)
    dark, light = [], []
    for i in range(9):
        y = 3.5 + i * 3.0 + rng.uniform(-0.7, 0.7)
        amp, freq, phase = rng.uniform(0.7, 1.7), rng.uniform(0.005, 0.01), rng.uniform(0, 6.28)
        pts = [(x, y + amp * math.sin(x * freq + phase)) for x in range(-40, 1000, 160)]
        mids = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in zip(pts, pts[1:])]
        d = f"M{mids[0][0]:.0f} {mids[0][1]:.1f}" + "".join(
            f"Q{p[0]} {p[1]:.1f} {m[0]:.0f} {m[1]:.1f}" for p, m in zip(pts[1:], mids[1:])
        )
        (light if i % 3 == 0 else dark).append(d)
    return (
        f'<path d="{"".join(dark)}" fill="none" stroke="#2e1a0d" stroke-width=".9" opacity=".5"/>'
        f'<path d="{"".join(light)}" fill="none" stroke="#a87a50" stroke-width=".75" opacity=".3"/>'
    )


def s6_track(frames, kind, discrete=False):
    kept = [frames[0]]
    for frame in frames[1:]:
        if frame != kept[-1]:
            kept.append(frame)
    if kept[-1][0] < DUR:
        kept.append((DUR, kept[-1][1]))
    times = ";".join(f"{at / DUR:.5f}" for at, _ in kept)
    if kind == "opacity":
        values = ";".join(str(v) for _, v in kept)
        return (
            f'<animate attributeName="opacity" dur="{DUR}s" repeatCount="indefinite" '
            f'keyTimes="{times}" values="{values}" calcMode="discrete"/>'
        )
    values = ";".join(f"0 {-60 * v}" if kind == "translate" else f"1 {v}" for _, v in kept)
    mode = "discrete" if discrete else "linear"
    return (
        f'<animateTransform attributeName="transform" type="{kind}" dur="{DUR}s" repeatCount="indefinite" '
        f'keyTimes="{times}" values="{values}" calcMode="{mode}"/>'
    )


def s6_flap(x, y, final, land, seed):
    half = 18
    origin = f'transform="translate({x:g} {y + 20:g})"'
    seam = (
        '<path d="M0 0H36" stroke="#050605" stroke-width="1.6"/>'
        '<path d="M0 0H3M33 0H36" stroke="#6d6e60"/>'
    )
    base = (
        f'<g {origin}>'
        '<rect y="-20" width="36" height="20" rx="2" fill="url(#s6-flapTop)"/>'
        '<rect width="36" height="20" rx="2" fill="url(#s6-flapBottom)"/>'
        f'<text x="{half:g}" y="12.5">{escape(final)}</text>{seam}</g>'
    )
    step = 0.085
    prior = 3 + seed % 2
    at = FLAP_DRUM.find(final)
    strip = final + "".join(FLAP_DRUM[(at - prior + k) % len(FLAP_DRUM)] for k in range(prior))
    xs = " ".join(f"{half:g}" for _ in strip)
    ys = " ".join(f"{12.5 + 60 * k:g}" for k in range(len(strip)))
    glyphs = f'<text x="{xs}" y="{ys}">{escape(strip)}</text>'
    current, upcoming, fold, unfold, show = [(0, 0)], [(0, 0)], [(0, 1)], [(0, 0)], [(0, 0)]
    begin = round(land - (prior + 1) * step, 3)
    show += [(begin, 1), (land, 0)]
    for j, target in enumerate(list(range(1, prior + 1)) + [0]):
        flip = round(begin + j * step, 3)
        mid, end = round(flip + step / 2, 3), round(flip + step, 3)
        upcoming.append((flip, target))
        current.append((end, target))
        fold += [(flip, 1), (mid, 0), (end, 0), (end, 1)]
        unfold += [(mid, 0), (end, 1), (end, 0)]
    now = f'<g>{s6_track(current, "translate", True)}{glyphs}</g>'
    next_up = f'<g>{s6_track(upcoming, "translate", True)}{glyphs}</g>'
    overlay = (
        f'<g {origin} opacity="0">{s6_track(show, "opacity")}'
        f'<g clip-path="url(#s6-flapUp)"><rect y="-20" width="36" height="20" fill="url(#s6-flapTop)"/>{next_up}</g>'
        f'<g clip-path="url(#s6-flapDn)"><rect width="36" height="20" fill="url(#s6-flapBottom)"/>{now}</g>'
        f'<g>{s6_track(fold, "scale")}<g clip-path="url(#s6-flapUp)"><rect y="-20" width="36" height="20" fill="#2f302b"/>{now}</g></g>'
        f'<g>{s6_track(unfold, "scale")}<g clip-path="url(#s6-flapDn)"><rect width="36" height="20" fill="#121311"/>{next_up}</g></g>'
        f'{seam}</g>'
    )
    return base, overlay


def s6_phone_flap(x, y, final, land, seed):
    half = 17
    origin = f'transform="translate({x:g} {y + 16:g})"'
    seam = (
        '<path d="M0 0H34" stroke="#050605" stroke-width="1.6"/>'
        '<path d="M0 0H2.5M31.5 0H34" stroke="#6d6e60"/>'
    )
    base = (
        f'<g {origin}>'
        '<rect y="-16" width="34" height="16" rx="2" fill="url(#s6-flapTop)"/>'
        '<rect width="34" height="16" rx="2" fill="url(#s6-flapBottom)"/>'
        f'<text x="{half:g}" y="10">{escape(final)}</text>{seam}</g>'
    )
    step = 0.085
    prior = 3 + seed % 2
    at = FLAP_DRUM.find(final)
    strip = final + "".join(FLAP_DRUM[(at - prior + k) % len(FLAP_DRUM)] for k in range(prior))
    xs = " ".join(f"{half:g}" for _ in strip)
    ys = " ".join(f"{10 + 60 * k:g}" for k in range(len(strip)))
    glyphs = f'<text x="{xs}" y="{ys}">{escape(strip)}</text>'
    current, upcoming, fold, unfold, show = [(0, 0)], [(0, 0)], [(0, 1)], [(0, 0)], [(0, 0)]
    begin = round(land - (prior + 1) * step, 3)
    show += [(begin, 1), (land, 0)]
    for j, target in enumerate(list(range(1, prior + 1)) + [0]):
        flip = round(begin + j * step, 3)
        mid, end = round(flip + step / 2, 3), round(flip + step, 3)
        upcoming.append((flip, target))
        current.append((end, target))
        fold += [(flip, 1), (mid, 0), (end, 0), (end, 1)]
        unfold += [(mid, 0), (end, 1), (end, 0)]
    now = f'<g>{s6_track(current, "translate", True)}{glyphs}</g>'
    next_up = f'<g>{s6_track(upcoming, "translate", True)}{glyphs}</g>'
    overlay = (
        f'<g {origin} opacity="0">{s6_track(show, "opacity")}'
        f'<g clip-path="url(#s6-pFlapUp)"><rect y="-16" width="34" height="16" fill="url(#s6-flapTop)"/>{next_up}</g>'
        f'<g clip-path="url(#s6-pFlapDn)"><rect width="34" height="16" fill="url(#s6-flapBottom)"/>{now}</g>'
        f'<g>{s6_track(fold, "scale")}<g clip-path="url(#s6-pFlapUp)"><rect y="-16" width="34" height="16" fill="#2f302b"/>{now}</g></g>'
        f'<g>{s6_track(unfold, "scale")}<g clip-path="url(#s6-pFlapDn)"><rect width="34" height="16" fill="#121311"/>{next_up}</g></g>'
        f'{seam}</g>'
    )
    return base, overlay


def s6_spline_anim(kind, frames):
    times = ";".join(f"{t / DUR:.4f}" for t, _ in frames)
    values = ";".join(str(v) for _, v in frames)
    splines = ";".join([SPLINE] * (len(frames) - 1))
    return (
        f'<animateTransform attributeName="transform" type="{kind}" dur="{DUR}s" repeatCount="indefinite" '
        f'keyTimes="{times}" values="{values}" calcMode="spline" keySplines="{splines}"/>'
    )


def s6_sprocket(cx, cy, r_outer, r_inner, teeth, animated):
    pts = []
    for k in range(teeth * 2):
        angle = math.radians(k * 360 / (teeth * 2))
        r = r_outer if k % 2 == 0 else r_inner
        pts.append(f"{r * math.cos(angle):.1f} {r * math.sin(angle):.1f}")
    gear_d = "M" + "L".join(pts) + "Z"
    spokes = "".join(
        f'<path d="M0 0L{(r_inner - 2.6) * math.cos(math.radians(a)):.1f} {(r_inner - 2.6) * math.sin(math.radians(a)):.1f}" stroke="#221e16" stroke-width="2.2"/>'
        for a in (0, 60, 120, 180, 240, 300)
    )
    rot = s6_spline_anim("rotate", [(0, 0), (1.4, 0), (4.8, 360), (12, 360)]) if animated else ""
    return (
        f'<g transform="translate({cx} {cy})">'
        f'<circle cy="1.5" r="{r_outer + 0.8:.1f}" fill="#050605" opacity=".55"/>'
        f'<g>{rot}'
        f'<path d="{gear_d}" fill="url(#s6-brass)" stroke="#5c441c" stroke-width=".85"/>'
        f'<circle r="{r_inner - 2.3:.1f}" fill="#2b261d" stroke="#99773a" stroke-width=".8"/>'
        f'{spokes}'
        '<circle r="6" fill="#c7c5bd" stroke="#47433c" stroke-width=".8"/>'
        '</g></g>'
    )


def s6_roller(cx, cy, r, direction, animated):
    rot = s6_spline_anim("rotate", [(0, 0), (1.4, 0), (4.8, 360 * direction), (12, 360 * direction)]) if animated else ""
    return (
        f'<g transform="translate({cx} {cy})">'
        f'<circle cy="1.5" r="{r + 1}" fill="#050605" opacity=".62"/>'
        f'<circle r="{r}" fill="url(#s6-alu)" stroke="#57534b" stroke-width=".9"/>'
        f'<g>{rot}'
        f'<circle r="{r * 0.56:.1f}" fill="#35322c" stroke="#8a867b" stroke-width=".7"/>'
        f'<path d="M0 {-r * 0.85:.1f}V{-r * 0.56:.1f}M0 {r * 0.56:.1f}V{r * 0.85:.1f}" stroke="#57534b" stroke-width="1.2"/>'
        '<circle r="2.2" fill="#c7c5bd"/>'
        '</g></g>'
    )


def s6_screw(cx, cy, r=2.7):
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#8a8c83" stroke="#2d2f29" stroke-width=".7"/>'
        f'<path d="M{cx - r * 0.65:.1f} {cy + r * 0.4:.1f}l{r * 1.3:.1f} {-r * 0.8:.1f}" stroke="#22241f" stroke-width=".9"/>'
    )


def s6_tape_marks(x0, x1, y_top, h, pitch, animated):
    items = []
    start = x0 - pitch
    count = int((x1 - x0) / pitch) + 3
    for k in range(count):
        x = start + k * pitch
        items.append(
            f'<path d="M{x} {y_top + 2}v{h - 4}M{x + 28} {y_top + 3}v{h - 6}M{x + 56} {y_top + 2}v{h - 4}'
            f'M{x + 104} {y_top + 3}v{h - 6}M{x + 132} {y_top + 2}v{h - 4}" stroke="#7d4f2c" stroke-width=".9" opacity=".62"/>'
        )
        items.append(
            f'<path d="M{x + 76} {y_top + 1}L{x + 84} {y_top + h - 1}H{x + 77}L{x + 69} {y_top + 1}Z" '
            'fill="#efe6d2" stroke="#9e8f75" stroke-width=".5" opacity=".92"/>'
        )
    shift = s6_spline_anim("translate", [(0, "0 0"), (1.4, "0 0"), (4.8, f"{pitch} 0"), (12, f"{pitch} 0")]) if animated else ""
    return f'<g>{shift}{"".join(items)}</g>'


def s6_vert_marks(x_left, w, y0, y1, pitch, animated):
    items = []
    start = y0 - pitch
    count = int((y1 - y0) / pitch) + 3
    for k in range(count):
        y = start + k * pitch
        items.append(
            f'<path d="M{x_left + 2} {y}h{w - 4}M{x_left + 3} {y + 20}h{w - 6}M{x_left + 2} {y + 40}h{w - 4}'
            f'M{x_left + 3} {y + 60}h{w - 6}" stroke="#7d4f2c" stroke-width=".9" opacity=".65"/>'
        )
        items.append(
            f'<path d="M{x_left + 1} {y + 50}L{x_left + w - 1} {y + 56}V{y + 50}L{x_left + 1} {y + 44}Z" '
            'fill="#efe6d2" stroke="#9e8f75" stroke-width=".5" opacity=".88"/>'
        )
    shift = s6_spline_anim("translate", [(0, "0 0"), (1.4, "0 0"), (4.8, f"0 {pitch}"), (12, f"0 {pitch}")]) if animated else ""
    return f'<g>{shift}{"".join(items)}</g>'


def build(s):
    style = (
        '<style>'
        '.s6-phone,.still{display:none}'
        '@media (prefers-reduced-motion:reduce){.replay{display:none}.still{display:inline}}'
        '@media (max-width:500px){.s6-desk{display:none}.s6-phone{display:inline}}'
        '</style>'
    )
    defs = (
        '<defs>'
        '<linearGradient id="s6-wood" x2="1" y2=".06">'
        '<stop stop-color="#74492a"/><stop offset=".34" stop-color="#5d3a20"/>'
        '<stop offset=".62" stop-color="#6e4628"/><stop offset="1" stop-color="#4e2f1a"/></linearGradient>'
        '<linearGradient id="s6-metal" x2="0" y2="1">'
        '<stop stop-color="#3e4039"/><stop offset=".35" stop-color="#343630"/><stop offset="1" stop-color="#51534b"/></linearGradient>'
        '<linearGradient id="s6-boardBot" x2="0" y2="1">'
        '<stop stop-color="#0d0e0c"/><stop offset=".8" stop-color="#0d0e0c"/><stop offset="1" stop-color="#141512"/></linearGradient>'
        '<linearGradient id="s6-bezel" x2="0" y2="1">'
        '<stop stop-color="#4c4e46"/><stop offset="1" stop-color="#282a25"/></linearGradient>'
        '<linearGradient id="s6-alu" x2="0" y2="1">'
        '<stop stop-color="#e8e6df"/><stop offset=".5" stop-color="#cfcdc5"/><stop offset="1" stop-color="#aeaca3"/></linearGradient>'
        '<linearGradient id="s6-brass" x2="1" y2="1">'
        '<stop stop-color="#e3c06f"/><stop offset=".5" stop-color="#b9903d"/><stop offset="1" stop-color="#d4ae5a"/></linearGradient>'
        '<linearGradient id="s6-tapeH" x2="0" y2="1">'
        '<stop stop-color="#7c4e2c"/><stop offset=".24" stop-color="#422512"/>'
        '<stop offset=".76" stop-color="#291509"/><stop offset="1" stop-color="#623b1f"/></linearGradient>'
        '<linearGradient id="s6-tapeV" x2="1" y2="0">'
        '<stop stop-color="#784b29"/><stop offset=".26" stop-color="#3e2311"/>'
        '<stop offset=".78" stop-color="#271408"/><stop offset="1" stop-color="#5c371d"/></linearGradient>'
        '<linearGradient id="s6-flapTop" x2="0" y2="1"><stop stop-color="#2a2b27"/><stop offset="1" stop-color="#212220"/></linearGradient>'
        '<linearGradient id="s6-flapBottom" x2="0" y2="1"><stop stop-color="#1a1b19"/><stop offset="1" stop-color="#20211e"/></linearGradient>'
        '<linearGradient id="s6-shaft" x2="0" y2="1"><stop stop-color="#7c7e74"/><stop offset=".45" stop-color="#d4d5cc"/><stop offset="1" stop-color="#3e4039"/></linearGradient>'
        '<linearGradient id="s6-topShadow" x2="0" y2="1"><stop stop-color="#070503" stop-opacity=".75"/><stop offset="1" stop-color="#070503" stop-opacity="0"/></linearGradient>'
        '<clipPath id="s6-grainClip"><rect x="0" y="1" width="880" height="28"/></clipPath>'
        '<clipPath id="s6-tapeHClip"><rect x="118" y="51" width="361" height="10"/></clipPath>'
        '<clipPath id="s6-tapeVClip"><rect x="97" y="23" width="10" height="26"/></clipPath>'
        '<clipPath id="s6-phoneTapeClip"><rect x="115" y="34" width="426" height="11"/></clipPath>'
        '<clipPath id="s6-flapUp"><rect y="-20" width="36" height="20"/></clipPath>'
        '<clipPath id="s6-flapDn"><rect width="36" height="20"/></clipPath>'
        '<clipPath id="s6-pFlapUp"><rect y="-16" width="34" height="16"/></clipPath>'
        '<clipPath id="s6-pFlapDn"><rect width="34" height="16"/></clipPath>'
        '</defs>'
    )

    walnut_apron = (
        '<rect width="880" height="30" fill="url(#s6-wood)"/>'
        f'<g clip-path="url(#s6-grainClip)">{s6_grain()}</g>'
        '<path d="M0 27.5H880" stroke="#8c5f3b" stroke-opacity=".55" stroke-width="1"/>'
        '<path d="M0 29.5H880" stroke="#241308" stroke-width="2"/>'
        '<path d="M.75 0V30M879.25 0V30" stroke="#2b1809" stroke-width="1.5"/>'
    )

    slot_plate = (
        '<rect x="65" y="9" width="76" height="20" rx="2" fill="url(#s6-alu)" stroke="#4c3928" stroke-width=".9"/>'
        '<path d="M67 10.5H139" stroke="#fff" stroke-opacity=".7" stroke-width=".8"/>'
        '<rect x="83" y="18" width="40" height="11" rx="1.5" fill="#140c06" stroke="#5f5b53" stroke-width=".8"/>'
        '<rect x="89" y="21" width="28" height="8" fill="#090502"/>'
        + s6_screw(74, 19, 2.6)
        + s6_screw(132, 19, 2.6)
    )

    guide_bracket = (
        '<rect x="190" y="42" width="18" height="29" rx="2" fill="#232520" stroke="#454840" stroke-width=".8"/>'
        '<rect x="194" y="45" width="10" height="4.5" rx="1" fill="#9a9c92"/>'
        '<rect x="194" y="62.5" width="10" height="4.5" rx="1" fill="#9a9c92"/>'
    )

    lower_housing = (
        f'<rect y="30" width="880" height="{H - 30}" fill="url(#s6-metal)"/>'
        f'<path d="M1 30V{H}M879 30V{H}" stroke="#77786e"/>'
        f'<rect x="8" y="30" width="864" height="{H - 29}" fill="url(#s6-boardBot)" stroke="#050605" stroke-width="2"/>'
        '<rect x="8" y="30" width="428" height="67" fill="#141612"/>'
        '<rect x="18" y="38" width="406" height="49" rx="3" fill="#191b16" stroke="#282b24" stroke-width=".8"/>'
        '<path d="M20 39.5H422" stroke="#2e3129" stroke-width=".7"/>'
        + s6_screw(28, 47, 2.5)
        + s6_screw(28, 78, 2.5)
        + s6_screw(414, 47, 2.5)
        + guide_bracket
        + '<rect x="8" y="30" width="864" height="9" fill="url(#s6-topShadow)"/>'
        '<rect x="434" y="31" width="438" height="65" fill="#0d0e0c"/>'
        '<path d="M435 30V97" stroke="#3c3e37" stroke-width="2.5"/>'
        '<path d="M436.5 30V97" stroke="#050605" stroke-width="1"/>'
        '<rect x="430" y="46" width="12" height="20" rx="1.5" fill="url(#s6-bezel)" stroke="#686a60" stroke-width=".8"/>'
        '<rect x="433" y="49" width="7" height="14" fill="#050605"/>'
        '<rect x="448" y="39" width="66" height="50" rx="3" fill="#141512" stroke="#34362f" stroke-width="1"/>'
        '<path d="M450 40.5H512" stroke="#4d5047" stroke-width=".7"/>'
        '<rect x="477" y="62" width="376" height="4" fill="url(#s6-shaft)"/>'
        '<rect x="518" y="54" width="10" height="20" rx="1.5" fill="url(#s6-bezel)" stroke="#686a60" stroke-width=".8"/>'
        '<circle cx="523" cy="58" r="1.4" fill="#8b8d83"/><circle cx="523" cy="70" r="1.4" fill="#8b8d83"/>'
        '<rect x="847" y="56" width="8" height="16" rx="1.5" fill="url(#s6-bezel)" stroke="#686a60" stroke-width=".8"/>'
        '<circle cx="851" cy="64" r="1.6" fill="#9a9c92"/>'
        '<path d="M16 97H864" stroke="#34362f" stroke-width="1"/>'
    )

    tape_static_body = (
        '<path d="M97 23V43Q97 61 118 61H122V51H118Q107 51 107 43V23Z" fill="url(#s6-tapeV)"/>'
        '<path d="M97.5 23V43Q97.5 60.5 118 60.5" fill="none" stroke="#875631" stroke-width=".8" opacity=".8"/>'
        '<path d="M106.5 23V43Q106.5 51.5 118 51.5" fill="none" stroke="#875631" stroke-width=".7" opacity=".7"/>'
        '<rect x="118" y="51" width="361" height="10" fill="url(#s6-tapeH)"/>'
        '<path d="M118 51.5H479M118 60.5H479" stroke="#875631" stroke-width=".7" opacity=".75"/>'
        '<path d="M477 51A20 20 0 0 1 497 71V88H488V71A11 11 0 0 0 477 60Z" fill="#351d0e" stroke="#7c4e2c" stroke-width=".65"/>'
        '<rect x="485" y="85" width="16" height="4" fill="#090a08"/>'
    )

    def tension_assembly(animated):
        flex = s6_spline_anim("rotate", [(0, 0), (1.35, 0), (1.75, 1.4), (4.5, 1.4), (4.95, 0), (12, 0)]) if animated else ""
        return (
            f'<g transform="translate(260 39)"><g>{flex}'
            '<path d="M0 0L28 4" stroke="#686a60" stroke-width="3.2" stroke-linecap="round"/>'
            '<path d="M0 0L28 4" stroke="#bfc1b6" stroke-width=".9" stroke-linecap="round"/>'
            '<circle r="3.4" fill="#77796f" stroke="#22241f" stroke-width=".8"/>'
            + s6_roller(28, 4, 8, -1, animated)
            + '</g></g>'
        )

    def moving_mech(animated):
        return (
            f'<g clip-path="url(#s6-tapeVClip)">{s6_vert_marks(97, 10, 23, 49, 80, animated)}</g>'
            f'<g clip-path="url(#s6-tapeHClip)">{s6_tape_marks(118, 479, 51, 10, 160, animated)}</g>'
            + s6_roller(117.5, 42, 9, -1, animated)
            + tension_assembly(animated)
            + s6_roller(404, 69.5, 8.5, 1, animated)
            + s6_sprocket(477, 64, 15.5, 12.2, 12, animated)
            + '<circle cx="497" cy="73" r="4.2" fill="url(#s6-alu)" stroke="#4d4a42" stroke-width=".7"/>'
            + '<circle cx="497" cy="73" r="1.4" fill="#3a372f"/>'
            + '<rect x="477" y="62" width="54" height="4" fill="url(#s6-shaft)"/>'
            + '<circle cx="477" cy="64" r="4.2" fill="#d8d6ce" stroke="#47433c" stroke-width=".8"/>'
            + '<path d="M474.6 64H479.4" stroke="#35322b" stroke-width="1"/>'
            + '<rect x="518" y="54" width="10" height="20" rx="1.5" fill="url(#s6-bezel)" stroke="#686a60" stroke-width=".8"/>'
            + '<circle cx="523" cy="58" r="1.4" fill="#8b8d83"/><circle cx="523" cy="70" r="1.4" fill="#8b8d83"/>'
        )

    window_glass = '<path d="M449 40H513V53Q481 62 449 53Z" fill="#fff" opacity=".06"/>'

    flaps_still, flaps_replay = [], []
    for i, ch in enumerate(FLAP_WORD):
        fx = 536 + i * 39
        base, overlay = s6_flap(fx, 44, ch, round(2.95 + 0.16 * i, 3), i)
        flaps_still.append(base)
        flaps_replay.append(overlay)
    flap_faces = f'font-family="{s.COND}" font-weight="700" font-size="34" fill="#fff2cf" text-anchor="middle"'

    desk_copy = (
        s.t(
            28,
            127,
            "Said straight: when a machine makes a decision that can't be undone,",
            "#fff2cf",
            22.5,
            s.COND,
            500,
            extra='letter-spacing=".25"',
        )
        + s.t(
            28,
            156,
            'what evidence is left for a person to check it against? <tspan fill="#ffcd52" font-weight="700">That\'s the work.</tspan>',
            "#fff2cf",
            22.5,
            s.COND,
            500,
            extra='letter-spacing=".25"',
        )
    )

    desktop = (
        '<g class="s6-desk">'
        + lower_housing
        + walnut_apron
        + slot_plate
        + tape_static_body
        + f'<g class="replay">{moving_mech(True)}</g>'
        + f'<g class="still">{moving_mech(False)}</g>'
        + window_glass
        + '<rect x="83" y="17" width="40" height="5" fill="#120b06"/>'
        + f'<g {flap_faces}>{"".join(flaps_still)}</g>'
        + f'<g class="replay" {flap_faces}>{"".join(flaps_replay)}</g>'
        + desk_copy
        + '</g>'
    )

    p_flaps_still, p_flaps_replay = [], []
    for i, ch in enumerate(FLAP_WORD):
        px = 556 + i * 37
        base, overlay = s6_phone_flap(px, 23, ch, round(2.95 + 0.16 * i, 3), i)
        p_flaps_still.append(base)
        p_flaps_replay.append(overlay)
    p_flap_faces = f'font-family="{s.COND}" font-weight="700" font-size="27" fill="#fff2cf" text-anchor="middle"'

    def phone_moving(animated):
        return (
            f'<g clip-path="url(#s6-phoneTapeClip)">{s6_tape_marks(115, 541, 34, 11, 160, animated)}</g>'
            + s6_roller(115.5, 26.5, 7.5, -1, animated)
            + s6_roller(330, 26.5, 7.5, -1, animated)
        )

    phone = (
        '<g class="s6-phone">'
        f'<rect y="20" width="880" height="{H - 20}" fill="url(#s6-metal)"/>'
        f'<path d="M1 20V{H}M879 20V{H}" stroke="#77786e"/>'
        f'<rect x="8" y="20" width="864" height="{H - 19}" fill="url(#s6-boardBot)" stroke="#050605" stroke-width="2"/>'
        '<rect width="880" height="21" fill="url(#s6-wood)"/>'
        '<path d="M0 20.5H880" stroke="#241308" stroke-width="2"/>'
        '<rect x="78" y="7" width="54" height="14" rx="2" fill="url(#s6-alu)" stroke="#4c3928"/>'
        '<rect x="91" y="13" width="28" height="8" fill="#0b0603"/>'
        '<path d="M97 15V29Q97 45 115 45H118V34H115Q108 34 108 29V15Z" fill="url(#s6-tapeV)"/>'
        '<rect x="115" y="34" width="426" height="11" fill="url(#s6-tapeH)"/>'
        '<path d="M115 34.5H541M115 44.5H541" stroke="#875631" stroke-width=".7" opacity=".75"/>'
        + f'<g class="replay">{phone_moving(True)}</g>'
        + f'<g class="still">{phone_moving(False)}</g>'
        + '<rect x="538" y="27" width="11" height="24" rx="1.5" fill="url(#s6-bezel)" stroke="#686a60"/>'
        + f'<g {p_flap_faces}>{"".join(p_flaps_still)}</g>'
        + f'<g class="replay" {p_flap_faces}>{"".join(p_flaps_replay)}</g>'
        + '<path d="M16 60H864" stroke="#34362f" stroke-width="1"/>'
        + s.t(28, 91, "Said straight: when a machine makes a decision", "#fff2cf", 32, s.COND, 500)
        + s.t(28, 126, "that can't be undone, what evidence is left for a", "#fff2cf", 32, s.COND, 500)
        + s.t(28, 161, 'person to check it against? <tspan fill="#ffcd52" font-weight="700">That\'s the work.</tspan>', "#fff2cf", 32, s.COND, 500)
        + '</g>'
    )

    edges = (
        f'<path d="M-4 0H{W + 4}" stroke="{TOP_EDGE}" stroke-width="2" vector-effect="non-scaling-stroke" shape-rendering="crispEdges"/>'
        f'<path d="M-4 {H}H{W + 4}" stroke="{BOT_EDGE}" stroke-width="2" vector-effect="non-scaling-stroke" shape-rendering="crispEdges"/>'
    )

    label = (
        "Tape to board. Magnetic tape runs out of a slot in the walnut chassis, across, "
        "and threads into the back of a black station board, driving a row of flaps spelling EVIDENCE. "
        "Said straight: when a machine makes a decision that can't be undone, "
        "what evidence is left for a person to check it against? That's the work."
    )
    return s.svg(W, H, escape(label, {'"': "&quot;"}), s.BARLOW[1:], style + defs + desktop + phone + edges)
