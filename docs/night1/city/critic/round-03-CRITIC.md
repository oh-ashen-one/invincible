# CITY critic, P1 round 03 (judged on the images only)

## 1) Axis scores
- **Facade and building fidelity: 4.** The brick, stone banding and setbacks in S8 hold up. But almost every window is an opaque beige or white slab with no reflection, frame depth or interior. You can see this in the S1 crop `c_S1_facade`, S2 and S7, and in the ground-floor storefronts of `c_S1_storefront`, which are blank lit panels. Compare `street-avenue-hero-taxis__og_0000`, where the glass is dark and reflective and the frames are deep.
- **Street-level dressing: 3.** The street trees are now good, with textured leaves, grates and pits. Everything else is thin. There are no fire escapes, awnings with signage, hydrants or newspaper boxes to read, and the pavement is clean. The storefronts are empty, and the Times Square plaza (S5, S6) is sparse, with isolated benches and umbrellas. Cars are missing too, but that belongs to another piece.
- **Rooftops and skyline: 4.** The near roofs are dense (HVAC, water towers in S3 and S4). The far shore in `c_S4_farshore` is a problem. It is built from lavender, untextured, extruded boxes sitting on a blown-out white shoreline band. The river is flat milky glass, and there are no bridges or piers with any detail. The park canopy is acceptable at distance but uniform.
- **Composition and believability: 4.** S4 does read as Manhattan (park, river, towers), and S5 reads as Times Square. S8 does not: it shows a mass of glass towers with no street in view, and could be any downtown. The avenue in S1 is uniformly tree-lined and generic, where the reference avenues are lined with brownstones and pre-war buildings.
- **Image quality: 4.** In S5, the top-right corner holds a large untextured black mass (`c_S5_topright`). The shoreline strips in S4 are clipped to white. The windows across all shots are flat planes. Anti-aliasing is clean.

## 2) A/B decisions
- avenue-street, swing-height, rooftop, perch, park, timessq-street, sunset, aerial: **the reference wins every pair, by a large margin.** Its facades carry real material and depth, its window glass is dark and reflective, its streets are dense, and its far city has detail. My guesses at which image is ours: A, A, B, A, B, B, B, A.
- **progress-street: A is better, by a large margin.** B has grey, untextured, card-like foliage and untextured cones and barrels.
- **progress-perch: A is better, by a moderate margin.** In B the park canopy is grey untextured blobs. The rest of the frame is identical.

## 3) Single biggest gap
**The window glass.** Every glazed opening must stop rendering as an opaque beige or white plane. That covers the tower curtain walls in S1 (right third), S2 (left tower), S7 (both walls) and S8 (the brick towers), and the storefronts in S1 and S5.

The fix needs three things:
- **Reflective glass.** Dark glass that reflects the sky and nearby buildings (Fresnel), with roughness varying from pane to pane.
- **Real frame depth.** Recessed frames and sills that throw a contact shadow.
- **Interiors.** Interior mapping with varied blinds and lit or dark states, in roughly a 60/30/10 mix.

Storefronts need visible interiors: shelving, signage, people-scale props.

**Test:** in a 400 px crop at 4K of the S1 right facade and the S8 brick tower, no more than 10% of window pixels may be above 80% luminance in daylight.

**References:** `street-avenue-hero-taxis__og_0000` and `street-federal-hall-intersection__dn_1038`.

## 4) Secondary issues
1. **Far shore (S4).** Replace the lavender boxes and the white shoreline with textured distant blocks, a darker waterline, piers and bridges. See `river-queens-aerial__gr_0936` and `skyline-queens-aerial__gr_0033`.
2. **Black mass in S5.** Remove or texture the black occluder at the top right of the frame.
3. **Street clutter (S1, S5, S6).** Add fire escapes, awnings, hydrants and newspaper boxes, and add wet patches and cracks to the pavement.
4. **Billboard art copied from the reference.** Billboards in S5 and S6 reuse art from the reference ("FROSTED HALOS", "BOTANICA", "Hotel Mira"). The refs must not be copied into the public fork, so this art has to be replaced with original work.

## 5) Verdict
**FAILS** (lowest axis: 3, street-level dressing).
