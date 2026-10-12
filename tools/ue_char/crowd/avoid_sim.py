# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 07: offline model of the crowd (Line-mode walkers) for layout design and for checking the C++ avoidance (AWHCharLoopWalker::StepAvoidGroup).

The avoidance step below is the same algorithm as the C++ one (same constants, same order of operations); the engine's telemetry
(`-WHWalkerLog`) is the proof, this file is the design tool.  All lengths in cm, y = lateral world axis of the street (lanes run along X).

  python3 tools/ue_char/crowd/avoid_sim.py [--layout r6|r7] [--avoid 0|1] [--show]
"""
import math, sys, json
import numpy as np

CY5 = -1900.0
L5 = 9000.0
SPEED = {'walk': 117.3, 'walkF': 113.7, 'walkBrisk': 147.9, 'walkStroll': 76.0, 'walkOld': 58.4}
STYLE = {'03_white_tee': 'walk', '12_sundress_mom': 'walkF', '13_construction_worker': 'walkStroll', '15_executive': 'walkBrisk',
         '04_blue_sweatshirt': 'walkF', '08_black_suit': 'walkBrisk', '10_silver_tie': 'walk', '14_teen_skater': 'walk',
         '18_dapper_elder': 'walkOld', '19_marathon_runner': 'walkBrisk', '01_retired_gent': 'walkOld', '20_punk_artist': 'walkF',
         '02_leather_jacket': 'walk', '05_black_tee': 'walkBrisk', '06_chrome_shades': 'walkStroll', '09_kurta_waistcoat': 'walk',
         '16_lumberjack_hipster': 'walkStroll', '17_hijabi_student': 'walkF'}

# round-06 layout: (citizen, lane dy, x0 at the start of the shot, direction)
MID_R6 = [('03_white_tee', 150, -560, 1), ('12_sundress_mom', -140, -160, 1), ('13_construction_worker', 190, 150, 1), ('15_executive', -220, 420, 1),
          ('04_blue_sweatshirt', 60, -820, 1), ('19_marathon_runner', -60, 620, 1),
          ('10_silver_tie', -160, -420, -1), ('14_teen_skater', 200, 20, -1), ('01_retired_gent', -40, 520, -1), ('20_punk_artist', 120, 1050, -1),
          ('18_dapper_elder', -200, 1600, -1), ('08_black_suit', 40, 2200, -1)]
NEAR_R6 = [('02_leather_jacket', 690, -230, -1), ('06_chrome_shades', 730, 420, -1), ('16_lumberjack_hipster', 700, 1250, -1),
           ('05_black_tee', 720, -330, 1), ('17_hijabi_student', 680, 160, 1), ('09_kurta_waistcoat', 710, -640, 1)]

# avoidance constants (identical in WHCharLoopWalker.cpp)
R = 40.0              # capsule radius (cm): the brief asks >= 35
MARGIN = 15.0         # soft margin added to 2R when planning
HORIZONS = (0.0, 0.5, 1.0, 1.5, 2.0)
VLAT = 55.0           # max sideways speed (cm/s), never more than LAT_FRAC x the walker's own speed (max ~25 deg of yaw deviation)
LAT_FRAC = 0.47
OMAX = 260.0
OSTEP = 5.0
RIGHT_BIAS = 20.0     # cost of stepping to the left (right-hand traffic breaks head-on ties)
YAW_FILTER = 5.0
HARD_SLACK = 0.5      # the hard limit keeps centres 2R + 0.5 cm apart


class W:
    def __init__(s, name, dy, x0, d, avoid=True):
        s.name, s.dy, s.d, s.avoid = name, dy, d, avoid
        s.speed = SPEED[STYLE[name]]
        s.dir = np.array([1.0, 0.0]) if d > 0 else np.array([-1.0, 0.0])
        s.lat = np.array([0.0, 1.0]) if d > 0 else np.array([0.0, -1.0])      # right-hand side of the walker (UE: yaw + 90)
        s.center = np.array([0.0, CY5 + dy])
        s.line_d = (x0 + L5 / 2) if d > 0 else (L5 / 2 - x0)
        s.off = 0.0; s.latv = 0.0; s.yaw_dev = 0.0

    def along(s): return math.fmod(s.line_d, L5) - L5 / 2

    def pos(s, tau=0.0, off=None):
        return s.center + s.dir * (s.along() + s.speed * tau) + s.lat * (s.off if off is None else off)


def step(ws, dt, avoid=True):
    for w in ws: w.line_d += w.speed * dt
    if not avoid or dt <= 0: return 0
    G = [w for w in ws if w.avoid]
    n = len(G)
    cand = np.arange(int(-OMAX / OSTEP), int(OMAX / OSTEP) + 1) * OSTEP              # (K,)
    need = 2 * R + MARGIN
    # every walker's predicted position at each horizon at its CURRENT offset: (H, n, 2)
    Pj = np.array([[w.pos(t) for w in G] for t in HORIZONS])
    target = {}
    for i, m in enumerate(G):
        cost = np.abs(cand) + np.where(cand < 0, RIGHT_BIAS, 0.0) + 0.5 * np.abs(cand - m.off)
        for h, tau in enumerate(HORIZONS):
            base = m.center + m.dir * (m.along() + m.speed * tau)                       # (2,)
            Pm = base[None, :] + m.lat[None, :] * cand[:, None]                         # (K,2)
            for j in range(n):
                if j == i: continue
                d = np.linalg.norm(Pm - Pj[h, j][None, :], axis=1)
                v = np.maximum(need - d, 0.0) / need
                cost = cost + (100000.0 if tau == 0.0 else 1000.0) * v
        target[m] = float(cand[int(np.argmin(cost))])
    for m in G:
        vl = min(VLAT, LAT_FRAC * m.speed)
        d = float(np.clip(target[m] - m.off, -vl * dt, vl * dt))
        m.off += d
        m.latv += (d / dt - m.latv) * min(1.0, YAW_FILTER * dt)
        m.yaw_dev = math.degrees(math.atan2(m.latv, m.speed))
    # hard constraint: pairs closer than 2R are pushed apart along their joint axis, lateral component only
    fixed = 0
    for _ in range(6):
        any_v = False
        for a in range(len(G)):
            for b in range(a + 1, len(G)):
                A, B = G[a], G[b]
                dvec = A.pos() - B.pos(); dist = np.linalg.norm(dvec)
                if dist < 2 * R + HARD_SLACK and dist > 1e-3:
                    any_v = True; fixed += 1
                    nn = dvec / dist; deficit = 2 * R + HARD_SLACK - dist
                    A.off += float(np.dot(A.lat, nn)) * deficit * 0.5 * 1.05
                    B.off -= float(np.dot(B.lat, nn)) * deficit * 0.5 * 1.05
        if not any_v: break
    return fixed


def make(layout):
    ws = []
    if layout == 'r6':
        for c, dy, x0, d in MID_R6 + NEAR_R6: ws.append(W(c, dy, x0, d))
    else:                                            # a layout_search.py JSON
        d_ = json.load(open(layout))
        for c, dy, x0, d in d_['mid'] + d_['near']: ws.append(W(c, dy, x0, d))
    return ws


def run(ws, T, avoid, fps=60):
    dt = 1.0 / fps; n = int(T * fps)
    mind = []; hard = 0; maxoff = 0; hist = []
    for i in range(n):
        hard += step(ws, dt, avoid)
        P = np.array([w.pos() for w in ws])
        D = np.linalg.norm(P[:, None] - P[None], axis=2) + np.eye(len(ws)) * 1e9
        mind.append(D.min()); maxoff = max(maxoff, max(abs(w.off) for w in ws))
        hist.append(P.copy())
    return np.array(mind), hard, maxoff, np.array(hist)


if __name__ == '__main__':
    layout = 'r6'; avoid = True
    a = sys.argv[1:]
    if '--layout' in a: layout = a[a.index('--layout') + 1]
    if '--avoid' in a: avoid = a[a.index('--avoid') + 1] == '1'
    for T in (8.0, 6.0):
        ws = make(layout)
        mind, hard, mo, _ = run(ws, T, avoid)
        print('layout %s avoid %s window %.0f s: min pair distance %.1f cm, frames < 70 cm: %d, frames < 80 cm: %d, hard-projection pair fixes %d, max lateral offset %.0f cm, max yaw dev %.1f deg'
              % (layout, avoid, T, mind.min(), int((mind < 70).sum()), int((mind < 80).sum()), hard, mo, max(abs(w.yaw_dev) for w in ws)))
