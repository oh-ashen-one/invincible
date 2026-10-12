# Critic r07 — piece SW. Blind; pixels only.

## Scores
**1. Web deployment — 6/10.** Good: shot travel visible at s2_press_variety.mp4 @20.28→20.40 (strand grows hand→facade over ~3 frames @25 fps ≈0.12 s, W3); strand from the palm on canyon attaches (s1_swing_chain.mp4 @16.8; s2 @19.68); trick catch arm-up, body ~upright (s3b_flip_cases.mp4 @23.28). Fail: s2 @8.68–8.96 hero hangs vertical on a dark facade, arms out symmetric, the only candidate strand a ~1 px line landing on the head, not a hand (full-res crops). Release @20.24: strand full length 3 frames before, faint slack line +0.04/+0.12/+0.24 s after — visible retract, W8 OK.

**2. Web read — 5/10.** Measured profiles: s1 @2.36 strand 3 px mid tapering to 0.5–1.5 px; s2 @20.40 0.5–2.5 px with sub-threshold gaps; reference swing-canyon-chase @3.16: 1.5–3.5 px, brighter. Night (s5 @12.96) reads; golden-hour sky/facades and dark glass are too faint.

**3. Swing body — 6/10.** Drop-in superman (s2 @19.68), tucked bottoms, extended upswings; momentum carries. But the same straight-legged arms-out hang recurs (s1 6–10 s; s3b @16.2) and consecutive swings read near-identical vs canyon-chase's variety; leg lag barely readable.

**4. Flips and tricks — 6/10.** s3b @20.8–23.3: ~2 rotations in 2.1 s (≈340 °/s, in F2); tuck (22.20), inverted straddle (22.64), layouts ≥3 frames @25 fps each; catch ≤0.25 s after last shape (23.28). Wall-run present. Vs owner clip: no held open shape ≥0.3 s (owner: pencil 0.36–0.64 s, throne 0.48 s); shapes softer than the reference.

**5. Air and transitions — 5/10.** s4_release_float @15.2–16.5: one symmetric spread held >1 s skimming taxis — A4 wants silhouette change every 0.1 s; hover-y vs trick-release-sky. Chains elsewhere fluid (s2 @20.2–20.6; s3b @23.3).

**6. Camera — 6/10.** Smooth, no body-roll, hero centered; trick hero ≈0.3 frame height (F9 OK). Fails: s1 @15.7–16.3 camera brushes a facade corner (window frames fill half the screen); s3b @8–10 tricks small against busy facades.

## A/B (better → identity guess)
- swing-chain: B (energy, strand, arcs) — obviously reference. swing-presses: B (street-start pull-up) — obviously reference (HUD). release-air: A (hang time, wall catch) — obviously reference. aerial-flips: B (bigger hero, sky, richer shapes) — obviously the owner real-game recording. night-swing: A (lit pools, car-roof beat) — obviously reference (HUD).
- progress-swing: A marginally (deeper superman ~2.3 s); guess B = current (strand leaves extended hand @11.0; A reads hip-level), low confidence. progress-presses: near tie, A marginally (framing 8–10 s); no guess. progress-flips: B (big sky tricks vs A's dark-canyon reads @4.5–6.5); guess A = current, low confidence. progress-night: B marginally (brighter strand @1.8–3.0 s); guess B = current, low confidence.

## Biggest gaps (by score impact)
1. **Strand thickness/contrast (axes 1–2).** Draw 2–4 px at 1080 p, 5–60 m, brighter core; today 0.5–2.5 px, vanishes on dark glass. Ref: canyon-chase @3.16. Test: luminance profile at 8 points along the strand on 3 web-on frames per clip — each ≥2 px and ≥25 levels above background.
2. **Wall-adjacent press pose + origin (axis 1).** s2 @8.6–9.0: arms out, strand at head. Arm must reach within 20° of shoulder→anchor; strand from the palm, ≥2 px on dark facades. Ref: swing-start-from-street. Test: s2 wall-case attach frames — strand start within palm radius of hand bone, arm raised.
3. **Air-pose variety + release carry (axis 5).** s4 float holds one spread >1 s, low and slow. Release pops up/forward; float silhouette evolves every ~0.1 s. Ref: trick-release-sky @1–3 s. Test: pose-signature diff above threshold per 0.1 s sample; no pose held >0.6 s.

## Secondary
- Camera brushes facade corner, s1 @15.7–16.3.
- Flip framing against busy facades, hero small (s3b @8–10); F9 wants sky behind.
- No held open shape ≥0.3 s (F4) though rates are in range.
- s5 night very dark; little facade streak vs webwings-bridge-night.

## Verdict
**APPROACHES TARGET** — all axes 5–6 with evidence; nothing at the 8+ bar.
