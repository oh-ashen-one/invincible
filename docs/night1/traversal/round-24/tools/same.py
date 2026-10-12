#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game. r24: does a -nullrhi probe reproduce a captured clip's path and camera?
import csv, sys
a = list(csv.DictReader(open(sys.argv[1]))); b = list(csv.DictReader(open(sys.argv[2])))
n = min(len(a), len(b)); m = 0.0
for x, y in zip(a[:n], b[:n]):
    for k in ('x_m', 'y_m', 'z_m', 'cam_x', 'cam_y', 'cam_z'):
        m = max(m, abs(float(x[k]) - float(y[k])))
print('SAME' if m < 0.01 else 'DIFF', f'{m:.3f}', n)
