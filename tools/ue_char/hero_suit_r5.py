#!/usr/bin/env python3
"""Round-05 hero suit QUALITY pass, Unreal side only (the design and the colour layout are unchanged; the browser textures are untouched).
Fan homage project, not official Marvel/Sony/Insomniac; no affiliation.

Critic r04 (suit_closeup_4k, hero_turntable_4k): 'the knit is chunky like a sweater (each rib ~25 px), the web lines are painted flat and
wobble and are not raised, the lenses are flat white discs, the panel edge is sawtoothed'.  This script writes, into
art/night1/characters/hero/tex/ (derived, git-ignored):

  suit_basecolor_r5.png  r4 base colour (hand fix included) with the blue / red panel borders re-drawn smooth: the UV charts meet along a
                         zig-zag edge in 3D (see hb_cov overlay in round-05/evidence), so the boundary is smoothed IN 3D: the blue
                         membership of every border texel is a Gaussian average over the surface neighbours (KD-tree on the texel
                         positions, sigma 4 mm), thresholded with a short anti-aliased ramp.  Web lines (near black) are kept.
  suit_normal_r5.png     r3/GLB normal (embossed webs) x1.4  +  a raised, rounded thread profile derived from the web-line mask
                         (height = mask blurred 1.2 px + 0.5 * blurred 3 px), so the lines catch a light edge from both sides.
  suit_orm_r5.png        the GLB ORM with the web lines glossier (roughness x0.55 on the thread crest) and a soft contact occlusion.
  ../shared/suit_twill_n.png  seamless 1024 px twill weave normal map (2/2 twill, 32 yarns per tile, yarn twist + fuzz) that replaces the chunky
                         knit as the tiled DetailNormal (build_characters.py sets the tiling from the mesh's UV density: 0.45 mm per yarn).

  python3 tools/ue_char/hero_suit_r5.py [--skip-edges]
"""
import sys, os, json, time
import numpy as np
import cv2
from PIL import Image
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'skinfit')); sys.path.insert(0, os.path.join(HERE, 'people')); sys.path.insert(0, HERE)
import skinfit  # noqa: E402
from prepare_person import raster_positions  # noqa: E402
from p2paths import WT  # noqa: E402
Image.MAX_IMAGE_PIXELS = None
TEX = WT + '/art/night1/characters/hero/tex'
SHARED = WT + '/art/night1/characters/shared'
N = 4096
SIGMA = 0.007          # metres: panel-border smoothing (3D Gaussian)
BAND = 0.020           # metres: only border texels within this distance of a red|blue boundary are touched
YARN_MM = 0.45         # yarn pitch of the tiled twill (mm)


