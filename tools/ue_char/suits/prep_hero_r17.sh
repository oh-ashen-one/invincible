#!/bin/bash
# Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.
# Round 17: as round 16, then hero_weights_r17.py (sternum-strip torso smoothing + a smooth head / neck blend: the Ash / Verdant chest steps, the Cinder chin seam break). Round 16: as round 15 but the skin weights go through hero_weights_r16.py (motion-aware top-4 truncation: the armpit stair-step jogs). Round 15 (the scripts keep their r14 names; r15 numbers live in hero_head_r14.PARAMS / hero_lens_r14.setup) CPU preparation of the hero GLB (seconds), the same sequence as build_characters.py 'prep' (which the chain's content build does NOT run: the engine imports the GLB as it stands):
#   prep_glbs -> hero_head_r14 (sculpt) -> hero_lens_r14 (eyes in the sockets) -> hero_shoulder_r14 (de-faceted shoulders) -> hero_weights_r14 (armpit + trapezius weights)
# then the mesh profile numbers (head_profile_r14.py).  Rerun it after ANY change of those scripts, before the hold.
set -eu
WT="$(cd "$(dirname "$0")/../../.." && pwd)"
export P2_SCRATCH="${P2_SCRATCH:-/Users/midir/sm2-n1/_scratch/characters}"
G="$P2_SCRATCH/ueimport"
cd "$WT"
python3 tools/ue_char/prep_glbs.py > /dev/null
python3 tools/ue_char/suit8/hero_head_r14.py "$G/SK_Hero.glb"
python3 tools/ue_char/hero_lens_r14.py "$G/SK_Hero.glb" | tail -1
python3 tools/ue_char/suit8/hero_shoulder_r14.py "$G/SK_Hero.glb"
python3 tools/ue_char/suit8/hero_weights_r16.py "$G/SK_Hero.glb"
python3 tools/ue_char/suit8/hero_weights_r17.py "$G/SK_Hero.glb"
python3 tools/ue_char/suits/head_profile_r14.py "$G/SK_Hero.glb" --brief --h6 | python3 -c "import sys,json; d=json.load(sys.stdin); print('profile:', {k: d[k] for k in ('T1_pct_HH','T2_pct_HH','T2b_pct_HH','T3_nose_bump_pct_HH','mouth_chin_groove_mm')}, 'H6', d.get('H6_clearance_px'))"
md5 -q "$G/SK_Hero.glb" | sed 's/^/SK_Hero.glb md5 /'
