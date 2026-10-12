# P3 round 11: blind critic (Opus 5.5)
*Homage fan game. Not an official Marvel, Sony or Insomniac game.*

Evidence: `_scratch/critic-P3-r11-work/`.

## Scores
- **Swing arc and rhythm: 6.** In f4, T1 holds are 1.02–1.57 s and T7 height runs 7.5→49 m. T2 fails: attach gaps are 4.07 s and 3.62 s (limit 3.3).
- **Camera: 6.**
  - Pass: T9 (.47–.53), T12, T13, T14 (103°), T17 (.39/.54).
  - Fail: T8 (median .237), T10 (spread .175), T11 (p5 4.1° down), T18 (p50 .75).
- **Web read: 7.** T3 is 41%. At f4 5.0 s the rope is dark, 2–3 px wide, 22° from vertical, and runs from the hand to the edge.
- **Moves: 6.** In c, the wall-run camera looks up 44–56° and the top-out flip has a 0.99 sky ring. The release tricks fail T23. At b 6.5 s the hero goes from 52 m/s to a stop with no settle.
- **Body: 6.** The swan and pencil shapes are clean. At f4 12.5 s the legs wash out (saturation 8–21/255).
- **Flips/air tricks: 6.**
  - f2 is good: pencil then swan held 1.08 s, the swan at 81°/s.
  - backDouble (f1/f4) is not: it snaps at 640°/s through four shapes that last only 0.15–0.36 s.
  - The f4 twist (8.1–8.4 s) shows the hero at .08 of frame height against brick.

## A/B (judged blind)
| Pair | Better | Why |
|---|---|---|
| multi-flip | A | Flowing rotation. B steps between poses. |
| pencil-throne | A | Throne held 0.6 s against sky. |
| layout-catch | B | Continuous twist, tuck and catch in 1.9 s. |
| chain-flips | B | Flips run into the next web above the roofs. |
| wallrun-flip | B | Clear flip against blue sky. |
| progress-trick | B | Inverted shape, and the swing continues. |

Ours lost 4 of 5 reference pairs.

## Biggest gap
Release tricks happen low in the canyon, with a facade or billboard behind the hero. Sky share of a 40 px ring around the hero, median over trick frames:

| Clip | Median | Trick frames at least 50% sky |
|---|---|---|
| f1 | .16 | 3% |
| f2 | .26 | 11% |
| f3 | .28 | 6% |
| f4 | .05 | 15% |

**Instruction:** start every release trick from an apex at least 3 m above the tallest roof within 30 m, and bias the camera so the sky is behind the hero.

**Test:** at 10 fps, at least 70% of trick frames have a ring that is at least 50% sky, with the hero at least .15 of frame height.

## Secondary issues
1. backDouble: hold each shape for at least 0.5 s, use at most 2 shapes, and blend between them over at least 0.15 s.
2. Green lens ghosts cross the hero at f4 8.1–8.7 s and b 6.7 s (P4).
3. T2, T8, T10, T11 and T18 are out of band.

**Brands:** no exclusion-list names seen.

## Verdict: FAILS TARGET
The lowest axis is 6.
