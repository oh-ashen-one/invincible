#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Island r04: where do two route telemetries (same script, fixed 1/60 s step) part? Frame-by-frame 3D distance of the hero position.
usage: island_traj_diff.py <a.csv> <b.csv> [label]  -> one JSON line: frames, max_m, first frame / t with > 0.01 m, > 0.5 m, > 3 m, positions there"""
import csv, json, math, sys


def load(p):
    return [(float(r['t']), float(r['x_m']), float(r['y_m']), float(r['z_m']), r['mode'], r['sub']) for r in csv.DictReader(open(p))]


def main():
    a, b = load(sys.argv[1]), load(sys.argv[2])
    n = min(len(a), len(b))
    d = [math.dist(a[i][1:4], b[i][1:4]) for i in range(n)]
    out = {'label': sys.argv[3] if len(sys.argv) > 3 else '', 'a': sys.argv[1], 'b': sys.argv[2], 'frames': n, 'max_m': round(max(d), 3) if d else None}
    for th in (0.01, 0.5, 3.0):
        k = next((i for i, v in enumerate(d) if v > th), None)
        out['first_gt_%g' % th] = None if k is None else {'frame': k, 't': round(a[k][0], 3), 'a': [round(v, 2) for v in a[k][1:4]] + list(a[k][4:]), 'b': [round(v, 2) for v in b[k][1:4]] + list(b[k][4:])}
    print(json.dumps(out))


if __name__ == '__main__':
    main()
