#!/usr/bin/env python3
"""(r11) evidence image for the S4 far-band tests: pixels above Y 204 in red, the T2 box (0,150,1300,300) green, the T4 box (540,110,900,260) cyan, bright flat 8x8 blocks of the T4 box yellow.
usage: s4_mask.py <frame> <out.png>   (any resolution, reduced to 1920x1080)"""
import sys, cv2, numpy as np
im = cv2.imread(sys.argv[1]); im = im if im.shape[1] == 1920 else cv2.resize(im, (1920, 1080), interpolation=cv2.INTER_AREA)
Y = 0.2126 * im[:, :, 2] + 0.7152 * im[:, :, 1] + 0.0722 * im[:, :, 0]
v = im.copy(); v[Y > 204] = (0, 0, 255)
x0, y0, x1, y1 = 540, 110, 900, 260
for y in range(y0, y1 - 7, 8):
    for x in range(x0, x1 - 7, 8):
        b = Y[y:y + 8, x:x + 8]
        if b.mean() > 200 and b.std() < 3: cv2.rectangle(v, (x, y), (x + 7, y + 7), (0, 255, 255), -1)
cv2.rectangle(v, (0, 150), (1300, 300), (0, 255, 0), 1); cv2.rectangle(v, (x0, y0), (x1, y1), (255, 255, 0), 1)
cv2.imwrite(sys.argv[2], v[60:340, 0:1500]); print(sys.argv[2])
