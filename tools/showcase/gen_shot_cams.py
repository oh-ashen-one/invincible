#!/usr/bin/env python3
"""Matched-camera list for play.py --shot-cams (game -WHShotCam): one entry per shot of the author's reference captures (~/sm2-n1/_scratch/night/ref/ref_shots.json).
Each entry: t (game s), name, ue_pos_cm / ue_target_cm (UE cm = (x, z, y) * 100 from browser metres; the target is the reference camera's point 20 m along its forward),
fov = UE HORIZONTAL fov in degrees (the browser fov is vertical: hfov = 2 atan(tan(vfov / 2) x aspect)), fov_v_browser, hero_visible (shots.js compositions show the player, free cameras
hide it, as in the reference captures; the UE hero stays at its own spawn, it is not moved to the browser's player position).
usage: gen_shot_cams.py [--ref ref_shots.json] [--out file.json] [--t0 15] [--step 4]"""
import argparse
import json
import math
from pathlib import Path

REF = Path.home() / 'sm2-n1/_scratch/night/ref/ref_shots.json'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', default=str(REF))
    ap.add_argument('--out', default=str(Path.home() / 'sm2-n1/_scratch/night/ref/shot_cams.json'))
    ap.add_argument('--t0', type=float, default=15.0)
    ap.add_argument('--step', type=float, default=4.0)
    a = ap.parse_args()
    shots = json.loads(Path(a.ref).read_text())['shots']
    ue = lambda v: [round(v[0] * 100, 2), round(v[2] * 100, 2), round(v[1] * 100, 2)]
    players_f = Path(a.ref).with_name('ref_players.json')   # tools/night/ref_players.mjs
    players = json.loads(players_f.read_text()) if players_f.is_file() else {}
    out = []
    for i, s in enumerate(shots):
        c = s['camera']
        vf = c['fov']
        hf = math.degrees(2 * math.atan(math.tan(math.radians(vf) / 2) * c.get('aspect', 16 / 9)))
        out.append({'t': a.t0 + i * a.step, 'name': s['name'], 'ue_pos_cm': ue(c['pos']), 'ue_target_cm': ue(c['target_fwd20']), 'fov': round(hf, 3), 'fov_v_browser': vf,
                    'hero_visible': s.get('kind') == 'shots.js composition', 'ref': s['file']})
        p = players.get(s['name'])
        if p:   # the author's player position (UE axes: X = x, Y = z, Z = feet height) and heading; the ref pose (wall / swing / climb) cannot be reproduced, the hero is held there falling / standing
            out[-1]['hero_pos_m'] = [p['pos'][0], p['pos'][2], p['pos'][1]]
            out[-1]['hero_yaw_deg'] = round(math.degrees(math.atan2(p['dir'][2], p['dir'][0])), 2)
            out[-1]['hero_ref_mode'] = p.get('mode')
    Path(a.out).write_text(json.dumps(out, indent=1))
    print('wrote', a.out, len(out), 'shots')


if __name__ == '__main__':
    main()
