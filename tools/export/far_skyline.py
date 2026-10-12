#!/usr/bin/env python3
"""P1 city (r10): the far-shore band of the S4 perch view (critic r09: 'white box plateau', silhouette-top std 6.1 px, 'grey wall embankment').
Pure Python on the exporter's data (no browser, no Unreal): writes the extra far-field content that build_city.py imports (step `fsky`) into
<export>/mesh/farsky/*.glb, <export>/proto/farsky_clump.glb and <export>/farsky.json.

  1. Plateau towers  : Fort-Lee / Cliffside-like high-rise clusters on the Palisades plateau (60-280 m, podium + shaft + crown + spire, mid-grey / stone tones),
                       M_CityFarMass (window grid, same vertex-colour convention as the exporter's farCityMass: rgb = tone, alpha = 0 plain / 0.5 windows / 1 glass).
  2. Hinterland towers: 5-sided boxes in the browser's hinterland item format (x y z sx sy sz rot wall rgb roof rgb), 6-17 km west / north-west, 70-330 m:
                       the far horizon gets a real, uneven skyline (S4 silhouette-top std).
  3. Bluff           : replaces the flat Palisades face (`palisadesCliff`, one vertical quad per 80 m) by a displaced face (talus, ledges, ravines, wooded patches
                       through vertex colour R) + tree clumps on its wooded parts and along the brow.
  4. Shoreline       : seawall + cap + promenade on the New-Jersey shore, extra piers with sheds where the browser's piers stop (z < -2600), tree row on the promenade.
  5. Lawn trees      : tree clumps on the green (lawn / park) pixels of the far-land ground map: the browser's far canopy is not exported, the far shores had no trees.
(r11, critic r10: 'far towers are untextured two-tone extrusions with no windows') the plateau towers are now far-LOD facade towers: five archetypes (stepped deco, slab with setbacks, twin shafts,
glass slab, brick block), 1-4 tiers each with crown boxes / mechanical penthouses / a 45-degree chamfer overlay on some, and vertex-alpha window codes the M_CityFarMass shader reads
(0.40 punched, 0.62 ribbon, 0.90 glass-with-fins; the old 0 / 0.5 / 1.0 codes stay for the exporter's farCityMass); authored tones are mid-grey (albedo 0.22-0.36 after MPC FarGain).
The hinterland boxes get 1-3 setback tiers, yaw variety and original-art tones in the same 0.22-0.36 range. Layout draws of the first RNG are unchanged (details use their own RNGs).
Deterministic (seeded). Re-run after any change; then `build_city.py steps=fsky,map`.
usage: python3 tools/export/far_skyline.py
"""
import os, sys, json, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from citypaths import EXPORT
from glbio import write_glb

FAR_Y, PAL_Y, WATER_Y = 1.2, 58.0, -1.6
OUT = os.path.join(EXPORT, 'mesh', 'farsky'); os.makedirs(OUT, exist_ok=True)
POUT = os.path.join(EXPORT, 'proto'); os.makedirs(POUT, exist_ok=True)

# ---------------------------------------------------------------- the browser's Palisades line (farshore.js PAL_KEY / PAL_CLIFF, same wiggle)
PAL_KEY = [[-1880, -5200], [-1885, -3400], [-1905, -2300], [-1945, -1300], [-1985, -350], [-2030, 450], [-2120, 900], [-2330, 1150]]
def _pal_cliff():
    out = []
    for i in range(len(PAL_KEY) - 1):
        (ax, az), (bx, bz) = PAL_KEY[i], PAL_KEY[i + 1]
        n = max(1, int(math.floor(math.hypot(bx - ax, bz - az) / 80 + 0.5)))
        for k in range(n):
            t = k / n; z = az + (bz - az) * t
            e = 0 if i == 0 and k == 0 else 30 * math.sin(z * 0.0093 + 0.6) + 17 * math.sin(z * 0.031 + 2.3) + 9 * math.sin(z * 0.087 + 4.1)
            out.append([ax + (bx - ax) * t + e - 20, z])
    out.append(PAL_KEY[-1]); return np.array(out, float)
PAL = _pal_cliff()
def cliff_x(z): return float(np.interp(z, PAL[:, 1], PAL[:, 0]))
# NJ shoreline (farshore.js FAR_LANDS 'nj' east edge, z increasing)
NJ_SHORE = np.array([[-1500, -12000], [-1480, -5000], [-1510, -3500], [-1610, -2000], [-1690, -600], [-1735, 600], [-1760, 1600], [-1860, 2400]], float)
def shore_x(z): return float(np.interp(z, NJ_SHORE[:, 1], NJ_SHORE[:, 0]))

# ---------------------------------------------------------------- deterministic value noise
def _h(ix, iy, seed):
    n = (ix.astype(np.int64) * 374761393 + iy.astype(np.int64) * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0
def vnoise(x, y, seed=0):
    x = np.asarray(x, float); y = np.asarray(y, float)
    x0 = np.floor(x); y0 = np.floor(y); fx = x - x0; fy = y - y0
    fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    a = _h(x0, y0, seed); b = _h(x0 + 1, y0, seed); c = _h(x0, y0 + 1, seed); d = _h(x0 + 1, y0 + 1, seed)
    return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy
def sstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

# ---------------------------------------------------------------- mesh builder
class Mesh:
    def __init__(self): self.P = []; self.N = []; self.C = []; self.I = []; self.n = 0
    def quad(self, p, nrm, col):
        p = np.asarray(p, float)
        if np.dot(np.cross(p[1] - p[0], p[2] - p[0]), np.asarray(nrm, float)) < 0: p = p[[0, 3, 2, 1]]   # counter-clockwise seen from outside whatever order the caller used
        self.P.append(p); self.N.append(np.tile(np.asarray(nrm, float), (4, 1))); self.C.append(np.tile(np.asarray(col, float), (4, 1)))
        self.I.append(np.array([0, 1, 2, 0, 2, 3]) + self.n); self.n += 4
    def box(self, x0, z0, x1, z1, y0, y1, col_side, col_top=None, flag=0.0, bottom=False):
        """axis-aligned box in browser coordinates (x east, y up, z south); sides + top (no bottom) with outward counter-clockwise faces"""
        cs = list(col_side[:3]) + [flag]; ct = list((col_top or col_side)[:3]) + [0.0 if flag < 0.75 else 0.0]
        self.quad([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0]], [0, 0, -1], cs)   # north face (z0) seen from -z
        self.quad([[x1, y0, z0], [x1, y0, z1], [x1, y1, z1], [x1, y1, z0]], [1, 0, 0], cs)
        self.quad([[x1, y0, z1], [x0, y0, z1], [x0, y1, z1], [x1, y1, z1]], [0, 0, 1], cs)
        self.quad([[x0, y0, z1], [x0, y0, z0], [x0, y1, z0], [x0, y1, z1]], [-1, 0, 0], cs)
        self.quad([[x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]], [0, 1, 0], ct)
    def arrays(self, ox=0.0, oz=0.0):
        P = np.concatenate(self.P).astype(np.float32); P[:, 0] -= ox; P[:, 2] -= oz
        return P, np.concatenate(self.N).astype(np.float32), np.concatenate(self.C).astype(np.float32), np.concatenate(self.I).astype(np.int64)
    def write(self, path, name, center, rgba=True):
        P, N, C, I = self.arrays(center[0], center[2])
        if not rgba: C = C[:, :3]
        # winding: the quads above are wound so that (p1-p0) x (p2-p0) points along the outward normal in a RIGHT-handed frame with y up; glTF is right-handed, so nothing to flip
        write_glb(path, {'POSITION': P, 'NORMAL': N, 'TEXCOORD_0': np.zeros((len(P), 2), np.float32), 'COLOR_0': C}, I, name)

