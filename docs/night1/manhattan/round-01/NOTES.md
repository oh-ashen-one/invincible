# C Manhattan — round 01 notes (neutral facts)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Build: `python3 unreal/WebHomage/Scripts/build_manhattan.py` from an empty `Content/` on branch `night1/manhattan` (base 30d6926), all 8 steps,
~10 min total (city 7 min). P2 inputs staged from P2 HEAD `0ff9ec8` (P2 round 04). Map: `/Game/Maps/Manhattan` (golden rig).

## Files
| file | what |
|---|---|
| `route_30s.mp4` | 1920x1080, 60 fps, 29.95 s, `-movie` fixed 1/60 s step, `r.ScreenPercentage 100`, 0.8 s pre-roll trimmed (`capture_settings.json`) |
| `route_30s_telemetry.csv` | P3 per-frame telemetry of that run (1798 rows) |
| `route_check.json`, `anim_check.txt` | `../route_check.py` and P3 `docs/night1/traversal/anim_check.py` on the telemetry |
| `stills/route_NN_tSS.S.jpg` | 3840x2160 native (`r.ScreenPercentage 100`) stills of the same deterministic replay at t 4 / 10 / 16 / 24 s |
| `stills/view_S1.jpg`, `view_S2.jpg`, `view_S4.jpg` | 3840x2160 native stills from the P1 shot cameras (`Scripts/city_shots.json`) in `Manhattan_View_<S#>` at game t 14 s |
| `perf/` | P4 `run_perf.py` output (tsr67) + `perf_gpu.json` (GPU lock sidecar) |

## Route (scripts/route_30s.json), from route_check.json / anim_check.txt
- Start (249, 176) m on the avenue facing north; sprint, jump at 1.8 s, first web 2.6 s; end (262.1, -869.3) m; path 1084.8 m; max speed 61.8 m/s; max height 34.2 m.
- Modes: ground 2.2 s, swing 20.45 s, air 7.28 s; 18 web attaches.
- Fall-through: 0 frames (min feet height 1.113 m, min clearance over the floor below 0.163 m).
- Stuck: longest stretch under 1 m/s after the start 0.0 s; 0 windows with < 10 m net progress in 3 s; no wall/perch/zip segment > 3 s.
- T-pose / no-clip frames: 0. Air silhouettes at 6 fps: 25 pairs, 0 identical (min 0.281 m). Air cycles: 18, 0 consecutive identical.
- Camera inside geometry: 0 frames; hero occluded (> 2 % of his pixels): 0 frames.
- Detailed city block: the hero leaves it (y < -512 m) at t = 22.57 s; the last 7.4 s (444 frames) are over the park edge and far-LOD area
  (movie frames from ~22.6 s: flat dark ground plane, park tree masses, no street detail).

## Perf (one run, exclusive GPU lock)
`gpu_slot.sh perf` sidecar: exclusive true, waited 19.8 s, settle samples 10 (0-3 %), **util before 0 %, after 0 %**, during avg 81.9 % / max 100 % (this run),
Unreal instances before 1 (another piece's editor), max during 2, foreign captures during: none, `contaminated: false`, `perf_valid: true`.
P4's harness separately flagged one foreign CPU process during the run: a headless Blender (`tools/ue_char/eval/verify_fbx.py`, 97 % CPU, P2).

3840x2160 output, `r.ScreenPercentage 67` -> **internal 2573x1447** (TSR), Metal, fixed-step replay of the same route (`-benchmark -fps=60`),
window = the 30 s route (game t 15-45 s, after 15 s standing warm-up), 1800 frames:

| avg ms (fps) | p50 | p95 | p99 | max | hitches (> 25 ms and > 2x median) | frames > 16.67 ms | GPU avg / p95 ms | render thread avg | game thread avg |
|---|---|---|---|---|---|---|---|---|---|
| 51.99 (19.2) | 51.93 | 59.00 | 62.79 | 70.74 | 0 | 1800 / 1800 | 42.16 / 49.07 | 50.61 | 2.21 |

Best 5 s block 47.64 ms. Top GPU passes (avg ms): NaniteVisBuffer 10.13, LumenScreenProbeGather 7.53, ShadowDepths 5.81, Unaccounted 3.72,
Basepass 2.07, LumenSceneLighting 1.57, Postprocessing 1.44, VolumetricCloud 1.23. Render-thread time (50.6 ms) exceeds GPU time (42.2 ms).

## Stills (what is in them)
- view_S1: avenue at street level, golden rig; street people are present but small and in canyon shade; two figures readable behind props at the far left / right.
- view_S2: mid-height down the avenue; view_S4: high perch, skyline north-west with river and park.
- route stills: hero in frame at t 4 / 10 / 16 s; t 24 s is past the detailed block.

## Not done this round
- No critic pass (piece C round 01 is integration + evidence). No midday / night captures (maps build; not captured).
