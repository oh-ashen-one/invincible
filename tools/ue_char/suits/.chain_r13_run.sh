#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 13 capture chain (r12 chain + the sculpted-head views head / head34 / headside, a 3/4 lineup still) (P2 hero skins): ONE gpu_slot hold per call, every engine run nested in it (one engine at a time, run_game.sh stops by SIGTERM only).
#   /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label characters -- bash tools/ue_char/suits/chain_r13.sh <out_dir>
#   STEPS (default "stills pawn orbit hero chase fight crowd lineup"; "build" first = the content build nested in the same hold):
#     stills  4K real-time stills of every suit (Char_Skins: front / back framed for CH1 at 7.85 m, chest, head), EV bias $EV
#     pawn    the playable pawn cycling the suits with real T presses (Char_SkinsPlay, 1080p -movie fixed 1/60 s)
#     orbit   the stage hero orbit across every suit (1080p -movie)
#     hero    Char_Hero shots 1-3 (run side, run 3/4, run -> leap side), 1080p60 -movie, as round 08
#     chase   Char_Hero shots 6-7 (chase behind, run toward the camera), 1080p60 -movie, as round 08
#     fight   Char_Fight shot 0 (wide), 1080p60 -movie, the round-10 scripted fight unchanged (0.6 s warm-up + 8 s)
#     crowd   Char_Crowd shot 0 (tracking), 1080p60 -movie (8 s)
#     lineup  Char_Lineup shot 5 (the 7-enemy lineup, wide), 4K real-time still at 3.0 s
# (round 13: the lineup block runs right after the stills: the two most important results first, in case the 40 min hold limit ends the chain)
# Two engine runs without WH_QUIT (crash) -> the chain stops (RULES.md).
set -u
WT="$(cd "$(dirname "$0")/../../.." && pwd)"
export P2_SCRATCH="${P2_SCRATCH:-/Users/midir/sm2-n1/_scratch/characters}"
OUT="${1:?out dir}"; mkdir -p "$OUT"
STEPS="${STEPS:-stills lineup pawn orbit hero chase fight crowd}"
EV="${EV:-10.0}"
T0=$(date +%s); log() { echo "[r13 $(date +%H:%M:%S) +$(( $(date +%s) - T0 ))s] $*" | tee -a "$OUT/chain.log"; }
has() { case " $STEPS " in *" $1 "*) return 0;; esac; return 1; }
cd "$WT/unreal/WebHomage"
MAP=/Game/Tests/Characters/Char_Skins; MAPP=/Game/Tests/Characters/Char_SkinsPlay
HERO=/Game/Tests/Characters/Char_Hero; FIGHT=/Game/Tests/Characters/Char_Fight; CROWD=/Game/Tests/Characters/Char_Crowd; LINE=/Game/Tests/Characters/Char_Lineup
SJ="$P2_SCRATCH/skins_shots.json"
CFG="$WT/unreal/WebHomage/Saved/Config"
CAL="$WT/tools/ue_char/suits/ev_calib.py"
PAWN="-WHHeroMesh=/Game/Characters/Hero/SK_Hero -WHHeroLens=none -WHHeroClips=/Game/Characters/Hero/Anims -WHHeroClipPrefix=A_Hero_ -WHTravScript=$WT/tools/ue_char/suits/pawn_run.json -WHHeroFill=0,0"
CRASHES=0
check() {
  if ! grep -q "WH_QUIT" "$1/$2.log" 2>/dev/null; then CRASHES=$((CRASHES + 1)); log "ENGINE RUN WITHOUT WH_QUIT ($1/$2): crash count $CRASHES"; fi
  if [ "$CRASHES" -ge 2 ]; then log "two engine crashes: stopping the chain and reporting (RULES.md)"; exit 9; fi
}
gpu() { ioreg -r -d 1 -w 0 -c IOAccelerator | grep -o '"Device Utilization %"=[0-9]*' > "$OUT/gpu_util_before_$1.txt" || true; }
movie() {   # name map shot quit
  local D="$OUT/$1"; rm -rf "$D"; gpu "$1"
  Scripts/run_game.sh "$D" -map "$2" -res 1920x1080 -quit "$4" -name "$1" -movie -exec "r.MotionBlurQuality 0" -timeout 1500 -- -WHCharShot="$3" < /dev/null | tail -3
  check "$D" "$1"
}
log "steps: $STEPS, EV $EV"
if [ -n "${REQUIRE_BUILD_LOG:-}" ]; then      # queued behind its own content build: refuse to render stale / broken content
  if ! grep -q "skinsmap saved True True" "$REQUIRE_BUILD_LOG" 2>/dev/null || ! grep -q "map saved /Game/Tests/Characters/Char_Fight True" "$REQUIRE_BUILD_LOG" 2>/dev/null \
     || { [ -n "${REQUIRE_NEWER:-}" ] && [ ! "$REQUIRE_BUILD_LOG" -nt "$REQUIRE_NEWER" ]; }; then
    log "content build not finished OK ($REQUIRE_BUILD_LOG): no render"; exit 4; fi
  if grep -q "M_Char_Suit weave-from-position FAILED" "$REQUIRE_BUILD_LOG"; then log "NOTE: weave-from-position failed in the build, UV weave in use"; fi
