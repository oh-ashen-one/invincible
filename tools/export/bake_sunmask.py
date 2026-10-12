#!/usr/bin/env python3
"""(r09) Bake the building HEIGHT FIELD the city materials ray-march to know where the sun cannot reach (canyon shade; Shaders/City/ShadeFill.ush CitySunLit).
Sources (pure Python, no browser, no Unreal): the up-facing triangles of the export's roof meshes (rasterised: exact tiers, setbacks, terraces) + facade vertices (wall tops, parapets) scatter-max,
and layout.json footprint boxes (body height h) only for buildings outside the detailed block.  Output: <TEX>/sunmask_h.png, RGB8, R = high byte, G = low byte of height / 0.02 m (0..1310 m), B = min(height, 400 m) / 400 (mip-averaged: local mean height);
1 m per texel, 1024 x 1024, browser x -384..640 (columns), browser z -640..384 (rows, top row = smallest z = north).  The same extents are constants in ShadeFill.ush.
usage: bake_sunmask.py [export_dir] [tex_dir]"""
import json, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from glbio import read_glb

SCRATCH = os.environ.get('SM2_CITY_SCRATCH', '/Users/midir/sm2-n1/_scratch/city')
E = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SCRATCH, 'export', 'midtown3x3')
TEX = sys.argv[2] if len(sys.argv) > 2 else os.path.join(SCRATCH, 'tex')
# (island r01) island-wide: the grid covers the whole browser island (x -1024..1024, z -4096..4096: 2048 x 8192 texels, power-of-two for the
# mips); override with SM2_SUNMASK="x0,z0,cols,rows" (metres, texels). MUST match CITY_SM_X0 / Y0 / W / H in Shaders/City/ShadeFill.ush.
_sm = [float(v) for v in os.environ.get('SM2_SUNMASK', '-1024,-4096,2048,8192').split(',')]
X0, Z0, NW, NH = _sm[0], _sm[1], int(_sm[2]), int(_sm[3])   # metres of the texel grid origin, texels (1 m each)
N = max(NW, NH)
H = np.zeros((NH, NW), np.float32)           # H[row = z - Z0, col = x - X0]

L = json.load(open(os.path.join(E, 'layout.json')))
M = json.load(open(os.path.join(E, 'manifest.json')))
reg = M['region'] if isinstance(M.get('region'), dict) else L['region']
# 1) footprint boxes (body height h) ONLY outside the detailed block: inside it the roof meshes give the real tiered shape (a box of the tallest tier over the whole plot over-shadows
#    setback towers: r09b first version marked visibly sunlit faces of S8 as shaded).
DX0, DX1, DZ0, DZ1 = reg['x0'], reg['x1'], reg['z0'], reg['z1']
def put_box(f):
    c0, c1 = int(np.floor(f['x0'] - X0)), int(np.ceil(f['x1'] - X0)); r0, r1 = int(np.floor(f['z0'] - Z0)), int(np.ceil(f['z1'] - Z0))
    c0, c1, r0, r1 = max(c0, 0), min(c1, NW), max(r0, 0), min(r1, NH)
    if c1 > c0 and r1 > r0: H[r0:r1, c0:c1] = np.maximum(H[r0:r1, c0:c1], f['h'])
nfp = 0
for f in sorted(L['footprints'], key=lambda q: q['h']):
    cx, cz = 0.5 * (f['x0'] + f['x1']), 0.5 * (f['z0'] + f['z1'])
    if not (DX0 <= cx <= DX1 and DZ0 <= cz <= DZ1): put_box(f); nfp += 1
# 2) up-facing roof / terrace / ledge triangles of the detailed block, rasterised (ascending height, taller overwrites)
tris = []
for r in M['meshes']:
    if r['kind'] != 'roofs' or 'Lod' in r['file']: continue
    g = read_glb(os.path.join(E, r['file'])); P = g['attrs']['POSITION'].copy(); I = g['index'].reshape(-1, 3); c = r['center']
    P[:, 0] += c[0]; P[:, 2] += c[2]
    T = P[I]; nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); nn = np.linalg.norm(nrm, axis=1)
    up = (np.abs(nrm[:, 1]) > 0.7 * np.maximum(nn, 1e-9)) & (T[:, :, 1].min(axis=1) > 0.5) & (nn > 1e-6)
    tris.append(T[up])
