#!/usr/bin/env python3
"""Writes the final-loop clip scripts (docs/night1/traversal/scripts/final/*.json) and clips.json (clip -> [(script, quit_s)]).
Map frame: UE metres, x east, y south (north = -y), z up; the avenue x 250 (239..261), buildings east from x 266, west up to x 234.
s2_press_variety is 9 short case runs (one deliberately awkward press each), concatenated into one clip by run_clip.py.
usage: make_scripts.py"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[3] / 'docs/night1/traversal/scripts/final'
OUT.mkdir(parents=True, exist_ok=True)
CHAIN = {"autoChain": True, "releasePhase": 0.55, "gap": 0.3, "repressVz": 99.0, "trickEvery": 0, "skyEvery": 0, "skyTricks": 1, "skyRepressH": 30, "skyPhase": 0.8, "skyMax": 2.8}
clips = {}


def write(name, note, spawn, keys, quit_s, **extra):
    d = {"name": name, "note": note, "seed": 1234, "spawn": spawn, "keys": keys}
    d.update(extra)
    (OUT / (name + '.json')).write_text(json.dumps(d, indent=1))
    return name, quit_s


def air(pos, vel, yaw=-90.0, pitch=0.12):
    return {"pos": pos, "yaw": yaw, "camPitch": pitch, "vel": vel}


# s1 / s5: the r26 a_swing_chain rule (airborne swing chain north up the avenue; release on the rising front, re-press once falling at 8 m/s, every 3rd release a flow flip)
chain_keys = [{"t": 0.0, "move": [0, 1], "heading": -90, "swing": False}, dict({"t": 0.4}, **CHAIN)]
CHAIN_TUNE = "ArcLowMin=15,ArcDropShallow=8,ArcDropDeep=12,WallClearance=14,AltChain=0,AnchorAltDeg=8,AnchorElevMin=0.1,AnchorAheadMin=-2"   # swing bottoms >= 14 m over the street (above the street-tree canopy), the f4 altitude rule
clips['s1_swing_chain'] = [write('s1_swing_chain', 'a skilled player holding RMB: release on the rising front, re-press 0.3 s later (r26 a_swing_chain rule, gap 0.3 / repressVz 99), bottoms >= 14 m: 20 s', air([250, 560, 24], [0, -22, 0]), chain_keys, 20.0, tune=CHAIN_TUNE)]
clips['s5_night_swing'] = [write('s5_night_swing', 's1 inputs, night map', air([250, 560, 24], [0, -22, 0]), chain_keys, 20.0, tune=CHAIN_TUNE)]

# s4: releases without a trick, long air (re-press 1.6 s after each release)
f_keys = [{"t": 0.0, "move": [0, 1], "heading": -90, "swing": False}, {"t": 0.4, "autoChain": True, "releasePhase": 0.55, "gap": 1.6, "repressVz": -8.0, "trickEvery": 0, "skyEvery": 0, "skyTricks": 1, "skyRepressH": 30, "skyPhase": 0.8, "skyMax": 2.8}]
clips['s4_release_float'] = [write('s4_release_float', 'autoChain releases with no trick, re-press 1.6 s after each release (long air): 20 s', air([250, 240, 40], [0, -22, 0]), f_keys, 20.0)]

# s3: seven F presses, each its own 3.3 s case from the same airborne start (110 m up, 22 m/s north; the stick is set 0.1 s before the press at 0.4 s): forward / back / right / left / neutral / forward-right / back-left;
# a swing is pressed later (the catch out of the trick). (`heading` is not used: it overrides the stick.)
# round 05 (critic r04 gap 1): the pools lead with the doubles now; each case's FlipKStart picks a program whose catch window
# (CatchT x worst variant scale) lands by the press: fast tuck + a held pencil/throne/open shape + catch <= 0.25 s (F1/F3/F4/F8).
# round 06 (critic r05 gap 2): the picked programs are 720 deg now (2.0-2.4 s base), so each case's catch press sits just past
# its program's worst-case catch window (CatchT x the multi-rotation variant cap 1.06, +0.12 s), and the cases end ~1.6 s later.
# Picks: c1 frontSingle, c2 backSingle (pencil hold), c3 corkscrew, c4 barani, c5 frontPikeSwan (swan hold), c6 rudi, c7 fullTwist.
s3_ks = {'fwd': 3, 'back': 3, 'right': 2, 'left': 0, 'neutral': 7, 'fwd_right': 5, 'back_left': 1}
s3_press = {'fwd': 2.26, 'back': 1.58, 'right': 2.37, 'left': 2.30, 'neutral': 2.30, 'fwd_right': 2.43, 'back_left': 2.45}
s3c = []
for n, (nm, m) in enumerate([('fwd', [0, 1]), ('back', [0, -1]), ('right', [1, 0]), ('left', [-1, 0]), ('neutral', [0, 0]), ('fwd_right', [0.7, 0.7]), ('back_left', [-0.7, -0.7])], 1):
    ps = 0.4 + s3_press[nm]
    s3c.append(write('s3_c%d_%s' % (n, nm), 'F pressed 0.4 s in with the stick %s %s, swing %.2f s later' % (nm, m, s3_press[nm]), air([250, 200, 110], [0, -22, 6]),
                     [{"t": 0.0, "move": [0, 0], "swing": False}, {"t": 0.3, "move": m}, {"t": 0.4, "trick": True}, {"t": 0.5, "trick": False},
                      {"t": round(ps, 2), "swing": True}, {"t": round(ps + 1.1, 2), "swing": False}], round(ps + 1.6, 2), tune='FlipKStart=%d' % s3_ks[nm]))   # each case starts at another program of its stick pool
clips['s3b_flip_cases'] = s3c   # the round 00-02 s3 (7 separate cases) kept for progress pairs

# s3: ONE continuous chain: every release is a flow flip (F pressed with the release), the stick changes between flips (forward / forward-right / forward-left / back), the web catches each flip; 24 s
flow_moves = [(0.0, [0, 1]), (3.0, [0.7, 0.7]), (6.0, [0, 1]), (9.0, [-0.7, 0.7]), (12.0, [0, -0.8]), (15.0, [0, 1]), (18.0, [0.7, 0.7]), (21.0, [-0.7, 0.7])]
flow_keys = [dict({"t": t, "move": m}, **({"swing": False} if t == 0.0 else {})) for t, m in flow_moves] + [dict({"t": 0.4}, **dict(CHAIN, gap=0.3, trickEvery=1))]
flow_keys.sort(key=lambda k: k['t'])
clips['s3_flip_chain'] = [write('s3_flip_flow', 'one continuous chain: a flow flip on every release, stick changing between flips, 24 s', air([250, 560, 40], [0, -22, 6]), flow_keys, 24.0, tune=CHAIN_TUNE)]

clips['live_fix_clip'] = [('live_fix_clip', 15.0)]   # owner live fix clip (script written by the live-fix tooling, default tuning)

# s2: nine awkward-press cases (each 3-4 s after the cut)
cases = []
def case(n, name, note, spawn, keys, quit_s):
    cases.append(write('s2_c%d_%s' % (n, name), note, spawn, keys, quit_s))

# 1 roof jump: sprint off a 68 m roof edge toward the avenue (west), jump at the edge, press 0.2 s later
case(1, 'roof_jump', 'sprint west across the roof of E x266..291 z125..151 (h 68), jump at the edge, swing 0.2 s after the jump',
     {"pos": [287, 138, 69.2], "yaw": 180, "camPitch": 0.12, "vel": [0, 0, 0]},
     [{"t": 0.0, "move": [0, 1], "heading": 180, "sprint": True, "swing": False}, {"t": 1.9, "jump": True}, {"t": 2.05, "jump": False}, {"t": 2.25, "swing": True}, {"t": 4.2, "swing": False}], 5.0)
# 2 press mid-fall at speed (falling 17 m/s, 20 m/s forward)
case(2, 'midfall', 'free fall over the avenue (vz -14, 20 m/s north), swing pressed 0.5 s in',
     air([250, 150, 62], [0, -20, -14]),
     [{"t": 0.0, "move": [0, 1], "heading": -90, "swing": False}, {"t": 0.5, "swing": True}, {"t": 2.6, "swing": False}], 3.6)
# 3 press out of a wall run (east facade x=266), swing pressed 2.6 s in
case(3, 'wallrun', 'airborne into the east facade (x 266) of z 88..122 h 97, wall run, swing pressed 2.6 s in',
     air([250, 105, 30], [12, 0, 5], yaw=0),
     [{"t": 0.0, "move": [0, 1], "heading": 0, "sprint": True, "swing": False}, {"t": 0.6, "heading": False}, {"t": 2.6, "swing": True}, {"t": 4.3, "swing": False}], 5.2)
# 4 press during a flip (cancel)
case(4, 'flip_cancel', 'a backDouble flip requested at the start, swing pressed 0.9 s into the flip',
     air([250, 200, 50], [0, -22, 4]),
     [{"t": 0.0, "move": [0, 1], "heading": -90, "swing": False, "flip": "backDouble"}, {"t": 0.05, "trick": True}, {"t": 0.15, "trick": False}, {"t": 0.95, "swing": True}, {"t": 2.8, "swing": False}], 3.8)
# 5 rapid re-press right after a release
case(5, 'repress', 'swing 0.2..1.3 s, released, pressed again 0.15 s after the release, again released 2.4 s',
     air([250, 190, 30], [0, -22, 0]),
     [{"t": 0.0, "move": [0, 1], "heading": -90, "swing": False}, {"t": 0.2, "swing": True}, {"t": 1.3, "swing": False}, {"t": 1.45, "swing": True}, {"t": 2.9, "swing": False}], 3.8)
# 6 best anchor far to the side: hugging the east facade, stick to the right/left of travel
case(6, 'side_anchor', 'low and fast beside the east facade (x 262.5), stick held left (west) while pressing: the nearest face is the facade, the open anchors are across the avenue',
     air([262.5, 160, 22], [0, -20, 2]),
     [{"t": 0.0, "move": [-1, 0.2], "swing": False}, {"t": 0.3, "swing": True}, {"t": 2.2, "swing": False}], 3.2)
# 7 no anchor in range: far above the roofline
case(7, 'no_anchor', 'high above the roofline (z 330 m, 6 m/s north): nothing to attach to, swing pressed 0.3 s and 1.4 s in',
     air([250, 150, 330], [0, -6, 0]),
     [{"t": 0.0, "move": [0, 1], "heading": -90, "swing": False}, {"t": 0.3, "swing": True}, {"t": 0.7, "swing": False}, {"t": 1.4, "swing": True}, {"t": 1.8, "swing": False}], 3.0)
# 8 very close to a facade
case(8, 'close_facade', '1.5 m from the east facade (x 266), 18 m/s north, swing pressed 0.3 s in',
     air([264.5, 150, 35], [0, -18, 0]),
     [{"t": 0.0, "move": [0, 1], "heading": -90, "swing": False}, {"t": 0.3, "swing": True}, {"t": 2.2, "swing": False}], 3.2)
# 9 near street trees (east sidewalk x 262: trees at z 229, 218, 211, 106)
case(9, 'trees', 'low over the east sidewalk trees (x 262, z 229 / 218 / 211), swing pressed 0.2 s in',
     air([258, 244, 14], [0, -20, 0]),
     [{"t": 0.0, "move": [0, 1], "heading": -90, "swing": False}, {"t": 0.2, "swing": True}, {"t": 2.2, "swing": False}], 3.2)
clips['s2_press_variety'] = cases
clips['_q'] = {n: q + 0.5 for k, v in list(clips.items()) for n, q in v if k != '_q'}   # quit time (s after the cut, + the pre-roll the capture adds)
(OUT / 'clips.json').write_text(json.dumps(clips, indent=1))
print({k: [c[0] for c in v] for k, v in clips.items() if k != '_q'})
