# P1 City round 07 — captures and camera parameters

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Running game: `Scripts/run_game.sh` (`-game`, offscreen, map `/Game/Tests/City/City_View_<id>`, auto-activated CameraActor), screenshot at t = 28 s.
Frame times: game seconds 18-28, `t.MaxFPS 0`, no VSync, TSR with automatic screen percentage. GPU utilization read with ioreg before each run
(GPU shared with other sessions; the P1 editor was closed during the runs). Positions in browser metres (x east, y up, z south); UE = (100x, 100z, 100y) cm.

| id | camera pos | target | fov | sun (pitch, yaw) |
|---|---|---|---|---|
| S1_avenue_street | [246, 2.0, 150] | [251, 16, -300] | 75 | [-40, -45] |
| S2_avenue_swing | [243, 42, 185] | [252, 18, -350] | 80 | [-40, -45] |
| S3_rooftop_watertower | [166, 48.5, -122] | [158, 51, -150] | 75 | [-40, -45] |
| S4_perch_skyline | [182, 306, -92] | [-120, 150, -470] | 75 | [-40, -45] |
| S5_timessq_south | [-12, 6, -255] | [0, 48, -40] | 80 | [-40, -45] |
| S6_timessq_street | [8, 1.8, -110] | [-4, 26, -330] | 80 | [-40, -45] |
| S7_sunset_crosstown | [300, 30, -160] | [-300, 22, -160] | 75 | [-7, 0] |
| S8_aerial_midtown | [420, 160, 220] | [0, 20, -320] | 75 | [-40, -45] |

| id | output | internal | avg ms | p95 ms | GPU ms | GPU util before |
|---|---|---|---|---|---|---|
| S1_avenue_street | 1920x1080 | 1399x787 | 40.812 | 54.849 | 35.864 | 100 % |
| S1_avenue_street | 3840x2160 | 1920x1080 | 39.136 | 51.233 | 35.798 | 100 % |
| S2_avenue_swing | 1920x1080 | 1399x787 | 24.948 | 34.465 | 22.729 | 100 % |
| S2_avenue_swing | 3840x2160 | 1920x1080 | 36.4 | 50.266 | 32.343 | 100 % |
| S3_rooftop_watertower | 1920x1080 | 1399x787 | 13.551 | 23.059 | 12.1 | 100 % |
| S3_rooftop_watertower | 3840x2160 | 1920x1080 | 17.723 | 26.73 | 16.267 | 0 % |
| S4_perch_skyline | 1920x1080 | 1399x787 | 23.37 | 32.994 | 22.329 | 0 % |
| S4_perch_skyline | 3840x2160 | 1920x1080 | 31.929 | 41.647 | 30.875 | 0 % |
| S5_timessq_south | 1920x1080 | 1399x787 | 19.79 | 29.312 | 18.392 | 0 % |
| S5_timessq_south | 3840x2160 | 1920x1080 | 25.085 | 34.504 | 23.659 | 0 % |
| S6_timessq_street | 1920x1080 | 1399x787 | 19.729 | 29.258 | 18.307 | 0 % |
| S6_timessq_street | 3840x2160 | 1920x1080 | 24.777 | 34.309 | 23.328 | 0 % |
| S7_sunset_crosstown | 1920x1080 | 1399x787 | 17.62 | 27.732 | 16.209 | 0 % |
| S7_sunset_crosstown | 3840x2160 | 1920x1080 | 23.0 | 33.216 | 21.568 | 0 % |
| S8_aerial_midtown | 1920x1080 | 1399x787 | 18.236 | 27.674 | 16.616 | 0 % |
| S8_aerial_midtown | 3840x2160 | 1920x1080 | 23.148 | 32.438 | 21.485 | 0 % |

## Round 07 — what was built, what was measured (Sonnet 5.5 resumed the interrupted round; captures 2026-09-30 01:20-01:40)

