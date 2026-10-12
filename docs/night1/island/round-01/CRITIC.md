# CRITIC: Island A r01
Homage fan game, not affiliated with Marvel/Sony/Insomniac. No prior island verdict existed, so I used city r10's five axes plus two island axes.

## Scores
1. **Facades 5.** The brick has recesses. s4-B is identical beige bays.
2. **Street dressing 4.** There are 0 pedestrians in our clips. Lime trees cover 16-20 % of the frame at sat 0.65 (v1-B, s3-A). v1-B t≈1 s has an untextured grey sedan.
3. **Rooftops/skyline 5.** s1-A far shore (0,120,900,520) is pale windowless extrusions with 26 % flat 8×8 blocks. Roof props are bare slabs (v4-A t=6-8 s).
4. **Composition 5.** The avenues read as Manhattan. The r1 t=22-24 s plaza is an empty slab.
5. **Image quality 4.** s3-A has Y<25 on 20.0 % (ref 5.8 %). The camera is inside foliage in 6 r1 frames (t=14.0: 81 %).
6. **Streaming coverage 6.** Over 1.8 km of routes I saw no bare mass or pop-in. Whole-island coverage (I3) is unproven.
7. **Collision 2.**
   - v3-B t=0.0/0.7/1.1 s: the hero runs through tree trunks and pit fences (r3: constant 9.80 m/s, fixed y for 25 s).
   - r4 t=11-13.5 s: he runs inside a parapet (x fixed at 274.525), then falls through a fire escape at t=14.25.
   - r3: swing is held from t=4 to 30 s and never attaches, so the cross street cannot be swung.
   - Plausible web on nothing: r1 t=23.27 anchors at (266.35,−729,40.15), but frames show an open plaza at that curb.
   - Box count is 56,816 in the audit vs 56,534 in the game log.

**Content/:** 0 .uasset/.umap files on the branch or in its history.

## A/B
- v1 **A**: crowds, worn asphalt.
- v2 **B**: people, GI.
- v3 **A**: real swings; B only runs.
- v4 **B**: climb detail; A clips into the parapet.
- s1 **B**: materials.
- s2 **B**: depth and river.
- s3 **B**: A is crushed.
- s4 **A**: backlit water towers.
- p1 **A**: river, park and far skyline read continuous, though 16 % is >204.

## Single biggest gap
Make collision equal what is drawn: trunks, pit fences, parapets and fire escapes. Make every cross-street facade anchorable.
- Test: on r3 crosstown-east with swing held, the web attaches ≤0.5 s after each release and ground mode is ≤10 % of frames.
- Test: in v3/r4 frames the hero never overlaps a trunk or parapet, and lands on fire-escape grating.

## Secondary
1. Bring tree sat down to ≤0.50, and pull the camera back when foliage covers >40 % of the frame.
2. Give the far shore window grids: flat 8×8 blocks ≤10 %.
3. Add ≥5 pedestrians on v1/v3 sidewalks.
4. Bring s3-A Y<25 to ≤8 %.

## Brand/IP
TOKKA, SILVER FERN CAFE, SKYWARD, AMBROCHE and IRON GUARDIAN (a superhero-style mural; watch it). None is denylisted.

## Verdict: FAILS TARGET (lowest 2)
