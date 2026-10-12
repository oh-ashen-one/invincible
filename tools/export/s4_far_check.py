#!/usr/bin/env python3
"""(r10) S4 far-shore band checks: the critic's r09 'biggest gap' tests + CITY-SPEC C11-C15 on ONE frame (any resolution; 4K is reduced to 1080p).
  T1  silhouette-top row std over x 0..1300 (px), three definitions (the critic's exact one is not published; calibrated: r08 / r09 frames gave 6.0 / 6.1 with 'first Y<215' and
      'first |dY|>4', both reproduced here). Target >= 12 px.
  T2  share of the box (0,150,1300,300) above Y 204. Target <= 10 %.
  T3  C11-C15 with the boxes of docs/night1/city/spec_regions.json (the same code as city_spec_check.py).
  T4  (r11, critic r10) flat bright blocks in (540,110,900,260): non-overlapping 8x8 blocks, 'bright' = block mean Y > 200, 'flat' = block std < 3. Two readings of the critic's sentence are reported:
      flat_of_bright (flat bright blocks / bright blocks; target <= 10 %) and flat_of_all (flat bright blocks / all blocks; the r10 frame gives 24.3 %, the critic wrote 25 %).
usage: python3 tools/export/s4_far_check.py <frame.(jpg|png)> [more frames ...] [--json out.json]
"""
import sys, os, json
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import city_spec_check as C

def luma(im): return C.luma(im)

def silhouette_tops(Y, x0=0, x1=1300, y0=100, y1=420):
    """per-column first non-sky row under three definitions"""
    out = {}
    skyY = np.median(Y[0:60, x0:x1], axis=0)                       # per-column sky reference (rows 0..60: above any far building)
    g = cv2.GaussianBlur(Y, (0, 0), 1.0); gy = np.abs(np.diff(g, axis=0))
    t_a, t_b, t_c = [], [], []
    for x in range(x0, x1):
        col = Y[y0:y1, x]
        ia = np.where(col < 215)[0]; t_a.append(y0 + (ia[0] if len(ia) else y1 - y0))
        ib = np.where(gy[y0:y1, x] > 4)[0]; t_b.append(y0 + (ib[0] if len(ib) else y1 - y0))
        ic = np.where(col < skyY[x - x0] - 12)[0]; t_c.append(y0 + (ic[0] if len(ic) else y1 - y0))
    for k, t in (('first_Y_lt_215', t_a), ('first_absdY_gt_4', t_b), ('first_Y_lt_sky_minus_12', t_c)):
        out[k] = dict(std=float(np.std(t)), mean=float(np.mean(t)), p5=float(np.percentile(t, 5)), p95=float(np.percentile(t, 95)))
    return out

def flat_blocks(Y, box=(540, 110, 900, 260), bs=8, ymin=200.0, smax=3.0):
    x0, y0, x1, y1 = box; b = Y[y0:y1, x0:x1]; H, W = b.shape; n = bright = flat = 0
    for y in range(0, H - bs + 1, bs):
        for x in range(0, W - bs + 1, bs):
            blk = b[y:y + bs, x:x + bs]; n += 1
            if blk.mean() > ymin:
                bright += 1
                if blk.std() < smax: flat += 1
    return dict(blocks=n, bright=bright, flat_bright=flat, flat_of_bright_pct=100.0 * flat / max(bright, 1), flat_of_all_pct=100.0 * flat / max(n, 1), bright_of_all_pct=100.0 * bright / max(n, 1))

