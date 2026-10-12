# CITY-SPEC check (tools/export/city_spec_check.py, regions docs/night1/city/spec_regions.json v1)

round folder: `/Users/midir/sm2-n1/city/docs/night1/city/round-06`

## C11-C15 far field (S4)

| line | 1080 | 4k | target |
|---|---|---|---|
| C11 far_shore lap / sky lap | +4.76 FAIL | +5.04 FAIL | >= 6.0 |
| C11 far_shore flat 8x8 blocks % | +20.18 PASS | +19.82 PASS | <= 40 |
| C12 far_shore (B-R) - sky (B-R) | -1.04 PASS | -0.94 PASS | +-10 |
| C13 far_shore Y - sky Y | -14.04 FAIL | -14.05 FAIL | -35..-25 |
| C13 far_shore Y > near_city Y | +116.52 PASS | +116.07 PASS | > 0 |
| C14 far_shore Y - river Y | -3.39 FAIL | -3.33 FAIL | 5..35 |
| C15 rms far_shore / near_city | +0.08 FAIL | +0.08 FAIL | 0.25..0.45 |

| region (1080) | Y | B-R | RMS | lap | flat 8x8 pct |
|---|---|---|---|---|---|
| sky | 229.9 | +11.1 | 0.017 | 0.70 | 95 |
| far_shore | 215.9 | +10.1 | 0.040 | 3.33 | 20 |
| river | 219.3 | +9.7 | 0.012 | 1.00 | 83 |
| mid_city | 187.0 | +0.2 | 0.176 | 15.80 | 4 |
| near_city | 99.4 | +4.5 | 0.497 | 22.47 | 1 |
| horizon_far | 235.2 | +5.0 | 0.036 | 2.44 | 60 |

## C1 / C2 facade crops (C1: <= 1.5 % of pixels above Y 204, p95 <= 192, p99 <= 206; C2: mean Y 52..119; daylight views gated, dusk view informational)

| region | res | > 204 % | p95 | p99 | mean Y | C1 | C2 |
|---|---|---|---|---|---|---|---|
| s1_left_stone | 1080 | 0.00 | 57 | 82 | 35.1 | pass | FAIL |
| s1_left_glass | 1080 | 0.00 | 107 | 133 | 60.3 | pass | pass |
| s1_right_brick | 1080 | 0.02 | 125 | 163 | 45.5 | pass | FAIL |
| s1_right_dark | 1080 | 0.00 | 39 | 76 | 21.3 | pass | FAIL |
| s1_left_stone | 4k | 0.00 | 59 | 85 | 35.9 | pass | FAIL |
| s1_left_glass | 4k | 0.00 | 111 | 140 | 61.7 | pass | pass |
| s1_right_brick | 4k | 0.04 | 126 | 165 | 43.8 | pass | FAIL |
| s1_right_dark | 4k | 0.00 | 39 | 77 | 21.2 | pass | FAIL |
| s2_left_stone | 1080 | 21.57 | 226 | 230 | 118.9 | FAIL | pass |
| s2_gold_glass | 1080 | 0.15 | 164 | 184 | 95.5 | pass | pass |
| s2_white_tower | 1080 | 4.55 | 204 | 221 | 110.3 | FAIL | pass |
| s2_dark_tower | 1080 | 0.00 | 130 | 150 | 34.1 | pass | FAIL |
| s2_left_stone | 4k | 21.62 | 226 | 231 | 119.2 | FAIL | FAIL |
| s2_gold_glass | 4k | 0.18 | 164 | 184 | 92.9 | pass | pass |
| s2_white_tower | 4k | 4.98 | 204 | 225 | 109.2 | FAIL | pass |
| s2_dark_tower | 4k | 0.00 | 131 | 150 | 33.5 | pass | FAIL |
| s5_left_dark | 1080 | 0.48 | 153 | 189 | 59.0 | pass | pass |
| s5_grey_tower | 1080 | 3.78 | 192 | 232 | 104.9 | FAIL | pass |
| s5_teal_glass | 1080 | 0.36 | 159 | 179 | 100.3 | pass | pass |
| s5_left_dark | 4k | 0.51 | 151 | 192 | 52.7 | pass | pass |
| s5_grey_tower | 4k | 4.02 | 192 | 233 | 106.1 | FAIL | pass |
| s5_teal_glass | 4k | 0.54 | 161 | 182 | 100.1 | pass | pass |
| s6_right_white | 1080 | 49.36 | 225 | 231 | 180.8 | FAIL | FAIL |
| s6_left_brown | 1080 | 0.08 | 86 | 126 | 49.4 | pass | FAIL |
| s6_right_white | 4k | 49.20 | 226 | 233 | 179.3 | FAIL | FAIL |
| s6_left_brown | 4k | 0.09 | 88 | 128 | 49.9 | pass | FAIL |
| s7_left_glass (dusk) | 1080 | 0.00 | 65 | 72 | 28.9 | pass | FAIL |
| s7_mid_dark (dusk) | 1080 | 0.07 | 104 | 147 | 37.8 | pass | FAIL |
| s7_right_masonry (dusk) | 1080 | 0.00 | 45 | 106 | 15.6 | pass | FAIL |
| s7_left_glass (dusk) | 4k | 0.00 | 64 | 73 | 28.7 | pass | FAIL |
| s7_mid_dark (dusk) | 4k | 0.09 | 105 | 150 | 36.8 | pass | FAIL |
| s7_right_masonry (dusk) | 4k | 0.00 | 47 | 108 | 14.6 | pass | FAIL |
| s8_glass_right | 1080 | 16.54 | 216 | 225 | 129.0 | FAIL | FAIL |
| s8_pale_glass | 1080 | 7.54 | 210 | 220 | 141.8 | FAIL | FAIL |
| s8_brick_a | 1080 | 0.08 | 134 | 166 | 70.3 | pass | pass |
| s8_brick_b | 1080 | 10.88 | 224 | 239 | 115.5 | FAIL | pass |
| s8_grey_tower | 1080 | 5.64 | 211 | 230 | 135.0 | FAIL | FAIL |
| s8_glass_right | 4k | 15.34 | 216 | 227 | 127.0 | FAIL | FAIL |
| s8_pale_glass | 4k | 8.36 | 211 | 219 | 138.3 | FAIL | FAIL |
| s8_brick_a | 4k | 0.14 | 136 | 165 | 69.2 | pass | pass |
| s8_brick_b | 4k | 10.90 | 226 | 240 | 113.5 | FAIL | pass |
| s8_grey_tower | 4k | 5.52 | 210 | 230 | 132.3 | FAIL | FAIL |

- 1080: daylight crops C1 pass 10/18, C2 pass 9/18
- 4k: daylight crops C1 pass 10/18, C2 pass 8/18

## Lines not measurable by pixels (judged / hand count; see spec_regions.json manual_lines)

- C3: window-opening depth (frames/sills/recess, varied interior states): judged side by side with the named refs
- C5: night street frame: no night view in the S-set
- C7: S1 trees >= 3, signed storefronts >= 2 per side: hand count
- C8: per-20 m clutter checklist: presence list, not numeric
- C9: S3 wooden water towers >= 2: hand count
- C10: clutter per rooftop: judged
- C16: shore embankment strip vs water: unmeasured in the spec
