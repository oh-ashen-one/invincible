#!/usr/bin/env python3
"""Upright street-thug walk and heavy brute walk, derived from the hero's `walk` clip (numpy, no Blender).

Fan homage project; not official Marvel/Sony/Insomniac; no affiliation.

The hero `walk` is a stalking, bent-knee cycle (knee flexion 35-64 deg throughout, hips 6-9 cm below standing height). For an
upright walk the hips are raised and both legs are re-solved with analytic two-bone IK so every foot keeps its ORIGINAL world position
and orientation (no foot sliding, same stride). The brute adds a weight shift over the stance foot (hip sway plus opposite torso
roll) and a slower cadence.

usage: python3 tools/ue_char/people/make_walk.py FIT.glb OUT.glb
  FIT.glb : any skinfit output (its skeleton nodes are the game's); the animations are appended to a copy of it.
Clips written: walkStreet (thug), walkBrute (brute). Same 58 joints, same node names, key times 1/30 s (brute stretched).
"""
import sys, os, json, struct, math
import numpy as np
from scipy.spatial.transform import Rotation as Rot

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'skinfit'))
import skinfit  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '../../..'))
HERO = os.path.join(ROOT, 'public/assets/spiderman.glb')


def mat(t, q):
    M = np.eye(4)
    M[:3, :3] = Rot.from_quat(q).as_matrix()
    M[:3, 3] = t
    return M


def arc(d0, d1):
    d0 = d0 / np.linalg.norm(d0); d1 = d1 / np.linalg.norm(d1)
    c = np.cross(d0, d1); s = np.linalg.norm(c); dt = float(np.dot(d0, d1))
    if s < 1e-9:
        return np.eye(3) if dt > 0 else Rot.from_rotvec(np.pi * np.array([0, 0, 1.0])).as_matrix()
    return Rot.from_rotvec(c / s * math.atan2(s, dt)).as_matrix()


def solve_two_bone(H, A, K0, L1, L2):
    """Knee position for hip H, ankle A (clamped to reach), pole taken from the original knee K0."""
    d = A - H
    dist = np.linalg.norm(d)
    dist = min(dist, (L1 + L2) * 0.9995)
    dh = d / np.linalg.norm(d)
    a = (L1 * L1 - L2 * L2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(L1 * L1 - a * a, 0.0))
    pole = (K0 - H) - np.dot(K0 - H, dh) * dh
    n = np.linalg.norm(pole)
    pole = pole / n if n > 1e-6 else np.array([0, 0, 1.0])
    return H + dh * a + pole * h, H + dh * dist


