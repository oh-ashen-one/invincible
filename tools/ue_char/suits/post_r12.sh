#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 12 post-processing (CPU only) after chain_r12.sh: fills docs/night1/characters/round-12 (stills, swatch sheet, clips, evidence) and measures:
# relief / sash / jog (relief_check_r12.py), CH1 (loco_r12.py ch1), CH6 / CH7 / CH10 on the stage-hero clips (eval/video_checks.py + loco_r12.py),
# the pawn's step rate and start pop (loco_r12.py, cross-piece numbers for P3), swap latency, OCR, IP guard, seams, tangent check.
#   bash tools/ue_char/suits/post_r12.sh <chainA out> <chainB out>
set -u
WT="$(cd "$(dirname "$0")/../../.." && pwd)"
export P2_SCRATCH="${P2_SCRATCH:-/Users/midir/sm2-n1/_scratch/characters}"
A="${1:?chainA dir}"; B="${2:-$1}"
R="$WT/docs/night1/characters/round-12"; E="$R/evidence"; M="$E/measures"
mkdir -p "$R/stills" "$E" "$M"
cd "$WT"
T=tools/ue_char/suits/relief_check_r12.py
acc() { python3 -c "import json;d=json.load(open('tools/ue_char/suits/suits.json'));e=next(x for x in d['suits'] if x['id']=='$1');print(e.get('style',{}).get('palette',{}).get('accent','#e0780c'))"; }
# --- stills: front + chest 4K jpg (q2), back + head 1920 px; the measures run on the lossless PNG originals
S="$A/stills"
rm -f "$R"/stills/skin_*.jpg
for f in "$S"/skin_*_4k.png; do
  [ -f "$f" ] || continue
  b=$(basename "${f%.png}")
  case "$b" in
    *_front_4k|*_chest_4k) ffmpeg -loglevel error -y -i "$f" -q:v 2 "$R/stills/$b.jpg";;
    *) ffmpeg -loglevel error -y -i "$f" -vf scale=1920:-2 -q:v 3 "$R/stills/${b%_4k}_1080p.jpg";;
  esac
