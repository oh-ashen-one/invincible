# Round test numbers (numbers only)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Produced by `tools/perf_ue/round_tests.py` from the stills / clips in this folder: `look_spec_check.py` (LOOK-SPEC lines of `docs/night1/look/SPEC.md`), `night_tests.py` (round-1 critic tests), `clip_check.py` (clips).
Luma Y = 0.2126 R + 0.7152 G + 0.0722 B of the 8-bit sRGB values; every still is resized to 1920 px wide first; near-black = Y < 10; clipped = any channel >= 250; B-R = mean(B) - mean(R).
Bands: golden L1 mean 61..100, near-black <= 8 %, clipped <= 1.8 %, B-R -55..-20 (S7: L5, clipped <= 0.7 %); midday L2 mean 83..97, near-black <= 0.05 %, clipped 0.00 %, B-R -19..+8 (S4: L11 horizon - sky >= +3);
night L3 mean 37..60, near-black <= 1 %, clipped <= 1.7 %, B-R -13..+13 (L8), street views S1 / S5 / S6: L13 >= 5 lit blobs, L14 bottom-third p10 15..30 and p90 >= 100; L10 far shore 15..32 Y below the sky and B-R within +-10 of the sky; L17 glass p10 >= 20 (daylight).

## Stills 1920x1080

| still | spec | mean Y | Y<10 % | clipped % | B-R | lit blobs (bottom half) | bottom-third p90 / p10 | within (mean / near-black / clipped / B-R) |
|---|---|---|---|---|---|---|---|---|
| midday_S1_1920x1080.jpg | L2 | 91.7 | 0.00 | 0.00 | -3.5 | 4 | 146 / 84 | yes / yes / yes / yes |
| midday_S2_1920x1080.jpg | L2 | 88.5 | 0.00 | 0.00 | -12.4 | 16 | 121 / 29 | yes / yes / yes / yes |
| midday_S3_1920x1080.jpg | L2 | 93.7 | 0.00 | 0.02 | -4.9 | 11 | 148 / 32 | yes / yes / NO / yes |
| midday_S4_1920x1080.jpg | L2 | 84.6 | 0.00 | 0.00 | +2.9 | 12 | 94 / 29 | yes / yes / yes / yes |
| midday_S5_1920x1080.jpg | L2 | 93.8 | 0.00 | 0.00 | -4.3 | 5 | 162 / 21 | yes / yes / yes / yes |
| midday_S6_1920x1080.jpg | L2 | 91.3 | 0.00 | 0.00 | -5.9 | 8 | 142 / 55 | yes / yes / yes / yes |
| midday_S7_1920x1080.jpg | L2 | 89.0 | 0.00 | 0.04 | -1.6 | 10 | 127 / 27 | yes / yes / NO / yes |
| midday_S8_1920x1080.jpg | L2 | 92.7 | 0.00 | 0.00 | +2.9 | 9 | 124 / 25 | yes / yes / yes / yes |
| golden_S1_1920x1080.jpg | L1 | 96.4 | 0.00 | 0.11 | -24.9 | 4 | 164 / 96 | yes / yes / yes / yes |
| golden_S2_1920x1080.jpg | L1 | 93.4 | 0.01 | 0.17 | -43.4 | 14 | 119 / 27 | yes / yes / yes / yes |
| golden_S3_1920x1080.jpg | L1 | 74.5 | 0.00 | 0.36 | -19.8 | 11 | 115 / 22 | yes / yes / yes / NO |
| golden_S4_1920x1080.jpg | L1 | 111.5 | 0.00 | 0.06 | -52.3 | 17 | 146 / 37 | NO / yes / yes / yes |
| golden_S5_1920x1080.jpg | L1 | 88.9 | 0.00 | 0.10 | -41.9 | 8 | 127 / 15 | yes / yes / yes / yes |
| golden_S6_1920x1080.jpg | L1 | 93.9 | 0.00 | 0.02 | -37.1 | 6 | 136 / 73 | yes / yes / yes / yes |
| golden_S7_1920x1080.jpg | L5 | 87.9 | 0.00 | 3.19 | -43.2 | 10 | 125 / 23 | yes / yes / NO / yes |
| golden_S8_1920x1080.jpg | L1 | 83.8 | 0.00 | 0.72 | -39.2 | 16 | 111 / 17 | yes / yes / yes / yes |

