# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 06 offline CH18 gate for the crowd citizens (no GPU): enclosed see-through pixels and stretch spikes on the crowd's own clips.

  python3 tools/ue_char/eval/eval_r6.py [--legacy] [--ppm 700] [--thin 7] [--yaws 8] [--step 4] [--json OUT] [--imgs DIR] NAME [NAME ...]

For every citizen, its own walk style (CIT_WALK) + idle, every `step`-th frame, `yaws` orthographic views around the vertical axis, single-sided:
  key    = background pixels enclosed by the person mask.  thin = enclosed components that a `thin` px opening removes (cracks, slivers);
           wide = the rest (gaps between limbs, natural).  The engine's key_holes.py uses the same definition.
  spikes = triangles whose worst edge grows by more than 5 cm / 10 cm over the sampled frames (cit_proxy.stretch, top-4 skinning).
--legacy measures the round-05 geometry (crowd pack LOD0, 3 mm expanded triangles, two-layer hull) with the same code, for the before / after.
"""
import json, os, sys
import numpy as np
import cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from p2paths import scr  # noqa: E402
import cit_proxy as CP   # noqa: E402

CIT_WALK = {'03_white_tee': 'walk', '12_sundress_mom': 'walkF', '13_construction_worker': 'walkStroll', '15_executive': 'walkBrisk',
            '04_blue_sweatshirt': 'walkF', '08_black_suit': 'walkBrisk', '10_silver_tie': 'walk', '14_teen_skater': 'walk',
            '18_dapper_elder': 'walkOld', '19_marathon_runner': 'walkBrisk', '01_retired_gent': 'walkOld', '20_punk_artist': 'walkF',
            '02_leather_jacket': 'walk', '05_black_tee': 'walkBrisk', '06_chrome_shades': 'walkStroll', '09_kurta_waistcoat': 'walk',
            '16_lumberjack_hipster': 'walkStroll', '17_hijabi_student': 'walkF'}


def load_r6(name, suffix='_final', cores=True):
    z = np.load(os.path.join(scr('eval', 'refit'), name + suffix + '.npz'))
    tex = np.asarray(Image.open(os.path.join(scr('eval', 'refit'), name + '_tex.png')).convert('RGB').resize((1024, 1024), Image.LANCZOS))
    m = CP.Mesh(z['pos'], z['idx'], z['uv'], z['dense'], tex, name); m.n_garment_tris = len(z['idx'])
    return m


def load_legacy(name):
    import underlayer as U
    pos, tuv, idx, nrm, (si, sw) = U.load(name)
    dense = U.final_weights(pos, nrm, idx, U.dense_weights(pos, si, sw))
    P3, UV3 = U.expand_triangles(pos, idx, tuv, 0.003)
    Pe = P3.reshape(-1, 3); De = dense[idx.reshape(-1)]
    T = np.arange(len(Pe)).reshape(-1, 3)
    H = np.load(os.path.join(scr('eval', 'hull'), name + '.npz'))
    dh = np.einsum('nk,nkb->nb', H['nw'], dense[H['nn']])
    Pall = np.vstack([Pe, H['V']]); Dall = np.vstack([De, dh]); Tall = np.vstack([T, H['T'] + len(Pe)])
    uv = np.vstack([UV3.reshape(-1, 2), np.repeat(H['tri_uv'], 3, axis=0)])
    uv = np.c_[uv[:, 0], 1.0 - uv[:, 1]]
    return CP.Mesh(Pall, Tall, uv, Dall, None, name)


def evaluate(m, name, ppm=700, thin=7, yaws=8, step=4, imgs=None, log=print):
    clip = CIT_WALK.get(name, 'walk')
    frames = [(clip, f) for f in range(0, CP.rig().clip_len(clip), step)] + [('idle', 0)]
    Pws = [m.posed(c, f) for c, f in frames]
    W, H, ox, oy = CP.frame_view(Pws, ppm)
    from scipy import ndimage
    gid = CP.tri_groups(m)
    tot_thin = tot_px = tot_wide = tot_gap_px = 0; worst = []
    poke_px = 0; bygrp = {}; spk_n = spk_px = 0
    ng = getattr(m, 'n_garment_tris', len(m.T))
    ts_comp = ts_px = 0                              # the same measure with back faces drawn (two-sided material, what ships)
    for (c, f), Pw in zip(frames, Pws):
        for k in range(yaws):
            yaw = 360.0 * k / yaws
            _, mask, gbuf = CP.raster(Pw, m.T, m.uv, None, yaw, ppm, W, H, ox, oy, colour=False, gid=gid)
            nt, tp, wp, tm, wm = CP.key_holes(mask, thin=thin)
            sn, spx, _ = CP.silhouette_spikes(gbuf); spk_n += sn; spk_px += spx
            crack, gap, by = CP.classify_holes(tm, gbuf, wm)
            for g_, l_ in by.items(): bygrp[g_] = bygrp.get(g_, 0) + sum(l_)
            ncr = int(ndimage.label(crack)[1])
            tot_thin += ncr; tot_px += int(crack.sum()); tot_wide += wp; tot_gap_px += int(gap.sum())
            if ncr: worst.append((int(crack.sum()), c, f, yaw, ncr))
            if ng < len(m.T):      # cores poking out of the cloth: core pixels farther than 2 px from the garment silhouette
                _, mg = CP.raster(Pw, m.T[:ng], m.uv, None, yaw, ppm, W, H, ox, oy, colour=False)
                _, mc = CP.raster(Pw, m.T[ng:], m.uv, None, yaw, ppm, W, H, ox, oy, colour=False)
                sil = ndimage.binary_dilation(ndimage.binary_fill_holes(mg), iterations=2)
                poke_px += int((mc & ~sil).sum())
            _, mask2, gbuf2 = CP.raster(Pw, m.T, m.uv, None, yaw, ppm, W, H, ox, oy, colour=False, gid=gid, cull=False)
            nt2, tp2, wp2, tm2, wm2 = CP.key_holes(mask2, thin=thin)
            crack2, gap2, _ = CP.classify_holes(tm2, gbuf2, wm2)
            n2 = int(ndimage.label(crack2)[1]); ts_comp += n2; ts_px += int(crack2.sum())
            if imgs and ncr and len(worst) <= 6:
                vis = np.zeros((H, W, 3), np.uint8); vis[mask] = (150, 150, 150); vis[gap] = (0, 160, 0); vis[crack] = (0, 0, 255); vis[wm] = (255, 0, 255)
                cv2.imwrite(os.path.join(imgs, '%s_%s_f%d_y%d.png' % (name, c, f, yaw)), vis)
    el, er = CP.stretch(m)
    n_views = len(frames) * yaws
    res = dict(name=name, tris=int(len(m.T)), views=n_views, crack_components=int(tot_thin), crack_px=int(tot_px), crack2s_components=int(ts_comp), crack2s_px=int(ts_px), silhouette_spike_components=int(spk_n), silhouette_spike_px=int(spk_px), crack_px_by_group={str(k): v for k, v in sorted(bygrp.items())}, gap_px=int(tot_gap_px), wide_px=int(tot_wide),
               views_with_cracks=len(worst), spike_over_5cm=int((el > 0.05).sum()), spike_over_10cm=int((el > 0.10).sum()), max_growth_cm=float(el.max() * 100),
               worst=sorted(worst, reverse=True)[:3])
    log(json.dumps(res))
    return res


if __name__ == '__main__':
    a = sys.argv[1:]
    opt = dict(ppm=700, thin=7, yaws=8, step=4)
    legacy = '--legacy' in a
    if legacy: a.remove('--legacy')
    js = imgs = None
    suffix = '_final'
    for key in ('--ppm', '--thin', '--yaws', '--step', '--json', '--imgs', '--suffix'):
        if key in a:
            k = a.index(key); v = a[k + 1]; a = a[:k] + a[k + 2:]
            if key == '--json': js = v
            elif key == '--imgs': imgs = v; os.makedirs(v, exist_ok=True)
            elif key == '--suffix': suffix = v
            else: opt[key[2:]] = type(opt[key[2:]])(v)
    out = {}
    for n in a:
        m = load_legacy(n) if legacy else load_r6(n, suffix)
        out[n] = evaluate(m, n, imgs=imgs, **opt)
    tot = {k: sum(r[k] for r in out.values()) for k in ('crack_components', 'crack_px', 'crack2s_components', 'crack2s_px', 'silhouette_spike_components', 'silhouette_spike_px', 'spike_over_5cm', 'spike_over_10cm')}
    print('TOTAL', json.dumps(tot))
    if js: json.dump(out, open(js, 'w'), indent=1)
