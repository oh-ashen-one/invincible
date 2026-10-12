# P6 City Life — critic r01 (blind, pixels only)
Tool: count_people_vehicles.py settings (YOLO11x-seg, conf .35, 1920 px). Clip sampled every 0.5 s (43 samples).

| Axis | Score | Evidence |
|---|---|---|
| 1 Traffic density/variety | **4** | S1_street 1080p 5 veh / 4K 9 (C4 5–19, med 11: low edge). Clip med 13 (pass). **S2_avenue 13 (1080p) / 7 (4K) vs C6 med 14–22: FAIL**; ref avenue-traffic-A 28. Lanes mostly empty mid-block. Types: taxis, sedans, box truck, vans; no bus seen. |
| 2 Traffic motion | **3** | Cars do move (taxi crossing @8 s, blue car + taxi pacing camera @12–14 s). Most vehicles in frame are parked. Signal heads are blank yellow boxes, so stopping at a light can't be seen. No queue or following seen at any t. White car stopped inside the intersection box (S2_4k x≈1500–1830,y≈2340–2420). Loop cut @20.03 s is one motion-blur smear frame (diff 31 vs med 3.5). |
| 3 Ped density/variety | **2** | Clip people med **4** (p10 0, p90 6); S1 4/6; S2 0 detected (~10 by hand, all at one crosswalk). CH16 8–25 and C4 med 24: FAIL. Ref sidewalk-B 30. About 5 outfits. **Twin heads**: same bearded head twice, S1_4k x≈790–980,y≈1230 (CH17 fail). |
| 4 Ped motion | **4** | Legs cycle, directions mixed (strip 12.0–13.1 s @10 fps). Only ≤6 walkers per frame, so CH19 (≥6 walkers, phase spread ≥0.2) is **unmeasurable = unproven**. Foot plant is unresolvable at this size. |
| 5 Believability + IQ | **3** | Reads as a quiet Sunday, not Midtown. Vehicles are low-poly blobs: blue minivan @14 s, van with oversized flat windshield (S1), fuzzy/noisy white convertible texture (S2 crop). People pass at >10 m but not up close. |

**A/B (decided on merit first)**
- avenue-street: **A better**. 11 vs 7 veh; double-parked rows, detailed cars. A=ref, B=ours.
- sidewalk: **B better**. 30 vs 7 people, dense two-way flow. B=ref.
- avenue-traffic: **A better**. 28 vs 8 veh, bumper-to-bumper avenue. A=ref.
- street-clip: **A better**. Close, dense walkers with visible gait; B is a sparse scripted drive-by. A=ref.
- progress-street (ours vs ours): **A (newer, life on) beats B (empty)**: 7 people / 7 veh vs 0 / 0. That is a large step, but it only moves from "absent" to "sparse".

**Ranked gaps (testable)**
1. Pedestrian density: count_people_vehicles.py med ≥16 people on the street clip and ≥16 on S1; ≥6 distinct models; zero repeated heads within a frame.
2. Swing-height traffic: S2 median ≥14 vehicles over a 10 s clip at swing height, with moving flow in every through-lane.
3. Signals plus queues: lit signal heads, and in a fixed-camera 10 s clip at least one queue of ≥3 cars stops at red and pulls away on green, with no car stopped inside the intersection box.

**Secondary**
- Vehicle mesh quality and variety (blobby minivan/van; add buses and more body types).
- Frame 0 of the clip renders unlit (mean luma 27 vs 76 by frame 6).
- Smear frame at the 20.03 s loop cut.
- No swing-height motion clip was supplied, so C6 motion is unproven.

Brands: none copied. METRO LOCAL SHIPPING (555 number), FUHGEDDABOUTIT PIZZA and the shop names are invented.

**Verdict: FAILS.** Lowest axis is 2 (pedestrian density).
