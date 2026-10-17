# Round 7 notes: piece "breach FX" (builder C: boom ring, breach holes, debris by building type, thin solids)

Source edits only. Nothing was launched in Unreal, no Blender, no GPU, no git, no `build_editor.sh` / UBT. Items from `docs/invincible/captures/r6/CRITIC.md` defect #4 (ring) and #8 (destruction).

Numbers below are **design values** or **CPU-model values** (see "Checks run"), not measurements of a render.

`-WHFlight=0` is unchanged: the director only exists in flight mode.

## Root actions needed

1. Rerun `Scripts/build_invincible_fx.py`. It rebuilds `M_BreachHole` (new graph, new parameters), `M_InvShockRing` (new Custom node, new `RimGain` parameter) and creates `M_InvGlassShard`. It still ends with `SM2_BUILD_OK: build_invincible_fx.py`.
2. Compile. `WHBreachDirector.h` gained UPROPERTYs and private members, so UHT regenerates.
3. Without the rebuilt assets the C++ still runs: the old hole look, the old ring shape, and `M_CmbTrans` for the panes (parameters set on a material that lacks them are ignored).

## Files changed

- `Flight/WHBreachDirector.h/.cpp`
- `Scripts/build_invincible_fx.py`
- this note

Not touched: `WebTravCamera.*`, `WHFlightComponent.*`, `WebTravCharacter.cpp`, `WHHeroV2AnimInstance.*`, `WHRescueDirector.*`. The public API of the director is unchanged (`OnFlightEvents`, `CutSlowMo`, `SetFlightFx`).

## 1. Boom ring (critic #4, fl04 1.517: "a soft filled disc, luma lifted evenly 131-173, no edge peak")

**Material (`M_InvShockRing` r7).** The annulus profile is now asymmetric, in band widths `dr` from the ring centre line (+ outside):
- outside: a hard leading edge, opaque to `dr` 0.08, gone by 0.42;
- inside: a soft wake, gone at `dr` -2.4;
- everything further in: opacity 0 (clear interior).

The Custom node returns `(opacity, emissive multiplier)`. The multiplier is `Gain x (0.25 + 0.75 x profile) + RimGain x hot core`. The hot core peaks at the leading edge and is gone about 0.9 band widths inside it. Emissive is still `Color x multiplier x EyeAdaptationInverse` (exposure-independent). `Soft` default 0.3, so the noise no longer breaks the rim.

**Director.**
- The main ring leads the hero: centre 0.6 m ahead of his chest, glued for 0.3 s, radius 0.5 m to `BoomRingMaxM` (4.6 m) with the existing ease-out, tube half thickness 4.5 % of radius (clamped 12-70 cm), axis = flight line.
- A weaker echo ring sits just behind the chest: radius 0.4 to 3.0 m, 60 % opacity, life 0.34 s.
- The launch ring is left where he fired: radius 1 to 14 m, 55 % opacity.
- New envelope `Env 3` for the rings: snaps in over 15 ms, holds to 30 % of the life, fades to 0 by the end. `BoomRingLife` is 0.40 s.
- The cone keeps `BoomConeOpacityK` 0.40 of its opacity (0.30 -> 0.12) and 0.7 x the life (0.6 -> 0.42 s), so the ring is the read, not a veil.
- New tunables: `BoomRingLife`, `BoomRingMaxM`, `BoomRingOpacity` 0.95, `BoomRimGain` 3.2, `BoomConeOpacityK`.
- Fallback when `M_InvShockRing` is missing: the tube ring, with its peak capped at the old boom opacity.

**CPU model of the profile** (face-on to 30 deg view, Th 20 cm, Rad 300 cm, opacity 0.95, `RimGain` 3.2, Narkowicz ACES stand-in, sky modelled at pre-tonemap 0.25 = luma 165):

| quantity | value |
|---|---|
| peak rim luma | 250 / 255 |
| rim samples >= 220 | about 0.8 band widths (16 cm at Th 20 cm) |
| leading edge, 0.78 -> 0.06 opacity | 0.32 band widths (about 6 cm) |
| interior (opacity 0) | luma 165 = the sky, unchanged |

The real tonemapper and bloom can move the rim luma. The critic test (`annulus edge >= 40 above the interior within boom +2..+10 frames`) should be read off the new capture.

## 2. Breach holes (critic #8, fl14 4.98 / fl15: "crack decals, no interior")

