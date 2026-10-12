# P6 City life round 01: GPU-locked perf (S1 street view, Life_View_S1, game t = 22-52 s)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Every run: `gpu_slot.sh perf` (exclusive, waited for GPU < 15 % for 10 s, `contaminated=false`), Mac Studio M3 Ultra, Metal SM6, golden-hour rig, `r.ScreenPercentage 100` (NATIVE internal resolution = output resolution, so 1080p is 1920x1080 internal and 4K is 3840x2160 internal; the project default would render 4K at 67 % / 50 %). Frame times include everything else in the P1 / P4 scene (Lumen, VSM, ...), which alone is ~21 ms GPU at native 1080p; read the DIFFERENCE between rows. Run-to-run spread is a few ms (the two 4K "life off" runs differ by 9 ms).

## 1920x1080

| variant | frames | avg ms | p95 | p99 | GPU avg ms | GPU util before / during avg | valid |
|---|---|---|---|---|---|---|---|
| life off (`-WHLifeOff`: no traffic, no crowd), run 1 | 1321 | 22.70 | 27.50 | 29.74 | 20.48 | 0 % / 78 % | perf_valid |
| life ON, ray-tracing visible (first build: `-WHLifeRT`) | 774 | 38.77 | 41.23 | 43.17 | 34.74 | 0 % / 78 % | perf_valid |
| life ON (default now: instances invisible to ray tracing) | 1272 | 23.59 | 28.61 | 29.90 | 22.62 | 0 % / 80 % | perf_valid |
| life ON, no shadows from life actors (`-WHLifeNoShadow`) | 1235 | 24.29 | 29.31 | 30.54 | 22.01 | 0 % / 79 % | perf_valid |
| traffic only (`-WHCrowdOff`) | 1330 | 22.57 | 27.37 | 28.45 | 21.07 | 0 % / 77 % | perf_valid |
| crowd only (`-WHTrafficOff`) | 1244 | 24.13 | 29.25 | 30.08 | 21.81 | 0 % / 80 % | perf_valid |

## 3840x2160

| variant | frames | avg ms | p95 | p99 | GPU avg ms | GPU util before / during avg | valid |
|---|---|---|---|---|---|---|---|
| life off, run 1 | 465 | 64.43 | 113.68 | 130.08 | 61.72 | 0 % / 80 % | perf_valid |
| life off, run 2 (repeat: run 1 is a slow outlier) | 542 | 55.38 | 60.67 | 101.53 | 52.64 | 0 % / 81 % | perf_valid |
| life ON, ray-tracing visible (first build) | 372 | 80.79 | 144.23 | 150.94 | 78.30 | 0 % / 74 % | perf_valid |
| life ON (default now) | 516 | 58.09 | 63.10 | 79.84 | 54.64 | 0 % / 80 % | perf_valid |

