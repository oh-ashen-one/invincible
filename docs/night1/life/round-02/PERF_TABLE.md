# P6 City life round 02: GPU-locked perf (S1 street view, Life_View_S1, game t = 22-52 s)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Every run: `gpu_slot.sh perf` (exclusive, waited for GPU < 15 % for 10 s, `contaminated=false`), Mac Studio M3 Ultra, Metal SM6, golden-hour rig, **3840x2160 output, `r.ScreenPercentage 67` (TSR, internal 2573x1447)**. Frame times include everything else in the P1 / P4 scene (Lumen, VSM, ...); read the DIFFERENCE between rows. Run-to-run spread of the scene itself is a few ms (round 01 measured up to 9 ms between two identical 4K runs), so the difference of single runs is indicative, not exact. Budget from the brief: <= 3 ms GPU.

| variant | frames | avg ms | p95 | p99 | GPU avg ms | GPU util before / during avg | valid |
|---|---|---|---|---|---|---|---|
| life off (`-WHLifeOff`: no traffic, no crowd, no signal lenses) | 942 | 31.86 | 36.95 | 38.94 | 29.76 | 0 % / 78 % | perf_valid |
| life ON (default: traffic 2.3 x browser density, ~1460 camera-centred walkers of which about 500 are live skinned meshes, 100 looks, lit signal lenses) | 860 | 34.87 | 40.79 | 42.08 | 32.61 | 0 % / 80 % | perf_valid |

Life ON minus OFF: **+2.85 ms GPU**, +3.01 ms frame (avg), +3.84 ms p95 frame.


The life actors cost **+2.85 ms GPU** at the edge of the 3 ms budget; round 01's bisect (traffic only ~0, crowd only +1.4 ms frame, life total +2.0 ms GPU with 290 live walkers at 4K) points at the ~500 live skinned walkers; the round-02 crowd-only / traffic-only variants were not re-run. The scene without any life is already 29.8 ms GPU at 4K / 67 % (about 34 fps), so the 60 fps budget belongs to the city / look pieces and the perf piece, not to P6. Two runs, one each, both exclusive and not contaminated; the "on" run waited 30 minutes twice (the first attempt timed out in the queue with exit 75 and did not run). The pre-interruption WIP runs (life ON +1.73 ms GPU with ~1130 walkers and 60 looks) are in `wip_perf_pre_interruption/`.
