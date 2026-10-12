#!/usr/bin/env python3
"""Paint the brute's base colour ON THE THUG UV LAYOUT (fan homage project; not official Marvel/Sony/Insomniac).

Why: the shipped `brute_basecolor.webp` was authored for a different UV layout than `thug.glb`, so every mesh section
sampled the wrong garment (skin through trousers, the thug's bandana dots on the back, a black head). The brute is the
thug mesh scaled up, so its texture has to use the thug's islands.

Inputs (all regenerable):
  - art/night1/characters/thug/tex/thug_basecolor.png        (tools/ue_char/extract_textures.py)
  - $P2_SCRATCH/r2/uvgeom.npz    (blender -b -P tools/ue_char/brute/uvgeom.py)
Outputs:
  - public/assets/enemies/brute_basecolor.webp               (the browser runs this; committed)
  - art/night1/characters/thug/tex/brute_basecolor.png       (UE import, git-ignored derived copy)
  - art/night1/characters/thug/tex/brute_regions.png         (R = face skin, G = hands, B = everything else; for the skin/white test)
  - <scratch>/brute_paint_debug.jpg                          (contact sheet)

usage: python3 tools/ue_char/brute/paint_brute.py [--geom NPZ] [--no-webp]
Islands are found from the mesh (dominant skin bone + rest-pose position), not from hard-coded ids, so a re-pack of the
thug UVs keeps working as long as the bone/zone rules hold. Colour values are sRGB 0-255.
"""
import os, sys, json, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); from p2paths import WT as _P2WT, scr as _scr  # noqa: E402
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
ART = os.path.join(ROOT, 'art/night1/characters/thug/tex')
SCR = _scr('r2')
ap = argparse.ArgumentParser()
ap.add_argument('--geom', default=SCR + '/uvgeom.npz')
ap.add_argument('--src', default=ART + '/thug_basecolor.png')
ap.add_argument('--no-webp', action='store_true')
ap.add_argument('--audit-png', default=None, help='only audit this texture (skin-like / white texels outside hands+face on the thug UVs), then exit')
ap.add_argument('--out-dir', default=ART)
ap.add_argument('--webp', default=os.path.join(ROOT, 'public/assets/enemies/brute_basecolor.webp'))
A = ap.parse_args()

N = 2048
rng = np.random.RandomState(20260930)

# ------------------------------------------------------------------ palette (sRGB)
VEST = np.array([50, 56, 40], np.float32)        # olive work jacket, body
VEST_DK = np.array([28, 32, 25], np.float32)     # collar, hem, yoke seams
SLEEVE = VEST * 1.04                              # same garment as the body: the torso/sleeve UV cut is jagged, so no colour step across it
SLEEVE_DK = np.array([32, 36, 27], np.float32)   # cuffs, elbow patches
TROUSER = np.array([42, 44, 52], np.float32)     # charcoal work trousers
TROUSER_WEAR = np.array([60, 62, 70], np.float32)
BOOT = np.array([40, 40, 43], np.float32)        # near-neutral dark work boots (a saturated brown would read as skin under sun)
BOOT_SOLE = np.array([20, 19, 18], np.float32)
LACE = np.array([80, 80, 80], np.float32)
BEANIE = np.array([58, 64, 40], np.float32)    # olive-green knit beanie (a khaki/tan one reads as skin-coloured in sun)
HAIR = np.array([32, 30, 32], np.float32)     # near-neutral dark hair (dark brown reads as skin-coloured in sun)
BANDANA = np.array([48, 50, 56], np.float32)     # plain slate bandana (no dot pattern)
BANDANA_PAT = np.array([70, 72, 80], np.float32)
STITCH = np.array([84, 84, 66], np.float32)
ZIP = np.array([104, 104, 96], np.float32)


def fbm(scale_px, octaves=4, seed=0):
    r = np.random.RandomState(seed)
    acc = np.zeros((N, N), np.float32); amp = 1.0; tot = 0.0
    for o in range(octaves):
        g = ndi.gaussian_filter(r.randn(N, N).astype(np.float32), scale_px / (2 ** o), mode='wrap')
        g /= g.std() + 1e-6
        acc += amp * g; tot += amp; amp *= 0.55
    return acc / tot


