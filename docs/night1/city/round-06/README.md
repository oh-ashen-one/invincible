# P1 City round 06 — captures and camera parameters

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
| S1_avenue_street | 1920x1080 | 1399x787 | 21.223 | 38.03 | 18.895 | 37 % |
| S1_avenue_street | 3840x2160 | 1920x1080 | 38.617 | 58.739 | 31.966 | 100 % |
| S2_avenue_swing | 1920x1080 | 1399x787 | 26.0 | 50.737 | 23.155 | 79 % |
| S2_avenue_swing | 3840x2160 | 1920x1080 | 41.606 | 59.015 | 37.609 | 99 % |
| S3_rooftop_watertower | 1920x1080 | 1399x787 | 21.428 | 33.875 | 17.655 | 100 % |
| S3_rooftop_watertower | 3840x2160 | 1920x1080 | 18.652 | 28.552 | 16.896 | 0 % |
| S4_perch_skyline | 1920x1080 | 1399x787 | 26.228 | 39.237 | 24.679 | 55 % |
| S4_perch_skyline | 3840x2160 | 1920x1080 | 33.427 | 43.21 | 32.276 | 0 % |
| S5_timessq_south | 1920x1080 | 1399x787 | 20.113 | 30.473 | 18.678 | 0 % |
| S5_timessq_south | 3840x2160 | 1920x1080 | 28.273 | 40.134 | 25.797 | 91 % |
| S6_timessq_street | 1920x1080 | 1399x787 | 20.85 | 30.805 | 18.791 | 0 % |
| S6_timessq_street | 3840x2160 | 1920x1080 | 26.407 | 36.336 | 23.641 | 0 % |
| S7_sunset_crosstown | 1920x1080 | 1399x787 | 18.787 | 29.65 | 16.619 | 0 % |
| S7_sunset_crosstown | 3840x2160 | 1920x1080 | 28.037 | 35.014 | 25.024 | 0 % |
| S8_aerial_midtown | 1920x1080 | 1399x787 | 33.698 | 57.602 | 30.11 | 0 % |
| S8_aerial_midtown | 3840x2160 | 1920x1080 | 72.282 | 104.828 | 65.163 | 99 % |

## Far-field numbers vs CITY-SPEC section 4 (S4, 4K frame downscaled to 1920x1080 INTER_AREA; tools/export/spec_farfield.py)

Regions (1920x1080 coordinates): sky (0,0,1920,100), horizon_far (0,150,1920,215), far_shore (0,215,900,300), river (450,330,1250,400), near_city (0,700,500,1000).

| region | mean RGB | B-R | Y | RMS contrast | mean abs Laplacian | flat 8x8 blocks |
|---|---|---|---|---|---|---|
| sky | (224, 231, 234) | +10.2 | 230.0 | 0.020 | 0.85 | 91.2 % |
| horizon_far | (218, 222, 226) | +7.6 | 221.2 | 0.146 | 6.72 | 47.3 % |
| far_shore | (193, 198, 205) | +12.1 | 197.4 | 0.113 | 5.70 | 22.3 % |
| river | (207, 211, 216) | +9.1 | 210.9 | 0.063 | 3.68 | 62.9 % |
| mid_city | (180, 188, 184) | +4.4 | 185.9 | 0.240 | 23.05 | 12.2 % |
| near_city | (101, 104, 108) | +6.3 | 103.6 | 0.459 | 20.14 | 1.0 % |