def build(game, an, mode):
    j, b = game.j, game.b
    nodes = j['nodes']
    name2i = {nodes[i]['name']: i for i in game.joints}
    chan = {}
    for c in an['channels']:
        i = c['target']['node']
        if i in name2i.values():
            s = an['samplers'][c['sampler']]
            chan[(i, c['target']['path'])] = (skinfit.accessor(j, b, s['input'])[:, 0], skinfit.accessor(j, b, s['output']))
    times = chan[(name2i['hips'], 'rotation')][0]
    n = len(times)

    def val(i, path, k):
        t, v = chan[(i, path)]
        return v[min(k, len(v) - 1)] if len(v) != n else v[k]

    hips = name2i['hips']
    par = game.parent
    rot = {i: np.array([val(i, 'rotation', k) for k in range(n)]) for i in game.joints}            # (n, 4) xyzw
    tra = {i: np.array([val(i, 'translation', k) for k in range(n)]) for i in game.joints}
    out_rot = {i: rot[i].copy() for i in game.joints}
    out_tra = {i: tra[i].copy() for i in game.joints}
    P = {'street': dict(raise_=0.055, sway=0.012, roll=0.0, stretch=1.0),
         'brute': dict(raise_=0.045, sway=0.032, roll=3.0, stretch=1.125)}[mode]   # 32 source frames -> 36 (1.2 s): UE imports on the 1/30 s grid only
    # phase: left foot planted around key t_L (lowest left ankle), so weight goes over the left foot then the right
    def glob_all(k, R_, T_):
        G = {}
        for i in game.order:
            M = (G[par[i]] if par.get(i) in G else game.base[i]) @ mat(T_[i][k], R_[i][k])
            G[i] = M
        return G
    G0 = [glob_all(k, rot, tra) for k in range(n)]
    zL = np.array([G0[k][name2i['foot.L']][1, 3] for k in range(n)])
    tL = int(np.argmin(zL[: n - 1]))
    for k in range(n):
        ph = 2 * math.pi * (k - tL) / (n - 1)
        sway = P['sway'] * math.cos(ph)                # +X = character's left: over the left foot at mid stance
        # 1) hips: raise (and sway); local translation of hips is expressed in its parent's frame (identity above the joints)
        Ph = par.get(hips)
        Gp = G0[k][Ph] if Ph in G0[k] else game.base[hips]
        dW = np.array([sway, P['raise_'], 0.0])
        out_tra[hips][k] = tra[hips][k] + np.linalg.inv(Gp)[:3, :3] @ dW
        # torso roll against the sway (spine local rotation about the parent's forward axis)
        if P['roll']:
            sp = name2i['spine']
            th = -math.radians(P['roll']) * math.cos(ph)
            Rz = Rot.from_rotvec([0, 0, th]).as_matrix()
            out_rot[sp][k] = Rot.from_matrix(Rz @ Rot.from_quat(rot[sp][k]).as_matrix()).as_quat()
        # 2) legs: two-bone IK to the ORIGINAL ankle positions / orientations
        Gn = {}
        for i in game.order:                                # globals with the new hips (before the leg solve)
            M = (Gn[par[i]] if par.get(i) in Gn else game.base[i]) @ mat(out_tra[i][k], out_rot[i][k])
            Gn[i] = M
        for side in ('L', 'R'):
            th_, sh_, ft_ = name2i['thigh.' + side], name2i['shin.' + side], name2i['foot.' + side]
            H = Gn[th_][:3, 3]
            A = G0[k][ft_][:3, 3]
            K0 = G0[k][sh_][:3, 3]
            L1 = np.linalg.norm(tra[sh_][k]); L2 = np.linalg.norm(tra[ft_][k])
            K, A2 = solve_two_bone(H, A, K0, L1, L2)
            R_th = Gn[th_][:3, :3]
            a1 = tra[sh_][k] / L1
            R_th_new = arc(R_th @ a1, (K - H) / L1) @ R_th
            Rp = Gn[par[th_]][:3, :3]
            out_rot[th_][k] = Rot.from_matrix(Rp.T @ R_th_new).as_quat()
            R_sh = R_th_new @ Rot.from_quat(rot[sh_][k]).as_matrix()
            a2 = tra[ft_][k] / L2
            R_sh_new = arc(R_sh @ a2, (A2 - K) / L2) @ R_sh
            out_rot[sh_][k] = Rot.from_matrix(R_th_new.T @ R_sh_new).as_quat()
            R_ft_orig = G0[k][ft_][:3, :3]
            out_rot[ft_][k] = Rot.from_matrix(R_sh_new.T @ R_ft_orig).as_quat()
    # keep quaternion signs continuous
    for i in game.joints:
        q = out_rot[i]
        for k in range(1, n):
            if np.dot(q[k], q[k - 1]) < 0:
                q[k] = -q[k]
    # resample to the 1/30 s grid (slerp / lerp) so the stretched clip has whole frames
    if P['stretch'] != 1.0:
        nk = int(round((n - 1) * P['stretch']))
        u = np.arange(nk + 1) / P['stretch']                  # fractional source key for every new key
        u = np.minimum(u, n - 1)
        k0 = np.floor(u).astype(int); k1 = np.minimum(k0 + 1, n - 1); f = (u - k0)[:, None]
        for i in game.joints:
            q0, q1 = out_rot[i][k0], out_rot[i][k1]
            q1 = np.where(((q0 * q1).sum(1) < 0)[:, None], -q1, q1)
            q = q0 * (1 - f) + q1 * f
            out_rot[i] = q / np.linalg.norm(q, axis=1, keepdims=True)
            out_tra[i] = out_tra[i][k0] * (1 - f) + out_tra[i][k1] * f
        times = np.arange(nk + 1) / 30.0
        return times, out_rot, out_tra, name2i, P
    return times, out_rot, out_tra, name2i, P


def gait_stats(game, name2i, rot, tra):
    """Knee flexion (deg, 0 = straight), hips height, ankle world positions per key (from FK of the given local tracks)."""
    n = len(rot[name2i['hips']])
    par = game.parent
    kn, hh, ank = [], [], []
    for k in range(n):
        G = {}
        for i in game.order:
            G[i] = (G[par[i]] if par.get(i) in G else game.base[i]) @ mat(tra[i][k], rot[i][k])
        fl = []
        for side in ('L', 'R'):
            H, K, A = (G[name2i[b + side]][:3, 3] for b in ('thigh.', 'shin.', 'foot.'))
            v1, v2 = (H - K) / np.linalg.norm(H - K), (A - K) / np.linalg.norm(A - K)
            fl.append(180.0 - math.degrees(math.acos(np.clip(np.dot(v1, v2), -1, 1))))
        kn.append(fl); hh.append(G[name2i['hips']][1, 3]); ank.append([G[name2i['foot.L']][:3, 3], G[name2i['foot.R']][:3, 3]])
    kn = np.array(kn); ank = np.array(ank)
    return dict(knee_flexion_mean=float(kn.mean()), knee_flexion_min=float(kn.min()), knee_flexion_max=float(kn.max()),
                stance_knee_flexion_mean=float(np.minimum(kn[:, 0], kn[:, 1]).mean()), hips_height_mean=float(np.mean(hh)),
                hips_height_min=float(np.min(hh)), hips_height_max=float(np.max(hh))), ank