def soft(d, w=0.0012):
    """1 inside d<0, soft edge of w metres (~1.2 px at 1000 px/m)."""
    return np.clip(0.5 - d / w, 0.0, 1.0)


def band(c, lo, hi, w=0.0012):
    return soft(np.maximum(lo - c, c - hi), w)


def line(c, centre, half, w=0.0012):
    return soft(np.abs(c - centre) - half, w)


def rect_outline(x, z, x0, x1, z0, z1, t):
    outer = band(x, x0, x1) * band(z, z0, z1)
    inner = band(x, x0 + t, x1 - t) * band(z, z0 + t, z1 - t)
    return np.clip(outer - inner, 0, 1)


def mix(dst, col, a):
    return dst * (1 - a[..., None]) + np.asarray(col, np.float32) * a[..., None]


def lum(c):
    return c @ np.array([0.299, 0.587, 0.114], np.float32)


# ------------------------------------------------------------------ geometry maps
d = np.load(A.geom)
tris, bones = d['tris'], list(d['bones'])
# rasterise island id, rest position and dominant bone per texel
isl = np.full((N, N), -1, np.int16); pos = np.zeros((N, N, 3), np.float32); bone = np.full((N, N), -1, np.int16)
for r in tris:
    uv = r[1:7].reshape(3, 2).copy(); uv[:, 1] = 1 - uv[:, 1]; u = uv * N
    p = r[7:16].reshape(3, 3)
    x0 = max(int(np.floor(u[:, 0].min() - 0.5)), 0); x1 = min(int(np.ceil(u[:, 0].max() + 0.5)), N - 1)
    y0 = max(int(np.floor(u[:, 1].min() - 0.5)), 0); y1 = min(int(np.ceil(u[:, 1].max() + 0.5)), N - 1)
    if x1 < x0 or y1 < y0:
        continue
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, b, c = u
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-9:
        continue
    w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
    w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
    w2 = 1 - w0 - w1
    m = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
    if not m.any():
        continue
    P = w0[..., None] * p[0] + w1[..., None] * p[1] + w2[..., None] * p[2]
    sl = (slice(y0, y1 + 1), slice(x0, x1 + 1))
    isl[sl][m] = int(r[0]); pos[sl][m] = P[m]; bone[sl][m] = int(r[16])
covered = isl >= 0
X, Y, Z = pos[..., 0], pos[..., 1], pos[..., 2]

# island roles from bones + position (Blender axes: +Z up, -Y front, T-pose along X)
roles = {}
for iid in np.unique(isl[covered]):
    m = isl == iid
    if m.sum() < 500:
        continue
    names, cnt = np.unique(bone[m], return_counts=True)
    dom = bones[int(names[np.argmax(cnt)])]
    my, mz = float(Y[m].mean()), float(Z[m].mean())
    base = dom.split('.')[0]
    if base in ('hips', 'spine', 'spine1', 'spine2'):
        roles[iid] = 'torso_front' if my < 0 else 'torso_back'
    elif base == 'head' or base == 'neck':
        roles[iid] = 'head'
    elif base == 'thigh':
        roles[iid] = 'thigh'
    elif base == 'shin':
        roles[iid] = 'shin'
    elif base in ('upperArm', 'deltoid', 'shoulder'):
        roles[iid] = 'upperarm'
    elif base in ('forearm', 'forearmTwist'):
        roles[iid] = 'forearm'
    elif base in ('hand', 'thumb1', 'index1', 'middle1', 'ring1', 'pinky1'):
        roles[iid] = 'hand'
    elif base in ('foot', 'toe'):
        roles[iid] = 'sole' if mz < 0.03 else 'boot'
    else:
        roles[iid] = 'other:' + dom
R = lambda *names: np.isin(isl, [i for i, r in roles.items() if r in names])
print('roles', {int(k): v for k, v in sorted(roles.items())})
assert not any(v.startswith('other') for v in roles.values()), roles

