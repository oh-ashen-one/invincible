#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 17: the measurement behind 'streaming vs content' for the r16 lineup corruption (copper blotches on the garments, halos, ghost bats).

  python3 tools/ue_char/suits/lineup_cause_r17.py --e0 DIR --e1 DIR --e2 DIR [--x0 DIR] --ref ROUND14_LINEUP.jpg --out evidence/lineup_cause.json [--md evidence/lineup_cause.md]

E0  = the r16 command (-shots 3.0, no settle protocol) with the per-frame probe (-WHProbeFrames): at every frame the number of assets still compiling (FAssetCompilingManager), shaders compiling and
      textures of the visible actors that are not fully resident.  The still is compared with the previous clean lineup (round 14) and the luma-difference share is reported.
E1  = the settle protocol with texture streaming ON, E2 = the settle protocol with -NoTextureStreaming: the same camera and content; the director dumps a screenshot after 1, 2, 4, 8, 16, 24 static
      rendered frames (once everything is resident) and the final shot (>= 34 frames, >= 4 s): each against the round-14 lineup and against the final shot (the convergence curve).
X0  = (optional) the r16 command with shots at 1, 2, 3, 4, 5, 6, 8, 10 world seconds in one run + the probe: the blotch share against the number of assets still compiling at each shot.
Reading: if the blotches follow `assets_compiling` (corrupt while > 0, clean once 0, whatever the frame count) the cause is the CAPTURE moment (async asset compile unfinished), not the content and not the
texture streaming (textures_not_resident is read at the same frames).  If a clean frame appears only after many static frames, it is temporal convergence.
"""
import sys, os, re, json, glob, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))


def arg(k, d=None):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


def diff(a, b):
    r = json.loads(subprocess.check_output([sys.executable, os.path.join(HERE, 'lineup_diff_r17.py'), a, b]).decode())
    return dict(pct_over=r['pct_over'], pct_over_in_band=r['pct_over_in_band'], mean_abs=r['mean_abs'], tiles_over_20pct=r['tiles_over_20pct'])


def probes(log):
    out = {}
    for ln in open(log, errors='replace'):
        m = re.search(r'WH_PROBE tick=(\d+) frame=(\d+) world=([\d.]+) stage_T=([\d.]+) dt_ms=([\d.]+) textures_not_resident=(\d+) \((.*?)\) assets_compiling=(\d+) shaders_compiling=(\d+)', ln)
        if m: out[int(m.group(2))] = dict(frame=int(m.group(2)), world=float(m.group(3)), dt_ms=float(m.group(5)), tex_bad=int(m.group(6)), assets=int(m.group(8)), shaders=int(m.group(9)))
    return out


def shots(log):
    out = []
    for ln in open(log, errors='replace'):
        m = re.search(r'\]\[\s*(\d+)\]LogWebHomage: Display: WH_SHOT (\S+)', ln)
        if m: out.append((int(m.group(1)), m.group(2)))
    return out


def main():
    ref = arg('--ref'); res = {}
    e0 = arg('--e0')
    if e0:
        pr = probes(glob.glob(os.path.join(e0, '*.log'))[0]); sh = shots(glob.glob(os.path.join(e0, '*.log'))[0])
        png = sorted(glob.glob(os.path.join(e0, '*_t*.png')))[0]
        fr = sh[0][0] if sh else None
        # the log prefix frame is GFrameCounter % 1000; the probe frames are < 1000 in these short runs
        p = pr.get(fr) or pr.get(max(k for k in pr if k <= (fr or 0)))
        res['E0_r16_protocol'] = dict(shot_frame=fr, probe_at_shot=p, probe_frame1=pr.get(1), vs_ref=diff(png, ref), still=png,
                                      first_frame_with_zero_assets=next((k for k in sorted(pr) if pr[k]['assets'] == 0), None), max_tex_not_resident=max(v['tex_bad'] for v in pr.values()))
    for key, d in (('E1_settle_streaming_on', arg('--e1')), ('E2_settle_no_streaming', arg('--e2'))):
        if not d: continue
        lg = glob.glob(os.path.join(d, '*.log'))[0]
        txt = open(lg, errors='replace').read()
        final = sorted(glob.glob(os.path.join(d, '*_t*.png')))[0]
        curve = []
        for f in sorted(glob.glob(os.path.join(d, '*_c*.png'))):
            n = int(re.search(r'_c(\d+)\.png', f).group(1))
            curve.append(dict(static_frames=n, vs_ref=diff(f, ref), vs_final=diff(f, final)))
        m = re.search(r'resident after ([\d.]+) s wall \((\d+) frames\)', txt); st = re.search(r'WH_STAGE_SHOT .*settle_frames=(\d+) static_world_s=([\d.]+) resets=(\d+) wall_s=([\d.]+)', txt)
        res[key] = dict(resident_after_s=float(m.group(1)) if m else None, resident_after_frames=int(m.group(2)) if m else None,
                        final=dict(settle_frames=int(st.group(1)), static_world_s=float(st.group(2)), resets=int(st.group(3)), wall_s=float(st.group(4))) if st else None,
                        final_vs_ref=diff(final, ref), curve=curve)
    x0 = arg('--x0')
    if x0:
        lg = glob.glob(os.path.join(x0, '*.log'))[0]
        rows = []
        for ln in open(lg, errors='replace'):
            m = re.search(r'WH_SHOTFRAME (\S+) requested at frame (\d+) \(target (\d+)\) world=([\d.]+) assets_compiling=(\d+) shaders_compiling=(\d+) textures_not_resident=(\d+)', ln)
            if not m: continue
            png = os.path.join(x0, os.path.basename(m.group(1)))
            if not os.path.exists(png): continue
            rows.append(dict(shot=os.path.basename(png), frame=int(m.group(2)), probe=dict(frame=int(m.group(2)), world=float(m.group(4)), assets=int(m.group(5)), shaders=int(m.group(6)), tex_bad=int(m.group(7))), valid=float(m.group(4)) < 5.9, vs_ref=diff(png, ref)))      # Char_Lineup shot 5 lasts 6 s of world time: later frames are the NEXT director shot (other camera), excluded
        res['X0_r16_protocol_shots'] = rows
    out = arg('--out')
    if out: json.dump(res, open(out, 'w'), indent=1)
    md = ['| run | frame | assets compiling | textures not resident | >20 luma vs r14 (whole / character band) | mean abs luma |', '|---|---|---|---|---|---|']
    r = res.get('E0_r16_protocol')
    if r: md.append('| E0 r16 command (-shots 3.0) | %s | %s | %s | %.2f %% / %.2f %% | %.2f |' % (r['shot_frame'], (r['probe_at_shot'] or {}).get('assets'), (r['probe_at_shot'] or {}).get('tex_bad'), r['vs_ref']['pct_over'], r['vs_ref']['pct_over_in_band'], r['vs_ref']['mean_abs']))
    for k, v in res.items():
        if k.startswith('X0'):
            for row in v:
                if row.get('valid', True): md.append('| X0 %s | %s | %s | %s | %.2f %% / %.2f %% | %.2f |' % (row['shot'], row['frame'], (row['probe'] or {}).get('assets'), (row['probe'] or {}).get('tex_bad'), row['vs_ref']['pct_over'], row['vs_ref']['pct_over_in_band'], row['vs_ref']['mean_abs']))
        if k.startswith('E1') or k.startswith('E2'):
            for c in v['curve']: md.append('| %s after %d static frames | | 0 | 0 | %.2f %% / %.2f %% | %.2f (vs final %.2f %%) |' % (k.split('_')[0], c['static_frames'], c['vs_ref']['pct_over'], c['vs_ref']['pct_over_in_band'], c['vs_ref']['mean_abs'], c['vs_final']['pct_over']))
            md.append('| %s final shot | | 0 | 0 | %.2f %% / %.2f %% | %.2f |' % (k.split('_')[0], v['final_vs_ref']['pct_over'], v['final_vs_ref']['pct_over_in_band'], v['final_vs_ref']['mean_abs']))
    if arg('--md'): open(arg('--md'), 'w').write('\n'.join(md) + '\n')
    print('\n'.join(md))


if __name__ == '__main__':
    main()
