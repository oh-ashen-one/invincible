#!/usr/bin/env python3
"""Terrain r04 lawn prep (piece E, CPU only). Replaces the r01-r03 star-sprite tufts (9 blades, SM_tuft) by dense blade-clump grass and adds the lawn / blanket detail textures.
Inputs: <export>/terrain.json + parkmask.rgba (browser grass density / height mask), <prep>/pathmask.png (path + drive coverage, written by prep_terrain.py).
Outputs in <prep>:
  grass_near_<k>.glb  4 variants: a 2.3 m disc of ~1150 blades (clumps of 22-34 blades + loose single blades), 3 tris per blade, unit height, vertex colour R = height along the blade,
                      G = per-blade random, B = per-clump random, normals = blade-plane normal blended 55 % toward up (two-sided foliage shading)
  grass_far_<k>.glb   2 variants: a 3.2 m disc of ~230 wider, taller blades (the 16-60 m layer)
  grass_near.bin / grass_far.bin   float32 records [x, z, yaw, xy scale, height m] (browser frame) scattered over the grass mask: jittered grid (1.5 m / 2.6 m cells), kept by the browser density
                      mask, cleared of paths / drives (0.45 m), of picnic blankets and of the five water bodies' banks (the mask already holds those)
  lawn_detail.png     1024^2 RGBA tileable noise (R clump luminance, G wear, B clover, A grain), sampled by the park / lawn materials at 1.15 m, 4.7 m and 16.3 m
  blanket_weave.png   256^2 RGBA tileable gingham weave (R thread luminance, G plaid level, B slub), one tile = 0.24 m
  lawn_stats.json     counts for the checkers
usage: prep_lawn.py [export_dir] [prep_dir]"""
import os, sys, json, math
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'export'))
from glbio import write_glb
SCR = os.environ.get('SM2_TERRAIN_SCRATCH', '/Users/midir/sm2-n1/_scratch/terrain')
EXP = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('SM2_TERRAIN_EXPORT', os.path.join(SCR, 'export'))
PREP = sys.argv[2] if len(sys.argv) > 2 else os.path.join(SCR, 'prep')
os.makedirs(PREP, exist_ok=True)
T = json.load(open(os.path.join(EXP, 'terrain.json')))
PARK = T['G']['PARK']

# ------------------------------------------------------------------ tileable noise (FFT low-pass of white noise: periodic by construction)
def tile_noise(n, sigma_tex, seed):
    rng = np.random.default_rng(seed)
    w = rng.standard_normal((n, n))
    f = np.fft.rfft2(w)
    fy = np.fft.fftfreq(n)[:, None]; fx = np.fft.rfftfreq(n)[None, :]
    f *= np.exp(-2.0 * (math.pi ** 2) * (sigma_tex ** 2) * (fx ** 2 + fy ** 2))
    z = np.fft.irfft2(f, s=(n, n))
    return (z - z.mean()) / (z.std() + 1e-9)

def fractal(n, sigmas, weights, seed):
    z = sum(w * tile_noise(n, s, seed * 131 + i) for i, (s, w) in enumerate(zip(sigmas, weights)))
    return (z - z.mean()) / (z.std() + 1e-9)

N = 1024
R = 0.5 + 0.22 * fractal(N, (60, 28, 14, 7, 3.5), (1.0, 0.85, 0.7, 0.5, 0.35), 11)      # clump luminance (tile/17 .. tile/290)
G = 0.5 + 0.24 * fractal(N, (110, 55, 26), (1.0, 0.8, 0.5), 23)                         # wear / dirt field (coarse: patches of tile/9 .. tile/40)
B = 0.5 + 0.24 * fractal(N, (90, 45, 20), (1.0, 0.8, 0.5), 37)                          # clover field
A = 0.5 + 0.26 * tile_noise(N, 0.9, 51)                                                  # fine grain (mips out to 0.5 with distance)
det = np.stack([np.clip(c, 0, 1) for c in (R, G, B, A)], -1)
Image.fromarray((det * 255 + 0.5).astype(np.uint8), 'RGBA').save(os.path.join(PREP, 'lawn_detail.png'))
print('lawn_detail.png 1024x1024 (R sd %.3f G sd %.3f B sd %.3f A sd %.3f)' % tuple(det[..., i].std() for i in range(4)))

