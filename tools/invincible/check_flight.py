#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound game; no affiliation. See DISCLAIMER.md.
"""Mechanical checks for the Invincible flight suite: reads <work>/<case>/<case>_telemetry.csv + <case>.log, applies the per-case checks in
flight_cases/cases.json plus suite-wide camera/body sanity, prints measured numbers, writes CHECK.json + CHECK.md into <docs>.
A PASS here is necessary, not sufficient: pixels are judged by the independent critic.
usage: check_flight.py <work_dir> <docs_dir> [--cases a,b]"""
import argparse, csv, json, math, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser(); ap.add_argument('work'); ap.add_argument('docs'); ap.add_argument('--cases')
a = ap.parse_args()
meta = json.loads((HERE / 'flight_cases/cases.json').read_text())
names = a.cases.split(',') if a.cases else list(meta)
work, docs = Path(a.work), Path(a.docs)


def f(r, k, d=0.0):
    try: return float(r.get(k, d))
    except (TypeError, ValueError): return d


def entries(rows, sub):
    n, prev = 0, None
    for r in rows:
        s = r.get('fl_sub', '')
        if s == sub and prev != sub: n += 1
        prev = s
    return n


out = {}
for n in names:
    d = work / n
    tel, log = d / (n + '_telemetry.csv'), d / (n + '.log')
    res = {'checks': [], 'pass': True}
    def chk(name, ok, val, want):
        res['checks'].append({'check': name, 'ok': bool(ok), 'value': val, 'want': want})
        if not ok: res['pass'] = False
    if not tel.exists():
        chk('telemetry', False, 'missing', 'csv'); out[n] = res; continue
    rows = list(csv.DictReader(tel.open()))
    if not rows:
        chk('telemetry', False, 0, '> 0 rows'); out[n] = res; continue
    L = log.read_text(errors='replace') if log.exists() else ''
    c = meta[n]['checks']
    subs = [r.get('fl_sub', '') for r in rows]
    sp = [f(r, 'speed_mps') for r in rows]
    z = [f(r, 'z_m') for r in rows]
    last = rows[-1]
    seen = sorted(set(subs))
    res['seen_subs'] = seen
    res['max_speed'] = round(max(sp), 1)
    res['z_start_end'] = [round(z[0], 1), round(z[-1], 1)]
    res['frames'] = len(rows)
    for s in c.get('subs', []): chk('sub %s seen' % s, s in seen, seen, s)
    if 'min_speed' in c: chk('max speed', max(sp) >= c['min_speed'], round(max(sp), 1), '>= %s' % c['min_speed'])
    if 'max_speed' in c:
        fly = [s for s, r in zip(sp, rows) if f(r, 't') > 2.0]
        chk('speed cap after 2 s', max(fly or [0]) <= c['max_speed'], round(max(fly or [0]), 1), '<= %s' % c['max_speed'])
    if 'booms' in c: chk('sonic booms', int(f(last, 'fl_booms')) == c['booms'], int(f(last, 'fl_booms')), c['booms'])
    if 'breaches' in c: chk('breaches', int(f(last, 'fl_breaches')) >= c['breaches'] if c['breaches'] else int(f(last, 'fl_breaches')) == 0, int(f(last, 'fl_breaches')), c['breaches'])
    if 'hero_lands' in c: chk('hero landings', int(f(last, 'fl_hero_lands')) == c['hero_lands'], int(f(last, 'fl_hero_lands')), c['hero_lands'])
    if 'max_hero_lands' in c: chk('no crater landing', int(f(last, 'fl_hero_lands')) <= c['max_hero_lands'], int(f(last, 'fl_hero_lands')), '<= %d' % c['max_hero_lands'])
    if 'brakes' in c: chk('brake entries', entries(rows, 'brake') >= c['brakes'], entries(rows, 'brake'), c['brakes'])
    if 'dashes' in c: chk('dash entries', entries(rows, 'dash') >= c['dashes'], entries(rows, 'dash'), c['dashes'])
    if 'max_end_speed' in c: chk('end speed', sp[-1] <= c['max_end_speed'], round(sp[-1], 2), '<= %s' % c['max_end_speed'])
    if c.get('grounded_end'): chk('grounded at end', last.get('mode') == 'ground', last.get('mode'), 'ground')
    if 'min_rise_m' in c: chk('altitude gained', max(z) - z[0] >= c['min_rise_m'], round(max(z) - z[0], 1), '>= %s' % c['min_rise_m'])
    if 'max_alt_drift_m' in c:
        flz = [zz for zz, r in zip(z, rows) if f(r, 't') > 1.0]
        drift = max(abs(zz - flz[0]) for zz in flz) if flz else 0
        chk('hands-off altitude drift', drift <= c['max_alt_drift_m'], round(drift, 1), '<= %s m' % c['max_alt_drift_m'])
    if 'min_abs_bank_deg' in c:
        b = max(abs(f(r, 'fl_bank_deg')) for r in rows)
        chk('peak bank', b >= c['min_abs_bank_deg'], round(b, 1), '>= %s deg' % c['min_abs_bank_deg'])
    if 'min_yaw_change_deg' in c:
        hy = [math.degrees(math.atan2(f(r, 'vy'), f(r, 'vx'))) for r in rows if math.hypot(f(r, 'vx'), f(r, 'vy')) > 5]
        tot, prev = 0.0, None
        for y in hy:
            if prev is not None: tot += ((y - prev + 180) % 360) - 180
            prev = y
        chk('travel heading change', abs(tot) >= c['min_yaw_change_deg'], round(tot, 1), '>= %s deg' % c['min_yaw_change_deg'])
    if c.get('walked'):
        g = [r for r in rows if r.get('mode') == 'ground' and f(r, 'hspeed_mps') > 1.0]
        chk('walked on the ground', len(g) > 30, len(g), '> 30 frames')
    if 'rescue_saved_min' in c:
        m = re.findall(r'WH_RESCUE saved id \d+ type (\w+) \+(\d+)', L)
        chk('rescue lives saved', sum(int(x[1]) for x in m) >= c['rescue_saved_min'], [x[0] for x in m], '>= %d saved' % c['rescue_saved_min'])
    # suite-wide sanity: camera never inside geometry for long, hero on screen, no NaN, no fall through the floor
    cig = sum(1 for r in rows if f(r, 'cam_in_geometry') > 0.5)
    chk('camera inside geometry frames', cig <= 6, cig, '<= 6')
    inf = [f(r, 'hero_in_frame', 1) for r in rows]
    off = sum(1 for v in inf if v < 0.5)
    chk('hero off-screen frames', off <= max(6, len(rows) // 50), off, '<= %d' % max(6, len(rows) // 50))
    under = sum(1 for r in rows if f(r, 'height_above_floor_m', 1) < -0.5)
    chk('below the floor frames', under == 0, under, 0)
    jumps = 0
    for p, q in zip(rows, rows[1:]):
        dd = math.dist((f(p, 'x_m'), f(p, 'y_m'), f(p, 'z_m')), (f(q, 'x_m'), f(q, 'y_m'), f(q, 'z_m')))
        if dd > max(4.0, 1.6 * f(q, 'speed_mps') / 60 + 0.5): jumps += 1
    chk('position teleports', jumps == 0, jumps, 0)
    errs = len(re.findall(r'(?m)^.*(LogWebHomage: Error|Ensure condition failed|Fatal error)', L))
    chk('log errors', errs == 0, errs, 0)
    res['log_flight'] = re.findall(r'WH_FLIGHT (sonic boom|breach in|heroLand|breach out)[^\n]*', L)[:12]
    out[n] = res
    print('%-26s %s  %s' % (n, 'PASS' if res['pass'] else 'FAIL', '; '.join('%s=%s(want %s)' % (x['check'], x['value'], x['want']) for x in res['checks'] if not x['ok'])), flush=True)

(docs / 'CHECK.json').write_text(json.dumps(out, indent=1) + '\n')
md = ['# Flight suite checks (mechanical)', '', 'Telemetry gates only; pixels are judged separately by the critic. Fixed-step capture is not real-time FPS proof.', '',
      '| case | result | failing checks (measured vs wanted) |', '|---|---|---|']
for n, r in out.items():
    bad = '; '.join('%s = %s (want %s)' % (x['check'], x['value'], x['want']) for x in r['checks'] if not x['ok'])
    md.append('| %s | %s | %s |' % (n, 'PASS' if r['pass'] else 'FAIL', bad or '-'))
(docs / 'CHECK.md').write_text('\n'.join(md) + '\n')
print('%d/%d cases pass' % (sum(1 for r in out.values() if r['pass']), len(out)))
