# P3 round 20: blind critic (Opus 5.5)
*Homage fan game. Not an official Marvel, Sony or Insomniac game.* Evidence: `_scratch/critic-P3-r20-work/`

## Scores (r18 merged in brackets)
- **Swing: 7 [7].** T1 holds 0.88–1.37 s (a). T7 fails: apex 14–24 m, never the roofline. s1 holds 2.18 s (T1).
- **Camera: 6 [6].**
  - Fixed: the perch and the blackouts (f4 luma ≥57).
  - x2 3.3–3.7 s: distance 2.5 m, hero at cx .17, yaw −35→+32° in 0.45 s.
  - Leaf cards cover the hero (f4 3.5 s), yet occl reads 0 (T19).
- **Web: 6 [6].** Web is on 55% of a (T3).
- **Moves: 6 [6].**
  - Upright vertical run, camera +29° (T22 passes, c 2.65–4.15 s).
  - Mid-facade hop at c 3.55 s.
  - The side-run is a plank with the legs together (w1 2.9–3.53 s).
- **Body: 6 [6].** At ≥42 m/s the body aligns with velocity (4–13°), but it is one repeated pose (a 4.25, 10.25 and 14.0 s).
- **Flips: 7 [7].** Lit, and the tuck reads. The arcs dip into the canopy.

No axis is below r18.

## Owner bugs
1. **Swing always available: PASS.** RMB 1.750 s → rope at 1.767 s (x1). Side-run RMB 3.20 s → swing at 3.20 s (x2).
2. **Zip from side-run: PASS.** E at 3.50 s → perched at 5.08 s (w2). But the side-run lasted 0.31 s.
3. **Wall-run animation: FAIL.** See Moves.
4. **Air at speed: PASS.**
5. **Perch occlusion: PASS.**
   - The full body is visible at c 9.0–10.3 s, r1 7.6 s and w1 5.25 s.
   - w2 is too far: bbox .079.
6. **Mouse look: PASS.**
   - m1 yaw is 36° off a at 2.75 s, and the frames differ.
   - The input is injected. Sensitivity disagrees with the log (0.0075 against 0.12 °/px).

## A/B (judged blind, before identity)
| Pair | Better | Why |
|---|---|---|
| wallrun | B | Alternating sprint. A planks. |
| wallrun-flip | B | Stride and vault. A is a stiff climb. |
| swing-chain | B | Street-to-roof altitude. A is one low arc. |
| multi-flip | A | Real fall. B sinks into leaves. |
| chain-flips | B | Tower arcs. A skims the canopy. |
| progress-wallrun | A | Upright. B frog-climbs. |

Identity, guessed afterwards: the reference won 5 of 5. In progress-wallrun, A is r20, so r20 improved.

## Biggest gap
**Instruction:** make wallRunSide a real stride.
- Feet alternate contacts every ≤0.18 s.
- Peak foot gap ≥0.35 m in every cycle.
- Torso within 30° of the wall's up axis (no plank).
- Run ≥0.6 s before any input.
- No limb more than 0.5 m off the wall mid-facade.

**Test:**
- w1 2.9–3.6 s at 8 fps: legs apart in ≥3 of 6 frames.
- c 3.4–3.7 s: limbs within 0.3 m of the wall.

## Secondary
1. **Camera after a cancel:** yaw ≤90°/s, distance ≥3.5 m, cx .44–.56 (x2).
2. **Altitude:** T7 roofline every 4 s. Park arcs ≥3 m above the canopy. occl counts leaves.
3. **Web and hold:** T3 ≤45% (a). s1 hold ≤1.6 s.
4. **Light and brand:**
   - The test facade's mean luma is 12–25 (w1, w2, x2 2–4 s), but the checker says 0 dark frames.
   - Brand: "POP TH… GUMM" billboard (a 12.25 s, P4).

## Verdict: FAILS TARGET
The lowest axes are at 6. No axis is below r18.
