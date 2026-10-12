# Critic r01: swing, web, air, flips (blind)

## 1. Axis scores (our clips = round-01/*.mp4, 1080p60)
1. **Web deployment: 3.** In s1 at 4.767 the strand appears at full length in a single 60 fps frame (more than 300 px, past the crop edge), which fails W3. At 4.783 the firing arm points horizontally while the strand rises at about 55°, roughly 45° off, which fails W2. In s2 at 11.183 the strand tip appears and then swings about 30° to a new direction in one frame (11.216→11.233). s2 at 2.36–2.44 is the only press I saw with a visible tip travelling out while the arm reaches.
2. **Web read: 5.** The strand is a thin white line about 1–2 px wide and straight under load. It reads well at night (s5, progress-night A at 6.0–7.8). It almost disappears against the bright facades and sky in s1 at 4.4–5.0. I could not see any taper.
3. **Swing body: 3.** In s1 at 4.77–4.92 the hero hangs plumb, legs together, under a rope that is about 50° off vertical. The body does not follow the rope and there is no leg drive. progress-presses B at 11.2–11.5 snaps straight into a stiff plank.
4. **Flips: 4.** s3 shows a readable inverted pencil at 12.2–12.3, a layout at 12.5 and a straddle at 12.7. However, s4/release-air A at 2.6–3.6 is a splayed ragdoll tumble, and s3 at 4.0–5.4 is loose reach poses. The owner clip at 8.9–9.3 holds a pencil and a throne with the hero at about 0.3 of frame height; ours sits at about 0.15 (release-air A at 2.0–3.8).
5. **Air and transitions: 3.** Airtime in release-air A at 2.6–3.6 is limp falling. In progress-flips A at 13.8 a camera snap blurs the whole frame and loses the hero right at the catch. s2 jumps the camera at 2.20.
6. **Camera: 3.** The hero is about 120 px tall out of 1080 (0.11) in s1 at 4.4–5.0, against F9's 0.18–0.36. Facade verticals are rolled by roughly 10–15° (estimated by eye) in the s1 sheet at 7.0, 12.0 and 18.5. In s3 at 21.5–22.0 a red facade fills the frame. The camera mostly sits above the hero looking down, so the trick is not framed against sky.

## 2. A/B decisions
- swing-chain: **B** is better (big hero, rope follows the body, steady chase). A's hero is tiny and the framing jumps.
- swing-presses: **A** is better (clean launch from the street). B pops the camera and the hero jumps around.
- aerial-flips: **B** is better (held, legible shapes at close range). A's shapes are small and loose.
- release-air: **B** is better (open shape against sky). A is a ragdoll tumble seen from above.
- night-swing: **B** is better. Note that B is a car chase, so the movement is only loosely comparable.
- progress-swing: **A**, slightly (about +0.5 on camera). It rolls less and its YDIF frame-change measure is calmer (frames above 25: 31 vs 75). Body is equal.
- progress-presses: **A**, by about +1 on deployment and swing body (A at 11.2–11.4: arm aligned with the strand and the strand persists). B planks and its strand vanishes by 11.5.
- progress-flips: **B**, by about +1 on flips and transitions (B: crisp pencil at 12.2 and a visible catch at 13.8). A blurs and snaps at 13.8.
- progress-night: **A**, by about +1 on camera. In B a dark near facade covers about 30% of the frame and verticals tilt about 15%.
- Identity (it was obvious for pairs 1–5): the reference is swing-chain B, swing-presses A, release-air B and night-swing B; the owner clip is aerial-flips B. For the progress pairs, the current round is likely presses A and flips B (both match round-01 s2 at 11.2 and s3 at 13.8). Swing and night are uncertain.

## 3. Biggest gaps (builder tests)
1. **Strand shot travel and arm aim (web/press system).** The tip should grow from the palm over 4–12 frames at 60 fps and never jump in direction. The shoulder→wrist line should be within 20° of the anchor when the tip lands. Reference: swing-start-from-street. Test: s1 at 4.75–4.95 and s2 at 11.15–11.35, with strand length per frame increasing monotonically and at most 25% per frame.
2. **Camera trick framing (camera rig).** The hero should be 0.18–0.36 of frame height, roll at most 5°, the camera level with or below the hero, and the camera must never end up inside a facade. Reference: trick-release-sky. Test: hero box height on s3 and s4 at 10 fps, at least 90% of samples in range, with no frame more than 50% covered by a single wall.
3. **Swing body follows the rope (swing animation).** The hips should go under the anchor within 0.35 s, the legs should tuck at the bottom and extend on the upswing, and the plumb hang must go. Reference: swing-canyon-chase. Test: body axis within 20° of the rope at the bottom of the arc in s1.

## 4. Secondary
- Free-fall in s4 at 2.6–3.6 needs authored float poses, not a ragdoll splay.
- There is no strand taper.
- The cyan emissive suit lines dominate the night silhouette in s5.
- Swings look uniform; I saw no visible style variety (A2).

## 5. Verdict: **FAILS TARGET**
