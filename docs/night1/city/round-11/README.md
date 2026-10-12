# P1 City round 11 — captures and camera parameters

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Running game: `Scripts/run_game.sh` (`-game`, offscreen, map `/Game/Tests/City/City_View_<id>`, auto-activated CameraActor), screenshots at t = 34 s and t = 38 s (settle pair; the t = 38 s frame is the round frame).
Frame times: game seconds 26-38 of a capture run under the shared GPU lock (`gpu_slot.sh capture`: frame cap 20 fps at 1080p / 8 fps at 3840 px, background priority, other agents render at the same time), NOT a performance measurement (a perf run needs the exclusive lock on an attended Mac); the 1080p frames use the automatic screen percentage (internal 1399x787), the 4K frames r.ScreenPercentage 100 (internal 3840x2160). GPU utilization read with ioreg before each run
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
| S1_avenue_street | 1920x1080 | 1399x787 | 158.938 | 147.973 | 20.024 | 32 % |
| S1_avenue_street | 3840x2160 | 3840x2160 | 459.351 | 324.257 | 58.426 | 22 % |
| S2_avenue_swing | 1920x1080 | 1399x787 | 172.034 | 147.198 | 26.68 | 23 % |
| S2_avenue_swing | 3840x2160 | 3840x2160 | 474.683 | 323.023 | 61.11 | 24 % |
| S3_rooftop_watertower | 1920x1080 | 1399x787 | 172.496 | 147.699 | 15.818 | 0 % |
| S3_rooftop_watertower | 3840x2160 | 3840x2160 | 316.96 | 222.884 | 38.698 | 24 % |
| S4_perch_skyline | 1920x1080 | 1399x787 | 160.363 | 147.261 | 24.458 | 0 % |
| S4_perch_skyline | 3840x2160 | 3840x2160 | 334.143 | 223.372 | 65.098 | 27 % |
| S5_timessq_south | 1920x1080 | 1399x787 | 355.686 | 174.048 | 36.452 | 0 % |
| S5_timessq_south | 3840x2160 | 3840x2160 | 450.51 | 323.349 | 53.551 | 24 % |
| S6_timessq_street | 1920x1080 | 1399x787 | 168.709 | 147.18 | 20.639 | 18 % |
| S6_timessq_street | 3840x2160 | 3840x2160 | 470.892 | 322.726 | 53.015 | 24 % |
| S7_sunset_crosstown | 1920x1080 | 1399x787 | 189.126 | 153.788 | 21.707 | 26 % |
| S7_sunset_crosstown | 3840x2160 | 3840x2160 | 487.876 | 323.095 | 52.02 | 20 % |
| S8_aerial_midtown | 1920x1080 | 1399x787 | 157.728 | 147.579 | 21.154 | 24 % |
| S8_aerial_midtown | 3840x2160 | 3840x2160 | 308.584 | 222.496 | 47.596 | 20 % |

## Round-11 target, configuration and measured numbers

Target (Opus director, after critic r10): give the S4 far-shore towers a far-LOD facade with a window grid, crown / setback variation and mid-grey albedo (0.25-0.35); pass lines measured at 1080p with `tools/export/s4_far_check.py` / `city_spec_check.py` (T2 <= 10 % above Y 204 in (0,150,1300,300); flat bright 8x8 blocks <= 10 % in (540,110,900,260); S8 glass (1270,0,1640,300) <= 1.5 % above 204; T1 >= 12 px and C11-C15 kept; the native-4K S3 board reads "MORE SHADE ON EVERY STREET" and no partial crop evokes a real brand).

Capture protocol: `tools/export/r11_plan.sh` inside one `gpu_slot.sh capture` hold per batch; two screenshots per run (t = 34 s and t = 38 s of game time), the t = 38 s frame is the round frame; `tools/export/settle_check.py` (`settle_check.txt`): mean |dY| between the pair 0.18-0.37 and 0.01-0.15 % of the pixels differing by more than 8 levels in every view (16 frames) (a cold-start run with the older 24 / 28 s pair gave 4.5 and 14 %, see HANDOFF gotcha 36). 1080p frames: automatic screen percentage, internal 1399x787 (TSR upscale). 4K frames: `r.ScreenPercentage 100`, output and internal 3840x2160 (`perf.json`). The shot list has no movements, so no mp4 was produced.

Final configuration: MPC_City `F0Scale` 0.25 (r10 0.8), `FarLitK` 0.30 (new), `FarFill` 0.12 (new), `FarSunK` 0.22, `FarGain` 4.0, `ShadeFill` 0.17, `GlassSky` 0.15, `SunK` 0.08 (others unchanged, `DebugMode` 0). S4 map: height fog 0.004 starting at 4 500 m, inscattering (0.60, 0.62, 0.66), aerial perspective scale 0.34, manual exposure +2 EV, SkyLight 1.7, sun 6 (the other seven maps are unchanged).

