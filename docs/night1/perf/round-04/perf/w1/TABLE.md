| config | SP | internal | avg ms (fps) | p50 ms (fps) | p95 ms (fps) | p99 | hitches | GPU ms | RT ms | GT ms | RHI ms | draw calls | cvars |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| warmW | ini | 1920x1080 | 15.54 (64.3) | 15.46 (64.7) | 18.04 (55.4) | 19.63 | 0 | 14.73 | 15.54 | 1.86 | 2.60 | 0 | - |
| ctl | ini | 1920x1080 | 15.52 (64.5) | 15.40 (64.9) | 18.05 (55.4) | 19.71 | 0 | 15.00 | 15.51 | 1.86 | 2.59 | 0 | - |
| cons | ini | 1920x1080 | 15.43 (64.8) | 15.39 (65.0) | 17.65 (56.6) | 18.67 | 0 | 14.91 | 15.42 | 1.86 | 2.55 | 0 | r.Shadow.Virtual.Clipmap.UseConservativeCulling=1 |
| cl20 | ini | 1920x1080 | 16.73 (59.8) | 16.63 (60.1) | 19.85 (50.4) | 21.26 | 0 | 15.94 | 16.72 | 1.85 | 2.58 | 0 | - |
| cl20d50 | ini | 1920x1080 | 15.81 (63.2) | 15.73 (63.6) | 18.25 (54.8) | 19.72 | 0 | 15.02 | 15.81 | 1.86 | 2.56 | 0 | r.VolumetricCloud.DistanceToSampleMaxCount=50 |
| ck20 | ini | 1920x1080 | 18.90 (52.9) | 18.88 (53.0) | 22.09 (45.3) | 23.63 | 0 | 17.29 | 18.90 | 1.93 | 2.69 | 0 | - |
| ck20all | ini | 1920x1080 | 17.91 (55.8) | 17.93 (55.8) | 20.48 (48.8) | 21.73 | 0 | 16.17 | 17.90 | 1.97 | 2.70 | 0 | r.Shadow.Virtual.Clipmap.UseConservativeCulling=1 r.VolumetricCloud.DistanceToSampleMaxCount=50 r.RayTracing.Culling.Angle=3 |
| ck20r100 | ini | 1920x1080 | 17.13 (58.4) | 17.14 (58.3) | 19.56 (51.1) | 20.61 | 0 | 15.91 | 17.12 | 1.93 | 2.63 | 0 | r.Shadow.Virtual.Clipmap.UseConservativeCulling=1 r.VolumetricCloud.DistanceToSampleMaxCount=50 r.RayTracing.Culling.Radius=10000 |
| ctl2 | ini | 1920x1080 | 15.41 (64.9) | 15.33 (65.2) | 17.78 (56.2) | 19.53 | 0 | 14.63 | 15.41 | 1.86 | 2.57 | 0 | - |
| cons2 | ini | 1920x1080 | 16.31 (61.3) | 15.23 (65.6) | 17.59 (56.8) | 19.53 | 7 | 14.68 | 16.30 | 1.98 | 2.66 | 0 | r.Shadow.Virtual.Clipmap.UseConservativeCulling=1 |
