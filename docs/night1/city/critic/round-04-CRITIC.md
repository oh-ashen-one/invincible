# P1 City r04 critic (pixels only)

## 1) Scores
- **Facade/building: 5.** S8 brick towers have setbacks, cornices and AC units. S1 ground floors are dark flat slabs with blurred photo storefronts, no fire escapes anywhere, flat windows (S2 left). Ref: `street-avenue-hero-taxis__og_0000`.
- **Street dressing: 3.** S1 sidewalks are bare: no hydrant or newspaper box, clean paving. S5/S6 tree guards hold no trees. Ref: `street-sidewalk-pedestrians__dn_0721`.
- **Rooftops/skyline: 4.** S4 far shore is untextured pastel boxes on white slabs. The river has no bridges. The park is pale lollipop trees. No water towers in S4/S8. Ref: `skyline-perch-dn`, `rooftops-watertowers-golden`.
- **Composition/believability: 4.** S1 is a generic office canyon, and the S4 perch has no landmark. Times Square billboards cover about 40% of facades against every surface in `timessquare-day-trailer__eny_0046`.
- **Image quality: 5.** S8 anti-aliasing is clean. Problems: white clipping on the S4 far shore and S6 curb, low-res storefront photos (S1), flat self-lit red steps (S6), S3 crushed near-black (partly lighting).

## 2) A/B
- avenue-street: A better, by a lot.
- intersection: A better, by a lot.
- swing-height: A better (brick, fire escapes, depth).
- rooftop: B better (A crushed).
- perch-skyline: A better, by a lot.
- timessq-street: A better (billboards on every surface, light spill).
- sunset: B better on city. A has atmosphere but crushed facades.
- aerial: B better, smallest gap.
- progress-aerial: A better, moderately (B shows egg-crate interior cells).
- progress-canyon: A better, clearly (B has blank white panes and mirrored billboard text ghosting).
- Guesses, made after judging: ours are B, B, B, A, B, B, A, A. In the progress pairs, A is newer. **Anonymisation is broken:** references show HUD, hero and a Marvel logo.

## 3) Biggest gap
**Street level (0–3 storeys) is unbuilt.** In S1, rebuild both street walls with a 3D kit:
- recessed storefront bays with mullions and parallax interiors (not blurred photos)
- awnings with legible signs
- brick or stone piers and a 2nd-floor cornice
- fire escapes on at least half of the pre-war facades
- sidewalk slabs with joints and cracks
- per 20 m: hydrant, trash can, newspaper box, tree pit

**Test:** 4K crop of S1 at x0–1600, y800–1700 shows at least 3 signed, awninged storefronts, 1 fire escape and visible slab joints. Target: `street-avenue-hero-taxis`.

## 4) Secondary
1. S4 far shore: use textured grey-brown impostors with window patterns, plus piers and a bridge.
2. Times Square: fill the tree guards, give the red steps real treads, stop white clipping, push billboard coverage above 80%.
3. Roofs in S4/S8: 1–3 water towers per block, plus bulkheads.
4. S4 park canopy: vary species, darken it, show paths.

**Brand:** no Marvel marks. "COLTEX SPORT" (S5) and "COLEX SPOR…" (S6) echo the game's fictional "COLEXCO" (seen in the perch reference). Rename both.

## 5) Verdict
**FAILS TARGET.**
