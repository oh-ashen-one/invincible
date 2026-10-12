#!/usr/bin/env python3
"""Round 10: measure the scripted fight against the round-10 target (critic r09) on a bone log.

Fan homage project; not an official Marvel, Sony or Insomniac game; no affiliation.

  python3 tools/ue_char/fight/r10_check.py <bones.csv> <out.json> [--script fight_script.json] [--windows 0.65:8.65,8.65:16.65,16.65:24.65] [--names wide,34,orbit]

<bones.csv> is either the engine's -WHBoneLog (the REAL game, 60 Hz) or the script's own prediction (`preview_cpu.py --bones`).  For every 8 s window it checks the critic's
round-09 gap, in the critic's words:
  * HIT REACTIONS: every scripted enemy reaction (fight:hit*, hero:hitReact, fight:down beats; contact = beat start - 0.02 s): max over [contact, contact + 0.2 s] of the 3-D
    displacement of the head and of spine2 relative to the contact instant, in stature (1.75 m x the actor's scale).  A reaction PASSES at >= 0.10 stature.  Target >= 4 passing
    reactions per window (knockdowns count as reactions here, and are also reported on their own).
  * KNOCKDOWNS: torso on the ground = spine2 < 45 cm and pelvis < 60 cm.  A run >= 1 s counts.  SIMULTANEOUS: the longest time two enemies are on the ground together; target >= 2
    knockdowns and >= 1 s of overlap in every window.
  * GET-UPS: distinct get-up clips (script beats fight:getUp*) that START inside the window; target >= 2 distinct.
  * GUARD HOLD: the longest time an enemy keeps ONE pose: standing, every joint (head, hands, feet, relative to the pelvis and the actor's yaw) within HOLD_CM of its position
    at the start of the run and the pelvis within HOLD_CM too.  Target <= 2.0 s for every enemy in every window (the critic: no enemy holds the same guard for > 2 s).
  * HERO FEET vs DOWNED BODIES: the closest a grounded enemy's bone comes to the hero's feet (the r09 critic: the hero's feet sink into the downed thug).
"""
import sys, os, json, csv
import numpy as np

HOLD_CM = 12.0
DOWN_SPINE, DOWN_HIPS = 45.0, 60.0
STATURE = 175.0
BONES = ('hips', 'spine2', 'head', 'hand.L', 'hand.R', 'foot.L', 'foot.R')
HERE = os.path.dirname(os.path.abspath(__file__))


def load(path):
    rows = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.setdefault(r['label'], {}).setdefault(r['bone'], []).append((float(r['time']), float(r['bx']), float(r['by']), float(r['bz']), float(r['x']), float(r['y']), float(r['yaw'])))
    return {l: {b: np.array(sorted(v)) for b, v in d.items()} for l, d in rows.items()}


def at(a, t):
    """nearest sample of a bone track at time t -> (x, y, z)"""
    i = int(np.argmin(np.abs(a[:, 0] - t))); return a[i, 1:4]


