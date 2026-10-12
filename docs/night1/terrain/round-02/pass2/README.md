# Terrain round 02 — trees / canopy at swing height: captures and measurements

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Target (round-01 critic's biggest gap): replace the flat hull crowns by foliage with real breakup. Test: every hand-picked 150 px crown crop of the new 4K `p1_south` has high-pass SD (luma, Gaussian sigma 3) >= 9, and no flat-shaded hull face wider than 40 px in `p1_south` / `p10_lawn_eye`.
**Result of this render (pass 2): the target is NOT met.** 9 of 24 crown crops reach 9; far and mid crowns (10 crops) are 8.2-13.8, the dark foreground canopy (9 crops, luma 21-66) is 2.2-5.7. Pass 3 (a physically scaled ambient fill for exactly that foreground) is queued, see the end.

Build: branch `night1/terrain`, base Manhattan content as in round 01, `build_terrain.py` run 2026-10-02 05:5x UTC (nullrhi commandlet, before the slot). Every game run through `gpu_slot.sh capture` (one hold, 1461 s incl. a 10 min health pause wait),
offscreen, throttled (`t.MaxFPS` 12 / 20). Perf is not measured (no perf claim). GPU `Device Utilization` printed before every launch: 0 %.

## Files (resolutions disclosed)
| file | what | resolution |
|---|---|---|
| `stills/p1_south.jpg` ... `p10_lawn_eye.jpg` (9) | terrain stills of `shots.json` (maps `/Game/Terrain/Maps/V_<id>`), game time 2 s, `-benchmark -fps=30` | **3840x2160 output, internal 1920x1080** (r.ScreenPercentage auto = 50 %, TSR 2x upscale) |
| `t4_lawn_sprint.mp4` (+ `_telemetry.csv`, `_log_excerpt.txt`) | hero (hidden) sprints 130 m north over the lawn, ground mode all 803 frames, floor height 0 (E7) | **1920x1080 output, internal 1920x1080** (`r.ScreenPercentage 100`), 60 fps fixed step, 805 frames, 14.8 MB |
| `t5_avenue_to_park.mp4` (+ csv) | street sprint + swing chain north up 5th Av, ends airborne over the park edge | same, 925 frames, 14.5 MB |
| `stills/t4_*_t{3,7,11}s_1920x1080.jpg`, `t5_*` | contact frames cut from the movies | 1920x1080 |
| `crops.json`, `crown_stats.json/.txt`, `crowns_preview.png`, `crop_manual.json/.txt`, `crop_stats.*`, `stats.json`, `shore_audit.*`, `hlsl_check.txt`, `warm_shader_check.txt` | measurements | |
| `pass1/` | the first render of this round (numbers + measurements only; its stills / movies are kept local) | same |

Movies: **the hero is hidden** (`ShowFlag.SkeletalMeshes 0`, checked on frames at 3 / 8 / 12 s): no dev-suit emblem (round-01 brand flag; the two round-01 movies and their contact frames were `git rm`ed).

## Measured against `SPEC.md`
| id | target | pass 2 | pass 1 | round 01 |
|---|---|---|---|---|
| **E8** crown crops hp-SD (sigma 3, 150 px, p1_south, 24 boxes in `crops.json`) | all >= 9 | **FAIL**: min 2.25, median 8.29, max 13.83; >= 9: 9 / 24 (far 3 crops 9.9-13.8; mid 7 crops 8.2-10.1; near-right 5 crops 3.9-13.6; foreground 9 crops 2.2-5.7) | min 2.23, median 6.66, 3 / 24 >= 9 | same boxes on the round-01 still: min 2.6, median 6.0 |
| **E8** no flat hull face > 40 px | p1_south, p10_lawn_eye | **p10_lawn_eye PASS** (max 12.8 px). **p1_south FAIL**: 3 patches > 40 px (max 82 px), all in the crushed dark foreground (luma 20-35: shadow, not lit hull faces) | p10 20 px, p1 72 px | p1 56 px, p10 41 px (same metric, lawn and sky excluded) |
| E1 lawn crops hp-SD (sigma 6, 512 px) | no lower than round 1 (4.65 / 4.92 / 6.93 / 15.09) | the same boxes: 4.31 / **6.23** / 5.78 / 12.82 -> **guard FAILS on 3 of 4** (the round-1 p9 / p4 boxes contain tree parts, so they track tree edges). Like-for-like pure-lawn windows found in BOTH renders: p10 (2240,1856) 4.74 -> **5.38**, p9 (512,1856) 2.81 -> 2.33, p4 (3520,1856) 1.52 -> 1.33 | | 4.92 / 4.65 / 6.93 / 15.09 |
| E2 grass cover of open land | >= 90 % | 89.9 % (unchanged, `stats.json`) | | 89.9 % |
| E3 shoreline gaps > 5 m | <= 5 m | 0 (unchanged, `shore_audit.json`) | | 0 |
| E7 collision | hero runs the lawn | 803 / 803 frames ground mode over 130 m, floor height 0 | | |
| lawn colour (secondary) | G/R >= 1.05, saturation >= 0.55 | p10 crop G/R 1.20, sat 0.51; aerial crops G/R 0.78-0.96 (p9 0.96 / 0.89, p4 tree-heavy 0.78), sat 0.53-0.57 -> partly met (the lawn is vivid green from p1 / p10; golden haze keeps the far lawn yellow) | | G/R 0.80-0.97, sat 0.41-0.58 |
| picnic-blanket slabs (critic secondary 4) | none dark | gone (blanket colours were double-linearised); small pale patches remain | | |
| E5 axes | >= 6 | not judged here (blind critic) | | |

Honest reading: far / mid crowns moved from "flat green hulls" (3.3-6.5 in the round-01 critic's crops) to clumpy leaf-speckled crowns that mostly clear 9; the dark foreground canopy (ez-tree L1 + leaf cards seen from 30-80 m, mostly in the sun's shadow) does not,
and a pure-lawn aerial crop is still smooth (1.3-2.8). The lawn E1 guard is not held on the aerial boxes.

## What changed since round 01 (all in the committed scripts)
1. `collect_terrain.js` exports the park-tree chain `trees-*-near / -crown / -crownfar`, `trunks-*` with each pool's near / far / fades. 2. `Shaders/Terrain/Foliage.ush` + 5 materials: dithered distance bands (ez L0 < 20 m, ez L1 < 44 m, leaf cards 44-165 m, clump crowns 165-520 m, crownfar >= 520 m),
ports of the browser's `crownMaterial` / `leafMaterial`; 46 HISM pools / 47,710 instances. 3. Nanite usage flag on the ez materials (round 01 drew the grey default material for ez L1 / bark). 4. Lawn albedo grade, brighter blankets. 5. Cameras: `p3` raised, `p6` moved off a pier-shed roof, `p7` moved off the far-bank masses.
6. Pass 2: crown contrast (extra 1 m octave, bump 3 / 0.5 -> 7.5 / 0.2, deeper gaps) and an ambient-fill emissive on the leaf materials (**scaled 1000x too small: no visible effect**, the rig is physical: sun 44000 lux; corrected in pass 3).

## Incidents (said plainly)
- Warm-up (2026-10-01 ~00:46): all five new tree materials failed to compile in the game (`float4` `band` vs UE's `float3` VectorParameter); the hold driver's warm-up check aborted the hold after 41 s (no stills wasted), fixed, re-queued (2 h). `tools/terrain/scw_check.py` now verifies fixes offline with UE's ShaderCompileWorker.
- Pass 2 hold (03:44-04:08): the health monitor stopped the first 4K still launch (`WS-STARVED`: GPU 100 %, WindowServer CPU 2 %, probe fail) and auto-paused at 03:45; the pause was lifted by the monitor itself after 10 calm minutes (03:55), I did not lift it, no engine of mine ran meanwhile. After the resume
  the 9 stills + 2 movies ran with at most single `probe=FAIL` samples (`_scratch/gpu/health.log`), no further stop. Treat a 4K still launch as the risky moment.

## Known defects visible in these captures
Dark foreground canopy; far crowns still read as lumpy boulders at 165-300 m (the browser's 4-lobe crown LOD, now with strong bump); the t5 perimeter ground at 13-15 s is flat grey city asphalt (not terrain); aerial lawn smooth (E1).
