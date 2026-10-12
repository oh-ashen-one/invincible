# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Tricks C round 1: cut one excerpt per trick instance out of a capture (release - 0.35 s .. catch + 0.45 s), named <nn>_<program>.mp4.
#   python3 tools/tricks/cut_tricks.py <capture.mp4> <telemetry.csv> <out dir> [--chain <prog>,<prog>:<name>]
# --chain a,b:name cuts one excerpt from the first instance of a through the end of the next instance of b (chained tricks).
import csv, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tricks_check import instances  # noqa: E402

mp4, tel, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
T = list(csv.DictReader(open(tel)))
I = instances(T)


def cut(t0, t1, name):
    dst = os.path.join(out, name + '.mp4')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', '%.3f' % max(0, t0), '-t', '%.3f' % (t1 - max(0, t0)), '-i', mp4, '-an',
                    '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', dst], check=True)
    return dst


for k, c in enumerate(I):
    if c['scale'] <= 0: continue
    print(cut(c['t0'] - 0.35, c['t0'] + c['len'] + 0.45, '%02d_%s' % (k, c['prog'])))
if '--chain' in sys.argv:
    spec = sys.argv[sys.argv.index('--chain') + 1]
    progs, name = spec.split(':')
    a, b = progs.split(',')
    for i, c in enumerate(I):
        if c['prog'] == a:
            nxt = [d for d in I[i + 1:] if d['prog'] == b]
            if nxt:
                print(cut(c['t0'] - 0.35, nxt[0]['t0'] + nxt[0]['len'] + 0.45, name)); break
