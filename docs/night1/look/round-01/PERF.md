# P4 perf: 3840x2160 output, real gameplay (round 01)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

## Summary (numbers only)

Deterministic route, 3840x2160 output, real gameplay, GPU shared with other agents (see below). "Best 5 s block" = the fastest 5 s stretch of the 30 s window (other processes can only add time).

- **tsr50** (internal 1920x1080): best 5 s block 23.9 to 24.4 ms (41 to 42 fps); whole-window average 24.9 to 29.9 ms over 2 runs
- **tsr67** (internal 2573x1447): best 5 s block 28.5 to 28.8 ms (35 to 35 fps); whole-window average 30.1 to 31.8 ms over 2 runs
- **native100** (internal 3840x2160): best 5 s block 40.9 to 43.0 ms (23 to 24 fps); whole-window average 43.3 to 45.6 ms over 2 runs
- No config reached 16.7 ms (60 fps) in any 5 s block.

## How it was measured

Real game (`Scripts/run_game.sh`: standalone `-game`, offscreen, true 3840x2160 back buffer, `t.MaxFPS 0`, no vsync), map `/Game/Tests/Look/Look_Midtown` (midday preset, city + traversal boxes),
the P3 traversal hero (real hero mesh, C++ animation) replaying `tools/perf_ue/scripts/city_swing_avenue.json`: 14 s standing warm-up, then sprint, jump and a continuous swing chain up the avenue.
Main table: `run_perf.py --fixed-step` = `-benchmark -fps=60`, a fixed 1/60 s game step, so the hero flies the SAME route in every config (free-running, the swing rhythm depends on the frame time and the hero
ends up on a different, shorter route in every run: see the second table). Frame times are wall-clock either way (CSV profiler `FrameTime`, identical to the in-game `WH_PERF` json `avg_ms`).
Perf window: game seconds 22 to 52 (30 s, swinging the whole time). Internal resolution = the `WH_PERF` json (`r.ScreenPercentage` set explicitly, TSR upscale).
A "hitch" = a frame slower than 25 ms and slower than twice the run median. GPU utilisation is `ioreg -r -d 1 -c IOAccelerator | grep "Device Utilization"` (3 samples before the run, plus a 1 Hz mean during it).

## READ THIS FIRST: the GPU is shared

Other agents' Unreal editors, game runs, Blender and Chrome used the GPU during the whole session: device utilisation before a run was 40 to 100 % for most of it. Identical builds then differ by up to 2x between repeats
(`perf_free_*`, `perf_variants`). Each run's `result.json` carries `contaminated` (utilisation before the run >= 10 % or another busy Unreal / Blender / Chrome process) and the reason;
a run is only a clean measurement of this machine when the last column says so. `run_perf.py --wait-idle N` waits for an idle GPU before each run.

## Frame times, three resolution configs, deterministic route (fixed step), two repeats

| run | config | output | internal (pre-TSR) | avg ms (fps) | best 5 s block ms | p50 | p95 | p99 | max | hitches | GPU ms (avg) | GPU util % before the run (3 samples) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| perf_fixed_a | tsr50 (SP 50) | 3840x2160 | 1920x1080 | 29.9 (33.4) | 23.9 | 25.2 | 45.7 | 52.0 | 63.7 | 26 | 27.8 | 100/100/100 (during: mean 97) |
| perf_fixed_a | tsr67 (SP 67) | 3840x2160 | 2573x1447 | 30.1 (33.3) | 28.5 | 29.7 | 35.5 | 44.4 | 57.8 | 0 | 27.3 | 99/100/99 (during: mean 99) |
| perf_fixed_a | native100 (SP 100) | 3840x2160 | 3840x2160 | 45.6 (21.9) | 43.0 | 45.1 | 52.8 | 58.1 | 77.6 | 0 | 42.2 | 44/49/43 (during: mean 95) |
| perf_fixed_b | tsr50 (SP 50) | 3840x2160 | 1920x1080 | 24.9 (40.2) | 24.4 | 24.2 | 30.7 | 35.4 | 56.5 | 1 | 22.4 | 50/49/51 (during: mean 91) |
| perf_fixed_b | tsr67 (SP 67) | 3840x2160 | 2573x1447 | 31.8 (31.5) | 28.8 | 29.8 | 36.5 | 44.2 | 1051.7 | 11 | 28.1 | 47/46/46 (during: mean 91) |
| perf_fixed_b | native100 (SP 100) | 3840x2160 | 3840x2160 | 43.3 (23.1) | 40.9 | 43.1 | 49.2 | 52.6 | 75.9 | 0 | 40.7 | 100/100/100 (during: mean 97) |

