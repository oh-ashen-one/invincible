#!/usr/bin/env python3
"""Original replacement art for excluded ts_ads.webp cells (Unreal port only; nothing here is copied from any game, film, brand or agency).
Every image is drawn from scratch with PIL shapes and system fonts (supersampled 3x, then reduced). Used by ip_sanitize.py; run directly to
write a contact sheet:  ip_original_art.py [out.png]

cell   replaces                                          design
L 23   'SEE SOMETHING? SAY SOMETHING.' (transit slogan)   RIVERSIDE GARDEN WEEKEND - flat hills, sun, flowers
L 39   'NEON RACERS - OUT NOW' (game key art)               NIGHT LANTERN MARKET - strings of paper lanterns over a pier
L 41   'NEON RACERS - OUT NOW' (same art, second cell)     HARBOR POOL - waves and a sun disc
L 61   'STAR RAIDERS 3 - OUT NOW' (game key art)           LATE NIGHT BAKERY - crescent moon, bread, steam
P 8    Kinetix 'RISE ABOVE' sneaker photo                  GOOD MORNING, CITY - painted skyline sunrise mural (no photo, no shoe)
P 27   Kinetix 'RISE ABOVE' sneaker photo (second cell)    PLANT A TREE - leaf pattern poster
"""
import math, random, sys
from PIL import Image, ImageDraw, ImageFont

SS = 3
F = {'impact': ('/System/Library/Fonts/Supplemental/Impact.ttf', 0), 'futura': ('/System/Library/Fonts/Supplemental/Futura.ttc', 2), 'georgia': ('/System/Library/Fonts/Supplemental/Georgia Bold.ttf', 0),
     'gill': ('/System/Library/Fonts/Supplemental/GillSans.ttc', 2), 'didot': ('/System/Library/Fonts/Supplemental/Didot.ttc', 2), 'arial': ('/System/Library/Fonts/Supplemental/Arial Black.ttf', 0),
     'avenir': ('/System/Library/Fonts/Avenir Next.ttc', 8), 'copper': ('/System/Library/Fonts/Supplemental/Copperplate.ttc', 1)}
def font(k, s):
    p, i = F[k]
    try: return ImageFont.truetype(p, int(s), index=i)
    except Exception: return ImageFont.truetype(F['arial'][0], int(s))
def grad(w, h, top, bot):
    im = Image.new('RGB', (w, h)); d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / max(1, h - 1); d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return im
def text_fit(d, s, fk, box, fill, anchor='mm', shadow=None):
    x0, y0, x1, y1 = box; size = (y1 - y0)
    while size > 6:
        f = font(fk, size); b = d.textbbox((0, 0), s, font=f)
        if b[2] - b[0] <= (x1 - x0): break
        size -= 2
    cx = (x0 + x1) / 2; cy = (y0 + y1) / 2
    if shadow: d.text((cx + shadow[0], cy + shadow[1]), s, font=f, fill=shadow[2], anchor=anchor)
    d.text((cx, cy), s, font=f, fill=fill, anchor=anchor)

def hills(d, W, H, y0, cols, rnd, amp):
    for k, c in enumerate(cols):
        ph = rnd.random() * 6; base = y0 + k * H * 0.1
        pts = [(x, base + math.sin(x / W * 5.0 + ph) * amp + math.sin(x / W * 11.0 + ph * 2) * amp * 0.4) for x in range(0, W + 8, 8)]
        d.polygon(pts + [(W, H), (0, H)], fill=c)
def flower(d, x, y, r, petal, centre):
    for a in range(6):
        ang = a * math.pi / 3; d.ellipse([x + math.cos(ang) * r * 0.9 - r * 0.55, y + math.sin(ang) * r * 0.9 - r * 0.55, x + math.cos(ang) * r * 0.9 + r * 0.55, y + math.sin(ang) * r * 0.9 + r * 0.55], fill=petal)
    d.ellipse([x - r * 0.5, y - r * 0.5, x + r * 0.5, y + r * 0.5], fill=centre)
