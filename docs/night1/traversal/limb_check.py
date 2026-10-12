# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 round 18: the critic r17 "alive limbs" test. In every trick window (flip_t >= 0, telemetry sampled every 6th frame = 0.1 s at 60 fps)
# at least one limb_z component must change by >= 0.10 between consecutive samples. Also reports the critic's pose.py still count
# (pose_sig norm < .06 per 0.1 s).   python3 limb_check.py <round dir> [clip prefix ...]
import csv, glob, os, sys, math

def check(path, thr=0.10):
    T = list(csv.DictReader(open(path)))
    rows = [r for i, r in enumerate(T) if i % 6 == 0 and float(r['flip_t'] or -1) >= 0]
    fails, still, n = [], [], 0
    for a, b in zip(rows, rows[1:]):
        za = [float(x) for x in a['limb_z'].split()]; zb = [float(x) for x in b['limb_z'].split()]
        d = max(abs(x - y) for x, y in zip(za, zb)); n += 1
        if d < thr: fails.append((float(a['t']), round(d, 3), a['flip_shape'], a['flip_prog']))
        pa = [float(x) for x in a['pose_sig'].split()]; pb = [float(x) for x in b['pose_sig'].split()]
        ds = math.sqrt(sum((x - y) ** 2 for x, y in zip(pa, pb)))
        if ds < 0.06: still.append((float(a['t']), round(ds, 3)))
    return n, fails, still

if __name__ == '__main__':
    R = sys.argv[1]; pre = sys.argv[2:] or ['f1', 'f2', 'f3', 'f4', 'f5']
    tot_n = tot_f = 0
    for p in pre:
        for f in sorted(glob.glob(os.path.join(R, p + '*_telemetry.csv'))):
            n, fails, still = check(f)
            tot_n += n; tot_f += len(fails)
            print('%-34s samples %3d  limb_z slow %2d  pose_sig still %d' % (os.path.basename(f), n, len(fails), len(still)))
            for x in fails: print('    slow  t %.2f  dmax %.3f  %s / %s' % x)
    print('TOTAL limb_z slow samples: %d of %d' % (tot_f, tot_n))
