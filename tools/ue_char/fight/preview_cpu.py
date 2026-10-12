#!/usr/bin/env python3
"""Round 09: CPU preview of the scripted fight with the REAL meshes (numpy, no GPU, no Unreal): the hero and the six enemies skinned with the clips the engine will play,
blended like UWHCharAnimInstance does (script beats over the base idle / walk), placed by the actors' paths, seen from a shot camera of Char_Fight.

Fan homage project; not an official Marvel, Sony or Insomniac game; no affiliation.  A design aid only (flat lighting, hero in one colour, single texture per enemy): every claim in the round
documents is measured on frames of the real game.  Its job is to catch what a stick figure cannot: mirrored sides, a knock-back the wrong way, a fist that misses, bodies inside bodies.

  python3 tools/ue_char/fight/preview_cpu.py OUT.png T1,T2,... [--cam wide|34|orbit] [--size 1280x720] [--cols 2]
"""
import os, sys, json, math
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, os.path.join(HERE, '..', 'heroanim')); sys.path.insert(0, os.path.join(HERE, '..', 'people')); sys.path.insert(0, os.path.join(HERE, '..', 'suit8'))
from p2paths import WT, SCRATCH  # noqa: E402
from ganim import Doc, qslerp  # noqa: E402
import pose_view as pv  # noqa: E402
import softrender as sr  # noqa: E402

FS = json.load(open(os.path.join(HERE, 'fight_script.json')))
BRUTE = json.load(open(os.path.join(HERE, '..', 'people', 'people.json')))['brute']
IMP = os.path.join(SCRATCH, 'ueimport')
MESHES = {'Fight_Hero': ('SK_Hero', None, (0.10, 0.50, 0.55)), 'Fight_Thug': ('SK_Street_Thug_Bat', 'StreetThug', None), 'Fight_Brute': ('SK_Street_Brute_Pipe', 'StreetBrute', None),
          'Fight_Hood': ('SK_Street_Hood_Pistol', 'StreetHood', None), 'Fight_Tee': ('SK_Street_Tee', 'StreetTee', None), 'Fight_Beard': ('SK_Street_Beard', 'StreetBeard', None),
          'Fight_Oxblood': ('SK_Street_Thug', 'StreetThug_Oxblood', None)}
_SRC = {}


def src(which):
    if which not in _SRC:
        f = {'hero': os.path.join(WT, 'public/assets/spiderman.glb'), 'thug': os.path.join(WT, 'public/assets/thug.glb'), 'fight': os.path.join(IMP, 'SK_Street_Fight.glb'),
             'walk': os.path.join(IMP, 'SK_Street_Walks.glb')}[which]
        _SRC[which] = Doc(f)
    return _SRC[which]


def dur(key):
    w, c = key.split(':'); return src(w).duration(c)


