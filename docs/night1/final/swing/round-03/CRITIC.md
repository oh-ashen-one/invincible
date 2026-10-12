# Critic r03 (blind)

## 1. Scores
| Axis | Score | Evidence |
|---|---|---|
| Web deployment | 4 | s2 11.167: no strand. 11.183: full-length strand to frame top, arm rises same frame. No travel, no lead. s3 5.52: anchor level, not above. |
| Web read | 5 | Night: clean 2-3 px (night-swing B 0.6). Pale facades: ~2 px, nearly lost (s3 4.25-4.33). Canyon ref: every strand reads. |
| Swing body | 4 | s1 3.0-6.8 (5 fps): same diagonal arm-up pose in every sample. Canyon ref cycles hang, curl, horizontal. |
| Flips | 6 | s3 4.40-5.52: swan, then inverted straddle held ~0.3 s, then tuck, then reach. Eased (~560°/s). Pencil legs apart. Owner shapes tighter. |
| Air/transitions | 4 | Holds >0.6 s: progress-flips 16.5-17.4, 20.0-20.9; progress-presses 5.0-6.2 (1.2 s). s2 11.25-11.33: upright to 45° in 0.08 s. |
| Camera | 4 | s3 4.4-5.9: hero 0.10 of frame height (F9: 0.18-0.36). aerial-flips B 10.0: centroid y 0.09, head cropped. Wall fills frame at progress-flips 21.2-21.9. Tricks against street, not sky. Ref rolls ~15° (canyon 3.0). |

## 2. A/B
- **swing-chain:** A much better: varied body, readable webs.
- **swing-presses:** B better: crouch, two-hand launch.
- **aerial-flips:** A better: sky behind, web curves in flight (0.4-0.6).
- **release-air:** B better: sky behind trick, hang time.
- **night-swing:** A better, but mismatched (A is a dive).
- **progress-swing:** A +0.5 camera (hero 0.22 vs 0.13 at 8.75). Rest equal.
- **progress-presses:** Tie; same strand pop at 11.217. B +0.25 framing at 23.0.
- **progress-flips:** Tie; motion matches frame for frame 4-22 s.
- **progress-night:** B +0.5 web (slack release 8.8). Motion equal.

Identity obvious every pair.
- Reference: swing-chain A, swing-presses B, release-air B, night-swing A. Owner: aerial-flips A.
- Progress: teal build = round 03 (A, B, A, B). Barely differs from the previous build.

## 3. Biggest gaps
1. **Swing/air pose evolution.** No pose held >0.4 s. Swing: drop-in, legs tucked at bottom, then driven forward (swing-canyon-chase).
   - Test: silhouette IoU, 0.3 s apart, <0.85 at s1 3.0-6.8 and progress-flips 16.5-17.4 / 20.0-20.9.
2. **Web shot travel.** Arm leads the strand by 2-3 frames (60 fps). First strand frame ≤35% of hand-to-anchor; tip lands 4-12 frames later. Anchor above and ahead (owner 0.4-0.6).
   - Test: s2 11.183, s3 5.52.
3. **Trick camera.** Hero 0.18-0.36 of frame height, centroid y 0.25-0.70. Camera at/below hero, sky behind. Walls/foliage ≤40% of frame.
   - Test: s3 4.4-5.9, aerial-flips 9.8-10.2, progress-flips 21.2-21.9.

## 4. Secondary
- Strand needs a dark core/rim on bright facades (s3 4.25).
- Chest pops at attach (s2 11.25-11.33).
- 2 s wall stall with no strand (progress-presses 22.4-24.4).
- Strand vanishes mid-hang (progress-flips 21.8).

## 5. Verdict
**FAILS TARGET.** No axis reaches 8; best is 6.
