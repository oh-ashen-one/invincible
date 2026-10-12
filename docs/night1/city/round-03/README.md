# P1 City round 03 — captures and camera parameters

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Running game: `Scripts/run_game.sh` (`-game`, offscreen, map `/Game/Tests/City/City_View_<id>`, auto-activated CameraActor), screenshot at t = 28 s.
Frame times: game seconds 18-28, `t.MaxFPS 0`, no VSync, TSR with automatic screen percentage. GPU utilization read with ioreg before each run
(GPU shared with other sessions; the P1 editor was also open). Positions in browser metres (x east, y up, z south); UE = (100x, 100z, 100y) cm.

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
| S1_avenue_street | 1920x1080 | 1399x787 | 58.139 | 132.855 | 40.989 | 82 % |
| S1_avenue_street | 3840x2160 | 1920x1080 | 66.914 | 163.497 | 48.575 | 94 % |
| S2_avenue_swing | 1920x1080 | 1399x787 | 65.849 | 143.494 | 40.04 | 83 % |
| S2_avenue_swing | 3840x2160 | 1920x1080 | 56.426 | 102.427 | 44.103 | 88 % |
| S3_rooftop_watertower | 1920x1080 | 1399x787 | 45.428 | 132.345 | 26.581 | 95 % |
| S3_rooftop_watertower | 3840x2160 | 1920x1080 | 49.702 | 100.66 | 31.558 | 86 % |
| S4_perch_skyline | 1920x1080 | 1399x787 | 57.543 | 126.769 | 39.562 | 64 % |
| S4_perch_skyline | 3840x2160 | 1920x1080 | 61.482 | 82.249 | 55.349 | 88 % |
| S5_timessq_south | 1920x1080 | 1399x787 | 45.02 | 70.133 | 37.931 | 95 % |
| S5_timessq_south | 3840x2160 | 1920x1080 | 41.838 | 57.424 | 38.217 | 89 % |
| S6_timessq_street | 1920x1080 | 1399x787 | 31.218 | 43.047 | 27.781 | 93 % |
| S6_timessq_street | 3840x2160 | 1920x1080 | 35.532 | 50.866 | 32.254 | 90 % |
| S7_sunset_crosstown | 1920x1080 | 1399x787 | 26.28 | 45.564 | 22.621 | 92 % |
| S7_sunset_crosstown | 3840x2160 | 1920x1080 | 50.548 | 79.84 | 44.461 | 52 % |
| S8_aerial_midtown | 1920x1080 | 1399x787 | 27.022 | 42.707 | 24.07 | 87 % |
| S8_aerial_midtown | 3840x2160 | 1920x1080 | 34.269 | 58.962 | 30.34 | 51 % |
