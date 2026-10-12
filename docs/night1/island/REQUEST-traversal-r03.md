# Request to traversal (piece P3) from the Island (piece A), round 03

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Filed 2026-10-02 by the island builder (round 03, M2 whole island). The island never edits `Source/WebHomage/Traversal`. The fire-escape
top-out loop, the wall-run through decks and camera-in-foliage are explicitly *not* island work this round (director's brief); they are
filed here with the island-side facts. Items 1-2 repeat `REQUEST-traversal-r02.md` §3-§4 (still open).

## 0. Index the collision of cells that stream in AFTER BeginPlay (found 2026-10-03, the biggest open item for "swingable everywhere")
`AWebTravCharacter::BeginPlay` calls `Traversal->InitWorld(GetWorld(), this)` with the pawn at the map's PlayerStart, and only then teleports
to the script spawn. `FWebTravWorld::InitWorld` walks `TActorIterator<AActor>` once and fills `AllowedComps`; `Raycast` ignores every component
that is not in it (`Allowed()`). On the whole-island World Partition map only the cells inside the 1.2 km loading range of the PlayerStart exist
at that moment, so a cell that streams in later is **not a traversal solid** (no web anchor, no wall, no roof; the always-loaded ground still
catches the hero). Measured on `Manhattan_WP` (PlayerStart y 178 m): the 775 solids of `round-03/prims_dump.csv.gz` include 55 facade / roofs /
detail / fire-escape tiles with centres y -896 .. 1404 m (tile rows to y 1536); in 17 telemetry-only runs of 30 s swing chains from y 1010 on the default map the last
web anchor is always y <= 1,506 m and the hero then falls to the street (e.g. x 250 route: last anchor (195.6, 1490.4), ground at y 1551;
spawn at y 1700 = no web for 1.6 s, ground at 1.67 s). With an extra always-loaded World Partition streaming source at (250, 1560) (`Scripts/island_wp_sources.py`, island build) the same
engine, content and route index 918 instead of 775 solids and the 30 s route r5 passes its swing lines (round-03/README.md).
Ask: re-index when World Partition cells load / unload (e.g. `FWorldDelegates::LevelAddedToWorld`, or `UWorldPartitionSubsystem` cell-loaded
events, or a 1 Hz rescan of `Allowed()` misses), at least for the facade / roofs / detail / fireescape / ground components. The island's content-side workaround is one extra streaming source per area to be
swung in (it also works as a load-everything switch, at the cost of start-up time and memory that the island has not measured).

## 1. topOut loop under a fire-escape deck (open since r02)
`round-02/r3_crosstown_east_telemetry.csv` t 2.50-8.50 s: `air / topOut` re-launches from the 32.0 m kit deck into the underside of the
35.7 m deck (x -235.5, y 616.4), no web for 6.43 s while swing is held. Ask: abort top-out when the climb path is capped by an overhang
(or after one failed attempt) and allow webs from `topOut`. The decks are drawn platforms (complex-traced solids); the island keeps them.

## 2. Wall-run passes up through fire-escape decks (open since r02)
`round-02/r4_wallrun_roofs_telemetry.csv` t 17.37-18.83 s: feet pass through three kit decks (up to 0.72 m capsule penetration).
`PushOutCapsule` keeps only horizontal MTD directions; ask for a vertical sweep in wall mode (stop / hang / top-out onto the deck).

## 3. Camera inside foliage (round-02 critic: r1 t=17.25 s 70 %, t=23.25 s 75 %, r4 t=15.5 s 60 % of the frame)
Street trees are instanced props without camera collision (r20 default `-WHTravIsmSolid=0`: trees are not solids). The camera boom does
not test them, so a low chase camera passes into crowns. Ask: a camera-only probe against tree crowns (ISM `ISM_tree*` / `CROWN` protos,
or a sphere sweep on the Camera channel with crowns set to Block on Camera only), or a fade of crown instances within ~2 m of the camera.
Island side: crown meshes keep their names (`build_city.py` `CROWN`), so a per-proto camera response can be set at build time if the
traversal prefers that — tell the island and it will set `Camera: Block` on the crown ISMs.

## 4. WHBox cubes as per-tile components (island r03, for information)
`Manhattan_WP` now holds the island's ~173 k WHBox cubes as plain invisible `/Engine/BasicShapes/Cube` StaticMeshComponents, one
always-loaded actor `WHBoxes__t<ix>_<iz>` per 256 m tile (`SM2_WHBOX_MODE=comp`, default). `WebTravWorld.cpp` SolidMode 2 indexes
`IsTravCube()` per component, so the index is identical to one actor per box; nothing to change. ISM instance indexing (r02 §1) is no
longer needed by the island.
