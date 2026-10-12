#!/usr/bin/env python3
"""CITY-SPEC checker: computes every measurable CITY-SPEC line (docs/night1/city/SPEC.md) for a round folder, with the ONE set of pixel
regions in docs/night1/city/spec_regions.json. Builder and critic both run this script; neither uses private crops for a spec line.

usage:  city_spec_check.py <round_dir> [--res 1080|4k|both] [--yolo] [--ip] [--overlay <dir>] [--json <out.json>] [--md <out.md>]
  round_dir    folder holding S<n>_*_1920x1080.jpg / _3840x2160.jpg (jpg or png)
  --res        which frames to measure (default both; the table has one column per resolution)
  --yolo       C4 / C6 vehicle + person counts (ultralytics YOLO11x-seg, conf 0.35, same recipe as specs/tools/count_people_vehicles.py);
               needs a python with ultralytics: env CITY_YOLO_PY (default: the spec venv) and CITY_YOLO_WEIGHTS
  --ip         OCR every 4K frame (tesseract, 4 quadrants x normal / inverted) against the denylist in spec_regions.json
  --overlay    write the frames with all regions drawn (evidence that builder and critic look at the same pixels)

Rules (spec header + spec_regions.json _doc): luma Y = .2126R + .7152G + .0722B; texture statistics (mean |Laplacian|, RMS contrast std/mean, flat 8x8
blocks std < 1.5) are taken on a 1920x1080 frame (4K frames are downscaled with INTER_AREA first); mean-type statistics (Y, B-R, share above 204,
percentiles) use the native frame and the box of that resolution.  Formulas are far.py / haze_regions.py from the round-06 critic and the spec tools."""
import argparse, glob, json, os, subprocess, sys, tempfile
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
REGFILE = os.path.join(ROOT, 'docs', 'night1', 'city', 'spec_regions.json')
RES_NAME = {'1080': '1920x1080', '4k': '3840x2160'}
YOLO_PY = os.environ.get('CITY_YOLO_PY', '/Users/midir/sm2-n1/_scratch/traversal/specv/bin/python')
YOLO_W = os.environ.get('CITY_YOLO_WEIGHTS', '/Users/midir/sm2-n1/_scratch/city/yolo/yolo11x-seg.pt')
YOLO_CONF = float(os.environ.get('CITY_YOLO_CONF', '0.30'))   # (r08) the critic's test is conf .30 (r07 used .35); the worker also reports the count at .35
YOLO_ANN = os.environ.get('CITY_YOLO_ANN')                    # (r08) directory for annotated detection frames (evidence)


def load(view, root, res):
    pat = os.path.join(root, f'{view}_{RES_NAME[res]}.*')
    hits = [f for f in sorted(glob.glob(pat)) if f.lower().endswith(('.jpg', '.png'))]
    if not hits: return None, None
    return cv2.imread(hits[0]), hits[0]


def to1080(im):
    return im if im.shape[1] == 1920 else cv2.resize(im, (1920, 1080), interpolation=cv2.INTER_AREA)


def luma(c):
    c = c.astype(np.float32); return .2126 * c[..., 2] + .7152 * c[..., 1] + .0722 * c[..., 0]


def crop(im, box):
    x0, y0, x1, y1 = box; return im[y0:y1, x0:x1]