fi

if has build; then      # the content build nested in this hold (gpu_slot passes nested launches through): one queue turn for build + captures
  log "build: clean,tex,mat,mesh,citizens,rename,fightclips,abp,map,maps5,skins,skinsmap"
  BUILD_STDOUT="$OUT/build.stdout" bash "$WT/tools/ue_char/fight/build_fight.sh" clean,tex,mat,mesh,citizens,rename,fightclips,abp,map,maps5,skins,skinsmap 2>&1 | tail -3 | tee -a "$OUT/chain.log"
  cp "$WT/unreal/WebHomage/Saved/Logs/characters_build.log" "$OUT/characters_build.log" 2>/dev/null
  if ! grep -q "skinsmap saved True True" "$OUT/characters_build.log" || ! grep -q "map saved /Game/Tests/Characters/Char_Fight True" "$OUT/characters_build.log"; then log "build FAILED: no render"; exit 5; fi
  grep -E "weave from pre-skinned|weave-from-position FAILED" "$OUT/characters_build.log" | sed 's/^.*LogPython: //' | tee -a "$OUT/chain.log"
fi

if has stills; then
  TIMES=$(python3 - <<PY
import json
d = json.load(open("$SJ")); t0 = 0.0; out = []
for k in range(d['stills']):
    out.append('%.1f' % (t0 + 2.2)); t0 += d['shot_s'] + (1.0 if k == 0 else 0.0)
print(','.join(out), end='')
PY
)
  log "stills: 4K, internal 3840x2160, EV $EV"; gpu stills
  NS=$(python3 -c "import json;d=json.load(open('$SJ'));print(int(d['stills']*d['shot_s']+1+8))")      # last still at stills*shot_s + 1 - 0.8 s, 8 s of margin
  Scripts/run_game.sh "$OUT/stills" -map $MAP -res 3840x2160 -exec "r.ScreenPercentage 100,r.MotionBlurQuality 0" -perf 3:$((NS - 5)) -quit $NS -name skins -timeout 1800 \
      -- -WHCharShot=0 -WHStageShot="$TIMES" -WHExposure=$EV < /dev/null | tail -3
  check "$OUT/stills" skins
  python3 - <<PY