def load_all(doc):
    """All primitives of a GLB concatenated (hero: lenses + suit) -> P, N, UV, J, W, F, joints, ibm."""
    Ps, Ns, UVs, Js, Ws, Fs = [], [], [], [], [], []; off = 0
    for m in doc.j['meshes']:
        for pr in m['primitives']:
            at = pr['attributes']
            P = pv.acc(doc, at['POSITION']).astype(float); Ps.append(P); Ns.append(pv.acc(doc, at['NORMAL']).astype(float))
            UVs.append(pv.acc(doc, at['TEXCOORD_0']).astype(float)); Js.append(pv.acc(doc, at['JOINTS_0']).astype(int)); Ws.append(pv.acc(doc, at['WEIGHTS_0']).astype(float))
            Fs.append(pv.acc(doc, pr['indices']).reshape(-1, 3).astype(int) + off); off += len(P)
    sk = doc.j['skins'][0]
    ibm = pv.acc(doc, sk['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1).astype(float)
    return np.vstack(Ps), np.vstack(Ns), np.vstack(UVs), np.vstack(Js), np.vstack(Ws), np.vstack(Fs), sk['joints'], ibm


def tracks_for(key, target):
    w, c = key.split(':'); s = src(w); by = {n: i for i, n in enumerate(target.names)}; out = {}
    for node, chs in s.tracks(c).items():
        nm = s.names[node]
        if nm in by: out[by[nm]] = chs
    return out


def blend_locals(Ls, ws):
    """Weighted blend of local TRS dicts (translation / scale lerp, rotation hemisphere-aligned nlerp)."""
    tot = sum(ws); out = {}
    for n in Ls[0]:
        t = sum(w * L[n][0] for L, w in zip(Ls, ws)) / tot; s_ = sum(w * L[n][2] for L, w in zip(Ls, ws)) / tot
        q0 = Ls[0][n][1]; q = np.zeros(4)
        for L, w in zip(Ls, ws):
            qq = L[n][1]; q += w * (qq if qq @ q0 >= 0 else -qq)
        out[n] = (t, q / np.linalg.norm(q), s_)
    return out


def smooth(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


def layers_at(a, t, speed):
    """[(clip key, local time, weight)] of an actor at stage time t (the AnimInstance's maths)."""
    beats = []; tot = 0.0
    for b in FS['actors'][a]['beats']:
        if t < b['start']: continue
        L = dur(b['clip']); rate = max(0.05, b['rate']); pe = b['start'] + L / rate; he = 1e9 if b['hold'] < 0 else pe + b['hold']
        win = min(1.0, (t - b['start']) / b['blend_in']) if b['blend_in'] > 1e-3 else 1.0
        wout = 1.0 if t <= he else (max(0.0, 1 - (t - he) / b['blend_out']) if b['blend_out'] > 1e-3 else 0.0)
        w = b['weight'] * smooth(win) * smooth(wout)
        if w > 1e-3: beats.append([b['clip'], min(max((t - b['start']) * rate, 0), L), w]); tot += w
    if tot > 1: beats = [[c, tt, w / tot] for c, tt, w in beats]; tot = 1.0
    base_w = 1 - tot
    base = FS['actors'][a]['base']
    lay = list(beats)
    if base_w > 1e-3:
        mw = min(max((speed - 20.0) / (57.0 - 20.0), 0.0), 1.0)
        bw, bc = base.split(':'); L = dur(base)
        lay.append([base, t % L, base_w * (1 - mw)])
        if mw > 1e-3:
            lay.append(['walk:walkBrute' if a == 'Fight_Brute' else 'walk:walkStreet', (t * (speed / 114.0) / 1.067) % 1.0 * dur('walk:walkStreet'), base_w * mw])
    return [l for l in lay if l[2] > 1e-3]


def path_at(a, t):
    ks = FS['actors'][a]['path']
    if t <= ks[0]['t']: k = ks[0]; return np.array([k['x'], k['y']]), k['yaw']
    for k0, k1 in zip(ks, ks[1:]):
        if k0['t'] <= t <= k1['t']:
            u = (t - k0['t']) / max(1e-6, k1['t'] - k0['t']); dy = (k1['yaw'] - k0['yaw'] + 180) % 360 - 180
            return np.array([k0['x'] + (k1['x'] - k0['x']) * u, k0['y'] + (k1['y'] - k0['y']) * u]), k0['yaw'] + dy * u
    k = ks[-1]; return np.array([k['x'], k['y']]), k['yaw']


class Actor:
    def __init__(self, label):
        self.label = label; name, tex, col = MESHES[label]
        self.doc = Doc(os.path.join(IMP, name + '.glb'))
        self.P, self.N, self.UV, self.J, self.W, self.F, self.joints, self.ibm = load_all(self.doc)
        self.col = col
        self.tex = None
        if tex:
            f = os.path.join(SCRATCH, 'r3', 'people', 'Street%s_atlas.png' % tex.replace('Street', '', 1)) if not tex.endswith('Oxblood') else os.path.join(SCRATCH, 'r3', 'people', 'StreetThug_Oxblood_atlas.png')
            im = cv2.imread(f)[..., ::-1].astype(np.float32) / 255
            self.tex = cv2.resize(im, (2048, 2048), interpolation=cv2.INTER_AREA) ** 2.2
        self.xy = BRUTE['scale'] * BRUTE['girth'] if label == 'Fight_Brute' else 1.0
        self.zs = BRUTE['scale'] if label == 'Fight_Brute' else 1.0
        self._trk = {}

    def world_bones(self, t, names=('hips', 'spine2', 'head', 'hand.L', 'hand.R', 'foot.L', 'foot.R')):
        """World position (UE cm, left-handed like the engine's bone log) of a few joints at stage time t: the EXPECTED bone log of the script."""
        p, yaw = path_at(self.label, t); prev, _ = path_at(self.label, t - 1 / 30.0)
        speed = float(np.linalg.norm(p - prev)) * 30.0
        lay = layers_at(self.label, t, speed); Ls = []
        for key, tl, w in lay:
            ck = (key, self.label)
            if ck not in self._trk: self._trk[ck] = tracks_for(key, self.doc)
            Ls.append(self.doc.sample(self._trk[ck], tl))
        L = blend_locals(Ls, [w for _, _, w in lay]) if len(Ls) > 1 else Ls[0]
        Wm = self.doc.world(L); r = math.radians(yaw); f = np.array([math.cos(r), math.sin(r)]); l_ = np.array([math.sin(r), -math.cos(r)])
        out = {}
        for n in names:
            m = Wm[self.doc.idx[n]][:3, 3]
            xy = p + (f * m[2] + l_ * m[0]) * 100.0 * self.xy
            out[n] = (xy[0], xy[1], m[1] * 100.0 * self.zs)
        return p, yaw, out

    def world_mesh(self, t):
        p, yaw = path_at(self.label, t)
        prev, _ = path_at(self.label, t - 1 / 30.0)
        speed = float(np.linalg.norm(p - prev)) * 30.0
        lay = layers_at(self.label, t, speed)
        Ls = []
        for key, tl, w in lay:
            ck = (key, self.label)
            if ck not in self._trk: self._trk[ck] = tracks_for(key, self.doc)
            w_, c_ = key.split(':'); Ls.append(self.doc.sample(self._trk[ck], tl))
        L = blend_locals(Ls, [w for _, _, w in lay]) if len(Ls) > 1 else Ls[0]
        Wm = self.doc.world(L)
        Pp, Np = pv.skin(self.P, self.N, self.J, self.W, self.joints, self.ibm, Wm)
        # glTF (x left, y up, z forward, m) -> right-handed world (X forward, Y_rh = -Y_ue, Z up; cm): the actor faces UE yaw
        r = math.radians(yaw); f = np.array([math.cos(r), -math.sin(r)]); l_ = np.array([math.sin(r), math.cos(r)])
        pr = np.array([p[0], -p[1]])
        def tr(V, vec):
            xy = (f[None, :] * V[:, 2:3] + l_[None, :] * V[:, 0:1]) * (100.0 * self.xy) if not vec else (f[None, :] * V[:, 2:3] + l_[None, :] * V[:, 0:1])
            z = V[:, 1:2] * (100.0 * self.zs) if not vec else V[:, 1:2]
            return np.hstack([xy + (pr[None, :] if not vec else 0), z])
        return tr(Pp, False), tr(Np, True)


def bone_log(path, t1=24.5, fps=60):
    actors = [Actor(l) for l in MESHES]
    with open(path, 'w') as fo:
        fo.write('frame,time,label,x,y,yaw,bone,bx,by,bz\n')
        for k in range(int(t1 * fps)):
            t = k / fps
            for ac in actors:
                p, yaw, bs = ac.world_bones(t)
                for n, (bx, by, bz) in bs.items(): fo.write('%d,%.4f,%s,%.2f,%.2f,%.2f,%s,%.2f,%.2f,%.2f\n' % (k, t, ac.label, p[0], p[1], yaw, n, bx, by, bz))
    print('wrote', path)


def main():
    a = sys.argv[1:]
    if a[0] == '--bones': return bone_log(a[1])
    out, ts = a[0], [float(x) for x in a[1].split(',')]
    cam_name = a[a.index('--cam') + 1] if '--cam' in a else '34'
    W_, H_ = [int(x) for x in (a[a.index('--size') + 1] if '--size' in a else '1280x720').split('x')]
    cols = int(a[a.index('--cols') + 1]) if '--cols' in a else 2
    cams = {'wide': ((-30, -900, 500), 52.0), '34': ((-660, -335, 410), 48.0)}
    actors = [Actor(l) for l in MESHES]
    tiles = []
    for t in ts:
        if cam_name == 'orbit':
            az = math.radians(271 + 16 * max(0.0, t - 16.6)); ex, ey = 830 * math.cos(az), 830 * math.sin(az); eye_ue = (ex, ey, 95 + 280); fov = 48.0
        else:
            eye_ue, fov = cams[cam_name]
        eye = np.array([eye_ue[0], -eye_ue[1], eye_ue[2]], float); tgt = np.array([0, 0, 95.0])
        cam = sr.look_at(eye, tgt, up=(0, 0, 1))
        fov_v = 2 * math.degrees(math.atan(math.tan(math.radians(fov) / 2) * H_ / W_))
        img = np.zeros((H_, W_, 3), np.float32); img[:] = (0.62, 0.66, 0.72)
        zb_all = np.full((H_, W_), np.inf, np.float32)
        # ground grid
        for x in range(-600, 601, 100):
            for (p0, p1) in (((x, -600, 0), (x, 600, 0)), ((-600, x, 0), (600, x, 0))):
                s0 = sr.project(np.array([[p0[0], -p0[1], p0[2]]], float), cam, fov_v, W_, H_)[0]; s1 = sr.project(np.array([[p1[0], -p1[1], p1[2]]], float), cam, fov_v, W_, H_)[0]
                if s0[2] > 1 and s1[2] > 1: cv2.line(img, (int(s0[0]), int(s0[1])), (int(s1[0]), int(s1[1])), (0.56, 0.6, 0.66), 1)
        for ac in actors:
            P, N = ac.world_mesh(t)
            S = sr.project(P, cam, fov_v, W_, H_)
            fid, bc, zb = pv.raster_ids(S, ac.F, W_, H_)
            m = (fid >= 0) & (zb < zb_all)
            if not m.any(): continue
            sub = np.where(m, fid, -1)
            if ac.tex is not None:
                col, _ = pv.shade(P, N, ac.UV, ac.F, sub, bc, ac.tex, eye, light=(-0.45, -0.3, 0.75))
            else:
                ys, xs = np.nonzero(m); f = ac.F[fid[ys, xs]]
                Nn = N[f].mean(1); Nn /= np.linalg.norm(Nn, axis=1, keepdims=True) + 1e-9
                sun = np.array([-0.45, -0.3, 0.75]); sun /= np.linalg.norm(sun)
                shade = 0.35 + 0.65 * np.clip(Nn @ sun, 0, 1)
                col = np.full((H_, W_, 3), 0.0, np.float32); col[ys, xs] = np.array(ac.col)[None, :] * shade[:, None]; col = col ** (1 / 2.2)
            img[m] = col[m]; zb_all[m] = zb[m]
        im8 = (np.clip(img, 0, 1) * 255).astype(np.uint8)
        cv2.putText(im8, 't = %.2f s' % t, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        tiles.append(im8)
    rows = []
    for i in range(0, len(tiles), cols):
        row = tiles[i:i + cols]
        while len(row) < cols: row.append(np.zeros_like(tiles[0]))
        rows.append(np.concatenate(row, 1))
    cv2.imwrite(out, np.concatenate(rows, 0)[..., ::-1])
    print('wrote', out)


if __name__ == '__main__':
    main()
