# Island (piece A) — round 02: collision = what is drawn, under traversal r20

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Still M1 (Midtown 7 x 9 tiles); M2 waits. Branch `night1/island` = r01 + merged `Opus-5.5-Loop-Night-1` (traversal r20, SolidMode 2:
every visible mesh is a QueryOnly solid traced complex, WHBox cubes are an index only). Merged as-is, r01's build had no solids at all
(it stripped collision from every non-ground mesh). All captures: REAL game (`-game`, offscreen, `Scripts/run_game.sh`), map
`/Game/Maps/Manhattan_WP`, every run inside `gpu_slot.sh capture --label island` (holds `contaminated=true`: not perf runs, no frame
times here). Internal resolution: no `r.ScreenPercentage` passed (CAPTURE.md auto: **1920x1080 output = 1399x787 internal, TSR**;
3840x2160 stills = 1920x1080 internal).

## What changed (all script-generated; no Content committed)
| change | where |
|---|---|
| Cooked triangle collision (CTF_UseComplexAsSimple, no simple shapes, full Nanite fallback) + QueryOnly BlockAll components on every mesh r20 treats as a solid: facade, roofs (parapets + copings are drawn in the ROOFS mesh), detail (browser fire escapes), landmarks, plazas, podiums, bridges, seawalls, facadeLod masses. `solid_rec()` mirrors r20's exclusion list. In-place step `collide` (466 meshes, 275 s) | `Scripts/build_city.py` |
| Fire escapes of the Unreal street kit in their own tiles `fireescape__t*` (50 tiles, 1.26 M tris, solids); `streetkit__t*` (awnings, boards, storefronts) stays visual-only | `tools/export/street_kit.py`, `build_city.py` kit step |
| Sheds / shed tops / subway entrances (instanced, the meshes r20 keeps solid) carry cooked triangles + QueryOnly | `build_city.py` proto / `make_ism` |
| Every other instanced prop (benches, pit fences, barks, parked cars ...) carries cooked triangles with collision OFF: r20's default unchanged, `-WHTravIsmSolid=1` can re-enable them (A/B) | `build_city.py proto_ab()` |
| Bridges + river seawalls were 1.3-2 km components: r20's "giant" rule de-collided them INSIDE M1 (Queensboro approach from x 261 m). Split into <= 256 m pieces (194 pieces from 20 meshes) | `tools/export/split_giants.py` (city_prep) |
| WHBox cubes: actor mode, index only (r20 de-collides them). ISM cubes stay non-default: request filed | `REQUEST-traversal-r02.md` §1 |
| Checkers: drawn-surface support, capsule overlap (R 0.36 m) with collision.json parapet / coping / fire-escape / trunk solids + kit decks + UE street trunks, web/wall on drawn mass, re-web gaps; dump checker; r4 run/drop checker | `tools/export/island_route_check.py`, `island_dump_check.py`, `island_r4_check.py` |

Rebuild: `SM2_ISLAND_CITY_STEPS=kit,collide,map,wp python3 unreal/WebHomage/Scripts/build_manhattan.py --steps city,map` (2,743 s),
then `rebuild_r02b.sh` (split pieces: `SM2_ISLAND_MESH_ONLY=split SM2_ISLAND_CITY_STEPS=mesh,map,wp`, 2,244 s; WP populate 967 meshes =
117 ground / 532 solid / 291 visual-only, 100 kit actors, 56,816 WHBox actors).

## Test 1 — game log + primitive dump (`dump_check.json`, `prims_dump.csv.gz`, `warmup_webtravworld_log.txt`)
Game log: `WebTravWorld: solid mode 2 (visual triangles ... WHBox cubes index only)`; `0 with collision re-enabled` (the build already
made them QueryOnly), `56816 WHBox cubes de-collided`.
| check | result |
|---|---|
| visible SM_facade / SM_roofs / SM_detail / SM_fireescape tiles: role solid, ctf 3 (ComplexAsSimple), QueryOnly | **45 / 45 / 45 / 45 OK, 0 bad** (the 45 tiles streamed in at init; every solid row is ctf3 + coll1: 490 / 490) |
| sheds / shed tops / subway | 46 / 46 / 16 solid, ctf 3, QueryOnly |
| WHBox cubes with collision after init | 0 of 56,816 (index only) |
| far-off rows inside M1 (first build) | **6 centres inside / 9 overlapping: FAIL** -> bridges, seawall, Roosevelt Island land, far-shore tiles |
| after `split_giants.py` (r1 / r4 game logs; final dump `dump_check_final.json` from the A/B run) | far-off components 93 -> **72** (default mode), visible solids 490 -> **642**: bridges + seawalls are solids now. Final dump: far-off rows with centre inside M1 **2: FAIL by 2 rows, both scenery by design**: `SM_farLand_roos` (flat Roosevelt Island land strip, z 1 m, far by name) and `SM_hinterland` (the 34 km horizon ISM, centre falls inside; `excluded-ism` in default mode). Overlapping the M1 box: + far shore `SM_farCity*__t0_-1` (from x 882 m), `SM_farLand_east`. No drawn M1 building / bridge / seawall is de-collided |

