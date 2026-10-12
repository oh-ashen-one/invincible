# CRITIC: Island A r03
Homage fan game, not affiliated with Marvel/Sony/Insomniac. Same 7 axes as r02. Frames at 4 fps. Ref: `streets/street-midtown-high__og_0410.jpg`.

## Scores
1. **Facades 5.** Brick holds up. Far fire escapes are still zigzag slabs (r5 t=20).
2. **Street dressing 4.** M2 has paint, crosswalks, bike lanes, signals, kerbs and cars. But r5 has 0 pedestrians and about 6 cars against about 40 in og_0410.
3. **Rooftops 5.** a1 is dense to the horizon. p3 has black glass cells.
4. **Composition 5.** r5 reads as an avenue canyon for all 30 s.
5. **Image 4.** Camera in foliage: r5 t=6.75 (78 %) and 25.25 (68 %); r1 t=17.25 (72 %); r4 t=15.5 (62 %).
6. **Streaming 6.** r5 runs 1482 m to y=2285 with no bare mass. The audit (x ±1024, y ±3584) has 0 facadeLod.
7. **Collision 4.**
   - r3 is still stuck under the fire escape from t=2.4 to 8.7: 6 topOut loops at x≈-235.5, the same as r02.
   - Raw hollow went from 16.72 % to 17.68 %.
   - The hero and rope pass through canopies (r5 t=10.2 and 26.8).

## Checks
- **a PASS.** 20/20 releases got a re-web. Max gap 0.30 s; 100 % of gaps ≤0.5 s.
- **b PASS.** 0 ground frames after 1 s, 0 stalls. 24/26 anchors sit on a WHBox. The t=26.6 re-anchor is 2.5 m off a box and runs through a tree.
- **c PASS.** Paint is 3.0 / 0.85\* / 1.4 / 1.1 % of the road (\*t=20 is a full crosswalk). Std is 43 / 44 / 37 / 37.
- **d PASS.** Capsule overlap is 0 frames on every r02 and r03 route.
- **e** Dressed, but no people.
- **f** No regression. Frame diff vs r02 is ≤4.0 on r1 and r4; r3 is unchanged.
- **g** No real brand (tesseract at 2 fps on 5 clips, plus an eye scan).
- **h** r2 has 187 wall frames, a 2.65 s gap and ends at z=95. Recorded, not scored.

## A/B
v1 A, v2 A, v3 B, v4 A, s1 B, s2 A, s3 B, s4 B, s5 B, s6 A, p1 B, p2 tie (0.005 % of pixels differ), p3 B, p4 A.

## Biggest gap
Make fire-escape collision match the drawn platforms, with a top-out. **Test on r3, from t=2.4:**
- 0 s stuck (no 1-s window moves <3 m)
- ≤1 topOut loop
- the hero clears x=-235.5 by t=3.5

## Secondary
1. The camera must be in foliage (>40 %) on 0 frames, and ropes must never cross a canopy.
2. On r5, show ≥5 pedestrians per block and ≥15 cars per frame.
3. The fire-escape LOD should be see-through grating.
4. Review CHOCO LOCO, TOKKA and IRON GUARDIAN.

## Verdict: FAILS TARGET (lowest 4)
