# CRITIC: P1 City r09 (pixels only)
Homage fan game, not affiliated with Marvel/Sony/Insomniac. Tools: `_scratch/critic-P1-r09-work/`. No clips this round, so motion is unproven. S8 is unchanged since r08 (diff 2.5).

## Scores
1. **Facades: 5.** C2 is fixed. S1 (0,0,480,300) mean Y 66.6 and (1360,0,1740,400) 53.8. C1 still fails: S8 glass (1270,0,1640,300) 70.4% >204 (unchanged), S5 mid tower (640,40,880,700) 5.7% >204, p95 208.
2. **Street dressing: 5.** C4: S1 has 15–17 vehicles. C6: S2 has 19–20. C7: S1 has ≥6 trees and 2 + 2 signs. People: 0 in S1 and S2. The cars are toy-like, with flat paint, no reflections and blank plates.
3. **Rooftops/skyline: 4.** S3 is no longer crushed (tank mean 41.8). C9 passes with 2 tanks. S3 props at (1280–1700, 930–1010) are untextured white primitives, and the mural is flat vector art. S4 passes C11–C15. The far band is still a white box plateau: silhouette row std 6.1 px (r08 6.0), and 38.8% of (0,150,1300,300) is >204. The grey embankment wall (y230–290) is still there.
4. **Composition: 5.** S5 reads as Times Square. The S6 red steps got worse: saturation 0.31 and V 227, against r08's 0.37/197.
5. **Image quality: 5.** The black crush is fixed: Y<25 is 19.7% in S3 (≤25) and 3.6% in S7 (≤30). Clipping remains: S6 curb (1150,760,1920,1080) is 14.65% >204 (unchanged).

## A/B
- street-avenue **B**: warm bounce, people.
- avenue-swing-height **B**: graded GI, plaza detail.
- rooftop-watertowers **B**: A has a flat mural and no atmosphere.
- perch-skyline **B**: A's far band is a plateau.
- perch-skyline-dn **A**: bridges, graded haze.
- plaza-red-steps **A**: saturated steps, people, emissive light.
- plaza-street **B**: lit signage, people.
- sunset-crosstown **B**: sky, depth.
- aerial-midtown **A**: haze falloff. B is crisp but flat.
- progress-street **A**: facades are lifted (r09).
- progress-rooftop **B**: the tank is readable (r09).
- progress-sunset **B**: the facades are readable (r09).

## Biggest gap
Rebuild the S4 far-shore city band (x0–1300, y150–300). Use varied-height far buildings with mid-grey albedo, and replace the grey wall embankment with a seawall, piers and trees.
- Test: silhouette-top row std ≥12 px (now 6.1).
- Test: ≤10% of the box >204 (now 38.8%).
- Test: C11–C15 must still pass.

## Secondary
1. S8 glass (1270,0,1640,300): reduce sky reflection so ≤1.5% is >204 (C1). It is 70.4% now.
2. S6 curb and plaza (1150,760,1920,1080): ≤1.5% >204. Red steps: saturation ≥0.44 and V ≤200.
3. Texture the S3 roof props: no white untextured meshes (C-E).
4. Cars: add clearcoat or reflections and plates. Flag to P6: 0 people.

## Brand/IP
The in-frame names have 0 hits on the §5 denylist. Nothing to flag.

## Verdict: FAILS TARGET (lowest 4)
