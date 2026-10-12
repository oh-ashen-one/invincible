#!/usr/bin/env python3
"""Writes docs/night1/final/swing/SHOTLIST.md for a round from clips.json, the scripts and the round's *_render.json. usage: make_shotlist.py <round> <build commit>"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
rnd, commit = sys.argv[1], sys.argv[2]
S = ROOT / 'docs/night1/traversal/scripts/final'; D = ROOT / 'docs/night1/final/swing'
clips = json.loads((S / 'clips.json').read_text())
L = ['# Final swing loop: shot list (builder SW)', '', '> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.', '',
     'Round `%s`; build commit %s (round 00 = behaviour of tag `final-before` 16d24911 plus telemetry-only columns); scripts `docs/night1/traversal/scripts/final/`.' % (rnd, commit), '',
     '## Settings (every clip)', '- real `-game` (`tools/final/swing/run_clip.py` -> `tools/showcase/play.py --capture`), `-WHProfile=playable -WHResScale=100`, `-WHPerfPreset=unreal/WebHomage/Config/PerfPlayableFast.cvars`, TSR (r.AntiAliasingMethod 4)',
     '- output 1920x1080, internal 1920x1080 (r.ScreenPercentage 100), fixed 1/60 s (`-benchmark -fps=60`), `-dumpmovie` through `-WHMovieAsync`, `-WHTravPreroll=1.5` (the 1.5 s of pre-roll frames are cut: frames - telemetry rows)',
     '- default suit (DA_HeroSuits entry 0, Tessera); maps `/Game/Showcase/Maps/Manhattan_Island` (golden: s1-s4) and `Manhattan_Island_Night` (s5); H.264 mp4 <= 15 MB (crf raised until it fits)',
     '- evidence = offline visual evidence of scripted input routes, never perf', '',
     '- scene difference against round 00: from round 01 on the island maps also compose /Game/PropsM3/Maps/PropsM3_Island (supplied props, mostly on lawns and plazas, tiny from swing height) -- not a swing change', '', '## Clips']
for clip, cases in [(k, v) for k, v in clips.items() if k != '_q']:
    rj = D / rnd / (clip + '_render.json')
    r = json.loads(rj.read_text()) if rj.exists() else None
    L.append('### %s%s' % (clip, ' (%.1f s, %d frames, %.1f MB, crf %d, engine wall %.0f s)' % (r['duration_s'], r['frames'], r['mp4_mb'], r['crf'], r['wall_s_total']) if r else ''))
    for name, q in cases:
        d = json.loads((S / (name + '.json')).read_text()); sp = d['spawn']
        L.append('- `%s` (%.1f s): spawn %s yaw %s vel %s; %s' % (name, q, sp['pos'], sp.get('yaw'), sp.get('vel'), d.get('note', '')))
        L.append('  keys: `%s`%s' % (json.dumps([{k: v for k, v in kk.items()} for kk in d['keys']])[:900], ' tune `%s`' % d['tune'] if d.get('tune') else ''))
    if r: L.append('  render throughput: ' + '; '.join('%s %d frames in %.0f s = %.1f fps' % (c['case'], c['frames_rendered'], c['wall_s'], c['fps_render']) for c in r['cases']))
(D / 'SHOTLIST.md').write_text('\n'.join(L) + '\n')
print('wrote', D / 'SHOTLIST.md')
