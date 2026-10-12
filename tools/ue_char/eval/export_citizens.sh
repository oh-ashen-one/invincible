#!/bin/bash
# Regenerate the Unreal citizen FBX + basecolor PNG (derived, git-ignored) from the shipped crowd packs.
# Fan homage, not official Marvel/Sony/Insomniac; no affiliation.
#   tools/ue_char/eval/export_citizens.sh [NAME ...]   (default: the 4 lineup citizens)
set -e
cd "$(dirname "$0")/../../.."
P2_SCRATCH="${P2_SCRATCH:-$(pwd)/unreal/WebHomage/Saved/P2Build}"; export P2_SCRATCH   # tools/ue_char/p2paths.py
S="$P2_SCRATCH/eval"
mkdir -p "$S/stats"
python3 tools/ue_char/eval/tiles.py "$S/tiles" "$S/stats/tiles.json" > /dev/null
N="${@:-03_white_tee 12_sundress_mom 13_construction_worker 15_executive}"
blender -b -P tools/ue_char/eval/citizens.py -- fbx $N 2>&1 | grep RESULT
E=art/night1/characters/export/citizens
blender -b -P tools/ue_char/eval/verify_fbx.py -- "$S/stats/fbx_verify.json" $(for n in $N; do echo $E/$n.fbx; done) 2>&1 | grep -c VERIFY
