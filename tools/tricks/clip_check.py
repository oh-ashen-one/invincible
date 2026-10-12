# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Tricks C round 1: offline geometry of the keyed flip clips (make_flip_shapes.py report 'frames': every bone head in the BODY frame
# [forward, up, x] relative to the hips, frames 0..30 of each 1 s clip). Prints per clip and frame range: hip and knee angles
# (180 - angle(hips->spine2, knee->hip joint); hip joint-knee-ankle), foot-vs-shin angle (pointed toes), head-vs-chest angle (from neck->head vs spine2->neck).
#   python3 tools/tricks/clip_check.py <HeroFlips_report.json>
import json, math, sys


def sub(a, b): return [x - y for x, y in zip(a, b)]


def ang(a, b):
    na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(x * x for x in b))
    c = sum(x * y for x, y in zip(a, b)) / max(1e-9, na * nb)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


R = json.load(open(sys.argv[1]))
for clip, seq in sorted(R['frames'].items()):
    hip, knee, toe, head = [], [], [], []
    for fr in seq:
        H, S2, N, Hd = fr['hips'], fr['spine2'], fr['neck'], fr['head']
        h = k = t = 0
        hl, kl, tl = [], [], []
        for sd in 'LR':
            Th, Kn, A, To = fr['thigh.' + sd], fr['shin.' + sd], fr['foot.' + sd], fr['toe.' + sd]
            hl.append(180 - ang(sub(S2, H), sub(Th, Kn))); kl.append(ang(sub(Th, Kn), sub(A, Kn))); tl.append(ang(sub(A, Kn), sub(To, A)))
        hip.append(min(hl)); knee.append(min(kl)); toe.append(max(tl)); head.append(ang(sub(N, S2), sub(Hd, N)))
    fmt = lambda v: ' '.join('%3.0f' % x for x in v[::3])
    print('%-13s hip  %s\n%-13s knee %s\n%-13s toe  %s\n%-13s head %s' % (clip, fmt(hip), '', fmt(knee), '', fmt(toe), '', fmt(head)))
