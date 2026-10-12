# Island (piece A) — round 04: merged branch, fire-escape collision, fresh rebuild

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Builder: Claude Opus 5.5 high via Devin, 2026-10-03. Branch `night1/island` (pushed). All captures: REAL game (`-game`, offscreen,
`Scripts/run_game.sh`), map `/Game/Maps/Manhattan_WP`, every Unreal process (commandlets included) inside `gpu_slot.sh capture --label island`.

**Status: STOPPED mid-rebuild (section 6).** Done: merge, C++, fire-escape collision, WHBox rule 5, leaf fade, checkers, telemetry sims.
Not done: the rest of the fresh rebuild, the r1-r5 re-capture, frame / foliage / road-band measurements on renders, the critic pack.

| round target | result |
|---|---|
| 0 merge + C++ + fresh rebuild time / Content size | merge clean, C++ 15.7 s; rebuild **partial** (11,262 s of holds for tex, mat, 1,642 meshes, protos, 128 / 272 kit tiles), total not measured (projection ~5.2 h vs I8 <= 90 min); Content 1.2 GB partial |
| 1 fire escapes on r3 from 2.4 s (sim) | at the r03 spot: **0 top-outs** (r03 6), past x -235.5 at 2.7 s (x -218 at 3.5 s); route-wide "never stuck" **fails** on 5 short-rope stalls elsewhere (traversal, no fire escape near) |
| 2 raw hollow <= 16.72 %, I5 <= 1 / 2 % | **16.43 %**, 0.25 % / 0.36 % (offline audit of the boxes the build spawns) |
| 2 r5 checks a-d | default merged traversal (altitude chain): **a fails** (max gap 5.55 s); `AltChain=0`: a / b / d pass (0.30 s, 100 %, 0 ground, 0 webs on nothing, 0 overlap); c (road band) not measured (no render) |
| 2 foliage <= 40 %, ropes through crowns | leaf fade built into `M_CityLeaves`, not measured on renders; ropes through crowns on merge-only sims: r1 / r4 / r5 **0 frames** |
| 2 r1 / r4 frame differences | merge alone changes r1 from 3.95 s and r4 from 2.57 s (sims); island-side diffs not measured (no render) |
| 3 r1-r5 from one build | **not done** |

## 0. Integration merge
`git merge origin/Opus-5.5-Loop-Night-1` at 8b7a8301 (352 commits since aad3ac3: traversal r25 / r26 — new camera, rope material, original
default suit — city r11, terrain r05, characters r17): **no conflicts** (merge commit 70ce4f12). Island-owned files the merge changed:
`Scripts/build_city.py` (city r11: facade F0Scale 0.8 -> 0.25, grazing-angle curtain glass, far-LOD tower / hinterland panel structure,
FarLitK / FarFill, fog start per shot, fabric without distance fields) and `tools/export/far_skyline.py` / `bake_sunmask.py`; the browser
sources (`src/`, `public/`) are unchanged, so the island export is unchanged.
C++ rebuilt with `Scripts/build_editor.sh`: 15.7 s (UBA, 20 actions), `UnrealEditor.modules -> libUnrealEditor-WebHomage.dylib`.

Merged C++ on the round-03 map (telemetry-only sim, same r3 script): identical to the round-03 capture for 648 frames (0.000 m), first
deviation at t = 10.8 s (new traversal); the fire-escape loop at x -235.5 is unchanged by the merge (6 top-out loops, stuck 2.4-8.5 s).

## 1. Fire escapes: collision = the drawn landings (round-03 critic's biggest gap)
Round 03: each fire escape was ONE solid (QueryOnly, cooked triangles): landings, 1.05 m railing planes, stair flights, drop / roof ladders.
On r3 the hero swung into the escape at x -235.5 / y 616.4 (west facade of the block x -234 .. -206, roof 37.8 m, cornice 37.9-39.05 m,
belt course 33.84-34.20 m; landings every 3.7 m from 6.1 to 35.7 m): 6 top-out loops from t = 2.4 s, stuck to 8.5 s.
Round 04 (`tools/export/street_kit.py` `fire_escape`, 8,562 fire escapes / 58,770 landings island-wide):
* **solid** (`fireescape__t*` tiles, traversal solids with their own triangles): ONLY the landings: grating top + underside, front lip beam
  and side beams; every landing has an **open well**: the flight arriving from below comes up through a 1.5 m x 0.70 m opening, the lowest
  landing has a 0.6 m x 0.5 m **drop-ladder hatch** (58,770 wells / hatches);
