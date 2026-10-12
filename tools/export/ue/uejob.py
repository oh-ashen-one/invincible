#!/usr/bin/env python3
"""Submit a Python file (or -c code) to this worktree's editor job server (tools/export/ue/job_server.py) and wait.
usage: uejob.py file.py [key=value ...]  |  uejob.py -c "code"      (key=value pairs are exposed as JOB_ARGS dict)"""
import os, sys, time, json, uuid
JOBS = os.environ.get('SM2_CITY_JOBS', os.path.join(os.environ.get('SM2_CITY_SCRATCH', '/Users/midir/sm2-n1/_scratch/city'), 'uejobs'))
os.makedirs(JOBS, exist_ok=True)
if sys.argv[1] == '-c': code, args = sys.argv[2], {}
else:
    code = open(sys.argv[1]).read(); args = dict(a.split('=', 1) for a in sys.argv[2:])
    code = 'JOB_SCRIPT_DIR = ' + repr(os.path.dirname(os.path.abspath(sys.argv[1]))) + '\n' + code   # (r07) the job runs from a copy: tell it where its sources live
jid = time.strftime('%H%M%S') + '_' + uuid.uuid4().hex[:6]
p = os.path.join(JOBS, jid + '.py')
open(p + '.tmp', 'w').write('JOB_ARGS = ' + json.dumps(args) + '\n' + code)
os.rename(p + '.tmp', p)
t0 = time.time(); timeout = float(os.environ.get('UEJOB_TIMEOUT', '3600'))
while not os.path.exists(p + '.done'):
    if time.time() - t0 > timeout: sys.exit('timeout waiting for ' + p)
    time.sleep(0.2)
print(open(p + '.out').read(), end='')
st = open(p + '.done').read()
if st != 'ok': sys.exit(1)
