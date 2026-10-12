| session | config | output / internal | p50 ms (fps) | p95 ms (fps) | p95 2-frame mean | avg ms | GPU ms (p95) | hitches | lock | settings |
|---|---|---|---|---|---|---|---|---|---|---|
| a1 | warm | 3840x2160 / 1766x994 | 16.43 (60.9) | 19.61 (51.0) | n/a (n/a) | 16.76 | 15.42 (n/a) | 15 | valid (util before 0.0 %) | - |
| a1 | ctl | 3840x2160 / 1766x994 | 16.39 (61.0) | 18.92 (52.9) | n/a (n/a) | 16.48 | 15.24 (n/a) | 0 | valid (util before 0.0 %) | - |
| a1 | occb2 | 3840x2160 / 1766x994 | 16.38 (61.0) | 19.01 (52.6) | n/a (n/a) | 16.46 | 15.31 (n/a) | 0 | valid (util before 0.0 %) | r.NumBufferedOcclusionQueries=2 |
| a1 | occ0 | 3840x2160 / 1766x994 | 16.57 (60.4) | 19.24 (52.0) | n/a (n/a) | 16.67 | 15.45 (n/a) | 0 | valid (util before 0.0 %) | r.AllowOcclusionQueries=0 |
| a1 | occ0_50 | 3840x2160 / 1920x1080 | 17.32 (57.7) | 19.75 (50.6) | n/a (n/a) | 17.39 | 14.73 (n/a) | 0 | valid (util before 0.0 %) | r.AllowOcclusionQueries=0 |
| a1 | occ0_58 | 3840x2160 / 2227x1253 | 19.02 (52.6) | 21.74 (46.0) | n/a (n/a) | 19.02 | 16.34 (n/a) | 0 | valid (util before 0.0 %) | r.AllowOcclusionQueries=0 |
| a1 | ctl2 | 3840x2160 / 1766x994 | 16.45 (60.8) | 19.02 (52.6) | n/a (n/a) | 16.52 | 15.27 (n/a) | 0 | valid (util before 0.0 %) | - |
| a1 | occb2_50 | 3840x2160 / 1920x1080 | 17.18 (58.2) | 19.70 (50.8) | n/a (n/a) | 17.23 | 14.53 (n/a) | 0 | valid (util before 0.0 %) | r.NumBufferedOcclusionQueries=2 |
| b1 | warmB | 3840x2160 / 1766x994 | 16.37 (61.1) | 18.88 (53.0) | n/a (n/a) | 16.43 | 15.20 (n/a) | 0 | valid (util before 0.0 %) | map /Game/PerfF/Cl4P/Manhattan; - |
| b1 | p | 3840x2160 / 1766x994 | 16.29 (61.4) | 18.77 (53.3) | n/a (n/a) | 16.35 | 15.11 (n/a) | 0 | valid (util before 0.0 %) | map /Game/PerfF/Cl4P/Manhattan; - |
| b1 | ctl3 | 3840x2160 / 1766x994 | 16.43 (60.9) | 18.79 (53.2) | n/a (n/a) | 16.48 | 15.27 (n/a) | 0 | valid (util before 0.0 %) | - |
| b1 | sk0 | 3840x2160 / 1766x994 | 14.79 (67.6) | 17.41 (57.4) | n/a (n/a) | 14.90 | 13.65 (n/a) | 0 | valid (util before 0.0 %) | r.RayTracing.Geometry.SkeletalMeshes=0 |
| b1 | p48 | 3840x2160 / 1843x1037 | 16.83 (59.4) | 19.37 (51.6) | n/a (n/a) | 16.87 | 14.21 (n/a) | 0 | valid (util before 0.0 %) | map /Game/PerfF/Cl4P/Manhattan; - |
| b1 | p50 | 3840x2160 / 1920x1080 | 17.23 (58.0) | 19.81 (50.5) | n/a (n/a) | 17.30 | 14.65 (n/a) | 0 | valid (util before 0.0 %) | map /Game/PerfF/Cl4P/Manhattan; - |
| b1 | sw | 3840x2160 / 1766x994 | 14.37 (69.6) | 16.92 (59.1) | n/a (n/a) | 14.45 | 13.80 (n/a) | 0 | valid (util before 0.0 %) | r.Lumen.HardwareRayTracing=0 |
| b1 | p2 | 3840x2160 / 1766x994 | 16.36 (61.1) | 19.07 (52.4) | n/a (n/a) | 16.47 | 13.71 (n/a) | 0 | valid (util before 0.0 %) | map /Game/PerfF/Cl4P/Manhattan; - |
| c1 | warmC | 3840x2160 / 1766x994 | 16.49 (60.6) | 19.21 (52.1) | n/a (n/a) | 16.59 | 15.30 (n/a) | 0 | valid (util before 0.0 %) | - |
| c1 | sk0_46 | 3840x2160 / 1766x994 | 15.05 (66.5) | 17.68 (56.6) | n/a (n/a) | 15.11 | 13.91 (n/a) | 0 | valid (util before 0.0 %) | r.RayTracing.Geometry.SkeletalMeshes=0 |
| c1 | sk0_48 | 3840x2160 / 1843x1037 | 15.21 (65.8) | 17.74 (56.4) | n/a (n/a) | 15.28 | 14.08 (n/a) | 0 | valid (util before 0.0 %) | r.RayTracing.Geometry.SkeletalMeshes=0 |
| c1 | sk0_50 | 3840x2160 / 1920x1080 | 15.67 (63.8) | 18.12 (55.2) | n/a (n/a) | 15.71 | 14.49 (n/a) | 0 | valid (util before 0.0 %) | r.RayTracing.Geometry.SkeletalMeshes=0 |
| c1 | dg1 | 3840x2160 / 1766x994 | 16.34 (61.2) | 18.88 (53.0) | n/a (n/a) | 16.41 | 15.22 (n/a) | 0 | valid (util before 0.0 %) | r.RayTracing.DynamicGeometry.MaxUpdatePrimitivesPerFrame=1 |
| c1 | sk0_48b | 3840x2160 / 1843x1037 | 15.20 (65.8) | 17.81 (56.2) | n/a (n/a) | 15.27 | 14.07 (n/a) | 0 | valid (util before 0.0 %) | r.RayTracing.Geometry.SkeletalMeshes=0 |
| c1 | sk0_50b | 3840x2160 / 1920x1080 | 15.64 (63.9) | 18.29 (54.7) | n/a (n/a) | 15.71 | 14.45 (n/a) | 0 | valid (util before 0.0 %) | r.RayTracing.Geometry.SkeletalMeshes=0 |
| c1 | sk0_46b | 3840x2160 / 1766x994 | 14.90 (67.1) | 17.44 (57.3) | n/a (n/a) | 14.98 | 13.67 (n/a) | 0 | valid (util before 0.0 %) | r.RayTracing.Geometry.SkeletalMeshes=0 |
| d1 | warmD | 3840x2160 / 1843x1037 | 15.37 (65.1) | 17.88 (55.9) | n/a (n/a) | 15.41 | 14.20 (n/a) | 0 | valid (util before 0.0 %) | - |
| d1 | ship_a | 3840x2160 / 1843x1037 | 15.27 (65.5) | 17.61 (56.8) | n/a (n/a) | 15.32 | 14.01 (n/a) | 0 | valid (util before 0.0 %) | - |
| d1 | ship_b | 3840x2160 / 1843x1037 | 15.25 (65.6) | 17.86 (56.0) | n/a (n/a) | 15.34 | 14.04 (n/a) | 0 | valid (util before 0.0 %) | - |
| d1 | ship_s2 | 3840x2160 / 1843x1037 | 14.01 (71.4) | 14.95 (66.9) | n/a (n/a) | 14.01 | 13.20 (n/a) | 0 | valid (util before 0.0 %) | map Manhattan_View_S2; - |
| d1 | hero_in | 3840x2160 / 1843x1037 | 16.70 (59.9) | 19.29 (51.8) | n/a (n/a) | 16.78 | 15.53 (n/a) | 0 | valid (util before 0.0 %) | r.RayTracing.Geometry.SkeletalMeshes=1 |
| d1 | fb1 | 3840x2160 / 1843x1037 | 16.75 (59.7) | 19.20 (52.1) | n/a (n/a) | 16.79 | 15.46 (n/a) | 0 | valid (util before 0.0 %) | r.RayTracing.Geometry.SkeletalMeshes=1 r.Metal.RayTracing.DebugForceBuildMode=1 |
| d1 | pd32 | 3840x2160 / 1843x1037 | 15.22 (65.7) | 17.72 (56.4) | n/a (n/a) | 15.24 | 13.92 (n/a) | 0 | valid (util before 0.0 %) | r.Lumen.ScreenProbeGather.DownsampleFactor=32 |
| d1 | sw48 | 3840x2160 / 1843x1037 | 14.74 (67.8) | 17.10 (58.5) | n/a (n/a) | 14.79 | 14.10 (n/a) | 0 | valid (util before 0.0 %) | r.Lumen.HardwareRayTracing=0 |
| e1 | warmE | 3840x2160 / 1843x1037 | 15.17 (65.9) | 17.72 (56.4) | n/a (n/a) | 15.26 | 14.19 (n/a) | 0 | valid (util before 0.0 %) | - |
| e1 | gi48 | 3840x2160 / 1843x1037 | 15.10 (66.2) | 17.55 (57.0) | n/a (n/a) | 15.20 | 14.44 (n/a) | 0 | valid (util before 0.0 %) | r.Lumen.ScreenProbeGather.HardwareRayTracing=1 |
| e1 | gi50 | 3840x2160 / 1920x1080 | 15.60 (64.1) | 18.15 (55.1) | n/a (n/a) | 15.68 | 14.90 (n/a) | 0 | valid (util before 0.0 %) | r.Lumen.ScreenProbeGather.HardwareRayTracing=1 |
| e1 | m8_50 | 3840x2160 / 1920x1080 | 15.40 (64.9) | 17.93 (55.8) | n/a (n/a) | 15.46 | 14.22 (n/a) | 0 | valid (util before 0.0 %) | r.Nanite.MaxPixelsPerEdge=8 |
| e1 | m8_48 | 3840x2160 / 1843x1037 | 15.13 (66.1) | 17.54 (57.0) | n/a (n/a) | 15.17 | 13.92 (n/a) | 0 | valid (util before 0.0 %) | r.Nanite.MaxPixelsPerEdge=8 |
| e1 | gi50m8 | 3840x2160 / 1920x1080 | 15.42 (64.9) | 18.03 (55.5) | n/a (n/a) | 15.52 | 14.72 (n/a) | 0 | valid (util before 0.0 %) | r.Lumen.ScreenProbeGather.HardwareRayTracing=1 r.Nanite.MaxPixelsPerEdge=8 |
| e1 | ship_c | 3840x2160 / 1843x1037 | 15.21 (65.7) | 17.64 (56.7) | n/a (n/a) | 15.28 | 14.05 (n/a) | 0 | valid (util before 0.0 %) | - |
| e1 | gi46 | 3840x2160 / 1766x994 | 14.81 (67.5) | 17.41 (57.4) | n/a (n/a) | 14.91 | 14.12 (n/a) | 0 | valid (util before 0.0 %) | r.Lumen.ScreenProbeGather.HardwareRayTracing=1 |
| f1 | warmF | 3840x2160 / 1920x1080 | 15.46 (64.7) | 17.91 (55.8) | n/a (n/a) | 15.55 | 14.73 (n/a) | 0 | valid (util before 2.0 %) | - |
| f1 | hwl_a | 3840x2160 / 1920x1080 | 15.46 (64.7) | 17.88 (55.9) | n/a (n/a) | 15.54 | 14.72 (n/a) | 0 | valid (util before 2.0 %) | - |
| f1 | hwl_b | 3840x2160 / 1920x1080 | 15.34 (65.2) | 17.91 (55.8) | n/a (n/a) | 15.41 | 14.58 (n/a) | 0 | valid (util before 2.0 %) | - |
| f1 | hwl_s2 | 3840x2160 / 1920x1080 | 14.49 (69.0) | 15.45 (64.7) | n/a (n/a) | 14.48 | 13.60 (n/a) | 0 | valid (util before 2.0 %) | map Manhattan_View_S2; - |
| f1 | hwl_m10 | 3840x2160 / 1920x1080 | 15.36 (65.1) | 17.88 (55.9) | n/a (n/a) | 15.46 | 14.65 (n/a) | 0 | valid (util before 2.0 %) | r.Nanite.MaxPixelsPerEdge=10 |
| f1 | hwl_smrt | 3840x2160 / 1920x1080 | 15.44 (64.8) | 17.75 (56.3) | n/a (n/a) | 15.53 | 14.77 (n/a) | 0 | valid (util before 2.0 %) | r.Shadow.Virtual.SMRT.SamplesPerRayDirectional=4 |
| f1 | hwl_hero | 3840x2160 / 1920x1080 | 16.94 (59.0) | 19.48 (51.3) | n/a (n/a) | 17.05 | 16.23 (n/a) | 0 | valid (util before 2.0 %) | r.RayTracing.Geometry.SkeletalMeshes=1 |
| f1 | hwl_sw | 3840x2160 / 1920x1080 | 14.95 (66.9) | 17.30 (57.8) | n/a (n/a) | 14.97 | 14.32 (n/a) | 0 | valid (util before 2.0 %) | r.Lumen.HardwareRayTracing=0 |
| g1 | warmG | 3840x2160 / 1920x1080 | 17.71 (56.5) | 20.30 (49.3) | n/a (n/a) | 17.73 | 16.09 (n/a) | 0 | valid (util before 0.0 %) | map /Game/PerfF/RTvC/Manhattan; - |
| g1 | rtvC | 3840x2160 / 1920x1080 | 17.67 (56.6) | 20.32 (49.2) | n/a (n/a) | 17.69 | 16.05 (n/a) | 0 | valid (util before 0.0 %) | map /Game/PerfF/RTvC/Manhattan; - |
| g1 | rtvC_r100 | 3840x2160 / 1920x1080 | 16.77 (59.6) | 19.40 (51.5) | n/a (n/a) | 16.79 | 15.57 (n/a) | 0 | valid (util before 0.0 %) | map /Game/PerfF/RTvC/Manhattan; r.RayTracing.Culling.Radius=10000 |
| g1 | rtvC_r50 | 3840x2160 / 1920x1080 | 16.14 (62.0) | 18.78 (53.2) | n/a (n/a) | 16.11 | 15.43 (n/a) | 0 | valid (util before 0.0 %) | map /Game/PerfF/RTvC/Manhattan; r.RayTracing.Culling.Radius=5000 |
| g1 | rtvA | 3840x2160 / 1920x1080 | 17.90 (55.9) | 20.44 (48.9) | n/a (n/a) | 17.87 | 16.14 (n/a) | 0 | valid (util before 0.0 %) | map /Game/PerfF/RTvA/Manhattan; - |
| g1 | rtvB | 3840x2160 / 1920x1080 | 16.31 (61.3) | 18.74 (53.4) | n/a (n/a) | 16.35 | 14.82 (n/a) | 0 | valid (util before 0.0 %) | map /Game/PerfF/RTvB/Manhattan; - |
| g1 | hwl_c | 3840x2160 / 1920x1080 | 15.45 (64.7) | 17.92 (55.8) | n/a (n/a) | 15.52 | 15.01 (n/a) | 0 | valid (util before 0.0 %) | - |
| g1 | rtvC_b | 3840x2160 / 1920x1080 | 17.71 (56.5) | 20.25 (49.4) | n/a (n/a) | 17.71 | 16.07 (n/a) | 0 | valid (util before 0.0 %) | map /Game/PerfF/RTvC/Manhattan; - |
