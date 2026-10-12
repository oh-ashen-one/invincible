# P3 round 14: blind critic (Opus 5.5)
*Homage fan game. Not an official Marvel, Sony or Insomniac game.*
Evidence: `_scratch/critic-P3-r14-work/`

## Scores
- **Swing arc and rhythm: 6.** T1 and T2 pass. 5 of 7 gaps in a are exactly 0.80 s. T7 low point 0.6 m (a 10–14 s).
- **Camera: 5.**
  - Fixed: post-attach pitch 5.5–11.5° down; side-on trick orbit.
  - Fail: T8 f4 median .27 / p90 .43; kickouts reach .58.
  - Fail: T10 spread .18–.19; T11 f4 median 2.6° down, 20.5° up.
  - Fail: T14 93–95° in b/c/d.
- **Web read: 6.** T5 passes. T3: a fails at 53%.
- **Moves: 7.** T22 passes (55.8° up). Throne 0.14 s (c 4.68 s); wall-run uses sprint clip.
- **Body: 6.** Arms now asymmetric (f4 4.65 s). Open tuck (1.95 s); twist is an arms-down plank (6.95 s).
- **Flips / air tricks: 7.**
  - Now good: rotation eases 308→766→410→73°/s (f4 1.42–2.67 s). Holds 0.37–0.55 s; four tricks chain into catches.
  - Fail: at f4 9.75–10.05 s, 93–97% of the hero box is clipped white. Flare ghosts cover the tuck at 1.75–2.05 s.

## A/B (judged blind, before identity)
| Pair | Better | Why |
|---|---|---|
| multi-flip | A | Continuous. B whips at 2.27 s (4.0× median frame difference). |
| pencil-throne | A | Throne held about 0.75 s. B's hero flares white at 1.5 s. |
| layout-catch | A | Readable shapes. B's hero is about 0.1 of the frame. |
| chain-flips | B | Clearer shapes. A has more natural weight. |
| wallrun-flip | A | Organic. B is a symmetric inverted Y. |
| progress-trick | B | Side-on tuck. A tilts about 30°. Both lose the hero at 2.375 s. |

Identity guessed afterwards: ours won 2 of 5 reference pairs.

## Biggest gap
The trick camera climbs to 20–27° up and looks into the sun, which flares out the flips.

**Instruction:** cap the trick camera at 8° up. Orbit to the ±90° side that puts the sun behind the camera (at least 100° between sun and view).

**Test (f4):** `pcm_pitch` never above 10° up; no frame with >5% hero-box pixels at luma ≥245; T11 median 4–12° down.

## Secondary
1. Pull trick framing back to T8 (median ≤.23, p90 ≤.38).
2. Hold throne and kickout ≥0.3 s.
3. Close the tuck; wrap arms during the twist.
4. Vary the gaps by ±25%. Fix T3 on a, T10 and T14 (b/c/d).

Brand: chest emblem copies the real game's (P2).

## Verdict: FAILS TARGET
The lowest axis is Camera at 5.