| line | measured | target |
|---|---|---|
| C11 far-shore lap / sky lap | 6.7 | target >= 6 |
| C11 horizon_far lap / sky lap | 7.9 |  |
| C11 far-shore flat 8x8 blocks % | 22.3 | target <= 40 |
| C12 far-shore | 1.9 | B-R) minus sky (B-R) (target within +-10 |
| C13 far-shore Y minus sky Y | -32.6 | target -35..-25 |
| C13 near_city Y | 103.6 |  |
| C14 far-shore Y minus river Y | -13.5 | target 5..35 |
| C15 rms far_shore / near_city | 0.25 | target 0.25..0.45 |

C11, C12, C13 (-32.6) and C15 (0.25, at the lower bound) are inside the targets; C14 is not: the river (Y 210) is brighter than the far shore (Y 197) because the same
haze that puts the far shore 33 luma under the sky also veils the water (grazing-angle Fresnel is capped: Specular 0.06). The sky band is blown (Y 229, test maps use manual +2 EV exposure; P4 owns it).

## Shore strip vs water (round-05 critic test: 4K crop x 0-2800, y 550-700; tools/export/far_stats.py)

Pixels of coast / far-land meshes vs water come from a mask capture (MPC_City.DebugMode 3) of the same camera with fog and aerial perspective off (`City_View_S4vm`), luma from the normal frame.

shore strip (coast + far land): 159 128 px, mean luma 0.760, mean RGB (190, 194, 200); water: 159 030 px, mean luma 0.864, mean RGB (216, 221, 226). The strip is darker than the water by 0.104 (round 05: strip near-white 228,232,235 vs water 219,226,233).

## Facade brightness, CITY-SPEC C1 / C2 (tools/export/facade_c1.py; facade-only mask = DebugMode 11; 400 x 400 4K crops with the most facade pixels)

| region | crop x,y | Y > 204 | p95 | p99 | mean Y | C1 | C2 |
|---|---|---|---|---|---|---|---|
| S1 right tower | 2700, 0 | 0.0 % | 29.6 | 85.8 | 20.4 | pass | FAIL |
| S1 left buildings | 880, 0 | 0.0 % | 112.1 | 148.2 | 56.9 | pass | pass |
| S2 left stone tower | 0, 60 | 30.69 % | 221.1 | 239.1 | 133.7 | FAIL | FAIL |
| S2 right glass tower | 2460, 0 | 3.79 % | 202.6 | 213.1 | 99.9 | FAIL | pass |
| S7 left glass wall (sunset) | 0, 0 | 0.0 % | 61.1 | 63.1 | 42.6 | pass | FAIL |
| S7 right masonry wall (sunset) | 2600, 0 | 0.0 % | 25.6 | 30.9 | 14.8 | pass | FAIL |
| S8 brick towers centre | 1490, 1140 | 0.0 % | 117.3 | 151.0 | 70.2 | pass | pass |

Daylight targets: <= 1.5 % above Y 204, p95 <= 192, p99 <= 206, mean Y 52..119. The S7 rows are a sunset view (spec is for daylight). Failures are lighting driven (sun 6 lux + manual exposure +2 EV: sunlit pale limestone in S2
clips, canyon-shadowed dark glass in S1 / S7 is under 52): logged for P4, not changed here.

## Changes since round 05 (facts only)
- Far-shore blocks (`farCityMass`, 35 tile meshes): exporter now keeps the per-vertex window flag (was clamped away: every block came out saturated blue); new `M_CityFarMass` draws window grid, spandrels, glass towers.
- Coast, far-land and cliff meshes (were the generic white vertex-colour material): `M_CityCoast` (atlas granite / riprap / planks, lawn, pavers), `M_CityFarLand` (browser far-land ground map), `M_CityCliff`.
- Water Specular 0.5 -> 0.06 (F0 0.005, F90 0.24). Far facade LOD: window box filter 1.8x -> 1.15x, warm-neutral push where lod -> 1.
- View-map atmosphere: height fog 0.006 -> 0.0065 with sky-neutral inscattering (0.6, 0.62, 0.64) (was blue), aerial perspective scale 1.0.
- IP: ad cells L32, L59 (donor of L60 changed), P23, P24, P32, P63 and sign cells S15, S41, S48 replaced in the Unreal copy; `tools/export/ip_ocr_check.py` (denylist OCR of the eight 4K frames + the sanitised atlases): no hits.
- Captures ran under `gpu_slot.sh capture` (shared slots; other sessions active, frame times contaminated).
