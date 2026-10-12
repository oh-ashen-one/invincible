# P2 Characters: round-03 critic (blind, pixels only)

Captures dir = `round-03/captures/` (CAP). Test-stage lighting is not scored. Where lighting causes something, I say so.

## Scores
| Axis | Score | Evidence |
|---|---|---|
| Hero model & suit (CH1,3,4,5) | **4** | CAP/hero_turntable_4k.jpg: FFT weave period is 15.5 px on the chest and 8 px on the head, at about 1500 px/m. That is roughly 1 cm cells, a coarse knit jersey, not the ref's micro-hex (press-suit-closeup-fire). Web lines are flat print with no raised relief (hero_suit_fabric_closeup.mp4, whole clip). Lenses are flat white with no specular and a gapped bezel rim. hero_run_34_4k.jpg (2690-2960, 710-900): **white emblem texture bleeds onto the back of the hand, 5 950 px**. CH1/CH3 are unproven because no gameplay framing and no texel data were supplied. |
| Hero animation (CH6,7,10) | **3** | hero_run_side_34_hop.mp4, 0.1–4.0 s side run. Step rate: bob FFT gives 2.93 Hz, and passing frames n72→176 give 5 steps in 104 f = **2.9 steps/s**, below CH6's 3.2–3.8. Head-to-hip lean: **median 7°, max 11°**, below CH7's ≥15° (ref about 30°). Run to full leap takes **6 frames (0.10 s, n240→246)** with no anticipation crouch, below CH10's ≥0.15 s. The "hop" becomes a horizontal belly-dive 0.3 m above the ground (n270–285). |
| Enemies (CH11–14) | **3** | No capture shows more than **2 enemies** (CH11 needs 5–7). There are 2 outfits and **0 weapons** (CH13 needs ≥5 outfits and ≥2 weapon types). brute_face_4k and thug_face_4k: bandanas are flat paper cards with hard polygon edges. They show an obvious tiled circle pattern, clip through the ear, and the nose pokes through a jagged cut. There is a hard scalp/forehead polygon seam, a stair-stepped untextured band under the beanie, and flat black untextured patches on the hoodie. thug_brute_pair_side_4k: the brute sleeve cuff has mis-UV red/green blotches (659 red and 69 green px). Faces and eyes are good (partly meets CH14). The walk cycle is plausible. |
| Civilians (CH16,17,19) | **2** | citizens_walk.mp4 has only 4 civilians in frame (CH16 needs 8–25). The camera is static (building fixed, n180 vs n300). **The woman in the orange dress glides about 560 px in 2 s with both legs straight and together (n180→300)**, and the hard-hat worker glides too. Both violate CH17's 0-gliders rule. The background "walkers" are 5 hero-suit clones, not civilians. |
| Image quality (CH5,18) | **4** | Stills are native 3840×2160, so CH5 is met. CH18 fails on 6+ defect types (listed above), plus white streak sparkles on the woman's jacket (citizens_walk @5 s). Heavy motion blur smears the hero in the side run. |

## A/B
- thugs-group: **A better** (ref: 5 enemies, crowbar, bat). B = ours (2 walkers, no weapons).
- thug-close: **B better**. A = ours (paper mask, ear clipping).
- thugs-close-2: **A better** (ref: pistols, varied outfits, grounded).
- hero-run: **A better** (ref: strong lean, crouched gait). B = ours (upright).
- citizens: **B better** (ref: dense crowd, walking). A = ours (static and gliding).
- progress-enemies: **A is clearly better**, by about +2.5 on the enemy-model sub-score. A has scanned denim, leather seams and real boots. B is flat-shaded untextured with mitten hands and block shoes. I take A to be the newer version (round-03). Both versions crop the head out of frame.

## Single biggest gap
The hero run fails CH6, CH7 and CH10 at once, and the hero is on screen 100% of the time. **Test:** re-run the side-run capture with the hop removed. It passes when bob FFT or passing-frame count gives **3.2–3.8 steps/s**, head-to-hip lean has a **median ≥15°** on every frame from 0.5–4 s, and the run→jump pose change spans **≥9 frames at 60 fps** with a visible crouch.

## Secondary
1. Enemy masks: model them as skinned cloth that conforms to nose and chin with no ear clipping, replace the tiled pattern, and fix the beanie band and hoodie flat patches (CH14, CH18).
2. Enemy lineup: ≥7 enemies, ≥5 silhouettes, ≥2 weapon types, 0.16–0.60 height (CH11–13).
3. Civilians: ≥8 per frame, every mover drives foot bones (0 gliders), ≥6 distinct models, no hero clones as crowd (CH16–17).
4. Suit: fix the hand UV bleed, add lens specular/curvature, and move to a finer weave with raised web lines (CH4).

## Brand/IP flag
The hero suit is a near-copy of a studio-owned suit: elongated white spider wrapping the shoulders, blue flank panels, red leg stripe, red belt band. SPEC says the suit "must not copy a studio-owned suit design". ai_suits_walk also shows the franchise's alternate suits. The owner must decide. No copied logos or text were seen.

## Verdict
**FAILS.** Lowest axis is 2 (civilians), and no axis reaches 8.
