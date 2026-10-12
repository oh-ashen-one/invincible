#!/usr/bin/env python3
"""Round 09: the thug collar wedge (critic r07 / r08: 'thug_face_4k has a 100 x 180 px skin wedge in the collar').

Fan homage project; not an official Marvel, Sony or Insomniac game; no affiliation.

Found with tools/ue_char/people/pose_view.py (the lineup's close-up camera on the skinned, walking thug, no engine): the wedge is the skin of the NAPE / the side of the neck behind the
jaw, bind-pose cylinder azimuth |phi| > 96 deg, y 1.545 - 1.600 m (neck radius < 7 cm), between the hair line and the hood collar (triangles 4192 - 4220 of SK_Street_Thug).  The hood collar is open there, so the
neck is really visible, but as a lit, stair-stepped skin triangle in a dark hood it reads as a defect.  The round-08 texel fix ran on the PRE-fit mesh at y < 1.505 (below the wedge).  This step
runs after skinfit on the FINAL bind-pose mesh: the atlas texels of those triangles (weight fading in over |phi| 88 - 98 deg and out above y 1.572 - 1.582 m) that are skin-coloured take the
hood's shadow (x 0.22 towards a neutral dark), so the gap shows shaded inner hood instead of skin.  The front neck, the jaw and the ears are untouched.
  python3 tools/ue_char/people/nape_fix.py GLB ATLAS.png [ATLAS2.png ...]     (rewrites the atlases in place)
"""
import os, sys, json
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pose_view import Doc, load_mesh  # noqa: E402


def sm(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def main():
    glb, atlases = sys.argv[1], sys.argv[2:]
    doc = Doc(glb)
    P, N, UV, J, W, F, joints, ibm = load_mesh(doc)
    cen = P[F].mean(1)
    phi = np.degrees(np.arctan2(cen[:, 0], cen[:, 2] + 0.02)); r = np.hypot(cen[:, 0], cen[:, 2] + 0.02)
    # round 09b: the first version (y < 1.582, any r) left the strip right under the ear (triangles 3231 / 3234 / 4209 / 4212, y 1.572 - 1.585, r 6.4 - 6.6 cm): the engine capture still showed it.
    # The neck is r < 7 cm there; the ear sticks out beyond (r > 8 cm), so the height limit is lifted for neck-radius triangles only.
    r_lim = 0.095 + (0.072 - 0.095) * sm(1.572, 1.580, cen[:, 1])      # below the ear: the hood-collar triangles of the strip (r 7.8 - 8.1 cm); beside the ear lobe: neck radius only
    # round 10: the r09 selection (a wider one, |phi| from 80 deg and y from 1.515 m, turned the whole neck under the ear into a flat dark-grey plate: tried and reverted)
    # round 11 (critic r10: the wedge = 72 x 151 px at 4K, triangles 4192 - 4216 / 2489 / 3227 found with pose_view's id buffer, |phi| 86 - 128 deg, y 1.538 - 1.578 m): the strip starts at
    # |phi| 86 deg (was 88 - 98) and from y 1.528 m
    w_tri = sm(84, 92, np.abs(phi)) * sm(1.522, 1.534, cen[:, 1]) * (1 - sm(1.592, 1.602, cen[:, 1])) * (1 - sm(r_lim - 0.004, r_lim + 0.004, r))
    sel = np.where(w_tri > 0.02)[0]
    print('nape_fix: %d triangles (bind pose |phi| > 88 deg, y 1.535 - 1.582)' % len(sel))
    for path in atlases:
        im = cv2.imread(path)
        H, Wd = im.shape[:2]
        m = np.zeros((H, Wd), np.float32)
        for t in sel:
            pts = (UV[F[t]] * np.array([Wd, H])).astype(np.int32)
            cv2.fillPoly(m, [pts], float(w_tri[t]))
            cv2.polylines(m, [pts], True, float(w_tri[t]), 2)     # cover the texel gutter around the island edge
        m = cv2.GaussianBlur(m, (0, 0), 2.0)
        rgb = im[..., ::-1].astype(np.float32) / 255
        mx, mn = rgb.max(-1), rgb.min(-1)
        hue_skin = np.ones(rgb.shape[:2], bool)   # round 11: every texel under the selected triangles (rounds 09 / 10 kept the dim ones, which still lit up as tan in the engine)
        w = m * cv2.GaussianBlur(hue_skin.astype(np.float32), (0, 0), 1.0)
        hood = np.array([36, 35, 37], np.float32) / 255     # the hood's own dark (texels there measure 34 - 40)
        # round 10: hue-preserving shade (x 0.40) with a 25 % pull to the hood's dark: the round-09 'hood colour' version read as a flat dark-grey plate on the neck (CPU render), the lift of the
        # strip is the NORMALS (below), not the albedo
        # round 11: the round-10 hue-preserving shade (x 0.40 of the skin) still rendered as a lit tan plane in the engine (3,136 px, r > g + 8): the strip now takes the hood's own dark
        # colour (neutral, 36 / 35 / 37) with 12 % of the texel's luminance detail, so a lit strip reads as the inside of the hood, never as skin
        lum = (rgb @ np.array([0.299, 0.587, 0.114], np.float32))[..., None]
        k = (1.0 * w)[..., None]
        out = rgb * (1 - k) + (hood * (0.88 + 0.12 * lum / max(float(lum.mean()), 1e-3))) * k
        cv2.imwrite(path, (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1])
        print('  %s: %d texels darkened (weight > 0.5)' % (os.path.basename(path), int((w > 0.5).sum())))
    fix_normals(doc, glb, P, N, F, w_tri, cen)


def fix_normals(doc, glb, P, N, F, w_tri, cen):
    """Round 10: the strip's vertex normals point UP (triangle 4192: N = (-0.57, 0.73, 0.26)) = lit by the sun like a shoulder, while the cloth round it faces outward: they take the collar's
    outward, slightly downward normal (weight = the triangle weight, per vertex the maximum), so the strip is shaded like the hood.  Writes the NORMAL accessor of the GLB in place."""
    wv = np.zeros(len(P))
    for t in np.where(w_tri > 0.02)[0]:
        wv[F[t]] = np.maximum(wv[F[t]], w_tri[t])
    rad = np.stack([P[:, 0], np.full(len(P), -0.12), P[:, 2] + 0.02], 1)
    rad[:, [0, 2]] *= 1.0 / (np.hypot(P[:, 0], P[:, 2] + 0.02)[:, None] + 1e-9)
    rad /= np.linalg.norm(rad, axis=1, keepdims=True) + 1e-12
    N2 = N * (1 - wv[:, None]) + rad * wv[:, None]
    N2 /= np.linalg.norm(N2, axis=1, keepdims=True) + 1e-12
    pr = doc.j['meshes'][0]['primitives'][0]; a = doc.j['accessors'][pr['attributes']['NORMAL']]; v = doc.j['bufferViews'][a['bufferView']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0); st = v.get('byteStride', 12)
    import struct
    for i in np.where(wv > 1e-3)[0]: struct.pack_into('<fff', doc.bin, off + i * st, *[float(x) for x in N2[i]])
    doc.write(glb)
    print('nape_fix: normals of %d vertices turned to the collar direction (max change %.0f deg)' % (int((wv > 1e-3).sum()), float(np.degrees(np.arccos(np.clip((N * N2).sum(1), -1, 1))).max())))


if __name__ == '__main__':
    main()
