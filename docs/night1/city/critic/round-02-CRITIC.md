# CRITIC — P1 City, round-02 (pixels only)

## 1) Axis scores
- **Facade fidelity: 5** — S8 4K: brick towers have sills, belt courses, setbacks, window ACs. But every daytime window is the same flat white emissive rectangle (S2, S7, S5), and glass towers repeat one interior-cube card.
- **Street dressing: 2** — S1: trees are black faceted paper cards. Storefronts are blank glowing planes with one blurred sign (S1 right, 4K). No fire escapes, awnings, hydrants, boxes or steam. Pavement is clean, not cracked or wet. Ref: `street-avenue-hero-taxis__og_0000`.
- **Rooftops & skyline: 4** — S4/S8 roof clutter is good. But the S3 water tower is an untextured faceted cylinder on two sticks. S4's far shore is blue-tinted untextured boxes on pure-white quays, and the park is grey untextured spheres. The haze is flat milk. Ref: `skyline-perch-nm__nm_0846`.
- **Manhattan believability: 4** — Times Square (S5/S6) reads, with the red steps, billboards and plaza. Avenues are over-wide, identical and sterile, and S4 has no landmarks or bridges.
- **Image quality: 3** — Missing materials (park trees, far-shore ground). The S1 canopy is crushed black.

## 2) A/B decisions
- avenue-street **A** · avenue-swing-height **B** · rooftop **A** · perch-skyline **A** · timessq-wide **B** · timessq-street **A** · sunset **B** · aerial **A**.
- Each winner has traffic, weathered brick, lit foliage, emissive spill and a real far shore. The empty, sterile frame loses every pair; that frame is ours.
- progress-perch: **B, by a wide margin (~3 points on skyline).** A ends in an infinite grey ground plane under a flat blue ocean, and its billboard face is black with holes.

## 3) Single biggest gap
**Replace all foliage.** In S1 (left 45% of frame), S2/S7 (both avenue edges), S5 and S4 (right third, the park), trees are black faceted cards or grey spheres.

Build alpha-masked leaf clusters with green albedo, two-sided translucency and sky gaps.

**Test:** the S1 canopy reads green with visible leaf clusters and a mean luma of at least 25%. S4's park reads as a green canopy mass with paths, as in `centralpark-skyline-over-park__cp_1230` and `street-avenue-hero-taxis__og_0000`.

## 4) Secondary
1. **Ground floors (S1, S6):** recessed storefronts with mullions, awnings, legible signs and interiors.
2. **Far shore (S4 top-left):** texture it, remove the blue tint and the white quays, and add piers and bridges.
3. **S3 water tower:** staved wood, hoop bands and a steel lattice stand (`rooftops-watertowers-golden__nm_0314`).
4. **Street clutter:** hydrants, boxes, fire escapes and wet patches. Vary the daytime windows (dark, curtained, reflective).

## 5) Verdict
**FAILS** (lowest axis = 2). Lighting deepens the black canopies, but the grey park, the white far shore and the flat storefronts are asset failures.
