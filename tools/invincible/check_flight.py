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
docs.mkdir(parents=True, exist_ok=True)


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
    # owner 2026-10-16 ("always floating, even near the floor"): flight mode never enters the traversal ground mode
    if c.get('floating_end'): chk('floating near a surface at the end', last.get('mode') == 'air' and f(last, 'height_above_floor_m', 99) < 2.0, (last.get('mode'), round(f(last, 'height_above_floor_m', 99), 2)), 'air, < 2 m')
    if c.get('never_ground'):
        gnd = sum(1 for r in rows if r.get('mode') in ('ground', 'land'))
        chk('never in ground mode', gnd == 0, gnd, 0)
    if c.get('glided'):
        g = [r for r in rows if r.get('mode') == 'air' and f(r, 'height_above_floor_m', 99) < 2.0 and f(r, 'hspeed_mps') > 1.0]
        chk('glided near the floor', len(g) > 30, len(g), '> 30 frames')
    if c.get('camera_calm'):   # owner fl18 bug: camera 'having a seizure up and down' while landed on a roof
        flips, prev_d = 0, None
        for p, q in zip(rows, rows[1:]):
            dz = f(q, 'cam_z') - f(p, 'cam_z')
            if prev_d is not None and abs(dz) > 0.05 and abs(prev_d) > 0.05 and dz * prev_d < 0: flips += 1
            prev_d = dz
        chk('camera calm (vertical reversals > 5 cm/frame)', flips <= 4, flips, '<= 4')
    if c.get('walked'):
        g = [r for r in rows if r.get('mode') == 'ground' and f(r, 'hspeed_mps') > 1.0]
        chk('walked on the ground', len(g) > 30, len(g), '> 30 frames')
    if 'rescue_saved_min' in c:
        m = re.findall(r'WH_RESCUE saved id \d+ type (\w+) \+(\d+)', L)
        chk('rescue lives saved', sum(int(x[1]) for x in m) >= c['rescue_saved_min'], [x[0] for x in m], '>= %d saved' % c['rescue_saved_min'])
    # suite-wide sanity: camera never inside geometry for long, hero on screen, no NaN, no fall through the floor
    cig = sum(1 for r in rows if f(r, 'cam_in_geometry') > 0.5)
    chk('camera inside geometry frames', cig <= 6, cig, '<= 6')
    # a breach puts the body inside a solid on purpose: those frames are judged by the blackout length, every other frame by the count
    # (the camera follows him out of the exit hole: the first 6 frames after a breach count as part of it)
    in_b, since = [], 99
    for r in rows:
        since = 0 if r.get('fl_sub') == 'breach' else since + 1
        in_b.append(since <= 6)
    # critic r1: hidden = projected off-screen OR occluded (hero_occl >= 0.9, the pixel mask) OR a dark frame (mean luma < 40/255, rendered
    # runs: <case>/luma.txt from the mp4, frame i = row i). Outside breach windows no hidden run may exceed 6 frames.
    luma = [float(v) for v in re.findall(r'lavfi\.signalstats\.YAVG=([\d.]+)', (d / 'luma.txt').read_text())] if (d / 'luma.txt').exists() else []
    res['luma_frames'] = len(luma)
    def hidden(i, r):
        return f(r, 'hero_in_frame', 1) < 0.5 or f(r, 'hero_occl', -1) >= 0.9 or (i < len(luma) and luma[i] < 40.0)
    hid = [hidden(i, r) for i, r in enumerate(rows)]
    run_, worst, total = 0, 0, 0
    for h_, b in zip(hid, in_b):
        if h_ and not b: run_ += 1; total += 1
        else: run_ = 0
        worst = max(worst, run_)
    chk('longest hidden run outside breaches (off-screen / occluded / dark)', worst <= 6, '%d frames (%d total)' % (worst, total), '<= 6')
    dark = sum(1 for i, b in enumerate(in_b) if i < len(luma) and luma[i] < 40.0 and not b)
    chk('dark frames outside breaches (luma < 40)', dark == 0, dark, 0)
    run_, worst = 0, 0
    for h_, b in zip(hid, in_b):
        run_ = run_ + 1 if (b and h_) else 0
        worst = max(worst, run_)
    chk('longest hidden stretch inside a breach', worst <= 36, '%d frames' % worst, '<= 36 (0.6 s)')
    # critic r1: frozen against geometry while the reported speed stays up (actual displacement vs speed_mps)
    frozen = 0
    for p, q, b in zip(rows, rows[1:], in_b[1:]):
        act = math.dist((f(p, 'x_m'), f(p, 'y_m'), f(p, 'z_m')), (f(q, 'x_m'), f(q, 'y_m'), f(q, 'z_m'))) / max(1e-4, f(q, 't') - f(p, 't'))
        if f(q, 'speed_mps') > 5.0 and act < 0.2 * f(q, 'speed_mps') and not b and q.get('mode') == 'air': frozen += 1
    chk('frozen frames (speed > 5 m/s reported, < 20 % actual)', frozen <= 15, frozen, '<= 15')
    under = sum(1 for r in rows if f(r, 'height_above_floor_m', 1) < -0.5)
    chk('below the floor frames', under == 0, under, 0)
    jumps = 0
    for p, q in zip(rows, rows[1:]):
        dd = math.dist((f(p, 'x_m'), f(p, 'y_m'), f(p, 'z_m')), (f(q, 'x_m'), f(q, 'y_m'), f(q, 'z_m')))
        if dd > max(4.0, 1.6 * max(f(p, 'speed_mps'), f(q, 'speed_mps')) / 60 + 0.5): jumps += 1   # (r4: speed resets to 0 on the impact frame of a 300 m/s dive)
    chk('position teleports', jumps == 0, jumps, 0)
    # known pre-existing engine ensure in every RENDERED run, frame 0, also in the pre-change smoke log (2026-10-15): reported, not gated
    KNOWN = 'Ensure condition failed: OriginX <= OriginMax'
    lines_ = re.findall(r'(?m)^.*(?:LogWebHomage: Error|Ensure condition failed|Fatal error).*$', L)
    res['known_preexisting_ensures'] = sum(1 for l in lines_ if KNOWN in l)
    errs = [l for l in lines_ if KNOWN not in l]
    chk('log errors', not errs, len(errs), 0)
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
