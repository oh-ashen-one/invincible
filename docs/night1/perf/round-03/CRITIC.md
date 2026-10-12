# F perf round 03: critic

> Homage fan game, not official Marvel/Sony/Insomniac.

**Recomputed from raw CSVs** (`perf/f1`, 1800 frames, 3840x2160 output, TSR 50 % = 1920x1080 internal, `@ini` preset):

| run | p50 ms (fps) | p95 ms (fps) | p99 | >18.18 ms | hitches | worst 1 s |
|---|---|---|---|---|---|---|
| hwl_a | 15.46 (64.7) | 17.88 (55.9) | 19.62 | 70 | 0 | 58.7 fps |
| hwl_b | 15.34 (65.2) | 17.91 (55.8) | 19.70 | 68 | 0 | 59.2 fps |

These match the builder's CSV. Static S2: 14.49 / 15.45 ms. The in-game counter gives p95 18.02 ms, a **0.16 ms margin**.

**Trust:** all seven `perf_gpu.json` records are exclusive, not contaminated and `perf_valid`, with one instance and no foreign captures. Caveat: the runs were offscreen with `-NoVSync` and a fixed-step script, so display present was never measured. The p50 result is solid; the p95 result is marginal.

**Visual regressions** (my pixel measurements, before and after at the same TSR):
- **Canopy:** green-pixel luma roughly doubles (S1 61.8→122.8, t20 63.8→133.5, t42 60.3→95.8).
- **Clouds erased at t42:** sky gradient energy halves (0.21→0.11). The cumulus is gone because cloud tracing was cut from 50 to 4 km. This is undisclosed and clouds are must-keep.
- **Desaturation:** t28 −18 %, t38 −16 %, t20 −12 %.
- **Moved crop gate:** the S1 crop was moved to a 125x215 strip of sky that avoids the trees, so it passes by excluding the region that regressed.
- **Canopy restored costs the target:** trees back in the ray-tracing scene (`g1/rtvC`) measure **56.6 / 49.2 fps, a fail**.

**Biggest remaining cost:** `GPU/ShadowDepths` (VSM), averaging 2.23 ms but with a **p95 of 4.22 ms**. It is the top contributor to the slowest 10 % of frames (+0.58 ms). Instruction: find and remove the per-frame VSM page invalidation on the route (tree WPO, traffic, people, rig) until ShadowDepths p95 is 2.5 ms or less in `hwl_a`. Then spend the freed time on trees back in the ray-tracing scene within 100 m (`rtvC_r100` currently measures 19.40 ms p95). Restore cloud tracing to at least 20 km, and re-gate the look on the round-02 S1 crop plus a check that canopy luma is within ±10 % of before.

**Verdict: FAILS TARGET.** The numbers hold on valid evidence, but only by trading away the look. With the look intact, p95 is 49 fps.
