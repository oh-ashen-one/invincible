# Blind critique — SW round 12 (2026-10-11)

Measured from extracted frames (60 fps hero crops at presses/releases, 25 fps labeled flip strips).

## Scores

1. **Web deployment — 6.** Presses fire from the palm, arm reaches to the anchor, tip travel ~0.15 s (s4 t=0.42–0.60; s2 t=16.07–16.20); no pop-in, wrong hand, or through-wall seen. Release too fast: s4 t=15.75–15.817, strand 520→303→235→30→0 px in 4 frames (W8 wants 0.15–0.40 s).
2. **Web read — 4.** Daylight strand is beaded/dashed with real gaps (s4 t=15.63–15.75 vs sky; s3 t=14.2 across open sky; s4 c_00024/27 vs facade) and flickers dark↔white (s4 c_00012 vs c_00013). Night is solid white ~3 px, good (s5 t=3.5). Reference (canyon_010): clean solid line.
3. **Swing body — 6.** Phases, leg lag, variety read (s1). Dead stalls: s2 t≈12.2–15.2 vertical hang ~3 s; s3 t≈13.5–14.1 near-static float. No FOV kick; blur weaker than canyon-chase.
4. **Flips — 5.** Real shapes with easing (s3 t=1.0–2.4: ~560°/s tucked vs ~220°/s open; s3b 26.6–29.5 tuck/pike/layout). But 1–1.5 rotations per release vs owner 2–3; best held open shape ~0.16 s (s3b 28.52–28.68) vs owner pencil 0.36–0.64 s, throne 0.48 s; framed against facades, not sky.
5. **Air/transitions — 5.** s4 float→catch (15.8→17.2) smooth, no whip. But body opens ~0.3 s after release (target 0.1 s); hero lies flat on the wall post-wall-run (s3 22.8–23.4).
6. **Camera — 5.** No roll with the body; hero usually 0.2–0.35 h. But hero fully out of frame ~0.3 s (s3b t≈11.62–11.94; t=11.7/11.8 show only city), h 0.49→gone→0.14 in 0.6 s; tricks rarely framed low against sky.

## A/B (decided before identity)

- swing-chain: **B** (speed, blur, framing). Obvious: B = reference.
- swing-presses: **B** (crouch-zip, low avenue swing). Obvious: B = reference.
- aerial-flips: **A** (held layouts/pencil/straddle vs sky). Obvious: A = owner clip.
- release-air: **A** (hang time + sky trick). Obvious: A = reference.
- night-swing: **A** (richer night light). Obvious: A = reference.
- progress-swing: **A**, marginal (strand readable vs near-invisible t=9.3–11.5). Guess: B = r12 (pixel diff to s1 at t=10.0: 28.8 vs 41.0).
- progress-presses: **A**, marginal (better shot-travel curl t≈2.1–2.3). Guess: A = r12 (duration + pixels).
- progress-flips: **A**, marginal (clearer held shapes vs sky). Guess: B = r12 (24.0 s ≈ s3's 23.98 s).
- progress-night: **tie**, hair to B (brighter strand t=11.2). Guess: A = r12 (pixel diff at t=10.6: 35.9 vs 43.9).

## Biggest gaps (score impact order)

1. **Strand renderer** (axes 1+2): continuous solid 2–3 px line, constant contrast, no flicker (fails s4 t=15.6–15.8, s3 t=14.2; ref canyon_010). Test: zero gaps along 200 px vs sky and facade; brightness stable over 3 consecutive frames.
2. **Trick camera + density** (axes 4+6): hero in frame 100% of trick frames (fails s3b 11.62–11.94); camera level/below with sky behind; 2–3 rotations + one ≥0.3 s held open shape per long release (owner S6). Test: bbox-in-frame, flip_check rotation/hold counts, sky behind hero ≥60% of trick frames.
3. **Release timing** (axes 1+5): retract over 0.15–0.40 s with slack (now 4 frames: 520/303/235/30/0 px); body opens ≤0.1 s after release (now ~0.3 s). Test: decay spans 9–24 frames at 60 fps; silhouette change >0.15 within 6 frames.

## Secondary

- Near-horizontal strand to a low/behind anchor mid-corner (progress-night both, t≈10.6).
- Hero lies flat on the wall after the wall-run (s3 t=22.8–23.4).
- ~3 s vertical hang kills momentum (s2 t≈12.2–15.2).
- Camera distance swings: 0.49 h → out of frame → 0.14 h in 0.6 s (s3b 11.5–12.1).

## Verdict

**APPROACHES TARGET** — presses answer, catches smooth, night webs good; dashed/flickering daylight strand, thin trick density vs the owner clip, and the camera losing the hero hold every axis at 4–6.
