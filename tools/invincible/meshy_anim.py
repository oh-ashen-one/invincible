#!/usr/bin/env python3
# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation. See DISCLAIMER.md.
"""Starter animation library for the Invincible-homage hero through Meshy (existing credits only).
The key is read from ~/.agents-md/.secrets/meshy.env inside this process and never printed or written anywhere.
State: docs/invincible/character/meshy/state.json.

usage: meshy_anim.py library [--grep fly,land,punch]   free: list the preset library (writes library.json)
       meshy_anim.py rig <model_url> [--height 1.8]      rig the v2 hero (5 credits)
       meshy_anim.py animate <id,id,...>                 apply up to 10 presets as one merged GLB (3 credits / action)
       meshy_anim.py balance"""
import argparse, json, os, sys, time, urllib.request
from pathlib import Path

API = 'https://api.meshy.ai/openapi/v1'
OUT = Path(__file__).resolve().parents[2] / 'docs/invincible/character/meshy'
STATE = OUT / 'state.json'


def key():
    for line in (Path.home() / '.agents-md/.secrets/meshy.env').read_text().splitlines():
        if line.strip().startswith('MESHY_API_KEY='):
            return line.split('=', 1)[1].strip().strip('"\'')
    raise SystemExit('MESHY_API_KEY missing')


def req(method, path, body=None):
    r = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                               headers={'Authorization': 'Bearer ' + key(), 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(r, timeout=120) as f: return json.loads(f.read())
    except urllib.error.HTTPError as e:
        raise SystemExit('HTTP %s %s: %s' % (e.code, path, e.read().decode()[:400]))


def load(): return json.loads(STATE.read_text()) if STATE.exists() else {}
def save(s): OUT.mkdir(parents=True, exist_ok=True); STATE.write_text(json.dumps(s, indent=1) + '\n')


def wait(kind, tid):
    t0 = time.time()
    while True:
        t = req('GET', '/%s/%s' % (kind, tid))
        print('  %4.0fs %s %s%%' % (time.time() - t0, t.get('status'), t.get('progress')), flush=True)
        if t.get('status') in ('SUCCEEDED', 'FAILED', 'CANCELED'): return t
        time.sleep(8)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('step'); ap.add_argument('arg', nargs='?'); ap.add_argument('--grep'); ap.add_argument('--height', type=float, default=1.8)
    a = ap.parse_args(); s = load()
    if a.step == 'balance':
        print(req('GET', '/balance'))
    elif a.step == 'library':
        lib = req('GET', '/animations/library'); OUT.mkdir(parents=True, exist_ok=True)
        (OUT / 'library.json').write_text(json.dumps(lib, indent=1) + '\n')
        words = [w.strip().lower() for w in (a.grep or '').split(',') if w.strip()]
        for x in lib:
            txt = json.dumps(x).lower()
            if not words or any(w in txt for w in words):
                print(x.get('action_id'), '|', x.get('name'), '|', x.get('category'), '|', x.get('sub_category') or x.get('subcategory') or '')
        print(len(lib), 'animations in the library')
    elif a.step == 'rig':
        tid = req('POST', '/rigging', {'model_url': a.arg, 'height_meters': a.height})['result']
        s['rig_task'] = tid; save(s); t = wait('rigging', tid)
        s['rig'] = {k: t.get(k) for k in ('status', 'consumed_credits', 'task_error')}; s['rig_result'] = t.get('result'); save(s)
        if t.get('status') == 'SUCCEEDED':
            urllib.request.urlretrieve(t['result']['rigged_character_glb_url'], OUT / 'meshy_rigged.glb'); print('rigged ->', OUT / 'meshy_rigged.glb')
        else: print(json.dumps(t.get('task_error')))
    elif a.step == 'animate':
        ids = [int(x) for x in a.arg.split(',')]
        tid = req('POST', '/animations', {'rig_task_id': s['rig_task'], 'action_ids': ids, 'post_process': {'operation_type': 'change_fps', 'fps': 30}})['result']
        t = wait('animations', tid)
        s.setdefault('anim', []).append({'task': tid, 'ids': ids, 'status': t.get('status'), 'credits': t.get('consumed_credits'), 'error': t.get('task_error')}); save(s)
        if t.get('status') == 'SUCCEEDED':
            n = len(s['anim']); dst = OUT / ('meshy_anims_%02d.glb' % n)
            urllib.request.urlretrieve(t['result']['animation_glb_url'], dst); print('anims ->', dst, dst.stat().st_size)
        else: print(json.dumps(t.get('task_error')))


if __name__ == '__main__':
    main()
