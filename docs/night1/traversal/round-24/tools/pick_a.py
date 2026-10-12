#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game. P3 r24: score the a-chain probe variants (r24_checks T7/T3/T1/T2/T4).
import os, re, subprocess, sys
TD = '/Users/midir/sm2-n1/traversal/docs/night1/traversal'
OUT = sys.argv[1]; names = sys.argv[2:]
best = None
for n in names:
    d = os.path.join(OUT, n)
    if not os.path.isdir(d): continue
    txt = subprocess.run(['python3', f'{TD}/r24_checks.py', d, '--clip', n], capture_output=True, text=True).stdout
    open(os.path.join(d, 'check.txt'), 'w').write(txt)
    m = re.search(r'T7 4 s windows .*?: (\d+)/(\d+) hold', txt)
    t7 = int(m.group(1)) / max(1, int(m.group(2))) if m else 0.0
    w = re.search(r'T3 web_on ([\d.]+) %', txt); web = float(w.group(1)) if w else 99
    t1 = 'T1 rope' in txt and re.search(r'T1 .*-> PASS', txt) is not None
    t2 = re.search(r'T2 .*-> PASS', txt) is not None
    t4 = re.search(r'T4 -> PASS', txt) is not None
    score = 100 * t7 + (25 if 25 <= web <= 45 else -abs(web - 35)) + 10 * t1 + 10 * t2 + 15 * t4
    print(f'{n}: T7 {t7*100:.0f} %  web_on {web:.1f} %  T1 {t1} T2 {t2} T4 {t4}  score {score:.1f}')
    if best is None or score > best[0]: best = (score, n)
if best: print('BEST', best[1]); open(os.path.join(OUT, 'BEST_A'), 'w').write(best[1])
