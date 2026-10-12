# Browser game performance ("before")

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

**Read this first: every number below is contaminated.** The Mac Studio GPU was shared with other sessions' Unreal editors (traversal, city, characters pieces), stuck `CrashReportClient` processes, a Blender and another agent's Chrome. `ioreg -r -d 1 -c IOAccelerator` "Device Utilization %" read **99-100 % before Chrome was even launched in 9 of the 12 runs** and 56-62 % in the other 3; the first pass (before GPU timers were added) saw 40-100 %. The same scenario at the same resolution varied by up to 2x from run to run (street at 3840x2160: rAF median 12.2 ms in the first pass, 28.2 / 26.5 / 16.2 ms in three later runs). Treat these as a pessimistic bound and a way to compare scenarios and resolutions, not as the browser game's ceiling. A quiet-GPU re-run is the first open item (`QUIET_WAIT=<s>` in `tools/playtest.mjs` waits for < 25 %; it never got there tonight).

## Method

- **Machine / browser:** Mac Studio, Apple M3 Ultra (80-core GPU), Chrome 154 through Playwright `channel: 'chrome'` in new headless mode (`--headless=new` equivalent), ANGLE Metal, GPU on (`--use-angle=metal --enable-gpu --ignore-gpu-blocklist`), `WEBGL_debug_renderer_info` = `ANGLE (Apple, ANGLE Metal Renderer: Apple M3 Ultra)`. Own scratch profile under `_scratch/baseline/`, dev server on port 5201, quality `high`, `renderScale` 1 (defaults).
- **Real rendering, not throttled:** the game's own real-time loop (`renderer.setAnimationLoop`, `manualStep` off); flags `--disable-renderer-backgrounding --disable-backgrounding-occluded-windows --disable-background-timer-throttling --disable-frame-rate-limit --disable-gpu-vsync`. There is no display, so there is no vsync quantisation: numbers are uncapped, not "locked 60".
- **Two instruments per run:** (1) `requestAnimationFrame` deltas from an in-page logger (the "rAF" columns; every frame counted, first frame dropped); (2) GPU time per frame from `EXT_disjoint_timer_query_webgl2` wrapped around `pipeline.render()` (the whole scene + post chain, no JS world / player update). rAF deltas alone can under-report when the browser does not throttle to GPU completion, so the GPU column is the one to trust for "is it GPU bound"; under time-slicing with another process it over-reports. Truth for a quiet machine lies below the GPU column and above the rAF column.
- **Scenarios** (same scripts as the clips, real key / mouse events, wall-clock paced; `tools/playtest.mjs`): `swingChain` (20 s swing chain down the avenue), `street` (steered sidewalk sprint + Shift parkour run, 29 s), `fight` (8 thugs, combo / dodge / web / finisher rounds, 26 s), `water` (Hudson seawall run, dive, swing, 14 s), `crowd` (dog walker / critter walk, 18 s). `wallRun`, `trickZip`, `skins` were filmed only. One scenario per Chrome launch.
- **GPU utilisation:** read once before Chrome is launched (external load only), sampled every 1.5 s during the run (includes this game) and once after; stored per run in `perf/*.json` (`gpuUtil`). A run is flagged CONTAMINATED when the external reading before launch is > 25 % or missing.
- **Harness overhead:** the runner polls player state every 15 ticks and, in `street` / `crowd`, evaluates one steering call per tick (about 1 ms of main thread), so those two carry slightly more JS load than free play.

## Internal resolution and pixel ratio

`renderer.setPixelRatio(min(devicePixelRatio, 1.5))` (`src/main.js:29`), times the Settings "Render Resolution" `renderScale` (0.6-1.25, default 1; `src/game/systems/index.js:86`). `pipeline.setSize` sizes the scene, AO, lit, TAA-history and post targets at css size x pixelRatio, and the sky, DOF, SSR, light-shaft and SSGI targets at half of that (`src/render/pipeline.js:1201`). Measured with `renderer.getPixelRatio()` / `getDrawingBufferSize()` at the start and end of every run (no dynamic resolution: identical at both ends):

| context | css px | devicePixelRatio | pixel ratio used | drawing buffer (full-res passes) | half-res passes (SSR, shafts, SSGI, DOF) |
|---|---|---|---|---|---|
| native 4K | 3840x2160 | 1 | 1 | **3840x2160** | 1920x1080 |
| 1080p | 1920x1080 | 1 | 1 | **1920x1080** | 960x540 |
| 1080p css on a 4K panel (macOS default scaled mode) | 1920x1080 | 2 | 1.5 (capped) | **2880x1620** (75 % of native 4K per axis, 56 % of the pixels) | 1440x810 |
| (not measured; same pixel count as native 4K) | 2560x1440 | 1.5 | 1.5 | 3840x2160 | 1920x1080 |

