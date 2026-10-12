#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat r04: build the blind critic pack (pairs.json + abpack) from round-04/ and the private refs.
#   critic_pack_r04.sh <critic_dir>       e.g. /Users/midir/sm2-n1/_scratch/critic-P5-r04
set -uo pipefail
C="$1"; HERE="$(cd "$(dirname "$0")" && pwd)"; R="$HERE/round-04"; R3="$HERE/round-03"
REFS=/Users/midir/spiderman-learnings/refs/combat
mkdir -p "$C"
# finisher excerpt (8 s around the finisher push-in) and a hit-dense excerpt (10 s) of the published movie
FT=$(python3 - "$R/ue/movie/fight_events.jsonl" <<'PY'
import json, sys
ev = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
t = next((e['rt'] for e in ev if e['ev'].startswith('cine finisher')), 14.0)
print('%.2f' % max(0.0, t - 0.9 - 1.0))
PY
)
HT=$(python3 - "$R/ue/movie/fight_events.jsonl" <<'PY'
import json, sys
ev = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
hits = [e['rt'] for e in ev if e['ev'].startswith('hit ') and '->' in e['ev']]
best = max(range(0, 20), key=lambda s: sum(1 for h in hits if s + 0.9 <= h < s + 10.9))
print('%.2f' % best)
PY
)
ffmpeg -loglevel error -y -ss "$FT" -t 8 -i "$R/fight30_1080p60.mp4" -an -c:v libx264 -crf 22 -pix_fmt yuv420p "$C/ours_finisher.mp4"
ffmpeg -loglevel error -y -ss "$HT" -t 10 -i "$R/fight30_1080p60.mp4" -an -c:v libx264 -crf 22 -pix_fmt yuv420p "$C/ours_hits.mp4"
python3 - "$C" "$R" "$R3" "$REFS" <<'PY'
import glob, json, os, re, sys
C, R, R3, REFS = sys.argv[1:5]
def still(d, t):
    """the still of directory d closest to game time t (file names still_NN_tTT.TT.jpg)"""
    best = None
    for f in glob.glob(os.path.join(d, 'stills', 'still_[0-9]*_t*.jpg')):
        m = re.search(r'_t([0-9.]+)\.jpg$', f)
        if m and (best is None or abs(float(m.group(1)) - t) < best[0]): best = (abs(float(m.group(1)) - t), f)
    return best[1] if best else None
pairs = [
 dict(id='street-combo', x=R + '/fight30_1080p60.mp4', y=REFS + '/clips/street-combo__nm_0214-0224.mp4', note='street fight combo against a group'),
 dict(id='street-fight-2', x=R + '/fight30_1080p60.mp4', y=REFS + '/clips/street-fight-cars__nm_0500-0510.mp4', note='street fight'),
 dict(id='plaza-fight', x=R + '/fight30_1080p60.mp4', y=REFS + '/clips/plaza-fight__dn_0818-0828.mp4', note='open-space group fight'),
 dict(id='night-street-fight', x=R + '/fight30_1080p60.mp4', y=REFS + '/clips/night-street-fight__nt_0755-0805.mp4', note='street fight, attackers around the hero'),
 dict(id='hit-moments', x=C + '/ours_hits.mp4', y=REFS + '/clips/street-combo__nm_0214-0224.mp4', note='ten seconds of blows landing: the impact effect and the reaction of each victim'),
 dict(id='finisher', x=C + '/ours_finisher.mp4', y=REFS + '/clips/symbiote-finisher__nm_0530-0538.mp4', note='takedown finisher beat'),
 dict(id='group-still', x=still(R, 3.05), y=REFS + '/group-fight-nm__nm_0223.jpg', note='hero fighting a group'),
 dict(id='air-still', x=still(R, 7.78), y=REFS + '/air-combat-nm__nm_0248.jpg', note='air combat / juggle'),
 dict(id='contact-still', x=still(R, 1.87), y=REFS + '/combo-hit-nm__nm_0217.jpg', note='the moment of a hit (first blow of a combo)'),
 dict(id='contact-still-2', x=still(R, 2.66), y=REFS + '/combo-hit-nm__nm_0217.jpg', note='the moment of a hit (the ender of a combo)'),
 dict(id='web-still', x=still(R, 9.37), y=REFS + '/web-shooter-nm__nm_0244.jpg', note='web shot at an enemy'),
 dict(id='prev-vs-now', x=R + '/fight30_1080p60.mp4', y=R3 + '/fight30_1080p60.mp4', note='two versions of the same scripted street fight'),
 dict(id='prev-vs-now-hit', x=still(R, 15.65), y=still(R3, 15.65), note='the same instant of two versions of the fight: a takedown blow lands'),
]
pairs = [p for p in pairs if p['x'] and p['y']]
json.dump(pairs, open(C + '/pairs.json', 'w'), indent=1)
print('pairs', len(pairs))
PY
python3 /Users/midir/spider-man-2-astra6/tools/night1/abpack.py "$C/pack" "$C/pairs.json"
