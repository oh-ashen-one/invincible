# CRITIC — P4 LOOK, round-01 (pixels and motion only)

## 1) Axis scores
| Axis | Score | Evidence |
|---|---|---|
| Sun/sky/TOD | 5 | golden_S4/S8 have a believable warm haze, but golden_S1 is lit cool grey at street level with no warm key. The midday_S4 horizon band is darker than the sky above it. |
| GI & shadows | 3 | night_S1 has 85% of pixels below 10/255 (ref swing-night-canyon__nt_0221: 0.3%). In swing_midday.mp4 at about 0–2 s, the shaded facade in the left foreground is near-black with no bounce. |
| Atmosphere & depth | 4 | golden_S7 and golden_S4 have real inscatter. In the midday_S4 4K top band, the far shore is a white slab and the far city is saturated violet with no contrast loss (ref midday-perch B). |
| Reflections & materials | 3 | In swing_midday.mp4 at about 8 s, the centre glass panel is pure black. No wet or specular street at night. The golden_S2 gold tower is the only convincing reflection. |
| Post & exposure | 3 | golden_S7 clips 4.7% of pixels to white in a sun column that swallows the canyon. The golden_S1 road centre has a green lens-ghost blob with no source. Night mean luma is 9/255 against a ref mean of 42. |
| Night look | 2 | night_S1/S6 have no lamp pools and no car lights. In the night swing clip the hero is invisible. Window variety is the only pass. |

## 2) A/B decisions
- **midday-canyon:** A is better. It has warm bounce, a populated street and lit windows; B is flat and empty.
- **midday-perch:** B is better. It has layered aerial perspective; A has a white slab shore and a violet far LOD.
- **golden-canyon:** B is better. It has warm glare with filled shadows; A is grey fog that doesn't read as golden.
- **golden-skyline:** B is better. It holds cloud and facade detail; A blows out.
- **night-street:** B is better, by a mile.
- **night-above:** A is better. It has a dense lit grid, emissive signage and street glow; B reads as a moonlit dusk with a dead street grid.
- **golden-swing-clip:** B is better. It has a sun disc, water glitter, clouds and speed blur; A has neutral haze and grey trees.
- **night-swing-clip:** A is better. B is a black canyon with the hero lost.
- **progress-canyon (ours vs ours):** A is better by about 1 point on axes 1–3. It has a sunlit left facade with a soft terminator, deeper distance haze and readable foliage. B has the whole left wall in shade, which reads flat. B is identical to round-01 midday_S2.

## 3) Single biggest gap
**Night street lighting and exposure.** On the night preset, views S1 and S6 plus swing_night:
- Add street-lamp pools: sodium and LED lamps with falloff every 25–30 m on both sides.
- Add storefront emissive spill onto the sidewalks.
- Add car head- and taillights.
- Lift the ambient/sky fill so building silhouettes read.

Reference: traversal/swing-night-canyon__nt_0221 and streets/night-street-2__nt_0715.

**Tests:**
- night_S1 mean luma is at least 35/255, and at most 3% of pixels fall below 10/255.
- The bottom third of night_S1 shows at least 4 distinct pools, each peaking at 120/255 or more and dropping to 40/255 or less between pools.
- The hero's bounding box has mean luma of at least 40/255 in every frame of swing_night.

## 4) Secondary issues
1. **Golden hour is missing at street level.** golden_S1 is cool grey, and the green ghost sits at 4K crop x1500–2300, y900–1600. Fix: add a warm key or bounce fill and remove the ghost. Target: golden-canyon B.
2. **golden_S7 blowout.** Target: clipped pixels at or below 0.5%, with facades still readable inside the sun column.
3. **Dead glass.** Glass panels go black mid-swing, and night glass doesn't pick up city lights. Needs reflection captures or Lumen reflections on curtain walls, plus a damp-asphalt specular term at night.
4. **Midday far field.** Needs height-fog tinting that desaturates the far LOD and lifts it toward the sky colour. The horizon must come out brighter than the zenith.

## 5) Verdict
**FAILS.** Every axis is below 8, and night lighting and post/exposure are at prototype level.
