# P1 City round 09 — captures, camera parameters and the shade-fill measurements

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Running game: `Scripts/run_game.sh` (`-game`, offscreen, map `/Game/Tests/City/City_View_<id>`, auto-activated CameraActor), screenshot at t = 28 s, `tools/export/capture_one.sh`. Positions in browser metres (x east, y up, z south); UE = (100x, 100z, 100y) cm.

| id | camera pos | target | fov | sun (pitch, yaw) |
|---|---|---|---|---|
| S1_avenue_street | [246, 2.0, 150] | [251, 16, -300] | 75 | [-40, -45] |
| S2_avenue_swing | [243, 42, 185] | [252, 18, -350] | 80 | [-40, -45] |
| S3_rooftop_watertower | [166, 48.5, -122] | [158, 51, -150] | 75 | [-40, -45] |
| S4_perch_skyline | [182, 306, -92] | [-120, 150, -470] | 75 | [-40, -45] |
| S5_timessq_south | [-12, 6, -255] | [0, 48, -40] | 80 | [-40, -45] |
| S6_timessq_street | [8, 1.8, -110] | [-4, 26, -330] | 80 | [-40, -45] |
| S7_sunset_crosstown | [300, 30, -160] | [-300, 22, -160] | 75 | [-7, 0] |
| S8_aerial_midtown | [420, 160, 220] | [0, 20, -320] | 75 | [-40, -45] |

## Round 09 — shadowed facades lifted into the C2 range (Sonnet 5.5, 2026-09-30 04:10 on; target from the r08 critic)

