#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Ranks the variants of a live-tuning sweep (capture_tour.py --variants ...): stills named <preset>_<S#>_<res>_<variant>.jpg in one folder.
For every variant it prints, per shot, mean Y / near-black % / clipped % / B-R and how many of the four LOOK-SPEC lines of the preset (look_spec_check.py: L1 / L2 / L3 / L5)
that shot passes, plus the S4 far-field lines (L10 / L11) and, for night, the street-level L13 / L14 lines. Same instrument as look_spec_check.py (imported).
usage: sweep_report.py --dir <stills dir> [--res 1920x1080] [--preset midday]"""
import argparse, glob, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import look_spec_check as L

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--dir', required=True); ap.add_argument('--res', default='1920x1080'); ap.add_argument('--preset', default='')
    a = ap.parse_args()
    rows = {}
    for f in sorted(glob.glob(os.path.join(a.dir, '*_%s_*.jpg' % a.res))):
        m = re.match(r'(midday|golden|night)_(S\d)_%s_(.+)\.jpg$' % a.res, os.path.basename(f))
        if not m or (a.preset and m.group(1) != a.preset): continue
        d = L.stats(f); v = L.verdict(os.path.basename(f), d)
        rows.setdefault((m.group(1), m.group(3)), {})[m.group(2)] = (d, v)
    for (pre, var), shots in sorted(rows.items()):
        tot = ok = 0; cells = []
        for sid in sorted(shots):
            d, v = shots[sid]
            w = v[1] if v else {}
            n = sum(1 for k in w if w[k]); tot += len(w); ok += n
            cells.append('%s Y%.0f nb%.2f cl%.2f BR%+.0f [%d/%d]' % (sid, d['mean'], d['near_black_pct'], d['clipped_pct'], d['b_minus_r'], n, len(w)))
        extra = []
        s4 = shots.get('S4')
        if s4 and 'far' in s4[0]:
            f = s4[0]['far']; dy = f['far_shore']['Y'] - f['sky']['Y']; dbr = f['far_shore']['BR'] - f['sky']['BR']; hz = f['horizon_far']['Y'] - f['sky']['Y']
            extra.append('L10 dY %+.1f%s dBR %+.1f%s' % (dy, '' if -32 <= dy <= -15 else '!', dbr, '' if abs(dbr) <= 10 else '!'))
            if pre == 'midday': extra.append('L11 %+.1f%s' % (hz, '' if hz >= 3 else '!'))
        for sid in ('S1', 'S5', 'S6'):
            if pre == 'night' and sid in shots:
                d = shots[sid][0]; extra.append('%s L13 %d%s L14 p10 %.0f%s p90 %.0f%s' % (sid, d['lit_blobs_bottom_half'], '' if d['lit_blobs_bottom_half'] >= 5 else '!', d['bottom_third_p10'], '' if 15 <= d['bottom_third_p10'] <= 30 else '!',
                                                                                     d['bottom_third_p90'], '' if d['bottom_third_p90'] >= 100 else '!'))
        print('== %s %-12s passes %d/%d' % (pre, var, ok, tot))
        for c in cells: print('   ' + c)
        for e in extra: print('   ' + e)

if __name__ == '__main__':
    main()
