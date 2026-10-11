# Critic, final piece SW, round 11 — blind review (pixels/motion only)

Clips: `round-11/{s1..s5}.mp4` at 25/10 fps, cropped pixel counts. Times = clip seconds.

## Per-axis scores

**1. Web deployment — 5.** Correct reach and origin at fire (s2 t=2.40); hand matches anchor side (s3 t=4.08). But: (a) strand fleck→full length in one 25 fps frame (t=2.36→2.40; 3-before none/none/fleck, 3-after full/full/full), under W3's 0.06 s min; (b) strand hand-end floats off the palm ~0.3 s post-attach: 83 px at t=2.56, 65 px at t=2.72 (~0.4 m; W1 allows 8 cm). Release retracts ~0.08 s (s4 t=4.64–4.80), under W8's 0.15 s.

**2. Web read — 8.** ~3 px at 1080p (s2 t=2.72 crop), stable, tapered, no glow/flicker; readable vs facades (s1), sky (s3b t=12.0), night (s5).

**3. Swing body — 6.** Variety: horizontal drive (s1 t=0.95), tucked bottom → seated upswing (s1 t=2.0–2.8), upright hang (s3 t=4.4), inverted star (s2 t=14.9). But the superman pose holds flat for long stretches (s1 t=8.0; s4 t=2.0–4.5); leg lag weak vs `swing-canyon-chase`.

**4. Flips — 5.** Eased shapes at right rates: s3 t=3.16–3.56 straddle→tuck→spread ~400–500°/s; clean upright catch t=4.08. Vs owner clip: no held open shape ≥0.3 s at ≤150°/s (s3 t=3.16–3.8, s3b t=7.2–7.8, 11.6–12.4 rotate continuously; owner holds pencil 0.64 s, throne 0.48 s); no 2–3-rotation long release; facades behind tricks, not sky.

**5. Air/transitions — 6.** Chains flow (s3 t=3.8→4.08; s4 t=4.6 → catch t=6.8); float poses evolve (t=5.2–8.4) but a spread fall sits ~1.0 s near-held (t=4.7–5.8, borderline A4). No pops at viewed catches.

**6. Camera — 6.** No roll through flips, smooth trailing, hero 0.19–0.39 frame height in most tricks. Losses: hero out the right edge ~0.6 s (s3b t=7.4–7.8); hero 0.14 of height, top-down (s3 t=20.0).

## A/B pack (decision → identity)

- swing-chain: **A** — faster canyon pendulum; obvious: reference.
- swing-presses: **A** — crisp street launch; obvious: reference.
- release-air: **A** — inverted trick against sky; obvious: reference.
- night-swing: **B** — swing-to-car landing; obvious: reference (HUD).
- aerial-flips: **A** — multi-rotation, held shapes; obvious: real-game recording.
- progress-flips: **B** — hero ~1.5–2x larger, readable shapes; not obvious; B matches round-11 s3 ⇒ B = current, A = previous.
- progress-presses/-swing/-night: **ties** — pose-identical at matched times; both ours.

## Biggest gaps (by score impact)

1. **Weld strand to palm; show shot travel (W1+W3).** s2 t=2.4–2.8: pops full-length ≤0.04 s, floats 65–83 px off the glove ~0.3 s. Target: tip travels visibly 0.06–0.20 s (ref `swing-start-from-street`), tail ≤8 cm from palm. Test: every web-on 25 fps frame, strand start ≤15 px from glove; tip advances ≥4 consecutive 60 fps frames per press.
2. **Hold one open shape per trick (F4/F1).** s3/s3b rotate continuously; no ≥0.3 s hold, no 2–3-rotation release. Target: one pencil/throne/layout ≥0.35 s at ≤150°/s before the catch (owner 5.00–5.64, 23.00–23.48). Test: ≥9 identical-shape 25 fps frames per trick.
3. **Keep the hero framed during tricks (F9).** s3b t=7.4–7.8 off-frame right; s3 t=20.0 at 0.14 height, top-down. Target: bbox center in central 60 %, height 0.18–0.36, sky behind. Test: bounds on 100 % of trick frames.

## Secondary issues

- W8: retraction ~0.08 s (s4 t=4.64–4.80) — add 2–3 slack frames.
- A4: ~1.0 s near-held spread fall (s4 t=4.7–5.8).
- s1 t=8.0: strand near-end reads at the waist for one frame (maybe mid-release; unverified).
- Trick backgrounds mostly facades, not sky (F9 prefers sky).

## Verdict

**APPROACHES TARGET.** Axes 1/3/4/5/6 at 5–6: vocabulary right, nothing broken, but measured attach behavior, missing held shapes and trick framing stay clearly below the reference. Web read (8) alone holds up side by side.
