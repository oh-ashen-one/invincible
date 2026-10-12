#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Owner swatch sheet of all hero suits, composed from the 4K ENGINE stills (front, back, chest) of the round: one panel per suit with its name, concept line and palette chips.

  python3 tools/ue_char/suits/swatch_sheet.py STILLS_DIR OUT.jpg [--cols 4]
STILLS_DIR holds skin_<id>_{front,back,chest,head}_4k.jpg (chain_r11.sh); the order and names come from tools/ue_char/suits/suits.json.
"""
import sys, os, json
import numpy as np
import cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'suit8'))
import design  # noqa: E402


def crop_center(im, w_frac_of_h, out_w, out_h):
    h, w = im.shape[:2]
    cw = int(h * w_frac_of_h); x0 = max(0, (w - cw) // 2)
    return cv2.resize(im[:, x0:x0 + cw], (out_w, out_h), interpolation=cv2.INTER_AREA)


def main():
    d, out = sys.argv[1], sys.argv[2]
    cols = int(sys.argv[sys.argv.index('--cols') + 1]) if '--cols' in sys.argv else 4
    cfg = json.load(open(os.path.join(HERE, 'suits.json')))
    H = 780; WF, WB, WC = 360, 360, 640
    panels = []
    for e in cfg['suits']:
        sid = e['id']
        row = []
        for v, (fw, ow) in (('front', (0.46, WF)), ('back', (0.46, WB)), ('chest', (0.82, WC)), ('head', (0.667, 520))):      # round 13: + the sculpted head
            p = os.path.join(d, 'skin_%s_%s_4k.jpg' % (sid, v))
            if os.path.exists(p): row.append(crop_center(cv2.imread(p), fw, ow, H))
            else: row.append(np.full((H, ow, 3), 40, np.uint8))
        body = np.concatenate(row, 1)
        pal = design.resolve(e.get('style'))['palette']
        lab = np.full((92, body.shape[1], 3), 22, np.uint8)
        cv2.putText(lab, '%s' % e.get('name', sid).upper(), (14, 34), cv2.FONT_HERSHEY_DUPLEX, 1.0, (235, 235, 235), 1, cv2.LINE_AA)
        cv2.putText(lab, e.get('concept', '')[:78], (14, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (170, 170, 170), 1, cv2.LINE_AA)
        for i, k in enumerate(('body', 'deep', 'accent', 'accent_d', 'stitch')):
            c = design.srgb(pal[k]); x0 = body.shape[1] - 14 - (5 - i) * 34
            cv2.rectangle(lab, (x0, 14), (x0 + 28, 42), tuple(int(v * 255) for v in c[::-1]), -1)
        panels.append(np.concatenate([lab, body], 0))
    rows = []
    for i in range(0, len(panels), cols):
        r = panels[i:i + cols]
        while len(r) < cols: r.append(np.full_like(panels[0], 22))
        rows.append(np.concatenate([np.pad(p, ((0, 0), (0, 6), (0, 0)), constant_values=12) for p in r], 1))
    sheet = np.concatenate(rows, 0)
    cv2.imwrite(out, sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
    print('swatch sheet', out, sheet.shape)


if __name__ == '__main__':
    main()
