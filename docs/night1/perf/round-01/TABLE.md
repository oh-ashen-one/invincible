| session | config | output / internal | p50 ms (fps) | p95 ms (fps) | p95 2-frame mean | avg ms | GPU ms (p95) | hitches | lock | settings |
|---|---|---|---|---|---|---|---|---|---|---|
| perf/route/s1 | warm | 3840x2160 / 1920x1080 | 16.43 (60.9) | 19.75 (50.6) | 19.36 (51.6) | 16.50 | 15.68 (18.76) | 0 | valid (util before 0.0 %) | set:perf60 |
| perf/route/s1 | f_base50 | 3840x2160 / 1920x1080 | 26.45 (37.8) | 32.09 (31.2) | 31.21 (32.0) | 26.64 | 25.03 (30.74) | 0 | valid (util before 0.0 %) | - |
| perf/route/s1 | f_perf60_50 | 3840x2160 / 1920x1080 | 16.44 (60.8) | 19.86 (50.4) | 19.48 (51.3) | 16.58 | 15.80 (18.93) | 0 | valid (util before 0.0 %) | set:perf60 |
| perf/route/s1 | f_perf60_mpe6_50 | 3840x2160 / 1920x1080 | 15.79 (63.3) | 19.00 (52.6) | 18.60 (53.8) | 15.95 | 15.20 (18.09) | 0 | valid (util before 0.0 %) | set:perf60_mpe6 |
| perf/route/s1 | f_cand1_50 | 3840x2160 / 1920x1080 | 16.42 (60.9) | 19.91 (50.2) | 19.49 (51.3) | 16.57 | 15.84 (18.91) | 0 | valid (util before 0.0 %) | set:cand1 |
| perf/route/s1 | f_perf60_sp58 | 3840x2160 / 2227x1253 | 17.76 (56.3) | 20.83 (48.0) | 20.42 (49.0) | 17.82 | 17.09 (19.92) | 0 | valid (util before 0.0 %) | set:perf60 |
| perf/route/s1 | f_perf60_sp67 | 3840x2160 / 2573x1447 | 19.61 (51.0) | 22.54 (44.4) | 22.19 (45.1) | 19.66 | 18.93 (21.61) | 0 | valid (util before 0.0 %) | set:perf60 |
| perf/route/s1 | f_base67 | 3840x2160 / 2573x1447 | 31.20 (32.0) | 37.43 (26.7) | 36.55 (27.4) | 31.41 | 28.12 (33.94) | 0 | valid (util before 0.0 %) | - |
| perf/s2/s1 | f_s2_warm | 3840x2160 / 1920x1080 | 13.86 (72.2) | 21.24 (47.1) | 19.60 (51.0) | 14.78 | 13.85 (16.34) | 14 | valid (util before 0.0 %) | map Manhattan_View_S2; set:perf60 |
| perf/s2/s1 | f_s2_base50 | 3840x2160 / 1920x1080 | 21.39 (46.8) | 26.96 (37.1) | 26.10 (38.3) | 21.98 | 21.15 (26.82) | 0 | valid (util before 0.0 %) | map Manhattan_View_S2; - |
| perf/s2/s1 | f_s2_perf60_50 | 3840x2160 / 1920x1080 | 13.39 (74.7) | 17.32 (57.7) | 16.55 (60.4) | 13.90 | 13.46 (15.51) | 1 | valid (util before 0.0 %) | map Manhattan_View_S2; set:perf60 |
| perf/native/s1 | f_base100 | 3840x2160 / 3840x2160 | 42.52 (23.5) | 50.13 (19.9) | 49.21 (20.3) | 42.92 | 39.86 (46.74) | 0 | valid (util before 0.0 %) | - |
| perf/native/s1 | f_perf60_100 | 3840x2160 / 3840x2160 | 28.65 (34.9) | 32.25 (31.0) | 31.61 (31.6) | 28.68 | 27.98 (30.97) | 0 | valid (util before 0.0 %) | set:perf60 |
| perf/reserve/s1 | f_mpe6_sp46 | 3840x2160 / 1766x994 | 15.39 (65.0) | 18.53 (54.0) | 18.10 (55.3) | 15.51 | 14.78 (17.62) | 0 | valid (util before 0.0 %) | set:perf60_mpe6 |
| perf/reserve/s1 | f_mpe6_sp42 | 3840x2160 / 1613x907 | 14.45 (69.2) | 17.47 (57.3) | 17.17 (58.2) | 14.59 | 13.85 (16.80) | 0 | valid (util before 0.0 %) | set:perf60_mpe6 |
| perf/reserve/s1 | f_perf60_sp46 | 3840x2160 / 1766x994 | 16.03 (62.4) | 22.72 (44.0) | 23.94 (41.8) | 17.47 | 15.67 (19.48) | 50 | valid (util before 0.0 %) | set:perf60 |
