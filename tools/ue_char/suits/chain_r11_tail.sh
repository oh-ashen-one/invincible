#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 11: re-take of the LAST still shots (saffron chest / head, all four sage views). The first stills run (chain_r11.sh) quit at automation time 102 s while the director's
# stage clock was only at ~80 s (the game clock ran at 0.86 x wall in that 4K run), so shots 26 - 31 were never reached.  This run starts the director at shot 24 (the first saffron shot,
# which sets the suit) and takes shots 26 - 31 at their stage times (1 + 3 k + 2.2 s).
#   /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label characters -- bash tools/ue_char/suits/chain_r11_tail.sh <out_dir>
set -u
WT="$(cd "$(dirname "$0")/../../.." && pwd)"
export P2_SCRATCH="${P2_SCRATCH:-/Users/midir/sm2-n1/_scratch/characters}"
OUT="${1:?out dir}"; mkdir -p "$OUT/stills_tail"
cd "$WT/unreal/WebHomage"
SJ="$P2_SCRATCH/skins_shots.json"
FROM=24; TIMES="81.2,84.2,87.2,90.2,93.2,96.2"
# round-11 fix list from the first chain: (1) the pawn shots now ORBIT with aim 0 (the SIDE shot lagged the runner and aimed 0.95 m too high), (2) the pawn's own hero fill light (5000 cd, tuned for the city)
# blew the hero out in this bare map: -WHHeroFill=0,0, (3) the stills quit before shots 26 - 31.
echo "[tail $(date +%H:%M:%S)] rebuild skinsmap"
BUILD_STDOUT="$OUT/build2.stdout" bash "$WT/tools/ue_char/fight/build_fight.sh" skinsmap 2>&1 | tail -5
echo "[tail $(date +%H:%M:%S)] stills tail: director from shot $FROM, stage shots $TIMES"
Scripts/run_game.sh "$OUT/stills_tail" -map /Game/Tests/Characters/Char_Skins -res 3840x2160 -exec "r.ScreenPercentage 100,r.MotionBlurQuality 0" -perf 3:48 -quit 50 -name skins -timeout 1200 \
    -- -WHCharShot=$FROM -WHStageShot="$TIMES" < /dev/null | tail -8
python3 - <<PY
import json, glob, subprocess, os
d = json.load(open("$SJ")); views = d['views']
for f in sorted(glob.glob("$OUT/stills_tail/skins_[0-9][0-9]_t*.png")):
    nn = int(os.path.basename(f).split('_')[1]); k = 26 + nn
    suit = d['suits'][k // len(views)].lower(); view = views[k % len(views)]
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', f, '-q:v', '2', "$OUT/stills_tail/skin_%s_%s_4k.jpg" % (suit, view)]); os.remove(f)
    print('tail still', k, suit, view)
PY
PAWN="-WHHeroMesh=/Game/Characters/Hero/SK_Hero -WHHeroLens=none -WHHeroClips=/Game/Characters/Hero/Anims -WHHeroClipPrefix=A_Hero_ -WHTravScript=$WT/tools/ue_char/suits/pawn_run.json -WHHeroFill=0,0"
CFG="$WT/unreal/WebHomage/Saved/Config"
MAPP=/Game/Tests/Characters/Char_SkinsPlay
find "$CFG" -name GameUserSettings.ini -delete 2>/dev/null
echo "[tail $(date +%H:%M:%S)] pawn swap movie"
Scripts/run_game.sh "$OUT/pawn2" -map $MAPP -res 1920x1080 -quit 11.5 -name pawn -movie -exec "r.MotionBlurQuality 0,wh.Suit 2" -timeout 1200 \
    -- -WHCharShot=0 $PAWN -WHSuitPersist -WHSuitKeyScript=1.5,2.7,3.9,5.1,6.3,7.5,8.7 < /dev/null | tail -6
find "$CFG" -name GameUserSettings.ini -exec cp {} "$OUT/pawn2/GameUserSettings_after_pawn.ini" \; 2>/dev/null
grep -E "WH_SUIT|WH_SETTINGS|WH_TRAV hero" "$OUT/pawn2/pawn.log" > "$OUT/pawn2/suit_log.txt" 2>/dev/null
echo "[tail $(date +%H:%M:%S)] persist relaunch"
Scripts/run_game.sh "$OUT/persist2" -map $MAPP -res 960x540 -shots 3 -quit 4.5 -name persist -exec "r.MotionBlurQuality 0" -timeout 900 -- -WHCharShot=0 $PAWN -WHSuitPersist < /dev/null | tail -4
grep -E "WH_SUIT|WH_SETTINGS" "$OUT/persist2/persist.log" > "$OUT/persist2/suit_log.txt" 2>/dev/null
echo "[tail $(date +%H:%M:%S)] settings menu"
Scripts/run_game.sh "$OUT/menu2" -map $MAPP -res 1920x1080 -shots 4 -quit 5.5 -name menu -exec "r.MotionBlurQuality 0" -timeout 900 -- -WHCharShot=0 $PAWN -WHSuitPersist -WHShowSettings < /dev/null | tail -4
grep -E "WH_SUIT|WH_SETTINGS" "$OUT/menu2/menu.log" > "$OUT/menu2/suit_log.txt" 2>/dev/null
echo "[tail $(date +%H:%M:%S)] done"
