# Critic round 05 — swing/web/flips (blind, pixels only)

## Axis scores

1. **Web deployment: 6** — s2 t=5.50–5.58 (60 fps frames): arm rises before the strand, strand grows hand→up-right over ~3–4 frames (~0.06 s, fast end of W3); s2 t=5.74 crop: strand starts at the raised palm; s3 t=15.2 catch: arm leads, strand from hand. FAILS: s4 t≈1.72 (60 fps r_007→r_008): strand vanishes in ONE frame at release (W8); s2 t=10.4–12.8: hero dangles plumb-static on a vertical strand against a dark facade >2 s — reads as a barely-answered press (W10 spirit).
2. **Web read: 7** — s2 t=5.83 (p_08 crop): strand ~2–3 px at 1080p, white on dark facade, continuous; s5 t=4.0/8.0: bright readable line at night, no segment gaps, no bloom beam; 60 fps sweep s2 t=5.70–5.95: no flicker. No taper toward anchor measured — line is uniform width.
3. **Swing body: 6** — s1 t=1.0 horizontal superman legs trailing; t=5.1 vertical hang by facade; t=5.4 legs trail through arc: poses evolve per swing, several styles per 6 swings. But leg lag/drive is subtler than swing-canyon-chase (hero's legs never snap through the bottom), and the s2 hang kills momentum dead.
4. **Flips/tricks: 6** — s3 t=12.4–15.3: invert→tuck→held spread ~1.0 s (body axis ~140°±5° at t=12.9–13.8, ≤60°/s — F4 met)→swan dive (t=14.7, fully extended)→catch 15.2 within ~0.25 s (F8 met). s3b t=15.7–16.3: edge vault→inverted pencil→straddle. BUT owner clip S3 does 3 rotations in 2.8 s (~385°/s mean); ours manages ~1–1.5 per long release with long near-frozen holds (F1/F5 short). Hero ~18–23 % of frame height (s3 t=14.7: ~190/1080 px; s3b t=12.0: ~250/1080) — low edge of F9.
5. **Air/transitions: 5** — s4 t≈2.0–3.2: same spread falling pose held >0.6 s with minimal silhouette change (A4 fail); the one-frame strand vanish breaks release→float continuity (W8); s4 t=17.5–18.5 hero drifts to the frame edge mid-float. Good: s3 t=15.0–15.4 catch blends arm-first, no chest whip visible.
6. **Camera presentation: 5** — s4 spends long stretches with the hero at ~5–10 % of frame height (t=7.0: ~40 px tall); reference swing-canyon-chase f_0040 hero ≈32 %. s1/s4 favor high top-down angles instead of the close 3–6 m chase; tricks sit at the low F9 bound. No roll with the body (verticals stay vertical through the s3 t=12.4–15.3 trick), no wall clips, stable tracking.

## A/B decisions (then identity)

- swing-chain: **B** — close chase cam, hero ~30 % of frame, speed reads. Identity obvious (different game): B = reference.
- swing-presses: **A** — street-level start, web visibly fired from hand at t≈2–3, large hero. B (ours) opens with a long unanswered rooftop fall and the dark-facade dangle. Obvious: A = reference.
- night-swing: **A** — close framing, HUD, bright speed. B = ours (s5-like). Obvious: A = reference.
- release-air: **A** — big hero against sky on release, visible web arc. B = ours (s4-like, tiny hero). Obvious: A = reference.
- aerial-flips: **A** — hero large, rotations readable. B = ours (golden, smaller hero). Obvious: A = reference.
- progress-swing: **tie** — matched frames at t=2/5/8/14/16/17.5 near-identical (same poses, same strand). Guess: A = previous round, B = current (no visual evidence).
- progress-night: **tie** — same. Guess B = current.
- progress-presses: **tie** — same. Guess B = current.
- progress-flips: **A** — canyon route reads closer and cleaner; B's rooftop cases show checkerboard placeholder roofs (t=12.0) and a smaller hero. Identity: A = current s3_flip_chain, B = current s3b_flip_cases (lengths/routes match).

## Biggest gaps (ordered by score impact)

1. **Camera distance/framing** (axes 6, 5, 4): bring the chase camera to 3–6 m behind and slightly above the hero; reference swing-canyon-chase f_0040 and trick-release-sky keep hero ≈25–35 % of frame height. Test: hero bbox height ≥0.25 of frame height on ≥95 % of swing frames and ≥0.18 on every trick frame, s1–s5.
2. **Release lifecycle** (axes 5, 1): strand must leave the hand and retract/go slack over 0.15–0.40 s (W8) — today it vanishes in one 60 fps frame (s4 t≈1.72); and falling poses must evolve every ~0.1 s sample, no held spread >0.6 s (s4 t≈2.0–3.2). Reference: trick-release-sky release beat. Test: strand tip visible shrinking handward on ≥90 % of releases; pose signature changes ≥0.15 per 0.3 s in float.
3. **Flip energy vs owner clip** (axis 4): 2–3 rotations per long release at 300–500°/s mean with fast tucks between held open shapes (owner S3: 1080°/2.8 s); ours holds a near-static spread ~1.0 s mid-trick (s3 t=12.9–13.8). Test: per trick, total rotation ≥720° and peak/slowest rate ratio ≥3 (F1/F2/F5) measured from body axis.

## Secondary issues

- s2 t=10.4–12.8: static plumb-bob hang on a vertical strand — add pendulum sway/leg drift or re-fire promptly.
- Shot travel ~0.06 s and no in-flight wave (W3 fast edge, W6 missing curvature before tension).
- Checkerboard placeholder rooftops under tricks (s3b t=12.0 etc.) break trick presentation.
- s4 t=17.5–18.5: hero near/behind frame edge during low float.

## Verdict: **FAILS TARGET** (no axis ≥8; strongest axes: web read 7, deployment/swing/flips 6)
