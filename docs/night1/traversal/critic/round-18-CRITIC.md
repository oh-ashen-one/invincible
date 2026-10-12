# P3 round 18: blind critic (Opus 5.5)
*Homage fan game. Not an official Marvel, Sony or Insomniac game.* Evidence: `_scratch/critic-P3-r18-work/`

## Scores (r15 merged in brackets)
- **Swing: 7 [7].** T1 passes: holds 0.88–1.38 s (a). T7 fails: the arc bottoms inside the tree canopy (f4 3.5–3.9 s).
- **Camera: 6 [5].** TC-A/B/D/E/F/H pass: yaw offset 31–50°, range ≤6°. Fails:
  - TC-C: f3 p90 .370.
  - TC-G: canopy hides his legs at f4 3.75 s, but hero_occl reads 0.
  - So the camera stays below 7 (TRICK_CAMERA_SPEC L51).
- **Web: 6 [6].** Web on for 53% of a (T3 limit 45%).
- **Moves: 6 [6].** The wall-run is a crawl, not a sprint (c 2.3–3.6 s).
- **Body: 6 [6].** Kickouts no longer freeze. The tuck is loose: knees apart, arms out (f1 2.0–2.2 s).
- **Flips: 7 [7].** The limbs are alive (0 slow 0.1 s samples), and layout, straddle and pike read. But every program is a replay: flip_rate curves are identical to the degree across instances in f1, f2, f3 and f5. Durations are fixed at 1.57, 1.40 and 1.48 s.

## A/B (judged blind, before identity)
| Pair | Better | Why |
|---|---|---|
| multi-flip | B | Flows near the facades. A is small keyed poses. |
| pencil-throne | B | A's tuck flashes 0.13 s, then the catch sinks into trees (2.4 s). |
| layout-catch | A | Crisp layout and straddle. B is a backlit blob. |
| chain-flips | B | A dips into canopy (2.5–3.25 s). |
| street-multi-flip | B | Same as multi-flip. |
| wallrun-flip | B | Stride. A crawls. |
| progress-chain | B | Arms unwind. A holds a split (4.03–4.37 s). |

Identity, guessed afterwards: the reference won 5 of 6.

## Biggest gap
Each trick is a canned playback with a loose tuck.

**Instruction:**
- Scale each program's duration and peak rate ±10–20% from release speed and apex height.
- Vary the arm timing per instance.
- Tuck: wrists ≤0.15 m from the shins, knees ≤0.25 m apart, held ≥0.25 s. Log these in telemetry.

**Test:**
- Same-type tricks in a clip differ by ≥40°/s in at least one 0.1 s rate sample.
- The tuck numbers pass on f1/f5.

## Secondary
1. Swing low point and catch: clear of foliage (T7). hero_occl must count leaves.
2. Web on ≤45% of a.
3. Wall-run: sprint stride. f3 TC-C p90 ≤.36.
4. Brand / world:
   - Chest emblem (P2).
   - "…ON BURGER" ad with a face (c 3.0 s, P4).
   - Roof props floating in the sky (f4 10.25–11.5 s, P4).

## Verdict: FAILS TARGET
The lowest axes are at 6.
