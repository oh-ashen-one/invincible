"""Texture pass for one AI suit: cleaned basecolor, height (for the normal bake), ORM.

    python3 tools/ue_char/suitmaps/build_maps.py <suit> [--no-delight]

Inputs: the Tripo source's 8K basecolor (_scratch/.../<suit>_src8k.png, same UVs as the fitted skin) and the geometry
maps from bake_base.py (mask, pos, onrm, ao). Outputs in _scratch/characters/suits/<suit>/:
  bc.png      4096 basecolor: back emblem painted out (Gemini/Qwen), mild top-light removal, gutters re-dilated
  height.png  4096 16-bit height, height.json its scale in metres (panel/piping/emblem relief + fine luminance detail)
  orm.png     4096 R = baked AO, G = roughness, B = metalness (glTF / UE packing)
  roles.png   preview of the material-role classification
Material roles come from a per-suit palette (nearest colour in Lab, soft-assigned); lenses are found geometrically
(eye box on the mask front) because their colour repeats elsewhere on the suit.

Homage fan project, not an official Marvel/Sony/Insomniac product.
"""
import os, sys, json
os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
import numpy as np, cv2
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SCRATCH  # noqa: E402
Image.MAX_IMAGE_PIXELS = None
R = 4096

# role: (sRGB ref, roughness, metalness, relief mm)
PAL = {
    'claude': {'head': 'fabric', 'lens_metal': 0.0, 'refs': [
        ('fabric', (0.16, 0.13, 0.16), 0.74, 0.0, 0.0), ('fabric_b', (0.13, 0.13, 0.17), 0.74, 0.0, 0.0),
        ('rubber', (0.62, 0.27, 0.24), 0.36, 0.0, 0.5), ('rubber_2', (0.64, 0.27, 0.23), 0.36, 0.0, 0.5),
        ('rubber_dk', (0.44, 0.20, 0.20), 0.45, 0.0, 0.3)]},
    'codex': {'head': 'fabric', 'lens_metal': 0.6, 'refs': [
        ('fabric', (0.84, 0.83, 0.86), 0.70, 0.0, 0.0), ('fabric_2', (0.88, 0.87, 0.90), 0.70, 0.0, 0.0),
        ('fabric_sh', (0.77, 0.76, 0.79), 0.68, 0.0, 0.0), ('rubber', (0.08, 0.07, 0.08), 0.34, 0.0, 0.5),
        ('grey', (0.61, 0.61, 0.62), 0.45, 0.0, 0.2), ('rubber_2', (0.23, 0.23, 0.24), 0.40, 0.0, 0.4)]},
    'gemini': {'head': 'red', 'lens_metal': 0.6, 'refs': [
        ('red', (0.64, 0.02, 0.14), 0.45, 0.0, 0.0), ('blue', (0.07, 0.16, 0.43), 0.45, 0.0, 0.0),
        ('silver', (0.68, 0.66, 0.69), 0.30, 0.85, 0.8), ('purple', (0.44, 0.26, 0.75), 0.32, 0.0, 0.6),
        ('purple_dk', (0.27, 0.09, 0.33), 0.45, 0.0, 0.0), ('magenta', (0.48, 0.15, 0.28), 0.45, 0.0, 0.0)]},
    'kimi': {'head': 'crimson', 'lens_metal': 0.3, 'refs': [
        ('navy', (0.12, 0.16, 0.32), 0.60, 0.0, 0.0), ('crimson', (0.48, 0.05, 0.22), 0.55, 0.0, 0.0),
        ('crimson_dk', (0.33, 0.05, 0.17), 0.58, 0.0, 0.0), ('piping', (0.09, 0.08, 0.10), 0.38, 0.0, 0.3),
        ('gold', (0.88, 0.49, 0.14), 0.30, 0.80, 0.5), ('white', (0.86, 0.86, 0.86), 0.35, 0.0, 0.3)]},
    'qwen': {'head': 'red', 'lens_metal': 0.0, 'refs': [
        ('red', (0.80, 0.03, 0.14), 0.55, 0.0, 0.0), ('blue', (0.10, 0.22, 0.70), 0.55, 0.0, 0.0),
        ('violet', (0.51, 0.18, 0.71), 0.32, 0.0, 0.6), ('violet_2', (0.52, 0.18, 0.85), 0.32, 0.0, 0.6),
        ('violet_3', (0.51, 0.20, 0.62), 0.35, 0.0, 0.5), ('magenta', (0.68, 0.07, 0.34), 0.50, 0.0, 0.2)]},
}
# back emblem paint-out: band (x0, x1, y0, y1 in bind-pose metres) and roles to replace with the fill role
BACK = {'gemini': ((-0.28, 0.28, 0.98, 1.56), ('purple', 'purple_dk', 'magenta'), 'red'),
        'qwen': ((-0.16, 0.16, 1.16, 1.50), ('violet', 'violet_2', 'violet_3', 'magenta'), 'red')}
