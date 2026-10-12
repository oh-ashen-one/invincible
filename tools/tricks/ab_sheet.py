# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Tricks C round 1: side-by-side contact sheets of OUR flips vs the owner's reference clip at matched phases (shape held).
#   python3 tools/tricks/ab_sheet.py <ours.mp4> <telemetry.csv> <out.jpg> [--owner <owner.mov>] [--ours-only | --owner-only] [--nolabel]
# One row per phase (tuck, pike, layout, inverted pencil, straddle, throne / upright spread, twist, open-out / catch reach): the owner frame
# (FLIPS_SPEC segment times) on the left, then up to 3 of our frames from DIFFERENT programs at the middle of a held segment of that shape
# (telemetry flip_shape = flip_shape_legs), cropped around the hero's pixel box (px_*) so he fills ~0.3 of the crop height like the owner
# clip (FLIPS_SPEC F9: 0.18-0.36). The owner frames are footage of the real game: a sheet made WITH them stays in _scratch (never committed);
# --ours-only makes the committable half.
import csv, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

OWNER_T = {  # owner clip seconds per phase (FLIPS_SPEC measured segments)
    'Tuck': [1.12, 9.94], 'Pike': [21.90], 'Layout': [1.88, 8.80], 'Pencil': [5.30, 22.30], 'Straddle': [10.48, 22.58],
    'Throne': [23.20], 'Twist': [8.84], 'Reach': [2.40], 'Kickout': [11.32],
}
ROWS = ['Tuck', 'Pike', 'Layout', 'Twist', 'Straddle', 'Pencil', 'Kickout', 'Reach']
CW, CH = 420, 383  # cell (owner clip aspect 610:556)


def grab(video, t, out):
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', '%.3f' % t, '-i', video, '-frames:v', '1', out], check=True)
    return Image.open(out).convert('RGB')


def main():
    a = sys.argv[1:]
    ours, tel, out = a[0], a[1], a[2]
    owner = a[a.index('--owner') + 1] if '--owner' in a else '/Users/midir/sm2-n1/_scratch/refs/owner/flips_owner_2026-09-29.mov'
    ours_only = '--ours-only' in a
    owner_only = '--owner-only' in a
    nolabel = '--nolabel' in a
    T = list(csv.DictReader(open(tel)))
    # held segments: runs of the same shape on body + legs inside one program instance
    segs, cur = [], None
    for r in T:
        s, l, p = r.get('flip_shape', ''), r.get('flip_shape_legs', ''), r.get('flip_prog', '')
        if s and s == l:
            if cur and cur['shape'] == s and cur['prog'] == p and float(r['t']) - cur['t1'] < 0.05:
                cur['t1'] = float(r['t']); cur['rows'].append(r)
            else:
                cur = dict(shape=s, prog=p, t0=float(r['t']), t1=float(r['t']), rows=[r]); segs.append(cur)
        else:
            cur = None
    tmp = tempfile.mkdtemp(prefix='absheet_', dir='/Users/midir/sm2-n1/_scratch/tricks')
    font = ImageFont.load_default()
    ncol = 3 if ours_only else (2 if owner_only else 4)
    sheet = Image.new('RGB', (CW * ncol, CH * len(ROWS)), (20, 20, 20))
    dr = ImageDraw.Draw(sheet)
    for ri, shape in enumerate(ROWS):
        y = ri * CH
        c0 = 0
        if not ours_only:
            ts = OWNER_T.get(shape, [])
            for oi, ot in enumerate(ts[:2 if owner_only else 1]):
                im = grab(owner, ot, os.path.join(tmp, 'o_%s_%d.png' % (shape, oi))).resize((CW, CH))
                sheet.paste(im, (oi * CW, y))
                if not nolabel: dr.text((oi * CW + 6, y + 6), 'REFERENCE %s  t %.2f s' % (shape, ot), fill=(255, 255, 0), font=font)
            c0 = 1
            if owner_only: continue
        # our segments of this shape: longest per program first, different programs
        cand = sorted([s for s in segs if s['shape'] == shape and len(s['rows']) >= 6], key=lambda s: -len(s['rows']))
        used, picks = set(), []
        for s in cand:
            if s['prog'] in used: continue
            used.add(s['prog']); picks.append(s)
            if len(picks) == ncol - c0: break
        for ci, s in enumerate(picks):
            r = s['rows'][len(s['rows']) // 2]
            t = float(r['t'])
            im = grab(ours, t, os.path.join(tmp, 'u_%s_%d.png' % (shape, ci)))
            try:
                x0, x1, y0, y1 = float(r['px_left']), float(r['px_right']), float(r['px_top']), float(r['px_bottom'])
                ok = x1 > x0 and y1 > y0
            except Exception:
                ok = False
            W, H = im.size
            sx, sy = W / 1920.0, H / 1080.0
            if ok:
                cx, cy, hh = (x0 + x1) / 2 * sx, (y0 + y1) / 2 * sy, max((y1 - y0) * sy, (x1 - x0) * sy)
                ch = min(H, max(160.0, hh / 0.30)); cw = ch * CW / CH
                bx = max(0, min(W - cw, cx - cw / 2)); by = max(0, min(H - ch, cy - ch / 2))
                im = im.crop((int(bx), int(by), int(bx + cw), int(by + ch)))
            im = im.resize((CW, CH))
            sheet.paste(im, ((c0 + ci) * CW, y))
            if not nolabel: dr.text(((c0 + ci) * CW + 6, y + 6), 'OURS %s  %s  t %.2f s' % (shape, s['prog'], t), fill=(0, 255, 255), font=font)
    sheet.save(out, quality=88)
    print('sheet', out, sheet.size)


if __name__ == '__main__':
    main()
