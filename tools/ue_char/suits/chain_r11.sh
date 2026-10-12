#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 11 (first-pass piece G, hero skins): ONE GPU-lock hold = rebuild of /Game/Characters (+ the suits and the Char_Skins map) -> 4K stills of every suit
# -> the playable-pawn swap movie (real T key presses) -> a persistence re-launch -> the orbit movie that cycles the suits.
#
#   /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label characters -- bash tools/ue_char/suits/chain_r11.sh <out_dir>
#
# Every Unreal launch below is nested inside that hold (the lock passes nested wrappers through), one engine at a time, SIGTERM-only stops (run_game.sh).
# Steps skip themselves when the hold is nearly used up (CHAIN_LIMIT_S, default 2100 s of the 2400 s max hold); STEPS="build stills pawn persist orbit" selects.
set -u
WT="$(cd "$(dirname "$0")/../../.." && pwd)"
export P2_SCRATCH="${P2_SCRATCH:-/Users/midir/sm2-n1/_scratch/characters}"
OUT="${1:?out dir}"; mkdir -p "$OUT"
STEPS="${STEPS:-build stills pawn persist menu orbit}"
T0=$(date +%s); LIMIT="${CHAIN_LIMIT_S:-2100}"
left() { echo $(( LIMIT - ($(date +%s) - T0) )); }
log() { echo "[chain $(date +%H:%M:%S) +$(( $(date +%s) - T0 ))s] $*" | tee -a "$OUT/chain.log"; }
has() { case " $STEPS " in *" $1 "*) return 0;; esac; return 1; }
cd "$WT/unreal/WebHomage"
MAP=/Game/Tests/Characters/Char_Skins; MAPP=/Game/Tests/Characters/Char_SkinsPlay
SJ="$P2_SCRATCH/skins_shots.json"
PAWN="-WHHeroMesh=/Game/Characters/Hero/SK_Hero -WHHeroLens=none -WHHeroClips=/Game/Characters/Hero/Anims -WHHeroClipPrefix=A_Hero_ -WHTravScript=$WT/tools/ue_char/suits/pawn_run.json"
CFG="$WT/unreal/WebHomage/Saved/Config"   # GameUserSettings.ini lands in Saved/Config/<MacEditor|Mac>/ of THIS worktree

if has build; then
  log "build: clean,tex,mat,mesh,citizens,rename,fightclips,abp,skins,skinsmap"
  BUILD_STDOUT="$OUT/build.stdout" bash "$WT/tools/ue_char/fight/build_fight.sh" clean,tex,mat,mesh,citizens,rename,fightclips,abp,skins,skinsmap 2>&1 | tee "$OUT/build_summary.txt" | tail -60
  cp "$WT/unreal/WebHomage/Saved/Logs/characters_build.log" "$OUT/characters_build.log" 2>/dev/null
  [ -f "$SJ" ] || { log "no skins_shots.json: build failed"; exit 3; }
fi

# (the pawn run starts in suit 2 through the real console command `wh.Suit 2`, then 7 T presses cycle 3 4 5 6 7 0 1: it ends in suit 1 = verdant, saved to GameUserSettings.ini)
# stage times of the 32 still shots: shot k starts at 3 k (+1 s warm-up on the first), the still is taken 2.2 s into it
if has stills && [ "$(left)" -gt 420 ] && [ -f "$SJ" ]; then
  TIMES=$(python3 - <<EOF
import json
d = json.load(open("$SJ"))
t0 = 0.0; out = []
for k in range(d['stills']):
    dur = d['shot_s'] + (1.0 if k == 0 else 0.0)
    out.append('%.1f' % (t0 + 2.2)); t0 += dur
print(','.join(out), end='')
EOF
)
  QUIT=$(python3 -c "print(int(float('${TIMES##*,}') + 6))")   # the stage clock trails the automation clock by up to ~2.4 s in a real-time run
  log "stills: 4K, internal 3840x2160 (r.ScreenPercentage 100), stage shots at $TIMES, quit $QUIT"
  ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' > "$OUT/gpu_util_before_stills.txt" || true
  Scripts/run_game.sh "$OUT/stills" -map $MAP -res 3840x2160 -exec "r.ScreenPercentage 100,r.MotionBlurQuality 0" -perf 3:$(( QUIT - 1 )) -quit $QUIT -name skins -timeout 1500 \
      -- -WHCharShot=0 -WHStageShot="$TIMES" < /dev/null | tail -12
  python3 - <<EOF