src = np.array(Image.open(A.src).convert('RGB'), np.float32)
out = src.copy()
L_src = lum(src)

n1 = fbm(6, 4, 1); n2 = fbm(1.6, 3, 2); n3 = fbm(40, 3, 3)
weave = (np.sin(np.arange(N)[None, :] * 1.7) * np.sin(np.arange(N)[:, None] * 1.7)).astype(np.float32)


def fabric(col, strength=0.06, dirt=0.10):
    """flat colour + fine fbm grain + low-frequency grime (multiplies)."""
    f = 1 + strength * (0.7 * n2 + 0.5 * weave * 0.3) + 0.5 * strength * n1 + dirt * n3
    return col[None, None, :] * f[..., None]


# ------------------------------------------------------------------ torso: work vest / jacket
for role in ('torso_front', 'torso_back'):
    m = R(role)
    img = fabric(VEST, 0.05, 0.12)
    # keep the thug hoodie's painted pocket/fold lines (darker than the median) as subtle relief; drop its white drawstrings
    rel = np.clip(L_src / (np.median(L_src[m]) + 1e-6), 0.55, 1.0)
    img = img * (0.6 + 0.4 * rel)[..., None]
    hem = band(Z, -1, 0.885)
    img = mix(img, VEST_DK, hem * 0.9)
    collar = band(Z, 1.47, 3)
    img = mix(img, VEST_DK, collar * 0.9)
    if role == 'torso_front':
        img = mix(img, ZIP, line(X, 0.0, 0.0045) * band(Z, 0.87, 1.5) * 0.85)
        img = mix(img, VEST_DK, line(X, 0.0, 0.011) * band(Z, 0.87, 1.5) * 0.45)
        for sx in (1, -1):
            xs = sx * X                                   # chest pockets with flap + stitching
            img = mix(img, STITCH, rect_outline(xs, Z, 0.045, 0.18, 1.20, 1.34, 0.0035) * 0.55)
            img = mix(img, VEST_DK, band(xs, 0.045, 0.18) * band(Z, 1.315, 1.34) * 0.55)
    else:
        img = mix(img, VEST_DK, line(X, 0.0, 0.0035) * band(Z, 0.88, 1.47) * 0.8)              # centre-back seam
        img = mix(img, VEST_DK, band(Z, 1.385, 1.395) * 0.6)                                    # yoke
        img = mix(img, STITCH, band(Z, 1.397, 1.402) * 0.35)
    out[m] = img[m]

# ------------------------------------------------------------------ waist: jacket hem rib and belt live on the TORSO islands only (the pelvis is rigid with
# the torso; painting them on the thigh islands showed up as a strap across the swinging thigh). The torso's lowest part, which meets the
# jagged UV cut against the thigh islands, is trouser coloured so that cut is invisible.
BELT = np.array([24, 22, 21], np.float32)
BUCKLE = np.array([96, 94, 88], np.float32)
waist = R('torso_front', 'torso_back') & (Z > 0.80) & (Z < 1.02)
wimg = out.copy()
wimg = mix(wimg, VEST_DK, band(Z, 0.935, 0.985, 0.006) * 0.9)                                      # ribbed jacket hem
wimg = mix(wimg, BELT, band(Z, 0.90, 0.938, 0.004))                                                # belt
wimg = mix(wimg, (38, 36, 34), band(Z, 0.90, 0.938, 0.004) * line(Z, 0.919, 0.0018) * 0.8)         # belt stitching
wimg = mix(wimg, BUCKLE, band(X, -0.030, 0.030, 0.002) * band(Z, 0.902, 0.936, 0.002) * (Y < -0.05) * (1 - band(X, -0.020, 0.020, 0.002) * band(Z, 0.908, 0.930, 0.002) * 0.7))
wimg = mix(wimg, fabric(TROUSER, 0.05, 0.14), band(Z, 0.0, 0.896, 0.004))                          # trouser colour below the belt
out[waist] = wimg[waist]