For comparison, free-running (real-time step) repeats of the same three configs. The hero route differs per run (it can stall on a wall for several seconds) and the GPU load of other agents changed between runs:

| run | config | output | internal (pre-TSR) | avg ms (fps) | best 5 s block ms | p50 | p95 | p99 | max | hitches | GPU ms (avg) | GPU util % before the run (3 samples) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| perf_free_a | tsr50 (SP 50) | 3840x2160 | 1920x1080 | 26.5 (37.8) | 20.6 | 21.5 | 50.1 | 58.0 | 77.5 | 133 | 24.2 | 92/92/92 (during: mean 79) |
| perf_free_a | tsr67 (SP 67) | 3840x2160 | 2573x1447 | 44.3 (22.6) | 30.9 | 45.5 | 65.1 | 75.8 | 109.6 | 1 | 40.4 | 0/35/35 (during: mean 86) |
| perf_free_a | native100 (SP 100) | 3840x2160 | 3840x2160 | 49.6 (20.2) | 42.9 | 45.5 | 74.9 | 83.0 | 100.1 | 2 | 46.4 | 0/19/17 (during: mean 88) |
| perf_free_b | tsr50 (SP 50) | 3840x2160 | 1920x1080 | 23.9 (41.9) | 23.3 | 23.6 | 29.1 | 37.3 | 65.3 | 7 | 22.5 | 47/100/100 (during: mean 97) |
| perf_free_b | tsr67 (SP 67) | 3840x2160 | 2573x1447 | 31.8 (31.4) | 29.9 | 31.2 | 37.6 | 42.8 | 199.6 | 3 | 28.9 | 0/0/0 (during: mean 78) |
| perf_free_b | native100 (SP 100) | 3840x2160 | 3840x2160 | 53.4 (18.7) | 44.6 | 47.5 | 81.6 | 90.3 | 94.8 | 0 | 50.2 | 0/35/51 (during: mean 86) |
| perf_free_c | tsr50 (SP 50) | 3840x2160 | 1920x1080 | 23.5 (42.6) | 22.4 | 23.4 | 28.3 | 30.5 | 64.8 | 1 | 22.1 | 5/22/20 (during: mean 81) |
| perf_free_c | tsr67 (SP 67) | 3840x2160 | 2573x1447 | 29.4 (34.0) | 28.5 | 29.2 | 35.0 | 38.2 | 42.4 | 0 | 27.5 | 0/18/2 (during: mean 86) |
| perf_free_c | native100 (SP 100) | 3840x2160 | 3840x2160 | 46.0 (21.8) | 41.7 | 45.5 | 55.3 | 61.7 | 66.8 | 0 | 42.5 | 17/47/16 (during: mean 96) |

## What the hero does inside the perf window (perf_fixed_a / tsr50 telemetry, hero time 22 s to 52 s)

1801 frames; modes {'air': '40 %', 'swing': '60 %'}; travels from y = 60 m to y = -532 m (north = -Y); speed mean 27.6 m/s, max 42.9 m/s; height above the floor 0.8 to 123.2 m.

## Top GPU costs during the swing chain (CSV `GPU/*` stats, ms per frame, averaged over the window)

Same GPU pass timers that `stat gpu` shows (`-csvGpuStats`). Absolute values inherit the contamination above; the ranking and the shares are the useful part.

