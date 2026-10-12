# F perf round 05: independent critic (Opus 5.5)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

**Verdict: APPROACHES TARGET.**

## Recomputed from the raw CSVs (`perf/g1`, 1800 frames each, 4K output, TSR 50 % = 1920x1080 internal)
| config | p50 ms | p95 ms | p99 | >18.18 ms | hitches |
|---|---|---|---|---|---|
| ship a/b/c | 15.65/15.68/15.72 (63.8 fps) | 17.79/17.76/17.75 (56.3) | 18.8-18.9 | 50-51 | 0 |
| life a/b/c (traffic + crowd) | 17.11-17.13 (58.4) | 19.37-19.61 (51) | 20.5-20.9 | 416-428 | 1 |
| notree | 14.83 | 16.93 | 17.68 | 7 | 0 |

The builder's figures match these to within 0.01 ms.

## Can the numbers be trusted?
- The lock record reads exclusive=true, contaminated=false and perf_valid=true, with GPU utilisation 0 % before the run and one Unreal instance.
- The hero moved, judged from frame times across 5 s blocks (14.7-16.5 ms here, a flat 14.8 in the void runs). The telemetry file was not kept, so this is indirect.
- Caveats:
  - The runs used a fixed step and rendered offscreen.
  - The build is behind the integration branch: traversal r15/r16 and characters r7 are not merged.
  - The p95 margin is only 0.4 ms.
- **The pass holds only because the shipped map has no traffic or crowd.** With the merged life piece on, both lines fail (58.4 / 51 fps). Life adds +1.24 ms of `GPU/Unaccounted`, the game thread goes from 1.8 to 3.5 ms and the RHI thread from 2.7 to 5.2 ms.

## Visual regressions (full-res PNGs, own SSIM)
- **S1 canopy crop:** SSIM against the as-found image is **0.931**, below the 0.97 gate. The builder's repeat noise floor is 0.986, so noise does not explain it. Brightness matches, but the leaf-level GI pattern differs: the deep crown is darker and the speckle harsher.
- **Recess under the elevated structure behind the taxi** (S1, x1700-1850 y540-650): luma is **17.5 as found and 30.0 now (+71 %)**. This light leak was already in the round-04 control (29.3) and nobody caught it.
- S2 and S7 full-frame SSIM are 0.978 and 0.988.

## Biggest remaining frame-time cost
`LumenScreenProbeGather` averages **2.96 ms**, the largest pass. The tree proxies add 0.76 ms of that.

**Instruction:**
1. In the P4 preset, lower `r.Lumen.ScreenProbeGather.DownsampleFactor` / tracing resolution to save at least 1.3 ms.
2. Re-run 3 ship and 3 life runs in one exclusive session.
3. It passes when life p95 is at most 18.0 ms, S1 crop SSIM is at least 0.97 and the recess luma is within ±10 %.

## Scores
Validity 8, shipped numbers 7, life coverage 3, visual fidelity 4, margin 4.
