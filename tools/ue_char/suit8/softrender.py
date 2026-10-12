# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""CPU preview renderer for the round-08 suit and lens work (numpy z-buffer, no GPU, no Unreal).  Rest-pose meshes, simple sun + sky shading with a
Blinn highlight; textures are sampled bilinearly (base colour, optional tangent-space normal map).  It is a design aid only: every claim in the
round documents is measured on frames of the real game.
"""
import numpy as np
import cv2


def look_at(eye, target, up=(0, 1, 0)):
    eye = np.asarray(eye, float); target = np.asarray(target, float)
    f = target - eye; f /= np.linalg.norm(f)
    r = np.cross(f, up); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return eye, r, u, f


def project(P, cam, fov_deg, w, h):
    eye, r, u, f = cam
    d = P - eye
    x = d @ r; y = d @ u; z = d @ f
    s = 0.5 * h / np.tan(np.radians(fov_deg) / 2)
    return np.stack([w / 2 + s * x / z, h / 2 - s * y / z, z], -1)


class Prim:
    def __init__(self, P, N, F, UV=None, tex=None, nmap=None, color=None, rough=0.6, spec=0.3, name=''):
        self.P, self.N, self.F, self.UV, self.tex, self.nmap = P, N, F, UV, tex, nmap
        self.color = np.asarray(color if color is not None else (0.6, 0.6, 0.6), np.float32)
        self.rough, self.spec, self.name = rough, spec, name


def sample(tex, uv):
    """Bilinear texture lookup (wrap = clamp)."""
    h, w = tex.shape[:2]
    x = np.clip(uv[:, 0] * w - 0.5, 0, w - 1.001); y = np.clip(uv[:, 1] * h - 0.5, 0, h - 1.001)
    x0 = x.astype(np.int32); y0 = y.astype(np.int32); fx = (x - x0)[:, None]; fy = (y - y0)[:, None]
    t00 = tex[y0, x0]; t10 = tex[y0, x0 + 1]; t01 = tex[y0 + 1, x0]; t11 = tex[y0 + 1, x0 + 1]
    return (t00 * (1 - fx) + t10 * fx) * (1 - fy) + (t01 * (1 - fx) + t11 * fx) * fy


def render(prims, cam, fov, w, h, sun=(-0.45, 0.65, 0.62), sky=(0.50, 0.58, 0.70), ground=(0.22, 0.2, 0.18), bg=(0.42, 0.46, 0.50), sun_col=(1.0, 0.95, 0.85), ssaa=1):
    if ssaa > 1:
        im = render(prims, cam, fov, w * ssaa, h * ssaa, sun, sky, ground, bg, sun_col, 1)
        return cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA)
    zbuf = np.full((h, w), np.inf, np.float32)
    pid = np.full((h, w), -1, np.int16); fid = np.full((h, w), -1, np.int32)
    b0 = np.zeros((h, w), np.float32); b1 = np.zeros((h, w), np.float32)
    eye = cam[0]
    for pi, pr in enumerate(prims):
        S = project(pr.P.astype(np.float64), cam, fov, w, h)
        fn = np.cross(pr.P[pr.F[:, 1]] - pr.P[pr.F[:, 0]], pr.P[pr.F[:, 2]] - pr.P[pr.F[:, 0]])
        cen = pr.P[pr.F].mean(1)
        for fi in range(len(pr.F)):
            a, b, c = S[pr.F[fi, 0]], S[pr.F[fi, 1]], S[pr.F[fi, 2]]
            if a[2] <= 0.01 or b[2] <= 0.01 or c[2] <= 0.01: continue
            x0 = max(int(np.floor(min(a[0], b[0], c[0]))), 0); x1 = min(int(np.ceil(max(a[0], b[0], c[0]))), w - 1)
            y0 = max(int(np.floor(min(a[1], b[1], c[1]))), 0); y1 = min(int(np.ceil(max(a[1], b[1], c[1]))), h - 1)
            if x1 < x0 or y1 < y0: continue
            den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(den) < 1e-9: continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
            w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
            w2 = 1 - w0 - w1
            m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not m.any(): continue
            z = w0 * a[2] + w1 * b[2] + w2 * c[2]
            sl = (slice(y0, y1 + 1), slice(x0, x1 + 1))
            ok = m & (z < zbuf[sl])
            if not ok.any(): continue
            zbuf[sl][ok] = z[ok]; pid[sl][ok] = pi; fid[sl][ok] = fi; b0[sl][ok] = w0[ok]; b1[sl][ok] = w1[ok]
    img = np.zeros((h, w, 3), np.float32); img[:] = np.asarray(bg, np.float32)
    sun = np.asarray(sun, float); sun /= np.linalg.norm(sun)
    for pi, pr in enumerate(prims):
        ys, xs = np.nonzero(pid == pi)
        if len(ys) == 0: continue
        f = pr.F[fid[ys, xs]]
        a = b0[ys, xs][:, None]; b = b1[ys, xs][:, None]; c = 1 - a - b
        Pp = a * pr.P[f[:, 0]] + b * pr.P[f[:, 1]] + c * pr.P[f[:, 2]]
        Nn = a * pr.N[f[:, 0]] + b * pr.N[f[:, 1]] + c * pr.N[f[:, 2]]
        Nn /= np.linalg.norm(Nn, axis=1, keepdims=True) + 1e-9
        if pr.UV is not None and pr.tex is not None:
            uv = a * pr.UV[f[:, 0]] + b * pr.UV[f[:, 1]] + c * pr.UV[f[:, 2]]
            alb = sample(pr.tex, uv)[:, :3]
            if pr.nmap is not None:   # tangent space from the triangle's UV frame
                fe = pr.F[fid[ys, xs]]
                p0, p1, p2 = pr.P[fe[:, 0]], pr.P[fe[:, 1]], pr.P[fe[:, 2]]
                t0, t1, t2 = pr.UV[fe[:, 0]], pr.UV[fe[:, 1]], pr.UV[fe[:, 2]]
                e1, e2 = p1 - p0, p2 - p0; d1, d2 = t1 - t0, t2 - t0
                r = 1.0 / (d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1] + 1e-12)
                T = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) * r[:, None]
                T -= Nn * (T * Nn).sum(1, keepdims=True); T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-12
                Bt = -np.cross(Nn, T)        # glTF v is down: bitangent points along -v
                nm = sample(pr.nmap, uv)[:, :3] * 2 - 1
                Nn = nm[:, 0:1] * T + nm[:, 1:2] * Bt + nm[:, 2:3] * Nn
                Nn /= np.linalg.norm(Nn, axis=1, keepdims=True) + 1e-9
        else:
            alb = np.tile(pr.color, (len(ys), 1))
        V = eye - Pp; V /= np.linalg.norm(V, axis=1, keepdims=True)
        ndl = np.clip(Nn @ sun, 0, 1)
        up = 0.5 + 0.5 * Nn[:, 1]
        amb = up[:, None] * np.asarray(sky, np.float32) + (1 - up)[:, None] * np.asarray(ground, np.float32)
        Hh = V + sun; Hh /= np.linalg.norm(Hh, axis=1, keepdims=True)
        shin = max(2.0, 2.0 / max(pr.rough, 0.05) ** 2)
        sp = pr.spec * np.clip((Nn * Hh).sum(1), 0, 1) ** shin
        col = alb * (0.55 * amb + 1.05 * ndl[:, None] * np.asarray(sun_col, np.float32)) + sp[:, None]
        img[ys, xs] = col
    return np.clip(img, 0, 1) ** (1 / 2.2)


def save(img, path):
    cv2.imwrite(path, (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)[..., ::-1])
