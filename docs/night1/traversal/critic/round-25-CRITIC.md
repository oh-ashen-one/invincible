# P3 round 25: blind critic (Opus 5.5)
*Homage fan game. Not an official Marvel, Sony or Insomniac game.* Evidence: `_scratch/critic-P3-r25-work/`.

All clips were re-captured. f1, m1, r1, s1, w2, x1 and x2 match r24 (frame diff ≤5.1/255). f4 is missing; p1 is new. Visual sheet: `sm/ALL.jpg`.

## Scores (r24 in brackets)
- **Swing: 7 [7].** T7 passes: lows 7.5–11.2 m every ≤3.5 s. T2 fails: gaps 3.37 and 3.38 s. T4 fails: a 12.4–13.1 s is a held skydive.
- **Camera: 6 [6].** The perch is fixed. Wall-run bbox p90 .44 at 3.4 m (T8/T15 fail). Pitch matches the vanishing points (±0.4°).
- **Web: 7 [6].** Check (a) passes. T3 is 42%. Angle p50 36°.
- **Moves: 6 [6].** T22 passes (29° up). The vertical run is the same frog pose in 4 of 4 frames.
- **Body: 6 [6].** knee_gap_lat .49 m (unchanged). Pawn run is upright.
- **Flips: 7 [7].** Unchanged.

## Checks
- **(a) PASS.** 63/65 web_on frames have ≥95% of samples at ≥25/255 against both bands.
  - Width median 2–4 px.
  - Dark glass passes (≥0.958 at 10.5–11.2 s, ≥0.966 at 0.9–1.1 s).
  - At 3.4 and 13.5 s the rope ends at an in-frame anchor.
  - Control line: 0.067.
- **(b) PASS.** Hero in frame 113/113 frames, but only 77–206 suit px at 8.80–8.82 s. Distance 4.14–6.0 m. Max pitch change 14.3° per 0.3 s.
- **(c) PASS.** 3.61 Hz.
- **(d) PASS.**
  - T7 holds; web_on 41.8%.
  - c 0–8.6 s is identical to r24.
  - Owner bugs 1–6 pass.

## A/B (blind)
| Pair | Better | Why |
|---|---|---|
| swing-chain-1 | A | Rooftops, traffic. B: empty fog canyon. |
| street-run | A | Lean, leaps. B: locked and upright. |
| multi-flip | B | Facade falls. A: canopy height. |
| wallrun-vertical | A | Sprint, camera looks up. B: frog pose. |
| wallrun-side | B | Lean, roof flip. |
| rooftop-perch | B | Skyline ledge. A: flat wall. |
| progress-perch | A | B whips top-down at 2.7 s. |
| progress-swing | B | Rope visible at 5 and 7 s. |

swing-chain-2: no image delivered. Guess: the reference won 6/6. Progress B and perch A are r25.

## Biggest gap
**Instruction:** make the vertical wall-run a sprint (w1, 0.95–3.58 s).
- knee_gap_lat ≤0.25 m.
- At 10 fps, limb pose differs at every 0.3 s.
- Camera ≥4 m, so bbox p90 ≤.38.

## Secondary
1. **Swing timing:** T2 gaps ≤3.3 s. T4: pose must change every 0.1 s at 12.4–13.1 s.
2. **Perch visibility:** ≥500 suit px at c 8.80–8.82 s.
3. **P4:** empty streets, fog wall, green ghost (B3.0).
4. **P2:** the back emblem copies the licensed suit.

## Verdict: FAILS TARGET
Lowest axis is 6. No axis is below r24, so merging is allowed.
