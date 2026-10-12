# CITY-SPEC check (tools/export/city_spec_check.py, regions docs/night1/city/spec_regions.json v3)

round folder: `/Users/midir/sm2-n1/city/docs/night1/city/round-10`

## C11-C15 far field (S4)

| line | 1080 | target |
|---|---|---|
| C11 far_shore lap / sky lap | +20.84 PASS | >= 6.0 |
| C11 far_shore flat 8x8 blocks % | +4.11 PASS | <= 40 |
| C12 far_shore (B-R) - sky (B-R) | -1.68 PASS | +-10 |
| C13 far_shore Y - sky Y | -38.48 FAIL | -35..-25 |
| C13 far_shore Y > near_city Y | +106.80 PASS | > 0 |
| C14 far_shore Y - river Y | +16.90 PASS | 5..35 |
| C15 rms far_shore / near_city | +0.24 FAIL | 0.25..0.45 |
| T1 silhouette-top std (min of 3 defs, px) | +18.98 PASS | >= 12 |

| region (1080) | Y | B-R | RMS | lap | flat 8x8 pct |
|---|---|---|---|---|---|
| sky | 229.0 | +9.8 | 0.019 | 0.82 | 89 |
| far_shore | 190.5 | +8.1 | 0.138 | 17.13 | 4 |
| river | 173.6 | +16.0 | 0.054 | 4.18 | 31 |
| mid_city | 156.1 | -7.6 | 0.283 | 27.47 | 1 |
| near_city | 83.7 | +1.4 | 0.565 | 20.18 | 2 |
| horizon_far | 205.9 | +7.3 | 0.109 | 11.82 | 10 |

## C1 / C2 facade crops (C1: <= 1.5 % of pixels above Y 204, p95 <= 192, p99 <= 206; C2: mean Y 52..119; daylight views gated, dusk view informational)

| region | res | > 204 % | p95 | p99 | mean Y | C1 | C2 |
|---|---|---|---|---|---|---|---|
| s1_left_stone | 1080 | 0.00 | 95 | 106 | 75.1 | pass | pass |
| s1_right_brick | 1080 | 0.00 | 140 | 164 | 73.7 | pass | pass |
| s1_right_dark | 1080 | 0.00 | 93 | 108 | 64.8 | pass | pass |
| s2_left_stone | 1080 | 0.00 | 176 | 179 | 102.4 | pass | pass |
| s2_gold_glass | 1080 | 0.00 | 153 | 171 | 95.6 | pass | pass |
| s2_white_tower | 1080 | 0.03 | 125 | 152 | 75.0 | pass | pass |
| s2_dark_tower | 1080 | 0.00 | 109 | 114 | 54.3 | pass | pass |
| s5_left_dark | 1080 | 0.49 | 149 | 189 | 59.8 | pass | pass |
| s5_grey_tower | 1080 | 3.73 | 185 | 226 | 98.5 | FAIL | pass |
| s5_teal_glass | 1080 | 0.36 | 127 | 160 | 79.2 | pass | pass |
| s6_left_brown | 1080 | 0.20 | 100 | 142 | 61.9 | pass | pass |
| s7_left_glass (dusk) | 1080 | 0.00 | 98 | 106 | 71.5 | pass | pass |
| s7_mid_dark (dusk) | 1080 | 0.09 | 118 | 155 | 56.3 | pass | pass |
| s7_right_masonry (dusk) | 1080 | 0.00 | 93 | 123 | 69.0 | pass | pass |
| s8_glass_right | 1080 | 0.23 | 167 | 187 | 80.3 | pass | pass |
| s8_pale_glass | 1080 | 0.00 | 164 | 175 | 108.9 | pass | pass |
| s8_brick_a | 1080 | 0.00 | 104 | 134 | 60.9 | pass | pass |
| s8_brick_b | 1080 | 0.66 | 188 | 203 | 104.9 | pass | pass |
| s8_grey_tower | 1080 | 0.00 | 176 | 189 | 97.9 | pass | pass |

- 1080: daylight crops C1 pass 15/16, C2 pass 16/16

## Critic r09 boxes (share of pixels above Y 204; C1 limit 1.5 %, S4 far band 10 %)

| region | res | box | > 204 % | limit | p95 | mean Y | result |
|---|---|---|---|---|---|---|---|
| s4_far_band | 1080 | (0, 150, 1300, 300) | 29.55 | 10.0 | 228 | 182.4 | FAIL |
| s5_mid_tower | 1080 | (640, 40, 880, 700) | 5.65 | 1.5 | 208 | 101.9 | FAIL |
| s6_curb_plaza | 1080 | (1150, 760, 1920, 1080) | 14.65 | 1.5 | 238 | 80.0 | FAIL |
| s8_glass_upper | 1080 | (1270, 0, 1640, 300) | 70.37 | 1.5 | 232 | 208.1 | FAIL |

## C4 / C6 vehicle and person counts (YOLO11x-seg, conf 0.3, 1080p frame; the count at conf 0.35 is in the json as vehicles_c35)

| view | vehicles | people | traffic lights | line | result |
|---|---|---|---|---|---|
| S1_avenue_street | 17 | 0 | 0 | C4 (cars 5-19, people 6-32, lights >= 1) | cars pass, people FAIL, lights FAIL |
| S2_avenue_swing | 15 | 0 | 0 | C6 (vehicles 14-22) | pass |
| S6_timessq_street | 18 | 1 | 0 | C4 (cars 5-19, people 6-32, lights >= 1) | cars pass, people FAIL, lights FAIL |

## IP text check (OCR of the 4K frames vs denylist)

- S1_avenue_street_1920x1080.jpg: clean
- S2_avenue_swing_1920x1080.jpg: clean
- S3_rooftop_watertower_1920x1080.jpg: clean
- S4_perch_skyline_1920x1080.jpg: clean
- S5_timessq_south_1920x1080.jpg: clean
- S6_timessq_street_1920x1080.jpg: clean
- S7_sunset_crosstown_1920x1080.jpg: clean
- S8_aerial_midtown_1920x1080.jpg: clean

## Lines not measurable by pixels (judged / hand count; see spec_regions.json manual_lines)

- C3: window-opening depth (frames/sills/recess, varied interior states): judged side by side with the named refs
- C5: night street frame: no night view in the S-set
- C7: S1 trees >= 3, signed storefronts >= 2 per side: hand count
- C8: per-20 m clutter checklist: presence list, not numeric
- C9: S3 wooden water towers >= 2: hand count
- C10: clutter per rooftop: judged
- C16: shore embankment strip vs water: unmeasured in the spec
