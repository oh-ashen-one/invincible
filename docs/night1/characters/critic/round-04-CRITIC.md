# P2 Characters, round 04: blind critic (Opus 5.5)

Our captures are in `.../round-04/captures/`. The references are the `refs/characters/*` stills, `animation/clips/run-crosswalk`, and the ref clips in the pack. The lighting is a flat test stage. I say so wherever lighting affects a finding.

## Scores
| Axis | Score | Evidence |
|---|---|---|
| Hero model & suit (CH1/3/4/5) | **4** | The knit is chunky, like a sweater: each rib is about 25 px tall in `suit_closeup_4k`, where the ref has a fine sheen weave. The web lines are painted flat, wobble, and are not raised. The lenses in `hero_turntable_4k` are flat white discs with no specular highlight or curvature. The panel edge is sawtoothed at `suit_closeup_4k` (≈860–920, 1760–1840). CH1 and CH2 are unproven because no clip uses a gameplay chase camera. **IP flag:** the suit copies Insomniac's PS4 "Advanced Suit" (white long-leg spider, blue legs with red stripes). This breaks the SPEC header rule. |
| Hero animation (CH6/7/9/10 + §5) | **5** | CH6 is met: bbox-height oscillation is 3.53 Hz in `hero_run_side` and 3.40 Hz in `hero_run_jump_side`. CH7 is met: lean is 29–33° at frames 75, 105 and 135 (gridded hand-read). The jump fails. In `hero_run_jump_side` f96→f104 (0.13 s, under CH10's 0.15 s), the torso snaps from about 30° to vertical into a straight-legged, arm-up pose, and both jumps are identical. There is no start, stop or turn, and none of the §5 clips exist. CH9 can't be measured because the ground is untextured. `hero_jump_4k` has the hero outside the frame. |
| Enemies (CH11–14) | **4** | CH13 is met, just: 7 thugs, weapon types bat, golf club and cleaver. Thugs #1 and #6 are near-twins (same head, sunglasses, green mask and cargos). In `enemy_lineup_wide_4k`, 5 of 7 heads crane up to the sky. The masks are shrink-wrapped, so the brute's lips and chin show through the cloth (`brute_face_4k`). The hoodie shoulder silhouette is faceted (`hood_face_4k` ≈770–880, 1770–1940). The pipe and golf clubs are untextured grey. CH11 and CH12 are unproven because there is no fight capture. |
| Civilians (CH16/17/19) | **3** | The YOLO median in `civilians_tracking` is 11 people, below the busy-sidewalk median of 16–25. The crowd walks single file, all in one direction, bunched up and overlapping. Tallest person is 0.29H, the ref's is 0.71H, so nobody comes near the camera. |
| Image quality (CH5/18) | **3** | CH18 fails. I found 26 thin background-coloured slivers on 8 dark-clothed walkers in `civilians_tracking_4k`, and native crops confirm the wall showing through the suits and hoodie (see the zoomed crops). There is a tear on the green mask (`hood_face_4k`). The stills are native 4K, but the clips are 1080p. |

## A/B pack
- **hero-run:** A (the ref) is better. B is ours, with smeared limb blur and a duplicate hero walking in frame at 0.05 s.
- **thugs-group:** A (the ref) is better. Ours is a static lineup with heads craned up.
- **thug-close:** A (the ref) is better. Ours shows mask tears and faceted jacket geometry.
- **citizens:** B (the ref) is better. It has people near the camera and bidirectional flow.
- **progress-run** (ours vs ours): **B is newer and clearly better.** Lean is about 30° in B against 9–13° in A (f30, 60, 90; A fails CH7), with more arm swing.
- **progress-citizens** (ours vs ours): **B is newer and better.** Median is 10 people per frame in B against 2 in A. A is sparse, with one idle woman and hero-suited walkers in the background.

## Biggest gaps, ranked
1. **CH18 seam cracks on civilians.** Test: rerun the thin-sliver count on `civilians_tracking_4k`; it must be 0. Also check the orange and white wall showing through dark suits.
2. **Suit (CH4 plus the IP rule).** Replace the Advanced-Suit layout with an original design. Test with a 4K closeup against `press-suit-closeup-fire`: the weave must be fine and not visible as rows at 1 m; the web lines must be raised with a specular edge; the lenses need curvature and a highlight.
3. **Enemies as combatants (CH11/12/14).** Add a fight capture with 5–7 enemies around the hero, each 0.16–0.60 of frame height. Fix the head look-at so no head is pitched up more than 10°, and give the masks drape instead of skin conformity.

## Secondary issues
- Re-author the jump take-off: it needs at least a 0.15 s blend, a forward lean, and a tucked or split leg pose.
- Swap the untextured grey weapons and one twin of the thug #1/#6 pair.
- Retake `hero_jump_4k` so the hero is in frame, and remove the duplicate hero instance from the capture scenes.
- The crowd needs a bidirectional flow and walkers passing within 0.5H of the camera.

## Verdict: **FAILS**
The lowest axes are Civilians and Image quality, both at 3.
