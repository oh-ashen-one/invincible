#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat r03: build the blind critic pack (pairs.json + abpack) from round-03/ and the private refs.
#   critic_pack_r03.sh <critic_dir>       e.g. /Users/midir/sm2-n1/_scratch/critic-P5-r03
set -uo pipefail
C="$1"; HERE="$(cd "$(dirname "$0")" && pwd)"; R="$HERE/round-03"; R2="$HERE/round-02"
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
S=$(ls "$R"/stills/still_0[0-9]_*.jpg 2>/dev/null)
st() { ls "$R"/stills/still_$1_*.jpg | head -1; }
python3 - "$C" "$R" "$R2" "$REFS" "$(st 05)" "$(st 02)" "$(st 01)" "$(st 04)" <<'PY'
import json, sys
C, R, R2, REFS, group, air, contact, web = sys.argv[1:9]
pairs = [
 dict(id='street-combo', x=R + '/fight30_1080p60.mp4', y=REFS + '/clips/street-combo__nm_0214-0224.mp4', note='street fight combo against a group'),
 dict(id='street-fight-2', x=R + '/fight30_1080p60.mp4', y=REFS + '/clips/street-fight-cars__nm_0500-0510.mp4', note='street fight'),
 dict(id='plaza-fight', x=R + '/fight30_1080p60.mp4', y=REFS + '/clips/plaza-fight__dn_0818-0828.mp4', note='open-space group fight'),
 dict(id='night-street-fight', x=R + '/fight30_1080p60.mp4', y=REFS + '/clips/night-street-fight__nt_0755-0805.mp4', note='street fight, attackers around the hero'),
 dict(id='hit-moments', x=C + '/ours_hits.mp4', y=REFS + '/clips/street-combo__nm_0214-0224.mp4', note='ten seconds of blows landing: the reaction and impact of each hit'),
 dict(id='finisher', x=C + '/ours_finisher.mp4', y=REFS + '/clips/symbiote-finisher__nm_0530-0538.mp4', note='takedown finisher beat'),
 dict(id='group-still', x=group, y=REFS + '/group-fight-nm__nm_0223.jpg', note='hero fighting a group'),
 dict(id='air-still', x=air, y=REFS + '/air-combat-nm__nm_0248.jpg', note='air combat / juggle'),
 dict(id='contact-still', x=contact, y=REFS + '/combo-hit-nm__nm_0217.jpg', note='the moment of a hit'),
 dict(id='web-still', x=web, y=REFS + '/web-shooter-nm__nm_0244.jpg', note='web shot at an enemy'),
 dict(id='prev-vs-now', x=R + '/fight30_1080p60.mp4', y=R2 + '/fight30_1080p60.mp4', note='two versions of the same scripted street fight'),
]
json.dump(pairs, open(C + '/pairs.json', 'w'), indent=1)
print('pairs', len(pairs))
PY
python3 /Users/midir/spider-man-2-astra6/tools/night1/abpack.py "$C/pack" "$C/pairs.json"
