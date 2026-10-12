#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 16: turns TRICKCAM_CHECK.txt (trickcam_check.py v2 output per clip) + SKY_CHECK.txt (TC-I pooled) into a clip x test table.
#   usage: tc_table.py <round dir>   -> prints markdown (redirect to TC_TABLE.md)
import re, sys, os
R = sys.argv[1]
txt = open(os.path.join(R, 'TRICKCAM_CHECK.txt')).read()
clips = {}
cur = None
for line in txt.splitlines():
    m = re.match(r'^(\w+) \(.*\): (\d+) flip programs', line)
    if m: cur = m.group(1); clips[cur] = {'n': int(m.group(2)), 'lines': {}}; continue
    if cur is None: continue
    m = re.match(r'^(TC-[A-K])\b.*-> (PASS\(hold\)|PASS|FAIL|n/a)\s*$', line)
    if m: clips[cur]['lines'][m.group(1)] = m.group(2)
    m = re.match(r'^TC-I sky', line)
order = ['f4_chain_flips', 'f1_flow_backDouble', 'f2_flow_pikeSwan', 'f3_flow_corkscrew', 'f5_canyon_backDouble', 'a_swing_chain', 'b_release_trick_dive_zip']
tests = ['TC-A', 'TC-B', 'TC-C', 'TC-D', 'TC-E', 'TC-F', 'TC-G', 'TC-H', 'TC-J', 'TC-K']
print('| test | ' + ' | '.join(c.split('_')[0] for c in order if c in clips) + ' |')
print('|---|' + '---|' * len([c for c in order if c in clips]))
for t in tests:
    print('| %s | ' % t + ' | '.join(clips[c]['lines'].get(t, '-') for c in order if c in clips) + ' |')
sk = os.path.join(R, 'SKY_CHECK.txt')
if os.path.exists(sk):
    for l in open(sk):
        if l.startswith('TC-I pooled'): print('\nTC-I (pooled f1-f5): ' + l.strip()); break
