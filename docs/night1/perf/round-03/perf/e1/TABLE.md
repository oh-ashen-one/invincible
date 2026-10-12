| config | SP | internal | avg ms (fps) | p50 ms (fps) | p95 ms (fps) | p99 | hitches | GPU ms | RT ms | GT ms | RHI ms | draw calls | cvars |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| warmE | ini | 1843x1037 | 15.26 (65.5) | 15.17 (65.9) | 17.72 (56.4) | 19.67 | 0 | 14.19 | 15.25 | 1.83 | 2.66 | 0 | - |
| gi48 | ini | 1843x1037 | 15.20 (65.8) | 15.10 (66.2) | 17.55 (57.0) | 19.31 | 0 | 14.44 | 15.20 | 1.85 | 2.53 | 0 | r.Lumen.ScreenProbeGather.HardwareRayTracing=1 |
| gi50 | 50 | 1920x1080 | 15.68 (63.8) | 15.60 (64.1) | 18.15 (55.1) | 19.91 | 0 | 14.90 | 15.68 | 1.86 | 2.52 | 0 | r.Lumen.ScreenProbeGather.HardwareRayTracing=1 |
| m8_50 | 50 | 1920x1080 | 15.46 (64.7) | 15.40 (64.9) | 17.93 (55.8) | 19.96 | 0 | 14.22 | 15.45 | 1.85 | 2.69 | 0 | r.Nanite.MaxPixelsPerEdge=8 |
| m8_48 | ini | 1843x1037 | 15.17 (65.9) | 15.13 (66.1) | 17.54 (57.0) | 19.49 | 0 | 13.92 | 15.17 | 1.83 | 2.75 | 0 | r.Nanite.MaxPixelsPerEdge=8 |
| gi50m8 | 50 | 1920x1080 | 15.52 (64.4) | 15.42 (64.9) | 18.03 (55.5) | 19.73 | 0 | 14.72 | 15.52 | 1.84 | 2.59 | 0 | r.Lumen.ScreenProbeGather.HardwareRayTracing=1 r.Nanite.MaxPixelsPerEdge=8 |
| ship_c | ini | 1843x1037 | 15.28 (65.4) | 15.21 (65.7) | 17.64 (56.7) | 19.56 | 0 | 14.05 | 15.28 | 1.83 | 2.70 | 0 | - |
| gi46 | 46 | 1766x994 | 14.91 (67.1) | 14.81 (67.5) | 17.41 (57.4) | 19.24 | 0 | 14.12 | 14.90 | 1.83 | 2.57 | 0 | r.Lumen.ScreenProbeGather.HardwareRayTracing=1 |
