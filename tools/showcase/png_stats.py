#!/usr/bin/env python3
"""Pure-python PNG luminance stats (8-bit RGB / RGBA, no dependencies): mean sRGB luma overall and per horizontal third (sky = top third), plus the 5/50/95 % luma of each third.
usage: png_stats.py image.png [...]"""
import json
import struct
import sys
import zlib


def decode(path):
    d = open(path, 'rb').read()
    assert d[:8] == b'\x89PNG\r\n\x1a\n'
    pos, idat, ihdr = 8, b'', None
    while pos < len(d):
        n, t = struct.unpack('>I4s', d[pos:pos + 8])
        body = d[pos + 8:pos + 8 + n]
        if t == b'IHDR':
            ihdr = struct.unpack('>IIBBBBB', body)
        elif t == b'IDAT':
            idat += body
        pos += 12 + n
    w, h, depth, ctype = ihdr[:4]
    assert depth == 8 and ctype in (2, 6), (depth, ctype)
    bpp = 3 if ctype == 2 else 4
    raw = zlib.decompress(idat)
    stride = w * bpp
    rows, prev = [], bytearray(stride)
    p = 0
    for _ in range(h):
        f = raw[p]; line = bytearray(raw[p + 1:p + 1 + stride]); p += 1 + stride
        if f == 1:
            for i in range(bpp, stride): line[i] = (line[i] + line[i - bpp]) & 255
        elif f == 2:
            for i in range(stride): line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride): line[i] = (line[i] + (((line[i - bpp] if i >= bpp else 0) + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0; b = prev[i]; c = prev[i - bpp] if i >= bpp else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else (b if pb <= pc else c))) & 255
        rows.append(line); prev = line
    return w, h, bpp, rows


def stats(path, step=4):
    w, h, bpp, rows = decode(path)
    out = {'file': path, 'size': [w, h]}
    thirds = []
    for t in range(3):
        vals = []
        for y in range(t * h // 3, (t + 1) * h // 3, step):
            r = rows[y]
            for x in range(0, w * bpp, bpp * step):
                vals.append(0.2126 * r[x] + 0.7152 * r[x + 1] + 0.0722 * r[x + 2])
        vals.sort()
        thirds.append({'mean': round(sum(vals) / len(vals), 1), 'p5': round(vals[len(vals) // 20], 1), 'p50': round(vals[len(vals) // 2], 1), 'p95': round(vals[len(vals) * 19 // 20], 1)})
    out['top_third'], out['mid_third'], out['bottom_third'] = thirds
    out['mean'] = round(sum(t['mean'] for t in thirds) / 3, 1)
    return out


if __name__ == '__main__':
    for f in sys.argv[1:]:
        print(json.dumps(stats(f)))
