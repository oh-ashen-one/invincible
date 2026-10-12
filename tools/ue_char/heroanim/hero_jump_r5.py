"""Round-05 hero running leap (P2 characters). Fan homage project; not an official Marvel, Sony or Insomniac game.

Critic r04 (hero_run_jump_side f96 -> f104, 0.13 s): 'the torso snaps from about 30 deg to vertical into a straight-legged, arm-up pose (the
`jump` clip) and both jumps are identical'.  Adds two NEW clips (nothing existing is edited or renamed):
  runLeap   0.73 s: starts on exactly the runTakeoff crouch (t = 0.25 s), stretches into an open stride (front knee driven up, rear leg
            trailing, the sprint clip's 0.12 s pose), tucks at the apex (airApex pose leaned forward), and reaches for the landing with the
            run's contact pose (front leg out, torso ~26 deg forward), held until the actor lands.  The torso never returns to vertical.
  runLeapB  the same leap mirrored left/right (the other leg leads): the lineup alternates them, so consecutive jumps differ.
Run with plain python3 (numpy only):  python3 tools/ue_char/heroanim/hero_jump_r5.py [--src GLB] [--out GLB]     (default: in place)
Idempotent: refuses to run twice (extras.p2_r5 on runLeap)."""
import sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ganim import Doc, qmul, qinv, qslerp
from hero_run_r4 import lean_pose, pack

ROOT = os.path.abspath(os.path.join(HERE, '../../..'))
SRC = os.path.join(ROOT, 'public/assets/spiderman.glb')
FRAMES = 22                                   # 0.733 s on the 1/30 s grid
KEYS = [0.0, 0.13, 0.34, 0.60, FRAMES / 30.0]  # crouch, open stride, tuck, reach, hold


def args():
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    o = {'src': SRC, 'out': None}
    for i, k in enumerate(a):
        if k in ('--src', '--out'): o[k[2:]] = a[i + 1]
    o['out'] = o['out'] or o['src']
    return o


def mirror(d, L):
    """Mirror a local-pose dict across the sagittal plane (x -> -x): swap .L / .R bones, q -> (x, -y, -z, w), local x translation flipped.
    Valid because the hero skeleton's left and right rest rotations / offsets are exact mirrors (checked on upperArm, thigh, shin, foot ...)."""
    out = {}
    for i in L:
        nm = d.names[i]
        j = i
        if nm.endswith('.L') and nm[:-2] + '.R' in d.idx: j = d.idx[nm[:-2] + '.R']
        elif nm.endswith('.R') and nm[:-2] + '.L' in d.idx: j = d.idx[nm[:-2] + '.L']
        tj, qj, sj = L[j]
        mq = np.array([qj[0], -qj[1], -qj[2], qj[3]])
        out[i] = (np.array([-tj[0], tj[1], tj[2]]), mq / np.linalg.norm(mq), L[i][2])
    return out


def blend(d, A, B, u):
    out = {}
    for i in A:
        out[i] = (A[i][0] * (1 - u) + B[i][0] * u, qslerp(A[i][1], B[i][1], u), A[i][2] * (1 - u) + B[i][2] * u)
    return out


def main():
    o = args()
    d = Doc(o['src'])
    if 'runLeap' in [a['name'] for a in d.j['animations']]:
        print('runLeap already present - nothing to do'); return
    S = lambda clip, t: d.sample(d.tracks(clip), t)
    K0 = S('runTakeoff', 0.25)
    K1 = S('sprint', 0.12)
    K2 = lean_pose(d, S('airApex', 0.10), {'spine': 5.0, 'spine1': 5.0, 'spine2': 5.0, 'neck': -3.0, 'head': -4.0})
    K3 = lean_pose(d, S('run', 0.0), {'spine': 1.0, 'spine1': 1.0, 'spine2': 1.0})
    hips = d.idx['hips']
    # keep the hips at a believable height: the tuck sits ~6 cm above the stride, the reach ~4 cm above the run contact height
    for K, dy in ((K2, 0.02),): K[hips] = (K[hips][0] + np.array([0, dy, 0]), K[hips][1], K[hips][2])
    variants = {'runLeap': [K0, K1, K2, K3, K3], 'runLeapB': [K0, mirror(d, K1), mirror(d, K2), mirror(d, K3), mirror(d, K3)]}
    times = np.arange(FRAMES + 1) / 30.0
    run = d.anim('run')
    for name, keys in variants.items():
        frames = []
        for t in times:
            k = max(0, min(len(KEYS) - 2, int(np.searchsorted(KEYS, t, side='right') - 1)))
            u = 0.0 if KEYS[k + 1] == KEYS[k] else min(1.0, max(0.0, (t - KEYS[k]) / (KEYS[k + 1] - KEYS[k])))
            u = u * u * (3 - 2 * u)
            frames.append(blend(d, keys[k], keys[k + 1], u))
        tpl = json.loads(json.dumps(run)); tpl['name'] = name
        tpl['extras'] = {'p2_r5': {'frames': FRAMES, 'keys_s': KEYS}}
        d.j['animations'].append(tpl)
        d.set_clip(name, times, pack(d, frames))
    d.write(o['out'])
    print(json.dumps({'out': o['out'], 'clips': list(variants), 'len_s': FRAMES / 30.0, 'animations': len(d.j['animations']), 'bytes': os.path.getsize(o['out'])}))


if __name__ == '__main__':
    main()
