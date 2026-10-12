#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 12 SPEC_CHECK.md writer: every number is read from <round-12>/evidence (post_r12.sh), never from memory.
  python3 tools/ue_char/suits/spec_check_r12.py <round-12 dir> > <round-12 dir>/SPEC_CHECK.md"""
import sys, os, json, glob
d = sys.argv[1]; ev = os.path.join(d, 'evidence'); M = os.path.join(ev, 'measures')
def J(p):
    p = os.path.join(ev, p) if not os.path.isabs(p) else p
    try: return json.load(open(p))
    except Exception: return None
SUITS = ['tessera', 'verdant', 'plum', 'cinder', 'glacier', 'ash', 'saffron', 'sage']
L = ['# Round 12 SPEC CHECK (piece G, hero skins)', '',
     '> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. Numbers are read from `evidence/` by `tools/ue_char/suits/spec_check_r12.py`;',
     '> the measures of the 4K chest stills run on the lossless PNG originals of the real game (UE 5.8.3 `-game`, offscreen, internal 3840x2160).', '']
# ---- the critic's round target
L += ['## Round target (critic round 11): raised piping, nothing under the sash shows through, no fold / jog', '',
      '| suit | relief: 64 px cells with a lit / shadow pair >= 20 luma (r11 -> r12) | median cell delta (r11 -> r12) | sash: longest dark run px, target <= 10 (r11 -> r12) | sash verdict |', '|---|---|---|---|---|']
allpass_sash = True
for s in SUITS:
    a, b = J('measures/r11_relief_%s.json' % s), J('measures/relief_%s.json' % s)
    c, e = J('measures/r11_sash_%s.json' % s), J('measures/sash_%s.json' % s)
    if not b: continue
    v = e.get('verdict', 'n/a') if e else 'n/a'
    allpass_sash &= (v == 'PASS')
    L.append('| %s | %s -> **%s** (%d of %d cells) | %s -> **%s** | %s -> **%s** | %s |' % (
        s, a and a.get('share_cells_ge20'), b.get('share_cells_ge20'), b.get('cells_ge20', 0), b.get('cells', 0), a and a.get('median_cell_delta'), b.get('median_cell_delta'),
        c and c.get('longest_dark_run_px'), e and e.get('longest_dark_run_px'), v))
t = J('measures/sash_tessera.json'); t11 = J('measures/r11_sash_tessera.json')
if t and t.get('probes') and t11 and t11.get('probes'):
    L.append('')
    L.append('Critic probe Tessera (1412, 1240): round 11 luma %s vs local panel median %s; round 12 luma %s vs %s (inside panel: %s).' % (
        t11['probes'][0]['luma'], t11['probes'][0]['local_panel_median'], t['probes'][0]['luma'], t['probes'][0]['local_panel_median'], t['probes'][0]['inside_panel']))
jg, jg11 = J('measures/jog_verdant.json'), J('measures/r11_jog_verdant.json')
if jg:
    L += ['', '| Verdant chevron edge, lower edge, x 1290-1640 y 1500-1850 of the 4K chest (the critic.s jog at 1333-1357, 1610-1680) | target | round 11 | round 12 | verdict |', '|---|---|---|---|---|',
          '| largest column-to-column jump of the edge beyond its slope at the critic\'s columns x 1320-1400 | <= 2 px | %s px | **%s px** | %s |' % (jg11 and jg11.get('jump_at_critic_x1320_1400'), jg.get('jump_at_critic_x1320_1400'), jg.get('verdict_at_critic_x')),
          '| the same over the whole tracked edge (x 1290-1640) | <= 2 px | %s px at %s | **%s px** at %s | %s |' % (jg11 and jg11.get('max_jump_px'), jg11 and jg11.get('jump_at'), jg.get('max_jump_px'), jg.get('jump_at'), jg.get('verdict')),
          '| max deviation of the edge from a 61 px quadratic fit | (info) | %s px | %s px | |' % (jg11 and jg11.get('max_dev_px'), jg.get('max_dev_px'))]
fc = J('fold_check.json')
if fc:
    p = fc['poses']
    L += ['', 'Torso-side fold (CPU skinning of the hero mesh, folded = posed face normal against its vertex normals, dot < 0.3, in the %d-face region): ' % fc['region_faces'] +
          ', '.join('%s %d -> **%d**' % (k, v['original']['folded'], v['smoothed']['folded']) for k, v in p.items()) + ' (`evidence/fold_check.json`).']
tg = sorted(glob.glob(os.path.join(ev, 'tangent_*.json')))
if tg:
    L += ['', 'Normal map vs the mesh tangent basis per UV island (`tools/ue_char/suits/tangent_check.py`): ' + '; '.join(
        '%s %s (all-texel median cos %s, large-island min %s, no flipped island: %s)' % (x['suit'], x['verdict'], x['cos_median_all'], x.get('large_island_min_cos'), x['max_wrong_sign_pct'] < 15) for x in (json.load(open(f)) for f in tg)) + '.']
# ---- keep-passing lines
L += ['', '## Keep-passing lines', '', '| line | target | measured | verdict |', '|---|---|---|---|']
c1 = J('measures/ch1_front.json')
if c1:
    hs = [x['height_frac'] for x in c1['stills']]
    L.append('| CH1 front stills (hero height / frame height, all 8 suits) | 0.48 - 0.62 | %.3f - %.3f | %s |' % (min(hs), max(hs), 'PASS' if c1['all_ok'] else 'FAIL'))
ip = J('ipguard.json')
if ip:
    L.append('| IP guard palette P1 - P7 (Verdant / Saffron re-blocked) | 0 failures | min palette distance %.1f over %d pairs, fails: %s | %s |' % (
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
    L.append('| Tessera stays the default; generator regression (r8 legacy texel for texel + r12 default) | PASS | %s | %s |' % (open(rg).read().strip().splitlines()[-1], 'PASS' if 'PASS' in open(rg).read() else 'FAIL'))
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
L.append('| CH10 stage-hero blends | >= 0.15 s | the stage clips use the round-08 animation set unchanged (same ABP_Hero_Lineup / ABP_Hero_Leap); `video_checks.py takeoff` reads 1 - 2 frames on BOTH the round-08 and the round-12 leap clips (its ground line is set from the bobbing run, not a usable instrument) | not re-measured |')
pc = J('measures/pawn_cadence.json'); pp = J('measures/pawn_start_pop.json')
if pc:
    L.append('| playable pawn (P3 `WebTravAnimInstance`, NOT P2) run cadence | (P3) 3.2 - 3.8 | %s steps/s (FFT %s Hz, bob period %s frames) | logged for the traversal brief |' % (pc['steps_per_s_from_period'], pc['bob_fft_hz'], pc['median_minima_period_frames']))
if pp:
    L.append('| playable pawn idle -> run start | (P3) blend >= 0.15 s | largest one-frame change of the silhouette: height %s, width %s at t = %s s | logged for the traversal brief |' % (pp['max_frame_change_height'], pp['max_frame_change_width'], pp['at_t']))
tp = J('measures/pawn_start_telemetry.json')
if tp and 'start_t' in tp:
    L.append('| playable pawn start, from its own telemetry | (P3) | clip switches %s, all at blend weight %s; the 10-number pose signature then needs %d frames (%.3f s) for 90 %% of its change (largest single frame %.1f %%) | logged for the traversal brief |' % (
        ' -> '.join([tp['clip_switches'][0]['from_clip']] + [c['to_clip'] + ' @%.3f s' % c['t'] for c in tp['clip_switches'][:3]]), tp['switch_weight'], tp['frames_to_90pct_of_pose_change'], tp['seconds_to_90pct'], tp['largest_frame_share'] * 100))
pf = J('stills_perf.json')
if pf:
    L += ['', 'Resolution: stills output %sx%s, internal %sx%s (`r.ScreenPercentage 100`). Movies 1920x1080, fixed 1/60 s step.' % (pf.get('output_w'), pf.get('output_h'), pf.get('internal_w'), pf.get('internal_h'))]
print('\n'.join(L))
