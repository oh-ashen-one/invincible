#!/usr/bin/env python3
"""Per-press diagnosis table of a clip / case from the telemetry (round-00 DIAGNOSIS evidence): for every swing press -- mode / anim at the press, response latency (first strand-on row), strand start vs the rendered
hand in cm and in 1080p px at the press frame and 3 frames later, tip progress in the first drawn frame, arm-to-anchor angle at the press / at tip arrival, chest-rate peak around the attach, hand chosen vs anchor side,
tension start vs tip landing, and what the strand does at the release.
usage: diagnose.py <telemetry.csv> [--case NAME]"""
import argparse, csv, math
a_ = argparse.ArgumentParser(); a_.add_argument('csv'); a_.add_argument('--case'); A = a_.parse_args()
R = [r for r in csv.DictReader(open(A.csv)) if not A.case or r.get('case', '') == A.case]
N = len(R); DT = 1 / 60.0
def f(r, k, d=0.0):
    try: return float(r[k])
    except Exception: return d
def v(r, p):
    k = p + 'x'
    return (f(r, p + 'x'), f(r, p + 'y'), f(r, p + 'z')) if k in r else (f(r, p + '_x'), f(r, p + '_y'), f(r, p + '_z'))
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def nrm(a): return math.sqrt(dot(a, a))
def ang(a, b):
    na, nb = nrm(a), nrm(b)
    return math.degrees(math.acos(max(-1, min(1, dot(a, b) / (na * nb))))) if na > 1e-6 and nb > 1e-6 else 0.0
def proj(r, p):
    y, pt = math.radians(f(r, 'cam_yaw_deg')), math.radians(f(r, 'cam_pitch_deg'))
    fw = (math.cos(pt) * math.cos(y), math.cos(pt) * math.sin(y), math.sin(pt)); rt = (-math.sin(y), math.cos(y), 0.0); up = (-math.sin(pt) * math.cos(y), -math.sin(pt) * math.sin(y), math.cos(pt))
    d = sub(p, (f(r, 'cam_x'), f(r, 'cam_y'), f(r, 'cam_z'))); z = dot(d, fw)
    if z < 0.05: return None
    tv = math.tan(math.radians(f(r, 'cam_vfov_deg')) / 2)
    return (0.5 + 0.5 * dot(d, rt) / (z * tv * 16 / 9)) * 1920, (0.5 - 0.5 * dot(d, up) / (z * tv)) * 1080
def nxt(i): return min(i + 1, N - 1)
# camera model check: our projection of the drawn start vs the logged rope_ax / rope_ay
dev = []
for i in range(N):
    if f(R[i], 'fw_s0_drawn') > 0.5 and f(R[i], 'rope_ax', -1) >= 0 and f(R[i], 'fw_s0_rel', -1) < 0:
        p = proj(R[i], v(R[i], 'fw_s0_s'))
        if p: dev.append(math.hypot(p[0] - f(R[i], 'rope_ax') * 1920, p[1] - f(R[i], 'rope_ay') * 1080))
dev.sort()
print('camera model check (|our projection - logged rope_ax/ay|, px): n %d median %.1f p90 %.1f' % (len(dev), dev[len(dev) // 2] if dev else -1, dev[int(0.9 * len(dev))] if dev else -1))
print('%-6s %-14s %-26s %-6s %-7s %-14s %-14s %-9s %-10s %-10s %-12s %-s' % ('t', 'mode/sub', 'anim_node/clip', 'lat_ms', 'hand/side', 'start-hand cm/px', '(+3 frames)', 'tip1', 'arm@press', 'arm@arrive', 'chest max', 'tension-land'))
for i in range(1, N):
    if not (f(R[i], 'in_swing') > 0.5 and f(R[i - 1], 'in_swing') < 0.5): continue
    on = next((j for j in range(i, min(N, i + 60)) if f(R[j], 'fw_s0_on') > 0.5 and f(R[j], 'fw_s0_rel', -1) < 0), None)
    lat = (on - i) * DT * 1000 if on is not None else None
    s = '%-6.2f %-14s %-26s' % (f(R[i], 't'), R[i]['mode'] + '/' + R[i]['sub'], (R[i]['anim_node'] + '/' + R[i]['anim_clip'])[:26])
    if on is None:
        print(s, 'NO STRAND within 0.67 s of the press (in_swing held %d frames)' % sum(1 for j in range(i, min(N, i + 60)) if f(R[j], 'in_swing') > 0.5)); continue
    right = f(R[on], 'fw_s0_hand') > 0.5
    def hand(k): return v(R[nxt(k)], 'fw_hr_' if right else 'fw_hl_')
    def sh(k): return v(R[nxt(k)], 'fw_shr_' if right else 'fw_shl_')
    def err(k):
        d = nrm(sub(v(R[k], 'fw_s0_s'), hand(k))) * 100
        p1, p2 = proj(R[k], v(R[k], 'fw_s0_s')), proj(R[nxt(k)], hand(k))
        return '%5.0f/%s' % (d, '%4.0f' % math.hypot(p1[0] - p2[0], p1[1] - p2[1]) if p1 and p2 else ' n/a')
    anc = v(R[on], 'fw_s0_a'); st = v(R[on], 'fw_s0_s'); L = nrm(sub(anc, st))
    tip1 = nrm(sub(v(R[on], 'fw_s0_t'), st)) / L if L > 1 else -1
    shoot = f(R[on], 'fw_s0_shoot')
    arr = next((j for j in range(on, min(N, on + 40)) if f(R[j], 'fw_s0_age') >= shoot), None)
    a_press = ang(sub(hand(max(i - 1, 0)), sh(max(i - 1, 0))), sub(anc, sh(max(i - 1, 0))))
    a_arr = ang(sub(hand(arr), sh(arr)), sub(anc, sh(arr))) if arr is not None else -1
    cm = max(f(R[j], 'fw_chest_rate_dps') for j in range(max(0, on - 3), min(N, on + 10)))
    ten = next((j for j in range(on, min(N, on + 40)) if f(R[j], 'tension') > 0.05), None)
    vx, vy = f(R[on], 'vx'), f(R[on], 'vy'); hs = math.hypot(vx, vy) or 1
    lat_side = (anc[0] - f(R[on], 'x_m')) * (-vy / hs) + (anc[1] - f(R[on], 'y_m')) * (vx / hs)
    print(s, '%-6.0f %-7s %-14s %-14s %-9.2f %-10.0f %-10.0f %-12.0f %s' % (lat, ('R' if right else 'L') + '/' + ('R' if lat_side > 0 else 'L'), err(on), err(min(N - 1, on + 3)), tip1, a_press, a_arr, cm,
          '%.2f s' % ((ten - arr) * DT) if ten is not None and arr is not None else 'n/a'), 'anchor %.0f m away, shoot %.2f s, hs %.0f m/s, vz %.0f' % (L, shoot, hs, f(R[on], 'vz')))