**Target (critic r08, biggest gap):** bring shadowed facades into C2 (mean Y 52-119): raise the albedo of shaded brick and dark curtain-wall glass, add a lit-interior / sky-reflection term; if GI or exposure is the cause, log it to P4.
Test 1: S1 1920x1080 crops (0,0,480,300) and (1360,0,1740,400) mean Y >= 52 (r08: 22.5 / 19.7). Test 2: share of pixels with Y < 25 over the whole frame <= 25 % in S3 (r08 72.2 %) and <= 30 % in S7 (r08 62.5 %).
Instrument: `tools/export/shade_check.py` (Y = .2126 R + .7152 G + .0722 B on the 8-bit frame; on the r08 frames it reproduces the critic's 22.5 / 19.7 / 72.2 / 62.5 exactly). Raw output `shade_check.md` / `.json`.

### Result (1920x1080 frames of this folder; ShadeFill 0.12, GlassSky 0.11)
| test | r08 | **r09** | target |
|---|---|---|---|
| Test 1 S1 crop (0,0,480,300) mean Y | 22.5 | **66.6** | >= 52 |
| Test 1 S1 crop (1360,0,1740,400) mean Y | 19.7 | **53.8** | >= 52 (thin margin: +1.8) |
| Test 2 S3 share Y < 25 | 72.2 % | **19.7 %** | <= 25 % |
| Test 2 S7 share Y < 25 | 62.5 % | **3.6 %** | <= 30 % |
| CITY-SPEC C2, 16 daylight facade boxes (spec_regions v2, 1080p) | 10 / 16 | **15 / 16** (s2_dark_tower 47.1) | 16 / 16 |
| CITY-SPEC C1, same boxes | 15 / 16 | 15 / 16 (s5_grey_tower 3.70 %, unchanged, P4 sun / sky ratio) | 16 / 16 |
| C11-C15 far field (S4) | pass | pass, same numbers (fill fades out 0.9-2.2 km) — **S4 is the r09 first-version frame, see limits** | pass |
| C4 / C6 YOLO conf .30: S1 vehicles / S2 vehicles | 16 / 17 | 17 / 19 | >= 5 / >= 14 |
Overall frame mean Y: S1 53 -> 74, S2 75 -> 89, S3 23 -> 54, S5 72 -> 80, S6 70 -> 83, S7 33 -> 63, S8 99 -> 100.

### C1 / C2 per box (mean Y / share of pixels above Y 204), spec_regions **v2** boxes on all three variants
`r08` = round 08 frames; `v1` = first version of the fill (added everywhere, no shadow information); `r09` = this folder (shadow-aware).
| box | r08 | v1 | **r09** | C1 | C2 |
|---|---|---|---|---|---|
| s1_left_stone | 21.5 / 0.00 | 62.7 / 0.00 | **61.9 / 0.00** | pass | pass |
| s1_right_brick | 45.7 / 0.00 | 81.9 / 0.00 | **66.5 / 0.00** | pass | pass |
| s1_right_dark | 16.8 / 0.00 | 55.2 / 0.00 | **53.1 / 0.00** | pass | pass |
| s2_left_stone | 89.3 / 0.00 | 119.1 / 0.01 | **98.9 / 0.00** | pass | pass |
| s2_gold_glass | 78.7 / 0.00 | 133.5 / 0.00 | **91.3 / 0.00** | pass | pass |
| s2_white_tower | 71.7 / 0.03 | 104.6 / 0.13 | **74.1 / 0.03** | pass | pass |
| s2_dark_tower | 26.2 / 0.00 | 70.7 / 0.00 | **47.1 / 0.00** | pass | FAIL |
| s5_left_dark | 47.7 / 0.48 | 69.6 / 0.50 | **56.6 / 0.48** | pass | pass |
| s5_grey_tower | 97.8 / 3.70 | 124.4 / 3.82 | **98.3 / 3.70** | FAIL | pass |
| s5_teal_glass | 76.4 / 0.34 | 100.9 / 0.39 | **78.5 / 0.35** | pass | pass |
| s6_left_brown | 44.6 / 0.21 | 74.9 / 0.25 | **57.2 / 0.19** | pass | pass |
| s7_left_glass (dusk) | 28.1 / 0.00 | 62.9 / 0.00 | **61.5 / 0.00** | pass | pass |
| s7_mid_dark (dusk) | 37.2 / 0.07 | 53.9 / 0.08 | **51.4 / 0.08** | pass | FAIL |
| s7_right_masonry (dusk) | 15.0 / 0.00 | 58.0 / 0.00 | **56.2 / 0.00** | pass | pass |
| s8_glass_right | 80.2 / 0.23 | 112.5 / 0.50 | **80.3 / 0.23** | pass | pass |
| s8_pale_glass | 108.5 / 0.00 | 147.6 / 0.03 | **108.8 / 0.00** | pass | pass |
| s8_brick_a | 60.7 / 0.00 | 91.3 / 0.01 | **60.9 / 0.00** | pass | pass |
| s8_brick_b | 105.0 / 0.67 | 119.7 / 3.22 | **105.0 / 0.65** | pass | pass |
| s8_grey_tower | 97.9 / 0.01 | 134.6 / 0.24 | **98.0 / 0.01** | pass | pass |
The v1 column is the lesson of the round: a uniform fill lifts every shaded box but pushes every sunlit one over the C2 ceiling (s2_gold_glass 133.5, s8_pale_glass 147.6, s8_grey_tower 134.6) and s8_brick_b over the C1 limit (3.22 %). It was thrown away.

### What was built
1. **Diagnosis** (masks + sweeps, `builder_checks/lit_mask/`): shaded walls were black for two reasons. Lumen sees a slit of sky inside a 30 m avenue, and the r07 albedo cap `SunK` is keyed on N.L, not on shadow, so a west wall that faces the sun but sits in canyon shade got the 0.08 luma cap AND no sun (the S1 right tower). GI / exposure part: logged to P4 in `HANDOFF.md`.
2. **Canyon shade fill** (`Shaders/City/ShadeFill.ush`, hand-written): emissive = surface albedo (before the sun cap, `^0.65`) x a sky-bounce irradiance (MPC `ShadeFill`), warm and weaker at low sun, faded out 0.9-2.2 km and by `1 - NightK`; coated curtain glass gets a sky-gradient reflection (MPC `GlassSky`, tint = the glass F0). Included by `M_CityFacade / Detail / Roof / Prop / VC (untextured solids) / Kit / Signage / Leaves (x 0.35)`.
3. **Shadow / enclosure weight from a baked height field** (`tools/export/bake_sunmask.py` -> `sunmask_h.png` -> build step `sunh`): rasterised roof / terrace triangles of the export (exact tiers), facade vertices, footprint boxes outside the detailed block; 1 m texels. `CitySunLit` marches 28 steps toward the sun, `CityEnclosure` compares the point's height with the mean building height around it (mips 5 / 7). Fill weight = enclosure x (1 - 0.88 x sunlit). A first height field made of whole footprint boxes marked visibly sunlit S8 faces as shaded (setback towers over-shadow); rasterising the roof triangles fixed it. Facade `DebugMode 12` shows the weight (blue = full fill, red = none): the S2 diagonal shadow on the left tower matches the real virtual-shadow-map shadow.
4. **K sweep on the first version** (1080p, S1 crops L / R, S3 / S7 share Y < 25): K 0.10 -> 67.8 / 53.9, 4.4 %, 5.2 %; K 0.22 -> 104.3 / 83.1, 0.0 %, 0.8 %; K 0.36 -> 134.3 / 108.8, 0.0 %, 0.5 % with 12.4 % of S3 above Y 204 (washed out, flat). 0.22 already looks flat (pastel trees); the final K is the smallest value that passes with the shadow-aware weight. One S1 frame at K 0.17 (same shader, not kept) measured 80.4 / 64.5, so the S1 right-crop margin can be widened with `set_mpc.py ShadeFill=0.17 GlassSky=0.15` (no rebuild); it was not verified on the other views.
5. **spec_regions v2** (r08 to-do 1): four boxes had grown over the street trees; re-placed foliage-free, two dropped (`spec_regions_v1.json` kept). 16 daylight boxes now: C1 / C2 counts are not comparable with r07 / r08, the table above re-measures r08 on the v2 boxes.

### Limits, honestly
- **Only 1920x1080 frames, no 4K, no perf window, no mp4** (`SHOTLIST.md` has no movement sequences). Internal resolution: 1080p output uses the same TSR auto screen percentage as r08 (1399x787 internal, `perf.json` of r08 / v1; these runs had no perf window so it was not re-logged).
- **`S4_perch_skyline_1920x1080.jpg` was captured with the first (uniform-fill) variant**, not with the final shader: the GPU driver wedged before S4 could be re-captured (below). Its far-field lines (C11-C15) do not depend on the fill (fades out at 0.9-2.2 km) and passed with the same numbers; its near-city roofs are brighter than the final shader would make them (enclosure ~0 at 300 m).
- The IP OCR (`--ip`, 4K frames only) was not re-run; this round added no text, sign or texture (only shader terms), the r08 run had 0 hits.
- **Performance of the shade fill is NOT measured.** The 28-step height-field march runs in the facade / roof / kit materials for every sun-facing pixel (+ 8 texture reads for the enclosure). Estimate, not a measurement: +40-80 % of a facade pixel's cost. The only frame times of the round are contaminated (`builder_checks/v1_uniform_fill_perf_CONTAMINATED.json`, first variant without the march, 4-5 foreign Unreal processes). Owner of the budget: F / P4; see HANDOFF for the cheap options (20 steps, early outs, `ShadeFill 0` switches fill + march off).
- Still open from the r08 critic (not this round's gap): S8 glass crop (1270,0,1640,300) 70 % above Y 204 (sky reflection saturates it), S4 far band silhouette, cars are matte, S6 red steps, 0 people (P6), 0 traffic lights found by YOLO.
- s2_dark_tower 47.1 (< 52) and the dusk box s7_mid_dark 51.4 are the two boxes still under the C2 floor; K 0.17 should clear both (see item 4), not verified.
- **GPU incident 2026-09-30 06:54:** during the final capture hold two Unreal processes (one of mine: the S2 launch that hung 15 minutes behind a process already stuck exiting, then killed by `run_game.sh`'s own 900 s `kill -9`; the other started 3 s earlier, owner not identified) ended as unkillable `?E` zombies inside the GPU driver, and the shared slot lock (correctly) refused every new launch for the rest of the session. I stopped my drivers, did not launch anything else, and hardened `capture_round.sh` (never launch while an engine is stuck exiting, `-timeout 7200`, stop_ue.sh watchdog, launch deadline). Details in HANDOFF gotcha 30.
