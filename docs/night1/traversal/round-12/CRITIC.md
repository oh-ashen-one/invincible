# P3 round 12: blind critic (Opus 5.5)
*Homage fan game. Not an official Marvel, Sony or Insomniac game.*
Evidence: `_scratch/critic-P3-r12-work/`

## Scores
- **Swing arc and rhythm: 5.** T4 fails: 5.3 s with no web (f1 1.67–6.97 s). T2 fails: f4 attaches 5.8 s apart. T1 fails: f4 hold is 1.75 s. f5 passes.
- **Camera: 5.** At f4 8.55→8.58 s there is a one-frame cut: pitch +27→−16°, yaw 54°, camera moves 3.1 m (f1 6.30 s is the same). T8 fails (f4 median .28, Reach .62) and T10 fails (spread .12–.18). T14 passes.
- **Web read: 6.** At f4 8.6 s the rope is 2–3 px and exits the top edge. T3 fails: f5 has the web on 62% of the time.
- **Moves: 7.** T22 passes (c 2.4–4.0 s, 52–56° up). T23 passes (at least 50% sky ring in every trick frame). T4 fails. Throne lasts 0.09 s.
- **Body: 6.** Layout is a rigid, identical plank. The hero is black at f4 8.45 s (V 44/255).
- **Flips / air tricks: 6.**
  - Now good: shapes are clear against sky, there is an eased ramp (186→531°/s over 0.15 s), and holds run 0.45–0.55 s.
  - Still failing:
    - The flip starts 1.7 s after release.
    - backDouble uses 5 shapes.
    - The trick ends in a 1.3 s dive with no web, then a cut.

## A/B (judged blind)
| Pair | Better | Why |
|---|---|---|
| multi-flip | B | Flowing body. A is a rigid plank. |
| pencil-throne | A | Goes into the shape immediately. B waits 2 s. |
| layout-catch | B | Catch 1.9 s after release. A takes 4.8 s. |
| chain-flips | A | Flip runs into the web. B has a dead rise. |
| wallrun-flip | A | The run reads as vertical. B looks like a floor sprint. |
| progress-trick | B | Trick against sky, not facade. |

Ours lost 5 of 5 reference pairs, on flow.

## Biggest gap
Each trick is an isolated set piece: 1.7 s rise, trick, 1.3 s dive, then a camera cut.

**Instruction:** start the first shape within 0.25 s of release. Attach a web within 0.3 s of Reach. Blend the trick camera back to the swing camera over at least 0.4 s.

**Test:**
- Release to attach is at most 3.1 s.
- Attach to attach is at most 3.3 s.
- No frame changes pitch by more than 3°, yaw by more than 4°, or camera position by more than 1.2 m.

## Secondary
1. backDouble uses at most 3 shapes. Throne holds at least 0.3 s.
2. Reach bbox is at most .38.
3. The hero goes black against backlight (P4 fill).
4. The suit uses the real game's chest emblem (P2). The billboards "BREWHOUSE COFFEE" and "SONARA" (c 8 s) are invented and not on the exclusion list.

## Verdict: FAILS TARGET
The lowest axis is 5.
