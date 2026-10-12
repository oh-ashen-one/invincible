#!/usr/bin/env python3
"""Original storefront signage atlas for the Unreal street-level kit (round 05). Everything here is drawn by this script from invented,
generic shop names with system fonts: no copied art, no real-game / Marvel-universe names (see docs/night1/city/IP_EXCLUSIONS.md).

Atlas 4096 x 2048 (RGB, sRGB), v = 0 at the TOP of the image:
  fascia signs : rows 0..7 (y 0..1279), 4 columns, cell 1024 x 160  -> index f = row * 4 + col  (32 cells, full colour boards)
  awning valances: rows y 1280..2047, 4 columns, cell 1024 x 64     -> index v = row * 4 + col  (48 cells; text coverage in R = G = B, the
                   material tints it: light or dark letters on the awning fabric)
usage: gen_street_signs.py [out_png]   (default _scratch/city/tex/street_signs.png; also writes street_signs.json with the names)
"""
import json, os, sys, random
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from citypaths import TEX as _TEX
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(_TEX, 'street_signs.png')
FONTS = {
    'futura': ('/System/Library/Fonts/Supplemental/Futura.ttc', 2), 'georgia': ('/System/Library/Fonts/Supplemental/Georgia Bold.ttf', 0),
    'copper': ('/System/Library/Fonts/Supplemental/Copperplate.ttc', 1), 'didot': ('/System/Library/Fonts/Supplemental/Didot.ttc', 2),
    'gill': ('/System/Library/Fonts/Supplemental/GillSans.ttc', 2), 'avenir': ('/System/Library/Fonts/Avenir Next.ttc', 8),
    'impact': ('/System/Library/Fonts/Supplemental/Impact.ttf', 0), 'baskerville': ('/System/Library/Fonts/Supplemental/Baskerville.ttc', 3),
    'din': ('/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf', 0), 'arial': ('/System/Library/Fonts/Supplemental/Arial Black.ttf', 0),
    'helv': ('/System/Library/Fonts/HelveticaNeue.ttc', 1), 'chancery': ('/System/Library/Fonts/Supplemental/Apple Chancery.ttf', 0),
}
def font(key, size):
    p, i = FONTS[key]
    try: return ImageFont.truetype(p, size, index=i)
    except Exception: return ImageFont.truetype(FONTS['arial'][0], size)

