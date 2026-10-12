#!/usr/bin/env python3
"""Dress a raw Tripo person as a street criminal and write a game-oriented static GLB for tools/skinfit/skinfit.py.

Fan homage project; not official Marvel/Sony/Insomniac; no affiliation. Sources are the owner's existing Tripo people
(~/sm2-assets/raw/*.glb, never committed). What this does, per character (see CFG):
  1. rotates the raw mesh (faces +X, arms along Z) to the game's frame (faces +Z, +X = left) and scales it to the hero's height;
  2. rasterises the UV layout into a per-texel 3D position map, so every texture edit is placed by body position, not by guesswork;
  3. fixes the seam artefacts: the raw atlas is thousands of islands with blurry inpainted gaps; the gaps are replaced by
     nearest-island colour (no dark dashes / sparkles at seams under mip filtering);
  4. recolours / removes items (brute: orange beanie -> charcoal knit, red-green plaid -> one flannel tone, pom-pom pulled onto the dome;
     thug: ornamental belt buckle and key-chain metal -> plain dark steel);
  5. round 04: the face mask is the head surface itself (tools/ue_char/people/mask.py): lower face / neck subdivided once and draped
     over the convex hull of the front of the head (spans nose -> cheeks and chin -> collar), cloth painted by 3D position with a
     stitched hem, a tie band round the back of the head, ears left bare; UV-island seams blended by 3D position; brute beanie
     knit + soft edge, plaid remnants cleared; chest print removed where a tee carries one; optional cap (raw Tripo cap fitted on
     the head, procedural twill in the accessory strip) and tint variants (extra atlases, same mesh);
  6. writes a 4096x4096 atlas (raw atlas squeezed to 4096x3584 + 512-px accessory strip) into ONE primitive / ONE material.
     (build_bandana / bandana_strip are the round-03 shell, kept for reference, no longer called.)

usage: python3 tools/ue_char/people/prepare_person.py thug|brute|hood|tee|beard [--out DIR]
"""
import os, sys, argparse, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); from p2paths import WT as _P2WT, scr as _scr, RAW as _P2RAW  # noqa: E402
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gltfio, skinfit, mask as M  # noqa: E402
import hair as HR  # noqa: E402   round 11: one hair asset per head (tools/ue_char/people/hair.py)

ROOT = os.path.abspath(os.path.join(HERE, '../../..'))
RAW = _P2RAW
SCR = _scr('r3')   # scratch, regenerated
ATLAS = 4096
SIZES = json.load(open(os.path.join(HERE, 'people.json')))
CONTENT_H = 3584            # raw atlas is squeezed into rows [0, 3584); rows [3584, 4096) hold the accessory strip (cap)

CFG = {
    'thug': dict(src='leather+jacket+man+3d+model.glb', name='StreetThug',
                 # landmarks measured on the normalised mesh with tools/ue_char/people/ortho.py (metres)
                 eye=1.652, nose=1.620, ear_lobe=1.591, chin=1.535, axis_z=-0.02,
                 mask=(38, 42, 60), seed=11, sink_neck=True, soften_neck=True,   # collar_dark=(42, 40, 42) was tried (offline): no visible effect, not built into the round-08 content; round 09: the wedge is fixed AFTER skinfit by nape_fix.py (build_people.sh)
                 tints={'Oxblood': dict(region='jacket', color=(58, 26, 24), mask_color=(30, 52, 44))}),   # round 05: the tint also swaps the mask (no near-twin with the base thug)
    'brute': dict(src='human+character+3d+model.glb', name='StreetBrute',
                  eye=1.616, nose=1.587, ear_lobe=1.563, chin=1.472, axis_z=-0.02,
                  mask=(66, 24, 22), seed=23, bot_drop=0.004),
    # round 04: three more raw Tripo people (owner's assets), landmarks from mask.auto_landmarks
    # hood: auto landmarks pick the sunglasses as the nose -> measured with ortho.py (side view, 2 cm grid)
    'hood': dict(src='human+figure+3d+model.glb', name='StreetHood', eye=1.630, nose=1.603, ear_lobe=1.582, chin=1.527, axis_z=-0.02,
                 mask=(58, 62, 42), seed=31, tie_band=False, clear_temple_text=True, drop_loose=1.635, unify_hair=True,   # round 11: drop_loose 1.655 -> 1.635 (the 14-tri curl on the right temple), blond -> maroon
                 tints={'Grey': dict(region='top', color=(104, 104, 108))}),
    'tee': dict(src='adult+male+3d+model.glb', name='StreetTee', auto=True, axis_z=-0.02,
                mask=(74, 20, 22), seed=41, tie_band=False, cap=dict(color=(36, 44, 70)),
                seethrough=True,   # round 09: flip the back-faced lip-crease slivers that are holes through the mask
                hang=dict(uncover_mouth=True), hair_shell=True),   # round 08: lips showed through the tee mask (the mouth slit was left as a ledge under the cloth)
    'beard': dict(src='human+character+3d+model (3).glb', name='StreetBeard', auto=True, axis_z=-0.02,
                  mask=(26, 46, 52), seed=53, tie_band=False, clear_graphic=True, hair_shell=True, hair_compress=True, scalp_side=0.014),   # round 11: bridge_gap ((0.05, 1.70, 0.08), 0.07) = the r10 flat card, replaced by hair.tuck_hair
}


# ------------------------------------------------------------------------------------------------------ helpers
def rgb2hsv(a):
    a = a.astype(np.float32) / 255.0
    mx, mn = a.max(-1), a.min(-1)
    d = mx - mn + 1e-9
    h = np.where(mx == a[..., 0], ((a[..., 1] - a[..., 2]) / d) % 6, np.where(mx == a[..., 1], (a[..., 2] - a[..., 0]) / d + 2, (a[..., 0] - a[..., 1]) / d + 4)) * 60.0
    s = np.where(mx > 0, (mx - mn) / (mx + 1e-9), 0.0)
    return h, s, mx


