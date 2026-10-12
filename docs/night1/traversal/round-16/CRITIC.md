# P3 round 16: blind critic (Opus 5.5)
*Homage fan game. Not an official Marvel, Sony or Insomniac game.* Evidence: `_scratch/critic-P3-r16-work/`

## Scores
- **Swing arc and rhythm: 7.** a: holds 0.53–1.37 s, gaps 1.68–2.62 s. T7 low point 0.6 m.
- **Camera: 5.** Pass: TC-B (held p95 30–38°/s), E, F (dz 0.87–0.93 m), K.
  - TC-A: k≥0.9 only 0.65 s after release; yaw range 52–67°.
  - TC4/TC-C: distance 4.2 m; h p90 .381 (f1), .373 (f4).
  - TC-D: cy p95 .52 (f2, f4).
  - TC-H: view_sun min 70–85°. f4 1.50 s torso blown (16.6% of box ≥245).
  - TC-I: 2 of 125 samples (2%) pass.
  - TC-G: leaves over his legs at f4 3.25 s; hero_occl=0.
- **Web read: 6.** Web on for 53% of a (T3 limit 45%).
- **Moves: 6.** Top-out flip reads well (c 3.5–4.5 s). Wall-run is one sliding pose (c 2.5–3.25 s).
- **Body: 6.** Limbs symmetric: swan arms even, legs together in every kickout.
- **Flips / air tricks: 6.** Tuck closes (f1 3.9–4.5 s), swan holds 0.4 s (f2 3.9–4.3 s). But the pike is a lump from 3/4 behind (f2 3.5–3.7 s) and release frames wash out (f1 3.5–3.6 s). The reference throws asymmetric shapes.

## A/B (judged blind, before identity)
| Pair | Better | Why |
|---|---|---|
| multi-flip | B | Flowing, uneven shapes. A's tuck is a grey blob (1.50 s). |
| pencil-throne | A | Held yaw, on sky. B swings onto dark facade (2.0 s). |
| layout-catch | B | Clean layout. A yaws ~90°, hero white (1.00 s). |
| chain-flips | A | Backlit on held yaw. B glares (0.50–0.75 s). |
| canyon-multi-flip | B | A glares (0.50 s), swings to facade. |
| wallrun-flip | A | Real run. B slides one pose. |
| progress-chain | B | A loses hero (2.25 s), enters tree (4.75 s). |

Identity guessed afterwards: the reference won 6 of 6, and the newer build beats the older one. Camera decided 5 pairs.

## Biggest gap
Every trick is shot from the street into a dark facade, and each starts facing the sun.

**Instruction:** fire flips from an apex with hips ≥3 m over the lower roofline (TC8). At release, pick the 35–55° side with view_sun ≥100°. Blend in within 0.35 s.

**Test (f1–f5, 10 fps):**
- ≥35% of samples: 40 px ring ≥50% sky, h ≥.15.
- view_sun_deg min ≥100.
- Suit luma ≥245 ≤5% on every frame.
- flipcam_k ≥0.9 by flip_t 0.35.

## Secondary
1. FlipDist 5.5 m, so that h p90 ≤.36 and cy p95 ≤.48.
2. Count foliage in the occlusion probe (f4 3.25 s).
3. Asymmetric limbs; turn the pike side-on.
4. Add a wall-run stride cycle. Web in a ≤45%. Swing T8 median ≤.23 (now .247).

**Brand:** chest emblem copies the real game's (P2). P4: check the faded wall sign (c 2.5–6.5 s) and green bokeh blobs (b 2.0–4.75 s).

## Verdict: FAILS TARGET
Lowest axis: Camera, 5.
