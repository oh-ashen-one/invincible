# Terrain round 05 — crowns as lit leaf volumes (and the lawn shadows they should cast)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Target (Opus director after the r04 critic [4,4,4,4,3]; r04 not merged, the integration still has r03): make the tree crowns read as lit leaf volumes that cast shadows on the lawn.
Measured on the 4K stills; stills AND the t4 / t5 movies are from the SAME build: content `/Game/TerrainR5b` (full build of 05:37 = build 4 + olive reeds + furniture vertex colours + crown shadow proxies for the conifers only), stills hold 05:58-06:17, movies hold right after it, nothing rebuilt in between.
A complete earlier package on `/Game/TerrainR5` (build 4, same shaders; white reeds, no proxies) is kept in `build4/` (stills + both movies + its measurements).
Spec: `SPEC.md` E1 (reconciled this round) and E11. Numbers: `tools/terrain/measure_r05.sh docs/night1/terrain/round-05` + `tools/terrain/tree_shadow_auto.py` (files beside this README).

## Captures
Real game (`-game`, offscreen), every launch through `gpu_slot.sh capture` (background priority), every launch with `-notraceserver`.
- Stills `stills/*.jpg`: 3840x2160 output, **internal 1920x1080** (auto 50 % screen percentage, TSR 2x), 4 fps frame cap, shot at game 2 s after a 960x540 warm-up (same as r04).
- Movies `t5_avenue_to_park.mp4`, `t4_lawn_sprint.mp4`: 1920x1080 output = **internal 1920x1080** (`r.ScreenPercentage 100`), fixed 1/60 s step, 12 fps wall cap, hero hidden, H.264 (t5 crf 30, 11.7 MB; t4 crf 32, 12.3 MB), telemetry beside them.
- Intermediate holds: `test/` (build 1), `test2/` (build 2), `build3/` (4 stills of build 3, the hold was stopped by me with `stop_ue.sh` to rebuild), `build4/` (complete package), `test5b/` (R5b test), `diag/` (lawn-shadow diagnostics, see `diag/NOTES.md`).
- GPU ms: **not measured (perf lock refused at 07:00: `gpu_slot.sh perf` exit 75, HID idle 5.5 h, `perf_refused.log`)**; the capture runs' own GPU frame time (contaminated, 1-2 other renders, frame-capped, 4K out / 1080p internal) is in `gpu_ms.txt`: p1 163.5 ms, p10 92.9 ms, p4 105.5 ms (r04 final hold 165.1 / 104.5; r03 161 / 92).

## Results (final build)
| target | wanted | measured | verdict |
|---|---|---|---|
| 1. p1 crown crops sigma-3 SD (24 E8 boxes) | all >= 9, median >= 12 | median **12.06**, 19 / 24 >= 9, min 6.11 (r04 median 8.13, 9 / 24, min 5.67; r03 7.74, 5 / 24) | median PASS, all-crops FAIL |
| 2. median crown-crop saturation | >= 0.65 | **0.636** (same tool: r04 0.518, r03 0.522) | FAIL |
| 3. E9c longest straight crown silhouette, p10 | <= 42 px, no floating hull / saucer cards | tool **40.3 px** (top 3: 40.3, 39.1, 34.2; the longest is the stepped roof of a building at x 3630-3670, y 340: `e9c_longest_segment_building.jpg`); no hull balls or saucer cards (the LOD1 core pool is not built) | PASS |
| 4. isolated p4 trees: lawn shadow / lit lawn luma | <= 0.6 each | 1 tree(s) measurable by geometry (`tree_shadow_auto.py`, isolation 12 m): ratio 1.011; no crown shadow visible on the p4 lawn (trunk / lamp shadows are) | FAIL |
| 5. E1 reconciled: p10 critic / guard sigma-6, p10 R / G | >= 8 / >= 8, 0.85-0.95 | **18.68 / 16.31**, R / G **0.920** (r04 11.25 / 9.97, 0.77) | PASS |
| 5. E1 reconciled: p4 critic box sigma-6 (aerial) | <= 5 | **5.48** (r04 10.85; the box holds a crown corner, an infield edge and a bench) | FAIL |
| E10 (b) lawn-crop saturation (5 boxes) | >= 0.70 | 0.917, 0.900, 0.777, 0.949, 0.700 | PASS |
| E10 (c) flat quads > 100 px in t4 at 4 fps | none | 1 in 54 frames | FAIL |
| E10 (d) t5 last 5 s, ground sigma-3 at 25-40 m | >= 5 | median 9.16, min 5.75 in 16 frames (r04 7.38 / 5.32) | PASS |

