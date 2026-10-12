# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""CPU preview of the round-08 suit: python3 preview.py TEXDIR OUTDIR [views]  (views: front back side three head headside)"""
import sys, os, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import meshio, softrender as sr


def load_tex(p, gamma=True):
    im = cv2.imread(p, cv2.IMREAD_COLOR)[..., ::-1].astype(np.float32) / 255
    return im ** 2.2 if gamma else im


def main():
    texdir, outdir = sys.argv[1], sys.argv[2]
    views = sys.argv[3:] or ['front', 'back']
    os.makedirs(outdir, exist_ok=True)
    m = meshio.load_body()
    bc = load_tex(texdir + '/suit_basecolor_r8.png')
    nm = None
    if os.path.exists(texdir + '/suit_normal_r8.png') and '--nonormal' not in sys.argv:
        nm = load_tex(texdir + '/suit_normal_r8.png', gamma=False)
    body = sr.Prim(m['P'], m['N'], m['F'], UV=m['UV'], tex=bc, nmap=nm, rough=0.7, spec=0.12, name='suit')
    prims = [body]
    extra = os.environ.get('LENS_GLB')
    if extra:
        import lens_io; prims += lens_io.prims_from_glb(extra)
    H = 1.0
    cams = {
        'front': ((0, 0.92, 4.2), (0, 0.92, 0), 26, (900, 1400)),
        'back': ((0, 0.92, -4.2), (0, 0.92, 0), 26, (900, 1400)),
        'side': ((4.2, 0.92, 0), (0, 0.92, 0), 26, (900, 1400)),
        'three': ((2.6, 1.15, 3.2), (0, 0.9, 0), 26, (1000, 1400)),
        'head': ((0, 1.66, 1.1), (0, 1.66, 0), 24, (1000, 1000)),
        'head3': ((0.55, 1.70, 0.95), (0, 1.66, 0), 22, (1000, 1000)),
        'headback': ((0.0, 1.68, -1.1), (0, 1.66, 0), 24, (1000, 1000)),
        'torso': ((0, 1.25, 1.6), (0, 1.25, 0), 24, (1100, 1100)),
        'torsoback': ((0, 1.25, -1.6), (0, 1.25, 0), 24, (1100, 1100)),
        'legs': ((1.2, 0.5, 2.2), (0, 0.5, 0), 26, (1000, 1000)),
        'arms': ((1.0, 1.15, 2.0), (0.25, 1.15, 0), 26, (1000, 1000)),
    }
    for v in views:
        if v.startswith('--'): continue
        eye, tgt, fov, (w, h) = cams[v]
        img = sr.render(prims, sr.look_at(eye, tgt), fov, w, h, ssaa=2)
        sr.save(img, '%s/%s.png' % (outdir, v))
        print('rendered', v)


if __name__ == '__main__':
    main()
