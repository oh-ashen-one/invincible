# P6 City Life, critic r03 (blind, pixels only)
Homage fan game, not an official Marvel, Sony or Insomniac game. YOLO11x-seg (conf .35, 1920 px, video frames every 0.5 s) matches detector.txt. Feet data: feet_clip.csv.

| Axis | r2 | r3 | Evidence |
|---|---|---|---|
| 1 Traffic density | 5 | **5** | S1 9 vehicles (C4 median 11). S2 14 (low edge of C6). Swing median 24, but cars are 30 px vs 47 px in the ref; nearest block has 5 cars in 4 lanes (swing@0.5 s). |
| 2 Traffic motion | 5 | **5** | Red queue (taxis, van, bus) holds, a truck crosses, the queue leaves by 12.25 s. Pickup-bed fault fixed. Near lanes at swing height are thin. |
| 3 Ped density/variety | 5 | **6** | S1 51 people (41 % right), street median 28, signal 48, ≥15 per near sidewalk at swing@5 s. Gap closed. The hi-vis worker look appears 4× in S1. Candy-saturated outfits, single-file lines, pink twins (swing@8 s). |
| 4 Ped motion | 4 | **4** | CH19 proven (phase spread 0.26). Stance foot slides 47–54 cm/s, about 40 % of walk speed. Ankle lift 31 cm, a back-kick (street@9.6 s). All periods 1.00–1.10 s. Legs clip through coats. A group walks mid-roadway (swing@8 s). |
| 5 Believability + IQ | 4 | **4** | Haze column on the road centre: asphalt luma 183 vs 100–131 beside it (S1_4k y=1450). Bus rear is a hollow smeared box (street@0.75 s). Untextured white plaza (swing@8 s). Plastic-lit people. |

**A/B (merit first)**: avenue-street **A**; sidewalk **A**; avenue-traffic **A** (28 vs 13 vehicles); swing-avenue **A** on fidelity (B denser). Progress-street **A** (right sidewalk 17 vs 3 people). Progress-avenue **B** (A has people in a pickup bed on a crosswalk). Progress-swing **A** (12 vs 0 people). Guesses: ref = A in the first four; newest = street A, avenue B, swing A.

**Biggest gap**: plant the feet. In feet_clip.csv (≥14 walkers), stance ankle speed (foot within 1 cm of its lowest point) needs a median ≤10 cm/s (now 47–54). Peak ankle lift ≤20 cm (now 31). Gait periods should span ≥0.25 s (now 0.10).

**Secondary**
1. Kill the haze column: S1_4k asphalt luma at x1880–1960 within ±10 of both neighbours at y=1450 and 1600.
2. Crowd mix: no look more than twice within 30 m, no twins, desaturated outfits, staggered two-way flow.
3. Swing: median car ≥45 px at 1080p, ≥8 moving cars on the nearest block, nobody in the roadway off crosswalks.
4. Closed, textured LOD0 bus and van rears. Flag the white plaza to the city owner.

Brands: none copied (METRO LOCAL SHIPPING, SALT & PEPPER DINER and the shop names are invented). The taxi has a checker stripe only.

**Verdict: FAILS TARGET** (lowest axis 4).