def check_winding():
    """quad winding self-test: geometric normal of the first triangle must agree with the stored normal"""
    m = Mesh(); m.box(0, 0, 10, 10, 0, 10, [.5, .5, .5]); P, N, C, I = m.arrays(); bad = 0
    for t in range(0, len(I), 3):
        a, b, c = P[I[t]], P[I[t + 1]], P[I[t + 2]]; g = np.cross(b - a, c - a)
        if np.dot(g, N[I[t]]) <= 0: bad += 1
    return bad

rng = np.random.default_rng(1010)
files = []          # [{'name','file','center','mat'}]
stats = {}
def tile_key(x, z, cell=1500.0): return (int(math.floor(x / cell)), int(math.floor(z / cell)))
def flush(meshes, prefix, mat, cell=1500.0):
    for (ix, iz), m in sorted(meshes.items()):
        if not m.n: continue
        cx, cz = (ix + 0.5) * cell, (iz + 0.5) * cell
        name = f'{prefix}__t{ix}_{iz}'; path = os.path.join(OUT, name + '.glb')
        m.write(path, name, (cx, 0, cz))
        files.append({'name': name, 'file': f'mesh/farsky/{name}.glb', 'center': [cx, 0.0, cz], 'mat': mat, 'verts': m.n, 'tris': int(sum(len(i) for i in m.I) // 3)})

# ================================================================ 1. plateau towers (r11: far-LOD facade towers)
# vertex colours in the farCityMass convention (linear, multiplied by MPC FarGain = 4 in M_CityFarMass): AUTHORED albedo 0.22-0.36 = mid-grey concrete / stone / brick / cool glass-grey.
# (the sun-facing luma is scaled down by MPC FarLitK / capped by FarSunK in the material: the test lighting is sun 6 + 2 EV, any lit albedo above ~0.1 clips to white)
GAIN = 4.0
def A(r, g, b): return (r / GAIN, g / GAIN, b / GAIN)
TONES = [A(.30, .30, .31), A(.27, .28, .30), A(.33, .31, .28), A(.31, .27, .23), A(.26, .30, .34), A(.35, .34, .32), A(.24, .25, .27), A(.34, .26, .21)]   # concrete, cool concrete, stone, tan brick, blue-grey, pale stone, graphite, red brick
GLASS = [A(.13, .15, .18), A(.11, .13, .15), A(.16, .17, .19), A(.10, .12, .16)]                                                                           # curtain-wall towers (the shader draws the glass; this is the frame / spandrel tone)
FL_PUNCHED, FL_RIBBON, FL_GLASS, FL_PLAIN = 0.40, 0.62, 0.90, 0.0                                                                                           # window codes read by M_CityFarMass (see its header)
CLUSTERS = [  # name, z centre, z spread, count, h min, h max, supertall count, supertall h range
    ('Weehawken', -700, 260, 14, 60, 135, 0, (0, 0)),
    ('Union City', -1800, 330, 16, 70, 160, 1, (165, 205)),
    ('North Bergen', -2800, 330, 18, 80, 190, 2, (190, 235)),
    ('Fort Lee', -3800, 380, 24, 90, 220, 3, (215, 255)),
    ('Cliffside', -4700, 300, 14, 65, 140, 1, (150, 185)),
]
def rbox(m, cx, cz, w, d, ang, y0, y1, col, flag, col_top=None):
    """box turned by ang (rad) about its centre: sides + top (a chamfer overlay: the tower reads as an octagon from far away)"""
    ca, sa = math.cos(ang), math.sin(ang)
    def R(px, pz): dx, dz = px - cx, pz - cz; return (cx + dx * ca - dz * sa, cz + dx * sa + dz * ca)
    c = [R(cx - w / 2, cz - d / 2), R(cx + w / 2, cz - d / 2), R(cx + w / 2, cz + d / 2), R(cx - w / 2, cz + d / 2)]
    cs = list(col[:3]) + [flag]; ct = list((col_top or col)[:3]) + [0.0]
    for i in range(4):
        a, b = c[i], c[(i + 1) % 4]; n = np.array([b[1] - a[1], 0.0, -(b[0] - a[0])]); n /= np.linalg.norm(n)
        mid = np.array([(a[0] + b[0]) / 2 - cx, 0.0, (a[1] + b[1]) / 2 - cz])
        if np.dot(n, mid) < 0: n = -n
        m.quad([[a[0], y0, a[1]], [b[0], y0, b[1]], [b[0], y1, b[1]], [a[0], y1, a[1]]], n, cs)
    m.quad([[p[0], y1, p[1]] for p in c], [0, 1, 0], ct)
def tone(rg, glass=False):
    t = (GLASS if glass else TONES)[rg.integers(len(GLASS) if glass else len(TONES))]
    k = rg.uniform(0.92, 1.08); return (t[0] * k, t[1] * k, t[2] * k)
def crown(m, x, z, w, d, y1, h, rg, t, fl):
    """top of a tower: stepped pyramid / mechanical penthouse / spire; returns the final y"""
    r = rg.random()
    if r < 0.34:   # stepped deco crown: 2-3 shrinking tiers
        cw, cd = w, d
        for k in range(int(rg.integers(2, 4))):
            cw *= rg.uniform(0.62, 0.78); cd *= rg.uniform(0.62, 0.78); ch = max(4.0, h * rg.uniform(0.045, 0.085))
            m.box(x - cw / 2, z - cd / 2, x + cw / 2, z + cd / 2, y1, y1 + ch, t, t, FL_PUNCHED if fl != FL_GLASS else FL_GLASS); y1 += ch
    elif r < 0.62:  # penthouse + mechanical box
        pw, pd, ph = w * rg.uniform(0.5, 0.72), d * rg.uniform(0.5, 0.72), rg.uniform(5, 11)
        m.box(x - pw / 2, z - pd / 2, x + pw / 2, z + pd / 2, y1, y1 + ph, t, t, FL_PLAIN); y1 += ph
        bw, bd = pw * rg.uniform(0.3, 0.5), pd * rg.uniform(0.3, 0.5)
        m.box(x - w * 0.12 - bw / 2, z + d * 0.08 - bd / 2, x - w * 0.12 + bw / 2, z + d * 0.08 + bd / 2, y1, y1 + rg.uniform(3, 6), A(.20, .20, .21), A(.20, .20, .21), FL_PLAIN)
    elif r < 0.80:  # flat roof with a parapet band and a lift core
        m.box(x - w * 0.18, z - d * 0.18, x + w * 0.18, z + d * 0.18, y1, y1 + rg.uniform(4, 8), A(.28, .28, .29), A(.24, .24, .25), FL_PLAIN); y1 += 5
    if h > 95 and rg.random() < 0.34:   # spire / mast
        s_ = rg.uniform(1.6, 3.0); sh = rg.uniform(22, 62); m.box(x - s_, z - s_, x + s_, z + s_, y1, y1 + sh, A(.2, .2, .21), A(.2, .2, .21), FL_PLAIN); y1 += sh
    return y1
def tower(m, x, z, w, d, h, rg):
    kind = rg.choice(['deco', 'slab', 'twin', 'glass', 'block'], p=[0.24, 0.30, 0.14, 0.20, 0.12])
    if h < 75 and kind in ('twin', 'deco'): kind = 'block'
    pod = rg.uniform(14, 26); pt = tone(rg)
    m.box(x - w * 0.62, z - d * 0.62, x + w * 0.62, z + d * 0.62, PAL_Y, PAL_Y + pod, pt, pt, FL_PUNCHED if rg.random() < 0.7 else FL_RIBBON)
    y0 = PAL_Y + pod
    if kind == 'deco':        # three-tier stepped shaft (setbacks at ~55 % and ~80 % of the height)
        t1 = tone(rg); t2 = tone(rg); fl = FL_PUNCHED if rg.random() < 0.75 else FL_RIBBON
        yb = PAL_Y + h * 0.55; yc = PAL_Y + h * 0.80
        m.box(x - w / 2, z - d / 2, x + w / 2, z + d / 2, y0, yb, t1, t1, fl)
        m.box(x - w * 0.39, z - d * 0.39, x + w * 0.39, z + d * 0.39, yb, yc, t2, t2, fl)
        m.box(x - w * 0.27, z - d * 0.27, x + w * 0.27, z + d * 0.27, yc, PAL_Y + h, t2, t2, fl)
        crown(m, x, z, w * 0.54, d * 0.54, PAL_Y + h, h, rg, t2, fl)
    elif kind == 'slab':      # one shaft, one setback tier, a crown; some get a 45-degree chamfer overlay (octagonal read)
        t1 = tone(rg); fl = FL_RIBBON if rg.random() < 0.4 else FL_PUNCHED; ys = PAL_Y + h * rg.uniform(0.72, 0.86)
        m.box(x - w / 2, z - d / 2, x + w / 2, z + d / 2, y0, ys, t1, t1, fl)
        if rg.random() < 0.4: rbox(m, x, z, w * 0.82, d * 0.82, math.pi / 4, y0, ys + 2, t1, fl)
        t2 = tone(rg)
        m.box(x - w * 0.36, z - d * 0.36, x + w * 0.36, z + d * 0.36, ys, PAL_Y + h, t2, t2, fl)
        crown(m, x, z, w * 0.72, d * 0.72, PAL_Y + h, h, rg, t2, fl)
    elif kind == 'twin':      # two shafts side by side, different heights, a link band
        t1 = tone(rg); t2 = tone(rg); fl = FL_PUNCHED if rg.random() < 0.6 else FL_RIBBON
        ax = rg.random() < 0.5; off = (w if ax else d) * 0.27; ww, dd = (w * 0.46, d) if ax else (w, d * 0.46)
        c1 = (x - off, z) if ax else (x, z - off); c2 = (x + off, z) if ax else (x, z + off)
        h2 = h * rg.uniform(0.62, 0.84)
        m.box(c1[0] - ww / 2, c1[1] - dd / 2, c1[0] + ww / 2, c1[1] + dd / 2, y0, PAL_Y + h, t1, t1, fl)
        m.box(c2[0] - ww / 2, c2[1] - dd / 2, c2[0] + ww / 2, c2[1] + dd / 2, y0, PAL_Y + h2, t2, t2, fl)
        m.box(x - w * 0.5, z - d * 0.5, x + w * 0.5, z + d * 0.5, y0 + (h2 - pod) * 0.55, y0 + (h2 - pod) * 0.7, A(.2, .2, .22), A(.2, .2, .22), FL_PLAIN)
        crown(m, c1[0], c1[1], ww, dd, PAL_Y + h, h, rg, t1, fl)
    elif kind == 'glass':     # wide curtain-wall slab with fins, flat mechanical top
        tg = tone(rg, True); ww, dd = (w * 1.25, d * 0.62) if rg.random() < 0.5 else (w * 0.62, d * 1.25)
        m.box(x - ww / 2, z - dd / 2, x + ww / 2, z + dd / 2, y0, PAL_Y + h * 0.92, tg, tg, FL_GLASS)
        m.box(x - ww * 0.4, z - dd * 0.4, x + ww * 0.4, z + dd * 0.4, PAL_Y + h * 0.92, PAL_Y + h, tg, tg, FL_GLASS)
        crown(m, x, z, ww * 0.8, dd * 0.8, PAL_Y + h, h, rg, A(.22, .22, .24), FL_PLAIN)
    else:                      # brick / stone block with a flat top and a water-tank box
        t1 = tone(rg); fl = FL_PUNCHED
        hb = h * rg.uniform(0.55, 0.8)
        m.box(x - w / 2, z - d / 2, x + w / 2, z + d / 2, y0, PAL_Y + hb, t1, t1, fl)
        m.box(x - w * 0.2, z - d * 0.2, x + w * 0.2, z + d * 0.2, PAL_Y + hb, PAL_Y + hb + rg.uniform(5, 9), A(.26, .22, .19), A(.2, .2, .2), FL_PLAIN)
def plateau_towers():
    meshes = {}; placed = []; rg = np.random.default_rng(2024)
    tot = 0
    for name, zc, zs, n, h0, h1, ns, hs in CLUSTERS:
        todo = [(False, 0, 0)] * n + [(True, hs[0], hs[1])] * ns
        for sup, a, b in todo:
            for _ in range(40):
                z = float(np.clip(zc + rg.normal(0, zs), -5100, 1000))
                off = 38 + 400 * rg.random() ** 1.7
                w, d = rg.uniform(26, 54), rg.uniform(26, 54)
                x = cliff_x(z) - off - w / 2
                if any(abs(x - px) < (w + pw) / 2 + 14 and abs(z - pz) < (d + pd) / 2 + 14 for px, pz, pw, pd in placed): continue
                h = rg.uniform(a, b) if sup else h0 + (h1 - h0) * rg.random() ** 1.6
                m = meshes.setdefault(tile_key(x, z), Mesh()); tower(m, x, z, w, d, h, np.random.default_rng(int(abs(x) * 7 + abs(z) * 13))); placed.append((x, z, w, d)); tot += 1; break
    flush(meshes, 'farsky_towers', 'towers')
    stats['plateau_towers'] = tot
    return placed
PLACED = plateau_towers()

# ================================================================ 1b. plateau fabric (r11): a carpet of mid-rise blocks on the Palisades plateau
# The S4 rows 165-230 look over the plateau at 2.5-8 km. Between the browser's farCityMass blocks and the hinterland boxes the ground was bare fogged land (Y ~ the sky), which made up
# most of the 'pixels above Y 204' of the critic's far-band test. The carpet is M_CityFarMass with the same window codes / authored mid-grey tones as the towers; cells grow with distance
# (64 m next to the cliff -> ~150 m at 4.8 km inland: blocks stay ~8-12 px wide on screen), heights follow smooth 'district' noise (lognormal, taller near the cliff).
def fabric():
    meshes = {}; rg = np.random.default_rng(909); n = 0; tris0 = 0
    u = 56.0
    while u < 4800.0:   # the plateau (y = 58 m) ends at x = -7000 (farshore.js PALISADES)
        cs = 64.0 + 0.018 * u
        z = -5050.0
        while z < 900.0:
            if rg.random() < 0.20: z += cs; continue
            zc = z + rg.uniform(-0.2, 0.2) * cs; uc = u + rg.uniform(-0.2, 0.2) * cs
            w, d = cs * rg.uniform(0.46, 0.80), cs * rg.uniform(0.46, 0.80)
            xc = cliff_x(zc) - uc - w / 2
            hood = float(vnoise(xc / 700.0, zc / 700.0, 21)); hood2 = float(vnoise(xc / 190.0, zc / 190.0, 22))
            h = float(np.clip(math.exp(rg.normal(math.log(25.0), 0.5)) * (0.65 + 1.5 * hood) * (1.0 + 0.5 * hood2) * (1.5 if uc < 700 else 1.0), 9.0, 150.0))
            if any(abs(xc - px) < (w + pw) / 2 + 6 and abs(zc - pz) < (d + pd) / 2 + 6 for px, pz, pw, pd in PLACED if abs(px - xc) < 400): z += cs; continue
            m = meshes.setdefault(tile_key(xc, zc), Mesh()); t = tone(rg, h > 70 and rg.random() < 0.4)
            glass = h > 70 and rg.random() < 0.35
            fl = FL_GLASS if glass else (FL_RIBBON if rg.random() < 0.18 else FL_PUNCHED)
            if h > 46 and rg.random() < 0.6:   # podium + setback shaft
                ph = h * rg.uniform(0.25, 0.4); m.box(xc - w / 2, zc - d / 2, xc + w / 2, zc + d / 2, PAL_Y, PAL_Y + ph, t, t, FL_PUNCHED)
                t2 = tone(rg, glass); m.box(xc - w * 0.38, zc - d * 0.38, xc + w * 0.38, zc + d * 0.38, PAL_Y + ph, PAL_Y + h, t2, t2, fl)
            else:
                m.box(xc - w / 2, zc - d / 2, xc + w / 2, zc + d / 2, PAL_Y, PAL_Y + h, t, A(.22, .22, .23), fl)
            n += 1; z += cs
        u += cs
    flush(meshes, 'farsky_fabric', 'fabric')
    stats['fabric_blocks'] = n
if os.environ.get('FAR_FABRIC', '1') != '0': fabric()

# ================================================================ 2. hinterland skyline (items in the exporter's hinterland.json format)
# camera of S4 (city_shots.json): used only to PLACE clusters at chosen screen columns; the clusters stay in the world for every other view
S4_POS = np.array([182, 306, -92.0]); S4_TGT = np.array([-120, 150, -470.0]); S4_FOV = 75.0
def s4_ray(px):
    f = S4_TGT - S4_POS; f /= np.linalg.norm(f); r = np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r)
    a = (px - 960) / ((1920 / 2) / math.tan(math.radians(S4_FOV / 2)))
    d = f + a * r; d[1] = 0; return d / np.linalg.norm(d)
HIN = []   # [x, y, z, sx, sy, sz, rot, wall rgb, roof rgb]
def hin_box(x, z, w, d, h, wall, roof, rot=0.0): HIN.append([x, 0.7, z, w, h, d, rot, *wall, *roof])
# (r11) authored albedo 0.22-0.36 (mid-grey stone / concrete / brick / cool glass-grey / graphite); 8 + 4 entries, the same counts as r10 so the layout RNG draws are unchanged
HWALL = [(0.30, 0.30, 0.31), (0.26, 0.27, 0.29), (0.33, 0.31, 0.28), (0.22, 0.24, 0.28), (0.35, 0.33, 0.30), (0.31, 0.26, 0.22), (0.20, 0.23, 0.27), (0.36, 0.35, 0.34)]
HROOF = [(0.27, 0.27, 0.28), (0.31, 0.30, 0.29), (0.23, 0.23, 0.25), (0.34, 0.33, 0.31)]
FP = (1920 / 2) / math.tan(math.radians(S4_FOV / 2))
def top_to_height(y_top, D):
    """height (m above the ground at y = 0.7) that puts a roof at screen row y_top of the S4 view at horizontal distance D (camera altitude 306 m, horizon row ~136)"""
    return 306.0 - (y_top - 136.0) * D / FP
def hinterland():
    """skyline by design: the S4 columns 0..1560 are cut into regimes (downtown / mid-rise / gap) and filled with buildings whose roofs land on a chosen screen row (the far sprawl keeps the rest).
    (r11) crown / setback variation: every building over 70 m gets 1-3 shrinking tiers (own RNG, the placement draws are the r10 ones), 22 % are turned 8-35 degrees so two faces catch different light,
    tall ones get a stepped top or a slender mast."""
    rg = np.random.default_rng(777); rc = np.random.default_rng(4141); n = 0
    x = -40.0; bands = []
    while x < 1580:
        kind = rg.choice(['down', 'mid', 'gap'], p=[0.42, 0.36, 0.22]); w = {'down': rg.uniform(110, 250), 'mid': rg.uniform(80, 190), 'gap': rg.uniform(40, 120)}[kind]
        bands.append((kind, x, x + w)); x += w
    # (r11, critic r10 T4: 'in (540,110,900,260) 25 % of the 8x8 blocks are bright and flat'): 120 of the 197 flat bright blocks of the r10 frame were SKY above a low skyline (rows 110-135, Y 229, std < 1),
    # which no material can texture. The central columns 500-940 are now one downtown cluster (taller roofs, rows 98-150) so towers, not sky, fill the top of the critic's box.
    bands = [(('down' if (xb > 500 and xa < 940) else kind), xa, xb) for kind, xa, xb in bands]
    landmarks = 0
    def stack(cx, cz, wd, dp, h, wall, roof, rot):
        """body + 1-3 setback tiers + optional top; returns the number of boxes added"""
        k = 0; hin_box(cx, cz, wd, dp, h, wall, roof, rot); k += 1
        if h < 70: return k
        ntier = int(rc.choice([0, 1, 2, 3], p=[0.16, 0.38, 0.30, 0.16])); y = h; w_, d_ = wd, dp
        for t in range(ntier):
            w_ *= rc.uniform(0.58, 0.8); d_ *= rc.uniform(0.58, 0.8); th = h * rc.uniform(0.05, 0.14) * (1.0 if t == 0 else 0.8)
            wall_t = tuple(float(np.clip(c * rc.uniform(0.85, 1.12), 0.12, 0.42)) for c in wall)
            hin_box(cx, cz, w_, d_, th, wall_t, roof, rot); HIN[-1][1] = 0.7 + y; y += th; k += 1
        if h > 150 and rc.random() < 0.55:   # slender mast / spire on the last tier
            m_ = max(5.0, w_ * 0.12); hin_box(cx, cz, m_, m_, h * rc.uniform(0.09, 0.2), (0.2, 0.2, 0.22), (0.2, 0.2, 0.22), rot); HIN[-1][1] = 0.7 + y; k += 1
        return k
    for kind, xa, xb in bands:
        if kind == 'gap': continue
        px = xa
        while px < xb:
            bw = rg.uniform(7, 20)                        # screen width of one building (px)
            D = rg.uniform(5000, 9800) if kind == 'down' else rg.uniform(5000, 12500)
            y_t = rg.uniform(136, 163) if kind == 'down' else rg.uniform(160, 184)
            central = kind == 'down' and 500 < px < 940
            if central: y_t = rg.uniform(100, 148)                                    # (r11) the central downtown cluster rises well above the horizon row (136)
            if kind == 'down' and rg.random() < 0.10: y_t = rg.uniform(124, 140) if not central else rg.uniform(92, 118)     # a spire / supertall
            h = float(np.clip(top_to_height(y_t, D), 28, 560))
            d0 = s4_ray(px + bw / 2); c = S4_POS[[0, 2]] + d0[[0, 2]] * D
            wd = max(24.0, bw * D / FP * rg.uniform(0.8, 1.1)); dp = wd * rg.uniform(0.8, 1.3)
            wall = HWALL[rg.integers(len(HWALL))]; roof = HROOF[rg.integers(len(HROOF))]
            rot = float(rc.uniform(0.14, 0.6) * rc.choice([-1, 1])) if rc.random() < 0.22 else 0.0
            n += stack(c[0], c[1], wd, dp, h, wall, roof, rot)
            if h > 120 and rg.random() < 0.6: pass    # (the r10 crown draw is kept so the RNG sequence is unchanged; crowns come from stack())
            if h > 300 and rg.random() < 0.7: landmarks += 1
            # neighbours of lower height behind / beside (cluster depth)
            for _ in range(rg.integers(0, 3)):
                D2 = D * rg.uniform(0.9, 1.25); c2 = S4_POS[[0, 2]] + s4_ray(px + bw / 2 + rg.uniform(-0.6, 0.6) * bw)[[0, 2]] * D2
                h2 = h * rg.uniform(0.3, 0.8)
                n += stack(c2[0], c2[1], wd * rg.uniform(0.8, 1.3), dp * rg.uniform(0.8, 1.2), max(24.0, h2), HWALL[rg.integers(len(HWALL))], HROOF[rg.integers(len(HROOF))], 0.0)
            px += bw * rg.uniform(0.9, 1.5)
    # (r11) backdrop row of the central cluster: a second, farther row of supertall towers (8-11 km, roofs on rows 98-120) behind the gaps of the first row, so the top rows of the critic's box (110-125)
    # are towers instead of sky (the 43 'flat bright' blocks of the first r11 frame were the sky between the tower tops)
    rb = np.random.default_rng(5151); px = 500.0
    while px < 960:
        bw = rb.uniform(11, 22); D = rb.uniform(8000, 11000); y_t = rb.uniform(98, 120)
        h = float(np.clip(top_to_height(y_t, D), 28, 620)); d0 = s4_ray(px + bw / 2); c = S4_POS[[0, 2]] + d0[[0, 2]] * D
        wd = max(24.0, bw * D / FP * rb.uniform(0.9, 1.15)); dp = wd * rb.uniform(0.8, 1.2)
        n += stack(c[0], c[1], wd, dp, h, HWALL[rb.integers(len(HWALL))], HROOF[rb.integers(len(HROOF))], 0.0)
        px += bw * rb.uniform(0.85, 1.25)
    stats['hinterland_boxes'] = n; stats['hinterland_landmarks'] = landmarks
hinterland()

# ================================================================ 3. bluff (displaced Palisades face)
def bluff():
    # one continuous strip along the polyline PAL (z increasing), 14 m columns, 24 rows
    pts = PAL.copy()
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
    ns = int(s[-1] / 12.0)
    ss = np.linspace(0, s[-1], ns + 1)
    X = np.interp(ss, s, pts[:, 0]); Z = np.interp(ss, s, pts[:, 1])
    tx = np.gradient(X, ss); tz = np.gradient(Z, ss); L = np.hypot(tx, tz); tx /= L; tz /= L
    nx, nz = tz, -tx                      # normal: face toward +x (river)
    flip = nx < 0; nx = np.where(flip, -nx, nx); nz = np.where(flip, -nz, nz)
    R = 26; Y = np.concatenate([[0.7], np.linspace(1.5, 12, 7), np.linspace(14, 55, 14), [58.0]])  # heights of the rows
    NR = len(Y)
    # displacement toward the river (+) / into the hill (-)
    Sg, Yg = np.meshgrid(ss, Y, indexing='ij')
    zc = np.interp(Sg, ss, Z)
    talus = 15.0 * np.clip(1 - Yg / 24.0, 0, 1) ** 1.5
    led = vnoise(Yg / 8.5, zc / 90.0, 3)                           # ledge phase
    saw = np.abs(((Yg / 9.0 + 0.35 * led) % 1.0) - 0.5) * 2.0       # 0..1 triangular
    ledge = 4.0 * (sstep(0.0, 1.0, saw) - 0.5) * sstep(6, 16, Yg) * (1 - sstep(48, 58, Yg))
    bay = np.clip(vnoise(zc / 130.0, Yg * 0 + 1.0, 5) - 0.52, 0, None) / 0.48
    bays = -16.0 * bay * sstep(4, 20, Yg) * (1 - sstep(50, 58, Yg))
    head = 7.0 * np.clip(vnoise(zc / 210.0, Yg * 0 + 2.0, 8) - 0.45, 0, None) * sstep(2, 14, Yg) * (1 - sstep(40, 58, Yg))
    rough = 2.2 * (vnoise(zc / 14.0, Yg / 5.0, 9) - 0.5) * sstep(3, 12, Yg) * (1 - sstep(52, 58, Yg))
    off = np.maximum(talus + ledge + bays + head + rough, -14.0)
    off[:, -1] = 0.0; off[:, 0] = np.maximum(off[:, 0], 6.0)                       # brow exactly on the plateau edge, foot a little out in the shallows
    PX = X[:, None] + nx[:, None] * off; PZ = Z[:, None] + nz[:, None] * off; PY = np.broadcast_to(Y[None, :], PX.shape).copy()
    # vegetation fraction: wooded talus + brow, patches on the face (vertex colour R), rock tone G, tree-clump candidates
    veg = np.clip(0.30 + 0.9 * (vnoise(zc / 40.0, Yg / 7.0, 11) - 0.45) + 0.55 * np.clip(1 - Yg / 20.0, 0, 1) + 0.5 * sstep(44, 58, Yg), 0, 1)
    tone = 0.75 + 0.5 * vnoise(zc / 33.0, Yg / 11.0, 12)
    C = np.stack([veg, np.clip(tone, 0, 1), np.ones_like(veg), np.ones_like(veg)], -1)
    P = np.stack([PX, PY, PZ], -1).reshape(-1, 3)
    # normals from the displaced grid
    dPs = np.gradient(np.stack([PX, PY, PZ], -1), axis=0); dPy = np.gradient(np.stack([PX, PY, PZ], -1), axis=1)
    Nn = np.cross(dPy, dPs).reshape(-1, 3)   # (d/dy) x (d/ds): for s along z-ish, y up -> +x
    Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-9)
    ref = np.stack([nx[:, None].repeat(NR, 1), np.zeros((len(ss), NR)), nz[:, None].repeat(NR, 1)], -1).reshape(-1, 3)
    Nn = np.where((Nn * ref).sum(1, keepdims=True) < 0, -Nn, Nn)
    idx = []
    for i in range(len(ss) - 1):
        for j in range(NR - 1):
            a = i * NR + j; b = (i + 1) * NR + j; c = (i + 1) * NR + j + 1; d = i * NR + j + 1
            idx += [a, b, c, a, c, d]
    I = np.array(idx, np.int64).reshape(-1, 3)
    # winding agrees with the outward normal?
    g = np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]]); sgn = (g * Nn[I[:, 0]]).sum(1)
    I[sgn < 0] = I[sgn < 0][:, [0, 2, 1]]
    I = I.reshape(-1)
    # tiles: split the strip by z into 1500 m tiles (separate GLBs, own centre)
    tiles = {}
    cz_of_vert = P[:, 2]; tz_of_tri = np.floor(P[I.reshape(-1, 3)[:, 0], 2] / 1500.0).astype(int)
    for t in np.unique(tz_of_tri):
        sel = I.reshape(-1, 3)[tz_of_tri == t]; used = np.unique(sel); remap = -np.ones(len(P), np.int64); remap[used] = np.arange(len(used))
        cx, cz = -1900.0, (t + 0.5) * 1500.0
        Pv = P[used].astype(np.float32); Pv[:, 0] -= cx; Pv[:, 2] -= cz
        name = f'farsky_bluff__t0_{t}'
        write_glb(os.path.join(OUT, name + '.glb'), {'POSITION': Pv, 'NORMAL': Nn[used].astype(np.float32), 'TEXCOORD_0': np.zeros((len(used), 2), np.float32), 'COLOR_0': C.reshape(-1, 4)[used].astype(np.float32)}, remap[sel].reshape(-1), name)
        files.append({'name': name, 'file': f'mesh/farsky/{name}.glb', 'center': [cx, 0.0, cz], 'mat': 'bluff', 'verts': int(len(used)), 'tris': int(len(sel))})
    stats['bluff_tris'] = int(len(I) // 3)
    # tree clump candidates on the wooded parts of the face
    cl = []
    Pg = np.stack([PX, PY, PZ], -1)
    for i in range(0, len(ss), 1):
        for j in range(1, NR - 1):
            v = veg[i, j]
            if v < 0.5: continue
            pr = 2.4 * ((0.35 if Y[j] < 20 else 0.18) * (v - 0.4) / 0.6) + (0.55 if Y[j] > 52 else 0.0)   # (r10 second pass: the first render showed the face as a bare grey-blue band between the tree lines)
            if rng.random() > pr: continue
            p = Pg[i, j] + np.array([nx[i], 0, nz[i]]) * 1.0
            cl.append([p[0] + rng.uniform(-4, 4), p[1], p[2] + rng.uniform(-4, 4), rng.uniform(3.2, 6.8) * (1.0 if Y[j] < 52 else 1.3), rng.uniform(0.7, 1.15), rng.uniform(0.45, 0.8)])
    return cl
CLUMPS = bluff()
stats['bluff_clumps'] = len(CLUMPS)

# brow trees (plateau side of the lip) and talus-foot trees
for i in range(len(PAL) - 1):
    (ax, az), (bx, bz) = PAL[i], PAL[i + 1]; L = math.hypot(bx - ax, bz - az)
    for u in np.arange(0, L, 7.0):
        t = u / L; x = ax + (bx - ax) * t; z = az + (bz - az) * t
        wb = math.sin(z * 0.019 + 0.4) + 0.7 * math.sin(z * 0.047 + 2.2) + 0.4 * math.sin(z * 0.11)
        if rng.random() < (0.9 if wb > 0.3 else 0.5 if wb > -0.4 else 0.16):
            CLUMPS.append([x - rng.uniform(2, 30), PAL_Y, z + rng.uniform(-5, 5), rng.uniform(3.4, 6.2), rng.uniform(0.75, 1.15), rng.uniform(0.5, 0.8)])
stats['clumps_after_brow'] = len(CLUMPS)

# ================================================================ 4. shoreline: seawall, cap, promenade, piers, tree row
def shoreline():
    meshes = {}
    z_lo, z_hi = -5100.0, 2300.0
    zs = np.arange(z_lo, z_hi, 25.0)
    wall_dark = (0.07, 0.072, 0.075); cap = (0.26, 0.255, 0.245); prom = (0.27, 0.265, 0.25); pave = (0.19, 0.19, 0.19)
    # edge normal (toward the river, +x): the shore runs along z, so n ~ (1, 0, -dx/dz)
    def edge(z):
        x = shore_x(z); dx = shore_x(z + 5) - shore_x(z - 5); n = np.array([1.0, -dx / 10.0]); n /= np.linalg.norm(n); return x, n
    for z in zs:
        x0, n0 = edge(z); x1, n1 = edge(z + 25.0)
        m = meshes.setdefault(tile_key(x0, z), Mesh())
        a = np.array([x0 + 0.8 * n0[0], z + 0.8 * n0[1]]); b = np.array([x1 + 0.8 * n1[0], z + 25.0 + 0.8 * n1[1]])
        # seawall face (toward the river)
        m.quad([[a[0], WATER_Y - 0.3, a[1]], [b[0], WATER_Y - 0.3, b[1]], [b[0], FAR_Y + 1.5, b[1]], [a[0], FAR_Y + 1.5, a[1]]], [n0[0], 0, n0[1]], list(wall_dark) + [1])
        # cap (2 m wide strip on top of the wall)
        ai = a - n0 * 2.0; bi = b - n1 * 2.0
        m.quad([[ai[0], FAR_Y + 1.5, ai[1]], [bi[0], FAR_Y + 1.5, bi[1]], [b[0], FAR_Y + 1.5, b[1]], [a[0], FAR_Y + 1.5, a[1]]], [0, 1, 0], list(cap) + [1])
        # promenade 13 m wide, slightly above the far-land slab, pale pavers
        aj = a - n0 * 15.0; bj = b - n1 * 15.0
        m.quad([[aj[0], FAR_Y + 0.35, aj[1]], [bj[0], FAR_Y + 0.35, bj[1]], [bi[0], FAR_Y + 0.35, bi[1]], [ai[0], FAR_Y + 0.35, ai[1]]], [0, 1, 0], list(prom if (int(z) // 25) % 2 == 0 else pave) + [1])
        # (quads above are wound for a top view where +x is east, +z south, normal +y: p0 -> p1 along +z, p3 -> p0 toward the river = +x ... checked below by check_winding_quads)
    # piers where the browser's piers stop (z < -2600): perpendicular to the shore, 28-42 m wide, 90-200 m long, 70 % with a long shed
    rg = np.random.default_rng(31)
    z = -5000.0; npier = 0
    while z < -2650:
        x0, n0 = edge(z); w = rg.uniform(28, 42); ln = rg.uniform(90, 200); tdir = np.array([-n0[1], n0[0]])  # along the shore
        c0 = np.array([x0, z]); p = [c0 + tdir * (-w / 2) + n0 * 0.5, c0 + tdir * (w / 2) + n0 * 0.5, c0 + tdir * (w / 2) + n0 * ln, c0 + tdir * (-w / 2) + n0 * ln]
        m = meshes.setdefault(tile_key(x0, z), Mesh())
        yd = 2.4
        for k in range(4):   # dark fascia (piles) on the three seaward sides
            a, b = p[k], p[(k + 1) % 4]
            if k == 0 and False: continue
            nn = np.array([b[1] - a[1], -(b[0] - a[0])]); nn /= np.linalg.norm(nn)
            m.quad([[a[0], WATER_Y - 0.3, a[1]], [b[0], WATER_Y - 0.3, b[1]], [b[0], yd, b[1]], [a[0], yd, a[1]]], [nn[0], 0, nn[1]], [0.10, 0.10, 0.105, 1])
        m.quad([[p[0][0], yd, p[0][1]], [p[1][0], yd, p[1][1]], [p[2][0], yd, p[2][1]], [p[3][0], yd, p[3][1]]], [0, 1, 0], [0.20, 0.197, 0.19, 1])
        if rg.random() < 0.72:
            sw = w * rg.uniform(0.55, 0.78); sl = ln * rg.uniform(0.62, 0.86); sh = rg.uniform(9, 14)
            q0 = c0 + n0 * (ln * 0.1 + 6)
            wall = [(0.20, 0.205, 0.22, 1), (0.25, 0.15, 0.11, 1), (0.25, 0.245, 0.23, 1), (0.15, 0.18, 0.21, 1)][rg.integers(4)]
            roof = [0.14, 0.14, 0.15, 1]
            # shed body (axis-aligned footprint approximation: the shore is nearly N-S, so the pier points along +x)
            xa, xb = q0[0], q0[0] + sl * abs(n0[0]); za, zb = q0[1] - sw / 2, q0[1] + sw / 2
            m.box(xa, za, xb, zb, yd, yd + sh, wall[:3], roof[:3], 0.0)
            m.box(xa + 1, za + sw * 0.28, xb - 1, zb - sw * 0.28, yd + sh, yd + sh + 3.2, roof[:3], roof[:3], 0.0)   # ridge
        npier += 1; z += rg.uniform(150, 240)
    stats['new_piers'] = npier
    flush(meshes, 'farsky_shore', 'shore')
    # tree row on the promenade
    rg = np.random.default_rng(32); nt = 0
    for z in np.arange(z_lo, z_hi, 17.0):
        x0, n0 = edge(z + rg.uniform(-4, 4))
        c = np.array([x0, z]) - n0 * rg.uniform(7, 12)
        CLUMPS.append([c[0], FAR_Y + 0.3, c[1], rg.uniform(2.6, 4.2), rg.uniform(0.9, 1.3), rg.uniform(0.35, 0.6)]); nt += 1
    stats['promenade_trees'] = nt
shoreline()

# ================================================================ 5. trees on the lawns of the far-land ground map (farshore.js bakes parks / lawns / yards in it; no canopy is exported)
def lawn_trees():
    from PIL import Image
    mp = os.path.join(EXPORT, 'farland_map.png')
    if not os.path.exists(mp): stats['lawn_trees'] = 0; return
    a = np.asarray(Image.open(mp).convert('RGB')).astype(int)
    MAPX0, MAPZ0, PX = -6000.0, -7600.0, 5.0
    rg = np.random.default_rng(55); n = 0
    for z in np.arange(-5200.0, 2500.0, 11.0):
        for x in np.arange(-3300.0, -1300.0, 11.0):
            if x > shore_x(z) - 14: continue
            ix = int((x - MAPX0) / PX); iz = int((z - MAPZ0) / PX)
            if not (0 <= iz < a.shape[0] and 0 <= ix < a.shape[1]): continue
            r, g, b = a[iz, ix]; gr = g - max(r, b)
            if gr < 6: continue
            if rg.random() > min(1.0, 0.18 + gr / 30.0): continue
            y = PAL_Y if x < cliff_x(z) else FAR_Y
            CLUMPS.append([x + rg.uniform(-5, 5), y, z + rg.uniform(-5, 5), rg.uniform(3.0, 5.6), rg.uniform(0.8, 1.2), rg.uniform(0.3, 0.7)]); n += 1
    stats['lawn_trees'] = n
lawn_trees()

# ================================================================ clump proto: a lumpy ellipsoid (radius 1, height 1.25, sitting on y = 0), 80 triangles
def clump_proto():
    t = (1 + 5 ** 0.5) / 2
    V = np.array([[-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0], [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t], [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]], float)
    F = [[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11], [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8], [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9], [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]]
    V /= np.linalg.norm(V, axis=1, keepdims=True)
    # one midpoint subdivision -> 80 faces
    verts = [v for v in V]; cache = {}
    def mid(i, j):
        k = (min(i, j), max(i, j))
        if k not in cache: v = verts[i] + verts[j]; verts.append(v / np.linalg.norm(v)); cache[k] = len(verts) - 1
        return cache[k]
    F2 = []
    for a, b, c in F:
        ab, bc, ca = mid(a, b), mid(b, c), mid(c, a); F2 += [[a, ab, ca], [b, bc, ab], [c, ca, bc], [ab, bc, ca]]
    V = np.array(verts); rg2 = np.random.default_rng(3)
    V = V * (0.82 + 0.3 * rg2.random(len(V)))[:, None]
    V[:, 1] = V[:, 1] * 0.62 + 0.62; V[:, 1] = np.maximum(V[:, 1], 0.0)   # base on the ground, lumpy top
    F2 = np.array(F2)
    # outward winding
    for k, (a, b, c) in enumerate(F2):
        g = np.cross(V[b] - V[a], V[c] - V[a]); ctr = (V[a] + V[b] + V[c]) / 3 - np.array([0, 0.62, 0])
        if np.dot(g, ctr) < 0: F2[k] = [a, c, b]
    N = V - np.array([0, 0.5, 0]); N /= np.linalg.norm(N, axis=1, keepdims=True)
    write_glb(os.path.join(POUT, 'farsky_clump.glb'), {'POSITION': V.astype(np.float32), 'NORMAL': N.astype(np.float32), 'TEXCOORD_0': np.zeros((len(V), 2), np.float32), 'COLOR_0': np.ones((len(V), 4), np.float32)}, F2.reshape(-1), 'farsky_clump')
    stats['clump_tris'] = int(len(F2))
clump_proto()

# ================================================================ manifest
CL = np.array(CLUMPS); CL[:, 4] *= 1.9   # height scale of the unit blob (radius 1, height 1.24): crowns 7-25 m tall
json.dump({'note': 'P1 city r10 far skyline (tools/export/far_skyline.py)', 'files': files, 'clumps': np.round(CL, 2).tolist(), 'hinterland': np.round(np.array(HIN), 3).tolist(),
           'clump_proto': 'proto/farsky_clump.glb', 'stats': stats}, open(os.path.join(EXPORT, 'farsky.json'), 'w'))
print('winding self-test, bad triangles:', check_winding())
print(json.dumps(stats, indent=1)); print(len(files), 'glb files,', len(CLUMPS), 'clumps,', len(HIN), 'hinterland boxes')
