#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 16 SPEC_CHECK.md writer: every number is read from <round-16>/evidence (post_r16.sh), never from memory.
Part 1 = the round-16 target (the four 4K defects of the r15 critic + Q6 + the limb net ends), part 2 = the round-15 instrument set re-run on the round-16 evidence
(spec_check_r15.py executed with its baseline files renamed: in part 2 "r15" = the baseline = round 15, "r16" = this round).
  python3 tools/ue_char/suits/spec_check_r16.py <round-16 dir> > <round-16 dir>/SPEC_CHECK.md"""
import sys, os, json, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
d = sys.argv[1]; ev = os.path.join(d, 'evidence')
def J(p):
    try: return json.load(open(os.path.join(ev, p)))
    except Exception: return None
SUITS = ['tessera', 'verdant', 'plum', 'cinder', 'glacier', 'ash', 'saffron', 'sage']
L = ['# Round 16 SPEC CHECK (piece G, hero skins)', '',
     '> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. Numbers are read from `evidence/` by `tools/ue_char/suits/spec_check_r16.py`;',
     '> every measure of a still runs on the lossless 3840x2160 PNG originals of the real game (UE 5.8.3 `-game`, offscreen, internal 3840x2160); the round-15 baseline = the r15 PNG originals.', '',
     '## Part 1: round-16 target (critic r15 image-quality defects; first-pass acceptance line IQ >= 6)', '']
ok_all = {}
bb, bb15 = J('back_bleed.json') or {}, J('back_bleed_r15.json') or {}
L += ['**(1) Back bleed** (`back_bleed_r16.py`, 8 back stills at 4K): accent-family pixels (the front emblem / sash fill colour and its darker shade, colour direction within 20 deg) inside the back torso mask; gate: no cluster >= 20 px.', '',
      '| suit | clusters >= 20 px r15 -> **r16** | largest cluster px r15 -> **r16** | accent px in the mask r15 -> **r16** | verdict |', '|---|---|---|---|---|']
n = 0
for s in SUITS:
    a, b = bb15.get(s) or {}, bb.get(s) or {}
    ok = bool(b.get('ok')) and b.get('clusters_ge20', 1) == 0; n += ok
    L.append('| %s | %s -> **%s** | %s -> **%s** | %s -> **%s** | %s |' % (s, a.get('clusters_ge20'), b.get('clusters_ge20'), a.get('largest'), b.get('largest'), a.get('accent_px'), b.get('accent_px'), 'PASS' if ok else 'FAIL'))
ok_all['back'] = n == 8
L += ['', '%d of 8 backs pass (overlays `evidence/measures/back_bleed/`, mask yellow, accent pixels magenta). All 8 back stills are committed at 4K (`stills/skin_<suit>_back_4k.jpg`).' % n, '']
cj, cj15 = J('cord_jog.json') or {}, J('cord_jog_r15.json') or {}
L += ['**(2) Cord jogs** (`cord_jog_r16.py`, 8 chest stills: the yoke seam cord tracked across the image-left torso side under the arm, the largest row step between neighbouring columns beyond the local slope; gate <= 4 px). The r15 critic boxes: Verdant ~(1300, 1310), Ash / Cinder the same side.', '',
      '| suit | max jump r15 -> **r16** (px) | at (x, y) r16 | tracked columns r16 | verdict |', '|---|---|---|---|---|']
n = 0
for s in SUITS:
    a, b = cj15.get(s) or {}, cj.get(s) or {}
    ok = bool(b.get('ok')) and b.get('max_jump_px', 99) <= 4; n += ok
    L.append('| %s | %s -> **%s** | %s | %s | %s |' % (s, a.get('max_jump_px'), b.get('max_jump_px'), b.get('jump_at'), b.get('columns'), 'PASS' if ok else 'FAIL'))
ok_all['jog'] = n == 8
L += ['', '%d of 8 chest stills pass (overlays `evidence/measures/cord_jog/`).' % n, '']
st, st15 = J('seam_track.json') or {}, J('seam_track_r15.json') or {}
L += ['**(3) Face centre seam** (`seam_track_r16.py`, 8 headfront stills: the light seam cord tracked row by row from the crown to the chin; `dev100` = the largest lateral change over 100 rows; gate <= 10 px). r16: the headfront portrait follows the head bone (`WHShot.bHeadLock`, log `evidence/headlock_log.txt`).', '',
      '| suit | dev100 r15 -> **r16** (px) | lateral range r15 -> **r16** | residual from a line r16 | tracked rows r16 | verdict |', '|---|---|---|---|---|---|']
n = 0
for s in SUITS:
    a, b = st15.get(s) or {}, st.get(s) or {}
    ok = bool(b.get('ok')) and b.get('dev100', 99) <= 10; n += ok
    L.append('| %s | %s -> **%s** | %s -> **%s** | %s | %s | %s |' % (s, a.get('dev100'), b.get('dev100'), a.get('range_x'), b.get('range_x'), b.get('resid_max'), b.get('n_rows'), 'PASS' if ok else 'FAIL'))
ok_all['seam'] = n == 8
L += ['', '%d of 8 headfront stills pass (overlays `evidence/measures/seam_track/`).' % n]
h2 = J('seam_track_hold2.json')
if h2:
    L += ['', 'Supplementary (NOT the committed set): the same content in this round\'s hold 2 (13:01, same maps except Saffron\'s arm ring cords; idle phase differs): dev100 ' + ', '.join('%s %s' % (s_, (h2.get(s_) or {}).get('dev100')) for s_ in SUITS) + ' - the residual depends on the idle phase (the lower face is partly neck-weighted, the head lock follows the head bone only).']
L += ['']
ne, ne15 = J('net_end.json'), J('net_end_r15.json')
if ne and ne15:
    t = lambda x, k: sum(e[k] for e in x)
    L += ['**(4a) Net ends** (`net_end_check_r15.py --n 4096`, the paint itself): dead-end blobs in open fabric r15 **%d** -> r16 **%d** (armpit crease zone, folded under the arm, not counted: %d -> %d).' % (
        t(ne15, 'dead_end_blobs_in_open_fabric'), t(ne, 'dead_end_blobs_in_open_fabric'), t(ne15, 'dead_end_blobs_in_armpit_crease_zone'), t(ne, 'dead_end_blobs_in_armpit_crease_zone')), '',
          '| suit | open fabric r15 -> **r16** | by layer r16 |', '|---|---|---|']
    for a, b in zip(ne15, ne): L.append('| %s | %s -> **%s** | %s |' % (b['id'], a['dead_end_blobs_in_open_fabric'], b['dead_end_blobs_in_open_fabric'], b['open_fabric_by_layer']))
    ok_all['net'] = t(ne, 'dead_end_blobs_in_open_fabric') == 0
iq = J('iq_check.json') or {}
q6 = iq.get('Q6_verdant_armpit') or {}
if q6.get('r15'):
    a, b = q6.get('r14') or {}, q6['r15']
    ok_all['q6'] = bool(b.get('Q6_unpinched_ge_0p5'))
    L += ['', '**(4b) Q6 Verdant armpit cord** (`iq_check_r15.py`, its keys: r14 = the baseline = r15 stills, r15 = this round): pinch ratio (min / median thickness along the run) r15 %s -> **r16 %s** (min %s px, median %s px, %s gap columns); gate >= 0.5: **%s**.' % (
        a.get('pinch_ratio'), b.get('pinch_ratio'), b.get('min_thickness_px'), b.get('median_thickness_px'), b.get('gap_columns_in_run'), 'PASS' if ok_all['q6'] else 'FAIL')]
L += ['', '**(4c) Ash notch smear (~1480, 1170)** and **(5) the no-new-defect crop pass**: read by eye on `evidence/measures/crops/crops_<suit>.jpg` (r15 row over r16 row); the list is in `CAPTURES.md`.', '',
      '**Summary of the measured gates:** ' + ', '.join('%s %s' % (k, 'PASS' if v else 'FAIL') for k, v in ok_all.items()), '', '## Part 2: the round-15 instrument set re-run on round 16 (baseline = round 15)', '']
print('\n'.join(L))
src = open(os.path.join(HERE, 'spec_check_r15.py')).read()
for a, b in (("'rim_depth_r14.json'", "'rim_depth_r15.json'"), ("'net_end_r14.json'", "'net_end_r15.json'"), ("'measures/r14_jog_verdant.json'", "'measures/r15_jog_verdant.json'"), ("r14_relief_", "r15_relief_"), ("r14_sash_", "r15_sash_")):
    src = src.replace(a, b)
buf = io.StringIO(); sys.argv = ['spec_check_r15.py', d]
with contextlib.redirect_stdout(buf): exec(compile(src, 'spec_check_r15.py', 'exec'), {'__name__': '__main__'})
txt = buf.getvalue()
for a, b in (('_r15.py', '§TOOL15'), ('_r14.py', '§TOOL14'), ('_r12.py', '§TOOL12'), ('round-15', '§R16D'), ('Round 15', '§R16T'), ('r15', '§r16'), ('round-14', 'round-15'), ('Round 14', 'Round 15'), ('r14', 'r15'), ('§R16D', 'round-16'), ('§R16T', 'Round 16'), ('§r16', 'r16'), ('§TOOL15', '_r15.py'), ('§TOOL14', '_r14.py'), ('§TOOL12', '_r12.py')):
    txt = txt.replace(a, b)
txt = txt.replace('# Round 16 SPEC CHECK', '### (round-15 set) Round 16 SPEC CHECK', 1)
print(txt)
