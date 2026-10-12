#!/usr/bin/env python3
"""(r11) the pass-line numbers of a round folder in one table (r10 reference values from docs/night1/city/round-10): S4 T1 / T2 / T4 / C11-C15 (+ the critic's C13 box), S8 glass box, C1 / C2 / C4 / C6 counts.
usage: r11_numbers.py [round_dir (default docs/night1/city/round-11)]"""
import sys, os, json
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import s4_far_check as S, city_spec_check as C
R = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', 'docs', 'night1', 'city', 'round-11')
P = os.path.join(R, '..', 'round-10')
cfg = json.load(open(C.REGFILE))
def s4(path):
    r = S.analyse(path, cfg); L = {k: v['value'] for k, v in r['lines'].items()}; t4 = r['T4']
    return dict(T1=min(r['T1_std'].values()), T2=r['box_pct204'], T4_all=t4['flat_of_all_pct'], T4_bright=t4['flat_of_bright_pct'], bright_blocks=t4['bright'], C11=L['C11 lap/sky'], C11f=L['C11 flat8 %'], C12=L['C12 dBR'],
                C13=L['C13 far-sky Y'], C13_critic_box=r['C13_critic_box'], C14=L['C14 far-river Y'], C15=L['C15 rms far/near'], sky=r['sky_Y'], far=r['far_Y'], river=r['river_Y'])
def s8(path):
    im = cv2.imread(path); im = im if im.shape[1] == 1920 else cv2.resize(im, (1920, 1080), interpolation=cv2.INTER_AREA)
    Y = 0.2126 * im[:, :, 2] + 0.7152 * im[:, :, 1] + 0.0722 * im[:, :, 0]; b = Y[0:300, 1270:1640]; return dict(pct204=float((b > 204).mean() * 100), meanY=float(b.mean()))
rows = []
for tag, d in (('r10', P), ('r11', R)):
    f = os.path.join(d, 'S4_perch_skyline_1920x1080.jpg')
    if os.path.exists(f): rows.append((tag + ' 1080p', s4(f), s8(os.path.join(d, 'S8_aerial_midtown_1920x1080.jpg'))))
f4 = os.path.join(R, 'S4_perch_skyline_3840x2160.jpg')
if os.path.exists(f4): rows.append(('r11 4K->1080p', s4(f4), s8(os.path.join(R, 'S8_aerial_midtown_3840x2160.jpg'))))
keys = ['T1', 'T2', 'T4_all', 'T4_bright', 'bright_blocks', 'C11', 'C11f', 'C12', 'C13', 'C13_critic_box', 'C14', 'C15', 'sky', 'far', 'river']
print('%-16s' % 'frame' + ''.join('%9s' % k[:9] for k in keys) + '   S8 glass >204 %   mean Y')
for tag, a, b in rows: print('%-16s' % tag + ''.join('%9.2f' % a[k] for k in keys) + '   %8.2f %10.1f' % (b['pct204'], b['meanY']))
print('targets          T1 >= 12 | T2 <= 10 | T4 <= 10 (of all blocks; of bright blocks: critic wrote both) | C11 >= 6, flat <= 40 | C12 +-10 | C13 -35..-25 | C14 5..35 | C15 0.25..0.45 | S8 glass <= 1.5')
