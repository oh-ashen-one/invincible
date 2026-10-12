#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat: turn a record run (reactive 'threat' / 'free' beats) into a fixed-time playback script.
#   freeze_script.py <record script.json> <record run beats.jsonl> <out script.json>
# Every beat gets t = the real time it fired in the record run (minus a quarter frame, so the replay fires on the same frame);
# 'react' / 'window' are dropped. The replay must reproduce the record run exactly (deterministic fixed-step sim): check_replay
# compares the two event logs.
import json, sys
src, beats_log, out = sys.argv[1:4]
S = json.load(open(src))
fired = [json.loads(l) for l in open(beats_log) if l.strip()]
# r02: 'reflex' dodges (script "reflex": the record run dodges telegraphed blows) become plain fixed-time beats
reflex = [f for f in fired if f['label'].startswith('reflex dodge')]
fired = [f for f in fired if not f['label'].startswith('reflex dodge')]
beats = sorted(S['beats'], key=lambda b: b['t'])
assert len(fired) == len(beats), (len(fired), len(beats))
# r02: beats the record run skipped ('react: air' with no air state) are dropped from the replay
skipped = [f for f in fired if f.get('react', '').startswith('skipped')]
fired = [f for f in fired if not f.get('react', '').startswith('skipped')]
# beats fire in script order except reactive ones (they may fire later than later-listed beats): match by label + key
by = {}
for f in fired: by.setdefault((f['label'], f['key']), []).append(f)
nb = []
skip_labels = {(f['label'], f['key']) for f in skipped}
for b in beats:
    if (b['label'], b['key']) in skip_labels and not by.get((b['label'], b['key'])): continue
    f = by[(b['label'], b['key'])].pop(0)
    c = {k: v for k, v in b.items() if k not in ('react', 'window', 'rel')}
    c['t'] = round(f['rt'] - 1 / 240, 4)
    if b.get('react'): c['recorded'] = '%s: %s' % (b['react'], f.get('react', ''))
    nb.append(c)
for f in reflex:
    nb.append({'t': round(f['rt'] - 1 / 240, 4), 'key': 'dodge', 'label': f['label'], 'recorded': f.get('react', '')})
S.pop('reflex', None)
S['beats'] = sorted(nb, key=lambda b: b['t'])
S['frozen_from'] = src.split('/')[-1]
json.dump(S, open(out, 'w'), indent=1)
print('wrote', out, len(nb), 'beats;', len(skipped), 'skipped in the record run;', len(reflex), 'reflex dodges')
