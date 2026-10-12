#!/usr/bin/env python3
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
"""Round 17: shot-cut / snap detector for the character clips (critic r16: the pawn clip's 'yaw snap' at 9.933 s: frame diff 15.5 against 3.4 for its neighbours, and the crowd clip's cut at 7.483 s: 56.7 against 1.4).

  python3 tools/ue_char/suits/cut_check_r17.py CLIP.mp4 [--json OUT.json] [--at 9.933,7.483] [--ratio 4]

Frame-to-frame mean absolute luma difference on 480-px-wide frames (ffmpeg decode, every frame).  Reports: median, p99, the 5 largest steps with their times, and for each --at time the step at that time
against the median of the +-0.5 s neighbours.  PASS = no step > RATIO x the median of its +-0.5 s neighbours AND > 8 luma (a deliberate suit swap of the pawn clip is a hero-colour step of a few luma only; a
director shot cut is a whole-frame change of 15 - 60).
"""
import sys, json, subprocess
import numpy as np


def frames(path, w=480):
    p = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate,nb_frames', '-of', 'json', path], capture_output=True, text=True)
    st = json.loads(p.stdout)['streams'][0]
    W, H = int(st['width']), int(st['height']); h = int(round(H * w / W / 2) * 2)
    num, den = st['r_frame_rate'].split('/'); fps = float(num) / float(den)
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf', 'scale=%d:%d' % (w, h), '-pix_fmt', 'gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.int16)
    return a, fps


def main():
    path = sys.argv[1]
    a, fps = frames(path)
    d = np.abs(np.diff(a, axis=0)).mean(axis=(1, 2))
    t = (np.arange(len(d)) + 1) / fps
    ratio = float(sys.argv[sys.argv.index('--ratio') + 1]) if '--ratio' in sys.argv else 4.0
    out = dict(clip=path, frames=int(len(a)), fps=fps, duration=round(len(a) / fps, 3), median=round(float(np.median(d)), 2), p99=round(float(np.percentile(d, 99)), 2),
               top=[dict(t=round(float(t[i]), 3), diff=round(float(d[i]), 2)) for i in np.argsort(-d)[:5]])
    cuts = []
    k = int(0.5 * fps)
    for i in range(len(d)):
        nb = np.concatenate([d[max(0, i - k):max(0, i - 1)], d[i + 2:i + k]])
        if len(nb) < 4: continue
        m = float(np.median(nb))
        if d[i] > 8 and d[i] > ratio * max(m, 1.0): cuts.append(dict(t=round(float(t[i]), 3), diff=round(float(d[i]), 2), neighbours=round(m, 2)))
    out['cuts'] = cuts; out['pass'] = not cuts
    if '--at' in sys.argv:
        out['at'] = []
        for s in sys.argv[sys.argv.index('--at') + 1].split(','):
            ta = float(s)
            if ta * fps >= len(d): out['at'].append(dict(t=ta, note='beyond the clip (%.2f s)' % out['duration'])); continue
            i = int(round(ta * fps)) - 1; nb = np.concatenate([d[max(0, i - k):max(0, i - 1)], d[i + 2:i + k]])
            out['at'].append(dict(t=ta, diff=round(float(d[max(0, i - 1):i + 2].max()), 2), neighbours=round(float(np.median(nb)), 2)))
    if '--json' in sys.argv: json.dump(out, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
    print(json.dumps(out))


if __name__ == '__main__':
    main()
