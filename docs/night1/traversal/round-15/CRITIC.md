# P3 round 15: blind critic (Opus 5.5)
*Homage fan game. Not an official Marvel, Sony or Insomniac game.*
Evidence: `_scratch/critic-P3-r15-work/`

## Scores
- **Swing arc and rhythm: 7.** T1/T2 pass: holds 0.53–1.37 s, gaps vary 1.68–2.62 s (a). T7 low point is still 0.6 m.
- **Camera: 5.** Pitch cap holds (f4 median 5.5° down). Fails: T8 median .246–.299 on all clips (f4 p90 .497), T9 f4 .31–.67, T10 a .18, T14 b/c/d 93–95°. At f4 5.62–5.82 s the camera flies through a tree and loses the hero.
- **Web read: 6.** T5 passes. Web is on for 53% of a (T3 limit 45%).
- **Moves: 6.** T22 passes (c 2.3–4.5 s). The wall-run is one pose sliding up (c 2.25–3.25 s). Throne 0.07 s.
- **Body: 6.** The tuck is now closed (f1 3.7–4.2 s). The twist washes out (f3 1.85–2.05 s).
- **Flips / air tricks: 7.** Rotation is eased. Pike held 0.38 s, swan 0.43 s. Each trick flows into the catch within 0.02 s. Glare is down from 93% to 25% of the hero box at luma ≥245, but the tuck is still white at f4 9.85 s. The tricks are canned: every backDouble has the same rate curve (a, f1, f4 ×2, f5), and the tuck spins for 1.18 s without changing shape.

## A/B (judged blind, before identity)
| Pair | Better | Why |
|---|---|---|
| multi-flip | A | Organic. B's hero turns white at 2.1–2.3 s. |
| pencil-throne | A | Held pencil, then throne. B flares at 2.0–2.4 s. |
| layout-catch | B | Steady camera. A yaws about 90° at 0.75–1.1 s and clips the hero at 2.5 s. |
| chain-flips | B | Keeps its weight. A has no hero at 2.375 s. |
| wallrun-flip | A | A real run. B slides one pose, then a symmetric Y. |
| progress-chain | B | No flare over the tuck (A: 1.0–1.5 s). |

Identity guessed afterwards: the reference won 5 of 5. The newer build (B) beats the older one.

## Biggest gap
The flip camera orbits freely. It overfills the frame, pushes the hero off centre, flies through trees and finds the sun.

**Instruction:** at release, pick one side-on yaw that is clear of trees and at least 100° from the sun. Hold it within ±30° for the whole trick. Set the distance so hero height is .15–.38 of frame and hero x is .44–.56.

**Test (f4, while flip_t ≥ 0 plus 0.5 s):**
- hero in frame on every frame;
- hero height p90 ≤ .38;
- hero x p5–p95 inside .44–.56;
- no frame with more than 5% of hero pixels at luma ≥245.

## Secondary
1. Vary trick rate and holds ±15% with release speed, and make the limbs asymmetric.
2. Split the tuck (tuck, open, tuck). Hold the kickout and throne ≥0.3 s.
3. Replace the single wall-run pose with a stride cycle.
4. T8 median ≤.23; T14 100–110° on b/c/d.

**Brand:** the chest emblem copies the real game's (P2). P4 should check the faded wall sign in c (3–5 s).

## Verdict: FAILS TARGET
The lowest axis is Camera at 5.