# ------------------------------------------------------------------ sleeves
xa = np.abs(X)
m = R('upperarm')
img = fabric(SLEEVE, 0.06, 0.12)
img = mix(img, SLEEVE_DK, line(np.where(Y >= 0, Y, Y), -0.02, 0.003) * 0.5)   # long seam along the arm
img = mix(img, SLEEVE_DK, band(xa, 0.18, 0.215) * 0.55)                          # shoulder seam
out[m] = img[m]
m = R('forearm')
img = fabric(SLEEVE, 0.06, 0.12)
img = mix(img, SLEEVE_DK, band(xa, 0.335, 0.375) * 0.6)                          # elbow patch
img = mix(img, SLEEVE_DK, band(xa, 0.545, 0.60) * 0.95)                          # ribbed cuff
img = mix(img, STITCH, band(xa, 0.542, 0.5455) * 0.35)
out[m] = img[m]

# ------------------------------------------------------------------ trousers
for role in ('thigh', 'shin'):
    m = R(role)
    img = fabric(TROUSER, 0.05, 0.14)
    if role == 'thigh':
        img = mix(img, TROUSER_WEAR, band(Z, 0.62, 0.78, 0.10) * (0.25 + 0.2 * n3.clip(-1, 1)) * 0.45)
        img = mix(img, VEST_DK, line(xa, 0.0, 0.003) * 0.5)                                       # inseam
        img = mix(img, TROUSER_WEAR, rect_outline(xa, Z, 0.105, 0.215, 0.56, 0.74, 0.0035) * 0.7)  # cargo pocket
        img = mix(img, VEST_DK, band(xa, 0.105, 0.215) * band(Z, 0.72, 0.74) * 0.5)
    else:
        img = mix(img, TROUSER_WEAR, band(Z, 0.42, 0.54, 0.10) * (0.3 + 0.2 * n3.clip(-1, 1)) * 0.4)   # worn knees (soft: no ring around the leg)
        img = mix(img, (46, 42, 38), band(Z, -1, 0.14, 0.09) * 0.5)                                    # dirty hem over the boots (soft)
    out[m] = img[m]

# ------------------------------------------------------------------ boots (sneaker islands: white body, dark stripes, dark sole rim)
m = R('boot')
Ls = L_src
leather = fabric(BOOT, 0.05, 0.18)
light = Ls > 140
stripe = (~light) & (Ls < 100)
img = leather.copy()
# the source's dark border becomes the sole, its dark stripes become laces
edge = ndi.binary_erosion(light, iterations=1) ^ light
sole_zone = (~light)
lace_zone = ndi.binary_dilation(ndi.binary_closing(stripe & (Z > 0.05), iterations=6), iterations=1) & ndi.binary_fill_holes(light | stripe)
img = mix(img, BOOT_SOLE, sole_zone.astype(np.float32) * (Z < 0.05).astype(np.float32))
img = mix(img, LACE, (stripe & (Z > 0.05)).astype(np.float32) * 0.9)
img = mix(img, BOOT_SOLE, band(Z, -1, 0.03) * 0.9)
img = mix(img, (62, 62, 64), band(Z, 0.10, 0.16) * 0.5)      # boot collar highlight
out[m] = img[m]
m = R('sole')
out[m] = fabric(BOOT_SOLE, 0.05, 0.1)[m]

# ------------------------------------------------------------------ hands: source skin, slightly weathered (keeps island rim clean)
m = R('hand')
hand = src * (1 + 0.05 * n1[..., None] + 0.03 * n2[..., None])
out[m] = hand[m]

