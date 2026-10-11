# Critic: SW round 09

Blind review of `round-09/*.mp4` vs reference + owner clips. Frames at 10/25/60 fps in `critic-r09/frames/`; hero tracked by suit color; strand width from perpendicular brightness slices.

## Scores

1. **Web deployment: 7** — s2 press t≈2.36–2.42 (60 fps): arm chambers, extends, strand is a ~25 px stub at the fist at t=2.360, >400 px one frame later — palm origin, correct hand, but travel ≈0.03 s vs W3's 0.06–0.20 s. Release at s4 t≈1.63–1.87 retracts with slack over ~0.23 s (W8 met).
2. **Web read: 7** — Core 3–4 px at 1080p (s2 f_0010 slices: 5/4/4/3 px), readable day and night (s5 t≈5.56). Retraction renders as dark dashes (s4 t≈1.67–1.80) — reads as gaps.
3. **Swing body: 6** — Drop-in → tucked bottom → extended upswing with leg lag (s1 t≈4.74/5.14/5.54); styles vary. No FOV kick/radial blur at peak speed; momentum soft vs `swing-low-street-speed` t≈3.0.
4. **Flips and tricks: 5** — Held layout (s3 t≈0.9–1.1), inverted straddle (s3b t≈3.76), tuck (s3b t≈3.3), roof vault (s3 t≈2.36); easing ~260→450 °/s (s3b t 3.0–4.1). But ≈1 rotation/release vs owner S3's 3 in 2.8 s; splayed-leg layouts (s3 t≈1.0); facade backdrops not sky; hero ~0.09 of frame at s3 t≈3.16 (F9 wants 0.18–0.36).
5. **Air/transitions: 6** — Float poses evolve (s4 t≈1.5–3.5); catch with arm already reaching (t≈3.56). But releases fire low mid-arc (t≈1.5), not at the top; long floats play top-down against street.
6. **Camera: 6** — Stable, no roll, hero 0.18–0.35 of frame in s3b/s4. Tricks drift too far (s3 t≈3.16); chase sits higher/farther than `swing-canyon-chase`.

## A/B (decision → identity; all obvious from suit/aspect)

- swing-chain: **B** — faster, closer, real momentum. A=ours, B=ref.
- swing-presses: **A** — crouch→run→jump→fire reads better. A=ref, B=ours.
- release-air: **B** — top-of-arc release, sky silhouette. A=ours, B=ref.
- night-swing: **B** — dive speed/drama; A floaty. A=ours, B=ref.
- aerial-flips: **B** — tuck/open alternation, more rotations. B=owner clip, A=ours.
- progress-presses / progress-swing / progress-night: near-ties, slight edge **B** (cleaner strand at press f_020–021; natural landing f_072). Both ours; neither pixel-matches r09 — guess B=current.
- progress-flips: **B** — more rotations, open skyline. Both ours; guess B=current.

## Biggest gaps

1. **Flip density (axes 4+5):** ≈1 rotation/release (s3b t≈3.0–4.4); chain 2–3 with tuck↔open alternation on >1.5 s airtime (owner S3). Test: ≥2 rotations/release from rendered body axis, mean 300–500 °/s, peak 450–750 °/s, one open shape held ≥0.3 s at ≤150 °/s.
2. **Trick/float camera (axes 4+6):** level-or-below looking up, sky backdrop, hero 0.18–0.36 of frame (`trick-release-sky`, owner S6). Test: hero bbox-height fraction + share of trick frames with sky above the shoulders.
3. **Shot travel + speed feel (axes 1+3):** tip flight 0.06–0.20 s with slight wave (now 2 frames at 60 fps, s2 t≈2.36); FOV kick + radial blur at arc bottom (`swing-low-street-speed`). Tests: strand grows over ≥4 consecutive 60 fps frames; FOV/edge-motion rises at peak speed.

## Secondary

- Retract renders as dark dashes (s4 t≈1.67–1.80) — keep a solid fading line (W5).
- Open shapes splay ragdoll-like (s3 t≈1.0) — tighten pike/layout (A7).
- One press fires down toward street level (s2-like t≈32.9) — anchors stay above/ahead.
- Hero over-bright at night (s5 t≈5.6), muddying hand/strand contact.

## Verdict

**APPROACHES TARGET** — deployment and web read are close, swing structure real, but flips run at a third of the reference's rotational richness, camera undersells tricks/air, and speed cues are missing. Axes 4 (5) and 3/5/6 (6) are below the ≥8 bar.
