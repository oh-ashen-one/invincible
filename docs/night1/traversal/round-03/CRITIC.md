# P3 Traversal + Camera — round 03 critic

## 1) Scores
- **Swing arc & momentum 3**: a repeats one cycle (~4.7 s). Rope on 0–2.0, 3.9–6.5, 8.7–11.7, 13.9 s, with dead gaps of 1.3–1.6 s.
- **Camera 3**: locked straight behind, hero pinned centre every frame (ref swing-canyon-chase 0–5 s yaws off-axis). Edge blur stays heavy at the apex (a 7.4–8.2). b 5.617→5.65: hard snap from canyon to roof ledge, with a window filling the lens. c 1.8–3.9: flat-on to the wall (ref wallrun-glass-midday 2.7–6.4 looks up it).
- **Web read 4**: rope is straight and taut. Anchors are always off-frame. On release it becomes a thick stub into air (a 1.8–2.0, 6.5, 11.7). Sides go right, right, right, left, so no reliable alternation.
- **Move variety & transitions 2**: the same flip then T-pose every cycle (a 2.6/12.1, b 3.7). No dive: b 4.7–5.5 has no pitch-down or streaks (ref dive-empire). The zip ends in a cut. After the wall-run top-out: T-pose, face-into-wall, falls flat (c 7.5), corner crouch. No landing, no glide.
- **Body readability 2**: rigid poses held 1.3–2.5 s: star pose in air (a 7.2–8.5), identical wall-run splay c 1.8–3.9 with no limb cycle. Body horizontal and perpendicular to the rope (d 3.0–3.7). Ref swing-canyon-chase 5.5–7.75 changes pose every ~0.25 s.

## 2) A/B
- swing-chain **B**; swing-chain-2, release-trick-dive, wallrun, street-start **A**. Every winner has continuous pose change, a choreographed camera and visible anchors; ours loses each by 5+ points.
- progress-swing: **B**, by ~0.25. The pulled-back camera shows more canyon, but the hero drops to ~4% of frame height.
- progress-wallrun: **B**, by ~0.5. In A the camera passes through the hero's head at 6.96.

## 3) Biggest gap: dead air phase
From release to the next attach (a 2.2–3.8, 6.9–8.5, 12.1–13.4), the hero holds a rigid T-pose while the camera stays locked.
- **Do:** play tuck → flip/spin → extend → reach, varied per cycle. Pitch/yaw the camera so the hero sits upper-centre against sky at the apex.
- **Test at fps=6:** no two consecutive air frames share a silhouette, and no two cycles match in a 15 s chain.
- **Ref:** swing-canyon-chase__nm_0139-0147 5.0–7.75; trick-release-sky__nm_0425-0433.

## 4) Secondary
1. Zip end (b 5.62): teleport cut plus facade clip. Needs a continuous blend of ≤0.3 s.
2. Wall-run: camera behind/below looking up a converging facade, with a visible climb and alternating limbs.
3. Chase cam: add lateral lead, speed-scaled blur, and a low dip (swing-avenue-midday 3.0–3.8).
4. Release: drop the stub, alternate sides, show the facade attach point.

## 5) Verdict
**FAILS.** Every axis is ≤4; the lowest is 2. The placeholder hero is unreadable at 4% frame height.
