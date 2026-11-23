import math


def seam5_definitions():
    return '''<defs>
<linearGradient id="s5-room" x2="0" y2="1">
 <stop stop-color="#1d1424"/><stop offset=".14" stop-color="#211725"/><stop offset=".40" stop-color="#38262a"/><stop offset=".71" stop-color="#513520"/><stop offset="1" stop-color="#4a2e17"/>
</linearGradient>
<linearGradient id="s5-wood" x1="0" y1="0" x2="1" y2=".08">
 <stop stop-color="#74492a"/><stop offset=".33" stop-color="#5d3a20"/><stop offset=".62" stop-color="#6e4628"/><stop offset="1" stop-color="#4e2f1a"/>
</linearGradient>
<linearGradient id="s5-wood-fade" x2="0" y2="1">
 <stop offset=".06" stop-color="black"/><stop offset=".55" stop-color="#a3a3a3"/><stop offset=".84" stop-color="white"/><stop offset=".96" stop-color="#f3f3f3"/><stop offset="1" stop-color="black"/>
</linearGradient>
<mask id="s5-grain-fade" maskUnits="userSpaceOnUse" x="0" y="0" width="880" height="162">
 <rect width="880" height="162" fill="url(#s5-wood-fade)"/>
</mask>
<linearGradient id="s5-chrome" x1=".15" y1=".04" x2=".86" y2="1">
 <stop stop-color="#a49aae"/><stop offset=".17" stop-color="#f0e8ee"/><stop offset=".30" stop-color="#b0a6b6"/><stop offset=".44" stop-color="#5a5161"/><stop offset=".50" stop-color="#332c39"/><stop offset=".54" stop-color="#e5dcda"/><stop offset=".68" stop-color="#b6acaf"/><stop offset=".83" stop-color="#756978"/><stop offset="1" stop-color="#d2c7be"/>
</linearGradient>
<linearGradient id="s5-pivot" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="40">
 <stop stop-color="#1d1424" stop-opacity="0"/><stop offset=".29" stop-color="#65586b" stop-opacity=".35"/><stop offset=".56" stop-color="#a397a4"/><stop offset="1" stop-color="#6c626f"/>
</linearGradient>
<linearGradient id="s5-metal" x1=".08" y1="0" x2=".90" y2="1">
 <stop stop-color="#9b9995"/><stop offset=".20" stop-color="#eeebe1"/><stop offset=".44" stop-color="#b6b2a9"/><stop offset=".65" stop-color="#e4e0d4"/><stop offset="1" stop-color="#9e978c"/>
</linearGradient>
<clipPath id="s5-insert"><circle r="30.1"/></clipPath>
<clipPath id="s5-aperture"><circle r="25.5"/></clipPath>
<radialGradient id="s5-glass" cx=".29" cy=".25" r=".91">
 <stop stop-color="#736c7d"/><stop offset=".36" stop-color="#393440"/><stop offset=".72" stop-color="#22202d"/><stop offset=".90" stop-color="#392e40"/><stop offset="1" stop-color="#796e83"/>
</radialGradient>
<linearGradient id="s5-paper" x1="0" y1="0" x2=".08" y2="1">
 <stop stop-color="#d8c6a1"/><stop offset=".16" stop-color="#eedfc1"/><stop offset=".53" stop-color="#eee2ca"/><stop offset=".86" stop-color="#e3d3b7"/><stop offset="1" stop-color="#bdab8c"/>
</linearGradient>
<linearGradient id="s5-flip" x1="0" y1="0" x2="1" y2=".3">
 <stop stop-color="#39241a"/><stop offset=".43" stop-color="#815736"/><stop offset=".74" stop-color="#b99165"/><stop offset="1" stop-color="#634027"/>
</linearGradient>
<pattern id="s5-brush" width="41" height="3.4" patternUnits="userSpaceOnUse" patternTransform="rotate(-8)">
 <path d="M0 .4h23m8 0h10M4 2.1h20" fill="none" stroke="#fff" stroke-width=".42" opacity=".55"/>
</pattern>
</defs>'''


