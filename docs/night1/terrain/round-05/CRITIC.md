# Terrain (E) round 5: critic verdict

Homage fan game, not official Marvel, Sony or Insomniac. My own measurements: 4K stills, t4/t5 frames at 4 fps, refs cp_0554/cp_0605 at 2x. Round-4 scores in brackets.

## Scores
- **Lawn 4 (4):** p10 R/G 0.920, but chartreuse (saturation 0.917 vs 0.84 on the ref). A 287 px pale slab sits at (449,1439). p4 σ6 5.48 vs 0.4–2.1 on the ref.
- **Paths + water edges 4 (4):** p3 rocks are smooth olive eggs (hp3 SD 0.75–0.90). Infields are faint.
- **Shoreline 4 (4):** the p6 seam stays (89→67 within 25 px at y=2000). Water is khaki (82,76,47), σ6 3.7. Esplanade trees cast no shadows.
- **Trees 5 (4):** crowns read as leaves: 19/24 at σ3 ≥ 9, median 12.06 (r04: 9/24, 8.1).
- **Overall 3 (3):** golden light, but nothing shadows the ground. The reference won 11/11.

## Checks
- **a) FAIL.** 19/24 pass. Below 9: (1500,1950) 6.11, (2250,1800) 7.12, (3450,1200) 8.14, (2400,1650) 8.25, (2100,1950) 8.34.
- **b) FAIL.** Median saturation 0.636.
- **c) FAIL.** No straight edge ≥ 30 px. A smooth hull ball floats at (1125–1200, 235–295): hp3 SD 3.4 vs 12.9 on the leaves.
- **d) FAIL.** Tree (3005,1100) 0.71× the lit luma. Tree (3040,1078) 0.62×. Only the pair at (2900,1060) passes (0.51×).
- **e) PARTIAL.** p10 σ6 18.68, guard 16.31, R/G 0.92/0.94. p4 σ6 5.48 > 5.
- **f)** b PASS (0.700–0.95). c marginal: blankets woven, but a 360 px trunk is untextured (hp3 SD 1.1, 0.75 s). d FAIL: σ3 < 5 at 11.0–11.5 s and 14.75–15.25 s.
- **g) PASS:** [4,4,4,5,3].
- **h) PASS:** new build preferred 5/5.
- **GPU ms:** not credited.

## A/B (decided before identity)
- **Views:**

| South | Reservoir | Pond | Great-lawn | Panorama | Lawn-eye | Shore-west | Shore-east | Piers |
|---|---|---|---|---|---|---|---|---|
| B | B | B | A | A | A | B | B | B |

- **Motion:** sprint B, avenue B.
- **Progress:** south B, reservoir B, lawn-eye A, great-lawn A, panorama B (marginal).
- **Pack:** 1612 vs 3226 px widths leak identity.

## Biggest gap
Trees must cast sun shadows on the lawn and paving. Test:
- p4: trees (3005,1100), (3040,1078) and (2900,1060) each have a 15 px lawn box within 60 px on the anti-sun side at ≤ 0.6× the lit lawn (≈105).
- p6: every esplanade tree shadow ≤ 0.6× the paving luma.

## Secondary
1. No sky-bordered patch in p10 wider than 30 px with hp3 SD < 5.
2. Foreground crowns all at σ3 ≥ 9. Median crown saturation ≥ 0.65.
3. p6: step < 8 per 50 px. Water σ6 ≥ 12 and B ≥ R.
4. Rocks hp3 SD ≥ 5 and grey. No p10 slab. Barked trunks. p4 σ6 ≤ 5.

## Brand
t5 at 7.0 s: an invented "NOVA FOLD" billboard (city piece). No logo in the terrain.

## Verdict
**FAILS TARGET.** Lowest score 3.
