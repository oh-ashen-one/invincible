# P6 round 03: experiment runs (evidence, not the final captures)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Real game (`-game`, offscreen, `Scripts/run_game.sh`, inside `gpu_slot.sh capture`), 1920x1080 (S2 g7: 3840x2160), `r.ScreenPercentage 100`, stills at game t = 12 / 16 / 20 / 24 / 28 s (swing runs: 4.5 / 6.5 / 8.5 / 10.5 / 12.5 s of a real-time flight). YOLO11x-seg conf 0.35 imgsz 1920 (CPU) = the spec instrument; "right" = box centre in the right half of the frame; "crop" = the same on the 84 % centre crop the critic pack applies. Engine probe: people >= 20 px tall, ray-unoccluded, within 80 m.

| run | YOLO people per still (full frame) | right | right share % (median, per still) | crop84 right share % (median, per still) | probe within 80 m >= 20 px: median / min of samples |
|---|---|---|---|---|---|
| `e1_s1_fill` | 31, 28, 24, 24, 33 | 2, 3, 1, 0, 7 | **6** (6, 11, 4, 0, 21) | **7** (7, 4, 0, 8, 13) | 97 / 84 (n=21) |
| `e2_s1_d2000` | 33, 44, 36, 45, 48 | 6, 11, 3, 18, 15 | **25** (18, 25, 8, 40, 31) | **21** (17, 21, 12, 36, 25) | 130 / 118 (n=21) |
| `e3_s1_d2800` | 29, 35, 38, 43, 39 | 0, 7, 5, 11, 11 | **20** (0, 20, 13, 26, 28) | **12** (0, 10, 12, 19, 26) | 151 / 120 (n=21) |
| `g1_s1_d1600_f2500` | 34, 32, 37, 43, 42 | 7, 6, 6, 17, 16 | **21** (21, 19, 16, 40, 38) | **29** (29, 19, 23, 33, 31) | 108 / 94 (n=21) |
| `g2_s1_d1600_f4500` | 34, 34, 31, 38, 49 | 6, 9, 4, 13, 19 | **26** (18, 26, 13, 34, 39) | **23** (23, 23, 16, 34, 38) | 108 / 98 (n=21) |
| `g3_s1_d1600_f2500_gap` | 36, 41, 30, 42, 44 | 10, 16, 5, 18, 20 | **39** (28, 39, 17, 43, 45) | **42** (21, 42, 11, 44, 42) | 106 / 96 (n=21) |
| `g5_s1_fillall2500` | 32, 36, 35, 38, 38 | 7, 12, 3, 12, 11 | **29** (22, 33, 9, 32, 29) | **25** (23, 33, 10, 35, 25) | 107 / 97 (n=21) |
| `e4_s2_d2000` | 2, 6, 0, 2, 5 | 0, 2, 0, 1, 2 | **33** (0, 33, 0, 50, 40) | **0** (0, 0, 0, 0, 0) | 2 / 0 (n=21) |
| `g6_s2_d1600` | 4, 2, 4, 3, 1 | 1, 0, 1, 1, 1 | **25** (25, 0, 25, 33, 100) | **0** (0, 0, 0, 0, 0) | 2 / 1 (n=20) |
| `g7_s2_4k_d1600` | 7 | 1 | **14** (14) | **0** (0) | 2 / 0 (n=20) |
| `g8_swing_a` | 14, 11, 9, 13, 1 | 7, 1, 1, 6, 0 | **11** (50, 9, 11, 46, 0) | **7** (56, 7, 0, 62, 0) | 45 / 3 (n=19) |
