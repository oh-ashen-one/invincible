#!/usr/bin/env python3
"""Round 09: CPU render of a POSED street enemy from the exact close-up camera of the lineup captures (numpy, no GPU, no Unreal).

Fan homage project; not an official Marvel, Sony or Insomniac game; no affiliation.

Why: the thug collar wedge of rounds 07 / 08 (a skin-coloured triangle in the dark hood collar of thug_face_4k, 100 x 180 px) survived three mitigations because it was
never reproduced outside the engine.  This tool skins SK_Street_<Name>.glb (the UE import GLB, 58 joints) with a clip of SK_Street_Walks.glb (the walkStreet the thug lane plays),
renders it with back-face culling (the game draws single-sided) from the lineup's close-up camera (shot: CLOSEUP, 105 cm, aim height 160, cam height 0, FOV 28 deg, azimuth +25 deg from the
walker's facing) and writes a triangle-id buffer, so a skin-coloured patch in the collar can be traced to the triangle(s) and texels that cause it.

  python3 tools/ue_char/people/pose_view.py Thug OUT_PREFIX [--t 0.5,1.0] [--clip walkStreet] [--size 1920x1080] [--dist 105] [--aim 1.60] [--az 25]
  writes OUT_PREFIX_t<t>.png (colour) and OUT_PREFIX_t<t>_ids.npy (int32 triangle id per pixel, -1 = background) and prints the skin-coloured components found in the collar box.
"""
import os, sys, json, struct
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, os.path.join(HERE, '..', 'heroanim')); sys.path.insert(0, os.path.join(HERE, '..', 'suit8'))
from p2paths import SCRATCH  # noqa: E402
from ganim import Doc  # noqa: E402
import softrender as sr  # noqa: E402


def acc(doc, i):
    a = doc.j['accessors'][i]; v = doc.j['bufferViews'][a['bufferView']]
    nc = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a['type']]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a['componentType']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    st = v.get('byteStride', nc * np.dtype(dt).itemsize)
    if st == nc * np.dtype(dt).itemsize:
        out = np.frombuffer(doc.bin, dtype=dt, count=a['count'] * nc, offset=off).reshape(a['count'], nc).copy()
    else:
        out = np.zeros((a['count'], nc), dt)
        for k in range(a['count']): out[k] = np.frombuffer(doc.bin, dtype=dt, count=nc, offset=off + k * st)
    if a.get('normalized') and dt != np.float32: out = out.astype(np.float32) / np.iinfo(dt).max
    return out


