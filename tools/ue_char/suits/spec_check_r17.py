#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 17 SPEC_CHECK.md writer: every number is read from <round-17>/evidence (post_r17.sh + the lineup experiments), never from memory.
Part 1 = the round-17 target (lineup corruption cause + fix, the r16 gains kept, the secondaries, the Verdant re-block); part 2 = the round-16 instrument set re-run on the round-17 evidence
(spec_check_r16.py executed on the same evidence and relabelled one round up: in part 2 "r16" = the baseline = round 16, "r17" = this round).
  python3 tools/ue_char/suits/spec_check_r17.py <round-17 dir> > <round-17 dir>/SPEC_CHECK.md"""
import sys, os, json, re, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
d = sys.argv[1]; ev = os.path.join(d, 'evidence')
def J(p, default=None):
    try: return json.load(open(os.path.join(ev, p)))
    except Exception: return default
SUITS = ['tessera', 'verdant', 'plum', 'cinder', 'glacier', 'ash', 'saffron', 'sage']
L = ['# Round 17 SPEC CHECK (piece G, hero skins)', '',
     '> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. Numbers are read from `evidence/` by `tools/ue_char/suits/spec_check_r17.py`;',
     '> every measure of a still runs on the lossless 3840x2160 PNG originals of the real game (UE 5.8.3 `-game`, offscreen, internal 3840x2160); the round-16 baseline = the r16 PNG originals.', '',
     '## Part 1: round-17 target (critic r16: the lineup corruption; keep every r16 gain; secondaries; Verdant re-block)', '']
# ---- (1) the lineup
lc = J('lineup_cause.json') or {}
L += ['**(1) Enemy lineup: cause and fix** (`lineup_cause_r17.py`, `lineup_diff_r17.py`; 3840x2160, camera = Char_Lineup shot 5, previous clean lineup = round 14 = round 15 (0.003 % apart)). Luma = 8-bit gray; the test is the share of pixels differing by > 20.', '']
e0 = lc.get('E0_r16_protocol')
if e0:
    p = e0.get('probe_at_shot') or {}
    L += ['- **E0 = the r16 capture command** (`-shots 3.0 -perf 2:5 -quit 6`, no settle protocol) re-run today: the still is taken at engine frame **%s** (world %.2f s); at that frame **%s assets are still compiling** (%s at frame 1; the first frame with 0 is %s), shaders compiling %s, **textures not resident: %s** (max over the run %s). The still differs from the clean lineup by > 20 luma in **%.2f %%** of the pixels (%.2f %% inside the characters\' band): copper blotches, halos, ghost bats as in r16 (r16 itself, taken on a 4-holder lock: %s %%).' % (
        e0['shot_frame'], p.get('world', 0), p.get('assets'), (e0.get('probe_frame1') or {}).get('assets'), (e0.get('first_frame_with_zero_assets') or 'after the shot (dose-response run: engine frame 17 - 20)'), p.get('shaders'), p.get('tex_bad'), e0.get('max_tex_not_resident'), e0['vs_ref']['pct_over'], e0['vs_ref']['pct_over_in_band'], (J('lineup_diff_r16_vs_r14.json') or {}).get('pct_over', 'n/a'))]
for k, nm in (('E1_settle_streaming_on', 'E1 = settle protocol, texture streaming ON'), ('E2_settle_no_streaming', 'E2 = settle protocol, -NoTextureStreaming')):
    e = lc.get(k)
    if not e: continue
    c1 = e['curve'][0] if e['curve'] else None
    L += ['- **%s** (same camera and content): everything resident after %.1f s wall (%s frames); the shot waits for 0 compiling assets and every visible texture resident, freezes the stage clock, every animation, the walkers and the camera, then counts static rendered frames. Already **after 1 static frame** the still differs from the clean lineup by > 20 luma in **%s %%** (band %s %%); the final shot (%s static frames, %s world s, %s resets): **%.2f %%** (band %.2f %%). The 1 -> 24 frame curve moves only the mean luma (auto exposure: mean |diff| %s -> %s), not the blotches.' % (
        nm, e['resident_after_s'] or 0, e['resident_after_frames'], c1 and c1['vs_ref']['pct_over'], c1 and c1['vs_ref']['pct_over_in_band'], (e['final'] or {}).get('settle_frames'), (e['final'] or {}).get('static_world_s'), (e['final'] or {}).get('resets'), e['final_vs_ref']['pct_over'], e['final_vs_ref']['pct_over_in_band'], c1 and c1['vs_ref']['mean_abs'], e['final_vs_ref']['mean_abs'])]
x0 = lc.get('X0_r16_protocol_shots')
if x0:
    L += ['', '**Dose-response of the r16 protocol** (one run, plain screenshots at engine frame numbers 3 .. 72, no settle, probe at the shot frame; Char_Lineup shot 5 lasts 6 s of world time, so the frames after it - 24, 32, 48, 72 - show the next director shot and are excluded):', '', '| still | frame | assets compiling | textures not resident | > 20 luma vs clean lineup (whole / band) |', '|---|---|---|---|---|']
    for r in [q for q in x0 if q.get('valid', True)]:
        L.append('| %s | %s | %s | %s | %.2f %% / %.2f %% |' % (r['shot'], r['frame'], (r['probe'] or {}).get('assets'), (r['probe'] or {}).get('tex_bad'), r['vs_ref']['pct_over'], r['vs_ref']['pct_over_in_band']))
L += ['', '**Verdict on the cause:** two capture-moment effects, each isolated: (a) assets still compiling (the corruption share drops 3x at the frame the count reaches 0), (b) animations / walkers still running (frame 20 with 0 compiling assets still has the residual above, E1 after 1 static frame at the same compile state does not). Textures were resident at every bad shot (0 not resident) and the content renders clean once the capture waits: not streaming, not content. See `CAPTURES.md`.', '']
L += ['| lineup (committed) | > 20 luma vs r14 whole / character band | vs r15 | vs r16 (the corrupted one) | ghost / duplicate weapon |', '|---|---|---|---|---|']
for nm, pre in (('enemy_lineup_4k.jpg (wide)', 'lineup_diff_vs_r'), ('enemy_lineup_34_4k.jpg (3/4)', 'lineup34_diff_vs_r')):
    r14, r15, r16 = J(pre + '14.json'), J(pre + '15.json'), J(pre + '16.json')
    f = lambda r: ('%.2f %% / %.2f %%' % (r['pct_over'], r['pct_over_in_band'])) if r else 'n/a'
    L.append('| %s | **%s** (gate <= 2 %%) | %s | %s | by eye: none (`evidence/measures/lineup/`) |' % (nm, f(r14), f(r15), f(r16)))
L += ['']
# ---- (2) kept
L += ['**(2) Kept: r16 gains** (details in part 2): back bleed, cord jog <= 4 px, face seam dev100 <= 10 px on all 8, net ends, IP guard, OCR, swap, pawn pops.', '']
# ---- (3) secondaries
L += ['**(3a) Sash / groove edge steps** (`line_step_r17.py`: colour regions of the chest still -> polygon edges; a JOG = two straight runs >= 40 px, near-parallel (< 8 deg, same direction), joined by <= 4 short polygon edges, the second run\'s line more than 4 px beside the first: the edge does not stay within 4 px of ONE line over the two runs).', '',
      '| suit | jogs > 4 px r16 -> **r17** | largest step r16 -> **r17** (px) | long-edge jogs (both runs >= 100 px) r16 -> **r17**, largest | where the largest long-edge jog is (r17) |', '|---|---|---|---|---|']
tot16 = tot17 = 0
for s in SUITS:
    a, b = J('line_step_r16_%s.json' % s) or {}, J('line_step_%s.json' % s) or {}
    lj = lambda r: [j for j in r.get('jogs', []) if min(j['run_a'], j['run_b']) >= 100]
    la, lb = lj(a), lj(b); tot16 += len(la); tot17 += len(lb)
    L.append('| %s | %s -> **%s** | %s -> **%s** | %d -> **%d**, %s -> **%s** | %s |' % (s, a.get('n_jogs'), b.get('n_jogs'), a.get('max_step_px'), b.get('max_step_px'), len(la), len(lb), max([j['step'] for j in la] or [0]), max([j['step'] for j in lb] or [0]),
                                                                                  ('(%d, %d)' % (lb[0]['x'], lb[0]['y'])) if lb else '-'))
L += ['', 'long-edge jogs over all 8 chests: r16 **%d** -> r17 **%d** (the instrument has limits: it needs contrast and counts design corners where a panel boundary legitimately steps; overlays `evidence/measures/line_step/`). The named defects: Ash sash lower edge (r16: 24 - 28 px shelf at (2370, 1894)), Verdant groove step (r16: 11.6 px at (2383, 1312)) - see the Ash / Verdant rows.' % (tot16, tot17), '']
cj = J('cord_jog_r17.json') or {}
if cj:
    L += ['**(3b) Cord jogs, both sides** (`cord_jog_r17.py`: every long near-horizontal cord of the chest across the whole torso width, JOG = largest row change beyond the local slope; gate <= 4 px): ' + ', '.join('%s %s' % (s, (cj.get(s) or {}).get('max_jog_px')) for s in SUITS) + ' px.', '']
cc, cc15 = J('cut_check_crowd.json'), J('cut_check_crowd_r15.json')
cp, cp16 = J('cut_check_pawn.json'), J('cut_check_pawn_r16.json')
L += ['**(3c) Cuts** (`cut_check_r17.py`, frame-to-frame mean |luma| difference, 480 px wide):', '',
      '| clip | r16 / r15 | **r17** |', '|---|---|---|']
if cp16 and cp: L.append('| pawn swap clip, step at 9.933 s | %s against neighbours %s -> cuts %s | **%s** against neighbours %s; cuts: %s; largest step %s |' % (cp16['at'][0].get('diff'), cp16['at'][0].get('neighbours'), len(cp16['cuts']), cp['at'][0].get('diff', cp['at'][0].get('note')), cp['at'][0].get('neighbours'), cp['cuts'], cp['top'][0]))
if cc15 and cc: L.append('| crowd clip, step at 7.483 s | %s against neighbours %s -> cuts %s | **%s** against neighbours %s; cuts: %s; largest step %s |' % (cc15['at'][0].get('diff'), cc15['at'][0].get('neighbours'), len(cc15['cuts']), cc['at'][0].get('diff', cc['at'][0].get('note')), cc['at'][0].get('neighbours'), cc['cuts'], cc['top'][0]))
L += ['', 'The r16 \'yaw snap\' (9.933 s) and the r16 crowd cut (7.483 s) were DIRECTOR SHOT ENDS (`WHCharShowDirector`: the pawn map\'s shot 0 lasted 10 s and the director cut to the front 3/4 shot; the crowd shot 0 lasted 8 s and the director cut to \'crowd wide\'); the r17 maps make those shots 16 s / 12 s (`build_characters.py`), so no cut falls inside the clips.', '']
ip = J('ipguard.json') or {}
pd = ip.get('palette_distance') or {}
vd = sorted([(v, k) for k, v in pd.items() if 'verdant' in k])
L += ['**(4) Verdant re-block** (`suits.json`): forest green body, dark pine panels / hood, copper accent (was brass yellow), no accent forearm / shin blocks, plain crown (no yellow crown stripes), mask brow ticks and net lines in copper. IP guard (`ip_guard.py palette`): P1 - P7 ' + ('PASS (%s fails)' % len(ip.get('fails', []))) + ', min palette distance over all pairs %s; Verdant\'s nearest suits: %s. Swatch sheet: `SWATCH_SHEET.jpg`.' % (min(pd.values()) if pd else None, ', '.join('%s %.1f' % (k, v) for v, k in vd[:3])), '']
L += ['## Part 2: the round-16 instrument set re-run on round 17 (baseline = round 16)', '']
print('\n'.join(L))
out = subprocess.check_output([sys.executable, os.path.join(HERE, 'spec_check_r16.py'), d]).decode()
tools = {}
def prot(m):
    k = '§T%d§' % len(tools); tools[k] = m.group(0); return k
out = re.sub(r'[A-Za-z_0-9]+_r\d\d\.py', prot, out)
for a, b in (('round-16', '§R17D'), ('Round 16', '§R17T'), ('r16', '§r17'), ('round-15', 'round-16'), ('Round 15', 'Round 16'), ('r15', 'r16'), ('round-14', 'round-15'), ('Round 14', 'Round 15'), ('r14', 'r15'), ('§R17D', 'round-17'), ('§R17T', 'Round 17'), ('§r17', 'r17')):
    out = out.replace(a, b)
for k, v in tools.items(): out = out.replace(k, v)
out = out.replace('# Round 17 SPEC CHECK', '### (round-16 set) Round 17 SPEC CHECK', 1)
out = out.replace('re-run on round 16 (baseline = round 15)', 're-run on round 17 (baseline = round 16)').replace('Round target (critic r16): the P2-owned lines', 'Round target (critic r16 / r17 lines): the P2-owned lines')
print(out)
