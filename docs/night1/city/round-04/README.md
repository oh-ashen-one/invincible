# P1 City round 04 — captures and camera parameters

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
| S1_avenue_street | 1920x1080 | 1399x787 | 21.957 | 31.9 | 20.59 | 34 % |
| S1_avenue_street | 3840x2160 | 1920x1080 | 32.054 | 43.275 | 29.624 | 38 % |
| S2_avenue_swing | 1920x1080 | 1399x787 | 18.607 | 28.732 | 17.714 | 12 % |
| S2_avenue_swing | 3840x2160 | 1920x1080 | 48.19 | 59.063 | 43.222 | 12 % |
| S3_rooftop_watertower | 1920x1080 | 1399x787 | 15.643 | 29.902 | 14.163 | 100 % |
| S3_rooftop_watertower | 3840x2160 | 1920x1080 | 29.472 | 39.867 | 26.13 | 30 % |
| S4_perch_skyline | 1920x1080 | 1399x787 | 34.165 | 43.741 | 31.67 | 100 % |
| S4_perch_skyline | 3840x2160 | 1920x1080 | 44.976 | 54.423 | 42.734 | 100 % |
| S5_timessq_south | 1920x1080 | 1399x787 | 20.838 | 31.293 | 19.677 | 3 % |
| S5_timessq_south | 3840x2160 | 1920x1080 | 26.256 | 37.03 | 24.825 | 82 % |
| S6_timessq_street | 1920x1080 | 1399x787 | 32.028 | 43.499 | 28.521 | 100 % |
| S6_timessq_street | 3840x2160 | 1920x1080 | 39.608 | 49.403 | 36.49 | 100 % |
| S7_sunset_crosstown | 1920x1080 | 1399x787 | 19.233 | 29.782 | 17.697 | 100 % |
| S7_sunset_crosstown | 3840x2160 | 1920x1080 | 24.914 | 35.161 | 23.257 | 77 % |
| S8_aerial_midtown | 1920x1080 | 1399x787 | 32.69 | 42.732 | 28.346 | 48 % |
| S8_aerial_midtown | 3840x2160 | 1920x1080 | 25.703 | 35.024 | 23.514 | 49 % |

## Changes since round 03 (facts only)
- Facade windows: interior-mapping mip level, room width / back-wall wrap, lit / dim / dark room mix, daylight emission scale (MPC DayEmisK 0.22), sash-glass
  Specular 0.5, blind albedo, ceiling / floor brightness (tools/export/gen_shaders.mjs `uePatch` list; HANDOFF.md "Facade patch layer").
- Storefronts: room photo wraps once per storefront (open shop), sign-band mip bias, new M_CitySignage material (signage.js port) on the 13 signage meshes.
- Times Square ad / sign atlas cells with Marvel-universe or real-game brand art replaced in the Unreal copy (docs/night1/city/IP_EXCLUSIONS.md; browser atlas files untouched).
- S5: the dark tsFrames housing hovering next to the camera was removed from the exported mesh (tools/export/patch_export.py); other tsFrames parts use M_CityFrame.
- Editor: launched offscreen (-RenderOffScreen -NoSound) and closed during all captures. Other Unreal sessions were running during the captures (GPU util column).
- Frame times are the 10 s window at game seconds 18-28 in the real game (offscreen `-game`); 3840x2160 output renders internally at 1920x1080 (TSR).

## Window brightness test (critic r03 test)

Window pixels = pixels of glass panes, taken from a second capture of the same view with the facade material in debug mode 3
(MPC_City.DebugMode = 3: red = glass, everything else black). In each 4K frame the 400 x 400 px crop with the most window pixels inside
the listed region was measured (chosen from the mask only). Luminance = Rec.709 luma of the 8-bit sRGB frame, 0..1.

| region | crop (x, y) | window px | > 80 % lum. | > 60 % lum. | median | mean | round 03 > 80 % | round 03 median |
|---|---|---|---|---|---|---|---|---|
| S1 right facade (tower right of the avenue) | 3020, 360 | 50920 | 0.0 % | 0.0 % | 0.071 | 0.082 | 0.0 % | 0.286 |
| S8 brick tower (centre right) | 2150, 1590 | 36091 | 3.11 % | 16.48 % | 0.409 | 0.347 | 11.97 % | 0.619 |
| S8 brick tower (left) | 1450, 1140 | 30852 | 0.0 % | 2.51 % | 0.354 | 0.376 | 21.26 % | 0.743 |
| S2 left stone tower | 360, 900 | 48967 | 0.49 % | 1.6 % | 0.304 | 0.325 | 24.13 % | 0.764 |
| S7 left glass wall | 0, 680 | 160000 | 0.0 % | 0.0 % | 0.129 | 0.127 | 0.0 % | 0.388 |
| S7 right masonry wall | 3240, 760 | 29162 | 0.0 % | 0.0 % | 0.404 | 0.389 | 68.93 % | 0.847 |

Crops (`window_crops/`): `*_crop.jpg` = the measured crop, `*_over80.jpg` = window pixels above 80 % luminance in magenta.
