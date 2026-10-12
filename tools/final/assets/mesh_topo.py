#!/usr/bin/env python3
"""Topology check of the supplied GLBs (PA phase 1, CPU, read-only): open (boundary) edges after welding
positions, connected components, and the share of triangles in components < 1 % of the mesh (floating bits).
Texture: luminance spread of the albedo (strong dark/bright baked shading shows as a wide 5-95 % range).
usage: mesh_topo.py <glb_dir> <out_json> [file ...]"""
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from glb_inspect import load, accessor

def topo(path):
    js, binc = load(path)
    prim = js["meshes"][0]["primitives"][0]
    P = accessor(js, binc, prim["attributes"]["POSITION"]).astype(np.float64)
    I = accessor(js, binc, prim["indices"]).ravel().astype(np.int64).reshape(-1, 3)
    key = np.round(P / 1e-5).astype(np.int64)
    _, weld = np.unique(key, axis=0, return_inverse=True)
    weld = weld.ravel()
    F = weld[I]
    E = np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), axis=1)
    _, cnt = np.unique(E, axis=0, return_counts=True)
    # components via union-find on welded verts
    n = weld.max() + 1
    par = np.arange(n)
    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    for a, b, c in F:
        ra, rb, rc = find(a), find(b), find(c)
        par[rb] = ra; par[find(rc)] = ra
    roots = np.array([find(v) for v in F[:, 0]])
    _, comp_tris = np.unique(roots, return_counts=True)
    small = comp_tris[comp_tris < 0.01 * len(F)].sum()
    rec = {"file": path.name, "open_edges": int((cnt == 1).sum()), "nonmanifold_edges": int((cnt > 2).sum()),
           "components": int(len(comp_tris)), "tris_in_small_components_pct": round(100.0 * small / len(F), 2)}
    if js.get("images"):
        bv = js["bufferViews"][js["images"][0]["bufferView"]]
        raw = binc[bv.get("byteOffset", 0): bv.get("byteOffset", 0) + bv["byteLength"]]
        a = np.asarray(Image.open(io.BytesIO(raw)).convert("L").resize((512, 512))).astype(np.float32)
        nz = a[a > 2]
        rec["albedo_lum_p5_p95"] = [round(float(np.percentile(nz, 5)), 1), round(float(np.percentile(nz, 95)), 1)] if nz.size else None
    return rec

src, out = Path(sys.argv[1]), Path(sys.argv[2])
want = set(sys.argv[3:])
recs = []
for p in sorted(src.glob("*.glb")):
    if want and p.name not in want: continue
    r = topo(p); recs.append(r); print(r, flush=True)
out.write_text(json.dumps(recs, indent=1))
