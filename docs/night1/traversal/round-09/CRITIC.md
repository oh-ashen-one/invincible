# P3 Traversal + Camera, round 09: blind critic

I judged only pixels from the gray-box canyon. I read no builder files. I measured with the spec instruments: `vp_cam.py`, `nearflow.py 8`, and `ref_hero_dets.py` (YOLO11x-seg, 10 fps). For the hero pick, I used the detection that holds the most red suit pixels. For the rope, I used a black-hat line detector and checked its results by hand on full-res crops.

## Scores (a = a_swing_chain.mp4, 15.6 s; d = d_sprint_jump_first_swing.mp4)

**1. Swing arc and rhythm: 5**
- T1 passes. The rope is held about 1.0–1.5 s per swing (a: 0.4–1.9, 2.5–3.9, 4.3–5.8, 6.5–7.6).
- T2 passes, but only at the top edge: 4 attaches in 0–8 s.
- T4 mostly passes, since the silhouette changes in the gaps (for example the tumble at 6.1–6.4). The gaps are only 0.4–0.7 s long, so there is none of the ref's 1.5–3 s trick or dive phase.
- T7 fails. Across all 15.6 s, the hero never climbs to roofline height. There is always tall facade above him, and his low point barely changes.
- The swing period is a metronomic ~2 s, the same arc repeated.

**2. Camera: 6**
- a passes T8 (h p10/50/90 .177/.217/.272), T9 (cx p5–p95 .463–.545), T12 (yaw p50/p90 7.5/14.1°), T14 (hFOV 103°), T17 (.29/.46), T18 (side-third p50 .48, 47% > 50%), T20 (.29), T21 (3.64) and T16 (96%).
- a is marginal on three lines:
  - T10: cy p95 .719, above .70.
  - T11: pitch p5 3.0° and p50 11.8°, both at the band edge.
  - T13: |roll| p50 1.6°, above 1.5°.
- d fails T8 (median .266) and T10 (cy p95 .789).
- In a at 8.7 s, the hero is washed out where he overlaps the right facade. T19 is suspect.
- In b there is a camera pop between 0.000 and 0.017 s.
- T22 passes. In c, the camera pitches up 44–51° at 1.6–2.9 s (from the vertical vanishing point, with the hFOV assumed).

**3. Web read: 4**
- T3 fails. The rope is on screen 52% (detector, near-vertical lines excluded) to about 67% (hand-read) of each 8 s window, against a target of 25–45%.
- T5 is partial: the rope reaches the frame edge in 65% of rope frames.
- T6 passes: the rope is 3 px wide and its median angle from vertical is 32°, steeper than the typical 15–20°.
- At b 2.0 s, the rope runs down-left to the frame corner, so it is anchored below and behind the hero.
- At a 7.7–7.9 s, the hero holds a raised-fist hang pose with no rope visible.

**4. Moves and transitions: 5**
- The moves are all there: sprint-jump, swing, tumble, dive, point-zip with perch, wall-run with vault, idle, and zip.
- T23 fails. The b trick at 2.6–3.9 s is framed against a white facade, not the sky, with the hero at about 0.10 of frame height.
- There is no rise and hang time before the trick.
- The b landing snaps into a perch at 5.3 s, and the perch is held static for 1.5 s.

**5. Body animation: 5**
- The swing poses vary and the body follows the rope at the arc bottom in a, around 1.0 s and 5.0 s.
- At b 1.4–2.0 s, the body is inverted on a horizontal or descending rope and is not aligned to it.
- At a 6.1 s, the body is a rigid plank.
- P2 clip dependencies, noted but not scored: the sprint is upright with little lean, and the wall-run is a loop with one arm raised.

## A/B decisions (decided on motion first, identity guessed afterwards)
- **swing-chain:** A is better. It has roofline-to-street altitude, long web-less tricks and a varied rope. A is the ref, B is ours.
- **swing-chain-2:** A is better, for the same reasons. A is the ref, B is ours.
- **release-trick-dive:** B is better. It releases high, silhouettes the trick against the sky and dives. B is the ref, A is ours.
- **wallrun:** B is better. The run is continuous and the camera looks up the wall throughout. B is the ref, A is ours.
- **progress-swing:** Both clips are ours. A (the r09 version) beats B by about 1 point on camera:

| Line | A | B |
|---|---|---|
| T11 pitch p50 | 11.8° (pass) | 20.6° (fail) |
| T14 hFOV | 103° (pass) | 94° (fail) |
| T8 hero height median | .217 (pass) | .246 (fail) |
| T10 cy p95 | .719 | .766 |

  Near-field (T17/T18) is equal. Arc and rhythm are unchanged between the two.

## Single biggest gap
Change the chain in `a_swing_chain` so that every 8 s window has:
- rope on screen for 25–45% of the time (T3), measured with the same detector;
- at least one web-less release of 1.5 s or more in which the silhouette changes at every 0.1 s sample (T4);
- the hero peaking at roofline height in that release, then bottoming out 1–4 storeys above the street within 4 s (T7).

Right now the chain is 4 identical 2 s swings, with the rope on screen for 52–67% of the time and the hero never reaching the roofline.

## Secondary issues
1. The camera is marginal on T10 (cy p95 .72), T11 (p5 3.0°) and T13 (roll 1.6°). Clip d fails T8 (.266).
2. At b 2.0 s, the rope is anchored below and behind the hero. At a 7.7–7.9 s, there is a hang pose with no rope visible.
3. The b release trick is not silhouetted against the sky and has no rise (T23).
4. There is a camera pop at b 0.0 s, the hero is washed out near the facade at a 8.7 s (T19 is suspect), and the b perch landing snaps at 5.3 s.

## Verdict: FAILS
The lowest axis is web read at 4.
