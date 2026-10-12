| config | output | internal (pre-TSR) | avg ms (fps) | best 5 s block ms | p50 | p95 | p99 | max | hitches (>25 ms & >2x median) | >16.7 ms | GPU avg ms | GPU util before % | contaminated |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tsr50 (r.ScreenPercentage 50) | 3840x2160 | 1920x1080 | 24.88 (40.2) | 24.35 | 24.21 | 30.66 | 35.44 | 56.54 | 1 | 1795/1800 | 22.42 | 50/49/51 | YES: GPU utilisation before the run [50, 49, 51] % (>= 10) |
| tsr67 (r.ScreenPercentage 67) | 3840x2160 | 2573x1447 | 31.77 (31.5) | 28.84 | 29.80 | 36.48 | 44.19 | 1051.70 | 11 | 1793/1800 | 28.06 | 47/46/46 | YES: GPU utilisation before the run [47, 46, 46] % (>= 10) |
| native100 (r.ScreenPercentage 100) | 3840x2160 | 3840x2160 | 43.26 (23.1) | 40.94 | 43.13 | 49.25 | 52.61 | 75.89 | 0 | 1800/1800 | 40.72 | 100/100/100 | YES: GPU utilisation before the run [100, 100, 100] % (>= 10) |
