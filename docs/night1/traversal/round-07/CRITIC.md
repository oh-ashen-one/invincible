# P3 Traversal + Camera — critic, round 07

## 1) Scores
- **Swing arc / rhythm: 4.** `a_swing_chain` 0.5–11 s chains swings every 1.3–2 s with no stalls. But the camera is locked to the hero, so the arc barely reads (`swing-canyon-chase` 1.0–2.75 s shows it).
- **Camera: 3.** It enters facades at `a` 14.3–14.8 s and `d` 6.8–7.3 s, burying the hero. It jumps at `d` about 2.6 s. The hero is 6–8% of frame height (ref 15–25%). Radial blur never switches off.
- **Web read: 4.** The line is taut, but it is a thick blooming beam (`a` 5.5 s, 13.7 s). The anchor is level with the hero at `b` 2.0–2.3 s and behind him at `a` 14.5 s.
- **Move variety / transitions: 4.** The trick plays against a wall, not the sky (`b` 3.3–4.5 s vs `trick-release-sky` 1.25–2.5 s). The sprint launches with no crouch (`d` 2.3–2.6 s vs `swing-start-from-street` 3.25–4.0 s). Every landing uses one pose.
- **Body animation: 4.** Swing poses change. But the hero hangs rigid at `d` 4.5 s, blur ghosts him at `a` 2.33–2.5 s, and he lands in a sumo squat (`c` 5.3 s, 7.8 s).

## 2) A/B
- **Reference pairs:** the reference wins every one. That is swing-chain A, swing-chain-2 B, release-trick-dive B, wallrun A and street-start A. Our wall-run (wallrun B) comes closest.
- **progress-swing:** B is better by about 1. A drops the web for 1.7 s (7.2–9.0 s) in a starfish fall. B still clips a wall at 14.3–14.7 s.
- **progress-trick:** A is better by about 1.5. Its trick reads (2.0–4.4 s) and it ends in a clean perch. B's trick is unreadable, and B ends with the camera jammed in a wall corner (5.3–6.7 s).
- **Guess (after deciding):** current = progress-swing B and progress-trick A, so both improved.

## 3) Biggest gap
**Chase-camera framing and occlusion.** In every swing, hold the camera 3.5–4.5 m behind and 1–2 m above the hero. The hero should be 12–20% of frame height, in the centre or upper centre, and kept out of the blur. Never within 1.5 m of a facade. Test: in `a` 13.5–15.5 s and `d` 6.5–7.5 s, no wall covers more than 30% of the screen and the hero is never occluded. Target: `swing-canyon-chase__nm_0139-0147.mp4` 1.0–2.75 s.

## 4) Secondary
1. Rope: thin, no bloom, anchored at least 20° up and ahead.
2. Street start: add a 0.2–0.3 s crouch and remove the camera jump.
3. Trick: at the top of the arc, camera below, against the sky.
4. Landings: a 3-point landing with dust, and a real ledge crouch.

## 5) Verdict
**FAILS.** The lowest axis is Camera at 3, and no axis reaches 8.
