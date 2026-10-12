# CITY-SPEC check (tools/export/city_spec_check.py, regions docs/night1/city/spec_regions.json v1)

round folder: `/Users/midir/sm2-n1/city/docs/night1/city/round-07`

## C11-C15 far field (S4)

| line | 1080 | 4k | target |
|---|---|---|---|
| C11 far_shore lap / sky lap | +27.26 PASS | +23.38 PASS | >= 6.0 |
| C11 far_shore flat 8x8 blocks % | +1.25 PASS | +2.14 PASS | <= 40 |
| C12 far_shore (B-R) - sky (B-R) | -3.83 PASS | -3.63 PASS | +-10 |
| C13 far_shore Y - sky Y | -33.65 PASS | -33.94 PASS | -35..-25 |
| C13 far_shore Y > near_city Y | +112.53 PASS | +111.73 PASS | > 0 |
| C14 far_shore Y - river Y | +23.47 PASS | +23.49 PASS | 5..35 |
| C15 rms far_shore / near_city | +0.26 PASS | +0.26 PASS | 0.25..0.45 |

| region (1080) | Y | B-R | RMS | lap | flat 8x8 pct |
|---|---|---|---|---|---|
| sky | 228.9 | +9.8 | 0.019 | 0.83 | 89 |
| far_shore | 195.3 | +6.0 | 0.148 | 22.58 | 1 |
| river | 171.8 | +19.5 | 0.075 | 4.23 | 53 |
| mid_city | 154.0 | -11.6 | 0.298 | 24.73 | 1 |
| near_city | 82.8 | +1.3 | 0.575 | 20.36 | 2 |
| horizon_far | 219.2 | +3.2 | 0.072 | 15.12 | 1 |

## C1 / C2 facade crops (C1: <= 1.5 % of pixels above Y 204, p95 <= 192, p99 <= 206; C2: mean Y 52..119; daylight views gated, dusk view informational)