## Test 2 — critic test 1 on r3 take 2 (x -300 / 40 m / 26 m/s, swing held; `route_check_r3.json`)
r3 was captured on the first r02 build (before the bridge split; nothing near y 640 m changed).
| | target | r01 take 1 | **r02 take 2** |
|---|---|---|---|
| ground + land frames | <= 10 % | 82.9 % | **0.0 %** PASS |
| distinct swing anchors | >= 10 | 2 | **21** PASS |
| webs on nothing (drawn check / WHBox check) | 0 | 0 / 0 | **0** / 1 (an anchor on drawn mass > 1 m from any WHBox) PASS on drawn |
| each release -> next web | <= 0.5 s | no re-web at all | **8 of 13 <= 0.5 s; max 6.43 s: FAIL** |
The 6.43 s gap (t 2.4-8.8 s) is a `topOut` loop under a fire-escape deck: the hero bounces between the 32.0 m and 35.7 m kit decks of
the west face at x -234 (frame `stills/r3_crosstown_east_t5s_1920x1080.jpg`), no web while topOut. Collision is right (he stands on the
deck, never inside it); the loop is traversal state logic -> `REQUEST-traversal-r02.md` §3. The other 4 gaps > 0.5 s (0.77-1.43 s) are
re-press -> attach delays with the script's 0.3 s re-press gap.

## Test 3 — critic test 2: capsule never inside parapet / trunk / fire escape (`route_check_r*.json`, `r4_check.json`)
| route | r01 overlap frames (kind) | **r02** |
|---|---|---|
| r1 north avenue | 0 | **0** |
| r2 south avenue | 46 (parapet 38, coping 48) | **0** |
| r3 crosstown | 140 (trunk: ran through street trees on the sidewalk) | **7** (fire-escape kit, 0.09-0.20 m, airborne during the topOut loop; feet never inside) |
| r4 wall-run / roofs | 332 (coping 313, parapet 307, kit fire escape 22) | **31**: 24 kit fire-escape (wall-run passes up through decks, 18 frames feet inside) + 7 parapet/coping (2-4 frames per top-out, 1 swing frame) |
r4 parapet run: r01 ran 25 m INSIDE the west parapet (x 274.525, 161 overlap frames) then fell through a kit fire escape at 39.2 m.
r02: the zip now ends on the bulkhead top (48.4 m), the run drops to the roof and **ends in a vault over the north parapet** (t 13.47 s,
0 overlap frames during the run, frame check: hero on the coping). The drop then lands on the **street** (feet -0.06 m, no platform
passed through), not on a fire escape / roof: there is none under that line. The wall-run through decks is traversal's (MTD push-out is
horizontal only) -> `REQUEST-traversal-r02.md` §4.

## Test 4 — no regression
| line | target | r02 |
|---|---|---|
| I5 phantom / hollow (`coll_audit.json`) | <= 1 % / <= 2 % | **0.26 % / 0.22 %** (unchanged) |
| I6 fall / stuck / mid-air / wall-air, drawn checks | 0 | r1 **0/0/0/0**, r2 **0/0/0/0**, r3 **0/0/0/0**, r4 **0/0/0/0**. The old WHBox-based columns: r3 wall-air 8, r4 mid-air 2 + wall-air 23 — all on drawn surfaces (fire-escape faces, bulkhead tops) that have no WHBox; r20 no longer collides with WHBoxes |
| `-WHTravIsmSolid=1` A/B on r1 (stuck + trunk overlap) | reported | see below |
| I2 facadeLod >= 1.2 km | (M2) | 379-784 m on r1 / r3 / r4; **r2 now swings 1,273 m (r01: 801 m) and leaves M1 at y ~1,024 m after ~19 s** (frame `stills/r2_south_avenue_t20s`: facadeLod masses on plain ground). Its two webs past y 1,024 hit facadeLod walls (point-to-triangle 0.00 / 0.02 m): the far masses are solids too. Route 2 needs a later start / M2 |

## IsmSolid A/B (r1, fixed 1/60 s step; `route_check_r1.json` vs `route_check_r1_ism_solid.json`, `r1_ism_solid_log_excerpt.txt`)
| | default (`-WHTravIsmSolid=0`) | `=1` |
|---|---|---|
| traversal solids (game log) | 642 visible solids, 0 re-enabled | 3,955 visible solids, 3,313 re-enabled (QueryOnly) |
| stuck events | 0 | 0 |
| capsule overlap with trunks (collision.json CYL + UE street trees) | 0 | 0 (r1 never runs the sidewalk tree line; r01's r3 had 140 trunk frames) |
| path in 30 s / distinct swing anchors / max re-web gap | 1,166 m / 15 / 1.73 s | 942 m / 15 / 1.52 s |
| webs | all on buildings | one web on a street-tree branch (12.2 m, 2.5 m from the trunk at x 259.9 y 209.9, t 3.48 s) |
Island view for traversal's default decision: trees and props can be solids at no measured stuck cost on r1, but they also become web
targets (a branch anchor at 12 m); a trunk-run test needs a sidewalk route (r3 of r01 style).

## Files
`r1_north_avenue.mp4`, `r2_south_avenue.mp4`, `r3_crosstown_east.mp4`, `r4_wallrun_roofs.mp4` (1920x1080 60 fps, H.264 2-pass, <= 14.7 MB); `stills/a1_high_{north,south}_*_3840x2160.jpg` + `_telemetry.csv`
+ `_log_excerpt.txt`; `stills/` contact frames; `route_check_*.json`, `route_check_r01_baseline.json` (r01 telemetry under the r02
checker), `r4_check.json`, `dump_check.json`, `dump_check_final.json`, `prims_dump_ism_solid.csv.gz`, `route_check_r1_ism_solid.json`, `coll_audit.json`, `split_giants.json`, `gpu_hold_*.json`.
Critic pack (9 pairs: v1-v4 routes, s1/s2 4K stills, s3/s4 frames, p1 = r4 of r01 vs r02 on the same input): `/Users/midir/sm2-n1/_scratch/critic-A-r02/pack`
(key `pack.key.json` beside it; inputs `pairs.json`; built by `docs/night1/island/critic_prep_r02.py` + abpack).