**Material (`M_BreachHole` r7).**
- The decal now gets its own frame from the director (`Centre`, `AxU`, `AxV`, `AxN`, `HalfCm`, `Glass`, `Seed`, `Open`, `RimCol`). It no longer uses UE's decal UV, and there is no normal output, so nothing depends on UE's decal tangent frame.
- The opening is the same ragged star as before. Its warp is reduced from +-0.08 to +-0.035 of the box so the C++ rim chunks sit on the drawn edge.
- Inside the opening the shader traces the view ray into the wall:
  - **Reveal:** wall thickness 28 cm (11 cm for glass). If the ray leaves the opening (narrowed by 12 % at depth) before the back, it hits a lit concrete / steel side wall, darker with depth, with a brighter broken edge at the opening.
  - **Room:** otherwise it enters a virtual room (floors stacked every 3.8 m by world height, side walls every 6.4 m, depth 6.2 m): floor, ceiling with light panels, back wall with a desk band and monitor glow, daylight spill near the opening, falloff with distance.
  - The room is drawn dark (floor 0.05, walls 0.055, ceiling 0.075 display-referred, light panels 0.55) as exposure-independent emissive, with a 0.2 x base-colour fallback.
- Outside the opening: the broken rim, soot and radial cracks as before (rim band 40 % thinner for glass).

