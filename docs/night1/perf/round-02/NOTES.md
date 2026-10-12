# F perf, round 02: notes (neutral facts, no self-assessment)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. Numbers are from the RUNNING game (`-game`, offscreen, 3840x2160 back buffer) on piece C's
> integrated `/Game/Maps/Manhattan` (golden rig), the 30 s swing route `route_30s_warmup15.json`, window = game seconds 15..45, fixed step (`-benchmark -fps=60`), CSV profiler
> (1800 frames per run), every run inside `gpu_slot.sh perf` (exclusive lock; `perf_gpu.json` next to every session: `util_before` 0 %, `perf_valid: true`, one Unreal instance).
> Build under test = the round-01 build (binaries of integration 1bbd260, Manhattan content of 2026-09-29 22:25); the merge of integration e0ada6c is source-only and NOT rebuilt here.
> Critic instruction of round 01 (`../critic/round-01-CRITIC.md`): (1) cloud `TracingMaxDistance` <= 15 km, route p95 <= 18.18 ms, cloud last 600 frames <= 0.7 ms, t20 / t28 SSIM >= 0.98;
> (2) restore the lit windows / glass reflections: hardware-RT reflections back on, or crop SSIM >= 0.97 on S1 and S2 with software Lumen.

## 1. Cloud tracing distance (session `perf/s1_cloud`, TSR 50 % = 1920x1080 internal, perf60 = software Lumen; control in the same session, twice)
The shader clamps the marched segment to `min(TracingMaxDistance, distance through the layer)` from the layer entry point (engine `VolumetricCloud.usf` 671-675, mode `DistanceFromCloudLayerEntryPoint`), and
the sample count is `SampleCountMax * saturate(segment / DistanceToSampleMaxCount)` with `DistanceToSampleMaxCount` = 15 km (709-711). Measured: **15 km changes little (-0.4 ms on the pass, -0.4 ms route p95)**;
the pass only falls below 15 km, close to proportionally to the distance. Lowering `r.VolumetricCloud.ViewRaySampleMaxCount` from 256 to 96 instead did not move it (`vrs96`, 2.29 ms), so the segment
length, not the count cap, is the lever here.

