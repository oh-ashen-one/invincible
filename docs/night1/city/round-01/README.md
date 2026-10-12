# P1 City round 01 — captures and camera parameters

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Running game: `Scripts/run_game.sh` (`-game`, offscreen, map `/Game/Tests/City/City_View_<id>`, auto-activated CameraActor), screenshot at t = 28 s.
Frame times: game seconds 18-28, `t.MaxFPS 0`, no VSync, TSR with automatic screen percentage. GPU utilization was read with ioreg before each run
(the GPU is shared with other sessions; the P1 editor was also open). Positions in browser metres (x east, y up, z south); UE = (100x, 100z, 100y) cm.

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
| S1_avenue_street | 1920x1080 | 1399x787 | 32.642 | 45.575 | 29.817 | 99 % |
| S1_avenue_street | 3840x2160 | 1920x1080 | 43.492 | 57.807 | 40.343 | 99 % |
| S2_avenue_swing | 1920x1080 | 1399x787 | 30.983 | 48.717 | 27.663 | 100 % |
| S2_avenue_swing | 3840x2160 | 1920x1080 | 39.447 | 55.904 | 36.33 | 99 % |
| S3_rooftop_watertower | 1920x1080 | 1399x787 | 36.667 | 58.205 | 33.558 | 100 % |
| S3_rooftop_watertower | 3840x2160 | 1920x1080 | 41.225 | 58.957 | 36.918 | 99 % |
| S4_perch_skyline | 1920x1080 | 1399x787 | 38.403 | 54.803 | 36.385 | 99 % |
| S4_perch_skyline | 3840x2160 | 1920x1080 | 46.838 | 65.44 | 43.978 | 99 % |
| S5_timessq_south | 1920x1080 | 1399x787 | 31.646 | 44.319 | 28.824 | 99 % |
| S5_timessq_south | 3840x2160 | 1920x1080 | 41.189 | 58.689 | 38.094 | 99 % |
| S6_timessq_street | 1920x1080 | 1399x787 | 31.022 | 44.688 | 28.043 | 100 % |
| S6_timessq_street | 3840x2160 | 1920x1080 | 38.41 | 52.459 | 35.454 | 99 % |
| S7_sunset_crosstown | 1920x1080 | 1399x787 | 30.422 | 44.535 | 27.22 | 99 % |
| S7_sunset_crosstown | 3840x2160 | 1920x1080 | 39.087 | 57.057 | 36.019 | 99 % |
| S8_aerial_midtown | 1920x1080 | 1399x787 | 40.656 | 58.354 | 37.059 | 99 % |
| S8_aerial_midtown | 3840x2160 | 1920x1080 | 47.708 | 65.972 | 43.935 | 99 % |
