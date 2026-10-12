#!/usr/bin/env python3
"""(r10) stage-2 / final choice for the S4 sweep (see _scratch/city/r10/hold2.sh). Reads <out>/<TAG>/score.json (one JSON line each) for the tags
  A (FarGain 4, FarSunK .15, fog .0008), B (FarSunK .10), C (FarGain 2.5), A1 (fog .0011), A2 (fog .0014), A3 / A4 (darker fog colour), Z (the combination, stage 2).
usage: s4_pick.py <out> combine   -> prints shell assignments for the combined stage-2 configuration
       s4_pick.py <out> final     -> prints shell assignments of the best tag overall (FG FK FOG FOGC TAG)"""
import sys, os, json
out, mode = sys.argv[1], sys.argv[2]
BASE = dict(FG='4.0', FK='0.15', FOG='0.0008', FOGC='0.76,0.78,0.80')
CFG = {'A': {}, 'B': dict(FK='0.10'), 'B2': dict(FK='0.22'), 'C': dict(FG='2.5'), 'A1': dict(FOG='0.0012'), 'A2': dict(FOG='0.0014'), 'A3': dict(FOGC='0.62,0.64,0.67'), 'A4': dict(FOGC='0.50,0.52,0.55')}
def score(tag):
    p = os.path.join(out, tag, 'score.json')
    if not os.path.exists(p): return None
    try: return json.loads(open(p).read().strip().splitlines()[-1])['score']
    except Exception: return None
S = {t: score(t) for t in list(CFG) + ['Z']}
def sh(d): return ' '.join('%s=%s' % (k, v if ' ' not in str(v) else '"%s"' % v) for k, v in d.items())
if mode == 'combine':
    c = dict(BASE)
    if S['A'] is not None:
        fk = [(S[t], CFG[t]['FK']) for t in ('B', 'B2') if S[t] is not None and S[t] < S['A']]
        if fk: c['FK'] = min(fk)[1]
        if S['C'] is not None and S['C'] < S['A']: c['FG'] = CFG['C']['FG']
        fogs = [(S[t], CFG[t]['FOG']) for t in ('A1', 'A2') if S[t] is not None and S[t] < S['A']]
        if fogs: c['FOG'] = min(fogs)[1]
        fc = [(S[t], CFG[t]['FOGC']) for t in ('A3', 'A4') if S[t] is not None and S[t] < S['A']]
        if fc: c['FOGC'] = min(fc)[1]
    print(sh(c)); print('scores', S, file=sys.stderr)
else:
    cands = [(v, t) for t, v in S.items() if v is not None]
    best = min(cands)[1] if cands else 'A'
    if best == 'Z':
        z = json.load(open(os.path.join(out, 'Z', 'config.json'))); c = dict(BASE, **z)
    else: c = dict(BASE, **CFG[best])
    c['TAG'] = best; print(sh(c)); print('scores', S, file=sys.stderr)
