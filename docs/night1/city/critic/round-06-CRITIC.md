# P1 City critic, round 06 (blind, pixels only)

## Scores (reference: Marvel's Spider-Man 2)
**1. Facades & buildings: 5.** Good typology mix: pre-war brick with setbacks, limestone, curtain wall, gold glass, fire escapes (S2, S8). Fails **C1**: S2 limestone (150,100–600,900) has 21.6% of pixels >204 (p95 226). S8 glass tower (1270,350–1600,1000) has 16.5%, S8 tower (370,300–560,700) 7.5%, S6 (1100,0–1400,340) 49%. Target is ≤1.5%. Fails **C2**: S1 facades average 21–37 and S8 averages 129–142 (target 52–119). **C3** is weak: window interiors are thin. S1 repeats one shelf texture in 4 shop windows, and S7 windows read as flat pale tiles.

**2. Street dressing: 4.** **C7** passes: ≥3 trees on the right side, ≥2 signed storefronts on each side, a traffic light, a hydrant, trash cans, planters and a scaffold shed. The left side has no trees. **C4**: 0 parked cars and 0 taxis in S1 (target 5–19). **C6**: 0 vehicles in the near and mid avenue in S2 (target 14–22). Pavement is clean, with no cracks or wet patches.

**3. Rooftops & skyline: 4.** **C9** passes in S3 (two towers). S4 rooftops are dense with AC units. S3's roof plane is sparse. S4 far field fails every line:
- **C11**: far/sky Laplacian 4.8× (target ≥6×).
- **C13**: far shore −10.9 below sky (target −25 to −35).
- **C14**: river only 2 below far shore (target 5–35).
- **C15**: RMS far/near 0.09 (target 0.25–0.45).

The far shore is untextured box extrusions.

**4. Manhattan composition: 5.** It reads as New York: park edge, piers, a Grand Central-like terminal, Times Square steps and plaza. **C12** passes (+9.6 vs sky +11.9). The city is empty.

**IP flags:**
- S6 ≈(1270,210): "SEE SOMETHING? SAY SOMETHING." is the real MTA slogan.
- S5/S6 "NEO RACER … OUT NOW" copies racing-franchise key art.
- The S3 sneaker mural looks like real product photography.

No denylist hits.

**5. Image quality: 5.** C1 clipping as above. The flat-block rule passes (12%). Untextured flat grey stair wall and block in S5 (1250–1500,680–1000 and 1580–1920,900–1080). Low-res blurry sign in S1 (0–140,310–400).

## A/B (judged before identity)
The reference wins all 6: warmer and denser far field, parked traffic, and depth in its facades. ref/ours: perch-skyline B/A, river-aerial B/A, avenue-street A/B, avenue-swing-height A/B, timessq-street A/B, aerial A/B.

**progress-perch:** A (r06) is slightly better than B (older version), by about +0.5. It fixes C12 (far-shore B−R went from +29.4 against sky +7.1 to +9.2 against +5.7), removes the white shore slabs, and makes the river darker than the shore. It loses far texture (Laplacian 5.36 → 2.36), and C13/C15 still fail.

## Gaps (ranked)
1. **Far field (C11/C13–15):** replace far-shore boxes with window-atlas facades. On S4 the far band must reach Laplacian ≥6× sky, sit 25–35 Y below sky, with the river 5–35 below the shore and RMS far/near ≥0.25.
2. **Parked cars and props (C4/C6):** ≥5 parked cars including taxis in S1, ≥14 vehicles in the S2 avenue, trees on both sides of S1.
3. **Facade albedo (C1):** cap light stone and spandrel base colour until S2/S8 crops are ≤1.5% >204.

## Secondary
- Shop interiors reuse one texture.
- Untextured S5 blocks.
- Sparse S3 roof.
- Remove the MTA slogan and the NEO RACER art.

## Lighting (P4)
- S1/S7 crush (C2 means 21–44).
- S3 foreground near black.
- S4 whiteout (sky Y 229), which drives part of C13/C15.
- S7 sun blowout.
- Most of S6's clipping.

## Verdict: FAILS
