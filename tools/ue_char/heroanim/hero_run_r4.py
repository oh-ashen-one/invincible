"""Round-04 hero locomotion edit (P2 characters). Fan homage project; not an official Marvel, Sony or Insomniac game.

Edits public/assets/spiderman.glb IN PLACE (keeps every node, bone, mesh, texture and every other clip; clip names unchanged):
  run        : retimed 19/30 s -> 17/30 s (3.16 -> 3.53 steps/s at rate 1), forward lean added along the spine chain
               (world-space pitch, neck/head partly counter-rotated so the gaze stays down-range), arm swing amplified
               about the cycle mean (upper arm x ARM_K, forearm flex x FORE_K).
  runTakeoff : NEW clip (additive; nothing existing is renamed): 16/30 s grounded anticipation crouch before a jump. Starts from the
               retimed run's contact pose, gathers into the `jump` clip's first pose with the hips lowered so both feet stay on the
               ground (feet at the run's planted ankle height), deepens, and ends on exactly `jump` t=0 minus the hip drop, so the
               jump clip continues the motion when the character leaves the ground.
Run inside Blender headless or plain python3 (numpy only):
  blender -b -P tools/ue_char/heroanim/hero_run_r4.py -- [--src GLB] [--out GLB]      (default: in place)
Idempotent: refuses to run twice on an already-edited file (checks extras.p2_r4 on the run clip)."""
import sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ganim import Doc, qmul, qinv, qaxis, qslerp

ROOT = os.path.abspath(os.path.join(HERE, '../../..'))
SRC = os.path.join(ROOT, 'public/assets/spiderman.glb')
NEW_FRAMES = 17                 # run length in 1/30 s frames (UE imports clips on the 1/30 s grid only)
LEAN = {'spine': 7.0, 'spine1': 7.0, 'spine2': 6.0, 'neck': -5.0, 'head': -5.5}   # extra world pitch per bone (deg, + = forward)
ARM_K, FORE_K = 1.35, 1.15
TAKEOFF_FRAMES = 16             # 0.533 s authored; the lineup plays its first 0.25 s (15 frames at 60 fps) before lift-off
LAT = np.array([1.0, 0, 0])     # hero faces +Z, +X = left: pitch about +X moves the top forward


def args():
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    o = {'src': SRC, 'out': None}
    for i, k in enumerate(a):
        if k in ('--src', '--out'): o[k[2:]] = a[i + 1]
    o['out'] = o['out'] or o['src']
    return o


def sample_local(d, tr, t):
    return d.sample(tr, t)


def world_rot(d, L):
    """world rotation quaternion per node from local TRS dict (rotation part only; scales ~1)."""
    Wq = {}
    for i in d.order:
        q = L[i][1]
        Wq[i] = qmul(Wq[d.parent[i]], q) if i in d.parent else q
    return Wq


def lean_pose(d, L, lean):
    """add world pitch along the chain: bone b's world rotation becomes D_cum(b) * W_b; returns new local dict."""
    Wq = world_rot(d, L)
    cum = {}
    out = dict(L)
    chain = ['spine', 'spine1', 'spine2', 'neck', 'head']
    acc = 0.0
    for nm in chain:
        acc += lean.get(nm, 0.0); cum[d.idx[nm]] = acc
    newW = {}
    for i in d.order:
        p = d.parent.get(i)
        if i in cum:
            newW[i] = qmul(qaxis(LAT, np.radians(cum[i])), Wq[i])
        elif p is not None and p in newW:
            newW[i] = qmul(newW[p], L[i][1])
        else:
            newW[i] = Wq[i]
        if i in cum:
            pw = newW[p] if p in newW else Wq[p]
            q = qmul(qinv(pw), newW[i]); q /= np.linalg.norm(q)
            out[i] = (L[i][0], q, L[i][2])
    return out


def qlog(q):
    q = q / np.linalg.norm(q)
    if q[3] < 0: q = -q
    v = q[:3]; s = np.linalg.norm(v)
    if s < 1e-9: return np.zeros(3)
    return v / s * 2 * np.arctan2(s, q[3])


def qexp(r):
    a = np.linalg.norm(r)
    if a < 1e-9: return np.array([0, 0, 0, 1.0])
    return np.concatenate([r / a * np.sin(a / 2), [np.cos(a / 2)]])


def amplify(qs, k):
    """scale each key's rotation away from the cycle mean by k (log map about the mean)."""
    m = qs[0].copy()
    for _ in range(4):
        r = np.mean([qlog(qmul(qinv(m), q)) for q in qs], 0); m = qmul(m, qexp(r)); m /= np.linalg.norm(m)
    return np.array([qmul(m, qexp(k * qlog(qmul(qinv(m), q)))) for q in qs])