T = np.concatenate(tris); T = T[np.argsort(T[:, :, 1].mean(axis=1))]
ntri = len(T)
for t in T:
    y = float(t[:, 1].max()); xs = t[:, 0] - X0; zs = t[:, 2] - Z0
    c0, c1 = int(np.floor(xs.min())), int(np.ceil(xs.max())); r0, r1 = int(np.floor(zs.min())), int(np.ceil(zs.max()))
    if c1 <= 0 or r1 <= 0 or c0 >= NW or r0 >= NH: continue
    c0, r0, c1, r1 = max(c0, 0), max(r0, 0), min(c1, NW), min(r1, NH)
    if c1 <= c0 or r1 <= r0: continue
    gx, gz = np.meshgrid(np.arange(c0, c1) + 0.5, np.arange(r0, r1) + 0.5)
    (ax, az), (bx, bz), (cx_, cz_) = (xs[0], zs[0]), (xs[1], zs[1]), (xs[2], zs[2])
    d = (bz - cz_) * (ax - cx_) + (cx_ - bx) * (az - cz_)
    if abs(d) < 1e-9: continue
    w0 = ((bz - cz_) * (gx - cx_) + (cx_ - bx) * (gz - cz_)) / d; w1 = ((cz_ - az) * (gx - cx_) + (ax - cx_) * (gz - cz_)) / d; w2 = 1 - w0 - w1
    inside = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
    if inside.any():
        sub = H[r0:r1, c0:c1]; sub[inside] = np.maximum(sub[inside], y)
# 2b) inner footprints whose roof is missing / sparse in the roof meshes (dotted holes in the raster): fill the still-empty cells of the box with the body height
nfill = 0
for f in L['footprints']:
    cx, cz = 0.5 * (f['x0'] + f['x1']), 0.5 * (f['z0'] + f['z1'])
    if not (DX0 <= cx <= DX1 and DZ0 <= cz <= DZ1): continue
    c0, c1 = int(np.floor(f['x0'] - X0)), int(np.ceil(f['x1'] - X0)); r0, r1 = int(np.floor(f['z0'] - Z0)), int(np.ceil(f['z1'] - Z0))
    c0, c1, r0, r1 = max(c0, 0), min(c1, NW), max(r0, 0), min(r1, NH)
    if c1 <= c0 or r1 <= r0: continue
    sub = H[r0:r1, c0:c1]
    if (sub > 0).mean() < 0.85: sub[sub == 0] = f['h']; nfill += 1
# 3) facade vertices (wall tops, parapets, spires) scatter-max into their cell
nv = 0
for r in M['meshes']:
    if r['kind'] != 'facade' or 'Lod' in r['file']: continue
    g = read_glb(os.path.join(E, r['file'])); P = g['attrs']['POSITION']; c = r['center']
    x = P[:, 0] + c[0]; z = P[:, 2] + c[2]; y = P[:, 1]
    col = np.floor(x - X0).astype(np.int64); row = np.floor(z - Z0).astype(np.int64)
    ok = (col >= 0) & (col < NW) & (row >= 0) & (row < NH) & (y > 0.5)
    np.maximum.at(H, (row[ok], col[ok]), y[ok].astype(np.float32)); nv += int(ok.sum())
v = np.clip(np.round(H / 0.02), 0, 65535).astype(np.uint16)
img = np.zeros((NH, NW, 3), np.uint8); img[..., 0] = v >> 8; img[..., 1] = v & 255
img[..., 2] = np.clip(np.round(np.minimum(H, 400.0) / 400.0 * 255.0), 0, 255).astype(np.uint8)   # B = height / 400 m (8 bit): read at high mips = mean building height around a point (enclosure)
os.makedirs(TEX, exist_ok=True)
Image.fromarray(img, 'RGB').save(os.path.join(TEX, 'sunmask_h.png'))
os.makedirs(os.path.join(SCRATCH, 'r09'), exist_ok=True)   # (r11) fresh scratch: the preview folder did not exist
Image.fromarray(np.clip(H / 340.0 * 255, 0, 255).astype(np.uint8), 'L').save(os.path.join(SCRATCH, 'r09', 'sunmask_h_preview.png'))
json.dump({'x0': X0, 'z0': Z0, 'cols': NW, 'rows': NH, 'metres_per_texel': 1.0}, open(os.path.join(TEX, 'sunmask_h.json'), 'w'))
print(f'sunmask_h.png ({NW} x {NH} texels from x {X0:.0f} z {Z0:.0f}): {nfp} outer footprint boxes, {ntri} roof triangles, {nfill} inner boxes filled, {nv} facade vertices, max h {H.max():.1f} m, covered texels {(H > 0).mean() * 100:.1f} %')
