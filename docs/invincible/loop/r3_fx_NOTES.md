# Round 3 notes: piece `fx` (builder B)

Scope: `Flight/WHBreachDirector.cpp/.h` and the new `unreal/WebHomage/Scripts/build_invincible_fx.py`. Nothing was compiled, launched or
run in Unreal (brief rules). No git commands were run. `-WHFlight=0` (legacy hero) never spawns the director, so its behaviour is untouched.

## Files changed

| File | Change |
|---|---|
| `unreal/WebHomage/Scripts/build_invincible_fx.py` | NEW. Headless UE Python builder for five materials under `/Game/Invincible/FX/` (below). |
| `unreal/WebHomage/Source/WebHomage/Flight/WHBreachDirector.h` | New pools / structs / tunables / private helpers; `Decals` + `NextDecal` removed (replaced by `HoleDecals` / `CraterDecals`); `SpawnRim` and `SpawnDebris` added; `AudioKeep` split from `KeepAlive`. |
| `unreal/WebHomage/Source/WebHomage/Flight/WHBreachDirector.cpp` | Breach / Crater / Boom / Bump / debris / Tick rewritten around the new assets; every path keeps the round-2 fallback when an asset is missing. |

## What `build_invincible_fx.py` creates (no command is given here; the root decides how to run it)

Idempotent: a missing asset is created, an existing one has its expression graph cleared and rebuilt in place. It refuses to touch any
path outside `/Game/Invincible/FX/`, raises on any failure (including the compile-error list returned by `MaterialEditingLibrary.recompile_material`),
saves every asset, reloads and verifies domain / type, and prints `SM2_BUILD_OK: build_invincible_fx.py` as the last line. Plain `python3`
with `--dump-hlsl <dir>` writes the HLSL of every Custom node to files for review (needs no editor).

| Asset | Domain / blend | Content | Parameters (defaults) |
|---|---|---|---|
| `M_BreachHole` | deferred decal, translucent | Procedural jagged opening: outline = three triangle waves (7 / 11 / 19 teeth, periodic in the angle) + two low sines, warped by 3-octave value noise; near-black interior with a lit "wall thickness" reveal band at the edge; broken-concrete rim (eroded by noise); 12 radial cracks; soot smear; every alpha fades to 0 before the decal box edge; height-derived tangent normal. Opening mean diameter 0.39 x the box (3.1 m at `HoleHalfCm` 400). | `Seed` 0.37, `Open` 1 (0 -> 1 grows the opening), `Bump` 0.03, `RimCol` (0.30, 0.28, 0.25) |
| `M_CraterDecal` | deferred decal, translucent | Scorched near-black centre, fractured-slab band (cell grid cracks + per-slab shade), 14 long radial cracks + 27 hairlines (length grows with `Open`), soft soot halo, bowl / crack normal. Opacity fades to 0 before the box edge. | `Seed` 0.61, `Open` 1, `Bump` 0.10, `RimCol` (0.085, 0.082, 0.078) |
| `M_InvVapour` | surface, translucent, UNLIT, two-sided | White vapour; opacity = `Opacity` x noise turbulence (world pos - object pos + time, moves with the object) x (0.10 + 0.90 x fresnel^`EdgePow`), so face-on is nearly clear and grazing is opaque. Emissive = `Color` x `Gain`. | `Color` (0.92, 0.95, 1.0), `Opacity` 1, `EdgePow` 1.6, `Gain` 1.2, `Soft` 0.7 |
| `M_InvDust` | surface, translucent, LIT (surface lighting), two-sided | Dust puff for a sphere: opacity falls to 0 at the silhouette, lumpy noise erosion inside; base colour `Color`, small emissive lift. | `Color` (0.34, 0.31, 0.27), `Opacity` 0.7, `Emissive` 0.12, `Soft` 1, `Seed` 0.5 |
| `M_InvChunk` | surface, opaque, lit | Concrete speckle, or brick courses with mortar when `Brick` >= 0.5 (object-relative position, so it works per cube). `Color` / `Rough` match `M_CmbSolid`, so the director's MIDs work on either. | `Color` (0.40, 0.38, 0.35), `Rough` 0.9, `Brick` 0, `Seed` 0.5 |

