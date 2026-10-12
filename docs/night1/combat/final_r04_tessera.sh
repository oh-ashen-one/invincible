#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# P5 combat r04, hold 2: the same capture as final_r04.sh, but with P2's ORIGINAL "Tessera" hero suit (/Game/Characters/Hero/SK_Hero + its A_Hero_* clips)
# instead of the HeroDev proxy, whose chest / back emblem copies an official suit (critic r03, "Brand").
#   1. Content/Characters is backed up, then rebuilt by build_combat.py --steps characters (P2's build_characters.py on a read-only staged copy of P2's derived
#      inputs: Tessera maps r8, people, thug), then the combat map; if the characters build fails the backup is restored and the chain stops (exit 5)
#   2. movie A (starburst) / movie B (-WHCmbFlare=0) / native 4K stills, all with the Tessera hero flags; replay_diff against the r03 record for each
# One gpu_slot hold, one engine at a time, nothing SIGKILLed (run_fight.sh / stop_ue.sh).
#   final_r04_tessera.sh <work_dir> <still_times> [record_dir]
set -uo pipefail
WORK="$1"; STILLS="$2"; HERE="$(cd "$(dirname "$0")" && pwd)"; REC="${3:-$HERE/round-03/ue/record}"; G=/Users/midir/sm2-n1/_scratch/gpu/bin
WT="$(cd "$HERE/../../.." && pwd)"; CH="$WT/unreal/WebHomage/Content/Characters"; BK=/Users/midir/sm2-n1/_scratch/combat/r04b/chars_backup
case "$BK" in /Users/midir/sm2-n1/_scratch/combat/*) ;; *) exit 1;; esac
mkdir -p "$WORK" "$BK"; WORK="$(cd "$WORK" && pwd)"; REC="$(cd "$REC" && pwd)"
rsync -a --delete "$CH/" "$BK/Characters/" || { echo "backup failed"; exit 1; }
export GPU_SLOT_CAPTURE_MAX_HOLD=5400
exec $G/gpu_slot.sh capture --label combat --timeout 14400 -- bash -c '
  HERE="$1"; WORK="$2"; REC="$3"; STILLS="$4"; WT="$5"; CH="$6"; BK="$7"; SC="$HERE/scripts/fight30.json"
  date "+chain start %H:%M:%S"
  if ! SM2_COMBAT_NOWAIT=1 python3 "$WT/unreal/WebHomage/Scripts/build_combat.py" --steps characters,combat > "$WORK/map_build.out" 2>&1; then
    echo "characters / map build failed: restoring Content/Characters"; rsync -a --delete "$BK/Characters/" "$CH/"
    SM2_COMBAT_NOWAIT=1 python3 "$WT/unreal/WebHomage/Scripts/build_combat.py" --steps combat > "$WORK/map_build_restore.out" 2>&1; exit 5
  fi
  date "+characters + map built %H:%M:%S"
  HERO="-WHHeroMesh=/Game/Characters/Hero/SK_Hero.SK_Hero -WHHeroLens=none -WHHeroClips=/Game/Characters/Hero/Anims -WHHeroClipPrefix=A_Hero_"
  export WHCMB_EXEC="r.ScreenPercentage 100"
  WHCMB_EXTRA="$HERO" "$HERE/run_fight.sh" movie "$WORK/movieA" "$SC" > "$WORK/movieA.out" 2>&1; echo "movie A done rc=$?"; date "+%H:%M:%S"
  grep -h "WH_CMB_RES" "$WORK/movieA/fight.log" | head -2; grep -h "WH_TRAV hero" "$WORK/movieA/fight.log" | head -3
  python3 "$HERE/replay_diff.py" "$REC" "$WORK/movieA" | tee "$WORK/movieA_diff.txt"
  WHCMB_EXTRA="$HERO -WHCmbFlare=0" "$HERE/run_fight.sh" movie "$WORK/movieB" "$SC" > "$WORK/movieB.out" 2>&1; echo "movie B done rc=$?"; date "+%H:%M:%S"
  python3 "$HERE/replay_diff.py" "$REC" "$WORK/movieB" | tee "$WORK/movieB_diff.txt"
  if [ -n "$STILLS" ]; then
    WHCMB_EXTRA="$HERO" "$HERE/run_fight.sh" stills "$WORK/stills" "$SC" "$STILLS" > "$WORK/stills.out" 2>&1; echo "stills done rc=$?"; date "+%H:%M:%S"
    python3 "$HERE/replay_diff.py" "$REC" "$WORK/stills" | tee "$WORK/stills_diff.txt"
  fi
  echo "chain done"' _ "$HERE" "$WORK" "$REC" "$STILLS" "$WT" "$CH" "$BK"
