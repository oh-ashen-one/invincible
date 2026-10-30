# Invincible hero: in-game blind A/B of new clips (old vs new, same build, launch flag)

Homage fan game. Not an official Marvel, Sony, Image Comics or Skybound project; no affiliation. See DISCLAIMER.md.

The new clips are imported into their own folder, `/Game/Invincible/HeroV2R/Anims`, on the shipped hero's skeleton. The game picks
the folder at launch, so the shipped `/Game/Invincible/HeroV2/...` assets are never touched and one build serves both sides.
Ship rule (SEEDANCE.md): only "visibly better" ships, never a "tie"; judge on close-ups; a flat first blind round = stop and report.

## The flag

`-WHHeroV2Clips=<package path>` (`UWHHeroV2AnimInstance::ClipRootOverride`, read at every anim-instance init):

- Each of the 12 `AS_<Clip>` is looked up in `<package path>` first; a clip missing there falls back, per clip, to the shipped
  `/Game/Invincible/HeroV2/Anims`. A set with only 3 new clips still plays the other 9 shipped ones.
- No flag, an empty value, or the shipped folder itself = no override (the init line is byte-identical to before). A trailing `/` is
  ignored. The existence probe (`FPackageName::DoesPackageExist`) keeps missing override clips from logging load warnings.
- The skeleton-mismatch check is unchanged: a clip on another skeleton is still loaded and named under `skeleton mismatch:` (the
  importer below refuses to produce one).
- Land / boost / hover timings are re-measured from whichever clips were loaded (`AnalyzeLandClip` and the others run after the load).
- Only the hero. The chase villain (`WHChaseVillain.cpp`) still loads its 3 clips from the shipped folder.
- Log, with the override: `WH_HEROV2 anim init: 12/12 clips from /Game/Invincible/HeroV2R/Anims (fallback /Game/Invincible/HeroV2/Anims)
  [override 3/12: AS_Hover AS_LandHero AS_Takeoff] (missing: none; skeleton mismatch: none), ref ok ...`. The baseline run prints
  `... clips from /Game/Invincible/HeroV2/Anims (missing: none; ...`. The relevant line is the second one per run (see
  heroV2_integration_NOTES.md: the first init runs before the v2 mesh is set).

## 1. The GLB (rig + only the new clips; headless Blender, no GPU slot needed, waits for a Blender slot)

```bash
cd /Users/midir/spider-man-2-invincible
O=Local/video2rig/hero/out-glb      # run_clip.sh export output: <Clip>_v2r_v<N>.glb carrying the action <Clip>_v2r_v<N>
tools/invincible/v2r/make_v2r_glb.sh unreal/WebHomage/Saved/P2Build/invincible/SK_InvincibleV2R.glb \
  $O/Takeoff_v2r_v1.glb:Takeoff_v2r_v1=A_Takeoff \
  $O/LandHero_v2r_v1.glb:LandHero_v2r_v1=A_LandHero      # one spec per new clip; replace N with the takes that passed the first look
```

Expect `ANIMS A_LandHero A_Takeoff` and `MAKE_V2R_GLB_OK ...`. The script refuses unknown clip names, duplicates, and an output GLB
that does not carry exactly the listed animations.

## 2. Import (one headless editor commandlet through gpu_slot; nothing of this project may be running)

The same command line `build_manhattan.ue_python()` builds (`-run=pythonscript -unattended -nullrhi ...`, the shared coordinator root,
max hold), with the label `inv-v2r-import`. `import_invincible_v2.py` has no committed caller; HANDOFF.md documents `ue_python()` as
the pattern, which is mirrored here.

