"""Round-04 SPEC checks measured on OUR captures (pixels). Fan homage project; not official Marvel/Sony/Insomniac.
Needs opencv (+ ultralytics for `people`): run with a venv that has them.
  hero_run  CLIP t0 t1          step rate (bob FFT of the head top + bob minima), head-to-hip lean per frame (red/blue suit mask),
                                hero height / frame height                                              (CH2, CH6, CH7)
  takeoff   CLIP t0 t1          run -> jump: frames from the start of the crouch (mask height < 93 % of the running height) to the
                                last grounded frame (mask bottom leaves the ground line)                 (CH10)
  head_bob  CLIP t0 t1          step rate from the head blob only (CH6); lean_belt CLIP t0 t1: head -> red belt lean (CH7)
  people    CLIP|IMG [step_s]   YOLO11x person boxes per sampled frame: count, count >= 3 % height, heights (CH11, CH12, CH16)
Same colour-mask approach as the round-03 critic's bob.py / hero_meas.py."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); from p2paths import scr as _scr  # noqa: E402
import numpy as np
import cv2


def frames(path, t0=0, t1=1e9):
    cap = cv2.VideoCapture(path); fps = cap.get(5); i = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        t = i / fps; i += 1
        if t0 <= t <= t1: yield t, f, fps


def suit_mask(f):
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV); h, s, v = cv2.split(hsv)
    red = ((h < 8) | (h > 172)) & (s > 140) & (v > 60); blue = (h > 105) & (h < 130) & (s > 150) & (v > 40)
    # round 08: the original Tessera suit (teal panels + amber accents); the old red / blue stays so earlier clips still measure
    teal = (h > 82) & (h < 112) & (s > 120) & (v > 40); amber = (h > 8) & (h < 26) & (s > 170) & (v > 110)
    m = (red | blue | teal | amber).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)); md = cv2.dilate(m, np.ones((25, 25), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(md)
    if n < 2: return None
    k = 1 + np.argmax(st[1:, 4])
    return (lab == k) & (m > 0)


def hero_run(path, t0, t1):
    rows = []
    for t, f, fps in frames(path, t0, t1):
        m = suit_mask(f)
        if m is None: continue
        ys, xs = np.nonzero(m); top, bot = ys.min(), ys.max(); H = bot - top
        hd = ys < top + 0.10 * H; band = (ys > top + 0.45 * H) & (ys < top + 0.52 * H)
        lean = abs(np.degrees(np.arctan2(xs[hd].mean() - xs[band].mean(), ys[band].mean() - ys[hd].mean())))
        rows.append((t, np.percentile(ys, 0.2), H / f.shape[0], lean))
    R = np.array(rows); fps = 1 / np.median(np.diff(R[:, 0]))
    T = R[:, 1] - np.convolve(R[:, 1], np.ones(31) / 31, 'same'); T = T[15:-15]
    F = np.abs(np.fft.rfft(T * np.hanning(len(T)))); fr = np.fft.rfftfreq(len(T), 1 / fps)
    sel = (fr > 1) & (fr < 6)
    from scipy.signal import find_peaks
    pk, _ = find_peaks(-T, distance=8, prominence=2)
    return dict(clip=path, t0=t0, t1=t1, frames=len(R), bob_fft_hz=round(float(fr[np.argmax(F * sel)]), 3),
                bob_minima_per_s=round(len(pk) / (len(T) / fps), 3), lean_median_deg=round(float(np.median(R[:, 3])), 1),
                lean_p10_deg=round(float(np.percentile(R[:, 3], 10)), 1), lean_min_deg=round(float(R[:, 3].min()), 1),
                hero_height_median=round(float(np.median(R[:, 2])), 3))


def _red(f, smin=140, vmin=60):
    """Hero 'primary colour' mask: red (old suit) OR teal (Tessera crown / body); name kept for the callers."""
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV); h, s, v = cv2.split(hsv)
    return (((h < 8) | (h > 172)) & (s > smin) & (v > vmin)) | ((h > 82) & (h < 112) & (s > max(smin - 20, 100)) & (v > max(vmin - 10, 35)))


def head_bob(path, t0, t1):
    """Step rate from the HEAD alone (round 04): the head is the highest roughly square red blob in the upper 30 % of the hero.
    The whole-mask top used by hero_run() is hijacked by a hand swung above the head (the bigger round-04 arm swing), which puts the
    FFT peak at the stride frequency (half the step rate)."""
    from scipy.signal import find_peaks
    Y = []
    for t, f, fps in frames(path, t0, t1):
        m = suit_mask(f)
        if m is None: Y.append(np.nan); continue
        ys, _ = np.nonzero(m); top = ys.min(); H = ys.max() - top
        red = _red(f, 100, 50)[:int(top + 0.3 * H)].astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(red)
        c = [st[i, 1] for i in range(1, n) if st[i, 4] > 250 and 0.6 < st[i, 2] / max(st[i, 3], 1) < 1.6]      # round 08: 250 px (the Tessera crown is a smaller teal blob than the old red head)
        Y.append(min(c) if c else np.nan)
    Y = np.array(Y, float); ok = ~np.isnan(Y)
    Yi = np.interp(np.arange(len(Y)), np.nonzero(ok)[0], Y[ok])
    T = Yi - np.convolve(Yi, np.ones(31) / 31, 'same'); T = T[15:-15]; fps = 60.0
    F = np.abs(np.fft.rfft(T * np.hanning(len(T)))); fr = np.fft.rfftfreq(len(T), 1 / fps); sel = (fr > 1) & (fr < 6)
    pk, _ = find_peaks(-T, distance=8, prominence=2)
    return dict(clip=path, t0=t0, t1=t1, frames=len(Y), head_found=int(ok.sum()), head_bob_fft_hz=round(float(fr[np.argmax(F * sel)]), 3),
                head_bob_minima_per_s=round(len(pk) / (len(T) / fps), 3))


def lean_belt(path, t0, t1):
    """Torso lean from the head (top 10 % of the hero mask) to the red belt (row with most red pixels near the torso's blue centre,
    33-58 % of the height). Round 04: the hero_run() lean uses the mask's mid band, which the swinging arms drag around."""
    L = []
    for t, f, fps in frames(path, t0, t1):
        m = suit_mask(f)
        if m is None: continue
        hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV); h, s, v = cv2.split(hsv)
        red = _red(f) & m; blue = ((h > 105) & (h < 130) & (s > 150) & (v > 40)) & m
        ys, xs = np.nonzero(m); top = ys.min(); H = ys.max() - top
        hy, hx = np.nonzero(m[top:top + int(0.10 * H)]); head = (np.median(hx), top + hy.mean())
        z0, z1 = top + int(0.33 * H), top + int(0.58 * H)
        by, bx = np.nonzero(blue[z0:z1])
        if len(bx) == 0: continue
        cx = int(np.median(bx))
        rc = np.array([red[r, max(cx - 45, 0):cx + 45].sum() for r in range(z0, z1)])
        row = z0 + int(np.argmax(rc)); rx = np.nonzero(red[row, max(cx - 60, 0):cx + 60])[0] + max(cx - 60, 0)
        if len(rx) == 0: continue
        L.append(float(np.degrees(np.arctan2(head[0] - rx.mean(), row - head[1]))))
    A = np.array(L)
    return dict(clip=path, t0=t0, t1=t1, frames=len(A), lean_belt_median=round(float(np.median(A)), 1), lean_belt_p10=round(float(np.percentile(A, 10)), 1),
                lean_belt_p90=round(float(np.percentile(A, 90)), 1), frac_ge15=round(float((A >= 15).mean()), 2))


