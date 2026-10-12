#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Water acceptance numbers (docs/night1/director/PLAN-firstpass.md section 4 Water), measured the way the round-01 blind critic did.

Calibration (round-01 pack, docs/night1/water/critic/round-01-AB-CRITIC.md): the critic measured on the A/B pack, i.e. the 4K frame centre-cropped
to 84 % (3226 x 1814). Its 'near-water crop' is x 0-1500, y 1150-1800 of that frame. With high-pass = Y - GaussianBlur(sigma 8 px) this
reproduces its numbers for build O (mean 90.6, rgb 98/91/68, p99.5 117, high-pass sd 4.4) and G (4.2 vs 4.1). 'Glint pixels' = luma >= 140
(on the reference's water crops this gives 1.0-2.4 %, the critic quoted 2.2 %; >= 130 is printed too). Autocorrelation 'at 80 px' = dolly
frames as packed (84 % crop, 1612 px wide), water crop y 480-700, x 0-820, high-pass sigma 24 px, horizontal 80 px shift, mean over frames
at 10 fps (round-01 O 0.233 vs the critic's 0.25; G 0.016 vs 0.08).

usage:
  water_spec.py near <frame.png|jpg> [...]          near-crop numbers per frame (any resolution; resized to 3840x2160 first)
  water_spec.py dolly <clip.mp4>                     autocorrelation at 80 px + per-frame temporal change of the water crop
  water_spec.py s4 <S4 frame>                        CITY-SPEC C14 via tools/export/spec_farfield.py
  water_spec.py harbour <harbour_high frame>         (r03) harbour crop: high-pass sd, glints, pale blobs
  water_spec.py sparkle <river_sun frame>            (r03) sparkle width: % of frame width whose water column has >= 2 % of rows at Y >= 200
  water_spec.py all <round_dir> [--json out.json]    every known capture in a round dir (+ PASS / FAIL against the r03 targets)

r03 additions (so builder and critic measure identically; calibrated on round-02 + refs):
  harbour crop   = x 0-2400, y 1300-2100 of the NATIVE 3840x2160 frame (not the 84 % pack crop: y 2100 lies outside the pack frame).
                   Round-02 harbour_high_4k: hp sd 4.33 (critic 4.4), glints 0 %, pale blobs 109 (critic 106).
  pale blob      = 8-connected component of >= 20 px whose pixels are >= 18 Y above the local mean (Gaussian sigma 24 px) with
                   chroma (max - min) / max <= 0.35 and whose brightest pixel is < 140 (dull pale patch = foam decal, not a glint).
  sparkle width  = in the pack frame (84 % centre crop), water rows = rows >= 45 % of the height; a column 'sparkles' when >= 2 % of its
                   water rows have Y >= 200; result = % of columns. Round-02 river_sun_4k 35.5 %, reference waterfront-perch-trailer 67.1 %
                   (critic: 35.5 / 66).
Luma = Rec.709 on the 8-bit sRGB values."""
import json, os, subprocess, sys
import cv2, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.dirname(os.path.dirname(HERE))
NEAR = (0, 1500, 1150, 1800)          # x0, x1, y0, y1 in the 3226 x 1814 pack frame
DOLLY = (0, 820, 480, 700)            # in the 1612 x 906 pack frame


def luma(bgr):
    b, g, r = bgr[..., 0], bgr[..., 1], bgr[..., 2]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def pack_crop(img, w=3840, h=2160):
    img = cv2.resize(img, (w, h), interpolation=cv2.INTER_CUBIC if img.shape[1] < w else cv2.INTER_AREA)
    cw, ch = int(w * 0.84), int(h * 0.84)
    x0, y0 = (w - cw) // 2, (h - ch) // 2
    return img[y0:y0 + ch, x0:x0 + cw]


def near(path):
    im = cv2.imread(path).astype(np.float32)
    src_w = im.shape[1]
    p = pack_crop(im)
    x0, x1, y0, y1 = NEAR
    c = p[y0:y1, x0:x1]; Y = luma(c)
    hp = Y - cv2.GaussianBlur(Y, (0, 0), 8)
    rgb = c.reshape(-1, 3).mean(0)[::-1]
    return dict(file=os.path.basename(path), src_width=src_w, mean_Y=round(float(Y.mean()), 1), rgb=[round(float(v), 1) for v in rgb],
                p1=round(float(np.percentile(Y, 1)), 1), p99_5=round(float(np.percentile(Y, 99.5)), 1), highpass_sd=round(float(hp.std()), 2),
                glint_pct_ge140=round(float((Y >= 140).mean() * 100), 2), glint_pct_ge130=round(float((Y >= 130).mean() * 100), 2),
                note='1080p frames are upscaled to 4K before the crop: high-pass / glint numbers read lower than on a native 4K frame' if src_w < 3840 else '')


HARBOUR = (0, 2400, 1300, 2100)       # x0, x1, y0, y1 in the native 3840 x 2160 frame


def _frame4k(path):
    im = cv2.imread(path).astype(np.float32)
    if im.shape[1] != 3840: im = cv2.resize(im, (3840, 2160), interpolation=cv2.INTER_CUBIC if im.shape[1] < 3840 else cv2.INTER_AREA)
    return im


def pale_blobs(c, Y, dY=18.0, chroma=0.35, amin=20, glint=140.0):
    bg = cv2.GaussianBlur(Y, (0, 0), 24)
    mx, mn = c.max(2), c.min(2)
    m = ((Y - bg >= dY) & ((mx - mn) / np.maximum(mx, 1.0) <= chroma)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    peak = np.zeros(n); np.maximum.at(peak, lab.ravel(), Y.ravel())
    return int(sum(1 for i in range(1, n) if st[i, 4] >= amin and peak[i] < glint))


def harbour(path):
    im = _frame4k(path); x0, x1, y0, y1 = HARBOUR
    c = im[y0:y1, x0:x1]; Y = luma(c)
    hp = Y - cv2.GaussianBlur(Y, (0, 0), 8)
    return dict(file=os.path.basename(path), crop='native 4K x0-2400 y1300-2100', mean_Y=round(float(Y.mean()), 1),
                highpass_sd=round(float(hp.std()), 2), glint_pct_ge140=round(float((Y >= 140).mean() * 100), 2), pale_blobs_ge20px=pale_blobs(c, Y),
                p1=round(float(np.percentile(Y, 1)), 1), p99_5=round(float(np.percentile(Y, 99.5)), 1))


def sparkle(path, thr=200.0, frac=0.02, horizon=0.45):
    p = pack_crop(cv2.imread(path).astype(np.float32))
    Y = luma(p); h0 = int(Y.shape[0] * horizon)
    col = (Y[h0:] >= thr).mean(0)
    return dict(file=os.path.basename(path), sparkle_width_pct=round(float((col >= frac).mean() * 100), 1))


def _ac(c, dx):
    a = c[:, :-dx]; b = c[:, dx:]; a = a - a.mean(); b = b - b.mean()
    return float((a * b).mean() / np.sqrt((a * a).mean() * (b * b).mean()))


def dolly(path, fps_keep=10):
    cap = cv2.VideoCapture(path); fps = cap.get(cv2.CAP_PROP_FPS) or 60
    step = max(1, int(round(fps / fps_keep))); n = 0; acs = []; dts = []; prev = None
    x0, x1, y0, y1 = DOLLY
    while True:
        ok, im = cap.read()
        if not ok: break
        n += 1
        if (n - 1) % step: continue
        im = im.astype(np.float32)
        h, w = im.shape[:2]; cw, ch = int(w * 0.84), int(h * 0.84)
        p = im[(h - ch) // 2:(h - ch) // 2 + ch, (w - cw) // 2:(w - cw) // 2 + cw]
        if p.shape[1] > 1612: p = cv2.resize(p, (1612, int(round(p.shape[0] * 1612 / p.shape[1]))), interpolation=cv2.INTER_AREA)
        Y = luma(p)[y0:y1, x0:x1]
        acs.append(_ac(Y - cv2.GaussianBlur(Y, (0, 0), 24), 80))
        if prev is not None: dts.append(float(np.abs(Y - prev).mean()))
        prev = Y
    return dict(file=os.path.basename(path), frames=n, sampled=len(acs), autocorr_80px=round(float(np.mean(acs)), 3),
                autocorr_80px_max=round(float(np.max(acs)), 3), water_dT_per_sample=round(float(np.mean(dts)), 2) if dts else None)


def s4(path):
    js = path + '.farfield.json'
    out = subprocess.run([sys.executable, os.path.join(WT, 'tools', 'export', 'spec_farfield.py'), path, js], capture_output=True, text=True)
    d = json.load(open(js))
    return dict(file=os.path.basename(path), C14=d['spec']['C14 far-shore Y minus river Y (target 5..35)'], far_shore_Y=round(d['regions']['far_shore']['Y'], 1),
                river_Y=round(d['regions']['river']['Y'], 1), farfield_json=os.path.basename(js))


def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return
    cmd = a[0]
    if cmd == 'near':
        for f in a[1:]: print(json.dumps(near(f)))
    elif cmd == 'dolly':
        for f in a[1:]: print(json.dumps(dolly(f)))
    elif cmd == 's4':
        for f in a[1:]: print(json.dumps(s4(f)))
    elif cmd == 'harbour':
        for f in a[1:]: print(json.dumps(harbour(f)))
    elif cmd == 'sparkle':
        for f in a[1:]: print(json.dumps(sparkle(f)))
    elif cmd == 'all':
        R = a[1]; res = {}
        for f in sorted(os.listdir(R)):
            p = os.path.join(R, f)
            if f.endswith(('.jpg', '.png')) and ('river' in f or 'harbour' in f) and not f.startswith('crop'):
                res[f] = near(p)
                if 'harbour' in f: res[f]['harbour'] = harbour(p)
                if 'river_sun' in f: res[f].update(sparkle(p))
            if f.endswith(('.jpg', '.png')) and f.startswith('S4'):
                res[f] = s4(p)
            if f.endswith('.mp4'):
                res[f] = dolly(p)
        for k, v in res.items(): print(json.dumps(v))
        res['_checks_r03'] = checks(res)
        for c in res['_checks_r03']: print('%-4s %-58s %s' % ('PASS' if c[2] else 'FAIL', c[0], c[1]))
        if '--json' in a: json.dump(res, open(a[a.index('--json') + 1], 'w'), indent=1)


def checks(res):
    """round-03 targets (4K frames only; perf is checked from perf.json separately)"""
    out = []
    def add(name, v, ok): out.append((name, v, bool(ok)))
    r = res.get('river_low_4k.jpg')
    if r:
        add('river_low near hp sd >= 12', r['highpass_sd'], r['highpass_sd'] >= 12); add('river_low near p99.5 >= 150', r['p99_5'], r['p99_5'] >= 150)
        add('river_low near glints >= 1 %', r['glint_pct_ge140'], r['glint_pct_ge140'] >= 1); add('river_low near mean Y <= 80', r['mean_Y'], r['mean_Y'] <= 80)
        add('river_low near p1 <= 25', r['p1'], r['p1'] <= 25)
    r = res.get('river_sun_4k.jpg')
    if r:
        add('river_sun sparkle width >= 50 %', r['sparkle_width_pct'], r['sparkle_width_pct'] >= 50)
        add('river_sun near mean Y <= 90', r['mean_Y'], r['mean_Y'] <= 90); add('river_sun near glints 3..15 %', r['glint_pct_ge140'], 3 <= r['glint_pct_ge140'] <= 15)
    r = res.get('harbour_high_4k.jpg')
    if r:
        h = r['harbour']
        add('harbour crop hp sd >= 10', h['highpass_sd'], h['highpass_sd'] >= 10); add('harbour crop glints >= 2 %', h['glint_pct_ge140'], h['glint_pct_ge140'] >= 2)
        add('harbour crop pale blobs (>= 20 px) == 0', h['pale_blobs_ge20px'], h['pale_blobs_ge20px'] == 0)
    for k in ('river_low_dolly.mp4', 'river_sun_dolly.mp4'):
        if k in res: add('%s autocorr at 80 px <= 0.10' % k, res[k]['autocorr_80px'], res[k]['autocorr_80px'] <= 0.10)
    r = res.get('S4_golden_4k.jpg')
    if r: add('S4 C14 5..35', r['C14'], 5 <= r['C14'] <= 35)
    return out


if __name__ == '__main__':
    main()