* **visual only** (moved into the `streetkit__t*` tiles, which are on the traversal's exclusion list): railings, brackets, stair flights,
  stringers, drop and roof ladders, and a wall angle + inner frame rail;
* the landing grating (drawn and solid alike) starts **0.40 m off the wall** (r03: 0.02 m): a 0.38 m slot along the facade. Reason, measured
  below: the traversal's wall-run "wall top ahead" probe looks ~0.6 m inward of the hero; a landing reaching the wall is a "wall top" for a hero
  running up the facade under it, and the run top-out (fixed 11.5 m/s hop, ~3.5 m) cannot clear the landing 3.7 m above.

Sim evidence (telemetry-only, `-nullrhi`, fixed 1/60 s step, merged C++; tiles -2_2 / -1_2 / 0_2 patched with `build_manhattan.py --steps fepatch`
on the round-03 map), checker `tools/export/island_fe_check.py` (from t = 2.4 s):

| variant | top-outs at the r03 spot | 1 s windows < 3 m at the spot | hero at t = 3.5 s | free of the spot |
|---|---|---|---|---|
| r03 layout, merged C++ (`sim_base`) | 6 loops | 2.4-8.5 s | x -235.44, z 33.5 | 8.7 s |
| r04a: landings solid to the wall, railings / stairs visual-only | 3 (loops 2) | 2.4-4.4 s | x -235.01, z 34.0 | 4.9 s |
| V1 diagnostic: whole escape visual-only | 2 (belt course 34.2 m, then cornice) | none | x -234.5, z 37.4 | 3.9 s |
| **r04 final: landings solid from 0.40 m off the wall** | **0** | **none** | **x -218.1, z 46.1 (swinging east)** | **2.7 s (wall kick + release)** |

## 2. WHBox rule 5: drawn building mass without a box (raw hollow guard)
Round 03's raw (un-eroded) hollow went up from 16.72 % (M1) to 17.68 % (whole island). Of the 17.68 %, 13.26 % are 1-cell facade rims
(a box within one cell reaches the drawn height: raster rounding of facade edges) and 0.77 % 2-cell rims; **3.64 %** were real: drawn
mass with no box at all (1.27 %) or a box far below the drawn top (2.37 %) — the largest patches are the west-side pier sheds
(11-15 m, 200 m x 40 m; collision kind `pier` is not a kept box kind), stepped crowns, buildings whose solid is not a kept kind.
`tools/export/island_boxes.py` rule 5 (`fill_hollow`): those cells (not within 2 cells of a box that reaches their height), in 8-connected
patches >= 16 m2, are covered by maximal rectangles (min 2 x 2 m) with top = the 10th percentile of the drawn top in the rectangle,
bottom 0, up to 3 passes for stepped roofs: **+2,574 boxes (175,671 total), 51,353 m2**.

| audit (`tools/export/island_coll_audit.py`, whole island x +-1024 / y +-3584 m, 4.07 M building cells) | r02 (M1) | r03 | **r04** |
|---|---|---|---|
| I5 phantom (interior) | 0.26 % | 0.25 % | **0.25 %** |
| I5 hollow (interior) | 0.22 % | 0.37 % | **0.36 %** |
| raw phantom | 1.16 % | 1.35 % | **1.35 %** |
| raw hollow | 16.72 % | 17.68 % | **16.43 %** |
`coll_audit.json`, `coll_audit_map.png`.

## 3. Foliage: the lens out of street-tree crowns (guard: never > 40 % of the frame on r1 / r4 / r5)
`M_CityLeaves` (build_city.py `make_leaves`): leaf cards within 3.5 m of the camera are cut and dithered out up to 8.5 m (4 cm world-space
hash; shadow passes use their own view origin, so the crowns keep their shadows). Checker `tools/export/island_foliage_check.py`: share of
green-dominant pixels per frame at 4 fps; on the round-03 movies it reads the critic's numbers (r1 t = 17.25 s 73.7 % vs critic 72 %,
t = 23.25 s 72.3 % vs 75 %; r4 t = 15.5 s 79.9 % vs 62 %; r5 t = 6.75 s 79.4 % vs 78 %, t = 25.25 s 77.3 % vs 68 %): `foliage_r03_*.json`.