def seam5_wood(s):
    coves = []
    for i in range(6):
        y = 78 + i * 2.7
        length = 138 + i * 27
        coves.append(f'M858 {y:.1f}c-{length*.37:.1f} 2 -{length*.52:.1f} {-7-i:.1f} -{length} -3')
    return ('<rect width="880" height="162" fill="url(#s5-room)"/>'
            '<g mask="url(#s5-grain-fade)"><rect width="880" height="162" fill="url(#s5-wood)"/>'
            '<g transform="translate(0 -120)">' + s.undo_grain() + '</g>'
            '<path d="' + ''.join(coves) + '" fill="none" stroke="#372416" stroke-width=".8" opacity=".38"/>'
            '<path d="M.75 0V162M879.25 0V162" stroke="#2b1809" stroke-width="1.5"/></g>')


def seam5_rotor():
    outer, inner = 30.2, 12.3

    def point(r, angle):
        a = math.radians(angle)
        return f'{r * math.cos(a):.2f} {r * math.sin(a):.2f}'

    flange = 'M-36 0a36 36 0 1 0 72 0 36 36 0 1 0-72 0Z'
    for axis in (-76, 44, 164):
        flange += (f'M{point(inner,axis-37)}L{point(outer,axis-48)}'
                   f'A{outer} {outer} 0 0 1 {point(outer,axis+48)}L{point(inner,axis+37)}'
                   f'A{inner} {inner} 0 0 0 {point(inner,axis-37)}Z')
    return (f'<path d="{flange}" fill-rule="evenodd" fill="url(#s5-metal)" stroke="#655f59" stroke-width="1.1"/>'
            f'<path d="{flange}" fill-rule="evenodd" fill="url(#s5-brush)"/>'
            '<circle r="8.1" fill="#403b37" stroke="#e2ddd1" stroke-width="1.2"/>'
            '<path d="M-1.8-5.2h3.6v3.4l2.9 1.7-1.8 3.1L0 1.4l-2.9 1.6-1.8-3.1 2.9-1.7Z" fill="#b5ada2"/>'
            '<circle r="1.4" fill="#615a52"/><path d="M18.6 -26.9l4.2 3.5" stroke="#8a4e32" stroke-width="1.7" stroke-linecap="round"/>')


def seam5_rim():
    cuts = []
    for angle in range(0, 360, 8):
        x, y = math.sin(math.radians(angle)), math.cos(math.radians(angle))
        cuts.append(f'M{x*36:.1f} {y*36:.1f}l{-x*1.7:.1f} {-y*1.7:.1f}')
    return ('<circle r="35.1" fill="none" stroke="#332e37" stroke-width="5"/>'
            '<circle r="33.9" fill="none" stroke="url(#s5-chrome)" stroke-width="6.2"/>'
            '<circle r="35.7" fill="none" stroke="url(#s5-chrome)" stroke-width="1.2"/>'
            '<path class="s5-knurl" fill="none" stroke="#514753" opacity=".8" stroke-width=".85" d="'
            + ''.join(cuts) + '"/><circle r="30.4" fill="none" stroke="#29232c" stroke-width="1.8"/>'
            '<path d="M-16-29.8l4.1-1.8" stroke="#c48a6b" stroke-width="1.7" stroke-linecap="round"/>')


def seam5_pack():
    rings = ''.join(f'<circle r="{r}" fill="none" stroke="{color}" stroke-width=".8"/>' for r, color in
                    [(29.2, '#92694b'), (27.3, '#775033'), (25.4, '#7f593b'), (23.4, '#5b3c29'),
                     (21.1, '#88634a'), (18.9, '#684731'), (16.5, '#836049')])
    return f'<circle r="31.2" fill="#4c3120" stroke="#29211b" stroke-width="1.4"/>{rings}'


