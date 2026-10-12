#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# hold.sh time-guard estimate (s, before est_scale) of a split capture item "splitA|splitB:<clip>:<tm>", a clip name (one full movie run), warm, default:
#   STARTUP_S engine start (r26: 2-4 min under load) + dumped frames x DUMP_S + rendered-only frames x RENDER_S (r26 measured; edit after a measurement)
import sys
DUMP_S, RENDER_S, STARTUP_S = 3.6, 0.15, 240
import os
_f = '/Users/midir/sm2-n1/_scratch/traversal/r26/dump_s'   # measured s per dumped frame (overrides DUMP_S)
if os.path.exists(_f): DUMP_S = float(open(_f).read().split()[0])
RENDER_S = min(RENDER_S, DUMP_S)
Q = {'a_swing_chain': 15.6, 'c_wallrun_perch': 10.5, 'f1_flow_backDouble': 9.0, 'f4_chain_flips': 13.3, 'w1_wallrun_tall_zip': 7.5, 'w2_wallrun_side_zip': 7.0,
     'r1_roofrun_zip': 9.5, 's1_high_swing': 6.0, 'x1_rmb_cancel_flip': 4.0, 'x2_rmb_cancel_wall': 5.0, 'm1_mouse_swing': 6.0, 'p1_pawn_run': 12.0}
it = sys.argv[1]; pre = 0.8
if it == 'warm': print(int(200 / 1.35)); sys.exit()
if it == 'default': print(int(300 / 1.35)); sys.exit()
if it in Q: dumped, rend = (Q[it] + pre) * 60, 0
else:
    m, c, tm = it.split(':'); tm = float(tm)
    if m == 'splitA': dumped, rend = (tm + 0.5 + pre) * 60, 0
    else: dumped, rend = (Q[c] - tm) * 60, (tm + pre) * 60
print(int((STARTUP_S + dumped * DUMP_S + rend * RENDER_S) / 1.35))   # hold.sh multiplies by est_scale (1.35)
