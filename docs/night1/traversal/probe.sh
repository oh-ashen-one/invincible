#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P3 fast telemetry probe (no pixels: -nullrhi): replays a traversal script in the real game and writes <out>/probe_telemetry.csv.
# usage: docs/night1/traversal/probe.sh <script.json> <out dir> <quit s> [-WHTravTune=A=1,B=2 ...]   (map: TRAV_MAP, default the lit city)
HERE="$(cd "$(dirname "$0")" && pwd)"; UE_DIR="$(cd "$HERE/../../../unreal/WebHomage" && pwd)"
J="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"; OUT="$2"; Q="$3"; shift 3
MAP="${TRAV_MAP:-/Game/Maps/Manhattan}"
while [ "$(pgrep -x UnrealEditor | wc -l)" -ge 3 ]; do sleep 5; done
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label traversal -- "$UE_DIR/Scripts/run_game.sh" "$OUT" -map "$MAP" \
  -res 1920x1080 -quit "$Q" -name probe -timeout 900 -- -nullrhi -benchmark -fps=60 -WHTravScript="$J" -WHTravCsv="$OUT/probe_telemetry.csv" "$@" | tail -1
grep -E "building boxes|WH_TRAV_SCRIPT" "$OUT/probe.log" | sed 's/^.*Display: //' | head -3