def seam5_scene(s):
    release = s.anim('opacity', [(0,1),(2.22,1),(2.52,0),(6.95,0),(8.25,1),(12,1)],12)
    return f'''<path d="M-33 62.5 245 129Q268 135 280 134" fill="none" stroke="#20181b" stroke-width="5.2"/>
<path d="M-32 60.5 247 127Q268 132 280 132" fill="none" stroke="#a99b94" stroke-width="1.4"/>
<path d="M-32 61.3 247 128" fill="none" stroke="#6e6167" stroke-width="1.3"/>
<g class="s5-phone" fill="none" stroke-linecap="round">
 <path d="M258 -2C258 11 243 14 221 15l-66 5q-26 2-52 24" stroke="url(#s5-pivot)" stroke-width="4.4"/>
 <path d="M171 17.9l-18 1.4q-26 2-47 20" stroke="#d5c6cc" stroke-width="1.1" opacity=".6"/>
</g>
<g transform="translate(76 50)">
 <g class="s5-wide"><path d="M-111-30-39-18Q-27-16-24-5L-27 11-49-1-111-12Z" fill="#453c4a" stroke="#201a26" stroke-width="2"/>
 <path d="M-111-30-44-20Q-37-19-35-16L-39-9-111-20Z" fill="url(#s5-chrome)" stroke="#3c343f"/>
 <path d="M-108-27.6-49-18" stroke="#d4c9d0" stroke-width="1.1"/>
 <circle cx="-44" cy="-13" r="4.2" fill="url(#s5-chrome)" stroke="#28222e"/><path d="m-45.5-14.4 3.2 2.7" stroke="#362e3b"/></g>
 <circle cx="-3" cy="2" r="36.7" fill="#312b38" stroke="#8d8091" stroke-width="1.2"/>
 <circle r="31.5" fill="#302b34" stroke="#19161e" stroke-width="2"/>
 <circle r="27.8" fill="url(#s5-chrome)" stroke="#17171e" stroke-width="1.2"/>
 <circle r="25.5" fill="url(#s5-glass)"/>
 <g clip-path="url(#s5-aperture)">
  <path d="m-35-30 65 42v7l-65-42z" fill="#8490a2" opacity=".49"/>
  <path d="m-35-20 65 42v2.8l-65-42z" fill="#b0adba" opacity=".17"/>
 </g>
 <path d="M-18-15Q-10-24 0-24M10 22q7-2 12-10" stroke="#c3b7c8" opacity=".43" fill="none" stroke-width=".9"/>
 <g class="replay">{release}{seam5_rim()}</g><g class="still">{seam5_rim()}</g>
</g>
<g transform="translate(268 96)">
 <ellipse cy="33.7" rx="45" ry="4.1" fill="#281b16" opacity=".49"/>
 <circle cx="1.8" cy="2" r="35.8" fill="#4a4037" stroke="#2e251f" stroke-width="1.3"/>
 {seam5_pack()}
 <circle r="7.2" fill="#aca597" stroke="#403b34" stroke-width="2"/>
</g>'''


def seam5_slack(s, animate):
    loose = ('M265 124C294 129 303 137 326 127C338 122 345 103 356 102L378 112'
             'C355 111 350 125 330 132C303 141 293 133 264 129Z')
    taut = ('M265 124C294 127 307 127 327 121C341 117 348 106 356 102L378 112'
            'C355 111 348 119 330 125C307 132 293 131 264 129Z')
    motion = s.anim('d',[(0,loose),(3.45,loose),(6.35,taut),(8.05,loose),(12,loose)],12) if animate else ''
    return f'<path d="{loose}" fill="url(#s5-flip)" stroke="#422c1e" stroke-width=".8">{motion}</path>'


def seam5_leader(s):
    shape = ('M341 113C357 99 350 62 403 60L856 52L839 120L405 129'
             'C375 130 349 124 341 113Z')
    return (f'<path d="{shape}" fill="#2a1c16" opacity=".52" transform="translate(0 2.4)"/>'
            f'<g transform="translate(98.7) scale(.7105 1)"><g class="replay">{seam5_slack(s,True)}</g><g class="still">{seam5_slack(s,False)}</g></g>'
            f'<path d="{shape}" fill="url(#s5-paper)" stroke="#9b8666" stroke-width=".75"/>'
            '<path d="M343 113Q358 106 367 89Q367 111 381 124Q357 122 343 113Z" fill="#b9a582" opacity=".68"/>'
            '<path d="M407 60.9 853 53M407 128 838 119" stroke="#fff3d9" opacity=".67" fill="none" stroke-width=".9"/>'
            '<path d="M848.2 52.4l-16.5 67.1" stroke="#a26045" opacity=".63" stroke-width="2.1"/>'
            )


