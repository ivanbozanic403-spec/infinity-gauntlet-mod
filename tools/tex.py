"""Texture generation (32x32, Pillow). Imported by generate_resources.py.

- six animated, faceted Infinity Stones (each with its own gem cut and a signature effect)
- a gold Infinity Gauntlet with six sockets: 64 variants, one per combination of socketed stones
  (the item model picks the right one through the custom_model_data predicate)
- Loki's Scepter with an animated Mind Stone
"""
import math
from PIL import Image, ImageDraw

S = 32
FRAMES = 8

STONE_RGB = {
    'power': (168, 40, 245), 'space': (45, 120, 255), 'reality': (232, 38, 38),
    'soul': (255, 150, 30), 'time': (45, 220, 80), 'mind': (255, 226, 50),
}

# gem silhouettes in a 32x32 grid, drawn around (16,16)
SHAPES = {
    'power':   [(16, 4), (26, 10), (26, 22), (16, 28), (6, 22), (6, 10)],               # hexagon
    'space':   [(16, 3), (23, 13), (21, 24), (16, 29), (11, 24), (9, 13)],              # tall cut diamond
    'reality': [(11, 6), (22, 5), (27, 15), (22, 26), (10, 27), (5, 15)],               # irregular hex
    'soul':    [(10, 6), (22, 6), (27, 16), (16, 28), (5, 16)],                         # kite / pentagon
    'time':    [(12, 4), (20, 4), (27, 11), (27, 21), (20, 28), (12, 28), (5, 21), (5, 11)],  # octagon eye
    'mind':    [(9, 9), (16, 5), (23, 9), (23, 22), (16, 27), (9, 22)],                 # compact hexagon
}


def clamp(v):
    return max(0, min(255, int(v)))


def mul(c, f):
    return (clamp(c[0] * f), clamp(c[1] * f), clamp(c[2] * f))


def mix(a, b, t):
    return tuple(clamp(a[i] + (b[i] - a[i]) * t) for i in range(3))


def in_poly(px, py, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def sector(px, py, cx, cy, poly):
    """Index of the polygon edge whose wedge (from the centre) contains the point."""
    ang = math.atan2(py - cy, px - cx)
    best, bi = 9, 0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        mid = math.atan2((y1 + y2) / 2 - cy, (x1 + x2) / 2 - cx)
        d = abs((ang - mid + math.pi) % (2 * math.pi) - math.pi)
        if d < best:
            best, bi = d, i
    return bi


def centroid(poly):
    return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))


