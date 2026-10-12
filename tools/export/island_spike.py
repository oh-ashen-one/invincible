#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.
"""Island piece (A), Phase-0 spike: size the FULL-island browser export per district, idempotent and resumable.

    python3 tools/export/island_spike.py [--measure | --real] [--only midtown,upper] [--port 5208]

Districts are rectangles of 256 m tiles (browser tile ix = floor(x / 256), iz = floor(z / 256); north = -z). The browser island spans
x -790..870, z -3480..3330 (tiles ix -4..3, iz -14..13); every district runs in its OWN headless Chrome page (12 GB heap) with --nofar
(the far layer -- far shores, facadeLod ring, hinterland -- is a separate pass shared by every district).

  --measure (default)  export_city.mjs --measure: NOTHING but <scr>/spike/<district>/measure.json is written (tris, GLB bytes per tile,
                       JSON bytes, city-ready / collect seconds). Safe on a nearly full disk.
  --real               a real export into <scr>/export/<district>/ (GLBs + layout / collision / manifest). Refused below MIN_FREE_GB
                       free (RULES / PLAN-firstpass §5: abort M1 under 150 GB free).

A district whose measure.json (or manifest.json for --real) exists is skipped (resume = run again). Summary: <scr>/spike/summary.json.
Needs the Vite dev server of this worktree on --port (npx vite --port 5208 --host 127.0.0.1 --strictPort).
"""
import argparse, json, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, '..', '..'))
SCR = os.environ.get('SM2_ISLAND_SCR', '/Users/midir/sm2-n1/_scratch/island')
MIN_FREE_GB = float(os.environ.get('SM2_ISLAND_MIN_FREE_GB', '150'))

# (name, ix0, iz0, ix1, iz1) inclusive tile ranges, in PLAN-firstpass build order. Together they cover ix -4..3, iz -14..13 exactly once.
DISTRICTS = [
    ('midtown', -3, -5, 3, 3),        # Midtown 7 x 9 (Times Square, Grand Central, Hell's Kitchen, Chelsea / Murray Hill edge), the M1 target
    ('midtown_w', -4, -5, -4, 3),     # the Hudson-shore column west of the 7 x 9 (x -1024..-768: piers / west side highway sliver)
    ('fidi', -4, 8, 3, 13),           # Financial District + Battery (z 2048..3584)
    ('village', -4, 4, 3, 7),         # Village / SoHo / Chinatown / LES (z 1024..2048)
    ('upper', -4, -9, 3, -6),         # Central Park south half + Upper West / East Side (z -2560..-1280)
    ('north', -4, -14, 3, -10),       # Upper park, Harlem, north tip (z -3584..-2560)
]


def free_gb(path='/Users/midir'):
    st = os.statvfs(path)
    return st.f_bavail * st.f_frsize / 1e9


def run_district(name, t, mode, port):
    out = os.path.join(SCR, 'spike' if mode == 'measure' else 'export', name)
    done = os.path.join(out, 'measure.json' if mode == 'measure' else 'manifest.json')
    if os.path.exists(done):
        print('[spike] %s: already done (%s)' % (name, done)); return json.load(open(os.path.join(out, 'measure.json')))
    if mode == 'real' and free_gb() < MIN_FREE_GB:
        raise SystemExit('[spike] ABORT %s: %.0f GB free < %.0f GB (PLAN-firstpass §5)' % (name, free_gb(), MIN_FREE_GB))
    os.makedirs(out, exist_ok=True)
    cmd = ['node', 'tools/export/export_city.mjs', '--tiles', ','.join(map(str, t)), '--out', out, '--url', 'http://127.0.0.1:%d/' % port,
           '--profile', os.path.join(SCR, 'chrome-profile'), '--nofar'] + (['--measure'] if mode == 'measure' else [])
    log = os.path.join(SCR, 'logs', 'spike_%s_%s.log' % (mode, name))
    print('[spike] %s %s: %s  (log %s, %.0f GB free)' % (time.strftime('%H:%M:%S'), name, ' '.join(cmd), log, free_gb()), flush=True)
    t0 = time.time()
    with open(log, 'w') as f:
        r = subprocess.run(cmd, cwd=WT, stdout=f, stderr=subprocess.STDOUT)
    if r.returncode != 0 or not os.path.exists(os.path.join(out, 'measure.json')):
        raise SystemExit('[spike] %s failed (rc %d), see %s' % (name, r.returncode, log))
    m = json.load(open(os.path.join(out, 'measure.json')))
    m['wall_seconds'] = round(time.time() - t0, 1); m['free_gb_after'] = round(free_gb(), 1)
    json.dump(m, open(os.path.join(out, 'measure.json'), 'w'), indent=1)
    return m


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(); g.add_argument('--measure', action='store_true'); g.add_argument('--real', action='store_true')
    ap.add_argument('--only', default=''); ap.add_argument('--port', type=int, default=int(os.environ.get('SM2_CITY_PORT', '5208')))
    a = ap.parse_args()
    mode = 'real' if a.real else 'measure'
    os.makedirs(os.path.join(SCR, 'logs'), exist_ok=True)
    want = [w for w in a.only.split(',') if w]
    rows = []
    for name, *t in DISTRICTS:
        if want and name not in want: continue
        m = run_district(name, t, mode, a.port)
        land = {k: v for k, v in m['per_tile'].items() if v['tris'] > 0}
        rows.append({'district': name, 'tiles': t, 'tiles_total': (t[2] - t[0] + 1) * (t[3] - t[1] + 1), 'tiles_with_geometry': len(land),
                     'tris': m['totals']['tris'], 'glb_gb': round(m['totals']['glb_bytes'] / 1e9, 3), 'json_mb': round(m['totals']['json_bytes'] / 1e6, 1),
                     'collision_solids': m['json'].get('collision_solids'), 'city_ready_s': m['seconds']['city_ready'], 'collect_s': m['seconds']['collect'],
                     'wall_s': m.get('wall_seconds'), 'kinds': m['kinds']})
        print('[spike] %-10s tiles %3d (%3d with geometry)  tris %11d  GLB %6.2f GB  json %6.1f MB  ready %5.0f s  collect %5.0f s'
              % (name, rows[-1]['tiles_total'], rows[-1]['tiles_with_geometry'], rows[-1]['tris'], rows[-1]['glb_gb'], rows[-1]['json_mb'],
                 rows[-1]['city_ready_s'], rows[-1]['collect_s']), flush=True)
    summ = {'mode': mode, 'created': time.strftime('%Y-%m-%d %H:%M:%S'), 'districts': rows,
            'total': {k: sum(r[k] or 0 for r in rows) for k in ('tiles_total', 'tiles_with_geometry', 'tris', 'glb_gb', 'json_mb', 'collect_s', 'wall_s')}}
    os.makedirs(os.path.join(SCR, 'spike'), exist_ok=True)
    json.dump(summ, open(os.path.join(SCR, 'spike', 'summary%s.json' % ('' if not want else '_' + '_'.join(want))), 'w'), indent=1)
    print('[spike] total', json.dumps(summ['total']))


if __name__ == '__main__':
    main()