Build: `unreal/WebHomage/Scripts/build_city.py steps=mat,map` (commit of this round) through `tools/export/ue/run_commandlet.sh` (headless `-nullrhi` commandlet, inside `gpu_slot.sh capture`), then
`set_mpc.py FarGain=7.6 FarJit=1.3 SunK=0.08 DebugMode=0`, then `tools/export/capture_round.sh` (16 frames, one Unreal process at a time, one slot hold). MPC values read back from the saved asset:
`FarGain 7.6, FarJit 1.3, SunK 0.08, FarLandGain 1.6, WaterSpec 0.035, AlbKnee 0.30, AlbSlope 0.48, F0Scale 0.8, DayEmisK 0.22, GlassSpec 0.5, DebugMode 0`. Test-map atmosphere: height fog 0.0008, inscattering (0.76, 0.78, 0.80), aerial-perspective scale 0.34.
Content/ is not committed (public fork, no LFS); everything above is reproducible from the committed scripts. No `Failed to compile Material` line in any of the 16 game logs.
Resolution: output 1920x1080 renders internally at **1399x787**, output 3840x2160 renders internally at **1920x1080** (TSR, automatic screen percentage; `perf.json` `internal_w/h`). There are no movement sequences in `SHOTLIST.md` (8 stills), so there are no mp4 files this round.
**Frame times are contaminated**: taken inside a shared capture slot while 1-3 other Unreal processes and a foreign perf run were on the GPU (gpu_slot: `contaminated=true reasons=no-exclusive-lock`, `instances_before=4`; the ioreg reading before a run is one instantaneous sample). Do not use them as fps evidence; F/perf owns 4K/60.

### Measurements (`city_spec_check.md` / `.json`, `tools/export/city_spec_check.py`, regions `docs/night1/city/spec_regions.json`; same script for builder and critic)
| line | r06 (same script) | r07 first capture 20:20 (SunK cap not active) | **r07 final (this folder)** 1080p / 4K | target |
|---|---|---|---|---|
| C11 far shore Laplacian / sky | 4.76 | 27.3 | **27.3 / 23.4** | >= 6 |
| C11 flat 8x8 blocks % | 20 | 2.5 | **1.3 / 2.1** | <= 40 |
| C12 far shore (B-R) - sky (B-R) | -1.0 | -7.5 | **-3.8 / -3.6** | +-10 |
| C13 far shore Y - sky Y | -14.0 | -34.2 | **-33.7 / -33.9** | -35..-25 |
| C14 far shore Y - river Y | -3.4 | +17.8 | **+23.5 / +23.5** | 5..35 |
| C15 RMS(far) / RMS(near) | 0.08 | 0.25 (0.2534) | **0.257 / 0.258** | 0.25..0.45 |
| C1 facade crops passing (daylight, 18 crops) | 10/18 | 10/18 | **17/18 / 17/18** | all |
| C2 facade crops passing | 9/18 | 10/18 (9/18 at 4K) | **10/18 / 10/18** | all |
The far-field margins are small (C13 1.3 Y, C15 0.007): they ride one trade line (below). C1: only `s5_grey_tower` fails (3.7 % / 3.9 % > Y 204 = the lit interior windows of a grey tower, `DayEmisK` is the knob). C2 fails on S1 (crush, canyon shade),
S5 left dark tower, S6, S7 (dusk, informational) and the S2 dark tower: all lighting (sun 6 vs sky fill 1.7 at +2 EV), logged to P4 in HANDOFF.
C4 / C6 (YOLO11x-seg conf 0.35, 1080p frames): S1 0 vehicles / 0 people, S2 0 vehicles, S6 0 vehicles / 2 people: **all fail, there is no traffic or crowd in the City test maps** (P6 content). IP OCR of the 8 4K frames against the denylist: 0 hits.
Builder evidence crops of the areas the r06 critic named: `builder_checks/` (S1 fascia sign, S1 shop windows, S3 wall mural, S4 far band, S5 stair wall + block, S5 billboards, S6 slogan area, S6 billboard area).

