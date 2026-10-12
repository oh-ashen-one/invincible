#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 16: the round-12 / round-14 skin-weight smoothing with a MOTION-AWARE four-influence truncation.

Critic r15 (image quality): "a 20 px stair-step groove jog at the Verdant armpit (~1300, 1310)", "jogs where groove cords meet panel borders (Ash and Cinder left chest)".
Found on the CPU (posed render of the prepped GLB in the idle clip + edge strain, `_scratch/characters/r16/dev/strain.py`): at the torso side under the armpit
(|x| 0.15 - 0.18, y 1.29 - 1.34, the front) the smoothed weights mix FIVE bones (spine2, spine1, shoulder, deltoid, upperArm) and the plain top-4 truncation of round 12
(`hero_weights_r12.top4`) drops spine1 on one vertex and upperArm (0.14 - 0.18) on its neighbour: in the idle pose the arm hangs down, so the two neighbours move ~ 0.15 x the
arm's motion apart - an edge strain of 2.6 (median 0.22) and a visible stair-step in every cord that crosses that row of edges (the yoke seam, the rib net, the chevron edge).
The fix: when a vertex has more than four influences, bones that move almost alike are MERGED pairwise in a fixed order (spine1 into spine2, spine into spine1, hips into
spine, glute into hips, neck into spine2; the arm bones do NOT move alike: never merged) until four remain - an arm bone is not dropped while a spine bone can merge - so neighbours make the same decision and deform alike.

  python3 tools/ue_char/suit8/hero_weights_r16.py <SK_Hero.glb>     (in place; replaces hero_weights_r14.py in the prep chain: prep_hero_r16.sh)
"""
import sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hero_weights_r12 as hw  # noqa: E402
import hero_weights_r14 as h14  # noqa: E402

# merge partners, in order of preference: a dropped bone goes to the first of these that the vertex keeps
PARTNERS = {
    'spine1': ('spine2', 'spine'), 'spine': ('spine1', 'hips'), 'hips': ('spine', 'glute'), 'spine2': ('spine1', 'neck'), 'neck': ('spine2', 'head'),
    'shoulder': ('deltoid', 'upperArm', 'spine2'), 'deltoid': ('upperArm', 'shoulder'), 'upperArm': ('deltoid', 'shoulder'), 'glute': ('hips', 'thigh'),
}
NAMES = None


MERGE_ORDER = (('spine1', 'spine2'), ('spine', 'spine1'), ('hips', 'spine'), ('glute', 'hips'), ('neck', 'spine2'))


def top4_merge(dense):
    """More than four influences: merge bones PAIRWISE in a fixed priority order (spine1 into spine2 first, ...: bones that move almost alike), so two neighbouring vertices
    make the same decision; only if no listed pair is present the smallest bone goes to the largest kept one.  Then the plain top 4 (now exact) and renormalise."""
    cur = dense.copy()
    if NAMES is not None:
        base = [n.split('.')[0] for n in NAMES]
        side = [n.split('.')[1] if '.' in n else '' for n in NAMES]
        idx = {(b, s): k for k, (b, s) in enumerate(zip(base, side))}
        for a_, b_ in MERGE_ORDER:
            many = (cur > 1e-6).sum(1) > 4
            if not many.any(): break
            for s in ('', 'L', 'R'):
                ka = idx.get((a_, s)); kb = idx.get((b_, s)) if idx.get((b_, s)) is not None else idx.get((b_, ''))
                if ka is None or kb is None: continue
                sel = many & (cur[:, ka] > 1e-6) & (cur[:, kb] > 1e-6)
                cur[sel, kb] += cur[sel, ka]; cur[sel, ka] = 0.0
    out = np.zeros_like(cur)
    order = np.argsort(-cur, axis=1)
    rows = np.arange(len(cur))[:, None]
    keep = order[:, :4]
    out[rows, keep] = cur[rows, keep]
    rest = cur.sum(1) - out.sum(1)
    out[np.arange(len(cur)), keep[:, 0]] += rest          # anything still beyond four goes to the largest kept bone
    out /= out.sum(1, keepdims=True) + 1e-12
    return out


def install(names):
    global NAMES
    NAMES = list(names)
    hw.top4 = top4_merge


def rewrite(path):
    import json, struct
    sys.path.insert(0, os.path.join(HERE, '..', '..', 'skinfit'))
    import skinfit
    d = bytearray(open(path, 'rb').read())
    jl = struct.unpack('<I', d[12:16])[0]
    j = json.loads(bytes(d[20:20 + jl]))
    names = [j['nodes'][i].get('name') for i in j['skins'][0]['joints']]
    install(names)
    h14.rewrite(path)
    print('hero_weights_r16: motion-aware top-4 truncation installed (%d joints)' % len(names))


if __name__ == '__main__':
    rewrite(sys.argv[1])
