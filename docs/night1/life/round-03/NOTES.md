# P6 City life round 03: notes

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

**Status: code done and pushed, final round captures NOT taken.** At 06:55:42 the macOS WindowServer hit its watchdog (`/Library/Logs/DiagnosticReports/WindowServer-2026-09-30-065542.ips`,
`WindowServer_2026-09-30-065550_midirstudio.userspace_watchdog_timeout.spin`: main thread blocked in Metal / IOGPU for 40 s while three engines (this piece's swing run, city, combat) and the
always-busy GPU were running) and restarted. Since then the GUI session cannot start any Cocoa app: `NSApplication run` never delivers `applicationDidFinishLaunching`, so **every Unreal process
(`UnrealEditor`, `UnrealEditor-Cmd`, `-nullrhi` commandlets, `open -n` or launchd-submitted) hangs at 0.9 s CPU with no log** (`sample` of the hung processes: main thread in `-[NSApplication run]` waiting for a
mach message). New WindowServer pid 22610 had used 0.06 s CPU after 36 min (it never got a session), `system_profiler SPDisplaysDataType` lists no display, and a 20-line Swift `NSApplication.run()` program
hangs the same way (`_scratch/life/r03work/ns_test2.swift`). Nothing a session can fix without the owner (log in again / reboot); nothing of another session was touched.
My own hung engine (g9, swing B run, state UN, log silent since 06:54:14) and one hung commandlet were stopped with `stop_ue.sh` (SIGTERM, "stopped cleanly"); no engine, driver script or lock of this piece is left.
The map / content rebuild and the final capture batch therefore could not run after 06:54. What exists is the set of experiment runs below (real `-game`, offscreen, inside `gpu_slot.sh capture`, 06:21-06:54, builds of this branch as of each run),
which is the evidence for the code that is committed, plus a critic pack built from them.

## What changed in the code (all under `Source/WebHomage/Life`, `Scripts/build_life.py`, `tools/life`)

| change | why (critic r02 biggest gap: populate both sidewalks at every camera height) |
|---|---|
| **Character fill light** (`AWHLifeCrowd`, `FillLux` 1800 lux, 5200 K, channel 1, unshadowed, no GI) applied **only to walkers the sun does not reach** (a line trace towards the atmosphere sun light per live walker, about once a second, 24 per tick at most) | the walkers of the right (east) sidewalk stand under P1's green scaffolding shed in deep shade: the probe found ~50 of them >= 20 px and unoccluded, YOLO 2-5 (dark cut-outs). Sweep: 0 lux no readable people, 1500-2500 natural, 4000+ chalky (`stills/g4_s1_sweep_*`), all-walker fill 6000 glows (`stills/e2_*`) |
| **Fast-camera recycling** (camera speed > 5 m/s): walkers 60 m or more behind the camera (budget 28 per refresh) and beyond the disc are recycled to the sidewalks AHEAD (ring 62-98 % of the disc radius, within 60 deg of the velocity) | round 02 recycled only off-screen: a 25 m/s swing outran the population, 0 people in 20 of 20 samples. Experiment g8 (before the recycle-behind fix): 176 hand-countable people within 80 m at the start, 13-20 at 8-10 s, 3-4 after 10.5 s (the flight starts at the edge of the city, where the disc is half empty and the trailing walkers are not 213 m behind yet) |
| **Population disc 190 m** (was 130), live radius grows from 110 m to 180 m with camera height (12 m -> 32 m), far walkers step every 4th tick with 4 x dt, `MaxWalkers` 6000 with uniform thinning (never truncation) | S2 (42 m up) and swing cameras see people much farther down the avenue |
| Density 1600 / 1100 per km (was 1300 / 860), `NearAllRadius` 10 m (was 22 m: ~90 walkers behind a street camera were live for nothing) | more people in view for the same live budget |
| **Curb gaps** (`AWHLifeTraffic::ParkedGap*`): bus stop / loading zone on the far side of avenue-curb streets, 36 m, half of the (curb, street) pairs (seed 38), ~4 % of all parked cars | the three parked cars of the S1 east curb (z 122-144) hid the near part of the right sidewalk: experiment g3 (proxy: the same cars removed with `-WHLifeClearParked`) right share 39 % vs 21 % |
| Stills corridor `-WHLifeClearAhead=24` (half width 12.5 m) for the S1 stills only | a moving box truck in the curb lane at t = 20 s covered the right sidewalk in every run |
| Swing camera: 22 m up, aimed at the ground 70 m ahead (`AWHLifeCamRig::AimAheadCm`), 88 deg | round 02: 30 m up, aimed 150-400 m away: the street was a sliver under the buildings, cars 28 px vs 51 px in the reference, nothing to count. Experiment g8 stills show both sidewalks and 4-6 lanes |
| Keep-right lanes (78 % of walkers) + sidestep around walkers ahead (`UpdateAvoidance`) | critic r02: walkers interpenetrate, single file |
| Crowd waits for the crosswalk to clear of car bodies (`AnyCarNearSegment`) | critic r02: a pickup stopped on a crosswalk with people at its bed |
| Probe: people >= 20 px unoccluded, left / right of the view axis, within 80 m (`WH_LIFE_FRAME` / `WH_LIFE_SAMPLE`); detector: left / right split, `--crop 0.84`; `spec_table.py` round-03 rows; `summarize_exp.py` | the new target is a per-side count |
| Taxi label "NYC TAXI" repainted "CITY TAXI" in the atlas (`prep_vehicles.py`; applies at the next `content` step) | critic r02 brand note |

## Experiment results (`experiments/TABLE.md`, `experiments/stills`, `experiments/data`)

YOLO11x-seg (spec instrument, CPU), 1080p stills at game t = 12 / 16 / 20 / 24 / 28 s, "right" = box centre in the right half of the frame. Round 02 (critic): 0-17 % (S1 published still 5 of 30).

| run | build | people (5 stills) | right share % per still (median) | critic 84 % crop (median) |
|---|---|---|---|---|
| e1 | density 1300, the fill-sweep argument was mis-parsed (fill 0 all run), near-all 10 m | 31, 28, 24, 24, 33 | 6, 11, 4, 0, 21 (**6**) | 7 |
| e2 | 2000 / 1300, fill 6000 lux on everyone | 33, 44, 36, 45, 48 | 18, 25, 8, 40, 31 (**25**) | 21 |
| e3 | 2800 / 1700, fill 6000 lux | 29, 35, 38, 43, 39 | 0, 20, 13, 26, 28 (**20**) | 12 |
| g1 | 1600 / 1100, shade-only fill 2500 | 34, 32, 37, 43, 42 | 21, 19, 16, 40, 38 (**21**) | 29 |
| g2 | as g1, 4500 lux | 34, 34, 31, 38, 49 | 18, 26, 13, 34, 39 (**26**) | 23 |
| g5 | as g1, 2500 lux on everyone | 32, 36, 35, 38, 38 | 22, 33, 9, 32, 29 (**29**) | 25 |
| **g3** | as g1 + the near parked cars of the east curb removed (curb-gap proxy) | 36, 41, 30, 42, 44 | 28, 39, 17, 43, 45 (**39**) | **42** |

Reading: the fill lifts the right share from ~6 % to 21-29 %, the removal of the near parked cars to 39 %; the one still that stays low (t = 20) has a moving box truck (Metro shipping) in the curb lane
12-25 m ahead, which the new 24 m corridor removes. The engine probe counts **~50 unoccluded people >= 20 px on the right** (57 on the left) within 80 m in every S1 frame: the crowd is there; YOLO
sees only those that are large, lit and not behind a car. **The 35 % target is met on the median only by g3 (39 % / 42 % cropped), and only by 4 of 5 frames; it is not proven for the final build (defaults changed
after g3: fill 1800, curb-gap rule instead of the proxy, corridor 24 m).**
S1 people per still are 30-49 (>= 16 by the brief).

S2 (fixed camera 42 m up, 1080p / 4K): engine probe people >= 20 px unoccluded 19-27 (1080p, left 14-19 / right 5-8) and 33-43 (4K, left 30-36 / right 4-11); **hand count on the 4K still `g7` (t = 28 s), sidewalks of the
nearest block: about 40 on the west sidewalk (a tight file along the storefronts), about 9 on the east sidewalk (under the tree canopy and the shed) = about 49, target >= 15.** YOLO finds 0-7 people at S2 (they are 35-50 px tall at 4K, 18-25 px at 1080p);
vehicles 16-21. The east sidewalk of S2 is populated but half hidden by the P1 tree; the west one is a dense file (1.6 walkers per metre in a 2.5 m band), a little parade-like.

Swing (experiment g8, 22 m up, aimed 70 m ahead, real-time flight): frames show both sidewalks, 4-6 lanes, buses / taxis 35-60 px; probe people >= 20 px within 80 m: 44 / 79 / 146 / 176 / 155 / 88 / 81 / 72 / 45 / 48 / 58 (t = 2.5-7.6 s), 14 / 18 / 20 / 22 / 13 (t = 8-10 s),
4 / 4 / 4 (t >= 10.5 s). The fall-off is the start-of-flight supply hole described above; **the recycle-behind rule and the wider ring (62-98 %) were added after g8 and are unverified in the engine.**
The swing A/B without the ahead recycling (g10) and the second swing camera (g9) did not run (WindowServer incident).

## Not done (needs a working GUI session)

1. `python3 unreal/WebHomage/Scripts/build_life.py --steps content` (atlas repaint) and `--steps map` (the swing rig is also passed on the command line by `capture_round.sh`, so the map rebuild is optional).
2. A verification run of the swing rig (`Life_Swing_Clip`, `-WHLifeSample=2.5:12.5:0.5`): every sample should show >= 15 people within 80 m.
3. `docs/night1/life/capture_round.sh docs/night1/life/round-03 stills clips detect` (each call inside one `gpu_slot.sh capture` hold; the script refuses to start an engine when `_scratch/life/bin/gui_ok.sh` says the session cannot launch apps), then
   `tools/life/spec_table.py`, `perf_variants.sh` (fill light + shade traces + 190 m disc are new GPU / CPU cost: measure life ON vs OFF; budget <= 3 ms GPU), `hand_counts.json` (by-eye counts of the S2 4K still and of a few swing frames), the critic pack.

## Critic pack

`/Users/midir/sm2-n1/_scratch/critic-P6-r03/pack` (key outside it: `pack.key.json`; `pairs.json`; built with `tools/night1/abpack.py`). Because the final captures do not exist it is built from the experiment frames (all real game, 1080p unless noted):
avenue-street = `g3` S1 t = 28 s (1080p), sidewalk = `g3` t = 24 s, avenue-traffic = `g7` S2 4K t = 28 s, swing-avenue = `g8` t = 6.5 s (a still, not a clip), plus three ours-vs-ours pairs against the round 02 stills / swing clip frame.
The S1 frames are from the g3 build (curb-gap proxy, fill 2500 lux, density 1600 / 1100); the committed defaults differ slightly (fill 1800, rule-based curb gaps, corridor 24 m). No street / signal clip pairs: they were not re-shot.

