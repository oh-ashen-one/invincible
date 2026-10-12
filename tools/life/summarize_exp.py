#!/usr/bin/env python3
# Homage fan game tooling (not affiliated with Marvel/Sony/Insomniac). P6 round 03: table of the experiment runs (real -game stills, 1080p, scratch dirs) from their detector JSON
# (det.json full frame, det_crop84.json = the critic pack's 84 % centre crop) and engine probe lines (probe.txt).
#   python3 tools/life/summarize_exp.py <out.md> <exp dir> [<exp dir> ...]
import glob, json, os, re, statistics, sys
out, dirs = sys.argv[1], sys.argv[2:]
def med(v): return statistics.median(v) if v else float('nan')
rows = []
for d in dirs:
    n = os.path.basename(d.rstrip('/'))
    def load(f):
        p = os.path.join(d, f)
        return json.load(open(p)) if os.path.exists(p) else {}
    full, crop = load('det.json'), load('det_crop84.json')
    def side(dd):
        ks = sorted(k for k in dd if k.endswith('.jpg') and 'people_right' in dd[k])
        return ks, [dd[k]['people'] for k in ks], [dd[k]['people_right'] for k in ks]
    ks, P, R = side(full); kc, Pc, Rc = side(crop)
    share = [100.0 * r / max(1, p) for p, r in zip(P, R)]; sharec = [100.0 * r / max(1, p) for p, r in zip(Pc, Rc)]
    pr = os.path.join(d, 'probe.txt'); fr, sm = [], []
    if os.path.exists(pr):
        for l in open(pr):
            m = re.search(r'WH_LIFE_FRAME t=([\d.]+).*people >=20px unoccluded: (\d+) \(left of view axis (\d+), right (\d+); within 80 m (\d+)', l)
            if m: fr.append(tuple(int(float(x)) for x in m.groups()[1:]))
            m = re.search(r'WH_LIFE_SAMPLE t=([\d.]+) .*people >=20px: (\d+) \(left (\d+) right (\d+); within 80 m (\d+): left (\d+) right (\d+)\)', l)
            if m: sm.append((float(m.group(1)), int(m.group(2)), int(m.group(5)), int(m.group(6)), int(m.group(7))))
    rows.append((n, ks, P, R, share, Pc, Rc, sharec, sm))
L = ['# P6 round 03: experiment runs (evidence, not the final captures)', '',
     '> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.', '',
     'Real game (`-game`, offscreen, `Scripts/run_game.sh`, inside `gpu_slot.sh capture`), 1920x1080 (S2 g7: 3840x2160), `r.ScreenPercentage 100`, stills at game t = 12 / 16 / 20 / 24 / 28 s (swing runs: 4.5 / 6.5 / 8.5 / 10.5 / 12.5 s of a real-time flight). '
     'YOLO11x-seg conf 0.35 imgsz 1920 (CPU) = the spec instrument; "right" = box centre in the right half of the frame; "crop" = the same on the 84 % centre crop the critic pack applies. Engine probe: people >= 20 px tall, ray-unoccluded, within 80 m.', '',
     '| run | YOLO people per still (full frame) | right | right share % (median, per still) | crop84 right share % (median, per still) | probe within 80 m >= 20 px: median / min of samples |', '|---|---|---|---|---|---|']
for n, ks, P, R, share, Pc, Rc, sharec, sm in rows:
    near = [x[2] for x in sm]
    L.append('| `%s` | %s | %s | **%.0f** (%s) | **%.0f** (%s) | %s |' % (n, ', '.join(map(str, P)), ', '.join(map(str, R)), med(share), ', '.join('%.0f' % x for x in share), med(sharec), ', '.join('%.0f' % x for x in sharec),
                                                                      ('%g / %d (n=%d)' % (med(near), min(near), len(near))) if near else 'n/a'))
open(out, 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
