# River water A/B (Opus 5.5 build), round 01: capture notes

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Build: `night1/water-ab-opus`, `Scripts/build_manhattan.py` (unchanged, via the scratch wrapper below) + `Scripts/build_water.py`.
Views: `../views.json`. Every Unreal run went through `gpu_slot.sh` (captures: shared slot; perf: exclusive lock).

## Files

| file | map | rig | output | internal | notes |
|---|---|---|---|---|---|
| S4_golden_4k.jpg | /Game/Maps/Manhattan_View_S4 | golden | 3840x2160 | 3840x2160 (r.ScreenPercentage 100) | t = 16 s; JPEG q92 of the PNG |
| S4_golden_1080.jpg | same | golden | 1920x1080 | 1920x1080 | t = 16 s |
| river_low_4k.jpg | /Game/Water/Maps/Water_View_RiverLow | golden | 3840x2160 | 3840x2160 | t = 16 s |
| river_low_1080.jpg | same | golden | 1920x1080 | 1920x1080 | t = 16 s |
| river_low_dolly.mp4 | /Game/Water/Maps/Water_View_RiverLow_Dolly | golden | 1920x1080 60 fps, 600 frames | TSR auto (engine default for 1080p output) | `-benchmark -fps=60 -dumpmovie`, frames t = 6.0..16.0 s, H.264 crf 20; camera at river_low at the first frame, 2 m/s forward |
| extra_river_low_midday_1080.jpg | Water_View_RiverLow_Midday | midday | 1920x1080 | 1920x1080 | extra |
| extra_S4_midday_1080.jpg | Water_View_S4_Midday | midday | 1920x1080 | 1920x1080 | extra |
| farfield_*.json | | | | | `tools/export/spec_farfield.py` on the S4 PNGs (CITY-SPEC C11-C15 instrument) |
| perf.json, perf_gpu.json, perf_gpu_S4_rerun.json | | | | | perf below; `perf_gpu*.json` = gpu_slot sidecars |

Still captures were not exclusive (GPU util before each: 100, 53, 0, 9, 100, 100 % for the six stills in table order); they are images, not timings.

## CITY-SPEC C14 at S4 (far shore Y minus river Y, target 5..35)

| capture | far_shore Y | river Y | C14 |
|---|---|---|---|
| S4_golden_4k (this water) | 171.1 | 130.2 | 40.9 |
| S4_golden_1080 (this water) | 171.7 | 130.7 | 41.1 |
| Water_Perf_S4_Base 1080 (P1 flat water, same build, iteration capture) | 172.9 | 124.6 | 48.3 |

## GPU cost (perf.json)

3840x2160 output, TSR 67 % (internal 2573x1447), static camera, frames t = 16..36 s, `tools/perf_ue/run_perf.py -csvGpuStats`,
water map vs the same view with P1's previous flat water plane (`Water_Perf_*_Base`).

Run 1: one exclusive lock for all four maps. `gpu_slot.sh summary`: `class=perf exclusive=yes util_before=0% util_after=0%
util_during_avg=61.7% wait_s=117.58 instances_before=1 instances_max=3 contaminated=false` (perf_valid true). run_perf.py additionally lists one
foreign Unreal editor process (pid 11322, 6-10 % CPU) as present.

| view | GPU avg ms water / base | delta | SingleLayerWater | SLW depth prepass | LumenReflections delta | Basepass delta | sum of these |
|---|---|---|---|---|---|---|---|
| river_low | 26.66 / 26.67 | -0.01 | 0.75 | 0.25 | +0.54 | +0.01 | 1.54 |
| S4 | 33.66 / 27.24 | +6.41 | 0.55 | 0.30 | +0.24 | +0.07 | 1.15 |

In run 1 the S4 water map had 45 hitch frames and 5-s block averages 36.5 / 42.3 / 48.6 / 59.1 ms (frame), the S4 base map 33.2 / 34.6 / 33.9.

Run 2 (S4 pair only, repeated): lock sidecar `contaminated=true reasons=foreign-capture-process-during-run` (a combat `-game` capture
started during the run), so these numbers are contaminated.

| view | GPU avg ms water / base | delta | SingleLayerWater | SLW depth prepass | LumenReflections delta | Basepass delta | sum |
|---|---|---|---|---|---|---|---|
| S4 (contaminated) | 31.91 / 31.03 | +0.88 | 0.58 | 0.32 | +0.09 | -0.02 | 0.97 |

## Build facts relevant to reading the captures
- The P1 flat `WaterPlane` is hidden in every map that has this water; the `_Base` maps show it with its original material.
- river_low camera x = -768.0 m, not the layout's shoreX (-744.16 m, which lies on the esplanade in the UE build); see views.json.
- The dolly map uses InterpToMovement; offsets are un-rotated because the component rotates control points by the actor rotation.
- Grid mesh import: mesh description 207 745 verts / 415 104 tris; `get_num_vertices(0)` in the -nullrhi commandlet returns 254.
- Emissive output of the SLW material did not appear in renders (debug test); glitter is implemented through normal / roughness.

## Scratch wrapper used for the city build (not committed; `/Users/midir/sm2-n1/_scratch/water-ab-opus/run_manhattan.py`)
```python
import os, sys, time, subprocess as _sp
WT = '/Users/midir/sm2-n1/water-ab-opus'
os.environ['SM2_MANHATTAN_SCR'] = '/Users/midir/sm2-n1/_scratch/water-ab-opus'
sys.path.insert(0, WT + '/unreal/WebHomage/Scripts'); os.chdir(WT)
import build_manhattan as b
b.DEV_PORT = int(os.environ.get('WATER_DEV_PORT', '5231'))
b.SCR = os.environ['SM2_MANHATTAN_SCR']
b.EXPORT = os.path.join(b.SCR, 'export', 'midtown3x3'); b.TEX = os.path.join(b.SCR, 'tex'); b.CHAR_STAGE = os.path.join(b.SCR, 'chars')
def _wait_slot():  # same rule (wait while 3+ Unreal instances run), polled every 5 s
    while int(_sp.run("pgrep -f '^/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor( |$)' | wc -l",
                      shell=True, capture_output=True, text=True).stdout.strip() or 0) >= 3: time.sleep(5)
b.wait_slot = _wait_slot
sys.argv = ['build_manhattan.py'] + sys.argv[1:]; b.main()
```
