#!/usr/bin/env python3
# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation. See DISCLAIMER.md.
"""Invincible-homage hero through CustomUse (Hari's 3D provider, HTTP MCP via ~/.config/customuse/mcp.sh; the key never leaves that
script): concept image -> 3D mesh -> auto-rig, all on one CustomUse workflow canvas the owner can reopen.
State (workflow + node ids, result URLs) is kept in docs/invincible/character/customuse/state.json so steps can be re-run one at a time.

usage: customuse_hero.py image [--prompt-file F]     concept sheet (front view, A-pose, white background)
       customuse_hero.py mesh  [--model "Tripo v3.1"] image -> textured mesh
       customuse_hero.py rig                         mesh -> auto-rigged biped GLB
       customuse_hero.py poll                        status + URLs of every node
       customuse_hero.py fetch                       download the image / mesh / rigged GLB next to state.json"""
import argparse, json, subprocess, sys, time, urllib.request
from pathlib import Path

MCP = Path.home() / '.config/customuse/mcp.sh'
OUT = Path(__file__).resolve().parents[2] / 'docs/invincible/character/customuse'
STATE = OUT / 'state.json'
PROMPT = ('Full-body character reference, FRONT VIEW ONLY, single character centred on a plain pure white background, neutral A-pose '
          '(arms straight, angled about 45 degrees down from the shoulders, palms facing the thighs, feet shoulder-width apart), '
          'orthographic-style camera at chest height, even soft studio lighting, no shadow on the background. Original superhero in a '
          '2010s comic-book animated style homage: athletic young man about 18 years old, short messy dark brown-black hair, '
          'yellow-tinted wraparound flight goggles over his eyes, face visible below the goggles. Skin-tight suit: bright yellow torso '
          'and upper chest with a rounded collar, royal blue sleeves from the shoulders down, blue gloves, blue trunks and blue '
          'leggings, blue boots, a black belt, black accents on the boots and gloves. NO cape, NO logo, NO emblem, NO letters on the '
          'chest, no text anywhere. Clean readable silhouette, game-ready character design reference for 3D modelling.')


def call(tool, args):
    r = subprocess.run([str(MCP), tool, json.dumps(args)], capture_output=True, text=True, timeout=180)
    txt = (r.stdout or '') + (r.stderr or '')
    for chunk in (txt, txt[txt.find('{'):] if '{' in txt else ''):
        try: return json.loads(chunk)
        except ValueError: pass
    return {'raw': txt}


def load(): return json.loads(STATE.read_text()) if STATE.exists() else {}
def save(s): OUT.mkdir(parents=True, exist_ok=True); STATE.write_text(json.dumps(s, indent=1) + '\n')


def nodes(s):
    g = call('customuse_get_workflow', {'workflowId': s['workflowId']})
    return {n.get('id'): n for n in g.get('nodes', [])} if isinstance(g, dict) else {}, g


def wait(s, nid, every=6, limit=1500):
    t0 = time.time()
    while time.time() - t0 < limit:
        ns, g = nodes(s)
        n = ns.get(nid, {})
        st = n.get('status')
        print('  %4.0fs %s %s' % (time.time() - t0, nid[:8], st), flush=True)
        if st in ('complete', 'error'): return n
        time.sleep(every)
    raise SystemExit('timeout waiting for node %s' % nid)


def created(r, cid):
    for n in r.get('created_nodes', []) if isinstance(r, dict) else []:
        if n.get('client_id') == cid: return n.get('id')
    m = (r.get('idMap') or r.get('client_id_map') or {}) if isinstance(r, dict) else {}
    return m.get(cid)


