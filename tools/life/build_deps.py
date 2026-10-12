#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
# P6 City life: build the pieces this piece stands on (city geometry, look rigs) with piece C's build_manhattan.py steps,
# but on THIS worktree's dev port (5207) and THIS piece's scratch dir, without editing build_manhattan.py.
#   python3 tools/life/build_deps.py [--steps cpp,city_export,city_prep,city,city2,look]
# default steps: cpp, city_export, city_prep, city (pass 1), city2 (pass 2 'kit' only), look. 'traversal', 'characters' and 'map' of
# piece C are not needed by the life test map.
# Slot rule (RULES.md, owner 16:43 incident): the commandlets are headless (-nullrhi, no GPU); they wait while the number of running
# Unreal processes of any kind is >= N, N = /Users/midir/sm2-n1/_scratch/gpu/slots (auto-tuned by the health monitor, default 3).
import os, sys, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.dirname(os.path.dirname(HERE))
os.environ.setdefault('SM2_MANHATTAN_SCR', '/Users/midir/sm2-n1/_scratch/life/manhattan')
sys.path.insert(0, os.path.join(WT, 'unreal/WebHomage/Scripts'))
import build_manhattan as bm  # noqa: E402
bm.DEV_PORT = 5207

def slots():
    try: return int(open('/Users/midir/sm2-n1/_scratch/gpu/slots').read().strip())
    except Exception: return 3

def wait_slot():
    while True:
        n = subprocess.run("pgrep -f 'MacOS/UnrealEditor( |$)' | wc -l", shell=True, capture_output=True, text=True).stdout.strip()
        if int(n or 0) < slots(): return
        bm.log('%s Unreal processes running (cap %d), waiting 60 s' % (n, slots())); time.sleep(60)
bm.wait_slot = wait_slot

def step_city2():
    env = {'SM2_CITY_EXPORT': bm.EXPORT, 'SM2_CITY_TEX': bm.TEX}
    bm.ue_python('city_pass2_kit', bm.exec_wrapper(os.path.join(bm.HERE, 'build_city.py'), bm.LOAD_SME + 'JOB_ARGS = {"steps": "kit"}'), env)
bm.step_city2 = step_city2
def step_city_pass1_only():
    env = {'SM2_CITY_EXPORT': bm.EXPORT, 'SM2_CITY_TEX': bm.TEX}
    bm.ue_python('city_pass1', bm.exec_wrapper(os.path.join(bm.HERE, 'build_city.py'), bm.LOAD_SME + 'JOB_ARGS = {"steps": "clean,tex,mat,mesh,proto,map"}'), env)
bm.step_city = step_city_pass1_only
bm.STEPS_ALL = ['cpp', 'city_export', 'city_prep', 'city', 'city2', 'look']
if '--steps' not in sys.argv:
    sys.argv += ['--steps', ','.join(bm.STEPS_ALL)]
bm.main()