```bash
cd /Users/midir/spider-man-2-invincible
P=$PWD/unreal/WebHomage; L=$HOME/sm2-invincible-cache/v2r-import; mkdir -p "$L"
[ -e "$HOME/.cache/gpu-slot/PAUSED" ] && echo "STOP: GPU coordinator PAUSED (never clear it)"
pgrep -f "$P/WebHomage.uproject" && echo "STOP: an engine of THIS project runs (stop your own driver first; never touch others)"
GPU_SLOT_DIR=$HOME/.cache/gpu-slot GPU_SLOT_CAPTURE_MAX_HOLD=1800 \
WH_V2R_GLB=$P/Saved/P2Build/invincible/SK_InvincibleV2R.glb WH_V2R_DEST=/Game/Invincible/HeroV2R/Anims \
tools/gpu/gpu_slot.sh capture --label inv-v2r-import --timeout 3600 -- \
  "/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" "$P/WebHomage.uproject" \
  -run=pythonscript -script="$P/Scripts/import_invincible_v2r_anims.py" \
  -unattended -nullrhi -nosplash -RenderOffScreen -NoSound -NoCrashReports -abslog="$L/import.log"
echo "rc=$?"; grep -E 'CLIPS|DEST|SM2_BUILD_OK|LogPython: Error|Traceback|invincible-v2r' "$L/import.log"
```

Success = `SM2_BUILD_OK: import_invincible_v2r_anims.py`, a `CLIPS [...]` line naming exactly the new clips, and no
`LogPython: Error` or `Traceback`. rc 1 with the sentinel present is the known GameFeatureData exit (HANDOFF.md); rc 75 = GPU admission
timed out (not run; do not retry in a loop); rc 124 = max hold exceeded.
The script clears ONLY `WH_V2R_DEST` (it refuses `/Game/Invincible/HeroV2` and anything above it) and saves only that folder.

Same thing through the helper. The label becomes `sm2-showcase-inv-v2r-import`. The helper raises SystemExit on rc 1 even when the
sentinel is present. It also refuses to start below `SM2_ISLAND_MIN_FREE_GB` (default 150 GB). On 2026-10-30 the data volume had
44 GB free, so the helper needs the override below. The direct command above has no disk floor.

```bash
cd /Users/midir/spider-man-2-invincible && mkdir -p $HOME/sm2-invincible-cache/v2r-import/{jobs,logs}
SM2_ISLAND_MIN_FREE_GB=20 SM2_MANHATTAN_SCR=$HOME/sm2-invincible-cache/v2r-import python3 -c "
import os, sys; sys.path.insert(0, 'unreal/WebHomage/Scripts'); import build_manhattan as bm
bm.ue_python('inv-v2r-import', bm.exec_wrapper(os.path.join(bm.HERE, 'import_invincible_v2r_anims.py'), ''),
             {'WH_V2R_GLB': os.path.join(bm.PROJ, 'Saved/P2Build/invincible/SK_InvincibleV2R.glb')}, timeout=1800,
             sentinel='import_invincible_v2r_anims.py')"
```

## 3. Close camera (is there a tunable?)

There is no single "chase distance" flag. The flight framing (`-WHCamTune=FlightDistMin=..,FlightDistMax=..,FlightPixH=..`) applies only to
fly / boost / dash / breach lines. Hover, takeoff, slam dive, and ground all keep the chase framing, and `AWebTravCharacter::FlightFrame`
overwrites `Cam.ChaseDist` every frame. `ChaseDist` and the hard floor `MinHeroDist` (2.2 m) are not in `FWebTravCamera::SetTune`.
The chase distance can still be pulled in through tunables that ARE in the table. The chase hold radius is `3.5..5.0 x ChaseKNow - 0.4`
(airborne), and `ChaseKNow` is clamped to `[ChaseFbMin, ChaseFbMax]`. On the ground the lens cranes up when it is nearer than `GndMinDist`.

Close-up flag (starting values, not yet run):
`-WHCamTune=ChaseFbMin=0.5,ChaseFbMax=0.6,GndMinDist=2.3`. This gives a horizontal hold of 2.25..2.6 m instead of about 3.1..4.6 m.
The earlier sim telemetry (`~/sm2-invincible-cache/simR7`, older build) shows `cam_dist_m` median 5.04 m on fl01 and fl11. Check the new
value with a cheap nullrhi run before rendering. The goal is a median of about 3 m. Adjust `ChaseFbMax` to suit:

