# Request to traversal (piece P3) from the Island (piece A), round 04

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Filed 2026-10-03 by the island builder (round 04). The island never edits `Source/WebHomage/Traversal`. Open items of
`REQUEST-traversal-r03.md` (§0 streamed cells are not indexed, §2 wall-run up through decks) stay open; this file adds what round 04 measured.
Numbers: `round-04/README.md`.

## 1. Ropes through street-tree canopies (critic r03: r5 t = 10.2 s and 26.8 s)
Street trees are instanced props and not traversal solids (r20 default `-WHTravIsmSolid=0`; they must not be floors or web targets), so
`FWebTravAnchors::Confirm` (`World.Raycast` skips non-`Allowed` components) accepts a facade anchor whose rope line crosses a crown.
Island side there is no lever that does not turn crowns into solids. Ask: in `Confirm`, reject (or score down) a candidate whose segment
hand -> anchor passes through a tree crown: e.g. an extra `LineTraceSingleByObjectType` that does NOT skip the `ExcludedComps` whose mesh name
contains `leaves` / `crown` (ISM `ISM_ez-street*_leaves`), or a sphere test against the crown instances' bounds.
The island measures it per frame (`tools/export/island_rope_canopy.py`: rope segment vs crown spheres from `streettrees.json`).

## 2. Top-out from a fire-escape railing into the landing above (r3 crosstown east, open since r02)
Round 04 moved the railings, stair flights and ladders of the island's fire escapes to the visual-only street-kit tiles (only the landings
with their stair wells / ladder hatches are solids), which removes the railing "wall" the hero topped out from (6 top-outs at x -235.5 m in
r03). The traversal-side guard is still worth having for any wall with an overhang 2-4 m above its top: abort `StartWallHop`'s run
top-out when a ray up from the hop apex hits a ceiling, and allow a web from `topOut`.

## 3. Camera inside tree crowns
Island side since round 04: `M_CityLeaves` cuts leaf cards within 3.5 m of the lens and dithers them out to 8.5 m (round-04 README for the
measured foliage share). A camera-only probe against crowns (REQUEST-r03 §3) would still keep the lens out of the trunk / branch meshes.

## 4. Short-rope stalls on r3 (merged traversal, not fire escapes)
Round-04 r3 sim (`round-04/sims/fe_final_gap040_r3_telemetry.csv.gz`): 1-s windows with < 3 m of movement at t 4.0-5.2 s (x -208, rope 3.25 m),
10.0-11.1 s (x -84, rope 7.85 m), 15.3-16.4 s (jump launch in place at x -90), 18.8-19.9 s (x -85), 24.1-25.3 s (x -39, rope 1.05 m) — swings
on anchors a few metres from the hero near facade tops, no fire escape within 12 m. Ask: a minimum rope length / a minimum anchor
distance for re-anchors, as for the r20 "must be >= 4 m in front of the face" rule of the WHBox face candidates.

## 5. r5 re-web gaps with the r24 altitude chain
Default `AltChain = 1`: r5 (M2 avenue, swing held, autoChain gap 0.3 s) max re-web gap 5.55 s, 33 % of gaps <= 0.5 s, plus a top-out loop at
(-44, 1246) 12.0-14.5 s; with `AltChain=0` the same route passes (0.30 s, 100 %). If the altitude chain is the intended default, the island
measures r5 with the tune and reports both.
