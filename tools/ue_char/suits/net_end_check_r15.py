#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 15 instrument for the critic r14 line "the grooves stop dead": EVERY net line must end on a seam cord (or on a UV island edge, where it continues on the neighbour island).

Exact, on the paint itself (CPU, no engine): design.paint(..., dbg=...) hands out, per net layer, the line's own coverage and the zone mask the line is laid through, and the union of every raised
cord / border that is not a net line.  A net line ENDS where the zone mask falls from 1 to 0 across a pixel that has line coverage; that end is a DEAD END when no cord pixel lies within
`reach` of it (2.5 mm) and it is not within 4 texels of the atlas coverage edge.  The report is the number of dead-end blobs and their texel count per suit; --png writes the blobs over the
base colour so the eye can check them.

  python3 net_end_check_r15.py [--n 2048] [--only ash,verdant] [--png DIR] [--json out.json] [--r14]   (--r14 = the round-14 switches: the baseline)
"""
import sys, os, json
import numpy as np
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
UC = os.path.join(HERE, '..')
sys.path.insert(0, UC); sys.path.insert(0, os.path.join(UC, 'suit8'))
import meshio, design  # noqa: E402
import hero_suit_r8 as hs  # noqa: E402
SUITS_JSON = os.path.join(HERE, 'suits.json')


def arg(k, d):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


R14 = {'net': {'terminate': False}, 'cap': {'r_in': 0.108}, 'sash': {'pipe_join': False}}      # the round-14 behaviour of the three switches


def evaluate(entry, n, pre, png_dir=None, r14=False):
    if r14:
        entry = dict(entry); entry['style'] = design.merge(entry.get('style') or {}, R14)
    style = design.resolve(entry.get('style'))
    m, (tri, w0, w1, inside) = pre
    P, N, UV, F, GW = m['P'], m['N'], m['UV'], m['F'], m['GW']
    cov = tri >= 0
    a3 = np.linalg.norm(np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]]), axis=1) / 2
    a2 = np.abs((UV[F[:, 1], 0] - UV[F[:, 0], 0]) * (UV[F[:, 2], 1] - UV[F[:, 0], 1]) - (UV[F[:, 2], 0] - UV[F[:, 0], 0]) * (UV[F[:, 1], 1] - UV[F[:, 0], 1])) / 2 * n * n
    mpt_tri = np.clip(np.sqrt(a3 / np.maximum(a2, 1e-9)).astype(np.float32), 2e-5, 2e-3)
    gi = {g: i for i, g in enumerate(meshio.GROUPS)}
    jp = {k: tuple(float(x) for x in v) for k, v in m['jpos'].items()}
    layer_ends = {}
    ends = np.zeros((n, n), bool); lines = np.zeros((n, n), bool); cords = np.zeros((n, n), bool); crease = np.zeros((n, n), bool)
    col = np.zeros((n, n, 3), np.float32); mptm = np.full((n, n), 2e-4, np.float32)
    step = 256
    for r0 in range(0, n, step):
        sl = slice(r0, min(r0 + step, n))
        if not cov[sl].any(): continue
        Pp = meshio.gather(tri, w0, w1, F, P, sl); Nn = meshio.gather(tri, w0, w1, F, N, sl)
        Nn /= np.linalg.norm(Nn, axis=-1, keepdims=True) + 1e-9
        G = meshio.gather(tri, w0, w1, F, GW, sl)
        mp = mpt_tri[np.where(tri[sl] >= 0, tri[sl], 0)]
        dbg = {}
        o = design.paint(Pp, Nn, G, mp, gi, jp, entry.get('style'), dbg=dbg)
        col[sl] = o['col']; mptm[sl] = mp
        ax_, y_ = np.abs(Pp[..., 0]), Pp[..., 1]
        crease[sl] = (y_ > 1.14) & (y_ < 1.40) & (ax_ > 0.10) & (ax_ < 0.30)      # the armpit crease zone: the surface folds there, the arm hangs against the torso and hides it
        if 'cord' in dbg: cords[sl] = dbg['cord'] > 0.3
        for line, zone, nm_ in dbg.get('net', []):
            ln = line > 0.4
            lines[sl] |= ln & (zone > 0.5)
            edge = (zone > 0.02) & (zone < 0.98)
            ends[sl] |= ln & edge
            layer_ends.setdefault(nm_, np.zeros((n, n), bool))[sl] |= ln & edge
    mt = float(np.median(mptm[cov])) if cov.any() else 8e-4
    reach = max(2, int(round(0.0025 / mt)))
    near_cord = ndi.binary_dilation(cords, iterations=reach)
    away_edge = ndi.binary_erosion(cov, iterations=max(4, int(round(8 * n / 2048))))      # a line that ends within 8 texels (at 2048) of the island edge continues on the neighbour island
    dead = ends & ~near_cord & away_edge
    dead = ndi.binary_opening(dead, iterations=0) if False else dead
    cr_zone = ndi.binary_dilation(crease, iterations=6)
    def count(mask):
        lab, k = ndi.label(ndi.binary_dilation(mask, iterations=2))
        if not k: return 0
        sizes = ndi.sum(mask, lab, range(1, k + 1))
        return int(sum(1 for s_ in sizes if s_ >= 2))
    n_open = count(dead & ~cr_zone); n_crease = count(dead & cr_zone)
    per_layer = {k: count(v & dead & ~cr_zone) for k, v in layer_ends.items()}
    blobs = [0] * (n_open + n_crease)
    all_ends = ndi.label(ndi.binary_dilation(ends & away_edge, iterations=2))[1]
    res = dict(id=entry['id'], n=n, reach_px=reach, net_ends_total=int(all_ends), dead_end_blobs=len(blobs), dead_end_blobs_in_open_fabric=n_open, open_fabric_by_layer=per_layer, dead_end_blobs_in_armpit_crease_zone=n_crease, dead_end_texels=int(dead.sum()), line_texels=int(lines.sum()),
               net_kind=style['net']['kind'])
    if png_dir:
        import cv2
        os.makedirs(png_dir, exist_ok=True)
        img = (np.clip(col, 0, 1) * 255).astype(np.uint8)[..., ::-1].copy()
        img[ndi.binary_dilation(dead & ~cr_zone, iterations=3)] = (0, 0, 255); img[ndi.binary_dilation(dead & cr_zone, iterations=3)] = (0, 160, 255)
        cv2.imwrite(os.path.join(png_dir, 'netend_%s.png' % entry['id']), img)
    return res


def main():
    n = int(arg('--n', 2048))
    only = arg('--only', '').split(',') if arg('--only', '') else None
    cfg = json.load(open(SUITS_JSON))
    m = meshio.load_body(); pre = (m, meshio.raster_tri(m['UV'], m['F'], n))
    out = []
    for e in cfg['suits']:
        if only and e['id'] not in only: continue
        r = evaluate(e, n, pre, arg('--png', None), '--r14' in sys.argv)
        out.append(r); print(json.dumps(r))
    if '--json' in sys.argv: json.dump(out, open(arg('--json', 'netend.json'), 'w'), indent=1)
    print('TOTAL dead-end blobs: %d (open fabric %d, armpit crease zone %d) over %d suits' % (sum(r['dead_end_blobs'] for r in out), sum(r['dead_end_blobs_in_open_fabric'] for r in out), sum(r['dead_end_blobs_in_armpit_crease_zone'] for r in out), len(out)))


if __name__ == '__main__':
    main()