def star(d, x, y, r, fill):
    d.polygon([(x + math.cos(a * math.pi / 4 - math.pi / 2) * (r if a % 2 == 0 else r * 0.38), y + math.sin(a * math.pi / 4 - math.pi / 2) * (r if a % 2 == 0 else r * 0.38)) for a in range(8)], fill=fill)

def art_L23(W, H):  # RIVERSIDE GARDEN WEEKEND
    rnd = random.Random(2301); im = grad(W, H, (120, 196, 232), (238, 244, 226)); d = ImageDraw.Draw(im)
    d.ellipse([W * 0.70, H * 0.08, W * 0.70 + H * 0.34, H * 0.08 + H * 0.34], fill=(255, 226, 120))
    hills(d, W, H, H * 0.55, [(120, 176, 96), (86, 148, 82), (58, 120, 70)], rnd, H * 0.05)
    for i in range(46):
        x = rnd.random() * W; y = H * (0.68 + rnd.random() * 0.3); flower(d, x, y, H * (0.028 + rnd.random() * 0.02), rnd.choice([(255, 120, 150), (255, 250, 240), (255, 196, 70), (190, 130, 230)]), (250, 200, 60))
    d.rounded_rectangle([W * 0.05, H * 0.10, W * 0.66, H * 0.56], radius=H * 0.04, fill=(255, 252, 244))
    text_fit(d, 'RIVERSIDE', 'gill', (W * 0.08, H * 0.13, W * 0.63, H * 0.30), (40, 92, 60))
    text_fit(d, 'GARDEN WEEKEND', 'impact', (W * 0.08, H * 0.30, W * 0.63, H * 0.46), (214, 78, 96))
    text_fit(d, 'PLANT SALE  ·  SATURDAYS IN JUNE', 'futura', (W * 0.08, H * 0.46, W * 0.63, H * 0.54), (90, 90, 84))
    return im
def art_L39(W, H):  # NIGHT LANTERN MARKET
    rnd = random.Random(3901); im = grad(W, H, (16, 20, 52), (60, 44, 86)); d = ImageDraw.Draw(im)
    for i in range(70): x = rnd.random() * W; y = rnd.random() * H * 0.5; d.ellipse([x, y, x + 2, y + 2], fill=(255, 250, 230))
    d.rectangle([0, H * 0.90, W, H], fill=(20, 24, 44)); [d.rectangle([x, H * 0.86, x + 8, H * 0.94], fill=(52, 46, 60)) for x in range(10, W, 46)]
    for row, yy in enumerate([0.10, 0.27, 0.44]):
        pts = [(x, H * yy + math.sin(x / W * math.pi * 2 + row) * H * 0.035) for x in range(0, W + 8, 8)]; d.line(pts, fill=(170, 160, 150), width=2)
        for x in range(30 + row * 23, W, 70):
            y = H * yy + math.sin(x / W * math.pi * 2 + row) * H * 0.035
            c = rnd.choice([(255, 90, 70), (255, 178, 60), (255, 220, 110), (250, 120, 150)]); r = H * 0.05
            d.line([x, y, x, y + r * 0.6], fill=(170, 160, 150), width=2)
            d.ellipse([x - r * 1.25, y + r * 0.5, x + r * 1.25, y + r * 3.1], fill=c); d.rectangle([x - r * 0.5, y + r * 0.3, x + r * 0.5, y + r * 0.7], fill=(60, 40, 40)); d.rectangle([x - r * 0.4, y + r * 2.9, x + r * 0.4, y + r * 3.4], fill=(60, 40, 40))
            d.line([x - r * 0.9, y + r * 1.8, x + r * 0.9, y + r * 1.8], fill=tuple(int(v * 0.7) for v in c), width=2)
    text_fit(d, 'NIGHT LANTERN MARKET', 'copper', (W * 0.1, H * 0.66, W * 0.9, H * 0.80), (255, 226, 160))
    text_fit(d, 'FRIDAYS ON THE PIER  ·  FOOD  ·  MUSIC', 'futura', (W * 0.14, H * 0.80, W * 0.86, H * 0.87), (200, 196, 220))
    return im
