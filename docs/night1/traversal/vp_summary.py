#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Summary of specs/tools/vp_cam.py output (TRAVERSAL-SPEC T11-T14), same statistics as the round-09 critic (vpsum.py).
# usage: vp_summary.py <label>_cam.csv [t0 t1]
import csv, sys, numpy as np
f = sys.argv[1]; T0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0; T1 = float(sys.argv[3]) if len(sys.argv) > 3 else 1e9
R = [r for r in csv.DictReader(open(f)) if T0 <= float(r['t']) <= T1]
def col(k): return np.array([float(r[k]) for r in R if r.get(k) not in (None, '')])
p = col('pitch_down_deg'); y = np.abs(col('yaw_off_deg')); ro = np.abs(col('roll_deg')); fv = col('hfov_deg')
print(f, 'n', len(R))
if len(p): print(' T11 pitch down p5/50/95 %.1f/%.1f/%.1f (n %d)' % (*np.percentile(p, [5, 50, 95]), len(p)))
if len(y): print(' T12 yaw off p50/90 %.1f/%.1f' % tuple(np.percentile(y, [50, 90])))
if len(ro): print(' T13 |roll| p50/90/max %.1f/%.1f/%.1f' % (np.median(ro), np.percentile(ro, 90), ro.max()))
if len(fv): print(' T14 hfov p25/50/75 %.0f/%.0f/%.0f' % tuple(np.percentile(fv, [25, 50, 75])))
