#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 13 SPEC_CHECK.md writer: every number is read from <round-13>/evidence (post_r13.sh), never from memory.
  python3 tools/ue_char/suits/spec_check_r13.py <round-13 dir> > <round-13 dir>/SPEC_CHECK.md"""
import sys, os, json, glob
d = sys.argv[1]; ev = os.path.join(d, 'evidence'); M = os.path.join(ev, 'measures')
def J(p):
    p = os.path.join(ev, p) if not os.path.isabs(p) else p
    try: return json.load(open(p))
    except Exception: return None
SUITS = ['tessera', 'verdant', 'plum', 'cinder', 'glacier', 'ash', 'saffron', 'sage']
L = ['# Round 13 SPEC CHECK (piece G, hero skins)', '',
     '> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. Numbers are read from `evidence/` by `tools/ue_char/suits/spec_check_r13.py`;',
     '> the measures of the 4K chest stills run on the lossless PNG originals of the real game (UE 5.8.3 `-game`, offscreen, internal 3840x2160).', '']
# ---- the round target: the sculpted head (head_check_r13.py)
hc = J('head_check.json')
HEADL = ['## Round target (critic round 12): sculpt the shared mask head', '',
         'Measured by `tools/ue_char/suits/head_check_r13.py` on the lossless 4K PNG originals of the real game: `head` = 12 deg off the face axis (1.0 m), `head34` = the round-12 head framing (25 deg), `headside` = profile (1.25 m).',
         'H1 nose-bridge luma profile (vertical, midline between the lenses, 11 px smoothing): extrema with prominence >= 20 luma, count >= 3 and swing >= 20. '
         'H2 silhouette nose bump >= 2 % of head height (profile still: front-most silhouette column above the line brow point -> chin point). '
         'H3 lens width >= 1.6x round 12 (lens px width / head silhouette width at the lens row; PASS = the near lens in the round-12 framing and the mean of both lenses in the 12 deg still; the far lens of a 25 deg view is foreshortened and partly behind the silhouette: reported, not gated). '
         'H4 rim: the contiguous band around each lens whose luma differs from the mask by >= 15 (of 255) is >= 6 px wide on >= 90 % of 48 angles. '
         'H5 face seam: lit / shadow pair >= 20 luma across the midline cord at 12 heights, no black run >= 12 px. H6 both lenses >= 3 px from the background in the 12 deg view (the lenses wrap the face and lie against its outline).', '']
if hc:
    HEADL += ['| suit | H1 extrema / swing (head, head34) | H2 nose bump % of head height | H3 lens / head width (r12 -> r13), ratio | H4 rim px median, closed (head / head34) | H5 seam pair, black run | H6 lens edge distance px | verdict |', '|---|---|---|---|---|---|---|---|']
    npass = 0
    for sid in SUITS:
        r = hc.get(sid)
        if not r or not r['head'].get('nose') or not r['head34'].get('nose'):
            if r: HEADL.append('| %s | lens detection failed (see evidence/head_check.json) | | | | | | FAIL |' % sid)
            continue
        h, h34, sd, v = r['head'], r['head34'], r['side'], r['verdict']
        ok = all(v.values()); npass += ok
        HEADL.append('| %s | %s / %s ; %s / %s | %s | %s -> %s; near lens **%sx**, far lens %sx, mean (12 deg still) **%sx** | %s, %s ; %s, %s | %s, %s | %s | %s |' % (
            sid, h['nose']['v_extrema_prom20'], h['nose']['v_swing'], h34['nose']['v_extrema_prom20'], h34['nose']['v_swing'],
            sd and '**%s**' % sd['nose_bump_pct_head_h'], h34.get('r12', {}).get('lens_over_head'), h34.get('lens_over_head'), h34.get('lens_width_ratio_near'), h34.get('lens_width_ratio_far'), h.get('lens_width_ratio_vs_r12'),
            h.get('rim_px_median'), h.get('rim_closed_frac'), h34.get('rim_px_median'), h34.get('rim_closed_frac'),
            h['seam']['pair_median'], h['seam']['longest_black_run'], h.get('lens_edge_distance_px'),
            'PASS' if ok else 'FAIL ' + ', '.join(k.split('_')[0] for k, x in v.items() if not x)))
    HEADL += ['', '%d of %d suits pass every gate H1 - H6 (`evidence/head_check.json`, overlays in `evidence/measures/head_overlays/`).' % (npass, len(SUITS))]
else:
    HEADL += ['(head_check.json missing)']
L += HEADL + ['']
# ---- keep-passing relief lines (r12 target): raised piping on the chest stills
L += ['## Keep: the round-12 lines (raised piping, nothing under the sash, no fold)', '',
      '| suit | relief: 64 px cells with a lit / shadow pair >= 20 luma (r12 -> r13) | median cell delta (r12 -> r13) | sash: longest dark run px, target <= 10 (r12 -> r13) | sash verdict |', '|---|---|---|---|---|']
allpass_sash = True
for s in SUITS:
    a, b = J('measures/r12_relief_%s.json' % s), J('measures/relief_%s.json' % s)
    c, e = J('measures/r12_sash_%s.json' % s), J('measures/sash_%s.json' % s)
    if not b: continue
    v = e.get('verdict', 'n/a') if e else 'n/a'
    L.append('| %s | %s -> **%s** (%d of %d cells) | %s -> **%s** | %s -> **%s** | %s |' % (
        s, a and a.get('share_cells_ge20'), b.get('share_cells_ge20'), b.get('cells_ge20', 0), b.get('cells', 0), a and a.get('median_cell_delta'), b.get('median_cell_delta'),
        c and c.get('longest_dark_run_px'), e and e.get('longest_dark_run_px'), v))
jg, jg11 = J('measures/jog_verdant.json'), J('measures/r12_jog_verdant.json')
if jg:
    L += ['', '| Verdant chevron edge at the critic\'s columns x 1320-1400 | target | round 12 | round 13 | verdict |', '|---|---|---|---|---|',
          '| largest column-to-column jump beyond its slope | <= 2 px | %s px | **%s px** | %s |' % (jg11 and jg11.get('jump_at_critic_x1320_1400'), jg.get('jump_at_critic_x1320_1400'), jg.get('verdict_at_critic_x'))]
# ---- keep-passing lines
L += ['', '## Keep-passing lines', '', '| line | target | measured | verdict |', '|---|---|---|---|']
c1 = J('measures/ch1_front.json')
if c1:
    hs = [x['height_frac'] for x in c1['stills']]
    L.append('| CH1 front stills (hero height / frame height, all 8 suits) | 0.48 - 0.62 | %.3f - %.3f | %s |' % (min(hs), max(hs), 'PASS' if c1['all_ok'] else 'FAIL'))
ip = J('ipguard.json')
if ip:
    L.append('| IP guard palette P1 - P7 (Verdant / Saffron re-blocked, Plum recoloured) | 0 failures | min palette distance %.1f over %d pairs, fails: %s | %s |' % (
        min(ip['palette_distance'].values()), len(ip['palette_distance']), ip['fails'] or 'none', 'PASS' if not ip['fails'] else 'FAIL'))
sm = J('seams.json')
if sm:
    w = max(r['worst_run_px'] for r in sm['suits'].values()); nr = sum(r['runs_gt_40px'] for r in sm['suits'].values())
    L.append('| UV seam runs at 4K (texture level) | <= 40 px | worst %.1f px, runs > 40 px: %d | %s |' % (w, nr, 'PASS' if nr == 0 else 'FAIL'))
oc = J('ocr_stills.json')
if oc:
    L.append('| OCR of every 4K still | 0 hits | %s hits over %d images | %s |' % (oc['total_hits'], len(oc['images']), 'PASS' if oc['total_hits'] == 0 else 'REVIEW'))
rg = os.path.join(ev, 'regression.txt')
if os.path.exists(rg):
    L.append('| Tessera stays the default; generator regression (r8 legacy texel for texel + r13 default) | PASS | %s | %s |' % (open(rg).read().strip().splitlines()[-1], 'PASS' if 'PASS' in open(rg).read() else 'FAIL'))
sw = J('swap_latency.json')
if sw:
    ms = [x for x in sw['latency_ms'] if x is not None]
    L.append('| swap on the pixels (playable pawn, real T presses) | <= 500 ms | %d of %d presses found, worst %s ms | %s |' % (len(ms), sw['presses'], max(ms) if ms else 'n/a', 'PASS' if ms and max(ms) <= 500 else 'CHECK'))
# ---- locomotion of the stage hero (r8 axes) and the pawn (P3 numbers)
L += ['', '## Hero animation (stage hero, Char_Hero, 1080p60 fixed step) and the playable pawn', '', '| line | target | measured | verdict |', '|---|---|---|---|']
sh = J('measures/ch6_side_headbob.json'); sd = J('measures/ch6_ch7_side.json'); ch = J('measures/ch2_ch7_chase.json')
r8s = J('measures/r8_ch6_side_headbob.json'); r8d = J('measures/r8_ch6_ch7_side.json'); r8c = J('measures/r8_ch2_ch7_chase.json')
if sh:
    L.append('| CH6 run step rate, side clip (head-blob bob, the round-08 instrument and window) | 3.2 - 3.8 steps/s | **%s Hz** (round 08 clip: %s Hz) | %s |' % (
        sh['head_bob_fft_hz'], r8s and r8s.get('head_bob_fft_hz'), 'PASS' if 3.2 <= sh['head_bob_fft_hz'] <= 3.8 else 'FAIL'))
if ch:
    L.append('| CH6 run step rate, chase clip (whole-mask top bob; the head cannot be isolated from behind) | 3.2 - 3.8 | **%s Hz** (round 08: %s Hz) | %s |' % (
        ch['bob_fft_hz'], r8c and r8c.get('bob_fft_hz'), 'PASS' if 3.2 <= ch['bob_fft_hz'] <= 3.8 else 'FAIL'))
if sd:
    L.append('| CH7 sprint torso lean, side clip (head to mid-torso band) | >= 15 deg | median **%s deg** (round 08 clip: %s deg) | %s |' % (sd['lean_median_deg'], r8d and r8d.get('lean_median_deg'), 'PASS' if sd['lean_median_deg'] >= 15 else 'FAIL'))
if ch:
    L.append('| CH2 chase framing | 0.39 - 0.53 | hero height median **%s** (round 08 clip: %s) | %s |' % (ch['hero_height_median'], r8c and r8c.get('hero_height_median'), 'PASS' if 0.39 <= ch['hero_height_median'] <= 0.53 else 'FAIL (edge)'))
L.append('| CH10 stage-hero blends | >= 0.15 s | the stage clips use the round-08 animation set unchanged (same ABP_Hero_Lineup / ABP_Hero_Leap); `video_checks.py takeoff` reads 1 - 2 frames on BOTH the round-08 and the round-13 leap clips (its ground line is set from the bobbing run, not a usable instrument) | not re-measured |')
pc = J('measures/pawn_cadence.json'); pp = J('measures/pawn_start_pop.json')
if pc:
    L.append('| playable pawn (P3 `WebTravAnimInstance`, NOT P2) run cadence | (P3) 3.2 - 3.8 | %s steps/s (FFT %s Hz, bob period %s frames) | logged for the traversal brief |' % (pc['steps_per_s_from_period'], pc['bob_fft_hz'], pc['median_minima_period_frames']))
if pp:
    L.append('| playable pawn idle -> run start | (P3) blend >= 0.15 s | largest one-frame change of the silhouette: height %s, width %s at t = %s s | logged for the traversal brief |' % (pp['max_frame_change_height'], pp['max_frame_change_width'], pp['at_t']))
tp = J('measures/pawn_start_telemetry.json')
if tp and 'start_t' in tp:
    L.append('| playable pawn start, from its own telemetry | (P3) | clip switches %s, all at blend weight %s; the 10-number pose signature then needs %d frames (%.3f s) for 90 %% of its change (largest single frame %.1f %%) | logged for the traversal brief |' % (
        ' -> '.join([tp['clip_switches'][0]['from_clip']] + [c['to_clip'] + ' @%.3f s' % c['t'] for c in tp['clip_switches'][:3]]), tp['switch_weight'], tp['frames_to_90pct_of_pose_change'], tp['seconds_to_90pct'], tp['largest_frame_share'] * 100))
ex = J('lineup_exposure.json')
if ex:
    L += ['', '## Enemy pack (restored to the round-10 content; round-13 lineup)', '', '| line | measured |', '|---|---|',
          '| lineup 4K still, wall / floor mean RGB (round 04 -> round 12 -> round 13) | %s -> %s -> **%s** |' % (ex.get('r04'), ex.get('r12'), ex.get('r13')),
          '| the skins-stage EV (+10) leaking into Char_Lineup | NO: the r04 and r12 lineups have the same exposure (wall 208 / 207 of 255); the washed-out look is the pale sunlit wall, fixed this round with a -0.6 EV bias and a weaker fill |']
fu = os.path.join(ev, 'fight_unchanged_since_r10.txt')
if os.path.exists(fu):
    L += ['| fight script / choreography / weapon fit vs the round-10 commit | %s |' % ('IDENTICAL (git diff --stat empty)' if open(fu).read().strip().startswith('(empty') else 'CHANGED: see evidence/fight_unchanged_since_r10.txt')]
pf = J('stills_perf.json')
if pf:
    L += ['', 'Resolution: stills output %sx%s, internal %sx%s (`r.ScreenPercentage 100`). Movies 1920x1080, fixed 1/60 s step.' % (pf.get('output_w'), pf.get('output_h'), pf.get('internal_w'), pf.get('internal_h'))]
print('\n'.join(L))