# ------------------------------------------------------------------ head: beanie + hair + plain bandana + skin around the eyes (source skin/eyes kept)
m = R('head')
r_, g_, b_ = src[..., 0], src[..., 1], src[..., 2]
red = (r_ > g_ + 55) & (r_ > 100) & (b_ < 90)                  # bandana body
bright = L_src > 150                                           # bandana dots/streaks and eye whites
skin = (np.abs(r_ - 176) < 38) & (np.abs(g_ - 122) < 34) & (np.abs(b_ - 92) < 38) & (r_ > g_) & (g_ > b_)
dark = L_src < 75
# eye zone: keep everything (skin, brows, eyes) within a radius of the eye centres
eyes = [(-0.0357, -0.0903, 1.668), (0.0360, -0.0902, 1.6655)]
eye_zone = np.zeros((N, N), bool); eye_white_zone = np.zeros((N, N), bool)
for ex, ey, ez in eyes:
    dd = np.sqrt((X - ex) ** 2 + (Y - ey) ** 2 + (Z - ez) ** 2)
    eye_zone |= dd < 0.030
    eye_white_zone |= dd < 0.0125
keep_face = m & (skin | (eye_zone & ~bright) | eye_white_zone) & ~red
bandana_zone = m & (red | (bright & ~eye_white_zone))
# grow the bandana over the anti-aliased dark-red rim
rim = m & ~keep_face & ~dark & ~bandana_zone & (r_ > 70) & (r_ > g_ + 25)
bandana_zone |= rim
cap = m & (dark | (Z > 1.70)) & ~keep_face & ~bandana_zone
# beanie (top/side, ribbed) vs hair (back of head below the beanie rim): beanie above z=1.64 or ribbed radial lines near the crown
beanie_zone = cap & ((Z > 1.665) | (Y < -0.0))
beanie_zone |= m & (Z > 1.70)
hair_zone = cap & ~beanie_zone
img = out.copy()
rib = np.clip((L_src - 26.0) / 6.0, -1, 1)                                         # the thug beanie's rib pattern (few levels of luma)
bean = fabric(BEANIE, 0.05, 0.10) * (1 + 0.08 * rib[..., None])
img[beanie_zone] = bean[beanie_zone]
img[hair_zone] = fabric(HAIR, 0.10, 0.2)[hair_zone]
pat = np.clip((L_src - 60) / 160.0, 0, 1)
band_img = fabric(BANDANA, 0.05, 0.08)
band_img = mix(band_img, BANDANA_PAT, (bright & bandana_zone).astype(np.float32) * 0.55)   # dots become a faint paisley, not white
img[bandana_zone] = band_img[bandana_zone]
# face: source skin with a heavier brow shadow + slight stubble grain (keeps the original eyes)
face = src * (1 + 0.05 * n2[..., None])
brow_shadow = np.zeros((N, N), np.float32)
for ex, ey, ez in eyes:
    dd = np.sqrt((X - ex) ** 2 + (Y - ey) ** 2 + (Z - (ez + 0.014)) ** 2)
    brow_shadow = np.maximum(brow_shadow, np.clip(1 - dd / 0.018, 0, 1))
face = face * (1 - 0.30 * brow_shadow[..., None])
img[keep_face] = face[keep_face]
out[m] = img[m]

def hsv(a):
    a = a / 255.0
    mx, mn = a.max(-1), a.min(-1)
    dlt = mx - mn + 1e-9
    h = np.where(mx == a[..., 0], ((a[..., 1] - a[..., 2]) / dlt) % 6, np.where(mx == a[..., 1], (a[..., 2] - a[..., 0]) / dlt + 2, (a[..., 0] - a[..., 1]) / dlt + 4)) * 60
    return h, np.where(mx > 0, (mx - mn) / (mx + 1e-9), 0), mx


def audit_texture(tex):
    h, s_, v = hsv(tex)
    skin_like = (h >= 8) & (h <= 38) & (s_ >= 0.22) & (s_ <= 0.65) & (v >= 0.42)
    white_like = (v >= 0.80) & (s_ <= 0.18)
    allowed = (keep_face & m) | R('hand')
    return dict(cloth_texels=int((covered & ~allowed).sum()),
                skin_like_outside=int((skin_like & covered & ~allowed).sum()),
                white_like_outside=int((white_like & covered & ~allowed).sum()),
                white_like_in_face_or_hands=int((white_like & covered & allowed).sum())), skin_like, allowed


if A.audit_png:
    print('audit', A.audit_png, audit_texture(np.array(Image.open(A.audit_png).convert('RGB'), np.float32))[0])
    sys.exit(0)

