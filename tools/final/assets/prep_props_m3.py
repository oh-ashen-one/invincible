#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""PA phase 2 prep (CPU only): the 7 approved supplied GLBs -> game-ready LOD GLBs + downscaled textures for build_props_m3.py.

For each item: Blender background decimation (tools/crowdfit/decimate_lods.py via crowdfit.decimate: Tripo +X front turned to glTF +Z,
no render, no GPU), real-world scale + base on y = 0 (critterfit.normalise), animals tagged with critterfit's rigid-part rig
(part id + weight per vertex, pivots), written as GLB with TEXCOORD_0 (albedo uv) and TEXCOORD_1 = (part id, weight).
Texture: the embedded 8192^2 JPEG, Lanczos-downscaled (2048 props, 1024 animals) with the UV islands dilated 16 px so mips and the
Tripo white padding never bleed into the shape.
Sources are read-only (never written): ~/Documents/SpiderMan_Asset_Import_M3_2026-10-08_task-4/GLBs/.
usage: prep_props_m3.py [--out DIR] [--only a,b]
"""
import argparse, io, json, os, struct, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(TOOLS, 'critterfit'))
sys.path.insert(0, os.path.join(TOOLS, 'crowdfit'))
sys.path.insert(0, os.path.join(TOOLS, 'skinfit'))
import critterfit  # noqa: E402  (tag_quadruped / tag_bird / normalise / PART)
from crowdfit import decimate  # noqa: E402

SRC = os.path.expanduser('~/Documents/SpiderMan_Asset_Import_M3_2026-10-08_task-4/GLBs')
OUT = os.path.expanduser('~/sm2-n1/_scratch/final/assets/prep')
# name -> source file (the textured copy of each pair, PLAN.md section 1), real size, LOD triangle targets, texture px, rig (critterfit manifest values)
ITEMS = {
    'oildrum':  dict(glb='blue+oil+drum+3d+model.glb', size={'h': 0.88}, lods=[2500, 700], tex=2048),
    'crate':    dict(glb='wooden+crate+3d+model (1).glb', size={'h': 0.64}, lods=[2000, 500], tex=2048),
    'pigeon':   dict(glb='pigeon+3d+model (1).glb', size={'l': 0.33}, lods=[1500, 400], tex=1024, desat=0.6, rig={'type': 'bird', 'head_u': 0.72, 'head_v': 0.6}),
    'gull':     dict(glb='seagull+3d+model (1).glb', size={'l': 0.58}, lods=[1500, 400], tex=1024, rig={'type': 'bird', 'head_u': 0.75, 'head_v': 0.62}),
    'cat':      dict(glb='orange+tabby+cat+3d+model (1).glb', size={'l': 0.58}, lods=[3000, 700], tex=1024,
                     rig={'type': 'quadruped', 'leg_v': 0.3, 'tail_u': 0.13, 'head_u': 0.8, 'head_v': 0.5}),
    'squirrel': dict(glb='squirrel+3d+model (1).glb', size={'l': 0.45}, lods=[2000, 500], tex=1024, yaw='-90:weld',
                     rig={'type': 'quadruped', 'leg_v': 0.25, 'tail_u': 0.4, 'head_u': 0.78, 'head_v': 0.3}),
    'rat':      dict(glb='rat+3d+model (1).glb', size={'l': 0.48}, lods=[1500, 400], tex=1024,
                     rig={'type': 'quadruped', 'leg_v': 0.3, 'tail_u': 0.42, 'head_u': 0.82, 'head_v': 0.2}),
}


def write_glb(path, P, N, UV0, UV1, F):
    """minimal GLB: one mesh, one primitive, no material (the UE build assigns its own)"""
    P = P.astype(np.float32); N = N.astype(np.float32); UV0 = UV0.astype(np.float32); UV1 = UV1.astype(np.float32)
    idx = F.astype(np.uint32).ravel()
    blobs = [P.tobytes(), N.tobytes(), UV0.tobytes(), UV1.tobytes(), idx.tobytes()]
    views, off, binb = [], 0, b''
    for b in blobs:
        views.append({'buffer': 0, 'byteOffset': off, 'byteLength': len(b)})
        binb += b + b'\0' * ((4 - len(b) % 4) % 4); off = len(binb)
    acc = [{'bufferView': 0, 'componentType': 5126, 'count': len(P), 'type': 'VEC3', 'min': P.min(0).tolist(), 'max': P.max(0).tolist()},
           {'bufferView': 1, 'componentType': 5126, 'count': len(N), 'type': 'VEC3'},
           {'bufferView': 2, 'componentType': 5126, 'count': len(UV0), 'type': 'VEC2'},
           {'bufferView': 3, 'componentType': 5126, 'count': len(UV1), 'type': 'VEC2'},
           {'bufferView': 4, 'componentType': 5125, 'count': len(idx), 'type': 'SCALAR'}]
    js = {'asset': {'version': '2.0', 'generator': 'sm2 prep_props_m3'}, 'scene': 0, 'scenes': [{'nodes': [0]}],
          'nodes': [{'mesh': 0, 'name': os.path.basename(path)[:-4]}],
          'meshes': [{'name': os.path.basename(path)[:-4], 'primitives': [{'attributes': {'POSITION': 0, 'NORMAL': 1, 'TEXCOORD_0': 2, 'TEXCOORD_1': 3}, 'indices': 4}]}],
          'accessors': acc, 'bufferViews': views, 'buffers': [{'byteLength': len(binb)}]}
    jb = json.dumps(js).encode(); jb += b' ' * ((4 - len(jb) % 4) % 4)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(jb) + 8 + len(binb)))
        f.write(struct.pack('<II', len(jb), 0x4E4F534A)); f.write(jb)
        f.write(struct.pack('<II', len(binb), 0x004E4942)); f.write(binb)


def dilated_texture(tex_bytes, UV, F, px, pad=16):
    """downscale + dilate: pixels outside every UV triangle take the colour of the nearest covered pixel"""
    im = Image.open(io.BytesIO(tex_bytes)).convert('RGB').resize((px, px), Image.LANCZOS)
    mask = Image.new('L', (px, px), 0); d = ImageDraw.Draw(mask)
    uv = np.clip(UV, 0, 1) * (px - 1)
    for a, b, c in F:
        d.polygon([tuple(uv[a]), tuple(uv[b]), tuple(uv[c])], fill=255)
    m = np.asarray(mask) > 0
    m = ndimage.binary_dilation(m, iterations=1)   # the triangle rasteriser undershoots edges by a texel
    a = np.asarray(im).copy()
    if (~m).any():
        _, (iy, ix) = ndimage.distance_transform_edt(~m, return_indices=True)
        a = a[iy, ix]   # every uncovered texel takes its nearest covered colour (no white / grey frames reach the mips)
    return Image.fromarray(a), float(m.mean())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default=OUT); ap.add_argument('--only', default='')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    meta = json.load(open(os.path.join(a.out, 'meta.json'))) if os.path.exists(os.path.join(a.out, 'meta.json')) else {}
    for name, it in ITEMS.items():
        if a.only and name not in a.only.split(','): continue
        src = os.path.join(SRC, it['glb'])
        with tempfile.TemporaryDirectory() as wd:
            lods, tex = decimate(src, wd, it['lods'], it.get('yaw', -90))
        norm = critterfit.normalise(lods[0][0], it['size'])
        rec = {'src': it['glb'], 'size_target': it['size'], 'lods': [], 'rig': (it.get('rig') or {}).get('type'), 'tex_px': it['tex']}
        for li, (P, N, UV, F) in enumerate(lods):
            P = norm(P)
            if it.get('rig'):
                part, w, piv = critterfit.TAGGERS[it['rig']['type']](P, it['rig'])
                if li == 0: rec['pivots_m'] = piv
            else:
                part, w = np.zeros(len(P)), np.zeros(len(P))
            UV1 = np.stack([part.astype(np.float32), w.astype(np.float32)], 1)
            write_glb(os.path.join(a.out, '%s_lod%d.glb' % (name, li)), P, N, UV, UV1, F)
            lo, hi = P.min(0), P.max(0)
            rec['lods'].append({'verts': int(len(P)), 'tris': int(len(F)), 'min': [round(float(v), 4) for v in lo], 'max': [round(float(v), 4) for v in hi],
                                'parts': {k: int((part == v).sum()) for k, v in critterfit.PART.items() if (part == v).any()} if it.get('rig') else {}})
            if li == 0:
                im, cov = dilated_texture(tex, UV, F, it['tex'])
                if it.get('desat'):   # Tripo's pigeon albedo is saturated blue-violet; rock pigeons read slate grey (the neck sheen stays faintly visible)
                    px = np.asarray(im).astype(np.float32); lum = px @ np.array([0.2126, 0.7152, 0.0722], np.float32)
                    px = px * (1 - it["desat"]) + lum[..., None] * it["desat"]; im = Image.fromarray(np.clip(px, 0, 255).astype(np.uint8))
                im.save(os.path.join(a.out, 'T_PropM3_%s_D.png' % name))
                rec['uv_coverage'] = round(cov, 3)
        rec['extent_m'] = [round(rec['lods'][0]['max'][i] - rec['lods'][0]['min'][i], 3) for i in range(3)]
        meta[name] = rec
        print(name, rec['extent_m'], [l['tris'] for l in rec['lods']], rec.get('pivots_m', ''), flush=True)
    json.dump(meta, open(os.path.join(a.out, 'meta.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
