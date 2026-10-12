# P2 Characters, round 07: blind critic (Opus 5.5)

Homage fan game, not affiliated with Marvel, Sony or Insomniac. Coordinates are native 4K.

## Scores
| Axis | Score | Evidence |
|---|---|---|
| Hero model & suit | **4** | `hero_face_lens_4k` is unchanged: the right lens sits outside the head, with a background gap at (3250–3300, 900–1250). Web lines stair-step. **IP:** the Advanced-Suit layout is still copied. |
| Hero animation | **5** | CH6 met: bob 3.51–3.61 Hz. CH2 met: chase 0.41–0.45H. There is no start, stop, turn or idle; every clip is a loop. |
| Enemies | **5** | The fight is unchanged (PSNR 38.7 dB vs r06) with 0 knockdowns. Collar shards remain at (1745–1800, 1345–1520). Lips show through the tee mask. |
| Civilians | **5** | The walkers now pass at clear depths (`crowd_avoidance_demo` 2.5–3.4 s). Density is 10–14 people, under the busy 16–25. The rear foot still lifts 17–23 % of stature. |
| Image quality | **5** | CH18 met: 0 green interior pixels in all 4 key stills, and the triangle is gone. Shoe shards of 29 and 19 px remain. Clips are 1080p. |

## A/B decisions
- hero-run: **B**.
- hero-chase: **A**.
- hero-standing: **B**.
- suit-close: **A**.
- hero-face: **B**.
- thugs-group and fight-clip: **A**.
- thug-close: **A**.
- citizens-clip: **A**.
- citizens-still: **B**.
- progress-crowd-clip: **A**. B passes the hoodie through the coat at 0.5–0.75 s.
- progress-crowd-still: **tie**. Both have fused heads.
- progress-key-a: **B**.
- progress-key-c: **A**.
- progress-avoid: **A**.
- jeans-leg, overlap-near, ankle-close and floating-shape: **A**. The B side has green tint, touching heads, a cuff sliver and the triangle.

## Single biggest gap
Replace the copied suit layout with an original one. Rebuild each lens as one closed rim sealed to a lens that sits inside the head silhouette.

Re-capture `hero_face_lens_4k` and check it at 3× crops:
- 0 background pixels between rim and lens;
- no lens beyond the mask outline;
- no web-line stair step wider than 2 px.

## Secondary issues
1. Cap rear-foot lift at 12 % of stature.
2. Keep at least 0.5 m of personal space. In `crowd_tracking_4k` two heads are fused at (1440–1560, 850–920).
3. Remove the thug collar shards, and add hit reactions and knockdowns.
4. Remove the shoe shards so no component is over 4 px. Raise density to at least 16 people.

## Verdict: **FAILS TARGET**
Lowest axis: 4.
