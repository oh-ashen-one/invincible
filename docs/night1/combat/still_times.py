#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat r02: pick the 10 native-4K still moments from a run's event log (ring with telegraphs, launch contact, air juggle, slam contact,
# web shot, web strike, finisher push-in + contact, ground pound, second finisher contact).  still_times.py <run_dir>  -> "t1,t2,..."
import json, os, sys
ev = [json.loads(l) for l in open(os.path.join(sys.argv[1], 'fight_events.jsonl')) if l.strip()]
def first(pred, n=0):
    m = [e for e in ev if pred(e['ev'])]
    return m[n]['rt'] if len(m) > n else None
T = [3.05,
     (first(lambda s: s.startswith('hit launch')) or 6.3) + 0.04,
     (first(lambda s: 'airStrike seg 1' in s) or 7.2) + 0.05,
     (first(lambda s: s.startswith('hit slam')) or 7.6) + 0.04,
     (first(lambda s: s.startswith('web fired')) or 9.5) + 0.25,
     (first(lambda s: 'webStrike ->' in s) or 10.0) + 0.15,
     (first(lambda s: s.startswith('cine finisher')) or 14.5) + 0.55,
     (first(lambda s: s.startswith('hit finisher')) or 15.2) + 0.05,
     (first(lambda s: s == 'groundPound', 1) or 20.6) + 0.04,
     (first(lambda s: s.startswith('hit finisher'), 1) or 27.7) + 0.05]
print(','.join('%.2f' % t for t in T))
