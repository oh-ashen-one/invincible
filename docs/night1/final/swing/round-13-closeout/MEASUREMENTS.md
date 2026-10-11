# Pixel review evidence

Independent review, 2026-10-11; GPT-6.1 Sol / extra-high as selected for this task. CPU extraction on verified Apple M3 Ultra. All output lives in this review folder. No source, telemetry, keys or builder history read. A/B decisions were saved in AB_CHOICES.md before IDENTITY_GUESSES.md and native candidate inspection.

All six native candidate clips were inspected in timestamped overviews, with dense sequences for web presses, releases, flips, catches and the seven-case sequence. Reference clips named by the prompt and the owner aerobatics clip were inspected. Overview sheets are context; dense frames determine motion findings. Camera scale and containment use uncropped 1920x1080 native frames.

## Native roof containment

s3b_flip_cases frames 1425–1434 (23.750–23.900 s): ten consecutive native frames clipped or absent, 10/60 = 0.167 s of frame slots. Frames 1431, 1432, 1433 (23.850, 23.8667, 23.8833 s) contain no visible hero: 3/60 = 0.050 s. Frame 1430 has only a tiny body fragment at the bottom; frame 1434 has a partial arm/torso at the bottom. Frame 1435 (23.9167 s) again contains the full body. Evidence: roof_dense sheets and roof_full PNGs. This is a visible framing defect; the movement continues and recovers.

Manual silhouette traces (approximately +/-10 px) at frames 1425 and 1426 show visible spans about 875 and 863 px, or 0.81 and 0.80 of native frame height. The arm/head extends above frame, so these are lower bounds on the complete hero height. The nearby second frame confirms the extreme. Ordinary inverted-shape frames 96 and 102 (1.600 and 1.700 s) are approximately 0.45 and 0.40 H. Manual traced boxes are in manual_pixel_bounds.json and manual_bbox JPGs. Automatic HSV isolation was rejected because it missed disconnected limbs; its outputs were removed. Do not infer a pooled percentile from these selected extremes.

s3_flip_chain also clips the feet at its native top edge around 11.98–12.10 s, corroborating a recurring containment concern. Dense crop starts at native y=0; native overview corroborates this top-edge loss.

## Web press / travel

s2_press_variety firing hand changes from beside the hip at frame 141 (2.350 s) to overhead at frame 142 (2.3667 s). The arm snaps visibly within one 60 Hz interval. The camera/background change is small compared with the arm movement. This is a pose finding, not an inferred input time.

Visible strand lengths on three frames before and three starting with appearance: frames 139,140,141,142,143,144 = approximately 0,0,0,20,360,330 native pixels. These are visible bright-segment lengths; the last two run out of the top edge, so complete hand-to-anchor lengths and landing time cannot be measured. Do not call this a one-frame full-length appearance: a short tip is present in frame 142. The launch_full PNG crops preserve native pixel scale. The strand visibly goes slack/retracts over s2 4.30–4.55 s; no one-frame disappearance finding is made.

s5_night_swing 1.000 s: three normal scans across its taut strand, centered near native (562,100), (627,200), (692,300), give bright-core width approximately 3.25 px at grayscale >=160 using 0.25 px bilinear samples. Measurement uncertainty is roughly 0.5 px from compression/threshold. See night_line_native.png, night_line_crop.png and night_line_widths.json. Day and night sequences show strong continuous readability; this is sampled visual evidence, not a claimed exhaustive 95 percent census.

## Held shapes and rotation

s3b first release: approximately two complete body rotations over 0.48–2.12 s, about 720/1.64 = 439 degrees/s mean. The inverted straddle remains open approximately 1.48–1.80 s = 0.32 s, with head–hip axis around 160–175 degrees and much slower motion than the preceding tuck. Pencil around 5.10–5.40 s is also readable. Layout around 9.44–9.72 s is near a 0.3 s hold, with about +/-0.04 s boundary uncertainty; it is not counted as a definitive extra pass. All seven cases show readable distinct air actions. Compressed shapes most consistently read as tuck; a tight straight-leg pike is not convincingly demonstrated.

Screen-axis sample after camera blend: native frames 67 (1.1167 s) and 77 (1.2833 s) show roughly 140 degrees of head–hip turn over 0.1667 s (~840 degrees/s). Foreshortening/manual endpoint error gives at least +/-180 degrees/s uncertainty. This does not establish a world-space >800 degrees/s violation; no such hard failure is scored. The first rotation and the later fast tuck/open contrast establish easing rather than a uniform spin.

## Catch variety

At s3b 2.76, 6.80, 10.80, 15.10, 19.30 and 28.10 s, catches converge on an upright one-arm reach with similar knee flexion; hand side and camera-facing direction change, but three distinct end/catch body styles are not visibly established. First-case upright reach occupies approximately 2.24–2.64 s before the web/catch, a more conspicuous preparation pause than the owner 2.24–2.44 s transition. Catch onset/anchor landing is not precisely measured because the anchor is off frame.