def url(n): return n.get('meshUrl') or n.get('resultUrl') or n.get('previewUrl') or (n.get('data') or {}).get('meshUrl') or (n.get('data') or {}).get('resultUrl')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('step'); ap.add_argument('--prompt-file'); ap.add_argument('--model', default='Tripo v3.1')
    ap.add_argument('--faces', type=int, default=60000)
    a = ap.parse_args(); s = load()
    if a.step == 'image':
        prompt = Path(a.prompt_file).read_text() if a.prompt_file else PROMPT
        args = {'nodeType': 'gptImage25Flare', 'prompt': prompt, 'data': {'aspect_ratio': '3:4', 'resolution': '2K', 'quality': 'high'}}
        if s.get('workflowId'): args['workflowId'] = s['workflowId']
        else: args['workflowName'] = 'Invincible homage hero (WebHomage)'
        r = call('customuse_generate', args); print(json.dumps(r)[:800])
        s['workflowId'] = r.get('workflowId', s.get('workflowId')); s['imageNode'] = r.get('nodeId') or r.get('node', {}).get('id')
        s['canvasUrl'] = r.get('canvasUrl', s.get('canvasUrl')); save(s)
        n = wait(s, s['imageNode'], 4, 300); s['imageUrl'] = url(n); save(s); print('image', s['imageUrl'])
    elif a.step == 'mesh':
        r = call('customuse_edit_workflow_graph', {'workflowId': s['workflowId'], 'summary': 'hero mesh from the concept sheet',
                  'create_nodes': [{'client_id': 'mesh', 'type': 'modelTextureGeneration', 'position': {'x': 520, 'y': 0},
                                    'data': {'selectedModelId': a.model, 'providerModelId': a.model, 'faceLimit': a.faces, 'textureResolution': '2K',
                                             'textureMaterialMode': 'pbr', 'enableImageAutofix': True}}],
                  'connect_nodes': [{'source_node_id': s['imageNode'], 'target_node_id': 'mesh', 'source_handle': 'image-out', 'target_handle': 'image-in'}],
                  'run_node_ids': ['mesh'], 'run_mode': 'single'})
        print(json.dumps(r)[:800]); s['meshNode'] = created(r, 'mesh')
        if not s['meshNode']:
            raise SystemExit('could not read the mesh node id from the response above')
        save(s); n = wait(s, s['meshNode'], 10); s['meshUrl'] = url(n); save(s); print('mesh', s['meshUrl'])
    elif a.step == 'rig':
        r = call('customuse_edit_workflow_graph', {'workflowId': s['workflowId'], 'summary': 'auto-rig the hero (biped)',
                  'create_nodes': [{'client_id': 'rig', 'type': 'autoRigging', 'position': {'x': 1040, 'y': 0},
                                    'data': {'provider': 'cartwheel', 'rigType': 'biped', 'outputFormat': 'glb'}}],
                  'connect_nodes': [{'source_node_id': s['meshNode'], 'target_node_id': 'rig', 'source_handle': 'mesh-out', 'target_handle': 'mesh-in'}],
                  'run_node_ids': ['rig'], 'run_mode': 'single'})
        print(json.dumps(r)[:800]); s['rigNode'] = created(r, 'rig')
        if not s['rigNode']:
            raise SystemExit('could not read the rig node id from the response above')
        save(s); n = wait(s, s['rigNode'], 10); s['rigUrl'] = url(n); save(s); print('rig', s['rigUrl'])
    elif a.step == 'wait':   # resume waiting on a node already started: wait <state key of the node id> <state key for its url>
        n = wait(s, s[a.prompt_file], 10); k = {'meshNode': 'meshUrl', 'rigNode': 'rigUrl'}[a.prompt_file]; s[k] = url(n); save(s); print(k, s[k])
    elif a.step == 'poll':
        ns, g = nodes(s); print(json.dumps(g)[:3000])
    elif a.step == 'fetch':
        for k, name in (('imageUrl', 'concept.png'), ('meshUrl', 'mesh.glb'), ('rigUrl', 'rigged.glb')):
            if s.get(k):
                dst = OUT / name; urllib.request.urlretrieve(s[k], dst); print(name, dst.stat().st_size)
    else:
        ap.error('unknown step')


if __name__ == '__main__':
    main()
