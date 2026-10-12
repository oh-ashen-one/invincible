# P3 Traversal + Camera — round 04 critic (blind)

## 1) Scores
- **Swing arc & momentum: 4.** Left/right pendulum alternates (swing-chain/A), but there is 1.2–1.5 s of rope-less, floaty drift at 2.1–3.5 and 12.2–13.9. Arcs are identical.
- **Camera: 3.** Camera sits ~12–15 m back, pitched 45–60° down. The hero is 4–6 % of frame height (ref 15–25 %) and there is never any sky. It nearly rolls top-down at swing-chain/A 12.3–13.9. It faces the wall flat, so the hero is a static blob (wallrun/A 1.7–4.0). It jams into a wall and crops the hero (release-trick-dive/B 5.8–6.6).
- **Web read: 4.** Rope is straight, taut and hand-attached (swing-chain/A 3.6–5.1), but it is an over-bright beam. The anchor is never on screen: the rope exits the top edge and reads as tied to sky (13.9–15.3).
- **Moves/transitions: 3.** The trick is a tiny blurred tumble against facades with no hang time (release-trick-dive/B 3.4–4.1, vs ref trick-release-sky 1.3–2.7). The wall-top is an arms-out float, then a stiff stand, with no crouch or impact (wallrun/A 4.3–5.3).
- **Body animation: 4.** The hang is decent (swing-chain/A 4.6–5.1), but the body lies flat, perpendicular to the rope, at 3.9–4.5. The wall-climb holds one frozen pose for 2.5 s with no alternating limbs (wallrun/A 1.7–4.0). The run is upright with arms pinned (street-start/A 0–2.0).

## 2) A/B
- swing-chain: **B** (wide margin).
- swing-chain-2: **A**.
- release-trick-dive: **A**.
- wallrun: **B**.
- street-start: **B**.
- progress-swing: **A** better, moderately (~+1.5 body, ~0 camera). B's mannequin T-poses at 3.0–3.3 and goes inverted at 2.7.
- progress-trick: **A** better, slightly (~+1 body only). Identical camera and path; B is a rigid spread-eagle at 4.0–4.3.

## 3) Biggest gap: chase-camera distance and framing
On every rope-attached or airborne frame:
- **Camera:** boom 4–5 m behind and 1–1.5 m above the hero, pitched 10–20° down.
- **Framing:** hero upper-centre at ≥160 px of 1080. The facade anchor point and a band of sky are visible at each attach.
- **Test:** on a recapture of swing-chain, hero bbox ≥160 px in ≥90 % of frames 0–15.6 s, and the anchor on-screen for every attach.
- **Reference:** swing-canyon-chase 0:00–0:03, trick-release-sky 0:00–0:02.

## 4) Secondary
1. Re-attach ≤0.5 s after release, or play a real trick with visible hang time.
2. Wall-run camera below and behind, looking up the wall, with an alternating hand/foot cycle (ref wallrun-empire 2.0–3.0).
3. Every touchdown gets a crouch or three-point pose; the camera settles in ≤0.3 s and never clips into walls.
4. Lock the torso to the rope line at the bottom of the arc.

## 5) Verdict
**FAILS.** Lowest axes are camera and moves, at 3. No axis reaches 8.
