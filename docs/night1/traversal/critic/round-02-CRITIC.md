# P3 Traversal + Camera — critic round 02 (fresh eyes, pixels only)

## 1. Axis scores
| Axis | Score | Evidence |
|---|---|---|
| Swing arc & momentum | **3** | a_swing_chain 4.0–5.8 s: hero stays pinned at the same screen spot and height while the vanishing point doesn't move. Stretches with no rope at 2.0–3.4, 6.3–8.3 and 12.0–13.9 s (about 1.5–2 s each) are dead glides. In ref swing-canyon-chase 0:01–0:05 the rope is almost always attached and the hero climbs to rooftop height. |
| Camera | **2** | b_release_trick_dive_zip 5.5–5.8 s: the camera slams into the hero's head. c_wallrun_perch 6.5–7.2 s: the camera is inside the hero's head and torso, and at 6.67–6.83 s the hero is out of frame. Outside those moments it's a rigid lock-behind with the hero dead centre, which gives no sense of trailing or lag. |
| Web read | **4** | The rope is straight and taut, and in d it alternates sides (right 2.6–4.2 s, left 5.3–7.0 s). But no anchor point is ever visible; every rope exits off the top of frame. At d 4.0–4.17 s the rope runs horizontally to a wall at hero height, so the anchor isn't above him. At a/d 11.5 s the rope reads as a thick white bar. |
| Move variety & transitions | **3** | c 1.5–4.0 s: the wall-run is filmed straight at the wall, so height and speed don't read. At the top he stands in a T-pose (4.2–5.3 s) instead of vaulting. The zip (b 4.7–5.8 s) ends in a camera crash, and the landing is the hero lying flat on the roof (c 7.3–7.7 s). Ref wallrun-glass-tower looks up along the facade instead. |
| Body motion readability | **3** | a 4.0–5.8 s: one arm up and legs straight, held for about 2 s with no tuck or leg trail. b 3.2 s: the hero dissolves into a red smear. d 1.5–2.0 s: an upright run with no forward lean. |

## 2. A/B
- swing-chain, swing-chain-2, release-trick-dive, wallrun, street-start: **B is better in every one, by a wide margin.** B has a trailing camera with large vertical travel, a small hero moving inside the frame, and a clear trick silhouette against the sky. My guess: A is ours in all five (gray-box).
- progress-swing: **B beats A by about 1 point** (2 → 3). A is a blur tunnel with the hero locked in the centre and the rope nearly invisible. B has a readable rope most of the time, some movement in frame and glimpses of rooftops. B matches round-02 a_swing_chain frame for frame.

## 3. Single biggest gap
Replace the fixed-offset camera with a lagged chase camera that has collision handling:
- Sit 4–6 m behind the hero and 1–2 m above, pitched down 10–30°.
- Let the hero move within the frame: lower third at the bottom of the arc, upper centre at the apex. Hero screen-y should swing by at least 20% of frame height on every swing.
- Probe for collisions: no frame where the camera is within 2 m of the hero, and no frame where the hero's bounding box exceeds 30% of the frame or leaves it.

Test: a_swing_chain, b_release_trick_dive_zip 4.5–6.5 s and c_wallrun_perch 6–8 s. Reference: swing-canyon-chase 0:01–0:05.

## 4. Secondary
1. Cut the rope-less gaps to 0.5 s or less after the apex, and shorten swings to 1.2–1.8 s.
2. Anchors must sit above and ahead of the hero, and be visible in frame when the rope attaches. d 4.0 s is not.
3. Wall-run camera should sit behind and below, looking up the wall with the roofline visible, and end in a vault or launch (ref wallrun-glass-tower 0:02–0:07).
4. Remove the hero smear (b 3.2 s) and the held static poses. Swing body needs to tuck and extend, and the landing needs a crouch with no prone pop (ref landing-street).

## 5. Verdict
**FAILS TARGET.** The lowest axis is camera at 2, and every axis is well below 8.