### Far field (S4, boxes of docs/night1/city/spec_regions.json v1, 1080p)

| still | sky Y (B-R) | horizon_far Y (B-R) | far_shore Y (B-R) | river Y | L10 far-shore Y - sky Y (-32..-15) | L10 far-shore B-R - sky B-R (+-10) | L11 horizon_far - sky (>= +3, midday) | far-shore - river Y (P1 C14: 5..35) |
|---|---|---|---|---|---|---|---|---|
| midday_S4_1920x1080.jpg | 124.1 (+4.1) | 133.0 (+4.6) | 105.4 (+4.3) | 96.0 | -18.8 yes | +0.2 yes | +8.9 yes | +9.3 yes |
| golden_S4_1920x1080.jpg | 144.7 (-78.7) | 114.2 (-48.0) | 117.1 (-60.5) | 120.0 | -27.6 yes | +18.2 NO | -30.5 (n/a) | -2.9 NO |

### Glass p10 (L17: >= 20; glass-only boxes)

| still | box | p10 Y | mean Y | B-R | L17 |
|---|---|---|---|---|---|
| midday_S1_1920x1080.jpg | s1_left_glass | 66.0 | 103.6 | -1.5 | yes |
| midday_S2_1920x1080.jpg | s2_gold_glass | 47.1 | 80.1 | -39.2 | yes |
| midday_S5_1920x1080.jpg | s5_teal_glass | 96.8 | 144.5 | +8.6 | yes |
| midday_S7_1920x1080.jpg | s7_left_glass | 28.6 | 57.5 | +0.5 | yes |
| midday_S8_1920x1080.jpg | s8_glass_right | 28.6 | 123.9 | +7.0 | yes |
| midday_S8_1920x1080.jpg | s8_pale_glass | 45.6 | 90.4 | +13.0 | yes |
| golden_S1_1920x1080.jpg | s1_left_glass | 50.3 | 101.0 | -24.5 | yes |
| golden_S2_1920x1080.jpg | s2_gold_glass | 40.3 | 78.9 | -72.7 | yes |
| golden_S5_1920x1080.jpg | s5_teal_glass | 86.1 | 148.2 | -45.2 | yes |
| golden_S7_1920x1080.jpg | s7_left_glass | 20.6 | 43.5 | -18.7 | yes |
| golden_S8_1920x1080.jpg | s8_glass_right | 17.0 | 93.2 | -21.1 | NO |
| golden_S8_1920x1080.jpg | s8_pale_glass | 31.7 | 87.8 | -35.0 | yes |

### Night street views (L13 / L14)

| still | lit blobs (L13 >= 5) | bottom-third p10 (L14 15..30) | bottom-third p90 (L14 >= 100) |
|---|---|---|---|



## Stills 3840x2160