So "4K output" from this game needs a 3840x2160 css viewport at DPR 1 or a 2560x1440 css viewport at DPR 1.5; a 4K panel at its default 1920x1080 @2x renders 2880x1620 and upscales in the browser.

## Results (real-time, GPU shared: all rows CONTAMINATED)

| scenario | viewport @DPR | drawing buffer (pixelRatio) | frames | rAF median ms | p95 | p99 | max | >33 ms | >50 ms | >100 ms | rAF fps | GPU ms median / p95 / p99 | external GPU util before launch / mean during | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| swingChain | 3840x2160 @1 | 3840x2160 (1) | 876 | 24.3 | 65.8 | 182.7 | 1115.7 | 265 | 117 | 13 | 32.5 | 52.86 / 91.31 / 115.29 | 100% / 99.8% | CONTAMINATED |
| street | 3840x2160 @1 | 3840x2160 (1) | 1109 | 28.2 | 66 | 69.8 | 1013 | 363 | 159 | 7 | 33.8 | 50.87 / 74.64 / 93.46 | 100% / 99.1% | CONTAMINATED |
| fight | 3840x2160 @1 | 3840x2160 (1) | 1024 | 30.2 | 66.5 | 86.2 | 481.9 | 356 | 177 | 9 | 31.1 | 55.76 / 78.31 / 90.92 | 100% / 99.6% | CONTAMINATED |
| water | 3840x2160 @1 | 3840x2160 (1) | 713 | 15.5 | 51.3 | 229.1 | 567.5 | 141 | 44 | 11 | 41.1 | 37.93 / 64.12 / 79.91 | 56% / 99.5% | CONTAMINATED |
| crowd | 3840x2160 @1 | 3840x2160 (1) | 1807 | 20.8 | 50.7 | 65.8 | 501 | 374 | 97 | 7 | 41.2 | 46.33 / 71.39 / 84.94 | 99% / 99.3% | CONTAMINATED |
| swingChain | 1920x1080 @1 | 1920x1080 (1) | 1128 | 15.6 | 50.2 | 63.8 | 415.5 | 198 | 57 | 6 | 45.3 | 29.96 / 51.15 / 64.06 | 99% / 99.1% | CONTAMINATED |
| street | 1920x1080 @1 | 1920x1080 (1) | 2087 | 10.6 | 31.8 | 49.6 | 444.9 | 86 | 19 | 6 | 67.7 | 15.65 / 41.15 / 55.71 | 100% / 99.3% | CONTAMINATED |
| fight | 1920x1080 @1 | 1920x1080 (1) | 1272 | 17.2 | 50.4 | 69.5 | 396.7 | 268 | 70 | 8 | 41.2 | 31.68 / 57.3 / 73.43 | 100% / 99% | CONTAMINATED |
| water | 1920x1080 @1 | 1920x1080 (1) | 1027 | 12.1 | 32.6 | 49.7 | 460.6 | 43 | 10 | 9 | 63.3 | 18.61 / 35.47 / 44.34 | 62% / 98.3% | CONTAMINATED |
| crowd | 1920x1080 @1 | 1920x1080 (1) | 2127 | 12 | 33.1 | 46 | 417.8 | 93 | 10 | 3 | 61.2 | 26.95 / 41.69 / 53.74 | 61% / 99.6% | CONTAMINATED |
| swingChain | 1920x1080 @2 | 2880x1620 (1.5) | 976 | 24.7 | 51.5 | 99.8 | 452.1 | 247 | 59 | 9 | 38.4 | 43.44 / 69.2 / 80.22 | 99% / 100% | CONTAMINATED |
| street | 1920x1080 @2 | 2880x1620 (1.5) | 1733 | 13 | 36 | 50.2 | 428.1 | 141 | 20 | 4 | 56.5 | 25.56 / 46.3 / 58.75 | 99% / 99.5% | CONTAMINATED |

Repeat runs of the same scenario at 3840x2160 (run-to-run noise under the shared GPU):

