#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Piece F: build /Game/Maps/Manhattan in THIS worktree with piece C's UNCHANGED Scripts/build_manhattan.py.
Differences from running build_manhattan.py directly (both are parameters, not code changes):
  * scratch = /Users/midir/sm2-n1/_scratch/perf (env SM2_MANHATTAN_SCR), so nothing of C's scratch is touched;
  * the browser export uses F's own Vite port 5209 (C's 5208 is C's), started from this worktree and stopped afterwards.
Round 03 additions (F-owned steps appended to C's list; C's steps and files are untouched):
  city_extra   P1's placement tools that build_manhattan.py (round 01) predates and build_city.py r08 / r09 needs: export_vehicles.py, street_cars.py,
               street_trees.py, street_traffic.py, bake_sunmask.py (tools/export/build_city.sh order), paths relocated with SM2_CITY_* env
  tree_proxy   (round 05) tree_proxy_dump.py (commandlet) + tree_proxy_build.py: one merged ray-tracing proxy GLB per city tile -> <SCR>/rtproxy
  perf_apply   perf_apply.py steps SM2_PERF_APPLY_STEPS (default rt_lite,cloud) on the rebuilt content, in one headless commandlet
  perf_preset  writes the round-02 preset (overrides/perf60_hwrefl.cvars + r.ScreenPercentage) as a marked [ConsoleVariables] block of
               Config/Mac/MacEngine.ini (generated, untracked, never `git add`ed; project platform layer, read by every Mac launch of THIS checkout: editor, -game, commandlets)
  perf_audit   commandlet perf_audit.py: reads the rebuilt content back and writes docs/night1/perf/round-03/content_audit.json
