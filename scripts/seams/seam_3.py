"""Seam 3: Water into ink (Spillway cyanotype blueprint -> Certified Blind journal paper)."""


def _s3_anim(attr, frames, dur, mode="spline", spline="0.4 0 0.2 1"):
    frames = sorted(frames, key=lambda f: f[0])
    if frames[0][0] > 0:
        frames.insert(0, (0, frames[0][1]))
    if frames[-1][0] < dur:
        frames.append((dur, frames[-1][1]))
    kt = ";".join(f"{t / dur:.4f}" for t, _ in frames)
    vs = ";".join(str(v) for _, v in frames)
    n = len(frames)
    if mode == "discrete":
        cm = 'calcMode="discrete"'
    elif mode == "linear":
        cm = 'calcMode="linear"'
    else:
        splines = ";".join([spline] * (n - 1))
        cm = f'calcMode="spline" keySplines="{splines}"'
    return f'<animate attributeName="{attr}" dur="{dur}s" repeatCount="indefinite" keyTimes="{kt}" values="{vs}" {cm}/>'


def _s3_move(frames, dur, kind="translate", spline="0.4 0 0.2 1"):
    frames = sorted(frames, key=lambda f: f[0])
    if frames[0][0] > 0:
        frames.insert(0, (0, frames[0][1], frames[0][2]))
    if frames[-1][0] < dur:
        frames.append((dur, frames[-1][1], frames[-1][2]))
    kt = ";".join(f"{t / dur:.4f}" for t, _, _ in frames)
    vs = ";".join(f"{x} {y}" for _, x, y in frames)
    splines = ";".join([spline] * (len(frames) - 1))
    return (
        f'<animateTransform attributeName="transform" type="{kind}" dur="{dur}s" '
        f'repeatCount="indefinite" keyTimes="{kt}" values="{vs}" '
        f'calcMode="spline" keySplines="{splines}"/>'
    )