def takeoff(path, t0, t1):
    rows = []
    for t, f, fps in frames(path, t0, t1):
        m = suit_mask(f)
        if m is None: rows.append((t, np.nan, np.nan)); continue
        ys, _ = np.nonzero(m); rows.append((t, ys.max() - ys.min(), ys.max()))
    R = np.array(rows); H, B = R[:, 1], R[:, 2]
    run_h = np.nanmedian(H[:30]); ground = np.nanmedian(B[:30])
    lift = next(i for i in range(len(R)) if B[i] < ground - 0.04 * run_h and i > 5)          # feet 4 % of body height above the ground line
    last_ground = lift - 1
    c0 = last_ground
    while c0 > 0 and H[c0 - 1] < 0.93 * run_h: c0 -= 1
    return dict(clip=path, fps=round(1 / np.median(np.diff(R[:, 0])), 2), crouch_start_t=round(float(R[c0, 0]), 3), liftoff_t=round(float(R[lift, 0]), 3),
                anticipation_frames=int(lift - c0), min_height_ratio=round(float(np.nanmin(H[c0:lift + 1]) / run_h), 3) if lift > c0 else None)


def people(path, step=0.5):
    from ultralytics import YOLO
    import os
    m = YOLO(os.environ.get('YOLO_WEIGHTS', _scr('r4', 'spectools', 'yolo11x-seg.pt')))   # same weights as specs/tools
    out = []
    ims = [(0.0, cv2.imread(path))] if path.lower().endswith(('.jpg', '.png')) else None
    if ims is None:
        ims = []; last = -1e9
        for t, f, fps in frames(path):
            if t - last >= step - 1e-6: ims.append((t, f)); last = t
    for t, im in ims:
        r = m.predict(im, classes=[0], conf=0.35, verbose=False, device=__import__('os').environ.get('YOLO_DEVICE','mps'), imgsz=1920)[0]
        b = r.boxes.xyxy.cpu().numpy(); hts = (b[:, 3] - b[:, 1]) / im.shape[0]
        out.append(dict(t=round(t, 2), people=int(len(hts)), people_h3=int((hts >= 0.03).sum()), heights=[round(float(x), 3) for x in sorted(hts, reverse=True)]))
    P3 = np.array([o['people_h3'] for o in out])
    return dict(clip=path, samples=len(out), people_h3_median=float(np.median(P3)), people_h3_min=int(P3.min()), people_h3_max=int(P3.max()), per_sample=out)


if __name__ == '__main__':
    cmd, a = sys.argv[1], sys.argv[2:]
    if cmd == 'hero_run': r = hero_run(a[0], float(a[1]), float(a[2]))
    elif cmd == 'takeoff': r = takeoff(a[0], float(a[1]), float(a[2]))
    elif cmd == 'head_bob': r = head_bob(a[0], float(a[1]), float(a[2]))
    elif cmd == 'lean_belt': r = lean_belt(a[0], float(a[1]), float(a[2]))
    else: r = people(a[0], float(a[1]) if len(a) > 1 else 0.5)
    print(json.dumps(r))
