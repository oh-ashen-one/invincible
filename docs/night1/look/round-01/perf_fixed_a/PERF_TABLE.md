| config | output | internal (pre-TSR) | avg ms (fps) | best 5 s block ms | p50 | p95 | p99 | max | hitches (>25 ms & >2x median) | >16.7 ms | GPU avg ms | GPU util before % | contaminated |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tsr50 (r.ScreenPercentage 50) | 3840x2160 | 1920x1080 | 29.92 (33.4) | 23.89 | 25.15 | 45.67 | 51.96 | 63.65 | 26 | 1796/1800 | 27.81 | 100/100/100 | YES: GPU utilisation before the run [100, 100, 100] % (>= 10); foreign processes: 1 |
| tsr67 (r.ScreenPercentage 67) | 3840x2160 | 2573x1447 | 30.07 (33.3) | 28.47 | 29.65 | 35.52 | 44.41 | 57.84 | 0 | 1799/1800 | 27.31 | 99/100/99 | YES: GPU utilisation before the run [99, 100, 99] % (>= 10) |
| native100 (r.ScreenPercentage 100) | 3840x2160 | 3840x2160 | 45.61 (21.9) | 43.05 | 45.10 | 52.76 | 58.13 | 77.56 | 0 | 1800/1800 | 42.21 | 44/49/43 | YES: GPU utilisation before the run [44, 49, 43] % (>= 10); foreign processes: 1 |
