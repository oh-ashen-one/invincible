#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Submit a Python file (or -c code) to THIS worktree's Look editor job server (tools/perf_ue/job_server.py) and wait.
usage: uejob.py file.py [key=value ...]  |  uejob.py -c "code"      (key=value pairs are exposed as JOB_ARGS dict)
The job runs with __file__ = the submitted file's real path (so scripts find their sibling data files) and with the
P4 scratch locations for the city export / textures (P1's scripts read SM2_CITY_EXPORT / SM2_CITY_TEX)."""
import os, sys, time, json, uuid
SCR = os.environ.get('SM2_LOOK_SCRATCH', '/Users/midir/sm2-n1/_scratch/look')   # scratch root (export/, tex/, uejobs/, capture/ ...)
JOBS = os.environ.get('SM2_LOOK_JOBS', SCR + '/uejobs')
os.makedirs(JOBS, exist_ok=True)
if sys.argv[1] == '-c': code, args, real = sys.argv[2], {}, '<inline>'
else:
    real = os.path.abspath(sys.argv[1]); code = open(real).read(); args = dict(a.split('=', 1) for a in sys.argv[2:])
pre = ('import os\nos.environ.setdefault("SM2_CITY_EXPORT", %r)\nos.environ.setdefault("SM2_CITY_TEX", %r)\n__file__ = %r\nJOB_ARGS = %s\n'
       % (SCR + '/export/midtown3x3', SCR + '/tex', real, json.dumps(args)))
jid = time.strftime('%H%M%S') + '_' + uuid.uuid4().hex[:6]
p = os.path.join(JOBS, jid + '.py')
open(p + '.tmp', 'w').write(pre + code)
os.rename(p + '.tmp', p)
t0 = time.time(); timeout = float(os.environ.get('UEJOB_TIMEOUT', '3600'))
while not os.path.exists(p + '.done'):
    if time.time() - t0 > timeout: sys.exit('timeout waiting for ' + p)
    time.sleep(0.2)
print(open(p + '.out').read(), end='')
if open(p + '.done').read() != 'ok': sys.exit(1)
