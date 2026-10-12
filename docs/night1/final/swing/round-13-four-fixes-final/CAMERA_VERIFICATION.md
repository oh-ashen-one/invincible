# Camera containment verification

2026-10-12. GPT-6.1 Sol / xhigh camera worker; read-only runtime review. Targets and masks unchanged. This note records the camera-loss repairs, not a full TC-A..TC-K or owner-gameplay acceptance.

## Latest c3 catch completion

**PASS on runtime `19521659`.** Source evidence: `../round-13-four-fixes-completion-probe/s3b_flip_cases.mp4` and its telemetry; raw case `s3_c3_right/route_telemetry.csv` under the task cache. The c3 case contains 262 telemetry rows through 4.3500 s: zero absent masks, zero contacts with any of the four native mask edges, zero `hero_in_frame=0`, and zero lens-sphere/geometry flags.

The previous final candidate lost the hero at case **3.9000 s**, full-clip **11.7166 s**, with adjacent right-edge clipping. Native 1920x1080 PNGs `MovieFrame00323` through `00326` were inspected before cleanup: the complete hero remains visible over case 3.8500–3.9000 s. The render metadata records 92 pre-roll frames cut, making `MovieFrame00326` the formerly missing 3.9000 s frame. It also matches encoded combined-movie frame 703 at 11.7167 s, which the root inspected independently. No head, hand or foot crosses an image edge in those samples.

| Telemetry case time | Native mask bounds: left, top, right, bottom | Closest image-edge margin |
| --- | --- | --- |
| 3.8833 s | 1192, 196, 1576, 584 | 196 px top |
| 3.9000 s | 1268, 172, 1760, 564 | 160 px right |
| 3.9167 s | 1292, 216, 1892, 552 | 28 px right |
| 3.9333 s | 1200, 348, 1748, 576 | 172 px right |

These margins are the existing rendered-mask telemetry measurements. Its rendered-pose/mask sampling has a frame delay; native PNGs were inspected directly rather than treating a padded projected body box as a silhouette. All 19 rows over case 3.8000–4.1000 s have nonzero masks fully inside 1920x1080. Placement-backtracking bit 32 occurs at 3.8667, 3.8833, 3.9000 and 3.9167 s; the final angle and physical collision checks remain active.

The original raw PNGs were cleaned after encoding. A 1920x1080 critical-frame extraction from completion-movie frame 703 is published as [camera-c3-retained.png](camera-c3-retained.png). Root inspected an independent extraction too. No engine was launched or source edited for this review.

## Earlier c6 roof/wall evidence

The camera worker directly inspected camera3's native c6 wall frame at 3.3333 s and confirmed head/right-arm clipping. The subsequent tail-guard c6 probe was independently inspected by the root: zero disappeared or clipped native silhouettes over 2.5000–3.5500 s, including all four mask edges. Roof rows at 3.0333/3.0500 s retained conservative padded-box failure flags while their native masks were fully inside the image; those flags were not described as disappearance.

That c6 result predates the latest c3 completion build. It is prior scoped evidence, not a claim that c6 was recaptured in the completion subset. The final promoted movie/telemetry set is the root's integration verification gate. Nominal TC-K limits still do not fully pass: the root measured c6 maxima improving from 14.96 to 8.47 degrees pitch, 12.25 to 9.95 degrees yaw, and 2.118 to 1.485 m position per frame. Camera loss completion does not imply all camera presentation or continuity targets passed.

## Final seven-case integration gate

The same runtime19521659 complete seven-case movie and telemetry are now present in this folder. All1,776 native-mask rows have a visible hero, no image-edge contact and no hero_in_frame failure. This includes both c3 and c6 in the same final build. Root independently recomputed those four fields from the final CSV using the published fourfix checker. The earlier targeted native-frame inspections remain the visual evidence at the previously failing moments. Nominal TC-K presentation limits remain a separate qualification.

Root also viewed final native c6 frames at23.7833 and24.0833seconds: see [roof](final-c6-roof.png) and [wall](final-c6-wall.png). The hero remains on-screen, but the rooftop parapet briefly occludes the lower body in the first image; the wall image shows the whole character. The mask/frustum result is containment evidence, not proof that every limb remains unobstructed by world geometry. Do not relabel it as perfect full-body visibility throughout the route. Independent visual review remains separate.
