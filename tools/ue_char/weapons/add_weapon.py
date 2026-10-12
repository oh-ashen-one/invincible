#!/usr/bin/env python3
"""Put a weapon (tools/ue_char/weapons/make_weapons.py GLB) into a fitted enemy's right hand, rigidly skinned to hand.R.
Fan homage project; not official Marvel/Sony/Insomniac; no affiliation.
  python3 add_weapon.py FIT.glb WEAPON.glb OUT.glb
Grip frame from the bind-pose joints: handle axis = index1.R - pinky1.R (a fist holds a stick parallel to its knuckle line; +Y of the
weapon = thumb side; bat / pipe tilted -10 deg (round 10; was +58) so they rise from the fist instead of pointing at the opponent), forward = hand.R -> middle1.R, grip centre between wrist and knuckles, pushed toward the palm. The weapon's
materials become solid tiles in the reserved right 512 columns of the atlas strip (prepare_person.py paints them): same one
primitive / one material / one atlas; the weapon's vertices get JOINTS (hand.R) / WEIGHTS (1)."""
import sys, os, json, struct
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'skinfit'))
import skinfit  # noqa

TILES = ['wood', 'steel', 'polymer', 'grip', 'tape']          # order of the tiles in prepare_person.WEAPON_TILES
ATLAS, CONTENT_H, TILE_X0 = 4096, 3584, 3584
TEXTURED = True        # round 05: procedural weapon textures (weapon_textures.py) instead of one solid colour per material


def tile_uv(k):
    h = (ATLAS - CONTENT_H) / len(TILES)
    u = (TILE_X0 + 256) / ATLAS; v = (CONTENT_H + h * (k + 0.5)) / ATLAS
    return np.array([u, v])


def part_uv(P, k):
    """Round 05: real uvs into tile k (weapon_textures.py): u along the part's long axis, v = |angle around it| / pi (triangle wave: no seam)."""
    h = (ATLAS - CONTENT_H) / len(TILES)
    lo, hi = P.min(0), P.max(0)
    a = int(np.argmax(hi - lo)); b1, b2 = [i for i in range(3) if i != a]
    u = (P[:, a] - lo[a]) / max(hi[a] - lo[a], 1e-6)
    ang = np.arctan2(P[:, b2] - (lo[b2] + hi[b2]) / 2, P[:, b1] - (lo[b1] + hi[b1]) / 2)
    vt = np.abs(ang) / np.pi
    mx = 6.0; w = ATLAS - TILE_X0 - 2 * mx
    return np.stack([(TILE_X0 + mx + u * w) / ATLAS, (CONTENT_H + h * (k + 0.05 + 0.90 * vt)) / ATLAS], 1)


def weapon_mesh(path):
    j, b = skinfit.read_glb(path)
    P_, N_, UV_, F_ = [], [], [], []
    n = 0
    for nd in j['nodes']:
        if 'mesh' not in nd: continue
        M = skinfit.trs(nd)
        for p in j['meshes'][nd['mesh']]['primitives']:
            P = skinfit.accessor(j, b, p['attributes']['POSITION']) @ M[:3, :3].T + M[:3, 3]
            N = skinfit.accessor(j, b, p['attributes']['NORMAL']) @ M[:3, :3].T
            P = np.stack([P[:, 0], -P[:, 2], P[:, 1]], 1); N = np.stack([N[:, 0], -N[:, 2], N[:, 1]], 1)   # glTF -> Blender (weapon frame)
            F = skinfit.accessor(j, b, p['indices']).reshape(-1, 3).astype(np.int64)
            mn = j['materials'][p['material']]['name'].split('.')[0]
            P_.append(P); N_.append(N); UV_.append(part_uv(P, TILES.index(mn)) if TEXTURED else np.tile(tile_uv(TILES.index(mn)), (len(P), 1))); F_.append(F + n); n += len(P)
    return np.concatenate(P_), np.concatenate(N_), np.concatenate(UV_), np.concatenate(F_)


