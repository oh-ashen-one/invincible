# Terrain round 02 — trees / canopy at swing height: captures and measurements

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Target (round-01 critic's biggest gap): replace the flat hull crowns by foliage with real breakup. Test: every hand-picked 150 px crown crop of the new 4K `p1_south` has high-pass SD (luma, Gaussian sigma 3) >= 9, and no flat-shaded hull face wider than 40 px in `p1_south` / `p10_lawn_eye`.
**Result (the final render, "pass 3"): the numeric target is NOT met, the picture is much better.** 10 of 24 crown crops reach 9 (round-01 boxes on the round-01 still: 2.6 min / 6.0 median); far crowns 10.3-13.7, mid crowns 8.1-10.3, near-right 5.4-13.1, foreground canopy 6.3-7.5 (was 2.2-5.7 before the ambient fill).
p10_lawn_eye has no flat face > 40 px (12 px); p1_south has 2 patches > 40 px (max 108 px) in the crushed black pockets of the bottom-left foreground (luma 25-37: deep shadow, not lit hull faces).

Build: branch `night1/terrain`, base Manhattan content as in round 01, `build_terrain.py` through the nullrhi commandlet before every slot (about 2-9 min, no GPU), every game run through `gpu_slot.sh capture` offscreen with a frame cap (`t.MaxFPS` 12 / 20). No perf claim. GPU `Device Utilization` printed before each launch: 0-58 %.
Three renders of this round exist (pass 1 / 2 / 3; numbers of 1 and 2 in `pass1/`, `pass2/`; their media are not kept in the tree, history has pass 2). This directory is pass 3: the first hold (05:19) produced 5 stills and was stopped by the health monitor (see Incidents), the second hold (06:29, `ONLY_IDS`) the other 4 stills and both movies, same content.

## Files (resolutions disclosed)
| file | what | resolution |
|---|---|---|
| `stills/p1_south.jpg` ... `p10_lawn_eye.jpg` (9) | terrain stills of `shots.json` (maps `/Game/Terrain/Maps/V_<id>`), game time 2 s, `-benchmark -fps=30` | **3840x2160 output, internal 1920x1080** (r.ScreenPercentage auto = 50 %, TSR 2x upscale) |
| `t4_lawn_sprint.mp4` (+ `_telemetry.csv`, `_log_excerpt.txt`) | hero (hidden) sprints 130 m north over the lawn, ground mode 803 / 803 frames, floor height 0 (E7) | **1920x1080 output, internal 1920x1080** (`r.ScreenPercentage 100`), 60 fps fixed step, 805 frames, 12.5 MB |
| `t5_avenue_to_park.mp4` (+ csv) | street sprint + swing chain north up 5th Av, ends airborne over the park edge | same, 925 frames, 14.5 MB |
| `stills/t4_*_t{3,7,11}s_1920x1080.jpg`, `t5_*` | contact frames cut from the movies | 1920x1080 |
| `crops.json`, `crown_stats.json/.txt`, `crowns_preview.png`, `crop_manual.*`, `crop_stats.*`, `stats.json`, `shore_audit.*`, `hlsl_check.txt`, `warm_shader_check.txt` | measurements (boxes picked by eye with `tools/terrain/grid_overlay.py`) | |

Movies: **the hero is hidden** (`ShowFlag.SkeletalMeshes 0`, checked on frames): no dev-suit emblem (round-01 brand flag; the two round-01 movies and their contact frames were `git rm`ed). Blind critic pack: `/Users/midir/sm2-n1/_scratch/critic-E-r02/pack` (key outside: `pack.key.json`, pairs `pairs.json`),
14 pairs: 9 stills vs references, 3 previous-round vs this-round (p1 / p2 / p10; the shore cameras moved so no shore progress pair), 2 movies vs reference clips. Reservoir pair: the private refs have **no frame of the Reservoir itself** (all 127 street / traversal stills were scanned); it uses a park-water-basin aerial frame cut from the pond clip.

## Measured against `SPEC.md`
| id | target | result (pass 3) | pass 2 | pass 1 |
|---|---|---|---|---|
| **E8** crown crops hp-SD (sigma 3, 150 px, p1_south, 24 boxes in `crops.json`) | all >= 9 | **FAIL**: min 5.41, median 8.34, max 13.66; >= 9: 10 / 24 (far 3: 10.3-13.7; mid 7: 8.1-10.3; near-right 5: 5.4-13.1; foreground 9: 6.3-7.5, luma 54-129) | min 2.25, median 8.29, 9 / 24 (foreground luma 21-66, 2.2-5.7) | min 2.23, median 6.66, 3 / 24 |
| **E8** no flat hull face > 40 px | p1_south, p10_lawn_eye | p10 **PASS** (12 px); p1 **FAIL**: 2 patches, max 108 px, both in black shadow pockets (luma 25-37) | p1 82 px, p10 13 px | p1 72 px, p10 20 px |
| E1 lawn crops hp-SD (sigma 6, 512 px) | no lower than round 1 (4.65 / 4.92 / 6.93 / 15.09) | round-1 boxes: p9 4.32 / 5.72, p10 **6.10** (up), p4 13.54 -> **guard fails on 3 of 4** (the round-1 p9 / p4 boxes contain tree parts). Like-for-like pure-lawn windows (found in both renders, last box per image in `crops.json`): p10 4.74 -> **5.32**, p9 2.81 -> 2.33, p4 1.52 -> 1.33 | similar | |
| E2 grass cover of open land | >= 90 % | 89.9 % (unchanged) | | |
| E3 shoreline gaps > 5 m | <= 5 m | 0 (unchanged) | | |
| E7 collision | hero runs the lawn | ground mode 803 / 803 frames over 130 m, floor height 0 | | |
| lawn colour (secondary) | G/R >= 1.05, saturation >= 0.55 | **met on the pure-lawn windows**: p10 G/R 1.40 / sat 0.58, p9 1.12 / 0.64, p4 1.16 / 0.63 (round 1: 0.80-0.97 / 0.41-0.58); tree-containing round-1 boxes 0.82-1.03 | | |
| picnic-blanket slabs (critic secondary 4) | none dark | gone (blanket colours were double-linearised); small mauve / pale patches remain | | |
| shore shots (critic secondary 3) | waterline across >= 50 % of the frame, nothing occluding | p6 and p7 now show a continuous seawall + esplanade + water across the frame; p8 pier sheds are textured | p7 against a wall | p6 / p7 63-70 % building |
| E5 axes | >= 6 | not judged here (blind critic) | | |

Honest reading: the crowns went from flat hulls to leafy, autumn-tinted, textured foliage at every distance (see p1 / p3 / p10); far / mid crowns mostly clear 9; the foreground and near-right canopy sits at 5-8 because the ambient fill that lifted it from near-black also flattens it,
and the aerial lawn is still smooth (E1 aerial 1.3-2.8). Not met: E8 crop minimum (5.4), p1 flat black pockets, E1 guard on the aerial boxes.

## What changed since round 01 (all in the committed scripts)
1. `collect_terrain.js` exports the park-tree chain `trees-*-near / -crown / -crownfar`, `trunks-*` with each pool's near / far / fades. 2. `Shaders/Terrain/Foliage.ush` + 5 materials: dithered distance bands (ez L0 < 20 m, ez L1 < 44 m, leaf cards 44-165 m, clump crowns 165-520 m, crownfar >= 520 m),
ports of the browser's `crownMaterial` / `leafMaterial`; 46 HISM pools / 47,710 instances; the clip is skipped in shadow-depth / Lumen-card passes. 3. Nanite usage flag on the ez materials (round 01 drew the grey default material for ez L1 / bark). 4. Lawn albedo grade, brighter blankets.
5. Cameras: `p3` raised, `p6` moved off a pier-shed roof, `p7` moved to z -1270 (the browser export's far-city masses overhang the water along z -1080..-320). 6. Crown contrast (extra 1 m octave, bump 3 / 0.5 -> 7.5 / 0.2, deeper gaps, clump contrast 0.42-1.35).
7. Ambient fill `Emis = c * 1800 * (0.4 + 0.6 expo)` on the ez / leaf-card materials: the golden rig is physical (sun 44000 lux, EV 8-13), pass 2 had 0.65 (1000x too small, no effect), pass 3 raised foreground luma 40 -> 90.

## Incidents (said plainly)
- Warm-up #1 (2026-10-02 00:46): all five new tree materials failed to compile in the game (`float4` `band` vs UE's `float3` VectorParameter); the hold driver's warm-up check aborted the hold after 41 s (no stills wasted), fixed, re-queued (~1 h). `tools/terrain/scw_check.py` now verifies shader fixes offline with UE's ShaderCompileWorker (27 permutations), `check_hlsl.py` mirrors UE's parameter types.
- Pass 2 hold (03:44): the health monitor stopped the first 4K still launch (`WS-STARVED`: GPU 100 %, WindowServer CPU 2 %, probe fail) and auto-paused; the monitor itself lifted the pause after 10 calm minutes (03:55); I did not lift it; no engine of mine ran meanwhile; the rest of the hold ran clean.
- Pass 3 hold #1 (05:22:39): the monitor stopped my engine during the p4 still again (`WS-STARVED`, slots demoted to 1; a `look` perf engine was rendering at the same time = two heavy renders). I killed my own hold scripts by PID so nothing relaunched, and re-queued only the missing stills + movies (hold #2, 06:29-06:41, ran clean with one `probe=FAIL` sample, no stop).
  Two monitor stops in this task: treat the first 4K launch with another engine rendering as the risky moment.
- Pass-3 `Emis` is too strong close to the camera: in `t4_lawn_sprint` at 3 s a branch 3 m from the camera reads pale mint-white (fill on a sunlit leaf). Next: scale the fill by shade / distance (about 1000 and only beyond 10 m) rather than a constant.

## Known defects visible in these captures
Far crowns (165-300 m) read as bumpy boulders (the browser's 4-lobe crown LOD, now with strong bump); crushed black pockets in the p1 foreground; pale fill on very close leaves; aerial lawn smooth; the t5 perimeter ground at 13-15 s is flat grey city asphalt (not terrain); rock banks of the p3 pond are white lumps.