| scenario | run | rAF median / p95 ms | GPU ms median / p95 | >33 ms | external GPU util before / mean during |
|---|---|---|---|---|---|
| swingChain | r1 | 24.3 / 65.8 | 52.86 / 91.31 | 265 | 100% / 99.8% |
| swingChain | r2 | 29 / 67.4 | 57.89 / 94.41 | 286 | 100% / 99.8% |
| swingChain | r3 | 24.7 / 67.1 | 54.16 / 90.91 | 266 | 100% / 99.9% |
| swingChain | spread | rAF median 24.3-29 | GPU median 52.86-57.89 | | |
| street | r1 | 28.2 / 66 | 50.87 / 74.64 | 363 | 100% / 99.1% |
| street | r2 | 26.5 / 59.3 | 49.6 / 83.15 | 306 | 100% / 100% |
| street | r3 | 16.2 / 47.7 | 34.64 / 60.97 | 234 | 100% / 99.7% |
| street | spread | rAF median 16.2-28.2 | GPU median 34.64-50.87 | | |

Worst frame gaps (>50 ms) in each run, "seconds since the rAF logger started : ms" (the first one is the scenario start: teleport + streaming):
- swingChain_3840x2160: 1.2s:1116ms, 5.8s:289ms, 5.3s:278ms, 7.1s:269ms, 10.1s:263ms  (last frame: 474 draw calls, 10,980,854 triangles)
- street_3840x2160: 1.0s:1013ms, 5.8s:264ms, 9.9s:243ms, 31.3s:214ms, 2.6s:196ms  (last frame: 716 draw calls, 14,468,148 triangles)
- fight_3840x2160: 0.5s:482ms, 2.3s:322ms, 7.1s:263ms, 11.9s:262ms, 4.1s:251ms  (last frame: 847 draw calls, 16,147,851 triangles)
- water_3840x2160: 0.6s:568ms, 5.6s:281ms, 2.0s:278ms, 7.8s:264ms, 8.7s:261ms  (last frame: 661 draw calls, 12,348,822 triangles)
- crowd_3840x2160: 0.5s:501ms, 38.0s:334ms, 5.7s:199ms, 2.1s:171ms, 4.9s:164ms  (last frame: 677 draw calls, 14,121,083 triangles)
- swingChain_1920x1080: 0.5s:416ms, 14.0s:228ms, 4.8s:150ms, 17.5s:149ms, 1.8s:136ms  (last frame: 667 draw calls, 13,369,321 triangles)
- street_1920x1080: 0.5s:445ms, 8.7s:235ms, 2.0s:161ms, 4.8s:154ms, 1.8s:105ms  (last frame: 502 draw calls, 11,484,634 triangles)
- fight_1920x1080: 0.4s:397ms, 2.0s:221ms, 18.6s:203ms, 26.6s:199ms, 11.2s:172ms  (last frame: 801 draw calls, 15,199,020 triangles)
- water_1920x1080: 0.5s:461ms, 1.8s:206ms, 5.2s:184ms, 3.3s:172ms, 4.8s:160ms  (last frame: 621 draw calls, 10,370,400 triangles)
- crowd_1920x1080: 0.4s:418ms, 29.1s:171ms, 2.0s:152ms, 4.1s:88ms, 4.1s:84ms  (last frame: 551 draw calls, 11,666,200 triangles)
- swingChain_1920x1080_dpr2: 0.5s:452ms, 8.5s:227ms, 6.3s:210ms, 12.9s:193ms, 4.6s:177ms  (last frame: 636 draw calls, 11,912,817 triangles)
- street_1920x1080_dpr2: 0.5s:428ms, 4.8s:151ms, 1.9s:147ms, 8.6s:138ms, 2.1s:76ms  (last frame: 469 draw calls, 10,783,299 triangles)

Draw load in the last frame of each run (from `renderer.info`): 470-850 draw calls and 10.4-16.1 million triangles per frame, largest in `fight` (thugs + street) and `street` (crowd + traffic).

### First pass, rAF only (no GPU timers; same scenarios; `perf/v1_raf_only/*.json`)

| scenario | 3840x2160 median / p95 / p99 ms (>33 ms frames) | 1920x1080 median / p95 / p99 ms (>33 ms) | external GPU util before (4K / 1080p) |
|---|---|---|---|
| swingChain | 19.0 / 52.0 / 80.9 (289) | 12.5 / 31.3 / 43.5 (30) | 42 % / 68 % |
| street | 12.2 / 32.7 / 48.6 (76) | 11.3 / 33.2 / 47.2 (95) | 40 % / 100 % |
| fight | 28.6 / 51.7 / 70.5 (371) | 22.8 / 51.2 / 84.6 (292) | 72 % / 99 % |
| water | 13.8 / 47.6 / 189.6 (126) | 14.8 / 49.0 / 133.6 (108) | 66 % / 100 % |
| crowd | 14.0 / 39.1 / 52.8 (321) | 15.9 / 46.0 / 54.8 (359) | 58 % / 100 % |

