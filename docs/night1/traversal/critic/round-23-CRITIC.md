# P3 round 23: blind critic (Opus 5.5)
*Homage fan game. Not an official Marvel, Sony or Insomniac game.* Evidence: `_scratch/critic-P3-r23-work/`

## Scores (r22 in brackets)
- **Swing: 7 [7].** a, f1, f4, m1, x1, s1 match r22 (frame diff ≤3.8/255). T7 fails: the largest 4 s drop is 18 m, hfloor 5–23 m.
- **Camera: 6 [6].** w2 hero in frame .84→1.00. **c regressed:** at 7.73–8.48 s the orbit hits a wall. Yaw goes −88°→−46°→−99°, cam 1.6 m, hero out of frame 45 frames, occl 1.0 at 7.78 s.
- **Web: 6 [6].** w2 zip ends on a perch (5.75 s, z 96; r22 232 m). After the rope (4.00–4.48 s), 1.0 s with no rope. T3: rope on screen 55% in a (target ≤45%).
- **Moves: 6 [6].** Wall-run → zip → perch completes in w1, w2; T22 passes.
- **Body: 6 [6].** Vertical-run legs now cycle (w2 1.0–2.8 s, bbox_w ≥25% change in 4/4 windows). But the knees splay: knee_gap_lat median .49 m (r22 .16). Frog shimmy, not a sprint.
- **Flips: 7 [7].** Unchanged.

## Owner bugs
1. **Swing always: PASS.** x1 rope 1.75 s, x2 swing 3.20 s.
2. **Zip from side-run: PASS.** zipFire 4.00 s → perch 5.75 s.
3. **Wall-run animation: PASS.** Legs apart in 13/15 frames at 8 fps. The pose is wrong (Body).
4. **Air at speed: PASS.** Unchanged.
5. **Perch occlusion: PASS.** occl 0 on the c, w1 and w2 perches.
6. **Mouse look: PASS.** m1 unchanged.

## A/B (blind)
| Pair | Better | Why |
|---|---|---|
| wallrun-vertical-1 | B | Leaning sprint. A frog-climbs a pole. |
| wallrun-vertical-2 | A | Ornate facade, ledge vault. B crawls brick. |
| wallrun-side | B | Lean, ledge flip. A is upright. |
| swing-chain | B | Roofline drops. A is low, gray-box plaza at 6.0–6.75 s. |
| multi-flip | B | Real fall past a facade. A stays at canopy height. |
| progress-vertical | B | Legs cycle. A slides with legs together. |

Guess: the reference won 5/5; progress B is r23.

## Biggest gap
**Instruction:** make the swing chain use altitude and less rope time (T7, T3).
**Test (a_swing_chain):**
- Every 4 s window has a release from hfloor ≥30 m down to a low point of 3–13 m.
- That drop is ≥20 m.
- web_on is 25–45% of the time.

## Secondary
1. **c camera, 7.7–8.5 s:** hero_in_frame=1, occl ≤.02, cam ≥3 m, no yaw reversal.
2. **Vertical-run pose:** knee_gap_lat median ≤.25 m. Knees drive forward, arms alternate.
3. **Zip rope:** draw it until zipCatch. Superman pose holds 4.50–5.00 s with no rope.
4. **Framing and P4:**
   - Wall-run bbox .40–.47 and cam 3.4 m (T8, T15).
   - Source-check the billboards: "…ULSE/…ERY BEAT", "BROA…" (w2 4.62 s), mural (c 4.5 s). No real brand recognised.

## Verdict: FAILS TARGET
Lowest axes are 6. None is below r22, so merging is allowed. Camera drops to 5 if the c snap is still there next round.
