# P3 round 13: blind critic (Opus 5.5)
*Homage fan game. Not an official Marvel, Sony or Insomniac game.*
Evidence: `_scratch/critic-P3-r13-work/`

## Scores
- **Swing arc and rhythm: 6.** T1, T2 and T4 pass. The cadence is metronomic: every chain alternates 0.80 s and 1.48 s gaps.
- **Camera: 5.**
  - Fixed: no hard cut (largest frame difference 2.3× the median).
  - Fail: T11 (pitch p5 51–56° up; still 53° up after the attach at f4 8.2 s), T8 (f4 p90 .42) and T10 (spread .12–.19).
  - Camera in foliage at f4 8.75–9.0 s.
- **Web read: 6.** T5 passes. T3 fails: the rope is on for 53–56% (a, f1, f2, f5).
- **Moves: 7.** T22 passes (c 2.23–3.85 s, 13→56° up). The throne still lasts 0.09 s (c 4.68–4.77 s). The wall-run uses a floor-sprint clip.
- **Body: 6.** The hero is no longer black. The swan and layout shapes are a symmetric inverted T with arms at 90°, which looks like a mannequin (f4 7.4–7.8 and 11.5 s).
- **Flips / air tricks: 6.**
  - Now good: the shape starts 0.03 s after release and the web attaches at the flip's end (f4 1.50–2.95 s).
  - Fail: the tuck spins at a constant 678°/s with no ease, and backDouble reads as a spinning ball (f4 1.9–2.4 s). b uses 5 shapes in 1.7 s.

## A/B (judged blind, before identity)
| Pair | Better | Why |
|---|---|---|
| multi-flip | A | Organic tumbling. B loses the hero at 2.375 s. |
| pencil-throne | A | Close. B's inverted T is stiff. |
| layout-catch | B | One tumble into the web. A holds a rigid T. |
| chain-flips | B | Flows. A's flips are clearer but stiff. |
| wallrun-flip | A | Natural. B lands after a camera swing. |
| progress-trick | A | Web within 2.5 s. B is black and web-less for over 5 s. |

Guessed identity afterwards: ours lost all 5 reference pairs.

## Biggest gap
The flip camera looks up from under the hero, so the rotation doesn't read and the camera stays tilted up into the next swing.

**Instruction:** during a trick, orbit the camera side-on to the somersault axis (at least 60° from it) and cap the upward pitch at 30°. Within 0.5 s of attach, return the pitch to 4–12° down.

**Test on f4:**
- Pitch is never above 30° up.
- Median pitch 0.5–1.0 s after each attach is 4–12° down.
- The tuck's head-to-hip axis turns at least 300° on screen.

## Secondary
1. Ease the rotation (ends at least 30% slower than mid-flip). Hold each shape, including throne, at least 0.3 s.
2. Make the 90° arm shapes asymmetric.
3. Meet T8 (median at most .23), T10 (spread at least .20) and T3 (rope at most 45%).
4. Vary rope and gap lengths by at least ±25%.

Brand: the chest emblem copies the real game's (P2). The signs are invented.

## Verdict: FAILS TARGET
The lowest axis is Camera at 5.
