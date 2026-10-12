# P2 Characters — round 01 critic (fresh eyes, pixels only)

Captures: `characters/docs/night1/characters/round-01/captures/` (C/). Refs: `spiderman-learnings/refs/`.

## 1) Scores
| Axis | Score | Evidence |
|---|---|---|
| Hero model & suit | **4** | C/lineup4k_04_t021.jpg: the weave is a coarse knit/corduroy rib, not a fine hex. The web lines are painted black strokes, not raised. The emblem is flat white paint. lineup4k_00: the lenses are flat white decals with no curvature or specular. Compare refs/characters/press-suit-closeup-fire, miles-face-closeup. Silhouette and panel layout are acceptable. |
| Hero animation | **4** | C/hero_run_side_34_hop.mp4 0–5 s: the run is upright with forearms held up (a jog), with little forward lean. At ~5.5–6.0 s the "hop" is a flat Superman dive at knee height that reads as a glitch. ai_suits_walk.mp4: all 5 suits walk in phase-locked sync. Compare refs/animation/clips/run-crosswalk. |
| Enemies | **2** | C/brute_walk_1080.jpg + thug_brute_walk.mp4 4.5–7 s: the brute's texture is scrambled. Skin patches show through the pants on knee and forearm, there are white blotches, the thug's red bandana dot pattern is smeared across its back, and the head is a featureless black blob. Thug (thug_walk_1080): the eyes are flat cartoon decals, the hands are mitten-like, and the walk is a stiff wide-knee shuffle. Compare refs/characters/thugs-group-nm. |
| Civilians | **2** | C/citizens_walk.mp4 2–5 s: the foreground businesswoman glides several metres in a frozen stand pose with no leg motion. At 9–13 s the close-up civilians only stand. The background "pedestrians" are hero-suit clones. At 11 s the construction worker is covered in white shard or crack artifacts (face, vest, jeans). The woman's suit has the same streaks (citizens_wide_1080). Compare refs/characters/clips/street-npcs-idle and npc-group-dn. |
| Image quality | **3** | The shard artifacts and the broken brute texture above. Shadow tails at the feet are dithered and noisy (ai_suits_1080). The 4K weave aliases into moiré (lineup4k_04). The lighting is a test stage, but none of these defects is a lighting issue. |

## 2) A/B decisions (decided on merit)
- hero-run: **B** is better (grounded weight, lean, contextual transitions). A is an upright jog with a dive glitch.
- hero-closeup: **B** is better (raised web lines, curved rimmed lenses, fine micro-weave, correct material split). A is a knit-sweater weave with painted lines.
- citizens: **B** is better (NPCs walk and react, with varied faces and cloth). In A the NPCs stand or glide.
- thug: **A** is better (real anatomy, cloth, face). B is a toy-like decal face.
- walk: **A** is better (planted feet, weight shift, varied NPCs). B is a stiff walk on a bare stage.

Guess: our build is hero-run A, hero-closeup A, citizens A, thug B and walk B.

## 3) Single biggest gap
**Brute enemy: fix the material and UV binding so that every mesh section samples its own texture set.** When the brute walks past in thug_brute_walk.mp4 (4.5–7 s), it must read as one coherent heavy-set street criminal: solid jacket or vest and trousers, no skin showing through clothing, no bandana pattern on the torso, a lit face with a readable head silhouette. It should match `refs/characters/thugs-group-nm__nm_0049.jpg` and `thugs-close-nm__nm_0947.jpg`. Test: at 4K, no frame from 4.5–7 s shows skin-coloured or white patches outside the hands and face.

## 4) Secondary issues
1. Civilians glide in a frozen idle pose (citizens_walk 2–5 s). They need a real walk cycle with foot lock, and the close-up NPCs must move.
2. White shard or crack artifacts on the construction worker and the businesswoman (citizens_walk 11 s): bad normals, tangents or a broken seam.
3. Hero lenses and web lines: give the lenses curved, glossy inserts with a thick rim. Make the web lines raised geometry or a normal map. Reduce the weave scale about 4x (press-suit-closeup-fire).
4. Hero run: add a 10–15° forward lean and a full arm swing. Replace the knee-height dive "hop". Desync the AI-suit walk phases.

## 5) Verdict
**FAILS.** The lowest axes are 2 (enemies, civilians), and no axis is at 8 or above.