# ------------------------------------------------------------------ blanket weave (gingham): one tile = 0.24 m, 1 mm threads
M2 = 256
yy, xx = np.meshgrid(np.arange(M2), np.arange(M2), indexing='ij')
warp = ((xx // 1 + yy // 1) % 2).astype(np.float64)                                      # over / under checker at texel (thread) scale
slub = tile_noise(M2, 1.5, 5) * 0.5 + 0.4 * tile_noise(M2, 5.0, 6)
weave = np.clip(0.78 + 0.16 * (warp - 0.5) * 2 + 0.07 * slub, 0, 1)
band_u = ((xx / M2 * 3.0) % 1.0) < (1.0 / 3.0 + 0.0)                                      # 3 checks per tile in each direction
band_v = ((yy / M2 * 3.0) % 1.0) < (1.0 / 3.0 + 0.0)
lvl = (band_u.astype(np.float64) + band_v.astype(np.float64)) / 2.0                        # 0 = plain, 0.5 = single stripe, 1 = crossing
img = np.stack([weave, lvl, np.clip(0.5 + 0.25 * slub, 0, 1), np.ones_like(weave)], -1)
Image.fromarray((img * 255 + 0.5).astype(np.uint8), 'RGBA').save(os.path.join(PREP, 'blanket_weave.png'))
print('blanket_weave.png 256x256')

# ------------------------------------------------------------------ blade patches (r04 v2: after a Cycles preview the first 650-blade 1.9 m discs left ~45 % of the ground bare)
def make_patch(seed, radius, n_clumps, per_clump, loose, hlo, hhi, w_lo, w_hi, lean_lo, lean_hi, crad_lo, crad_hi, min_gap):
    rng = np.random.default_rng(seed)
    P, Nn, C, I = [], [], [], []
    def blade(bx, bz, hk, w, dirv, lean, g, b):
        px, pz = -dirv[1], dirv[0]
        pts = []
        for t, wf, ht, lf in ((0.0, 1.0, 0.0, 0.0), (0.5, 0.78, 0.5 * hk, 0.28 * lean), (1.0, 0.0, hk, lean)):
            cx, cz = bx + dirv[0] * lf, bz + dirv[1] * lf
            if wf > 0: pts.append(((cx - px * w * wf * 0.5, ht, cz - pz * w * wf * 0.5), t, g, b)); pts.append(((cx + px * w * wf * 0.5, ht, cz + pz * w * wf * 0.5), t, g, b))
            else: pts.append(((cx, ht, cz), t, g, b))
        v0 = len(P)
        nrm = np.array([dirv[0] * 0.55, 0.83, dirv[1] * 0.55]); nrm /= np.linalg.norm(nrm)
        for pos, t, gg, bb in pts: P.append(pos); Nn.append(nrm); C.append((t, gg, bb, 1.0))
        I.extend([v0, v0 + 1, v0 + 3, v0, v0 + 3, v0 + 2, v0 + 2, v0 + 3, v0 + 4])
    # clump centres: dart throwing inside the disc, minimum spacing 0.9 of the clump radius
    centres = []
    tries = 0
    while len(centres) < n_clumps and tries < 4000:
        tries += 1
        a = rng.uniform(0, 2 * math.pi); r = radius * 0.92 * math.sqrt(rng.uniform())
        c = (r * math.cos(a), r * math.sin(a))
        if all((c[0] - o[0]) ** 2 + (c[1] - o[1]) ** 2 > min_gap ** 2 for o in centres): centres.append(c)
    for c in centres:
        crad = rng.uniform(crad_lo, crad_hi); cb = rng.uniform(); chh = rng.uniform(0.82, 1.12)
        for _ in range(int(rng.integers(per_clump[0], per_clump[1] + 1))):
            a = rng.uniform(0, 2 * math.pi); r = crad * abs(rng.standard_normal()) * 0.7
            bx, bz = c[0] + r * math.cos(a), c[1] + r * math.sin(a)
            out = math.atan2(bz - c[1], bx - c[0]) if r > 1e-4 else rng.uniform(0, 2 * math.pi)
            ang = out + rng.normal(0, 0.55)
            hk = rng.uniform(hlo, hhi) * chh * (1.0 - 0.25 * (r / (crad + 1e-6)) / 3.0)
            blade(bx, bz, hk, rng.uniform(w_lo, w_hi), (math.cos(ang), math.sin(ang)), rng.uniform(lean_lo, lean_hi) * (0.4 + r / (crad + 1e-6)), rng.uniform(), cb)
    for _ in range(loose):
        a = rng.uniform(0, 2 * math.pi); r = radius * 0.95 * math.sqrt(rng.uniform()); ang = rng.uniform(0, 2 * math.pi)
        blade(r * math.cos(a), r * math.sin(a), rng.uniform(hlo, hhi) * 0.9, rng.uniform(w_lo, w_hi), (math.cos(ang), math.sin(ang)), rng.uniform(lean_lo, lean_hi), rng.uniform(), rng.uniform())
    return np.array(P, np.float32), np.array(Nn, np.float32), np.array(C, np.float32), np.array(I, np.int64)

NEAR = dict(radius=1.15, n_clumps=26, per_clump=(30, 44), loose=200, hlo=0.62, hhi=1.0, w_lo=0.011, w_hi=0.019, lean_lo=0.05, lean_hi=0.12, crad_lo=0.12, crad_hi=0.22, min_gap=0.30)
FAR = dict(radius=1.7, n_clumps=12, per_clump=(24, 34), loose=70, hlo=0.6, hhi=1.0, w_lo=0.018, w_hi=0.030, lean_lo=0.06, lean_hi=0.16, crad_lo=0.2, crad_hi=0.34, min_gap=0.5)
tri_total = {}
for name, cfg, nv in (('near', NEAR, 4), ('far', FAR, 2)):
    for k in range(nv):
        Pp, Nn, Cc, Ii = make_patch(100 + k + (0 if name == 'near' else 50), **cfg)
        write_glb(os.path.join(PREP, 'grass_%s_%d.glb' % (name, k)), {'POSITION': Pp, 'NORMAL': Nn, 'TEXCOORD_0': np.zeros((len(Pp), 2), np.float32), 'COLOR_0': Cc}, Ii, 'grass_%s_%d' % (name, k))
        tri_total[name] = len(Ii) // 3; print('grass_%s_%d.glb: %d blades, %d verts, %d tris' % (name, k, len(Ii) // 9, len(Pp), len(Ii) // 3))

# ------------------------------------------------------------------ scatter
PX0, PZ0, PW, PH = T['mask']['x0'], T['mask']['z0'], T['mask']['w'], T['mask']['h']
M = np.fromfile(os.path.join(EXP, T['mask']['file']), np.uint8).reshape(PH, PW, 4)
dens = M[..., 0] / 255.0; hgt = M[..., 1] / 255.0
pm = np.asarray(Image.open(os.path.join(PREP, 'pathmask.png')).convert('RGBA'))
pmj = json.load(open(os.path.join(PREP, 'pathmask.json'))); TEXEL = pmj['texel']
PATH = (pm[..., 1] > 0) | (pm[..., 2] > 0)
clear = ndimage.distance_transform_edt(~PATH) * TEXEL                                    # metres to the nearest path / drive texel
blank = T['instances'].get('park-blankets', {}).get('items', [])
BL = np.array([[r[0], r[2], 0.5 * math.hypot(1.8 * r[4], 1.5 * r[6]) + 0.45] for r in blank], np.float64) if blank else np.zeros((0, 3))

def _sstep(a, b, v): t = np.clip((v - a) / (b - a), 0.0, 1.0); return t * t * (3.0 - 2.0 * t)
def infield_sand(x, z):
    """r04: the ball-field clay (skinned fan + pitcher's mound) of Park.ush, evaluated here WITHOUT its noise gate: blades are removed there so the clay reads (round-03 critic: pale squares
    for ball fields; the blades had hidden the browser's dirt). Same geometry as Park.ush's `for (i = 1..2, k = 0..3)` loop over the meadows uMd[1], uMd[2] (browser x, z in metres)."""
    out = np.zeros_like(x)
    for i in (1, 2):
        m = T['meadows'][i]; c = np.array([m['x'], m['z']]); half = np.array([m['rx'], m['rz']])
        for k in range(4):
            if i == 2 and k in (1, 2): continue
            fk = float(i * 4 + k)
            hp = c + np.array([(k & 1) * 2.0 - 1.0, (k >> 1) * 2.0 - 1.0]) * half * np.array([0.55 + 0.08 * math.sin(fk * 2.3), 0.5 + 0.08 * math.cos(fk * 1.7)])
            d0 = c - hp; d0 = d0 / np.linalg.norm(d0)
            ra = 0.35 * math.sin(fk * 3.1 + 0.4)
            dv = np.array([d0[0] * math.cos(ra) - d0[1] * math.sin(ra), d0[0] * math.sin(ra) + d0[1] * math.cos(ra)])
            R = 22.0 + 5.0 * ((fk * 0.618) % 1.0)
            dx, dz = x - hp[0], z - hp[1]; r = np.hypot(dx, dz); ca = (dx * dv[0] + dz * dv[1]) / np.maximum(r, 1e-3)
            fan = (1.0 - _sstep(R, R + 1.5, r)) * _sstep(0.66, 0.72, ca)
            qx = dx * dv[0] + dz * dv[1]; qy = -dx * dv[1] + dz * dv[0]
            qdx = (qx + qy) * 0.7071; qdy = (qx - qy) * 0.7071; gs = R * 0.64
            grass_sq = (qdx >= 1.5) & (qdy >= 1.5) & (qdx <= gs) & (qdy <= gs)
            mound = 1.0 - _sstep(2.5, 3.2, np.hypot(qx - R * 0.48, qy))
            out = np.maximum(out, np.maximum(fan * (~grass_sq), mound))
    return out

def scatter(cell, seed, hcap, dens_pow):
    rng = np.random.default_rng(seed)
    nx, nz = int((PARK['x1'] - PARK['x0']) / cell), int((PARK['z1'] - PARK['z0']) / cell)
    gi, gj = np.meshgrid(np.arange(nx), np.arange(nz))
    jit = rng.uniform(0, 1, (nz, nx, 5))
    x = PARK['x0'] + (gi + jit[..., 0]) * cell; z = PARK['z0'] + (gj + jit[..., 1]) * cell
    mi = np.clip(np.floor(x - PX0).astype(int), 0, PW - 1); mj = np.clip(np.floor(z - PZ0).astype(int), 0, PH - 1)
    keep = jit[..., 2] < dens[mj, mi] ** dens_pow
    pi_ = np.clip(np.floor((x - PX0) / TEXEL).astype(int), 0, pm.shape[1] - 1); pj_ = np.clip(np.floor((z - PZ0) / TEXEL).astype(int), 0, pm.shape[0] - 1)
    keep &= (clear[pj_, pi_] > 0.45)
    keep &= jit[..., 4] > 0.93 * infield_sand(x, z)                                      # r04: bare clay on the ball-field infields (a few stray blades remain)
    xk, zk = x[keep], z[keep]
    if len(BL):
        ok = np.ones(len(xk), bool)
        for bx, bz, br in BL: ok &= (xk - bx) ** 2 + (zk - bz) ** 2 > br * br
        keep_idx = np.flatnonzero(keep); keep = np.zeros_like(keep); keep.flat[keep_idx[ok]] = True
    sel = keep
    h = (0.05 + 0.34 * hgt[mj, mi]) * (0.75 + 0.5 * jit[..., 3])                          # mowed lawn ~ 9-15 cm, taller where the browser mask grows tall grass
    rec = np.stack([x[sel], z[sel], rng.uniform(0, 2 * math.pi, sel.sum()), rng.uniform(0.85, 1.2, sel.sum()), np.clip(h[sel], 0.07, hcap)], 1).astype(np.float32)
    return rec
near = scatter(1.5, 7, 0.30, 0.5)
far = scatter(2.6, 8, 0.38, 0.5)
near.tofile(os.path.join(PREP, 'grass_near.bin')); far.tofile(os.path.join(PREP, 'grass_far.bin'))
st = {'near_patches': int(len(near)), 'far_patches': int(len(far)), 'near_tris_per_patch': tri_total.get('near'), 'far_tris_per_patch': tri_total.get('far'), 'blankets_cleared': int(len(BL)),
      'near_blades_per_m2_at_full_density': round(tri_total['near'] / 3 / 1.5 ** 2, 1), 'far_blades_per_m2_at_full_density': round(tri_total['far'] / 3 / 2.6 ** 2, 1)}
json.dump(st, open(os.path.join(PREP, 'lawn_stats.json'), 'w'), indent=1)
print(json.dumps(st))
