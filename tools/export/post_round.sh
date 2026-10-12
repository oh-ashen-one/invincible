#!/bin/zsh
# (r10) after capture_round.sh: JPGs + perf + README skeleton, CITY-SPEC check (C1 / C2, C4 / C6 YOLO, C11-C15, T1 / T2, critic boxes), the S4 far-band report, the r09 shade tests.
# usage: tools/export/post_round.sh <raw_dir_with_raw/> <NN>      e.g. post_round.sh /Users/midir/sm2-n1/_scratch/city/r10/h2/final 10
set -u
HERE=${0:A:h}; WT=${HERE:h:h}; cd $WT
RAW=$1; NN=$2; R=docs/night1/city/round-$NN
python3 tools/export/assemble_round.py $RAW/raw $R $NN
CITY_YOLO_ANN=$R/builder_checks/yolo python3 tools/export/city_spec_check.py $R --res 1080 --yolo --ip --json $R/city_spec_check.json --md $R/city_spec_check.md > /dev/null 2>$R/city_spec_check.err
python3 tools/export/s4_far_check.py $R/S4_perch_skyline_1920x1080.jpg --json $R/s4_far_check.json | tee $R/s4_far_check.txt
python3 tools/export/shade_check.py $R --json $R/shade_check.json > $R/shade_check.md 2>&1
python3 tools/export/city_spec_check.py $R --res 1080 --overlay $R/builder_checks/regions > /dev/null 2>&1
echo "post_round done: $R"