# name, sub line, font, board colour, text colour, accent
FASCIA = [
    ('HALVORSEN & DAUGHTERS', 'BOOKS  ·  EST. 1961', 'georgia', (22, 40, 30), (232, 205, 130), (232, 205, 130)),
    ('SILVER FERN CAFE', 'COFFEE · PASTRY · BREAKFAST', 'futura', (240, 236, 224), (28, 70, 50), (28, 70, 50)),
    ('OSTERIA LUNA', 'CUCINA ITALIANA', 'didot', (110, 22, 30), (245, 232, 205), (245, 232, 205)),
    ('PINE STREET PHARMACY', 'PRESCRIPTIONS · HEALTH', 'avenir', (250, 250, 248), (14, 90, 70), (14, 90, 70)),
    ('GOLDEN LOTUS', 'CHINESE KITCHEN · TAKE OUT', 'copper', (140, 20, 20), (245, 205, 90), (245, 205, 90)),
    ('KESTREL WATCH & CLOCK', 'REPAIRS · JEWELRY', 'baskerville', (18, 24, 44), (222, 196, 140), (222, 196, 140)),
    ('HARBOR HARDWARE', 'TOOLS · PAINT · KEYS CUT', 'impact', (200, 40, 30), (255, 255, 255), (255, 235, 120)),
    ('NORTH CORNER DELI', 'GROCERY · SANDWICHES · 24 HRS', 'din', (30, 100, 60), (255, 255, 255), (255, 220, 90)),
    ('SUNRISE BAGELS', 'FRESH BAKED DAILY', 'gill', (250, 214, 96), (60, 28, 12), (60, 28, 12)),
    ('VELVET & VINE', 'WINE · SPIRITS', 'didot', (36, 18, 40), (226, 190, 120), (226, 190, 120)),
    ('ANTONELLI PIZZA', 'SLICES · PIES · CALZONES', 'arial', (204, 36, 32), (255, 250, 240), (255, 230, 120)),
    ('BLUEBIRD LAUNDRY', 'WASH · DRY · FOLD', 'avenir', (34, 84, 150), (255, 255, 255), (170, 220, 255)),
    ('MERCER OPTICAL', 'EYE EXAMS · FRAMES', 'helv', (245, 245, 242), (20, 30, 60), (20, 30, 60)),
    ('COPPER KETTLE TEA ROOM', 'LOOSE LEAF TEAS', 'georgia', (54, 30, 20), (222, 160, 96), (222, 160, 96)),
    ("ROSA'S FLOWERS", 'FRESH CUT · WEDDINGS', 'chancery', (238, 226, 232), (150, 30, 90), (150, 30, 90)),
    ('IRON GATE FITNESS', 'GYM · YOGA · TRAINING', 'impact', (20, 20, 22), (255, 210, 40), (255, 210, 40)),
    ('LARK & FINCH', 'MEN\'S & WOMEN\'S CLOTHIERS', 'copper', (232, 226, 214), (40, 40, 44), (40, 40, 44)),
    ('HARBOR LIGHT PHOTO', 'PRINTS · FRAMING · PASSPORT', 'futura', (18, 18, 20), (250, 250, 250), (240, 90, 60)),
    ('THE PAPER MILL', 'STATIONERY · PENS · CARDS', 'baskerville', (30, 60, 100), (245, 240, 225), (245, 240, 225)),
    ('DR. AMARA VOSS', 'FAMILY DENTISTRY', 'avenir', (236, 244, 246), (20, 96, 120), (20, 96, 120)),
    ("HALEY'S SHOE REPAIR", 'HEELS · SOLES · KEYS', 'din', (90, 50, 24), (250, 232, 190), (250, 232, 190)),
    ('ORCHARD STREET BAKERY', 'BREAD · CAKES · COOKIES', 'chancery', (250, 236, 214), (140, 70, 30), (140, 70, 30)),
    ('FIRST HARBOR CREDIT UNION', 'MEMBER OWNED', 'georgia', (12, 44, 84), (255, 255, 255), (150, 200, 240)),
    ('LOTUS NAIL & SPA', 'MANICURE · PEDICURE · WAX', 'gill', (250, 232, 236), (170, 40, 100), (170, 40, 100)),
    ('ANCHOR & OAK', 'PUB · KITCHEN · TAPS', 'copper', (24, 44, 34), (236, 214, 160), (236, 214, 160)),
    ('SALT & PEPPER DINER', 'BREAKFAST ALL DAY', 'arial', (216, 60, 44), (255, 255, 255), (255, 236, 150)),
    ('MAPLE LEAF FRUIT MARKET', 'PRODUCE · FLOWERS · JUICE', 'futura', (40, 120, 50), (255, 255, 255), (255, 236, 120)),
    ('QUILL & INK', 'TATTOO · PIERCING', 'impact', (10, 10, 12), (230, 230, 230), (210, 50, 50)),
    ('CORNERSTONE MEDICAL', 'WALK-INS WELCOME', 'helv', (240, 246, 250), (30, 90, 150), (30, 90, 150)),
    ('NEON DRAGON NOODLES', 'RAMEN · DUMPLINGS · TEA', 'impact', (16, 10, 30), (255, 96, 170), (90, 220, 255)),
    ('SAGE HEALTH FOOD', 'ORGANIC · VITAMINS · JUICE BAR', 'avenir', (226, 236, 216), (44, 84, 40), (44, 84, 40)),
]
VALANCE = [  # text, awning tone hint (0 light letters / 1 dark letters)
    'FRESH BAKED DAILY', 'COFFEE & TEA', 'OPEN 7 DAYS', 'GROCERY & DELI', 'PIZZA BY THE SLICE', 'FLOWERS & GIFTS', 'WINE & SPIRITS', 'CAFE',
    'LUNCH SPECIALS', 'NEWS & MAGAZINES', 'BOOKS · MUSIC', 'LAUNDRY SERVICE', 'BARBER SHOP', 'SHOE REPAIR', 'DRY CLEANING', 'HOME COOKING',
    'SANDWICHES', 'BAGELS & LOX', 'ORGANIC MARKET', 'ICE CREAM', 'PHARMACY', 'TAILOR & ALTERATIONS', 'KEYS CUT WHILE YOU WAIT', 'THAI KITCHEN',
    'ESPRESSO BAR', 'FRUIT & VEGETABLES', 'CHEESE & CHARCUTERIE', 'NOODLE HOUSE', 'SPORTS PUB', 'JUICE BAR', 'PHOTO & PRINT', 'TRAVEL AGENCY',
    'DUMPLING HOUSE', 'BRUNCH ALL DAY', 'CRAFT BEER', 'ANTIQUES', 'PET SUPPLIES', 'VITAMINS', 'HARDWARE', 'CHOCOLATE SHOP',
    'SUSHI & ROLLS', 'TAQUERIA', 'BUTCHER', 'SEAFOOD MARKET', 'TEA ROOM', 'YOGURT & SMOOTHIES', 'STATIONERY', 'GALLERY',
]

