# P3 round 19: blind critic (Opus 5.5)
*Homage fan game. Not an official Marvel, Sony or Insomniac game.* Evidence: `_scratch/critic-P3-r19-work/`

## Scores (r18 in brackets)
- **Swing: 6 [7].** T1 holds 0.97–1.38 s and T2 pass. T7 fails: apex 16–21 m, never at roofline. The bottom plank is identical at 31 and 55 m/s (a 1.0 / 15.25 s).
- **Camera: 4 [6].**
  - f4 1.75–6.5 s: 15 of 21 frames have luma <15. At 5.25 s the max pixel is 1.
  - After a zip, a parapet hides the hero: c 9.0–10.25 s shows only the shoulders, about 40 px. Telemetry wrongly reports bbox .25 and occl 0.
- **Web: 6 [6].** Web on for 55% of a (T3 limit 45%).
- **Moves: 4 [6].**
  - The wall-run is a splayed-knee frog scramble: w/h 0.73, pitch −24…−33°.
  - The side-run lies flat: w/h 1.30, pitch −68° (w2).
  - T22 passes.
- **Body: 5 [6].** fallCalm stands upright at 43–51 m/s (a 4.25 and 10.25 s). On a zip the hero hangs limp (w1 3.8–4.4 s).
- **Flips: 7 [7].** Instances now vary: 1.25–1.55 s, peak 791–924°/s. The tuck passes: wrist .04 m, knee ≤.20 m, held 0.87 s. But most f1/f4 flips play in black frames.

## Owner bugs
1. **Swing always available: FAIL.** Swing restarts after a release during pause (5 of 5, in 0.02 s). But a held RMB during a trick or wall-run waits 0.47–1.08 s (f4 11.02 s; probe s1 3.13 s).
2. **Zip: FAIL (partial).**
   - Passes from the roof (c 8.5 s, r1 6.2 s) and from a vertical wall-run (w1 3.6 s → perch).
   - Fails from a side-run: w2 3.5 s ends clinging mid-facade at 61 m.
3. **Wall-run animation: FAIL.** See Moves.
4. **Air at speed: FAIL.** The pose does not change with speed.
5. **Mouse look: UNPROVEN, so FAIL.** The input logs read "mouse 0 px over 0 frames".
- **Mid-air landing: UNPROVEN.** The r1 landing (9.37 s) falls in a black frame. The c roof run is grounded.

## A/B (judged blind, before identity)
| Pair | Better | Why |
|---|---|---|
| wallrun | A | Upright alternating sprint. B scrambles. |
| wallrun-flip | A | Horizontal stride. B is a frog climb. |
| swing-chain | A | The pose changes and there is speed blur. B is one plank. |
| multi-flip | A | B goes black. |
| chain-flips | A | B goes black. |
| progress-wallrun | B | One top flip. A has head-down mid-facade flips. |

Identity, guessed afterwards: A is the reference in five pairs. In progress-wallrun, A matches c 2.25–5.75 s, so r19 regressed.

## Biggest gap
**Instruction:** replace the wall-run with an upright sprint.
- Torso within ±15° of the wall's up axis.
- Side-run: body within 20° of the run direction, head leading.
- Silhouette w/h ≤0.55, knee gap ≤0.35 m.
- Alternate hand/foot contacts every ≤0.18 s.
- No mid-facade flips.
- E from a side-run must end on a perch.

**Test:** c 2.75–3.25 s, w1 2.4–3.6 s, w2 2.5–3.5 s.

## Secondary
1. **Blackouts:** no frame below mean luma 25 while the hero is on screen. Route away from unlit courtyards and log it with P4.
2. **Perch camera:** the parapet must not occlude the hero. Fix bbox/occl against pixels.
3. **Swing input:** RMB cancels a trick or wall-run into a swing within ≤0.1 s.
4. **Missing tests and brand check:**
   - Inject mouse look.
   - Show a lit landing.
   - Brand check (P4): "POP TH… GUM" billboard (a 12.0 s).

## Verdict: FAILS TARGET
The lowest axes are at 4.