def load_mesh(doc):
    pr = doc.j['meshes'][0]['primitives'][0]; at = pr['attributes']
    P = acc(doc, at['POSITION']).astype(np.float64); N = acc(doc, at['NORMAL']).astype(np.float64)
    UV = acc(doc, at['TEXCOORD_0']).astype(np.float64)
    J = acc(doc, at['JOINTS_0']).astype(int); W = acc(doc, at['WEIGHTS_0']).astype(np.float64)
    F = acc(doc, pr['indices']).reshape(-1, 3).astype(int)
    sk = doc.j['skins'][0]
    ibm = acc(doc, sk['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1).astype(np.float64)   # glTF is column-major
    return P, N, UV, J, W, F, sk['joints'], ibm


def pose(doc, walks, clip, t):
    """Joint world matrices of `doc`'s skeleton with `clip` of `walks` at time t (nodes matched by name)."""
    tr_src = walks.tracks(clip); by_name = {n: i for i, n in enumerate(doc.names)}
    tr = {}
    for node, chs in tr_src.items():
        nm = walks.names[node]
        if nm in by_name: tr[by_name[nm]] = chs
    return doc.world(doc.sample(tr, t))


def skin(P, N, J, Wt, joints, ibm, W):
    jm = np.stack([W[joints[k]] @ ibm[k] for k in range(len(joints))])       # (nj, 4, 4)
    Ph = np.c_[P, np.ones(len(P))]
    out = np.zeros_like(P); outn = np.zeros_like(N)
    for k in range(4):
        M = jm[J[:, k]]
        out += Wt[:, k:k + 1] * np.einsum('nij,nj->ni', M, Ph)[:, :3]
        outn += Wt[:, k:k + 1] * np.einsum('nij,nj->ni', M[:, :3, :3], N)
    outn /= np.linalg.norm(outn, axis=1, keepdims=True) + 1e-12
    return out, outn


def raster_ids(S, F, w, h, cull=True):
    zb = np.full((h, w), np.inf, np.float32); fid = np.full((h, w), -1, np.int32)
    bc = np.zeros((h, w, 2), np.float32)
    for fi in range(len(F)):
        a, b, c = S[F[fi, 0]], S[F[fi, 1]], S[F[fi, 2]]
        if a[2] <= 0.01 or b[2] <= 0.01 or c[2] <= 0.01: continue
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-9: continue
        if cull and den > 0: continue          # screen y points down: front-facing triangles of the glTF winding have den < 0
        x0 = max(int(np.floor(min(a[0], b[0], c[0]))), 0); x1 = min(int(np.ceil(max(a[0], b[0], c[0]))), w - 1)
        y0 = max(int(np.floor(min(a[1], b[1], c[1]))), 0); y1 = min(int(np.ceil(max(a[1], b[1], c[1]))), h - 1)
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        w2 = 1 - w0 - w1
        m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not m.any(): continue
        z = w0 * a[2] + w1 * b[2] + w2 * c[2]
        sl = (slice(y0, y1 + 1), slice(x0, x1 + 1))
        ok = m & (z < zb[sl])
        if not ok.any(): continue
        zb[sl][ok] = z[ok]; fid[sl][ok] = fi; bc[sl][ok] = np.stack([w0[ok], w1[ok]], -1)
    return fid, bc, zb


def shade(P, N, UV, F, fid, bc, tex, eye, light=(-0.45, 0.65, 0.62)):
    h, w = fid.shape
    img = np.zeros((h, w, 3), np.float32); img[:] = (0.42, 0.46, 0.50)
    ys, xs = np.nonzero(fid >= 0)
    f = F[fid[ys, xs]]
    a = bc[ys, xs, 0][:, None]; b = bc[ys, xs, 1][:, None]; c = 1 - a - b
    Nn = a * N[f[:, 0]] + b * N[f[:, 1]] + c * N[f[:, 2]]; Nn /= np.linalg.norm(Nn, axis=1, keepdims=True) + 1e-9
    uv = a * UV[f[:, 0]] + b * UV[f[:, 1]] + c * UV[f[:, 2]]
    alb = sr.sample(tex, uv)[:, :3]
    sun = np.asarray(light, float); sun /= np.linalg.norm(sun)
    ndl = np.clip(Nn @ sun, 0, 1); up = 0.5 + 0.5 * Nn[:, 1]
    col = alb * (0.55 * (up[:, None] * np.array([0.5, 0.58, 0.7]) + (1 - up)[:, None] * np.array([0.22, 0.2, 0.18])) + 1.05 * ndl[:, None])
    img[ys, xs] = col
    return np.clip(img, 0, 1) ** (1 / 2.2), alb


def main():
    a = sys.argv[1:]
    name, out = a[0], a[1]
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    ts = [float(x) for x in opt('--t', '0.5').split(',')]
    clip = opt('--clip', 'walkStreet'); W_, H_ = [int(x) for x in opt('--size', '1920x1080').split('x')]
    dist = float(opt('--dist', '105')) / 100.0; aim_y = float(opt('--aim', '1.60')); az = float(opt('--az', '25'))
    doc = Doc(opt('--glb', os.path.join(SCRATCH, 'ueimport', 'SK_Street_%s.glb' % name))); walks = Doc(os.path.join(SCRATCH, 'ueimport', 'SK_Street_Walks.glb'))
    P, N, UV, J, Wt, F, joints, ibm = load_mesh(doc)
    atlas = cv2.imread(opt('--atlas', os.path.join(SCRATCH, 'r3', 'people', 'Street%s_atlas.png' % name)))[..., ::-1].astype(np.float32) / 255
    tex = cv2.resize(atlas, (4096, 4096), interpolation=cv2.INTER_AREA) ** 2.2 if atlas.shape[0] != 4096 else atlas ** 2.2
    # camera: 105 cm from the aim point, azimuth +25 deg toward the walker's RIGHT (glTF: forward +z, left +x), same height as the aim point (cam height 0)
    r = np.radians(az)
    eye = np.array([-np.sin(r) * dist, aim_y, np.cos(r) * dist]); tgt = np.array([0, aim_y, 0.0])
    cam = sr.look_at(eye, tgt)
    fov_v = 2 * np.degrees(np.arctan(np.tan(np.radians(28.0) / 2) * H_ / W_))
    for t in ts:
        Wm = pose(doc, walks, clip, t)
        Pp, Np = skin(P, N, J, Wt, joints, ibm, Wm)
        S = sr.project(Pp, cam, fov_v, W_, H_)
        fid, bc, zb = raster_ids(S, F, W_, H_)
        img, alb = shade(Pp, Np, UV, F, fid, bc, tex, eye)
        tag = '%s_t%.2f' % (out, t)
        sr.save(img, tag + '.png'); np.save(tag + '_ids.npy', fid)
        print('t=%.2f: rendered %s (%d px covered)' % (t, tag + '.png', int((fid >= 0).sum())))


if __name__ == '__main__':
    main()