def fit(draw, text, key, w, h):
    lo, hi = 8, 400
    while lo < hi - 1:
        mid = (lo + hi) // 2; f = font(key, mid); b = draw.textbbox((0, 0), text, font=f)
        if b[2] - b[0] <= w and b[3] - b[1] <= h: lo = mid
        else: hi = mid
    return font(key, lo)

def fascia(cell_w, cell_h, item):
    name, sub, fk, bg, fg, ac = item
    im = Image.new('RGB', (cell_w, cell_h), bg); d = ImageDraw.Draw(im)
    m = 6
    d.rectangle([m, m, cell_w - m - 1, cell_h - m - 1], outline=ac, width=4)  # border
    d.rectangle([m + 9, m + 9, cell_w - m - 10, cell_h - m - 10], outline=tuple(int(0.55 * a + 0.45 * b) for a, b in zip(ac, bg)), width=1)
    th = int(cell_h * (0.46 if sub else 0.62)); f = fit(d, name, fk, int(cell_w * 0.9), th)
    b = d.textbbox((0, 0), name, font=f); tw, tht = b[2] - b[0], b[3] - b[1]
    cy = cell_h * (0.36 if sub else 0.5)
    d.text(((cell_w - tw) // 2 - b[0], int(cy - tht / 2) - b[1]), name, font=f, fill=fg)
    if sub:
        fs = fit(d, sub, 'gill', int(cell_w * 0.62), int(cell_h * 0.15)); bs = d.textbbox((0, 0), sub, font=fs)
        d.text(((cell_w - (bs[2] - bs[0])) // 2 - bs[0], int(cell_h * 0.73 - (bs[3] - bs[1]) / 2) - bs[1]), sub, font=fs, fill=ac)
    return im

def valance(cell_w, cell_h, text, fk):
    im = Image.new('L', (cell_w, cell_h), 0); d = ImageDraw.Draw(im)
    f = fit(d, text, fk, int(cell_w * 0.86), int(cell_h * 0.62)); b = d.textbbox((0, 0), text, font=f)
    d.text(((cell_w - (b[2] - b[0])) // 2 - b[0], (cell_h - (b[3] - b[1])) // 2 - b[1]), text, font=f, fill=255)
    return im.convert('RGB')

if __name__ == '__main__':
    atlas = Image.new('RGB', (4096, 2048), (0, 0, 0))
    names = {'fascia': [], 'valance': []}
    for i, item in enumerate(FASCIA):
        atlas.paste(fascia(1024, 160, item), ((i % 4) * 1024, (i // 4) * 160)); names['fascia'].append(item[0])
    vf = ['futura', 'gill', 'copper', 'avenir', 'georgia', 'din']
    for i, t in enumerate(VALANCE):
        atlas.paste(valance(1024, 64, t, vf[i % len(vf)]), ((i % 4) * 1024, 1280 + (i // 4) * 64)); names['valance'].append(t)
    os.makedirs(os.path.dirname(OUT), exist_ok=True); atlas.save(OUT)
    json.dump({'fascia': names['fascia'], 'valance': names['valance'], 'fascia_cell': [1024, 160], 'valance_cell': [1024, 64], 'valance_y0': 1280}, open(OUT.replace('.png', '.json'), 'w'), indent=1)
    print('street_signs', atlas.size, len(names['fascia']), 'fascia', len(names['valance']), 'valances ->', OUT)