# ------------------------------------------------------------------ gutters: extend island colours outward (no lavender bleed into mips)
edt_d, (iy, ix) = ndi.distance_transform_edt(~covered, return_indices=True)
filled = out[iy, ix]
grow = ndi.binary_dilation(covered, iterations=2)          # 1-2 px inside the UV border also repainted from neighbours
res = np.where(covered[..., None], out, filled)
res = np.clip(res, 0, 255)
res_img = Image.fromarray(res.astype(np.uint8))
os.makedirs(A.out_dir, exist_ok=True)
res_img.save(os.path.join(A.out_dir, 'brute_basecolor.png'))

# region mask for the skin/white test: R face skin (skin + eyes), G hands, B everything else
reg = np.zeros((N, N, 3), np.uint8)
reg[..., 2] = 255
face_reg = keep_face & m
hand_reg = R('hand')
reg[face_reg] = (255, 0, 0)
reg[hand_reg] = (0, 255, 0)
reg = np.where(covered[..., None], reg, reg[iy, ix])
Image.fromarray(reg).save(os.path.join(A.out_dir, 'brute_regions.png'))

# texture-level audit: skin-coloured or white texels outside hands/face
audit, skin_like, allowed = audit_texture(res)
face_reg = keep_face & m
hand_reg = R('hand')
print('texture audit', audit)
json.dump(audit, open(os.path.join(SCR, 'brute_texture_audit.json'), 'w'), indent=1)
if not A.no_webp:
    res_img.save(A.webp, 'WEBP', quality=90, method=6)
    print('webp', os.path.getsize(A.webp) // 1024, 'KB ->', A.webp)
sheet = Image.new('RGB', (2048, 1024))
sheet.paste(res_img.resize((1024, 1024)), (0, 0)); sheet.paste(Image.fromarray(reg).resize((1024, 1024)), (1024, 0))
sheet.save(os.path.join(SCR, 'brute_paint_debug.jpg'), quality=88)

if os.environ.get('BRUTE_DEBUG'):
    bad = skin_like & covered & ~allowed
    for iid, role in sorted(roles.items()):
        c = int((bad & (isl == iid)).sum())
        if c:
            print('  skin-like outside allowed in island', iid, role, c)

if os.environ.get('BRUTE_IDTEX'):
    cols = {'torso_front': (255, 0, 0), 'torso_back': (0, 255, 0), 'head': (0, 0, 255), 'upperarm': (255, 255, 0), 'forearm': (0, 255, 255),
            'thigh': (255, 0, 255), 'shin': (255, 128, 0), 'boot': (255, 255, 255), 'sole': (128, 128, 128), 'hand': (128, 0, 255)}
    idt = np.zeros((N, N, 3), np.uint8)
    for iid, role in roles.items():
        idt[isl == iid] = cols[role]
    idt = np.where(covered[..., None], idt, idt[iy, ix])
    Image.fromarray(idt).save(SCR + '/brute_idtex.png')

if os.environ.get('BRUTE_ZTEX'):
    zt = np.zeros((N, N, 3), np.uint8)
    bands = [(-9, 0.5, (255, 0, 0)), (0.5, 0.9, (0, 255, 0)), (0.9, 1.2, (0, 0, 255)), (1.2, 1.47, (255, 255, 0)), (1.47, 1.6, (0, 255, 255)), (1.6, 9, (255, 0, 255))]
    for lo, hi, c in bands:
        zt[(Z >= lo) & (Z < hi)] = c
    zt = np.where(covered[..., None], zt, zt[iy, ix])
    Image.fromarray(zt).save(SCR + '/brute_ztex.png')

if os.environ.get('BRUTE_PROBE'):
    for role in ('torso_front', 'torso_back'):
        for lo, hi in ((1.47, 1.7), (1.2, 1.47), (0.9, 1.2), (0, 0.9)):
            mm = R(role) & (Z >= lo) & (Z < hi)
            if mm.any():
                print(role, lo, hi, mm.sum(), res[mm].mean(0).astype(int))
