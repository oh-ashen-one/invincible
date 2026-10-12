# CITY-SPEC check (tools/export/city_spec_check.py, regions docs/night1/city/spec_regions.json v1)

round folder: `/Users/midir/sm2-n1/city/docs/night1/city/round-08`

## C11-C15 far field (S4)

| line | 1080 | 4k | target |
|---|---|---|---|
| C11 far_shore lap / sky lap | +27.08 PASS | +23.47 PASS | >= 6.0 |
| C11 far_shore flat 8x8 blocks % | +1.43 PASS | +2.14 PASS | <= 40 |
| C12 far_shore (B-R) - sky (B-R) | -3.84 PASS | -3.63 PASS | +-10 |
| C13 far_shore Y - sky Y | -33.65 PASS | -33.95 PASS | -35..-25 |
| C13 far_shore Y > near_city Y | +112.47 PASS | +111.65 PASS | > 0 |
| C14 far_shore Y - river Y | +23.42 PASS | +23.49 PASS | 5..35 |
| C15 rms far_shore / near_city | +0.26 PASS | +0.26 PASS | 0.25..0.45 |

| region (1080) | Y | B-R | RMS | lap | flat 8x8 pct |
|---|---|---|---|---|---|
| sky | 228.9 | +9.8 | 0.019 | 0.84 | 89 |
| far_shore | 195.3 | +6.0 | 0.149 | 22.63 | 1 |
| river | 171.8 | +19.6 | 0.075 | 4.21 | 55 |
| mid_city | 152.4 | -8.6 | 0.301 | 29.51 | 1 |
| near_city | 82.8 | +1.3 | 0.575 | 20.30 | 2 |
| horizon_far | 219.2 | +3.2 | 0.072 | 15.15 | 0 |

## C1 / C2 facade crops (C1: <= 1.5 % of pixels above Y 204, p95 <= 192, p99 <= 206; C2: mean Y 52..119; daylight views gated, dusk view informational)

| region | res | > 204 % | p95 | p99 | mean Y | C1 | C2 |
|---|---|---|---|---|---|---|---|
| s1_left_stone | 1080 | 0.00 | 42 | 68 | 22.0 | pass | FAIL |
| s1_left_glass | 1080 | 0.00 | 76 | 113 | 34.9 | pass | FAIL |
| s1_right_brick | 1080 | 0.00 | 121 | 155 | 37.4 | pass | FAIL |
| s1_right_dark | 1080 | 0.00 | 39 | 75 | 17.6 | pass | FAIL |
| s1_left_stone | 4k | 0.00 | 44 | 71 | 22.2 | pass | FAIL |
| s1_left_glass | 4k | 0.00 | 85 | 119 | 35.8 | pass | FAIL |
| s1_right_brick | 4k | 0.01 | 122 | 157 | 35.6 | pass | FAIL |
| s1_right_dark | 4k | 0.00 | 38 | 77 | 17.4 | pass | FAIL |
| s2_left_stone | 1080 | 0.00 | 175 | 178 | 89.3 | pass | pass |
| s2_gold_glass | 1080 | 0.00 | 145 | 165 | 78.7 | pass | pass |
| s2_white_tower | 1080 | 0.03 | 123 | 149 | 71.7 | pass | pass |
| s2_dark_tower | 1080 | 0.00 | 108 | 113 | 26.2 | pass | FAIL |
| s2_left_stone | 4k | 0.00 | 176 | 178 | 89.4 | pass | pass |
| s2_gold_glass | 4k | 0.00 | 144 | 165 | 76.1 | pass | pass |
| s2_white_tower | 4k | 0.09 | 123 | 154 | 71.0 | pass | pass |
| s2_dark_tower | 4k | 0.00 | 109 | 114 | 25.9 | pass | FAIL |
| s5_left_dark | 1080 | 0.48 | 147 | 187 | 47.7 | pass | FAIL |
| s5_grey_tower | 1080 | 3.70 | 185 | 226 | 97.8 | FAIL | pass |
| s5_teal_glass | 1080 | 0.34 | 126 | 159 | 76.4 | pass | pass |
| s5_left_dark | 4k | 0.51 | 149 | 191 | 48.6 | pass | FAIL |
| s5_grey_tower | 4k | 3.89 | 189 | 225 | 99.6 | FAIL | pass |
| s5_teal_glass | 4k | 0.54 | 128 | 164 | 76.8 | pass | pass |
| s6_right_white | 1080 | 0.42 | 178 | 193 | 77.4 | pass | pass |
| s6_left_brown | 1080 | 0.08 | 77 | 122 | 39.4 | pass | FAIL |
| s6_right_white | 4k | 0.51 | 179 | 197 | 75.3 | pass | pass |
| s6_left_brown | 4k | 0.08 | 80 | 124 | 39.4 | pass | FAIL |
| s7_left_glass (dusk) | 1080 | 0.00 | 64 | 70 | 28.1 | pass | FAIL |
| s7_mid_dark (dusk) | 1080 | 0.07 | 104 | 147 | 37.2 | pass | FAIL |
| s7_right_masonry (dusk) | 1080 | 0.00 | 44 | 106 | 15.0 | pass | FAIL |
| s7_left_glass (dusk) | 4k | 0.00 | 64 | 70 | 27.9 | pass | FAIL |
| s7_mid_dark (dusk) | 4k | 0.09 | 105 | 149 | 36.2 | pass | FAIL |
| s7_right_masonry (dusk) | 4k | 0.00 | 46 | 108 | 14.0 | pass | FAIL |
| s8_glass_right | 1080 | 0.23 | 167 | 188 | 80.2 | pass | pass |
| s8_pale_glass | 1080 | 0.00 | 164 | 175 | 108.5 | pass | pass |
| s8_brick_a | 1080 | 0.00 | 103 | 134 | 60.7 | pass | pass |
| s8_brick_b | 1080 | 0.67 | 188 | 202 | 105.0 | pass | pass |
| s8_grey_tower | 1080 | 0.01 | 176 | 189 | 97.9 | pass | pass |
| s8_glass_right | 4k | 0.42 | 167 | 190 | 78.4 | pass | pass |
| s8_pale_glass | 4k | 0.00 | 165 | 177 | 104.0 | pass | pass |
| s8_brick_a | 4k | 0.00 | 105 | 137 | 60.5 | pass | pass |
| s8_brick_b | 4k | 0.85 | 188 | 203 | 103.4 | pass | pass |
| s8_grey_tower | 4k | 0.00 | 178 | 189 | 96.8 | pass | pass |

- 1080: daylight crops C1 pass 17/18, C2 pass 11/18
- 4k: daylight crops C1 pass 17/18, C2 pass 11/18

## C4 / C6 vehicle and person counts (YOLO11x-seg, conf 0.3, 1080p frame; the count at conf 0.35 is in the json as vehicles_c35)

| view | vehicles | people | traffic lights | line | result |
|---|---|---|---|---|---|
| S1_avenue_street | 16 | 0 | 0 | C4 (cars 5-19, people 6-32, lights >= 1) | cars pass, people FAIL, lights FAIL |
| S2_avenue_swing | 17 | 0 | 0 | C6 (vehicles 14-22) | pass |
| S6_timessq_street | 16 | 1 | 0 | C4 (cars 5-19, people 6-32, lights >= 1) | cars pass, people FAIL, lights FAIL |

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
