# Terrain (E) round 4: critic verdict

Homage fan game, not official Marvel, Sony or Insomniac. Numbers are my own, measured on the 4K stills, 4 fps frames and refs `centralpark-meadow-skyline` and `centralpark-aerial-ballfields` (cp_0554). Round-3 scores in brackets.

## Scores

- **Lawn: 4 (4).** p10 has blades and no stars, but is lime: R/G 0.77 vs 0.88 (meadow ref). From the air it is moss noise: p4 σ6 10.85 vs 1.2–1.6 (cp_0554 lawn), and the diamonds are lost. A 490 px pale slab sits in p10 (300–790, 1450).
- **Paths + water edges: 4 (4).** p3 bank rocks unchanged: 22 white blobs (luma > 190, saturation < 0.15), the largest with luma SD 3.3. No clay infields.
- **Shoreline: 4 (4).** The p6 seam remains: luma 93→62 within 50 px at y = 2000. River σ6 2.09; p7 water saturation 0.29 (khaki). Empty esplanades.
- **Trees: 4 (4).** p1 crowns: 9/24 reach σ3 ≥ 9 (r3: 5/24), median 8.1 vs 13–23 (cp_0554), saturation 0.52. Saucer cards float in p10 (≈2280, 490). No tree shadows on the lawn.
- **Overall: 3 (3).** The t5 tail now flies over the park, but the reference wins every pair, and I preferred the old build in 4 of 5 progress pairs.

## Checks

- **a) PASS.** p4 σ6 10.85, saturation 0.874; p10 σ6 11.25, saturation 0.930; guard boxes 11.57 / 9.97 / 8.99, saturation ≥ 0.916. p10 yellow-pixel share fell from 1.21 % to 0.26 %.
- **b) PASS.** The blankets are woven. Flag: at 1.0 s and 4.5 s the t4 camera passes through untextured trunks 320–460 px wide.
- **c) PASS, marginal.** Hero 21–41 m over the park. Lawn σ3 5.4–8.4 over 11–15 s, but 2.6 at 10.5 s.
- **d) PASS.** No canopy regression.
- **e) PASS.** [4, 4, 4, 4, 3] equals r3.
- **f) INVALID.**
  - The raw `_perf.json` records no GPU utilization or contamination.
  - These are capture runs, not `gpu_slot perf` runs.
  - The r03 re-run read 169 / 113 ms against the 161 / 92 baseline.
  - r04 reads 165–169 / 102–104 ms, so p10 would be +10–14 % even if valid. No credit.

## A/B (decided before identity)

- **Views:** south B, reservoir A, pond B, great-lawn A, panorama B (the two views don't match), lawn-eye A, shore-west B, shore-east B, piers A.
- **Motion:** sprint B, avenue A.
- **Progress:** south A, reservoir A, lawn-eye B, great-lawn B, panorama B; both shores tie (identical).
- **Identity guessed afterwards:** the reference won 11/11. I preferred the newer build once in 5.

## Biggest gap

Make the crowns lit leaf volumes that cast shadows. Test:

- All 24 p1 crown crops σ3 ≥ 9, median ≥ 12.
- Crown saturation ≥ 0.65.
- No floating cards in p10.
- Each isolated p4 tree casts lawn shadow at ≤ 0.6× the lit luma.

## Secondary

1. **Aerial lawn:** structure (stripes, shadows, infields) instead of noise. Test: p4 σ6 ≤ 5 while p10 stays ≥ 8; p10 R/G 0.85–0.95. This conflicts with E1's p4 threshold of ≥ 8.
2. **Water:** no p6 seam (luma step < 8 across 50 px); river σ6 ≥ 15.
3. **Bank rocks:** textured grey, luma SD ≥ 12 inside each.
4. **t4:** trunk bark and collision.

## Brand flag

A t5 storefront at 5.5 s reads "THE PA… / SEAFOOD". It is generic and belongs to the city piece. No logo in the terrain.

## Verdict

**FAILS TARGET.** Lowest score 3.
