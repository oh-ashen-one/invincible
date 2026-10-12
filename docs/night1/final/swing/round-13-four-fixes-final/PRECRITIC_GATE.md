# Final four-fix pre-critic gate

**Technical capture gate: PASS.** The three runtime `19521659` clips have matching ordered CSV/render/encoded frame and case counts, H.264 yuv420p 1920×1080 at fixed 60 fps, and unchanged BUILD file hashes. This is offline capture completeness; quality review remains open.

| Final clip | Frames | Cases | Quality FAIL lines | Full-clip absent pixels |
| --- | ---: | ---: | --- | --- |
| s3_flip_chain | 1439 | 1 | P1, W3, W4, W5, W7, A5, A7 | none |
| s3b_flip_cases | 1776 | 7 | W2, P1, W3, W5, W7, A2 | none |
| s2_press_variety | 2031 | 9 | W2, P1, W3, W5, W7, W9, W10, A1, A5, A7 | 0.1167–0.1333 (2f) |

The `s3b` final movie has no absent hero mask, no image-edge contact and no `hero_in_frame=0` telemetry row across 1,776 frames; baseline had seven absent-mask frames. This is frame containment, not perfect unobstructed body visibility: the final c6 roof frame at 23.7833 s shows brief parapet occlusion of the lower body, documented in `CAMERA_VERIFICATION.md`. `s3_flip_chain` has no absent or edge-clipped pixel frames. `s2` retains two early absent-mask frames at 0.1167–0.1333 s.

All primary `s3b` strict projected F3 peaks are ≤800°/s (rudi 779, fullTwist 784); W4 is PASS at six of six catches, worst chest rate 354°/s, hand-speed ratio max 2.15. `s3_flip_chain` frontDouble is 773°/s projected and 796°/s true 3D; late barani remains a strict projected F3 failure at 1136°/s while its true 3D axis peak is 686°/s. Its W4 still fails due to a 900°/s wallJump chest rate and one 2.95 hand-speed ratio.

In `s2`, the first firing-arm direction step is 26.0° (closeout 131.6°), with 2.1° tip-arrival aim error; W1 and W4 pass. W2 still fails its broader swing-angle clause despite nine of nine tip arrivals within 20°. The A6 checker counts clip identifiers; the fresh blind critic must judge whether catch endings look distinct in the native footage.

There was no final `s1_swing_chain` recapture for this source. The earlier ordinary-swing candidate remains separate evidence and is not counted in this three-clip gate. See `PRECRITIC_GATE.json` for case counts, quality lines, full-clip camera intervals and flip rates; `FOURFIX_COMPARISON.json` contains the focused baseline-to-final comparison.
