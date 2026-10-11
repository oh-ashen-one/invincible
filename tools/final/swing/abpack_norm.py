#!/usr/bin/env python3
"""Normalised blind A/B pack (final loop). Like tools/night1/abpack.py, but both sides of a pair are trimmed to the same duration
(xs/xd, ys/yd seconds; d defaults to the shorter clip), scaled + padded to 1280x720, 30 fps, centre-cropped 84 %, no audio/metadata,
so pairs can't be told apart by duration, resolution or frame rate.
  python3 abpack_norm.py <pack_dir> <pairs.json>
pairs.json: [{"id", "x", "y", "note", "xs"?, "ys"?, "d"?}]"""
import json, os, random, subprocess, sys

def dur(p):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout.strip())

pack, pairs = sys.argv[1], json.load(open(sys.argv[2]))
os.makedirs(pack, exist_ok=True)
key, lines = {}, ['# Pairs', '', 'Each folder holds A and B of comparable movement. Judge each on its own merits.', '']
VF = 'crop=iw*0.84:ih*0.84,scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=30'
for p in pairs:
    xs, ys = p.get('xs', 0.0), p.get('ys', 0.0)
    d = p.get('d') or min(dur(p['x']) - xs, dur(p['y']) - ys)
    out = os.path.join(pack, p['id']); os.makedirs(out, exist_ok=True)
    order = [('x', p['x'], xs), ('y', p['y'], ys)]; random.shuffle(order)
    for slot, (who, src, s) in zip('AB', order):
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', str(s), '-t', str(d), '-i', src, '-map_metadata', '-1', '-an', '-vf', VF,
                        '-c:v', 'libx264', '-crf', '20', '-preset', 'fast', os.path.join(out, slot + '.mp4')], check=True)
        key.setdefault(p['id'], {})[slot] = who
    lines.append(f"- `{p['id']}/` — {p.get('note', '')} ({d:.1f} s)")
open(os.path.join(pack, 'PAIRS.md'), 'w').write('\n'.join(lines) + '\n')
json.dump(key, open(pack.rstrip('/') + '.key.json', 'w'), indent=1)
print(f'packed {len(pairs)} pairs -> {pack}')
