# F perf round 02: independent critic (Opus 5.5)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

## Recomputed from raw CSVs (1800 frames, 4K output, route 15..45 s)
| run | internal | p50 ms | p95 ms | p99 | hitches | GPU p50 |
|---|---|---|---|---|---|---|
| fin46_a | 1766x994 | 16.01 (62.5 fps) | 18.05 (55.4) | 19.08 | 0 | 13.14 |
| fin46_b | 1766x994 | 16.02 | 18.06 | 19.08 | 0 | 13.13 |
| b50 | 1920x1080 | 16.75 | 18.95 | 20.48 | 0 | 15.39 |
| sw4_50 | 1920x1080 | 15.32 | 17.48 | 18.68 | 0 | 14.46 |
| s2_fin46 | 1766x994 | 13.20 | 13.98 | 14.46 | 0 | 12.56 |

The builder's numbers reproduce to 0.01 ms. The scene captures are off.

## Trust
- Lock: exclusive, util 0 %, not contaminated. `instances_max_during` is 2, but health.log shows ue=1 for the whole session, so it is probably the run's own launch/exit overlap.
- **Not the integrated map.** The runs used the round-01 binaries on a local copy, `/Game/PerfF/Cl4RT`. Integration e0ada6c (water, combat, life) was never built. Cloud 4 km and RT-lite are not in shipped content. The p95 margin is 0.12 ms.

## Visual regressions (my box-SSIM, luma)
- The builder's own crop gate fails: S1 glass 0.921, S2 gold 0.947, threshold 0.97.
- Route stills are about 6 % darker (Y 67.7->63.5, 69.2->65.4). Trees at t28 are duller.
- Horizon clouds are gone at t42: pink sky pixels fall from 11.9 % to 2.1 % (`cloud/cmp_cloudhz/cl4/route_t42_sbs.jpg`).

## Biggest remaining cost
The preset is no longer GPU-bound. **FrameTime - GPUTime = 2.89 ms per frame**, against 0.81 ms with software Lumen. Going from 50 % to 46 % saved 2.3 ms of GPU time but only 0.75 ms of frame time. The render thread waits 12.0 ms in `EventWait/Visibility`.

Instruction: take an Insights trace (`-trace=cpu,gpu,frame,rhicommands`) of fin46 under `gpu_slot.sh perf`. Find and remove the serialisation between the CPU and GPU that the hardware-RT reflection path adds: TLAS gather, skeletal BLAS refit (sk0: -1.5 ms) or occlusion readback. Pass line: FrameTime - GPUTime ≤ 1.0 ms.

## Verdict: APPROACHES TARGET
The numbers hold under a valid lock, but on a stale, non-integrated map copy, and the no-visual-regression condition fails.
