#!/usr/bin/env python3
"""IP sanitiser for the UNREAL port only (owner rule: we copy nothing).

The browser game's Times Square ad atlas (public/assets/city/tex/ts_ads.webp, 4096x4096) and storefront sign atlas
(ts_signs.webp, 2048x2048) contain cells that show Marvel-universe / real-game brand names. The browser atlas files are
never modified. When prep_textures.py converts the atlases for Unreal it calls sanitize() here, which overwrites every
excluded cell with the pixels of another, original-brand cell of the same orientation (a UV-slot remap, done on the
Unreal-side copy). The table below is the single source of truth; docs/night1/city/IP_EXCLUSIONS.md lists it in prose.

Cell layout (from src/world/timessq.js):
  ts_ads.webp     top half: 64 landscape cells 512x256 (8 x 8, index = row * 8 + col);
                  bottom half: 64 portrait cells 256x512 (16 x 4, index = row * 16 + col, y offset 2048)
  ts_signs.webp   64 signs 512x128 (4 cols x 16 rows, index = row * 4 + col)
  signs.png       (island r03) facade shop-fascia atlas 1024x2048: 16 one-row signs 1024x128 (src/world/facade.js tSigns: row = floor(h * 16),
                  the whole row is one fascia; the billboard path samples a quarter of it)
"""
import os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# (kind, excluded cell, donor cell, why)
ADS = [
    ('L', 0, 55, 'OSCORP - Tomorrow, Engineered (Marvel-universe company)'),
    ('L', 1, 63, 'RE-ELECT OSBORN - Safe Streets, Strong City (Marvel-universe politician)'),
    ('L', 2, 52, 'THE DAILY BUGLE - cafe / newspaper (Marvel-universe newspaper)'),
    ('L', 3, 53, 'ROXXON - Powering New York (Marvel-universe company)'),
    ('L', 22, 45, 'EMPIRE STATE UNIVERSITY - Enroll for Fall (Marvel-universe university)'),
    ('L', 26, 43, 'FROSTED HALOS - Part of a Heavenly Breakfast (brand from the real game)'),
    ('L', 33, 46, 'BOTANICA - Now Playing, Majestic Theatre (show ad from the real game)'),
    ('L', 34, 20, 'FROSTED HALOS - Start Bright (brand from the real game)'),
    ('L', 39, 'art', "HELL'S KITCHEN BLUES (Marvel-universe / Netflix-Marvel reference); r05 donor L41 was 'NEON RACERS - OUT NOW' game key art (round-06 critic) -> original NIGHT LANTERN MARKET"),
    ('L', 41, 'art', "NEON RACERS - OUT NOW (racing-franchise key art; round-06 critic) -> original HARBOR POOL"),
    ('L', 23, 'art', "SEE SOMETHING? SAY SOMETHING. + call number (the real transit-authority slogan; round-06 critic, S6) -> original RIVERSIDE GARDEN WEEKEND"),
    ('L', 61, 'art', "STAR RAIDERS 3 - OUT NOW (game key art, same 'OUT NOW' pattern as L39 / L41) -> original LATE NIGHT BAKERY"),
    ('P', 8, 'art', "KINETIX - RISE ABOVE: basketball-shoe photo, the S3 wall mural (round-06 critic: 'looks like real product photography') -> original GOOD MORNING, CITY mural"),
    ('P', 27, 'art', "COLTEX - Own the Court (portrait cell excluded since round 04); its donor P8 was the Kinetix shoe photo -> original PLANT A TREE poster"),
    ('L', 60, 16, "THE DAILY BUGLE - New York's News (Marvel-universe newspaper)"),
    ('L', 27, 4, 'COLTEX SPORT (sneaker brand too close to a real-game brand; round-04 critic)'),
    ('P', 38, 15, 'COLEXCO - Run the City (near-copy of the real game\'s COLEXCO brand)'),
    ('L', 35, 47, 'COLEXCO SPORT (red-on-white sneaker ad; it is the "COLEX SPOR..." banner seen in S6; real-game brand)'),
    ('L', 32, 7, 'HAUTE UNLIMITED - New York / Paris / Milan (fictional brand of the real game; round-05 critic)'),
    ('L', 59, 29, 'NEW YORK KNIGHTS - Tickets on sale (blue / orange basketball ad, evokes a real NBA club; conservative)'),
    ('P', 24, 10, 'HAUTE UNLIMITED (portrait cell, blue gown)'),
    ('P', 32, 44, 'HAUTE UNLIMITED (portrait cell, dark gown); OCR read "TAUTE UNLIMITED"'),
    ('P', 23, 3, 'LIVE AT MADISON ARENA - One night only (evokes Madison Square Garden)'),
    ('P', 63, 5, 'NOVA LEE - MADISON ARENA - LIVE (evokes Madison Square Garden)'),
    ('P', 6, 20, 'OSCORP - A Healthier Tomorrow (Marvel-universe company)'),
    ('P', 7, 22, 'DAILY BUGLE - Read All About It (Marvel-universe newspaper)'),
    ('P', 13, 31, 'ROXXON - Fueling Tomorrow (Marvel-universe company)'),
    ('P', 39, 49, 'FROSTED HALOS (brand from the real game)'),
    ('P', 41, 18, 'HYDRA PRO (Marvel-universe organisation name)'),
]
SIGNS = [
    (48, 51, 'HOTEL MIRA (brand from the real game); replaced by BAKERY'),
    (15, 53, 'HOTEL ASTORIA (evokes the real Hotel Astor / Waldorf Astoria; round-05 critic)'),
    (41, 55, 'BOREAL OUTDOOR (critic read "...REAL OUTDOOR": evokes L\'Oreal / an outdoor brand)'),
]

