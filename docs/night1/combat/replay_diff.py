#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat: compare the event logs of two runs of the same fight (record run vs frozen replay, or nullrhi vs rendered movie).
#   replay_diff.py <run_a_dir> <run_b_dir> [tolerance_s=0.02]
import json, os, sys
a, b = sys.argv[1:3]; tol = float(sys.argv[3]) if len(sys.argv) > 3 else 0.02
def load(d):
    return [json.loads(l) for l in open(os.path.join(d, 'fight_events.jsonl')) if l.strip()]
A, B = load(a), load(b)
same = 0; first = None
for x, y in zip(A, B):
    if x['ev'] == y['ev'] and abs(x['rt'] - y['rt']) <= tol: same += 1
    elif first is None: first = (x['rt'], x['ev'][:80], y['rt'], y['ev'][:80])
print('events %d vs %d, identical (text + time within %.3f s): %d%s' % (len(A), len(B), tol, same, '' if first is None else '; first difference %s' % (first,)))
sys.exit(0 if len(A) == len(B) and same == len(A) else 1)