def main():
    a = sys.argv[1:]
    src, out = a[0], a[1]
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    wins = [tuple(float(x) for x in w.split(':')) for w in opt('--windows', '0.65:8.65,8.65:16.65,16.65:24.65').split(',')]
    names = opt('--names', 'wide,34,orbit').split(',')
    sc = json.load(open(opt('--script', os.path.join(HERE, 'fight_script.json'))))
    zscale = {l: 1.0 for l in sc['actors']}
    for l, d in sc['actors'].items():
        if l == 'Fight_Brute': zscale[l] = json.load(open(os.path.join(HERE, '..', 'people', 'people.json')))['brute']['scale']
    D = load(src)
    enemies = [l for l in D if l != 'Fight_Hero']
    t = D['Fight_Hero']['hips'][:, 0]
    res = {'source': src, 'windows': {}}
    # ---- per-enemy per-frame state
    down = {}; stand_pose = {}
    for l in enemies:
        b = D[l]
        sz, hz = b['spine2'][:, 3], b['hips'][:, 3]
        down[l] = (sz < DOWN_SPINE) & (hz < DOWN_HIPS)
    # ---- reactions
    reacts = []
    for l in enemies:
        for bt in sc['actors'][l]['beats']:
            c = bt['clip']
            if not (c.startswith('fight:hit') or c == 'hero:hitReact' or c == 'fight:down'): continue
            tc = bt['start'] - 0.02
            m = (t >= tc - 1e-6) & (t <= tc + 0.2 + 1e-6)
            if m.sum() < 3: continue
            ds = []
            for bone in ('head', 'spine2'):
                p = D[l][bone][m][:, 1:4]; ds.append(float(np.linalg.norm(p - p[0], axis=1).max()))
            stat = STATURE * zscale[l]
            reacts.append({'walker': l, 'clip': c, 'contact': round(tc, 3), 'head_cm': round(ds[0], 1), 'spine2_cm': round(ds[1], 1), 'stature_frac': round(max(ds) / stat, 3), 'pass': bool(max(ds) / stat >= 0.10)})
    # ---- knockdown runs
    runs = {}
    for l in enemies:
        r = []; s = None; d = down[l]
        for i, f in enumerate(d):
            if f and s is None: s = t[i]
            if (not f or i == len(d) - 1) and s is not None:
                r.append((float(s), float(t[i]))); s = None
        runs[l] = [x for x in r if x[1] - x[0] >= 0.5]
    # ---- guard hold
    def hold_runs(l):
        b = D[l]; n = len(t)
        yaw = np.radians(b['hips'][:, 6]); hip = b['hips'][:, 1:4]
        rel = []
        for bone in ('head', 'hand.L', 'hand.R', 'foot.L', 'foot.R'):
            v = b[bone][:, 1:4] - hip
            c, s_ = np.cos(-yaw), np.sin(-yaw)
            rel.append(np.stack([v[:, 0] * c - v[:, 1] * s_, v[:, 0] * s_ + v[:, 1] * c, v[:, 2]], 1))
        rel = np.stack(rel, 1)            # (n, 5, 3) in the actor's frame
        standing = ~down[l] & (b['spine2'][:, 3] > 70)
        res_ = []; i = 0
        while i < n:
            if not standing[i]: i += 1; continue
            j = i
            while j + 1 < n and standing[j + 1]:
                dr = np.abs(rel[j + 1] - rel[i]).max(); dh = np.linalg.norm(hip[j + 1, :2] - hip[i, :2])
                if dr > HOLD_CM or dh > HOLD_CM: break
                j += 1
            res_.append((float(t[i]), float(t[j])))
            i = j + 1 if j > i else i + 1
        return res_
    holds = {l: hold_runs(l) for l in enemies}
    # ---- per window
    hero_feet = np.stack([D['Fight_Hero']['foot.L'][:, 1:4], D['Fight_Hero']['foot.R'][:, 1:4]], 1)
    for (w0, w1), nm in zip(wins, names):
        inw = [r for r in reacts if w0 <= r['contact'] < w1]
        kd = []
        for l in enemies:
            for (s, e) in runs[l]:
                ov = min(e, w1) - max(s, w0)
                if ov >= 1.0: kd.append({'walker': l, 'ground': [round(s, 2), round(e, 2)], 'seconds_in_window': round(ov, 2)})
        grounded = np.sum([down[l] for l in enemies], axis=0)
        m = (t >= w0) & (t < w1)
        best = 0.0; cur = 0.0; dt = float(np.median(np.diff(t)))
        for g in grounded[m]:
            cur = cur + dt if g >= 2 else 0.0; best = max(best, cur)
        gets = set(); get_list = []
        for l in enemies:
            for bt in sc['actors'][l]['beats']:
                if bt['clip'].startswith('fight:getUp') and w0 <= bt['start'] < w1 - 0.9: gets.add(bt['clip']); get_list.append((l, bt['clip'], bt['start']))
        # guard hold inside the window (a run is clipped to the window)
        hh = {}
        for l in enemies:
            best_h = 0.0
            for (s, e) in holds[l]:
                ov = min(e, w1) - max(s, w0)
                best_h = max(best_h, ov)
            hh[l] = round(best_h, 2)
        # the hero's feet vs grounded enemies (any bone of a grounded enemy)
        mind = 1e9
        for l in enemies:
            idx = np.nonzero(down[l] & m)[0]
            for i in idx[::3]:
                for bone in BONES:
                    p = D[l][bone][i, 1:4]
                    for k in range(2): mind = min(mind, float(np.linalg.norm(p[:2] - hero_feet[i, k, :2])))
        res['windows'][nm] = {'window': [w0, w1],
                              'reactions_total': len(inw), 'reactions_pass_0.1_stature_in_0.2s': sum(r['pass'] for r in inw), 'reactions': inw,
                              'knockdowns_ge_1s': kd, 'knockdowns_count': len(kd), 'simultaneous_grounded_ge2_longest_s': round(best, 2),
                              'getups_distinct': sorted(gets), 'getups': get_list,
                              'guard_hold_longest_s_per_enemy': hh, 'guard_hold_max_s': max(hh.values()),
                              'hero_feet_to_grounded_body_min_cm': None if mind > 1e8 else round(mind, 1)}
    json.dump(res, open(out, 'w'), indent=1)
    ok_all = True
    for nm, w in res['windows'].items():
        npass = w['reactions_pass_0.1_stature_in_0.2s']
        flags = {'>=4 reactions': npass >= 4, '>=2 knockdowns': w['knockdowns_count'] >= 2, 'simultaneous>=1s': w['simultaneous_grounded_ge2_longest_s'] >= 1.0,
                 '>=2 distinct get-ups': len(w['getups_distinct']) >= 2, 'no hold>2s': w['guard_hold_max_s'] <= 2.0}
        ok_all &= all(flags.values())
        print('%-6s [%5.2f,%5.2f] reactions %d/%d pass | knockdowns %d | simult %.2f s | get-ups %s | guard hold max %.2f s %s | feet clearance %s cm  => %s' % (
            nm, w['window'][0], w['window'][1], npass, w['reactions_total'], w['knockdowns_count'], w['simultaneous_grounded_ge2_longest_s'], w['getups_distinct'],
            w['guard_hold_max_s'], {k.split('_')[1]: v for k, v in w['guard_hold_longest_s_per_enemy'].items() if v > 2.0} or '', w['hero_feet_to_grounded_body_min_cm'],
            'PASS' if all(flags.values()) else 'FAIL ' + ', '.join(k for k, v in flags.items() if not v)))
    print('ALL WINDOWS PASS' if ok_all else 'NOT ALL WINDOWS PASS')


if __name__ == '__main__':
    main()
