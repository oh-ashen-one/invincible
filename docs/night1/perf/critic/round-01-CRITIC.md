# F perf, round 01: independent critic

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

**Verdict: FAILS TARGET**: p95 misses, and the look regressed.

## Recomputed from raw CSVs
1800 frames each; 4K output, 1080p internal (TSR 50 %).
- base50 (before): p50 26.45 ms, p95 32.09, p99 34.53.
- **perf60 (the preset): p50 16.44 ms (60.8 fps), p95 19.86 ms (50.4 fps), p99 21.10, max 23.73.** 356 frames are above 18.18 ms. None are above 33 ms.
- perf60 + MaxPixelsPerEdge 6: p50 15.79, p95 19.00.

These match the builder's table. perf60 misses the p95 target of 18.18 ms by 1.7 ms. The p50 of each third of the route is 15.05, 16.19 and **17.96 ms**: the last 10 s miss 60 fps even at p50.

## Trust
All 4 gpu_slot JSONs show `exclusive: true`, `contaminated: false` and one Unreal instance; the health log agrees. Valid, with these caveats:
- Only 6 of 16 runs keep a raw CSV. `f_mpe6_sp42` (907p internal), the only config that reaches 55 fps at p95, has no CSV and no look check.
- The build tested is `1bbd260`, from before the look R2 / water / combat merge. The current HEAD has not been measured.
- `route_30s.mp4` is 1080p with MaxPixelsPerEdge 2, not the measured config.

## Visual regressions (perf60 vs before, crops measured)
Software Lumen (`r.Lumen.HardwareRayTracing 0`) changes the look (whole-frame PSNR 23-25 dB):
- **S2:** the warm lit windows are gone (warm pixels 1.45 % → 0.14 %). The gold glass tower's warm reflections are halved (9.4 % → 4.1 %).
- **S1:** the glass tower's reflections turn into a flat blue sky tone (crop PSNR 15.2 dB, mean luma +17).
- **Route t28:** the facade loses its warm bounce.

MaxPixelsPerEdge 4 alone is clean (SSIM ≥ 0.99).

## Biggest remaining cost
The late-route horizon view. From the first 600 frames to the last 600:
- VolumetricCloud goes from 0.52 to 2.32 ms.
- NaniteVisBuffer goes from 1.32 to 2.88 ms.

**Instruction:** set the VolumetricCloud component's `TracingMaxDistance` from 50 km to ≤15 km. Re-run the route under `gpu_slot perf`. It passes if:
- VolumetricCloud over the last 600 frames is ≤0.7 ms;
- route p95 is ≤18.18 ms;
- the t20 and t28 stills keep SSIM ≥0.98.

Also restore the reflections and lit windows:
- either re-enable hardware ray-traced reflections (`r.Lumen.HardwareRayTracing 1`, `ScreenProbeGather.HardwareRayTracing 0`), budgeting about +4 ms for the ray-tracing scene;
- or reach crop SSIM ≥0.97 on S1 and S2 with software Lumen.
