#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""P4 capture driver for the critic: every city shot view (Scripts/city_shots.json S1..S8) under each time-of-day preset at
3840x2160 and 1920x1080 (stills, from the RUNNING game: Scripts/run_game.sh, offscreen -game), plus one 60 fps swing-chain clip
per preset (fixed 1/60 s step, every frame dumped, H.264 <= 15 MB). Heavy frames go to the scratch dir, the round folder gets
JPEGs, mp4s and NOTES.md (neutral facts only: preset, camera, output size, internal resolution).

usage: tools/perf_ue/capture_looks.py --round docs/night1/look/round-01 [--presets midday,golden,night] [--shots S1,S2,...]
         [--res 3840x2160,1920x1080] [--shot-times 12,20] [--clips] [--clip-seconds 12] [--no-stills]"""
import argparse, json, os, re, shutil, subprocess, sys, time, glob

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, '..', '..'))
UE = os.path.join(WT, 'unreal', 'WebHomage')
RUN_GAME = os.path.join(UE, 'Scripts', 'run_game.sh')
GPU_SLOT = os.environ.get('GPU_SLOT', '/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh')   # docs/night1/gpu/PROTOCOL.md: every game capture runs inside a shared slot (2 at once)
def slot(cmd): return [GPU_SLOT, 'capture', '--label', 'look', '--'] + cmd if os.path.exists(GPU_SLOT) else cmd
SCR = os.path.join(os.environ.get('SM2_LOOK_SCRATCH', '/Users/midir/sm2-n1/_scratch/look'), 'capture')   # heavy frames (env SM2_LOOK_SCRATCH)

def util():
    s = subprocess.run("ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '\"Device Utilization %\"=[0-9]*'", shell=True, capture_output=True, text=True).stdout
    m = re.findall(r'=(\d+)', s); return int(m[0]) if m else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--round', required=True); ap.add_argument('--presets', default='midday,golden,night')
    ap.add_argument('--shots', default=''); ap.add_argument('--res', default='3840x2160,1920x1080')
    ap.add_argument('--shot-times', default='12,20'); ap.add_argument('--clips', action='store_true'); ap.add_argument('--no-stills', action='store_true')
    ap.add_argument('--clip-seconds', type=float, default=12.0); ap.add_argument('--sp', default='100', help='r.ScreenPercentage for the captures')
    ap.add_argument('--jpeg-q', type=int, default=90); ap.add_argument('--redo', action='store_true', help='recapture stills that already exist')
    ap.add_argument('--no-warmup', action='store_true', help='skip the unrecorded 960x540 shader warm-up render before each clip (the shaders are already in the DDC)')
    a = ap.parse_args()
    sys.path.insert(0, HERE)
    import ensure_boxes
    if not ensure_boxes.ensure(): sys.exit('traversal boxes are stale (see above): capture / perf would run against boxes of an older city')
    rnd = os.path.abspath(a.round); os.makedirs(rnd + '/stills', exist_ok=True); os.makedirs(SCR, exist_ok=True)
    shots = json.load(open(os.path.join(UE, 'Scripts', 'city_shots.json')))
    want = [s for s in a.shots.split(',') if s]
    notes = []
    times = [float(t) for t in a.shot_times.split(',')]
    fails = [0]   # RULES (2026-09-29 incident): no crash-relaunch loops: stop after 2 consecutive failed game runs
    def failed(what):
        fails[0] += 1
        if fails[0] >= 2: flush(rnd, notes, shots); sys.exit('two consecutive failed game runs (last: %s): stopping, not relaunching in a loop' % what)
    if not a.no_stills:
        for preset in a.presets.split(','):
            for s in shots:
                sid = s['id'].split('_')[0]
                if want and sid not in want: continue
                for res in a.res.split(','):
                    name = '%s_%s_%s' % (preset, sid, res)
                    if os.path.exists('%s/stills/%s.jpg' % (rnd, name)) and not a.redo: continue   # already captured (resume)
                    d = os.path.join(SCR, name); shutil.rmtree(d, ignore_errors=True)
                    u = util(); t0 = time.time()
                    cmd = [RUN_GAME, d, '-map', '/Game/Tests/Look/Look_View_%s_%s' % (preset, sid), '-res', res, '-shots', a.shot_times, '-name', name,
                           '-timeout', '900', '-exec', 'r.ScreenPercentage %s' % a.sp]
                    r = subprocess.run(slot(cmd), capture_output=True, text=True)
                    pngs = sorted(glob.glob(d + '/*.png'))
                    if not pngs: print('FAILED', name, r.stdout[-400:], r.stderr[-400:]); failed(name); continue
                    fails[0] = 0
                    last = pngs[-1]
                    out = '%s/stills/%s.jpg' % (rnd, name)
                    subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', str(a.jpeg_q), last, '--out', out], capture_output=True)
                    notes.append({'kind': 'still', 'file': os.path.relpath(out, rnd), 'preset': preset, 'view': s['id'], 'desc': s['desc'], 'output': res,
                                  'internal': ('%s%% of output' % a.sp), 'camera_pos_m': s['pos'], 'camera_target_m': s['target'], 'fov_deg': s.get('fov', 70),
                                  'game_time_s': times[-1], 'gpu_util_before_pct': u, 'wall_s': round(time.time() - t0)})
                    if preset == 'night' and sid in ('S1', 'S6'):
                        sys.path.insert(0, HERE)
                        import night_tests
                        tst = {'still': night_tests.still_stats(last), 'pools_bottom_third': night_tests.pool_stats(last)}
                        json.dump(tst, open('%s/stills/%s_tests.json' % (rnd, name), 'w'), indent=1)
                        notes[-1]['tests'] = {'mean_luma': tst['still']['mean_luma'], 'pct_below_10': tst['still']['pct_below_10'], 'distinct_pools_bottom_third': tst['pools_bottom_third']['distinct_pools']}
                    print('still', name, os.path.getsize(out) // 1024, 'KB', round(time.time() - t0), 's', flush=True)
                    flush(rnd, notes, shots)
    if a.clips:
        PRE = 0.8   # pre-roll (s): start pose rendered, traversal not stepped (exposure / Lumen / TSR settle); those frames are trimmed from the clip
        for preset in a.presets.split(','):
            name = 'swing_%s' % preset
            mp = '/Game/Tests/Look/Look_Midtown' + ('' if preset == 'midday' else '_' + preset)
            if not a.no_warmup:
                wd = os.path.join(SCR, name + '_warmup'); shutil.rmtree(wd, ignore_errors=True)   # shader / texture warm-up render, not kept
                subprocess.run(slot([RUN_GAME, wd, '-map', mp, '-res', '960x540', '-quit', '14', '-name', 'warmup', '-timeout', '2400', '--', '-benchmark', '-fps=60',
                                '-WHTravScript=' + os.path.join(HERE, 'scripts', 'city_swing_clip.json')]), capture_output=True, text=True)
                shutil.rmtree(wd, ignore_errors=True)
            d = os.path.join(SCR, name); shutil.rmtree(d, ignore_errors=True)
            u = util(); t0 = time.time()
            cmd = [RUN_GAME, d, '-map', mp, '-res', '1920x1080', '-quit', str(a.clip_seconds + PRE),
                   '-name', name, '-movie', '-timeout', '7000', '-exec', 'r.ScreenPercentage %s' % a.sp,
                   '--', '-WHTravScript=' + os.path.join(HERE, 'scripts', 'city_swing_clip.json'), '-WHTravCsv=' + os.path.join(d, name + '_telemetry.csv'), '-WHTravPreroll=%s' % PRE]
            r = subprocess.run(slot(cmd), capture_output=True, text=True)
            mp4 = os.path.join(d, name + '.mp4')
            fr = os.path.join(d, name + '_frames'); csvp = os.path.join(d, name + '_telemetry.csv')
            if not os.path.isdir(fr) or not glob.glob(fr + '/*.png'): print('FAILED clip', name, r.stdout[-400:]); failed(name); continue
            fails[0] = 0
            nfr_all = len(glob.glob(fr + '/*.png')); nrows = (sum(1 for _ in open(csvp)) - 1) if os.path.exists(csvp) else nfr_all
            skip = max(0, nfr_all - nrows)           # rendered frames before the sequence's first telemetry row (engine start + pre-roll)
            out = os.path.join(rnd, name + '.mp4')
            def enc(extra):
                subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-framerate', '60', '-start_number', str(skip), '-i', fr + '/MovieFrame%05d.png', '-c:v', 'libx264',
                                '-pix_fmt', 'yuv420p', '-movflags', '+faststart'] + extra + [out])
            enc(['-crf', '18'])
            dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', out], capture_output=True, text=True).stdout)
            if os.path.getsize(out) > 15_000_000:
                kbps = int(14.5e6 * 8 / 1000 / dur)
                enc(['-preset', 'slow', '-b:v', '%dk' % kbps, '-maxrate', '%dk' % kbps, '-bufsize', '%dk' % (kbps * 2)])
            if os.path.exists(csvp): shutil.copy(csvp, os.path.join(rnd, name + '_telemetry.csv'))
            tests = None
            if os.path.exists(csvp):   # hero-only pixel box (P3 depth capture) -> mean luma per frame
                sys.path.insert(0, HERE)
                import night_tests
                tests = night_tests.hero_stats(fr, csvp, skip=skip)
                json.dump(tests, open(os.path.join(rnd, name + '_hero_luma.json'), 'w'), indent=1)
                print('hero luma', name, tests, flush=True)
            notes.append({'kind': 'clip', 'file': os.path.basename(out), 'preset': preset, 'map': mp, 'output': '1920x1080 60 fps H.264',
                          'internal': '%s%% of output (1920x1080)' % a.sp, 'frames': nrows, 'seconds': round(dur, 2), 'bytes': os.path.getsize(out),
                          'script': 'tools/perf_ue/scripts/city_swing_clip.json (P3 traversal hero, -WHTravScript, 0.8 s pre-roll trimmed)', 'time_step': 'fixed 1/60 s (-benchmark -fps=60 -dumpmovie)',
                          'gpu_util_before_pct': u, 'wall_s': round(time.time() - t0), 'hero_bbox_mean_luma': tests})
            shutil.rmtree(fr, ignore_errors=True)  # heavy PNG frames are disposable once encoded
            print('clip', name, os.path.getsize(out) // 1024, 'KB', nrows, 'frames', flush=True)
            flush(rnd, notes, shots)
    flush(rnd, notes, shots)

def scan_stills(rnd, shots, have):
    """notes entries for stills on disk that have none (a resumed run, or a run that died before writing its notes)"""
    out = []
    for f in sorted(glob.glob(rnd + '/stills/*.jpg')):
        rel = os.path.relpath(f, rnd)
        m = re.match(r'(midday|golden|night)_(S\d)_(\d+x\d+)\.jpg$', os.path.basename(f))
        if rel in have or not m: continue
        s = next((x for x in shots if x['id'].startswith(m.group(2) + '_')), None)
        if not s: continue
        out.append({'kind': 'still', 'file': rel, 'preset': m.group(1), 'view': s['id'], 'desc': s['desc'], 'output': m.group(3), 'internal': '100% of output', 'camera_pos_m': s['pos'], 'camera_target_m': s['target'],
                    'fov_deg': s.get('fov', 70), 'game_time_s': 20.0, 'gpu_util_before_pct': None, 'wall_s': None})
    return out

def flush(rnd, notes, shots):
    prev = []
    if os.path.exists(rnd + '/notes.json'):
        try: prev = json.load(open(rnd + '/notes.json'))
        except Exception: prev = []
    keep = {n['file']: n for n in prev}; keep.update({n['file']: n for n in notes})
    for n in scan_stills(rnd, shots, set(keep)): keep[n['file']] = n
    json.dump(list(keep.values()), open(rnd + '/notes.json', 'w'), indent=1)
    write_notes(rnd, list(keep.values()))

def write_notes(rnd, notes):
    L = ['# Look round capture notes (neutral facts only)', '',
         '> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.', '',
         'Everything below was rendered by the running game (`Scripts/run_game.sh`: standalone `-game`, offscreen, true back-buffer size; every run inside `gpu_slot.sh capture`), not by an editor viewport.',
         'Presets are defined in `unreal/WebHomage/Scripts/look_presets.json` (midday / golden / night) and built by `unreal/WebHomage/Scripts/build_look.py`.',
         'Camera positions are browser metres (x east, y up, z south); the UE position is (100 x, 100 z, 100 y) cm. Stills are JPEG converted from the PNG screenshot taken at the given game time.', '',
         '## Stills', '', '| file | preset | view | output | internal resolution | camera pos (m) | camera target (m) | fov | game time (s) |', '|---|---|---|---|---|---|---|---|---|']
    for n in sorted([n for n in notes if n['kind'] == 'still'], key=lambda n: (n['preset'], n['view'], n['output'])):
        L.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (n['file'], n['preset'], n['view'], n['output'], n['internal'], n['camera_pos_m'], n['camera_target_m'], n['fov_deg'], n['game_time_s']))
    L += ['', '## Clips', '', '| file | preset | map | output | internal resolution | frames | seconds | bytes | time step | script |', '|---|---|---|---|---|---|---|---|---|---|']
    for n in sorted([n for n in notes if n['kind'] == 'clip'], key=lambda n: n['preset']):
        L.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (n['file'], n['preset'], n['map'], n['output'], n['internal'], n['frames'], n['seconds'], n['bytes'], n['time_step'], n['script']))
    tt = [n for n in notes if n.get('tests') or n.get('hero_bbox_mean_luma')]
    if tt:
        L += ['', '## Night test numbers (tools/perf_ue/night_tests.py; luma Y = 0.2126 R + 0.7152 G + 0.0722 B of the 8-bit sRGB values)', '']
        for n in sorted(tt, key=lambda n: n['file']):
            if n.get('tests'): L.append('- %s: mean luma %s /255, %s %% of pixels < 10/255, distinct light pools in the bottom third (peak >= 120, valley <= 40) %s' % (n['file'], n['tests']['mean_luma'], n['tests']['pct_below_10'], n['tests']['distinct_pools_bottom_third']))
            if n.get('hero_bbox_mean_luma'):
                h = n['hero_bbox_mean_luma']
                L.append('- %s: hero pixel bounding box mean luma per frame: min %s, p5 %s, mean %s, max %s /255 over %s frames (%s frames below 40; %s frames without hero pixels)' % (n['file'], h['bbox_mean_luma_min'], h['bbox_mean_luma_p5'], h['bbox_mean_luma_mean'], h['bbox_mean_luma_max'], h['frames_measured'], h['frames_below_threshold'], h['frames_without_hero_pixels']))
    L += ['', 'Clip frames are rendered offline at a fixed 1/60 s step (`-benchmark -fps=60 -dumpmovie`), so a clip says nothing about real-time frame rate; see `PERF.md` for measured frame times.', '']
    open(rnd + '/NOTES.md', 'w').write('\n'.join(L))

if __name__ == '__main__':
    main()
