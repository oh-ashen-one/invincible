#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# P6 City life: prepare the browser's vehicle pack for Unreal.
#   python3 tools/life/prep_vehicles.py [--out /Users/midir/sm2-n1/_scratch/life/vehicles]
# reads   public/assets/city/vehicles.glb            15 vehicle types x 3 LODs (<name>, <name>_l1, <name>_l2), no materials
#         public/assets/city/tex/vehicles_atlas2.webp  the code-side atlas (interiors, ads, plates, grilles, lights, swatches)
# writes  <out>/glb/<name>.glb       one GLB per mesh (POSITION, NORMAL, TEXCOORD_0 atlas uv, TEXCOORD_1 (part id, 0), COLOR_0 baked AO)
#         <out>/vehicles_atlas_clean.png   the atlas with every Marvel-universe / real-brand livery cell painted out (see docs/night1/life/IP_EXCLUSIONS.md)
#         <out>/vehicles.json               per type: LOD mesh names, bbox (m), used atlas cells
import argparse, json, os, struct, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ap = argparse.ArgumentParser()
ap.add_argument('--out', default='/Users/midir/sm2-n1/_scratch/life/vehicles')
a = ap.parse_args()
OUT = a.out
os.makedirs(os.path.join(OUT, 'glb'), exist_ok=True)

# ------------------------------------------------------------------------------------------------ split the GLB
SRC = os.path.join(ROOT, 'public/assets/city/vehicles.glb')
b = open(SRC, 'rb').read()
(jl,) = struct.unpack('<I', b[12:16]); js = json.loads(b[20:20 + jl])
off = 20 + jl; (bl,) = struct.unpack('<I', b[off:off + 4]); bin_ = b[off + 8:off + 8 + bl]
DT = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}

def acc(i):
    ac = js['accessors'][i]; bv = js['bufferViews'][ac['bufferView']]
    n = NC[ac['type']]; o = bv.get('byteOffset', 0) + ac.get('byteOffset', 0)
    stride = bv.get('byteStride'); isz = np.dtype(DT[ac['componentType']]).itemsize
    if stride and stride != n * isz:
        raw = np.frombuffer(bin_, np.uint8, offset=o)
        arr = np.stack([np.frombuffer(raw[k * stride:k * stride + n * isz].tobytes(), DT[ac['componentType']]) for k in range(ac['count'])])
    else:
        arr = np.frombuffer(bin_, DT[ac['componentType']], ac['count'] * n, o).reshape(-1, n)
    if ac.get('normalized'): arr = arr.astype(np.float64) / np.iinfo(DT[ac['componentType']]).max
    return arr

def write_glb(path, attrs, index, name):
    chunks, views, accs, ap_ = [], [], [], {}
    def add(arr, dtype, typ, ctype, target, minmax=False):
        arr = np.ascontiguousarray(arr.astype(dtype)); data = arr.tobytes()
        off_ = sum(len(c) for c in chunks); pad = (4 - len(data) % 4) % 4
        chunks.append(data + b'\0' * pad)
        views.append({'buffer': 0, 'byteOffset': off_, 'byteLength': len(data), 'target': target})
        ac = {'bufferView': len(views) - 1, 'componentType': ctype, 'count': int(arr.shape[0]), 'type': typ}
        if minmax: ac['min'] = arr.min(0).astype(float).tolist(); ac['max'] = arr.max(0).astype(float).tolist()
        accs.append(ac); return len(accs) - 1
    for k, v in attrs.items():
        ap_[k] = add(v, np.float32, {1: 'SCALAR', 2: 'VEC2', 3: 'VEC3', 4: 'VEC4'}[v.shape[1]], 5126, 34962, minmax=(k == 'POSITION'))
    ii = add(np.asarray(index).reshape(-1, 1), np.uint32, 'SCALAR', 5125, 34963)
    j = {'asset': {'version': '2.0', 'generator': 'sm2 life prep_vehicles'}, 'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'mesh': 0, 'name': name}],
         'meshes': [{'name': name, 'primitives': [{'attributes': ap_, 'indices': ii, 'mode': 4}]}],
         'buffers': [{'byteLength': sum(len(c) for c in chunks)}], 'bufferViews': views, 'accessors': accs}
    jb = json.dumps(j, separators=(',', ':')).encode(); jb += b' ' * ((4 - len(jb) % 4) % 4)
    bn = b''.join(chunks)
    open(path, 'wb').write(struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(jb) + 8 + len(bn)) + struct.pack('<I4s', len(jb), b'JSON') + jb + struct.pack('<I4s', len(bn), b'BIN\0') + bn)

