#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 11, final hold: re-import the suits (cinder was recoloured), rebuild the stage maps with a MANUAL exposure (auto exposure re-normalised every close-up: a dark suit filling the frame
# came out pastel), then THREE complete 4K still runs at exposure bias A = map default -0.3, B = +0.7, C = -1.3 (the director's stage clock ran at 0.86 x wall in a 4K run: quit 135 s),
# the playable-pawn swap movie, the persistence relaunch, the settings-menu shot and the orbit movie.
#   /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label characters -- bash tools/ue_char/suits/chain_r11_final.sh <out_dir>
set -u
WT="$(cd "$(dirname "$0")/../../.." && pwd)"
export P2_SCRATCH="${P2_SCRATCH:-/Users/midir/sm2-n1/_scratch/characters}"
OUT="${1:?out dir}"; mkdir -p "$OUT"
T0=$(date +%s); log() { echo "[final $(date +%H:%M:%S) +$(( $(date +%s) - T0 ))s] $*" | tee -a "$OUT/final.log"; }
cd "$WT/unreal/WebHomage"
MAP=/Game/Tests/Characters/Char_Skins; MAPP=/Game/Tests/Characters/Char_SkinsPlay
SJ="$P2_SCRATCH/skins_shots.json"
CFG="$WT/unreal/WebHomage/Saved/Config"
PAWN="-WHHeroMesh=/Game/Characters/Hero/SK_Hero -WHHeroLens=none -WHHeroClips=/Game/Characters/Hero/Anims -WHHeroClipPrefix=A_Hero_ -WHTravScript=$WT/tools/ue_char/suits/pawn_run.json -WHHeroFill=0,0"

log "build: skins,skinsmap"
BUILD_STDOUT="$OUT/build3.stdout" bash "$WT/tools/ue_char/fight/build_fight.sh" skins,skinsmap 2>&1 | tail -4
cp "$WT/unreal/WebHomage/Saved/Logs/characters_build.log" "$OUT/characters_build3.log" 2>/dev/null
[ -f "$SJ" ] || { log "no skins_shots.json"; exit 3; }
TIMES=$(python3 - <<PY
import json
d = json.load(open("$SJ")); t0 = 0.0; out = []
for k in range(d['stills']):
    out.append('%.1f' % (t0 + 2.2)); t0 += d['shot_s'] + (1.0 if k == 0 else 0.0)
print(','.join(out), end='')
PY
)
stills() {   # dir ev-arg
  local dir="$1" ev="$2"
  log "stills $dir ($ev): 4K, internal 3840x2160"
  Scripts/run_game.sh "$OUT/$dir" -map $MAP -res 3840x2160 -exec "r.ScreenPercentage 100,r.MotionBlurQuality 0" -perf 3:130 -quit 135 -name skins -timeout 1200 \
      -- -WHCharShot=0 -WHStageShot="$TIMES" $ev < /dev/null | tail -4
  python3 - <<PY
import json, glob, subprocess, os
d = json.load(open("$SJ")); views = d['views']
files = sorted(glob.glob("$OUT/$dir/skins_[0-9][0-9]_t*.png"))
for f in files:
    k = int(os.path.basename(f).split('_')[1]); suit = d['suits'][k // len(views)].lower(); view = views[k % len(views)]
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', f, '-q:v', '2', "$OUT/$dir/skin_%s_%s_4k.jpg" % (suit, view)]); os.remove(f)
print("$dir", len(files), 'stills')
PY
  grep -E "WH_SUIT|WH_STAGE_SHOT|WH_EXPOSURE" "$OUT/$dir/skins.log" > "$OUT/$dir/suit_log.txt" 2>/dev/null
}
stills stills_a ""
stills stills_b "-WHExposure=0.7"
stills stills_c "-WHExposure=-1.3"

find "$CFG" -name GameUserSettings.ini -delete 2>/dev/null
log "pawn swap movie"
Scripts/run_game.sh "$OUT/pawn3" -map $MAPP -res 1920x1080 -quit 11.5 -name pawn -movie -exec "r.MotionBlurQuality 0,wh.Suit 2" -timeout 1200 \
    -- -WHCharShot=0 $PAWN -WHSuitPersist -WHSuitKeyScript=1.5,2.7,3.9,5.1,6.3,7.5,8.7 < /dev/null | tail -4
find "$CFG" -name GameUserSettings.ini -exec cp {} "$OUT/pawn3/GameUserSettings_after_pawn.ini" \; 2>/dev/null
grep -E "WH_SUIT|WH_SETTINGS|WH_TRAV hero" "$OUT/pawn3/pawn.log" > "$OUT/pawn3/suit_log.txt" 2>/dev/null
log "persist relaunch"
Scripts/run_game.sh "$OUT/persist3" -map $MAPP -res 960x540 -shots 3 -quit 4.5 -name persist -exec "r.MotionBlurQuality 0" -timeout 900 -- -WHCharShot=0 $PAWN -WHSuitPersist < /dev/null | tail -3
grep -E "WH_SUIT|WH_SETTINGS" "$OUT/persist3/persist.log" > "$OUT/persist3/suit_log.txt" 2>/dev/null
log "settings menu"
Scripts/run_game.sh "$OUT/menu3" -map $MAPP -res 1920x1080 -shots 4 -quit 5.5 -name menu -exec "r.MotionBlurQuality 0" -timeout 900 -- -WHCharShot=0 $PAWN -WHSuitPersist -WHShowSettings < /dev/null | tail -3
grep -E "WH_SUIT|WH_SETTINGS" "$OUT/menu3/menu.log" > "$OUT/menu3/suit_log.txt" 2>/dev/null
log "orbit movie"
FIRST=$(python3 -c "import json;print(json.load(open('$SJ'))['first_orbit'])")
Scripts/run_game.sh "$OUT/orbit3" -map $MAP -res 1920x1080 -quit 12.6 -name orbit -movie -exec "r.MotionBlurQuality 0" -timeout 1200 -- -WHCharShot=$FIRST < /dev/null | tail -3
grep -E "WH_SUIT" "$OUT/orbit3/orbit.log" > "$OUT/orbit3/suit_log.txt" 2>/dev/null
log "final done (hold used $(( $(date +%s) - T0 )) s)"