Notes on the table: E10 (c) — the single hit is the ez-tree trunk the t4 camera passes at 1.0 s (109 x 52 px of smooth sunlit bark inside a 400 px trunk, `flatquad_t4.json`); the same trunk sat just under
the threshold in the build-4 movie (0 hits) and the r04 critic flagged it too; the bark furrows of `M_TerrainBark` do not read on it (open item). Target 1: the five crops under 9 (luma 52-74) are
mostly dark lawn between foreground crowns. Target 2: the far crowns (y 450-750) read 0.54-0.64 through the golden haze. Target 4: see below.
Bank rocks: the 'white egg-shaped lumps' of p3 (r03 / r04 critics) were the reed clumps' white default tint — olive now (`round-05/stills/p3_lake.jpg` vs `build4/stills/p3_lake.jpg`); the
grey rock luma-SD target was not measured. Capture GPU ms (contaminated, see Captures). GPU ms under the exclusive perf lock: **not measured (perf lock refused: exit 75, Mac unattended, `perf_refused.log`)**.

## What changed (all in committed scripts; Content is generated, never committed)
1. `Shaders/Terrain/Foliage.ush`: `tfSummer` regrades the browser's per-tree autumn tints (hue 22-68 deg, brown .. olive) to a yellow-green .. leaf-green pair with the same luminance (per-tree variety kept);
   `tfClumpShade` world-space light / shade clumps (0.15-1.1 m octaves, x0.28-1.8) on the leaf cards beyond 25 m with yellower sunlit clumps; edge-on cards fade by their geometric facing
   (the p10 'saucer' streaks); 2.5 % dry leaves (r04 7 %); distant cards (+35 % beyond 450 m) and the >= 520 m hull (+50 %) gain albedo saturation against the golden haze; the cards use a fixed
   coverage threshold in the shadow pass.
2. `build_terrain.py`: the near leaf-card canopy (`trees-*-near`, 220-240 cards around a 0.27 core) is drawn out to 520 m (`NEAR_FAR`); the LOD1 pool (18-24 cards around a 0.85 solid core,
   the 'hull balls' of p10 and the smooth olive mid band of p1) is not built; bark tint 0.2 / 0.175 / 0.15 (was 0.33 / 0.29 / 0.25).
   R5b additions: furniture / reed meshes read their vertex colours (the export names the attribute `color`; r01-r04 drew them with a white (1, 1, 1) tint), olive `parkReeds` clumps (the p3 'white lumps'),
   hidden shadow-only crown proxies (`ISM_shadowproxy_*`, hull x0.85, in the RT scene, out of Lumen; R5b has them for the conifers only, the committed script builds all three kinds).
3. `terrain_materials.py`: `M_TerrainBark` vertical furrows / ridges / grain / lichen (triplanar on the two horizontal axes); blades R x1.53 (p10 R / G); lawn grade R 0.8; turf normal bent
   toward the sun (`Lawn.ush lwTurfNormal`, tilt 0.85; albedo x0.55); pond Specular 0.25 (water F0 0.02: the p3 Lake mirrored the pale sky as white blobs); greyer schist; FILL 650.
4. `Shaders/Terrain/Lawn.ush`: aerial fade of the lawn detail (`fa` = smoothstep 90-200 m: mottling / wear / clover x0.05, the base photo's own variation divided out, Park.ush's mid-scale
   patches compressed toward the nominal meadow luminance, softer stripe edges); the eye-level lawn is unchanged.
5. Tools: `measure_r05.sh`, `tree_shadow_auto.py` (shadow position predicted from the rig's sun and the crown heights, projected with the shot camera), `shadow_ratio.py` (hand boxes),
   crown saturation in `crown_stats.py`; `round5.sh` hold driver; `-notraceserver` in `capture_round.sh` / `run_build.sh`.

## Lawn shadows (target 4): not reached — what was found
See `diag/NOTES.md`. Our lawn shows no crown shadow in any build of this round, with VSM or CSM, while the city's own flat land in the city-only baseline VB_p4 shows long tree shadows.
Material AO + albedo gain (test 1) and a sun-facing turf normal (test 2 on) changed the lawn's colour / brightness but no crown shadow appeared. Open hypotheses for the next round, in order:
(a) the leaf pools are out of the ray-tracing scene (r03 fix for the black Lumen shells): if the sun's shadows are ray traced anywhere in this project's path (MegaLights / RT shadows), they cast nothing;
the city's trees (in the RT scene) do. Test: one still with `r.MegaLights.EnableForProject 0` / `r.RayTracing.Shadows 0`, and one with the near-card pool `visible_in_ray_tracing = True`.
(b) the non-Nanite VSM path (`[VSM] Non-Nanite Marking Job Queue overflow` in every terrain log). (c) a debug cube on the lawn to separate casting from receiving.
Update after diag5 (`diag/NOTES.md`): MegaLights off and the non-Nanite VSM thresholds off change nothing (0.23 / 0.27 mean abs luma), so (a) via MegaLights and (b) are ruled out; trunks and lamp posts DO cast crisp shadows on the lawn in the sunlit strip of p4 — the leaf cards do not.
