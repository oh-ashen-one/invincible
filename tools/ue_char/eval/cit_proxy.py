# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Offline stand-in for the engine's citizen rendering (round 06): the crowd pack's baked skinning matrices (people.bin), linear blend skinning with
<= 4 influences per vertex (what the GPU does), single-sided orthographic raster with cv2, and the two CH18 measures:

  * key holes  = background pixels ENCLOSED by the person mask (same definition as key_holes.py on the engine's green-key stills)
  * spikes     = per-triangle edge stretch over the crowd's own walk / idle clips (posed edge length - rest edge length, in cm)

No GPU, no Blender.  Everything the FBX exporter consumes goes through `Mesh` so the proxy sees the same geometry.
"""
import json, os, sys
import numpy as np
import cv2
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from p2paths import WT  # noqa: E402

NPC = os.path.join(WT, 'public/assets/city/npc')
CLIPS_USED = ('walk', 'walkF', 'walkBrisk', 'walkStroll', 'walkOld', 'idle')


class Rig:
    def __init__(self):
        p = json.load(open(os.path.join(NPC, 'people.json')))
        pb = open(os.path.join(NPC, 'people.bin'), 'rb').read()
        self.p = p
        self.A = np.frombuffer(pb, np.float32, p['frames'] * p['nb'] * 12, p['anim']).reshape(p['frames'], p['nb'], 3, 4).astype(float)
        self.nb = p['nb']
        self.names = [b['name'] for b in p['bones']]

    def mats(self, clip, frame):
        cl = self.p['clips'][clip]
        return self.A[cl['row'] + (frame % cl['len'])]

    def clip_len(self, clip):
        return self.p['clips'][clip]['len']


RIG = None


def rig():
    global RIG
    if RIG is None: RIG = Rig()
    return RIG


def skin(P, dense, Mf, top=4):
    """LBS with at most `top` influences per vertex (dense (n, nb) weights, renormalised after truncation)."""
    D = dense
    if top and (D > 0).sum(1).max() > top:
        idx = np.argsort(-D, axis=1)[:, :top]
        w = np.take_along_axis(D, idx, 1); w /= np.maximum(w.sum(1, keepdims=True), 1e-9)
        Ph = np.c_[P, np.ones(len(P))]
        out = np.zeros((len(P), 3))
        for k in range(top):
            M = Mf[idx[:, k]]                                   # (n,3,4)
            out += w[:, k:k + 1] * np.einsum('nij,nj->ni', M, Ph)
        return out
    Ph = np.c_[P, np.ones(len(P))]
    return np.einsum('nb,nbi->ni', D, np.einsum('bij,nj->nbi', Mf, Ph))


class Mesh:
    """rest positions P (nv,3), triangles T (nt,3), per-vertex uv (u, v_img) with v_img measured from the top of the texture, dense weights (nv, 18)."""
    def __init__(self, P, T, uv, dense, tex=None, name=''):
        self.P, self.T, self.uv, self.dense, self.tex, self.name = P, T, uv, dense, tex, name

    def posed(self, clip, frame, top=4):
        return skin(self.P, self.dense, rig().mats(clip, frame), top)


def view_matrix(yaw_deg):
    th = np.radians(yaw_deg)
    return np.array([[np.cos(th), 0, np.sin(th)], [0, 1, 0], [-np.sin(th), 0, np.cos(th)]])


def raster(Pw, T, uv, tex, yaw, ppm, W, H, ox, oy, colour=True, bg=(60, 255, 60), cull=True, light=(0.35, 0.55, 0.75), gid=None):
    """Painter's raster of the front-facing triangles, far to near.  Returns (image BGR uint8, mask bool).  ox, oy = pixel of the world origin."""
    R = view_matrix(yaw)
    Q = Pw @ R.T
    A, B, C = Q[T[:, 0]], Q[T[:, 1]], Q[T[:, 2]]
    fn = np.cross(B - A, C - A)
    fl = np.linalg.norm(fn, axis=1) + 1e-15
    fn /= fl[:, None]
    front = fn[:, 2] > 0 if cull else np.ones(len(T), bool)
    order = np.where(front)[0]
    order = order[np.argsort((A[order, 2] + B[order, 2] + C[order, 2]))]      # far first
    img = np.zeros((H, W, 3), np.uint8); img[:] = np.array(bg, np.uint8)[::-1]
    mask = np.zeros((H, W), np.uint8)
    gbuf = np.zeros((H, W), np.uint8) if gid is not None else None
    L = np.asarray(light, float); L /= np.linalg.norm(L)
    lam = 0.5 + 0.5 * np.clip(fn @ L, 0, 1)
    sx = Q[:, 0] * ppm + ox; sy = oy - Q[:, 1] * ppm
    P2 = np.stack([sx, sy], 1)
    SH = 4; ONE = 1 << SH
    if colour and tex is not None:
        th_, tw_ = tex.shape[:2]
        cuv = uv[T].mean(1) if uv.ndim == 2 else uv.mean(1)
        col = tex[np.clip((cuv[:, 1] * th_).astype(int), 0, th_ - 1), np.clip((cuv[:, 0] * tw_).astype(int), 0, tw_ - 1)].astype(float)
        col = np.clip(col * lam[:, None], 0, 255).astype(np.uint8)[:, ::-1]
    for t in order:
        pts = np.round(P2[T[t]] * ONE).astype(np.int32)
        if colour and tex is not None:
            cv2.fillConvexPoly(img, pts, tuple(int(x) for x in col[t]), lineType=cv2.LINE_8, shift=SH)
        cv2.fillConvexPoly(mask, pts, 1, lineType=cv2.LINE_8, shift=SH)
        if gbuf is not None: cv2.fillConvexPoly(gbuf, pts, int(gid[t]), lineType=cv2.LINE_8, shift=SH)
    if gid is not None: return img, mask.astype(bool), gbuf
    return img, mask.astype(bool)


GROUP = {0: 1, 1: 1, 2: 1, 3: 7, 4: 7, 5: 2, 6: 2, 8: 3, 9: 3, 11: 4, 12: 4, 13: 4, 14: 5, 15: 5, 16: 5, 7: 6, 10: 6, 17: 6}   # 1 torso, 2 arm L, 3 arm R, 4 leg L, 5 leg R, 6 hands, 7 head + neck


def tri_groups(mesh):
    """Limb group id (1..6, see GROUP) of every triangle = the group holding most of its three vertices' skin weight."""
    g = np.zeros((len(mesh.dense), 8))
    for b, k in GROUP.items(): g[:, k] += mesh.dense[:, b]
    return (g[mesh.T].sum(1)).argmax(1).astype(np.uint8)


def classify_holes(thin_m, gbuf, wide_m=None, ring=3):
    """Split thin enclosed components into cracks (all bordering pixels belong to ONE limb group: a tear in a garment) and gaps (the border
    touches two limb groups, or only the hands: the air between an arm and the torso, between the legs, between fingers = natural).
    Returns (crack_mask, gap_mask, cracks_by_group {group id: [px counts]})."""
    lab, n = ndimage.label(thin_m)
    crack = np.zeros_like(thin_m); gap = np.zeros_like(thin_m); by = {}
    if not n: return crack, gap, by
    objs = ndimage.find_objects(lab)
    for i, sl in enumerate(objs, 1):
        y0, y1 = max(0, sl[0].start - ring - 1), sl[0].stop + ring + 1; x0, x1 = max(0, sl[1].start - ring - 1), sl[1].stop + ring + 1
        comp = lab[y0:y1, x0:x1] == i
        if wide_m is not None and (ndimage.binary_dilation(comp, iterations=2) & wide_m[y0:y1, x0:x1]).any():   # tip / edge of a big natural gap
            gap[y0:y1, x0:x1] |= comp; continue
        rim = ndimage.binary_dilation(comp, iterations=ring) & ~comp
        ids = np.unique(gbuf[y0:y1, x0:x1][rim]); ids = ids[ids > 0]
        if len(ids) >= 2 or (len(ids) == 1 and ids[0] >= 6): gap[y0:y1, x0:x1] |= comp     # two limbs, only hands (fingers) or only head / hair
        else:
            crack[y0:y1, x0:x1] |= comp; by.setdefault(int(ids[0]) if len(ids) else 0, []).append(int(comp.sum()))
    return crack, gap, by


def key_holes(mask, thin=5, min_person=2000):
    """Background pixels enclosed by the person: (thin_components, thin_px, wide_px, thin_mask).  `thin` = opening size (px)."""
    lab, n = ndimage.label(mask)
    sz = np.bincount(lab.ravel())
    m = (sz[lab] >= min_person) & (lab > 0)
    m = ndimage.binary_closing(m, structure=np.ones((3, 3), bool))
    filled = ndimage.binary_fill_holes(m)
    holes = filled & ~m
    op = ndimage.binary_opening(holes, structure=np.ones((thin, thin), bool))
    thin_m = holes & ~op
    lt, nt = ndimage.label(thin_m)
    if nt:
        st = np.bincount(lt.ravel())[1:]
        keep = np.where(st >= 4)[0] + 1
        thin_m = np.isin(lt, keep)
        nt = len(keep)
    return int(nt), int(thin_m.sum()), int(op.sum()), thin_m, op


def stretch(mesh, clips=CLIPS_USED, every=2, top=4):
    """Per-triangle worst edge elongation (posed - rest edge length, metres) and worst ratio over the sampled frames."""
    T = mesh.T
    E = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    rest = np.linalg.norm(mesh.P[E[:, 0]] - mesh.P[E[:, 1]], axis=1)
    worst = np.zeros(len(E)); wr = np.zeros(len(E))
    for cn in clips:
        if cn not in rig().p['clips']: continue
        for f in range(0, rig().clip_len(cn), every):
            Q = mesh.posed(cn, f, top)
            ln = np.linalg.norm(Q[E[:, 0]] - Q[E[:, 1]], axis=1)
            worst = np.maximum(worst, ln - rest); wr = np.maximum(wr, ln / (rest + 1e-4))
    return worst.reshape(3, -1).max(0), wr.reshape(3, -1).max(0)


def frame_view(Pw_list, ppm, margin=0.08):
    """Common frame for a list of posed point sets: (W, H, ox, oy) at the given yaw-independent extents (uses max radius around the vertical axis)."""
    allp = np.vstack(Pw_list)
    r = np.sqrt(allp[:, 0] ** 2 + allp[:, 2] ** 2).max() + margin
    ymax = allp[:, 1].max() + margin; ymin = min(0.0, allp[:, 1].min()) - margin
    W = int(2 * r * ppm); H = int((ymax - ymin) * ppm)
    return W, H, W / 2.0, ymax * ppm


def raster_tex(Pw, T, uv, tex, yaw, ppm, W, H, ox, oy, bg=(190, 190, 190), light=(0.35, 0.55, 0.75), cull=True, ambient=0.55, nrm=None):
    """Textured painter's raster (per-triangle affine texture warp, bilinear): for close-up inspection (few thousand triangles in view)."""
    R = view_matrix(yaw)
    Q = Pw @ R.T
    A_, B_, C_ = Q[T[:, 0]], Q[T[:, 1]], Q[T[:, 2]]
    fn = np.cross(B_ - A_, C_ - A_); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-15
    front = fn[:, 2] > 0 if cull else np.ones(len(T), bool)
    sx = Q[:, 0] * ppm + ox; sy = oy - Q[:, 1] * ppm
    P2 = np.stack([sx, sy], 1)
    th_, tw_ = tex.shape[:2]
    img = np.zeros((H, W, 3), np.uint8); img[:] = np.array(bg, np.uint8)[::-1]
    L = np.asarray(light, float); L /= np.linalg.norm(L)
    lam = ambient + (1 - ambient) * np.clip(fn @ L, 0, 1)
    order = np.where(front)[0]
    order = order[np.argsort(A_[order, 2] + B_[order, 2] + C_[order, 2])]
    texb = np.ascontiguousarray(tex[..., ::-1])
    for t in order:
        s = P2[T[t]].astype(np.float32)
        x0, y0 = np.floor(s.min(0)).astype(int) - 1; x1, y1 = np.ceil(s.max(0)).astype(int) + 1
        if x1 < 0 or y1 < 0 or x0 >= W or y0 >= H: continue
        x0c, y0c, x1c, y1c = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
        if x1c <= x0c or y1c <= y0c: continue
        u = (uv[T[t]] * np.array([tw_, th_])).astype(np.float32)
        M = cv2.getAffineTransform(u, s - np.array([x0c, y0c], np.float32))
        patch = cv2.warpAffine(texb, M, (x1c - x0c, y1c - y0c), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        m = np.zeros((y1c - y0c, x1c - x0c), np.uint8)
        cv2.fillConvexPoly(m, np.round((s - np.array([x0c, y0c], np.float32)) * 16).astype(np.int32), 1, lineType=cv2.LINE_AA, shift=4)
        sub = img[y0c:y1c, x0c:x1c]
        mm = m.astype(bool)
        sub[mm] = np.clip(patch[mm].astype(np.float32) * lam[t], 0, 255).astype(np.uint8)
    return img


def silhouette_spikes(gbuf, groups=(1, 2, 3, 4, 5), r=6, min_len=6):
    """Thin protrusions of the garment silhouette (torso, arms, legs; not hands / head): pixels that a disc opening of radius r removes, as components
    whose longest side is >= min_len px.  A protrusion thinner than 2 r px and longer than `min_len` px is what a stretched triangle / vertex spike
    looks like from the side (the critic's "spike longer than 5 px outside the cloth hull").  Returns (count, px, mask)."""
    m = np.isin(gbuf, groups)
    m = ndimage.binary_closing(m, structure=np.ones((3, 3), bool))
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    op = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, k).astype(bool)
    thin = m & ~op
    lab, n = ndimage.label(thin)
    if not n: return 0, 0, thin
    keep = np.zeros(n + 1, bool); px = 0
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        h = sl[0].stop - sl[0].start; w = sl[1].stop - sl[1].start
        if max(h, w) >= min_len and (lab[sl] == i).sum() >= 12: keep[i] = True; px += int((lab[sl] == i).sum())
    return int(keep.sum()), px, keep[lab]