| TracingMaxDistance | cloud pass, last 600 frames (ms) | first 600 | route p50 | route p95 | p95 last 600 | frames > 18.18 ms | t20 / t28 SSIM vs control run |
|---|---|---|---|---|---|---|---|
| 50 km (as found; control 1 / 2 / 3) | 2.34 / 2.32 / 2.32 | 0.52 | 16.52 / 16.42 / 16.40 | 19.92 / 19.85 / 19.75 | 20.70 | 266 | 0.9973 / 0.9968 (control vs control, noise floor) |
| 15 km (critic's value) | 1.97 | 0.44 | 16.33 | 19.55 | 20.33 | 210 | 0.9963 / 0.9953 |
| 10 km | 1.22 | 0.31 | 15.88 | 18.41 | 18.91 | 82 | - |
| **6 km** | **0.62** | 0.19 | 15.49 | 17.81 | 18.19 | 31 | 0.9954 / 0.9945 |
| **4 km** | **0.41** | 0.13 | 15.33 | 17.62 | 17.98 | 23 | 0.9939 / 0.9946 |
| 3 km | 0.31 | 0.11 | 15.26 | 17.39 | 17.74 | 14 | 0.9934 / 0.9945 |
Cloud pass = CSV column `GPU/VolumetricCloud` (the three cloud passes together: 2.45 -> 0.51 ms at 4 km). NaniteVisBuffer is unchanged (1.34 first / 2.88 last 600): the late-route Nanite rise is a separate cost.
Implementation for the shipped content: `look_presets.json` `clouds.tracing_max_distance` (50 / 40 / 30 for golden / midday / night) -> 4.0 (or the value you choose); F does not own that file.
Local reproduction: `tools/perf_ue2/make_variants.py` (map copies under `/Game/PerfF/Cl<N>/`, the shipped content is untouched) or `perf_content.sh apply cloud` (edits the rigs in place, backed up).

## 2. Glass reflections and lit windows (stills of S1 / S2, 4K, TSR 50 %; reference = the as-found look: all Epic-tier defaults, hardware-RT Lumen, Nanite error 1 px; fresh PNGs of this round)
Round 01 dropped hardware-RT Lumen (`r.Lumen.HardwareRayTracing 0`). Which part lost the look? Software tracing cvars do nothing; **the hardware-RT REFLECTIONS alone restore it**
(`HardwareRayTracing 1`, `ScreenProbeGather.HardwareRayTracing 0`, `Reflections.HardwareRayTracing 1` = software GI + hardware reflections). Crops are the round-01 critic's areas
(`tools/perf_ue2/crop_ssim.py`, 8x8 box SSIM on luma of the 1920x1080 downsample; raw `refl/crop_ssim_batch1.json`, side-by-sides `refl/sbs/`). Two runs of the same config differ by SSIM 0.997 (still noise floor).
| config (all 4K, TSR 50 %, perf60 unless noted) | S1 glass tower SSIM | S2 lit windows SSIM | S2 gold tower SSIM | warm px S2 windows % (before -> test) | warm px S2 gold % |
|---|---|---|---|---|---|
| perf60 (software Lumen, as round 01) | 0.595 | 0.967 | 0.766 | 4.8 -> 2.0 | 41.6 -> 25.3 |
| + `r.Lumen.DiffuseIndirect.SurfaceBias 100` | - | 0.970 | 0.762 | 4.8 -> 2.2 | 41.6 -> 25.2 |
| + `r.Lumen.Reflections.TraceMeshSDFs 0` | 0.594 | 0.966 | 0.766 | 4.8 -> 2.0 | 41.6 -> 25.2 |
| + `r.Lumen.TraceMeshSDFs 0` | - | 0.968 | 0.764 | 4.8 -> 2.0 | 41.6 -> 24.7 |
| + `r.Lumen.Reflections.SampleSceneColorAtHit 2` | - | 0.967 | 0.761 | 4.8 -> 2.0 | 41.6 -> 25.4 |
| HW-RT reflections + software GI, full RT scene | 0.958 | 0.992 | 0.967 | 4.8 -> 4.7 | 41.6 -> 37.8 |
| same, RT-lite scene (RT1: hinterland, trees, far ground out) | 0.960 | 0.991 | 0.966 | 4.8 -> 4.6 | 41.6 -> 37.5 |
| RT2: also Nanite street kit + detail tiles out | 0.961 | 0.991 | 0.963 | 4.8 -> 4.6 | 41.6 -> 37.5 |
| RT3: also signage, markings, generic (glass towers) out | 0.962 | 0.990 | 0.906 | 4.8 -> 4.6 | 41.6 -> 37.5 |
| RT1 + `Reflections.HardwareRayTracing.FarField 0` | - | 0.991 | 0.967 | 4.8 -> 4.6 | 41.6 -> 37.1 |
| RT1 + `Reflections.DownsampleFactor 2` | 0.939 | 0.976 | 0.957 | 4.8 -> 2.2 | 41.6 -> 37.4 |
| RT1 + `Reflections.MaxRoughnessToTrace 0.25` | - | 0.991 | 0.950 | 4.8 -> 4.5 | 41.6 -> 37.2 |
Reading: none of the five software-tracing cvars moves the crops (the S1 glass tower stays at SSIM 0.59: reflections of a flat sky tone instead of the soft, warm, building-filled ones). With hardware-RT reflections the warm-pixel
fractions return (S2 windows 4.8 -> 4.6 %, gold tower 41.6 -> 37.5 %) and the glass tower reads like the reference (`refl/sbs/hybrt_S1_glass.jpg`). What is left (SSIM 0.96-0.99, not 1.0) is software GI, Nanite error 4 and the cheap cvar set of perf60.
`DownsampleFactor 2` loses the windows again (warm 4.6 -> 2.2 %) and `MaxRoughnessToTrace 0.25` costs the gold tower: not adopted. RT3 loses the gold glass tower's reflections: not adopted.
The round-01 critic's alternative ("crop SSIM >= 0.97 with software Lumen") is not reachable with any cvar tried: S1 crop 0.59.

## 3. What hardware-RT reflections cost (route, TSR 50 %, p50 / p95 ms; a control or the software twin is in the same session)
| session | config | p50 | p95 | note |
|---|---|---|---|---|
| s1 | software Lumen, cloud 6 km (`cl6`) | 15.49 | 17.81 | |
| s1 | HW-RT reflections, FULL ray-tracing scene, cloud 6 km (`hyb_cl6`) | 19.58 | 21.80 | +4.1 ms |
| s2 | software Lumen, cloud 4 km (`sw4`) | 15.30 | 17.53 | |
| s2 | HW-RT reflections, RT-lite scene, cloud 4 km (`f4`) | 17.26 | 19.44 | **+1.96 ms**: RT-lite (hinterland, trees, far ground out of the RT scene) is worth 2.2 ms |
| s2 | + `FarField 0` / `DownsampleFactor 2` / `MaxRoughnessToTrace 0.25` | 17.29 / 16.92 / 17.12 | 19.31 / 19.11 / 19.31 | look cost of the last two: section 2 |
| s3 | RT2 / RT3 scene (mpe 6, TSR 50) vs RT1 | 16.58 / 16.42 vs 16.63 | 18.61 / 18.53 vs 19.23 (cold first run) | RT2 = no gain; RT3 -0.2 ms but loses the gold tower |
The `RayTracingScene` GPU pass is 1.56 ms in the moving route and 0.03 ms in the static S2 view (static S2: hardware reflections cost +0.5 ms, `perf/s3_probe/s2_f4m6rt3` vs `s2_sw4`), i.e. the remaining cost belongs to the moving / dynamic geometry
of the route, not to the static city.

## 4. Route and static-view frame times (3840x2160 OUTPUT, session `perf/s4_official`, one exclusive lock session, `perf_valid: true`, GPU 0 % before, one Unreal instance)
Internal (pre-TSR) resolution is disclosed per row (`wh_perf.internal_w/h`). "SW" = software Lumen (perf60 as round 01) + cloud 4 km. "HWR" = `perf60_hwrefl` = perf60 + Nanite error 6 + hardware-RT reflections with software GI (section 2)
+ RT-lite ray-tracing scene (hinterland, trees, far ground out) + cloud 4 km. The first config of the session (`warm4`) is cold and is not evidence. Hitch = frame > 25 ms and > 2x the median.
| config | TSR | internal | p50 ms (fps) | p95 ms (fps) | hitches | P1 (<= 16.67) | P2 (<= 18.18, 0 hitches) |
|---|---|---|---|---|---|---|---|
| SW `sw4_50` | 50 % | 1920x1080 | 15.32 (65.3) | 17.48 (57.2) | 0 | pass | pass |
| SW `sw4_58` | 58 % | 2227x1253 | 16.67 (60.0) | 18.93 (52.8) | 0 | pass (16.67) | fail |
| HWR `b50` | 50 % | 1920x1080 | 16.75 (59.7) | 18.95 (52.8) | 0 | fail by 0.08 | fail by 0.77 |
| **HWR `fin46_a` / `fin46_b`** | 46 % | 1766x994 | **16.01 (62.5) / 16.02 (62.4)** | **18.05 (55.4) / 18.06 (55.4)** | 0 / 0 | **pass** | **pass (margin 0.12)** |
| HWR `fin44` | 44 % | 1690x950 | 15.65 (63.9) | 17.69 (56.5) | 0 | pass | pass |
| static S2, HWR `s2_fin46` | 46 % | 1766x994 | 13.20 (75.8) | 13.98 (71.5) | 0 | P3 pass (<= 18.2) | |
Same session, ray-tracing probes on HWR TSR 50 % (`b50` 16.75 / 18.95): `RayTracing.Scene.BuildMode 0` 16.77 / 18.81, `RayTracing.Culling 0` 17.12 / 19.18 (worse), `Geometry.SkeletalMeshes.LODBias 3` 16.83 / 19.20 (no gain),
`Geometry.SkeletalMeshes 0` 15.28 / 21.83 (p50 -1.5 ms: skeletal meshes in the ray-tracing scene cost 1.5 ms; the run has 37 hitch frames, so its p95 is not usable).

## 5. Visual check of the recommended preset (`perf60_hwrefl` at TSR 46 %, RT-lite scene, cloud 4 km) against the as-found look (P4; `stills/`, `cmp/after_vs_before/`)
| still (4K) | SSIM luma vs as-found | PSNR dB | mean Y as-found -> now | near-black < 10 % | clipped % | round 01 (software Lumen, TSR 50) SSIM |
|---|---|---|---|---|---|---|
| view_S1 | 0.9638 | 32.3 | 83.1 -> 81.6 | 0.37 -> 0.48 | 2.40 -> 2.41 | 0.9278 |
| view_S2 | 0.9635 | 30.6 | 97.9 -> 95.2 | 0.01 -> 0.02 | 1.83 -> 1.81 | 0.8952 |
| view_S7 | 0.9799 | 31.8 | 68.9 -> 68.3 | 21.13 -> 21.75 | 8.73 -> 8.73 | 0.9728 |
| route_t20 | 0.9462 | 28.9 | 67.2 -> 63.1 | 2.05 -> 1.76 | 1.36 -> 1.38 | 0.9064 |
| route_t28 | 0.9401 | 28.5 | 68.5 -> 64.6 | 0.08 -> 0.04 | 2.89 -> 2.88 | 0.8969 |
Crops of the round-01 critic (`cmp/crop_final_vs_before.json`, side-by-sides `cmp/crop_sbs/`): S1 glass tower SSIM **0.921** (software Lumen: 0.596), S2 lit windows **0.986** (0.967), S2 gold tower **0.947** (0.766); warm pixels S2 windows 4.8 -> 4.5 %,
gold tower 41.6 -> 37.1 % (software: 2.0 / 25.3 %). Luma lines (near-black, clipped) are unchanged within 0.7 points; mean Y is 0.6-4.1 lower (software GI). The S1 / S2 references are fresh PNGs of this round (`refl1/before`);
the route stills are fixed-step frames but the two runs are not pixel-locked, so route SSIM is indicative (two identical runs: 0.997).
Late-route horizon (t38 / t42, cloud 4 km): stills SSIM 0.9963 / 0.9968 vs the 50 km control, **but the distant cloud wisps at the horizon are gone** (control has pink-lit wisps top-left, the 3 / 4 / 6 km stills have a plain sky gradient there;
`cloud/cmp_cloudhz/cl4/route_t42_sbs.jpg`). SSIM does not see it (small area). It is the visible price of the cloud pass going 2.3 -> 0.4 ms; 10 km (1.22 ms) does not meet the 0.7 ms line and I did not capture its horizon.

## 6. Events and limits of this round (facts)
- Build under test is the round-01 build (binaries 1bbd260, Manhattan content 22:25). Integration e0ada6c (look R2, water, combat, life) is merged at the source level only; nothing was rebuilt or re-measured on it.
- `look_presets.json` / `build_look.py` (cloud distance), and the city / manhattan build scripts (RT-lite component flags) are not F's files: F's changes are local content variants (`make_variants.py`) and `perf_apply.py` steps `cloud`, `rt_lite`. Nothing under `Content/` is committed.
- Lock: every perf session waited 12-26 min (up to 5 concurrent capture holders of other agents); the perf ticket's 30 min wait timeout (exit 75) hit once (session 5) and the queue re-queued it at the back.
- 2026-09-30 06:54: a 1080p movie launch hung 15 min with 0.1 % CPU (main thread in a macOS ViewBridge XPC wait, before the first frame). SIGTERM did not end it; it was SIGKILLed while idle (not rendering; it exited in 2 s). `route_movie.sh` now has a log-idle watchdog + one retry.
- From ~06:55 two engines of other agents (pids 17555 and 17831, `?E` = stuck exiting; a `CrashReportClient` of pid 3980 at 100 % CPU for > 1 h) kept the GPU at 100 %; `gpu_slot.sh` correctly refused every new launch (unhealthy-wait). F did not touch them. Consequence: **no 1080p60 route clip
  and no session 5 (street people out of the ray-tracing scene)** this round; both tickets were cancelled at 07:55. `perf_apply.py` `cloud` / `rt_lite` (and the per-file backup in `perf_content.sh`) were written but not run for the same reason: unverified.
