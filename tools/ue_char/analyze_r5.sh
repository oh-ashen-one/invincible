#!/bin/bash
# Round-05 measurements on the captures (pixels), written to <captures>/../evidence/. Fan homage project; not official Marvel/Sony/Insomniac.
#   tools/ue_char/analyze_r5.sh <captures_dir> <evidence_dir>
# needs the ultralytics venv ($P2_SCRATCH/r4/yv) and the critic's scripts (tools/ue_char/eval/critic_r04).
set -e
WT="$(cd "$(dirname "$0")/../.." && pwd)"
P2_SCRATCH="${P2_SCRATCH:-$WT/unreal/WebHomage/Saved/P2Build}"
PY="$P2_SCRATCH/r4/yv/bin/python"
CAP="${1:?captures}"; EV="${2:?evidence}"; mkdir -p "$EV"
CR="$WT/tools/ue_char/eval/critic_r04"; VC="$WT/tools/ue_char/eval/video_checks.py"
export YOLO_WEIGHTS="${YOLO_WEIGHTS:-/Users/midir/sm2-n1/_scratch/city/yolo/yolo11x-seg.pt}"
{ for f in crowd_tracking_4k crowd_wide_4k; do [ -f "$CAP/$f.jpg" ] && "$PY" "$CR/cracks.py" "$CAP/$f.jpg"; done; } > "$EV/cracks_stills.txt" 2>&1 || true
{ for f in crowd_tracking crowd_wide street_fight_wide street_fight_34 street_fight_orbit; do [ -f "$CAP/$f.mp4" ] && "$PY" "$CR/count.py" "$CAP/$f.mp4"; done; } > "$EV/count_videos.txt" 2>&1 || true
for f in crowd_tracking_4k crowd_wide_4k street_fight_wide_4k street_fight_34_4k street_fight_orbit_4k; do
  [ -f "$CAP/$f.jpg" ] && "$PY" "$VC" people "$CAP/$f.jpg" > "$EV/yolo_$f.json" 2>&1 || true
done
[ -f "$CAP/hero_run_side.mp4" ] && "$PY" "$VC" head_bob "$CAP/hero_run_side.mp4" 0.5 5.9 > "$EV/video_hero_run_side_headbob.json" 2>&1 || true
[ -f "$CAP/hero_run_side.mp4" ] && "$PY" "$VC" lean_belt "$CAP/hero_run_side.mp4" 0.5 5.9 > "$EV/video_hero_run_side_leanbelt.json" 2>&1 || true
[ -f "$CAP/hero_run_leap_side.mp4" ] && "$PY" "$VC" takeoff "$CAP/hero_run_leap_side.mp4" 0.3 3.0 > "$EV/hero_leap_takeoff.json" 2>&1 || true
# round 05b additions: gameplay (chase / toward) cameras, takeoff window of the leap clip, chroma-key see-through count (CH18 in the real engine)
for f in hero_run_chase hero_run_toward; do
  [ -f "$CAP/$f.mp4" ] && "$PY" "$VC" hero_run "$CAP/$f.mp4" 0.5 5.5 > "$EV/video_${f}_heroRun.json" 2>&1 || true
done
[ -f "$CAP/hero_run_leap_side.mp4" ] && "$PY" "$VC" takeoff "$CAP/hero_run_leap_side.mp4" 1.0 2.6 > "$EV/hero_leap_takeoff.json" 2>&1 || true
for f in "$CAP"/crowd_key_*_4k.jpg; do
  [ -f "$f" ] && "$PY" "$WT/tools/ue_char/eval/key_holes.py" "$f" "$EV/keyholes_$(basename "${f%.jpg}").png" >> "$EV/key_holes_after.jsonl" 2>&1 || true
done
[ -f "$CAP/crowd_tracking_4k.jpg" ] && "$PY" "$WT/tools/ue_char/eval/cracks_classify.py" "$CAP/crowd_tracking_4k.jpg" > "$EV/cracks_classify.jsonl" 2>&1 || true
python3 "$WT/tools/ue_char/eval/gait_phase.py" 0 5.5 11.5 > "$EV/gait_phase.json"
ls -la "$EV"
