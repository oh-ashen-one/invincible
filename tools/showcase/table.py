#!/usr/bin/env python3
"""compact ours/ref table of a pairs.json: table.py <run dir> [<run dir> ...]"""
import json
import sys
from pathlib import Path

for run in sys.argv[1:]:
    d = json.loads((Path(run) / 'pairs.json').read_text())
    print(run)
    print('%-26s %7s %7s %7s %7s %7s %7s %7s' % ('shot', 'sky_t3', 'probe', 'fac_mn', 'fac_md', 'street', 'litfrac', 'mean'))
    for n, v in d.items():
        r = v['ratio_ours_over_ref']
        print('%-26s %7.2f %7.2f %7.2f %7.2f %7.2f %7.2f %7.2f' % (n, r['sky_top_third'], r['sky_probe'] or 0, r['facade_mid_third'], r['facade_mid_median'], r['street_bottom_third'], r['lit_fraction_mid_gt_0.1'], r['mean']))
