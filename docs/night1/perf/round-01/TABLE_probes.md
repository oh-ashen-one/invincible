| session | config | output / internal | p50 ms (fps) | p95 ms (fps) | p95 2-frame mean | avg ms | GPU ms (p95) | hitches | lock | settings |
|---|---|---|---|---|---|---|---|---|---|---|
| r02/p1 | base50 | 3840x2160 / 1920x1080 | 27.96 (35.8) | 34.15 (29.3) | 33.30 (30.0) | 28.24 | 26.29 (32.10) | 5 | valid (util before 0.0 %) | - |
| r02/p1 | npr0_50 | 3840x2160 / 1920x1080 | 26.53 (37.7) | 61.96 (16.1) | 57.60 (17.4) | 31.76 | 24.23 (33.21) | 160 | valid (util before 0.0 %) | r.Nanite.ProgrammableRaster=0 |
| r02/p1 | mpe2_50 | 3840x2160 / 1920x1080 | 25.09 (39.9) | 38.31 (26.1) | 51.86 (19.3) | 31.92 | 24.97 (30.11) | 80 | valid (util before 0.0 %) | r.Nanite.MaxPixelsPerEdge=2 |
| r02/p1 | mpe4_50 | 3840x2160 / 1920x1080 | 22.53 (44.4) | 28.04 (35.7) | 27.23 (36.7) | 22.89 | 19.03 (24.00) | 0 | valid (util before 0.0 %) | r.Nanite.MaxPixelsPerEdge=4 |
| r02/p1 | vsmc0_50 | 3840x2160 / 1920x1080 | 34.45 (29.0) | 44.00 (22.7) | 43.46 (23.0) | 35.11 | 33.91 (42.60) | 0 | valid (util before 0.0 %) | r.Shadow.Virtual.Cache=0 |
| r02/p1 | vsmbias1_50 | 3840x2160 / 1920x1080 | 27.30 (36.6) | 33.33 (30.0) | 32.22 (31.0) | 27.38 | 25.58 (30.79) | 0 | valid (util before 0.0 %) | r.Shadow.Virtual.ResolutionLodBiasDirectional=1 |
| r02/p1 | coarse0_50 | 3840x2160 / 1920x1080 | 27.87 (35.9) | 33.65 (29.7) | 32.66 (30.6) | 28.02 | 26.45 (32.20) | 1 | valid (util before 0.0 %) | r.Shadow.Virtual.NonNanite.IncludeInCoarsePages=0 |
| r02/p2 | clip18_50 | 3840x2160 / 1920x1080 | 27.73 (36.1) | 33.39 (29.9) | 32.55 (30.7) | 27.83 | 26.29 (31.79) | 0 | valid (util before 0.0 %) | r.Shadow.Virtual.Clipmap.LastLevel=18 |
| r02/p2 | gi2_50 | 3840x2160 / 1920x1080 | 27.84 (35.9) | 33.91 (29.5) | 32.81 (30.5) | 28.04 | 24.73 (30.33) | 0 | valid (util before 0.0 %) | sg.GlobalIlluminationQuality=2 |
| r02/p2 | sh2_50 | 3840x2160 / 1920x1080 | 27.83 (35.9) | 33.81 (29.6) | 32.74 (30.5) | 28.02 | 26.18 (31.88) | 0 | valid (util before 0.0 %) | sg.ShadowQuality=2 |
| r02/p2 | fog16_50 | 3840x2160 / 1920x1080 | 27.65 (36.2) | 33.59 (29.8) | 32.73 (30.5) | 27.80 | 26.30 (31.82) | 0 | valid (util before 0.0 %) | r.VolumetricFog.GridPixelSize=16 |
| r02/p2 | cloud512_50 | 3840x2160 / 1920x1080 | 27.77 (36.0) | 33.70 (29.7) | 32.67 (30.6) | 27.96 | 26.53 (32.17) | 0 | valid (util before 0.0 %) | r.VolumetricCloud.ViewRaySampleMaxCount=512 |
| r02/p2 | skyres64_50 | 3840x2160 / 1920x1080 | 27.55 (36.3) | 31.91 (31.3) | 31.42 (31.8) | 27.53 | 25.06 (29.63) | 0 | valid (util before 0.0 %) | r.SkyLight.RealTimeReflectionCapture.ResolutionOverride=64 |
| r02/p2 | skyoff_50 | 3840x2160 / 1920x1080 | 27.16 (36.8) | 31.23 (32.0) | 30.89 (32.4) | 27.06 | 25.46 (29.40) | 0 | valid (util before 0.0 %) | r.SkyLight.RealTimeReflectionCapture=0 |
| r02/p2 | hwrt0_50 | 3840x2160 / 1920x1080 | 23.37 (42.8) | 28.90 (34.6) | 28.07 (35.6) | 23.52 | 22.74 (28.01) | 0 | valid (util before 0.0 %) | r.Lumen.HardwareRayTracing=0 |
| r03/q1 | mpe3_50 | 3840x2160 / 1920x1080 | 23.24 (43.0) | 29.74 (33.6) | 29.00 (34.5) | 23.79 | 21.98 (27.24) | 6 | valid (util before 0.0 %) | r.Nanite.MaxPixelsPerEdge=3 |
| r03/q1 | mpe6_50 | 3840x2160 / 1920x1080 | 22.14 (45.2) | 27.69 (36.1) | 26.74 (37.4) | 22.70 | 20.86 (25.96) | 3 | valid (util before 0.0 %) | r.Nanite.MaxPixelsPerEdge=6 |
| r03/q1 | hwrtgi0_50 | 3840x2160 / 1920x1080 | 27.54 (36.3) | 34.06 (29.4) | 33.38 (30.0) | 28.88 | 24.62 (30.32) | 23 | valid (util before 0.0 %) | r.Lumen.ScreenProbeGather.HardwareRayTracing=0 |
| r03/q1 | hwrtrefl0_50 | 3840x2160 / 1920x1080 | 27.28 (36.7) | 34.42 (29.1) | 33.16 (30.2) | 27.62 | 25.41 (31.13) | 3 | valid (util before 0.0 %) | r.Lumen.Reflections.HardwareRayTracing=0 |
| r03/q1 | mpe4_hwrt0_50 | 3840x2160 / 1920x1080 | 18.35 (54.5) | 24.76 (40.4) | 24.07 (41.6) | 21.18 | 18.91 (23.54) | 33 | valid (util before 0.0 %) | set:mpe4 r.Lumen.HardwareRayTracing=0 |
| r03/q1 | mpe4_cheap_50 | 3840x2160 / 1920x1080 | 22.36 (44.7) | 26.91 (37.2) | 26.66 (37.5) | 24.17 | 21.89 (25.63) | 21 | valid (util before 0.0 %) | set:mpe4 set:cheap |
| r03/c1 | ctl1080_100 | 1920x1080 / 1920x1080 | 23.11 (43.3) | 30.08 (33.2) | 29.31 (34.1) | 25.23 | 20.68 (26.21) | 26 | valid (util before 0.0 %) | - |
| r03/t1 | tr_base50 | 3840x2160 / 1920x1080 | 27.85 (35.9) | 33.67 (29.7) | 32.76 (30.5) | 28.02 | 26.22 (31.83) | 0 | valid (util before 0.0 %) | - |
| r03/t1 | tr_mpe4_50 | 3840x2160 / 1920x1080 | 22.60 (44.3) | 27.99 (35.7) | 27.12 (36.9) | 22.90 | 21.23 (26.21) | 0 | valid (util before 0.0 %) | set:mpe4 |
| r05/q1 | occ0_50 | 3840x2160 / 1920x1080 | 28.15 (35.5) | 34.93 (28.6) | 33.98 (29.4) | 28.30 | 26.61 (32.28) | 4 | valid (util before 0.0 %) | r.AllowOcclusionQueries=0 |
| r05/q1 | occbuf2_50 | 3840x2160 / 1920x1080 | 27.62 (36.2) | 34.01 (29.4) | 33.14 (30.2) | 27.80 | 26.10 (31.79) | 2 | valid (util before 0.0 %) | r.NumBufferedOcclusionQueries=2 |
| r05/q1 | hzbocc_50 | 3840x2160 / 1920x1080 | 32.65 (30.6) | 38.58 (25.9) | 37.97 (26.3) | 32.76 | 27.37 (33.12) | 0 | valid (util before 0.0 %) | r.HZBOcclusion=1 |
| r05/q1 | mpe4_hwrt0_occ0_50 | 3840x2160 / 1920x1080 | 18.05 (55.4) | 26.64 (37.5) | 23.77 (42.1) | 18.99 | 18.25 (23.37) | 7 | valid (util before 0.0 %) | set:mpe4 set:hwrt0 set:occ0 |
| r05/q1 | mpe4_occ0_50 | 3840x2160 / 1920x1080 | 22.59 (44.3) | 28.58 (35.0) | 27.47 (36.4) | 23.05 | 21.54 (26.38) | 0 | valid (util before 0.0 %) | set:mpe4 set:occ0 |
| r05/q1 | floor25_50 | 3840x2160 / 960x540 | 14.14 (70.7) | 26.26 (38.1) | 20.89 (47.9) | 15.40 | 14.65 (19.51) | 45 | valid (util before 0.0 %) | set:mpe4 set:hwrt0 set:occ0 |
| r05/q1 | mpe4_hwrt0_occ0_cheap_50 | 3840x2160 / 1920x1080 | 17.61 (56.8) | 24.81 (40.3) | 21.83 (45.8) | 18.15 | 17.42 (20.59) | 0 | valid (util before 0.0 %) | set:mpe4 set:hwrt0 set:occ0 set:cheap |
| r05/q1 | mpe4_hwrt0_occ0_sp58 | 3840x2160 / 2227x1253 | 19.53 (51.2) | 25.95 (38.5) | 24.38 (41.0) | 20.07 | 19.28 (23.73) | 0 | valid (util before 0.0 %) | set:mpe4 set:hwrt0 set:occ0 |
| r05/q1 | mpe4_hwrt0_occ0_sp67 | 3840x2160 / 2573x1447 | 21.50 (46.5) | 27.02 (37.0) | 26.09 (38.3) | 21.95 | 21.25 (25.76) | 0 | valid (util before 0.0 %) | set:mpe4 set:hwrt0 set:occ0 |
| r05/q2 | base67 | 3840x2160 / 2573x1447 | 32.42 (30.8) | 38.83 (25.8) | 37.92 (26.4) | 32.66 | 29.54 (35.35) | 0 | valid (util before 0.0 %) | - |
| r05/s1 | s2_base50 | 3840x2160 / 1920x1080 | 23.52 (42.5) | 29.16 (34.3) | 28.21 (35.4) | 24.08 | 22.04 (27.18) | 0 | valid (util before 0.0 %) | map Manhattan_View_S2; - |
| r05/s1 | s2_mpe4_hwrt0_occ0_50 | 3840x2160 / 1920x1080 | 15.02 (66.6) | 20.90 (47.8) | 19.91 (50.2) | 15.67 | 15.43 (20.65) | 0 | valid (util before 0.0 %) | map Manhattan_View_S2; set:mpe4 set:hwrt0 set:occ0 |
| r06/q1 | aa2_50 | 3840x2160 / 1920x1080 | 26.35 (38.0) | 32.04 (31.2) | 31.17 (32.1) | 26.40 | 24.49 (29.92) | 0 | valid (util before 0.0 %) | sg.AntiAliasingQuality=2 |
| r06/q1 | tsrh100_50 | 3840x2160 / 1920x1080 | 26.36 (37.9) | 32.21 (31.0) | 31.33 (31.9) | 26.47 | 24.85 (30.44) | 0 | valid (util before 0.0 %) | r.TSR.History.ScreenPercentage=100 |
| r06/q1 | pp2_50 | 3840x2160 / 1920x1080 | 26.17 (38.2) | 31.98 (31.3) | 31.00 (32.3) | 26.24 | 24.18 (29.63) | 0 | valid (util before 0.0 %) | sg.PostProcessQuality=2 |
| r06/q1 | mbhalf_50 | 3840x2160 / 1920x1080 | 26.36 (37.9) | 32.31 (31.0) | 31.23 (32.0) | 26.56 | 24.75 (30.34) | 0 | valid (util before 0.0 %) | r.MotionBlur.HalfResGather=1 r.MotionBlur.HalfResInput=1 |
| r06/q1 | mpe4_hwrt0_aa2_50 | 3840x2160 / 1920x1080 | 16.75 (59.7) | 22.20 (45.1) | 21.36 (46.8) | 17.13 | 16.42 (21.31) | 0 | valid (util before 0.0 %) | set:mpe4 set:hwrt0 sg.AntiAliasingQuality=2 |
| r06/q1 | mpe4_hwrt0_aa2_pp2_50 | 3840x2160 / 1920x1080 | 16.79 (59.6) | 22.25 (44.9) | 21.33 (46.9) | 17.15 | 16.45 (21.38) | 0 | valid (util before 0.0 %) | set:mpe4 set:hwrt0 sg.AntiAliasingQuality=2 sg.PostProcessQuality=2 |
| r07/q1 | ctl_base50 | 3840x2160 / 1920x1080 | 26.45 (37.8) | 33.49 (29.9) | 32.52 (30.7) | 26.90 | 24.47 (30.14) | 3 | valid (util before 0.0 %) | - |
| r07/q1 | ctl_mpe4_hwrt0_50 | 3840x2160 / 1920x1080 | 16.76 (59.7) | 22.12 (45.2) | 21.26 (47.0) | 17.08 | 16.34 (21.08) | 0 | valid (util before 0.0 %) | set:mpe4 set:hwrt0 |
| r07/q1 | rep_tsr100_50 | 3840x2160 / 1920x1080 | 26.55 (37.7) | 35.41 (28.2) | 34.53 (29.0) | 28.03 | 26.26 (33.68) | 63 | valid (util before 0.0 %) | set:tsr100 |
| r07/q1 | rep_mbhalf_50 | 3840x2160 / 1920x1080 | 26.39 (37.9) | 32.07 (31.2) | 31.12 (32.1) | 26.56 | 24.74 (30.26) | 0 | valid (util before 0.0 %) | r.MotionBlur.HalfResGather=1 |
| r07/q1 | gate_on50 | 3840x2160 / 1920x1080 | 38.03 (26.3) | 44.22 (22.6) | 43.63 (22.9) | 38.07 | 30.01 (36.01) | 0 | valid (util before 0.0 %) |  -WHTravMask |
| r07/q1 | lpg32_50 | 3840x2160 / 1920x1080 | 26.15 (38.2) | 32.02 (31.2) | 31.03 (32.2) | 26.24 | 24.41 (29.76) | 0 | valid (util before 0.0 %) | r.Lumen.ScreenProbeGather.DownsampleFactor=32 |
| r07/q1 | oct6_50 | 3840x2160 / 1920x1080 | 26.43 (37.8) | 32.37 (30.9) | 31.28 (32.0) | 26.63 | 24.78 (30.39) | 0 | valid (util before 0.0 %) | r.Lumen.ScreenProbeGather.TracingOctahedronResolution=6 |
| r07/q1 | vrt2_50 | 3840x2160 / 1920x1080 | 27.38 (36.5) | 33.11 (30.2) | 32.19 (31.1) | 27.70 | 26.20 (31.66) | 0 | valid (util before 0.0 %) | r.VolumetricRenderTarget.Mode=2 r.VolumetricRenderTarget.Scale=0.7 |
| r08/v0/p1 | cand1_v0 | 3840x2160 / 1920x1080 | 16.41 (60.9) | 19.83 (50.4) | 19.47 (51.4) | 16.54 | 15.82 (19.00) | 0 | valid (util before 0.0 %) | set:cand1 |
| r08/v0/p1 | cand1_v0_sp67 | 3840x2160 / 2573x1447 | 19.69 (50.8) | 22.56 (44.3) | 22.24 (45.0) | 19.72 | 18.99 (21.72) | 0 | valid (util before 0.0 %) | set:cand1 |
| r08/v0s2/p1 | s2_cand1_v0 | 3840x2160 / 1920x1080 | 13.26 (75.4) | 16.02 (62.4) | 15.85 (63.1) | 13.90 | 13.36 (15.39) | 36 | valid (util before 0.0 %) | map Manhattan_View_S2; set:cand1 |
| r08/trace/t1 | tr_cand1_50 | 3840x2160 / 1920x1080 | 16.37 (61.1) | 19.84 (50.4) | 19.46 (51.4) | 16.49 | 15.77 (18.97) | 0 | valid (util before 0.0 %) | set:cand1 |
| r08/matrix/v1_static/p1 | cand1_c | 3840x2160 / 1920x1080 | 16.34 (61.2) | 20.31 (49.2) | 19.91 (50.2) | 16.69 | 15.86 (19.20) | 7 | valid (util before 0.0 %) | set:cand1 |
| r08/matrix/v2_far_plain/p1 | cand1_c | 3840x2160 / 1920x1080 | 16.43 (60.9) | 19.90 (50.3) | 19.53 (51.2) | 16.55 | 15.81 (19.02) | 0 | valid (util before 0.0 %) | set:cand1 |
| r08/matrix/v3_kit_plain/p1 | cand1_c | 3840x2160 / 1920x1080 | 16.43 (60.9) | 19.83 (50.4) | 19.54 (51.2) | 16.53 | 15.80 (18.94) | 0 | valid (util before 0.0 %) | set:cand1 |
| r09/q1 | ctlF | 3840x2160 / 1920x1080 | 16.71 (59.9) | 20.36 (49.1) | 19.96 (50.1) | 16.86 | 16.05 (19.24) | 0 | valid (util before 0.0 %) | set:cand1 |
| r09/q1 | skyslice | 3840x2160 / 1920x1080 | 16.48 (60.7) | 19.98 (50.1) | 19.52 (51.2) | 16.56 | 15.86 (19.05) | 0 | valid (util before 0.0 %) | set:cand1 r.SkyLight.RealTimeReflectionCapture.TimeSlice=1 |
| r09/q1 | mpe6 | 3840x2160 / 1920x1080 | 15.93 (62.8) | 19.17 (52.2) | 18.75 (53.3) | 16.09 | 15.33 (18.32) | 0 | valid (util before 0.0 %) | set:cand1 r.Nanite.MaxPixelsPerEdge=6 |
| r09/q1 | cld256 | 3840x2160 / 1920x1080 | 16.49 (60.6) | 19.91 (50.2) | 19.55 (51.2) | 16.59 | 15.84 (18.96) | 0 | valid (util before 0.0 %) | set:cand1 r.VolumetricCloud.ViewRaySampleMaxCount=256 |
| r09/q1 | cldd8 | 3840x2160 / 1920x1080 | 16.53 (60.5) | 20.01 (50.0) | 19.62 (51.0) | 16.63 | 15.86 (19.06) | 0 | valid (util before 0.0 %) | set:cand1 r.VolumetricCloud.DistanceToSampleMaxCount=8 |
| r09/q1 | vsmmov | 3840x2160 / 1920x1080 | 16.47 (60.7) | 19.88 (50.3) | 19.53 (51.2) | 16.60 | 15.86 (18.94) | 0 | valid (util before 0.0 %) | set:cand1 r.Shadow.Virtual.ResolutionLodBiasDirectionalMoving=1 |
| r09/q1 | smrt4 | 3840x2160 / 1920x1080 | 16.29 (61.4) | 19.70 (50.8) | 19.31 (51.8) | 16.43 | 15.71 (18.82) | 0 | valid (util before 0.0 %) | set:cand1 r.Shadow.Virtual.SMRT.RayCountDirectional=4 |
| r09/q1 | ctlF2 | 3840x2160 / 1920x1080 | 16.52 (60.5) | 19.91 (50.2) | 19.57 (51.1) | 16.62 | 15.87 (19.03) | 0 | valid (util before 0.0 %) | set:cand1 |
