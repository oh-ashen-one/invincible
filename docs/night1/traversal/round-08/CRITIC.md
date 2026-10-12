# P3 Traversal + Camera, round 08: critic

Our clips are in `sm2-n1/traversal/docs/night1/traversal/round-08/`. The references are in `refs/traversal/clips/`. Key sheets are in `keep/`.

## 1. Axis scores
| Axis | Score | Evidence |
|---|---|---|
| Swing arc, rhythm, momentum | **4** | `a_swing_chain` 0–15 s: a new rope about every 2 s (≈0.5/2.3/6.3/8.2/12.2 s). The period, arc height and lateral line are the same every time. Across 91 frames, the hero's screen x stays at 46–56 % (p5–p95, measured). This reads as a treadmill. In `swing-canyon-chase` 2.0–4.5 s, swings alternate from street level up to roof level. |
| Camera | **4** | Across all of `a_swing_chain`, the camera is locked on the avenue axis, stays symmetric on the vanishing point, and does not yaw or roll toward the anchor. Its only motion is edge blur. At 10.0–10.5 s it dips to the tarmac without purpose. The reference's camera re-composes on every swing (`swing-canyon-chase` 2.0–5.0 s). |
| Web read | **4** | Anchors sit plausibly above and ahead and alternate sides. At 1.0 s the rope is about 2 px wide and fades into the pale facades. It is invisible at 480 px (sheet `pk_swing-chain_A_00`). In `b_…zip` 3.6–5.1 s, the zip onto the roof shows no line. |
| Move variety & transitions | **3** | `b_release_trick_dive_zip`: the release trick at 2.9–3.5 s reads. After that the hero floats upright past the wall (3.6–4.3 s) and there is no dive. At 4.97→5.10 s he pops from horizontal to an inverted ball to standing, then crouches at 5.37 s: the landing is in reverse order. `c_wallrun_perch` 4.3–5.2 s: the top-out is a slow upright drop past an empty facade. |
| Body animation | **3** | `d_…` 0.5/1.6 s: the run is upright with no lean and the arms hang dead. At 2.5 s the jump has both arms straight up. `c_…` 6.8–7.2 s: a stiff standing idle. The swing pose (one arm up, trailing legs, `keep/hero_measure.png`: 18–22 % of frame height at 1.0/3.0/7.5 s) is the best part. |

## 2. A/B
- **swing-chain, swing-chain-2, release-trick-dive, wallrun:** B, B, B, B are better, overwhelmingly. They have off-axis framing, altitude swings, a crisp hero inside heavy blur, and a readable trick silhouette. The A side of each pair is ours.
- **street-start:** A is better, overwhelmingly (idle→anticipation→two-hand zip launch). B is ours.
- **progress-swing:** B is better, marginally (+0.5). The rope reads and there is speed. But the rope is too thick and emissive, the whole hero smears for 3 frames at each attach (≈2.55 s), the blur makes the facades unreadable, and the camera grazes a wall at 14.3–14.7 s.
- **progress-start:** B is better, by about 1 point. At 6.8–7.3 s in A, the camera and hero sink into the left facade. The hero is half-occluded and smeared, and the rope is aliased (`keep/progress-start_A_7.0_wallclip.jpg`).

## 3. Biggest gap: a locked, symmetric chase camera plus identical swings
In `a_swing_chain`, every swing should:
- Yaw the camera 10–20° toward the active anchor side and roll it 3–8° with the arc.
- Alternate the hero's screen x between about 30 % and 70 %.
- Vary the arc bottom by at least one storey between consecutive swings, so that the vanishing point moves by at least 15 % of frame height per swing.
- Keep the hero crisp while the world blurs.

Test: over 10 s, the hero's x p5–p95 spread is at least 30 % (it is 10 % today). Match `swing-canyon-chase__nm_0139-0147` 2.0–4.5 s and the reference in `pack/swing-chain/B` 2.0–4.8 s.

## 4. Secondary issues
1. Landing order: impact crouch first, then rise, with no mid-air snap (`b_…` 4.97–5.37 s; compare `landing-crosswalk-night` 2.0–3.5 s).
2. The zip and top-out need a visible line, an arc and a vault pose (`c_…` 4.3–5.2 s and 7.3–7.7 s; compare `wallrun-empire` at the ledge vault).
3. Run cycle: forward lean and arm swing (`d_…` 0–2.3 s).
4. The rope needs contrast: thin but dark-edged or lit, not near-invisible (current) and not a glowing bar (progress variant).

## 5. Verdict
**FAILS.** The lowest axis is 3. No axis reaches 8.
