#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Piece F: run a list of perf_route.py configs through as many EXCLUSIVE gpu_slot.sh perf sessions as needed (the lock's max hold is
15 min, so perf_route skips configs past its --budget-s; the skipped ones go into the next session). Exit 75 (lock wait timed out,
nothing ran) is retried up to --retries times; it never runs anything outside the lock.
usage: perf_queue.py --out <dir> --configs a@50,b@67,... [--tag s] [perf_route.py args after --]
Session n writes <out>/<tag><n>/ (perf_route output) + <out>/<tag><n>/perf_gpu.json (lock sidecar)."""
import argparse, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
G = '/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh'


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); ap.add_argument('--configs', required=True)
    ap.add_argument('--tag', default='s'); ap.add_argument('--retries', type=int, default=6); ap.add_argument('--start', type=int, default=1)
    ap.add_argument('rest', nargs=argparse.REMAINDER)
    a = ap.parse_args()
    rest = [x for x in a.rest if x != '--']
    todo = a.configs.split(','); n = a.start; fails = 0
    while todo:
        d = os.path.join(os.path.abspath(a.out), '%s%d' % (a.tag, n)); os.makedirs(d, exist_ok=True)
        cmd = [G, 'perf', '--label', 'perf', '--json', os.path.join(d, 'perf_gpu.json'), '--', sys.executable, os.path.join(HERE, 'perf_route.py'),
               '--out', d, '--configs', ','.join(todo)] + rest
        print(time.strftime('%H:%M:%S'), 'session', n, 'configs', todo, flush=True)
        rc = subprocess.run(cmd).returncode
        print(time.strftime('%H:%M:%S'), 'session', n, 'rc', rc, flush=True)
        if rc == 75:
            fails += 1
            if fails > a.retries: print('lock wait timed out %d times: giving up' % fails, flush=True); sys.exit(75)
            continue
        import glob
        ran = {os.path.basename(os.path.dirname(r)) for r in glob.glob(os.path.join(d, '*', 'result.json'))}  # survives a max-hold kill
        # configs perf_route skipped for budget are listed by name only: map back to their spec
        nxt = [s for s in todo if s.split('+')[0].split('@')[0] not in ran]
        if len(nxt) == len(todo): print('no progress in session %d (rc %s): stopping' % (n, rc), flush=True); sys.exit(1)
        todo = nxt; n += 1
    print('queue done', flush=True)


if __name__ == '__main__':
    main()