```bash
python3 tools/invincible/run_flight_suite.py ab-v2r-camsim --sim --cases fl01,fl11 --game-arg=-WHCamTune=ChaseFbMin=0.5,ChaseFbMax=0.6,GndMinDist=2.3
python3 -c "
import csv, statistics, sys
for c in ('fl01_takeoff_hover', 'fl11_slam_crater'):
    r = list(csv.DictReader(open('$HOME/sm2-invincible-cache/ab-v2r-camsim/report/%s_telemetry.csv' % c)))
    print(c, 'cam_dist_m median %.2f' % statistics.median(float(x['cam_dist_m']) for x in r))"
```

Smallest C++ addition if the indirect knob is not close enough (proposal, NOT implemented). In `WebTravCamera.cpp`
`FWebTravCamera::SetTune`, add `{TEXT("MinHeroDist"), &MinHeroDist}` (one table entry, so the 2.2 m floor becomes tunable). Also add a
`double ChaseCloseK = 1.0;` in `WebTravCamera.h` with a matching table entry, and multiply it into `BackDist`, `MinH` and `MaxH` in the
chase block (`WebTravCamera.cpp` ~1311 / ~1372). `-WHCamTune=ChaseCloseK=0.6,MinHeroDist=1.6` would then be a direct close-up control.

## 4. Two rendered runs, same cases, same camera, only the clip folder differs

Rendered = 1920x1080, fixed 1/60 s, through gpu_slot one engine per case (the suite stops after two runs without telemetry). Run them one
after the other, never both at once:

```bash
cd /Users/midir/spider-man-2-invincible
CAM=--game-arg=-WHCamTune=ChaseFbMin=0.5,ChaseFbMax=0.6,GndMinDist=2.3      # or the values the sim check settled on
python3 tools/invincible/run_flight_suite.py ab-v2r-new --cases fl01,fl11 $CAM --game-arg=-WHHeroV2Clips=/Game/Invincible/HeroV2R/Anims
python3 tools/invincible/run_flight_suite.py ab-v2r-old --cases fl01,fl11 $CAM
grep -h 'WH_HEROV2 anim init' $HOME/sm2-invincible-cache/ab-v2r-{new,old}/fl01_takeoff_hover/fl01_takeoff_hover.log
```

Use the `--game-arg=<value>` form: argparse rejects `--game-arg -WH...` because the value starts with `-`. Check the init lines: the new
run must show `[override K/12: ...]` naming the new clips, and the old run must show plain `/Game/Invincible/HeroV2/Anims`. Without that,
the pair is not an A/B. Outputs go to `docs/invincible/captures/ab-v2r-{new,old}/{fl01_takeoff_hover,fl11_slam_crater}.mp4` plus
`_sheet.jpg` and CHECK.md. fl01 covers takeoff and hover (AS_Takeoff, AS_Hover, AS_LaunchUp). fl11 covers the slam dive and hero landing
(AS_LandHero, then AS_GroundIdle).

## 5. Blind pack (critic sees A / B only; the key stays outside the pack)

```bash
cd /Users/midir/spider-man-2-invincible
N=docs/invincible/captures/ab-v2r-new; O=docs/invincible/captures/ab-v2r-old; K=$HOME/sm2-invincible-cache/ab-v2r
mkdir -p $K && cat > $K/pairs.json <<EOF
[{"id": "takeoff-hover", "x": "$PWD/$N/fl01_takeoff_hover.mp4", "y": "$PWD/$O/fl01_takeoff_hover.mp4",
  "note": "close chase camera: ground takeoff into a hover, climb, strafe, touchdown. Judge the hero's motion only: weight, anticipation, follow-through, fluidity, stiffness, pops, foot contact"},
 {"id": "slam-landing", "x": "$PWD/$N/fl11_slam_crater.mp4", "y": "$PWD/$O/fl11_slam_crater.mp4",
  "note": "close chase camera: hover, straight slam dive, superhero landing, stand-up. Judge the hero's motion only: dive pose, impact, kneel, recovery, fluidity, pops, foot contact"}]
EOF
python3 tools/night1/abpack.py $K/pack $K/pairs.json      # -> $K/pack/<id>/{A,B}.mp4 + PAIRS.md; key in $K/pack.key.json
```

Give only `$K/pack` to a separate critic (never the key, never this doc's flag names). x = new clips. Ship only on "new visibly better"
in both pairs. A tie or a split is a stop-and-report.