def analyse(path, cfg):
    im = cv2.imread(path)
    if im is None: return None
    im1 = im if im.shape[1] == 1920 else cv2.resize(im, (1920, 1080), interpolation=cv2.INTER_AREA)
    Y = luma(im1)
    F = cfg['views']['S4_perch_skyline']['C11_C15_far']; th = cfg['thresholds']
    S = {k: C.region_stats(im1, im1, v, '1080') for k, v in F.items()}
    sky, fs, rv, nc = S['sky'], S['far_shore'], S['river'], S['near_city']
    box = Y[150:300, 0:1300]
    lines = {
        'C11 lap/sky': (fs['lap'] / max(sky['lap'], 1e-6), '>= %.1f' % th['C11']['far_over_sky_lap_min'], fs['lap'] / max(sky['lap'], 1e-6) >= th['C11']['far_over_sky_lap_min']),
        'C11 flat8 %': (fs['flat'], '<= %d' % th['C11']['flat_blocks_pct_max'], fs['flat'] <= th['C11']['flat_blocks_pct_max']),
        'C12 dBR': (fs['BR'] - sky['BR'], '+-%d' % th['C12']['br_diff_max'], abs(fs['BR'] - sky['BR']) <= th['C12']['br_diff_max']),
        'C13 far-sky Y': (fs['Y'] - sky['Y'], '%d..%d' % tuple(th['C13']['far_minus_sky_Y']), C.ok(fs['Y'] - sky['Y'], *th['C13']['far_minus_sky_Y'])),
        'C13 far>near': (fs['Y'] - nc['Y'], '> 0', fs['Y'] > nc['Y']),
        'C14 far-river Y': (fs['Y'] - rv['Y'], '%d..%d' % tuple(th['C14']['river_below_far_Y']), C.ok(fs['Y'] - rv['Y'], *th['C14']['river_below_far_Y'])),
        'C15 rms far/near': (fs['rms'] / max(nc['rms'], 1e-6), '%.2f..%.2f' % tuple(th['C15']['rms_far_over_near']), C.ok(fs['rms'] / max(nc['rms'], 1e-6), *th['C15']['rms_far_over_near'])),
    }
    fb = flat_blocks(Y)
    crit_c13 = float(Y[150:215, 0:1300].mean() - sky['Y'])   # (r11) the r10 critic's C13 box (0,150,1300,215): -30.3 on the r10 frame, -29.5 here; the committed far_shore box gives -38.5
    sil = silhouette_tops(Y)
    t1 = {k: v['std'] for k, v in sil.items()}
    return dict(file=path, sky_Y=sky['Y'], far_Y=fs['Y'], river_Y=rv['Y'], near_Y=nc['Y'], box_mean_Y=float(box.mean()), box_pct204=float((box > 204).mean() * 100),
                T1_std=t1, T1_pass=bool(min(t1.values()) >= 12.0), T2_pass=bool((box > 204).mean() <= 0.10), C13_critic_box=crit_c13, T4=fb, T4_pass=bool(fb['flat_of_bright_pct'] <= 10.0 and fb['flat_of_all_pct'] <= 10.0),
                lines={k: dict(value=round(float(v[0]), 2), target=v[1], passed=bool(v[2])) for k, v in lines.items()}, silhouette=sil)

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; jo = None
    if '--json' in sys.argv: jo = sys.argv[sys.argv.index('--json') + 1]; args = [a for a in args if a != jo]
    cfg = json.load(open(C.REGFILE)); res = []
    for p in args:
        r = analyse(p, cfg)
        if r is None: print('unreadable', p); continue
        res.append(r)
        print('==', os.path.basename(p))
        print('  sky Y %.1f  far Y %.1f  river Y %.1f  near Y %.1f | box(0,150,1300,300) mean Y %.1f  > 204: %.1f %%  (T2 <= 10: %s)' % (r['sky_Y'], r['far_Y'], r['river_Y'], r['near_Y'], r['box_mean_Y'], r['box_pct204'], 'PASS' if r['T2_pass'] else 'fail'))
        print('  C13 with the critic box (0,150,1300,215): far - sky Y = %.1f (target -35..-25)' % r['C13_critic_box'])
        f4 = r['T4']; print('  T4 flat bright 8x8 blocks in (540,110,900,260): %d of %d bright (%d blocks): %.1f %% of bright / %.1f %% of all  (<= 10 %%: %s)' % (f4['flat_bright'], f4['bright'], f4['blocks'], f4['flat_of_bright_pct'], f4['flat_of_all_pct'], 'PASS' if r['T4_pass'] else 'fail'))
        print('  T1 silhouette-top std (px): ' + '  '.join('%s %.1f' % (k, v) for k, v in r['T1_std'].items()) + '  (>= 12: %s)' % ('PASS' if r['T1_pass'] else 'fail'))
        print('  ' + ' | '.join('%s %s %s' % (k, v['value'], 'ok' if v['passed'] else 'FAIL') for k, v in r['lines'].items()))
    if jo: json.dump(res, open(jo, 'w'), indent=1)