| region | res | > 204 % | p95 | p99 | mean Y | C1 | C2 |
|---|---|---|---|---|---|---|---|
| s1_left_stone | 1080 | 0.00 | 45 | 73 | 23.8 | pass | FAIL |
| s1_left_glass | 1080 | 0.00 | 95 | 128 | 49.8 | pass | FAIL |
| s1_right_brick | 1080 | 0.00 | 121 | 155 | 37.8 | pass | FAIL |
| s1_right_dark | 1080 | 0.00 | 37 | 75 | 17.2 | pass | FAIL |
| s1_left_stone | 4k | 0.00 | 46 | 73 | 24.1 | pass | FAIL |
| s1_left_glass | 4k | 0.00 | 98 | 131 | 50.5 | pass | FAIL |
| s1_right_brick | 4k | 0.01 | 122 | 157 | 35.8 | pass | FAIL |
| s1_right_dark | 4k | 0.00 | 37 | 77 | 17.2 | pass | FAIL |
| s2_left_stone | 1080 | 0.00 | 175 | 178 | 89.2 | pass | pass |
| s2_gold_glass | 1080 | 0.00 | 145 | 165 | 78.9 | pass | pass |
| s2_white_tower | 1080 | 0.03 | 123 | 149 | 71.7 | pass | pass |
| s2_dark_tower | 1080 | 0.00 | 108 | 113 | 26.3 | pass | FAIL |
| s2_left_stone | 4k | 0.00 | 176 | 178 | 89.3 | pass | pass |
| s2_gold_glass | 4k | 0.00 | 145 | 165 | 76.4 | pass | pass |
| s2_white_tower | 4k | 0.10 | 123 | 154 | 71.0 | pass | pass |
| s2_dark_tower | 4k | 0.00 | 109 | 114 | 26.0 | pass | FAIL |
| s5_left_dark | 1080 | 0.48 | 149 | 188 | 52.0 | pass | FAIL |
| s5_grey_tower | 1080 | 3.71 | 185 | 226 | 98.0 | FAIL | pass |
| s5_teal_glass | 1080 | 0.36 | 126 | 159 | 76.8 | pass | pass |
| s5_left_dark | 4k | 0.51 | 149 | 191 | 48.8 | pass | FAIL |
| s5_grey_tower | 4k | 3.90 | 189 | 225 | 99.8 | FAIL | pass |
| s5_teal_glass | 4k | 0.55 | 128 | 164 | 77.0 | pass | pass |
| s6_right_white | 1080 | 0.88 | 189 | 203 | 151.6 | pass | FAIL |
| s6_left_brown | 1080 | 0.07 | 80 | 124 | 42.3 | pass | FAIL |
| s6_right_white | 4k | 1.03 | 192 | 204 | 150.9 | pass | FAIL |
| s6_left_brown | 4k | 0.09 | 82 | 125 | 42.6 | pass | FAIL |
| s7_left_glass (dusk) | 1080 | 0.00 | 64 | 71 | 28.3 | pass | FAIL |
| s7_mid_dark (dusk) | 1080 | 0.07 | 104 | 147 | 37.6 | pass | FAIL |
| s7_right_masonry (dusk) | 1080 | 0.00 | 44 | 106 | 15.1 | pass | FAIL |
| s7_left_glass (dusk) | 4k | 0.00 | 64 | 71 | 28.0 | pass | FAIL |
| s7_mid_dark (dusk) | 4k | 0.09 | 105 | 150 | 36.6 | pass | FAIL |
| s7_right_masonry (dusk) | 4k | 0.00 | 46 | 108 | 14.1 | pass | FAIL |
| s8_glass_right | 1080 | 0.24 | 167 | 187 | 80.2 | pass | pass |
| s8_pale_glass | 1080 | 0.00 | 164 | 175 | 108.5 | pass | pass |
| s8_brick_a | 1080 | 0.00 | 104 | 134 | 60.8 | pass | pass |
| s8_brick_b | 1080 | 0.63 | 188 | 203 | 105.0 | pass | pass |
| s8_grey_tower | 1080 | 0.01 | 176 | 189 | 97.9 | pass | pass |
| s8_glass_right | 4k | 0.41 | 167 | 190 | 78.4 | pass | pass |
| s8_pale_glass | 4k | 0.00 | 165 | 177 | 104.1 | pass | pass |
| s8_brick_a | 4k | 0.00 | 105 | 137 | 60.5 | pass | pass |
| s8_brick_b | 4k | 0.86 | 188 | 203 | 103.5 | pass | pass |
| s8_grey_tower | 4k | 0.00 | 178 | 189 | 96.8 | pass | pass |

- 1080: daylight crops C1 pass 17/18, C2 pass 10/18
- 4k: daylight crops C1 pass 17/18, C2 pass 10/18

## C4 / C6 vehicle and person counts (YOLO11x-seg, conf 0.35, 1080p frame)

| view | vehicles | people | traffic lights | line | result |
|---|---|---|---|---|---|
| S1_avenue_street | 0 | 0 | 0 | C4 (cars 5-19, people 6-32, lights >= 1) | cars FAIL, people FAIL, lights FAIL |
| S2_avenue_swing | 0 | 0 | 0 | C6 (vehicles 14-22) | FAIL |
| S6_timessq_street | 0 | 2 | 0 | C4 (cars 5-19, people 6-32, lights >= 1) | cars FAIL, people FAIL, lights FAIL |

## IP text check (OCR of the 4K frames vs denylist)

- S1_avenue_street_3840x2160.jpg: clean
- S2_avenue_swing_3840x2160.jpg: clean
- S3_rooftop_watertower_3840x2160.jpg: clean
- S4_perch_skyline_3840x2160.jpg: clean
- S5_timessq_south_3840x2160.jpg: clean
- S6_timessq_street_3840x2160.jpg: clean
- S7_sunset_crosstown_3840x2160.jpg: clean
- S8_aerial_midtown_3840x2160.jpg: clean

## Lines not measurable by pixels (judged / hand count; see spec_regions.json manual_lines)

- C3: window-opening depth (frames/sills/recess, varied interior states): judged side by side with the named refs
- C5: night street frame: no night view in the S-set
- C7: S1 trees >= 3, signed storefronts >= 2 per side: hand count
- C8: per-20 m clutter checklist: presence list, not numeric
- C9: S3 wooden water towers >= 2: hand count
- C10: clutter per rooftop: judged
- C16: shore embankment strip vs water: unmeasured in the spec