done
mkdir -p "$P2_SCRATCH/r12/stills_jpg"; for f in "$S"/skin_*_4k.png; do ffmpeg -loglevel error -y -i "$f" -q:v 2 "$P2_SCRATCH/r12/stills_jpg/$(basename "${f%.png}").jpg"; done
python3 tools/ue_char/suits/swatch_sheet.py "$P2_SCRATCH/r12/stills_jpg" "$R/SWATCH_SHEET.jpg"
# --- clips
enc() { ffmpeg -loglevel error -y -ss "$3" -i "$1" ${4:+-t $4} -c:v libx264 -pix_fmt yuv420p -crf "${5:-20}" -movflags +faststart "$2"; }
frames2mp4() { ffmpeg -loglevel error -y -framerate 60 -start_number "$(python3 -c "print(int(round($3*60)))")" -i "$1/MovieFrame%05d.png" -frames:v "$(python3 -c "print(int(round($4*60)))")" -c:v libx264 -pix_fmt yuv420p -crf "${5:-20}" -movflags +faststart "$2"; }
[ -f "$A/pawn/pawn.mp4" ] && enc "$A/pawn/pawn.mp4" "$R/swap_pawn_T_key.mp4" 0.1 "" 18
[ -f "$A/orbit/orbit.mp4" ] && enc "$A/orbit/orbit.mp4" "$R/orbit_all_suits.mp4" 0.6 11.4 20
D=0.05
[ -d "$B/hero/hero_frames" ] && { frames2mp4 "$B/hero/hero_frames" "$R/hero_run_side.mp4" 0.65 5.4; frames2mp4 "$B/hero/hero_frames" "$R/hero_run_34.mp4" 6.05 5; frames2mp4 "$B/hero/hero_frames" "$R/hero_run_leap_side.mp4" 11.05 6.5; }
[ -d "$B/chase/chase_frames" ] && { frames2mp4 "$B/chase/chase_frames" "$R/hero_run_chase.mp4" 0.65 5.4; frames2mp4 "$B/chase/chase_frames" "$R/hero_run_toward.mp4" 6.05 6; }
[ -d "$B/fight/fight_frames" ] && frames2mp4 "$B/fight/fight_frames" "$R/street_fight_wide.mp4" 0.65 8
[ -d "$B/crowd/crowd_frames" ] && frames2mp4 "$B/crowd/crowd_frames" "$R/crowd_tracking.mp4" 0.55 8
for f in "$B"/lineup/lineup_*_t*.png; do [ -f "$f" ] && ffmpeg -loglevel error -y -i "$f" -q:v 2 "$R/enemy_lineup_4k.jpg" && break; done
ls -la "$R"/*.mp4 "$R"/*.jpg 2>/dev/null | awk '{print $5, $9}'
# --- evidence copies
cp "$A/pawn/suit_log.txt" "$E/pawn_suit_log.txt" 2>/dev/null; cp "$A/pawn/GameUserSettings_after_pawn.ini" "$E/" 2>/dev/null
cp "$S/suit_log.txt" "$E/stills_suit_log.txt" 2>/dev/null; cp "$S/skins_perf.json" "$E/stills_perf.json" 2>/dev/null; cp "$B/lineup/lineup_perf.json" "$E/lineup_perf.json" 2>/dev/null
cat "$A/chain.log" "$B/chain.log" 2>/dev/null | sort -u > "$E/chain.log"; cat "$A"/gpu_util_before_*.txt "$B"/gpu_util_before_*.txt > "$E/gpu_util_before_runs.txt" 2>/dev/null
cp "$WT/unreal/WebHomage/Saved/Logs/characters_build.log" "$E/characters_build.log" 2>/dev/null
[ -d "$A/pawn/pawn_frames" ] && python3 tools/ue_char/suits/analyze_swap.py "$A/pawn/pawn_frames" "$E/pawn_suit_log.txt" "$E/swap_latency.json" | tail -2
# --- the critic's three numbers on every 4K chest still (lossless PNG originals) + the round-11 baseline of the same views
for s in tessera verdant plum cinder glacier ash saffron sage; do
  a=$(acc $s)
  python3 $T relief "$S/skin_${s}_chest_4k.png" --overlay "$M/relief_${s}.jpg" > "$M/relief_${s}.json"
  python3 $T sash "$S/skin_${s}_chest_4k.png" --accent "$a" --overlay "$M/sash_${s}.jpg" --probe 1412 1240 > "$M/sash_${s}.json"
  python3 $T relief "docs/night1/characters/round-11/stills/skin_${s}_chest_4k.jpg" > "$M/r11_relief_${s}.json"
  python3 $T sash "docs/night1/characters/round-11/stills/skin_${s}_chest_4k.jpg" --accent "$a" --probe 1412 1240 > "$M/r11_sash_${s}.json"
done
python3 $T jog "$S/skin_verdant_chest_4k.png" --accent "$(acc verdant)" --roi 1290 1500 1640 1850 > "$M/jog_verdant.json"
python3 $T jog "docs/night1/characters/round-11/stills/skin_verdant_chest_4k.jpg" --accent "$(acc verdant)" --roi 1290 1500 1640 1850 > "$M/r11_jog_verdant.json"
# --- CH1 on the front stills, CH6 / CH7 / CH10 on the stage-hero clips, the pawn's cadence and start pop (P3 numbers)
python3 tools/ue_char/suits/loco_r12.py ch1 "$S"/skin_*_front_4k.png > "$M/ch1_front.json"
[ -f "$R/hero_run_chase.mp4" ] && { python3 tools/ue_char/eval/video_checks.py head_bob "$R/hero_run_chase.mp4" 0.3 5.3 > "$M/ch6_chase_headbob.json"; python3 tools/ue_char/suits/loco_r12.py bob "$R/hero_run_chase.mp4" 0.3 5.3 > "$M/ch6_chase_bob.json"; python3 tools/ue_char/eval/video_checks.py hero_run "$R/hero_run_chase.mp4" 0.3 5.3 > "$M/ch2_ch7_chase.json"; }
[ -f "$R/hero_run_side.mp4" ] && { python3 tools/ue_char/eval/video_checks.py hero_run "$R/hero_run_side.mp4" 0.3 5.3 > "$M/ch6_ch7_side.json"; python3 tools/ue_char/eval/video_checks.py head_bob "$R/hero_run_side.mp4" 0.3 5.3 > "$M/ch6_side_headbob.json"; }
# the round-08 clips through the same instruments (same windows): the A/B of the stage-hero animation
R8C=docs/night1/characters/round-08/captures
python3 tools/ue_char/eval/video_checks.py head_bob "$R8C/hero_run_side.mp4" 0.3 5.3 > "$M/r8_ch6_side_headbob.json"; python3 tools/ue_char/eval/video_checks.py hero_run "$R8C/hero_run_side.mp4" 0.3 5.3 > "$M/r8_ch6_ch7_side.json"
python3 tools/ue_char/eval/video_checks.py hero_run "$R8C/hero_run_chase.mp4" 0.3 5.3 > "$M/r8_ch2_ch7_chase.json"
[ -f "$R/swap_pawn_T_key.mp4" ] && { python3 tools/ue_char/suits/loco_r12.py bob "$R/swap_pawn_T_key.mp4" 2 9.5 > "$M/pawn_cadence.json"; python3 tools/ue_char/suits/loco_r12.py pop "$R/swap_pawn_T_key.mp4" 0 2.5 > "$M/pawn_start_pop.json"; }
[ -f "$A/pawn/pawn_telemetry.csv" ] && { cp "$A/pawn/pawn_telemetry.csv" "$E/pawn_telemetry.csv"; python3 tools/ue_char/suits/loco_r12.py tpop "$A/pawn/pawn_telemetry.csv" 0.5 2.0 > "$M/pawn_start_telemetry.json"; }
# --- CPU checks of the maps (IP guard palette, seams, per-island tangent basis), OCR of the 4K stills, regression
python3 tools/ue_char/suits/ip_guard.py palette art/night1/characters/hero/suits "$E/ipguard.json" | tail -3
python3 tools/ue_char/eval/suit_seams.py art/night1/characters/hero/suits "$E/seams.json" | tail -2
python3 tools/ue_char/suits/ip_guard.py ocr "$E/ocr_stills.json" "$P2_SCRATCH"/r12/stills_jpg/skin_*_4k.jpg | tail -2
python3 tools/ue_char/suits/test_regression.py > "$E/regression.txt"; tail -1 "$E/regression.txt"
python3 tools/ue_char/suit8/hero_weights_r12.py --check "$E/fold_check.json" > /dev/null
du -sh "$R"; ls -la "$R"/*.mp4 | awk '$5 > 15000000 {print "OVER 15 MB:", $9}'
