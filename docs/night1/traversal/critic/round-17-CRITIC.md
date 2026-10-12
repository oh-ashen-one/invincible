# P3 round 17: blind critic (Opus 5.5)
*Homage fan game. Not an official Marvel, Sony or Insomniac game.* Evidence: `_scratch/critic-P3-r17-work/`

## Scores
- **Swing: 7.** a: one hold of 1.87 s (T1 limit 1.6). Low point 0.6 m (T7).
- **Camera: 6.** Pass: TC-B (p95 ≤35°/s), D, E, F, H (sun ≥129°, hot suit ≤3.1%), I (sky 79%, was 2%), J, K.
  - TC-A: offset p5 20–29° (needs ≥30). Range >20° on 12 of 15 tricks.
  - TC-C: distance 4.1–4.4 m. h p90 .37–.38, and .46 at f5 3.9 s. p50 .29–.31 on f2/f3.
  - TC-G: foliage over his legs at a 12.3 s, but hero_occl reads 0.
- **Web: 6.** Web on for 53% of a (T3 limit 45%).
- **Moves: 6.** Wall-run is one sliding pose (c 2.25–3.25 s).
- **Body: 6.** Kickouts freeze (f1 2.7–2.8 s, f5 5.3–5.4 s).
- **Flips / air tricks: 6.** The tuck now opens with asymmetric arms (f1 1.6 s) and the corkscrew reads (f3 1.7–2.0 s). But f2, f3 and f4 share one inverted split.
  - The split is frozen for 0.3 s: limbs move <0.10 per 0.1 s, and the body turns at 87°/s (f2 1.9–2.2 s).
  - The tuck blurs to a ball (f3 2.6 s). The pike is a lump (f2 1.6 s).

## A/B (judged blind, before identity)
| Pair | Better | Why |
|---|---|---|
| multi-flip | A | Uneven, flowing shapes. B tucks into a ball (1.25 s). |
| pencil-throne | A | Arms keep unwinding. B holds a split (1.00–1.38 s). |
| layout-catch | B | Continuous twist. A holds a split (1.25–1.50 s). |
| chain-flips | A | Weight and parallax. B repeats the split (4.00–4.38 s). |
| street-multi-flip | B | Same as multi-flip. |
| wallrun-flip | A | Real stride. B slides (0.38–1.38 s). |
| progress-chain | B | Held 3/4 on sky. A goes through trees (3.12 s). |

Identity guessed afterwards: the reference won 6 of 6, and the newer build won the progress pair. Body shapes decided 5 pairs, camera 1.

## Biggest gap
Every trick holds a frozen inverted split.

**Instruction:** in every trick window, at least one limb_z component must change by ≥0.10 between consecutive 0.1 s samples. Today 31 of 242 samples fail (f2 1.9/4.8/7.3 s, f4 4.9 s, every kickout).

Replace the split with a continuous unwind:
- arms sweep from overhead to the sides;
- one knee bends;
- each program's inverted shape is different.

**Test:** `pose.py` reports 0 slow samples on f1–f5.

## Secondary
1. FlipDist 5.5 m, so that h p90 ≤.36.
2. Clamp the yaw offset so that p5 ≥30° and range ≤20°.
3. Count foliage in hero_occl. Web on ≤45% of a.
4. Add a wall-run stride. The tree canopy under every flip reads as forest (P4).

**Brand:**
- Chest emblem (P2).
- P4: wall ad "…ON BURGER" with a face (c 3.0 s).
- P4: "POP THE SUMM…" billboard (a 12.3 s).

## Verdict: FAILS TARGET
Lowest axis: 6.