info = {}
for n in js['nodes']:
    mesh = js['meshes'][n['mesh']]; name = n['name']
    pr = mesh['primitives'][0]
    A = {k: acc(v).astype(np.float64) for k, v in pr['attributes'].items()}
    idx = acc(pr['indices']).reshape(-1).astype(np.uint32)
    attrs = {k: A[k] for k in ('POSITION', 'NORMAL', 'TEXCOORD_0', 'TEXCOORD_1', 'COLOR_0') if k in A}
    if 'COLOR_0' in attrs and attrs['COLOR_0'].shape[1] == 3:
        attrs['COLOR_0'] = np.c_[attrs['COLOR_0'], np.ones(len(attrs['COLOR_0']))]
    if 'TEXCOORD_1' in attrs and attrs['TEXCOORD_1'].shape[1] == 1:
        attrs['TEXCOORD_1'] = np.c_[attrs['TEXCOORD_1'], np.zeros(len(attrs['TEXCOORD_1']))]
    write_glb(os.path.join(OUT, 'glb', name + '.glb'), attrs, idx, name)
    P = A['POSITION']
    base = name.split('_l')[0] if name.endswith(('_l1', '_l2')) else name
    d = info.setdefault(base, {'lods': {}})
    d['lods'][name] = {'verts': int(len(P)), 'tris': int(len(idx) // 3)}
    if name == base:
        d['bbox_min'] = P.min(0).round(3).tolist(); d['bbox_max'] = P.max(0).round(3).tolist()
        d['parts'] = sorted({int(round(v)) for v in A['TEXCOORD_1'][:, 0]}) if 'TEXCOORD_1' in A else []
print('split %d meshes' % len(js['nodes']))

# ------------------------------------------------------------------------------------------------ IP-clean atlas
im = Image.open(os.path.join(ROOT, 'public/assets/city/tex/vehicles_atlas2.webp')).convert('RGB')
assert im.size == (2048, 2048), im.size
W = H = 2048
d = ImageDraw.Draw(im)
# taxi-topper ad tiles: 2 columns x 4 rows in the top right quarter (browser: u 0.5 + (k % 2) * 0.25 .. , v = floor(k / 2) * 170 / 2048, tile k = 0..7).
# Cells were read tile by tile (docs/night1/life/IP_EXCLUSIONS.md): k=1 DAILY BUGLE, k=3 ROXXON ENERGY, k=5 OSCORP are Marvel-universe brands.
AD_W, AD_H = 512, 170
EXCLUDED_ADS = {1: 'DAILY BUGLE (Marvel universe)', 3: 'ROXXON ENERGY (Marvel universe)', 5: 'OSCORP (Marvel universe)',
                7: 'Skyline Sneakers (shoe with an orange swoosh-like mark; excluded as a precaution)'}
KEPT_ADS = {0: 'Fuhgeddaboutit Pizza', 2: 'Wolf & Sheep (invented musical)', 4: 'Empire Bagel Co.', 6: 'Hudson Injury Law'}
for k in EXCLUDED_ADS:
    x0 = W // 2 + (k % 2) * 512; y0 = (k // 2) * AD_H
    # neutral panel + a plain diagonal stripe so a stray sample reads as a blank sign
    d.rectangle([x0, y0, x0 + AD_W - 1, y0 + AD_H - 1], fill=(206, 204, 198))
    d.rectangle([x0, y0 + AD_H // 2 - 6, x0 + AD_W - 1, y0 + AD_H // 2 + 6], fill=(150, 150, 146))
# real-world transit branding on the two bus sign cells ("M15 SELECT BUS 2 AV" = a real route, "NYC TRANSIT" = a real agency): replaced by generic text.
# Cells measured on the 2048 px atlas: black destination band x 0-512 / y 1214-1280, off-white agency band x 512-1024 / y 1248-1314.
try:
    F = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 46)
except Exception:
    F = ImageFont.load_default()
for (x, y, w, h), text, fg, bg in (((0, 1214, 512, 66), 'CROSSTOWN  LOCAL', (250, 168, 20), (8, 8, 8)), ((512, 1248, 512, 66), 'CITY  TRANSIT', (28, 66, 140), (245, 245, 242))):
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=bg)
    tw = d.textlength(text, font=F); d.text((x + (w - tw) / 2, y + (h - 46) / 2 - 2), text, font=F, fill=fg)
# round 03 (critic r02): the taxi label "NYC TAXI" (the NYC taxi logo text) is a real-world mark -> generic "CITY TAXI". Cell x 768-1024 / y 1024-1150 of the 2048 px atlas:
# black rounded square x 780-882 / y 1038-1138 carrying "NYC" in taxi yellow, then the word TAXI. Only the three letters inside the square are repainted.
try:
    F2 = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 34, index=1)
except Exception:
    F2 = F
d.rectangle([786, 1062, 878, 1116], fill=(15, 15, 15))
tw2 = d.textlength('CITY', font=F2); d.text((831 - tw2 / 2, 1088 - 21), 'CITY', font=F2, fill=(244, 170, 0))
im.save(os.path.join(OUT, 'vehicles_atlas_clean.png'))
# crops for the record
for k in range(8):
    x0 = W // 2 + (k % 2) * 512; y0 = (k // 2) * AD_H
    im.crop((x0, y0, x0 + AD_W, y0 + AD_H)).save(os.path.join(OUT, 'ad_tile_%d.png' % k))
json.dump({'types': info, 'atlas_clean': 'vehicles_atlas_clean.png', 'ad_tiles_excluded': EXCLUDED_ADS, 'ad_tiles_kept': KEPT_ADS,
           'bus_text_replaced': ['bus_dest', 'bus_text', 'taxi_label_nyc_to_city']}, open(os.path.join(OUT, 'vehicles.json'), 'w'), indent=1)
print('atlas cleaned; excluded ad tiles', sorted(EXCLUDED_ADS))
