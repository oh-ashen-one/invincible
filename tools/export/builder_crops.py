#!/usr/bin/env python3
"""Builder evidence crops of a round (4K frames), written to <round>/builder_checks/: the areas of the round's target (round 11: S4 far band / tower box, S8 upper glass, S3 board), so a reader sees the same pixels
the builder looked at. Crops are plain pixel copies (no annotation).   usage: builder_crops.py <round_dir> [out_dir]"""
import os, sys
from PIL import Image
R = sys.argv[1]; O = sys.argv[2] if len(sys.argv) > 2 else os.path.join(R, 'builder_checks'); os.makedirs(O, exist_ok=True)
CROPS = [  # name, 4K frame, x0, y0, x1, y1   (round 11: the critic r10 gap: the S4 far-shore towers; S8 upper glass; the S3 board caption)
 ('S4_far_band_4k', 'S4_perch_skyline', 0, 300, 2600, 600), ('S4_tower_box_4k', 'S4_perch_skyline', 1080, 220, 1800, 520), ('S4_shore_strip_4k', 'S4_perch_skyline', 900, 384, 2700, 472),
 ('S8_glass_upper_4k', 'S8_aerial_midtown', 2540, 0, 3280, 600),
 ('S3_board_4k', 'S3_rooftop_watertower', 200, 0, 1900, 2000),
]
for name, view, x0, y0, x1, y1 in CROPS:
    f = os.path.join(R, f'{view}_3840x2160.jpg')
    if not os.path.exists(f): print('missing', f); continue
    Image.open(f).convert('RGB').crop((x0, y0, x1, y1)).save(os.path.join(O, name + '.jpg'), quality=92); print(name)
