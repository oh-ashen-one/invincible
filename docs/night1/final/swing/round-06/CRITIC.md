# Critic r06 — swing / web / flips (blind, pixels only)

Frames at 10/25/60 fps in `critic-r06/frames`, crops in `critic-r06/crops`.

## Axis scores

1. **Web deployment — 5.** Strand connects to the raised palm, arm leads toward the anchor (s5 t=2.9 hand zoom; s2 t=6.9). But the strand **pops in full-length in one frame** at every sampled press: s2 t=5.52→5.53 (60 fps f_0007→f_0008), zero travel frames (W3 wants 0.06–0.2 s flight). Release is better: s4 t=7.25–7.37 the line visibly shortens over ~5 frames. No through-tree/wall lines found (s1 t=2.4, s2 t=14.9, s5 t=2.9).
2. **Web read — 7.** Thin white line ~2–3 px at 1080p (s5 t=2.9: peak 247 vs bg 45), unbroken over 12 consecutive 60 fps frames (s5 t=2.95–3.13), readable day and night, no glow/gaps. No taper; far end fades against sky haze (s2 t=5.9).
3. **Swing body — 6.** Phases read: drop-in extended → legs drive under → lean-back upswing (s1 t=2.0–3.4 strip); sides alternate; poses vary. But the horizontal superman spread is the overused default air pose (s1 t=0.9/5.4/9.1, s4 t=1.1–2.6); leg lag milder than ref swing-canyon-chase t=2.9.
4. **Flips and tricks — 6.** Readable tuck / layout / inverted straddle / upright spread, ~0.4 s held open shapes (s3b t=4.7–6.4; t=8.9 inverted straddle, hero ~0.25 frame height, sky behind). Rotation gentle vs owner clip's ~700°/s tucks (owner S3); ours change shape every ~0.16–0.32 s. s3_flip_chain spends t≈9.5–18 s wall-crawling — trick content runs out mid-clip.
5. **Air and transitions — 6.** Release→float→catch chains without pops; catch pre-reaches the anchor (s4 t=6.5). Float poses evolve too slowly: s4 t=0–1.0 hands-at-head drifts minimally for ~1 s (A4 wants silhouette change per 0.1 s).
6. **Camera presentation — 5.** No roll with the body (s3b t=4.2/5.0 verticals stay vertical); hero usually 0.13–0.25 frame height (bbox-measured). But often steeply top-down (s1 t=2.4, s4 t=5.9) where the reference frames from behind against sky, and no FOV kick or radial speed blur at peak speed — momentum reads flat vs swing-canyon-chase. Hero shrinks to ~0.14 on high flips (s3b t=19.9).

## A/B pack

- swing-chain: B better (blur, momentum). Obvious: B=reference, A=ours.
- swing-presses: B better (two-hand street launch). Obvious: B=reference, A=ours.
- aerial-flips: B better (crisp sky silhouettes). Obvious: B=owner recording, A=ours.
- release-air: B better. Obvious: B=reference, A=ours.
- night-swing: B better. Obvious: B=reference, A=ours.
- progress-swing: no meaningful difference (matched t=2/6/8.5). Guess B=current — low confidence.
- progress-presses: B better — A shows a missing-texture checkerboard on the opening wall (A f_001). Confident: B=current (matches r06 s2), A=previous.
- progress-flips: A better — tricks high against sky, large readable hero (A t=10.3, t=20); B's low against dark facades. Guess A=current (frame-matches r06 s3b), B=previous.
- progress-night: near-identical. Guess B=current — low confidence.

## Biggest gaps (by score impact)

1. **Web shot travel (W3).** Strand pops in full-length every press (s2 t=5.53). Animate tip hand→anchor over 0.06–0.2 s with slight curve (ref swing-start-from-street t≈2.5–3.0). Test: at 60 fps strand grows over ≥4 frames per press; zero pop-ins.
2. **Speed sensation / camera (axes 6, 3).** Add ~10° FOV kick + radial edge blur at swing bottom; cap top-down pitch ≤30° (ref swing-canyon-chase t=2.9). Test: hero 0.2–0.3 frame height at swing bottom; measurable FOV delta stall→peak.
3. **Air-pose evolution/variety (A3/A4/A2).** Float drifts too slowly (s4 t=0–1.0); superman spread recurs (s1 t=0.9/5.4/9.1). Reposition limbs every ~0.2 s; rotate ≥3 air poses (ref owner S6 t=22.1–23.5). Test: pose-signature delta ≥0.15 per 0.3 s; no pose repeats twice in 6 swings.

## Secondary

- No strand taper; far end vanishes against haze (s2 t=5.9).
- Flip tuck peaks gentle; push toward owner's 600–750°/s (F3).
- s3_flip_chain becomes ~8 s of wall-crawl after t≈9.5.
- Hero too small on some high tricks (s3b t=19.9, ~0.14 vs F9's 0.18–0.36).

## Verdict

**APPROACHES TARGET.** Best axis 7 (web read); deployment and camera at 5. Nothing prototype-broken, but one-frame web pop-in, flat speed presentation and slow air poses keep it below the reference. MEETS needs ≥8 everywhere — not met.
