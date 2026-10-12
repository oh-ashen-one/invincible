# P3 round 22: blind critic (Opus 5.5)
*Homage fan game. Not an official Marvel, Sony or Insomniac game.* Evidence: `_scratch/critic-P3-r22-work/`

## Scores (r21 merged in brackets)
- **Swing: 7 [7].** Trajectory identical to r21. T1 0.88–1.38 s. T7 fails: z 6–24 m.
- **Camera: 6 [6].** x2 3.38 s: cx .19, 2.48 m. w2 zip too tight: bbox .46–.60 (T8, T15).
- **Web: 6 [6].** Rope on screen 55% of a (T3 ≤45%). w2 zip: no rope 5.25–6.97 s at 60 m/s.
- **Moves: 6 [6].** Side-run fixed: box tall 69/69, legs apart 7/10 at 12 fps (w2 3.10–3.85 s), facade luma 59–107. The w2 vertical run (1.0–2.8 s) freezes.
- **Body: 6 [6].** Side-run stride alternates. The vertical run keeps legs together: bbox_w .082–.088 for 1.5 s. Sun bloom greys his legs (1.6 s).
- **Flips: 7 [7].** f1 and f4 identical to r21.

No axis is below r21.

## Owner bugs
1. **Swing always: PASS.** x1 flip 1.50 s → rope 1.75 s. x2 side-run 2.88 s → swing 3.25 s.
2. **Zip from side-run: PASS.** w2 zipFire 4.00 s. It never lands (z 232 m at 6.97 s).
3. **Wall-run animation: FAIL.** Side run passes. Vertical run slides frozen: foot_sep .12→.47 m, no alternation.
4. **Air at speed: PASS.** Same as r21.
5. **Perch occlusion: PASS.** hero_occl 0 in the c and w2_r21route perches.
6. **Mouse look: PASS.** 3.0 s yaw: m1 −45°, a −81°.

## A/B (judged blind, before identity)
| Pair | Better | Why |
|---|---|---|
| wallrun-side-1 | A | Lit facade, vault into flip. B is dark, ends hanging. |
| wallrun-side-2 | B | As above. A's stride looks pasted on. |
| wallrun-vertical | B | Sprint, camera up. A crouch-climbs (1.12 s). |
| swing-chain | B | Roof altitude. A is low, past a gray-box plaza (6.0 s). |
| multi-flip | A | Real fall. B skims the canopy. |
| chain-flips | A | Tower arcs. B is the canopy. |
| progress-wallrun | B | Upright stride. A planks (0.75–1.12 s). |

Identity guess: the reference won 6/6; progress B is r22.

## Biggest gap
**Instruction:** make the vertical wall-run cycle its legs.
**Test (w2, 1.0–2.8 s):**
- foot_sep_run_m crosses below 0.15 m and above 0.35 m at least 4 times per second.
- bbox_w changes by ≥25% within every 0.4 s.
- At 12 fps, the legs are visibly apart in ≥6 of 10 frames.

## Secondary
1. **Zip:** draw the rope for the whole zip, or cap it at 1.2 s, and end on a perch. Now: arms-up hold 2.7 s, no rope (T4, T5).
2. **Camera:** x2 yaw −28°→+26° in 0.25 s after the cancel; keep cx .44–.56, distance ≥3.5 m. Wall-run bbox median .40–.43 (T15: 4–7 m).
3. **Altitude:** T7 roofline drop every 4 s. f4 still skims the canopy.
4. **P4:** source-check the face mural (c 4.5 s). No real brand found.

## Verdict: FAILS TARGET
Lowest axes are 6. None is below r21, so merging is allowed.