### What changed this round (r07)
1. **CITY-SPEC measured once** (`spec_regions.json`, `city_spec_check.py`): the r06 builder and critic disagreed on S4 because of different boxes; the same frames now give C11 4.76x / C13 -14.0 / C14 -3.3 / C15 0.08 (critic: 4.8x / -10.9 / +2 / 0.09). See `city_spec_check_r06_baseline.md`.
2. **Far field (the r06 critic's biggest gap)**: `M_CityFarMass` had never compiled in r06 (`vc.a` on an RGB input), so every far-shore block of r03-r06 was the default grey material; new vertex-colour alpha output, per-cell tone jitter (`FarJit`),
   floor banding, dark-glass blocks, window grid that never fades below 18 %; `M_CityFarLand` canopy clumps / lot tones / street lines; `M_CityCliff` basalt columns + ledges + wooded top band; real-water Fresnel; thinner haze
   (fog 0.0065 -> 0.0008, inscattering = the blown horizon luma, aerial scale 1.0 -> 0.34).
3. **Facade albedo (r06 critic gap 3)**: sun-facing base colours are limited to a luma of `SunK` (0.08) with an N.L ramp, faded out beyond 0.9-2.2 km (the far skyline keeps its albedo) in `M_CityFacade`, `M_CityDetail`, `M_CityRoof`, plus `AlbKnee/AlbSlope/F0Scale` in the facade.
   **Bug found and fixed at the start of this session**: the interrupted WIP had the distance-fade edit glued onto a `//` comment line, so the whole cap was commented out in all three materials (the committed 20:20 frames therefore had NO cap: C1 10/18). Fixed by one statement per line.
   Cost, measured: S1 left stone mean Y 33.5 -> 23.8, S1 right brick 44.2 -> 37.8 (already failing C2; sun-facing by orientation but in canyon shadow: the material cannot see shadows). Recommended P4 fix: sun / sky-fill ratio ~4:1, then SunK -> 1.
4. IP: removed the MTA slogan, the racing-franchise key art (NEON RACERS / STAR RAIDERS ad cells) and the sneaker photography (`ip_original_art.py`, `IP_EXCLUSIONS.md`), 0 OCR hits. Sign atlases `never_stream` (S1 blurry fascia gone), `tsFrames` panelled cladding (S5 flat wall), 7 shop-interior types instead of 4 (S1 repeated shelf).
5. Scripts: `run_commandlet.sh` / `launch_editor.sh` no longer `pkill -9` an engine (2026-09-29 kernel panic): they refuse when an engine of this project runs; MPC defaults in `build_city.py` now equal the tuned values so a clean rebuild reproduces them.

### S4 sweep behind the far-field parameters (1080p, real -game, SunK cap active; `M_CityFarMass` FarGain / FarJit, height fog, aerial scale)
Each lever: fog -1e-4 = C13 -1.7 Y, C15 +0.011; FarGain +1 = C13 +1.8 (+0.8 above ~6) Y, C15 -0.004; FarJit +0.3 = C13 -1.5 Y, C15 +0.005. Sky Y is 229 (blown, exposure +2 EV, P4) so the window is ~0.01 wide in C15.
| fog | aerial | FarGain | FarJit | C11 | C13 | C14 | C15 |
|---|---|---|---|---|---|---|---|
| 0.0010 | 0.34 | 3.4 | 1.0 | 26.8 | -35.41 fail | +17.4 | 0.239 fail |
| 0.0010 | 0.34 | 4.6 | 1.0 | 25.6 | -32.36 | +20.4 | 0.237 fail |
| 0.0010 | 0.34 | 4.6 | 1.3 | - | -33.83 | +18.9 | 0.243 fail |
| 0.0010 | 0.34 | 4.6 | 1.6 | - | -35.29 fail | +17.5 | 0.248 fail |
| 0.0010 | 0.22 | 5.6 | 1.3 | 26.3 | -33.48 | +20.4 | 0.248 fail |
| 0.0009 | 0.34 | 6.6 | 1.3 | 26.3 | -32.95 | +22.0 | 0.248 fail |
| 0.0007 | 0.34 | 5.6 | 1.3 | 28.9 | -37.09 fail | +22.5 | 0.272 |
| 0.0007 | 0.34 | 7.6 | 1.3 | 28.1 | -35.26 fail | +24.3 | 0.269 |
| 0.0005 | 0.34 | 5.6 | 1.3 | 31.7 | -40.81 fail | +24.1 | 0.300 |
| 0.0008 | 0.34 | 6.6 | 1.3 | 27.4 | -34.44 | +22.7 | 0.260 |
| **0.0008** | **0.34** | **7.6** | **1.3** | 26.9 | **-33.66** | +23.4 | **0.258** (chosen; full frames: -33.65 / 0.257) |
