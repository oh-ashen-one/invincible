#!/usr/bin/env python3
"""Run a Python file (or -c code) inside the P2 Characters Unreal editor via the file mailbox (see ue_mailbox.py).
usage: tools/ue_char/uebox.py script.py [--timeout S]   |   tools/ue_char/uebox.py -c "print(1)"
Scripts may read ARGS (json from --args) from globals."""
import os, sys, time, json, uuid
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '.')); from p2paths import WT as _P2WT, scr as _scr  # noqa: E402
BOX = _scr('uebox')
a = sys.argv[1:]
timeout = 900
if '--timeout' in a:
    i = a.index('--timeout'); timeout = float(a[i + 1]); del a[i:i + 2]
args = '{}'
if '--args' in a:
    i = a.index('--args'); args = a[i + 1]; del a[i:i + 2]
if a[0] == '-c':
    code = a[1]; base = 'inline'
else:
    code = open(a[0]).read(); base = os.path.splitext(os.path.basename(a[0]))[0]
code = 'import json\nARGS = json.loads(%r)\n' % args + code
name = '%d_%s_%s.py' % (time.time() * 1000, base, uuid.uuid4().hex[:6])
tmp = os.path.join(BOX, 'in', name + '.part')
open(tmp, 'w').write(code)
os.replace(tmp, os.path.join(BOX, 'in', name))
out = os.path.join(BOX, 'out', name + '.txt')
t0 = time.time()
while not os.path.exists(out):
    if time.time() - t0 > timeout:
        sys.exit('timeout waiting for ' + out)
    time.sleep(0.2)
txt = open(out).read()
print(txt, end='')
sys.exit(0 if txt.startswith('OK') else 1)
