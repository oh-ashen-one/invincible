#!/usr/bin/env python3
"""Tree-shadow depth on the lawn, located geometrically (r05 target 4: every isolated tree in p4 casts a lawn shadow <= 0.6 x the lit lawn luma). CPU only.
Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

For every park tree of the browser export (pools trees-{park,elm,conifer}-near: position, scale) that is ISOLATED (no other tree within --iso m), its crown shadow on the
ground is predicted from the golden rig's sun (look_presets.json golden: elevation / azimuth) and the crown's height range (the near-card mesh bounds x instance scale):
the shadow core = ground points P + t * d_shadow, t in [(cy - 0.4 r) / tan(elev), (cy + 0.4 r) / tan(elev)] x s, lateral offsets within +-0.35 r s.
The lit reference = the same along-range at lateral offsets +-(r s + 4 .. 10 m). Every sample point is projected into the still with the shot camera (shots.json: pos / target /
horizontal fov, 3840 x 2160) and kept only if (a) it is not inside ANY tree's predicted shadow core (for the lit set), (b) the camera ray to it does not pass through any crown
sphere (no crown in front), (c) it is off the park paths (pathmask G), (d) the pixel is lawn-coloured (G >= 0.75 R, G >= 2 B). ratio = median luma(core) / median luma(lit),
reported per tree with >= 12 valid samples in each set.
usage: tree_shadow_auto.py <still.jpg> <shot id> <out.json> [--iso 25] [--preview out.jpg]"""
import sys, json, math, os
import numpy as np
from PIL import Image, ImageDraw
args = sys.argv[1:]
def opt(k, d):
    if k in args: i = args.index(k); v = args[i + 1]; del args[i:i + 2]; return v
    return d
ISO = float(opt('--iso', '25')); PREVIEW = opt('--preview', None)
still, shot_id, out = args[:3]
WT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SCR = '/Users/midir/sm2-n1/_scratch/terrain'
TJ = json.load(open(os.path.join(SCR, 'export', 'terrain.json')))
shot = [s for s in json.load(open(os.path.join(WT, 'docs/night1/terrain/shots.json')))['shots'] if s['id'] == shot_id][0]
P = json.load(open(os.path.join(WT, 'unreal/WebHomage/Scripts/look_presets.json')))
G = (P.get('golden') or P['presets']['golden'])['sun']
el, az = math.radians(G['elev']), math.radians(G['az'])
# browser frame: x east, y up, z south (north = -z). Direction TO the sun, horizontal: (sin az, -cos az); shadows run the opposite way.
dsh = np.array([-math.sin(az), math.cos(az)])          # (x, z) per metre, away from the sun
tanE = math.tan(el)
# crown height ranges of the near-card meshes (y min / max of tools/export prototypes, metres before the instance scale)
CROWN = {'park': (3.83, 14.80, 5.5), 'elm': (6.14, 18.34, 6.4), 'conifer': (1.33, 12.43, 4.2)}
trees = []
for kind in CROWN:
    for it in TJ['instances'].get('trees-%s-near' % kind, {}).get('items', []):
        s = it.get('s', 1.0); s3 = it.get('s3') or [1, 1, 1]
        y0, y1, r = CROWN[kind]
        trees.append((it['x'], it['z'], it.get('y', 0.17), s * s3[1] * (y0 + y1) / 2, s * s3[1] * (y1 - y0) / 2, s * max(s3[0], s3[2]) * r, kind))
T = np.array([t[:6] for t in trees]); kinds = [t[6] for t in trees]
# camera (shots.json: UE metres x east, y SOUTH, z up = browser (x, z, y))
cp = np.array([shot['pos'][0], shot['pos'][2], shot['pos'][1]], float); ct = np.array([shot['target'][0], shot['target'][2], shot['target'][1]], float)
f = ct - cp; f /= np.linalg.norm(f); up = np.array([0.0, 1.0, 0.0]); r_ = np.cross(f, up); r_ /= np.linalg.norm(r_); u_ = np.cross(r_, f)
W, H = 3840, 2160; tf = math.tan(math.radians(shot.get('fov', 66)) / 2)
def project(pts):
    d = pts - cp; z = d @ f
    x = W / 2 + (d @ r_) / z / tf * W / 2; y = H / 2 - (d @ u_) / z / tf * W / 2
    return x, y, z
im = np.asarray(Image.open(still).convert('RGB')).astype(np.float32); Y = im @ np.array([0.299, 0.587, 0.114], np.float32)
pm = np.asarray(Image.open(os.path.join(SCR, 'prep', 'pathmask.png')).convert('RGBA')); PM = json.load(open(os.path.join(SCR, 'prep', 'pathmask.json')))
def on_path(x, z):
    i = ((x - PM['x0']) / PM['texel']).astype(int); j = ((z - PM['z0']) / PM['texel']).astype(int)
    ok = (i >= 0) & (j >= 0) & (i < pm.shape[1]) & (j < pm.shape[0])
    g = np.zeros(len(x), bool); g[ok] = pm[j[ok], i[ok], 1] > 20   # M_TerrainPark samples the mask at (p - mo) / ms without a v flip: row = (z - z0) / texel
    return g
def in_any_shadow(x, z):
    # a point is in tree k's shadow core if its offset from the trunk projects onto the shadow axis within the core range and laterally within the crown radius
    dx = x[:, None] - T[None, :, 0]; dz = z[:, None] - T[None, :, 1]
    a = dx * dsh[0] + dz * dsh[1]; l = np.abs(-dx * dsh[1] + dz * dsh[0])
    a0 = (T[:, 3] - T[:, 4]) / tanE; a1 = (T[:, 3] + T[:, 4]) / tanE
    return ((a > a0[None] - 2) & (a < a1[None] + 2) & (l < T[None, :, 5] + 1.5)).any(1)
