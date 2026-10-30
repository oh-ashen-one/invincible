#!/usr/bin/env python3
# Homage fan game tooling. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation. Copied from the Hulk project (tools/brute/v2r/size_gate.py, 2026-10-30), creature-agnostic.
"""Size gate for a generated video2rig clip: does the creature stay the size of the model?

    ~/video2rig/.venv/bin/python tools/brute/v2r/size_gate.py <project_dir> <clip|path.mp4> [--max 1.3]
        [--metric area|box] [--edge-frames 12] [--start start.png] [--json out.json] [--debug-dir dir]

Run it under the video2rig fork's venv (~/video2rig/.venv: numpy, OpenCV, SciPy). It imports the fork's own clip
helpers (video2rig.clip: background, silhouette, Panel) from ~/video2rig (or $V2R_HOME), so silhouettes are made the
way video2rig makes them. Frames are decoded with OpenCV at 960 px wide (no ffmpeg temp files). It never writes into
the project.

Why: `python -m video2rig check` measures how well the two panels agree, not size. On 2026-10-28 two MiniMax roar
clips drew the dragon's wings at about 2x the model's span and off the panel edge and still passed the check
(boss-fight-blueprint/references/veyr-application.md, "size gate").

Panels: side-by-side views are split at the dark split line found in the clip's own frame 0 (generators re-frame the
start picture: Seedance omni-reference clips of the dragon moved the line from 44% to 50% of the width, so
cameras.json rectangles were wrong for them); names come from <start dir>/cameras.json. Stacked/turned views use
cameras.json through video2rig.clip.Panel. Nothing found: the midline.

Per panel and frame: silhouette = pixels that differ from the empty grey studio (video2rig.clip.silhouette: colour
difference from the backdrop, soft floor shadows and specks removed; backdrop = video2rig.clip.background over the
take, per panel, as creature.py does). Measured: box width and height, area, left/right reach from the frame-0 box
centre, contact with a panel edge (the split line itself is masked out). Ratios are against frame 0 of the clip (the
start frame as delivered); the start picture is measured too (backdrop = cubic fit to its border band) and frame 0's
drift from it is reported as a framing check. Each ratio series goes through a 3-frame running median so one bad
mask cannot fail a clip; raw maxima are printed beside it.

Verdict: FAIL when (metric area, default) scale = sqrt(area / frame-0 area) exceeds --max in any panel, or (metric
box) box width or height / frame 0 exceeds --max in any panel; and in both, when the silhouette touches a panel edge
frame 0 did not touch for --edge-frames frames or more (a part that leaves the panel saturates the box, so its size
cannot be measured; shorter contacts are a WARN). Why area by default: on the dragon's clips the box metric also
fails pose changes that keep the size (rise rears onto the hind legs: box height 1.38, scale 1.18; land2's hop
pitches the body up: box 1.57, scale 1.19), while both metrics fail the oversized MiniMax roars (scale 1.55 / 1.56).
For the Brute the box metric would fail most attacks (a punch toward the side camera or a clap with arms spread
doubles a box width without changing the body's size).

Output, first line (the gate line), then per-panel lines, FAIL reasons and WARNs:
  SIZE_GATE <clip> PASS|FAIL width x.xx height x.xx peak_frame N scale x.xx metric area|box
--debug-dir writes frame 0 and the peak frame with the silhouette tinted, the frame-0 box green, the frame box red.
Exit code 0 PASS, 1 FAIL, 2 could not measure.
"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

V2R_HOME = Path(os.environ.get('V2R_HOME', Path.home() / 'video2rig'))
sys.path.insert(0, str(V2R_HOME))
try:
    import cv2
    from video2rig.clip import Panel, background, silhouette
except ImportError as e:            # pragma: no cover
    sys.exit(f'needs the video2rig fork and its venv: run with {V2R_HOME}/.venv/bin/python ({e})')

EDGE_MARGIN = .006       # of the panel width, masked at the panel's left/right edges (the split line is drawn there)
PROC_W = 960             # frames are processed at this width (both start picture and clip)


def load_cameras(start_dir):
    p = start_dir / 'cameras.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None


class Rect:
    """A full-height column of the frame (side-by-side panels), with the cut/put of video2rig.clip.Panel."""

    def __init__(self, x0, x1, H):
        self.x0i, self.y0i, self.w, self.h, self.turn = int(x0), 0, int(x1 - x0), H, 0

    def cut(self, img):
        return img[:, self.x0i:self.x0i + self.w]

    def put(self, full, part):
        full[:, self.x0i:self.x0i + self.w] = part


def find_split(img, expect=None):
    """The dark split line between side-by-side panels: columns whose median brightness over the rows is under half
    the frame's, in a run at most 2% of the width, outside the outer 5%; the run nearest `expect` (px). Generators
    re-frame the start picture (a Seedance omni-reference clip moved the line from 44% to 50% of the width), so the
    line is looked for in the clip itself rather than trusted from cameras.json. (x_first, x_last) or None."""
    g = img.astype(np.float32).mean(2)
    col = np.median(g, 0)
    W = len(col)
    dark = col < .5 * np.median(col)
    dark[:int(.05 * W)] = dark[W - int(.05 * W):] = False
    runs, x = [], 0
    while x < W:
        if dark[x]:
            x1 = x
            while x1 + 1 < W and dark[x1 + 1]:
                x1 += 1
            if x1 - x + 1 <= max(2, .02 * W):
                runs.append((x, x1))
            x = x1 + 1
        else:
            x += 1
    if not runs:
        return None
    mid = expect if expect is not None else W / 2
    return min(runs, key=lambda r: abs(.5 * (r[0] + r[1]) - mid))


def panels_for(img, cams):
    """[(name, panel)] for one image, plus where the split came from. Side-by-side views: split at the dark line found
    in the image (names from cameras.json); stacked or turned views: cameras.json via video2rig.clip.Panel; nothing
    found and no cameras: the midline."""
    H, W = img.shape[:2]
    views = (cams or {}).get('views') or []
    stacked = any(v.get('turn') or v.get('y0_px') for v in views)
    if views and stacked:
        return [(v['name'], Panel(v, (W, H), cams['frame_px'])) for v in views], 'cameras.json (stacked)'
    names = [v['name'] for v in views] if len(views) == 2 else ['left', 'right']
    expect = views[1]['x0_px'] * W / cams['frame_px'][0] if len(views) == 2 else None
    sp = find_split(img, expect)
    if sp is not None:
        src = f'split line found at x {sp[0]}-{sp[1]} of {W}' + (f' (cameras.json: {expect:.0f})' if expect else '')
        return [(names[0], Rect(0, sp[0], H)), (names[1], Rect(sp[1] + 1, W, H))], src
    if views:
        return [(v['name'], Panel(v, (W, H), cams['frame_px'])) for v in views], 'cameras.json (no split line seen)'
    return [('left', Rect(0, W // 2, H)), ('right', Rect(W // 2, W, H))], 'midline (no split line, no cameras.json)'


def shrink(img):
    h, w = img.shape[:2]
    if w <= PROC_W:
        return img
    return cv2.resize(img, (PROC_W, int(round(h * PROC_W / w))), interpolation=cv2.INTER_AREA)


def read_clip(path):
    cap = cv2.VideoCapture(str(path))
    out = []
    while True:
        ok, img = cap.read()
        if not ok:
            break
        out.append(shrink(img))
    cap.release()
    if not out:
        raise SystemExit(f'cannot read {path}')
    return out


def border_background(img, panels):
    """The empty studio behind a single picture, per panel: a cubic surface fitted to the panel's border band, then
    refitted to every pixel within 10 levels of it (the creature never reaches the border in a start picture)."""
    bg = np.zeros(img.shape, np.float32)
    for _, p in panels:
        sub = img[p.y0i:p.y0i + p.h, p.x0i:p.x0i + p.w].astype(np.float32)
        h, w = sub.shape[:2]
        ys, xs = np.mgrid[0:h, 0:w]
        u, v = xs / w, ys / h
        basis = np.stack([u ** a * v ** b for a in range(4) for b in range(4 - a)], -1).reshape(-1, 10)
        m = max(3, int(EDGE_MARGIN * w) + 2)
        band = np.zeros((h, w), bool)
        bw, bh = max(m + 4, w // 12), max(4, h // 12)
        band[:bh, m:w - m] = band[-bh:, m:w - m] = True
        band[:, m:bw] = band[:, w - bw:w - m] = True
        inside = ((xs >= m) & (xs < w - m)).ravel()          # never the split line
        keep = band.ravel()
        px = sub.reshape(-1, 3)
        for it in range(4):
            coef = np.linalg.lstsq(basis[keep], px[keep], rcond=None)[0]
            fit = basis @ coef
            near = np.abs(px - fit).max(1) < 10
            keep = near & (band.ravel() if it == 0 else inside)
        bg[p.y0i:p.y0i + p.h, p.x0i:p.x0i + p.w] = fit.reshape(h, w, 3)
    return bg


def measure(mask):
    """Box, area and edge contact of one panel's silhouette (the panel's own pixels), or None when empty."""
    m = mask.copy()
    h, w = m.shape
    e = max(2, int(round(EDGE_MARGIN * w)))
    m[:, :e] = False
    m[:, w - e:] = False
    band = max(e + 2, int(.04 * w))             # a split line left in the edge band: nearly full-height columns
    full = m.mean(0) > .85
    full[band:w - band] = False
    m[:, full] = False
    cols, rows = np.flatnonzero(m.any(0)), np.flatnonzero(m.any(1))
    if len(cols) == 0:
        return None
    x0, x1, y0, y1 = int(cols[0]), int(cols[-1]), int(rows[0]), int(rows[-1])
    edges = {'left': x0 <= e, 'right': x1 >= w - e - 1, 'top': y0 <= 1, 'bottom': y1 >= h - 2}
    return dict(x0=x0, x1=x1, y0=y0, y1=y1, w=x1 - x0 + 1, h=y1 - y0 + 1, area=int(m.sum()), edges=edges, pw=w, ph=h)


def run_median(x):
    x = np.asarray(x, float)
    out = x.copy()
    for i in range(len(x)):
        out[i] = np.nanmedian(x[max(0, i - 1):i + 2])
    return out


def main():
    ap = argparse.ArgumentParser(prog='size_gate.py', description='silhouette size gate for a video2rig clip')
    ap.add_argument('project')
    ap.add_argument('clip', help='clip name (clips/<clip>.mp4) or a path to an mp4')
    ap.add_argument('--max', type=float, default=1.3, help='largest allowed width/height ratio vs frame 0')
    ap.add_argument('--start', help='start picture (default <project>/start/start.png)')
    ap.add_argument('--edge-frames', type=int, default=12, help='FAIL when the silhouette touches a panel edge (that '
                    'frame 0 did not touch) in at least this many frames (12 = 0.5 s at 24 fps); shorter contacts are a '
                    'WARN; 0 turns the rule off')
    ap.add_argument('--metric', choices=('area', 'box'), default='area', help='area (default): sqrt of the silhouette '
                    'area per panel vs frame 0, a size measure that ignores pose (rearing, a hop, arms overhead, a '
                    'punch toward a camera keep the area; a body or wings drawn bigger do not); box: the silhouette '
                    'box width and height per panel vs frame 0 (the literal spec; fails pose changes too)')
    ap.add_argument('--json', help='write the per-frame numbers here')
    ap.add_argument('--debug-dir', help='write frame 0 and the peak frame with silhouettes and boxes drawn (PNG)')
    a = ap.parse_args()

    project = Path(a.project).expanduser().resolve()
    clip_path = Path(a.clip).expanduser()
    if clip_path.suffix.lower() != '.mp4':
        clip_path = project / 'clips' / f'{a.clip}.mp4'
    name = clip_path.stem
    start = Path(a.start).expanduser() if a.start else project / 'start' / 'start.png'
    cams = load_cameras(start.parent)

    frames = read_clip(clip_path)
    H, W = frames[0].shape[:2]
    panels, split_src = panels_for(frames[0], cams)
    per = {n: [] for n, _ in panels}
    full = [np.zeros((H, W), bool) for _ in frames] if a.debug_dir else None
    for n, p in panels:                          # per panel, as video2rig's creature.py does
        cut = [np.ascontiguousarray(p.cut(f)) for f in frames]
        bg = background(cut)
        for t, f in enumerate(cut):
            sil = silhouette(f, bg)
            per[n].append(measure(sil))
            if full is not None:
                p.put(full[t], sil)
    ref = {n: per[n][0] for n, _ in panels}
    if any(r is None for r in ref.values()):
        print(f'SIZE_GATE {name} FAIL width nan height nan peak_frame 0')
        print(f'  cannot measure: no silhouette in frame 0 of panel(s) {[n for n, r in ref.items() if r is None]}')
        return 2

    # start picture: the framing check (frame 0 against our own render, panel-relative units)
    start_info = {}
    if start.exists():
        img = cv2.imread(str(start), cv2.IMREAD_COLOR)
        img = shrink(img)
        sp, start_split = panels_for(img, cams)
        sbg = border_background(img, sp)
        for (n, p), (_, pv) in zip(sp, panels):
            s = measure(silhouette(np.ascontiguousarray(p.cut(img)),
                                   np.ascontiguousarray(p.cut(sbg))))
            r = ref[n]
            if s:
                start_info[n] = dict(start_w=round(s['w'] / s['pw'], 4), start_h=round(s['h'] / s['ph'], 4),
                                     f0_over_start_scale=round(float(np.sqrt((r['area'] / (r['pw'] * r['ph'])) /
                                                                             (s['area'] / (s['pw'] * s['ph'])))), 3),
                                     f0_over_start_w=round((r['w'] / r['pw']) / (s['w'] / s['pw']), 3),
                                     f0_over_start_h=round((r['h'] / r['ph']) / (s['h'] / s['ph']), 3))

    T = len(frames)
    series, reasons, panel_lines, warns = {}, [], [], []
    worst = (0.0, None, None, 0)                # ratio, panel, measure, frame
    for n, _ in panels:
        r = ref[n]
        cx0 = .5 * (r['x0'] + r['x1'])
        L0, R0 = max(cx0 - r['x0'], 1), max(r['x1'] - cx0, 1)
        wr = np.array([m['w'] / r['w'] if m else np.nan for m in per[n]])
        hr = np.array([m['h'] / r['h'] if m else np.nan for m in per[n]])
        lr = np.array([(cx0 - m['x0']) / L0 if m else np.nan for m in per[n]])
        rr = np.array([(m['x1'] - cx0) / R0 if m else np.nan for m in per[n]])
        sr = np.array([np.sqrt(m['area'] / r['area']) if m else np.nan for m in per[n]])
        wm, hm, sm = run_median(wr), run_median(hr), run_median(sr)
        series[n] = dict(width=wr.round(4).tolist(), height=hr.round(4).tolist(), left=lr.round(4).tolist(),
                         right=rr.round(4).tolist(), scale=sr.round(4).tolist())
        for meas, s in ((('width', wm), ('height', hm)) if a.metric == 'box' else (('scale', sm),)):
            if np.isnan(s).all():
                continue
            k = int(np.nanargmax(s))
            if s[k] > worst[0]:
                worst = (float(s[k]), n, meas, k)
        # edges touched later than frame 0
        f0e = r['edges']
        for edge in ('left', 'right', 'top', 'bottom'):
            hit = [t for t in range(T) if per[n][t] and per[n][t]['edges'][edge] and not f0e[edge]]
            if not hit:
                continue
            msg = (f'{n}: silhouette touches the {edge} edge of the panel in {len(hit)} frames (first {hit[0]}, last '
                   f'{hit[-1]}); frame 0 did not')
            if a.edge_frames and len(hit) >= a.edge_frames:
                reasons.append(msg + ': the part leaves the panel, its size cannot be measured there')
            elif len(hit) >= 2:
                warns.append(msg + f' (under {a.edge_frames} frames: brief contact, look at the clip)')
        kw, kh = int(np.nanargmax(wm)), int(np.nanargmax(hm))
        panel_lines.append(
            f'  {n}: width {np.nanmax(wm):.2f} (raw {np.nanmax(wr):.2f}) at frame {kw} | height {np.nanmax(hm):.2f} '
            f'(raw {np.nanmax(hr):.2f}) at frame {kh} | scale {np.nanmax(sm):.2f} at frame {int(np.nanargmax(sm))} '
            f'| frame-0 box {r["w"]}x{r["h"]} px of {r["pw"]}x{r["ph"]}'
            + (f' | frame0/start w {start_info[n]["f0_over_start_w"]} h {start_info[n]["f0_over_start_h"]}'
               if n in start_info else ''))

    pk = worst[3]
    wmax = max(np.nanmax(run_median(series[n]['width'])) for n, _ in panels)
    hmax = max(np.nanmax(run_median(series[n]['height'])) for n, _ in panels)
    smax = max(np.nanmax(run_median(series[n]['scale'])) for n, _ in panels)
    for n, _ in panels:
        for meas in (('width', 'height') if a.metric == 'box' else ('scale',)):
            s = run_median(series[n][meas])
            if np.nanmax(s) > a.max:
                k = int(np.nanargmax(s))
                reasons.insert(0, f'{n} {meas} ratio {np.nanmax(s):.2f} > {a.max:.2f} at frame {k}')
    verdict = 'FAIL' if reasons else 'PASS'
    print(f'SIZE_GATE {name} {verdict} width {wmax:.2f} height {hmax:.2f} peak_frame {pk} scale {smax:.2f} '
          f'metric {a.metric}')
    print(f'  limit {a.max:.2f} on {"scale = sqrt(silhouette area / frame 0)" if a.metric == "area" else "box width and height / frame 0"}'
          f' per panel; edge rule {a.edge_frames} frames; panels: {split_src}')
    for ln in panel_lines:
        print(ln)
    lat = ', '.join(f'{n} L {series[n]["left"][pk]:.2f} R {series[n]["right"][pk]:.2f}' for n, _ in panels)
    print(f'  lateral reach at peak frame {pk} (vs frame 0, from the frame-0 box centre): {lat}')
    print(f'  worst: {worst[1]} {worst[2]} {worst[0]:.2f} at frame {pk} of {T}; limit {a.max:.2f}')
    for x in reasons:
        print(f'  FAIL: {x}')
    for x in warns:
        print(f'  WARN: {x}')
    for n, d in start_info.items():
        drift = max(abs(d['f0_over_start_w'] - 1), abs(d['f0_over_start_h'] - 1))
        if drift > .10:
            print(f'  WARN: {n}: frame 0 differs from the start picture by {100 * drift:.0f}% in box size: the '
                  f'generator reframed the start, or the start picture is not this clip\'s')
    if a.debug_dir:
        dd = Path(a.debug_dir)
        dd.mkdir(parents=True, exist_ok=True)
        for t, tag in ((0, 'frame0'), (pk, f'peak{pk}')):
            img = frames[t].copy()
            sil = full[t]
            img[sil] = (.5 * img[sil] + .5 * np.array([0, 200, 255])).astype(np.uint8)
            for n, p in panels:
                m = per[n][t]
                if m and getattr(p, 'turn', 0) == 0:
                    cv2.rectangle(img, (p.x0i + m['x0'], p.y0i + m['y0']), (p.x0i + m['x1'], p.y0i + m['y1']),
                                  (0, 0, 255), 1)
                r = ref[n]
                if getattr(p, 'turn', 0) == 0:
                    cv2.rectangle(img, (p.x0i + r['x0'], p.y0i + r['y0']), (p.x0i + r['x1'], p.y0i + r['y1']),
                                  (0, 255, 0), 1)
            cv2.imwrite(str(dd / f'{name}_{tag}.png'), img)
    if a.json:
        Path(a.json).write_text(json.dumps(dict(clip=name, verdict=verdict, metric=a.metric, max=a.max,
                                                scale=round(float(smax), 4), width=round(wmax, 4),
                                                height=round(hmax, 4), peak_frame=pk, frames=T, size=[W, H],
                                                reasons=reasons, warnings=warns, panels=split_src, start=start_info, series=series,
                                                frame0={n: {k: v for k, v in r.items()} for n, r in ref.items()}),
                                           indent=1), encoding='utf-8')
    return 1 if reasons else 0


if __name__ == '__main__':
    sys.exit(main())
