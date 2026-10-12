# P3 r06 critic: traversal + camera

## 1) Scores
- **Swing arc/momentum: 4.** swing-chain/B has a web on 0.3–2.4 s, a 1.5 s ropeless tuck-fall (2.5–3.9), a web on 4.0–6.5, then a ~2 s fall. That is about a 4 s cycle, against about 1.3 s in swing-canyon-chase__nm_0139-0147.
- **Camera: 4.** Blur and FOV breathing exist (swing-chain/B 0.7→1.3). But release-trick-dive/A snaps viewpoint in one frame (5.57→5.65) after grinding against a wall (5.3–5.6). The hero sits on the bottom frame edge (street-start/B 2.9–3.1). The camera stays level at hero height, where the ref pitches 10–25° down.
- **Web read: 5.** The line is straight, taut and hand-attached (swing-chain/B 4.0–6.3). The anchor is never seen hitting a facade. The near-camera rope smears into a fat white band (3.97). There is no visible detach on release.
- **Moves/transitions: 4.** The trick is a tiny tuck/starfish inside the canyon, with no roof clearance and no sky silhouette (release-trick-dive/A 3.3–4.7, against ref B 1.3–2.7). There is no dive. The wall-run top-out goes crouch → stand → 1 s dead orbit → zip (wallrun/A 5.3–7.3).
- **Body animation: 4.** At the arc bottom the body is a plank about 45° off the rope with a locked straight arm (swing-chain/B 4.1–4.5). The sprint is upright with no lean, and the suit blows out to white in sun (street-start/B 0–1.2). The idle is a stiff neutral stand (wallrun/A 6.3–7.0).

## 2) A/B
- swing-chain **A**, release-trick-dive **B**, wallrun **B**, wallrun-2 **A**, street-start **A**.
- progress-wallrun: **B** is much better (about +2). A slides up the wall in a frozen splayed pose (1.7–4.0) and ends with the camera buried in the wall (6.7–7.3).
- progress-swing: a tie. B is marginally cleaner (A's hero ghost-smears at 2.5), by under 0.25.

## 3) Biggest gap: swing cadence
Re-time the chain so attach→release takes 1.2–1.8 s. Release at the apex, re-attach within 0.5 s, and never free-fall without a rope for more than 0.6 s unless a trick is triggered. At the arc bottom the body should follow the rope within ±15°. Target: `refs/traversal/clips/swing-canyon-chase__nm_0139-0147.mp4` 0–8 s, which has about 5 swings. Test: swing-chain/B has 3 attaches in 12 s now and needs 7 or more, with the rope on screen at least 75% of the time.

## 4) Secondary
1. No viewpoint snaps. Add wall avoidance, and pitch down 10–25° in canyons.
2. Release/trick: clear the roofline, hang for at least 1 s, and fill at least 12% of frame height against the sky.
3. Remove dead beats after top-out. Give the sprint a forward lean.
4. Fix suit exposure in direct sun, and thin the near-camera rope.

## 5) Verdict
**FAILS.** Every axis is at 5 or below.