## 4. Ropes through crowns
`tools/export/island_rope_canopy.py`: rope segment (hand -> anchor) per frame against the 38,818 street-tree crowns of the build (ellipsoids
from the ez_street leaf protos, inner 80 %). Round-03 captures: r1 8 frames (t 17.2, 23.2 s), r4 0, r5 63 frames (incl. 10.97 and 25.3 s, the
critic's 10.2 / 26.8 s). The island cannot keep anchors off crowns without making crowns solids (they would become floors / web targets):
`../REQUEST-traversal-r04.md` §1.

## 5. The merged traversal on the island routes (telemetry sims, round-03 map + merged C++)
| route | first deviation from the round-03 capture | note |
|---|---|---|
| r1 | t = 3.95 s (air release) | traversal r25 / r26 (release / camera changes) |
| r3 | t = 10.8 s | before that identical (incl. the fire-escape loop) |
| r4 | t = 2.57 s (wall run) | |
| r5 | t = 1.68 s (air release) | **r24 altitude chain** (`AltChain = 1`, default since the merge): releases solved for a 33 m apex, ~1.5-5.5 s between webs. Swing pass lines on the merge-only map: max re-web gap **5.55 s**, 33 % of gaps <= 0.5 s, 744 m, ends y 1528 (FAIL). The same route with the script tune `AltChain=0` (`scripts/r5_m2_avenue_alt0.json`, the r23 chain) on the same map: **max gap 0.30 s, 100 % <= 0.5 s, 0 ground frames, 0 webs on nothing, 0 fall / stuck / mid-air / wall-air, 0 overlap, 1,481.6 m** (= round 03) |
So r1 / r4 frames differ from round 03 from the first seconds because of the merge alone; round-04 r1 / r4 are compared with these
merge-only sims (`sim_merge/*`, section 7) to separate the island's own changes. Ropes through crowns on the merge-only sims: r1 0, r4 0, r5 0 frames.

## 6. Fresh rebuild (SPEC I8) — STOPPED, partial, measured
`docs/night1/island/build_r04.sh` (= `build_manhattan.py --steps cpp,city,traversal,characters,look,map` with `SM2_ISLAND_GPU_SLOT=1`: every
commandlet its own `gpu_slot.sh capture --label island` hold, `-nullrhi`). Content/City, Content/Tests/City and the WP map were deleted on
disk at 16:49 (build_city's own `clean` loads every asset to delete it: 346 meshes in 6 min, stopped; the on-disk delete takes < 1 s).
Inputs: the island export (browser sources unchanged by the merge, so `city_export` / `city_prep` were not re-run: they need a vite
listener; r03 timings 172 s + 885 s), `city_extra` re-run (188 s) and `street_kit.py` re-run (215 s).

| commandlet | hold s | what |
|---|---|---|
| cpp (`build_editor.sh`) | 4 (15.7 s on the first, real rebuild after the merge) | |
| city_a `clean,tex` | 92.6 | |
| city_a2 `mat` | 54.2 | |
| city_mesh_00 / 01 / 02 | 2,338.4 / 1,960.2 / 685.0 | all 1,642 tile meshes (640 / 802 / 200): ~1-2 s per mesh, ~15-35 s per `detail` (Nanite, full fallback) mesh |
| city_proto_00 | 328.4 | |
| city_kit_00 / 01 / 02 | 1,885.1 / 1,510.0 / 2,403.3 | 128 of 136 street-kit tiles, ~25-60 s per tile (Nanite + distance field, built twice: the import does not apply full-precision UVs / tangent settings, `finish_mesh` logs the difference) |
| **sum so far** | **11,262 s (3.1 h)** of holds, 16:49 -> 20:17 wall | |
city_kit_02 printed its `DONE` at 1,901 s of script time but the engine had not exited when gpu_slot's 2,400 s max hold terminated it
(rc 124; a `-nullrhi` commandlet, every asset already saved). From 20:33 the GPU lock was paused by the health monitor
(`WindowServer starved (gpu 100 % ws_cpu 0)`, screencapture probe failing, **no Unreal or Blender process running**); my next kit
commandlet waited 60 min (gpu_slot exit 75), re-queued, and at 21:50 I stopped the build driver (no engine was running).
**Not built yet:** 8 street-kit + 136 fire-escape tiles, `fsky,map,coll`, `wp` (WP map + 175,671 WHBoxes), traversal, characters, look,
`manhattan_map`. Projection from the measured rates (NOT a measurement): ~4,300 s kit + ~600 s b + ~1,700 s wp + ~1,000 s rest = a fresh
rebuild of ~18,900 s (~5.2 h) of commandlet time, against the SPEC I8 target of <= 90 min. Content now 1.2 GB (r03 complete: 1.5 GB).
Resume: `SPLIT_FROM=kit docs/night1/island/build_r04.sh` (the kit step imports only missing tiles).

## 7. Captures — NOT DONE
There is no playable island map until the rebuild finishes (WP map deleted for the fresh build): r1-r5 were not re-captured this round;
the critic pack was not built. Evidence this round is telemetry-only (sims on the round-03 map + merged C++, `sims/`).
