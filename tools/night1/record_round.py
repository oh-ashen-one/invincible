#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# Record one finished round in docs/night1/model-ledger.json and docs/night1/progress.json.
# usage: record_round.py '<json>'  where json = {t, piece_id, piece, round, model, effort, verdict, scores:[..], gap, notes, clip?: {src, title, caption}}
import json, sys
r = json.loads(sys.argv[1])
L = 'docs/night1/model-ledger.json'; led = json.load(open(L))
led['rounds'].append({'piece': r['piece'], 'round': r['round'], 'model': r['model'], 'effort': r['effort'], 'scores': r['scores']})
json.dump(led, open(L, 'w'), indent=1)
P = 'docs/night1/progress.json'; d = json.load(open(P))
v = {'FAILS TARGET': 'fails', 'APPROACHES TARGET': 'approaches', 'MEETS TARGET': 'meets'}.get(r['verdict'], r['verdict'])
d['critic'].append({'t': r['t'], 'piece': r['piece'], 'round': r['round'], 'verdict': v, 'gap': r['gap'], 'notes': r.get('notes', '')})
for p in d['pieces']:
    if p['id'] == r['piece_id']:
        p.update(round=r['round'], verdict='%s — lowest %s (%s)' % (v, min(r['scores']), r['model']), gap=r['gap'], state='active')
if r.get('clip'): d['clips'].append(r['clip'])
d['updated'] = r['t']
json.dump(d, open(P, 'w'), indent=1)
print('recorded', r['piece'], r['round'])