def raster_positions(P, UV, F, n):
    """Per texel: covered flag and interpolated 3D position. Image row = v * n (glTF v is down)."""
    pos = np.zeros((n, n, 3), np.float32)
    cov = np.zeros((n, n), bool)
    for f in F:
        u = UV[f] * n
        x0 = max(int(np.floor(u[:, 0].min() - 0.5)), 0); x1 = min(int(np.ceil(u[:, 0].max() + 0.5)), n - 1)
        y0 = max(int(np.floor(u[:, 1].min() - 0.5)), 0); y1 = min(int(np.ceil(u[:, 1].max() + 0.5)), n - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = u
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        w2 = 1 - w0 - w1
        m = (w0 >= -0.05) & (w1 >= -0.05) & (w2 >= -0.05)
        if not m.any():
            continue
        Pp = w0[..., None] * P[f[0]] + w1[..., None] * P[f[1]] + w2[..., None] * P[f[2]]
        sl = (slice(y0, y1 + 1), slice(x0, x1 + 1))
        pos[sl][m] = Pp[m]
        cov[sl][m] = True
    return cov, pos


def fill_gutters(img, cov, erode=1):
    """Replace everything outside the (slightly eroded) covered texels by the nearest covered colour."""
    keep = ndi.binary_erosion(cov, iterations=erode) if erode else cov
    _, (iy, ix) = ndi.distance_transform_edt(~keep, return_indices=True)
    return img[iy, ix]


def weave(shape, seed, period=5.0):
    r = np.random.RandomState(seed)
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]].astype(np.float32)
    w = 0.5 + 0.25 * np.sin(xx * 2 * np.pi / period) + 0.25 * np.sin(yy * 2 * np.pi / period)
    n = ndi.gaussian_filter(r.randn(*shape).astype(np.float32), 1.2)
    n /= n.std() + 1e-6
    return w, n


# ------------------------------------------------------------------------------------------------------ mesh edits
def ray_hits(P, F, origins, dirs, ymin, ymax):
    """First triangle hit (distance) for each ray (Moller-Trumbore, vectorised over rays, restricted to triangles in the y band)."""
    tri = P[F]
    cy = tri[:, :, 1].mean(1)
    sel = (cy > ymin - 0.04) & (cy < ymax + 0.04) & (np.hypot(tri[:, :, 0].mean(1), tri[:, :, 2].mean(1)) < 0.4)
    tri = tri[sel]
    v0, v1, v2 = tri[:, 0], tri[:, 1], tri[:, 2]
    e1, e2 = v1 - v0, v2 - v0
    out = np.full(len(origins), np.inf)
    for i in range(len(origins)):
        o, d = origins[i], dirs[i]
        h = np.cross(d, e2)
        a = np.einsum('ij,ij->i', e1, h)
        ok = np.abs(a) > 1e-10
        f = np.where(ok, 1.0 / np.where(ok, a, 1), 0)
        s = o - v0
        u = f * np.einsum('ij,ij->i', s, h)
        q = np.cross(s, e1)
        v = f * (q @ d)
        t = f * np.einsum('ij,ij->i', e2, q)
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0.01)
        if hit.any():
            out[i] = t[hit].min()
    return out


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def build_bandana(P, F, cfg, seed):
    """Shell around the lower face and neck. Returns (verts, normals, uv(0..1 over the strip), faces)."""
    eye, ear, chin, z0 = cfg['eye'], cfg['ear_lobe'], cfg['chin'], cfg['axis_z']
    NPHI, NH = 72, 14
    phi = np.linspace(-np.pi, np.pi, NPHI + 1)              # seam at the back (phi = +-180 deg)
    a = np.abs(phi)
    # lower-face mask over nose, mouth, chin and the front/side of the neck (top under the eyes, bottom on the jacket collar);
    # behind the ears it narrows to a tie strap that runs round the back of the head
    ang = np.radians([0, 35, 70, 90, 105, 125, 150, 180])
    top = np.interp(a, ang, [eye - .015, eye - .030, ear - .008, ear - .014, ear - .004, ear + .026, ear + .028, ear + .028])
    bot = np.interp(a, ang, [chin - .032, chin - .030, chin - .012, chin + .005, ear - .030, ear - .003, ear - .003, ear - .003])
    t = np.linspace(0, 1, NH + 1)
    H = bot[:, None] + (top - bot)[:, None] * t[None, :]      # (NPHI+1, NH+1) heights
    origins = np.stack([np.full(H.shape, 0.0), H, np.full(H.shape, z0)], -1).reshape(-1, 3)
    dirs = np.stack([np.repeat(np.sin(phi)[:, None], NH + 1, 1), np.zeros(H.shape), np.repeat(np.cos(phi)[:, None], NH + 1, 1)], -1).reshape(-1, 3)
    dist = ray_hits(P, F, origins, dirs, H.min(), H.max()).reshape(H.shape)
    fin = np.isfinite(dist)
    med = np.median(dist[fin]) if fin.any() else 0.09
    dist = np.where(fin, dist, med)
    dist0 = np.clip(dist, 0.5 * med, 1.7 * med)
    # cloth bridges bumps: dilate (so nose, lips and chin never poke through), smooth, then never go below the real surface
    dist = ndi.maximum_filter(dist0, size=(3, 3), mode='nearest')
    for _ in range(3):
        dist = (dist + np.roll(dist, 1, 0) + np.roll(dist, -1, 0)) / 3.0
        pad = np.pad(dist, ((0, 0), (1, 1)), mode='edge')
        dist = (pad[:, :-2] + pad[:, 1:-1] + pad[:, 2:]) / 3.0
    dist = np.maximum(dist, dist0)
    rng = np.random.RandomState(seed)
    # folds: diagonal ridges + low-frequency noise, damped at the top edge (which gets a rolled hem instead)
    ph, tt = np.meshgrid(phi, t, indexing='ij')
    folds = 0.0018 * np.sin(ph * 7 + tt * 9 + 0.6 * np.sin(ph * 3)) + 0.0012 * np.sin(-ph * 11 + tt * 5 + 1.3)
    lf = ndi.gaussian_filter(rng.randn(*H.shape), 2.0); lf = 0.0018 * lf / (lf.std() + 1e-6)
    hem = 0.0026 * smoothstep(0.86, 1.0, tt) + 0.0016 * (1 - smoothstep(0.0, 0.10, tt))
    off = 0.0085 + folds + lf + hem
    r = dist + off
    X = r * np.sin(phi)[:, None]; Z = z0 + r * np.cos(phi)[:, None]
    V = np.stack([X, H, Z], -1)
    # wrap: last column of phi equals first geometrically; keep separate vertices (UV seam)
    V[-1] = V[0] * 0 + np.stack([X[-1], H[-1], Z[-1]], -1)
    verts = V.reshape(-1, 3)
    # normals from the grid
    dphi = np.gradient(V, axis=0); dh = np.gradient(V, axis=1)
    nn = np.cross(dphi, dh)
    nn /= np.linalg.norm(nn, axis=-1, keepdims=True) + 1e-12
    radial = np.stack([np.sin(phi)[:, None] * np.ones_like(H), np.zeros_like(H), np.cos(phi)[:, None] * np.ones_like(H)], -1)
    flip = (nn * radial).sum(-1, keepdims=True) < 0
    nn = np.where(flip, -nn, nn)
    normals = nn.reshape(-1, 3)
    # faces (winding so the geometric normal points outward)
    idx = np.arange((NPHI + 1) * (NH + 1)).reshape(NPHI + 1, NH + 1)
    f = []
    for i in range(NPHI):
        for j in range(NH):
            a0, a1, b0, b1 = idx[i, j], idx[i + 1, j], idx[i, j + 1], idx[i + 1, j + 1]
            f.append([a0, a1, b1]); f.append([a0, b1, b0])
    faces = np.array(f)
    g = np.cross(verts[faces[:, 1]] - verts[faces[:, 0]], verts[faces[:, 2]] - verts[faces[:, 0]])
    if (g * normals[faces[:, 0]]).sum(1).mean() < 0:
        faces = faces[:, [0, 2, 1]]
    uv = np.stack([np.repeat((phi / (2 * np.pi) + 0.5)[:, None], NH + 1, 1), np.repeat(t[None, :], NPHI + 1, 0)], -1).reshape(-1, 2)
    return verts, normals, uv, faces


