| config | output | internal (pre-TSR) | avg ms (fps) | best 5 s block ms | p50 | p95 | p99 | max | hitches (>25 ms & >2x median) | >16.7 ms | GPU avg ms | GPU util before % | contaminated |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tsr50 (r.ScreenPercentage 50) | 3840x2160 | 1920x1080 | 23.86 (41.9) | 23.26 | 23.58 | 29.09 | 37.32 | 65.26 | 7 | 1230/1257 | 22.48 | 47/100/100 | YES: GPU utilisation before the run [47, 100, 100] % (>= 10) |
| tsr67 (r.ScreenPercentage 67) | 3840x2160 | 2573x1447 | 31.83 (31.4) | 29.89 | 31.22 | 37.64 | 42.83 | 199.62 | 3 | 940/943 | 28.87 | 0/0/0 | YES: ; foreign processes: 1 |
| native100 (r.ScreenPercentage 100) | 3840x2160 | 3840x2160 | 53.36 (18.7) | 44.63 | 47.50 | 81.59 | 90.33 | 94.80 | 0 | 563/563 | 50.20 | 0/35/51 | YES: GPU utilisation before the run [0, 35, 51] % (>= 10); foreign processes: 1 |
