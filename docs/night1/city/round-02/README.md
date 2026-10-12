# P1 City round 02 — captures and camera parameters

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
| S1_avenue_street | 1920x1080 | 1399x787 | 42.796 | 66.028 | 37.736 | 100 % |
| S1_avenue_street | 3840x2160 | 1920x1080 | 61.266 | 83.421 | 55.4 | 99 % |
| S2_avenue_swing | 1920x1080 | 1399x787 | 41.929 | 61.499 | 37.833 | 100 % |
| S2_avenue_swing | 3840x2160 | 1920x1080 | 53.144 | 70.253 | 48.935 | 99 % |
| S3_rooftop_watertower | 1920x1080 | 1399x787 | 37.703 | 56.926 | 33.89 | 99 % |
| S3_rooftop_watertower | 3840x2160 | 1920x1080 | 52.151 | 76.016 | 47.314 | 99 % |
| S4_perch_skyline | 1920x1080 | 1399x787 | 47.602 | 70.722 | 44.107 | 100 % |
| S4_perch_skyline | 3840x2160 | 1920x1080 | 52.257 | 72.223 | 49.214 | 99 % |
| S5_timessq_south | 1920x1080 | 1399x787 | 40.851 | 61.098 | 36.808 | 99 % |
| S5_timessq_south | 3840x2160 | 1920x1080 | 50.035 | 71.735 | 45.789 | 100 % |
| S6_timessq_street | 1920x1080 | 1399x787 | 38.19 | 54.915 | 34.968 | 99 % |
| S6_timessq_street | 3840x2160 | 1920x1080 | 59.84 | 81.7 | 55.58 | 99 % |
| S7_sunset_crosstown | 1920x1080 | 1399x787 | 36.646 | 52.524 | 32.583 | 100 % |
| S7_sunset_crosstown | 3840x2160 | 1920x1080 | 46.389 | 65.512 | 43.229 | 100 % |
| S8_aerial_midtown | 1920x1080 | 1399x787 | 48.5 | 62.766 | 43.372 | 100 % |
| S8_aerial_midtown | 3840x2160 | 1920x1080 | 56.152 | 75.794 | 50.015 | 99 % |
