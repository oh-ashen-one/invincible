#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 17 post-processing (= post_r16.sh with round-17 paths, the round-16 PNG originals as the baseline, and the round-17 instruments at the end: lineup diff, cut checks, line steps, both-side cord jogs, seam through the chin)
# Round 16 post-processing (CPU only) after chain_r16.sh (= post_r15.sh with round-17 paths, every still committed at 4K, the round-15 PNG originals as the baseline, plus the round-17 instruments at the end): fills docs/night1/characters/round-17 (stills, swatch sheet, clips, evidence) and measures:
# relief / sash / jog (relief_check_r12.py), CH1 (loco_r12.py ch1), CH6 / CH7 / CH10 on the stage-hero clips (eval/video_checks.py + loco_r12.py),
# the pawn's step rate and start pop (loco_r12.py, cross-piece numbers for P3), swap latency, OCR, IP guard, seams, tangent check.
#   bash tools/ue_char/suits/post_r17.sh <chainA out> <chainB out>
# New in round 14: the finished-sculpt pass test (head_check_r14.py: G1 bridge recess, G2 brow overhang, G3 cheek luma lines + every round-13 gate H1 - H6) on the head / headfront / head34 / headside 4K stills,
# the mesh profile (head_profile_r14.py), the image-quality items of the round-13 critic (iq_check_r14.py) and the trapezius fold check (hero_weights_r14.py --check).
set -u
WT="$(cd "$(dirname "$0")/../../.." && pwd)"
export P2_SCRATCH="${P2_SCRATCH:-/Users/midir/sm2-n1/_scratch/characters}"
A="${1:?chainA dir}"; B="${2:-$1}"
R="$WT/docs/night1/characters/round-17"; E="$R/evidence"; M="$E/measures"
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
    *) ffmpeg -loglevel error -y -i "$f" -q:v 2 "$R/stills/$b.jpg";;          # round 16: every view at 4K (the back stills too)
  esac
