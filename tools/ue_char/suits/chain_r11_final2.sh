#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 11, final hold (resume after the 14:22 interruption): the manual-exposure stills of chain_r11_final.sh came out BLACK (AEM_Manual = camera EV100 9.9 - bias; the stage's sun is 8 lux), so this
# chain first CALIBRATES the exposure bias on the real map (960x540 front shots, the bias whose bare-floor luma matches auto exposure's 170), then runs, all with that bias:
# 4K stills of every suit -> playable-pawn swap movie (7 real T presses) -> persistence relaunch -> settings-menu shot -> orbit movie.
#   /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label characters -- bash tools/ue_char/suits/chain_r11_final2.sh <out_dir>
# Every launch is nested in that hold (one engine at a time, run_game.sh stops by SIGTERM only).  Two engine crashes -> the chain stops (RULES.md).
#   STEPS="build calib stills pawn persist menu orbit"   EV=<bias> skips the calibration
set -u
WT="$(cd "$(dirname "$0")/../../.." && pwd)"
export P2_SCRATCH="${P2_SCRATCH:-/Users/midir/sm2-n1/_scratch/characters}"
OUT="${1:?out dir}"; mkdir -p "$OUT"
STEPS="${STEPS:-build calib stills pawn persist menu orbit}"
T0=$(date +%s); log() { echo "[final2 $(date +%H:%M:%S) +$(( $(date +%s) - T0 ))s] $*" | tee -a "$OUT/final.log"; }
has() { case " $STEPS " in *" $1 "*) return 0;; esac; return 1; }
cd "$WT/unreal/WebHomage"
MAP=/Game/Tests/Characters/Char_Skins; MAPP=/Game/Tests/Characters/Char_SkinsPlay
SJ="$P2_SCRATCH/skins_shots.json"
CFG="$WT/unreal/WebHomage/Saved/Config"
CAL="$WT/tools/ue_char/suits/ev_calib.py"
PAWN="-WHHeroMesh=/Game/Characters/Hero/SK_Hero -WHHeroLens=none -WHHeroClips=/Game/Characters/Hero/Anims -WHHeroClipPrefix=A_Hero_ -WHTravScript=$WT/tools/ue_char/suits/pawn_run.json -WHHeroFill=0,0"
CRASHES=0
check() {   # dir name: an engine run that never logged WH_QUIT crashed (or was killed)
  if ! grep -q "WH_QUIT" "$1/$2.log" 2>/dev/null; then CRASHES=$((CRASHES + 1)); log "ENGINE RUN WITHOUT WH_QUIT ($1): crash count $CRASHES"; fi
  if [ "$CRASHES" -ge 2 ]; then log "two engine crashes: stopping the chain and reporting (RULES.md)"; exit 9; fi
}
if [ -n "${EV:-}" ]; then :; else EV=""; fi

if has build; then
  log "build: skins,skinsmap (bias default in build_characters.py)"
  BUILD_STDOUT="$OUT/build4.stdout" bash "$WT/tools/ue_char/fight/build_fight.sh" skins,skinsmap 2>&1 | tail -4
  cp "$WT/unreal/WebHomage/Saved/Logs/characters_build.log" "$OUT/characters_build4.log" 2>/dev/null
fi
[ -f "$SJ" ] || { log "no skins_shots.json"; exit 3; }

