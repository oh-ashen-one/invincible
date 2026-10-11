# Blind critique — piece SW, round-10 (pixels/motion only; ffmpeg-measured)

## Per-axis scores

**1. Web deployment — 6.** Arm leads, tip travels visibly (s2_press_variety t=2.72 arm out, no strand; lands by t=2.84, close anchor, W3 OK); origin at palm once attached (s1_swing_chain t=2.0–2.4). Fail: in flight the strand is a mid-air segment off the hand — 25 fps: t=2.72 none, t=2.76 ~87 px gap, t=2.80 two pieces ~70 px gap, t=2.84 continuous. W1/W5 violated on flight frames.

**2. Web read — 7.** Night strand core 2–4 px at 1080p (s5_night_swing t=8.4), white, stable, no flicker (s1 t=2.0–3.4). Docked for in-flight gaps.

**3. Swing body — 7.** Phases read: horizontal extension at bottom (s1 t=2.44–2.92), legs trail, upright upswing hang, crouch variants (t=6–9); no robotic loop. Below reference snap (swing-canyon-chase).

**4. Flips and tricks — 6.** Eased readable shapes: ~180° tuck in ~0.28 s (~640 °/s) into held inverted hang ~0.4 s on the web (s3_flip_chain t=17.0–17.8); spread, pike, swan (s3b t=0.7–1.6, 5.0). Hero size compliant: 0.19 (t=0.82) and 0.32 (t=5.0) of frame height by visual recount. Gap: ours chain 1 rotation + hold; owner chains 3 in 2.8 s (S3 8.32–11.36); tricks often against facades, not sky (F9).

**5. Air and transitions — 6.** Release→float→trick→catch flows (s3 t=17–19; s4_release_float t≈1.8 retracts over ~2–4 frames, no one-frame vanish at 25 fps). Borderline held float ~0.6 s (s4 t=1.0–1.6). Sampled catches pop-free.

**6. Camera presentation — 6.** No roll with body (verticals constant, s3 t=17–19); readable framing. Missing reference speed language: no FOV kick or radial streaks (ref trick-release-sky t≈4.2 vs static-sharp s1/s4).

## A/B decisions (then identity)

- swing-chain: **A** (blur, speed, snap). A = reference, obvious (symbiote suit); B = ours.
- swing-presses: **B**. B = reference, obvious (red/blue suit + HUD); A = ours.
- aerial-flips: **A** (crisp sky silhouettes). A = reference/owner footage, obvious (purple tint); B = ours.
- release-air: **B**. B = reference, obvious; A = ours.
- night-swing: **A**. A = reference, obvious (HUD); B = ours.
- progress-swing: **A** — bigger hero, clearer bottom extension + release flip; B repeats flat hangs. Both ours; guess A = current (closer frame-match to s1).
- progress-flips: **A** — sky-backdrop tricks, held inversions; B low against dark glass, hero lost behind buildings t≈5.5–8. Guess A = current (closer to s3b).
- progress-presses: **tie, lean A** — same choreography incl. the flight gap t=2.76–2.80; A frames hero better t≈17.3. Guess A = current (low confidence).
- progress-night: **tie, lean A** — both sag at t=8.5, straighten by ~8.67; A's strand brighter. Guess A = current (low confidence).

## Top gaps (builder instructions)

1. **Grow the strand from the palm during flight** (s2 t=2.76–2.80, 70–87 px hole). Draw hand→tip every flight frame. Test: 60 fps on s2, palm-to-strand < 8 cm-equivalent every press→attach frame.
2. **Chain 2–3 rotations on long releases** (ours: 1 + hold, s3 t=17.0–17.8; owner S3: 3 in 2.8 s, ~385 °/s). Test: ≥ 2 rotations per long release, mean 300–500 °/s, peak ≤ 800 °/s (F1–F3).
3. **Add speed sensation at peak velocity**: FOV kick 10–15° + radial edge blur at swing bottom/dives (ref trick-release-sky t≈4.2). Test: FOV(peak) − FOV(stall) ≥ 8°.

## Secondary issues

1. Strand behind a foreground building corner, s2 t≈2.96 — verify W7 clearance.
2. Float pose near the 0.6 s A4 limit (s4 t=1.0–1.6).
3. Tricks framed against facades/billboards, not sky (s3 t≈18.6–19) — F9 backdrop.
4. Pack night strands border on glowing beam (progress-night t=8.53).

## Verdict

**APPROACHES TARGET.** No axis ≥ 8 with evidence. Cheapest big wins: flight-frame strand gap, multi-rotation chains, speed sensation.
