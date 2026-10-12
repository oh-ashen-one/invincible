# Island r01 — Phase-0 measurements (full-island spike + Midtown M1 build)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

All numbers measured on the Mac Studio on 2026-10-01 (logs under `/Users/midir/sm2-n1/_scratch/island/logs/`, a symlink to the SD card).

## Full-island export spike (`tools/export/island_spike.py --measure`, exporter `--nofar --measure`, 13:02-13:07)
| district | tiles (ix0,iz0,ix1,iz1) | tiles / with geometry | tris | GLB GB | JSON MB | collision solids | page ready s | collect s |
|---|---|---|---|---|---|---|---|---|
| midtown (M1) | -3,-5,3,3 | 63 / 55 | 8,815,271 | 1.127 | 111.8 | 401,161 | 81 | 30 |
| midtown_w | -4,-5,-4,3 | 9 / 0 | 0 | 0 | 0.4 | 2,078 | 26 | 0 |
| fidi | -4,8,3,13 | 48 / 27 | 2,712,294 | 0.348 | 54.3 | 193,593 | 26 | 10 |
| village | -4,4,3,7 | 32 / 28 | 4,187,860 | 0.539 | 53.5 | 198,310 | 26 | 15 |
| upper | -4,-9,3,-6 | 32 / 24 | 3,222,564 | 0.419 | 48.5 | 142,667 | 26 | 12 |
| north | -4,-14,3,-10 | 40 / 25 | 3,131,416 | 0.413 | 37.8 | 143,691 | 24 | 12 |
| **island** | -4,-14,3,13 | **224 / 159** | **22,069,405** | **2.85** | **306** | 1,081,500 | | **79 s collect, 295 s wall** |

## Midtown M1 build (`build_manhattan.py`, all headless `-nullrhi` commandlets, one at a time)
| step | seconds | note |
|---|---|---|
| city_export (55 geo tiles) | 153 | Vite :5208 + export_city.mjs, 2.3 GB export folder on the SD card |
| city_prep | 288 | patch_export, prep_textures, street signs / kit / props, shaders |
| city_extra | 41 | sun mask (2048 x 8192), vehicles, far skyline, street cars / traffic / trees |
| city (import pass, 13:20-14:24) | 3,862 | textures 6 s, materials 2 s, **meshes 2,470 s (793)**, protos 164 s, kit 558 s, far sky + maps 28 s, **classic WHBox level 610 s (53,405 cubes)**; the process then got the 14:24 system quit (reboot) inside the WP step |
| city, step `wp` only (re-run 14:41-14:59) | 1,077 | populate 13 s, **53,405 WHBox actors 1,040 s**, save 59,574 external-actor packages |
| traversal / characters / look / map | 36 / 97 / 13 / 69 | |
| **total, fresh Content -> playable** | **~5,640 s = 94 min** | target for the WHOLE island: <= 90 min -> M1 alone already misses it |

Content after the build: **1.4 GB** (City 430 MB, WP external actors 289 MB = 59,574 packages, Characters 495 MB, Tests 131 MB, Traversal 64 MB).
Internal disk 177 GB free after the build (gate 150 GB); the export / GLBs live on the SD card only.

## Whole-island extrapolation (linear in tris / boxes; to be re-measured in M2)
- tris x 2.50 -> mesh import ~6,200 s (103 min); WHBox actors ~133 k -> ~45 min in the WP step (+ ~25 min if the classic collision level is still built).
- Estimated fresh island build **~4 h** vs the 90 min target: **fails** unless (1) the classic `City_Midtown_Geo` / `City_Midtown_Collision` pass is dropped
  for the WP map (saves the 610 s duplicate box pass), (2) WHBox cubes become per-tile collision-only meshes / ISM bodies instead of one actor
  each (53 k actors = 1,040 s and 59 k packages), (3) mesh import is split per district across 2 commandlets (PLAN allows 2 `-nullrhi`).
- Content estimate ~3.5 GB (<= 40 GB: passes by a wide margin).

## Collision audit (`tools/export/island_coll_audit.py`, M1 region, 1 m grid, 1.5 m tolerance)
| line | target | measured |
|---|---|---|
| I1 facadeLod meshes inside the detailed region | 0 | **0** |
| I5 phantom (box above the drawn roof) | <= 1 % | **0.21 %** (mass > 6 m: 0.18 %) |
| I5 hollow (drawn building without a box) | <= 2 % | **5.81 %: FAIL** (mass > 6 m: 0.39 %, i.e. most hollow cells miss by less than 6 m of height; not yet located on the map) |

## Resume 17:05 (after the owner's 15:41 pause): rooftop equipment boxes
- Cause of the I5 hollow FAIL: hollow interior cells had drawn top - box top = **5.02 m median** (IQR 4.98-5.07 m, roofs median 132 m).
  Every sampled cell sat under a collision.json BOX solid of kind `equipment` (mechanical penthouse / plant room, drawn in the roofs mesh)
  that the WHBox rule did not keep. Fix: `island_boxes.py` rule 4 keeps equipment BOX solids >= 2 m in both horizontal sides and >= 0.8 m tall.
  Size sweep (simulated on the audit grid): min side 1.2 m -> +9,491 boxes, hollow 0.20 %; **2.0 m -> +3,411, hollow 0.22 %** (chosen);
  3.0 m -> +1,746, 0.31 %; 4.0 m -> +894, 0.58 %; 6.0 m -> +176, 1.11 %.
- Audit after the fix (`round-01/coll_audit_equip.json`, map `coll_audit_equip_map.png`; before: `coll_audit_before.json`):

| line | target | before | after |
|---|---|---|---|
| I1 facadeLod meshes inside the detailed region | 0 | 0 | **0** |
| I5 phantom | <= 1 % | 0.21 % | **0.26 %** |
| I5 hollow | <= 2 % | 5.81 % FAIL | **0.22 % PASS** (mass > 6 m: 0.02 %) |
| WHBox cubes | | 53,405 | 56,816 |

- WP-only rebuild with the new boxes (`SM2_ISLAND_CITY_STEPS=wp build_manhattan.py --steps city,map`, 17:09-17:47): city/wp **2,203 s**
  (vs 1,077 s for 53,405 boxes at 14:41) + map 54 s. Spawn rate fell from ~51 actors/s to ~19 actors/s past 45 k actors: one actor per box
  scales super-linearly in a WP commandlet. The whole island (~140 k boxes) cannot use one actor per box; per-tile collision bodies
  (one ISM / merged collision-only mesh per 256 m cell) are required for the 90 min target.

## Per-tile collision ISMs (`SM2_WHBOX_MODE=ism`, test map `/Game/Maps/Manhattan_WP_ism`, 18:22)
- WP step **45 s** (vs 2,203 s with one actor per box), map step 48 s; 58 tile actors, 56,816 instances; external-actor packages 6,227 / 88 MB
  (actor build: 62,985 / 303 MB). Content total 1.5 GB.
- Headless inspection (`-nullrhi` commandlet, `_scratch/island/jobs/ism_inspect.py`, 21:13): 58 always-loaded tile actors, 56,816 instances,
  0 components that are not invisible + BlockAll + `/Engine/BasicShapes/Cube`; 40 sampled instance transforms match `whboxes.json` exactly
  (0.000 cm centre / size error). **Not yet verified in the running game** (traversal ISM indexing + capsule collision): queued as hold B.
