# Request to traversal (piece P3) from the Island (piece A), round 02

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Filed 2026-10-01 by the island builder. The island never edits `Source/WebHomage/Traversal`; these are asks, with the island-side facts.

## 1. Index WHBox cube ISM instances per instance in SolidMode 2

**Why:** the island's `SM2_WHBOX_MODE=ism` build puts the ~57 k WHBox cubes in 58 always-loaded actors (one invisible
`InstancedStaticMeshComponent` of `/Engine/BasicShapes/Cube` per 256 m tile). It builds the WP map in ~20 s instead of 1,077-2,203 s
(actor mode), and it is the only way the whole island (~140 k boxes, M2) can be built at all.

**What breaks today (WebTravWorld.cpp, round 20, `Init`):** in `SolidMode == 2` the `IsTravCube(P)` branch runs before the ISM branch and
calls `AddBox(P->Bounds.GetBox())` once per *component*. An ISM cube component is accepted by `IsTravCube` (it is a
`UStaticMeshComponent`, invisible, mesh `Cube`), so each tile's ~1,000 boxes collapse into ONE 256 m index box. The anchor / canyon /
zip-point / perch logic would then see a 256 m block per tile.

**Ask:** in the SolidMode-2 cube branch, when `P` is an `UInstancedStaticMeshComponent`, add one box per instance (as the old SolidMode-0
ISM branch does: `GetInstanceTransform(I, T, true)`, `AddBox(MeshBounds.TransformBy(T))`, fill `InstToBox`) and keep the component
de-collided (index only). The `bHasBoxes` probe at the top of `Init` already accepts ISM cubes.

**Until then:** the island keeps actor-mode WHBox cubes as the default (`SM2_WHBOX_MODE=actor`); `Manhattan_WP` is built that way.

## 2. Default for instanced props / trees (`-WHTravIsmSolid`)

r02 makes the A/B meaningful: every instanced prop that is not on the r20 exclusion list (benches, pit fences, planters, kiosks,
bus shelters, dumpsters, parked cars, tree barks ...) now carries cooked triangle collision with its collision **off** and BlockAll
responses (`build_city.py proto_ab()`). r20's default (`-WHTravIsmSolid=0`) is unchanged; with `=1` the traversal re-enables them
(QueryOnly). Sheds, shed tops and subway entrances are solids in both modes. The measured A/B (stuck frames, trunk-overlap frames, same
r1 route, fixed 1/60 s step) is in `docs/night1/island/round-02/README.md` ("IsmSolid A/B"); the default decision is traversal's.

## 3. topOut loop under a fire-escape deck (r02 r3 take 2, measured)

`round-02/r3_crosstown_east_telemetry.csv` t 2.50 - 8.50 s: after a swing into the west face of the block at x -234 m (wall top 37.8 m,
parapet to 38.95 m), the hero stays in `air / topOut` at x -235.5, y 616.4 for 6 s, bouncing between feet z ~32.5 and ~35.5 (vz +9.9 m/s
kicks every ~1.3 s). The face carries a fire escape (kit decks at 28.3 / 32.0 / 35.7 m, outer edge x -235.15). The top-out keeps
re-launching from the 32.0 m deck into the underside of the 35.7 m deck (headroom 3.6 m) instead of giving up / letting the swing
button fire a web: no web for 6.43 s while swing is held. This one event fails critic test 1 (each release -> next web <= 0.5 s).
Ask: abort top-out when the climb path is capped by an overhang (or after one failed attempt) and allow webs from `topOut`.
The geometry is what is drawn (decks are real platforms, traced complex); the island will not remove fire escapes to avoid it.

## 4. Wall-run passes through overhanging decks (r02 r4, measured)

`round-02/r4_wallrun_roofs_telemetry.csv` t 17.37 - 18.83 s: wall-running up the south face at y 151.38 (x 285 -> 281.6), the feet
pass through three fire-escape kit decks (z ~9.5, ~13.2, ~16.9 m; up to 0.72 m capsule penetration, 18 frames with the feet column inside
the deck; `round-02/route_check_r4.json` drawn.events.feet_overlap). `PushOutCapsule` keeps only horizontal MTD directions (|N.xy| >= 0.3),
so a deck met from below while wall-running never stops the climb. Ask: in wall mode, a vertical sweep (feet -> head) against Allowed
solids; on an overhang either stop the climb (hang / drop) or top-out onto the deck. Also seen: 2-4 frames of parapet / coping overlap
during each top-out (r4 t 3.35, 19.33 s).
