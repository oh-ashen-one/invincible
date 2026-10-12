# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Generated inputs of the river water (round 02), used by unreal/WebHomage/Scripts/build_water.py (step 'inputs').

slope_texture(path)        T_WaterSlope: tileable 1024^2 RGBA8, two independent random-phase realizations of a wind-sea slope
                           spectrum (RG = d h / d x, d h / d y of realization A; BA = realization B), unit RMS per axis encoded as
                           0.5 + s / 6. Elevation spectrum F(k) ~ k^-4 (saturation range: equal slope variance per octave) on 3..24
                           cycles per tile, directional spread cos^4(theta / 2) around +x. Replaces round 01's 12 analytic capillary
                           sinusoids, whose sum formed a regular lattice (the critic's ring artifact / 0.25 autocorrelation at 80 px).
contact_map(export, png)   T_WaterContact: distance (m, 0..32 -> 0..255) from every water point to the nearest place where exported
                           geometry crosses the water plane (seawalls, bulkheads, pier piles, bridge piers), rasterised from the city
                           export's GLBs at 0.5 m/px (coarser only if the export is larger than 4 km). Feeds the contact foam; the
                           depth-based foam (SceneDepthWithoutWater) did not show in round 01.
Pure numpy + opencv; deterministic (fixed seeds)."""
import glob, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'export'))

SLOPE_N = 1024
SLOPE_K = (3, 24)          # cycles per tile
SLOPE_ENC = 6.0            # unit-RMS slope s -> 0.5 + s / SLOPE_ENC
WATER_Y = -1.6             # browser G.WATER_Y (m)
CONTACT_MAX = 32.0         # metres encoded in the contact map


def _realization(seed, n=SLOPE_N, k0=SLOPE_K[0], k1=SLOPE_K[1]):
    rng = np.random.default_rng(seed)
    f = np.fft.fftfreq(n) * n
    kx, ky = np.meshgrid(f, f)              # kx varies along columns (x), ky along rows (y)
    k = np.hypot(kx, ky)
    th = np.arctan2(ky, kx)
    band = (k >= k0) & (k <= k1)
    amp = np.where(band, np.maximum(k, 1e-6) ** -2.0, 0.0) * np.cos(th * 0.5) ** 4   # |H| ~ k^-2 -> F ~ k^-4; spread cos^4(theta/2)
    # soft band edges (no ringing in the spatial domain)
    amp *= np.clip((k - k0 + 1.0) / 2.0, 0, 1) * np.clip((k1 + 1.0 - k) / 4.0, 0, 1)
    H = amp * (rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n)))
    h = np.real(np.fft.ifft2(H))
    Hh = np.fft.fft2(h)                     # hermitian-symmetric spectrum of the real field
    sx = np.real(np.fft.ifft2(1j * kx * Hh)); sy = np.real(np.fft.ifft2(1j * ky * Hh))
    sc = 1.0 / max(sx.std(), sy.std())
    return sx * sc, sy * sc


CHOP_N = 512
CHOP_K = (3, 10)           # cycles per tile: on a 1.5 m tile = 0.15 .. 0.5 m wind chop (r03)


def chop_texture(path):
    """r03 T_WaterChop: the resolved 0.15-0.5 m wind-chop slope layer (two realizations, broad short-crested spread cos^2(theta/2)),
    same encoding as T_WaterSlope. Sampled without mip bias in the near field (<= 150 m) and never turned into roughness there."""
    import cv2
    def real(seed):
        rng = np.random.default_rng(seed); n = CHOP_N; k0, k1 = CHOP_K
        f = np.fft.fftfreq(n) * n
        kx, ky = np.meshgrid(f, f); k = np.hypot(kx, ky); th = np.arctan2(ky, kx)
        amp = np.where((k >= k0) & (k <= k1), np.maximum(k, 1e-6) ** -2.0, 0.0) * np.cos(th * 0.5) ** 2
        amp *= np.clip((k - k0 + 1.0) / 2.0, 0, 1) * np.clip((k1 + 1.0 - k) / 2.0, 0, 1)
        H = amp * (rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n)))
        Hh = np.fft.fft2(np.real(np.fft.ifft2(H)))
        sx = np.real(np.fft.ifft2(1j * kx * Hh)); sy = np.real(np.fft.ifft2(1j * ky * Hh))
        sc = 1.0 / max(sx.std(), sy.std())
        return sx * sc, sy * sc
    ax, ay = real(9101); bx, by = real(9102)
    enc = lambda s: np.clip(0.5 + s / SLOPE_ENC, 0.0, 1.0)
    rgba = np.stack([enc(ax), enc(ay), enc(bx), enc(by)], -1)
    cv2.imwrite(path, (rgba * 255.0 + 0.5).astype(np.uint8)[..., [2, 1, 0, 3]])
    return dict(n=CHOP_N, k=list(CHOP_K), rms_x=float(ax.std()), rms_y=float(ay.std()))


def slope_texture(path):
    import cv2
    ax, ay = _realization(9001); bx, by = _realization(9002)
    enc = lambda s: np.clip(0.5 + s / SLOPE_ENC, 0.0, 1.0)
    rgba = np.stack([enc(ax), enc(ay), enc(bx), enc(by)], -1)
    cv2.imwrite(path, (rgba * 255.0 + 0.5).astype(np.uint8)[..., [2, 1, 0, 3]])   # cv2 writes BGRA
    clip = float(np.mean(np.abs(np.stack([ax, ay, bx, by])) > SLOPE_ENC * 0.5) * 100)
    return dict(n=SLOPE_N, k=list(SLOPE_K), enc=SLOPE_ENC, rms_x=float(ax.std()), rms_y=float(ay.std()), clipped_pct=clip)


SKIP = ('farCityMass', 'horizonSkirt', 'farsky', 'facade', 'roofs', 'signage', 'markings', 'asphalt', 'sidewalk', 'streetkit',
        'coast_f', 'farLand', 'palisades')   # far shores (NJ / Brooklyn / Queens, >= 1.2 km from the island) get no contact foam


def contact_map(export_dir, png_path, px_min=0.5, max_px=8192):
    # 8192 px on the long side: ~1.1 m/px for the whole island's shore (bilinear distance keeps the band edge smooth)
    """-> dict(box=[x0, z0, w, h] browser metres (UE X = x, UE Y = z), px, segments, files)"""
    import cv2, glbio
    # positions in the export are relative to each mesh's tile centre (manifest.json 'center', browser metres)
    man = json.load(open(os.path.join(export_dir, 'manifest.json')))
    ents = [(os.path.join(export_dir, m['file']), m.get('center', [0, 0, 0])) for m in man['meshes']
            if not os.path.basename(m['file']).startswith(SKIP) and os.path.exists(os.path.join(export_dir, m['file']))]
    segs, used, core = [], [], []
    for f, ctr in ents:
        try:
            g = glbio.read_glb(f)
        except Exception:
            continue
        P = g['attrs']['POSITION'] + np.asarray(ctr, float)[None, :]; I = g['index'].reshape(-1, 3)
        if P[:, 1].min() > WATER_Y or P[:, 1].max() < WATER_Y: continue
        d = P[:, 1] - WATER_Y
        D = d[I]
        cross = (D.min(1) < 0) & (D.max(1) > 0)
        if not cross.any(): continue
        T = I[cross]; Dt = D[cross]
        out = []
        for a, b in ((0, 1), (1, 2), (2, 0)):              # edge crossings: each crossing triangle has exactly two
            da, db = Dt[:, a], Dt[:, b]
            m = (da < 0) != (db < 0)
            u = np.where(m, da / np.where(m, da - db, 1.0), np.nan)
            pa, pb = P[T[:, a]], P[T[:, b]]
            out.append(np.where(m[:, None], pa + (pb - pa) * u[:, None], np.nan)[:, [0, 2]])
        E = np.stack(out, 1)                                # (n, 3 edges, 2)
        ok = np.isfinite(E[..., 0])
        two = ok.sum(1) == 2
        E, ok = E[two], ok[two]
        pts = E[ok].reshape(-1, 2, 2)
        segs.append(pts); used.append(os.path.basename(f)); core.append(os.path.basename(f).startswith(('coast_m', 'seawall')))
    if not segs: raise SystemExit('contact_map: no geometry crosses the water plane in ' + export_dir)
    # map box = the island's own shore (coast_m* + seawalls) + 200 m; far bulkheads / bridge piers outside it are dropped
    C = np.concatenate([s for s, c in zip(segs, core) if c] or segs).reshape(-1, 2)
    lo = C.min(0) - 200.0; hi = C.max(0) + 200.0
    S = np.concatenate(segs)
    S = S[((S >= lo) & (S <= hi)).all(axis=(1, 2))]
    px = max(px_min, float((hi - lo).max()) / max_px)
    nw, nh = int(math.ceil((hi[0] - lo[0]) / px)), int(math.ceil((hi[1] - lo[1]) / px))
    img = np.full((nh, nw), 255, np.uint8)
    Q = np.round((S - lo) / px * 16).astype(np.int64)
    for (x0, z0), (x1, z1) in Q:
        cv2.line(img, (int(x0), int(z0)), (int(x1), int(z1)), 0, 1, cv2.LINE_8, 4)
    dist = cv2.distanceTransform(img, cv2.DIST_L2, 5) * px
    cv2.imwrite(png_path, np.clip(dist / CONTACT_MAX * 255.0 + 0.5, 0, 255).astype(np.uint8))
    return dict(box=[float(lo[0]), float(lo[1]), nw * px, nh * px], px=px, size=[nw, nh], segments=int(len(S)), files=used)


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--slope'); ap.add_argument('--chop'); ap.add_argument('--contact', nargs=2, metavar=('EXPORT_DIR', 'PNG'))
    a = ap.parse_args()
    if a.slope: print(json.dumps(slope_texture(a.slope)))
    if a.chop: print(json.dumps(chop_texture(a.chop)))
    if a.contact: print(json.dumps({k: v for k, v in contact_map(*a.contact).items() if k != 'files'}))
