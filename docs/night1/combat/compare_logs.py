#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat: compare the Unreal fight telemetry with the browser fight log (same script, same schema).
#   compare_logs.py <ue_dir> <browser_dir> <out.md> [<out.json>]
# Reads fight_summary.json, fight_events.jsonl, fight_beats.jsonl, fight_telemetry.csv from both.
import csv, json, os, sys

ue_dir, br_dir, out_md = sys.argv[1:4]
out_json = sys.argv[4] if len(sys.argv) > 4 else None


def load(d):
    S = json.load(open(os.path.join(d, 'fight_summary.json')))
    E = [json.loads(l) for l in open(os.path.join(d, 'fight_events.jsonl')) if l.strip()]
    B = [json.loads(l) for l in open(os.path.join(d, 'fight_beats.jsonl')) if l.strip()]
    T = list(csv.DictReader(open(os.path.join(d, 'fight_telemetry.csv'))))
    return S, E, B, T


Su, Eu, Bu, Tu = load(ue_dir)
Sb, Eb, Bb, Tb = load(br_dir)


def moves_after(T, rt, span=0.7):
    """first non-free move that starts within [rt, rt+span] (telemetry move column)"""
    prev = None
    for r in T:
        t = float(r['rt'])
        if t < rt - 1e-6:
            prev = r['move']; continue
        if t > rt + span: break
        if r['move'] != prev and r['move'] != 'free': return r['move'], round(t - rt, 3)
        prev = r['move']
    return '-', None


def first_event(E, rt, prefixes, span=0.9):
    for e in E:
        if rt - 1e-6 <= e['rt'] <= rt + span and any(e['ev'].startswith(p) for p in prefixes): return e['ev']
    return '-'


def ts_stats(T):
    ts = [float(r['timescale']) for r in T]
    slow = sum(1 for v in ts if v < 0.999) / 60.0
    return min(ts), slow


keys = ['frames', 'real_s', 'game_s', 'enemies', 'enemies_alive', 'hero_hp', 'hero_focus', 'damage_taken', 'hits', 'whiffs', 'kos', 'launches',
        'air_hits', 'finishers', 'dodges', 'perfect_dodges', 'web_hits', 'enemy_melee_hits', 'shots', 'shot_hits', 'hitstops', 'slowmos',
        'min_timescale', 'slowmo_real_s', 'beats', 'beats_fired']
rows = []
for k in keys:
    rows.append((k, Su.get(k, '-'), Sb.get(k, '-')))
mu, su = ts_stats(Tu); mb, sb = ts_stats(Tb)

L = ['# P5 combat round 01: Unreal fight vs browser fight (same script)', '',
     '> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.', '',
     'Unreal: `%s`  |  browser: `%s`' % (ue_dir, br_dir), '',
     'Both runs: fixed 1/60 s real step, seeded RNG, the same beats at the same REAL times. The worlds differ (Unreal: Combat_Street test '
     'street; browser: an open street spot in the browser city) and each engine has its own RNG stream, so the fights diverge after the first '
     'random choice; compare the rules (damage, hit-stop, slow-mo, move choice, AI tokens), not frame-exact positions.', '',
     '## Totals', '', '| metric | Unreal | browser |', '|---|---|---|']
for k, a, b in rows: L.append('| %s | %s | %s |' % (k, a, b))
L += ['| slow-mo real s (telemetry) | %.2f | %.2f |' % (su, sb), '| min time scale (telemetry) | %.3f | %.3f |' % (mu, mb), '']
L += ['## Beat by beat (first move started within 0.7 s; first hit / action event within 0.9 s)', '',
      '| t (s) | beat | key | Unreal move (+s) | Unreal event | browser move (+s) | browser event |', '|---|---|---|---|---|---|---|']
bmap = {}
for b in Bb: bmap.setdefault((b['label'], b['key']), []).append(b)
beats_out = []
for b in Bu:
    bb = bmap.get((b['label'], b['key']), [None]).pop(0) if bmap.get((b['label'], b['key'])) else None
    mu_, du = moves_after(Tu, b['rt'])
    eu = first_event(Eu, b['rt'], ['action', 'hit', 'dodge', 'web hit', 'cine'])
    if bb:
        mb_, db = moves_after(Tb, bb['rt'])
        eb = first_event(Eb, bb['rt'], ['hit', 'dodge', 'web hit', 'cine', 'move'])
    else:
        mb_, db, eb = '-', None, '(not fired)'
    beats_out.append({'t': b['t'], 'label': b['label'], 'key': b['key'], 'ue_move': mu_, 'ue_dt': du, 'ue_event': eu, 'br_move': mb_, 'br_dt': db, 'br_event': eb})
    L.append('| %.2f | %s | %s | %s (%s) | %s | %s (%s) | %s |' % (b['t'], b['label'], b['key'], mu_, du, eu.replace('|', '/')[:90], mb_, db, eb.replace('|', '/')[:90]))
agree = sum(1 for x in beats_out if x['ue_move'] == x['br_move'])
L += ['', 'Beats whose first move matches: **%d / %d**.' % (agree, len(beats_out)), '']
open(out_md, 'w').write('\n'.join(L) + '\n')
if out_json:
    json.dump({'totals': {k: {'ue': a, 'browser': b} for k, a, b in rows}, 'slowmo_real_s': {'ue': su, 'browser': sb}, 'beats': beats_out,
               'beats_move_agree': agree}, open(out_json, 'w'), indent=1)
print('wrote', out_md, 'move agreement %d/%d' % (agree, len(beats_out)))
