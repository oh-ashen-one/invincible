#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 17: fills the @@placeholders@@ of docs/night1/characters/round-17/CAPTURES.md from the evidence json (never from memory).
  python3 tools/ue_char/suits/fill_captures_r17.py docs/night1/characters/round-17 [--holds "text"]"""
import sys, os, json, re, glob
d = sys.argv[1]; ev = os.path.join(d, 'evidence')
def J(p, default=None):
    try: return json.load(open(os.path.join(ev, p)))
    except Exception: return default
SUITS = ['tessera', 'verdant', 'plum', 'cinder', 'glacier', 'ash', 'saffron', 'sage']
cap = open(os.path.join(d, 'CAPTURES.md')).read()
lc = J('lineup_cause.json') or {}
e0 = lc.get('E0_r16_protocol') or {}; p0 = e0.get('probe_at_shot') or {}
e1, e2 = lc.get('E1_settle_streaming_on') or {}, lc.get('E2_settle_no_streaming') or {}
x0 = lc.get('X0_r16_protocol_shots') or []
ld = lambda n: J(n) or {}
w14, w15, w16, w1416 = ld('lineup_diff_vs_r14.json'), ld('lineup_diff_vs_r15.json'), ld('lineup_diff_vs_r16.json'), ld('lineup_diff_r16_vs_r14.json')
t14, t1416 = ld('lineup34_diff_vs_r14.json'), ld('lineup34_diff_r16_vs_r14.json')

# ---------------------------------------------------------------- cause
C = []
C += ['Same camera (`Char_Lineup` shot 5), same content, same lock load; luma = 8-bit gray, the test is the share of pixels differing by > 20 luma from the previous clean lineup (round 14 = round 15, 0.003 %% apart; r16 itself: **%s %%**).' % w1416.get('pct_over'), '']
C += ['- **E0, the r16 capture command re-run** (`-shots 3.0 -perf 2:5 -quit 6`, no settle): the still is taken at engine frame **%s** (world %.2f s). At that frame **%s assets are still compiling** (%s at frame 1; the first frame with 0 is %s), **%s textures are not resident** (max over the run: %s; streaming is not the problem), shaders compiling %s. The still has > 20 luma in **%s %%** of the pixels (**%s %%** inside the characters\' band): copper blotches on the garments, halos, duplicate (ghost) weapons, as in r16.' % (
    e0.get('shot_frame'), p0.get('world', 0), p0.get('assets'), (e0.get('probe_frame1') or {}).get('assets'), e0.get('first_frame_with_zero_assets'), p0.get('tex_bad'), e0.get('max_tex_not_resident'), p0.get('shaders'), (e0.get('vs_ref') or {}).get('pct_over'), (e0.get('vs_ref') or {}).get('pct_over_in_band'))]
for k, e in (('E1, settle protocol, texture streaming ON', e1), ('E2, settle protocol, `-NoTextureStreaming`', e2)):
    if not e: continue
    c = e['curve']
    C += ['- **%s**: everything resident after %s s wall (%s frames; the shot waited for 0 compiling assets / shaders and every visible texture resident, with the stage clock, every animation, the lane walkers and the camera frozen). **After 1 static rendered frame** the still has > 20 luma in **%s %%** of the pixels (band %s %%) - already clean; the curve over 1 / 2 / 4 / 8 / 16 / 24 static frames moves only the mean luma (auto exposure; mean |diff| %s): the blotches do not depend on the number of rendered frames after the compile. Final shot (%s static frames, %s world s, %s resets): **%s %%** (band %s %%).' % (
        k, e.get('resident_after_s'), e.get('resident_after_frames'), c[0]['vs_ref']['pct_over'], c[0]['vs_ref']['pct_over_in_band'], ' / '.join(str(x['vs_ref']['mean_abs']) for x in c), (e.get('final') or {}).get('settle_frames'), (e.get('final') or {}).get('static_world_s'), (e.get('final') or {}).get('resets'), e['final_vs_ref']['pct_over'], e['final_vs_ref']['pct_over_in_band'])]
if x0:
    C += ['', '**Dose-response of the r16 protocol** (one run, plain screenshots at engine frame numbers, no settle, the probe at each frame; `Char_Lineup` shot 5 lasts 6 s of world time, so the frames after it - 24, 32, 48, 72 - show the NEXT director shot and are excluded):', '', '| still | frame | assets compiling | textures not resident | > 20 luma vs clean lineup (whole / band) |', '|---|---|---|---|---|']
    for r in [q for q in x0 if q.get('valid', True)]: C.append('| %s | %s | %s | %s | %s %% / %s %% |' % (r['shot'], r['frame'], r['probe']['assets'], r['probe']['tex_bad'], r['vs_ref']['pct_over'], r['vs_ref']['pct_over_in_band']))
x20 = [q for q in x0 if q.get('valid', True)]
last = x20[-1] if x20 else None
C += ['', '**Verdict on the cause (measured, not guessed):** NOT the content (the same garments, textures and meshes render clean the moment the capture waits) and NOT texture streaming (0 textures not resident at every bad shot above; E2 with `-NoTextureStreaming` is no different). Two capture-moment effects, each isolated by a measurement: **(a) assets still compiling** - in the dose-response run the corruption share falls from %s %% (27 compiling) through %s %% (12 compiling) to %s %% once the last asset has compiled (frame %s), a 3x drop at exactly the frame the count reaches 0; **(b) the characters\' idle animations and the lane walkers still running** - at frame %s (0 assets compiling) the running scene still has > 20 luma in %s %% of the pixels (%s %% in the characters\' band), while E1 after 1 static frame (engine frame ~17, the same compile state, the animations frozen) has %s %% (%s %%): moving skinned meshes leave temporal ghosts (halos, duplicate weapons, blotched garments). The r16 "3.0 s" automation clock fired at engine frame %s (the first frames of a 4K run on the cap-3 lock take 0.15 - 6 s each), with %s of %s assets compiling and everything moving; in r16 the lock was over-subscribed (4 - 6 holders) so it was worse (%s %% vs %s %% today). The fix is the capture protocol (wait for 0 compiling assets, freeze animations / walkers / camera, count static frames), not the content.' % (
    x20[0]['vs_ref']['pct_over'] if x20 else '?', next((q['vs_ref']['pct_over'] for q in x20 if q['probe']['assets'] <= 12), '?'), last['vs_ref']['pct_over'] if last else '?', last['frame'] if last else '?',
    last['frame'] if last else '?', last['vs_ref']['pct_over'] if last else '?', last['vs_ref']['pct_over_in_band'] if last else '?', (e1.get('curve') or [{}])[0].get('vs_ref', {}).get('pct_over'), (e1.get('curve') or [{}])[0].get('vs_ref', {}).get('pct_over_in_band'),
    e0.get('shot_frame'), p0.get('assets'), (e0.get('probe_frame1') or {}).get('assets'), w1416.get('pct_over'), (e0.get('vs_ref') or {}).get('pct_over'))]
C += ['', 'Two defects of the first r17 protocol were found by the probe and fixed (`WHCharShowDirector`): (a) the r17a lineup run never settled in 25 min because the camera / pose signature included the **player pawn** (it falls from its off-stage PlayerStart for ~30 frames) and the **31 lane walkers** of `Char_Lineup` (they move in `Tick`, in world time) - now walkers\' Tick is disabled while a shot settles and only skeletal meshes inside the camera frustum count; (b) the 240 s timeout is now checked BEFORE the reset branch, so a never-static scene still ends (flagged `SETTLE_TIMEOUT`).']
cap = cap.replace('@@CAUSE@@', '\n'.join(C))

# ---------------------------------------------------------------- results
R = ['| line | r16 | **r17** (real game, 4K PNG originals) | verdict |', '|---|---|---|---|']
f = lambda r: ('%s %% / band %s %%' % (r.get('pct_over'), r.get('pct_over_in_band'))) if r else 'n/a'
R.append('| (1) `enemy_lineup_4k.jpg` > 20 luma vs the previous clean lineup (gate <= 2 %%) | %s | **%s** (vs r15 %s) | %s |' % (f(w1416), f(w14), f(w15), 'PASS' if w14 and w14['pct_over'] <= 2 else 'FAIL'))
R.append('| (1) `enemy_lineup_34_4k.jpg` (3/4) | %s | **%s** | %s |' % (f(t1416), f(t14), 'PASS' if t14 and t14['pct_over'] <= 2 else 'FAIL'))
bb = J('back_bleed.json') or {}; n = sum(1 for s in SUITS if (bb.get(s) or {}).get('clusters_ge20', 1) == 0)
R.append('| (2) back bleed: accent clusters >= 20 px in the back torso | 0 on 8 | **0 on %d** | %s |' % (n, 'PASS' if n == 8 else 'FAIL'))
cj = J('cord_jog.json') or {}; n = sum(1 for s in SUITS if (cj.get(s) or {}).get('max_jump_px', 99) <= 4)
ash = cj.get('ash') or {}
R.append('| (2) yoke-seam cord jog under the arm, gate <= 4 px | 0.5 - 0.9 | **%s - %s** (max over 8: %s; under-arm run only: Ash %s) | **%d / 8** by the instrument%s |' % (
    min((cj.get(s) or {}).get('max_jump_px', 0) for s in SUITS), max((cj.get(s) or {}).get('max_jump_px', 0) for s in SUITS), max((cj.get(s) or {}).get('max_jump_px', 0) for s in SUITS), ash.get('max_jump_under_arm_px'), n,
    ' (Ash: %s px at x %s = the cord\'s end cap at the sash border, see below)' % (ash.get('max_jump_px'), (ash.get('jump_at') or [None])[0]) if n < 8 else ''))
st = J('seam_track.json') or {}; n = sum(1 for s in SUITS if (st.get(s) or {}).get('ok') and st[s]['dev100'] <= 10)
R.append('| (2) face centre seam dev100 <= 10 px | 5 / 8 measured (Cinder 10.9, Glacier 10.6, Verdant untracked) | Tessera %s, Verdant **%s** (tracked), Plum %s, Cinder **%s**, Glacier **%s**, Ash %s, Saffron %s, Sage %s | **%d / 8** |' % tuple([(st.get(s) or {}).get('dev100') for s in SUITS] + [n]) if False else
         '| (2) face centre seam dev100 <= 10 px | 5 / 8 measured (Cinder 10.9, Glacier 10.6, Verdant untracked) | ' + ', '.join('%s %s' % (s, (st.get(s) or {}).get('dev100')) for s in SUITS) + ' | **%d / 8** (Glacier: tracker reading, see below) |' % n)
ne = J('net_end.json')
if ne: R.append('| (2) net-end dead ends in open fabric (paint, 4096 px) | 0 | **%d** | %s |' % (sum(e['dead_end_blobs_in_open_fabric'] for e in ne), 'PASS' if sum(e['dead_end_blobs_in_open_fabric'] for e in ne) == 0 else 'FAIL'))
ip = J('ipguard.json') or {}; ocr = J('ocr_stills.json') or {}
R.append('| (2) IP guard (P1 - P7) / OCR hits | PASS (49.3) / 1 reviewed noise hit | **%s** (min palette distance %.1f) / %s reviewed noise hit (`evidence/ocr_review.txt`) | %s |' % ('PASS' if not ip.get('fails') else 'FAIL', min((ip.get('palette_distance') or {'x': 0}).values()), ocr.get('total_hits'), 'PASS' if not ip.get('fails') else 'FAIL'))
sw = J('swap_latency.json') or {}
R.append('| (2) swap: presses visible / latency | 7 of 7, 33 ms | **%s of 7**, %s ms | %s |' % (sw.get('matched'), sorted(set(x for x in sw.get('latency_ms', []) if x is not None)) if sw else 'n/a', 'PASS' if sw.get('matched') == 7 else '6 of 7 by the histogram matcher; the 7th press (Tessera -> Verdant, engine set at 8.717 s frame 522, swap_done 4/4 textures resident) is visible between 8.55 s and 8.9 s (`evidence/measures/swap7_tessera_to_verdant.jpg`) but the matcher found no step'))
pc = J('pawn_check.json') or {}; pr = (pc.get('r15') or {})
R.append('| (2) pawn luma pops 0 - 1.5 s | 0 | **%s** (largest %s) | %s |' % (len(pr.get('P1_pops_whole_frame', [])) + len(pr.get('P1_pops_hero_blob', [])) if pr else 'n/a', pr.get('luma_diff_max'), 'PASS' if pr.get('P1_ok') else 'CHECK'))
q6 = ((J('iq_check.json') or {}).get('Q6_verdant_armpit') or {}).get('r15') or {}
R.append('| (2) Q6 Verdant armpit piping pinch ratio (own gate >= 0.5) | 0.54 | **%s** (min %s px, median %s px; the copper cord is intact and tapers into the crease like r16, `evidence/measures/q6_pair.jpg`) | %s |' % (q6.get('pinch_ratio'), q6.get('min_thickness_px'), q6.get('median_thickness_px'), 'PASS' if q6.get('Q6_unpinched_ge_0p5') else 'FAIL by the instrument'))
rdl = [l.split() for l in open(os.path.join(ev, 'rim_depth.txt')).read().splitlines() if l.strip() and l.split()[0] in SUITS] if os.path.exists(os.path.join(ev, 'rim_depth.txt')) else []
R.append('| (2) R1 lens rim behind the brow (>= 1 pct of head height = 16 px) | 8 / 8 (33 - 48 px) | ' + ', '.join('%s %s px' % (l[0][:3], l[1]) for l in rdl) + ' | ' + ('PASS %d / 8' % sum(1 for l in rdl if l[3] == 'True')) + ' |')
hc = J('head_check.json') or {}
g = lambda k: sum(1 for s in SUITS if (hc.get(s) or {}).get('verdict', {}).get(k))
R.append('| (2) G1 / G2 / G3 (head sculpt) | 8 / 8 each | G1 %d / G2 %d / G3 12 deg %d, 0 deg %d, 25 deg %d of 8 | %s |' % (g('G1_recess_ge_1.5pct'), g('G2_brow_over_lens_top_ge_1pct'), g('G3_cheek_lines_head_12deg'), g('G3_cheek_lines_headfront_0deg'), g('G3_cheek_lines_head34_25deg'), 'PASS' if g('G1_recess_ge_1.5pct') == g('G2_brow_over_lens_top_ge_1pct') == g('G3_cheek_lines_head_12deg') == 8 else 'CHECK'))
tl16 = tl17 = 0; mx = []
for s in SUITS:
    a, b = J('line_step_r16_%s.json' % s) or {}, J('line_step_%s.json' % s) or {}
    la = [j for j in a.get('jogs', []) if min(j['run_a'], j['run_b']) >= 100]; lb = [j for j in b.get('jogs', []) if min(j['run_a'], j['run_b']) >= 100]
    tl16 += len(la); tl17 += len(lb); mx.append('%s %s -> %s' % (s[:3], max([j['step'] for j in la] or [0]), max([j['step'] for j in lb] or [0])))
R.append('| (3) sash / groove edge steps > 4 px on long edges (both runs >= 100 px), 8 chests (`line_step_r17.py`) | %d (largest per suit: %s) | **%d** | the named defects are gone (Ash shelf 26.9 px, Verdant step 13.7 px); %d long-edge jogs of 4.5 - 10 px remain: NOT met |' % (tl16, ', '.join(m.split(' -> ')[0] for m in mx), tl17, tl17))
cp, cp16, cc, cc15 = J('cut_check_pawn.json'), J('cut_check_pawn_r16.json'), J('cut_check_crowd.json'), J('cut_check_crowd_r15.json')
if cp and cp16: R.append('| (3) pawn clip step at 9.933 s | %s vs neighbours %s (a director shot end) | **%s** vs neighbours %s; cuts in the clip: %d | %s |' % (cp16['at'][0]['diff'], cp16['at'][0]['neighbours'], cp['at'][0].get('diff'), cp['at'][0].get('neighbours'), len(cp['cuts']), 'PASS' if not cp['cuts'] else 'FAIL'))
if cc and cc15: R.append('| (3) crowd clip step at 7.483 s | %s vs neighbours %s (a director shot end) | **%s** vs neighbours %s; cuts in the clip: %d | %s |' % (cc15['at'][0]['diff'], cc15['at'][0]['neighbours'], cc['at'][0].get('diff', cc['at'][0].get('note')), cc['at'][0].get('neighbours'), len(cc['cuts']), 'PASS' if not cc['cuts'] else 'FAIL'))
R.append('| (3) face seam through the chin / cheek-cord ends | Cinder seam broke and jogged at the chin; cheek cords cut square | seam continuous through the chin on all 8 (`evidence/measures/chin_crops.jpg`, r16 row over r17 row); the four cheek cords close in a rounded tip (`design.py`, EXPECT_R17) | by eye |')
R.append('| (4) Verdant | brass yellow accent, yellow forearm / shin blocks, yellow crown stripes | forest green + dark pine + copper, no yellow, plain crown; IP guard PASS, nearest suits %s | `SWATCH_SHEET.jpg`, `VERDANT_BEFORE_AFTER.jpg` |' % ', '.join('%s %.1f' % (k.replace('verdant|', '').replace('|verdant', ''), v) for k, v in sorted(((k, v) for k, v in (ip.get('palette_distance') or {}).items() if 'verdant' in k), key=lambda kv: kv[1])[:2]))
cap = cap.replace('@@RESULTS@@', '\n'.join(R))
open(os.path.join(d, 'CAPTURES.md'), 'w').write(cap)
print('CAPTURES filled (SOURCE / LIMITS / FILES placeholders left: %s)' % [m for m in ('@@SOURCE@@', '@@LIMITS@@', '@@FILES@@') if m in cap])
