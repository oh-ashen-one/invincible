# Round 02 perf: 3840x2160 output, real gameplay, TSR 50 % (internal 1920x1080)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Real game (`Scripts/run_game.sh`, standalone `-game`, offscreen, true 3840x2160 back buffer, `t.MaxFPS 0`), the P3 traversal hero replaying `tools/perf_ue/scripts/city_swing_avenue.json` with a fixed 1/60 s step (`-benchmark -fps=60`),
perf window = game seconds 22 to 52 (1800 frames), `r.ScreenPercentage 50` (TSR upscale, internal 1920x1080, from the `WH_PERF` json). Both runs were taken under `gpu_slot.sh perf` (exclusive lock; waits for GPU < 15 % for 10 s; sidecars `perf_night/perf_gpu.json`, `perf_midday/perf_gpu.json`). Frame times are wall-clock (CSV profiler `FrameTime`).

| map | avg ms (fps) | best 5 s block ms | p50 | p95 | p99 | GPU avg ms | GPU lock line |
|---|---|---|---|---|---|---|---|
| Look_Midtown_night (night preset, city + night lights + hero) | 47.45 (21.1) | 40.89 | 46.73 | 55.60 | 61.38 | 37.76 | exclusive, util before 0 % / after 0 %, during avg 81.5 % (this run itself), waited 245 s, valid: True |
| Look_Midtown (midday preset, city + hero) | 40.99 (24.4) | 36.50 | 38.89 | 45.81 | 90.80 | 31.61 | exclusive, util before 0 % / after 0 %, during avg 81.1 % (this run itself), waited 241 s, valid: True |

Neither run reaches 16.7 ms (60 fps): 1800 of 1800 frames are above it in both.

## Top GPU passes (ms per frame, window average)

| pass | night | midday |
|---|---|---|
| NaniteVisBuffer | 6.86 | 7.04 |
| LumenScreenProbeGather | 5.41 | 5.42 |
| Unaccounted | 4.43 | 4.64 |
| ShadowDepths | 5.11 | 2.79 |
| VolumetricCloud | 1.80 | 1.57 |
| LumenSceneLighting | 1.62 | 1.42 |
| Basepass | 1.40 | 1.36 |
| Lights | 2.50 | 0.12 |
| LumenSceneUpdate | 0.82 | 0.85 |
| CaptureConvolveSkyEnvMap | 1.01 | 0.64 |
| RenderDeferredLighting | 0.86 | 0.49 |
| VolumetricFog | 0.20 | 0.84 |

## Facts

- Night vs midday, same city and route: +6.5 ms average frame time (+6.2 ms GPU). Passes that differ most: `Lights` 2.50 vs 0.12 ms (the night level has 634 lamps x 2 lights, about 900 storefront lights, 160 screen lights, about 1300 stand-in cars x 2 lights; all unshadowed and distance-culled), `ShadowDepths` 5.11 vs 2.79 ms, `RenderDeferredLighting` 0.86 vs 0.49 ms, `CaptureConvolveSkyEnvMap` 1.01 vs 0.64 ms; `VolumetricFog` is 0.20 vs 0.84 ms. The cause of the ShadowDepths difference was not isolated.
- Compared with round 01 (midday best 5 s block 23.9 to 24.4 ms, GPU shared at 40 to 100 %), the clean midday run is 36.5 ms: the city of P1 round 4 (Nanite visibility buffer about 7 ms, facade materials) and the merged traversal are heavier; the measurements of round 01 are void (contaminated) and this is the new baseline.
- The perf piece F profiles the integrated Manhattan map and will send exact lighting changes with measured savings; no perf optimisation was attempted this round.
