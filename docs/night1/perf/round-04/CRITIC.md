# F perf round 04: critic

> Homage fan game, not official Marvel/Sony/Insomniac.

**Recomputed** (`perf/f1` CSVs, 1800 frames, 4K output, TSR 50 % = 1080p internal):

| run | p50 ms (fps) | p95 ms (fps) | p99 | frames >18.18 | hitches | worst 1 s | in-game counter p95 |
|---|---|---|---|---|---|---|---|
| ship_a | 16.08 (62.2) | 18.03 (55.5) | 18.76 | 63 | 0 | 57.2 fps | **18.21 (54.9)** |
| ship_b | 16.03 (62.4) | 18.03 (55.5) | 18.85 | 71 | 0 | 57.3 fps | **18.23 (54.9)** |
| ship_c | 16.11 (62.1) | 18.05 (55.4) | 18.85 | 69 | 0 | 57.0 fps | **18.28 (54.7)** |

CSV matches the builder; ShadowDepths p95 2.44 ms confirmed.

**Trust:**
- All six `perf_gpu.json` records: exclusive, not contaminated, `perf_valid`.
- **The instruments disagree on p95.** The game's `wh_perf` counter puts it below 55 fps in all three runs, which NOTES.md omits. p95 is not established.
- Not real gameplay: scripted fixed-step route, round-03 build, no traffic or crowd, offscreen.

**Visual regressions** (my measurements, as-found vs final):
- **S1 round-02 crop: SSIM 0.955, fails 0.97.** Canopy luma 68.0→61.8.
- **route_t20:** worst tile ΔY 80; with bark out of ray tracing, the trunk and sidewalk under it are brighter and lose occlusion.
- **route_t42:** 5 % of pixels shift more than 20 in luma; the canopy is 6 % brighter and flatter.
- Clouds and saturation are restored.

**Biggest remaining cost:** the FrameTime−GPUTime gap, 1.40 ms mean and 2.92 ms p95. It makes up 1.29 ms of the 2.41 ms extra in the slowest 10 % of frames. It rose from 0.80 ms (`y1/base`) once the 42 k leaf instances entered ray tracing.

Instruction: merge the leaf, crown and bark cards per city tile into ray-tracing proxies, 1 k instances or fewer. Pass conditions:
- mean FT−GPU of 0.9 ms or less;
- in-game counter p95 of 17.9 ms or less in 3 runs;
- S1 round-02 crop SSIM of 0.97 or more.

**Verdict: APPROACHES TARGET.** p50 of 62 fps holds; p95 sits on the line and the look gate fails.