def _s3_hero_drop(x, rim_y, land_y, t0, dur, dot_r=3.8, dried_halo=0.0, scale=1.0):
    t_clear0, t_clear1 = 1.82, 2.18
    t_fall0 = round(t0 + 0.42, 3)
    t_swell_end = round(t_fall0 + 0.08, 3)
    fall_dur = round(0.36 + (land_y - rim_y) * 0.0024, 3)
    t_land = round(t_fall0 + fall_dur, 3)
    t_bloom1 = round(t_land + 0.22, 3)
    t_settle = round(t_land + 0.96, 3)

    bead_op = _s3_anim(
        "opacity",
        [(0, 0), (t0, 0), (round(t0 + 0.14, 3), 0.94), (t_fall0, 0.98), (t_swell_end, 0), (dur, 0)],
        dur,
        mode="linear",
    )
    bead_sc = _s3_move(
        [(0, 0.2, 0.2), (t0, 0.2, 0.2), (t_fall0, 1.06 * scale, 1.24 * scale), (t_swell_end, 0.35, 0.35), (dur, 0.2, 0.2)],
        dur,
        kind="scale",
        spline="0.3 0 0.25 1",
    )
    bead = (
        f'<g transform="translate({x} {rim_y})">'
        f'<g opacity="0">{bead_op}<g>{bead_sc}'
        '<path d="M-7.2 -2.2C-4.4 -1.4 -3.4 2.4 -2.8 5.2C-2.2 7.2 -1.2 8.2 0 8.2C1.2 8.2 2.2 7.2 2.8 5.2C3.4 2.4 4.4 -1.4 7.2 -2.2Z" fill="#2b8fd6"/>'
        '<path d="M-1.9 2.0C-1.7 4.0 -0.9 5.5 -0.1 5.9" fill="none" stroke="#8fd3ff" stroke-width="1.1" stroke-linecap="round"/>'
        "</g></g></g>"
    )

    drop_op = _s3_anim(
        "opacity",
        [(0, 0), (t_fall0, 0), (round(t_fall0 + 0.03, 3), 0.98), (round(t_land - 0.02, 3), 0.98), (round(t_land + 0.02, 3), 0), (dur, 0)],
        dur,
        mode="linear",
    )
    drop_tr = _s3_move(
        [(0, x, rim_y + 4), (t_fall0, x, rim_y + 4), (t_land, x, land_y), (round(t_land + 0.04, 3), x, land_y), (dur, x, rim_y + 4)],
        dur,
        kind="translate",
        spline="0.55 0 0.92 0.78",
    )
    drop_fill = _s3_anim(
        "fill",
        [(0, "#2b8fd6"), (t_fall0, "#2b8fd6"), (t_land, "#1f77b4"), (dur, "#2b8fd6")],
        dur,
        mode="linear",
    )
    tip = round(-8.4 * scale, 1)
    c1x = round(1.5 * scale, 1)
    c1y = round(-3.5 * scale, 1)
    rw = round(3.8 * scale, 1)
    rb = round(4.2 * scale, 1)
    ym = round(1.8 * scale, 1)
    drop_d = f"M0 {tip}C{c1x} {c1y} {rw} {round(-0.6 * scale, 1)} {rw} {ym}A{rw} {rb} 0 1 1 {-rw} {ym}C{-rw} {round(-0.6 * scale, 1)} {-c1x} {c1y} 0 {tip}Z"
    falling = (
        f'<g opacity="0">{drop_op}<g transform="translate({x} {rim_y + 4})">{drop_tr}'
        f'<path d="{drop_d}" fill="#2b8fd6">{drop_fill}</path>'
        f'<path d="M{round(-1.3 * scale, 1)} {round(0.3 * scale, 1)}C{round(-1.5 * scale, 1)} {round(2.1 * scale, 1)} {round(-0.8 * scale, 1)} {round(3.4 * scale, 1)} 0 {round(3.8 * scale, 1)}" '
        f'fill="none" stroke="#8fd3ff" stroke-width="{round(1.0 * scale, 1)}" stroke-linecap="round" opacity=".82"/>'
        "</g></g>"
    )

    halo_r_max = round(dot_r * 3.3, 1)
    halo_r_end = round(dot_r * 2.15, 1)
    halo_r_anim = _s3_anim(
        "r",
        [(0, halo_r_end), (t_clear1, halo_r_end), (t_land, round(dot_r * 0.55, 1)), (t_bloom1, halo_r_max), (t_settle, halo_r_end), (dur, halo_r_end)],
        dur,
    )
    halo_op_anim = _s3_anim(
        "opacity",
        [(0, dried_halo), (t_clear0, dried_halo), (t_clear1, 0), (t_land, 0), (round(t_land + 0.06, 3), 0.28), (t_bloom1, 0.21), (t_settle, dried_halo), (dur, dried_halo)],
        dur,
        mode="linear",
    )
    puff_r_anim = _s3_anim(
        "r",
        [(0, dot_r), (t_land, round(dot_r * 0.6, 1)), (t_bloom1, round(dot_r * 1.95, 1)), (t_settle, dot_r), (dur, dot_r)],
        dur,
    )
    puff_op_anim = _s3_anim(
        "opacity",
        [(0, 0), (t_land, 0), (round(t_land + 0.05, 3), 0.42), (t_bloom1, 0.22), (round(t_land + 0.60, 3), 0), (dur, 0)],
        dur,
        mode="linear",
    )
    ring_r_anim = _s3_anim(
        "r",
        [(0, halo_r_end), (t_land, round(dot_r * 0.75, 1)), (t_settle, round(dot_r * 3.5, 1)), (dur, round(dot_r * 3.5, 1))],
        dur,
    )
    ring_op_anim = _s3_anim(
        "opacity",
        [(0, 0), (t_land, 0), (round(t_land + 0.05, 3), 0.44), (t_bloom1, 0.24), (t_settle, 0), (dur, 0)],
        dur,
        mode="linear",
    )

    dot_op = _s3_anim(
        "opacity",
        [(0, 1), (t_clear0, 1), (t_clear1, 0), (t_land, 0), (round(t_land + 0.04, 3), 1), (dur, 1)],
        dur,
        mode="linear",
    )
    dot_r_anim = _s3_anim(
        "r",
        [(0, dot_r), (t_clear1, dot_r), (t_land, round(dot_r * 0.42, 1)), (t_bloom1, round(dot_r * 1.18, 1)), (t_settle, dot_r), (dur, dot_r)],
        dur,
    )

    bloom = (
        f'<circle cx="{x}" cy="{land_y}" r="{halo_r_end}" fill="#2b8fd6" opacity="{dried_halo}">{halo_r_anim}{halo_op_anim}</circle>'
        f'<circle cx="{x}" cy="{land_y}" r="{dot_r}" fill="#1f77b4" opacity="0">{puff_r_anim}{puff_op_anim}</circle>'
        f'<circle cx="{x}" cy="{land_y}" r="{halo_r_end}" fill="none" stroke="#2b8fd6" stroke-width="{round(0.95 * scale, 1)}" opacity="0">{ring_r_anim}{ring_op_anim}</circle>'
        f'<circle cx="{x}" cy="{land_y}" r="{dot_r}" fill="#1f77b4" opacity="1">{dot_op}{dot_r_anim}</circle>'
    )
    still_parts = []
    if dried_halo > 0:
        still_parts.append(f'<circle cx="{x}" cy="{land_y}" r="{halo_r_end}" fill="#2b8fd6" opacity="{dried_halo}"/>')
    still_parts.append(f'<circle cx="{x}" cy="{land_y}" r="{dot_r}" fill="#1f77b4"/>')
    return bead + falling + bloom, "".join(still_parts)


