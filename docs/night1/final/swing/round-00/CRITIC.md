# Critic r00: swing, web, air, flips (blind)

Clips: `round-00/s1..s5`. Refs: swing-canyon-chase, owner flips clip. Frames are in `critic-r00/w/`.

## 1. Scores
| Axis | Score | Evidence |
|---|---|---|
| Web deployment | 2 | s2 0.8–2.2 s: a perfectly vertical strand runs from empty sky down to the hero's head/upper back while both hands are at his sides (W1, W10). s1 3.40 s: the strand appears about 600 px long in one 60 fps frame, with no tip travel and no arm reach in the 9 frames before (W2, W3). s1 1.650→1.667 s: the strand vanishes in one frame (W8). |
| Web read | 5 | s1 3.5 s: against the facade the strand is about 6 px wide horizontally on a 41° diagonal, so about 4 px across, which is in spec. But it changes from black to white partway along, has no taper, and at s2 1.8 s it is a dark rope with a constant 5–8 px width. At night (s5) it reads as bright white, while the hero is invisible in most samples. |
| Swing body | 3 | s1 0.5–1.25 s: a rigid horizontal plank under the rope with no tuck at the bottom and no leg drive. Real swings are rare: in s1, strands are visible in only about 10 of 40 samples at 2 fps, and the hero mostly falls down the canyon into the trees (s1 3.9–4.6 s). |
| Flips/tricks | 4 | s3 0.4–2.8 s: tuck → stiff upright → inverted pencil held about 0.5 s (≈F4), but arms stay pinned and limbs change shape together. s3 repeats the same program every 7.5 s (0/7.5/15 s look identical). The owner clip shows throne, spread-eagle and layout shapes with the limbs well apart. Ours shows about 3 shapes. |
| Air/transitions | 3 | s1 1.68–3.30 s: 1.6 s of free fall with no press and the hero tumbling inverted (2.88–3.04 s). s1 8.4–9.6 s: the arm reaches left with no strand, then the hero tumbles inverted beside the wall. That is a reach with no follow-up, not a chain. The s3 2.4 s catch from inverted reads OK. |
| Camera | 3 | s1 and s4 are pitched 40–70° down at the street, unlike the level ref camera (canyon-chase 2.0 s). s3 5.0 s: the hero is 50/540 px tall, 0.09 of frame height (F9 asks 0.18–0.36), seen against a facade rather than sky. The camera is inside tree crowns at s2 31.5–32.0 s and s4 3.5 s. The hero's head is cut off at the top of frame at s1 0.0 s. |

## 2. A/B
- swing-chain: **B** is better (level camera, held hero, taut rope ahead and above). A falls and hugs walls.
- swing-presses: **A** is better. B has the sky strand to the head and the walls/trees.
- aerial-flips: **A** is better. It has larger and more varied shapes, the camera below the hero, and sky behind.
- release-air: **A** is better. B's air time is long, unpowered falling.
- night-swing: **B** is better. In A the hero is invisible against the night facades.

Identity was obvious in every pair from duration, resolution and suit. The 8 s / 24.3 s / 512×466 files are the reference or the owner clip. The 19.98 / 26.48 / 33.85 s files are this round's s1–s5. There is no previous-round clip in the pack.

## 3. Biggest gaps (builder tests)
1. **Strand origin and shot travel (web renderer).** At every press, draw the strand from the palm socket and grow the tip toward the anchor over 4–12 frames at 60 fps. The anchor must be a facade point above and ahead of the hero, never empty sky. Test: on s2 0.8–2.2 s and s1 3.25–3.45 s, the strand start is ≤ 8 cm / ≤ 10 px from the palm, and the visible length grows monotonically over ≥ 4 frames (ref swing-start-from-street).
2. **Swing frequency and arc (swing controller/AI inputs).** The chain must actually swing. Reattach within ≤ 0.5 s of the top of the arc and keep the bottom of the arc above the tree canopy. Test: in s1, web-on ≥ 70 % of frames, no unpowered fall > 0.8 s, and the hero never overlaps tree pixels (ref swing-canyon-chase).
3. **Trick camera (camera rig).** Keep the camera level or below the hero during tricks. Test: hero bbox 0.18–0.36 of frame height and pitch within ±15° on ≥ 80 % of s3 frames, plus a tree/geometry clearance probe (owner clip, last row of samples).

## 4. Secondary
- Release: the strand pops out (s1 1.667 s). It should go slack or retract over 0.15–0.40 s.
- The black/white two-tone strand and the lack of taper (s1 3.5 s).
- Trick limbs switch shape on the same frame, with no arms-lead overlap (F11, s3 0.7–1.8 s).
- The night hero needs a rim light or emissive accents. They are missing in s5, so the hero can't be seen.

## 5. Verdict
**FAILS TARGET**
