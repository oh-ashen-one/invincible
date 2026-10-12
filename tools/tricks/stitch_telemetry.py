# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Tricks C r01: one telemetry CSV for a reel rendered in windows (capture.sh SEGS). Every window's run simulates the whole sequence, but
# the pixel-readback columns (px_*, hero_occl, ...) are only valid where that run rendered, so rows with t in [A_k, B_k) are taken from
# window k's run. The simulation columns are identical across the runs (capture.sh prints the determinism line); this script re-checks
# position / flip state on every row it swaps in.
#   python3 tools/tricks/stitch_telemetry.py <capture dir (seg0..)> <name> <SEGS e.g. 0:15,15:30> <out.csv>
import csv, sys

D, NAME, SEGS, OUT = sys.argv[1:5]
segs = [tuple(float(x) for x in s.split(':')) for s in SEGS.split(',')]
runs = [list(csv.DictReader(open('%s/seg%d/%s_telemetry.csv' % (D, k, NAME)))) for k in range(len(segs))]
ref = runs[-1]
cols = list(ref[0].keys())
key = ('x_m', 'y_m', 'z_m', 'flip_prog', 'flip_t')
out, bad = [], 0
for i, r in enumerate(ref):
    t = float(r['t'])
    k = next((j for j, (a, b) in enumerate(segs) if a - 1e-4 <= t < b - 1e-4), len(segs) - 1)
    src = runs[k][i] if i < len(runs[k]) else r
    if tuple(src[c] for c in key) != tuple(r[c] for c in key): bad += 1
    out.append(src)
w = csv.DictWriter(open(OUT, 'w', newline=''), fieldnames=cols)
w.writeheader()
for r in out: w.writerow(r)
print('stitched %d rows from %d windows; rows whose position / flip state differ from the last run: %d' % (len(out), len(segs), bad))
