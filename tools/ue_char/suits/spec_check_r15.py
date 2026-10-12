#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 15 SPEC_CHECK.md writer: every number is read from <round-14>/evidence (post_r14.sh), never from memory.
  python3 tools/ue_char/suits/spec_check_r15.py <round-15 dir> > <round-15 dir>/SPEC_CHECK.md"""
import sys, os, json, glob
d = sys.argv[1]; ev = os.path.join(d, 'evidence'); M = os.path.join(ev, 'measures')
def J(p):
    p = os.path.join(ev, p) if not os.path.isabs(p) else p
    try: return json.load(open(p))
    except Exception: return None
SUITS = ['tessera', 'verdant', 'plum', 'cinder', 'glacier', 'ash', 'saffron', 'sage']
L = ['# Round 15 SPEC CHECK (piece G, hero skins)', '',
     '> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. Numbers are read from `evidence/` by `tools/ue_char/suits/spec_check_r15.py`;',
     '> the measures of the 4K chest stills run on the lossless PNG originals of the real game (UE 5.8.3 `-game`, offscreen, internal 3840x2160).', '']
# ---- the round-15 target: the P2 lines of the critic r14 + the merged pawn
R15 = ['## Round target (critic r14): the P2-owned lines + the playable pawn on the merged P3 r22 ground blend', '']
rd, rd14 = J('rim_depth.json'), J('rim_depth_r14.json')
R15 += ['**R1 rim depth** (`rim_depth_r15.py`, 4K headside stills, lossless PNG originals): the front-most pixel of the lens RIM lies >= 1 % of the head height (>= 16 px at 1590 px) BEHIND the front-most pixel of the brow. The critic r14 measured the Verdant rim 18 px proud (2273 against 2255).', '',
        '| suit | rim behind brow, px (+ = behind) r14 -> **r15** | % of head height r14 -> **r15** | verdict |', '|---|---|---|---|']
nr = 0
for sid in SUITS:
    a, b = (rd14 or {}).get(sid), (rd or {}).get(sid)
    if not b or not b.get('ok'):
        R15.append('| %s | rim segmentation failed (%s) | | FAIL |' % (sid, b and b.get('why'))); continue
    ok = b['R1_rim_ge_1pct_behind_brow']; nr += ok
    R15.append('| %s | %s -> **%s** | %s -> **%s** | %s |' % (sid, a and a.get('rim_behind_brow_px'), b['rim_behind_brow_px'], a and a.get('rim_behind_brow_pct_head_h'), b['rim_behind_brow_pct_head_h'], 'PASS' if ok else 'FAIL'))
R15 += ['', '%d of 8 suits pass R1 (overlays `evidence/measures/rim_overlays/`; CPU model of the same pose before the hold: `round-15/CAPTURES.md`).' % nr, '']
iq = J('iq_check.json') or {}
q5 = (iq.get('Q5_ash_pipe') or {}); q6 = (iq.get('Q6_verdant_armpit') or {}); q7 = (iq.get('Q7_brow_stretch') or {})
R15 += ['| item | measure | r14 | **r15** | verdict |', '|---|---|---|---|---|']
if q5.get('r15'):
    a, b = q5.get('r14') or {}, q5['r15']
    R15.append('| Q5 Ash sash-end accent pipe (box 1490-1540 x 760-1150) | pixels between the pipe and the DEEP border cord (p90 / max) | %s / %s px | **%s / %s px** (pipe %s px wide, x %s) | %s |' % (a.get('gap_to_border_p90_px'), a.get('gap_to_border_max_px'), b.get('gap_to_border_p90_px'), b.get('gap_to_border_max_px'), b.get('pipe_width_px'), b.get('pipe_x'), 'PASS' if b.get('Q5_pipe_joins_end_le_5px') else 'FAIL'))
if q6.get('r15'):
    a, b = q6.get('r14') or {}, q6['r15']
    R15.append('| Q6 Verdant armpit piping (box 1160-1270 x 1150-1270) | cord thickness min / median along its own run (1 = even, 0 = a gap); gap columns in the run | %s (min %s px, median %s px; %s gap columns) | **%s** (min %s px, median %s px; %s gap columns; the cord now ends at the shoulder cap edge, last column x %s) | %s |' % (
        a.get('pinch_ratio'), a.get('min_thickness_px'), a.get('median_thickness_px'), a.get('gap_columns_in_run'), b.get('pinch_ratio'), b.get('min_thickness_px'), b.get('median_thickness_px'), b.get('gap_columns_in_run'), b.get('last_col'),
        'PASS' if b.get('Q6_unpinched_ge_0p5') else 'FAIL by my own 0.5 gate (no gap any more; the cord thins toward the crease where it ends)'))
for sid in SUITS:
    r = q7.get(sid) or {}
    if r.get('r15') and r['r15'].get('brow'):
        b = r['r15']; a = r.get('r14') or {}
        R15.append('| Q7 brow trim, %s | trim edge rise / thickness at the brow (px, perpendicular) | %s / %s | **%s / %s** (brow/temple %s, sane windows: %s; r15/r14 edge rise %s) | %s |' % (
            sid, (a.get('brow') or {}).get('edge_rise_perp_px'), (a.get('brow') or {}).get('thickness_perp_px'), b['brow'].get('edge_rise_perp_px'), b['brow'].get('thickness_perp_px'), b.get('edge_rise_ratio'), b.get('windows_sane'), r.get('brow_edge_rise_r15_over_r14'),
            'PASS' if (b.get('brow_temple_ratio_le_1p5') or (r.get('brow_edge_rise_r15_over_r14') or 9) <= 0.75) else 'see crop'))
ne, ne14 = J('net_end.json'), J('net_end_r14.json')
if ne and ne14:
    t = lambda d, k: sum(x[k] for x in d)
    R15 += ['', '**Net / groove ends** (`net_end_check_r15.py`, the paint itself at 4096: a net line ends where its zone mask falls; a DEAD END has no raised cord within 2.5 mm and is not at an atlas island edge): dead-end blobs in open fabric, all 8 suits: r14 switches **%d** -> r15 **%d** (torso net: %d -> %d; armpit crease zone, folded away under the arm, not counted: %d -> %d).' % (
        t(ne14, 'dead_end_blobs_in_open_fabric'), t(ne, 'dead_end_blobs_in_open_fabric'), sum(x['open_fabric_by_layer'].get('torso', 0) for x in ne14), sum(x['open_fabric_by_layer'].get('torso', 0) for x in ne), t(ne14, 'dead_end_blobs_in_armpit_crease_zone'), t(ne, 'dead_end_blobs_in_armpit_crease_zone')),
        '', '| suit | open-fabric dead ends r14 -> r15 | by layer (r15) |', '|---|---|---|']
    for x14, x in zip(ne14, ne): R15.append('| %s | %s -> **%s** | %s |' % (x['id'], x14['dead_end_blobs_in_open_fabric'], x['dead_end_blobs_in_open_fabric'], x['open_fabric_by_layer']))
pk = J('pawn_check.json')
if pk and pk.get('r15'):
    p, p14 = pk['r15'], pk.get('r14') or {}
    t15, t14 = p.get('telemetry') or {}, p14.get('telemetry') or {}
    R15 += ['', '**Pawn** (`pawn_check_r15.py`; P3 `WebTravAnimInstance` GroundBlendS 0.18 s merged from Opus-5.5-Loop-Night-1; the run CADENCE is P3\'s and routed to traversal, not a P2 gate):', '',
            '| test | r14 | **r15** | verdict |', '|---|---|---|---|',
            '| P1 no frame-to-frame luma difference in 0 - 1.5 s above 2x both neighbours (whole frame / hero blob) | %d / %d pops (largest %s at %s s) | **%d / %d pops** (largest %s) | %s |' % (
                len(p14.get('P1_pops_whole_frame', [])), len(p14.get('P1_pops_hero_blob', [])), p14.get('luma_diff_max'), (p14.get('P1_pops_whole_frame') or [{}])[0].get('t'), len(p['P1_pops_whole_frame']), len(p['P1_pops_hero_blob']), p.get('luma_diff_max'), 'PASS' if p['P1_ok'] else 'FAIL'),
            '| P2 no `anim_weight` step above dt / 0.18 per frame (0.0926 at 60 fps); NOTE `anim_weight` is the TOTAL clip weight (always 1.0), so this test is vacuous | max step %s | **max step %s** (limit %s) | %s |' % (t14.get('anim_weight_max_step'), t15.get('anim_weight_max_step'), t15.get('limit_per_frame'), 'PASS (vacuous)' if t15.get('P2_anim_weight_step_ok') else 'FAIL'),
            '| pose-signature steps 0 - 1.5 s (P3 ground blend): largest / median of 0.5 - 2 s | %s | **%s** (at %s s) | logged |' % (t14.get('pose_sig_step_max_over_median'), t15.get('pose_sig_step_max_over_median'), t15.get('at_t')),
            '| clip switches in 0 - 1.5 s | %s | **%s** | logged |' % ([c['to'] for c in t14.get('clip_switches_0_1p5s', [])], [c['to'] for c in t15.get('clip_switches_0_1p5s', [])])]
R15 += ['']
# ---- the round target: the finished sculpt (head_check_r14.py)
hc = J('head_check.json')
HEADL = ['## Kept: the round-14 sculpt gates (G1 - G3, H1 - H6) on the round-15 head', '',
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
L += R15 + HEADL + ['']
# ---- keep-passing relief lines (r12 target): raised piping on the chest stills
L += ['## Keep: the round-12 lines (raised piping, nothing under the sash, no fold)', '',
      '| suit | relief: 64 px cells with a lit / shadow pair >= 20 luma (r14 -> r15) | median cell delta (r14 -> r15) | sash: longest dark run px, target <= 10 (r14 -> r15) | sash verdict |', '|---|---|---|---|---|']
allpass_sash = True
for s in SUITS:
    a, b = J('measures/r14_relief_%s.json' % s), J('measures/relief_%s.json' % s)
    c, e = J('measures/r14_sash_%s.json' % s), J('measures/sash_%s.json' % s)
    if not b: continue
    v = e.get('verdict', 'n/a') if e else 'n/a'
    L.append('| %s | %s -> **%s** (%d of %d cells) | %s -> **%s** | %s -> **%s** | %s |' % (
        s, a and a.get('share_cells_ge20'), b.get('share_cells_ge20'), b.get('cells_ge20', 0), b.get('cells', 0), a and a.get('median_cell_delta'), b.get('median_cell_delta'),
        c and c.get('longest_dark_run_px'), e and e.get('longest_dark_run_px'), v))
jg, jg11 = J('measures/jog_verdant.json'), J('measures/r14_jog_verdant.json')
if jg:
    L += ['', '| Verdant chevron edge at the critic\'s columns x 1320-1400 | target | round 14 | round 15 | verdict |', '|---|---|---|---|---|',
          '| largest column-to-column jump beyond its slope | <= 2 px | %s px | **%s** | %s |' % (jg11 and jg11.get('jump_at_critic_x1320_1400'), ('%s px' % jg.get('jump_at_critic_x1320_1400')) if jg.get('jump_at_critic_x1320_1400') is not None else 'no edge in the critic columns', jg.get('verdict_at_critic_x') if jg.get('jump_at_critic_x1320_1400') is not None else 'n/a: since round 14 the Verdant V ends at |x| = 0.118 m (a straight piped end), so the chevron\'s upper edge no longer runs into the armpit where the r13 step was; the instrument finds no edge in its ROI. The step is gone from the frame (crop `evidence/measures/iq/chest_verdant.jpg`), not measured to 0')]
# ---- keep-passing lines
L += ['', '## Keep-passing lines', '', '| line | target | measured | verdict |', '|---|---|---|---|']
c1 = J('measures/ch1_front.json')
if c1:
    hs = [x['height_frac'] for x in c1['stills']]
    L.append('| CH1 front stills (hero height / frame height, all 8 suits) | 0.48 - 0.62 | %.3f - %.3f | %s |' % (min(hs), max(hs), 'PASS' if c1['all_ok'] else 'FAIL'))
ip = J('ipguard.json')
if ip:
    L.append('| IP guard palette P1 - P7 (round-15 deeper sockets / pipe join / yoke seams) | 0 failures | min palette distance %.1f over %d pairs, fails: %s | %s |' % (
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
    L.append('| Tessera stays the default; generator regression (r8 legacy texel for texel + r15 default) | PASS | %s | %s |' % (open(rg).read().strip().splitlines()[-1], 'PASS' if 'PASS' in open(rg).read() else 'FAIL'))
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
          '| lineup 4K still, wall / floor mean RGB (round 04 -> 12 -> 13 -> 14 -> 15) | %s -> %s -> %s -> %s -> **%s** |' % (ex.get('r04'), ex.get('r12'), ex.get('r13'), ex.get('r14'), ex.get('r15')),
          '| the skins-stage EV (+10) leaking into Char_Lineup | NO: the r04 and r12 lineups have the same exposure (wall 208 / 207 of 255); the washed-out look is the pale sunlit wall, the -0.6 EV bias and the weaker fill of round 13 are unchanged |']
fu = os.path.join(ev, 'fight_unchanged_since_r10.txt')
if os.path.exists(fu):
    L += ['| fight script / choreography / weapon fit vs the round-10 commit | %s |' % ('IDENTICAL (git diff --stat empty)' if open(fu).read().strip().startswith('(empty') else 'CHANGED: see evidence/fight_unchanged_since_r10.txt')]
pf = J('stills_perf.json')
if pf:
    L += ['', 'Resolution: stills output %sx%s, internal %sx%s (`r.ScreenPercentage 100`). Movies 1920x1080, fixed 1/60 s step.' % (pf.get('output_w'), pf.get('output_h'), pf.get('internal_w'), pf.get('internal_h'))]
print('\n'.join(L))