def region_stats(im_native, im1080, boxes, res):
    """mean-type stats on the native frame, texture stats on the 1080p-normalised frame."""
    cn = crop(im_native, boxes[res]); c1 = crop(im1080, boxes['1080'])
    Yn = luma(cn); Y1 = luma(c1)
    b, g, r = [cn[..., i].astype(np.float32) for i in range(3)]
    h, w = Y1.shape
    blocks = Y1[:h // 8 * 8, :w // 8 * 8].reshape(h // 8, 8, w // 8, 8).std(axis=(1, 3))
    return dict(Y=float(Yn.mean()), BR=float(b.mean() - r.mean()), R=float(r.mean()), G=float(g.mean()), B=float(b.mean()),
                p95=float(np.percentile(Yn, 95)), p99=float(np.percentile(Yn, 99)), pct204=float((Yn > 204).mean() * 100),
                rms=float(Y1.std() / max(Y1.mean(), 1e-6)), lap=float(np.abs(cv2.Laplacian(Y1, cv2.CV_32F)).mean()), flat=float((blocks < 1.5).mean() * 100),
                px=int(Yn.size))


def ok(v, lo=None, hi=None):
    return (lo is None or v >= lo) and (hi is None or v <= hi)


def check_facades(cfg, frames, res_list, out):
    T1, T2 = cfg['thresholds']['C1'], cfg['thresholds']['C2']
    for view, vcfg in cfg['views'].items():
        if 'C1_C2_facade' not in vcfg: continue
        for res in res_list:
            im, path = frames[view][res]
            if im is None: continue
            im1080 = to1080(im)
            for name, boxes in vcfg['C1_C2_facade'].items():
                s = region_stats(im, im1080, boxes, res)
                c1 = s['pct204'] <= T1['pct_above_204_max'] and s['p95'] <= T1['p95_max'] and s['p99'] <= T1['p99_max']
                c2 = ok(s['Y'], T2['mean_Y_min'], T2['mean_Y_max'])
                out['facades'].append(dict(view=view, region=name, res=res, daylight=vcfg['daylight'], box=boxes[res], pct_above_204=round(s['pct204'], 2), p95=round(s['p95'], 1),
                                           p99=round(s['p99'], 1), mean_Y=round(s['Y'], 1), C1_pass=bool(c1), C2_pass=bool(c2)))


def check_crit(cfg, frames, res_list, out):
    """(r10) the critic's r09 boxes: share of pixels above Y 204 (C1 1.5 %, the S4 far band 10 %)"""
    for view, vcfg in cfg['views'].items():
        for name, boxes in (vcfg.get('crit_boxes') or {}).items():
            for res in res_list:
                im, path = frames[view][res]
                if im is None: continue
                s = region_stats(im, to1080(im), boxes, res); lim = boxes.get('max_pct204', 1.5)
                out['crit'].append(dict(view=view, region=name, res=res, box=boxes[res], pct_above_204=round(s['pct204'], 2), max_pct204=lim, p95=round(s['p95'], 1), mean_Y=round(s['Y'], 1), passed=bool(s['pct204'] <= lim)))


def check_far(cfg, frames, res_list, out):
    view = 'S4_perch_skyline'; F = cfg['views'][view]['C11_C15_far']; th = cfg['thresholds']
    for res in res_list:
        im, path = frames[view][res]
        if im is None: continue
        im1080 = to1080(im)
        S = {k: region_stats(im, im1080, v, res) for k, v in F.items()}
        sky, fs, rv, nc, hz = S['sky'], S['far_shore'], S['river'], S['near_city'], S['horizon_far']
        lines = {
            'C11 far_shore lap / sky lap': (fs['lap'] / max(sky['lap'], 1e-6), '>= %.1f' % th['C11']['far_over_sky_lap_min'], fs['lap'] / max(sky['lap'], 1e-6) >= th['C11']['far_over_sky_lap_min']),
            'C11 far_shore flat 8x8 blocks %': (fs['flat'], '<= %d' % th['C11']['flat_blocks_pct_max'], fs['flat'] <= th['C11']['flat_blocks_pct_max']),
            'C12 far_shore (B-R) - sky (B-R)': (fs['BR'] - sky['BR'], '+-%d' % th['C12']['br_diff_max'], abs(fs['BR'] - sky['BR']) <= th['C12']['br_diff_max']),
            'C13 far_shore Y - sky Y': (fs['Y'] - sky['Y'], '%d..%d' % tuple(th['C13']['far_minus_sky_Y']), ok(fs['Y'] - sky['Y'], *th['C13']['far_minus_sky_Y'])),
            'C13 far_shore Y > near_city Y': (fs['Y'] - nc['Y'], '> 0', fs['Y'] > nc['Y']),
            'C14 far_shore Y - river Y': (fs['Y'] - rv['Y'], '%d..%d' % tuple(th['C14']['river_below_far_Y']), ok(fs['Y'] - rv['Y'], *th['C14']['river_below_far_Y'])),
            'C15 rms far_shore / near_city': (fs['rms'] / max(nc['rms'], 1e-6), '%.2f..%.2f' % tuple(th['C15']['rms_far_over_near']), ok(fs['rms'] / max(nc['rms'], 1e-6), *th['C15']['rms_far_over_near'])),
        }
        try:
            import s4_far_check as _S4
            _t = {k: v['std'] for k, v in _S4.silhouette_tops(luma(im1080)).items()}
            lines['T1 silhouette-top std (min of 3 defs, px)'] = (min(_t.values()), '>= 12', min(_t.values()) >= 12.0)
        except Exception as _ex: print('T1 silhouette skipped:', _ex, file=sys.stderr)
        out['far'].append(dict(res=res, regions={k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in S.items()},
                               lines={k: dict(value=round(float(v[0]), 2), target=v[1], passed=bool(v[2])) for k, v in lines.items()}))


def yolo_counts(view, path):
    r = subprocess.run([YOLO_PY, os.path.abspath(__file__), '--yolo-worker', path], capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    if r.returncode != 0: return dict(error=(r.stderr or r.stdout)[-300:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def check_yolo(cfg, frames, out):
    if not (os.path.exists(YOLO_PY) and os.path.exists(YOLO_W)):
        out['yolo'] = 'unavailable (need CITY_YOLO_PY / CITY_YOLO_WEIGHTS)'; return
    th = cfg['thresholds']; res = '1080'
    for view, vcfg in cfg['views'].items():
        key = 'C4_yolo' if 'C4_yolo' in vcfg else 'C6_yolo' if 'C6_yolo' in vcfg else None
        if not key: continue
        im, path = frames[view][res]
        if im is None: continue
        c = yolo_counts(view, path)
        if 'error' in c: out['yolo'][view] = c; continue
        if key == 'C4_yolo':
            c['C4_cars_pass'] = ok(c['vehicles'], th['C4']['cars_min'], th['C4']['cars_max']); c['C4_people_pass'] = ok(c['people'], th['C4']['people_min'], th['C4']['people_max'])
            c['C4_lights_pass'] = c['traffic_lights'] >= th['C4']['traffic_lights_min']
        else:
            c['C6_vehicles_pass'] = ok(c['vehicles'], th['C6']['vehicles_min'], th['C6']['vehicles_max'])
        out['yolo'][view] = c


def check_ip(cfg, root, out):
    from PIL import Image, ImageOps
    tmp = tempfile.mkdtemp(); deny = cfg['ip_denylist']
    def ocr(img):
        txt = ''
        for inv in (False, True):
            v = ImageOps.invert(img.convert('RGB')).convert('L') if inv else img.convert('L'); v = v.resize((v.width * 2, v.height * 2)); p = os.path.join(tmp, 'c.png'); v.save(p)
            txt += ' ' + subprocess.run(['tesseract', p, '-', '--psm', '11'], capture_output=True, text=True).stdout.upper()
        return txt
    _fr = sorted(glob.glob(os.path.join(root, 'S*_3840x2160.*'))) or sorted(glob.glob(os.path.join(root, 'S*_1920x1080.*')))   # (r10) a 1080p-only round is OCR'd at 1080p (reported as such: smaller text can be missed)
    for f in _fr:
        if not f.lower().endswith(('.jpg', '.png')): continue
        im = Image.open(f).convert('L'); W, H = im.size; hits = set()
        for (x0, y0) in [(0, 0), (W // 2, 0), (0, H // 2), (W // 2, H // 2)]:
            t = ocr(im.crop((x0, y0, x0 + W // 2, y0 + H // 2))); hits |= {d for d in deny if d in t}
        out['ip'][os.path.basename(f)] = sorted(hits)


def draw_overlays(cfg, frames, outdir):
    os.makedirs(outdir, exist_ok=True)
    for view, vcfg in cfg['views'].items():
        im, path = frames[view]['1080']
        if im is None: continue
        im = im.copy()
        groups = {}
        for k in ('C1_C2_facade', 'C11_C15_far'):
            if k in vcfg: groups.update(vcfg[k])
        for name, b in groups.items():
            x0, y0, x1, y1 = b['1080']; cv2.rectangle(im, (x0, y0), (x1, y1), (0, 0, 255), 2); cv2.putText(im, name, (x0 + 4, y0 + 18), cv2.FONT_HERSHEY_SIMPLEX, .55, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.imwrite(os.path.join(outdir, f'{view}_regions.jpg'), im, [cv2.IMWRITE_JPEG_QUALITY, 85])


def render(out, res_list):
    L = []
    P = lambda s='': L.append(s)
    P('# CITY-SPEC check (tools/export/city_spec_check.py, regions docs/night1/city/spec_regions.json v%s)' % out['regions_version'])
    P(); P('round folder: `%s`' % out['round'])
    P()
    if out['far']:
        P('## C11-C15 far field (S4)'); P()
        P('| line | ' + ' | '.join(f['res'] for f in out['far']) + ' | target |'); P('|---|' + '---|' * (len(out['far']) + 1))
        for k in out['far'][0]['lines']:
            P(f'| {k} | ' + ' | '.join('%+.2f %s' % (f['lines'][k]['value'], 'PASS' if f['lines'][k]['passed'] else 'FAIL') for f in out['far']) + f' | {out["far"][0]["lines"][k]["target"]} |')
        P(); f0 = out['far'][0]
        P('| region (%s) | Y | B-R | RMS | lap | flat 8x8 pct |' % f0['res']); P('|---|---|---|---|---|---|')
        for k, v in f0['regions'].items(): P(f'| {k} | {v["Y"]:.1f} | {v["BR"]:+.1f} | {v["rms"]:.3f} | {v["lap"]:.2f} | {v["flat"]:.0f} |')
        P()
    if out['facades']:
        P('## C1 / C2 facade crops (C1: <= 1.5 % of pixels above Y 204, p95 <= 192, p99 <= 206; C2: mean Y 52..119; daylight views gated, dusk view informational)'); P()
        P('| region | res | > 204 % | p95 | p99 | mean Y | C1 | C2 |'); P('|---|---|---|---|---|---|---|---|')
        for f in out['facades']:
            tag = '' if f['daylight'] else ' (dusk)'
            P(f'| {f["region"]}{tag} | {f["res"]} | {f["pct_above_204"]:.2f} | {f["p95"]:.0f} | {f["p99"]:.0f} | {f["mean_Y"]:.1f} | {"pass" if f["C1_pass"] else "FAIL"} | {"pass" if f["C2_pass"] else "FAIL"} |')
        P()
        for res in res_list:
            day = [f for f in out['facades'] if f['res'] == res and f['daylight']]
            if day: P(f'- {res}: daylight crops C1 pass {sum(f["C1_pass"] for f in day)}/{len(day)}, C2 pass {sum(f["C2_pass"] for f in day)}/{len(day)}')
        P()
    if out.get('crit'):
        P('## Critic r09 boxes (share of pixels above Y 204; C1 limit 1.5 %, S4 far band 10 %)'); P()
        P('| region | res | box | > 204 % | limit | p95 | mean Y | result |'); P('|---|---|---|---|---|---|---|---|')
        for f in out['crit']: P(f'| {f["region"]} | {f["res"]} | {tuple(f["box"])} | {f["pct_above_204"]:.2f} | {f["max_pct204"]} | {f["p95"]:.0f} | {f["mean_Y"]:.1f} | {"pass" if f["passed"] else "FAIL"} |')
        P()
    if isinstance(out['yolo'], str): P('## C4 / C6 (YOLO): ' + out['yolo']); P()
    elif out['yolo']:
        P(f'## C4 / C6 vehicle and person counts (YOLO11x-seg, conf {YOLO_CONF}, 1080p frame; the count at conf 0.35 is in the json as vehicles_c35)'); P()
        P('| view | vehicles | people | traffic lights | line | result |'); P('|---|---|---|---|---|---|')
        for v, c in out['yolo'].items():
            if 'error' in c: P(f'| {v} | error | | | | {c["error"]} |'); continue
            if 'C4_cars_pass' in c:
                P(f'| {v} | {c["vehicles"]} | {c["people"]} | {c["traffic_lights"]} | C4 (cars 5-19, people 6-32, lights >= 1) | cars {"pass" if c["C4_cars_pass"] else "FAIL"}, people {"pass" if c["C4_people_pass"] else "FAIL"}, lights {"pass" if c["C4_lights_pass"] else "FAIL"} |')
            else: P(f'| {v} | {c["vehicles"]} | {c["people"]} | {c["traffic_lights"]} | C6 (vehicles 14-22) | {"pass" if c["C6_vehicles_pass"] else "FAIL"} |')
        P()
    if out['ip']:
        P('## IP text check (OCR of the 4K frames vs denylist)'); P()
        for k, v in out['ip'].items(): P(f'- {k}: {", ".join(v) if v else "clean"}')
        P()
    P('## Lines not measurable by pixels (judged / hand count; see spec_regions.json manual_lines)'); P()
    for k, v in out['manual'].items(): P(f'- {k}: {v}')
    return '\n'.join(L) + '\n'


def yolo_worker(path):
    from ultralytics import YOLO
    m = YOLO(YOLO_W); im = cv2.imread(path)
    r = m.predict(im, classes=[0, 2, 3, 5, 7, 9], conf=YOLO_CONF, verbose=False, device=os.environ.get('CITY_YOLO_DEVICE', 'cpu'), imgsz=1920)[0]
    cls = r.boxes.cls.cpu().numpy(); cf = r.boxes.conf.cpu().numpy()
    if YOLO_ANN:
        os.makedirs(YOLO_ANN, exist_ok=True); cv2.imwrite(os.path.join(YOLO_ANN, os.path.basename(path).rsplit('.', 1)[0] + '_yolo.jpg'), r.plot(boxes=True, masks=False, labels=False, conf=False, line_width=1))
    veh = np.isin(cls, [2, 3, 5, 7])
    print(json.dumps(dict(people=int((cls == 0).sum()), vehicles=int(veh.sum()), cars=int((cls == 2).sum()), traffic_lights=int((cls == 9).sum()), vehicles_c35=int((veh & (cf >= 0.35)).sum()), conf=YOLO_CONF)))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('round_dir', nargs='?'); ap.add_argument('--res', default='both'); ap.add_argument('--yolo', action='store_true'); ap.add_argument('--ip', action='store_true')
    ap.add_argument('--overlay'); ap.add_argument('--json'); ap.add_argument('--md'); ap.add_argument('--yolo-worker')
    a = ap.parse_args()
    if a.yolo_worker: yolo_worker(a.yolo_worker); return
    cfg = json.load(open(REGFILE)); res_list = ['1080', '4k'] if a.res == 'both' else [a.res]
    frames = {v: {r: load(v, a.round_dir, r) for r in ('1080', '4k')} for v in cfg['views']}
    out = dict(round=os.path.abspath(a.round_dir), regions_version=cfg['version'], facades=[], far=[], crit=[], yolo={}, ip={}, manual=cfg['manual_lines'])
    missing = [f'{v} {r}' for v in cfg['views'] for r in res_list if frames[v][r][0] is None]
    if missing: print('missing frames:', ', '.join(missing), file=sys.stderr)
    check_facades(cfg, frames, res_list, out); check_far(cfg, frames, res_list, out); check_crit(cfg, frames, res_list, out)
    if a.yolo: check_yolo(cfg, frames, out)
    if a.ip: check_ip(cfg, a.round_dir, out)
    if a.overlay: draw_overlays(cfg, frames, a.overlay)
    md = render(out, res_list); print(md)
    if a.json: json.dump(out, open(a.json, 'w'), indent=1)
    if a.md: open(a.md, 'w').write(md)


if __name__ == '__main__': main()