def occluded(pts):
    # ray camera -> ground point vs every crown sphere (centre at the crown middle, radius r)
    C = np.stack([T[:, 0], T[:, 2] + T[:, 3], T[:, 1]], 1)
    d = pts - cp; L = np.linalg.norm(d, axis=1); dn = d / L[:, None]
    oc = C[None] - cp[None, None]                              # (1, n, 3)
    tca = (oc * dn[:, None, :]).sum(2); d2 = (oc ** 2).sum(2) - tca ** 2
    return ((d2 < (T[None, :, 5] * 0.85) ** 2) & (tca > 0) & (tca < L[:, None] - 1.0)).any(1)
def sample(px, py):
    xi = np.round(px).astype(int); yi = np.round(py).astype(int)
    ok = (xi >= 2) & (yi >= 2) & (xi < W - 2) & (yi < H - 2)
    v = np.full(len(px), np.nan); rgb = np.zeros((len(px), 3))
    for k in np.nonzero(ok)[0]:
        blk = im[yi[k] - 1:yi[k] + 2, xi[k] - 1:xi[k] + 2]; rgb[k] = blk.reshape(-1, 3).mean(0); v[k] = Y[yi[k] - 1:yi[k] + 2, xi[k] - 1:xi[k] + 2].mean()
    lawn = (rgb[:, 1] >= 0.75 * rgb[:, 0]) & (rgb[:, 1] >= 2.0 * rgb[:, 2])
    return v, lawn & ok
# isolated trees
from scipy.spatial import cKDTree
kd = cKDTree(T[:, :2]); nn = kd.query(T[:, :2], k=2)[0][:, 1]
res = []; prev = []
for k in np.nonzero(nn > ISO)[0]:
    x0, z0, gy, cy, hh, rr = T[k]
    a0, a1 = (cy - 0.4 * hh) / tanE, (cy + 0.4 * hh) / tanE
    A = np.linspace(a0, a1, 9)
    core = [(x0 + a * dsh[0] - l * dsh[1], z0 + a * dsh[1] + l * dsh[0]) for a in A for l in np.linspace(-0.35 * rr, 0.35 * rr, 5)]
    lit = [(x0 + a * dsh[0] - l * dsh[1], z0 + a * dsh[1] + l * dsh[0]) for a in A for sgn in (-1, 1) for l in sgn * (rr + np.array([4.0, 6.0, 8.0, 10.0]))]
    out_ = {}
    for nm, pts in (('core', core), ('lit', lit)):
        q = np.array(pts); p3 = np.stack([q[:, 0], np.full(len(q), 0.2), q[:, 1]], 1)
        px, py, pz = project(p3)
        v, ok = sample(px, py)
        ok &= (pz > 1) & ~on_path(q[:, 0], q[:, 1]) & ~occluded(p3)
        if nm == 'lit': ok &= ~in_any_shadow(q[:, 0], q[:, 1])
        out_[nm] = (v[ok], px[ok], py[ok])
    if len(out_['core'][0]) >= 12 and len(out_['lit'][0]) >= 12:
        sc, sl = float(np.median(out_['core'][0])), float(np.median(out_['lit'][0]))
        tx, ty, _ = project(np.array([[x0, gy, z0]]))
        res.append({'tree_xz': [round(x0, 1), round(z0, 1)], 'kind': kinds[k], 'nearest_tree_m': round(float(nn[k]), 1), 'trunk_px': [int(tx[0]), int(ty[0])],
                    'core_n': len(out_['core'][0]), 'lit_n': len(out_['lit'][0]), 'core_luma': round(sc, 1), 'lit_luma': round(sl, 1), 'ratio': round(sc / max(sl, 1e-3), 3)})
        prev.append((out_, tx[0], ty[0]))
r = [p['ratio'] for p in res]
summ = {'still': os.path.basename(still), 'shot': shot_id, 'sun_elev_deg': G['elev'], 'sun_az_deg': G['az'], 'isolation_m': ISO, 'trees_measured': len(r),
        'max_ratio': max(r) if r else None, 'median_ratio': round(float(np.median(r)), 3) if r else None, 'pass_all_le_0.6': bool(r) and max(r) <= 0.6}
json.dump({'summary': summ, 'trees': res}, open(out, 'w'), indent=1)
print(json.dumps(summ))
for p in res: print('tree %-16s %-8s nn %5.1f m  trunk px %-12s core %5.1f (n %2d)  lit %5.1f (n %2d)  ratio %.3f' % (p['tree_xz'], p['kind'], p['nearest_tree_m'], p['trunk_px'], p['core_luma'], p['core_n'], p['lit_luma'], p['lit_n'], p['ratio']))
if PREVIEW:
    pv = Image.open(still).convert('RGB'); dr = ImageDraw.Draw(pv)
    for o, tx, ty in prev:
        for (v, px, py), col in ((o['core'], (255, 0, 255)), (o['lit'], (0, 255, 255))):
            for a, b in zip(px, py): dr.rectangle([a - 3, b - 3, a + 3, b + 3], outline=col)
        dr.ellipse([tx - 10, ty - 10, tx + 10, ty + 10], outline=(255, 255, 0), width=3)
    pv.resize((1920, 1080)).save(PREVIEW, quality=88)
