# Round 13 pre-critic gate

**Technical capture gate: PASS.** All six fixed-step clips have matching MP4/telemetry/metadata frame counts and case order, H.264 1920×1080 yuv420p at 60 fps, completed pixel-aware W/A checks, and unchanged BUILD.json runtime fingerprints. The s3 and s3b flip checks are present. This validates offline capture completeness, not gameplay acceptance or real-time frame rate.

**Quality checks contain FAIL lines.** They are preserved for the independent critic and do not indicate an incomplete capture.

| Clip | Frames | Cases | Quality FAIL lines |
| --- | ---: | ---: | --- |
| s1_swing_chain | 1199 | 1 | W2, P1, W4, W5, W7 |
| s2_press_variety | 2031 | 9 | W2, P1, W3, W5, W7, W9, W10, A1, A5, A7 |
| s3_flip_chain | 1439 | 1 | P1, W3, W4, W5, W7, A5, A7 |
| s3b_flip_cases | 1776 | 7 | W2, P1, W3, W5, W7, A2 |
| s4_release_float | 1199 | 1 | P1, W3, W4, W5 |
| s5_night_swing | 1199 | 1 | W2, P1, W4, W7 |

Full machine-readable evidence: `PRECRITIC_GATE.json`; per-clip `*_CHECK.txt`, `*_check.json`, and flip reports.
