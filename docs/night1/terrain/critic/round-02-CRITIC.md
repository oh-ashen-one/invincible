# Terrain (E) round 2: critic verdict

Homage fan game. Not official Marvel, Sony or Insomniac; no affiliation. Axes are SPEC E5. All numbers are my own measurements, taken on `round-02/stills` and on 4 fps frames. Round-1 scores are in brackets.

**Scores**
- **Lawn / ground cover: 4 (3).** The lawn is greener (G/R 1.12–1.40), but saturation is 0.46–0.64 against 0.80–0.83 on `centralpark-meadow-skyline`. E1 fails: 6 of 7 boxes score 1.33–6.09. E2 is unchanged at 89.90 %. p10 tufts are yellow star sprites. A pale lawn quad sits in t4 at 9.5 s (about 580×150 px, luma 172 against 101).
- **Paths + water edges: 4 (4).** The p2 Reservoir is good. The p3 bank rocks are still white lumps (luma 167 against 83 for the lawn, saturation 0.15).
- **Shoreline: 4 (3).** The seawall and railing run across 100 % of p7 and about 80 % of p6. The river is dead flat: p6 high-pass SD is 0.37 at luma 35, against 25.6 on `waterfront-og`. The esplanade is empty, with SD 5.5–5.8 against 15.5.
- **Trees / canopy: 3 (2).** The 165–520 m band is faceted, camo-blotched boulders. In p10 they float above the tree line with facets about 130 px long. E8 fails: 14 of 24 crowns score under 9 (minimum 5.4).
- **Overall: 3 (3).** In t5 at 13.25–14.0 s the park-edge ground is flat grey (σ3 SD 1.63–1.73).

**A/B (decided before guessing identity)**
- The reference-quality side wins all 11 view pairs: south-high B, reservoir B, pond-woods A, great-lawn B, panorama A, lawn-eye A, shore-west A, shore-east B, piers A, lawn-sprint A, avenue-park A.
- Progress: park-south B, reservoir B, lawn-eye A. The other lawn-eye side has hull blobs and a brown lawn.

**Biggest gap.** Replace the `trees-*-crown` band (165–520 m) with clustered leaf-card canopies shaded like the near band.

Test: all 24 `p1_south` crown boxes must have σ3 SD ≥ 9. No crown silhouette in `p10_lawn_eye` may have a straight edge longer than 40 px.

**Secondary**
1. Lawn: E1 ≥ 8 and saturation ≥ 0.70. Use blade clumps instead of the star sprites. Remove the t4 quads.
2. River: σ6 SD ≥ 4 and luma ≥ 55 in p6/p8.
3. Bank rocks: textured grey schist, with luma no more than 1.3 × the lawn.
4. t5 at 13–15 s: ground σ3 SD ≥ 5.

**Brand flag.** A t5 billboard reading "POP THE SUMM…" appears at about 6.5 s. It belongs to the city piece; check it.

**Verdict: FAILS TARGET.** The lowest score is 3.
