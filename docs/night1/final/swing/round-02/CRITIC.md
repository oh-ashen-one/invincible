# Critic r02: swing / web / air

## 1. Scores
1. **Web deployment: 4.** The strand starts at the palm and travels over about 3 frames (s2 2.333→2.367 s, so not full length on frame one). But at s2 1.75–2.33 the camera is behind a wall, so the press is unseen. On release the strand stays straight and is gone after about 0.10 s (s4 14.82→14.92; target 0.15–0.40 s, slack). Some anchors are level with the hero or to the side (progress-night A 10.0 s).
2. **Web read: 6.** The strand is 2–3 px, has a taper and is crisp at night (s5, progress-night). Against sunlit facades it fades (s4 14.85, s2 2.35).
3. **Swing body: 4.** Mostly a curled "cannonball" or a prone superman along the rope (progress-swing 4.2–5.6). There is a near-identical vertical dangle for about 1.2 s (progress-presses 10.0–11.2, both builds) and a near-T-pose fall at 9.2 s.
4. **Flips: 3.** Mostly horizontal layouts. An inverted pencil reads only occasionally (progress-flips B 2.2, 6.0). At 2.5–20 fps I could not read any tuck or pike. The owner clip holds a throne, a spread-eagle and an inverted pencil at about 1.5 s, all with sky behind.
5. **Air/transitions: 3.** The hero skims prone across a rooftop (s3 5.5–5.9 s; aerial A 5.5, 9.5). A frog sprawl is held for 0.45 s (s4 15.10–15.55). The camera snaps at s3 4.4→4.5.
6. **Camera: 2.** It sits high and pitched 40–60° down. The hero is about 0.05–0.15 of frame height (s4 3.0–7.5 hero not findable). Roll is 10–20° (s1 1.0, s5 2–6 s). The camera ends up inside geometry (progress-presses A 12.9–13.7; s2 1.75) and loses the hero (progress-flips A 6.4–7.2, 14.0–14.4).

## 2. A/B
- **swing-chain:** B is better (readable hero mid-frame, level camera). A's hero is tiny and the camera rolls. B is the reference (obvious).
- **swing-presses:** B is better (a readable two-hand launch). A's camera hits the wall at 4.5 s and looks straight down at 5–7 s. B is the reference (obvious).
- **aerial-flips:** B is better (held open shapes, sky behind). A repeats its runs and skids prone across the roof. B is the owner clip (obvious).
- **release-air:** A is better (swan dive and inverted dives, large hero). B's hero is tiny, in repeated frog sprawls. A is the reference (obvious).
- **night-swing:** B is better on motion, but it is a dive, not a swing. A has our best strand read. B is the reference.
- **progress-swing:** a tie (≤0.5 apart on every axis).
- **progress-presses:** B is better: +1 on camera (A's camera is in a dark interior at 12.9–13.7 s, with extra cuts at 5.0 and 13.77). The other axes are equal.
- **progress-flips:** B is better: +1 on flips (pencil at 2.2/6.0 and pike-V at 21.2, where A shows a superman pose) and +2 on camera (A frames the hero out after the catches).
- **progress-night:** B is slightly better: +0.5 on web deployment (anchors above and ahead, where A shows horizontal or sagging strands at 8.8 and 10.0).
- **Identity (low confidence):** the progress A clips match the round-02 renders a little more closely (PSNR 17.9 vs 16.5 on s3; A higher on all four). My guess is that A is the current build. If so, this round **regressed** on flips and presses.

## 3. Biggest gaps
1. **Air and trick camera.** After a release and through the catch:
   - Keep the hero at 0.18–0.36 of frame height.
   - Keep pitch at most 10° down and roll at most 5°.
   - Keep the camera out of geometry and never lose the hero.

   Reference: owner clip 0–8 s and trick-release-sky. Test: the hero's bbox is present on 100% of frames and is at least 0.18 of frame height on at least 90% of air frames; roll measured from building verticals is at most 5°.
2. **Flip programs.** Each trick needs a real tuck or pike (at least 3 frames at 25 fps) and one open shape (pencil, throne or spread) held at least 0.3 s at 150°/s or less. Remove the prone superman as the default pose. Reference: owner clip strip. Test: F4/F6 on s3, with a different end shape on 3 of 6 tricks.
3. **Swing body and release.** Each swing should read as drop-in → legs driven under → legs forward on the upswing. Replace the vertical dangle (more than 0.6 s) and the prone rooftop skim. Reference: swing-canyon-chase. Test: the pose signature changes by at least 0.15 per 0.3 s, with no held pose longer than 0.6 s.

## 4. Secondary
- The released strand should go slack and stay visible for 0.15–0.40 s (it lasts 0.10 s at s4 14.82).
- Anchors should sit above and ahead of the hero; drop horizontal side anchors (progress-night A 10.0).
- The cyan bands bloom and dominate the silhouette at night (s3 10.5–11.0).
- The mannequin-like hero hides the pose read. That is not my axis, but it hurts the flip read.

## 5. Verdict
**FAILS TARGET.**
