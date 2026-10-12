# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Tricks C round 1: offline port of WebFlips::Sample's momentum timeline (Source/WebHomage/Traversal/WebTravFlips.cpp).
# Parses the Add(TEXT("name"), pitch, { {S::Shape, dur, twist, easeIn, easeOut}, ... }) lines of the C++ file, so the numbers
# here always follow the committed programs. Prints, per program at duration scale 1.0 / 0.85 / 1.15:
#   dur, peak pitch rate, mean rate, longest open hold <= 150 deg/s, peak/slowest ratio inside the rotation (F5), peak twist rate.
#   python3 tools/tricks/flip_sim.py [WebTravFlips.cpp] [--csv out.csv]
import math, re, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', '..', 'unreal', 'WebHomage', 'Source', 'WebHomage', 'Traversal', 'WebTravFlips.cpp')
INERTIA = dict(Tuck=1.0, Pike=1.35, Layout=3.2, Swan=7.5, Pencil=9.0, Straddle=7.5, Throne=9.0, Twist=3.5, Reach=7.0, Kickout=10.5)
BPRE, BPOST, ENV_IN, ENV_OUT, HZ, EASEW = 0.06, 0.11, 0.12, 0.22, 240, 0.45


def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def parse(path):
    txt = open(path).read()
    progs = []
    for m in re.finditer(r'Add\(TEXT\("(\w+)"\),\s*(-?[\d.]+)f,\s*\{((?:\s*\{[^{}]*\}\s*,?)+)\s*\}', txt, re.S):
        name, pitch, body = m.group(1), float(m.group(2)), m.group(3)
        segs = []
        for s in re.finditer(r'\{S::(\w+),\s*([\d.]+)f(?:,\s*(-?[\d.]+)f)?(?:,\s*([\d.]+)f)?(?:,\s*([\d.]+)f)?\}', body):
            segs.append(dict(shape=s.group(1), dur=float(s.group(2)), tw=float(s.group(3) or 0), ein=float(s.group(4) or 0), eout=float(s.group(5) or 0)))
        progs.append(dict(name=name, pitch=pitch, segs=segs))
    return progs


class Prog:
    def __init__(self, p, scale=1.0):
        self.name, self.pitch = p['name'], p['pitch']
        self.segs = [dict(s, dur=s['dur'] * scale) for s in p['segs']]
        self.dur = sum(s['dur'] for s in self.segs)
        self.starts = [sum(s['dur'] for s in self.segs[:k]) for k in range(len(self.segs))]
        n = int(math.ceil(self.dur * HZ)) + 1
        g, acc = [0.0], 0.0
        for i in range(1, n + 1):
            tm = (i - 0.5) / HZ
            acc += self.env(tm) / self.inertia(tm) / HZ
            g.append(acc)
        gend = g[min(n, int(math.ceil(self.dur * HZ)))]
        self.L = self.pitch / gend

    def seg_at(self, t):
        acc = 0
        for i, s in enumerate(self.segs):
            acc += s['dur']
            if t < acc: return i
        return len(self.segs) - 1

    def seg_inertia(self, k, t):
        s = self.segs[k]
        u = min(1, max(0, (t - self.starts[k]) / max(0.05, s['dur'])))
        return INERTIA[s['shape']] * (1 + s['ein'] * (1 - smooth(u / EASEW)) + s['eout'] * (1 - smooth((1 - u) / EASEW)))

    def inertia(self, t):
        t = min(max(t, 0), self.dur - 1e-4)
        k = self.seg_at(t); s0 = self.starts[k]; s1 = s0 + self.segs[k]['dur']
        if k > 0 and t < s0 + BPOST:
            return self.seg_inertia(k - 1, t) + (self.seg_inertia(k, t) - self.seg_inertia(k - 1, t)) * smooth((t - (s0 - BPRE)) / (BPRE + BPOST))
        if k + 1 < len(self.segs) and t > s1 - BPRE:
            return self.seg_inertia(k, t) + (self.seg_inertia(k + 1, t) - self.seg_inertia(k, t)) * smooth((t - (s1 - BPRE)) / (BPRE + BPOST))
        return self.seg_inertia(k, t)

    def env(self, t):
        return (0.35 + 0.65 * smooth(t / ENV_IN)) * (0.12 + 0.88 * smooth((self.dur - t) / ENV_OUT))

    def rate(self, t):
        return self.L * self.env(t) / self.inertia(t)

    def twist_rate(self, t):
        r, st = 0.0, 0.0
        for s in self.segs:
            if s['tw'] and st <= t < st + s['dur']:
                u = (t - st) / s['dur']; r += s['tw'] * 0.5 * math.pi * math.sin(math.pi * u) / s['dur']
            st += s['dur']
        return r

    def stats(self):
        dt = 1.0 / 240
        ts = [i * dt for i in range(int(self.dur / dt))]
        rs = [abs(self.rate(t)) for t in ts]
        peak = max(rs); mean = abs(self.pitch) / self.dur
        # longest run at <= 150 deg/s inside an OPEN shape segment
        best, run = 0.0, 0.0
        for t, r in zip(ts, rs):
            sh = self.segs[self.seg_at(t)]['shape']
            if r <= 150 and sh not in ('Tuck', 'Pike'): run += dt; best = max(best, run)
            else: run = 0.0
        # F5: peak / slowest inside the rotation (exclude the 0.12 s set-in / 0.22 s settle envelopes)
        inner = [r for t, r in zip(ts, rs) if ENV_IN <= t <= self.dur - ENV_OUT]
        f5 = (max(inner) / max(1.0, min(inner))) if inner else 0
        tw = max(abs(self.twist_rate(t)) for t in ts)
        return dict(dur=self.dur, peak=peak, mean=mean, hold=best, f5=f5, twist_peak=tw)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    path = args[0] if args else SRC
    progs = parse(path)
    print('%d programs parsed from %s' % (len(progs), os.path.relpath(path)))
    print('%-16s %6s  %5s %7s %7s %6s %6s %8s   (scale 0.85 peak / 1.15 peak)' % ('program', 'pitch', 'dur', 'peak', 'mean', 'hold', 'F5', 'twistpk'))
    for p in progs:
        s = Prog(p).stats(); a = Prog(p, 0.85).stats(); b = Prog(p, 1.15).stats()
        print('%-16s %6.0f  %5.2f %7.0f %7.0f %6.2f %6.1f %8.0f   (%4.0f / %4.0f)' % (p['name'], p['pitch'], s['dur'], s['peak'], s['mean'], s['hold'], s['f5'], s['twist_peak'], a['peak'], b['peak']))
