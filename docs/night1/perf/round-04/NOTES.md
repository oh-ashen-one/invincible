# F perf, round 04: notes (neutral facts, no self-assessment)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. Numbers are from the RUNNING game (`-game`, offscreen, 3840x2160 back buffer, **internal 1920x1080 = TSR 50 %**, read back from `wh_perf.internal_w/h`)
> on the rebuilt integrated `/Game/Maps/Manhattan` (golden rig; same build as round 03: integration c4fffda, no new merge this round), the 30 s swing route `route_30s_warmup15.json`, window = game s 15..45, fixed step
> (`-benchmark -fps=60`), CSV profiler (1800 frames per run), every perf run inside `gpu_slot.sh perf` (exclusive, `perf_valid`, util before 0 %, one Unreal instance, `-notraceserver`; no Unreal Insights / trace server was started).
> Raw rows: `TABLE.md` (every run with its lock verdict), `perf/<session>/<config>/{result.json,run.txt,csv.csv.gz}`. Look gate: `LOOK_GATE.md` / `look_gate_final.json` (`tools/perf_ue2/look_gate.py`).

## 1. Round target (round-03 critic) and result
| line | target | result (`perf/f1`, shipped path `@ini`, no per-run cvars) | pass |
|---|---|---|---|
| P1 route p50 | <= 16.67 ms | **16.08 / 16.03 / 16.11** (`ship_a / ship_b / ship_c`) | yes (margin 0.56-0.64) |
| P2 route p95, hitches | <= 18.18 ms, 0 | **18.03 / 18.03 / 18.05**, 0 hitches (max frame 21.0 / 25.0 / 23.1 ms) | yes (**margin 0.13-0.15 ms: thin**) |
| VSM `GPU/ShadowDepths` p95 | <= 2.5 ms | **2.44 / 2.43 / 2.44** (mean 1.93; round 03 4.22, mean 2.23) | yes |
| trees within 100 m back in the ray-tracing scene | in | tree **leaves** (all LODs + park crown masses, 42 337 instances) back in, culled from the RT scene by solid angle 3 deg (a ~5 m street tree stays in to ~100 m); **bark stays out**; leaves are **opaque in ray tracing** (see 3) | yes, with the two limits named |
| cloud TracingMaxDistance | >= 20 km | **20 km** (golden / midday / night rigs, `content_audit.json`) | yes |
| round-02 S1 crop (485,0,710,490), same crop | SSIM >= 0.97 vs as-found | **0.9508** (round 03 on this crop: 0.4998); S2 windows 0.9932, S2 gold 0.9853 | **no (S1)** |
| canopy luma vs as-found | within +-10 % | S1 0.912, t20 0.948, t42 1.042, S2 1.026 | yes (S1 at the edge: -8.8 %) |
| route saturation vs as-found | within 5 % | t20 -1.7 %, t28 +2.0 %, t38 +0.2 %, t42 +1.1 % (round 03: -12 / -18 / -17 / -9 %) | yes |
| clouds at t42 (sky gradient, top 15 %) | restored | ratio to as-found 1.013 (round 03: 0.53) | yes |
| P3 static S2 p50 | <= 18.2 | 14.66 (p95 15.82) | yes |
| P6 cloud pass last 600 frames | <= 0.7 ms (round-01 line, set for the 4 km cloud) | **1.05 ms** (20 km as the critic asked; 20 km without the sample spread was 2.0+) | **no: superseded by the >= 20 km demand** |
| P8 mean FrameTime - GPUTime | <= 1.0 | **1.40** (round 03 0.82; the leaves in the RT scene add CPU / serialisation, 0.8 -> 1.4 in every tree run of y1 / z1 / f1) | **no** |

