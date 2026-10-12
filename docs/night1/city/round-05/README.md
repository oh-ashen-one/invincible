# P1 City round 05 — captures and camera parameters

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
| S1_avenue_street | 1920x1080 | 1399x787 | 19.269 | 29.12 | 18.166 | 98 % |
| S1_avenue_street | 3840x2160 | 1920x1080 | 28.59 | 38.592 | 25.667 | 99 % |
| S2_avenue_swing | 1920x1080 | 1399x787 | 23.2 | 36.029 | 21.198 | 99 % |
| S2_avenue_swing | 3840x2160 | 1920x1080 | 26.481 | 36.973 | 25.621 | 97 % |
| S3_rooftop_watertower | 1920x1080 | 1399x787 | 15.795 | 29.416 | 14.424 | 99 % |
| S3_rooftop_watertower | 3840x2160 | 1920x1080 | 18.383 | 28.093 | 16.884 | 99 % |
| S4_perch_skyline | 1920x1080 | 1399x787 | 24.729 | 34.37 | 23.871 | 6 % |
| S4_perch_skyline | 3840x2160 | 1920x1080 | 53.152 | 72.523 | 50.369 | 99 % |
| S5_timessq_south | 1920x1080 | 1399x787 | 20.816 | 31.035 | 19.716 | 99 % |
| S5_timessq_south | 3840x2160 | 1920x1080 | 26.057 | 36.268 | 24.947 | 0 % |
| S6_timessq_street | 1920x1080 | 1399x787 | 23.508 | 30.595 | 20.137 | 99 % |
| S6_timessq_street | 3840x2160 | 1920x1080 | 32.385 | 45.738 | 30.578 | 95 % |
| S7_sunset_crosstown | 1920x1080 | 1399x787 | 19.006 | 29.683 | 17.77 | 48 % |
| S7_sunset_crosstown | 3840x2160 | 1920x1080 | 35.032 | 55.677 | 32.561 | 28 % |
| S8_aerial_midtown | 1920x1080 | 1399x787 | 23.778 | 35.461 | 21.739 | 99 % |
| S8_aerial_midtown | 3840x2160 | 1920x1080 | 26.579 | 39.972 | 25.283 | 9 % |

## Changes since round 04 (facts only)
- Street level (ground to the second-floor cornice), both sides of every avenue face in the detailed block: 578 faces / 2225 storefront bays built as
  geometry (`tools/export/street_kit.py`): piers, stepped cornice, 3D storefront frames with mullions and doors, fascia boards with original generic shop names,
  fabric awnings with lettered valances or metal marquees, fire escapes (616 built on pre-war, side and deco faces, see
  streetkit.json), about 580 k triangles, Nanite, material `M_CityKit`.
- Shop interiors drawn analytically (four shop types, customers, floors, side walls) instead of the blurred atlas photos.
- Sidewalks: 1.5 m slab joints, per-slab tone, hairline cracks (visible in sunlit areas; the S1 avenue sidewalks are in canyon shade).
- Street furniture: hydrant / trash can / newspaper box / tree pit about every 20 m of avenue frontage (149 / 151 / 143 / 127 supplemental instances).
- S1 corridor: ~45 % of the street trees left out (100 % in front of the west deco podium, z 40-152); SkyLight intensity 1.0 -> 1.7 in every view map.
- IP: ad cells L27, P27, P38 and L35 (COLTEX / COLEXCO) replaced in the Unreal copy; see docs/night1/city/IP_EXCLUSIONS.md. OCR of the eight 4K frames finds
  none of the excluded names.
- S1 test crop (4K, x 0-1600, y 800-1700): `builder_checks/S1_crop_x0-1600_y800-1700.jpg`; the fire escapes of the far west tower: `builder_checks/S1_crop_fire_escapes_x1100-1900_y450-1000.jpg`.
  Projection census of kit elements into that crop (not depth-tested, trees and buildings ignored): 556 fascia boards, 198 awnings, 101 marquees, 142 fire escapes.
- Not re-measured this round: the window-glass brightness numbers of round 04.
