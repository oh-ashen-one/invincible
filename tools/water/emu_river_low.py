# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# usage: python3 tools/water/emu_river_low.py r03 '{"ChopK": 2.4, "MicroK": 1.6, "ScatK": 0.06, "SpecK": 1.6, "_envk": 1.4, "_body": [0.03, 0.027, 0.017]}'
# (mode r02 = round-02 shading for calibration; needs $SM2_WATER_SCR textures: water_slope.png, water_chop.png)
"""CPU emulation of the river_low near crop (4K) to rank r03 parameter variants before the GPU hold. Environment = the round-02 4K frame
itself (sky / far shore / buildings as the camera sees them), linearised with sRGB; GGX blur ~ Gaussian of the env with sigma = alpha (rad).
Rough, calibrated on the round-02 numbers (mean 79.3, p1 46, p99.5 122, hp 8.46)."""
import sys, math, json, numpy as np, cv2
sys.path.insert(0, '/Users/midir/sm2-n1/water/tools/water')
import water_spec as ws
S = __import__('os').environ.get('SM2_WATER_SCR', '/Users/midir/sm2-n1/_scratch/water') + '/'
ENV = cv2.imread('/Users/midir/sm2-n1/water/docs/night1/water/round-02/river_low_4k.jpg').astype(np.float32) / 255.0
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
enc = lambda l: np.where(l <= 0.0031308, l * 12.92, 1.055 * np.clip(l, 0, None) ** (1 / 2.4) - 0.055)
ENVL = lin(ENV)
SIG = [0, 8, 24, 60, 150, 300]
BL = [ENVL] + [cv2.GaussianBlur(ENVL, (0, 0), s) for s in SIG[1:]]
cam = np.array([-768.0, -128.0, 4.4]); WZ = -1.6
yaw, pitch = math.radians(-88.282), math.radians(-3.0)
F = np.array([math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)])
Rt = np.array([-math.sin(yaw), math.cos(yaw), 0.0])
Up = np.cross(Rt, F)   # UE left-handed: right = +Y when yaw 0
Up = Up if Up[2] > 0 else -Up
tex = cv2.imread(S + 'water_slope.png', -1)[..., [2, 1, 0, 3]].astype(np.float32) / 255.0
chp = cv2.imread(S + 'water_chop.png', -1)[..., [2, 1, 0, 3]].astype(np.float32) / 255.0
def pyr(t):
    P = [t]
    while P[-1].shape[0] > 4: P.append(cv2.resize(P[-1], (P[-1].shape[1] // 2, P[-1].shape[0] // 2), interpolation=cv2.INTER_AREA))
    return P
TP, CP = pyr(tex), pyr(chp)
def samp(P, ch, u, v, lod):
    lod = np.clip(lod, 0, len(P) - 1); out = np.zeros(u.shape, np.float32)
    l0 = np.floor(lod).astype(int); fr = lod - l0
    for L in np.unique(l0):
        m = l0 == L
        for LL, w in ((L, 1 - fr[m]), (min(L + 1, len(P) - 1), fr[m])):
            T = P[LL][..., ch]; N = T.shape[0]
            x = (u[m] * N - 0.5) % N; y = (v[m] * N - 0.5) % N; x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = x - x0; fy = y - y0
            x1 = (x0 + 1) % N; y1 = (y0 + 1) % N
            out[m] += w * (T[y0, x0] * (1 - fx) * (1 - fy) + T[y0, x1] * fx * (1 - fy) + T[y1, x0] * (1 - fx) * fy + T[y1, x1] * fx * fy)
    return out
def render(P, mode='r03', t=11.0, ss=1):
    # pixels of the near crop in the 4K frame: pack (x0-1500, y1150-1800) + offset (307, 173)
    xs = np.arange(307, 1807, 1.0 / ss) + 0.5 / ss; ys = np.arange(1323, 1973, 1.0 / ss) + 0.5 / ss
    X, Y = np.meshgrid(xs, ys)
    tn = 1.0 / 1920.0
    d = F[None, None] + ((X - 1920) * tn)[..., None] * Rt + (-(Y - 1080) * tn)[..., None] * Up
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    tt = (WZ - cam[2]) / d[..., 2]
    p = cam[None, None, :2] + d[..., :2] * tt[..., None]
    dist = tt
    # footprint (m per pixel): finite differences
    dpx = np.gradient(p, axis=1) * ss; dpy = np.gradient(p, axis=0) * ss
    foot = np.linalg.norm(np.abs(dpx) + np.abs(dpy), axis=-1)
    V = -d
    import build_water as bw
    sl = np.zeros(p.shape, np.float32)
    for w in bw.waves():
        if w['L'] < bw.PS_WAVE_MIN_L: continue
        ph = w['k'] * (p[..., 0] * w['dx'] + p[..., 1] * w['dy']) - w['w'] * t + w['ph']
        f = 1 - np.clip((foot * w['k'] / math.pi - 0.12) / 0.23, 0, 1)
        g = w['k'] * w['A'] * np.cos(ph) / np.maximum(1 - w['Q'] * w['k'] * w['A'] * np.sin(ph), 0.35) * f
        sl[..., 0] += w['dx'] * g; sl[..., 1] += w['dy'] * g
    var = np.zeros(p.shape[:2], np.float32)
    def layer(Pt, sc, ang, chs, amp, bias, vel, off=(0, 0)):
        th = math.radians(bw.WIND_DEG + ang); c, s = math.cos(th), math.sin(th)
        qx = (c * p[..., 0] + s * p[..., 1]) / sc - vel * t + off[0]; qy = (-s * p[..., 0] + c * p[..., 1]) / sc + off[1]
        ax = np.abs(c * dpx[..., 0] + s * dpx[..., 1]) + np.abs(c * dpy[..., 0] + s * dpy[..., 1]); ay = np.abs(-s * dpx[..., 0] + c * dpx[..., 1]) + np.abs(-s * dpy[..., 0] + c * dpy[..., 1])
        N = Pt[0].shape[0]; mj = np.maximum(ax, ay) / sc * N; mn = np.minimum(ax, ay) / sc * N
        lod = np.log2(np.maximum(np.maximum(mj / 8.0, mn), 1e-6)) + bias
        gx = (samp(Pt, chs[0], qx, qy, lod) - 0.5) * 6; gy = (samp(Pt, chs[1], qx, qy, lod) - 0.5) * 6
        return np.stack([c * gx - s * gy, s * gx + c * gy], -1) * amp
    gust = 0.5
    if mode == 'r02':
        ck = P['ChopK'] * 1.0
        for i, (sc, aA, aB, amp) in enumerate([(21.0, 8.0, -47.0, 0.050), (6.7, -19.0, 38.0, 0.055), (2.2, 27.0, -33.0, 0.055), (0.73, -11.0, 52.0, 0.050)]):
            kc = 2 * math.pi / (sc / 8.5); spd = math.sqrt(9.81 / kc + 7.28e-5 * kc)
            sl += ck * 0.7071 * (layer(TP, sc, aA, (0, 1), amp, 1.0, spd / sc) + layer(TP, sc * 0.87, aB, (2, 3), amp, 1.0, spd * 1.07 / (sc * .87), (0.37, 0.61 * (i + 1))))
            rf = np.clip(np.log2(sc / (12 * foot)) / 3, 0, 1); var += amp * amp * (1 - rf) * ck * ck
        a2 = 0.028 ** 2 + 1.2 * 2 * var
        rough = np.clip(a2 ** 0.25, 0.04, 0.7)
    else:
        ck = P['ChopK']; mk = P['ChopK'] * P['MicroK'] * 0.065
        for i, (sc, aA, aB, amp) in enumerate(bw.LAYERS):
            kc = 2 * math.pi / (sc / 8.5); spd = math.sqrt(9.81 / kc + 7.28e-5 * kc)
            sl += ck * 0.7071 * (layer(TP, sc, aA, (0, 1), amp, 0.0, spd / sc) + layer(TP, sc * 0.87, aB, (2, 3), amp, 0.0, spd * 1.07 / (sc * .87), (0.37, 0.61 * (i + 1))))
        for j, (sc, ang, vf) in enumerate(bw.CHOP):
            kc = 2 * math.pi / (sc / 5.5); spd = math.sqrt(9.81 / kc + 7.28e-5 * kc) * vf
            sl += mk * 0.7071 * layer(CP, sc, ang, (0, 1) if j == 0 else (2, 3), 1.0, 0.0, spd / sc, (0, 0.29 * (j + 1)))
        rough = np.full(p.shape[:2], P['RoughN'], np.float32)
    N = np.dstack([-sl[..., 0], -sl[..., 1], np.ones(sl.shape[:2])]); N /= np.linalg.norm(N, axis=-1, keepdims=True)
    R0 = 2 * np.sum(V * N, -1, keepdims=True) * N - V
    occ = 1 - P.get('OccK', 0.0) * (1 - np.clip((R0[..., 2] + 0.02) / 0.12, 0, 1) ** 2 * (3 - 2 * np.clip((R0[..., 2] + 0.02) / 0.12, 0, 1)))
    bk = P.get('BendK', 0.3)
    for thr, k in ((0.05, 8), (0.03, 12)):
        R = V * 0 - V + 2 * (np.sum(V * N, -1, keepdims=True)) * N
        R = 2 * np.sum(V * N, -1, keepdims=True) * N - V
        wl = np.clip((thr - R[..., 2]) * k, 0, 1)[..., None] * bk
        N = N * (1 - wl) + np.array([0, 0, 1.0]) * wl; N /= np.linalg.norm(N, axis=-1, keepdims=True)
    R = 2 * np.sum(V * N, -1, keepdims=True) * N - V
    R[..., 2] = np.maximum(R[..., 2], 0.002); R /= np.linalg.norm(R, axis=-1, keepdims=True)
    # env lookup: project R into the camera frame
    fz = R @ F; rx = (R @ Rt) / np.maximum(fz, 1e-3); ry = (R @ Up) / np.maximum(fz, 1e-3)
    u = np.clip(1920 + rx * 1920, 0, 3839); v = np.clip(1080 - ry * 1920, 0, 2159)
    alpha = rough ** 2; sig = alpha * 1920 * 1.0
    li = np.interp(sig, SIG, np.arange(len(SIG)))
    l0 = np.floor(li).astype(int); fr = (li - l0)[..., None]
    env = np.zeros(u.shape + (3,), np.float32)
    ui, vi = u.astype(int), v.astype(int)
    for L in range(len(SIG)):
        m0 = l0 == L; m1 = (l0 + 1) == L
        if m0.any(): env[m0] += BL[L][vi[m0], ui[m0]] * (1 - fr[m0])
        if m1.any(): env[m1] += BL[L][vi[m1], ui[m1]] * fr[m1]
    cosi = np.clip(np.sum(V * N, -1), 0, 1)[..., None]
    F0 = (0.02 * P.get('SpecK', 1.0) * occ)[..., None]
    Fc = (1 - cosi) ** 5
    Fr = np.clip(50 * F0, 0, 1) * Fc + (1 - Fc) * F0     # UE F_Schlick / EnvBRDF: F0 < 0.02 also kills the grazing term
    body = np.asarray(P['_body'], np.float32) * P['ScatK'] / 0.2
    col = Fr * env * P['_envk'] + (1 - Fr) * body
    out = enc(col)
    if ss > 1: out = cv2.resize(out, (out.shape[1] // ss, out.shape[0] // ss), interpolation=cv2.INTER_AREA)
    return np.clip(out * 255, 0, 255), rough.mean()
def metrics(img):
    Y = ws.luma(img); hp = Y - cv2.GaussianBlur(Y, (0, 0), 8)
    return dict(mean=round(float(Y.mean()), 1), p1=round(float(np.percentile(Y, 1)), 1), p995=round(float(np.percentile(Y, 99.5)), 1), hp=round(float(hp.std()), 2), gl=round(float((Y >= 140).mean() * 100), 2))
if __name__ == '__main__':
    sys.path.insert(0, '/Users/midir/sm2-n1/water/unreal/WebHomage/Scripts')
    P = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    base = dict(ChopK=2.6, ScatK=0.2, BendK=0.3, _body=np.array([0.035, 0.032, 0.02]), _envk=1.0, RoughN=0.06, MicroK=1.0, SpecK=1.0)
    base.update(P)
    img, r = render(base, mode=sys.argv[1], ss=int(base.get('_ss', 1)))
    print(sys.argv[1], json.dumps({k: v for k, v in P.items()}), metrics(img), 'mean rough %.3f' % r)
    cv2.imwrite(S + 'emu_river_low_%s.png' % sys.argv[1], img.astype(np.uint8))
