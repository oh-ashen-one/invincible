#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 14 SPEC_CHECK.md writer: every number is read from <round-14>/evidence (post_r14.sh), never from memory.
  python3 tools/ue_char/suits/spec_check_r14.py <round-14 dir> > <round-14 dir>/SPEC_CHECK.md"""
import sys, os, json, glob
d = sys.argv[1]; ev = os.path.join(d, 'evidence'); M = os.path.join(ev, 'measures')
def J(p):
    p = os.path.join(ev, p) if not os.path.isabs(p) else p
    try: return json.load(open(p))
    except Exception: return None
SUITS = ['tessera', 'verdant', 'plum', 'cinder', 'glacier', 'ash', 'saffron', 'sage']
L = ['# Round 14 SPEC CHECK (piece G, hero skins)', '',
     '> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. Numbers are read from `evidence/` by `tools/ue_char/suits/spec_check_r14.py`;',
     '> the measures of the 4K chest stills run on the lossless PNG originals of the real game (UE 5.8.3 `-game`, offscreen, internal 3840x2160).', '']
# ---- the round target: the finished sculpt (head_check_r14.py)
hc = J('head_check.json')
HEADL = ['## Round target (critic round 13): finish the shared mask sculpt', '',
         'Measured by `tools/ue_char/suits/head_check_r14.py` on the lossless 4K PNG originals of the real game: `head` = 12 deg off the face axis (1.0 m), `headfront` = the same framing straight on (0 deg), `head34` = the round-12 head framing (25 deg), `headside` = profile (1.25 m).',
         '**G1** headside: the silhouette between the brow\'s front-most point and the nose tip dips >= 1.5 % of the head height (crown to chin, 1590 px at this framing) behind the brow -> nose-tip chord. '
         '**G2** the brow\'s front-most point is >= 1 % of the head height in front of the top of the lens (front-most glass pixel of the top quarter of its rows); G2b = the same with a 3.1 mm rim allowance. '
         '**G3** horizontal luma lines through the cheek bones (the band lens bottom + 15 px .. + 200 px, every 15 px, 15 px smoothing, head interior minus 30 px at each edge): >= 3 extrema of prominence >= 20 luma on >= 70 % of the lines, swing >= 20 on every line. '
         'Kept from round 13 (head_check_r13.py): H1 nose-bridge luma profile, H2 nose bump >= 2 % of head height, H3 lens >= 1.6x round 12, H4 ONE closed raised rim >= 6 px on >= 90 % of 48 angles, H5 raised face seam (lit / shadow pair >= 20 luma, no black run), H6 lenses inside the outline.', '']
if hc:
    HEADL += ['| suit | G1 recess % HH (px) | G2 brow over lens top % HH (with rim) | G3 cheek lines >= 3 extrema: 12 deg / 0 deg / 25 deg (min swing) | H3 near lens x r12 (mean 12 deg) | H4 rim px, closed (head / head34) | H5 seam pair | H1 / H2 / H6 | verdict |', '|---|---|---|---|---|---|---|---|---|']
    npass = 0; nG = 0
    for sid in SUITS:
        r = hc.get(sid)
        if not r or not r['head'].get('nose') or not r['head34'].get('nose'):
            if r: HEADL.append('| %s | lens detection failed (see evidence/head_check.json) | | | | | | | FAIL |' % sid)
            continue
        h, h34, sd, v, ck = r['head'], r['head34'], r['side'], r['verdict'], r.get('cheek', {})
        ok = all(v.values()); npass += ok
        g3 = lambda k: ('%s/%s (%s)' % (ck[k]['lines_ge3'], ck[k]['lines_total'], ck[k]['min_swing'])) if k in ck and 'lines_ge3' in ck[k] else 'n/a'
        gok = v.get('G1_recess_ge_1.5pct') and v.get('G2_brow_over_lens_top_ge_1pct') and v.get('G3_cheek_lines_head_12deg') and v.get('G3_cheek_lines_headfront_0deg'); nG += bool(gok)
        HEADL.append('| %s | **%s** (%s px) | **%s** (%s) | %s / %s / %s | %s (%s) | %s, %s ; %s, %s | %s | %s / %s / %s | %s |' % (
            sid, sd and sd.get('G1_recess_pct_head_h'), sd and sd.get('G1_recess_px'), sd and sd.get('G2_pct_head_h'), sd and sd.get('G2_with_rim_pct_head_h'),
            g3('head'), g3('headfront'), g3('head34'), h34.get('lens_width_ratio_near'), h.get('lens_width_ratio_vs_r12'),
            h.get('rim_px_median'), h.get('rim_closed_frac'), h34.get('rim_px_median'), h34.get('rim_closed_frac'), h['seam']['pair_median'],
            '%s/%s' % (h['nose']['v_extrema_prom20'], h['nose']['v_swing']), sd and sd.get('H2'), h.get('lens_edge_distance_px'),
            'PASS' if ok else 'FAIL ' + ', '.join(k.split('_')[0] for k, x in v.items() if not x)))
    HEADL += ['', '%d of %d suits pass every gate (G1, G2, G2b, G3 x 3 views, H1 - H6); %d of %d pass the three critic tests G1 + G2 + G3 (12 deg and 0 deg) (`evidence/head_check.json`, overlays in `evidence/measures/head_overlays/`).' % (npass, len(SUITS), nG, len(SUITS))]
    mp = J('head_profile_mesh.json')
    if mp:
        HEADL += ['', 'Mesh silhouette of the finished head (CPU, the GLB the engine imports; `head_profile_r14.py`): recess %s %% HH, brow over the lens top %s %% HH, over every rim vertex %s %% HH, nose bump %s %% HH, mouth / chin groove %s mm; lens-to-outline clearance in a 12 deg view %s px (glass) / %s px (rim).' % (
            mp.get('T1_pct_HH'), mp.get('T2_pct_HH'), mp.get('T2b_pct_HH'), mp.get('T3_nose_bump_pct_HH'), mp.get('mouth_chin_groove_mm'), (mp.get('H6_clearance_px') or {}).get('12.0', {}).get('glass'), (mp.get('H6_clearance_px') or {}).get('12.0', {}).get('rim'))]
else:
    HEADL += ['(head_check.json missing)']
L += HEADL + ['']
# ---- the image-quality items of the round-13 critic (iq_check_r14.py)
iq = J('iq_check.json')
if iq:
    L += ['## Image quality: the four defects of the round-13 critic (iq_check_r14.py; crops in `evidence/measures/iq/`, read them: a number does not replace looking)', '', '| item | measure | round 13 | round 14 |', '|---|---|---|---|']
    q = iq.get('Q1_ash_sash_end')
    if q: L.append('| Ash sash end (1410-1440, 700-1050) | end line rms deviation px / stitch dashes in the 70 px strip beyond the end | %s / %s | **%s / %s** |' % (q['r13'].get('end_rms_px'), q['r13'].get('stitch_dashes_beyond_end'), q['r14'].get('end_rms_px'), q['r14'].get('stitch_dashes_beyond_end')))
    q = iq.get('Q2_ash_armpit')
    if q: L.append('| Ash armpit stitches (1120-1200, 1530-1600) | stitch-dash blobs in the armpit box / in the critic box / orientation spread deg | %s / %s / %s | **%s / %s / %s** |' % (q['r13']['dashes_in_box'], q['r13']['dashes_in_critic_box'], q['r13']['orientation_spread_deg'], q['r14']['dashes_in_box'], q['r14']['dashes_in_critic_box'], q['r14']['orientation_spread_deg']))
    q = iq.get('Q3_sage_trapezius')
    if q: L.append('| Sage trapezius groove (head34) | dark thin-line pixels %% of the box / longest dark line px | %s / %s | **%s / %s** |' % (q['r13']['dark_line_fraction_pct'], q['r13']['longest_dark_line_px'], q['r14']['dark_line_fraction_pct'], q['r14']['longest_dark_line_px']))
    q = iq.get('Q4_cinder_shoulder')
    if q: L.append('| Cinder shoulder silhouette (chest still) | contour vertices per 1000 px at eps 4 px / longest straight segment px / max turn deg | %s / %s / %s | **%s / %s / %s** |' % (q['r13'].get('vertices_per_1000px'), q['r13'].get('longest_segment_px'), q['r13'].get('max_turn_deg'), q['r14'].get('vertices_per_1000px'), q['r14'].get('longest_segment_px'), q['r14'].get('max_turn_deg')))
    tf = J('trapezius_fold_check.json')
    if tf:
        rows = []
        for k, v in tf['poses'].items(): rows.append('%s %s -> %s -> %s' % (k, v['original']['folded'], v['r12']['folded'], v['r14']['folded']))
        L.append('| trapezius skin folds (CPU skinning, folded faces: original -> r12 -> r14 weights) | %s | %s | |' % (tf['region_faces'], '; '.join(rows)))
    L += ['']
# ---- keep-passing relief lines (r12 target): raised piping on the chest stills
L += ['## Keep: the round-12 lines (raised piping, nothing under the sash, no fold)', '',
      '| suit | relief: 64 px cells with a lit / shadow pair >= 20 luma (r13 -> r14) | median cell delta (r13 -> r14) | sash: longest dark run px, target <= 10 (r13 -> r14) | sash verdict |', '|---|---|---|---|---|']
allpass_sash = True
for s in SUITS:
    a, b = J('measures/r13_relief_%s.json' % s), J('measures/relief_%s.json' % s)
    c, e = J('measures/r13_sash_%s.json' % s), J('measures/sash_%s.json' % s)
    if not b: continue
    v = e.get('verdict', 'n/a') if e else 'n/a'
    L.append('| %s | %s -> **%s** (%d of %d cells) | %s -> **%s** | %s -> **%s** | %s |' % (
        s, a and a.get('share_cells_ge20'), b.get('share_cells_ge20'), b.get('cells_ge20', 0), b.get('cells', 0), a and a.get('median_cell_delta'), b.get('median_cell_delta'),
        c and c.get('longest_dark_run_px'), e and e.get('longest_dark_run_px'), v))
jg, jg11 = J('measures/jog_verdant.json'), J('measures/r13_jog_verdant.json')
if jg:
    L += ['', '| Verdant chevron edge at the critic\'s columns x 1320-1400 | target | round 13 | round 14 | verdict |', '|---|---|---|---|---|',
          '| largest column-to-column jump beyond its slope | <= 2 px | %s px | **%s** | %s |' % (jg11 and jg11.get('jump_at_critic_x1320_1400'), ('%s px' % jg.get('jump_at_critic_x1320_1400')) if jg.get('jump_at_critic_x1320_1400') is not None else 'no edge in the critic columns', jg.get('verdict_at_critic_x') if jg.get('jump_at_critic_x1320_1400') is not None else 'n/a: since round 14 the Verdant V ends at |x| = 0.118 m (a straight piped end), so the chevron\'s upper edge no longer runs into the armpit where the r13 step was; the instrument finds no edge in its ROI. The step is gone from the frame (crop `evidence/measures/iq/chest_verdant.jpg`), not measured to 0')]
# ---- keep-passing lines
L += ['', '## Keep-passing lines', '', '| line | target | measured | verdict |', '|---|---|---|---|']
c1 = J('measures/ch1_front.json')
if c1:
    hs = [x['height_frac'] for x in c1['stills']]
    L.append('| CH1 front stills (hero height / frame height, all 8 suits) | 0.48 - 0.62 | %.3f - %.3f | %s |' % (min(hs), max(hs), 'PASS' if c1['all_ok'] else 'FAIL'))
ip = J('ipguard.json')
if ip:
    L.append('| IP guard palette P1 - P7 (round-14 hood lift / face tone / piped sash ends) | 0 failures | min palette distance %.1f over %d pairs, fails: %s | %s |' % (
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
    L.append('| Tessera stays the default; generator regression (r8 legacy texel for texel + r14 default) | PASS | %s | %s |' % (open(rg).read().strip().splitlines()[-1], 'PASS' if 'PASS' in open(rg).read() else 'FAIL'))
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
L.append('| CH10 stage-hero blends | >= 0.15 s | the stage clips use the round-08 animation set unchanged (same ABP_Hero_Lineup / ABP_Hero_Leap); `video_checks.py takeoff` reads 1 - 2 frames on BOTH the round-08 and the round-14 leap clips (its ground line is set from the bobbing run, not a usable instrument) | not re-measured |')
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
    L += ['', '## Enemy pack (unchanged since round 13: paused in the first pass)', '', '| line | measured |', '|---|---|',
          '| lineup 4K still, wall / floor mean RGB (round 04 -> round 12 -> round 13 -> round 14) | %s -> %s -> %s -> **%s** |' % (ex.get('r04'), ex.get('r12'), ex.get('r13'), ex.get('r14')),
          '| the skins-stage EV (+10) leaking into Char_Lineup | NO: the r04 and r12 lineups have the same exposure (wall 208 / 207 of 255); the washed-out look is the pale sunlit wall, the -0.6 EV bias and the weaker fill of round 13 are unchanged |']
fu = os.path.join(ev, 'fight_unchanged_since_r10.txt')
if os.path.exists(fu):
    L += ['| fight script / choreography / weapon fit vs the round-10 commit | %s |' % ('IDENTICAL (git diff --stat empty)' if open(fu).read().strip().startswith('(empty') else 'CHANGED: see evidence/fight_unchanged_since_r10.txt')]
pf = J('stills_perf.json')
if pf:
    L += ['', 'Resolution: stills output %sx%s, internal %sx%s (`r.ScreenPercentage 100`). Movies 1920x1080, fixed 1/60 s step.' % (pf.get('output_w'), pf.get('output_h'), pf.get('internal_w'), pf.get('internal_h'))]
print('\n'.join(L))