def art_L41(W, H):  # HARBOR POOL
    rnd = random.Random(4101); im = grad(W, H, (255, 214, 140), (255, 246, 214)); d = ImageDraw.Draw(im)
    d.ellipse([W * 0.62, H * 0.06, W * 0.62 + H * 0.5, H * 0.06 + H * 0.5], fill=(255, 150, 88))
    for k, c in enumerate([(70, 176, 200), (40, 140, 184), (24, 108, 160), (16, 82, 132)]):
        base = H * (0.56 + k * 0.12); ph = rnd.random() * 6
        d.polygon([(x, base + math.sin(x / W * 12 + ph) * H * 0.035) for x in range(0, W + 6, 6)] + [(W, H), (0, H)], fill=c)
    text_fit(d, 'HARBOR POOL', 'impact', (W * 0.06, H * 0.10, W * 0.66, H * 0.34), (18, 78, 128))
    text_fit(d, 'OPENS JUNE 1  ·  SWIM ALL SUMMER', 'gill', (W * 0.06, H * 0.36, W * 0.66, H * 0.46), (150, 70, 40))
    return im
def art_L61(W, H):  # LATE NIGHT BAKERY
    rnd = random.Random(6101); im = grad(W, H, (22, 30, 70), (54, 60, 110)); d = ImageDraw.Draw(im)
    for i in range(50): x = rnd.random() * W; y = rnd.random() * H * 0.7; star(d, x, y, rnd.choice([2, 3, 4]), (255, 246, 210))
    d.ellipse([W * 0.05, H * 0.08, W * 0.05 + H * 0.5, H * 0.08 + H * 0.5], fill=(255, 238, 170)); d.ellipse([W * 0.05 + H * 0.14, H * 0.04, W * 0.05 + H * 0.64, H * 0.04 + H * 0.5], fill=(30, 38, 86))
    d.rectangle([0, H * 0.88, W, H], fill=(84, 56, 44))
    for i, x in enumerate([0.12, 0.26, 0.40]):  # loaves on the counter
        cx = W * x; cy = H * 0.82; d.ellipse([cx - W * 0.055, cy - H * 0.08, cx + W * 0.055, cy + H * 0.08], fill=(214, 148, 78)); [d.line([cx - W * 0.035 + j * W * 0.035, cy - H * 0.05, cx - W * 0.015 + j * W * 0.035, cy + H * 0.04], fill=(150, 92, 44), width=3) for j in range(3)]
    text_fit(d, 'LATE NIGHT BAKERY', 'georgia', (W * 0.36, H * 0.14, W * 0.97, H * 0.40), (255, 228, 176))
    text_fit(d, 'FRESH BREAD  ·  OPEN TILL 2 AM', 'futura', (W * 0.36, H * 0.44, W * 0.97, H * 0.56), (200, 204, 232))
    return im
