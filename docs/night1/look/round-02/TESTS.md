# Round 02 test numbers (numbers only)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Produced by `tools/perf_ue/night_tests.py` (round-1 critic tests) and `tools/perf_ue/look_lum_check.py` (LOOK-SPEC lines, `docs/night1/look/SPEC.md`). Luma Y = 0.2126 R + 0.7152 G + 0.0722 B of the 8-bit sRGB values; stills resized to 1920 px wide; near-black = Y < 10; clipped = any channel >= 250.

## Round-1 critic night tests (night_S1, street level)

| test | target | 1080p (native internal) | 3840x2160 (native internal) |
|---|---|---|---|
| mean luma | >= 35 | 53.0 | 52.7 |
| share of pixels < 10/255 | <= 3 % (LOOK-SPEC L3: <= 1 %) | 0.13 % | 0.17 % |
| distinct light pools in the bottom third (peak >= 120, valley <= 40, blur sigma 8 px at 1080p) | >= 4 | 4 (peaks [253, 214, 181, 156]) | 4 (peaks [251, 215, 180, 157]) |
| hero pixel-box mean luma, every frame of swing_night (718 frames, hero pixels in all) | >= 40 | min 71.4, p5 83.4, mean 103.6, max 138.9; frames below 40: 0 | |

Hero box = telemetry `px_left/right/top/bottom` (P3 hero-only depth capture, 1080p coordinates; row i+1 describes frame i); the box contains background pixels too. For information, the same measure on the other clips: swing_golden min 73.0 (frames below 40: 0), swing_midday min 30.5 (frames below 40: 64).

## LOOK-SPEC lines per still (1080p)

L1 golden, L3 night, L4 day / afternoon (midday), L5 sun-facing golden view (S7). L13 = lit blobs in the bottom half (Gaussian sigma 12 px, Y >= 100, area >= 400 px; spec >= 5 for street-level night views S1 / S6), L14 = bottom third p90 >= 100 and p10 15..30 (street-level night views). The B-R column is the L6 / L7 / L8 colour line (golden -55..-20, midday -19..+8, night -13..+13).

| still | spec | mean Y | Y<10 % | Y<25 % | clipped % | p99 | B-R | lit blobs (bottom half) | bottom-third p90 / p10 | within spec (mean / near-black / clipped / B-R) |
|---|---|---|---|---|---|---|---|---|---|---|
| golden_S1_1920x1080.jpg | L1 | 95.6 | 0.00 | 8.0 | 0.54 | 242 | -50.9 | 3 | 167 / 97 | yes / yes / yes / yes |
| golden_S2_1920x1080.jpg | L1 | 93.7 | 0.04 | 6.2 | 1.07 | 230 | -66.7 | 15 | 118 / 31 | yes / yes / yes / NO |
| golden_S3_1920x1080.jpg | L1 | 57.6 | 0.00 | 29.6 | 0.82 | 246 | -30.6 | 7 | 94 / 19 | NO / yes / yes / yes |
| golden_S4_1920x1080.jpg | L1 | 104.8 | 0.00 | 1.9 | 0.51 | 209 | -57.1 | 20 | 131 / 29 | NO / yes / yes / NO |
| golden_S5_1920x1080.jpg | L1 | 85.5 | 0.00 | 16.1 | 1.64 | 240 | -51.4 | 8 | 122 / 14 | yes / yes / yes / yes |
| golden_S6_1920x1080.jpg | L1 | 92.2 | 0.00 | 9.4 | 0.95 | 233 | -52.8 | 5 | 127 / 67 | yes / yes / yes / yes |
| golden_S7_1920x1080.jpg | L5 | 76.4 | 0.00 | 12.3 | 2.58 | 254 | -41.8 | 11 | 116 / 21 | yes / yes / NO / yes |
| golden_S8_1920x1080.jpg | L1 | 83.1 | 0.01 | 17.8 | 2.05 | 235 | -53.5 | 16 | 111 / 16 | yes / yes / NO / yes |
| midday_S1_1920x1080.jpg | L4 | 80.7 | 3.36 | 9.7 | 0.07 | 222 | -15.3 | 8 | 98 / 47 | yes / yes / yes / yes |
| midday_S2_1920x1080.jpg | L4 | 77.9 | 4.93 | 11.8 | 0.03 | 214 | -19.6 | 9 | 158 / 21 | yes / yes / yes / NO |
| midday_S3_1920x1080.jpg | L4 | 67.2 | 2.20 | 13.9 | 0.65 | 246 | -13.0 | 10 | 124 / 19 | yes / yes / NO / yes |
| midday_S4_1920x1080.jpg | L4 | 90.7 | 0.46 | 5.6 | 0.00 | 194 | +25.8 | 16 | 144 / 19 | NO / yes / yes / NO |
| midday_S5_1920x1080.jpg | L4 | 69.7 | 3.30 | 21.2 | 0.08 | 217 | -11.5 | 9 | 183 / 13 | yes / yes / yes / yes |
| midday_S6_1920x1080.jpg | L4 | 62.6 | 5.59 | 33.5 | 0.05 | 205 | -11.8 | 12 | 158 / 17 | yes / yes / yes / yes |
| midday_S7_1920x1080.jpg | L4 | 62.2 | 7.29 | 25.0 | 1.24 | 247 | -3.6 | 3 | 95 / 9 | yes / yes / NO / yes |
| midday_S8_1920x1080.jpg | L4 | 73.4 | 2.22 | 17.6 | 0.00 | 198 | +13.2 | 14 | 140 / 12 | yes / yes / yes / NO |
| night_S1_1920x1080.jpg | L3 | 52.9 | 0.23 | 31.5 | 1.51 | 242 | -12.9 | 9 | 142 / 18 | yes / yes / yes / yes |
| night_S2_1920x1080.jpg | L3 | 46.4 | 0.61 | 32.6 | 0.07 | 143 | -5.3 | 1 | 73 / 15 | yes / yes / yes / yes |
| night_S3_1920x1080.jpg | L3 | 45.6 | 0.11 | 47.6 | 0.12 | 196 | -3.0 | 4 | 84 / 14 | yes / yes / yes / yes |
| night_S4_1920x1080.jpg | L3 | 52.1 | 0.04 | 13.9 | 0.00 | 199 | +26.9 | 3 | 78 / 17 | yes / yes / yes / NO |
| night_S5_1920x1080.jpg | L3 | 43.9 | 0.22 | 44.9 | 0.95 | 232 | +4.2 | 14 | 149 / 11 | yes / yes / yes / yes |
| night_S6_1920x1080.jpg | L3 | 47.7 | 0.32 | 33.7 | 0.66 | 208 | -2.0 | 9 | 94 / 19 | yes / yes / yes / yes |
| night_S7_1920x1080.jpg | L3 | 50.4 | 0.12 | 34.5 | 0.24 | 214 | -7.4 | 8 | 150 / 16 | yes / yes / yes / yes |
| night_S8_1920x1080.jpg | L3 | 45.3 | 0.66 | 30.4 | 0.00 | 136 | +19.8 | 0 | 91 / 12 | yes / yes / yes / NO |

## Not measured

L9..L12 (haze / far-field ratios), L17 (glass mask), L18..L20: not run this round (no depth / sky / glass-stencil capture).
