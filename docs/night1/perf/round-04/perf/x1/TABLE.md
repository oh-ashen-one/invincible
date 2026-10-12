| config | SP | internal | avg ms (fps) | p50 ms (fps) | p95 ms (fps) | p99 | hitches | GPU ms | RT ms | GT ms | RHI ms | draw calls | cvars |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| warmX | ini | 1920x1080 | 15.93 (62.8) | 15.48 (64.6) | 19.27 (51.9) | 32.05 | 21 | 14.84 | 15.92 | 2.08 | 3.01 | 0 | - |
| ctl | ini | 1920x1080 | 15.52 (64.4) | 15.47 (64.6) | 17.95 (55.7) | 19.63 | 0 | 14.70 | 15.52 | 1.85 | 2.56 | 0 | - |
| far0 | ini | 1920x1080 | 14.84 (67.4) | 14.74 (67.8) | 17.05 (58.6) | 18.35 | 0 | 14.05 | 14.83 | 1.86 | 2.58 | 0 | r.Shadow.Virtual.UseFarShadowCulling=0 |
| far0c | ini | 1920x1080 | 14.62 (68.4) | 14.58 (68.6) | 16.47 (60.7) | 17.37 | 0 | 13.83 | 14.62 | 1.87 | 2.56 | 0 | r.Shadow.Virtual.UseFarShadowCulling=0 r.Shadow.Virtual.Clipmap.UseConservativeCulling=1 |
| lk20 | ini | 1920x1080 | 17.64 (56.7) | 17.68 (56.6) | 19.93 (50.2) | 21.29 | 0 | 16.09 | 17.63 | 1.95 | 2.67 | 0 | r.Shadow.Virtual.Clipmap.UseConservativeCulling=1 r.VolumetricCloud.DistanceToSampleMaxCount=50 |
| lk20a | ini | 1920x1080 | 17.31 (57.8) | 17.30 (57.8) | 19.70 (50.8) | 21.20 | 0 | 15.93 | 17.31 | 1.91 | 2.90 | 0 | r.Shadow.Virtual.Clipmap.UseConservativeCulling=1 r.VolumetricCloud.DistanceToSampleMaxCount=50 r.RayTracing.Culling.Angle=3 |
| ck20op | ini | 1920x1080 | 16.98 (58.9) | 16.98 (58.9) | 19.31 (51.8) | 20.65 | 0 | 15.25 | 16.98 | 1.95 | 2.70 | 0 | r.Shadow.Virtual.Clipmap.UseConservativeCulling=1 r.VolumetricCloud.DistanceToSampleMaxCount=50 r.RayTracing.Culling.Angle=3 r.RayTracing.DebugForceOpaque=1 |
| far0b | ini | 1920x1080 | 14.88 (67.2) | 14.78 (67.6) | 16.95 (59.0) | 18.27 | 0 | 14.08 | 14.88 | 1.86 | 2.59 | 0 | r.Shadow.Virtual.UseFarShadowCulling=0 |
| ctl2 | ini | 1920x1080 | 15.56 (64.3) | 15.47 (64.6) | 17.98 (55.6) | 19.71 | 0 | 14.74 | 15.55 | 1.86 | 2.57 | 0 | - |