| still | spec | mean Y | Y<10 % | clipped % | B-R | lit blobs (bottom half) | bottom-third p90 / p10 | within (mean / near-black / clipped / B-R) |
|---|---|---|---|---|---|---|---|---|
| midday_S1_3840x2160.jpg | L2 | 91.5 | 0.00 | 0.00 | -3.6 | 4 | 143 / 80 | yes / yes / yes / yes |
| midday_S2_3840x2160.jpg | L2 | 89.3 | 0.00 | 0.00 | -12.0 | 15 | 124 / 30 | yes / yes / yes / yes |
| midday_S3_3840x2160.jpg | L2 | 94.3 | 0.00 | 0.04 | -4.6 | 13 | 149 / 32 | yes / yes / NO / yes |
| midday_S4_3840x2160.jpg | L2 | 85.2 | 0.00 | 0.00 | +2.8 | 4 | 97 / 28 | yes / yes / yes / yes |
| midday_S5_3840x2160.jpg | L2 | 94.5 | 0.00 | 0.00 | -4.0 | 7 | 164 / 21 | yes / yes / yes / yes |
| midday_S6_3840x2160.jpg | L2 | 92.3 | 0.00 | 0.00 | -5.9 | 8 | 143 / 56 | yes / yes / yes / yes |
| midday_S7_3840x2160.jpg | L2 | 91.7 | 0.00 | 0.04 | -1.5 | 16 | 130 / 27 | yes / yes / NO / yes |
| midday_S8_3840x2160.jpg | L2 | 93.9 | 0.00 | 0.00 | +2.9 | 9 | 126 / 25 | yes / yes / yes / yes |
| golden_S1_3840x2160.jpg | L1 | 96.4 | 0.00 | 0.06 | -24.3 | 7 | 165 / 94 | yes / yes / yes / yes |
| golden_S2_3840x2160.jpg | L1 | 93.2 | 0.00 | 0.15 | -42.1 | 15 | 122 / 28 | yes / yes / yes / yes |
| golden_S3_3840x2160.jpg | L1 | 74.8 | 0.00 | 0.41 | -19.6 | 10 | 119 / 22 | yes / yes / yes / NO |
| golden_S4_3840x2160.jpg | L1 | 110.0 | 0.00 | 0.04 | -51.1 | 18 | 150 / 35 | NO / yes / yes / yes |
| golden_S5_3840x2160.jpg | L1 | 88.2 | 0.00 | 0.08 | -41.9 | 7 | 128 / 15 | yes / yes / yes / yes |
| golden_S6_3840x2160.jpg | L1 | 93.7 | 0.00 | 0.02 | -38.3 | 6 | 139 / 74 | yes / yes / yes / yes |
| golden_S7_3840x2160.jpg | L5 | 88.2 | 0.00 | 3.10 | -43.3 | 10 | 126 / 23 | yes / yes / NO / yes |
| golden_S8_3840x2160.jpg | L1 | 82.6 | 0.00 | 0.66 | -37.5 | 14 | 110 / 17 | yes / yes / yes / yes |
| night_S1_3840x2160.jpg | L3 | 47.2 | 0.00 | 1.04 | -3.1 | 14 | 167 / 27 | yes / yes / yes / yes |
| night_S2_3840x2160.jpg | L3 | 51.0 | 0.00 | 0.12 | -8.6 | 6 | 106 / 18 | yes / yes / yes / yes |
| night_S3_3840x2160.jpg | L3 | 39.4 | 0.00 | 0.07 | -1.0 | 4 | 62 / 17 | yes / yes / yes / yes |
| night_S4_3840x2160.jpg | L3 | 58.1 | 0.00 | 0.01 | +5.9 | 12 | 101 / 23 | yes / yes / yes / yes |
| night_S5_3840x2160.jpg | L3 | 51.0 | 0.00 | 0.56 | +3.6 | 14 | 133 / 18 | yes / yes / yes / yes |
| night_S6_3840x2160.jpg | L3 | 52.0 | 0.00 | 0.14 | -3.7 | 9 | 119 / 25 | yes / yes / yes / yes |
| night_S7_3840x2160.jpg | L3 | 54.7 | 0.00 | 0.97 | -11.8 | 7 | 188 / 19 | yes / yes / yes / yes |
| night_S8_3840x2160.jpg | L3 | 52.0 | 0.00 | 0.01 | +3.2 | 7 | 110 / 17 | yes / yes / yes / yes |

### Far field (S4, boxes of docs/night1/city/spec_regions.json v1, 1080p)