def gem_frame(name, f):
    col = STONE_RGB[name]
    poly = SHAPES[name]
    cx, cy = centroid(poly)
    table = [(cx + (x - cx) * 0.5, cy + (y - cy) * 0.5 - 0.5) for x, y in poly]
    pulse = 0.5 + 0.5 * math.sin(2 * math.pi * f / FRAMES)
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    px = img.load()
    inside = [[in_poly(x + .5, y + .5, poly) for x in range(S)] for y in range(S)]
    light = (-0.55, -0.83)

    # halo first, so the gem draws on top
    for y in range(S):
        for x in range(S):
            if inside[y][x]:
                continue
            d = min((math.hypot(x - ix, y - iy) for iy in range(S) for ix in range(S) if inside[iy][ix]
                     and abs(ix - x) < 5 and abs(iy - y) < 5), default=99)
            if d <= 3.6:
                a = (1 - d / 3.7) ** 2 * (95 + 70 * pulse)
                px[x, y] = col + (clamp(a),)

    for y in range(S):
        for x in range(S):
            if not inside[y][x]:
                continue
            fx, fy = x + .5, y + .5
            i = sector(fx, fy, cx, cy, poly)
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % len(poly)]
            mx, my = (x1 + x2) / 2 - cx, (y1 + y2) / 2 - cy
            ln = math.hypot(mx, my) or 1
            facet = (mx / ln) * light[0] + (my / ln) * light[1]            # -1..1
            if in_poly(fx, fy, table):
                dist = math.hypot(fx - cx, fy - cy) / (math.hypot(x1 - cx, y1 - cy) * 0.5 + 1e-6)
                core = max(0.0, 1 - dist)
                c = mix(mul(col, 1.05), (255, 255, 255), 0.18 + 0.30 * pulse * core + 0.25 * core)
                px[x, y] = c + (255,)
            else:
                c = mul(col, 0.95 + 0.42 * facet)
                px[x, y] = c + (255,)
            # facet seams: boundary between two sectors in the crown ring
            for dx, dy in ((1, 0), (0, 1)):
                nx, ny = x + dx, y + dy
                if nx < S and ny < S and inside[ny][nx] and not in_poly(fx, fy, table):
                    if sector(nx + .5, ny + .5, cx, cy, poly) != i and not in_poly(nx + .5, ny + .5, table):
                        px[x, y] = mul(col, 0.62) + (255,)
            # table edge highlight line
            if in_poly(fx, fy, table) and any(not in_poly(fx + dx, fy + dy, table)
                                              for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = mix(col, (255, 255, 255), 0.55) + (255,)

    # outline
    for y in range(S):
        for x in range(S):
            if inside[y][x] and any(not (0 <= x + dx < S and 0 <= y + dy < S) or not inside[y + dy][x + dx]
                                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = mul(col, 0.30) + (255,)

    decorate(name, img, f, col, cx, cy, pulse)
    # sparkle (fixed top-left glint + moving twinkle)
    for gx, gy in ((cx - 4, cy - 6), (cx - 5, cy - 6), (cx - 4, cy - 5)):
        if 0 <= int(gx) < S and 0 <= int(gy) < S and px[int(gx), int(gy)][3] == 255:
            px[int(gx), int(gy)] = (255, 255, 255, 255)
    tw = [(cx + 4, cy - 3), (cx + 3, cy + 4), (cx - 3, cy + 3), (cx + 1, cy - 4)][(f // 2) % 4]
    if f % 2 == 0:
        tx, ty = int(tw[0]), int(tw[1])
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= tx + dx < S and 0 <= ty + dy < S and px[tx + dx, ty + dy][3] > 0:
                px[tx + dx, ty + dy] = (255, 255, 255, 255) if (dx, dy) == (0, 0) else \
                    mix(px[tx + dx, ty + dy][:3], (255, 255, 255), 0.6) + (255,)
    return img


def put(img, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < S and 0 <= y < S and img.getpixel((x, y))[3] == 255:
        img.putpixel((x, y), tuple(c[:3]) + (255,))


def decorate(name, img, f, col, cx, cy, pulse):
    ph = 2 * math.pi * f / FRAMES
    if name == 'reality':      # liquid red swirl (the Aether)
        for t in range(-7, 8):
            x = cx + t * 0.9
            y = cy + math.sin(t * 0.7 + ph) * 3.0
            put(img, x, y, mix(col, (255, 190, 190), 0.65))
            put(img, x, y + 1, mul(col, 0.55))
    elif name == 'time':       # ticking ring (the Eye of Agamotto)
        for k in range(12):
            a = k * math.pi / 6 + ph / 2
            r = 8.6
            put(img, cx + math.cos(a) * r, cy + math.sin(a) * r, (200, 255, 210) if k % 3 == 0 else mul(col, 0.5))
        a = ph
        for r in range(1, 5):
            put(img, cx + math.cos(a) * r, cy + math.sin(a) * r, (240, 255, 240))
    elif name == 'space':      # twinkling stars inside
        pts = [(cx - 2, cy - 1), (cx + 2, cy + 2), (cx + 1, cy - 4), (cx - 3, cy + 4), (cx + 3, cy - 1)]
        for k, (x, y) in enumerate(pts):
            if (f + k) % 3 != 0:
                put(img, x, y, (230, 245, 255))
    elif name == 'soul':       # rising wisps
        for k in range(3):
            x = cx - 3 + k * 3
            for t in range(6):
                y = cy + 7 - ((t * 2 + f * 2 + k * 3) % 14)
                put(img, x + math.sin(t + k + ph) * 1.2, y, mix(col, (255, 235, 180), 0.6))
    elif name == 'power':      # crackling hex core
        for k in range(6):
            a = k * math.pi / 3 + (0.3 if f % 2 else 0)
            for r in (2, 3):
                put(img, cx + math.cos(a) * r, cy + math.sin(a) * r, (255, 230, 255))
        put(img, cx, cy, (255, 255, 255))
    elif name == 'mind':       # blue energy motes orbiting the yellow core
        for k in range(4):
            a = k * math.pi / 2 + ph
            put(img, cx + math.cos(a) * 3.6, cy + math.sin(a) * 3.6, (110, 200, 255))
        put(img, cx, cy, (255, 255, 235))
        put(img, cx + 1, cy, (255, 255, 235))


def save_strip(path, frames, frametime=3):
    strip = Image.new('RGBA', (S, S * len(frames)), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        strip.paste(fr, (0, i * S))
    strip.save(path)
    return frametime


# ---------------------------------------------------------------- gauntlet
GOLD = [(255, 243, 160), (247, 212, 84), (219, 172, 46), (170, 120, 30), (112, 72, 18), (58, 34, 12)]
ORDER = list(STONE_RGB)  # power, space, reality, soul, time, mind  -> bit index


def plate(d, x0, y0, x1, y1):
    """Gold armour plate: lit top-left, shaded bottom-right, thin dark seam outline."""
    d.rectangle([x0, y0, x1, y1], fill=GOLD[2], outline=GOLD[3])
    d.line([x0 + 1, y0 + 1, x1 - 1, y0 + 1], fill=GOLD[1])
    d.line([x0 + 1, y0 + 1, x0 + 1, y1 - 1], fill=GOLD[1])
    d.point([(x0 + 1, y0 + 1)], fill=GOLD[0])
    d.line([x1 - 1, y0 + 2, x1 - 1, y1 - 1], fill=GOLD[3])
    d.line([x0 + 2, y1 - 1, x1 - 1, y1 - 1], fill=GOLD[3])


# socket gem boxes (x0, y0, size) in 32x32 space
SOCKETS = {
    'power': (9, 15, 3), 'space': (13, 15, 3), 'reality': (17, 15, 3), 'time': (21, 15, 3),
    'soul': (3, 20, 3), 'mind': (14, 20, 5),
}


def draw_socket(img, name, filled, pulse=0.0):
    d = ImageDraw.Draw(img)
    x0, y0, sz = SOCKETS[name]
    x1, y1 = x0 + sz - 1, y0 + sz - 1
    # bezel
    d.rectangle([x0 - 1, y0 - 1, x1 + 1, y1 + 1], fill=GOLD[0] if sz == 5 else GOLD[4], outline=GOLD[4])
    if sz == 5:
        d.rectangle([x0 - 1, y0 - 1, x1 + 1, y1 + 1], outline=GOLD[1])
        d.rectangle([x0, y0, x1, y1], outline=GOLD[5])
        x0, y0, x1, y1 = x0 + 1, y0 + 1, x1 - 1, y1 - 1
    if not filled:
        d.rectangle([x0, y0, x1, y1], fill=GOLD[5])
        d.point([(x0, y0)], fill=GOLD[4])
        return
    col = STONE_RGB[name]
    d.rectangle([x0, y0, x1, y1], fill=mul(col, 0.85))
    d.rectangle([x0, y0, x1, y1], outline=mul(col, 0.62))
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    d.point([(cx, cy)], fill=mix(col, (255, 255, 255), 0.4 + 0.3 * pulse))
    d.point([(x0, y0)], fill=mix(col, (255, 255, 255), 0.75))
    if x1 > x0 + 1:
        d.rectangle([x0, y0, x1, y1], outline=mul(col, 0.7))
        d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=mix(col, (255, 255, 255), 0.18 + 0.2 * pulse))
        d.point([(x0, y0)], fill=(255, 255, 255))


def gauntlet(mask, pulse=0.0):
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # cuff: dark leather with gold bands and rivets
    d.rectangle([10, 26, 25, 30], fill=GOLD[5], outline=GOLD[4])
    d.line([11, 27, 24, 27], fill=GOLD[2])
    d.line([11, 29, 24, 29], fill=GOLD[2])
    for x in (12, 15, 18, 21, 24):
        d.point([(x, 28)], fill=GOLD[0])
    # palm / back of hand
    plate(d, 8, 14, 25, 25)
    d.line([9, 24, 24, 24], fill=GOLD[3])
    # thumb: angled armour with two joints
    d.polygon([(1, 22), (2, 18), (5, 16), (8, 17), (8, 24), (3, 25)], fill=GOLD[2], outline=GOLD[3])
    d.line([2, 19, 4, 17], fill=GOLD[1])
    d.line([2, 23, 7, 22], fill=GOLD[3])
    # fingers (pinky, ring, middle, index), 4px wide, jointed
    for (x0, top) in ((9, 8), (13, 4), (17, 2), (21, 4)):
        x1 = x0 + 3
        plate(d, x0, top, x1, 15)
        d.line([x0 + 1, top + 4, x1 - 1, top + 4], fill=GOLD[3])
        d.line([x0 + 1, top + 8, x1 - 1, top + 8], fill=GOLD[3]) if 15 - top > 10 else None
        for p in ((x0, top), (x1, top)):
            d.point([p], fill=(0, 0, 0, 0))
    # decorative ridge lines on the hand back
    d.line([9, 19, 12, 19], fill=GOLD[3])
    d.line([20, 19, 24, 19], fill=GOLD[3])
    d.point([(9, 24), (24, 24), (19, 20), (9, 20)], fill=GOLD[0])
    for name in SOCKETS:
        draw_socket(img, name, bool(mask & (1 << ORDER.index(name))), pulse)
    return img


def scepter(f):
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pulse = 0.5 + 0.5 * math.sin(2 * math.pi * f / FRAMES)
    # shaft: 3px thick diagonal with decorative bands
    for k in range(0, 21):
        x, y = 2 + k, 29 - k
        band = k % 6 == 5
        for dx, dy, c in ((0, 0, GOLD[1]), (1, 0, GOLD[2]), (0, 1, GOLD[2]), (1, 1, GOLD[3]), (-1, 0, GOLD[3]),
                          (0, -1, GOLD[1]), (2, 0, GOLD[4]), (0, 2, GOLD[4]), (1, -1, GOLD[3])):
            if band:
                c = GOLD[5] if (dx, dy) in ((1, 1), (2, 0), (0, 2)) else GOLD[4]
            if 0 <= x + dx < S and 0 <= y + dy < S:
                img.putpixel((x + dx, y + dy), c + (255,))
    # pommel (spiked)
    d.polygon([(0, 31), (0, 27), (2, 28), (4, 31)], fill=GOLD[3], outline=GOLD[5])
    d.point([(1, 29)], fill=GOLD[0])
    # collar rings
    for (x, y) in ((17, 14), (18, 13)):
        d.rectangle([x - 1, y - 1, x + 2, y + 2], fill=GOLD[1], outline=GOLD[4])
    # blade head: long leaf around the gem
    cx, cy = 22.5, 9.5
    ux, uy = 0.7071, -0.7071
    vx, vy = 0.7071, 0.7071
    local = [(-6, 0), (-3, 4), (2, 4.6), (8, 0), (2, -4.6), (-3, -4)]
    poly = [(cx + u * ux + v * vx, cy + u * uy + v * vy) for u, v in local]
    d.polygon(poly, fill=GOLD[2], outline=GOLD[4])
    inner = [(cx + u * 0.68 * ux + v * 0.58 * vx, cy + u * 0.68 * uy + v * 0.58 * vy) for u, v in local]
    d.polygon(inner, fill=GOLD[5])
    # highlight edge of the blade
    d.line([(poly[1][0], poly[1][1]), (poly[2][0], poly[2][1]), (poly[3][0], poly[3][1])], fill=GOLD[0])
    # Mind Stone with a blue-white energy halo
    for yy in range(S):
        for xx in range(S):
            dd = math.hypot(xx - cx + .5, yy - cy + .5)
            if dd <= 3.3:
                c = mix((255, 205, 35), (255, 255, 235), max(0, 1 - dd / 3.0) * (0.55 + 0.45 * pulse))
                img.putpixel((xx, yy), c + (255,))
            elif dd <= 4.6 and img.getpixel((xx, yy))[3] < 255:
                img.putpixel((xx, yy), (255, 225, 90, clamp(160 * (1 - (dd - 3.3) / 1.3) * (0.5 + 0.5 * pulse))))
    for k in range(3):
        a = k * 2.1 + 2 * math.pi * f / FRAMES
        x, y = cx + math.cos(a) * 4.2, cy + math.sin(a) * 4.2
        if 0 <= int(x) < S and 0 <= int(y) < S:
            img.putpixel((int(round(x)), int(round(y))), (130, 215, 255, 255))
    img.putpixel((int(cx - 1), int(cy - 1)), (255, 255, 255, 255))
    return img
