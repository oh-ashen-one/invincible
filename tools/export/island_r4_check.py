#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Island piece (A), round 02: critic test 2 on r4 (wall-run / roofs). After the perch the script sprints along the roof (t >= RUN_T) toward a
parapet; the run must END in a stop or a vault at the parapet (not pass through it), and the first touchdown after the jump / drop must be on a
drawn surface (fire escape, roof, street) within 0.45 m.

    python3 tools/export/island_r4_check.py <export_dir> <r4_telemetry.csv> [--run-t 11.0] [--out report.json]"""
import csv, json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from island_route_check import Drawn, BODY_H


def main():
    a = sys.argv[1:]
    out = None; run_t = 11.0
    if '--out' in a: i = a.index('--out'); out = a[i + 1]; del a[i:i + 2]
    if '--run-t' in a: i = a.index('--run-t'); run_t = float(a[i + 1]); del a[i:i + 2]
    E, path = a
    D = Drawn(E)
    rows = [r for r in csv.DictReader(open(path))]
    f = lambda r, k: float(r[k]) if r.get(k) not in (None, '') else 0.0
    seg = [r for r in rows if f(r, 't') >= run_t]
    # the roof run: from the first ground frame above 10 m (t >= run_t) to the run's end = a vault / climb sub-state, a stop (speed < 1 m/s with
    # the stick held), or the last roof frame before the hero drops more than 2 m below the run level
    i0 = next((i for i, r in enumerate(seg) if r['mode'] == 'ground' and f(r, 'z_m') - BODY_H > 10.0), None)
    rep = {'csv': os.path.basename(path), 'run_t': run_t}
    if i0 is not None:
        zr = f(seg[i0], 'z_m') - BODY_H; end = None; reason = None
        for i in range(i0, len(seg)):
            r = seg[i]; z = f(r, 'z_m') - BODY_H; sub = r['sub'].lower()
            if any(k in sub for k in ('vault', 'mantle', 'climb', 'topout')): end, reason = i, 'vault (%s)' % r['sub']; break
            if r['mode'] == 'ground' and i > i0 + 5 and f(r, 'hspeed_mps') < 1.0 and abs(f(r, 'in_move_y')) + abs(f(r, 'in_move_x')) > 0.2: end, reason = i, 'stop'; break
            if r['mode'] in ('ground', 'land', 'perch') and z > 10.0: zr = min(zr, z)
            if z < zr - 5.0 and r['mode'] == 'air': end, reason = i, 'left the roof (fall / jump, no vault)'; break   # a step down to a lower roof (< 5 m) is part of the run
        run = seg[i0:end if end is not None else len(seg)]
        ovl = [(round(f(r, 't'), 3), D.overlap(f(r, 'x_m'), f(r, 'y_m'), f(r, 'z_m') - BODY_H)) for r in run]
        ovl = [o for o in ovl if o[1]]
        last = seg[end] if end is not None else run[-1]
        rep.update({'run_t0': f(seg[i0], 't'), 'run_end_t': f(last, 't'), 'run_start': [f(seg[i0], 'x_m'), f(seg[i0], 'y_m'), round(f(seg[i0], 'z_m') - BODY_H, 2)],
                    'run_end': [f(last, 'x_m'), f(last, 'y_m'), round(f(last, 'z_m') - BODY_H, 2)], 'run_end_reason': reason,
                    'run_subs': sorted(set(r['sub'] for r in run)), 'overlap_frames_during_run': len(ovl), 'overlap_examples': ovl[:5]})
        rep['run_pass'] = bool(reason and (reason.startswith('vault') or reason == 'stop') and not ovl)
        # the drop after the run: first touchdown (land / ground / perch / wall) >= 2 m below the run end
        after = seg[(end or len(seg) - 1):]
        zend = f(last, 'z_m') - BODY_H; td = None
        for r in after:
            if r['mode'] in ('land', 'ground', 'perch', 'wall') and f(r, 'z_m') - BODY_H < zend - 2.0: td = r; break
        thru = []; prev = None
        for r in after:
            x, y, z = f(r, 'x_m'), f(r, 'y_m'), f(r, 'z_m') - BODY_H
            if prev is not None and z < prev[2]:
                idx = D.near(x, y)
                if idx.size:
                    S = D.S[idx]; kk = D.k[idx]
                    m = (S[:, 0] - 0.2 <= x) & (x <= S[:, 3] + 0.2) & (S[:, 1] - 0.2 <= y) & (y <= S[:, 4] + 0.2) & (S[:, 5] <= prev[2] + 0.05) & (S[:, 5] > z + 0.1)
                    m &= np.isin(kk, ('fireescape', 'fireescape_kit', 'roof', 'wall', 'coping', 'parapet', 'ledge', 'cornice', 'equipment', 'bulkhead'))
                    for i in np.nonzero(m)[0][:3]: thru.append([round(f(r, 't'), 3), str(kk[i]), round(float(S[i, 5]), 2)])
            prev = (x, y, z)
            if td is not None and r is td: break
        rep['fell_through_platforms'] = thru[:20]
        if td is not None:
            x, y, z = f(td, 'x_m'), f(td, 'y_m'), f(td, 'z_m') - BODY_H
            what, dz = D.support(x, y, z, tol=0.45)
            rep['drop_touchdown'] = {'t': f(td, 't'), 'mode': td['mode'], 'sub': td['sub'], 'feet': [x, y, round(z, 2)], 'surface': what, 'dz_m': round(dz, 3),
                                     'on_drawn_surface': what is not None, 'on_fireescape_or_roof': what not in (None, 'street'), 'no_pass_through': not thru}
    if out: json.dump(rep, open(out, 'w'), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
