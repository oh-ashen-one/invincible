"""Crop citizen / fauna atlas tiles to PNG and measure UV coverage per item (system python3: numpy + Pillow).

Fan homage project, not official Marvel/Sony/Insomniac; no affiliation.

  python3 tools/ue_char/eval/tiles.py OUT_DIR STATS_JSON [--export NAME ...]
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
NPC = os.path.join(ROOT, 'public/assets/city/npc')
out, stats_path = sys.argv[1], sys.argv[2]
exp = sys.argv[sys.argv.index('--export') + 1:] if '--export' in sys.argv else []
os.makedirs(out, exist_ok=True)
stats = {}
for pack, key in (('citizens', 'variants'), ('fauna', 'items')):
    m = json.load(open(os.path.join(NPC, pack + '.json')))
    b = open(os.path.join(NPC, pack + '.bin'), 'rb').read()
    im = Image.open(os.path.join(NPC, m['atlas'] + '.webp')).convert('RGB')
    gx, gy = m['grid']
    tw, th = im.size[0] // gx, im.size[1] // gy
    for v in m[key]:
        c, r = v['tile']
        tile = im.crop((c * tw, r * th, (c + 1) * tw, (r + 1) * th))
        tile.save(os.path.join(out, v['name'] + '.png'))
        L = v['lods'][0]
        uv = np.frombuffer(b, np.float32, L['nv'] * 2, L['uv']).reshape(-1, 2)
        idx = np.frombuffer(b, np.uint32 if L.get('idx32') else np.uint16, L['nt'] * 3, L['idx']).reshape(-1, 3)
        pos = np.frombuffer(b, np.float32, L['nv'] * 3, L['pos']).reshape(-1, 3)
        tuv = np.c_[uv[:, 0] * gx - c, uv[:, 1] * gy - r]
        S = 512
        mask = Image.new('L', (S, S), 0)
        d = ImageDraw.Draw(mask)
        for t in idx:
            d.polygon([(float(tuv[k, 0] * S), float(tuv[k, 1] * S)) for k in t], fill=255)
        cov = np.asarray(mask).astype(bool).mean()
        # texel density: tile px per metre, median over triangles
        a3 = np.linalg.norm(np.cross(pos[idx[:, 1]] - pos[idx[:, 0]], pos[idx[:, 2]] - pos[idx[:, 0]]), axis=1) / 2
        u = tuv * tw
        a2 = np.abs(np.cross(u[idx[:, 1]] - u[idx[:, 0]], u[idx[:, 2]] - u[idx[:, 0]])) / 2
        ok = a3 > 1e-9
        dens = np.sqrt(a2[ok] / a3[ok])
        # UV islands via union-find on shared vertex indices (seams split vertices)
        par = list(range(L['nv']))
        def f(x):
            while par[x] != x:
                par[x] = par[par[x]]; x = par[x]
            return x
        for t in idx:
            a, b2, c2 = f(int(t[0])), f(int(t[1])), f(int(t[2]))
            par[b2] = a; par[c2] = a
        isl = len({f(int(i)) for i in idx.ravel()})
        stats[v['name']] = dict(pack=pack, tile_px=[tw, th], atlas=list(im.size), uv_coverage_pct=round(100 * cov, 1),
                                texel_px_per_m_median=round(float(np.median(dens)), 1),
                                texel_p10_p90=[round(float(np.percentile(dens, 10)), 1), round(float(np.percentile(dens, 90)), 1)],
                                uv_islands=isl, verts=L['nv'], tris=L['nt'], height_m=round(float(pos[:, 1].max() - pos[:, 1].min()), 3))
json.dump(stats, open(stats_path, 'w'), indent=1)
for k, v in stats.items():
    print(k, v)
