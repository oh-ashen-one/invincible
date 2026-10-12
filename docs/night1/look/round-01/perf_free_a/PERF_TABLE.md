| config | output | internal (pre-TSR) | avg ms (fps) | best 5 s block ms | p50 | p95 | p99 | max | hitches (>25 ms & >2x median) | >16.7 ms | GPU avg ms | GPU util before % | contaminated |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tsr50 (r.ScreenPercentage 50) | 3840x2160 | 1920x1080 | 26.45 (37.8) | 20.60 | 21.53 | 50.08 | 57.98 | 77.46 | 133 | 1112/1134 | 24.16 | 92/92/92 | YES: GPU utilisation before the run [92, 92, 92] % (>= 10) |
| tsr67 (r.ScreenPercentage 67) | 3840x2160 | 2573x1447 | 44.26 (22.6) | 30.89 | 45.51 | 65.13 | 75.80 | 109.56 | 1 | 675/678 | 40.44 | 0/35/35 | YES: GPU utilisation before the run [0, 35, 35] % (>= 10) |
| native100 (r.ScreenPercentage 100) | 3840x2160 | 3840x2160 | 49.56 (20.2) | 42.85 | 45.53 | 74.89 | 83.02 | 100.10 | 2 | 606/606 | 46.42 | 0/19/17 | YES: GPU utilisation before the run [0, 19, 17] % (>= 10) |
