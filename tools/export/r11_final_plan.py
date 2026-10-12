#!/usr/bin/env python3
"""(r11) writes the plan files of the final capture holds for tools/export/r11_plan.sh: 8 views at 1080p (auto screen percentage, perf window 26:38) and 8 views at 3840x2160 with r.ScreenPercentage 100 (native internal).
usage: r11_final_plan.py <out_dir>   -> <out_dir>/final_1080.txt, final_4k.txt"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ids = [s['id'] for s in json.load(open(os.path.join(HERE, '..', '..', 'unreal', 'WebHomage', 'Scripts', 'city_shots.json')))]
o = sys.argv[1]; os.makedirs(o, exist_ok=True)
open(os.path.join(o, 'final_1080.txt'), 'w').write('# final 1080p set (internal 1399x787 at auto screen percentage)\n' + ''.join('cap f1080 %s\n' % i for i in ids))
open(os.path.join(o, 'final_4k.txt'), 'w').write('# final native-4K set (r.ScreenPercentage 100: internal 3840x2160)\n' + ''.join('cap f4k %s 3840x2160 100\n' % i for i in ids))
print(ids)
