# P3 round 24: blind critic (Opus 5.5)
*Homage fan game. Not an official Marvel, Sony or Insomniac game.* Evidence: `_scratch/critic-P3-r24-work/`. Only a, c and m1 changed. The other clips differ from r23 by ≤2.2/255.

## Scores (r22 in brackets)
- **Swing: 7 [7].** T7 passes: lows 6.5–10 m every ≤3.5 s, drops 22–28 m. T2 fails: attach gaps 3.35–3.5 s (max 3.3). T4: 12.6–13.4 s is a held skydive pose.
- **Camera: 6 [6].** The r23 snap is gone. New faults in c: a pull-out to 10.3 m at 8.65–8.85 s (bbox .06), then a perch pitch whip from −6° to −45° (9.8–10.05 s).
- **Web: 6 [6].** T3 passes (41%). The rope is 2–3 px at 4.4 s. It is invisible against dark glass at 10.7–11.0 s.
- **Moves: 6 [6].** Unchanged.
- **Body: 6 [6].** Knee splay unchanged.
- **Flips: 7 [7].** f1 and f4 unchanged. a has one trick (r22 had 2).

## Owner bugs
1. **Swing: PASS.** x1 1.75 s, x2 3.20 s.
2. **Side-run zip: PASS.** w2 unchanged.
3. **Wall-run animation: PASS.** The pose is still wrong.
4. **Air speed: PASS.** a air 24–43 m/s.
5. **Perch: FAIL (regressed).** c 9.853–9.887 s: no hero pixels. hero_occl=1.0 at 9.88 s.
6. **Mouse look: PASS.** m1 yaw −95°→−44°.

## A/B (blind)
| Pair | Better | Why |
|---|---|---|
| swing-chain-1 | A | Clears rooftops at 5.25–7.75 s, traffic. B stays in the canyon. |
| swing-chain-2 | B | Bright rope against sky. A's rope fades. |
| progress-swing | B | Higher arcs. A hugs the street. |
| wallrun-vertical | A | Leaning sprint. B frog-climbs. |
| wallrun-side | B | Leans into the facade, then a ledge flip. A runs upright on panels. |
| multi-flip | A | Falls past facades. B stays at canopy height. |

Guess: the reference won 5/5; progress B is r24.

## Biggest gap
**Instruction:** make the rope readable on every web_on frame of a_swing_chain (T5/T6).
**Test (10 fps):**
- The rope runs hand → frame edge and is 2–4 px wide.
- Its luminance differs by ≥25/255 from a 6 px band either side, including over dark glass at 10.5–11.2 s and 0.9–1.1 s.

## Secondary
1. **c perch (bug 5), 8.6–10.5 s:** keep hero_in_frame=1 and cam 3.4–7 m. Pitch may change ≤15° per 0.3 s.
2. **T2/T4:** attach gaps ≤3.3 s. The silhouette must change every 0.1 s at 12.6–13.4 s.
3. **Vertical run:** knee_gap_lat median ≤.25 m.
4. **P4:** white plaza and acid-green tree at a 8.25 s. Signs are generic. No real brand recognised.

## Verdict: FAILS TARGET
No axis is below r22, so the axis rule allows a merge. Owner bug 5 regressed, so I recommend holding the merge until the perch keeps the hero in frame.