def bandana_strip(cfg, seed):
    """4096 x 512 cloth strip: dark base, thread weave, faint paisley-like dot print, no lettering."""
    W, Hh = ATLAS, ATLAS - CONTENT_H
    base = np.array(cfg['bandana'], np.float32); hi = np.array(cfg['bandana_hi'], np.float32)
    w, n = weave((Hh, W), seed, 4.0)
    yy, xx = np.mgrid[0:Hh, 0:W].astype(np.float32)
    # print: staggered rings/dots in a lattice, low contrast
    px, py = 48.0, 48.0
    cx = (xx % px) - px / 2 + 12 * (np.floor(yy / py) % 2)
    cy = (yy % py) - py / 2
    dots = np.clip(1.0 - np.hypot(cx * 0.9, cy * 1.1) / 9.0, 0, 1)
    dots2 = np.clip(1.0 - np.abs(np.hypot(cx, cy) - 15) / 2.0, 0, 1) * 0.6
    pat = np.clip(dots + dots2, 0, 1)
    img = base[None, None, :] * (0.86 + 0.16 * w[..., None] + 0.05 * n[..., None])
    img = img * (1 - 0.55 * pat[..., None]) + hi[None, None, :] * (0.55 * pat[..., None]) * (0.9 + 0.2 * w[..., None])
    return np.clip(img, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------------------------------------------ recolours
def recolor_brute(img, pos, cov):
    h, s, v = rgb2hsv(img)
    y = pos[..., 1]
    a = img.astype(np.float32)
    lum = (a @ np.array([0.299, 0.587, 0.114], np.float32))
    out = a.copy()
    # orange knit beanie (hue 30-48, saturated, high on the head; the pom-pom is deleted from the mesh) -> charcoal knit, luminance detail kept
    z = pos[..., 2]
    brim = 1.53 + (z + 0.18) * (0.10 / 0.27)                      # slanted lower limit of the beanie: high over the forehead, low at the nape
    orange = ((h >= 27) & (h <= 58) & (s >= 0.5) & (v > 0.12)) | ((h >= 10) & (h < 27) & (s >= 0.7) & (v < 0.45))   # ginger beard / skin stay out (hue < 27, sat < 0.7)
    brim_lo = 1.49 + (z + 0.18) * 0.40
    cuff = (h >= 24) & (h <= 60) & (s >= 0.58) & (v > 0.12)                  # orange cuff just below the slanted brim; skin (sat < 0.5) and ginger beard (hue < 24) stay out
    beanie = cov & (y > 1.48) & ((y > brim) | ((y > brim_lo) & cuff))         # above the brim geometry decides (the knit has orange, brown and black threads)
    tone = np.array([46, 47, 52], np.float32)
    out[beanie] = tone[None, :] * np.clip(lum[beanie] / 120.0, 0.35, 1.7)[:, None]
    # red/green flannel plaid on torso and arms -> one worn brown-grey flannel tone; the check survives only as a soft luminance pattern
    x = pos[..., 0]
    keep_skin = ((np.abs(x) > 0.50) & (y < 1.12)) | ((y > 1.40) & (np.abs(x) < 0.14))       # hands (A-pose, wrists out at |x| > 0.5) and neck / lower face
    core = cov & (y > 0.70) & (y < 1.55) & (((s > 0.32) & ((h < 14) | (h > 335))) | ((s > 0.14) & (h > 70) & (h < 190)))
    # sleeves: by position (the check has red, green and dark-green squares); dark vest texels (navy/black) are left alone
    sleeves = cov & (np.abs(x) > 0.19) & (np.abs(x) < 0.53) & (y > 0.93) & (y < 1.50) & ((lum > 52) | (s > 0.45))
    plaid = (core | sleeves) & (~keep_skin | (s > 0.58))
    grow = ndi.binary_dilation(plaid, iterations=1) & cov & (lum > 55) & (s > 0.10) & (y > 0.70) & (y < 1.55) & (~keep_skin | (s > 0.58))
    plaid |= grow
    Lm = ndi.gaussian_filter(np.where(plaid, lum, 0.0), 12) / np.maximum(ndi.gaussian_filter(plaid.astype(np.float32), 12), 1e-3)
    rel = np.clip(lum / np.maximum(Lm, 1.0), 0.55, 1.35)
    rel = 0.6 + 0.4 * ndi.gaussian_filter(rel, 0.8)                                                        # damp the pattern
    tone = np.array([50, 44, 41], np.float32)                                                             # worn dark brown-grey flannel (the lineup stage renders albedo ~3x brighter)
    out[plaid] = tone[None, :] * rel[plaid][:, None]
    npl = int(plaid.sum())
    return np.clip(out, 0, 255).astype(np.uint8), int(beanie.sum()), npl


def recolor_thug(img, pos, cov):
    """Ornamental belt buckle and key-chain (invented metalwork with pseudo-lettering) -> plain dark steel."""
    h, s, v = rgb2hsv(img)
    y, x, z = pos[..., 1], pos[..., 0], pos[..., 2]
    a = img.astype(np.float32)
    lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    metal = cov & (s < 0.18) & (lum > 60) & (y > 0.62) & (y < 1.10)          # belt zone and hip pocket: grey/silver metal only
    out = a.copy()
    steel = np.array([58, 60, 64], np.float32)
    out[metal] = steel[None, :] * np.clip(0.75 + 0.25 * lum[metal] / 160.0, 0.6, 1.2)[:, None]
    return np.clip(out, 0, 255).astype(np.uint8), int(metal.sum())


# ------------------------------------------------------------------------------------------------------ round-04 texture edits
def knit_beanie(out, img, pos, beanie, cfg):
    """the recoloured beanie + cuff get a knit rib (vertical ribs by azimuth, rows by height) instead of a flat tone, and a soft
    (2 texel) lower edge instead of the stair-stepped texel mask."""
    phi, r = M.cyl(pos, cfg)
    y = pos[..., 1]
    rib = 0.5 + 0.5 * np.sin(phi * np.maximum(r, 0.06) * 2 * np.pi / 0.0055)
    row = 0.5 + 0.5 * np.sin(y * 2 * np.pi / 0.0032)
    a = img.astype(np.float32); lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    lo = ndi.gaussian_filter(lum, 6)
    tone = np.array([46, 47, 52], np.float32)
    knit = tone[None, None, :] * (np.clip(lo / 120.0, 0.45, 1.5) * (0.78 + 0.16 * rib + 0.08 * row))[..., None]
    soft = ndi.gaussian_filter(beanie.astype(np.float32), 1.2)
    soft = np.where(beanie, np.maximum(soft, 0.5), soft)
    return out * (1 - soft[..., None]) + knit * soft[..., None]


def clear_plaid_remnants(img, pos, cov):
    """saturated red / green texels left on the brute's sleeves, cuffs and collar (the round-03 critic's 'mis-UV blotches') -> the
    flannel tone, by position (arms / torso / collar) and colour; hands and face are kept by position."""
    h, s_, v = rgb2hsv(img)
    x, y = pos[..., 0], pos[..., 1]
    a = img.astype(np.float32); lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    hands = (np.abs(x) > 0.55) & (y < 1.25)
    face = (y > 1.42) & (np.abs(x) < 0.13)
    red = (s_ > 0.28) & ((h < 16) | (h > 330)); green = (s_ > 0.16) & (h > 65) & (h < 200)
    sel = cov & (y > 0.62) & (y < 1.52) & (red | green) & ~hands & ~face
    sel = ndi.binary_dilation(sel, iterations=2) & cov & ~hands & ~face & (y > 0.62) & (y < 1.52) & ((s_ > 0.12) | (lum > 70))
    tone = np.array([50, 44, 41], np.float32)
    out = a.copy()
    out[sel] = tone[None, :] * np.clip(0.75 + 0.25 * lum[sel] / 90.0, 0.6, 1.2)[:, None]
    return np.clip(out, 0, 255).astype(np.uint8), int(sel.sum())


def clear_graphic(img, pos, cov):
    """chest print on a dark tee -> plain tee (no copied / pseudo graphics). Front torso band, bright texels on the dark shirt."""
    x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
    a = img.astype(np.float32); lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    band = cov & (((y > 0.98) & (y < 1.31) & (np.abs(x) < 0.24)) | ((y > 1.29) & (y < 1.43) & (x > 0.035) & (x < 0.19))) & (z > -0.03)   # chest print + left-chest logo; the neck chains (|x| < 0.035) stay
    shirt = band & (lum < 45)
    tee = np.median(a[shirt], 0) if shirt.any() else np.array([28, 28, 32], np.float32)
    sel = band & (lum >= 45)
    sel = ndi.binary_dilation(sel, iterations=3) & band
    shade = ndi.gaussian_filter(np.where(shirt, lum, np.median(lum[shirt]) if shirt.any() else 30), 10)
    out = a.copy()
    out[sel] = tee[None, :] * np.clip(shade[sel] / max(1.0, float(np.median(lum[shirt]) if shirt.any() else 30)), 0.7, 1.3)[:, None]
    return np.clip(out, 0, 255).astype(np.uint8), int(sel.sum())


def clear_temple_text(img, pos, cov, cfg):
    """round 04b: the hood person's raw white sunglasses carry small dark lettering on the temple arms (reads like a maker mark).
    No copied names: dark texels enclosed by the white frame on the temple band are filled with the frame's own white."""
    x, y = pos[..., 0], pos[..., 1]
    a = img.astype(np.float32); lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    _, s_, _ = rgb2hsv(img)
    eye = cfg.get('eye', 1.63)
    band = cov & (y > eye - 0.04) & (y < eye + 0.05) & (np.abs(x) > 0.045)
    frame = band & (lum > 175) & (s_ < 0.18)
    enclosed = ndi.binary_closing(frame, iterations=4) & band
    sel = enclosed & ~frame
    sel = ndi.binary_dilation(sel, iterations=1) & enclosed
    col = np.median(a[frame], 0) if frame.any() else np.array([235, 235, 235], np.float32)
    out = a.copy(); out[sel] = col[None, :]
    return np.clip(out, 0, 255).astype(np.uint8), int(sel.sum())


def tint_region(img, pos, cov, region, color):
    """luminance-preserving recolour of a garment for a variant atlas (same mesh, different material)."""
    h, s_, v = rgb2hsv(img)
    x, y = pos[..., 0], pos[..., 1]
    a = img.astype(np.float32); lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    skin = (h > 4) & (h < 40) & (s_ > 0.18) & (s_ < 0.65) & (v > 0.25)
    if region == 'jacket':       # leather jacket + hood: dark, low-saturation, above the hips
        sel = cov & (y > 0.92) & (y < 1.62) & (lum < 80) & (s_ < 0.35) & ~skin & ~((np.abs(x) < 0.12) & (y > 1.45) & (pos[..., 2] > 0.0))
    else:                        # 'top': hoodie / shirt, above the hips
        sel = cov & (y > 0.93) & (y < 1.52) & (lum < 70) & (s_ < 0.30) & ~skin & ~((np.abs(x) < 0.13) & (y > 1.42))
    ref = float(np.median(lum[sel])) if sel.any() else 40.0
    col = np.asarray(color, np.float32)
    out = a.copy()
    out[sel] = col[None, :] * np.clip(lum[sel] / max(ref, 1.0), 0.45, 1.8)[:, None]
    soft = ndi.gaussian_filter(sel.astype(np.float32), 0.8)
    out = a * (1 - soft[..., None]) + out * soft[..., None]
    return np.clip(out, 0, 255).astype(np.uint8), int(sel.sum())


# ------------------------------------------------------------------------------------------------------ weapon tiles
WEAPON_TEXTURED = True
WEAPON_X0 = 3584            # strip columns [3584, 4096): solid material tiles for tools/ue_char/weapons/add_weapon.py
WEAPON_TILES = [('wood', (150, 108, 66)), ('steel', (104, 108, 114)), ('polymer', (30, 30, 33)), ('grip', (44, 40, 38)), ('tape', (24, 24, 26))]


def weapon_tiles():
    if WEAPON_TEXTURED:   # round 05: procedural wood / steel / polymer / wrap / tape tiles (tools/ue_char/weapons/weapon_textures.py)
        sys.path.insert(0, os.path.join(HERE, '..', 'weapons'))
        import weapon_textures
        return weapon_textures.strip(ATLAS, CONTENT_H, WEAPON_X0)
    h = ATLAS - CONTENT_H
    out = np.zeros((h, ATLAS - WEAPON_X0, 3), np.float32)
    rng = np.random.RandomState(5)
    for k, (nm, col) in enumerate(WEAPON_TILES):
        y0, y1 = int(h * k / len(WEAPON_TILES)), int(h * (k + 1) / len(WEAPON_TILES))
        g = ndi.gaussian_filter(rng.randn(y1 - y0, ATLAS - WEAPON_X0), 2.0); g /= g.std() + 1e-6
        out[y0:y1] = np.asarray(col, np.float32)[None, None, :] * (1 + 0.03 * g[..., None])
    return np.clip(out, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------------------------------------------ cap (accessory)
CAP_SRC = 'baseball+cap+3d+model.glb'


def fit_cap(P, F, cfg, seed):
    """raw Tripo baseball cap on the person's head: scaled to the hair width, crown centred over the skull, brim over the eyes;
    hair vertices poking through the crown are pulled inside it. Returns (person P, cap verts, normals, uv 0..1, faces, strip RGB)."""
    Pc, Nc, UVc, Fc, imc = gltfio.read_person(os.path.join(RAW, CAP_SRC))
    R = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], float)      # like the people: bill +X -> +Z (forward)
    Pc = Pc @ R.T; Nc = Nc @ R.T
    crown = Pc[:, 2] < Pc[:, 2].min() + 0.62                      # crown = everything behind the bill
    cw = Pc[crown, 0].max() - Pc[crown, 0].min(); cd = Pc[crown, 2].max() - Pc[crown, 2].min()
    eye = cfg['eye']
    hair = (P[:, 1] > eye + 0.015) & (P[:, 1] < eye + 0.075) & (np.hypot(P[:, 0], P[:, 2] - cfg['axis_z']) < 0.16)
    hw = P[hair, 0].max() - P[hair, 0].min(); hz = (P[hair, 2].max() + P[hair, 2].min()) / 2
    hd = P[hair, 2].max() - P[hair, 2].min()
    k = max(hw * 0.98 / cw, hd * 0.96 / cd)
    ky = 0.125 / (Pc[crown, 1].max() - Pc[crown, 1].min())       # the raw cap is tall for its width: crown height 12.5 cm
    Pc = Pc * np.array([k, ky, k]); Nc = Nc / np.array([k, ky, k]); Nc /= np.linalg.norm(Nc, axis=1, keepdims=True) + 1e-12
    cc = (Pc[crown].max(0) + Pc[crown].min(0)) / 2
    Pc[:, 0] -= cc[0]; Pc[:, 2] += hz - cc[2]
    Pc[:, 1] += (eye + 0.022) - Pc[:, 1].min()
    # tilt 6 deg back (brim up a little)
    t = np.radians(-6); c_, s_ = np.cos(t), np.sin(t)
    piv = np.array([0, Pc[:, 1].min(), hz])
    q = Pc - piv; Pc = piv + np.stack([q[:, 0], c_ * q[:, 1] - s_ * q[:, 2], s_ * q[:, 1] + c_ * q[:, 2]], 1)
    Nc = np.stack([Nc[:, 0], c_ * Nc[:, 1] - s_ * Nc[:, 2], s_ * Nc[:, 1] + c_ * Nc[:, 2]], 1)
    # hair inside the crown: ellipsoid fitted to the crown (centre, semi-axes) shrunk 6 %; person points above the cap band and
    # outside it are pulled onto it
    cr = Pc[crown if len(crown) == len(Pc) else slice(None)]
    ctr = (cr.max(0) + cr.min(0)) / 2; ctr[1] = cr[:, 1].min()
    ax = np.array([(cr[:, 0].max() - cr[:, 0].min()) / 2, cr[:, 1].max() - cr[:, 1].min(), (cr[:, 2].max() - cr[:, 2].min()) / 2]) * 0.94
    P = P.copy()
    head = (P[:, 1] > ctr[1] - 0.005) & (np.hypot(P[:, 0], P[:, 2] - cfg['axis_z']) < 0.2)
    q = (P[head] - ctr) / ax
    n = np.linalg.norm(q, axis=1)
    out = n > 1.0
    idx = np.where(head)[0][out]
    P[idx] = ctr + (q[out] / n[out][:, None]) * ax
    # procedural dark twill strip (the raw cap texture is not used: no badge / logo can come along)
    W, Hh = ATLAS, ATLAS - CONTENT_H
    rng = np.random.RandomState(seed)
    yy, xx = np.mgrid[0:Hh, 0:W].astype(np.float32)
    tw = 0.5 + 0.5 * np.sin((xx + yy) * 2 * np.pi / 5.0)
    g = ndi.gaussian_filter(rng.randn(Hh, W).astype(np.float32), 1.0); g /= g.std() + 1e-6
    shade = np.asarray(imc.convert('L').resize((W, Hh), Image.BILINEAR), np.float32)
    shade = ndi.gaussian_filter(shade, 6); shade = shade / max(1.0, float(np.median(shade)))
    col = np.asarray(cfg['cap']['color'], np.float32)
    strip = col[None, None, :] * (np.clip(shade, 0.6, 1.4) * (0.88 + 0.10 * tw + 0.04 * g))[..., None]
    return P, Pc, Nc, UVc, Fc, np.clip(strip, 0, 255).astype(np.uint8), dict(cap_scale=round(float(k), 3), cap_scale_y=round(float(ky), 3), hair_pulled=int(out.sum()))


