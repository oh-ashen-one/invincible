#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 11 post-processing after chain_r11_final.sh (CPU only): copy the evidence into docs/night1/characters/round-11, build the swatch sheet, measure the swap on the pixels,
# OCR the 4K stills, write SPEC_CHECK.md.
#   STILLS=stills_a bash tools/ue_char/suits/post_r11.sh [chain4 out dir]       (STILLS = the exposure set that is committed: stills_a | stills_b | stills_c)
set -u
WT="$(cd "$(dirname "$0")/../../.." && pwd)"
export P2_SCRATCH="${P2_SCRATCH:-/Users/midir/sm2-n1/_scratch/characters}"
OUT="${1:-$P2_SCRATCH/r11/chain4}"; STILLS="${STILLS:-stills_a}"
R="$WT/docs/night1/characters/round-11"; E="$R/evidence"
mkdir -p "$R/stills" "$E"
cd "$WT"
S="$OUT/$STILLS"
# --- stills: front + chest stay 4K, back + head are committed at 1920 px (size); the swatch sheet uses the 4K originals
rm -f "$R"/stills/skin_*.jpg
for f in "$S"/skin_*_4k.jpg; do
  [ -f "$f" ] || continue
  b=$(basename "$f")
  case "$b" in
    *_front_4k.jpg|*_chest_4k.jpg) cp "$f" "$R/stills/$b";;
    *) ffmpeg -loglevel error -y -i "$f" -vf scale=1920:-2 -q:v 3 "$R/stills/${b%_4k.jpg}_1080p.jpg";;
  esac
done
python3 tools/ue_char/suits/swatch_sheet.py "$S" "$R/SWATCH_SHEET.jpg"
# --- clips (orbit trimmed to its 12 s: the director loops into the stills shots after that)
# (the pawn movie: the first 0.1 s are the director's camera settling; the orbit movie: the first 0.6 s show the first suit's 8192 px maps still streaming in, so both are trimmed)
[ -f "$OUT/pawn3/pawn.mp4" ] && ffmpeg -loglevel error -y -ss 0.1 -i "$OUT/pawn3/pawn.mp4" -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart "$R/swap_pawn_T_key.mp4"
ORB="${ORBIT_OUT:-$OUT}"      # ORBIT_OUT = a later run dir whose orbit3/ replaces the orbit of this chain
[ -f "$ORB/orbit3/orbit.mp4" ] && ffmpeg -loglevel error -y -ss 0.6 -i "$ORB/orbit3/orbit.mp4" -t 11.4 -c:v libx264 -pix_fmt yuv420p -crf 20 -movflags +faststart "$R/orbit_all_suits.mp4"
ls -la "$R"/*.mp4 | awk '{print $5, $9}'
for f in "$OUT"/persist3/persist_*.png; do [ -f "$f" ] && ffmpeg -loglevel error -y -i "$f" -q:v 3 "$R/persist_start.jpg" && break; done
for f in "$OUT"/menu3/menu_*.png; do [ -f "$f" ] && ffmpeg -loglevel error -y -i "$f" -q:v 3 "$R/settings_menu_suit_row.jpg" && break; done
# --- evidence copies
for n in pawn3 persist3 menu3; do [ -f "$OUT/$n/suit_log.txt" ] && cp "$OUT/$n/suit_log.txt" "$E/${n%3}_suit_log.txt"; done
[ -f "$ORB/orbit3/suit_log.txt" ] && cp "$ORB/orbit3/suit_log.txt" "$E/orbit_suit_log.txt"
cp "$OUT/pawn3/GameUserSettings_after_pawn.ini" "$E/" 2>/dev/null
cp "$OUT/characters_build4.log" "$E/characters_build.log" 2>/dev/null || cp "$OUT/characters_build3.log" "$E/characters_build.log" 2>/dev/null
for f in ev.txt calib.txt gpu_util_before_stills.txt gpu_wrapper.log; do cp "$OUT/$f" "$E/chain_$f" 2>/dev/null; done
cp "$OUT/final.log" "$E/chain.log" 2>/dev/null
for t in stills_a stills_b stills_c; do cp "$OUT/$t/suit_log.txt" "$E/${t}_suit_log.txt" 2>/dev/null; cp "$OUT/$t/skins_perf.json" "$E/${t}_perf.json" 2>/dev/null; done
cp "$S/skins_perf.json" "$E/stills_perf.json" 2>/dev/null; cp "$S/suit_log.txt" "$E/stills_suit_log.txt" 2>/dev/null
cp "$P2_SCRATCH/r11/ipguard_4096.json" "$E/ipguard.json" 2>/dev/null; cp "$P2_SCRATCH/r11/seams_4096.json" "$E/seams.json" 2>/dev/null; cp "$P2_SCRATCH/r11/ocr_atlas.json" "$E/ocr_atlas.json" 2>/dev/null
# --- swap latency on the pixels of the fixed-step movie (the hero is centred by the world-fixed orbit camera)
[ -d "$OUT/pawn3/pawn_frames" ] && python3 tools/ue_char/suits/analyze_swap.py "$OUT/pawn3/pawn_frames" "$E/pawn_suit_log.txt" "$E/swap_latency.json"
# --- persistence summary from the logs
{ echo "pawn run end: $(grep -h 'suit saved' "$E/pawn_suit_log.txt" 2>/dev/null | tail -1 | sed 's/^.*Display: //')";
  echo "relaunch:     $(grep -h 'start suit' "$E/persist_suit_log.txt" 2>/dev/null | tail -1 | sed 's/^.*Display: //')";
  echo "menu:         $(grep -h 'start suit' "$E/menu_suit_log.txt" 2>/dev/null | tail -1 | sed 's/^.*Display: //')";
  echo "ini:          $(grep -h -E 'HeroSuit' "$E/GameUserSettings_after_pawn.ini" 2>/dev/null | tr '\n' ' ')"; } > "$E/persist.txt"
cat "$E/persist.txt"
# --- OCR of every 4K still (4 quadrants, normal + inverted, tesseract)
python3 tools/ue_char/suits/ip_guard.py ocr "$E/ocr_stills.json" "$S"/skin_*_4k.jpg | tail -3
python3 tools/ue_char/suits/spec_check_r11.py "$R" > "$R/SPEC_CHECK.md" && echo "SPEC_CHECK.md written"
du -sh "$R"
