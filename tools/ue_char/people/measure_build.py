#!/usr/bin/env python3
"""Body-size numbers of the fitted street people in the game's rest pose (metres), with the lineup actor scale applied.

Fan homage project; not official Marvel/Sony/Insomniac; no affiliation.
python3 tools/ue_char/people/measure_build.py [--brute-scale 1.08] [--brute-girth 1.22] [--out JSON]
Shoulder width = x extent of the vertices whose dominant joint is a shoulder / deltoid / upper-arm / spine2 joint, between
y = 1.36 and 1.47 (the deltoid band; hands and forearms hang lower). Chest depth = z extent of spine1/spine2 vertices at y 1.20-1.32.
"""
import sys, os, json, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); from p2paths import WT as _P2WT, scr as _scr  # noqa: E402
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'skinfit'))
import skinfit
SCR = _scr('r3')

def measure(path):
    j, b = skinfit.read_glb(path)
    p = j['meshes'][0]['primitives'][0]
    P = skinfit.accessor(j, b, p['attributes']['POSITION'])
    J = skinfit.accessor(j, b, p['attributes']['JOINTS_0']).astype(int)
    W = skinfit.accessor(j, b, p['attributes']['WEIGHTS_0'])
    names = [j['nodes'][i]['name'] for i in j['skins'][0]['joints']]
    dom = np.take_along_axis(J, W.argmax(1)[:, None], 1)[:, 0]
    dn = np.array([names[d] for d in dom])
    sh = np.isin(dn, ['shoulder.L', 'shoulder.R', 'deltoid.L', 'deltoid.R', 'upperArm.L', 'upperArm.R', 'spine2'])
    band = (P[:, 1] > 1.36) & (P[:, 1] < 1.47)
    sel = sh & band
    ch = np.isin(dn, ['spine1', 'spine2']) & (P[:, 1] > 1.20) & (P[:, 1] < 1.32)
    hips = np.isin(dn, ['hips', 'glute.L', 'glute.R', 'spine']) & (P[:, 1] > 0.9) & (P[:, 1] < 1.05)
    tor = np.isin(dn, ['spine', 'spine1', 'spine2']) & (P[:, 1] > 1.20) & (P[:, 1] < 1.34)
    return dict(torso_width=float(P[tor, 0].max() - P[tor, 0].min()), height=float(P[:, 1].max() - P[:, 1].min()), shoulder_width=float(P[sel, 0].max() - P[sel, 0].min()),
                chest_depth=float(P[ch, 2].max() - P[ch, 2].min()), hip_width=float(P[hips, 0].max() - P[hips, 0].min()), n_sel=int(sel.sum()))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); SZ = json.load(open(os.path.join(HERE, 'people.json')))['brute']
    ap.add_argument('--brute-scale', type=float, default=SZ['scale']); ap.add_argument('--brute-girth', type=float, default=SZ['girth'])
    ap.add_argument('--out'); a = ap.parse_args()
    t = measure(SCR + '/fit/StreetThug.glb'); r = measure(SCR + '/fit/StreetBrute.glb')
    out = {'thug_mesh': t, 'brute_mesh': r}
    for k in ('shoulder_width', 'torso_width', 'chest_depth', 'hip_width'):
        f = a.brute_scale * (a.brute_girth if k != 'height' else 1.0)
        out['brute_world_' + k] = r[k] * f
    out['brute_world_height'] = r['height'] * a.brute_scale
    out['thug_world_height'] = t['height']
    out['ratio_shoulder_width'] = out['brute_world_shoulder_width'] / t['shoulder_width']
    out['ratio_torso_width'] = out['brute_world_torso_width'] / t['torso_width']
    out['ratio_chest_depth'] = out['brute_world_chest_depth'] / t['chest_depth']
    out['ratio_hip_width'] = out['brute_world_hip_width'] / t['hip_width']
    out['ratio_height'] = out['brute_world_height'] / out['thug_world_height']
    print(json.dumps(out, indent=1))
    if a.out: json.dump(out, open(a.out, 'w'), indent=1)
