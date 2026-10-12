# Terrain round 03 — canopy reads as leaves at every distance: captures and measurements

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Target (round-02 critic's biggest gap, Fable round target): the 165-520 m band becomes clustered leaf-card canopies, the canopy is lit by the engine instead of a constant emissive,
plus a silhouette test, and shore stills with the merged water. PASS needs: all 24 `p1_south` crown crops (round-02 boxes, `crops.json` copied unchanged) sigma-3 SD >= 9;
no foliage patch > 40 px with local luma SD <= 1.4 in `p1_south` (dark pockets included); no straight crown-silhouette edge > 40 px in `p10_lawn_eye`; capture GPU ms vs r2 disclosed.

**Status: pass 1 is the round's capture set (this directory). Pass 2 (built, not captured) was stopped: see Incidents. Numeric target NOT met (E9a, E9c fail; E9b passes).**

## Build (all in committed scripts; Content is generated, never committed)
1. `tools/export/collect_terrain.js`: exports `trees-{park,elm,conifer}-lod1` — the browser's own LOD1 generator (trees.js `canopyGeometry`, evaluated from the served trees.js source
   against the app's three.js and layout.js `mulberry32`, lobes from eztrees.js `buildEzArchetypes().lobes`) with `CARDS[kind][2..3]` = 22 x 2.8 m / 24 x 3.0 m / 18 x 2.0 m cards + solid
   core 0.85 (4 lobes, detail 0), instances = the near pool's, band 165-520 m. Self-check: the same code with the LOD0 recipe reproduces the exported `trees-*-near` geometry (all three kinds: true).
2. `build_terrain.py`: LOD1 pools on `M_TerrainCards`, no shadows; the clump hull (`trees-*-crown`, `M_TerrainClump`) only >= 520 m (band 520-3200), `trees-*-crownfar` no longer built;
   `Foliage.ush` bump back at the browser's 3.0 / 0.5.
3. **Why the r02 cards crushed to black** (found in the UE 5.8 source): Lumen runs with hardware ray tracing here; `RayTracingInstanceMask.cpp` makes every drawn primitive visible to indirect rays
   whatever `affect_dynamic_indirect_lighting` says ("only path tracing obeys the AffectsDynamicIndirectLighting flag"), and Lumen's minimal any-hit shader (`LumenHardwareRayTracingCommon.ush`
   `LumenMinimalRayAnyHitShader`) never evaluates an opacity mask. Every masked leaf pool was an opaque shell to Lumen, and the crown hull (no band clip outside raster) closed a solid ball
   around every card canopy at every distance: sky rays from a leaf hit it at once. Fix: foliage pools `visible_in_ray_tracing = False` (bark / trunks stay in).
4. `terrain_materials.py`: the constant `Emis = c * 1800 * (0.4 + 0.6 expo)` is gone from `M_TerrainLeaves` / `M_TerrainCards`; exposure drives material AO (`lerp(0.7, 1, expo)`, sky / indirect only)
   and a residual fill `c * FILL * tfFillW(...)` that is 0 on sun-facing outer leaves (SkyAtmosphere light direction), 0 within 10 m, ramps in to 30 m (`Foliage.ush tfFillW`). Two-sided foliage + subsurface unchanged.
5. Water: `build_water.py` run in this worktree (scratch `_scratch/terrain/water`); `Water_River` is a sublevel of every `V_*` / `VB_*` still map and `Manhattan_Terrain`; the city's flat WaterPlane is hidden in the private `City_Geo_T` copy too.
6. `crown_stats.py`: flat test counts dark pockets (luma < 40 near foliage); new silhouette test (foliage / sky boundary, Douglas-Peucker 1.5 px; axis-aligned, dark, thin or brick-hued segments listed apart with the reason).

Offline checks: `check_hlsl.py` 12 / 12, `scw_check.py` 27 / 27 permutations (UE ShaderCompileWorker, now also with new input pins). Warm-up shader check clean.

## Captures (pass 1, 2026-10-02 08:50-09:06, one GPU-lock hold)
| file | what | resolution |
|---|---|---|
| `stills/p1_south.jpg` ... `p10_lawn_eye.jpg` (9) | terrain stills of `shots.json`, game time 2 s, `-benchmark -fps=30`, frame cap 8 fps | **3840x2160 output, internal 1920x1080** (r.ScreenPercentage auto = 50 %, TSR) |
| `t4_lawn_sprint.mp4` (+ csv, log excerpt) | hero hidden, lawn sprint | 1920x1080 output, internal 1920x1080, 60 fps fixed step, 805 frames, 14.3 MB |
| `t5_avenue_to_park.mp4` (+ csv) | hero hidden, avenue sprint + swing chain to the park edge | same |
| `gpu_ms.txt` (pass 1: `pass1/gpu_ms.txt`) | `WH_PERF` per still over game 0.8-1.9 s (`RHIGetGPUFrameCycles`), frame-capped run | |