def seam5_caption(s):
    first = 'Which raises the question of'
    second = 'who should be checking, and when.'

    def line(x, y, words, size):
        return s.t(x, y, words, '#3e3127', size, s.SERIF, 400, extra='font-style="italic"')

    return ('<g transform="rotate(1.05 70 80)"><g class="s5-wide">'
            + line(68, 81, first, 26) + line(68, 110, second, 26)
            + '</g><g class="s5-phone">' + line(53, 79, first, 30)
            + line(53, 112, second, 30) + '</g></g>')


def seam5_motion(s):
    rolling = s.move([(0,76,50),(2.3,76,50),(6.6,268,96),(12,268,96)],12)
    degree = ('<animateTransform attributeName="transform" type="rotate" dur="12s" repeatCount="indefinite" '
              'keyTimes="0;.1917;.55;1" values="0;0;312;312" calcMode="spline" '
              'keySplines=".4 0 .2 1;.4 0 .2 1;.4 0 .2 1"/>')
    rotor = s.anim('opacity', [(0,0),(3.25,0),(5.95,1),(12,1)],12)
    rim = s.anim('opacity', [(0,1),(4.2,1),(6.55,0),(12,0)],12)
    coat = s.anim('opacity',[(0,0),(3.6,0),(6,1),(12,1)],12)
    veneer = s.anim('opacity',[(0,0),(3.1,0),(3.85,.95),(4.4,.95),(5.45,0),(12,0)],12)
    insert = ('<g clip-path="url(#s5-insert)"><circle r="30.4" fill="url(#s5-wood)"/>'
              '<path d="M-34-17q18 4 35 1t32-1M-34-9q10 2 21 0t27 2 22 1M-33 1q19-8 33 0t34 1'
              'M-32 5q19-7 31-1t34 2M-33 14q17-5 31-2t35 4M-30 22q21-4 40 0" '
              'fill="none" stroke="#371f12" stroke-width="1.15"/><path d="M-33 2q17-8 32-1t32 1M-33-11q15 3 28 0" '
              'fill="none" stroke="#b48358" stroke-width=".85"/></g>')
    moving = s.anim('opacity', [(0,0),(1.85,0),(2.25,1),(7,1),(7.5,0),(12,0)],12)
    seat = s.anim('opacity',[(0,1),(1.45,1),(2.5,0),(6.55,0),(6.93,1),(12,1)],12)
    end = f'<g transform="translate(268 96) rotate(312)">{seam5_rotor()}</g>'
    return (f'<g class="replay"><g>{seat}{end}</g><g opacity="0">{moving}'
            f'<g transform="translate(76 50)">{rolling}<ellipse cx="-7" cy="35.5" rx="12" ry="1.4" fill="#21171b" opacity=".62" transform="rotate(13 -7 35.5)"/><g>{degree}<g opacity="0">{coat}{seam5_pack()}</g>'
            f'<g opacity="0">{veneer}{insert}</g><g opacity="0">{rotor}{seam5_rotor()}</g><g>{rim}{seam5_rim()}</g></g></g></g></g>'
            f'<g class="still">{end}</g>')


def build(s):
    label = 'A chrome lens ring rolls into a tape reel. Which raises the question of who should be checking, and when.'
    style = ('<style>.s5-phone,.still{display:none}@media (max-width:500px){.s5-wide{display:none}.s5-phone{display:inline}.s5-knurl{display:none}}'
             '@media (prefers-reduced-motion:reduce){.replay{display:none}.still{display:inline}}</style>')
    return s.svg(880,162,label,[s.STIX[1]],style + seam5_definitions() + seam5_wood(s)
                 + '<g transform="translate(880) scale(-1 1)"><g transform="translate(22)">'
                 + seam5_scene(s) + '</g>' + seam5_leader(s) + '<g transform="translate(22)">'
                 + seam5_motion(s) + '</g></g>' + seam5_caption(s)
                 + '<path d="M-4 0H884" stroke="#1d1424" stroke-width="4" vector-effect="non-scaling-stroke" shape-rendering="crispEdges"/><path d="M-4 162H884" stroke="#4a2e17" stroke-width="4" vector-effect="non-scaling-stroke" shape-rendering="crispEdges"/>')
