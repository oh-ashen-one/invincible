# P2 Characters, round 05: blind critic (Opus 5.5)

Homage fan game, not affiliated with Marvel, Sony or Insomniac. Every capture is on the flat test stage, so lighting is not judged here.

## Scores
| Axis | Score | Evidence |
|---|---|---|
| Hero model & suit (CH1/3/4/5) | **4** | The weave is now fine (about 6 px pitch in `suit_closeup_4k`), but the web lines are only faintly raised. In `hero_face_lens_4k` (x≈2930–3010, y≈560–1100) the right lens rim is doubled and floats, with a mask-coloured gap between rim and lens. The head is egg-shaped. **IP:** the Advanced-Suit layout (white long-leg emblem, blue legs with red stripes) is unchanged from r04 and breaks the SPEC header rule. |
| Hero animation (CH6/7/9/10 + §5) | **5** | CH6 met: 3.50 Hz in `hero_run_side` and 3.51 Hz in `hero_run_chase`. CH7 met: lean is 27° on `hero_run_side_4k`. CH2 met: chase median 0.42H. CH10 met: the leap now crouches for 0.20 s (f78→f90) before a split-leg air pose. The two leaps (f84 and f240) are the same take. There is no start, stop or turn. CH9 can't be measured on the untextured ground. |
| Enemies (CH11–14) | **5** | CH11/12 met: 7 thugs at 0.23–0.40H (`street_fight_34_4k`), with bat, pipe and pistol. Faces have real eyes, but the masks are shrink-wrapped: lips show through on `tee_face_4k`. Hair has faceted cards and a scalp patch (`beard_face`) and a two-tone seam (`hood_face`). The hoodie collar has black shards (`thug_face`). In the fight, thugs shuffle on guard for 8 s with no hit reactions and no knockdowns. |
| Civilians (CH16/17/19) | **4** | Hand count on `crowd_tracking` gives 11, 9 and 11 people at 1, 4 and 7 s. That is inside 8–25 but below the busy 16–25. The nearest walker is 0.60H, and people now walk both ways. At 7 s the black-tee walker passes through the beanie man. Walkers hold their arms out about 30°. |
| Image quality (CH5/18) | **3** | CH18 fails. In `crowd_key_a_4k` the green key shows through the black-tee armpit (244 px, x413 y1167; 3× crop confirms). In `crowd_tracking_4k` (x≈2950–3350, y≈1300–1750) the olive coat is shredded into spikes and the fingers are claw-stretched. The trousers have spike vertices. Stills are native 4K; clips are 1080p. |

## A/B decisions
- hero-run: **B** is better. It has contextual motion and vaults; A is a looped cycle on an empty stage.
- hero-chase: **A** is better. B is a small, identical cycle.
- hero-standing: **A** is better. B has an awkward mid-stride pose and the copied suit.
- suit-close: **B** is better. It has a sheen hex weave and raised lines; A's lines are painted.
- hero-face: **A** is better. B has floating, doubled rims and halo-blurred lines.
- thugs-group / fight-clip: **A** is better. It has reactions, knockdowns and FX, where B punches air.
- thug-close: B's face beats A's blurry frame, but its collar is broken. Overall **A**.
- citizens-clip / citizens-still: the ref side is better (density, props, variety).
- progress-crowd: **A** (newer) is better: near-camera, bidirectional walkers.
- progress-run: **B** (newer) is better: no duplicate hero, crisp limbs.

## Single biggest gap
**CH18 plus garment integrity.** Rerun the green-key capture (`crowd_key_*_4k`) and require three things:
- zero enclosed key pixels inside any torso or sleeve silhouette;
- no vertex spikes longer than 5 px outside the cloth hull on the coat, trousers or hoodie collar in `crowd_tracking_4k` and `thug_face_4k`;
- no stretched fingers.

Prove it with 3× crops of the same regions.

## Secondary issues
1. Replace the Advanced-Suit layout with an original design (IP). Rebuild the lens rim as one closed rim that seals against the lens.
2. Add crowd avoidance so no two walkers overlap for more than 0 frames. Lower the arms to hang at 5–10°.
3. Fight: each landed hit plays a stagger or knockdown, and downed thugs stay down.
4. Masks need drape, not skin conformity (no lip read). Hair needs no faceted silhouette.

## Verdict: **FAILS TARGET**
The lowest axis is Image quality at 3.
