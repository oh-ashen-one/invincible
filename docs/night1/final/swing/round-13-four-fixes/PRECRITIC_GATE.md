# Four-fix pre-critic gate

**Technical capture gate: PASS.** All four fixed-step MP4s, ordered telemetry rows and case counts match their render metadata; H.264 yuv420p 1920×1080 at 60 fps. The BUILD.json binary, web material and render-profile hashes still match. These are offline captures, not measured real-time FPS or owner gameplay acceptance.

**Quality review remains open.** The unchanged checker FAIL lines below are retained for the critic. A6 program/clip counts do not establish visible catch styles.

| Clip | Frames | Cases | Quality FAIL lines | Full-clip absent pixels |
| --- | ---: | ---: | --- | --- |
| s3b_flip_cases | 1776 | 7 | W2, P1, W3, W4, W5, W7, A2 | 11.7166–11.7166 (1f) |
| s2_press_variety | 2031 | 9 | W2, P1, W3, W5, W7, W9, W10, A1, A5, A7 | 0.1167–0.1333 (2f) |
| s3_flip_chain | 1439 | 1 | W2, P1, W3, W4, W5, W7, A5, A7 | none |
| s1_swing_chain | 1199 | 1 | W2, P1, W4, W5, W7 | none |

The former `s3b` roof-catch absence at 23.867–23.900 s has zero absent pixel frames in this capture. The earlier `s3b` window retains one absent frame at 11.7166 s; `s2` retains two early absent frames at 0.1167–0.1333 s. `s3_flip_chain` has no absent or edge-clipped pixel frames. `s3b` c6 still has three `hero_in_frame=0` telemetry rows, but its hero pixel mask stays inside the native frame there; the critic should inspect this distinction.

The corrected strict projected F3 checker passes every primary `s3b` flip, including rudi 779°/s and fullTwist 784°/s. `s3_flip_chain` still fails frontDouble 818°/s (world 3D axis 827°/s) and late barani 1006°/s projected (world 3D axis 680°/s). Its backSingle catch has a 0.354 m hand step in one 60 Hz frame and W4 hand-speed ratio 6.37. `s3b` W4 also regresses from a closeout PASS to 67% within 400°/s and four of six hand-speed ratios above 2.5. `s2` W1 and W4 pass, with the first launch shoulder-to-hand step reduced from 131.6° to 26.0° and tip-arrival aim error 2.1°.

See `PRECRITIC_GATE.json` for exact case counts, clip checks, full-clip camera intervals and flip rates; `FOURFIX_COMPARISON.json` contains the focused before/after telemetry comparison.