Pre-run check done on the HLSL (outside Unreal): the Custom-node bodies were compiled as C++ through a throw-away shim (clang, no UE) and evaluated
on grids for 5 seeds x 3 `Open` values: 0 NaN; hole opening = 11.7 % of the box, crater scorch = 3.6 %; vapour / dust / chunk outputs in range. This
checks syntax and numeric sanity only, **not** the real shader compiler.

## Defects targeted and how

1. **Breaches look fake** (critic top defect). `Breach()` line-traces the facade (entry: along the flight line from 2 m before; exit: back into the far wall from 3 m outside; WorldStatic + WorldDynamic objects, complex trace like the traversal, up to 5 layers, invisible components skipped for the material), then:
   - `M_BreachHole` decal at entry and exit on the traced point, facing the traced normal (fallback +-flight dir), box 8 m (+18 % x severity), 0.9 m deep each side, grows open over 0.18 s (the material's `Open` parameter), sort order 2, kept in a 12-entry pool.
   - Debris: `ChunksPerBreach` 34 -> 44, `MaxChunks` 140 -> 240. Sizes: 66 % 8-25 cm, 26 % 20-34 cm, 8 % 34-50 cm (longest side); blocks / slabs / bars. They start on the outside of the wall over the opening and spray sideways / up / out at 2-20 m/s (was 6-44 m/s along the flight line, i.e. out of frame in ~0.2 s). `FacadeChunkFraction` (0.5, `-WHFacadeChunks=` overrides) of the pieces wear the traced facade material (opaque / masked game materials only; engine and glass / translucent materials are rejected); the rest use `M_InvChunk` (concrete / brick speckle, tints), else the old `M_CmbSolid` tints. 
   - Dust: `M_InvDust` puffs, 14 + 6 x severity per breach, 0.8-1.8 m growing to 2.3-6 m, peak opacity 0.62-0.78, life 1.35-1.9 s. They start on a ring around the opening (so the hole stays readable at +0.3 s) and billow outward along the wall; at the exit 30 % are blown out ahead of the hero. Fewer, larger, more opaque than the combat puffs (the old two `Fx.Dust` calls remain as the fallback).
   - Glass shards: 70 -> 26, 6-22 cm cards -> 4-12 cm, thinner, brighter (emissive 0.9, opacity 0.7).
2. **Sonic boom invisible.** `Boom()` spawns an `M_InvVapour` cone (engine `/Engine/BasicShapes/Cone`; its bounds and which end is the apex are probed at BeginPlay, nothing about its pivot is assumed): apex 1.4 m ahead of the hero, opening backwards, length 7 m -> 11.2 m, base radius 2.4 m -> 5.8 m, peak opacity 0.62, life 0.9 s, glued to the hero (`UWHFlightWorldSubsystem::HeroPosCm`) for 0.45 s, then it stays where it is. Plus three thin vapour pancakes (0.75 x life) 1.5 / 5.3 / 9.1 m behind him, radius 1.2-2.0 m -> 5.2-8.2 m. The additive `Fx.Hit` flash on the line stays (small). The existing camera kick is not touched (not this file).
3. **Crater is a flat dark disc.** `Crater()` traces the ground (z and material), places the `M_CraterDecal` (shallow 28 cm slab, 2.2-4.8 m radius, grows over 0.3 s), 16 physics ejecta pieces (ground material on part of them), `SpawnRim()`: 12-17 STATIC slab pieces (12-30 cm, one in five 32-50 cm) placed on traced ground height around the core, tilted <= 26 degrees and half sunk, popping in with a small overshoot and staying (so nothing can hang in the air), asphalt / concrete / ground-material look; dense dust ring (`CraterDust`).
   - Resting-piece check: every dynamic chunk older than 1.2 s that is nearly at rest is traced downward every 0.4 s; with no support (or an invisible WorldDynamic proxy under it) it shrinks away in 0.35 s. End of life is a 0.4 s shrink instead of a pop (targets "debris hanging above the van hood").
4. **Opaque flash discs (fl11 2.35 s, fl12 3.6 s).** The crater ring was a lit-translucent pancake up to 21 m wide; it is now a `M_InvVapour` pancake (radius 0.8 m -> 4.8-8.6 m, thin, fresnel edge, 0.55 s). With no vapour asset there is no ring at all. The boom flash is additive sparks only.
5. Decals and the hero: `ExcludeHeroFromDecals()` (BeginPlay + every breach / crater) sets `bReceivesDecals = false` on every primitive component of player pawn 0, otherwise the opening / crater decals would paint him when he flies through or stands in them. All director components (`MakeComp`) also have decals off.
6. MIDs of the pooled components are now kept in `KeepAlive` (a piece can switch to the facade material, which would otherwise leave its MID unreferenced); procedural sound waves moved to `AudioKeep` (the 900-entry trim no longer touches components / MIDs).

## What the root should check

- First: run the builder, then check the editor / game log of the first run for material shader errors (`LogShaderCompilers`, `LogMaterial: Error`, any "M_Breach" / "M_Crater" / "M_Inv" line). A `-nullrhi` commandlet does not compile shaders, so a HLSL error would only surface at the first draw (the decal / vapour would fall back to the default material). Log lines to grep: `WH_FLIGHT breach fx r3:` (which assets loaded, cone apex end and size), `WH_FLIGHT breach in|out fx` (facade trace hit / miss, normal, material name).
- Entry frame +0.3 s: dark jagged opening visible at the impact, dust around (not over) it; opening about 3-4 m across; >= 20 debris pieces, mixed sizes, none large on screen.
- Facade-material pieces: `M_CityFacade` is a texture-atlas material driven by the merged mesh's UV channels 0-7 and vertex colour; on a plain cube it may render flat / odd. If so, pass `-WHFacadeChunks=0` (all pieces use `M_InvChunk`) or lower `FacadeChunkFraction`; nothing else depends on it.
- Decal normal: the tangent-space normal axes (UV x / y vs the decal's local Y / Z) were not verified in a render; if the opening or crater lighting looks inverted, set the `Bump` parameter to 0 on the materials (or negate it).
- Boom frames (fl04 / fl15 around the boom +-0.1 s): cone / rings >= 25 % of the frame width, visible >= 0.3 s. Tunables on the director: `BoomOpacity`, `BoomConeLenM`, `BoomConeRadM`, `BoomLife`, `BoomFollow`; per material: `Opacity`, `EdgePow`, `Gain`, `Soft`. The chase camera sits ~3-4 m behind the hero, i.e. inside the cone: its walls fill the frame periphery; if it washes out luma, lower `BoomOpacity`.
- Exit frames: dust near the exit is placed on a ring around the opening and ahead of the hero; check `hero_occl` / hidden frames in the telemetry for fl14 / fl15 (the dust could add hidden frames right after the camera cut).
- Crater: fl11 / fl12 around landing +0.1 .. +1.0 s: cracked scorched decal (no flat disc), rim pieces sitting on the street, no piece in the air, vapour ring translucent. Chunk physics cost: up to 240 simulated cubes (was 140) plus 72 static rim pieces, 110 puffs, 12 + 6 decals.
- Slow-mo, audio, collateral, `GcAsset` (authored fracture) paths are unchanged.

## Cross-file requests

None required. Optional: the hero's `WHFlightComponent` already writes `HeroPosCm` / `bHeroValid` each frame (used for the cone follow); if the camera piece changes the chase distance a lot, retune `BoomConeLenM` / `BoomConeRadM`.
