#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round-11 measurements: everything of analyze_r10.sh (fight bone log, contact, video activity, YOLO, tee see-through, thug wedge) plus the hair check of the three hair
# faces (eval/hair_4k.py: straight colour seams >= 40 px inside the hair, flat cards > 20 px, background enclosed between hair and skin), on this round and the previous one.
#   tools/ue_char/analyze_r11.sh <captures_dir> <evidence_dir> [<round10_captures_dir>]
set -u
WT="$(cd "$(dirname "$0")/../.." && pwd)"
CAP=${1:?captures}; EV=${2:?evidence}; RP=${3:-}
mkdir -p "$EV"
"$WT/tools/ue_char/analyze_r10.sh" "$CAP" "$EV" "$RP"
# head boxes of the lineup close-ups (4K): the hair and the upper face
BOXES="hood:1150,0,2800,1150 beard:1250,0,2750,1100 tee:1050,150,2600,1600"
for tag in r11 prev; do
  D=$CAP; [ $tag = prev ] && D=$RP; [ -n "$D" ] || continue
  for f in $BOXES; do
    n=${f%%:*}; b=${f#*:}
    [ -f "$D/${n}_face_4k.jpg" ] && python3 "$WT/tools/ue_char/eval/hair_4k.py" "$D/${n}_face_4k.jpg" --box "$b" --json "$EV/hair_${n}_${tag}.json" --out "$EV/hair_${n}_${tag}.jpg" > /dev/null
  done
done
echo "analyze_r11 done -> $EV"
