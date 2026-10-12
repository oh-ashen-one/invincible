# CRITIC: P1 City r10 (pixels only)
Homage fan game, not affiliated with Marvel/Sony/Insomniac. Work: `_scratch/critic-P1-r10-work/`. Diff vs r09: S4 15.6, S8 1.8 (unchanged). No clips: motion unproven.

## Scores (r09 → r10)
1. **Facades 5 → 5.** C2 better: S1 (0,0,480,300) Y 80.6, (1360,0,1740,400) 64.7. C1 still FAILS, unchanged: S8 glass (1270,0,1640,300) 70.4 % >204; S5 (640,40,880,700) 5.65 %, p99 227.
2. **Street dressing 5 → 5.** C4: S1 17–18 vehicles, 1 traffic light, 0 people (P6). C6: S2 25–26 vehicles (above 14–22). C7 passes. Cars are toy-like with blank plates.
3. **Rooftops/skyline 4 → 5.** S4 plateau and wall are gone: varied towers and a tree-lined shore. But at 4× zoom, the far towers (540–900, 110–260) are untextured two-tone extrusions with no windows; 25 % of bright 8×8 blocks have std <3. S3 white untextured props remain (1590–1760, 960–1060).
4. **Composition 5 → 5.** S5 reads as Times Square. The S6 red steps are still a pink glow: sat 0.30, V 163 (r09 0.31/159; ref ≥0.44).
5. **Image quality 5 → 5.** Black crush: Y<25 is 13.2 % in S3 and 1.4 % in S7 (r09 19.7/3.6). The S6 curb (1150,760,1920,1080) is still 14.65 % >204, unchanged.

## Tests
SPEC defines no T1/T2. I used r09's gap tests on S4 (0,150,1300,300).
- **T1** silhouette-top std ≥12 px, far-only columns (x0–200, 460–1300; r09 13.0 by this method): **PASS**, 17.7.
- **T2** ≤10 % >204: **FAIL**, 29.5 % (r09 38.7 %).
- **C11** **PASS**: \|Lap\| far/sky 16–18×; flat blocks 9 %.
- **C12** **PASS**: B−R far − sky +0.3.
- **C13** **PASS**, box-dependent: far (0,150,1300,215) is 30.3 below sky. With y150–240 it is 36.7 (fail).
- **C14** **PASS**: river 13.9 below far shore.
- **C15** **PASS**: RMS far/near 0.32–0.45, at the upper edge.

## A/B (judged on merits)
street-avenue **A** (worn materials, people); avenue-swing **A** (crowds, GI); rooftop **B** (atmosphere); perch **A** (warm haze); perch-dn **A** (bridges, haze); plaza-steps **A** (saturated steps); plaza-street **A** (lit signage); sunset **A** (sky depth); aerial **B** (haze falloff); progress-skyline **A** (varied far towers, no wall: newer build).

## Single biggest gap
Give the S4 far-shore towers a far-LOD facade with a window grid, crown/setback variation and mid-grey albedo (~0.25–0.35) in place of the flat pale extrusions.
- Test: S4 (0,150,1300,300) has ≤10 % of pixels >204 (now 29.5 %).
- Test: in (540,110,900,260), ≤10 % of 8×8 blocks with Y>200 have std <3 (now 25 %).
- T1 and C11–C15 still pass.

## Secondary
1. S8 glass: ≤1.5 % >204 (C1). It has been 70.4 % for three rounds.
2. S6 curb crop: ≤1.5 % >204. Red steps: sat ≥0.44, V ≤200.
3. S3: texture the white roof primitives.
4. Cars: clearcoat and plates. S2 traffic: cut to ≤22. Flag to P6: 0 people.

## Brand/IP
Visual read, no OCR: AMBROCHE, FIZZO, VELVET & VINE, THE PAPER MILL, COMEDY CLUB, OÜR OÜ. None is on the §5 denylist; no taxi livery text. Nothing to flag.

## Verdict: FAILS TARGET (lowest 5)
