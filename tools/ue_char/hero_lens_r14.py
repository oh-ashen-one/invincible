#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 14 hero eyes on the SCULPTED mask (tools/ue_char/suit8/hero_head_r14.py); r13 numbers were 63 x 28 mm lenses at 39 mm, a 3.6 mm rim.  Round 14 seats each
lens + rim IN its eye socket under the brow ridge: 61 mm lenses (>= 1.6x r12) centred 41 mm from the midline, a 3.1 mm rim crest, ONE closed band (>= 6 px at 4K).

The round-13 text follows (hero_head_r13.py): the round-08 construction (one closed bezel ring sealed to a lens, both conformed to
the mask surface z(x, y), the bezel's outer foot buried in the mask) with the round-13 numbers:

  * lens >= 1.6x the round-12 width (r12: 38.5 mm x 17.7 mm, 12 deg tilt, blade shape; r13: 63 mm x ~30 mm (1.65x)), an ORIGINAL rounded pill / bean outline (tilt 3 deg, a
    little taller toward the nose, arched top; NOT a teardrop and not the slanted blade of r12), centred 39 mm from the midline, so it stays inside the mask outline;
  * ONE closed raised rim 3.4 mm wide (2.8 mm of lip + 0.6 mm shoulder; ~28 px at 4K head close-ups, the gate is 6 px), 3.6 mm proud of the mask (r12: 4.3 / 2.3 mm), dark gunmetal in the material (MI_Hero_LensFrame, polished so it reads on a dark mask);
  * a curved glossy lens: edge 0.8 mm + a 2.6 mm dome;
  * the surface under the eye comes from the sculpted mask: 2 mm envelope (r8: 5 mm) so the rim follows the eye socket and the nose bridge without floating.

  python3 tools/ue_char/hero_lens_r13.py SK_Hero.glb [--dump DIR]
"""
import sys, os
import numpy as np
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hero_lens_r8 as H  # noqa: E402

A_HALF, B_HALF = 30.5, 13.8        # mm, lens half length / half height before the arch and the taper
TILT_DEG = 3.0
RIM_H = 2.6                        # mm the rim's crest stands proud of the mask (r13 3.6, r14 3.1; round 15 2.6: the rim sits in the eye socket under the brow ridge)


def setup(a_half=None, b_half=None, cx=None, cy=None, rim_h=None, tilt=None):
    """Apply the lens numbers to the r8 library (call before main(); the defaults are the round-14 build)."""
    global A_HALF, B_HALF, TILT_DEG, RIM_H
    A_HALF = a_half if a_half is not None else A_HALF
    B_HALF = b_half if b_half is not None else B_HALF
    TILT_DEG = tilt if tilt is not None else TILT_DEG
    RIM_H = rim_h if rim_h is not None else RIM_H
    H.CENTER_X = cx if cx is not None else 0.0435          # round 15: 41.0 -> 43.5 mm (the nose end of the rim leaves the nose flank)
    H.CENTER_Y = cy if cy is not None else 1.6700
    H.N_OUT = 96
    H.RINGS = 10
    k = RIM_H / 3.6
    H.BEZEL = [(0.0, 0.8), (0.0, 0.8 + 2.0 * k), (0.7, 0.8 + 2.7 * k), (1.6, RIM_H), (2.6, 2.4 * k), (3.4, 0.9 * k), (3.9, -0.9)]     # (outward offset mm, height above the mask mm); first = lens edge
    H.LENS_EDGE_H, H.LENS_DOME_H = 0.8, 2.6
    H.TILT = np.radians(TILT_DEG)


setup()


def outline(mirror, n=None):
    n = n or H.N_OUT
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    p = 2.5                                              # super-ellipse exponent: a rounded pill, not an ellipse and not a blade
    c, s = np.cos(t), np.sin(t)
    u = A_HALF * np.sign(c) * np.abs(c) ** (2 / p)
    v = B_HALF * np.sign(s) * np.abs(s) ** (2 / p)
    v = v * (1.0 - 0.06 * (-u / A_HALF))                 # a little shorter at the nose end (u < 0 = toward the nose for the left eye): the bridge keeps a gap
    v = v + 2.6 * (1 - (u / A_HALF) ** 2)                # arched: the top and the bottom edges both bow up
    pts = np.stack([u, v], 1) * 1e-3
    ct, st = np.cos(H.TILT), np.sin(H.TILT)
    pts = pts @ np.array([[ct, -st], [st, ct]]).T
    # the left eye (x > 0) has its nose end at u < 0; mirror flips x of the right eye
    pts[:, 0] += 0.0
    if mirror: pts[:, 0] = -pts[:, 0]
    pts[:, 0] += (-H.CENTER_X if mirror else H.CENTER_X); pts[:, 1] += H.CENTER_Y
    return pts


def head_height_field(P, F, step=2.5e-4, x0=-0.11, x1=0.11, y0=1.55, y1=1.78):
    """r8's rasteriser with a 2 mm envelope (the sculpted face has relief within 5 mm of the eye)."""
    nx = int(round((x1 - x0) / step)); ny = int(round((y1 - y0) / step))
    Z = np.full((ny, nx), -1.0, np.float32)
    tri = P[F]
    keep = (tri[:, :, 1].max(1) > y0) & (tri[:, :, 1].min(1) < y1) & (np.abs(tri[:, :, 0]).min(1) < x1)
    fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    keep &= fn[:, 2] > 0
    for t in tri[keep]:
        px = (t[:, 0] - x0) / step; py = (t[:, 1] - y0) / step
        xa, xb = max(int(np.floor(px.min())), 0), min(int(np.ceil(px.max())), nx - 1)
        ya, yb = max(int(np.floor(py.min())), 0), min(int(np.ceil(py.max())), ny - 1)
        if xb < xa or yb < ya: continue
        gx, gy = np.meshgrid(np.arange(xa, xb + 1) + 0.5, np.arange(ya, yb + 1) + 0.5)
        a, b, c = np.stack([px, py], 1)
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12: continue
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        w2 = 1 - w0 - w1
        m = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
        z = w0 * t[0, 2] + w1 * t[1, 2] + w2 * t[2, 2]
        sl = (slice(ya, yb + 1), slice(xa, xb + 1))
        Z[sl] = np.where(m & (z > Z[sl]), z, Z[sl])
    hole = Z < 0
    if hole.any():
        _, (iy, ix) = ndi.distance_transform_edt(hole, return_indices=True); Z = Z[iy, ix]
    env = ndi.maximum_filter(Z, size=int(round(0.002 / step)))
    Zs = ndi.gaussian_filter(env, 0.0015 / step)
    Zs = np.maximum(Zs, ndi.gaussian_filter(Z, 0.001 / step))
    return Zs, Z, (x0, y0, step)


H.outline = outline
H.head_height_field = head_height_field

def main(path, dump=None):
    return H.main(path, dump)


if __name__ == '__main__':
    H.main(sys.argv[1], sys.argv[sys.argv.index('--dump') + 1] if '--dump' in sys.argv else None)
