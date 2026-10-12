#!/bin/bash
# Round-09 capture driver (Fan homage project; not official Marvel/Sony/Insomniac; no affiliation): the round-08 groups (run_r8_captures.sh) with the stills of the scripted fight
# picked at chosen instants of the choreography (tools/ue_char/fight/choreo.py: 3.8 s thug hit, 9.6 s knockdown, 21.0 s orbit).  F also writes the walkers' bone log (fight_bones.csv).
#   tools/ue_char/run_r9_captures.sh <out_dir> "F E C S"        (one engine of mine at any moment, every launch through gpu_slot.sh)
export GF_TIMES="${GF_TIMES:-3.8,9.6,21.0}"
exec "$(dirname "$0")/run_r8_captures.sh" "$@"
