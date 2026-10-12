# CITY-SPEC check (tools/export/city_spec_check.py, regions docs/night1/city/spec_regions.json v2)

round folder: `/Users/midir/sm2-n1/city/docs/night1/city/round-09`

## C11-C15 far field (S4)

| line | 1080 | target |
|---|---|---|
| C11 far_shore lap / sky lap | +27.03 PASS | >= 6.0 |
| C11 far_shore flat 8x8 blocks % | +1.43 PASS | <= 40 |
| C12 far_shore (B-R) - sky (B-R) | -3.82 PASS | +-10 |
| C13 far_shore Y - sky Y | -33.62 PASS | -35..-25 |
| C13 far_shore Y > near_city Y | +87.34 PASS | > 0 |
| C14 far_shore Y - river Y | +23.43 PASS | 5..35 |
| C15 rms far_shore / near_city | +0.39 PASS | 0.25..0.45 |

| region (1080) | Y | B-R | RMS | lap | flat 8x8 pct |
|---|---|---|---|---|---|
| sky | 228.9 | +9.9 | 0.019 | 0.84 | 89 |
| far_shore | 195.3 | +6.0 | 0.148 | 22.58 | 1 |
| river | 171.9 | +19.5 | 0.075 | 4.32 | 54 |
| mid_city | 164.4 | -7.5 | 0.236 | 27.24 | 1 |
| near_city | 108.0 | +3.3 | 0.383 | 21.91 | 0 |
| horizon_far | 219.3 | +3.1 | 0.071 | 15.02 | 1 |

## C1 / C2 facade crops (C1: <= 1.5 % of pixels above Y 204, p95 <= 192, p99 <= 206; C2: mean Y 52..119; daylight views gated, dusk view informational)

| region | res | > 204 % | p95 | p99 | mean Y | C1 | C2 |
|---|---|---|---|---|---|---|---|
| s1_left_stone | 1080 | 0.00 | 80 | 91 | 61.9 | pass | pass |
| s1_right_brick | 1080 | 0.00 | 139 | 164 | 66.5 | pass | pass |
| s1_right_dark | 1080 | 0.00 | 75 | 101 | 53.1 | pass | pass |
| s2_left_stone | 1080 | 0.00 | 176 | 179 | 98.9 | pass | pass |
| s2_gold_glass | 1080 | 0.00 | 151 | 169 | 91.3 | pass | pass |
| s2_white_tower | 1080 | 0.03 | 125 | 151 | 74.1 | pass | pass |
| s2_dark_tower | 1080 | 0.00 | 109 | 114 | 47.1 | pass | FAIL |
| s5_left_dark | 1080 | 0.48 | 149 | 188 | 56.6 | pass | pass |
| s5_grey_tower | 1080 | 3.70 | 185 | 226 | 98.3 | FAIL | pass |
| s5_teal_glass | 1080 | 0.35 | 127 | 160 | 78.5 | pass | pass |
| s6_left_brown | 1080 | 0.19 | 99 | 141 | 57.2 | pass | pass |
| s7_left_glass (dusk) | 1080 | 0.00 | 89 | 97 | 61.5 | pass | pass |
| s7_mid_dark (dusk) | 1080 | 0.08 | 115 | 153 | 51.4 | pass | FAIL |
| s7_right_masonry (dusk) | 1080 | 0.00 | 79 | 119 | 56.2 | pass | pass |
| s8_glass_right | 1080 | 0.23 | 167 | 188 | 80.3 | pass | pass |
| s8_pale_glass | 1080 | 0.00 | 164 | 175 | 108.8 | pass | pass |
| s8_brick_a | 1080 | 0.00 | 104 | 134 | 60.9 | pass | pass |
| s8_brick_b | 1080 | 0.65 | 188 | 202 | 105.0 | pass | pass |
| s8_grey_tower | 1080 | 0.01 | 176 | 189 | 98.0 | pass | pass |

- 1080: daylight crops C1 pass 15/16, C2 pass 15/16

## C4 / C6 vehicle and person counts (YOLO11x-seg, conf 0.3, 1080p frame; the count at conf 0.35 is in the json as vehicles_c35)

| view | vehicles | people | traffic lights | line | result |
|---|---|---|---|---|---|
| S1_avenue_street | 17 | 0 | 0 | C4 (cars 5-19, people 6-32, lights >= 1) | cars pass, people FAIL, lights FAIL |
| S2_avenue_swing | 19 | 0 | 0 | C6 (vehicles 14-22) | pass |
| S6_timessq_street | 16 | 1 | 0 | C4 (cars 5-19, people 6-32, lights >= 1) | cars pass, people FAIL, lights FAIL |

## Lines not measurable by pixels (judged / hand count; see spec_regions.json manual_lines)

- C3: window-opening depth (frames/sills/recess, varied interior states): judged side by side with the named refs
- C5: night street frame: no night view in the S-set
- C7: S1 trees >= 3, signed storefronts >= 2 per side: hand count
- C8: per-20 m clutter checklist: presence list, not numeric
- C9: S3 wooden water towers >= 2: hand count
- C10: clutter per rooftop: judged
- C16: shore embankment strip vs water: unmeasured in the spec