1080p @DPR2 (2880x1620): swingChain 14.5 / 35.5 / 54.2 ms (135 frames > 33 ms), street 11.8 / 32.9 / 47.7 ms (88). The first pass looks better than the second at 3840x2160 because the external load was lower (40-72 % vs 99-100 %), which is the point: the machine, not the game, moved these numbers.

### GPU-serialised cost of the `?shot=` compositions (`tools/perf.mjs`, 150 frames each, 1-pixel readback forces the GPU to finish every frame; `perf/shots_perf.txt`)

```
## shots at 3840x2160 (DPR1), external GPU util before launch: 55%
street                   frame median 52.70 ms  p95 60.90 ms  (cpu submit 9.64 ms)
swing                    frame median 38.70 ms  p95 44.60 ms  (cpu submit 7.85 ms)
swingBack                frame median 38.40 ms  p95 43.60 ms  (cpu submit 9.09 ms)
parkHigh                 frame median 43.60 ms  p95 55.30 ms  (cpu submit 7.02 ms)
riverHigh                frame median 29.80 ms  p95 35.90 ms  (cpu submit 7.16 ms)
## shots at 1920x1080 (DPR1), external GPU util before launch: 97%
street                   frame median 33.70 ms  p95 46.10 ms  (cpu submit 9.31 ms)
swing                    frame median 36.70 ms  p95 45.90 ms  (cpu submit 8.11 ms)
swingBack                frame median 38.50 ms  p95 47.40 ms  (cpu submit 9.12 ms)
parkHigh                 frame median 29.60 ms  p95 37.70 ms  (cpu submit 6.58 ms)
riverHigh                frame median 19.40 ms  p95 23.10 ms  (cpu submit 7.27 ms)
```
The CPU submit cost (world update + lighting + pipeline command submission) is 6.6-9.6 ms per frame in every composition, i.e. below the 16.7 ms budget with the JS side idle in between; the frame cost at 3840x2160 is GPU, not CPU. (The 1080p rows were measured with the external GPU load at 97 %, which is why they do not scale down from 3840x2160.)

## What the numbers say, and do not say

- **Not proven: 60 fps at 3840x2160.** Every 3840x2160 run averaged 31-41 fps by rAF (median frame 15.5-30.2 ms, p95 50.7-66.5 ms) with 20-35 % of frames over 33 ms (`fight`: 356 of 1024; `street`: 363 of 1109; `swingChain`: 265 of 876; `crowd`: 374 of 1807; `water`: 141 of 713) and a GPU time of 38-56 ms per frame at the median (2.3-3.3x the 16.7 ms budget). Even if the other sessions took half the GPU, a quiet 3840x2160 frame would still be around 20-28 ms; no measurement supports 60 fps at native 4K in the traversal and fight scenarios.
- **1920x1080 is closer:** 41-68 fps by rAF (median 10.6-17.2 ms), GPU 15.7-31.7 ms at the median, 4-21 % of frames over 33 ms (`street`, `water`, `crowd` about 4 %; `swingChain` 17.5 %; `fight` 21 %). `fight` is the heaviest scenario at every resolution (thugs, FX, 16 M triangles); `street` and `water` the lightest.
- **Resolution scaling is real but hidden by contention:** street GPU median 15.7 ms at 1080p vs 50.9 ms at 4K (3.3x for 4x the pixels); 2880x1620 lands between (25.6 ms).
- **Hitches independent of resolution:** each run opens with a 400-1100 ms gap in the first 0.5-1.2 s (the scripted teleport into a new part of the city: streaming plus first-use shaders), and then has 3-13 frames over 100 ms in every 14-29 s run, with individual gaps of 170-330 ms at both resolutions (top gaps per run are listed above). Free play never teleports, but chained swings into unseen blocks are the same streaming path.
- **The 17-sampler hero program** (`PLAYTEST.md` bug 3) fires 90 warnings per second of play; whether it also costs frame time was not isolated.
- **Frame-time budget for the Unreal port:** the browser reference at 1080p is about 16-32 ms GPU on a loaded machine and about 8-16 ms if the other load took half; it is not an upper bound for what the M3 Ultra can do.

## Raw data

`perf/*.json` (one file per run: stats, GPU utilisation samples, every raw rAF delta `rawFrameTimes` and GPU time `rawGpuMs`, render info at start and end), `perf/v1_raf_only/`, `perf/shots_perf.txt`. Regenerate the tables with `python3 docs/night1/baseline/tools/perf_table.py`.
