# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', 'skinfit'))
import skinfit, softrender as sr


def prims_from_glb(path):
    j, b = skinfit.read_glb(path)
    body = next(nd for nd in j['nodes'] if nd.get('name') == 'SpiderMan')
    out = []
    for p in j['meshes'][body['mesh']]['primitives']:
        nm = j['materials'][p['material']]['name']
        if nm not in ('Lens', 'LensFrame'): continue
        P = skinfit.accessor(j, b, p['attributes']['POSITION']).astype(np.float32); N = skinfit.accessor(j, b, p['attributes']['NORMAL']).astype(np.float32)
        F = skinfit.accessor(j, b, p['indices']).reshape(-1, 3).astype(int)
        col = (0.80, 0.42, 0.04) if nm == 'Lens' else (0.012, 0.016, 0.02)
        out.append(sr.Prim(P, N, F, color=np.array(col) ** 2.2 * 1.0 if nm == 'Lens' else np.array(col), rough=0.12 if nm == 'Lens' else 0.3, spec=0.9 if nm == 'Lens' else 0.25, name=nm))
    return out