if has calib && [ -z "$EV" ]; then
  : > "$OUT/calib.txt"
  for TRY in 8.8 10.2; do
    log "calib: EV bias $TRY (960x540 front still)"
    rm -rf "$OUT/calib_$TRY"
    Scripts/run_game.sh "$OUT/calib_$TRY" -map $MAP -res 960x540 -exec "r.ScreenPercentage 100,r.MotionBlurQuality 0" -quit 5 -name skins -timeout 300 -- -WHCharShot=0 -WHStageShot=2.2 -WHExposure=$TRY < /dev/null | tail -2
    check "$OUT/calib_$TRY" skins
    F=$(ls "$OUT/calib_$TRY"/skins_00_t*.png 2>/dev/null | head -1)
    [ -n "$F" ] && echo "$TRY $(python3 "$CAL" luma "$F")" >> "$OUT/calib.txt"
  done
  for _ in 1 2; do
    N=$(python3 "$CAL" next "$OUT/calib.txt" 170)
    case "$N" in DONE*) EV=${N#DONE }; break;; esac
    log "calib: next EV $N"
    rm -rf "$OUT/calib_$N"
    Scripts/run_game.sh "$OUT/calib_$N" -map $MAP -res 960x540 -exec "r.ScreenPercentage 100,r.MotionBlurQuality 0" -quit 5 -name skins -timeout 300 -- -WHCharShot=0 -WHStageShot=2.2 -WHExposure=$N < /dev/null | tail -2
    check "$OUT/calib_$N" skins
    F=$(ls "$OUT/calib_$N"/skins_00_t*.png 2>/dev/null | head -1)
    [ -n "$F" ] && echo "$N $(python3 "$CAL" luma "$F")" >> "$OUT/calib.txt"
  done
  [ -z "$EV" ] && { N=$(python3 "$CAL" next "$OUT/calib.txt" 170); EV=${N#DONE }; }
  log "calib points (EV luma): $(tr '\n' ';' < "$OUT/calib.txt") -> EV $EV"
fi
[ -n "$EV" ] || EV=9.2
echo "$EV" > "$OUT/ev.txt"
log "exposure bias for every run: $EV"

TIMES=$(python3 - <<PY
import json
d = json.load(open("$SJ")); t0 = 0.0; out = []
for k in range(d['stills']):
    out.append('%.1f' % (t0 + 2.2)); t0 += d['shot_s'] + (1.0 if k == 0 else 0.0)
print(','.join(out), end='')
PY
)
if has stills; then
  log "stills stills_a: 4K, internal 3840x2160, EV $EV"
  ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' > "$OUT/gpu_util_before_stills.txt" || true
  Scripts/run_game.sh "$OUT/stills_a" -map $MAP -res 3840x2160 -exec "r.ScreenPercentage 100,r.MotionBlurQuality 0" -perf 3:130 -quit 135 -name skins -timeout 1200 \
      -- -WHCharShot=0 -WHStageShot="$TIMES" -WHExposure=$EV < /dev/null | tail -4
  check "$OUT/stills_a" skins
  python3 - <<PY
import json, glob, subprocess, os
d = json.load(open("$SJ")); views = d['views']
files = sorted(glob.glob("$OUT/stills_a/skins_[0-9][0-9]_t*.png"))
for f in files:
    k = int(os.path.basename(f).split('_')[1]); suit = d['suits'][k // len(views)].lower(); view = views[k % len(views)]
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', f, '-q:v', '2', "$OUT/stills_a/skin_%s_%s_4k.jpg" % (suit, view)]); os.remove(f)
print("stills_a", len(files), 'stills')
PY
  grep -E "WH_SUIT|WH_STAGE_SHOT|WH_EXPOSURE" "$OUT/stills_a/skins.log" > "$OUT/stills_a/suit_log.txt" 2>/dev/null
  log "floor luma of the tessera front still: $(python3 "$CAL" luma "$OUT/stills_a/skin_tessera_front_4k.jpg")"
fi

if has pawn; then
  find "$CFG" -name GameUserSettings.ini -delete 2>/dev/null
  log "pawn swap movie (1080p -movie, fixed 1/60 s), EV $EV"
  Scripts/run_game.sh "$OUT/pawn3" -map $MAPP -res 1920x1080 -quit 11.5 -name pawn -movie -exec "r.MotionBlurQuality 0,wh.Suit 2" -timeout 1200 \
      -- -WHCharShot=0 $PAWN -WHSuitPersist -WHSuitKeyScript=1.5,2.7,3.9,5.1,6.3,7.5,8.7 -WHExposure=$EV < /dev/null | tail -4
  check "$OUT/pawn3" pawn
  find "$CFG" -name GameUserSettings.ini -exec cp {} "$OUT/pawn3/GameUserSettings_after_pawn.ini" \; 2>/dev/null
  grep -E "WH_SUIT|WH_SETTINGS|WH_TRAV hero|WH_EXPOSURE" "$OUT/pawn3/pawn.log" > "$OUT/pawn3/suit_log.txt" 2>/dev/null
  F=$(ls "$OUT/pawn3/pawn_frames"/MovieFrame00030.png 2>/dev/null | head -1)
  [ -n "$F" ] && log "floor luma of the pawn movie, frame 30: $(python3 "$CAL" luma "$F")"
fi

if has persist; then
  log "persist relaunch (960x540 still at 3 s)"
  Scripts/run_game.sh "$OUT/persist3" -map $MAPP -res 960x540 -shots 3 -quit 4.5 -name persist -exec "r.MotionBlurQuality 0" -timeout 900 -- -WHCharShot=0 $PAWN -WHSuitPersist -WHExposure=$EV < /dev/null | tail -3
  check "$OUT/persist3" persist
  grep -E "WH_SUIT|WH_SETTINGS" "$OUT/persist3/persist.log" > "$OUT/persist3/suit_log.txt" 2>/dev/null
fi

if has menu; then
  log "settings menu (1080p still at 4 s)"
  Scripts/run_game.sh "$OUT/menu3" -map $MAPP -res 1920x1080 -shots 4 -quit 5.5 -name menu -exec "r.MotionBlurQuality 0" -timeout 900 -- -WHCharShot=0 $PAWN -WHSuitPersist -WHShowSettings -WHExposure=$EV < /dev/null | tail -3
  check "$OUT/menu3" menu
  grep -E "WH_SUIT|WH_SETTINGS" "$OUT/menu3/menu.log" > "$OUT/menu3/suit_log.txt" 2>/dev/null
fi

if has orbit; then
  log "orbit movie (1080p -movie)"
  FIRST=$(python3 -c "import json;print(json.load(open('$SJ'))['first_orbit'])")
  Scripts/run_game.sh "$OUT/orbit3" -map $MAP -res 1920x1080 -quit 12.6 -name orbit -movie -exec "r.MotionBlurQuality 0,r.ScreenPercentage 100" -timeout 1200 -- -WHCharShot=$FIRST -WHExposure=$EV < /dev/null | tail -3
  check "$OUT/orbit3" orbit
  grep -E "WH_SUIT" "$OUT/orbit3/orbit.log" > "$OUT/orbit3/suit_log.txt" 2>/dev/null
fi
log "final2 done (hold used $(( $(date +%s) - T0 )) s), EV $EV, crashes $CRASHES"
