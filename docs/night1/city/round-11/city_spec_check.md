# CITY-SPEC check (tools/export/city_spec_check.py, regions docs/night1/city/spec_regions.json v3)

round folder: `/Users/midir/sm2-n1/city/docs/night1/city/round-11`

## C11-C15 far field (S4)

| line | 1080 | target |
|---|---|---|
| C11 far_shore lap / sky lap | +30.27 PASS | >= 6.0 |
| C11 far_shore flat 8x8 blocks % | +0.00 PASS | <= 40 |
| C12 far_shore (B-R) - sky (B-R) | -0.06 PASS | +-10 |
| C13 far_shore Y - sky Y | -68.21 FAIL | -35..-25 |
| C13 far_shore Y > near_city Y | +79.81 PASS | > 0 |
| C14 far_shore Y - river Y | +23.31 PASS | 5..35 |
| C15 rms far_shore / near_city | +0.31 PASS | 0.25..0.45 |
| T1 silhouette-top std (min of 3 defs, px) | +23.58 PASS | >= 12 |

| region (1080) | Y | B-R | RMS | lap | flat 8x8 pct |
|---|---|---|---|---|---|
| sky | 228.8 | +9.9 | 0.019 | 0.84 | 89 |
| far_shore | 160.6 | +9.9 | 0.186 | 25.43 | 0 |
| river | 137.3 | +24.8 | 0.147 | 7.94 | 27 |
| mid_city | 143.7 | -11.5 | 0.358 | 32.46 | 1 |
| near_city | 80.8 | +1.0 | 0.598 | 20.50 | 2 |
| horizon_far | 180.5 | +11.7 | 0.128 | 12.68 | 2 |

## C1 / C2 facade crops (C1: <= 1.5 % of pixels above Y 204, p95 <= 192, p99 <= 206; C2: mean Y 52..119; daylight views gated, dusk view informational)

| region | res | > 204 % | p95 | p99 | mean Y | C1 | C2 |
|---|---|---|---|---|---|---|---|
| s1_left_stone | 1080 | 0.00 | 93 | 102 | 74.0 | pass | pass |
| s1_right_brick | 1080 | 0.00 | 132 | 158 | 71.8 | pass | pass |
| s1_right_dark | 1080 | 0.00 | 89 | 103 | 58.7 | pass | pass |
| s2_left_stone | 1080 | 0.00 | 176 | 179 | 101.0 | pass | pass |
| s2_gold_glass | 1080 | 0.00 | 107 | 123 | 65.3 | pass | pass |
| s2_white_tower | 1080 | 0.03 | 114 | 151 | 69.4 | pass | pass |
| s2_dark_tower | 1080 | 0.00 | 109 | 114 | 52.8 | pass | pass |
| s5_left_dark | 1080 | 0.49 | 149 | 188 | 62.5 | pass | pass |
| s5_grey_tower | 1080 | 3.66 | 183 | 224 | 100.4 | FAIL | pass |
| s5_teal_glass | 1080 | 0.36 | 107 | 147 | 59.7 | pass | pass |
| s6_left_brown | 1080 | 0.21 | 100 | 142 | 61.5 | pass | pass |
| s7_left_glass (dusk) | 1080 | 0.00 | 77 | 85 | 48.2 | pass | FAIL |
| s7_mid_dark (dusk) | 1080 | 0.08 | 118 | 155 | 55.8 | pass | pass |
| s7_right_masonry (dusk) | 1080 | 0.00 | 90 | 113 | 67.3 | pass | pass |
| s8_glass_right | 1080 | 0.03 | 145 | 171 | 63.3 | pass | pass |
| s8_pale_glass | 1080 | 0.00 | 125 | 145 | 74.5 | pass | pass |
| s8_brick_a | 1080 | 0.00 | 96 | 131 | 58.7 | pass | pass |
| s8_brick_b | 1080 | 0.66 | 188 | 202 | 103.9 | pass | pass |
| s8_grey_tower | 1080 | 0.00 | 173 | 189 | 92.2 | pass | pass |

- 1080: daylight crops C1 pass 15/16, C2 pass 16/16

## Critic r09 boxes (share of pixels above Y 204; C1 limit 1.5 %, S4 far band 10 %)

| region | res | box | > 204 % | limit | p95 | mean Y | result |
|---|---|---|---|---|---|---|---|
| s4_far_band | 1080 | (0, 150, 1300, 300) | 6.60 | 10.0 | 208 | 151.7 | pass |
| s5_mid_tower | 1080 | (640, 40, 880, 700) | 6.01 | 1.5 | 213 | 103.1 | FAIL |
| s6_curb_plaza | 1080 | (1150, 760, 1920, 1080) | 14.65 | 1.5 | 238 | 78.2 | FAIL |
| s8_glass_upper | 1080 | (1270, 0, 1640, 300) | 0.70 | 1.5 | 188 | 162.5 | pass |

## C4 / C6 vehicle and person counts (YOLO11x-seg, conf 0.3, 1080p frame; the count at conf 0.35 is in the json as vehicles_c35)

| view | vehicles | people | traffic lights | line | result |
|---|---|---|---|---|---|
| S1_avenue_street | 17 | 0 | 0 | C4 (cars 5-19, people 6-32, lights >= 1) | cars pass, people FAIL, lights FAIL |
| S2_avenue_swing | 16 | 0 | 0 | C6 (vehicles 14-22) | pass |
| S6_timessq_street | 17 | 1 | 0 | C4 (cars 5-19, people 6-32, lights >= 1) | cars pass, people FAIL, lights FAIL |

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