# ------------------------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('which', choices=sorted(CFG))
    ap.add_argument('--out', default=SCR + '/people')
    a = ap.parse_args()
    cfg = dict(CFG[a.which])
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()
    game = skinfit.Game(os.path.join(ROOT, 'public/assets/spiderman.glb'))
    P, N, UV, F, im = gltfio.read_person(os.path.join(RAW, cfg['src']))
    R = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], float)      # raw faces +X, arms along Z -> game frame (faces +Z, +X left)
    P = P @ R.T; N = N @ R.T
    P = skinfit.normalise_target(P, game)
    print('%s: %d verts %d tris' % (a.which, len(P), len(F)))
    info = {}
    lm = M.auto_landmarks(P, cfg['axis_z'])
    if cfg.get('auto'):
        cfg.update({k: v for k, v in lm.items() if k != 'axis_z'})
    # nose-tip radius from the head axis at the measured nose height (bounds the mask region radially)
    fr = (np.abs(P[:, 1] - cfg['nose']) < 0.006) & (np.abs(P[:, 0]) < 0.02)
    cfg['nose_r'] = float(np.max(P[fr, 2]) - cfg['axis_z']) if fr.any() else 0.13
    info['landmarks'] = {k: round(float(cfg[k]), 4) for k in ('eye', 'nose', 'ear_lobe', 'chin', 'nose_r')}
    if a.which == 'brute':
        # pom-pom: pull its vertices onto the beanie dome (sphere fitted to the dome vertices) so no hole has to be capped
        pom = (P[:, 1] > 1.705) & (P[:, 2] < -0.07) & (np.abs(P[:, 0]) < 0.08)
        dome = (P[:, 1] > 1.66) & ~pom & (P[:, 1] < 1.72) & (np.abs(P[:, 0]) < 0.11)
        Q = P[dome]
        A_ = np.c_[2 * Q, np.ones(len(Q))]; b_ = (Q ** 2).sum(1)
        sol = np.linalg.lstsq(A_, b_, rcond=None)[0]
        ctr = sol[:3]; rad = float(np.sqrt(sol[3] + (ctr ** 2).sum()))
        d = P[pom] - ctr
        P[pom] = ctr + d / np.linalg.norm(d, axis=1, keepdims=True) * rad
        N[pom] = d / np.linalg.norm(d, axis=1, keepdims=True)
        info.update(pompom_verts=int(pom.sum()), dome_centre=[round(float(x), 3) for x in ctr], dome_radius=round(rad, 3))
    # ---- mask geometry: subdivide the lower face / neck once, then drape it over the front of the head
    wv = M.region_weight(P, cfg, feather=0.02)
    tri = (wv[F].max(1) > 0) & (np.hypot(P[F][:, :, 0], P[F][:, :, 2] - cfg['axis_z']).max(1) < 0.14)
    nt0 = len(F)
    P, N, UV, F = M.subdivide_region(P, N, UV, F, tri)
    P, moved = (M.drape if cfg.get('drape') == 'hull' else M.hang)(P, F, cfg, cfg['seed'], **(cfg.get('hang') or {}) if cfg.get('drape') != 'hull' else {})   # round 05: hanging cloth (mask.hang); 'hull' = the round-04 convex-hull drape
    nP0 = len(P)
    F, ndrop = M.drop_cavity(P, F, cfg)                           # round 05: mouth / nostril cavity walls removed, their loops closed below
    P, N, UV, F, nfill = M.fill_face_holes(P, N, UV, F, cfg)   # round 05: mouth slit / chin tears closed
    moved = np.concatenate([moved, np.zeros(len(P) - nP0)])
    F, nflip = M.fix_flips(P, F, cfg)                            # round 05: back-faced slivers at lips / nostrils
    if cfg.get('flatten_mouth'): P = M.flatten_mouth(P, cfg); F, nflip2 = M.fix_flips(P, F, cfg); nflip += nflip2           # round 08: the mouth slit ledge (lips showing through the cloth)
    if cfg.get('sink_neck'): P = M.sink_neck(P, F, cfg)             # round 08: slack for the neck skin under the collar (collar shards)
    nseethrough = 0
    if cfg.get('seethrough') and not os.environ.get('P2_NO_SEETHROUGH'): F, nseethrough = M.flip_seethrough(P, F, cfg)   # round 09: back-faced slivers of the lip crease = holes through the cloth (tee_face_4k 198 / 91 / 24 px)
    nbridge = 0
    if cfg.get('bridge_gap'): P, N, UV, F, nbridge = M.bridge_hair_gap(P, N, UV, F, *cfg['bridge_gap'], tex=im)   # round 10: the side-hair curtain's gap to the head surface (beard_face_4k)
    moved = np.concatenate([moved, np.zeros(len(P) - len(moved))])      # the bridge strip adds duplicated vertices
    nloose = 0
    if cfg.get('drop_loose'): F, nloose = M.drop_loose_shells(P, F, y_min=cfg['drop_loose'])   # round 10: loose hair-ribbon shells of the head (hood_face_4k)
    Hsh = None
    if cfg.get('hair_shell'):   # round 11: the hair shell's open edges tucked onto the head (no background / skin gap, no bridge card)
        Hsh = HR.hair_shell(P, F)
        P0_ = P.copy(); P, tinfo = HR.tuck_hair(P, F, Hsh, axis_z=cfg['axis_z']); info.update(tinfo)
        if cfg.get('hair_compress'): P, cinfo_ = HR.compress_hair(P, F, Hsh); info.update(cinfo_)
        moved = moved + np.linalg.norm(P - P0_, axis=1)
        info['hair_shell_tris'] = int(Hsh.sum())
    N2 = M.vertex_normals(P, F)
    chg = moved > 1e-5
    N[chg] = N2[chg]
    N = M.cloth_normals(P, F, N, cfg)                            # round 05: smoothed cloth normals over the mask region
    info.update(cavity_tris_dropped=int(ndrop), holes_filled=int(nfill), flipped_tris=int(nflip), seethrough_flipped=int(nseethrough), loose_shell_tris_dropped=int(nloose), bridge_tris=int(nbridge), mask_subdivided_tris=int(tri.sum()), tris_after_subdiv=len(F), tris_before=nt0, draped_verts=int(chg.sum()),
                drape_max_cm=round(float(moved.max() * 100), 2))
    # ---- texture
    im4 = np.asarray(im.resize((ATLAS, ATLAS), Image.LANCZOS))
    cov, pos = raster_positions(P, UV, F, ATLAS)
    print('  uv coverage %.1f%%' % (100 * cov.mean()))
    if a.which == 'brute':
        im4, nb, npl = recolor_brute(im4, pos, cov); info['beanie_px'] = nb; info['plaid_px'] = npl
        im4, nrem = clear_plaid_remnants(im4, pos, cov); info['plaid_remnant_px'] = nrem
    elif a.which == 'thug':
        im4, nm = recolor_thug(im4, pos, cov); info['metal_px'] = nm
    if cfg.get('soften_neck'):
        # round 08 (critic r07: 'thug collar shards'): the raw atlas has coarse, stair-stepped texels where the neck skin meets the dark collar / jacket interior; in the
        # close-up they read as jagged skin-coloured wedges in the collar.  Inside a ring around the neck / collar (y 1.36-1.50, r < 10 cm) the atlas is blurred (sigma 3 px, feathered)
        zone = cov & (pos[..., 1] > 1.36) & (pos[..., 1] < 1.50) & (np.hypot(pos[..., 0], pos[..., 2] - cfg['axis_z']) < 0.10)
        zf = ndi.gaussian_filter(zone.astype(np.float32), 5.0)[..., None]
        bl = np.stack([ndi.gaussian_filter(im4[..., k].astype(np.float32), 3.0) for k in range(3)], -1)
        im4 = np.clip(im4.astype(np.float32) * (1 - zf) + bl * zf, 0, 255).astype(np.uint8); info['neck_soften_px'] = int(zone.sum())
    if cfg.get('collar_dark'):
        # round 08: the pale 'collar shard' of the thug is neck skin seen through a gap of the hood collar at the sides / nape (round 08 captures: identical with and without the neck slack).
        # Skin-coloured texels of the neck below the ear line on the sides and the back (|azimuth| > 55 deg) take the collar's own dark colour, so a gap shows the inside of the hood.
        hh, ss_, vv = rgb2hsv(im4)
        skin_t = (hh > 5) & (hh < 40) & (ss_ > 0.15) & (ss_ < 0.65) & (vv > 0.40)
        az = np.degrees(np.arctan2(pos[..., 0], pos[..., 2] - cfg['axis_z']))
        rr = np.hypot(pos[..., 0], pos[..., 2] - cfg['axis_z'])
        zone = cov & skin_t & (np.abs(az) > 55) & (pos[..., 1] > 1.30) & (pos[..., 1] < 1.505) & (rr < 0.085)
        zf = ndi.gaussian_filter(zone.astype(np.float32), 1.5)[..., None]
        dark = np.array(cfg['collar_dark'], np.float32)[None, None, :]
        im4 = np.clip(im4.astype(np.float32) * (1 - zf) + dark * zf, 0, 255).astype(np.uint8); info['collar_dark_px'] = int(zone.sum())
    if cfg.get('clear_graphic'):
        im4, ng = clear_graphic(im4, pos, cov); info['graphic_px'] = ng
    if cfg.get('clear_temple_text'):
        im4, nt = clear_temple_text(im4, pos, cov, cfg); info['temple_text_px'] = nt
    if Hsh is not None:
        im4, sinfo = HR.paint_scalp(im4, cov, pos, P, N, UV, F, Hsh, axis_z=cfg['axis_z'], side_reach=cfg.get('scalp_side', 0.0), ear_y=cfg['ear_lobe'] + 0.03); info.update(sinfo)
    if cfg.get('unify_hair'):
        im4, uinfo = HR.unify_hair(im4, cov, pos, cfg); info.update(uinfo)
        if cfg.get('fringe_hairline'): im4, finfo = HR.fringe_hairline(im4, cov, pos, cfg); info.update(finfo)   # round 11: tried on the Hood, read as a dark stain on the forehead (CPU render): off
    im4 = fill_gutters(im4, cov, erode=1)
    im4, nbord = M.seam_blend(im4, cov, pos); info['seam_blend_px'] = nbord
    im4, mw = M.paint_mask(im4, cov, pos, cfg, cfg['seed']); info['mask_px'] = int((mw > 0.5).sum())
    im4 = fill_gutters(im4, cov, erode=0)
    variants = {}
    for tn, tc in (cfg.get('tints') or {}).items():
        variants[tn], npx = tint_region(im4, pos, cov, tc['region'], tc['color']); info['tint_%s_px' % tn] = npx
        if tc.get('mask_color'):   # round 05: re-tint the cloth mask (per-channel ratio keeps the weave, folds and stitching)
            ratio = np.asarray(tc['mask_color'], np.float32) / np.asarray(cfg['mask'], np.float32)
            sel = mw > 0.05
            v_ = variants[tn].astype(np.float32); v_[sel] = np.clip(v_[sel] * ratio[None, :], 0, 255)
            variants[tn] = v_.astype(np.uint8); info['tint_%s_mask_px' % tn] = int(sel.sum())
    if a.which == 'brute':
        # the actor is widened by `girth` in X/Y at run time: shrink the head (and the top of the neck) by 1/girth so it keeps natural proportions
        f = 1.0 / SIZES['brute']['girth']
        t = smoothstep(1.44, 1.52, P[:, 1])
        sx = 1.0 - (1.0 - f) * t
        z0 = CFG['brute']['axis_z']
        P[:, 0] *= sx
        P[:, 2] = z0 + (P[:, 2] - z0) * sx
        N = np.stack([N[:, 0] / sx, N[:, 1], N[:, 2] / sx], -1); N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
        info['head_shrink'] = round(f, 3)
    strip = np.zeros((ATLAS - CONTENT_H, ATLAS, 3), np.uint8) + 40
    Pf, Nf, Ff = P, N, F
    UV2 = UV.copy(); UV2[:, 1] = UV[:, 1] * (CONTENT_H / ATLAS)
    UVf = UV2
    if cfg.get('cap'):
        P2, cv, cn, cuv, cf, strip, cinfo = fit_cap(P, F, cfg, cfg['seed'])
        info.update(cinfo)
        m = 6.0 / ATLAS
        cuv2 = np.stack([np.clip(cuv[:, 0], m, 1 - m) * (WEAPON_X0 / ATLAS), (CONTENT_H + m * ATLAS + np.clip(cuv[:, 1], 0, 1) * (ATLAS - CONTENT_H - 2 * m * ATLAS)) / ATLAS], -1)
        Pf = np.concatenate([P2, cv]); Nf = np.concatenate([N, cn]); UVf = np.concatenate([UV2, cuv2]); Ff = np.concatenate([F, cf + len(P2)])
        info['cap_tris'] = len(cf)

    strip = np.asarray(Image.fromarray(strip).resize((WEAPON_X0, ATLAS - CONTENT_H), Image.LANCZOS)) if cfg.get('cap') else strip[:, :WEAPON_X0]
    strip = np.concatenate([strip, weapon_tiles()], 1)

    def atlas_of(img):
        at = np.zeros((ATLAS, ATLAS, 3), np.uint8)
        at[:CONTENT_H] = np.asarray(Image.fromarray(img).resize((ATLAS, CONTENT_H), Image.LANCZOS))
        at[CONTENT_H:] = strip
        return Image.fromarray(at)
    print('  total %d verts %d tris' % (len(Pf), len(Ff)))
    out = os.path.join(a.out, cfg['name'] + '_prepared.glb')
    atlas = atlas_of(im4)
    gltfio.write_static_glb(out, Pf, Nf, UVf, Ff, atlas, cfg['name'])
    atlas.save(os.path.join(a.out, cfg['name'] + '_atlas.png'))
    for tn, img in variants.items():
        atlas_of(img).save(os.path.join(a.out, cfg['name'] + '_' + tn + '_atlas.png'))
    np.savez_compressed(os.path.join(a.out, cfg['name'] + '_prepared.npz'), P=Pf, N=Nf, UV=UVf, F=Ff, n_body_verts=len(P), n_body_tris=len(F))
    info.update(name=cfg['name'], verts=len(Pf), tris=len(Ff), variants=sorted(variants), seconds=round(time.time() - t0, 1))
    json.dump(info, open(os.path.join(a.out, cfg['name'] + '_prepared.json'), 'w'), indent=1)
    print(json.dumps(info))


if __name__ == '__main__':
    main()
