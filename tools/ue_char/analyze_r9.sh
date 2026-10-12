#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round-09 measurements on a capture directory, written to <evidence_dir>.   tools/ue_char/analyze_r9.sh <captures_dir> <evidence_dir> [<round08_captures_dir>]
#   fight: bone log (fight_bones.csv) -> reactions / knockdown / idle windows (fight_check.py), strike reach (contact_check.py), pixel activity of every fight clip (video_activity.py,
#          per-walker boxes for the 3/4 clip), YOLO counts (analyze_r5.sh, CPU);   faces: see-through holes of tee_face_4k, skin components in the collar of thug_face_4k (before = round 08)
set -u
WT="$(cd "$(dirname "$0")/../.." && pwd)"
CAP=${1:?captures}; EV=${2:?evidence}; R8=${3:-}
export P2_SCRATCH="${P2_SCRATCH:-$WT/unreal/WebHomage/Saved/P2Build}"
mkdir -p "$EV"
F="$CAP/fight_bones.csv"
if [ -f "$F" ]; then
  python3 "$WT/tools/ue_char/fight/fight_check.py" "$F" "$EV/fight_check_street_fight_34.json" --t0 8 --t1 16 --video "$CAP/street_fight_34.mp4" --video-t0 8.05 --cam -660,-335,410,0,0,95,48 > "$EV/fight_check_street_fight_34.txt"
  python3 "$WT/tools/ue_char/fight/fight_check.py" "$F" "$EV/fight_check_street_fight_wide.json" --t0 0 --t1 8 --video "$CAP/street_fight_wide.mp4" --video-t0 0.05 --cam -30,-900,500,0,0,95,52 > "$EV/fight_check_street_fight_wide.txt"
  python3 "$WT/tools/ue_char/fight/fight_check.py" "$F" "$EV/fight_check_street_fight_orbit.json" --t0 16 --t1 24 > "$EV/fight_check_street_fight_orbit.txt"
  python3 "$WT/tools/ue_char/fight/contact_check.py" "$F" "$EV/contact_check.json" > "$EV/contact_check.txt"
fi
for c in street_fight_wide street_fight_34 street_fight_orbit; do
  [ -f "$CAP/$c.mp4" ] && python3 "$WT/tools/ue_char/fight/video_activity.py" "$CAP/$c.mp4" --json "$EV/video_activity_$c.json" > "$EV/video_activity_$c.txt"
done
[ -f "$CAP/tee_face_4k.jpg" ] && python3 "$WT/tools/ue_char/eval/seethrough_4k.py" "$CAP/tee_face_4k.jpg" --out "$EV/tee_seethrough_r9.png" > "$EV/tee_seethrough_r9.json"
[ -f "$CAP/thug_face_4k.jpg" ] && python3 "$WT/tools/ue_char/eval/wedge_4k.py" "$CAP/thug_face_4k.jpg" --out "$EV/thug_wedge_r9.png" > "$EV/thug_wedge_r9.json"
if [ -n "$R8" ]; then
  [ -f "$R8/tee_face_4k.jpg" ] && python3 "$WT/tools/ue_char/eval/seethrough_4k.py" "$R8/tee_face_4k.jpg" --out "$EV/tee_seethrough_r8.png" > "$EV/tee_seethrough_r8.json"
  [ -f "$R8/thug_face_4k.jpg" ] && python3 "$WT/tools/ue_char/eval/wedge_4k.py" "$R8/thug_face_4k.jpg" --out "$EV/thug_wedge_r8.png" > "$EV/thug_wedge_r8.json"
fi
YOLO_DEVICE=cpu OMP_NUM_THREADS=4 "$WT/tools/ue_char/analyze_r5.sh" "$CAP" "$EV" > "$EV/analyze_r5.log" 2>&1 || true
echo "analyze_r9 done -> $EV"
