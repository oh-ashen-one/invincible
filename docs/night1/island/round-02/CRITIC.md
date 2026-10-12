# CRITIC: Island A r02
Homage fan game, not affiliated with Marvel/Sony/Insomniac. Same 7 axes as r01. Frames are at 4 fps.

## Scores
1. **Facades 5.** Brick and grating read up close (r3 t=2-8). Distant fire escapes are solid zigzag slabs (r2 still t12), and glass reflects them (r4 t=19.5).
2. **Street dressing 3.** On new tiles the road is a bare slab. Lane paint is 1.21 % at r2 t=12 and 0.00 % at t=26/28; luminance std falls from 39 to 13-17. There are no cars and no people (ref `swing-avenue-traffic-dn__dn_0952`).
3. **Rooftops/skyline 5.** The tower field is dense (a1). The far shore is windowless extrusions, and roof props are slabs (r4 t=5-8).
4. **Composition 4.** From r2 t=25 to 30 the avenue reads as an empty plaza.
5. **Image quality 5.** Y<25 averages 4-8 %. The camera is inside foliage at r1 t=17.25 (70 %) and t=23.25 (75 %), and r4 t=15.5 (60 %).
6. **Streaming 4.** I saw no pop-in. The street layer ends at y≈1010 (r2 t≈19.5), and I3 is unproven.
7. **Collision 3.**
   - **Fixed since r01:** the p1 parapet clip.
   - **Anchors:** all 9 that were in frame project onto facades.
   - **r2:** from t=23.7 to 30 swing is held and never attaches (y>1228).
   - **r3:** from t=2.4 to 8.9 the hero is stuck under a fire-escape landing. He loops wallRun→topOut 5 times while z goes 32→36, and the camera ends up inside the escape (t=7.75).
   - **r4:** from t=13.7 to 15.5 he slides down glass in air mode.
   - **Audit:** raw hollow is 16.7 %.

**Content/:** 0 .uasset/.umap files on the branch and 0 in its history.

## A/B
- **v1: B.** It has traffic and people.
- **v2: B.** A's camera goes into the trees 3 times.
- **v3: A.** It is a real canyon swing; B lies prone on a roof.
- **v4: B.** It is a continuous wall-run.
- **s1: A.** Its far band is continuous.
- **s2: B.** It has material variety.
- **s3: A.** It has haze and speed lines.
- **s4: B.** A is a soft glass under-view.
- **p1: B.** A hides the hero inside the parapet from t=0 to 2.

## Single biggest gap
Give every tile past y>1010 the merged-city street layer and facade anchors.
- **Test:** rerun r2 with swing held. A web must attach ≤0.5 s after each release through t=30, with 0 ground frames after t=1.
- **Test:** the road band at t=26/28 must have ≥1 % lane paint and luminance std ≥35.

## Secondary
1. Fire-escape collision must allow a top-out. On r3, stuck time must be 0 s.
2. Replace the zigzag fire-escape LOD with see-through grating.
3. The camera must be in foliage on 0 frames (>40 % foliage).
4. Remove the real brand **CHASE BANK** (r2 t=25.0). Review CHOCO LOCO, TOKKA and the IRON GUARDIAN mural.

## Verdict: FAILS TARGET (lowest 3)