import json, glob, subprocess, os
d = json.load(open("$SJ")); views = d['views']
files = sorted(glob.glob("$OUT/stills/skins_[0-9][0-9]_t*.png"))
for f in files:
    k = int(os.path.basename(f).split('_')[1]); suit = d['suits'][k // len(views)].lower(); view = views[k % len(views)]
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', f, '-q:v', '2', "$OUT/stills/skin_%s_%s_4k.jpg" % (suit, view)])
    os.remove(f)
print(len(files), 'stills converted')
EOF
fi

if has pawn && [ "$(left)" -gt 420 ] && [ -f "$SJ" ]; then
  FIRST=0
  find "$CFG" -name GameUserSettings.ini -delete 2>/dev/null
  log "pawn: the playable hero swaps suits on injected T key presses (1080p -movie, fixed 1/60 s), pawn shot $FIRST"
  Scripts/run_game.sh "$OUT/pawn" -map $MAPP -res 1920x1080 -quit 11.5 -name pawn -movie -exec "r.MotionBlurQuality 0,wh.Suit 2" -timeout 1500 \
      -- -WHCharShot=$FIRST $PAWN -WHSuitPersist -WHSuitKeyScript=1.5,2.7,3.9,5.1,6.3,7.5,8.7 < /dev/null | tail -8
  find "$CFG" -name GameUserSettings.ini -exec cp {} "$OUT/pawn/GameUserSettings_after_pawn.ini" \; 2>/dev/null
  grep -E "WH_SUIT|WH_SETTINGS|WH_TRAV hero" "$OUT/pawn/pawn.log" > "$OUT/pawn/suit_log.txt" 2>/dev/null
fi

if has persist && [ "$(left)" -gt 300 ] && [ -f "$SJ" ]; then
  FIRST=0
  log "persist: a second launch reads the suit the pawn run left in GameUserSettings.ini (640x360, one still at 3 s)"
  Scripts/run_game.sh "$OUT/persist" -map $MAPP -res 960x540 -shots 3 -quit 4.5 -name persist -exec "r.MotionBlurQuality 0" -timeout 900 \
      -- -WHCharShot=$FIRST $PAWN -WHSuitPersist < /dev/null | tail -6
  grep -E "WH_SUIT|WH_SETTINGS" "$OUT/persist/persist.log" > "$OUT/persist/suit_log.txt" 2>/dev/null
fi

if has menu && [ "$(left)" -gt 300 ]; then
  log "menu: the settings menu with the HERO section (suit row), forced open (-WHShowSettings), 1080p still at 4 s, suit from GameUserSettings.ini"
  Scripts/run_game.sh "$OUT/menu" -map $MAPP -res 1920x1080 -shots 4 -quit 5.5 -name menu -exec "r.MotionBlurQuality 0" -timeout 900 \
      -- -WHCharShot=0 $PAWN -WHSuitPersist -WHShowSettings < /dev/null | tail -6
  grep -E "WH_SUIT|WH_SETTINGS" "$OUT/menu/menu.log" > "$OUT/menu/suit_log.txt" 2>/dev/null
fi

if has orbit && [ "$(left)" -gt 300 ] && [ -f "$SJ" ]; then
  FIRST=$(python3 -c "import json;print(json.load(open('$SJ'))['first_orbit'])")
  log "orbit: the stage hero in every suit, one orbit, a swap every 1.5 s (1080p -movie)"
  Scripts/run_game.sh "$OUT/orbit" -map $MAP -res 1920x1080 -quit 12.6 -name orbit -movie -exec "r.MotionBlurQuality 0" -timeout 1500 -- -WHCharShot=$FIRST < /dev/null | tail -6
  grep -E "WH_SUIT" "$OUT/orbit/orbit.log" > "$OUT/orbit/suit_log.txt" 2>/dev/null
fi
log "chain done (hold used $(( $(date +%s) - T0 )) s)"