**perf_fixed_a / tsr50, internal 1920x1080: GPU 27.8 ms per frame, render thread 29.9 ms, game thread 1.7 ms**

| pass | ms | share of GPU time |
|---|---|---|
| LumenScreenProbeGather | 4.68 | 17 % |
| Unaccounted | 3.31 | 12 % |
| ShadowDepths | 2.89 | 10 % |
| Basepass | 2.64 | 9 % |
| LumenSceneLighting | 1.29 | 5 % |
| DistanceFieldShadows | 1.13 | 4 % |
| RayTracingScene | 1.11 | 4 % |
| VolumetricCloud | 1.11 | 4 % |
| Postprocessing | 0.90 | 3 % |
| Prepass | 0.84 | 3 % |
| LumenSceneUpdate | 0.77 | 3 % |
| VolumetricFog | 0.76 | 3 % |

**perf_fixed_a / tsr67, internal 2573x1447: GPU 27.3 ms per frame, render thread 30.1 ms, game thread 1.8 ms**

| pass | ms | share of GPU time |
|---|---|---|
| LumenScreenProbeGather | 5.96 | 22 % |
| Unaccounted | 3.53 | 13 % |
| Basepass | 3.10 | 11 % |
| ShadowDepths | 2.75 | 10 % |
| VolumetricFog | 1.14 | 4 % |
| LumenSceneLighting | 1.11 | 4 % |
| VolumetricCloud | 1.08 | 4 % |
| DistanceFieldShadows | 0.97 | 4 % |
| RenderDeferredLighting | 0.71 | 3 % |
| CaptureConvolveSkyEnvMap | 0.66 | 2 % |
| ShadowProjection | 0.65 | 2 % |
| LumenSceneUpdate | 0.64 | 2 % |

**perf_fixed_a / native100, internal 3840x2160: GPU 42.2 ms per frame, render thread 45.6 ms, game thread 1.9 ms**

| pass | ms | share of GPU time |
|---|---|---|
| LumenScreenProbeGather | 11.24 | 27 % |
| Unaccounted | 5.85 | 14 % |
| Basepass | 4.53 | 11 % |
| ShadowDepths | 3.69 | 9 % |
| VolumetricFog | 2.44 | 6 % |
| ShadowProjection | 1.29 | 3 % |
| VolumetricCloud | 1.27 | 3 % |
| RenderDeferredLighting | 1.24 | 3 % |
| LumenSceneLighting | 1.17 | 3 % |
| DistanceFieldShadows | 1.05 | 2 % |
| LumenReflections | 0.96 | 2 % |
| LumenSceneUpdate | 0.74 | 2 % |

## Heaviest view (static shot cameras S1..S8, midday preset, 3840x2160 output, TSR 50 %, window 14 s to 24 s; measured just before the sky light cloud ambient occlusion was switched off, 2 passes, GPU shared)

| view | pass | avg ms (CSV) | GPU ms (avg) | GPU util % before |
|---|---|---|---|---|
| S1 | pass1 | 47.4 | 35.9 | 99/100/100 |
| S2 | pass1 | 66.8 | 60.7 | 99/99/90 |
| S3 | pass1 | 41.7 | 33.1 | 100/99/100 |
| S4 | pass1 | 69.8 | 55.3 | 52/54/51 |
| S5 | pass1 | 38.2 | 30.6 | 99/99/99 |
| S6 | pass1 | 49.6 | 44.2 | 51/50/52 |
| S7 | pass1 | 28.8 | 26.3 | 98/91/92 |
| S8 | pass1 | 36.5 | 32.2 | 41/41/40 |
| S1 | pass2 | 31.1 | 28.7 | 42/40/41 |
| S2 | pass2 | 49.9 | 45.7 | 47/49/41 |
| S3 | pass2 | 26.9 | 24.2 | 100/100/100 |
| S4 | pass2 | 30.9 | 29.1 | 43/43/42 |
| S5 | pass2 | 31.1 | 28.8 | 49/45/47 |
| S6 | pass2 | 31.0 | 28.4 | 49/46/52 |
| S7 | pass2 | 29.3 | 26.7 | 50/91/100 |
| S8 | pass2 | 56.9 | 52.0 | 56/55/54 |