def append_animations(glb_in, glb_out, clips):
    """clips: [(name, times, {node_name: (rot (n,4), tra (n,3))})] -> appended to a copy of the skinfit GLB (nodes matched by name)."""
    j, b = skinfit.read_glb(glb_in)
    data = bytearray(b)
    node_by_name = {n.get('name'): i for i, n in enumerate(j['nodes'])}
    j.setdefault('animations', [])
    def add(arr, typ, minmax=False):
        raw = np.ascontiguousarray(arr.astype(np.float32)).tobytes()
        while len(data) % 4: data.append(0)
        j['bufferViews'].append({'buffer': 0, 'byteOffset': len(data), 'byteLength': len(raw)})
        data.extend(raw)
        a = {'bufferView': len(j['bufferViews']) - 1, 'componentType': 5126, 'count': int(arr.shape[0]), 'type': typ}
        if minmax:
            a['min'] = [float(arr.min())]; a['max'] = [float(arr.max())]
        j['accessors'].append(a)
        return len(j['accessors']) - 1
    for name, times, chans in clips:
        samplers, channels = [], []
        tin = add(times.reshape(-1, 1), 'SCALAR', True)
        for nm, (rq, tr) in chans.items():
            ni = node_by_name[nm]
            samplers.append({'input': tin, 'output': add(rq, 'VEC4'), 'interpolation': 'LINEAR'})
            channels.append({'sampler': len(samplers) - 1, 'target': {'node': ni, 'path': 'rotation'}})
            samplers.append({'input': tin, 'output': add(tr, 'VEC3'), 'interpolation': 'LINEAR'})
            channels.append({'sampler': len(samplers) - 1, 'target': {'node': ni, 'path': 'translation'}})
        j['animations'].append({'name': name, 'channels': channels, 'samplers': samplers})
    while len(data) % 4: data.append(0)
    j['buffers'][0]['byteLength'] = len(data)
    js = json.dumps(j, separators=(',', ':')).encode()
    while len(js) % 4: js += b' '
    total = 12 + 8 + len(js) + 8 + len(data)
    with open(glb_out, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, total))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(data), 0x004E4942)); f.write(bytes(data))


def main():
    fit, out = sys.argv[1], sys.argv[2]
    game = skinfit.Game(HERO)
    an = next(a for a in game.j['animations'] if a['name'] == 'walk')
    clips = []
    report = {}
    # the original clip, for comparison
    name2i0 = {game.j['nodes'][i]['name']: i for i in game.joints}
    chn = {}
    for c in an['channels']:
        i = c['target']['node']
        if i in game.joints:
            chn[(i, c['target']['path'])] = skinfit.accessor(game.j, game.b, an['samplers'][c['sampler']]['output'])
    n0 = len(chn[(name2i0['hips'], 'rotation')])
    rot0 = {i: np.array([chn[(i, 'rotation')][min(k, len(chn[(i, 'rotation')]) - 1)] for k in range(n0)]) for i in game.joints}
    tra0 = {i: np.array([chn[(i, 'translation')][min(k, len(chn[(i, 'translation')]) - 1)] for k in range(n0)]) for i in game.joints}
    report['hero_walk'], ank0 = gait_stats(game, name2i0, rot0, tra0)
    for mode, name in (('street', 'walkStreet'), ('brute', 'walkBrute')):
        times, rot, tra, name2i, P = build(game, an, mode)
        ch = {game.j['nodes'][i]['name']: (rot[i], tra[i]) for i in game.joints}
        clips.append((name, times, ch))
        report[name], ankN = gait_stats(game, name2i, rot, tra)
        if len(ankN) == len(ank0):
            report[name]['max_ankle_error_vs_hero_walk_m'] = float(np.linalg.norm(ankN - ank0, axis=-1).max())
        report[name]['keys'] = len(times); report[name]['duration_s'] = float(times[-1])
        print(name, 'keys', len(times), 'duration %.3f s' % times[-1], P)
    append_animations(fit, out, clips)
    json.dump(report, open(os.path.splitext(out)[0] + '_report.json', 'w'), indent=1)
    print(json.dumps(report, indent=1))
    print('wrote', out)


if __name__ == '__main__':
    main()
