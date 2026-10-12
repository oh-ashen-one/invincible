# P2 Characters, round 06: blind critic (Opus 5.5)

Homage fan game, not affiliated with Marvel, Sony or Insomniac. Flat test stage, so lighting is not judged. Coordinates are native 4K.

## Scores
| Axis | Score | Evidence |
|---|---|---|
| Hero model & suit (CH1/3/4/5) | **4** | `hero_face_lens_4k`, right lens (x≈3140–3240, y≈700–1500): the rim is still doubled, and background shows between the rim and a floating lens sheet. Left lens: the rim splits at the top corner (x≈1650–1700, y≈760–800) and a white lens sliver pokes through. Mask web lines stair-step. **IP:** the Advanced-Suit layout is unchanged (SPEC header). Ref: miles-face-closeup. |
| Hero animation (CH6/7/9/10) | **5** | CH6 met: 3.52 Hz side, 3.50 Hz toward, 3.60 Hz 3/4. CH7 met: about 24° hip→neck on `hero_run_side_4k`. CH2 met: chase 0.42H at 2.0 s. Leap: crouch 1.40–1.60 s, a low hop 1.67–2.07 s. There is still no start, stop or turn, and every clip is a constant-speed loop. |
| Enemies (CH11–14) | **5** | CH11–13 met in `street_fight_34_4k`: 6 thugs at 0.23–0.39H, pipe plus bat, 5 silhouettes. Faces are scan-quality, but lips still read through the `tee_face` mask. `thug_face_4k` has a collar card shard (x1750–1960, y1340–1640), unchanged from r05 (collar-close A and B are identical). In the 8 s fight there are 2 pipe swings (0.25–0.75 s and 6.5–7.0 s), no knockdowns, and the hero kicks air at 1.25 s. |
| Civilians (CH16/17/19) | **4** | Hand count on `crowd_tracking` gives 10, 8 and 8 people at 1, 4 and 7 s, below the busy 16–25. The coat walker's rear foot flicks to knee height every stride (4.0 s, 7.0 s). Walkers interpenetrate: beanie man through the coat woman in `crowd_key_c_4k`, and black-tee's head inside the hoodie in `crowd_key_a_4k`. |
| Image quality (CH5/18) | **4** | Better than r05: the coat, hand and armpit are clean in `crowd_tracking_4k` and `crowd_key_a_4k`. CH18 still fails: in `crowd_key_c_4k` the rear jeans leg (x3215–3345, y1745–1940) is key-green (0,85,0), 19.5k of 25.4k px. A detached 37×27 px black triangle floats at (2225–2261, 1190–1216) in both key-c versions. Clips are 1080p. |

## A/B decisions (judged before identity)
- hero-run: **B**. It has starts, a crouch and a vault; A is a loop.
- hero-chase: **A**. It has traffic, a sprint and a launch; B is a small identical cycle.
- hero-standing: **A**. It has a grounded idle; B holds a mid-stride and uses the copied suit.
- suit-close and hero-face: **B**. It has a hex weave, raised lines and sealed rims.
- thugs-group and fight-clip: **B**. It has reactions, knockdowns and FX.
- thug-close: **B**. The face is readable, but the collar shard is visible.
- citizens-clip and citizens-still: **ref side** (density).
- progress-crowd-still, coat-close, hand-close, armpit-close: **B**. A is shredded, clawed or holed.
- progress-key-a: **A**. B has a coat flap spike.
- progress-key-c, collar-close, progress-run, progress-crowd-clip: **tie**. Both have the same defects.

## Single biggest gap
**Crowd separation plus the key see-through (CH17/18).** Add walker avoidance with a capsule radius of at least 0.35 m. Then re-capture `crowd_key_c_4k` and `crowd_key_a_4k` and pass three checks:
- zero pixels with G>R+40 inside any garment silhouette;
- no two walker masks overlapping for more than 0 frames across `crowd_tracking` at 60 fps;
- no detached polygon larger than 4 px anywhere.

Prove it with 3× crops.

## Secondary issues
1. Rebuild the lenses as one closed rim that seals to the lens, with no visible background. Replace the Advanced-Suit layout (IP).
2. Delete the collar card shard on the hoodie thug. Masks should drape, so no lip read. Blank the illegible "SLI…" label.
3. Fight: every landed hit should stagger or knock down, and downed thugs stay down.
4. Cap the walk rear-foot lift at shin height, and raise density to at least 16 people in frame.

## Verdict: **FAILS TARGET**
Lowest axis 4 (hero model, civilians, image quality).
