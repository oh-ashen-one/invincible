#!/usr/bin/env python3
"""Owner live-fix verification scripts (docs/night1/traversal/scripts/final/live/*.json), default tuning (NO tune string):
 air_<H>_<stick>_<d>: airborne at H m, swing from 0.2 s, release at 1.3 s, ONE mid-air F at release + d (d = 0.3 / 0.8 / 1.2 s), stick fwd / back / right / neutral (set at the release, heading off)
 street_swing: standing on the avenue street, jump, hold RMB (3 s)
 roof_swing: standing on the roof of E x266..291 (h 68), run west, jump at the edge, hold RMB
usage: make_livefix.py"""
import json
from pathlib import Path
OUT = Path(__file__).resolve().parents[3] / 'docs/night1/traversal/scripts/final/live'
OUT.mkdir(parents=True, exist_ok=True)
names = []
def w(name, note, spawn, keys):
    (OUT / (name + '.json')).write_text(json.dumps({"name": name, "note": note, "seed": 1234, "spawn": spawn, "keys": keys}, indent=1)); names.append(name)
sticks = {'fwd': [0, 1], 'back': [0, -1], 'right': [1, 0], 'neutral': [0, 0]}
for H in (24, 40):
    for sn, m in sticks.items():
        for d in (0.3, 0.8, 1.2):
            t = 1.3 + d
            w('air_%d_%s_%d' % (H, sn, int(d * 10)), 'airborne at %d m, swing 0.2-1.3 s, F at release+%.1f s, stick %s' % (H, d, sn),
              {"pos": [250, 560, H], "yaw": -90.0, "camPitch": 0.12, "vel": [0, -22, 0]},
              [{"t": 0.0, "move": [0, 1], "heading": -90, "swing": False}, {"t": 0.2, "swing": True}, {"t": 1.3, "swing": False, "heading": False, "move": m},
               {"t": t - 0.05, "move": m}, {"t": t, "trick": True}, {"t": t + 0.1, "trick": False}])
w('street_swing', 'standing on the avenue street, jump at 0.3 s, hold RMB from 0.5 s', {"pos": [250, 540, 1.2], "yaw": -90.0, "camPitch": 0.12, "vel": [0, 0, 0]},
  [{"t": 0.0, "move": [0, 1], "heading": -90, "swing": False}, {"t": 0.3, "jump": True}, {"t": 0.45, "jump": False}, {"t": 0.5, "swing": True}, {"t": 3.5, "swing": False}])
w('roof_swing', 'roof run west, jump at the edge, hold RMB', {"pos": [287, 138, 69.2], "yaw": 180, "camPitch": 0.12, "vel": [0, 0, 0]},
  [{"t": 0.0, "move": [0, 1], "heading": 180, "sprint": True, "swing": False}, {"t": 1.9, "jump": True}, {"t": 2.05, "jump": False}, {"t": 2.2, "swing": True}, {"t": 4.5, "swing": False}])
(OUT / 'index.json').write_text(json.dumps(names))
print(len(names), 'scripts')
