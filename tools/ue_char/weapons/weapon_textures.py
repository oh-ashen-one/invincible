"""Procedural textures for the enemy hand weapons (round 05: 'the pipe and golf clubs are untextured grey').
Fan homage project; not official Marvel/Sony/Insomniac; no affiliation.  Generic wear only: no brand, no lettering.

Each material gets a 512 x 102 tile in the reserved strip of the enemy atlas (prepare_person.WEAPON_X0..4096, rows CONTENT_H..4096).
add_weapon.py maps every weapon part to its tile with u = along the part's long axis, v = |angle around it| / pi (a triangle wave, so the
lathe seam has no jump).  numpy + scipy only.
"""
import numpy as np
from scipy import ndimage as ndi

W, H = 512, 102


def _n(rng, sy, sx, shape=(H, W)):
    g = ndi.gaussian_filter(rng.randn(*shape).astype(np.float32), (sy, sx), mode='wrap')
    return g / (g.std() + 1e-6)


def wood(seed=1):
    """lacquered ash bat: long grain streaks, faint growth rings, scuffs and a worn (lighter) hitting zone near the barrel end."""
    r = np.random.RandomState(seed)
    u = np.linspace(0, 1, W)[None, :]; v = np.linspace(0, 1, H)[:, None]
    base = np.array([158, 112, 68], np.float32)
    grain = _n(r, 0.6, 38) * 0.5 + _n(r, 1.5, 90) * 0.5
    rings = np.sin((v * 9 + 0.5 * _n(r, 4, 60)) * 2 * np.pi) * 0.5
    tone = 1 + 0.10 * grain + 0.05 * rings + 0.06 * _n(r, 10, 60)
    scuff = np.clip(_n(r, 1.2, 6), 1.2, None) - 1.2                       # sparse short dents
    tone = tone - 0.10 * scuff * (u > 0.45)
    wear = np.exp(-((u - 0.78) / 0.08) ** 2)                                # hitting zone: lighter, more scuffed
    tone = tone + 0.08 * wear * (0.6 + 0.4 * _n(r, 2, 10))
    lacq = 1 + 0.04 * np.sin(u * 40)                                        # faint lathe rings
    return np.clip(base[None, None, :] * (tone * lacq)[..., None], 0, 255)


def steel(seed=2):
    """galvanised pipe: brushed streaks along the length, rust bloom around the ends and in a few patches, bright scratches, grime."""
    r = np.random.RandomState(seed)
    u = np.linspace(0, 1, W)[None, :]; v = np.linspace(0, 1, H)[:, None]
    base = np.array([62, 64, 69], np.float32)     # round 10: was (112, 116, 122): in full sun the galvanised pipe read as a pale, untextured limb (critic r09 'grey arm'); now a weathered gunmetal pipe
    brushed = _n(r, 0.5, 60) * 0.6 + _n(r, 1.0, 20) * 0.4
    tone = 1 + 0.10 * brushed + 0.05 * _n(r, 8, 40)
    col = base[None, None, :] * tone[..., None]
    rust_field = _n(r, 5, 25) + 0.5 * _n(r, 2, 8) + 1.6 * (np.exp(-(u / 0.10) ** 2) + np.exp(-((1 - u) / 0.10) ** 2))
    rust = np.clip((rust_field - 1.75) * 1.1, 0, 0.75) ** 1.2
    rust_col = np.array([132, 74, 38], np.float32) * (0.75 + 0.25 * _n(r, 1, 3)[..., None].clip(-1, 1))
    col = col * (1 - rust[..., None]) + rust_col * rust[..., None]
    scr = (_n(r, 0.35, 30) > 2.6)                                             # thin bright scratches along the pipe
    col = np.where(scr[..., None], np.minimum(col * 1.35 + 20, 255), col)
    grime = np.clip(_n(r, 4, 50) - 0.6, 0, 1) * 0.35
    col = col * (1 - grime[..., None])
    # round 10: dark oil streaks / paint chips so the pipe has visible structure at 1080p (bands across the length, lighter bare-metal chips)
    bands = 0.5 + 0.5 * np.sin((u * 14 + 0.6 * _n(r, 3, 30)) * 2 * np.pi)
    col = col * (0.82 + 0.28 * bands[..., None] ** 1.5)
    chips = (_n(r, 0.8, 6) > 2.1)
    col = np.where(chips[..., None], np.minimum(col * 1.5 + 18, 255), col)
    return np.clip(col, 0, 255)


