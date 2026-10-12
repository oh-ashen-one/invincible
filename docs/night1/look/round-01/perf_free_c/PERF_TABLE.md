| config | output | internal (pre-TSR) | avg ms (fps) | best 5 s block ms | p50 | p95 | p99 | max | hitches (>25 ms & >2x median) | >16.7 ms | GPU avg ms | GPU util before % | contaminated |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tsr50 (r.ScreenPercentage 50) | 3840x2160 | 1920x1080 | 23.46 (42.6) | 22.40 | 23.36 | 28.30 | 30.54 | 64.76 | 1 | 1274/1278 | 22.13 | 5/22/20 | YES: GPU utilisation before the run [5, 22, 20] % (>= 10) |
| tsr67 (r.ScreenPercentage 67) | 3840x2160 | 2573x1447 | 29.41 (34.0) | 28.49 | 29.20 | 34.95 | 38.23 | 42.36 | 0 | 1020/1020 | 27.49 | 0/18/2 | YES: GPU utilisation before the run [0, 18, 2] % (>= 10) |
| native100 (r.ScreenPercentage 100) | 3840x2160 | 3840x2160 | 45.97 (21.8) | 41.69 | 45.46 | 55.29 | 61.72 | 66.83 | 0 | 653/653 | 42.53 | 17/47/16 | YES: GPU utilisation before the run [17, 47, 16] % (>= 10); foreign processes: 1 |
