#!/usr/bin/env python3
"""Contact sheets from preview_glbs.py tiles (PA phase 1). usage: contact_sheet.py <previews_dir> <out_prefix>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

src, pre = Path(sys.argv[1]), sys.argv[2]
files = sorted(p for p in src.glob("*.png") if not p.name.startswith(("_", "sheet_")))
HUM = ("human", "hijab", "woman", "male+", "leather+jacket", "traditional")
groups = {
    "humans": [p for p in files if p.stem.startswith(HUM)],
    "animals": [p for p in files if p.stem.split("+")[0] in ("pigeon", "seagull", "rat", "squirrel", "orange", "french", "golden")],
}
groups["props"] = [p for p in files if p not in groups["humans"] and p not in groups["animals"]]
T, COLS = 384, 5
for g, ps in groups.items():
    rows = (len(ps) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * T, rows * (T + 18)), (30, 30, 30))
    d = ImageDraw.Draw(sheet)
    for i, p in enumerate(ps):
        im = Image.open(p).convert("RGB").resize((T, T))
        x, y = (i % COLS) * T, (i // COLS) * (T + 18)
        sheet.paste(im, (x, y + 18))
        d.text((x + 4, y + 3), p.stem.replace("+3d+model", "").replace("+", " ")[:52], fill=(255, 255, 160))
    out = "%s_%s.jpg" % (pre, g)
    sheet.save(out, quality=88)
    print(out, len(ps))
