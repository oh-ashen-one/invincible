#!/usr/bin/env python3
"""Round 09: choreography of the staged street fight (Char_Fight) with real combat reactions.

Fan homage project; not an official Marvel, Sony or Insomniac game; no affiliation.

Why: critic r08 found every thug in a guard idle for 4 s of street_fight_34, 0 knockdowns, 0 hit reactions.  The fight is now a SCRIPT, a pure
function of the stage clock (WHCharStage.h; the capture director's shot clock), so a capture that starts at shot 1 sees the same state as one that
plays through shot 0.  This tool writes the script (hero + 6 enemies) that build_characters.py puts into the actors:
  * per actor a path (world x / y / yaw keys, linearly interpolated): walk-in from the ring, lunge before a strike, travel of the reaction clips
    (the in-place clips of make_fight_clips.py carry no pelvis travel, clip_motion.json does), step back in;
  * per actor timed clips (FWHScriptBeat): hero strikes / flinches, enemy strikes, hit reactions (stumble back / left / right, flinch), knockdown
    held on the ground, get-up.  Contact instants are measured on the clips (hand / foot at maximum reach), a reaction starts 20 ms after the contact.
Also: a timeline check (per-second activity, hit list, knockdown durations) and a CPU stick-figure preview (PIL, no engine) of chosen instants.

  python3 tools/ue_char/fight/choreo.py [--check] [--preview T1,T2,..] [--out DIR]     writes tools/ue_char/fight/fight_script.json
Coordinates: UE world cm, hero at the origin; yaw in degrees (UE: +X = 0, +Y = 90); an enemy at polar angle a faces yaw a + 180.
"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(HERE, '..', 'heroanim'))
from p2paths import WT, SCRATCH  # noqa: E402
from ganim import Doc  # noqa: E402

MOT = json.load(open(os.path.join(HERE, 'clip_motion.json')))
BRUTE = json.load(open(os.path.join(HERE, '..', 'people', 'people.json')))['brute']

# clip key -> (asset, contact time s)   asset prefixes are resolved in build_characters.py
REACH = {'hero:punch1': 74, 'hero:punch2': 86, 'hero:punch3': 72, 'hero:kick': 92, 'hero:uppercut': 62}   # hero pelvis -> victim pelvis at the contact (cm): fist / foot reach + the victim's face depth
CONTACT = {'hero:punch1': 0.33, 'hero:punch2': 0.27, 'hero:punch3': 0.33, 'hero:kick': 0.30, 'hero:uppercut': 0.25,
           'thug:thugPunch1': 0.33, 'thug:thugPunch2': 0.30, 'thug:thugKick': 0.33, 'thug:bruteSlam': 0.53}
_DOCS = {}


def doc(which):
    if which not in _DOCS:
        _DOCS[which] = {'hero': lambda: Doc(os.path.join(WT, 'public/assets/spiderman.glb')), 'thug': lambda: Doc(os.path.join(WT, 'public/assets/thug.glb')),
                        'fight': lambda: Doc(os.path.join(SCRATCH, 'ueimport', 'SK_Street_Fight.glb'))}[which]()
    return _DOCS[which]


def dur(key):
    w, c = key.split(':')
    if w == 'fight': return MOT[c]['duration']
    return doc(w).duration(c)


def P(r, a):   # polar (cm, deg) -> xy
    return np.array([r * math.cos(math.radians(a)), r * math.sin(math.radians(a))])


def bearing(frm, to):   # yaw (deg) of the direction frm -> to
    d = to - frm
    return math.degrees(math.atan2(d[1], d[0]))


def fwd(yaw): return np.array([math.cos(math.radians(yaw)), math.sin(math.radians(yaw))])
def left(yaw): return np.array([math.sin(math.radians(yaw)), -math.cos(math.radians(yaw))])   # UE: +Y is the right-hand side of +X, so left = (sin, -cos)


class Actor:
    def __init__(self, label, pos, yaw, xy=1.0, z=1.0, base='thug:thugIdle', speed=114.0):
        self.label, self.xy, self.z, self.base, self.speed = label, xy, z, base, speed
        self.keys = [(0.0, np.array(pos, float), float(yaw))]    # (t, xy, yaw)
        self.beats = []                                            # dicts (clip key, start, rate, blend_in, blend_out, hold, weight)
        self.busy = []                                             # (t0, t1, what)
        self.down = []                                             # (t_on_ground, t_up) intervals with the torso on the ground

    # -- path helpers
    @property
    def pos(self): return self.keys[-1][1]
    @property
    def yaw(self): return self.keys[-1][2]
    @property
    def t_end(self): return self.keys[-1][0]

    def pos_at(self, t):
        ks = self.keys
        if t <= ks[0][0]: return ks[0][1].copy(), ks[0][2]
        for (t0, p0, y0), (t1, p1, y1) in zip(ks, ks[1:]):
            if t0 <= t <= t1:
                u = (t - t0) / max(1e-6, t1 - t0)
                dy = (y1 - y0 + 180) % 360 - 180
                return p0 + (p1 - p0) * u, y0 + dy * u
        return ks[-1][1].copy(), ks[-1][2]

    def key(self, t, pos=None, yaw=None):
        assert t >= self.t_end - 1e-6, '%s: key at %.2f before last key %.2f' % (self.label, t, self.t_end)
        self.keys.append((t, self.pos.copy() if pos is None else np.array(pos, float), self.yaw if yaw is None else float(yaw)))

    def goto(self, t0, t1, pos, yaw=None, what='move'):
        """Straight move from the current position (held until t0) to pos, arriving at t1."""
        if t0 > self.t_end + 1e-6: self.key(t0)
        self.key(t1, pos, yaw)
        self.busy.append((t0, t1, what))

    def walk_to(self, t_arrive, pos, yaw=None, what='walk'):
        d = float(np.linalg.norm(np.array(pos) - self.pos))
        t0 = max(self.t_end, t_arrive - d / self.speed)
        self.goto(t0, t_arrive, pos, yaw, what)

    def play(self, t0, clip, rate=1.0, blend_in=0.06, blend_out=0.2, hold=0.0, weight=1.0, travel=True, what=None, travel_k=1.0, shove=0.0):
        """A clip beat at stage time t0; the clip's pelvis travel (clip_motion.json) moves the actor (scaled by the weight and travel_k).
        shove (m): round 10, an extra recoil along the line hero -> actor that builds up over the first 0.18 s of the clip (the blow's impulse: the head / torso moves >= 0.1 stature
        within 0.2 s of the contact, the critic's measure)."""
        T = dur(clip) / rate
        self.beats.append(dict(clip=clip, start=round(t0, 4), rate=rate, blend_in=blend_in, blend_out=blend_out, hold=hold, weight=weight))
        self.busy.append((t0, t0 + T + (0 if hold < 0 else hold), what or clip))
        w, c = clip.split(':')
        if travel and w == 'fight' and c in MOT:
            if t0 > self.t_end + 1e-6: self.key(t0)
            m = MOT[c]; p0, y0 = self.pos.copy(), self.yaw
            out_dir = p0 / max(1e-6, float(np.linalg.norm(p0)))
            for t, dx, dz in zip(m['times'][1:], m['dx_left'][1:], m['dz_fwd'][1:]):
                tau = t / rate
                extra = out_dir * shove * 100.0 * smooth01(min(1.0, tau / 0.18)) if shove else 0.0
                self.key(t0 + tau, p0 + (left(y0) * dx + fwd(y0) * dz) * 100.0 * self.xy * weight * travel_k + extra, y0)
        return t0 + T


def smooth01(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


HOME_ANG = {}   # label -> engage angle (deg): every step-in / lunge returns to it, so nobody drifts into a neighbour
HOME_R = {}     # label -> engage radius (cm)

# the three 8 s clips of the capture: the first run is trimmed by 0.6 s of texture-streaming warm-up, so shot 0 lasts 8.6 s (build_characters.py `fight_shots`) and every clip is a full 8.0 s
DOWN_HIPS_R = 150.0     # knocked-down pelvis distance from the hero (cm): legs end ~70 cm from his feet, the head stays inside the wide / orbit frames
WINDOWS = [(0.65, 8.65), (8.65, 16.65), (16.65, 24.65)]
SHOT_STARTS = (0.0, 8.6, 16.6)
TOTAL = 25.2

# round 10: who swings what in the gaps between the hits (every enemy leaves its guard at least every ~1.8 s: critic r09 "the red-hoodie thug guards 0 - 7.75 s")
FEINTS = {'Fight_Thug': ['thug:thugPunch2', 'thug:thugPunch1', 'thug:thugKick'], 'Fight_Brute': ['thug:bruteSlam', 'thug:thugPunch1', 'thug:thugPunch2'],
          'Fight_Hood': ['thug:thugPunch1', 'thug:thugKick', 'thug:thugPunch2'], 'Fight_Tee': ['thug:thugPunch1', 'thug:thugKick', 'thug:thugPunch2'],
          'Fight_Beard': ['thug:thugPunch2', 'thug:thugPunch1', 'thug:thugKick'], 'Fight_Oxblood': ['thug:thugKick', 'thug:thugPunch2', 'thug:thugPunch1']}


def build():
    hero = Actor('Fight_Hero', (0, 0), 240, base='hero:fightIdle')
    bxy = BRUTE['scale'] * BRUTE['girth']
    # label: (start polar angle, engage polar (angle, radius), xy scale, z scale, base idle, walk speed, arrival time at the ring)
    # round 10: every enemy starts walking at t = 0 from a radius that makes it arrive at the ring at t_arr, so nobody stands in a guard while the clip starts
    E = {'Fight_Thug':     (235, (240, 110), 1.0, 1.0, 'hero:idle', 114.0, 1.35),
         'Fight_Hood':     (188, (178, 110), 1.0, 1.0, 'hero:idle', 114.0, 1.55),
         'Fight_Tee':      (358, (0, 110), 1.0, 1.0, 'thug:thugIdle', 114.0, 1.95),
         'Fight_Beard':    (128, (118, 110), 1.0, 1.0, 'thug:thugIdle', 114.0, 1.85),
         'Fight_Oxblood':  (312, (300, 110), 1.0, 1.0, 'thug:thugIdle', 114.0, 1.75),
         'Fight_Brute':    (58, (55, 125), bxy, BRUTE['scale'], 'hero:idle', 110.0, 2.35)}
    act = {'Fight_Hero': hero}
    eng = {}
    HOME_ANG.clear(); HOME_R.clear()
    for lbl, (s_ang, e, xy, z, base, spd, t_arr) in E.items():
        HOME_ANG[lbl] = float(e[0]); HOME_R[lbl] = float(e[1])
        r0 = e[1] + spd * t_arr
        a = Actor(lbl, P(r0, s_ang), s_ang + 180, xy, z, base, spd)
        eng[lbl] = P(e[1], e[0])
        a.goto(0.0, t_arr, eng[lbl], e[0] + 180, 'walk-in')
        act[lbl] = a
    return hero, act, eng


def script(fill=True):
    """Hero + 6 enemies, 25 s.  Pass 1 builds the hand-written hits; pass 2 (fill=True) inserts feints / circling into every gap longer than ~1.7 s."""
    fillers = _fillers() if fill else []
    return _script(fillers)


def _fillers():
    hero, act, slots, _ = _script([])
    out = []; k = 0
    for lbl, a in act.items():
        if lbl == 'Fight_Hero': continue
        merged = []
        for b0, b1 in sorted((b0, b1) for b0, b1, what in a.busy):
            if merged and b0 <= merged[-1][1] + 1e-6: merged[-1][1] = max(merged[-1][1], b1)
            else: merged.append([b0, b1])
        edges = [(0.0, 0.0)] + [tuple(m) for m in merged] + [(TOTAL - 0.2, TOTAL)]
        for (p0, p1), (n0, n1) in zip(edges, edges[1:]):
            g0, g1 = p1, n0                                  # an idle gap of this enemy
            t = g0 + 0.3
            while g1 - t >= 0.7:
                room = g1 - t
                if room >= 1.9 and k % 3 == 2:               # a shuffle round the ring: 1.6 s
                    out.append(dict(t=t, who=lbl, kind='circle', sign=(1 if (k // 3) % 2 == 0 else -1))); e = t + 1.6
                else:
                    kinds = FEINTS[lbl]; clip = kinds[k % len(kinds)]; d = dur(clip)
                    if d > room - 0.15: clip = 'thug:thugPunch2'; d = dur(clip)
                    if d > room - 0.15: break
                    out.append(dict(t=t, who=lbl, kind='feint', clip=clip, dur=d)); e = t + d
                k += 1
                if g1 - e <= 1.6: break
                t = e + 1.0
    return out


def _script(fillers):
    hero, act, eng = build()
    H = hero
    hero_slots = []
    events = []        # (sort key, order, function): per actor the sort key never exceeds the actor's first new path key

    def face(target, t_turn0, t_turn1):
        """Hero turns to face `target` (its position at t_turn1); keyed so the turn takes t_turn1 - t_turn0."""
        tp, _ = target.pos_at(t_turn1)
        yaw = bearing(np.zeros(2), tp)
        H.key(max(t_turn0, H.t_end), None, H.yaw)
        d = (yaw - H.yaw + 180) % 360 - 180
        H.key(t_turn1, None, H.yaw + d)

    def hero_do(t0, clip, what, **kw):
        t1 = H.play(t0, clip, what=what, **kw)
        hero_slots.append((t0, t1, what))
        return t1

    def ev(key, f): events.append((key, len(events), f))

    def strike(t0, hero_clip, tgt, react, *, rate=1.0, react_kw=None, turn=0.30, ret=True, getup=None, getup_clip='fight:getUp', down_k=None, shove=0.10):
        """Hero strikes tgt at t0 (clip start); the target steps in to the strike's reach just before, reacts at the contact; react = clip key or 'down' (getup = start of the get-up)."""
        def f():
            T = act[tgt]
            contact = t0 + CONTACT[hero_clip] / rate
            reach = REACH[hero_clip] + (10.0 if tgt == 'Fight_Brute' else 0.0)
            ang = HOME_ANG[tgt]
            if float(np.linalg.norm(T.pos_at(t0)[0] - P(reach, ang))) > 3.0:
                T.goto(max(T.t_end, contact - 0.6), contact - 0.05, P(reach, ang), None, 'step-in')
            face(T, t0 - turn - 0.04, t0 - 0.04)
            hero_do(t0, hero_clip, '%s>%s' % (hero_clip.split(':')[1], tgt.split('_')[1]), rate=rate)
            kw = dict(react_kw or {})
            t_r = contact + 0.02
            if react == 'down':
                dk = down_k if down_k is not None else max(1.0, (DOWN_HIPS_R - reach) / 53.0)       # the body ends DOWN_HIPS_R cm from the hero: its legs clear his feet
                T.play(t_r, 'fight:down', hold=getup - (t_r + dur('fight:down')), blend_out=0.12, blend_in=0.05, what='knockdown', travel_k=dk, shove=shove)
                T.down.append((t_r + 0.62, getup + 0.3))
                t_end = T.play(getup, getup_clip, blend_in=0.12, blend_out=0.25, what='get-up')
            else:
                t_end = T.play(t_r, react, what='hit:' + react.split(':')[1], shove=shove, **kw)
            if ret and float(np.linalg.norm(T.pos - P(HOME_R[tgt], HOME_ANG[tgt]))) > 3.0:          # back to its place in the ring (a walk: the walk clip plays under it)
                home = P(HOME_R[tgt], HOME_ANG[tgt])
                T.goto(t_end + 0.1, t_end + 0.1 + float(np.linalg.norm(T.pos - home)) / 100.0, home, None, 'step-in')
        ev(t0 - 0.7, f)

    def enemy_hit(t0, who, clip, rate=1.0, lunge_to=82.0, react_clip='hero:hitReact'):
        """Enemy strikes the hero at t0; it lunges in to lunge_to cm before and the hero flinches at the contact."""
        def f():
            T = act[who]; C = CONTACT[clip] / rate
            ang = HOME_ANG[who]
            if float(np.linalg.norm(T.pos - P(lunge_to, ang))) > 2.0:
                T.goto(max(T.t_end, t0 - 0.45), t0 + 0.05, P(lunge_to, ang), None, 'lunge')
            face(T, t0 - 0.35, t0 - 0.02)
            T.play(t0, clip, rate=rate, what='strike:' + clip.split(':')[1])
            hero_do(t0 + C + 0.02, react_clip, 'flinch<' + who.split('_')[1])
            home = P(HOME_R[who], HOME_ANG[who]); t_e = t0 + dur(clip) / rate
            if float(np.linalg.norm(T.pos - home)) > 3.0: T.goto(t_e + 0.05, t_e + 0.05 + float(np.linalg.norm(T.pos - home)) / 100.0, home, None, 'step-in')
        ev(t0 - 0.5, f)

    def feint(t0, who, clip, rate=1.0, d=None):
        """Swing from range (no contact): an enemy circling the hero.  thugGunAim is a static aim pose: held for d seconds."""
        def f():
            T = act[who]
            if clip == 'thug:thugGunAim':
                T.play(t0, clip, blend_in=0.15, blend_out=0.2, hold=max(0.0, (d or 0.9) - dur(clip)), what='aim', travel=False)
            else:
                T.play(t0, clip, rate=rate, what='swing:' + clip.split(':')[1])
        ev(t0 - 0.05, f)

    def circle(t0, who, sign, dur_=0.7, deg=14.0):
        """A shuffle round the ring: out by `deg` degrees (dur_ s), a short stop, back (dur_ s)."""
        def f():
            T = act[who]; ang = HOME_ANG[who]; r = HOME_R[who]
            if float(np.linalg.norm(T.pos - P(r, ang))) > 3.0 or t0 < T.t_end: return
            T.goto(t0, t0 + dur_, P(r, ang + sign * deg), ang + sign * deg + 180, 'circle')
            T.goto(t0 + dur_ + 0.2, t0 + 2 * dur_ + 0.2, P(r, ang), ang + 180, 'circle')
        ev(t0 - 0.05, f)

    Th, Hd, Te, Be, Ox, Br = ['Fight_' + k for k in ('Thug', 'Hood', 'Tee', 'Beard', 'Oxblood', 'Brute')]

    # The hero works round the ring (angles 240 Thug, 300 Oxblood, 0 Tee, 55 Brute, 118 Beard, 178 Hood): no turn is larger than ~62 degrees; one reversal per window.
    # Per 8 s window: 2 knockdowns (two enemies on the ground together >= 1 s, two DIFFERENT get-ups: the hero's backward roll `getUp` and the sit-up `getUp2`),
    # 5 more hit reactions, one enemy blow that lands on the hero (his flinch), no hold of one guard pose longer than ~1.8 s.
    # ------------------------------------------------------------------ shot 0, wide (0.65 - 8.65 s): Thug and Oxblood (front of the wide camera) go down
    strike(1.60, 'hero:uppercut', Th, 'down', getup=5.05, getup_clip='fight:getUp')        # knockdown 1: on the ground 2.5 - 5.0 s, rolls up
    strike(2.65, 'hero:kick', Ox, 'down', getup=6.15, getup_clip='fight:getUp2')           # knockdown 2: on the ground 3.6 - 6.2 s, sits up (1.4 s together with the Thug)
    strike(3.70, 'hero:punch2', Te, 'fight:hitLeft')
    enemy_hit(4.50, Hd, 'thug:thugPunch2')                                                    # the pistol-whip lands: hero flinch 4.82 - 5.4 (round 10: was 4.03, which spun the hero away from the Tee mid-punch: facing error 165 deg at the contact)
    strike(5.55, 'hero:punch1', Br, 'fight:hitBack')
    strike(6.55, 'hero:punch3', Be, 'fight:hitRight')
    strike(7.55, 'hero:kick', Hd, 'fight:hitBack')
    # ------------------------------------------------------------------ shot 1, 3/4 (8.65 - 16.65 s): Hood and Beard go down
    strike(9.25, 'hero:uppercut', Hd, 'down', getup=12.7, getup_clip='fight:getUp')
    strike(10.30, 'hero:kick', Be, 'down', getup=13.4, getup_clip='fight:getUp2')
    strike(11.35, 'hero:punch2', Br, 'fight:hitLeft')
    strike(12.40, 'hero:punch1', Te, 'fight:hitBack')
    enemy_hit(13.15, Th, 'thug:thugPunch1')                                                   # a bat swing lands (the Thug, near the 3/4 camera): hero flinch ~13.5 - 14.0 (round 10: was 13.05: the hero began to turn 0.03 s before the contact of the punch at 12.73)
    strike(14.10, 'hero:punch3', Ox, 'fight:hitRight')
    strike(15.15, 'hero:punch2', Th, 'fight:hitLeft')
    strike(16.10, 'hero:kick', Hd, 'fight:hitBack')
    # ------------------------------------------------------------------ shot 2, orbit (16.65 - 24.65 s): Brute and Tee go down
    strike(17.15, 'hero:punch3', Be, 'fight:hitRight')
    strike(18.20, 'hero:uppercut', Br, 'down', getup=21.6, getup_clip='fight:getUp2')
    strike(19.25, 'hero:kick', Te, 'down', getup=21.95, getup_clip='fight:getUp')
    strike(20.30, 'hero:punch1', Ox, 'fight:hitBack')
    strike(21.35, 'hero:punch2', Th, 'fight:hitLeft')
    enemy_hit(22.05, Be, 'thug:thugPunch2')
    strike(23.15, 'hero:punch1', Hd, 'fight:hitBack')
    strike(24.15, 'hero:punch3', Be, 'fight:hitRight')
    for fl in fillers:
        if fl['kind'] == 'feint': feint(fl['t'], fl['who'], fl['clip'], d=fl['dur'])
        else: circle(fl['t'], fl['who'], fl['sign'])
    for _, _, f in sorted(events, key=lambda e: (e[0], e[1])): f()
    return hero, act, hero_slots, eng


def to_json(act, total=26.0):
    out = {'duration': total, 'actors': {}}
    for lbl, a in act.items():
        keys = a.keys + [(total, a.pos, a.yaw)] if a.t_end < total else a.keys
        out['actors'][lbl] = {'xy_scale': a.xy, 'base': a.base,
                              'path': [{'t': round(t, 4), 'x': round(float(p[0]), 2), 'y': round(float(p[1]), 2), 'yaw': round(y, 2)} for t, p, y in keys],
                              'beats': sorted(a.beats, key=lambda b: b['start'])}
    return out


def check(act, hero_slots, total=24.5):
    lines = []
    # 1. hero slots must not overlap
    hs = sorted(hero_slots)
    for (a0, a1, n0), (b0, b1, n1) in zip(hs, hs[1:]):
        if b0 < a1 - 0.02: lines.append('HERO OVERLAP %s [%.2f,%.2f] and %s [%.2f,%.2f]' % (n0, a0, a1, n1, b0, b1))
    # 2. walking speeds
    for lbl, a in act.items():
        trav = [(b['start'], b['start'] + dur(b['clip']) / b['rate']) for b in a.beats if b['clip'].startswith('fight:')]
        for (t0, p0, _), (t1, p1, _) in zip(a.keys, a.keys[1:]):
            v = float(np.linalg.norm(p1 - p0)) / max(1e-6, t1 - t0)
            if any(b0 - 1e-3 <= t0 and t1 <= b1 + 1e-3 for b0, b1 in trav): continue
            if v > 135 and lbl != 'Fight_Hero': lines.append('%s: %.0f cm/s between %.2f and %.2f s (walk clip slides above ~130)' % (lbl, v, t0, t1))
    # 3. activity per 1 s window: actors with a non-idle beat / move overlapping the window
    def active(a, t0, t1):
        return any(b0 < t1 and b1 > t0 for b0, b1, _ in a.busy)
    worst = (99, 0)
    for k in range(int(total * 10) - 9):
        t0 = k / 10.0; t1 = t0 + 1.0
        n = sum(active(a, t0, t1) for a in act.values())
        if n < worst[0]: worst = (n, t0)
    lines.append('activity: fewest actors busy in any 1 s window = %d (window starting %.1f s)' % worst)
    # 3a. text timeline, one column per 0.5 s: w walk/step, s strike / swing, f flinch, h hit reaction, D knocked down, u get-up, . guard idle
    sym = lambda what: ('w' if what in ('walk-in', 'step-in', 'lunge', 'move') else 's' if what.startswith(('strike', 'swing')) or what.split('>')[0] in ('punch1', 'punch2', 'punch3', 'kick', 'uppercut')
                        else 'f' if what.startswith('flinch') or what == 'hit:hitReact' else 'h' if what.startswith('hit') else 'D' if what == 'knockdown' else 'u' if what == 'get-up' else '?')
    lines.append('timeline (0.5 s per char, 0 .. %.0f s; w walk s strike f flinch h hit D down u get-up):' % total)
    lines.append('           ' + ''.join(str(int(t) % 10) if t == int(t) else ' ' for t in np.arange(0, total, 0.5)))
    for lbl, a in act.items():
        row = []
        for t in np.arange(0, total, 0.5):
            c = '.'
            for b0, b1, what in a.busy:
                if b0 < t + 0.5 and b1 > t: c = sym(what)
            row.append(c)
        lines.append('%-10s %s' % (lbl.split('_')[1], ''.join(row)))
    # 3b. closest approach of any two enemies (centres, cm) and of an enemy to the hero
    dmin = (1e9, 0, '', ''); hmin = (1e9, 0, '')
    for k in range(int(total * 20)):
        t = k / 20.0
        pos = {l: a.pos_at(t)[0] for l, a in act.items()}
        ls = [l for l in pos if l != 'Fight_Hero']
        for i in range(len(ls)):
            hd = float(np.linalg.norm(pos[ls[i]]))
            if hd < hmin[0]: hmin = (hd, t, ls[i])
            for j in range(i + 1, len(ls)):
                d = float(np.linalg.norm(pos[ls[i]] - pos[ls[j]]))
                if d < dmin[0]: dmin = (d, t, ls[i], ls[j])
    lines.append('closest enemy pair %.0f cm (%s / %s at %.2f s); closest enemy to the hero %.0f cm (%s at %.2f s)' % (dmin[0], dmin[2], dmin[3], dmin[1], hmin[0], hmin[2], hmin[1]))
    # 4. reactions / knockdowns inside shot 1 (8-16 s)
    for (w0, w1, nm) in ((WINDOWS[0][0], WINDOWS[0][1], 'shot 0 wide'), (WINDOWS[1][0], WINDOWS[1][1], 'shot 1 (street_fight_34)'), (WINDOWS[2][0], WINDOWS[2][1], 'shot 2 orbit')):
        hits = []
        for lbl, a in act.items():
            for b in a.beats:
                if w0 <= b['start'] < w1 and (b['clip'].startswith('fight:hit') or b['clip'] == 'hero:hitReact' or b['clip'] == 'fight:down') and lbl != 'Fight_Hero':
                    hits.append((round(b['start'], 2), lbl.split('_')[1], b['clip'].split(':')[1]))
        kinds = sorted(set(h[2] for h in hits))
        lines.append('%s: %d enemy reactions, %d distinct kinds %s' % (nm, len(hits), len(kinds), kinds))
        lines.append('   ' + ', '.join('%s %s@%.2f' % (h[1], h[2], h[0]) for h in sorted(hits)))
        for lbl, a in act.items():
            for (g0, g1) in a.down:
                ov = min(g1, w1) - max(g0, w0)
                if ov > 0: lines.append('   knockdown %s on the ground %.2f-%.2f s (%.2f s inside this window)' % (lbl.split('_')[1], g0, g1, ov))
    return lines


# ---------------------------------------------------------------------------------------------------------------- preview (PIL stick figures)
def pose_world(a, t, hero_actor=False):
    """Stick figure of actor a at stage time t: list of world-space segments (cm), from the dominant beat (or its base idle)."""
    w_beats = []
    for b in a.beats:
        w, c = b['clip'].split(':'); L = dur(b['clip']); rate = b['rate']
        tl = (t - b['start']) * rate
        if tl < 0: continue
        pe = b['start'] + L / rate; he = 1e9 if b['hold'] < 0 else pe + b['hold']
        wi = min(1.0, (t - b['start']) / max(1e-3, b['blend_in'])); wo = 1.0 if t <= he else max(0.0, 1 - (t - he) / max(1e-3, b['blend_out']))
        wt = b['weight'] * wi * wo
        if wt > 0.05: w_beats.append((wt, w, c, min(tl, L)))
    if w_beats:
        wt, w, c, tl = max(w_beats)
    else:
        w, c = a.base.split(':'); tl = t % doc(w).duration(c)
    d = doc(w)
    W = d.world(d.sample(d.tracks(c), tl))
    p, yaw = a.pos_at(t)
    f, l = fwd(yaw), left(yaw)
    def wp(i):
        m = W[i][:3, 3]
        xy = p + (f * m[2] + l * m[0]) * 100.0 * a.xy
        return np.array([xy[0], xy[1], m[1] * 100.0 * a.z])
    segs = []
    for i in d.joints:
        par = d.parent.get(i)
        if par in d.joints: segs.append((wp(par), wp(i)))
    names = {n: wp(d.idx[n]) for n in ('head', 'hips', 'hand.L', 'hand.R', 'foot.L', 'foot.R')}
    return segs, names


def render_preview(act, times, out, cam=(-760.0, -800.0, 330.0), aim=(0.0, 0.0, 95.0), fov=48.0, size=(1280, 720)):
    from PIL import Image, ImageDraw
    cam = np.array(cam, float); aim = np.array(aim, float)
    zf = (aim - cam); zf /= np.linalg.norm(zf)
    xr = np.cross(zf, np.array([0, 0, 1.0])); xr /= np.linalg.norm(xr)
    yu = np.cross(xr, zf)
    foc = 0.5 * size[0] / math.tan(math.radians(fov) / 2)
    def proj(q):
        v = q - cam; z = v @ zf
        return (size[0] / 2 + foc * (v @ xr) / z, size[1] / 2 - foc * (v @ yu) / z)
    sheets = []
    for t in times:
        im = Image.new('RGB', size, (200, 205, 210)); dr = ImageDraw.Draw(im)
        for x in range(-400, 401, 100):
            dr.line([proj(np.array([x, -400.0, 0])), proj(np.array([x, 400.0, 0]))], fill=(180, 184, 190))
            dr.line([proj(np.array([-400.0, x, 0])), proj(np.array([400.0, x, 0]))], fill=(180, 184, 190))
        cols = {'Fight_Hero': (20, 120, 130), 'Fight_Brute': (120, 40, 40)}
        for lbl, a in sorted(act.items(), key=lambda kv: -np.linalg.norm(kv[1].pos_at(t)[0] - cam[:2])):
            segs, names = pose_world(a, t)
            col = cols.get(lbl, (40, 40, 60))
            for p0, p1 in segs: dr.line([proj(p0), proj(p1)], fill=col, width=4)
            hp = proj(names['head']); dr.ellipse([hp[0] - 9, hp[1] - 9, hp[0] + 9, hp[1] + 9], outline=col, width=3)
            dr.text((hp[0] - 20, hp[1] - 26), lbl.split('_')[1], fill=(0, 0, 0))
        dr.text((10, 10), 't = %.2f s' % t, fill=(0, 0, 0))
        sheets.append(im)
    cols_n = 2; rows_n = (len(sheets) + 1) // 2
    sheet = Image.new('RGB', (size[0] * cols_n // 2, size[1] * rows_n // 2))
    for i, im in enumerate(sheets):
        sheet.paste(im.resize((size[0] // 2, size[1] // 2)), ((i % cols_n) * size[0] // 2, (i // cols_n) * size[1] // 2))
    sheet.save(out)
    return out


if __name__ == '__main__':
    a = sys.argv[1:]
    hero, act, slots, _ = script()
    js = to_json(act)
    tmp = os.path.join(HERE, 'fight_script.json.tmp'); json.dump(js, open(tmp, 'w'), indent=1); os.replace(tmp, os.path.join(HERE, 'fight_script.json'))   # atomic: a build that reads it meanwhile never sees half a file
    n_beats = sum(len(v['beats']) for v in js['actors'].values()); n_keys = sum(len(v['path']) for v in js['actors'].values())
    print('fight_script.json: %d beats, %d path keys, %d actors, %.0f s' % (n_beats, n_keys, len(act), js['duration']))
    if '--check' in a or '--preview' in a:
        for l in check(act, slots): print(l)
    if '--preview' in a:
        ts = [float(x) for x in a[a.index('--preview') + 1].split(',')]
        out = a[a.index('--out') + 1] if '--out' in a else os.path.join(SCRATCH, 'fight_preview.png')
        print('preview', render_preview(act, ts, out))