def art_P8(W, H):  # GOOD MORNING, CITY (mural)
    rnd = random.Random(801); im = grad(W, H, (255, 196, 120), (255, 120, 108)); d = ImageDraw.Draw(im)
    d.ellipse([W * 0.12, H * 0.16, W * 0.88, H * 0.16 + W * 0.76], fill=(255, 238, 190)); d.ellipse([W * 0.2, H * 0.16 + W * 0.08, W * 0.8, H * 0.16 + W * 0.68], fill=(255, 208, 130))
    layers = [((255, 150, 130), 0.52, 0.34), ((222, 110, 132), 0.60, 0.30), ((170, 84, 128), 0.68, 0.26), ((104, 58, 110), 0.76, 0.22), ((58, 40, 84), 0.86, 0.16)]
    for c, y0, hmax in layers:
        x = 0
        while x < W:
            bw = int(W * (0.08 + rnd.random() * 0.14)); bh = H * (hmax * (0.35 + rnd.random() * 0.65)); d.rectangle([x, H * (y0 + 0.18) - bh, x + bw, H], fill=c)
            for wy in range(int(H * (y0 + 0.18) - bh) + 8, H, 14):
                for wx in range(x + 5, x + bw - 6, 12):
                    if rnd.random() < 0.3 and wy < H * 0.94: d.rectangle([wx, wy, wx + 5, wy + 7], fill=(255, 226, 150))
            x += bw + int(W * 0.01)
    text_fit(d, 'GOOD MORNING', 'impact', (W * 0.08, H * 0.03, W * 0.92, H * 0.12), (255, 250, 236))
    text_fit(d, 'CITY', 'impact', (W * 0.08, H * 0.94, W * 0.92, H * 0.995), (255, 236, 190))
    return im
def art_P27(W, H):  # PLANT A TREE
    rnd = random.Random(2701); im = Image.new('RGB', (W, H), (236, 240, 218)); d = ImageDraw.Draw(im)
    for i in range(34):
        x = rnd.random() * W; y = H * (0.18 + rnd.random() * 0.62); r = W * (0.08 + rnd.random() * 0.12); a = rnd.random() * math.pi
        c = rnd.choice([(74, 150, 84), (110, 176, 90), (44, 116, 76), (166, 200, 96)])
        pts = [(x + math.cos(a) * r * math.cos(t) - math.sin(a) * r * 0.45 * math.sin(t), y + math.sin(a) * r * math.cos(t) + math.cos(a) * r * 0.45 * math.sin(t)) for t in [k * math.pi / 20 for k in range(41)]]
        d.polygon(pts, fill=c); d.line([(x - math.cos(a) * r, y - math.sin(a) * r), (x + math.cos(a) * r, y + math.sin(a) * r)], fill=tuple(int(v * 0.7) for v in c), width=2)
    d.rounded_rectangle([W * 0.06, H * 0.05, W * 0.94, H * 0.24], radius=W * 0.05, fill=(34, 92, 62))
    text_fit(d, 'PLANT', 'impact', (W * 0.1, H * 0.06, W * 0.9, H * 0.15), (250, 246, 226)); text_fit(d, 'A TREE', 'impact', (W * 0.1, H * 0.145, W * 0.9, H * 0.235), (250, 226, 120))
    d.rounded_rectangle([W * 0.06, H * 0.82, W * 0.94, H * 0.95], radius=W * 0.05, fill=(250, 246, 226))
    text_fit(d, 'GREENER BLOCKS START HERE', 'futura', (W * 0.1, H * 0.835, W * 0.9, H * 0.945), (34, 92, 62))
    return im

ART = {('L', 23): art_L23, ('L', 39): art_L39, ('L', 41): art_L41, ('L', 61): art_L61, ('P', 8): art_P8, ('P', 27): art_P27}
def render(kind, idx):
    W, H = (512, 256) if kind == 'L' else (256, 512)
    return ART[(kind, idx)](W * SS, H * SS).resize((W, H), Image.LANCZOS)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/Users/midir/sm2-n1/_scratch/city/r07/orig_art.png'
    sheet = Image.new('RGB', (512 * 4 + 20, 256 * 2 + 256 * 2 + 30), (30, 30, 30)); x = y = 0
    for i, k in enumerate([('L', 23), ('L', 39), ('L', 41), ('L', 61)]): sheet.paste(render(*k), (i * 522, 0))
    for i, k in enumerate([('P', 8), ('P', 27)]): sheet.paste(render(*k), (i * 266, 266))
    sheet.save(out); print(out)
