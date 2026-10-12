# P6 City life round 02: GPU-locked perf (S1 street view, Life_View_S1, game t = 22-52 s)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Every run: `gpu_slot.sh perf` (exclusive, waited for GPU < 15 % for 10 s, `contaminated=false`), Mac Studio M3 Ultra, Metal SM6, golden-hour rig, **3840x2160 output, `r.ScreenPercentage 67` (TSR, internal 2573x1447)**. Frame times include everything else in the P1 / P4 scene (Lumen, VSM, ...); read the DIFFERENCE between rows. Run-to-run spread of the scene itself is a few ms (round 01 measured up to 9 ms between two identical 4K runs), so the difference of single runs is indicative, not exact. Budget from the brief: <= 3 ms GPU.

| variant | frames | avg ms | p95 | p99 | GPU avg ms | GPU util before / during avg | valid |
|---|---|---|---|---|---|---|---|
| life off (`-WHLifeOff`: no traffic, no crowd, no signal lenses) | 933 | 32.18 | 37.28 | 38.00 | 29.96 | 0 % / 80 % | perf_valid |
| life ON (default: traffic 2.3 x browser density, ~1130 camera-centred walkers, lit signal lenses) | 898 | 33.41 | 38.56 | 40.18 | 31.70 | 0 % / 77 % | perf_valid |

Life ON minus OFF: **+1.73 ms GPU**, +1.23 ms frame (avg), +1.27 ms p95 frame.

