# Critic P3 round 01: traversal and camera

Standard: Marvel's Spider-Man 2. Our files are in `round-01/`. The reference clips are in `refs/traversal/clips/`.

## 1. Axis scores

1. **Swing arc and momentum: 3.** In `a_swing_chain.mp4` from 0 to 15.6 s, the vanishing point stays at the centre of the frame and the road wedge at the bottom never changes size. So the hero keeps the same altitude through every swing. It never dips toward the street and never climbs back up. Each swing takes about 1.5 s, and every one ends with the same flip (2.7, 5.7, 8.0, 9.3, 13.3 and 15.0 s). In `swing-canyon-chase` from 0 to 2.3 s, the hero drops from roof height to just above the cars and rises again. The only thing that sells speed in ours is the blur.
2. **Camera: 3.** The camera behaves as if it were on a rail down the centre of the avenue, with the hero fixed at about 50%/45% of the frame in every shot. The radial blur on the walls is the same strength all the time, and I could not see an FOV kick. In `c_wallrun_perch.mp4` at 7.1 s and 7.2 s, the camera sits inside the hero's torso and head, and the hero drops out of frame at 7.3–7.4 s. The reference `swing-canyon-chase` banks, pitches and reframes on every swing.
3. **Web read: 3.** The rope is thin, straight and taut, and it alternates sides, which is correct. But the anchor is never on screen: the rope always exits at the top edge (still `a_swing_chain_01_t005.0`). On every release, the old rope whips across the lens as a thick translucent white plank (`a_swing_chain` at 0.9, 2.1, 3.8, 7.6 and 11.7 s, and `b` at 1.3 s).
4. **Move variety and transitions: 2.** The dive in `b` from 2.0 to 2.9 s is a static T pose sinking, with no head-down tuck and no build-up of speed streaks (compare `dive-empire` from 0 to 2.5 s). The zip in `b` from 3.0 to 5.5 s ends with the hero seated in mid-air at the roof edge. The wall-run in `c` hits the wall and then holds a frozen frog pose. At the top it shows a T pose at 4.3–5.3 s, then the camera clips inside the hero.
5. **Body motion readability: 2.** In `c` from 1.6 to 4.1 s the wall-run pose is identical in every frame at 10 fps, with no alternating hands and feet. In `a` the legs stay straight and rigid through every swing. The street start in `d` from 0 to 2.0 s is an upright walk, not a sprint or crouch, before the launch. Compare `wallrun-glass-tower` from 2 to 7 s, where the stride is continuous.

## 2. A/B decisions

- **swing-chain: B is better.** It has height changes, a banking camera and anchors that can be seen. A is locked to one flat corridor.
- **release-trick-dive: A is better.** It has real hang time against the sky, a readable trick silhouette and a dive with speed streaks. B's trick is lost in a blurred corridor.
- **wallrun: B is better.** It has a continuous climbing stride, the camera looks up along the facade and it ends in a clean vault. A is a frozen pose, then a T pose, then a camera clip.
- **street-start: B is better.** It has a crouch, a two-rope launch and the camera rises with the hero. A walks and then pops into a swing.

## 3. Biggest gap

**Make each swing a real vertical pendulum and have the camera follow the height.** In `a_swing_chain` from 0 to 8 s, each swing should drop the hero from release height to a low point about 2–4 storeys above the street, or just over car roofs, and rise again past the anchor height before release. The camera should follow the height with lag and pitch changes, so the vanishing point moves at least 15% of the frame height between the low point and the release. Vary the depth and direction of each arc. Reference: `swing-canyon-chase__nm_0139-0147.mp4` from 0.0 to 2.3 s and from 4.0 to 5.7 s.

**Test:** in the telemetry, the height difference between release and low point should be at least 15 m on every swing, and no two consecutive arcs should be the same shape.

## 4. Secondary issues

- The released rope should retract or fade away from the camera, not sweep across the lens as a thick plank.
- Camera collision: the camera must never enter the hero or walls (`c` at 7.1 s, `b` at 3.3 s).
- The wall-run needs a looping climb cycle and a camera that looks up along the wall. Never show a T pose.
- Tricks should come from input, not fire on every release. The release should rise with visible hang time before the trick.

## 5. Verdict

**FAILS TARGET.** Every axis scored 3 or lower, and the lowest was 2.
