# P3 critic, round 05: traversal and camera

Judged from 6 fps frames and body crops. Disclosure: a byte-compare, run after I judged by eye, showed progress-wallrun/A equals wallrun/A. No verdict changed.

## 1) Scores
- **Swing arc & momentum: 5.** swing-chain/A chains low, with no stalls. 9–12 s repeats one arc and hang pose, and the camera straight behind flattens the pendulum (ref `swing-canyon-chase`).
- **Camera: 3.** wallrun/A 6.2–7.3 s: the hero drops off the bottom edge. rtd/B 5.7–7.0 s: the clip ends on a wall with no hero. street-start/A 2.7→2.8 s: the camera snaps in height.
- **Web read: 5.** The rope is straight and taut, and the zip draws a double line (rtd/B 4.8 s). Anchors sit level with the hero instead of above him (street-start/A 3.5–4.0 s, swing-chain/A 4.0 s and 14.0 s).
- **Move variety & transitions: 4.** Tuck, starfish, zip and perch exist. The top-out lands upright with arms out and no crouch (wallrun/A 4.8–5.2 s).
- **Body animation: 3.** wallrun/A 1.5–4.0 s: one frozen splayed pose slides up the wall. Release is a one-frame pose pop that smears the whole body (swing-chain/A 2.5 s and 8.5 s). The suit renders white and unshaded (street-start/A 0–1.7 s, rtd/B 0.2 s).

## 2) A/B
- **swing-chain: B**, far better. Real pendulum, readable anchors, and blur only at peak speed.
- **swing-chain-2: A**, far better.
- **release-trick-dive: A**, far better. Large trick silhouette against the sky; B's hero is about 60 px.
- **wallrun: B**, far better.
- **street-start: B**, far better. Crouched launch.
- **progress-swing: A**, by about 0.5. Tighter, readable body; B has a horizontal rope at 1.0–1.8 s.
- **progress-wallrun: B**, by about 0.5. It keeps the hero framed at 6–7.5 s.

## 3) Biggest gap
**Wall-run (c_wallrun_perch 1.5–4.0 s):**
- **Camera:** 3–5 m behind and below the hero, pitched 20–35° up the facade, with the roof edge in frame.
- **Body:** head-up, with alternating hands and feet at about 2–3 steps per second.
- **Ref:** `wallrun-glass-midday__dn_0011-0019.mp4` 2–6 s.
- **Test:** 6 fps frames show at least 4 distinct limb phases, the head above the hips in every frame, and the hero in frame through the top-out.

## 4) Secondary issues
1. Keep the hero inside the centre 60% of frame during zips and roof transitions (rtd/B 5.7–7.0 s, wallrun/A 6.2–7.3 s).
2. Blend release poses over at least 0.15 s so no smear frame appears (swing-chain/A 2.5 s and 8.5 s).
3. Put anchors above and ahead at 30–60° elevation, alternating sides.
4. Fix the white or unshaded suit, and the pale suit at wallrun/A 5.5 s. Give landings a crouch and a settle.

## 5) Verdict
**FAILS.** The lowest axes are 3 (camera and body animation). No axis reaches 8.
