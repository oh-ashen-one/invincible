# Orchestrator verification of independent critic claims

The critic received no builder notes, telemetry or identity map. After it reported its main findings, the orchestrator independently extracted the cited frames from the final native 60 fps MP4s.

- **Camera loss confirmed:** `s3b_flip_cases`, frames 1431-1433 (23.8500, 23.8667, 23.8833 s), has no visible hero. At frames 1425-1426 (23.7500 and 23.7667 s), the hero is already clipped at the top and occupies most of the image height. Frame 1434 (23.9000 s) shows partial recovery at the bottom. `verification-camera.jpg` contains these six native-frame samples with labels. This agrees with the three-zero-frame focused probe; it is not a 100% containment pass.
- **Firing-arm snap confirmed:** `s2_press_variety`, frames 141-142 (2.3500-2.3667 s), changes from an arm-down posture to an overhead firing posture in one frame. Adjacent frames 140 and 143 show the surrounding action in `verification-arm.jpg`. This validates the visual discontinuity without assigning a new root cause.

The contact sheets are resized for review; the unchanged native MP4s are the measurement source. Only candidate footage is published here. No reference footage is included. These confirmations do not initiate another implementation round.

After the critic finalized its report, the previously withheld key confirmed that progress-presses A and progress-flips B are the current checkpoint. Swing and night matched-route pairs were ties. Most reference pairs preferred the reference; the low-confidence night preference favored the current checkpoint. AB_REVIEW_MAP.json records the normalized-file identities/hashes. This is one subjective blind comparison, not a controlled cross-critic numerical improvement claim.

Criterion distinction: the firing-arm snap is confirmed from pixels at launch. The report mentions W4 as an easing target, but the unchanged automatic s2 W4 attach checker passes. The observed launch snap does not establish a W4 attach-window failure or an input-latency measurement.