| still | sky Y (B-R) | horizon_far Y (B-R) | far_shore Y (B-R) | river Y | L10 far-shore Y - sky Y (-32..-15) | L10 far-shore B-R - sky B-R (+-10) | L11 horizon_far - sky (>= +3, midday) | far-shore - river Y (P1 C14: 5..35) |
|---|---|---|---|---|---|---|---|---|
| midday_S4_3840x2160.jpg | 123.3 (+4.1) | 132.4 (+4.8) | 104.9 (+4.3) | 95.4 | -18.4 yes | +0.2 yes | +9.1 yes | +9.5 yes |
| golden_S4_3840x2160.jpg | 141.2 (-77.8) | 111.3 (-47.2) | 114.9 (-59.4) | 117.0 | -26.3 yes | +18.4 NO | -29.9 (n/a) | -2.1 NO |
| night_S4_3840x2160.jpg | 67.1 (+23.8) | 41.3 (+20.3) | 48.9 (+16.0) | 36.5 | -18.2 yes | -7.8 yes | -25.9 (n/a) | +12.4 yes |

### Glass p10 (L17: >= 20; glass-only boxes)

| still | box | p10 Y | mean Y | B-R | L17 |
|---|---|---|---|---|---|
| midday_S1_3840x2160.jpg | s1_left_glass | 68.2 | 107.5 | -1.2 | yes |
| midday_S2_3840x2160.jpg | s2_gold_glass | 47.1 | 77.7 | -37.6 | yes |
| midday_S5_3840x2160.jpg | s5_teal_glass | 98.1 | 146.2 | +9.2 | yes |
| midday_S7_3840x2160.jpg | s7_left_glass | 29.2 | 61.2 | +0.4 | yes |
| midday_S8_3840x2160.jpg | s8_glass_right | 26.4 | 123.9 | +6.8 | yes |
| midday_S8_3840x2160.jpg | s8_pale_glass | 43.4 | 90.7 | +12.8 | yes |
| golden_S1_3840x2160.jpg | s1_left_glass | 48.8 | 102.8 | -23.8 | yes |
| golden_S2_3840x2160.jpg | s2_gold_glass | 39.6 | 74.7 | -67.9 | yes |
| golden_S5_3840x2160.jpg | s5_teal_glass | 85.3 | 151.1 | -45.4 | yes |
| golden_S7_3840x2160.jpg | s7_left_glass | 20.8 | 44.8 | -18.9 | yes |
| golden_S8_3840x2160.jpg | s8_glass_right | 16.6 | 91.6 | -19.5 | NO |
| golden_S8_3840x2160.jpg | s8_pale_glass | 28.8 | 83.4 | -32.6 | yes |

### Night street views (L13 / L14)

| still | lit blobs (L13 >= 5) | bottom-third p10 (L14 15..30) | bottom-third p90 (L14 >= 100) |
|---|---|---|---|
| night_S1_3840x2160.jpg | 14 yes | 26.6 yes | 167.4 yes |
| night_S5_3840x2160.jpg | 14 yes | 17.6 yes | 133.1 yes |
| night_S6_3840x2160.jpg | 9 yes | 24.6 yes | 119.2 yes |



## Round-1 critic night tests (night_tests.py; peak >= 120, valley <= 40, blur sigma 8 px at 1080p, bottom third)

| still | mean Y | share < 10/255 | distinct light pools (target >= 4) | pool peaks |
|---|---|---|---|---|
| night_S1_3840x2160.jpg | 46.8 | 0.00 % | 3 | [254, 154, 147] |
| night_S6_3840x2160.jpg | 51.6 | 0.00 % | 4 | [226, 200, 134, 121] |

## Swing clips (clip_check.py on every 3rd frame at 960x540; hero luma from the P3 hero-only depth capture)

| clip | frames measured | mean Y (mean / min / max) | B-R (mean / p10 / p90) | frames outside B-R +-13 (night L8 band; midday / golden bands differ) | near-black % | clipped % | L18 edge / centre sharpness p10 / p50 / p90 (0.20..0.65) | hero box luma min / p5 / mean (frames < 40) |
|---|---|---|---|---|---|---|---|---|
| swing_midday.mp4 | 240 | 86.0 / 49.8 / 121.6 | -7.8 / -12.0 / -2.3 | 7.5 % | 0.02 | 0.01 | 0.61 / 0.78 / 1.17 | 45.2 / 57.4 / 100.8 (0) |