## 2. VSM: what invalidated pages every frame (sessions `v1`, `w1`, `x1`)
- VSM stats into the CSV (`-csvCategories=VSM`, `v1/st`): ~70 pages requested per frame, **54 of them dynamic pages invalidated every frame** (`VSM/DYNAMIC_INVALIDATED_PAGES` p50 55), static invalidations ~0. `WPO_CONSIDERED_PAGES` = 0: no WPO material in the map (the city build uses no World Position Offset).
- Debug switches (same session): skip all dynamic invalidation -> ShadowDepths p95 4.19 -> 2.25; **skip invalidation of REVEALED primitives only -> 2.39**. A revealed primitive = a non-Nanite primitive going from CPU-culled to rendered for the clipmap (engine `VirtualShadowMapClipmap.cpp` `OnPrimitiveRendered`, `VirtualShadowMapCacheManager.cpp` 1296): every reveal invalidates all pages of all its instances.
  The city meshes are non-Nanite (only the detail tiles are Nanite), so the hero / street people (deformable, a few pages) are not the cost; the swinging camera is: it re-reveals primitives every frame.
- Two CPU culls reveal them while the camera moves: **far-shadow culling** (primitives without "cast far shadow" are culled beyond the directional light's dynamic shadow distance) and the **frustum-clipped caster volume** of the clipmap.
  | config (x1 / w1, same session as its control) | p50 | p95 | ShadowDepths mean / p95 |
  |---|---|---|---|
  | control `x1/ctl`, `ctl2` | 15.47 / 15.47 | 17.95 / 17.98 | 2.23 / 4.20-4.24 |
  | `r.Shadow.Virtual.Clipmap.UseConservativeCulling 1` (`w1/cons`) | 15.39 | 17.65 | 2.13 / 3.87 |
  | `r.Shadow.Virtual.UseFarShadowCulling 0` (`far0`, `far0b`) | 14.74 / 14.78 | 17.05 / 16.95 | 2.11 / 3.62 |
  | **both (`far0c`)** | **14.58** | **16.47** | **1.92 / 2.44** |
  Side effect of `UseFarShadowCulling 0`: the distance-field far-shadow cascade is not rendered any more (`GPU/DistanceFieldShadows` 0.53 ms -> absent): far shadows come from the VSM clipmap (every primitive casts into it at every distance).
  Both are cvars (preset `overrides/perf60_hwl2.cvars`). `DebugSkip*` switches are NOT shipped (they would leave stale shadows).

## 3. Trees back in the ray-tracing scene (sessions `w1`, `x1`, `y1`, `z1`)
| config (cloud 20 km variant maps, VSM fix on unless noted) | p50 | p95 | note |
|---|---|---|---|
| all tree meshes (leaves + bark, 80 k instances) in, VSM fix off, cloud 20 km default sampling (`w1/ck20`) | 18.88 | 22.09 | |
| same + conservative culling + cloud sample spread + RT culling angle 3 (`w1/ck20all`) | 17.93 | 20.48 | |
| same, RT culling radius 100 m for EVERYTHING (`w1/ck20r100`; also culls facades beyond 100 m) | 17.14 | 19.56 | |
| leaves only (42 k instances), angle 3 (`y1/L3`) | 16.64 | 18.72 | alpha-masked leaves: any-hit shaders |
| leaves only, angle 3, `r.RayTracing.DebugForceOpaque 1` (`y1/L3op`, `L3op2`) | 15.82 / 15.80 | 17.75 / 17.68 | the any-hit cost is ~0.9 ms |
| leaves only, angle 1 (default), force opaque (`y1/L1op`) | 16.08 | 17.90 | |
| no trees, same cvars (`y1/base`, `base2`) | 15.01 / 14.98 | 16.89 / 16.87 | |
| shipped content, LOD0 street-tree leaves still masked, rest opaque (`z1/ship_a/b/c`) | 16.43-16.48 | 18.60-18.63 | fails P2 |
| same with every RT instance opaque (`z1/ship_op`, debug cvar) | 15.82 | 17.73 | |
| **shipped: every leaf mesh opaque in RT (per-asset section flag), `f1/ship_a/b/c`** | **16.08 / 16.03 / 16.11** | **18.03 / 18.03 / 18.05** | |
Shipped form: `perf_apply.py` steps `rt_lite_trees` (leaves + park crown masses in the RT scene, bark / street furniture / parked cars / hinterland / far ground out) and `tree_rt_opaque`
(`StaticMeshEditorSubsystem.enable_section_force_opaque` on the 22 leaf / crown meshes: ray tracing treats the leaf cards as opaque quads; the raster passes keep the alpha mask), plus `r.RayTracing.Culling.Angle 3` in the preset.
The remaining difference to `z1/ship_op` (0.26 ms p50, 0.3 ms p95) is the other masked geometry of the RT scene (street kit / detail tiles), still masked. Forcing all of it opaque (`r.RayTracing.DebugForceOpaque 1`, a debug cvar) would give the extra margin; not shipped.

## 4. Cloud at 20 km (session `w1`)
`cl20` (TracingMaxDistance 20 km, as-found sampling): route 16.63 / 19.85, cloud pass 1.24 ms (4 km control 0.30). The sample count is `max samples * saturate(segment / DistanceToSampleMaxCount)`, DistanceToSampleMaxCount = 15 km:
`r.VolumetricCloud.DistanceToSampleMaxCount 50` spreads the samples over 50 km, so a 20 km segment takes 40 % of the budget with the as-found step length (the as-found 50 km segment used the full budget): `cl20d50` 15.73 / 18.25, cloud 0.58 ms.
Look: t42 sky detail ratio to as-found 1.013 (round 03 4 km: 0.53); `cmp/route_t42_asfound_r03_r04.jpg` (left as found, middle round 03, right round 04).

## 5. Look gate (`LOOK_GATE.md`, reference = the round-03 as-found stills of the same build, `_scratch/perf/r03/before`, no preset, content untouched)
Stills `stills/final_*.jpg` (1920x1080 JPEG of the 3840x2160 PNGs in `_scratch/perf/r04/final`, internal 1920x1080). Whole-still SSIM vs as-found 0.959 (t42) .. 0.987 (S7) (round 03: 0.817 .. 0.979), `cmp/compare_whole_vs_asfound.json`.
- **Round-02 S1 crop 0.9508: below 0.97.** The crop is almost all street-tree canopy now. With opaque leaf cards the GI inside the crown is darker than as found (canopy luma S1 0.912); keeping the LOD0 street trees masked (closer) costs +0.6 ms p50 / +0.9 ms p95 and fails P2 (`z1`). `cmp/S1_crop_r02_asfound_r03_r04.jpg`.
  The round-03 crop set (moved crop, reported only for continuity, NOT the gate): S1 0.9858, S2 0.9932 / 0.9853.
- Disclosed visual differences vs as found: canopy interiors 5-9 % darker at street level (S1, t20), 3-4 % brighter at t42 (trees beyond ~100 m are culled from the RT scene by the 3 deg angle); tree bark is not in the RT scene (no bark in reflections / GI occlusion);
  characters are not in the RT scene (round 03, unchanged: not mirrored by ray-traced reflections); far shadows come from the VSM instead of the distance-field cascade; small RT instances (signage, markings) are culled from reflections beyond ~20-60 m instead of ~57-115 m (angle 3 vs 1).

## 6. Clip
`route_30s.mp4` (14.0 MB, 30.0 s, 1920x1080 output at native 1080p internal, `r.ScreenPercentage 100`, Nanite error 4 = the 8 px of the 4K run halved, fixed 1/60 s step, preset `perf60_hwl2` via cvars; footage only, says nothing about real-time speed). Settings `route_30s_settings.json`.

## 7. Events, mistakes, limits (facts)
- `w1/cons2` is contaminated: my own `make_rtvars.py` commandlet (-nullrhi, CPU only) started at 13:45:50, 5 s before the end of that run's window (7 hitches, a 668 ms frame). Not used; `cons` of the same session is.
- The look probes `_scratch/perf/r04/L3op`, `L1op` used the debug cvar `r.RayTracing.DebugForceOpaque` (every RT instance opaque); the final stills use the shipped per-asset flag (leaves only).
- The `capture` sidecars of stills / clip say `contaminated=true reasons=no-exclusive-lock`: that is the capture class (not a perf number).
- A foreign UnrealEditor (pid 8284, not F's) was reported stuck exiting by the lock at ~14:15; the lock waited, F did not touch it.
- Not merged: `origin/Opus-5.5-Loop-Night-1` has 30+ new commits (traversal camera r13, characters r5-r6); they change the route camera and characters, so this round stays on the round-03 build for comparability. The integrator's map still lacks life / water / combat content (moving traffic / crowd not measured).
- P8 regressed to 1.40 ms (CPU cost of the 42 k leaf instances in the RT scene); P6 (0.7 ms) is not met at 20 km.