## Measured (pass 1)
| test | target | round 03 pass 1 | round 02 |
|---|---|---|---|
| E9a crown crops sigma-3 SD (24 boxes) | all >= 9 | **FAIL**: min 4.28, median 7.74, max 12.09, 5 / 24 >= 9 (far 11.0-12.1; mid 6.7-9.8; near-right 6.3-7.8; foreground 4.3-7.8) | min 5.41, median 8.34, 10 / 24 |
| E9b flat foliage patch > 40 px (dark pockets incl.) | none in p1 | **PASS**: p1 max 24.7 px, dark pockets 0.06 % of the frame; p10 16.0 px | p1 126.8 px (6 patches, black pockets), same checker |
| E9c straight crown silhouette in p10 | <= 40 px | **FAIL (47.2 px, 1 segment > 40)**: the left edge of a near leaf spray (quad border); set aside: building edges, a bare limb, the lamp head | 75.6 px (8 segments > 40, clump-hull facets), same checker |
| E9d capture GPU ms (same hold, r02 scripts built side by side into `/Game/TerrainR2`) | disclosed | p1 **156.2-160.6 ms** vs r02 **163.8 ms**; p10 **90.3-91.8 ms** vs r02 **89.1 ms** (4K output, 1080p internal, frame-capped, not an exclusive perf lock: contaminated) | |
| E1 lawn crops (sigma 6, 512 px) | guard | p10 7.43 / 6.34 (r02 6.10 / 5.32), p9 2.63 (2.33), p4 1.41 (1.33) | |
| E2 / E3 | | 89.9 % / 0 gaps (unchanged) | |

Reading: the 165-520 m band is now leaf cards (no boulders; p1 / p10 / p9 look leafy at every distance) and the black pockets are gone, but the leaf-scale contrast fell:
the LOD1 core spheres read as smooth round puffs, and with every leaf pool out of ray tracing nothing occludes the sky under the canopy, so the foreground boxes that held black pockets in r02
now hold smooth sky-lit lawn (boxes [2250,1800], [1500,1950], [2100,1950] = 4.3-5.9).

## Pass 2 (content built from the committed scripts, NOT captured)
Lumen-only shade proxy (each crown hull at 0.6 scale about its centre, hidden in game, visible to ray tracing + `affect_indirect_lighting_while_hidden`: occludes sky under / inside the crown,
not the cards' outward rays; 2643 / 1281 / 847 instances); LOD1 core broken up by world-space clump noise + holes; deeper spray-interior occlusion and wider per-leaf value spread on the cards;
ragged card / leaf quad borders (aimed at the 47 px p10 edge); fill 700 -> 450. Offline: DXC 12 / 12, ShaderCompileWorker 27 / 27. No frame of it exists: its numbers are unknown.

## Incidents (said plainly)
- Pass 1 hold, 08:40: the health monitor auto-paused (`WS-STARVED`) during my 960x540 warm-up and stopped it (SIGTERM); the GPU had been at 100 % with WindowServer at 0 % since 08:38, before my launch.
  The pause auto-lifted at 08:50 (I did not lift it); the 9 stills and 2 movies then ran clean (a few `probe=FAIL` / `WS-STARVE-WARN` samples during the 4K p1 still: a 160 ms GPU frame under an 8 fps cap keeps the GPU pinned).
- Pass 2 hold, 10:38: the monitor stopped my warm-up again. This time the GPU was idle before the launch, so **my own warm-up** pinned it (100 %, WindowServer 0-2 %, probe FAIL). Second stop of my engine
  today: I killed my hold scripts by PID (`round3.sh` / `capture_round.sh` / their nested lock wrapper) before the auto-lift could relaunch anything, and did not re-queue. Nothing of this piece is running.
  For the successor: `round3.sh` now defaults to a 4 fps cap for 4K stills (GPU duty ~65 % at 160 ms / frame instead of pinned); the warm-up spike itself is not understood yet (startup: shader / Lumen surface-cache / proxy card capture?).

## Known defects
p6 shows a lighter rectangular seam on the water near the seawall (not yet traced); far crowns >= 520 m are the clump hull (bump 3.0 / 0.5); the lawn tufts are still star sprites (r4, Sonnet);
pond-bank rocks, esplanade dressing deferred to r4.
