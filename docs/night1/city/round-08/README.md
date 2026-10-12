# P1 City round 08 — captures and camera parameters

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Running game: `Scripts/run_game.sh` (`-game`, offscreen, map `/Game/Tests/City/City_View_<id>`, auto-activated CameraActor), screenshot at t = 28 s.
Frame times: game seconds 18-28, `t.MaxFPS 0`, no VSync, TSR with automatic screen percentage. GPU utilization read with ioreg before each run
(GPU shared with other sessions; the P1 editor was closed during the runs). Positions in browser metres (x east, y up, z south); UE = (100x, 100z, 100y) cm.

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

| id | output | internal | avg ms | p95 ms | GPU ms | GPU util before |
|---|---|---|---|---|---|---|
| S1_avenue_street | 1920x1080 | 1399x787 | 20.935 | 29.239 | 17.975 | 2 % |
| S1_avenue_street | 3840x2160 | 1920x1080 | 24.715 | 34.321 | 23.156 | 0 % |
| S2_avenue_swing | 1920x1080 | 1399x787 | 19.811 | 28.304 | 16.836 | 0 % |
| S2_avenue_swing | 3840x2160 | 1920x1080 | 30.684 | 35.666 | 22.837 | 2 % |
| S3_rooftop_watertower | 1920x1080 | 1399x787 | 16.848 | 24.315 | 13.402 | 3 % |
| S3_rooftop_watertower | 3840x2160 | 1920x1080 | 18.565 | 28.303 | 16.918 | 33 % |
| S4_perch_skyline | 1920x1080 | 1399x787 | 23.892 | 33.424 | 22.811 | 59 % |
| S4_perch_skyline | 3840x2160 | 1920x1080 | 31.455 | 41.041 | 30.307 | 53 % |
| S5_timessq_south | 1920x1080 | 1399x787 | 18.69 | 28.62 | 17.062 | 52 % |
| S5_timessq_south | 3840x2160 | 1920x1080 | 23.688 | 33.375 | 21.998 | 0 % |
| S6_timessq_street | 1920x1080 | 1399x787 | 19.658 | 29.446 | 18.027 | 52 % |
| S6_timessq_street | 3840x2160 | 1920x1080 | 24.204 | 33.899 | 22.512 | 57 % |
| S7_sunset_crosstown | 1920x1080 | 1399x787 | 18.035 | 28.286 | 16.489 | 69 % |
| S7_sunset_crosstown | 3840x2160 | 1920x1080 | 22.56 | 32.813 | 20.955 | 0 % |
| S8_aerial_midtown | 1920x1080 | 1399x787 | 19.316 | 29.32 | 17.582 | 77 % |
| S8_aerial_midtown | 3840x2160 | 1920x1080 | 37.233 | 111.35 | 26.773 | 0 % |

## Round 08 — parked cars, stopped traffic and street trees (Sonnet 5.5, 2026-09-30 02:00-04:10; target from the r07 critic: "streets are empty")

Target: cars and yellow taxis along both curbs of every avenue (>= 2 per 20 m per side), >= 2 street trees per 20 m on both sidewalks. Test 1: YOLO11x conf .30 finds >= 5 cars in S1 and >= 14 vehicles in S2. Test 2: >= 2 trees in S1 x 0-900 (hand count).
Captures: `S1..S8_*_{1920x1080,3840x2160}.jpg` (still views only: `SHOTLIST.md` has no movement sequences, so no mp4). **Internal resolution: 1920x1080 output renders at 1399x787, 3840x2160 output at 1920x1080 (TSR, automatic screen percentage; `perf.json` internal_w / internal_h).**
Frame times above are **contaminated** (shared GPU: `gpu_slot` `contaminated=true reasons=no-exclusive-lock`, 4-5 Unreal processes of other agents running, `gpu_util_before_pct` column; S8 4K p95 111 ms is a foreign perf run). They are not fps evidence. No `Failed to compile Material` in any of the 16 game logs.

### Measured (same instruments as r07: `tools/export/city_spec_check.py --yolo --ip`, `city_spec_check.md` / `.json`; YOLO worker now conf 0.30 like the critic's test, the json also has the count at 0.35)
| line | r07 | **r08** | target |
|---|---|---|---|
| Test 1 S1 (1080p): vehicles / cars, conf .30 | 0 / 0 | **16 / 15** (conf .35: 16; 4K frame: 17 / 17; conf .25: 16 / 15) | >= 5 cars (C4 band 5-19) |
| Test 1 S2 (1080p): vehicles / cars, conf .30 | 0-1 | **17 / 16** (conf .35: 16; 4K frame: 19 / 18; conf .25: 25 / 22) | >= 14 (C6 band 14-22) |
| S6 (1080p): vehicles | 0 | 16 (people 1, traffic lights 0: P6 / signals, not this round) | C4 5-19 |
| Test 2 S1 x 0-900: street trees (hand count) | 0 | **5 trunks** at x ~ 443, 590, 693, 727, 823 (1080p px), the first two with crowns over the storefronts: `builder_checks/S1_left_trees_x0-900.jpg` | >= 2 |
| Parked cars per 20 m of parkable curb (audit `streetcars_audit.json`) | 0 | mean 2.42, 85 % of the 62 windows >= 2 (sides without a parking lane excluded, see limits) | >= 2 |
| Trees per 20 m of avenue frontage (audit `streettrees_audit.json`) | ~1.1 (browser trees left after the r05 thinning, S1 corridor) | mean 2.67, 92 % of the 136 windows >= 2 (the rest: sidewalk sheds, dock, corners) | >= 2 |
| C11-C15 far field (S4) | pass | unchanged: C11 27.1x, C12 -3.8, C13 -33.7, C14 +23.4, C15 0.26 | pass |
| C1 facade crops passing / C2 | 17/18 / 10/18 | 17/18 / 11/18 (see the note below: not a facade improvement) | 18/18 |
| IP OCR (8 4K frames) | 0 hits | 0 hits | 0 |

