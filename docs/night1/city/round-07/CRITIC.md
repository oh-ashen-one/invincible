# CRITIC: P1 City r07 (pixels only)
Homage fan game, not affiliated with Marvel/Sony/Insomniac. Coordinates are 1080p. Tools: `_scratch/critic-P1-r07-work/{m,f}.py`.

## Scores
1. **Facades: 5.** S8 brick towers show cornices and setbacks. S1 facades fail C2: mean Y is 24.4 at (0,0,480,300) and 17.3 at (1360,0,1700,400). S8 glass at (1270,0,1640,300) fails C1 with 70% of pixels >204. S1 shop interiors are still flat cards.
2. **Street dressing: 3.** C4: S1 has 0 cars and 0 people. C6: the S2 4K avenue crop has ≤1 vehicle. The S1 left sidewalk has 0 trees, an empty tree pit and 1 trash can. The sidewalk shed is flat untextured green.
3. **Rooftops/skyline: 4.** S4 passes C11–C15 (Laplacian 10.4×; B−R +6.3 vs sky +9.6; far shore −28.8; river 29 below; C15 0.25, borderline). But the far band is a plateau of pale boxes: silhouette top-row std 3.8 px vs 18.9 on skyline-perch-nm. The embankment is a flat grey wall. S3 roof clutter is sparse.
4. **Composition: 4.** S5 billboard density reads as Times Square. S6 red steps are salmon at saturation 0.33, against 0.44 on the day ref's red walkway. Every street is empty.
5. **Image quality: 4.** Pixels with Y<25: S3 72%, S7 61% (sun clipped). The S4 sky is milky at Y 227–239.

## A/B
- street-avenue: **B**. Parked cars, trees, bounce light.
- avenue-swing-height: **A**. Traffic and people.
- rooftop-watertowers: **B**. A is crushed.
- perch-skyline: **A**. Varied skyline heights.
- perch-skyline-dn: **B**. Bridges, varied silhouettes.
- plaza-red-steps: **B**. Saturated steps, full emissive coverage.
- plaza-street: **A**. Dense signage and life.
- sunset-crosstown: **B**. A is crushed.
- aerial-midtown: **B**. City density runs to the horizon.
- progress-perch: **B**. A's fog flattens the mid-city.
- progress-swing: **A**. B's tower fails C1 (35% >204); A has 0%, but its texture is flatter.

## Biggest gap
Park cars and taxis on both curbs of every avenue (≥2 per 20 m per side). Plant ≥2 trees per 20 m on both sidewalks.
- Test: YOLO11x at conf .30 finds ≥5 cars in S1 and ≥14 vehicles in S2.
- Test: ≥2 trees in S1 x0–900.

## Secondary
1. S4 far band: silhouette top-row std ≥12 px at x0–1300 y150–260. Replace the wall with a seawall and piers.
2. S1 crops reach C2 (mean Y ≥52). The S8 glass crop has ≤1.5% of pixels >204.
3. Replace the card interiors. Texture the shed. Add paver joints and litter.
4. Red-step saturation ≥0.6. Remove the 63 white floor squares (Y>240) in S6 x1100–1920 y700–1080.

## Brand/IP
OCR of the captures against the refs matched only junk tokens. Last round's HAUTE UNLIMITED, Astor and Madison are gone. Nothing new to flag.

## Verdict: FAILS TARGET (lowest 3)
