#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""CPU swatch sheet of the generated suits (design aid, rest pose, simple sun + sky shading; the owner sheet is made from ENGINE captures by swatch_sheet.py).

  python3 tools/ue_char/suits/swatch_cpu.py MAPS_DIR OUT.jpg [--ids a,b] [--views front,three,back] [--h 760] [--cols 4]
MAPS_DIR holds <id>_basecolor.png / <id>_normal.png (gen_suits.py output).
"""
import sys, os, json
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'suit8')); sys.path.insert(0, os.path.join(HERE, '..'))
import meshio, softrender as sr  # noqa: E402

CAMS = {
    'front': ((0, 0.92, 4.2), (0, 0.92, 0), 26),
    'back': ((0, 0.92, -4.2), (0, 0.92, 0), 26),
    'side': ((4.2, 0.92, 0), (0, 0.92, 0), 26),
    'three': ((2.6, 1.15, 3.2), (0, 0.9, 0), 26),
    'torso': ((0, 1.25, 1.6), (0, 1.25, 0), 24),
    'head': ((0.55, 1.70, 0.95), (0, 1.66, 0), 22),
    'headfront': ((0, 1.66, 1.1), (0, 1.66, 0), 24),
}


def load_tex(p, gamma=True):
    im = cv2.imread(p, cv2.IMREAD_COLOR)[..., ::-1].astype(np.float32) / 255
    return im ** 2.2 if gamma else im


def render_suit(mesh, maps, sid, view, w, h, lens=None, use_normal=True):
    bc = load_tex('%s/%s_basecolor.png' % (maps, sid))
    nmp = '%s/%s_normal.png' % (maps, sid)
    nm = load_tex(nmp, gamma=False) if use_normal and os.path.exists(nmp) else None
    body = sr.Prim(mesh['P'], mesh['N'], mesh['F'], UV=mesh['UV'], tex=bc, nmap=nm, rough=0.7, spec=0.12, name='suit')
    prims = [body] + (lens or [])
    eye, tgt, fov = CAMS[view]
    return sr.render(prims, sr.look_at(eye, tgt), fov, w, h, ssaa=2)


def main():
    maps, out = sys.argv[1], sys.argv[2]
    a = sys.argv
    ids = a[a.index('--ids') + 1].split(',') if '--ids' in a else None
    views = a[a.index('--views') + 1].split(',') if '--views' in a else ['front', 'three', 'back']
    H = int(a[a.index('--h') + 1]) if '--h' in a else 760
    cols = int(a[a.index('--cols') + 1]) if '--cols' in a else 4
    if ids is None:
        ids = sorted(f[:-len('_basecolor.png')] for f in os.listdir(maps) if f.endswith('_basecolor.png'))
        order = [s['id'] for s in json.load(open(os.path.join(HERE, 'suits.json')))['suits']]
        ids = [i for i in order if i in ids]
    m = meshio.load_body()
    lens = None
    if os.environ.get('LENS_GLB'):
        import lens_io; lens = lens_io.prims_from_glb(os.environ['LENS_GLB'])
    W = int(H * 0.62)
    panels = []
    for sid in ids:
        vs = []
        for v in views:
            vw, vh = (W, H) if v in ('front', 'back', 'side', 'three') else (H, H)
            im = render_suit(m, maps, sid, v, vw, vh, lens)
            vs.append((im * 255).astype(np.uint8)[..., ::-1])
        row = np.concatenate(vs, 1)
        lab = np.full((46, row.shape[1], 3), 24, np.uint8)
        cv2.putText(lab, sid.upper(), (14, 33), cv2.FONT_HERSHEY_DUPLEX, 0.95, (230, 230, 230), 1, cv2.LINE_AA)
        panels.append(np.concatenate([lab, row], 0))
    rows = []
    for i in range(0, len(panels), cols):
        r = panels[i:i + cols]
        while len(r) < cols: r.append(np.full_like(panels[0], 24))
        rows.append(np.concatenate(r, 1))
    sheet = np.concatenate(rows, 0)
    cv2.imwrite(out, sheet, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print('swatch', out, sheet.shape)


if __name__ == '__main__':
    main()