Heaviest view by the lower GPU time of the two passes: **S2** (45.7 ms GPU at 1920x1080 internal). Its top GPU passes:

| pass | ms | share |
|---|---|---|
| Unaccounted | 7.09 | 16 % |
| LumenScreenProbeGather | 6.31 | 14 % |
| Basepass | 4.52 | 10 % |
| ShadowDepths | 4.27 | 9 % |
| Postprocessing | 2.29 | 5 % |
| Prepass | 2.07 | 5 % |
| DistanceFieldShadows | 2.03 | 4 % |
| NaniteVisBuffer | 1.77 | 4 % |
| LumenSceneLighting | 1.64 | 4 % |
| RenderDeferredLighting | 1.50 | 3 % |
| VolumetricCloudShadow | 1.21 | 3 % |
| LensFlare | 1.14 | 2 % |

## Console-variable variants at TSR 50 %, deterministic route (what each feature costs)

Same route every time (fixed step), so the route position is the same in block k of every row: compare blocks, not only averages. The GPU was shared while these ran (last column;
the second half of `base_b` and the first half of `no_dfshadow` show a burst of other load: 34 to 40 ms blocks). Differences under about 2 ms are inside the run-to-run spread.

| variant | cvars | avg ms | GPU ms | 5 s block averages, in route order (ms) | GPU util % before |
|---|---|---|---|---|---|
| base_a | (none) | 23.8 | 22.3 | 25.0 24.9 24.3 23.5 24.5 23.7 22.7 23.3 | 14/0/0 |
| sw_lumen | r.Lumen.HardwareRayTracing=0 | 22.3 | 21.6 | 24.1 23.0 22.9 21.8 22.2 22.4 21.6 20.6 | 56/58/58 |
| no_volfog | r.VolumetricFog=0 | 22.8 | 21.4 | 24.1 24.0 23.5 22.3 23.1 22.8 21.7 21.9 | 29/25/25 |
| no_clouds | r.VolumetricCloud=0 | 22.8 | 21.2 | 26.5 26.1 25.2 23.6 22.6 20.8 20.5 19.9 | 20/25/25 |
| no_flare_mblur | r.LensFlareQuality=0 r.MotionBlurQuality=0 | 23.3 | 21.6 | 25.1 25.2 25.2 22.8 23.3 22.5 21.9 22.5 | 21/30/19 |
| no_dfshadow | r.DistanceFieldShadowing=0 | 30.7 | 28.5 | 38.1 40.7 39.3 39.0 37.8 25.6 23.0 22.5 21.6 33.2 38.0 | 8/28/19 |
| probe32 | r.Lumen.ScreenProbeGather.DownsampleFactor=32 | 23.0 | 21.5 | 24.3 24.1 23.5 22.5 23.4 23.1 21.8 22.6 | 100/100/100 |
| base_b | (none) | 28.0 | 25.7 | 24.5 23.9 23.9 22.6 27.0 35.1 34.2 33.9 33.8 30.2 | 5/6/6 |

## Commands

```
unreal/WebHomage/Scripts/build_editor.sh                        # C++ (once)
tools/perf_ue/rebuild_city.sh; tools/perf_ue/rebuild_look.sh    # content, see HANDOFF.md
tools/perf_ue/run_perf.py --out docs/night1/look/round-01/perf_a --window 22:52 --wait-idle 40      # tsr50, tsr67, native100
tools/perf_ue/sweep_views.sh docs/night1/look/round-01/perf_views midday 2                          # heaviest view
```

Exact command line of every run: `command` in each `<run>/<config>/result.json` and `run.txt`. Per-frame CSVs: `<run>/<config>/csv.csv`; hero telemetry: `trav_telemetry.csv`.