def main(fit, weapon, out):
    j, b = skinfit.read_glb(fit)
    b = bytearray(b)
    names = [nd.get('name') for nd in j['nodes']]
    joints = j['skins'][0]['joints']
    IBM = skinfit.accessor(j, bytes(b), j['skins'][0]['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
    W = {names[jn]: np.linalg.inv(IBM[k]) for k, jn in enumerate(joints)}
    pos = lambda n: W[n][:3, 3]
    y = pos('index1.R') - pos('pinky1.R'); y /= np.linalg.norm(y)
    z = pos('middle1.R') - pos('hand.R'); z -= y * (z @ y); z /= np.linalg.norm(z)
    x = np.cross(y, z)
    # long weapons hang down-back: the wrist deviates, so the handle axis is tilted from the knuckle line toward the fingers
    # round 10: -10 deg (was +58): the old tilt pointed the bat / pipe across the guard of the wielder AT the hero: the Brute's pipe passed through the hero's back, its grey elbow fitting sticking out
    # of his flank (critic r09 'untextured grey arm'; weapon_clip_check.py: 1.4 s of the 24 s fight for the pipe, 5.9 s for the bat, up to 16 cm deep).  Now the weapon rises beside the fist; swept 0 - 180 deg on the CPU: hero 0.05 s, own head / torso 0.1 - 0.15 s.
    tilt = np.radians(0.0 if 'pistol' in os.path.basename(weapon) else -10.0)
    y, z = y * np.cos(tilt) - z * np.sin(tilt), z * np.cos(tilt) + y * np.sin(tilt)
    palm = np.sign((pos('thumb2.R') - pos('hand.R')) @ x) * x          # toward the thumb / palm side
    c = pos('hand.R') + 0.62 * (pos('middle1.R') - pos('hand.R')) + 0.018 * palm
    R = np.stack([x, y, z], 1)
    Pw, Nw, UVw, Fw = weapon_mesh(weapon)
    Pw = Pw @ R.T + c; Nw = Nw @ R.T
    prim = j['meshes'][0]['primitives'][0]
    A = prim['attributes']
    old = {k: skinfit.accessor(j, bytes(b), A[k]) for k in ('POSITION', 'NORMAL', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0')}
    Fo = skinfit.accessor(j, bytes(b), prim['indices']).reshape(-1, 3).astype(np.int64)
    hk = joints.index(names.index('hand.R'))
    Jw = np.zeros((len(Pw), 4)); Jw[:, 0] = hk
    Ww = np.zeros((len(Pw), 4)); Ww[:, 0] = 1.0
    newv = {'POSITION': np.concatenate([old['POSITION'], Pw]), 'NORMAL': np.concatenate([old['NORMAL'], Nw]),
            'TEXCOORD_0': np.concatenate([old['TEXCOORD_0'], UVw]), 'JOINTS_0': np.concatenate([old['JOINTS_0'], Jw]),
            'WEIGHTS_0': np.concatenate([old['WEIGHTS_0'], Ww])}
    Fn = np.concatenate([Fo, Fw + len(old['POSITION'])])

    def append(arr, ctype, typ, minmax=False):
        while len(b) % 4: b.append(0)
        dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[ctype]
        raw = np.ascontiguousarray(arr, dtype=dt).tobytes()
        j['bufferViews'].append({'buffer': 0, 'byteOffset': len(b), 'byteLength': len(raw)}); b.extend(raw)
        acc = {'bufferView': len(j['bufferViews']) - 1, 'componentType': ctype, 'count': int(arr.shape[0]), 'type': typ}
        if minmax: acc['min'] = [float(v) for v in arr.min(0)]; acc['max'] = [float(v) for v in arr.max(0)]
        j['accessors'].append(acc); return len(j['accessors']) - 1
    jt = j['accessors'][A['JOINTS_0']]['componentType']
    A['POSITION'] = append(newv['POSITION'], 5126, 'VEC3', True); A['NORMAL'] = append(newv['NORMAL'], 5126, 'VEC3')
    A['TEXCOORD_0'] = append(newv['TEXCOORD_0'], 5126, 'VEC2'); A['JOINTS_0'] = append(newv['JOINTS_0'], jt, 'VEC4')
    A['WEIGHTS_0'] = append(newv['WEIGHTS_0'], 5126, 'VEC4'); prim['indices'] = append(Fn.reshape(-1), 5125, 'SCALAR')
    while len(b) % 4: b.append(0)
    j['buffers'][0]['byteLength'] = len(b)
    js = json.dumps(j, separators=(',', ':')).encode(); js += b' ' * ((4 - len(js) % 4) % 4)
    with open(out, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(b)))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(b), 0x004E4942)); f.write(bytes(b))
    print(json.dumps({'out': out, 'weapon_verts': len(Pw), 'weapon_tris': len(Fw), 'grip_centre': [round(float(v), 3) for v in c]}))


if __name__ == '__main__':
    main(*sys.argv[1:4])
