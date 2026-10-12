#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round-10 measurements on a capture directory, written to <evidence_dir>.   tools/ue_char/analyze_r10.sh <captures_dir> <evidence_dir> [<round09_captures_dir>]
#   fight: the engine's bone log (fight_bones.csv) against the round-10 target (fight/r10_check.py: >= 4 hit reactions >= 0.1 stature within 0.2 s, >= 2 knockdowns with 2 enemies on the
#          ground together >= 1 s, >= 2 distinct get-ups, no guard held > 2 s) for the three 8 s clips; strike reach (contact_check.py); pixel activity of every clip; YOLO counts;
#   faces: tee see-through holes, thug collar skin components (before = round 09)
set -u
WT="$(cd "$(dirname "$0")/../.." && pwd)"
CAP=${1:?captures}; EV=${2:?evidence}; R9=${3:-}
export P2_SCRATCH="${P2_SCRATCH:-$WT/unreal/WebHomage/Saved/P2Build}"
mkdir -p "$EV"
F="$CAP/fight_bones.csv"
if [ -f "$F" ]; then
  python3 "$WT/tools/ue_char/fight/r10_check.py" "$F" "$EV/r10_check.json" > "$EV/r10_check.txt"
  python3 "$WT/tools/ue_char/fight/contact_check.py" "$F" "$EV/contact_check.json" > "$EV/contact_check.txt" 2>&1 || true
fi
for c in street_fight_wide street_fight_34 street_fight_orbit; do
  [ -f "$CAP/$c.mp4" ] && python3 "$WT/tools/ue_char/fight/video_activity.py" "$CAP/$c.mp4" --json "$EV/video_activity_$c.json" > "$EV/video_activity_$c.txt"
done
[ -f "$CAP/tee_face_4k.jpg" ] && python3 "$WT/tools/ue_char/eval/seethrough_4k.py" "$CAP/tee_face_4k.jpg" --out "$EV/tee_seethrough_r10.png" > "$EV/tee_seethrough_r10.json"
[ -f "$CAP/thug_face_4k.jpg" ] && python3 "$WT/tools/ue_char/eval/wedge_4k.py" "$CAP/thug_face_4k.jpg" --out "$EV/thug_wedge_r10.png" > "$EV/thug_wedge_r10.json"
if [ -n "$R9" ]; then
  [ -f "$R9/thug_face_4k.jpg" ] && python3 "$WT/tools/ue_char/eval/wedge_4k.py" "$R9/thug_face_4k.jpg" --out "$EV/thug_wedge_r9.png" > "$EV/thug_wedge_r9.json"
  [ -f "$R9/tee_face_4k.jpg" ] && python3 "$WT/tools/ue_char/eval/seethrough_4k.py" "$R9/tee_face_4k.jpg" --out "$EV/tee_seethrough_r9.png" > "$EV/tee_seethrough_r9.json"
fi
YOLO_DEVICE=cpu OMP_NUM_THREADS=4 "$WT/tools/ue_char/analyze_r5.sh" "$CAP" "$EV" > "$EV/analyze_r5.log" 2>&1 || true
echo "analyze_r10 done -> $EV"