| line | r10 (1080p) | r11 (1080p) | r11 (4K frame reduced to 1080p) | target |
|---|---|---|---|---|
| T1 S4 silhouette-top std, x 0-1300 (px, min of 3 definitions) | 19.0 | 23.6 | 23.6 | >= 12 |
| T2 S4 box (0,150,1300,300) above Y 204 (%) | 29.5 | 6.6 | 6.9 | <= 10 |
| T4 flat bright 8x8 blocks in (540,110,900,260), share of ALL blocks (%) | 24.3 | 1.4 | 1.5 | <= 10 |
| T4 same, share of the BRIGHT blocks (%) | 46.1 | 45.8 | 48.0 | <= 10 (other reading) |
| C11 far_shore lap / sky lap | 20.8 | 30.3 | 27.8 | >= 6 |
| C11 far_shore flat 8x8 (%) | 4.1 | 0.0 | 0.0 | <= 40 |
| C12 far_shore (B-R) - sky (B-R) | -1.7 | -0.1 | +0.8 | +-10 |
| C13 far_shore Y - sky Y (committed box) | -38.5 | -68.2 | -66.3 | -35..-25 |
| C13 with the box (0,150,1300,215) the critic used in r10 | -29.6 | -57.1 | -55.6 | -35..-25 |
| C14 far_shore Y - river Y | +16.9 | +23.3 | +26.4 | 5..35 |
| C15 rms far_shore / near_city | 0.24 | 0.31 | 0.31 | 0.25..0.45 |
| T5 S8 glass box (1270,0,1640,300) above Y 204 (%) | 70.4 | 0.69 | 0.37 | <= 1.5 |
| C1 daylight facade boxes passing (<= 1.5 % above 204; 16 boxes, 1080p) | 15 | 15 | - | 16 |
| C2 daylight facade boxes with mean Y 52-119 (16 boxes, 1080p) | 16 | 16 | - | 16 |
| S3 / S7 share of pixels below Y 25 (%) | 13.2 / 1.4 | 17.0 / 3.5 | - | <= 25 / <= 30 |
| C4 / C6 vehicles at YOLO conf 0.30: S1 / S2 | 17 / 15 | 17 / 16 | - | 5-19 / 14-22 |

The 1080p / 4K frame-time tables above and `s4_far_check.json`, `city_spec_check.{md,json}`, `shade_check.md`, `s8_glass_box.txt`, `ip_ocr_check.txt` are the measurements behind this table. The health monitor stopped the first native-4K S6 / S7 runs (WindowServer CPU 97 %, SIGTERM, then an automatic pause); both were re-run after the auto-lift (hold 11) with the same configuration; no engine crashed.
Evidence images: `builder_checks/s4_mask_1080p.png` (red = Y > 204, green = T2 box, cyan = T4 box, yellow = bright flat blocks), `S4_far_band_4k.jpg`, `S4_tower_box_4k.jpg`, `S8_glass_upper_4k.jpg`, `S3_board_4k.jpg` (pixel copies of the native-4K frames).

Sweeps that led to the configuration (S4 1080p, settled pairs; scratch, not committed): FarLitK 0.30 -> 0.45 moved the far-shore strip by +3 Y (the faces visible from the perch are almost all shaded) and T2 7.9 -> 12.2 %; FarFill 0 / 0.12 / 0.24 gave far-shore Y 176.8 / 182.9 / 187.5 and T2 7.9 / 8.3 / 9.4 % with C15 0.22 / 0.18 / 0.16; uniform height fog 0.003 from 400 m gave far-shore Y 196.6 (C13 -32.6) but T2 29.2 % and C15 0.16; fog 0.004 / 0.008 / 0.004 starting at 4 500 / 4 500 / 3 500 m gave T2 7.0 / 12.4 / 10.1 %. S8 glass box F0Scale 0.8 / 0.5 / 0.35 / 0.25 / 0.18: 70.4 / 43.6 / 6.8 / 3.1 / 3.0 % (the last 3 % was one tower side seen at a grazing angle; the grazing-angle fix took it to 0.7 %).

Measured failures and trade-offs, stated plainly:
- **C13 fails** (far shore Y minus sky Y -68 with the committed far_shore box (450,192,1350,236); -57 with the box the critic used in r10 (0,150,1300,215); r10 -38.5 / -29.6, the second one passed). The band that made C13 pass in r10 was the white haze (49 % of the rows 150-215 above Y 204). C13 (mean 25-35 below the sky) and T2 (<= 10 % above 204) did not hold together in any configuration tried: C13 -35 needs a far-shore mean of 194 with the RMS that C15 asks for (std ~27), i.e. roughly a third of that strip above Y 204. T2 is a pass line of this round; C13 is not met. C15 passes (0.31, r10 0.24 failed) and C14 passes (23.3).
- **Flat-block line**: 1.4 % of all 8x8 blocks of the box are bright and flat (r10 24.3 %, the critic's "25 %"). The other reading of the sentence (flat blocks as a share of the bright blocks) is 45.8 % at r11 against 46.1 % at r10: only 24 blocks are bright now (427 in r10), 11 of them are one pale lit face (x 740-790, y 142-175).
- Black crush (Y < 25) went up: S3 17.0 % (r10 13.2 %, limit 25 %), S7 3.5 % (r10 1.4 %, limit 30 %); `s7_left_glass` (dusk, informational) mean Y 48.2 (r10 71.5, C2 floor 52): the effect of F0Scale 0.25 on glass that reflected the sky.
- Unchanged and still open (r10 critic secondary items): S5 mid tower (640,40,880,700) 6.0 % above Y 204 (limit 1.5), S6 curb (1150,760,1920,1080) 14.65 %, S6 red steps saturation, S3 white roof primitives, `s5_grey_tower` C1 3.66 %, people 0-1 / traffic lights 0 (P6), cars (plates, clearcoat) not touched.