done
mkdir -p "$P2_SCRATCH/r17/stills_jpg"; for f in "$S"/skin_*_4k.png; do ffmpeg -loglevel error -y -i "$f" -q:v 2 "$P2_SCRATCH/r17/stills_jpg/$(basename "${f%.png}").jpg"; done
python3 tools/ue_char/suits/swatch_sheet.py "$P2_SCRATCH/r17/stills_jpg" "$R/SWATCH_SHEET.jpg"
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
for f in "$B"/lineup34/lineup34_*_t*.png; do [ -f "$f" ] && ffmpeg -loglevel error -y -i "$f" -q:v 2 "$R/enemy_lineup_34_4k.jpg" && break; done
ls -la "$R"/*.mp4 "$R"/*.jpg 2>/dev/null | awk '{print $5, $9}'
# --- evidence copies
cp "$A/pawn/suit_log.txt" "$E/pawn_suit_log.txt" 2>/dev/null; cp "$A/pawn/GameUserSettings_after_pawn.ini" "$E/" 2>/dev/null
cp "$S/suit_log.txt" "$E/stills_suit_log.txt" 2>/dev/null; cp "$S/skins_perf.json" "$E/stills_perf.json" 2>/dev/null; cp "$B/lineup/lineup_perf.json" "$E/lineup_perf.json" 2>/dev/null; cp "$B/lineup34/lineup34_perf.json" "$E/lineup34_perf.json" 2>/dev/null
cat "$A/chain.log" "$B/chain.log" 2>/dev/null | sort -u > "$E/chain.log"; cat "$A"/gpu_util_before_*.txt "$B"/gpu_util_before_*.txt > "$E/gpu_util_before_runs.txt" 2>/dev/null
cp "$WT/unreal/WebHomage/Saved/Logs/characters_build.log" "$E/characters_build.log" 2>/dev/null
[ -d "$A/pawn/pawn_frames" ] && python3 tools/ue_char/suits/analyze_swap.py "$A/pawn/pawn_frames" "$E/pawn_suit_log.txt" "$E/swap_latency.json" | tail -2
# --- the critic's three numbers on every 4K chest still (lossless PNG originals) + the round-11 baseline of the same views
for s in tessera verdant plum cinder glacier ash saffron sage; do
  a=$(acc $s)
  python3 $T relief "$S/skin_${s}_chest_4k.png" --overlay "$M/relief_${s}.jpg" > "$M/relief_${s}.json"
  python3 $T sash "$S/skin_${s}_chest_4k.png" --accent "$a" --overlay "$M/sash_${s}.jpg" --probe 1412 1240 > "$M/sash_${s}.json"
  python3 $T relief "docs/night1/characters/round-16/stills/skin_${s}_chest_4k.jpg" > "$M/r15_relief_${s}.json"
  python3 $T sash "docs/night1/characters/round-16/stills/skin_${s}_chest_4k.jpg" --accent "$a" --probe 1412 1240 > "$M/r15_sash_${s}.json"
done
python3 $T jog "$S/skin_verdant_chest_4k.png" --accent "$(acc verdant)" --roi 1290 1500 1640 1850 > "$M/jog_verdant.json"
python3 $T jog "docs/night1/characters/round-16/stills/skin_verdant_chest_4k.jpg" --accent "$(acc verdant)" --roi 1290 1500 1640 1850 > "$M/r15_jog_verdant.json"
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
python3 tools/ue_char/suits/ip_guard.py ocr "$E/ocr_stills.json" "$P2_SCRATCH"/r17/stills_jpg/skin_*_4k.jpg | tail -2
python3 tools/ue_char/suits/test_regression.py > "$E/regression.txt"; tail -1 "$E/regression.txt"
python3 tools/ue_char/suit8/hero_weights_r12.py --check "$E/fold_check.json" > /dev/null
# --- round 14: the finished-sculpt pass test on the lossless 4K PNG originals (baseline for H3 = the round-12 head stills, same framing as head34)
R12S=${R12S:-/Users/midir/sm2-n1/_scratch/characters/r12/chain3/stills}
mkdir -p "$M/head_overlays"
python3 tools/ue_char/suits/head_check_r14.py all "$S" "$R12S" "$E/head_check.json" "$M/head_overlays" > "$E/head_check.txt" 2>&1; tail -9 "$E/head_check.txt"
python3 tools/ue_char/suits/head_profile_r14.py "$P2_SCRATCH/ueimport/SK_Hero.glb" --brief --h6 --png "$M/head_profile_mesh.png" --relief "$M/head_relief_cpu.png" --json "$E/head_profile_mesh.json" > /dev/null
# --- round 15: the P2 lines of the critic r14 (rim depth behind the brow, Ash accent pipe on the sash end, Verdant armpit piping, the brow trim stretch), the round-14 PNG originals as the baseline
mkdir -p "$M/iq" "$M/rim_overlays"
R14S=${R16S:-/Users/midir/sm2-n1/_scratch/characters/r16/chain3/run/stills}      # (variable name kept: the BASELINE is round 16 now)
python3 tools/ue_char/suits/rim_depth_r15.py all "$S" "$E/rim_depth.json" "$M/rim_overlays" > "$E/rim_depth.txt" 2>&1; cat "$E/rim_depth.txt"
python3 tools/ue_char/suits/rim_depth_r15.py all "$R14S" "$E/rim_depth_r15.json" > "$E/rim_depth_r15.txt" 2>&1
python3 tools/ue_char/suits/iq_check_r15.py "$S" "$R14S" "$M/iq" > "$E/iq_check.json" 2> "$E/iq_check.log"; tail -3 "$E/iq_check.log"
python3 tools/ue_char/suit8/hero_weights_r14.py --check "$E/trapezius_fold_check.json" > /dev/null
# net lines that end where no cord is (design level, the paint itself): r15 vs the round-14 switches, 4096 px
python3 tools/ue_char/suits/net_end_check_r15.py --n 4096 --json "$E/net_end.json" --png "$M/net_end" > "$E/net_end.txt" 2>&1; tail -1 "$E/net_end.txt"
for f in "$M"/net_end/netend_*.png; do [ -f "$f" ] && ffmpeg -loglevel error -y -i "$f" -vf scale=2048:-2 -q:v 3 "${f%.png}.jpg" && rm -f "$f"; done      # 2048 px JPEG overlays (as round 15), not 4096 PNGs
cp docs/night1/characters/round-16/evidence/net_end.json "$E/net_end_r15.json"; cp docs/night1/characters/round-16/evidence/net_end.txt "$E/net_end_r15.txt"; tail -1 "$E/net_end_r15.txt"      # (file names kept for spec_check: the baseline is round 16)
# the pawn (P3's ground blend merged): luma pops 0 - 1.5 s and the anim_weight step, r14 movie / telemetry as the baseline
[ -f "$R/swap_pawn_T_key.mp4" ] && python3 tools/ue_char/suits/pawn_check_r15.py "$R/swap_pawn_T_key.mp4" "$A/pawn/pawn_telemetry.csv" docs/night1/characters/round-16/swap_pawn_T_key.mp4 docs/night1/characters/round-16/evidence/pawn_telemetry.csv > "$E/pawn_check.json"; tail -c 300 "$E/pawn_check.json"
# --- the enemy pack: lineup exposure (wall / floor luma, r04 + r12 for reference), the fight choreography unchanged since r10
python3 - <<'PY' > "$E/lineup_exposure.json"
import json
from PIL import Image
import numpy as np
def stats(p):
    im = np.asarray(Image.open(p).convert('RGB')).astype(float); sc = im.shape[1] / 2000.0
    def patch(x0, y0, x1, y1): return [round(float(v), 1) for v in im[int(y0*sc):int(y1*sc), int(x0*sc):int(x1*sc)].reshape(-1, 3).mean(0)]
    return dict(wall=patch(560, 300, 900, 420), floor=patch(200, 720, 900, 900), brick=patch(60, 300, 400, 500))
out = {}
for k, p in (('r04', 'docs/night1/characters/round-04/captures/enemy_lineup_wide_4k.jpg'), ('r12', 'docs/night1/characters/round-12/enemy_lineup_4k.jpg'), ('r13', 'docs/night1/characters/round-13/enemy_lineup_4k.jpg'), ('r14', 'docs/night1/characters/round-14/enemy_lineup_4k.jpg'), ('r15', 'docs/night1/characters/round-15/enemy_lineup_4k.jpg'), ('r16', 'docs/night1/characters/round-16/enemy_lineup_4k.jpg'), ('r17', 'docs/night1/characters/round-17/enemy_lineup_4k.jpg')):
    try: out[k] = stats(p)
    except Exception as e: out[k] = str(e)
print(json.dumps(out, indent=1))
PY
git diff --stat 37366e0 HEAD -- tools/ue_char/fight/fight_script.json tools/ue_char/fight/choreo.py tools/ue_char/fight/make_fight_clips.py tools/ue_char/weapons > "$E/fight_unchanged_since_r10.txt"; echo "(empty above = fight script / choreography / weapons identical to the round-10 commit 37366e0)" >> "$E/fight_unchanged_since_r10.txt"
du -sh "$R"; ls -la "$R"/*.mp4 | awk '$5 > 15000000 {print "OVER 15 MB:", $9}'

R16S=${R16S:-/Users/midir/sm2-n1/_scratch/characters/r16/chain3/run/stills}
# --- round 16: the four r15 4K defects (r15 PNG originals as the baseline) and the no-new-defect crop sheets
R15S=${R16S:-/Users/midir/sm2-n1/_scratch/characters/r16/chain3/run/stills}      # (variable name kept: the BASELINE is round 16 now)
python3 tools/ue_char/suits/back_bleed_r16.py "$S" "$E/back_bleed.json" --png "$M/back_bleed" | tail -9
python3 tools/ue_char/suits/back_bleed_r16.py "$R15S" "$E/back_bleed_r15.json" --png "$M/back_bleed_r15" | tail -1
python3 tools/ue_char/suits/cord_jog_r16.py "$S" "$E/cord_jog.json" --png "$M/cord_jog" | tail -9
python3 tools/ue_char/suits/cord_jog_r16.py "$R15S" "$E/cord_jog_r15.json" --png "$M/cord_jog_r15" | tail -1
python3 tools/ue_char/suits/seam_track_r16.py "$S" "$E/seam_track.json" --png "$M/seam_track" | tail -9
python3 tools/ue_char/suits/seam_track_r16.py "$R15S" "$E/seam_track_r15.json" --png "$M/seam_track_r15" | tail -1
grep -h "WH_HEADLOCK" "$S/skins.log" > "$E/headlock_log.txt" 2>/dev/null; wc -l < "$E/headlock_log.txt"
python3 tools/ue_char/suits/crop_sheets_r16.py "$S" "$R15S" "$M/crops"

# --- round 17: the lineup against the previous CLEAN lineup (r14 / r15) at the same camera, the cut checks, the line steps, the cord jogs on both sides, the seam through the chin
D=tools/ue_char/suits
mkdir -p "$M/lineup"
for ref in 14 15 16; do
  python3 $D/lineup_diff_r17.py "$R/enemy_lineup_4k.jpg" docs/night1/characters/round-$ref/enemy_lineup_4k.jpg --json "$E/lineup_diff_vs_r$ref.json" --diff-png "$M/lineup/diff_vs_r$ref.png" > /dev/null
  python3 $D/lineup_diff_r17.py "$R/enemy_lineup_34_4k.jpg" docs/night1/characters/round-$ref/enemy_lineup_34_4k.jpg --json "$E/lineup34_diff_vs_r$ref.json" > /dev/null
done
python3 $D/lineup_diff_r17.py "$B/lineup/lineup_4k.png" docs/night1/characters/round-14/enemy_lineup_4k.jpg --json "$E/lineup_diff_png_vs_r14.json" | cut -c1-200
[ -f "$R/swap_pawn_T_key.mp4" ] && python3 $D/cut_check_r17.py "$R/swap_pawn_T_key.mp4" --at 9.933 --json "$E/cut_check_pawn.json" | cut -c1-300
python3 $D/cut_check_r17.py docs/night1/characters/round-16/swap_pawn_T_key.mp4 --at 9.933 --json "$E/cut_check_pawn_r16.json" > /dev/null
[ -f "$R/crowd_tracking.mp4" ] && python3 $D/cut_check_r17.py "$R/crowd_tracking.mp4" --at 7.483 --json "$E/cut_check_crowd.json" | cut -c1-300
python3 $D/cut_check_r17.py docs/night1/characters/round-15/crowd_tracking.mp4 --at 7.483 --json "$E/cut_check_crowd_r15.json" > /dev/null
[ -f "$R/orbit_all_suits.mp4" ] && python3 $D/cut_check_r17.py "$R/orbit_all_suits.mp4" --json "$E/cut_check_orbit.json" > /dev/null
mkdir -p "$M/line_step"
for s in tessera verdant plum cinder glacier ash saffron sage; do
  python3 $D/line_step_r17.py "$S/skin_${s}_chest_4k.png" --out "$M/line_step/ls_${s}.jpg" --json "$E/line_step_${s}.json" > /dev/null
  python3 $D/line_step_r17.py "$R16S/skin_${s}_chest_4k.png" --json "$E/line_step_r16_${s}.json" > /dev/null
done
python3 $D/cord_jog_r17.py "$S" "$E/cord_jog_r17.json" --png "$M/cord_jog17" | tail -9
python3 $D/cord_jog_r17.py "$R16S" "$E/cord_jog_r17_on_r16.json" | tail -1
python3 $D/chin_crops_r17.py "$S" "$E/seam_track.json" "$R16S" "$E/seam_track_r15.json" "$M/chin_crops.jpg"
python3 $D/lineup_crops_r17.py "$M/lineup/weapons_crops.jpg" docs/night1/characters/round-14/enemy_lineup_4k.jpg docs/night1/characters/round-16/enemy_lineup_4k.jpg "$R/enemy_lineup_4k.jpg"
# the owner aid for the Verdant re-block: r16 (brass yellow) | r17 (copper) front + chest, side by side
python3 - "$R16S" "$S" "$R/VERDANT_BEFORE_AFTER.jpg" <<'PY'
import sys, cv2, numpy as np
s16, s17, out = sys.argv[1:4]
def crop(d, v, box):
    im = cv2.imread('%s/skin_verdant_%s_4k.png' % (d, v)); h, w = im.shape[:2]
    x0, y0, x1, y1 = [int(b * s) for b, s in zip(box, (w, h, w, h))]
    c = im[y0:y1, x0:x1]; return cv2.resize(c, (int(c.shape[1] * 900 / c.shape[0]), 900), interpolation=cv2.INTER_AREA)
fr = (0.36, 0.18, 0.64, 0.82); ch = (0.12, 0.05, 0.88, 0.95)
rows = [np.hstack([crop(s16, 'front', fr), crop(s17, 'front', fr)]), np.hstack([crop(s16, 'chest', ch)[:, :820], crop(s17, 'chest', ch)[:, :820]])]
W = max(r.shape[1] for r in rows)
sheet = np.vstack([cv2.copyMakeBorder(r, 0, 6, 0, W - r.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for r in rows])
cv2.putText(sheet, 'round 16 (brass yellow)', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 3); cv2.putText(sheet, 'round 17 (copper, dark pine)', (sheet.shape[1] // 2 + 20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 3)
cv2.imwrite(out, sheet, [cv2.IMWRITE_JPEG_QUALITY, 88]); print(out, sheet.shape)
PY
python3 $D/lineup_diff_r17.py docs/night1/characters/round-16/enemy_lineup_4k.jpg docs/night1/characters/round-14/enemy_lineup_4k.jpg --json "$E/lineup_diff_r16_vs_r14.json" > /dev/null
python3 $D/lineup_diff_r17.py docs/night1/characters/round-16/enemy_lineup_34_4k.jpg docs/night1/characters/round-14/enemy_lineup_34_4k.jpg --json "$E/lineup34_diff_r16_vs_r14.json" > /dev/null