def _s3_companion_dot(x, y, dur, t_revive, dot_r=3.8, halo=0.0):
    op_anim = _s3_anim(
        "opacity",
        [(0, 1), (1.88, 1), (2.22, 0.56), (t_revive, 0.56), (round(t_revive + 0.40, 3), 1), (dur, 1)],
        dur,
        mode="linear",
    )
    parts = []
    if halo > 0:
        parts.append(f'<circle cx="{x}" cy="{y}" r="{round(dot_r * 2.05, 1)}" fill="#2b8fd6" opacity="{halo}"/>')
    parts.append(f'<circle cx="{x}" cy="{y}" r="{dot_r}" fill="#1f77b4"/>')
    inner = "".join(parts)
    return f'<g opacity="1">{op_anim}{inner}</g>', inner


def build(s):
    w, h, dur = 880, 150, 12
    ink = "#0d2b4b"
    paper = "#ffffff"
    rule = "#c7cacf"
    text_ink = "#202325"

    css = (
        ".s3-phone,.still{display:none}"
        "@media(prefers-reduced-motion:reduce){.replay{display:none}.still{display:inline}}"
        "@media(max-width:500px){.s3-desk{display:none}.s3-phone{display:inline}}"
    )

    desk_bp_d = (
        "M0 0H880V14.5C836 14.8 784 13.8 730 14.8C684 15.6 648 16.5 620 21"
        "C602 24 594 31.2 581 31.8C569 32.3 561 28.4 550 29.2C534 30.4 525 38.6 508 38.8"
        "C492 39 485 33.8 472 34.4C456 35.2 448 42.4 431 41.6C414 40.8 408 35.6 394 36.4"
        "C382 37.1 376 39.2 365 37.8C351 36 344 30.8 330 33.4C317 35.8 304 33.5 292 27.6"
        "C274 19.2 250 15.8 214 15.2C160 14.2 82 15.4 0 14.5Z"
    )
    desk_fringe_d = (
        "M0 0H880V16.4C836 16.8 784 16 730 17.2C684 18.2 648 20.2 618 25.5"
        "C601 28.6 593 36.2 580 37.2C568 38 560 33.2 549 34.4C533 36 523 44.4 506 44.2"
        "C490 44 483 38.8 470 39.6C454 40.6 446 48 429 46.8C412 45.6 406 40.6 392 41.6"
        "C380 42.4 374 44.4 363 42.8C349 40.8 342 35.4 328 38.4C315 41.2 302 38.2 290 31.8"
        "C272 22.8 248 18.2 212 17.4C158 16.4 82 17.4 0 16.4Z"
    )
    desk_wash_d = (
        "M0 0H880V18.8C834 19.2 782 18.8 728 20.4C682 21.8 646 24.8 616 31.8"
        "C598 36 592 43.2 577 44.4C564 45.4 556 39.8 545 41.4C529 43.8 520 51.6 503 51.2"
        "C486 50.8 480 45.2 467 46.4C451 47.8 443 55.2 425 53.6C408 52 402 46.8 389 48.2"
        "C376 49.6 371 51.4 359 49.4C345 47 338 41.6 324 44.8C310 48 297 44.2 284 37"
        "C266 27.2 244 21 208 19.8C156 18.8 82 19.8 0 18.8Z"
    )
    desk_wick_d = (
        "M0 0H880V21.2C834 21.8 780 21.8 726 23.6C680 25.2 644 29.5 614 38"
        "C596 43 590 50.5 574 51.8C560 53 552 47 541 49C525 52 516 59.5 499 58.6"
        "C482 57.6 476 52.2 463 53.8C447 55.6 439 63 421 61C404 59 398 53.6 385 55.4"
        "C372 57.2 367 59 355 56.6C341 53.8 334 48.4 320 52C306 55.6 292 51 279 42.8"
        "C262 32 240 24 204 22.4C154 21.2 82 22.2 0 21.2Z"
    )

    phone_bp_d = (
        "M0 0H880V15.5C790 15.8 688 15 582 16C504 16.8 460 19.8 424 25.5"
        "C401 29.2 387 35.8 364 36.2C342 36.6 329 31.4 307 34.4C284 37.6 270 40.6 246 38.4"
        "C223 36.2 211 31.2 189 34.8C166 38.6 151 41.2 128 38C106 35 94 30.8 73 33.8"
        "C51 36.8 32 31.8 16 23.8C8 19.8 4 17.5 0 16.5Z"
    )
    phone_fringe_d = (
        "M0 0H880V18C790 18.4 688 17.8 582 19C504 19.8 458 23.8 422 30.4"
        "C399 34.6 385 41.8 362 42.2C340 42.6 327 37.2 305 40.4C282 43.8 268 47 244 44.4"
        "C221 41.8 209 36.8 187 40.8C164 45 149 47.6 126 44C104 40.6 92 36.2 71 39.6"
        "C49 43 30 37.2 14 28.4C6 23.8 3 20.5 0 19Z"
    )
    phone_wick_d = (
        "M0 0H880V21.8C790 22.4 688 22.2 582 23.8C502 25 456 30.2 420 38.4"
        "C396 43.4 382 50.8 359 51.2C337 51.6 324 45.8 302 49.4C279 53.2 265 56.6 241 53.6"
        "C218 50.6 206 45.4 184 49.8C161 54.4 146 57.2 123 53.2C101 49.2 89 44.6 68 48.6"
        "C46 52.6 27 45.8 12 35.8C5 30.8 2 26.5 0 24Z"
    )

    defs = (
        "<defs>"
        '<pattern id="s3-grid" width="16" height="16" patternUnits="userSpaceOnUse" patternTransform="translate(0 2)">'
        '<path d="M16 0H0V16" fill="none" stroke="#507d9e" stroke-opacity=".21" stroke-width=".7"/></pattern>'
        '<pattern id="s3-grid-major" width="80" height="80" patternUnits="userSpaceOnUse" patternTransform="translate(0 2)">'
        '<path d="M80 0H0V80" fill="none" stroke="#507d9e" stroke-opacity=".33" stroke-width=".9"/></pattern>'
        '<linearGradient id="s3-grid-fade" x1="0" y1="0" x2="0" y2="40" gradientUnits="userSpaceOnUse">'
        '<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".04" stop-color="#fff" stop-opacity="1"/>'
        '<stop offset=".45" stop-color="#fff" stop-opacity=".75"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        '<mask id="s3-grid-mask"><rect width="880" height="44" fill="url(#s3-grid-fade)"/></mask>'
        '<linearGradient id="s3-rail-fade" x1="0" y1="0" x2="0" y2="16" gradientUnits="userSpaceOnUse">'
        '<stop offset="0" stop-color="#81a4bc" stop-opacity="1"/>'
        '<stop offset=".68" stop-color="#81a4bc" stop-opacity=".85"/>'
        '<stop offset="1" stop-color="#81a4bc" stop-opacity="0"/></linearGradient>'
        '<linearGradient id="s3-cb-side" x1="0" y1="15" x2="0" y2="42" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{rule}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{rule}" stop-opacity="1"/></linearGradient>'
        '<linearGradient id="s3-wet-wash" x1="0" y1="12" x2="0" y2="56" gradientUnits="userSpaceOnUse">'
        '<stop offset="0" stop-color="#185182" stop-opacity=".78"/>'
        '<stop offset=".52" stop-color="#2b8fd6" stop-opacity=".34"/>'
        '<stop offset="1" stop-color="#b5dcf5" stop-opacity=".08"/></linearGradient>'
        f'<clipPath id="s3-bp-clip"><path d="{desk_bp_d}"/></clipPath>'
        f'<clipPath id="s3-ph-clip"><path d="{phone_bp_d}"/></clipPath>'
        "</defs>"
    )

    wick_move = _s3_move([(0, 0, 0), (1.8, 0, 0), (2.2, 0, -2.5), (3.8, 0, 3.0), (6.2, 0, 1.8), (9.6, 0, 0), (dur, 0, 0)], dur)
    wash_move = _s3_move([(0, 0, 0), (1.8, 0, 0), (2.2, 0, -1.8), (3.7, 0, 2.2), (6.2, 0, 1.2), (9.6, 0, 0), (dur, 0, 0)], dur)
    wick_op = _s3_anim("opacity", [(0, 0.72), (1.8, 0.72), (2.2, 0.44), (3.7, 0.94), (7.0, 0.78), (10.0, 0.72), (dur, 0.72)], dur, mode="linear")

    desk_blotches = (
        '<ellipse cx="436" cy="49" rx="22" ry="9" fill="#9ccceb" opacity=".22"/>'
        '<ellipse cx="512" cy="47" rx="18" ry="8" fill="#9ccceb" opacity=".20"/>'
        '<ellipse cx="366" cy="45" rx="16" ry="7" fill="#9ccceb" opacity=".18"/>'
    )
    desk_glints = (
        '<path d="M322 33.4Q333 35.6 344 33.8M358 37.2Q368 39.4 378 38.2M390 36.2Q400 38.2 411 36.8'
        'M424 41.2Q436 43.4 447 41.6M464 34.4Q474 36.4 484 34.8M500 38.4Q511 40.6 522 38.6'
        'M542 29.4Q552 31.4 562 29.8M573 31.6Q583 33.6 593 31.8" '
        'fill="none" stroke="#8fd3ff" stroke-width="1.05" stroke-linecap="round" opacity=".52"/>'
    )
    desk_bp_top = (
        f'<path d="{desk_bp_d}" fill="{ink}"/>'
        '<g clip-path="url(#s3-bp-clip)" mask="url(#s3-grid-mask)">'
        '<rect width="880" height="44" fill="url(#s3-grid)"/>'
        '<rect width="880" height="44" fill="url(#s3-grid-major)"/></g>'
        '<path d="M11.5 0V16M868.5 0V16" stroke="url(#s3-rail-fade)" stroke-width="1"/>'
    )
    desk_wet_replay = (
        f'<g>{wick_move}<path d="{desk_wick_d}" fill="#d6eaf7" opacity=".72">{wick_op}</path>{desk_blotches}</g>'
        f'<g>{wash_move}<path d="{desk_wash_d}" fill="url(#s3-wet-wash)"/></g>'
        f'<path d="{desk_fringe_d}" fill="#144975" opacity=".86"/>'
        f"{desk_bp_top}"
        f"{desk_glints}"
    )
    desk_wet_still = (
        f'<path d="{desk_wick_d}" fill="#d6eaf7" opacity=".72"/>{desk_blotches}'
        f'<path d="{desk_wash_d}" fill="url(#s3-wet-wash)"/>'
        f'<path d="{desk_fringe_d}" fill="#144975" opacity=".86"/>'
        f"{desk_bp_top}"
        f"{desk_glints}"
    )

    hero_specs = [
        (332, 33, 82, 2.08, 0.14),
        (366, 37, 122, 2.42, 0.0),
        (402, 36, 98, 2.76, 0.11),
        (434, 41, 134, 3.10, 0.0),
        (472, 34, 74, 3.44, 0.15),
        (510, 38, 114, 3.78, 0.0),
        (548, 29, 88, 4.12, 0.13),
        (582, 31, 128, 4.46, 0.0),
    ]
    companion_specs = [
        (318, 108, 2.68, 0.06),
        (348, 64, 3.02, 0.13),
        (388, 136, 3.36, 0.0),
        (422, 80, 3.70, 0.12),
        (458, 104, 4.04, 0.05),
        (488, 136, 4.38, 0.0),
        (530, 74, 4.72, 0.11),
        (564, 112, 5.06, 0.04),
    ]

    desk_replay_drops, desk_still_drops = [], []
    for x, rim_y, land_y, t0, halo in hero_specs:
        r_svg, st_svg = _s3_hero_drop(x, rim_y, land_y, t0, dur, dot_r=3.8, dried_halo=halo, scale=1.0)
        desk_replay_drops.append(r_svg)
        desk_still_drops.append(st_svg)
    for x, y, tr, halo in companion_specs:
        r_svg, st_svg = _s3_companion_dot(x, y, dur, tr, dot_r=3.8, halo=halo)
        desk_replay_drops.append(r_svg)
        desk_still_drops.append(st_svg)

    stray_specks = (
        '<circle cx="298" cy="52" r="1.7" fill="#4c9ed4" opacity=".52"/>'
        '<circle cx="305" cy="63" r="1.2" fill="#1f77b4" opacity=".40"/>'
        '<circle cx="603" cy="54" r="1.6" fill="#4c9ed4" opacity=".48"/>'
        '<circle cx="596" cy="66" r="1.1" fill="#1f77b4" opacity=".38"/>'
    )
    desk_text = (
        s.t(26, 86, "This one has a figure caption,", text_ink, 18, s.SERIF, 400)
        + s.t(26, 111, "so you know it's serious.", text_ink, 18, s.SERIF, 400)
    )

    phone_blotches = (
        '<ellipse cx="140" cy="49" rx="26" ry="9" fill="#9ccceb" opacity=".22"/>'
        '<ellipse cx="256" cy="48" rx="24" ry="8" fill="#9ccceb" opacity=".20"/>'
    )
    phone_glints = (
        '<path d="M62 33.6Q74 36 86 34.2M118 37.6Q131 40.2 144 38.4M178 34.6Q191 37.2 204 35.4'
        'M236 38.0Q249 40.6 262 38.6M296 34.2Q309 36.8 322 35.0M354 35.8Q367 38.2 380 36.2" '
        'fill="none" stroke="#8fd3ff" stroke-width="1.5" stroke-linecap="round" opacity=".55"/>'
    )
    phone_bp_top = (
        f'<path d="{phone_bp_d}" fill="{ink}"/>'
        '<g clip-path="url(#s3-ph-clip)" mask="url(#s3-grid-mask)">'
        '<rect width="880" height="44" fill="url(#s3-grid)"/>'
        '<rect width="880" height="44" fill="url(#s3-grid-major)"/></g>'
        '<path d="M11.5 0V18M868.5 0V16" stroke="url(#s3-rail-fade)" stroke-width="1"/>'
    )
    phone_top_replay = (
        f'<g>{wick_move}<path d="{phone_wick_d}" fill="#d6eaf7" opacity=".76">{wick_op}</path>{phone_blotches}</g>'
        f'<path d="{phone_fringe_d}" fill="#144975" opacity=".84"/>'
        f"{phone_bp_top}"
        f"{phone_glints}"
    )
    phone_top_still = (
        f'<path d="{phone_wick_d}" fill="#d6eaf7" opacity=".76"/>{phone_blotches}'
        f'<path d="{phone_fringe_d}" fill="#144975" opacity=".84"/>'
        f"{phone_bp_top}"
        f"{phone_glints}"
    )
    phone_specs = [
        (74, 34, 108, 2.20, 0.14),
        (134, 38, 82, 2.75, 0.15),
        (194, 35, 126, 3.30, 0.0),
        (254, 38, 94, 3.85, 0.13),
        (314, 34, 128, 4.40, 0.0),
    ]
    phone_replay_drops, phone_still_drops = [], []
    for x, rim_y, land_y, t0, halo in phone_specs:
        r_svg, st_svg = _s3_hero_drop(x, rim_y, land_y, t0, dur, dot_r=6.6, dried_halo=halo, scale=1.5)
        phone_replay_drops.append(r_svg)
        phone_still_drops.append(st_svg)
    for x, y, tr in [(104, 128, 3.0), (164, 102, 3.55), (224, 78, 4.1), (284, 112, 4.65), (356, 96, 5.0)]:
        r_svg, st_svg = _s3_companion_dot(x, y, dur, tr, dot_r=6.6, halo=0.07)
        phone_replay_drops.append(r_svg)
        phone_still_drops.append(st_svg)

    phone_text = (
        s.t(418, 86, "This one has a figure caption,", text_ink, 33, s.SERIF, 400)
        + s.t(418, 126, "so you know it's serious.", text_ink, 33, s.SERIF, 400)
    )

    side_borders = (
        '<path d="M.5 15V42M879.5 15V42" stroke="url(#s3-cb-side)" stroke-width="1"/>'
        f'<path d="M.5 42V{h}M879.5 42V{h}" stroke="{rule}" stroke-width="1"/>'
    )
    edge_caps = (
        f'<path d="M-4 0H{w + 4}" stroke="{ink}" stroke-width="2" vector-effect="non-scaling-stroke" shape-rendering="crispEdges"/>'
        f'<path d="M-4 {h}H{w + 4}" stroke="{paper}" stroke-width="2" vector-effect="non-scaling-stroke" shape-rendering="crispEdges"/>'
    )

    body = (
        f"<style>{css}</style>"
        f"{defs}"
        f'<rect width="{w}" height="{h}" fill="{paper}"/>'
        f"{side_borders}"
        '<g class="s3-desk">'
        f'<g class="replay">{desk_wet_replay}{stray_specks}{"".join(desk_replay_drops)}</g>'
        f'<g class="still">{desk_wet_still}{stray_specks}{"".join(desk_still_drops)}</g>'
        f"{desk_text}"
        "</g>"
        '<g class="s3-phone">'
        f'<g class="replay">{phone_top_replay}{"".join(phone_replay_drops)}</g>'
        f'<g class="still">{phone_top_still}{"".join(phone_still_drops)}</g>'
        f"{phone_text}"
        "</g>"
        f"{edge_caps}"
    )

    aria = (
        "Transition from Spillway blueprint to Certified Blind paper. "
        "The blueprint's lower edge gets wet, water drops fall onto white paper and bloom into matplotlib-blue plot dots. "
        "Narrator: This one has a figure caption, so you know it's serious."
    )
    return s.svg(w, h, aria, s.STIX[:1], body)
