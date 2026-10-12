# P3 round 26: blind critic (Opus 5.5)
*Homage fan game. Not official Marvel/Sony/Insomniac.* Evidence: `_scratch/critic-P3-r26-work/`.

All 12 clips viewed. a/c/p1 telemetry = r25.

## Scores [r25]
- **Swing 7 [7].** T7 lows 7.5–11.2 m. T2 fails (gaps 3.37/3.38 s).
- **Camera 7 [6].** w1: 4.09–4.50 m; bbox p90 .335 (telemetry), .322 (pixels). T22: 27.7° up.
- **Web 7 [7].** Rope passes 64/65 frames. web_on 41.8 %.
- **Moves 6 [6].** T4 fails: a 12.4–13.1 s is a held fallCalm. The wall-run is a 4-pose loop with hands at the hips.
- **Body 7 [6].** knee_gap .204 m (was .487). Pawn run 3.64 Hz. Right-arm centroid moves only .052 h.
- **Flips 7 [7].** f4: 7 somersaults and 1 twist. T23 hero ≥.10 on 99 % of frames. Canopy height, backlit.

## Checks
- **(a) Numbers PASS; looks like a jog.**
  - knee_gap median .204.
  - Gait period 0.40 s; pose_sig change over 0.3 s ≥.194 (r25: .065).
  - Shin moves only .07 h.
- **(b) PASS.** Every clip and both launch frames show the teal/yellow suit with a hex emblem. Red ≤2.1 % of the hero box. No white spider.
- **(c) PASS.**
  - Rope 2–4 px.
  - Perch: hero in 113/113 frames, 4.14–6.0 m, pitch 14.29° per 0.3 s.
  - Pawn run 3.64 Hz.
  - T7 holds.
  - f4: 7 flips.
- **(d)** No axis dropped. The stop gate fails: moves is still 6.

## A/B
| Pair | Pick | Why |
|---|---|---|
| wallrun-vertical | B | The facade converges. A looks flat. |
| wallrun-vertical-2 | A | Height. B climbs brick and goes inside a window. |
| wallrun-side | A | True side run, dive. |
| swing-chain-1 | B | Traffic and altitude. A is an empty fog street. |
| swing-chain-2 | A | Dives to the street. B: fog wall, green smear. |
| street-run | B | Lean, crowd, leap. |
| rooftop-perch | B | Skyline ledge. A perches facing a wall. |
| multi-flip | B | Facade plunge. A's hero is in the leaves. |
| progress-wallrun | B | Legs alternate. A: frog pose. |
| progress-perch | A | Same motion; B wears the licensed suit. |
| progress-swing | B | Same motion; A wears the licensed suit. |
| progress-flips | A | Same motion; B wears the licensed suit. |

Guess: the reference won 8/8. r26 is progress B, A, B, A.

## Biggest gap
**Instruction:** fix a_swing_chain 12.4–13.1 s (T4, SPEC line 25).
- Replace the held fallCalm with a trick/dive whose silhouette changes at every 0.1 s sample, or re-attach within 0.6 s.
- Keep T7, web_on and rope gates.

## Secondary
1. **w1 arms:** pump in antiphase; wrist travel ≥.20 of body height; shin span ≥.15 h.
2. **T2:** attach gaps ≤3.3 s.
3. **Default launch t7:** visible translucent box (+25/255 edges), a ghost mannequin and a green glow.
4. **c perch and mural:** at 8.80 s the hero is a sliver behind a corner. The 4.3 s mural text ("…ON BURROUGH") needs origin confirmed.

## Verdict: FAILS TARGET
Lowest: moves 6.
