| config | output | internal (pre-TSR) | avg ms (fps) | best 5 s block ms | p50 | p95 | p99 | max | hitches (>25 ms & >2x median) | >16.7 ms | GPU avg ms | GPU util before % | contaminated |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| base_a (r.ScreenPercentage 50) | 3840x2160 | 1920x1080 | 23.79 (42.0) | 22.69 | 23.31 | 28.67 | 31.49 | 52.60 | 1 | 1799/1800 | 22.27 | 14/0/0 | YES: GPU utilisation before the run [14, 0, 0] % (>= 10) |
| sw_lumen (r.ScreenPercentage 50) | 3840x2160 | 1920x1080 | 22.27 (44.9) | 20.59 | 21.90 | 26.82 | 29.73 | 58.89 | 1 | 1789/1800 | 21.59 | 56/58/58 | YES: GPU utilisation before the run [56, 58, 58] % (>= 10) |
| no_volfog (r.ScreenPercentage 50) | 3840x2160 | 1920x1080 | 22.80 (43.9) | 21.66 | 22.29 | 27.77 | 30.44 | 62.04 | 2 | 1793/1800 | 21.37 | 29/25/25 | YES: GPU utilisation before the run [29, 25, 25] % (>= 10) |
| no_clouds (r.ScreenPercentage 50) | 3840x2160 | 1920x1080 | 22.81 (43.8) | 19.86 | 22.08 | 28.22 | 31.37 | 72.04 | 4 | 1794/1800 | 21.19 | 20/25/25 | YES: GPU utilisation before the run [20, 25, 25] % (>= 10) |
| no_flare_mblur (r.ScreenPercentage 50) | 3840x2160 | 1920x1080 | 23.32 (42.9) | 21.91 | 22.35 | 27.60 | 49.10 | 170.42 | 22 | 1796/1800 | 21.59 | 21/30/19 | YES: GPU utilisation before the run [21, 30, 19] % (>= 10) |
| no_dfshadow (r.ScreenPercentage 50) | 3840x2160 | 1920x1080 | 30.71 (32.6) | 21.55 | 27.63 | 46.46 | 54.21 | 63.64 | 12 | 1798/1800 | 28.52 | 8/28/19 | YES: GPU utilisation before the run [8, 28, 19] % (>= 10) |
| probe32 (r.ScreenPercentage 50) | 3840x2160 | 1920x1080 | 23.01 (43.5) | 21.82 | 22.58 | 28.10 | 31.77 | 43.55 | 0 | 1772/1800 | 21.50 | 100/100/100 | YES: GPU utilisation before the run [100, 100, 100] % (>= 10) |
| base_b (r.ScreenPercentage 50) | 3840x2160 | 1920x1080 | 28.03 (35.7) | 22.60 | 25.08 | 41.07 | 48.68 | 64.25 | 13 | 1796/1800 | 25.68 | 5/6/6 | YES: ; foreign processes: 1 |