usage: python3 tools/perf_ue2/build_map.py [--steps cpp,city_export,city_prep,city_extra,city,traversal,characters,look,map,tree_proxy,perf_apply,perf_preset,perf_audit]   (editor closed)"""
import os, sys, subprocess, json
SCR = '/Users/midir/sm2-n1/_scratch/perf'
PORT = 5209
os.environ['SM2_MANHATTAN_SCR'] = SCR
HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(WT, 'unreal', 'WebHomage', 'Scripts'))
os.makedirs(os.path.join(SCR, 'logs'), exist_ok=True)
import build_manhattan as bm  # noqa: E402
bm.DEV_PORT = PORT


def _wait_slot():
    """same rule as bm.wait_slot (wait while 3+ Unreal run), but counts only real UnrealEditor processes: bm's
    `pgrep -f MacOS/UnrealEditor( |$)` also matches gpu_slot.py WAITERS (their argv holds the queued UnrealEditor command)"""
    import time
    while True:
        out = subprocess.run(['ps', '-axo', 'comm='], capture_output=True, text=True).stdout.splitlines()
        n = sum(1 for c in out if c.strip().endswith('MacOS/UnrealEditor'))
        if n < 3: return
        bm.log('3+ Unreal instances running (%d), waiting 60 s' % n); time.sleep(60)


bm.wait_slot = _wait_slot
UE_DIR = os.path.join(WT, 'unreal', 'WebHomage')
PRESET_STEM = os.environ.get('SM2_PERF_PRESET', 'perf60_hwl2')   # round 04 (round 03: perf60_hwl)
PRESET_SP = os.environ.get('SM2_PERF_PRESET_SP', '50')
INI = os.path.join(UE_DIR, 'Config', 'Mac', 'MacEngine.ini')   # project platform layer: generated, untracked, never rewritten by the engine. (Saved/Config/MacEditor/Engine.ini does NOT work: the engine deletes it at exit when it holds nothing but console variables)
BEGIN, END = '; >>> F perf preset (tools/perf_ue2/build_map.py step perf_preset) >>>', '; <<< F perf preset <<<'
os.environ['SM2_CITY_SCRATCH'] = SCR   # P1's tools default to THEIR scratch; every one of them honours these
os.environ['SM2_CITY_EXPORT'] = bm.EXPORT
os.environ['SM2_CITY_TEX'] = bm.TEX


def step_city_extra():
    e = bm.EXPORT
    os.makedirs(os.path.join(SCR, 'r09'), exist_ok=True)   # bake_sunmask.py writes its preview PNG to <SM2_CITY_SCRATCH>/r09/
    for name, cmd in (('export_vehicles', ['python3', 'tools/export/export_vehicles.py', e]), ('street_cars', ['python3', 'tools/export/street_cars.py', e]),
                      ('street_trees', ['python3', 'tools/export/street_trees.py', e]), ('street_traffic', ['python3', 'tools/export/street_traffic.py', e]),
                      ('bake_sunmask', ['python3', 'tools/export/bake_sunmask.py', e, bm.TEX])):
        bm.sh(cmd, log_name='city_extra_%s.log' % name)


PROXY_DIR = os.path.join(SCR, 'rtproxy')   # round 05: tree ray-tracing proxy GLBs (tree_proxy_build.py output), imported by perf_apply step rt_proxy_trees


def step_tree_proxy():
    """round 05: dump the tree instances of the rebuilt geometry level (commandlet, read-only), then build one merged ray-tracing proxy GLB per
    city tile (plain python3 + numpy). Must run BEFORE perf_apply; knobs SM2_PERF_PROXY_* (tree_proxy_build.py header)."""
    dump = os.path.join(SCR, 'tree_dump.json')
    if os.path.exists(dump): os.remove(dump)
    bm.ue_python('tree_proxy_dump', bm.exec_wrapper(os.path.join(HERE, 'tree_proxy_dump.py'), ''), {'SM2_PERF_PROXY_DUMP': dump})
    bm.sh([sys.executable, os.path.join(HERE, 'tree_proxy_build.py'), '--dump', dump, '--export', bm.EXPORT, '--out', PROXY_DIR], log_name='tree_proxy_build.log')
    bm.log('tree proxies', open(os.path.join(SCR, 'logs', 'tree_proxy_build.log')).read().strip().splitlines()[-1][:400])


def step_perf_apply():
    steps = os.environ.get('SM2_PERF_APPLY_STEPS', 'rt_lite_trees,rt_proxy_trees,cloud')   # round 05 (round 04: rt_lite_trees,tree_rt_opaque,cloud; round 03: rt_lite,cloud); cloud km = env SM2_PERF_CLOUD_KM (perf_apply default 20 since round 04)
    logp = os.path.join(SCR, 'perf_apply.json')
    if os.path.exists(logp): os.remove(logp)
    bm.ue_python('perf_apply', bm.exec_wrapper(os.path.join(HERE, 'perf_apply.py'), ''), {'SM2_PERF_APPLY': steps, 'SM2_PERF_APPLY_LOG': logp, 'SM2_PERF_PROXY_DIR': PROXY_DIR})
    rep = json.load(open(logp))
    bm.log('perf_apply', json.dumps(rep['changed']))
    if rep.get('errors'): raise SystemExit('perf_apply errors: %s' % rep['errors'][:5])
    if not rep.get('saved'): raise SystemExit('perf_apply: geometry level not saved')


def preset_lines():
    sys.path.insert(0, HERE)
    from perf_route import read_set
    d = dict(read_set(PRESET_STEM))   # later lines win, same rule as perf_route.py
    d['r.ScreenPercentage'] = PRESET_SP
    return sorted(d.items())


def step_perf_preset():
    ini = INI
    os.makedirs(os.path.dirname(ini), exist_ok=True)
    txt = open(ini).read() if os.path.exists(ini) else ''
    if BEGIN in txt:   # replace the marked block; nothing else in the file is touched
        a, b = txt.index(BEGIN), txt.index(END) + len(END)
        txt = txt[:a].rstrip('\n') + '\n' + txt[b:].lstrip('\n')
    block = BEGIN + '\n; preset %s at r.ScreenPercentage %s, generated from tools/perf_ue2/overrides/%s.cvars; removed again with `build_map.py --preset-off`\n[ConsoleVariables]\n' % (
        PRESET_STEM, PRESET_SP, PRESET_STEM) + ''.join('%s=%s\n' % kv for kv in preset_lines()) + END + '\n'
    open(ini, 'w').write(txt.rstrip('\n') + '\n\n' + block if txt.strip() else block)
    bm.log('preset written to', ini, '(%d cvars)' % len(preset_lines()))


def step_perf_preset_off():
    ini = INI
    if not os.path.exists(ini): return
    txt = open(ini).read()
    if BEGIN in txt:
        a, b = txt.index(BEGIN), txt.index(END) + len(END)
        rest = (txt[:a].rstrip('\n') + '\n' + txt[b:].lstrip('\n')).strip('\n')
        if rest: open(ini, 'w').write(rest + '\n')
        else: os.remove(ini)
    bm.log('preset removed from', ini)


def step_perf_audit():
    out = os.path.join(WT, 'docs', 'night1', 'perf', os.environ.get('SM2_PERF_ROUND', 'round-05'), os.environ.get('SM2_PERF_AUDIT_NAME', 'content_audit.json'))   # SM2_PERF_AUDIT_NAME=content_audit_asbuilt.json before perf_apply
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bm.ue_python('perf_audit', bm.exec_wrapper(os.path.join(HERE, 'perf_audit.py'), ''), {'SM2_PERF_AUDIT_OUT': out})
    a = json.load(open(out))
    bm.log('audit', json.dumps(a.get('summary')))


bm.step_city_extra, bm.step_tree_proxy, bm.step_perf_apply, bm.step_perf_preset, bm.step_perf_audit = step_city_extra, step_tree_proxy, step_perf_apply, step_perf_preset, step_perf_audit
bm.STEPS_ALL = ['cpp', 'city_export', 'city_prep', 'city_extra', 'city', 'traversal', 'characters', 'look', 'map', 'tree_proxy', 'perf_apply', 'perf_preset', 'perf_audit']
if '--preset-off' in sys.argv:   # take the preset block out of Config/Mac/MacEngine.ini (as-found comparison runs)
    step_perf_preset_off(); sys.exit(0)
try:
    bm.main()
finally:
    # stop F's own vite (only the process listening on F's port, started from this worktree)
    pids = subprocess.run(['lsof', '-t', '-nP', '-iTCP:%d' % PORT, '-sTCP:LISTEN'], capture_output=True, text=True).stdout.split()
    for p in pids:
        cmd = subprocess.run(['ps', '-o', 'command=', '-p', p], capture_output=True, text=True).stdout
        if 'vite' in cmd: subprocess.run(['kill', p])
