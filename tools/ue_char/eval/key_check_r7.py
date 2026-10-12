# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 07 chroma-key check on the stencil-keyed crowd stills (Char_CrowdKey: every pixel that is not a citizen is one flat key colour, the most frequent colour of the still, about (0, 217, 0) after the tonemapper;
citizen pixels are the normal, identically lit picture).

  python3 tools/ue_char/eval/key_check_r7.py STILL.png [...] --out DIR [--key auto|R,G,B] [--tol 6] [--iso 8]

Per still (all counts in px of the still; PNG, so no chroma bleed):
  key_exact_bg_px      pixels within --tol of the key colour (background + gaps)
  person_px            all other pixels = citizen pixels (exact: the keyer never touches them)
  g_dominant_person_px citizen pixels with G > R + 40 AND G > B + 40 (green dominant; teal / blue-green textures excluded)
  g_gt_r40_person_px   citizen pixels with G > R + 40 (the critic's test on garment silhouettes), and how many of them sit in clusters >= 50 px (`clusters`: bbox, px, mean BGR,
                       so a green plaid or a teal top can be told apart from a tinted / see-through region)
  enclosed_key         key-coloured pixels enclosed by citizen pixels (holes of the filled person mask), component by component: bbox, px, width (2 x inscribed radius), and `thin`
                       (an opening of 7 px removes it) - a thin enclosed component is a crack, a wide one is the air between limbs / walkers
  detached             citizen-pixel components of 5 .. 3000 px that do not touch (within --iso px) any other citizen pixel and not the image edge: a polygon floating in the air
  fringe_px            citizen pixels within 1 px of key with G > R + 40 that are NOT in a >= 50 px cluster: 1-px anti-aliasing / motion fringe (reported, not counted as garment)
Writes DIR/<name>_check.json and DIR/<name>_check.png (overlay: red = enclosed key, magenta = detached, yellow = G>R+40 person clusters)."""
import sys, os, json
import numpy as np
import cv2
from scipy import ndimage

a = sys.argv[1:]
def opt(k, d):
    if k in a:
        i = a.index(k); v = a[i + 1]; del a[i:i + 2]; return v
    return d
out = opt('--out', '.'); keyarg = opt('--key', 'auto'); tol = int(opt('--tol', '6')); iso = int(opt('--iso', '8'))
os.makedirs(out, exist_ok=True)
tot = {}
for f in a:
    im = cv2.imread(f, cv2.IMREAD_COLOR); H, W = im.shape[:2]
    if keyarg == 'auto':      # the key colour = the most frequent exact colour of the still (the keyer paints one flat colour over >50 % of the image)
        flat = im.reshape(-1, 3)[::7]; u, c = np.unique(flat, axis=0, return_counts=True); KB = u[int(np.argmax(c))].astype(int)
    else:
        kk = [int(x) for x in keyarg.split(',')]; KB = np.array([kk[2], kk[1], kk[0]])
    d = im.astype(int); b, g, r = d[..., 0], d[..., 1], d[..., 2]
    keym = (np.abs(d - KB[None, None, :]).max(axis=2) <= tol)
    person = ~keym
    filled = ndimage.binary_fill_holes(person)
    holes = filled & ~person
    lh, nh = ndimage.label(holes)
    dist_in = ndimage.distance_transform_edt(holes)
    comps = []
    for i, sl in enumerate(ndimage.find_objects(lh), 1):
        m = lh[sl] == i; px = int(m.sum())
        if px < 4: continue
        width = float(2 * dist_in[sl][m].max())
        comps.append(dict(bbox=[int(sl[1].start), int(sl[0].start), int(sl[1].stop - sl[1].start), int(sl[0].stop - sl[0].start)], px=px, width_px=round(width, 1), thin=bool(width <= 7)))
    comps.sort(key=lambda c: -c['px'])
    # person components
    lp, npn = ndimage.label(person, structure=np.ones((3, 3), bool)); sz = np.bincount(lp.ravel())
    det = []
    for i, sl in enumerate(ndimage.find_objects(lp), 1):
        if not (5 <= sz[i] <= 3000): continue
        m = lp == i
        grow = ndimage.binary_dilation(m, structure=np.ones((3, 3), bool), iterations=iso)
        others = grow & person & ~m
        touches_edge = sl[1].start == 0 or sl[0].start == 0 or sl[1].stop == W or sl[0].stop == H        # a person cut by the frame edge is not floating
        if not others.any() and not touches_edge:
            det.append(dict(bbox=[int(sl[1].start), int(sl[0].start), int(sl[1].stop - sl[1].start), int(sl[0].stop - sl[0].start)], px=int(sz[i])))
    gr = person & (g > r + 40)
    gdom = person & (g > r + 40) & (g > b + 40)          # green-dominant: teal tops and blue-green textures drop out
    lgd, ngd = ndimage.label(gdom, structure=np.ones((3, 3), bool)); sgd = np.bincount(lgd.ravel())
    gdom_big = int(sgd[sgd >= 50].sum() - (sgd[0] if sgd.size and sgd[0] >= 50 else 0))
    lg, ng = ndimage.label(gr, structure=np.ones((3, 3), bool)); sg = np.bincount(lg.ravel())
    clusters = []; big = np.zeros_like(gr)
    for i, sl in enumerate(ndimage.find_objects(lg), 1):
        if sg[i] < 50: continue
        m = lg == i; big |= m
        mc = im[m].mean(axis=0)
        clusters.append(dict(bbox=[int(sl[1].start), int(sl[0].start), int(sl[1].stop - sl[1].start), int(sl[0].stop - sl[0].start)], px=int(sg[i]), mean_bgr=[int(x) for x in mc]))
    clusters.sort(key=lambda c: -c['px'])
    res = dict(image=os.path.basename(f), size=[W, H], key_bgr=[int(x) for x in KB], key_exact_bg_px=int(keym.sum()), person_px=int(person.sum()),
               bg_median_bgr=[int(x) for x in np.median(im[keym].reshape(-1, 3), axis=0)] if keym.any() else None,
               g_gt_r40_person_px=int(gr.sum()), g_gt_r40_in_clusters_px=int(big.sum()), fringe_px=int((gr & ~big).sum()), g_dominant_person_px=int(gdom.sum()), g_dominant_in_clusters_px=gdom_big, clusters=clusters[:12],
               enclosed_key_components=len(comps), enclosed_key_px=int(sum(c['px'] for c in comps)), enclosed_key_thin_components=int(sum(c['thin'] for c in comps)),
               enclosed_key_top=comps[:12], detached_components=len(det), detached=det[:20])
    base = os.path.splitext(os.path.basename(f))[0]
    json.dump(res, open(os.path.join(out, base + '_check.json'), 'w'), indent=1)
    vis = im.copy()
    vis[holes] = (0, 0, 255)
    vis[big] = (0, 255, 255)
    for c in det:
        x, y, w, h = c['bbox']; cv2.rectangle(vis, (x - 6, y - 6), (x + w + 6, y + h + 6), (255, 0, 255), 2)
    cv2.imwrite(os.path.join(out, base + '_check.png'), vis)
    print(json.dumps({k: v for k, v in res.items() if k not in ('clusters', 'enclosed_key_top', 'detached')}))