# optional disc (x, y, radius m) limiting the paint-out, so piping around the back panels survives
BACK_DISC = {'qwen': (0.0, 1.334, 0.11)}


def lab_of(rgb01):
    return cv2.cvtColor(np.asarray(rgb01, np.float32).reshape(-1, 1, 3), cv2.COLOR_RGB2LAB).reshape(-1, 3)


def fill_gutters(img, mask):
    """Every texel outside `mask` takes the value of the nearest texel inside (re-dilation)."""
    _, (iy, ix) = ndimage.distance_transform_edt(~mask, return_indices=True)
    return img[iy, ix]


def main():
    suit = sys.argv[1]; cfg = PAL[suit]
    d = os.path.join(SCRATCH, suit)
    rd = lambda f: cv2.imread(os.path.join(d, f), cv2.IMREAD_UNCHANGED)
    mask = rd('mask.png')[..., 0] > 127
    pos = rd('pos.exr')[..., ::-1].astype(np.float32); onrm = rd('onrm.exr')[..., ::-1].astype(np.float32)
    ao = rd('ao.png')[..., 0].astype(np.float32) / 255
    src = Image.open(os.path.join(SCRATCH, f'{suit}_src8k.png')).convert('RGB')
    bc = np.array(src.resize((R, R), Image.BOX)).astype(np.float32) / 255     # area-filtered 8K -> 4K
    lab = cv2.cvtColor(bc, cv2.COLOR_RGB2LAB)
    info = {'suit': suit}

    # ---------------- role classification (soft) ----------------
    names = [r[0] for r in cfg['refs']]
    refl = lab_of([r[1] for r in cfg['refs']])
    wl = np.array([1.0, 1.0, 1.0], np.float32); wl[0] = 0.6          # lightness matters less than chroma
    d2 = (((lab[:, :, None, :] - refl[None, None]) * wl) ** 2).sum(-1)  # R,R,K
    dmin = d2.min(-1, keepdims=True)
    w = np.exp(-(d2 - dmin) / (2 * 6.0 ** 2)); w /= w.sum(-1, keepdims=True)
    hard = d2.argmin(-1)

    # ---------------- back emblem paint-out ----------------
    painted = np.zeros((R, R), bool)
    if suit in BACK:
        (x0, x1, y0, y1), bad, fill = BACK[suit]
        band = mask & (pos[..., 0] > x0) & (pos[..., 0] < x1) & (pos[..., 1] > y0) & (pos[..., 1] < y1) \
            & (onrm[..., 2] < -0.25) & (pos[..., 2] < -0.02)
        if suit in BACK_DISC:
            cx, cy, cr = BACK_DISC[suit]
            band &= np.hypot(pos[..., 0] - cx, pos[..., 1] - cy) < cr
        badm = band & np.isin(hard, [names.index(b) for b in bad])
        badm = cv2.dilate(badm.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2).astype(bool) & band
        fi = names.index(fill)
        ref = bc[band & (hard == fi)]
        fill_rgb = np.median(ref, 0) if len(ref) > 100 else np.array(cfg['refs'][fi][1], np.float32)
        # keep fine luminance texture of the fabric: add the high-pass of the fill-role texels' lightness
        Lhp = lab[..., 0] - cv2.GaussianBlur(lab[..., 0], (0, 0), 3)
        flab = lab_of(fill_rgb)[0]
        rep = np.zeros_like(lab); rep[..., 0] = flab[0] + np.clip(Lhp, -2, 2) * 0.3; rep[..., 1] = flab[1]; rep[..., 2] = flab[2]
        a = cv2.GaussianBlur(badm.astype(np.float32), (0, 0), 1.2) * band
        lab = lab * (1 - a[..., None]) + rep * a[..., None]
        onehot = np.zeros(len(names), np.float32); onehot[fi] = 1
        w = w * (1 - a[..., None]) + onehot * a[..., None]
        painted = a > 0.5
        info['back_painted_texels'] = int(painted.sum())
        info['back_fill_rgb'] = [round(float(c), 3) for c in fill_rgb]
        print(f'{suit}: painted out {painted.sum()} back-emblem texels ({painted.sum() / band.sum() * 100:.1f}% of band)')

    # ---------------- lenses (geometric eye box on the mask front) ----------------
    eye = mask & (pos[..., 1] > 1.58) & (pos[..., 1] < 1.72) & (pos[..., 2] > 0.04) & (onrm[..., 2] > 0.15) \
        & (np.abs(pos[..., 0]) > 0.008) & (np.abs(pos[..., 0]) < 0.085)
    head_ref = refl[names.index(cfg['head'])]
    far = np.sqrt((((lab - head_ref) * wl) ** 2).sum(-1)) > 22
    lens = eye & far
    lens = cv2.morphologyEx(lens.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)).astype(bool)
    lensw = cv2.GaussianBlur(lens.astype(np.float32), (0, 0), 0.8)
    info['lens_texels'] = int(lens.sum())
    print(f'{suit}: lens texels {lens.sum()}')

    # ---------------- mild top-light removal (Tripo bakes a soft overhead light into the colour) ----------------
    delight = '--no-delight' not in sys.argv
    if delight:
        ny = cv2.GaussianBlur(onrm[..., 1], (0, 0), 2)
        big = mask & ~painted
        # relative lightness change per unit n.y, fitted over the whole suit (clusters differ little; see analyze.py)
        L = lab[..., 0][big]; D = np.stack([np.ones(big.sum()), ny[big]], 1)
        # regress L on n.y within each hard role and pool relative slopes, weighted by coverage
        slopes, wts = [], []
        for k in range(len(names)):
            s = big & (hard == k)
            if s.sum() < 20000: continue
            Lk = lab[..., 0][s]; Dk = np.stack([np.ones(s.sum()), ny[s]], 1)
            c, *_ = np.linalg.lstsq(Dk, Lk, rcond=None)
            slopes.append(c[1] / max(c[0], 1)); wts.append(s.sum())
        rel = float(np.average(slopes, weights=wts)) if slopes else 0.0
        k = 0.7 * rel
        lab[..., 0] = lab[..., 0] / (1 + k * ny)
        info['delight_rel_slope_per_ny'] = round(rel, 4); info['delight_applied'] = round(k, 4)
        print(f'{suit}: top-light relative slope {rel:.3f} per unit n.y, removing {k:.3f}')

    out_bc = np.clip(cv2.cvtColor(lab.astype(np.float32), cv2.COLOR_LAB2RGB), 0, 1)
    out_bc = fill_gutters(out_bc, cv2.erode(mask.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool))

    # ---------------- roughness / metal / relief ----------------
    rough = (w * np.array([r[2] for r in cfg['refs']], np.float32)).sum(-1)
    metal = (w * np.array([r[3] for r in cfg['refs']], np.float32)).sum(-1)
    relief = (w * np.array([r[4] for r in cfg['refs']], np.float32)).sum(-1)
    L0 = cv2.cvtColor(out_bc, cv2.COLOR_RGB2LAB)[..., 0]
    dog = cv2.GaussianBlur(L0, (0, 0), 0.8) - cv2.GaussianBlur(L0, (0, 0), 4.0)
    rough = rough + np.clip(dog / 12, -1, 1) * -0.05        # brighter specks slightly smoother (wear / sheen)
    rough = rough * (1 - lensw) + 0.12 * lensw
    metal = metal * (1 - lensw) + cfg['lens_metal'] * lensw
    relief = relief * (1 - lensw) + 0.5 * lensw
    relief = cv2.GaussianBlur(relief, (0, 0), 0.9)
    height_mm = relief + np.clip(dog, -15, 15) * 0.02        # 10 L units of fine detail ~ 0.2 mm
    m2 = cv2.erode(mask.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    height_mm = fill_gutters(height_mm, m2); rough = fill_gutters(np.clip(rough, 0.05, 1), m2)
    metal = fill_gutters(np.clip(metal, 0, 1), m2)
    ao_c = fill_gutters(np.clip(ao, 0, 1) ** 0.8, m2)          # bind-pose AO, softened a touch

    hmin, hmax = float(height_mm.min()), float(height_mm.max())
    h16 = ((height_mm - hmin) / max(hmax - hmin, 1e-6) * 65535).astype(np.uint16)
    cv2.imwrite(os.path.join(d, 'height.png'), h16)
    info['height_m'] = {'min': hmin / 1000, 'max': hmax / 1000}
    orm = np.stack([ao_c, rough, metal], -1)
    Image.fromarray((out_bc * 255 + 0.5).astype(np.uint8)).save(os.path.join(d, 'bc.png'))
    Image.fromarray((orm * 255 + 0.5).astype(np.uint8)).save(os.path.join(d, 'orm.png'))
    pal = np.array([r[1] for r in cfg['refs']], np.float32)
    rolev = pal[hard]; rolev[lens] = (0, 1, 0); rolev[painted] = (1, 1, 0); rolev[~mask] = 0
    Image.fromarray((rolev * 255).astype(np.uint8)).resize((1024, 1024), Image.NEAREST).save(os.path.join(d, 'roles.png'))
    info['roughness_mean_in_mask'] = round(float(rough[mask].mean()), 3)
    info['metal_frac_in_mask'] = round(float((metal[mask] > 0.5).mean()), 4)
    json.dump(info, open(os.path.join(d, 'maps.json'), 'w'), indent=1)
    print(suit, json.dumps(info))


if __name__ == '__main__':
    main()