# (island r03) signs.png rows (row, replacement text, text colour, why): the row is repainted from its own left-edge vertical profile (keeps the
# board colour, bevel and border, removes the lettering) and new original lettering is drawn on it (system font, supersampled)
SIGN_ROWS = [
    (4, 'HARBOR SAVINGS', (250, 250, 255), "CHASE BANK (a real bank's name; round-02 critic, r2 t=25.0 s)"),
    (2, 'CORNER PHARMACY', (180, 20, 40), 'DUANE PHARMACY (evokes the real Duane Reade chain; conservative)'),
    (8, 'HERO SUBS', (250, 220, 0), "SUBWAY EATS (a real sandwich chain's name in its yellow-on-green colours; conservative)"),
]

def _sign_row(im, row, text, colour):
    from PIL import ImageDraw, ImageFont
    W, H, SS = im.size[0], 128, 3
    cell = im.crop((0, row * H, W, row * H + H))
    prof = [cell.getpixel((8, y)) for y in range(H)]
    out = Image.new('RGB', (W, H))
    for y in range(H):
        for x in range(W): out.putpixel((x, y), prof[y])
    for x in range(W):   # keep the left / right border columns as they were (bevel)
        if x < 12 or x >= W - 12:
            for y in range(H): out.putpixel((x, y), cell.getpixel((x, y)))
    big = out.resize((W * SS, H * SS), Image.BICUBIC); d = ImageDraw.Draw(big)
    size = int(H * SS * 0.62)
    while size > 10:
        f = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Black.ttf', size)
        b = d.textbbox((0, 0), text, font=f)
        if b[2] - b[0] <= W * SS * 0.86: break
        size -= 6
    d.text((W * SS / 2 + 4 * SS, H * SS / 2 + 4 * SS), text, font=f, fill=(0, 0, 0), anchor='mm')
    d.text((W * SS / 2, H * SS / 2), text, font=f, fill=colour, anchor='mm')
    return big.resize((W, H), Image.LANCZOS)

def _box(kind, i):
    if kind == 'L': return ((i % 8) * 512, (i // 8) * 256, (i % 8) * 512 + 512, (i // 8) * 256 + 256)
    if kind == 'P': return ((i % 16) * 256, 2048 + (i // 16) * 512, (i % 16) * 256 + 256, 2048 + (i // 16) * 512 + 512)
    if kind == 'S': return ((i % 4) * 512, (i // 4) * 128, (i % 4) * 512 + 512, (i // 4) * 128 + 128)

def sanitize(basename, im):
    """basename: file name stem (ts_ads / ts_signs / ...). Returns a sanitised copy (or im itself when nothing applies)."""
    stem = basename.split('.')[0].replace('assets_city_tex_', '')
    if stem == 'ts_ads':
        out = im.copy()
        for kind, ex, do, _ in ADS:
            if do == 'art':
                from ip_original_art import render  # original art drawn by tools/export/ip_original_art.py (no copied pixels)
                out.paste(render(kind, ex), _box(kind, ex)[:2])
            else: out.paste(im.crop(_box(kind, do)), _box(kind, ex)[:2])
        return out
    if stem == 'ts_signs':
        out = im.copy()
        for ex, do, _ in SIGNS: out.paste(im.crop(_box('S', do)), _box('S', ex)[:2])
        return out
    if stem == 'signs':   # (island r03) facade fascia atlas
        out = im.convert('RGB').copy()
        for row, text, colour, _ in SIGN_ROWS: out.paste(_sign_row(out, row, text, colour), (0, row * 128))
        return out
    return im

if __name__ == '__main__':
    import os, sys
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '../../public/assets/city/tex')
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.environ.get('SM2_CITY_SCRATCH', '/Users/midir/sm2-n1/_scratch/city'), 'r04', 'atlas')
    os.makedirs(dst, exist_ok=True)
    for f in ('ts_ads.webp', 'ts_signs.webp', 'signs.png'):
        im = Image.open(os.path.join(src, f)).convert('RGB'); s = sanitize(f, im)
        s.thumbnail((2000, 2000)); s.save(os.path.join(dst, f.split('.')[0] + '_clean.jpg'), quality=88); print(f, 'sanitised ->', dst)