import json, glob, subprocess, os
d = json.load(open("$SJ")); views = d['views']
files = sorted(glob.glob("$OUT/stills/skins_[0-9][0-9]_t*.png"))
for f in files:
    k = int(os.path.basename(f).split('_')[1]); suit = d['suits'][k // len(views)].lower(); view = views[k % len(views)]
    os.replace(f, "$OUT/stills/skin_%s_%s_4k.png" % (suit, view))
print("stills", len(files))
PY
  grep -E "WH_SUIT|WH_STAGE_SHOT|WH_EXPOSURE" "$OUT/stills/skins.log" > "$OUT/stills/suit_log.txt" 2>/dev/null
fi

if has lineup; then
  log "Char_Lineup shot 5 (7 enemies) 4K still"; gpu lineup
  Scripts/run_game.sh "$OUT/lineup" -map $LINE -res 3840x2160 -exec "r.ScreenPercentage 100,r.MotionBlurQuality 0" -shots 3.0 -perf 2:5 -quit 6 -name lineup -timeout 1200 -- -WHCharShot=5 < /dev/null | tail -3
  check "$OUT/lineup" lineup
  log "Char_Lineup shot 6 (3/4) 4K still"; gpu lineup34
  Scripts/run_game.sh "$OUT/lineup34" -map $LINE -res 3840x2160 -exec "r.ScreenPercentage 100,r.MotionBlurQuality 0" -shots 3.0 -perf 2:5 -quit 6 -name lineup34 -timeout 1200 -- -WHCharShot=6 < /dev/null | tail -3
  check "$OUT/lineup34" lineup34
fi

if has pawn; then
  find "$CFG" -name GameUserSettings.ini -delete 2>/dev/null
  log "pawn swap movie"; gpu pawn
  Scripts/run_game.sh "$OUT/pawn" -map $MAPP -res 1920x1080 -quit 11.5 -name pawn -movie -exec "r.MotionBlurQuality 0,wh.Suit 2" -timeout 1500 \
      -- -WHCharShot=0 $PAWN -WHSuitPersist -WHSuitKeyScript=1.5,2.7,3.9,5.1,6.3,7.5,8.7 -WHExposure=$EV < /dev/null | tail -3
  check "$OUT/pawn" pawn
  find "$CFG" -name GameUserSettings.ini -exec cp {} "$OUT/pawn/GameUserSettings_after_pawn.ini" \; 2>/dev/null
  grep -E "WH_SUIT|WH_SETTINGS|WH_TRAV|WH_EXPOSURE" "$OUT/pawn/pawn.log" > "$OUT/pawn/suit_log.txt" 2>/dev/null
fi

if has orbit; then
  FIRST=$(python3 -c "import json;print(json.load(open('$SJ'))['first_orbit'])")
  log "orbit movie"; gpu orbit
  Scripts/run_game.sh "$OUT/orbit" -map $MAP -res 1920x1080 -quit 12.6 -name orbit -movie -exec "r.MotionBlurQuality 0,r.ScreenPercentage 100" -timeout 1500 -- -WHCharShot=$FIRST -WHExposure=$EV < /dev/null | tail -3
  check "$OUT/orbit" orbit
fi

has hero && { log "Char_Hero shots 1-3 movie"; movie hero $HERO 1 18.5; }
has chase && { log "Char_Hero shots 6-7 movie"; movie chase $HERO 6 12.5; }
has fight && { log "Char_Fight wide movie"; movie fight $FIGHT 0 9.4; }
has crowd && { log "Char_Crowd tracking movie"; movie crowd $CROWD 0 8.6; }
log "chain done (hold used $(( $(date +%s) - T0 )) s), crashes $CRASHES"

# ---- APPENDED during the hold (round 13, after the first stills run): its quit time counts from process start (~35 s of start-up), so the last 7 stills (saffron headside, sage x 6)
# were not taken.  Re-shoot them in the SAME hold, from shot 36 (saffron front = the suit switch), one engine at a time.  (Appending at the end of a running bash script is safe.)
if has stills; then
  log "re-shoot of the last 7 stills (saffron headside, sage x 6): quit time counted from process start"
  TIMES2=$(python3 - <<PY
import json
d = json.load(open("$SJ")); out = []
for k in range(36, d['stills']):
    if k == 41 or k >= 42: out.append('%.1f' % (3 * k + 3.2))
print(','.join(out), end='')
PY
)
  gpu stills2
  Scripts/run_game.sh "$OUT/stills2" -map $MAP -res 3840x2160 -exec "r.ScreenPercentage 100,r.MotionBlurQuality 0" -perf 3:100 -quit 110 -name skins -timeout 900 -- -WHCharShot=36 -WHStageShot="$TIMES2" -WHExposure=$EV < /dev/null | tail -3
  check "$OUT/stills2" skins
  python3 - <<PY
import json, glob, os
d = json.load(open("$SJ")); views = d['views']
ks = [41] + list(range(42, d['stills']))
files = sorted(glob.glob("$OUT/stills2/skins_[0-9][0-9]_t*.png"))
for i, f in enumerate(files):
    k = ks[i]; suit = d['suits'][k // len(views)].lower(); view = views[k % len(views)]
    os.replace(f, "$OUT/stills/skin_%s_%s_4k.png" % (suit, view))
print("stills2", len(files))
PY
  grep -E "WH_SUIT|WH_STAGE_SHOT|WH_EXPOSURE" "$OUT/stills2/skins.log" > "$OUT/stills2/suit_log.txt" 2>/dev/null
fi
log "re-shoot done (hold used $(( $(date +%s) - T0 )) s), crashes $CRASHES"