Note on C1 / C2: `spec_regions.json` v1 boxes were placed when S1's west sidewalk and S6's right foreground had no trees. New crowns now overlap `s1_left_glass` (mean Y 49.8 -> 34.9), `s1_left_stone` and `s6_right_white` (151 -> 77): the S6 box "passes" C2 only because foliage lowers its mean. Real facade C2 stays 10/18; the boxes need re-placing (v2) before they are quoted again. S1 / S6 / S7 C2 failures are the lighting (P4) of r07, unchanged.

### What was built (all scripted, Content/ not committed; `tools/export/build_city.sh` runs it, `docs/night1/city/EXPORT.md` describes it)
1. **Car prototypes** (`tools/export/export_vehicles.py`): the browser's own Blender-built car models (`public/assets/city/vehicles.glb`, LOD0 of sedan, sedan2, hatch, suv, suv2, cross, pickup, van and four taxi bodies) as Nanite static meshes, material `M_CityProp` (part ids: paint / metal / glass / rubber / head / tail / taxi sign). **The livery atlas `vehicles_atlas2.webp` is not used** (Daily Bugle, Roxxon, Oscorp, "Wolf & Sheep" ... cells, `IP_EXCLUSIONS.md`): UVs are zeroed, every part has a plain colour x baked AO, paint takes the browser's NYC colour mix, taxis 0xf5a900, no toppers / plates / stripes.
2. **Parked cars and taxis** (`street_cars.py`, 197 cars, 37 yellow taxis): both avenue curbs at the browser's rules (no lane on Park Av, none in a bike lane, only the plain-asphalt ends of a red bus lane, 9.5 m clear of block ends, hydrants, bus stops, lane-closure props, 15 m clear of a street-level shot camera).
3. **Stopped avenue traffic** (`street_traffic.py`, 195 cars): queues at the stop lines + a few free-flow cars in the four travel lanes. Parked cars alone put ~10 detectable vehicles in S2 (its frame starts 80 m ahead). **Own actors, folder `City/Traffic` (`ISM_traffic_*`)**: P6 owns moving traffic; delete that folder in the integrated map or build with `traffic=0`.
4. **Street trees** (`street_trees.py`): every empty tree pit gets a tree (49), gaps > 9 m along both sidewalks of the four avenues are filled (130 trees, each with its own iron pit), the r05 `thin()` of the S1 / S2 corridor is gone, and browser trees within 16 m of a street-level camera are dropped (3: a trunk 12 m from the lens filled the S1 left edge).
5. **`M_CityLeaves` distance alpha** (`steps=leaves`): the leaf texture's alpha lost coverage in its mips, beyond ~25 m every leaf card was discarded and distant street trees (S2, S8) were bare branches. The alpha cut now falls with distance (0 at 25 m, 0.55 at 80 m) and far crowns darken (a lit opaque canopy glowed mint-green at the end of the avenue). Far crowns read as solid green masses (hedge-like), not as individual leaf clusters.
6. Build script: prop meshes re-imported over existing ones get a `_v<N>` suffix (`sm_path()`); renaming or deleting a referenced mesh in a commandlet leaves redirectors that break the next rename (two commandlet runs died on it, 12 errors).

### Limits, honestly
- The cars are still: no simulation, no wheel motion, no lights except the emissive tail / head material (no daylight clearcoat, matte paint, blank taxi toppers, no plates). Buses, box trucks and tour buses are exported by the browser but not placed.
- Sides without a parking lane keep no parked cars on purpose: the west curb of 5th Av (red bus lane; S1's left curb is that lane, so S1's cars are the east curb, the lanes and the far field), the west curb of the -250 avenue (bike lane), Park Av (median). "Every avenue, both curbs" is met at the browser's own rules, not literally.
- Cross streets carry no cars and no trees (S7 looks along one): only avenues were in the target.
- The S1 west sidewalk trees now cover most of the left storefront fascias (the r05 thinning existed for that); the crowns are dark under the test lighting (sun 6 / sky fill 1.7 at +2 EV, P4).
- S2's far end still has a faint bright-green haze where the darkened far crowns meet the blown sky band.
- 4K / 60: not measured (contaminated numbers). ~3.5 M Nanite triangles of cars (392 x ~9 k) and ~1.5 M of trees (179 x 6.8-14.7 k) were added; F / perf owns the budget.