def polymer(seed=3):
    """matte black polymer: fine stipple, lighter edge wear."""
    r = np.random.RandomState(seed)
    base = np.array([31, 31, 34], np.float32)
    g = _n(r, 0.7, 0.7)
    wear = np.clip(_n(r, 2, 12) - 1.4, 0, 1) * 0.5
    col = base[None, None, :] * (1 + 0.16 * g + 0.06 * _n(r, 6, 30))[..., None] + 40 * wear[..., None]
    return np.clip(col, 0, 255)


def grip(seed=4):
    """leather / cloth wrap on the pipe: diagonal wrap bands, frayed light edges, sweat-darkened middle."""
    r = np.random.RandomState(seed)
    u = np.linspace(0, 1, W)[None, :]; v = np.linspace(0, 1, H)[:, None]
    base = np.array([58, 48, 40], np.float32)
    band = np.sin((u * 28 + v * 3.5) * 2 * np.pi)
    ridge = 0.5 + 0.5 * band
    weave = 0.5 + 0.5 * np.sin(u * 700) * np.sin(v * 200)
    tone = 0.78 + 0.22 * ridge ** 0.7 + 0.05 * weave + 0.06 * _n(r, 1.2, 4)
    sweat = 1 - 0.25 * np.exp(-((u - 0.5) / 0.22) ** 2)
    edge = np.clip(1 - np.abs(band) ** 6, 0, 1)
    col = base[None, None, :] * (tone * sweat)[..., None] * (0.85 + 0.15 * edge)[..., None]
    return np.clip(col, 0, 255)


def tape(seed=5):
    """black cloth tape on the bat handle: overlapping wraps (soft steps), fine weave, a lighter frayed end."""
    r = np.random.RandomState(seed)
    u = np.linspace(0, 1, W)[None, :]; v = np.linspace(0, 1, H)[:, None]
    base = np.array([26, 26, 28], np.float32)
    step = ((u * 26 + v * 2.2) % 1.0)
    shade = 0.75 + 0.25 * (1 - step) ** 2
    weave = 0.5 + 0.5 * np.sin(u * 900) * np.sin(v * 260)
    tone = shade * (0.9 + 0.1 * weave) + 0.06 * _n(r, 1, 3)
    fray = np.exp(-((1 - u) / 0.04) ** 2) * 0.6
    col = base[None, None, :] * tone[..., None] + 55 * fray[..., None] * (0.5 + 0.5 * _n(r, 0.5, 1.5))[..., None]
    return np.clip(col, 0, 255)


MATERIALS = ['wood', 'steel', 'polymer', 'grip', 'tape']       # tile order (same as add_weapon.TILES)
FUNCS = {'wood': wood, 'steel': steel, 'polymer': polymer, 'grip': grip, 'tape': tape}


def strip(atlas=4096, content_h=3584, x0=3584):
    """The (atlas - content_h) x (atlas - x0) RGB uint8 strip: five stacked tiles, each stretched from 512 x 102 to its slot."""
    h = atlas - content_h; w = atlas - x0
    out = np.zeros((h, w, 3), np.float32)
    for k, nm in enumerate(MATERIALS):
        y0, y1 = int(h * k / len(MATERIALS)), int(h * (k + 1) / len(MATERIALS))
        t = FUNCS[nm](seed=k + 1)
        if t.shape[:2] != (y1 - y0, w):
            zy, zx = (y1 - y0) / t.shape[0], w / t.shape[1]
            t = np.stack([ndi.zoom(t[..., c], (zy, zx), order=1) for c in range(3)], -1)
        out[y0:y1] = t[:y1 - y0, :w]
    return np.clip(out, 0, 255).astype(np.uint8)


if __name__ == '__main__':
    import sys
    from PIL import Image
    Image.fromarray(strip()).save(sys.argv[1] if len(sys.argv) > 1 else 'weapon_strip.png')
