#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""P4 capture driver, tour version (round 03): ONE game session per preset and resolution visits every city shot pose (Scripts/city_shots.json S1..S8)
through the C++ shot tour (Source/WebHomage/Look/WHLookTour.cpp, -WHLookTour=<file>), waits for exposure / TSR / Lumen at each pose and writes a screenshot per pose.
Same running game, same maps (/Game/Tests/Look/Look_Midtown[_preset]: city + Look_Boxes + preset rig + traversal game mode), same hero (teleported to the
view's `player` position like the per-view maps do). Every run goes through gpu_slot.sh capture. Frames land in the scratch dir; JPEGs + notes go to the round folder.

usage: tools/perf_ue/capture_tour.py --round docs/night1/look/round-NN [--presets midday,golden,night] [--res 1920x1080,3840x2160] [--shots S1,S4,...]
         [--settle 4] [--min-frames 90] [--sp 100] [--work <dir>] [--redo] [--no-jpeg]      (--work: keep PNGs there instead of the default scratch dir)"""
import argparse, glob, json, math, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, '..', '..'))
UE = os.path.join(WT, 'unreal', 'WebHomage')
RUN_GAME = os.path.join(UE, 'Scripts', 'run_game.sh')
GPU_SLOT = os.environ.get('GPU_SLOT', '/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh')
SCR = os.path.join(os.environ.get('SM2_LOOK_SCRATCH', '/Users/midir/sm2-n1/_scratch/look'), 'tour')

def slot(cmd): return [GPU_SLOT, 'capture', '--label', 'look', '--'] + cmd if os.path.exists(GPU_SLOT) else cmd

def U(x, y, z): return (x * 100.0, z * 100.0, y * 100.0)   # browser metres (x east, y up, z south) -> UE cm

def look_rot(p, t):
    dx, dy, dz = t[0] - p[0], t[1] - p[1], t[2] - p[2]
    return (math.degrees(math.atan2(dz, math.hypot(dx, dy))), math.degrees(math.atan2(dy, dx)), 0.0)

def tour_lines(shots, settle, first_settle, variants=None):
    """variants: {name: [live-tuning command lines (see WHLookTour.h, '!' lines)]}; every variant visits every shot, pose names are <S#>@<variant>"""
    out = ['# name  x y z (cm)  pitch yaw roll  fov  settle_s  reserved  px py pz (hero, cm)']
    first = True
    for vname, cmds in (variants or {'': []}).items():
        for i, s in enumerate(shots):
            p, t = U(*s['pos']), U(*s['target']); r = look_rot(p, t); pl = s.get('player') or s['pos']; h = U(pl[0], pl[1] + 1.0, pl[2])
            if i == 0: out += ['! ' + c for c in cmds]
            out.append('%s%s %.1f %.1f %.1f %.4f %.4f %.4f %.2f %.1f 0 %.1f %.1f %.1f' % (s['id'].split('_')[0], ('@' + vname) if vname else '', p[0], p[1], p[2], r[0], r[1], r[2], s.get('fov', 70),
                                                                                         first_settle if first else (settle + (2.0 if i == 0 and vname else 0.0)), h[0], h[1], h[2]))
            first = False
    return '\n'.join(out) + '\n'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--round', required=True); ap.add_argument('--presets', default='midday,golden,night'); ap.add_argument('--res', default='1920x1080,3840x2160')
    ap.add_argument('--shots', default=''); ap.add_argument('--settle', type=float, default=4.0); ap.add_argument('--first-settle', type=float, default=10.0)
    ap.add_argument('--min-frames', type=int, default=90); ap.add_argument('--sp', default='100'); ap.add_argument('--redo', action='store_true'); ap.add_argument('--no-jpeg', action='store_true')
    ap.add_argument('--work', default=''); ap.add_argument('--jpeg-q', type=int, default=90); ap.add_argument('--start', type=float, default=8.0)
    ap.add_argument('--variants', default='', help='json {"variants": {name: [live tuning commands]}} : one session sweeps every variant over the selected shots'); ap.add_argument('--exec', default='', help='extra console commands, comma separated (debug variants)'); ap.add_argument('--timeout', type=int, default=1500); ap.add_argument('--suffix', default='', help='extra text appended to the file names (variants)')
    a = ap.parse_args()
    shots = json.load(open(os.path.join(UE, 'Scripts', 'city_shots.json')))
    want = [s for s in a.shots.split(',') if s]
    shots = [s for s in shots if not want or s['id'].split('_')[0] in want]
    rnd = os.path.abspath(a.round); os.makedirs(rnd + '/stills', exist_ok=True)
    sys.path.insert(0, HERE)
    import ensure_boxes
    if not ensure_boxes.ensure(): sys.exit('traversal boxes are stale (see above)')
    work = os.path.abspath(a.work) if a.work else SCR
    fails = 0; notes = []
    if a.variants:
        V = json.load(open(a.variants))['variants']
        for preset in a.presets.split(','):
            for res in a.res.split(','):
                d = os.path.join(work, 'var_%s_%s' % (preset, res)); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
                tf = os.path.join(d, 'tour.txt'); open(tf, 'w').write(tour_lines(shots, a.settle, a.first_settle, V))
                mp = '/Game/Tests/Look/Look_Midtown' + ('' if preset == 'midday' else '_' + preset)
                cmd = [RUN_GAME, d, '-map', mp, '-res', res, '-quit', '3000', '-name', 'tour', '-timeout', str(a.timeout), '-exec', 'r.ScreenPercentage %s' % a.sp + ((',' + a.exec) if a.exec else ''),
                       '--', '-WHLookTour=' + tf, '-WHLookTourDir=' + d, '-WHLookTourStart=%s' % a.start, '-WHLookTourMinFrames=%d' % a.min_frames]
                t0 = time.time(); subprocess.run(slot(cmd), capture_output=True, text=True)
                os.makedirs(rnd + '/stills', exist_ok=True); n = 0
                for f in sorted(glob.glob(d + '/S?@*.png')):
                    sid, v = os.path.basename(f)[:-4].split('@')
                    out = '%s/stills/%s_%s_%s_%s.jpg' % (rnd, preset, sid, res, v)
                    subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', str(a.jpeg_q), f, '--out', out], capture_output=True); n += 1
                print('variants', preset, res, n, 'stills', '%d s' % (time.time() - t0), flush=True)
        return
    for preset in a.presets.split(','):
        for res in a.res.split(','):
            names = ['%s_%s_%s%s' % (preset, s['id'].split('_')[0], res, a.suffix) for s in shots]
            todo = [s for s, n in zip(shots, names) if a.redo or not os.path.exists('%s/stills/%s.jpg' % (rnd, n))]
            if not todo: continue
            d = os.path.join(work, '%s_%s%s' % (preset, res, a.suffix)); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
            tf = os.path.join(d, 'tour.txt'); open(tf, 'w').write(tour_lines(todo, a.settle, a.first_settle))
            mp = '/Game/Tests/Look/Look_Midtown' + ('' if preset == 'midday' else '_' + preset)
            t0 = time.time()
            cmd = [RUN_GAME, d, '-map', mp, '-res', res, '-quit', '3000', '-name', 'tour', '-timeout', str(a.timeout), '-exec', 'r.ScreenPercentage %s' % a.sp + ((',' + a.exec) if a.exec else ''),
                   '--', '-WHLookTour=' + tf, '-WHLookTourDir=' + d, '-WHLookTourStart=%s' % a.start, '-WHLookTourMinFrames=%d' % a.min_frames]
            r = subprocess.run(slot(cmd), capture_output=True, text=True)
            got = {os.path.basename(p)[:-4]: p for p in glob.glob(d + '/S?.png')}
            miss = [s['id'].split('_')[0] for s in todo if s['id'].split('_')[0] not in got]
            print('tour', preset, res, 'poses', len(todo), 'got', len(got), 'missing', miss, '%d s' % (time.time() - t0), flush=True)
            if not got:
                print(r.stdout[-600:], r.stderr[-300:]); fails += 1
                if fails >= 2: sys.exit('two consecutive failed game runs: stopping, not relaunching in a loop')
                continue
            fails = 0
            for s in todo:
                sid = s['id'].split('_')[0]
                if sid not in got: continue
                name = '%s_%s_%s%s' % (preset, sid, res, a.suffix)
                out = '%s/stills/%s.jpg' % (rnd, name)
                if not a.no_jpeg: subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', str(a.jpeg_q), got[sid], '--out', out], capture_output=True)
                notes.append({'kind': 'still', 'file': os.path.relpath(out, rnd), 'preset': preset, 'view': s['id'], 'desc': s['desc'], 'output': res,
                              'internal': '%s%% of output' % a.sp, 'camera_pos_m': s['pos'], 'camera_target_m': s['target'], 'fov_deg': s.get('fov', 70), 'game_time_s': 'tour: %g s settle per pose (first pose %g s), >= %d frames' % (a.settle, a.first_settle, a.min_frames),
                              'gpu_util_before_pct': None, 'wall_s': None, 'method': 'shot tour (one session per preset and resolution)'})
    import capture_looks
    capture_looks.flush(rnd, notes, json.load(open(os.path.join(UE, 'Scripts', 'city_shots.json'))))

if __name__ == '__main__':
    main()