**Director.**
- `FitHoleHalf` is now called once in `Breach` (it was inside `PlaceHole`), so one set of traces fits the box and measures the surface span. The minimum half size is 170 cm (was 110 cm), so a building wall never gets a hole narrower than about 1.5 m.
- `PlaceHole` passes the frame to the material.
- `SpawnHoleRim` places `RimPerHole` (10) static pieces on the outline given by `BdHoleRadius` (the shader's formula, at full growth), standing off the facade plane and lit by the scene:
  - masonry: concrete / brick slabs;
  - curtain wall: 60 % thin tilted glass teeth, 40 % dark steel plates.
  - They pop in with the opening (delay 0.04-0.20 s) and stay 25 s, in the pool `HoleRim` (`MaxHoleRim` 40, oldest recycled; 20 prewarmed). They ride the same tick as the crater rubble.
  - Only placed when the trace found a wall (`bOnWall`), and only inside 92 % of the fitted box.

**CPU check of the shader.** Six renders (front, left, right, glass front, glass right, opening at 35 %) show a dark recessed room with floor, ceiling lights, side and back walls, monitors and a grey reveal ring. No NaN or out-of-range value in 1.5 M samples (12 seeds, 2 kinds, 40 view angles to +-83 deg, 2 growth values). Max emissive 0.60, max base 0.39.

## 3. Debris by building type (critic #8, fl17 12.9: a glass tower threw bricks)

`TraceFacade(..., bDescribe)` now records, for a breach:
- `Tag`: the lower-cased component, owner, mesh and material names of the first surface;
- `bFacadeSeen`: a city facade material (`M_CityFacade`, or an instance) anywhere along the trace;
- `Style`: read from the hit triangle's vertices of the merged facade mesh. Facade.ush reads `style = UV channel 4 .y + 0.01`: 1 masonry, 2 curtain-wall glass, 3 ribbon windows, 4 deco, 5 party wall, 6 stainless crown. The face index is walked the way `GetMaterialFromCollisionFaceIndex` does it; the CPU-copy flags of the vertex and index buffers are checked first (uncooked builds keep them).

Classification (`ClassifyHit`): style 2 / 3 or a glass / curtain / mirror name = **glass**; 6 = **steel**; other styles = **masonry**. If the style cannot be read (cooked build), a hit above `TowerHeightCm` (110 m) is taken as glass and anything lower as masonry.

| kind | physics chunks (budget 24) | other | dust | rim |
|---|---|---|---|---|
| masonry | 24 concrete / brick, facade look on 50 % | 10 glints (was 26) | concrete / brick, as before | concrete slabs |
| glass | 8 steel bars / plates | 26 panes + 8 glints | cool grey, 65 % of the puffs | glass teeth + steel |
| steel | 16 steel bars / plates | 6 glints | dark, 65 % of the puffs | steel plates |

- **Panes:** 18-55 cm flat boxes, 1.6 cm thick, `M_InvGlassShard` (translucent, unlit, two-sided; mostly clear face-on, bright at grazing angles, a per-shard glint). Kinematic like the glints: ballistic, tumbling, fade in 50 ms and out over the last 45 % of a 1.2-2.3 s life. Pool `MaxPanes` 40 (26 prewarmed, `ShardsPerBreach`).
- **Steel bits:** `SpawnDebris` got `Set` (1 = bars and plates in steel tints, never the facade look) and `SizeScale`. No physics piece is thinner than 3 cm.
- **`MaxChunks` 96 and `ChunksPerBreach` 24 are unchanged.** A glass breach now uses 8 physics chunks (was 24).

## 4. Thin / non-building solids (critic #8, fl15 10.15: "a small hole in a bridge girder")

With no facade material along the trace, a hit is **thin** when:
- its tag has a bridge / girder / truss / cable / railing / pylon / beam / deck / fire escape / scaffold / crane / antenna / street kit / awning / city kit / detail / frame / signage / car / prop / asphalt / sidewalk / land / coast / water / terrain key; or
- the surface is horizontal (|Nz| >= 0.8) and not a roof; or
- the narrower in-plane run of the surface (from the `FitHoleHalf` probes) is under 2.2 m.

`ThinStrike` then gives a spark flash, 3-5 small dust puffs, 3-6 small steel bits at 0.5 scale and a quiet impact (0.30-0.45). There is no hole decal, no rim, no pane or brick debris, no `Breaches` tally and no slow-mo. It adds a small collateral entry, "structure hit" ($3k-12k).

Roofs and a landmark / podium wall without the facade material stay masonry. A trace that finds nothing keeps the old behaviour (a masonry-style hole on the flight line).

## Checks run

All CPU-only, in `/tmp/fxcheck` (not part of the repository):
- All 9 Custom-node bodies from `--dump-hlsl` compile in a small C++ shim of the HLSL subset (types, redeclarations) and evaluate. This is not an HLSL compiler: UE's own compile of the Custom nodes is still the real check.
- `build_in_unreal()` was run end to end against a fake `unreal` module, twice (create path and idempotent path): it creates 8 materials, connects the new `Emis` additional output, and prints `SM2_BUILD_OK: build_invincible_fx.py` last.
- `clang -fsyntax-only` on `WHBreachDirector.cpp` with the flags of the existing build response file (`-Wall -Werror -Wshadow -Wundef`, the shared PCH, UE 5.8 headers) and a copy of the old `WHBreachDirector.generated.h` with its line-number macros shifted: 0 diagnostics. A negative control (a missing member and an undeclared name appended to a copy) was reported as 2 errors. Nothing was written under the project; the real UHT output is regenerated by the root build.
- APIs used were checked in the UE 5.8 headers: `FStaticMeshVertexBuffer::GetAllowCPUAccess / GetNumTexCoords / GetVertexUV`, `FRawStaticIndexBuffer::GetAllowCPUAccess / GetIndex`, `FStaticMeshSection::FirstIndex / NumTriangles / bEnableCollision`, `UStaticMesh::LODForCollision`, `FMath::Frac(double)`, `FQuat::GetAxisX / Y / Z`.

## Things to look at in the next capture

Logs:
- `WH_FLIGHT breach fx r7: glass shard material M_InvGlassShard, ...`
- per breach: `surface glass tower | steel | masonry, style N` (style -1 means no CPU vertex data, so the height fallback decided); `thin / non-building solid (sparks + dust only; tag '...')`.

Frames:
- fl04 / fl12 boom +2..+10 frames: the radial luma profile around the hero, the rim against the sky, the interior.
- fl14 / fl15 / fl17 breaches: the hole interior and rim at 3-6 m; fl17 12.9 s glass tower: panes and steel, no bricks; fl15 end: sparks and dust only on the girder.

## Limits and open points

- The recessed interior is a shader illusion on the facade plane (no geometry is cut). It reads correctly for a planar wall within the decal box; at very grazing angles it shows the box-sized room only.
- Emissive in a translucent deferred decal is assumed to render. If it does not, the room shows only the 0.2 x base-colour fallback (darker) and the lit reveal and rim are unaffected.
- The room's colours, floor height (3.8 m) and light panels are generic, not tied to the real interior textures of the facade.
- Facade style reading needs CPU vertex data. In a cooked build without `bAllowCPUAccess` on the facade meshes it falls back to name keys and the 110 m height rule (and the log prints style -1).
- Name keys are substrings of lower-cased names (for example "beam", "deck", "water"): a building mesh whose names contain one of them, and whose trace shows no facade material, would be taken for thin.
- Facade scrapes (`Bump`) still use the facade material for their chips regardless of the building type.
- `-Wshadow` is on in this project's flags: new locals avoid the names of enclosing locals.

## Process notes

- One read-only `ps` listing was run to confirm no editor was running before the clang check. No process was started other than short CPU-only compiles / scripts; nothing outside `/tmp/fxcheck` and the three owned files was written.
