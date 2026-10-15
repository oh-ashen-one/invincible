#!/usr/bin/env python3
# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation. See DISCLAIMER.md.
"""Hero model v2 on the CustomUse canvas: textured mesh candidates from the 4-view turnaround (multiview children recorded by
customuse_hero.py state.json 'mvChildren'), then auto-rig of the chosen one. Uses only existing CustomUse credits.
usage: customuse_v2.py candidates | wait | fetch | rig <candidate>"""
import json, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import customuse_hero as cu

CANDS = {   # name -> (node type, data)
    'hi3d':    ('modelTextureGeneration', {'selectedModelId': 'hitem3d/hi3d/v3.0', 'providerModelId': 'hitem3d/hi3d/v3.0'}),
    'tripoP2': ('modelTextureGeneration', {'selectedModelId': 'Tripo P2', 'providerModelId': 'Tripo P2', 'quad': True}),
    'meshy7':  ('modelTextureGeneration', {'selectedModelId': 'meshy-7', 'providerModelId': 'meshy-7'}),
    'hunyuan': ('hunyuanV31Mesh3d', {}),
}
COMMON = {'meshInputMode': 'multiview', 'faceLimit': 150000, 'textureResolution': '4K', 'textureMaterialMode': 'pbr'}


def views(s):
    def key(v):
        try: return json.loads(v).get('viewKey')
        except (TypeError, ValueError, AttributeError): return v
    return {key(c.get('view')): c['id'] for c in s['mvChildren']}


def main():
    step = sys.argv[1]; s = cu.load()
    if step == 'candidates':
        v = views(s); create, conn = [], []
        for i, (name, (typ, data)) in enumerate(CANDS.items()):
            d = dict(COMMON); d.update(data)
            if typ == 'hunyuanV31Mesh3d': d = {'faceLimit': 150000, 'textureResolution': '4K'}
            create.append({'client_id': name, 'type': typ, 'position': {'x': 520, 'y': 600 + 260 * i}, 'data': d})
            hmap = {'front': 'image-in' if typ == 'hunyuanV31Mesh3d' else 'front-image-in', 'left': 'left-image-in', 'right': 'right-image-in', 'back': 'back-image-in'}
            for k, h in hmap.items():
                conn.append({'source_node_id': v[k], 'target_node_id': name, 'source_handle': 'image-out', 'target_handle': h})
        r = cu.call('customuse_edit_workflow_graph', {'workflowId': s['workflowId'], 'summary': 'v2 mesh candidates from the 4-view turnaround',
                                                       'create_nodes': create, 'connect_nodes': conn, 'run_node_ids': list(CANDS), 'run_mode': 'single'})
        print(json.dumps(r)[:1200])
        s['v2'] = {name: {'node': cu.created(r, name)} for name in CANDS}; cu.save(s)
    elif step == 'wait':
        t0 = time.time()
        while time.time() - t0 < 260:
            g = cu.call('customuse_get_workflow', {'workflowId': s['workflowId'], 'nodeIds': [c['node'] for c in s['v2'].values() if c['node']]})
            ns = {n['id']: n for n in g.get('nodes', [])}
            st = {k: ns.get(c['node'], {}).get('status') for k, c in s['v2'].items()}
            for k, c in s['v2'].items():
                n = ns.get(c['node'], {})
                if n.get('status') == 'complete': c['url'] = cu.url(n)
                if n.get('status') == 'error': c['error'] = n.get('error') or n.get('errorMessage') or 'error'
            cu.save(s); print('%4.0fs' % (time.time() - t0), st, flush=True)
            if all(x in ('complete', 'error') for x in st.values()): break
            time.sleep(15)
    elif step == 'fetch':
        out = cu.OUT / 'v2'; out.mkdir(exist_ok=True)
        for k, c in s['v2'].items():
            if c.get('url'):
                dst = out / (k + '.glb'); urllib.request.urlretrieve(c['url'], dst); print(k, dst.stat().st_size)
    elif step == 'rig':
        name = sys.argv[2]; src = s['v2'][name]['node']
        r = cu.call('customuse_edit_workflow_graph', {'workflowId': s['workflowId'], 'summary': 'auto-rig v2 (%s)' % name,
                  'create_nodes': [{'client_id': 'rig2', 'type': 'autoRigging', 'position': {'x': 1040, 'y': 600}, 'data': {'provider': 'cartwheel', 'rigType': 'biped', 'outputFormat': 'glb'}}],
                  'connect_nodes': [{'source_node_id': src, 'target_node_id': 'rig2', 'source_handle': 'mesh-out', 'target_handle': 'mesh-in'}],
                  'run_node_ids': ['rig2'], 'run_mode': 'single'})
        s['v2rigNode'] = cu.created(r, 'rig2'); cu.save(s); print(json.dumps(r)[:500])
        n = cu.wait(s, s['v2rigNode'], 10); s['v2rigUrl'] = cu.url(n); cu.save(s)
        dst = cu.OUT / 'v2' / ('rigged_%s.glb' % name); urllib.request.urlretrieve(s['v2rigUrl'], dst); print('rigged', dst, dst.stat().st_size)


if __name__ == '__main__':
    main()
