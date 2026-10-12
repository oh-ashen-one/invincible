#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Writes <round>/TESTS.md (numbers only) for a look round: every check of docs/night1/look/SPEC.md that the still / clip captures allow.
  stills  <round>/stills/<preset>_<S#>_<res>.jpg : look_spec_check.py tables (L1 / L2 / L3 / L5 means, near-black, clipped, B-R, L10 / L11 far field of S4, L13 / L14 night pools, L17 glass p10)
                                                    for 1920x1080 and 3840x2160 (resized to 1920 wide by the instrument), plus night_tests.py (round-1 critic tests) for night S1 / S6
  clips   <round>/swing_<preset>.mp4              : clip_check.py (per-frame mean Y, B-R, near-black, clipped) and <round>/swing_<preset>_hero_luma.json (hero pixel-box luma, L15)
usage: round_tests.py --round docs/night1/look/round-NN"""
import argparse, glob, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import look_spec_check as LS
import night_tests as NT

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--round', required=True); a = ap.parse_args()
    rnd = os.path.abspath(a.round)
    L = ['# Round test numbers (numbers only)', '', '> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.', '',
         'Produced by `tools/perf_ue/round_tests.py` from the stills / clips in this folder: `look_spec_check.py` (LOOK-SPEC lines of `docs/night1/look/SPEC.md`), `night_tests.py` (round-1 critic tests), `clip_check.py` (clips).',
         'Luma Y = 0.2126 R + 0.7152 G + 0.0722 B of the 8-bit sRGB values; every still is resized to 1920 px wide first; near-black = Y < 10; clipped = any channel >= 250; B-R = mean(B) - mean(R).',
         'Bands: golden L1 mean 61..100, near-black <= 8 %, clipped <= 1.8 %, B-R -55..-20 (S7: L5, clipped <= 0.7 %); midday L2 mean 83..97, near-black <= 0.05 %, clipped 0.00 %, B-R -19..+8 (S4: L11 horizon - sky >= +3);',
         'night L3 mean 37..60, near-black <= 1 %, clipped <= 1.7 %, B-R -13..+13 (L8), street views S1 / S5 / S6: L13 >= 5 lit blobs, L14 bottom-third p10 15..30 and p90 >= 100; L10 far shore 15..32 Y below the sky and B-R within +-10 of the sky; L17 glass p10 >= 20 (daylight).', '']
    for res in ('1920x1080', '3840x2160'):
        files = sorted(glob.glob(os.path.join(rnd, 'stills', '*_%s.jpg' % res)))
        if not files: continue
        L += ['## Stills %s' % res, '']
        md = subprocess.run([sys.executable, os.path.join(HERE, 'look_spec_check.py')] + files, capture_output=True, text=True).stdout
        L += [md, '']
    ns = [f for f in sorted(glob.glob(os.path.join(rnd, 'stills', 'night_S[16]_*.jpg')))]
    if ns:
        L += ['## Round-1 critic night tests (night_tests.py; peak >= 120, valley <= 40, blur sigma 8 px at 1080p, bottom third)', '', '| still | mean Y | share < 10/255 | distinct light pools (target >= 4) | pool peaks |', '|---|---|---|---|---|']
        for f in ns:
            s = NT.still_stats(f); p = NT.pool_stats(f)
            L.append('| %s | %.1f | %.2f %% | %d | %s |' % (os.path.basename(f), s['mean_luma'], s['pct_below_10'], p['distinct_pools'], p['pool_peaks']))
        L.append('')
    clips = sorted(glob.glob(os.path.join(rnd, 'swing_*.mp4')))
    if clips:
        L += ['## Swing clips (clip_check.py on every 3rd frame at 960x540; hero luma from the P3 hero-only depth capture)', '',
              '| clip | frames measured | mean Y (mean / min / max) | B-R (mean / p10 / p90) | frames outside B-R +-13 (night L8 band; midday / golden bands differ) | near-black % | clipped % | L18 edge / centre sharpness p10 / p50 / p90 (0.20..0.65) | hero box luma min / p5 / mean (frames < 40) |', '|---|---|---|---|---|---|---|---|---|']
        for c in clips:
            name = os.path.basename(c)[:-4]
            r = json.loads(subprocess.run([sys.executable, os.path.join(HERE, 'clip_check.py'), c, '--every', '3'], capture_output=True, text=True).stdout)
            hp = os.path.join(rnd, name + '_hero_luma.json'); h = json.load(open(hp)) if os.path.exists(hp) else None
            hs = ('%s / %s / %s (%s)' % (h['bbox_mean_luma_min'], h['bbox_mean_luma_p5'], h['bbox_mean_luma_mean'], h['frames_below_threshold'])) if h else 'n/a'
            e = r['L18_edge_over_centre_sharpness']
            L.append('| %s | %d | %.1f / %.1f / %.1f | %+.1f / %+.1f / %+.1f | %.1f %% | %.2f | %.2f | %.2f / %.2f / %.2f | %s |' % (os.path.basename(c), r['frames_measured'], r['mean_Y']['mean'], r['mean_Y']['min'], r['mean_Y']['max'],
                     r['B_minus_R']['mean'], r['B_minus_R']['p10'], r['B_minus_R']['p90'], r['frames_outside_pm13_pct'], r['near_black_pct_mean'], r['clipped_pct_mean'], e['p10'], e['p50'], e['p90'], hs))
        L.append('')
    open(os.path.join(rnd, 'TESTS.md'), 'w').write('\n'.join(L))
    print('wrote', os.path.join(rnd, 'TESTS.md'))

if __name__ == '__main__':
    main()