# ------------------------------------------------------------------------------------------------ twill weave detail
def twill_normal(size=1024, yarns=32, strength=2.2, seed=7):
    """2/2 twill: a warp yarn is on top when ((i + j) mod 4) < 2.  Each cell is a rounded yarn bump elongated along the float, with per-yarn
    twist ripples and fuzz.  Tileable (all periodic).  Returns an (size, size, 3) uint8 tangent-space OpenGL normal map."""
    r = np.random.RandomState(seed)
    c = size // yarns
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    i = (xx // c).astype(int); j = (yy // c).astype(int)
    fx = (xx % c) / c - 0.5; fy = (yy % c) / c - 0.5
    warp_on_top = ((i + j) % 4) < 2
    # a yarn is a cylinder along its axis (warp = vertical, weft = horizontal): height profile cos across, gentle hump along
    across = np.where(warp_on_top, fx, fy)
    along = np.where(warp_on_top, fy, fx)
    prof = np.maximum(np.cos(np.clip(across * np.pi, -np.pi / 2, np.pi / 2)), 0.0) ** 0.9
    hump = 0.75 + 0.25 * np.cos(np.clip(along * np.pi, -np.pi, np.pi))
    h = prof * hump
    h = np.where(warp_on_top, h, 0.55 * h)                       # floats under: lower
    twist = 0.06 * np.sin((along * 5.0 + across * 2.0 + (i * 0.37 + j * 0.61)) * 2 * np.pi)   # yarn twist ripples along the float
    h = h + twist * prof
    fuzz = ndi.gaussian_filter(r.randn(size, size).astype(np.float32), 0.9, mode='wrap')
    h = h + 0.035 * fuzz / (fuzz.std() + 1e-6)
    h = ndi.gaussian_filter(h, 0.7, mode='wrap')
    gy, gx = np.gradient(h)
    nx = -gx * strength * yarns / 8.0; ny = gy * strength * yarns / 8.0    # image row grows downward: +Y (up) = -d/drow, so n_y = +dH/drow
    nz = np.ones_like(nx)
    n = np.stack([nx, ny, nz], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return ((n * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8), h


# ------------------------------------------------------------------------------------------------ panel edges
def classes(rgb):
    a = rgb.astype(np.int32)
    mx = a.max(-1)
    dark = mx < 70
    red = (a[..., 0] > 100) & (a[..., 1] < 80) & (a[..., 2] < 80)
    blue = (a[..., 2] > 60) & (a[..., 0] < 75) & (a[..., 2] > a[..., 0] + 25) & (a[..., 2] > a[..., 1] + 25)
    return red, blue, dark


def smooth_panel_edges(base, cov, pos, info):
    red, blue, dark = classes(base)
    red &= cov; blue &= cov
    col_red = np.median(base[red], axis=0)
    col_blue = np.median(base[blue], axis=0)
    info['col_red'] = [int(x) for x in col_red]; info['col_blue'] = [int(x) for x in col_blue]
    # coarse candidate band: coarse points of one class with a coarse point of the other class within BAND
    step = 3
    ys, xs = np.mgrid[0:N:step, 0:N:step]
    cm = (red | blue)[ys, xs] & cov[ys, xs]
    cp = pos[ys, xs][cm]; cb = blue[ys, xs][cm]
    tree = cKDTree(cp)
    pairs = tree.query_pairs(BAND, output_type='ndarray')
    diff = pairs[cb[pairs[:, 0]] != cb[pairs[:, 1]]]
    cand = np.zeros(len(cp), bool); cand[diff[:, 0]] = True; cand[diff[:, 1]] = True
    info['band_coarse_points'] = int(cand.sum())
    # fine band texels: every covered non-white texel whose nearest coarse point is a candidate (dark line texels included: filtered later)
    consider = cov & ~((base.min(-1) > 150))
    fy, fx = np.nonzero(consider)
    fp = pos[fy, fx]
    d, ni = tree.query(fp, k=1)
    inband = cand[ni] & (d < BAND)
    fy, fx, fp = fy[inband], fx[inband], fp[inband]
    info['band_texels'] = int(len(fy))
    # membership: Gaussian average of the blue indicator over the k nearest coarse points (red / blue only)
    k = 110
    dd, ii = tree.query(fp, k=k)
    w = np.exp(-(dd ** 2) / (2 * SIGMA * SIGMA))
    s = (w * cb[ii]).sum(1) / np.maximum(w.sum(1), 1e-9)
    alpha = np.clip((s - 0.5) / 0.10 + 0.5, 0, 1)                    # anti-aliased ramp about the smoothed border
    newc = col_red[None, :] * (1 - alpha[:, None]) + col_blue[None, :] * alpha[:, None]
    old = base[fy, fx].astype(np.float32)
    # keep the web lines: darkness of the old texel (near black) decides how much of the old value survives
    mx = old.max(-1)
    keep = np.clip((70 - mx) / 40.0, 0, 1)[:, None]
    lum_scale = np.clip(mx / max(1.0, float(np.maximum(col_red.max(), col_blue.max()))), 0, 1)[:, None]
    out = base.astype(np.float32).copy()
    out[fy, fx] = old * keep + newc * (1 - keep)
    changed = (np.abs(out[fy, fx] - old).sum(1) > 24)
    info['border_texels_recoloured'] = int(changed.sum())
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------------------------------------ web lines: height, normal, orm
def line_mask(base):
    a = base.astype(np.float32)
    mx = a.max(-1)
    return np.clip((95.0 - mx) / 50.0, 0, 1)                         # 1 on the near-black threads, 0 on any panel colour (blue max ~ 100)


def height_from_lines(t):
    h = ndi.gaussian_filter(t, 1.2) + 0.5 * ndi.gaussian_filter(t, 3.0)
    return h / max(1e-6, h.max())


def normal_from_height(h, strength):
    gy, gx = np.gradient(h)
    nx = -gx * strength
    ny = gy * strength                                                # n_y = +dH/drow (image rows grow downward, +Y is up)
    n = np.stack([nx, ny, np.ones_like(nx)], -1)
    return n


def main():
    skip_edges = '--skip-edges' in sys.argv
    info = {}
    t0 = time.time()
    j, b = skinfit.read_glb(WT + '/public/assets/spiderman.glb')
    nd = next(n for n in j['nodes'] if n.get('name') == 'SpiderMan'); p = j['meshes'][nd['mesh']]['primitives'][0]
    P = skinfit.accessor(j, b, p['attributes']['POSITION']); UV = skinfit.accessor(j, b, p['attributes']['TEXCOORD_0'])
    F = skinfit.accessor(j, b, p['indices']).reshape(-1, 3).astype(int)
    base_path = TEX + ('/suit_basecolor_r4.png' if os.path.exists(TEX + '/suit_basecolor_r4.png') else '/suit_basecolor.png')
    base = np.asarray(Image.open(base_path).convert('RGB'))
    assert base.shape[0] == N
    cov, pos = raster_positions(P, UV, F, N)
    info['coverage'] = round(float(cov.mean()), 4)
    if not skip_edges:
        base = smooth_panel_edges(base, cov, pos, info)
    Image.fromarray(base).save(TEX + '/suit_basecolor_r5.png')
    info['t_edges_s'] = round(time.time() - t0, 1)

    # ---- raised web threads
    t = line_mask(base)
    h = height_from_lines(t)
    n_line = normal_from_height(h, strength=14.0)
    n0 = np.asarray(Image.open(TEX + '/suit_normal.png').convert('RGB')).astype(np.float32) / 255.0 * 2 - 1
    n = np.stack([n0[..., 0] * 1.4 + n_line[..., 0], n0[..., 1] * 1.4 + n_line[..., 1], np.ones(n0.shape[:2], np.float32)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    Image.fromarray(((n * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)).save(TEX + '/suit_normal_r5.png')
    orm = np.asarray(Image.open(TEX + '/suit_orm.png').convert('RGB')).astype(np.float32)
    crest = np.clip(ndi.gaussian_filter(t, 1.0) * 1.6, 0, 1)
    orm[..., 1] *= (1 - 0.45 * crest)                                                   # glossier thread crest (roughness)
    contact = np.clip(ndi.gaussian_filter(t, 4.0) - ndi.gaussian_filter(t, 1.0) * 0.6, 0, 1)
    orm[..., 0] *= (1 - 0.35 * contact)                                                 # soft occlusion at the thread foot
    Image.fromarray(np.clip(orm, 0, 255).astype(np.uint8)).save(TEX + '/suit_orm_r5.png')
    info['thread_texels'] = int((t > 0.5).sum())

    # ---- twill weave detail
    os.makedirs(SHARED, exist_ok=True)
    tw, hh = twill_normal()
    Image.fromarray(tw).save(SHARED + '/suit_twill_n.png')
    # tiling for a 0.45 mm yarn pitch from the mesh's UV density (median UV units per metre of the suit primitive)
    a3 = np.linalg.norm(np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]]), axis=1) / 2
    a2 = np.abs((UV[F[:, 1], 0] - UV[F[:, 0], 0]) * (UV[F[:, 2], 1] - UV[F[:, 0], 1]) - (UV[F[:, 2], 0] - UV[F[:, 0], 0]) * (UV[F[:, 1], 1] - UV[F[:, 0], 1])) / 2
    ok = (a3 > 1e-9) & (a2 > 1e-12)
    uvpm = float(np.median(np.sqrt(a2[ok] / a3[ok])))
    tile_m = 32 * YARN_MM * 1e-3
    info.update(uv_units_per_m=round(uvpm, 4), detail_tiling=round(1.0 / (tile_m * uvpm), 1), yarn_mm=YARN_MM)
    json.dump(info, open(TEX + '/suit_r5.json', 'w'), indent=1)
    print(json.dumps(info))


if __name__ == '__main__':
    main()
