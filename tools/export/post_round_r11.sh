#!/bin/zsh
# (r11) after the final holds of r11_plan.sh (plan dirs <hold>/f1080 and <hold>/f4k): merge the raw frames, JPGs + perf + README skeleton, settle check, CITY-SPEC check (incl. YOLO + IP denylist), the S4 far-band report,
# the r09 shade tests, native-4K OCR of the denylist, builder crops.   usage: post_round_r11.sh <scratch_dir_with_hold_subdirs> <NN>      e.g. post_round_r11.sh /Users/midir/sm2-n1/_scratch/city/r11 11
set -u
HERE=${0:A:h}; WT=${HERE:h:h}; cd $WT
SRC=$1; NN=$2; R=docs/night1/city/round-$NN; RAW=$SRC/final/raw
mkdir -p $RAW $R/builder_checks
for d in $SRC/h*/f1080 $SRC/h*/f4k; do [ -d $d ] && cp -f $d/*.png $d/*.json $d/*.log $RAW/ 2>/dev/null; done
python3 tools/export/settle_check.py $RAW --json $R/settle_check.json | tee $R/settle_check.txt
python3 tools/export/assemble_round.py $RAW $R $NN
CITY_YOLO_ANN=$R/builder_checks/yolo python3 tools/export/city_spec_check.py $R --res 1080 --yolo --ip --json $R/city_spec_check.json --md $R/city_spec_check.md > /dev/null 2>$R/city_spec_check.err
python3 tools/export/s4_far_check.py $R/S4_perch_skyline_1920x1080.jpg --json $R/s4_far_check.json | tee $R/s4_far_check.txt
python3 tools/export/s4_mask.py $R/S4_perch_skyline_1920x1080.jpg $R/builder_checks/s4_mask_1080p.png
[ -f $R/S4_perch_skyline_3840x2160.jpg ] && python3 tools/export/s4_far_check.py $R/S4_perch_skyline_3840x2160.jpg | tee $R/s4_far_check_4k.txt
python3 tools/export/box_stats.py $R/S8_aerial_midtown_1920x1080.jpg 1270 0 1640 300 | tee $R/s8_glass_box.txt
python3 tools/export/shade_check.py $R --json $R/shade_check.json > $R/shade_check.md 2>&1
python3 tools/export/city_spec_check.py $R --res 1080 --overlay $R/builder_checks/regions > /dev/null 2>&1
[ -f $R/S3_rooftop_watertower_3840x2160.jpg ] && python3 tools/export/ip_ocr_check.py $R /Users/midir/sm2-n1/_scratch/city/tex > $R/ip_ocr_check.txt 2>&1
python3 tools/export/builder_crops.py $R
echo "post_round_r11 done: $R"
