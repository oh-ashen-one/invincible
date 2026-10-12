# Critic P1: CITY, round 01 (pixels only)

## 1) Axis scores (reference: Marvel's Spider-Man 2)
| Axis | Score | Evidence |
|---|---|---|
| Facade & building fidelity | **4** | S8 centre (4K x1200-2600,y600-1500) has real variety: brick pre-war towers with sills and cornices, interior-mapped glass. But in S2 the left tower is one flat window grid repeated for 40 storeys, the S1 storefronts are blank blown-white panels, and there are no fire escapes, awnings or signage anywhere (compare `street-avenue-hero-taxis__og_0000`). |
| Street-level dressing | **3** | The S1 asphalt and paint hold up at 4K, but an untextured grey cylinder stands in the middle lane (x2350,y1200-1500). The only street props are cones and barrels, with no hydrants, mailboxes, newspaper boxes or manholes. The S6 plaza is generic benches, cage tree pits and glowing floor tiles. |
| Rooftops & skyline | **2** | In S4 the city stops about 1 km out, on a flat tiled grey ground plane with a hard edge against the blue sky. There is no river, no far shore and no haze. The S3 roof holds one water tower and a few boxes. Compare `skyline-perch-nm__nm_0846` / `rooftops-watertowers-golden__nm_0314`. |
| Composition / Manhattan believability | **2** | The S5 and S6 "Times Square" frames are dead black boards on grey towers under noon light. They have no imagery and no red steps, and nothing in them reads as Times Square (compare `timessquare-swing-through__ts_0513`). S7 is a black canyon with no sunset read. The streets are empty. |
| Image quality | **3** | In S3 a huge stair-stepped white shape covers about 30% of the frame (x0-1700). It is either shadow-map aliasing or an unlit mesh. The S5/S6 billboards are black with white pixel blotches, which looks like missing textures. The ground tiling in S4 is visible from altitude. |

## 2) A/B decisions (judged on merit first)
In all eight pairs the other image is clearly better. Ours loses on material richness, lived-in dressing, skyline depth and signage.
- Better image: avenue-street **A**, avenue-swing-height **B**, rooftop **A**, perch-skyline **A**, timessq-wide **B**, timessq-street **A**, sunset **A**, aerial **B**.
- Guess (made afterwards, from the HUD and the SM2 logo): ours = avenue-street B, swing A, rooftop B, perch B, ts-wide A, ts-street B, sunset B, aerial A. No pair is close.

## 3) Single biggest gap: the world ends in view
In **S4 (perch_skyline)**, replace the flat grey ground plane that shows above roughly 4K y≈230-900 with continuous city to the horizon, using far-LOD or impostor blocks at Manhattan density. Add the East and Hudson rivers as water with a far-shore skyline (Queens/Jersey), and a distance haze band so the horizon is never a hard line against the sky. The target is `refs/streets/skyline-perch-nm__nm_0846.jpg` (and pack perch-skyline A).

Pass test: at S4 4K, zero pixels of bare ground plane are visible. Building silhouettes run across the full frame width up to the haze line. At least one river and a far shore are readable.

## 4) Secondary issues
1. **Times Square billboards** (S5, S6): every board is black with white blotches. They need real emissive ad imagery on every surface, the red TKTS steps, and light spill onto the ground (`timessquare-billboards-street__ts_0217`).
2. **S3 artifact**: the giant jagged white shape on the left wall. Fix the shadow resolution or remove the mesh, and add rooftop density (AC units, bulkheads, vents, more water towers).
3. **S1 street**: remove or texture the floating grey cylinder. Give the storefronts glazing, interiors, signage and awnings, and add hydrants, mailboxes and manholes at the guide's per-20 m density.
4. **Repetition and flat walls** (S2 left tower, S7 right wall): break them up with cornices, setbacks, fire escapes and window-state variety. Streets are also empty of cars, taxis and people. That belongs to another piece, but it still reads as a dead city.

## 5) Verdict: **FAILS** (lowest axis 2; every axis is below 8)
Lighting is a placeholder and is partly to blame for S3, S5 and S7. The geometry and content gaps above exist independently of lighting.
