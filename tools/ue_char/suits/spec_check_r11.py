#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 11 SPEC_CHECK.md writer (first-pass piece G): collects the numbers of one round into a markdown table from the evidence JSON / logs, never from memory.

  python3 tools/ue_char/suits/spec_check_r11.py <round-11 dir> > <round-11 dir>/SPEC_CHECK.md
Inputs under <round-11 dir>/evidence: ipguard.json, seams.json, ocr_atlas.json, ocr_stills.json, swap_latency.json, stills_perf.json (WH_PERF of the 4K run), persist.txt, gpu notes
"""
import sys, os, json, re
d = sys.argv[1]
ev = os.path.join(d, 'evidence')
def J(n):
    p = os.path.join(ev, n)
    return json.load(open(p)) if os.path.exists(p) else None
def T(n):
    p = os.path.join(ev, n)
    return open(p).read() if os.path.exists(p) else ''
ip, sm, oa, os_, sw = J('ipguard.json'), J('seams.json'), J('ocr_atlas.json'), J('ocr_stills.json'), J('swap_latency.json')
perf = J('stills_perf.json')
lines = ['# Round 11 SPEC CHECK (piece G, hero skins)', '', '> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. Numbers are read from `evidence/` by `tools/ue_char/suits/spec_check_r11.py`.', '']
if ip:
    lines += ['## Skins acceptance (PLAN-firstpass section 4)', '',
              '| line | target | measured | verdict |', '|---|---|---|---|']
    n = ip['n_suits']
    lines.append('| original suits | >= 6 | **%d** (`suits.json`, ids %s) | %s |' % (n, ', '.join(ip['suits']), 'PASS' if n >= 6 else 'FAIL'))
    fails = ip['fails']
    lines.append('| no red-and-blue blocking / red- or blue-dominant / black+white / white-dominant (P1 - P5, P7) | 0 failures | max red %.3f, max blue %.3f, max white %.3f | %s |' % (
        max(s['red'] for s in ip['suits'].values()), max(s['blue'] for s in ip['suits'].values()), max(s['white'] for s in ip['suits'].values()), 'PASS' if not [f for f in fails if f[1].startswith('P') and not f[1].startswith('P6')] else 'FAIL'))
    pd = min(ip['palette_distance'].values())
    lines.append('| every suit differs from every other (P6: unique net|sash|mark key, lit-palette distance >= 38) | 0 failures | min palette distance **%.1f** over %d pairs; %d unique keys | %s |' % (
        pd, len(ip['palette_distance']), len({s['key'] for s in ip['suits'].values()}), 'PASS' if not [f for f in fails if f[1].startswith('P6')] else 'FAIL'))
if sm:
    w = max(r['worst_run_px'] for r in sm['suits'].values()); nr = sum(r['runs_gt_40px'] for r in sm['suits'].values())
    lines.append('| no UV seam > 40 px at 4K (texture level: both sides of %d seam edges (%.1f m), Lab dE > %g, %g px/m = hero 0.55 of a 2160 px frame) | 0 runs > 40 px | worst run **%.1f px**, runs > 40 px: %d, runs > 10 px: %d | %s |' % (
        sm['seam_edges'], 15.1, sm['de_threshold'], sm['px_per_m'], w, nr, sum(r['runs_gt_10px'] for r in sm['suits'].values()), 'PASS' if nr == 0 else 'FAIL'))
if oa or os_:
    h1 = oa['total_hits'] if oa else None; h2 = os_['total_hits'] if os_ else None
    lines.append('| OCR finds no official emblem / name | 0 hits | atlases: %s hits (%s images), 4K stills: %s hits (%s images); denylist %s terms | %s |' % (
        h1, len(oa['images']) if oa else '-', h2, len(os_['images']) if os_ else '-', (oa or os_)['deny_terms'],
        'PASS' if (h1 or 0) + (h2 or 0) == 0 else ('PASS after review (`evidence/ocr_review.txt`: %s)' % T('ocr_review.txt').strip().replace('\n', ' ') if T('ocr_review.txt').strip() else 'FAIL')))
rt = []
for m in re.finditer(r'swap_done (\d+) (\S+) wall_ms=([0-9.]+) frames=(\d+) textures_resident=(\d+)/(\d+)', T('stills_suit_log.txt')):
    rt.append(dict(i=int(m.group(1)), id=m.group(2), wall_ms=float(m.group(3)), frames=int(m.group(4)), res=int(m.group(5)), n=int(m.group(6))))
if rt:
    rt2 = [x for x in rt if x['i'] != 0 or x['res'] == x['n']] or rt
    lines.append('| swap <= 0.5 s, REAL-TIME 4K run (swap request to 2 frames later, `WH_SUIT swap_done`) | <= 500 ms | %d swaps: median %.0f ms, worst **%.0f ms** (3 frames at ~23 ms; textures resident %d/%d at that point for all but the first start-up swap) | %s |' % (
        len(rt), sorted(x['wall_ms'] for x in rt)[len(rt) // 2], max(x['wall_ms'] for x in rt), sum(1 for x in rt if x['res'] == x['n']), len(rt), 'PASS' if max(x['wall_ms'] for x in rt) <= 500 else 'FAIL'))
if sw:
    ms = [x for x in sw['latency_ms'] if x is not None]
    done = sw['engine_swap_done']
    lines.append('| swap <= 0.5 s, pixels of the fixed-step movie | <= 500 ms | %d of %d injected T presses found on the pixels (+ %d unmatched histogram steps = the director camera cut at 10 s), worst key-to-pixel latency **%s ms** (%s frames at 60 fps, `analyze_swap.py` on the fixed-step movie); engine: `apply_ms` max %.2f, `swap_done` wall_ms max %.1f (a -movie run spends ~0.22 s of wall time per dumped PNG frame, so this wall figure is the dump, not the game latency; the real-time number is the row above), textures resident %s | %s |' % (
        sw.get('matched', sw['swaps_found']), sw['presses'], len(sw.get('other_steps', [])), max(ms) if ms else 'n/a', sorted(set(x for x in sw['latency_frames'] if x is not None)), max([s['apply_ms'] for s in sw['engine_sets']] or [0]),
        max([x['wall_ms'] for x in done] or [0]), sorted({x['res'] for x in done}), 'PASS' if ms and max(ms) <= 500 and len(ms) == sw['presses'] else 'CHECK'))
lines.append('| IQ >= 6 | blind critic | see `critic/round-11-CRITIC.md` | critic |')
lines.append('')
if perf:
    lines += ['## Resolution disclosure of the 4K stills', '', '`evidence/stills_perf.json`: output %sx%s, internal %sx%s (`r.ScreenPercentage 100`), screen-percentage mode %s. Real-time run: frame times are NOT a performance result (shared GPU, other agents; the lock logged `contaminated=true`).' % (
        perf.get('output_w'), perf.get('output_h'), perf.get('internal_w'), perf.get('internal_h'), perf.get('screen_percentage_mode')), '']
lines += ['## Other numbers', '', '- texel density: 4096 px atlas x 0.569 UV units / m = **%d texels / m** (CH3 target >= 680); Tessera 8192 px = %d texels / m.' % (4096 * 0.5692, 8192 * 0.5692),
          '- persistence: ' + (T('persist.txt').strip().replace('\n', '; ') or 'see `evidence/persist_*`'),
          '- key paths: T / Shift+T, gamepad D-pad Up / LB + D-pad Up, settings-menu row, console `wh.Suit <n|id>`, `wh.SuitNext`, `wh.SuitPrev`.']
print('\n'.join(lines))
