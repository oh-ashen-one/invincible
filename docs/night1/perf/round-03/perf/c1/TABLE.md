| config | SP | internal | avg ms (fps) | p50 ms (fps) | p95 ms (fps) | p99 | hitches | GPU ms | RT ms | GT ms | RHI ms | draw calls | cvars |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| warmC | ini | 1766x994 | 16.59 (60.3) | 16.49 (60.6) | 19.21 (52.1) | 21.46 | 0 | 15.30 | 16.58 | 2.14 | 3.51 | 0 | - |
| sk0_46 | ini | 1766x994 | 15.11 (66.2) | 15.05 (66.5) | 17.68 (56.6) | 19.52 | 0 | 13.91 | 15.10 | 2.00 | 3.16 | 0 | r.RayTracing.Geometry.SkeletalMeshes=0 |
| sk0_48 | 48 | 1843x1037 | 15.28 (65.5) | 15.21 (65.8) | 17.74 (56.4) | 19.63 | 0 | 14.08 | 15.27 | 1.86 | 2.71 | 0 | r.RayTracing.Geometry.SkeletalMeshes=0 |
| sk0_50 | 50 | 1920x1080 | 15.71 (63.6) | 15.67 (63.8) | 18.12 (55.2) | 20.00 | 0 | 14.49 | 15.71 | 1.86 | 2.77 | 0 | r.RayTracing.Geometry.SkeletalMeshes=0 |
| dg1 | ini | 1766x994 | 16.41 (60.9) | 16.34 (61.2) | 18.88 (53.0) | 20.94 | 0 | 15.22 | 16.41 | 1.92 | 2.86 | 0 | r.RayTracing.DynamicGeometry.MaxUpdatePrimitivesPerFrame=1 |
| sk0_48b | 48 | 1843x1037 | 15.27 (65.5) | 15.20 (65.8) | 17.81 (56.2) | 19.36 | 0 | 14.07 | 15.27 | 1.83 | 2.68 | 0 | r.RayTracing.Geometry.SkeletalMeshes=0 |
| sk0_50b | 50 | 1920x1080 | 15.71 (63.7) | 15.64 (63.9) | 18.29 (54.7) | 20.01 | 0 | 14.45 | 15.70 | 1.86 | 2.73 | 0 | r.RayTracing.Geometry.SkeletalMeshes=0 |
| sk0_46b | ini | 1766x994 | 14.98 (66.8) | 14.90 (67.1) | 17.44 (57.3) | 19.30 | 0 | 13.67 | 14.97 | 1.83 | 3.00 | 0 | r.RayTracing.Geometry.SkeletalMeshes=0 |
