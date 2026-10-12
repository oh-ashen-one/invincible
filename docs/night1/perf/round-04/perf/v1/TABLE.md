| config | SP | internal | avg ms (fps) | p50 ms (fps) | p95 ms (fps) | p99 | hitches | GPU ms | RT ms | GT ms | RHI ms | draw calls | cvars |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| warmV | ini | 1920x1080 | 15.40 (64.9) | 15.32 (65.3) | 17.82 (56.1) | 19.53 | 0 | 14.61 | 15.39 | 1.85 | 2.60 | 0 | - |
| st | ini | 1920x1080 | 15.70 (63.7) | 15.61 (64.0) | 18.21 (54.9) | 19.85 | 0 | 14.87 | 15.70 | 1.86 | 2.65 | 0 | - |
| skipdyn | ini | 1920x1080 | 15.23 (65.7) | 15.19 (65.8) | 17.14 (58.4) | 18.04 | 0 | 14.69 | 15.22 | 1.86 | 2.56 | 0 | r.Shadow.Virtual.Cache.DebugSkipDynamicPageInvalidation=1 |
| skiprev | ini | 1920x1080 | 15.43 (64.8) | 15.41 (64.9) | 17.38 (57.5) | 18.39 | 0 | 14.90 | 15.43 | 1.87 | 2.58 | 0 | r.Shadow.Virtual.Cache.DebugSkipRevealedPrimitivesInvalidation=1 |
| diag | ini | 1920x1080 | 16.07 (62.2) | 15.68 (63.8) | 19.48 (51.3) | 28.35 | 10 | 15.07 | 16.07 | 2.03 | 2.96 | 0 | r.Shadow.Virtual.NonNanite.NumPageAreaDiagSlots=16 |
| s2st | ini | 1920x1080 | 14.71 (68.0) | 14.71 (68.0) | 15.60 (64.1) | 15.98 | 0 | 13.83 | 14.71 | 1.39 | 2.30 | 0 | - |