def pack(d, frames):
    """frames: list of local dicts -> {node: {path: array}} for every channel target of the clip."""
    data = {}
    for i in d.joints:
        data[i] = {'translation': np.array([f[i][0] for f in frames]), 'rotation': np.array([f[i][1] for f in frames]),
                   'scale': np.array([f[i][2] for f in frames])}
        r = data[i]['rotation']
        for k in range(1, len(r)):
            if np.dot(r[k], r[k - 1]) < 0: r[k] = -r[k]
    return data


def main():
    o = args()
    d = Doc(o['src'])
    run = d.anim('run')
    if (run.get('extras') or {}).get('p2_r4'):
        print('already edited (extras.p2_r4) - nothing to do'); return
    T0 = d.duration('run'); tr = d.tracks('run')
    T1 = NEW_FRAMES / 30.0
    times = np.arange(NEW_FRAMES + 1) / 30.0
    frames = [lean_pose(d, sample_local(d, tr, t * T0 / T1), LEAN) for t in times]
    frames[-1] = frames[0]                                  # exact loop
    for nm, k in (('upperArm.L', ARM_K), ('upperArm.R', ARM_K), ('forearm.L', FORE_K), ('forearm.R', FORE_K)):
        i = d.idx[nm]
        qs = amplify(np.array([f[i][1] for f in frames[:-1]]), k)
        for f, q in zip(frames[:-1], qs): f[i] = (f[i][0], q / np.linalg.norm(q), f[i][2])
        frames[-1] = dict(frames[-1]); frames[-1][i] = frames[0][i]
    data = pack(d, frames)
    # ---- runTakeoff: run contact pose -> grounded crouch (jump t=0 pose, hips lowered to put the feet on the ground) -> deeper
    jt = d.tracks('jump')
    J0 = d.sample(jt, 0.0)
    WJ = d.world(J0)
    foot_y = min(WJ[d.idx['foot.L']][1, 3], WJ[d.idx['foot.R']][1, 3])
    Wr = d.world(frames[0]); run_foot = min(Wr[d.idx['foot.L']][1, 3], Wr[d.idx['foot.R']][1, 3])
    drop = float(foot_y - run_foot)                       # lower the hips by this -> feet on the run's planted ankle height
    hips = d.idx['hips']
    crouch = dict(J0); crouch[hips] = (J0[hips][0] - np.array([0, drop, 0]), J0[hips][1], J0[hips][2])
    deeper = lean_pose(d, dict(crouch), {'spine': 2.0, 'spine1': 2.0})
    deeper[hips] = (crouch[hips][0] - np.array([0, 0.03, 0]), crouch[hips][1], crouch[hips][2])
    tk_times = np.arange(TAKEOFF_FRAMES + 1) / 30.0
    tk = []
    for t in tk_times:
        u = min(1.0, t / 0.12); u = u * u * (3 - 2 * u)                # gather in 0.12 s
        v = min(1.0, max(0.0, (t - 0.12) / 0.13)); v = v * v * (3 - 2 * v)   # sink further until 0.25 s
        w = min(1.0, max(0.0, (t - 0.30) / 0.23))                           # then rise back toward the jump's start pose (never reached in the lineup)
        f = {}
        for i in d.joints:
            a, b, c = frames[0][i], crouch[i], deeper[i]
            q = qslerp(qslerp(a[1], b[1], u), c[1], v * (1 - w)) if True else None
            q = qslerp(q, b[1], w) if w > 0 else q
            tpos = a[0] * (1 - u) + b[0] * u
            tpos = tpos * (1 - v * (1 - w)) + c[0] * (v * (1 - w))
            f[i] = (tpos, q / np.linalg.norm(q), a[2] * (1 - u) + b[2] * u)
        tk.append(f)
    d.set_clip('run', times, data)
    run = d.anim('run'); run['extras'] = {'p2_r4': {'frames': NEW_FRAMES, 'lean': LEAN, 'arm_k': ARM_K, 'fore_k': FORE_K}}
    # new clip: clone the run's channel layout
    tpl = json.loads(json.dumps(run)); tpl['name'] = 'runTakeoff'; tpl['extras'] = {'p2_r4': {'frames': TAKEOFF_FRAMES, 'hip_drop_m': drop}}
    d.j['animations'].append(tpl)
    d.set_clip('runTakeoff', tk_times, pack(d, tk))
    d.write(o['out'])
    print(json.dumps({'out': o['out'], 'run_s': T1, 'takeoff_s': TAKEOFF_FRAMES / 30.0, 'hip_drop_m': round(drop, 3),
                      'animations': len(d.j['animations']), 'bytes': os.path.getsize(o['out'])}))


if __name__ == '__main__':
    main()
