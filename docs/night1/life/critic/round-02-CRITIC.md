# P6 City Life, critic r02 (blind, pixels only)
YOLO11x-seg, conf .35, 1920 px, sampled every 0.5 s. Work: `_scratch/critic-P6-r02-work/`.

| Axis | Score | Evidence |
|---|---|---|
| 1 Traffic density/variety | **5** | S1 10 (C4 pass). S2 14/16, low edge of C6. Swing median 17, but cars are 28 px vs 51 px in ref, so the camera is about 2× too far. Nearest block at swing@8.25 s: 6 cars in 4 lanes; ref is bumper-to-bumper. Bus and pickup added. |
| 2 Traffic motion | **5** | Heads lit: red 0 s, green 9.75 s. A queue of 3 plus a bus holds, then pulls away at 10.5 s. Fault: in S2_4k a red pickup is stopped on the crosswalk with pedestrians inside its bed (x≈2000, y≈1810). |
| 3 Ped density/variety | **5** | Street median 19 (CH16 pass), S1 30, signal 35. All on one side: S1 25 left / 5 right; series 27/0 and 24/0. Swing clip 0 people in 20/20 samples; hand count on the near sidewalks is 0 vs about 20 in ref. |
| 4 Ped motion | **4** | Legs cycle. Walkers interpenetrate (street@9.0 s). The crowd moves single-file along the storefront. CH19 is unproven. |
| 5 Believability + IQ | **4** | Bus is a white box with flat black panes. Taxi roof lights are dark blocks. Van rear is a flat texture (signal@11.25 s). A green flare ghost sits on walkers (street@7–9 s). The r01 frame-0 and smear faults are fixed. |

**A/B (on merit)**: avenue-street **B** (A has more people, 26 vs 7). Sidewalk **A**. Avenue-traffic **A** (28 vs 13 vehicles). Street-clip **A** on fidelity; B is denser (17 vs 6). Swing-clip **B**. Signal-queue **A**. Signal-clip **B**; only A shows the red→green queue. Progress-street **A** (26 vs 7 people) and progress-clip **B** (17 vs 4), both real steps. Guessed refs: avenue-street B, sidewalk A, avenue-traffic A, street-clip A, swing B, signal A, signal-clip B.

**Biggest gap**: populate both sidewalks at every height. S2 and every 0.5 s swing sample should reach ≥15 hand-counted pedestrians on the nearest block's sidewalks. S1 and the series should put ≥35 % of YOLO people on the right sidewalk (now 0–17 %).

**Secondary**
1. Swing height: continuous flow in every lane of the nearest block, and a lower camera (median car ≥45 px at 1080p).
2. No vehicle overlaps a pedestrian or stops on a crosswalk.
3. Zero body interpenetrations in the 18 s street clip.
4. Modelled windows, lamps and roof signs on the bus and taxis at LOD0.

Brands: "NYC TAXI" door text is a real trademark; make it generic. The shop and fleet names are invented.

**Verdict: FAILS TARGET.** Lowest score is 4.
