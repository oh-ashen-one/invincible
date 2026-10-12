# Supplied GLB integration: phase 1 plan (builder PA)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See DISCLAIMER.md.

Status: phase 1 (inspect + plan). Nothing has been imported into Unreal, no Unreal process launched, no map touched, no commit.
Measurements per file: `docs/night1/final/assets/INVENTORY.md`. Contact sheets (Blender 4 background, Cycles **CPU**, 4 views per item: 3/4,
-Y side, +X front, top): `~/sm2-n1/_scratch/final/assets/previews/sheet_{props,animals,humans}.jpg`, one 2×2 PNG per file next to them.
Tools (PA-owned): `tools/final/assets/{glb_inspect,mesh_topo,preview_glbs,contact_sheet}.py`.

## 0. The main finding: most of these assets are already in the game

38 of the 56 supplied GLBs are byte-identical (SHA-256) to files already on this M5 in `~/sm2-assets/raw/` (humans, accessories) and
`~/sm2-assets/raw2/` (props, animals); the other 18 are the near-duplicate (UUID-only difference) or untextured twins of those 38 (§1),
so every distinct item is covered. Those copies were turned into game content earlier:

| Supplied asset | Already in the game as | Evidence |
|---|---|---|
| 16 street props: hydrant, mesh trash can, park bench, street food cart, food cart, potted plant, blue mailbox, parking meter, red metal cabinet, trash bags, traffic barrel, sawhorse, shopping cart, street lamp (also blue oil drum, wooden crate: packed, **never placed**) | `tools/critterfit` pack `props_hq` (3000/700-tri LODs, 1024 px tile in `public/assets/city/props/props_hq_atlas.webp` 4096²). The browser placed them in pools; `tools/export/export_city.mjs` exported the pools to the island `layout.json`; `build_city.py` turned them into `/Game/City/Props/SM_<pool>` + per-256 m-tile HISMs in `/Game/Maps/Manhattan_WP` | `tools/critterfit/manifest.json` (glb `~/sm2-assets/raw2/*.glb`, sizes). `~/sm2-n1/_scratch/island/export/island/proto/hydrant.glb` = 3000 tris, 0.78 m tall (matches the manifest's `h 0.78`), likewise bench 1.9 m, cart 2.45 m, parklamp 4.2 m. Island `layout.json` instance counts: hydrant 3404 (+2641 from `tools/export/street_props.py`), trash 5166 (+2628), bench 3206, planter 7610, newsbox 3039 (+2493), meter 3262, bags 3091, mailbox 820, shopcart 391, drum (=traffic barrel) 228, cart 211, cart2 139, sawhorse 66, parklamp 1104. `Content/City/Props/SM_{hydrant,trash,bench,cart,cart2,planter,mailbox,meter,newsbox,bags,drum,sawhorse,shopcart,parklamp}.uasset`, `Content/City/Textures/Maps/assets_city_props_props_hq_atlas.uasset`. Island build log `~/sm2-n1/_scratch/island/logs/city_wp.log`: "WP map /Game/Maps/Manhattan_WP saved 1642 meshes 198063 instances". `props_hq` items `oildrum`, `crate` have no pool in `layout.json` (used by the browser's combat throwables only). |
| 11 civilians | `tools/crowdfit` citizens (fitted to the crowd body, skin weights transferred, A-pose undone), exported by `tools/life/citizens_fbx.py` (18-bone crowd rig, walk/run/idle) and imported by `build_life.py` as `/Game/Life/Citizens/SK_Citizen_NN_*` (20 citizens × 5 outfit/head variants) driven by `AWHLifeCrowd` (`Source/WebHomage/Life/WHLifeCrowd.*`) in `/Game/Tests/Life/Life_Actors`, an island level instance (`sm2_common.ISLAND_COMMON_LEVELS`) | `tools/crowdfit/manifest_citizens.json`: 02 leather jacket = `leather+jacket+man`, 03 = `male+character`, 04 = `human+character (1)`, 06 = `human+figure`, 07 = `human+character (3)`, 09 = `traditional+man+outfit`, 11 = `human+3d+model`, 12 = `woman+fashion`, 14 = `human+character (2)`, 16 = `human+character`, 19 marathon runner = `hijab+fashion+model+3d` (despite the name: a runner in a teal tank top). `Content/Life/Citizens/SK_Citizen_{01..20}_*.uasset` all present. |
| beanie, headphones, leather bag | crowdfit **browser** accessories (`beanie`, `headphones`, `messenger_bag`), attached to the head / torso bone in `src/world/npc/crowd.js`. Not ported to Unreal (no accessory code in `build_life.py` / `WHLifeCrowd`). | `tools/crowdfit/manifest_citizens.json` `accessories` |
| pigeon, seagull, pigeon in flight, cat, rat, squirrel, golden retriever, French bulldog | critterfit pack `fauna` (rigid-part vertex rig: per-vertex part id + weight, pivots) animated in the **browser** vertex shader (`src/world/npc/pigeons.js`, `fauna.js`, dogs in `crowd.js`). **Not in Unreal**: no fauna/pigeon code or content under `unreal/WebHomage/Source` or `Scripts`. | `tools/critterfit/manifest.json` (`fauna`), `public/assets/city/npc/fauna.json` |

So the genuinely new Unreal work is small: the animals and birds (with an in-material idle), plus the two props that were packed but never
placed (blue oil drum, wooden crate). Re-importing the 16 street props would duplicate what is already placed thousands of times.

## 1. Dedupe of the "(1)" pairs

Two kinds of pair, measured (geometry hash of welded positions, image SHA-256, `cmp`):

* **Byte-identical apart from the Tripo UUID names** (~85 bytes differ; same triangles, same positions, same 8192² image): mesh trash can,
  orange tabby cat, park bench, pigeon, pigeon in flight, rat, seagull, traffic barrel. Same item: keep either one; the plan uses the file
  that `~/sm2-assets/raw2` already matches (the "(1)" file for all of these).
* **Same mesh, one copy untextured** (same triangle count and bounds; the plain-name file has no UVs and no image, ~0.3-0.4 MB): metal
  shopping cart, parking meter, potted plant, red metal cabinet, squirrel, street food cart, street lamp, trash bags, weathered sawhorse,
  wooden crate. Same item: keep the **"(1)"** (textured) copy; the untextured one is a geometry-only export.
* `pigeon in flight`: both copies are identical and both are untextured (critterfit painted a top-view tile for it).
* `human+character`, `(1)`, `(2)`, `(3)` are four different people, not a pair.

No pair is a genuinely different variant.

## 2. Kept / skipped

| Asset (file used) | Decision | Reason | Real scale |
|---|---|---|---|
| blue oil drum (`blue+oil+drum+3d+model.glb`) | **KEEP, new placement** | clean (2 parts), not placed anywhere in the island today | 0.88 m tall (Ø 0.57 m) |
| wooden crate (`wooden+crate+3d+model (1).glb`) | **KEEP, new placement** | clean slatted crate, not placed today | 0.64 m tall (cube) |
| pigeon (`pigeon+3d+model (1).glb`) | **KEEP, new** (ground flocks, idle peck in material) | good texture/shape; in browser, not Unreal | 0.33 m long |
| seagull (`seagull+3d+model (1).glb`) | **KEEP, new** (waterfront) | good | 0.58 m long |
| orange tabby cat (`orange+tabby+cat+3d+model (1).glb`) | **KEEP, new** (few, tail sway) | good; a lone cat on a stoop / alley mouth reads naturally | 0.58 m long (≈0.45 m to tail tip height) |
| squirrel (`squirrel+3d+model (1).glb`) | **KEEP, new** (parks) | fur cards (2179 non-manifold edges): decimate with critterfit's `:weld` option | 0.45 m long incl. tail |
| rat (`rat+3d+model (1).glb`) | **KEEP, new, optional** (low count) | fur cards, 493 parts; tiny on screen at 4K street level; keep count low | 0.48 m long incl. tail |
| golden retriever, French bulldog | **SKIP for v1** (open question) | a standing dog with no owner or leash on a sidewalk reads wrong; walking with a crowd walker needs C++ in `Life/` (not PA-owned) | retriever 1.05 m long, bulldog 0.52 m |
| pigeon in flight (both) | **SKIP** | untextured; a frozen flying bird in a still/4K shot is the worst look; a WPO flight loop is possible (see §4) but not v1 | 0.66 m span |
| 16 street props (hydrant, trash can, bench, 2 carts, planter, mailbox, meter, cabinet/newsbox, trash bags, traffic barrel, sawhorse, shopping cart, street lamp) | **SKIP (already placed)** | same source files are already in `/Game/City/Props` with 1k-30k instances each; a second import would double objects at the same corners | (as placed: hydrant 0.78, trash 0.92, bench 1.9 w, carts 2.45 / 2.25 h, planter 1.15, mailbox 1.25, meter 1.55, newsbox 1.12, bags 0.8, barrel 1.0, sawhorse 1.5 w, cart 1.02, lamp 4.2) |
| street lamp specifically | **SKIP** | already the park-lamp pool (1104) and the owner rule: no new lamps (9,297 authored night lamp lights) | — |
| 11 civilians | **SKIP (already crowd walkers)** | already fitted, rigged and walking as `SK_Citizen_*`; static A-pose duplicates would look like mannequins | 1.70 m (crowd rest height) |
| beanie, headphones, leather bag | **SKIP** | accessories for people; alone on the ground they are litter. Attaching them to Unreal walkers is a `Life/` C++/ABP change outside PA ownership | — |

## 3. Import settings for the kept assets

* Texture: decode the embedded 8192² JPEG, Lanczos downscale offline (PIL, CPU) to **2048** for oil drum and crate, **1024** for the
  animals (≤0.6 m objects; the browser used 1024 tiles). One sRGB BC1 texture per asset (`T_PropM3_<name>_D`), mips on, streaming on.
  The mailbox / oil drum atlases have white padding at the top edge: dilate the UV islands by 8 px before the downscale so mips do not bleed.
  Optional derived normal map: none (Tripo bakes cavity shading into the albedo, mild; a derived normal would double it).
* Mesh: decimate offline in Blender CPU with the existing `tools/crowdfit/decimate_lods.py` path (as critterfit does: yaw -90 so Tripo +X
  faces glTF +Z, scale to the real size above): LOD0 3000 tris (crate/drum 2500), LOD1 600-800 tris; animals carry the critterfit rig in
  UV1 (`part`, `weight`) and the pivots as material constants. Import with Interchange, `build_nanite False`, `generate_lightmap_uvs False`,
  `recompute_normals False`, materials/textures not imported (PA builds its own).
* **Nanite: no.** At 600-3000 tris and a few thousand instances Nanite gains nothing; the animals use World Position Offset (cheaper and
  simpler on classic LODs), and it matches the city's prop HISMs (`build_city.py` keeps instanced props non-Nanite).
* Material: one master `M_PropM3` (base colour texture param, roughness 0.85 / metal 0; oil drum instance: roughness 0.5, metallic 0.5,
  constants per material instance) + `M_PropM3_Critter` with the WPO idle (head peck / look for birds, tail sway + head turn for
  cat/squirrel/rat, time offset from `PerInstanceRandom`). Usage flags: instanced static meshes. Night: no emissive; they are lit by the
  authored lamp lights like the rest of the street.
* Cull: LOD screen sizes 1.0 / 0.25; HISM `instance_end_cull_distance` 60 m (animals 45 m, crates/drums 120 m); animals do not cast shadows
  beyond 25 m (dynamic shadow distance) to keep VSM cost low.

## 4. Feasibility verdict: civilians and animals

* **Civilians → crowd walkers: already done.** The pipeline `tools/crowdfit/crowdfit.py` (pose fit to the crowd body, weight transfer,
  un-pose to arms-down 1.70 m +Z) → `tools/life/citizens_fbx.py` (18-bone crowd rig) → `build_life.py` step `citizens` → `/Game/Life/Citizens`
  already contains all 11 supplied civilians (table in §0). Nothing to add; placing static A-pose copies is **not recommended**.
  If the owner wants them more visible, the lever is crowd density / variant weighting in `AWHLifeCrowd` (`Life/`, orchestrator decision, not PA).
* **Animals/birds moving: partially.** critterfit's output is rig *data* (per-vertex part id + weight, pivots); the motion lives in browser
  shaders + JS (`pigeons.js`: flocks peck, shuffle, take off from the hero, circle, resettle; `fauna.js`). Unreal has no equivalent runtime.
  Content-only (PA scope) can do **in-place idle motion** via WPO in the material (peck, head turn, tail sway, wing fold/flap), driven by time
  + per-instance random: feasible and cheap. **Locomotion, take-off/flee and flight paths need a ticking actor (C++ under `Source/WebHomage/Life/`)**,
  which PA does not own. Recommendation: ground pigeons / gulls / cats / squirrels / rats with WPO idle only; **do not place static
  "in flight" birds**; dogs skipped. A C++ flock (port of `pigeons.js`) is a possible later orchestrator task.

## 5. Collision / traversal policy (props must never be web anchors or blockers)

How the traversal sees geometry (`Source/WebHomage/Traversal/WebTravWorld.cpp`): on the island (World Partition, WHBox cubes) the world
runs in **SolidMode 2** ("collision = visual triangles"): `IndexLevelActors` walks every primitive of every loaded level (streamed levels
are added by `AddLevel`). An `InstancedStaticMeshComponent` (HISM included) that is not `SM_shed/SM_shedtop/SM_subway` is **excluded**
(`excluded-ism`) unless `-WHTravIsmSolid=1`. Any other *visible* static mesh whose actor/label/component/mesh name does not contain an
`IsExcludedName` token (`prop_`, `_prop`, `streetprop`, `hydrant`, `lamp`, ...) is turned into a solid and **its collision is re-enabled
QueryOnly** even if the build disabled it. Web traces are complex traces against WorldStatic + WorldDynamic.

Rules for `/Game/PropsM3` (belt and braces):
1. Only HISM components (one actor per 256 m tile per kind, like `build_city.py` `make_ism`), never plain StaticMeshComponents/StaticMeshActors.
2. Names carry the exclusion token: meshes `SM_PropM3_<name>` (contains `_prop`), actors `PropsM3_prop_<kind>_<tile>`.
3. Components `NoCollision` profile + `CollisionEnabled.NO_COLLISION`; meshes get `remove_collisions` (no simple shapes) and
   `CTF_USE_SIMPLE_AS_COMPLEX`, so even an A/B with `-WHTravIsmSolid=1` finds nothing to trace. Never tag `WHGround`.
4. `can_character_step_up_on = No`, `generate_overlap_events False`, not in the navmesh (no nav relevance).
5. Verify with `-WHTravDumpPrims=<csv>`: every PropsM3 row must have role `excluded-ism` and `coll_after 0`; total solid count of the map
   unchanged versus the run without the PropsM3 level.

## 6. Placement rules (all positions deterministic from data, hashed per position like `street_props.py`)

Data: island `layout.json` instance pools (`~/sm2-n1/_scratch/island/export/island/layout.json`; browser frame metres, UE = (x, z, y)·100,
sidewalk top y = 0.15, road y = 0), and `unreal/WebHomage/Scripts/life_data_island/walk.txt` (1628 sidewalk corners, 2164 edges).
Global constraints: keep out of the crowd's walking band (`AWHLifeCrowd` Avenue band -2.25..+0.25 m, street band -1.65..+0.2 m around each
walk edge, +roadward): a prop sits either ≥0.6 m roadward of the edge line (kerb zone, where hydrants/meters are) or ≥2.7 m toward the
buildings; ≥1.1 m from any existing pool item (same obstacle test as `street_props.py` `free()`), never on asphalt, crosswalks or in the
4 m around signal masts (`signals.txt`); never on rooftops (no roof placements at all); max one cluster per 25 m of frontage.

| Class | Count (target) | Where (driving data) |
|---|---|---|
| Blue oil drums | ~150 (2-3 per site) | 87 construction sites = clusters (12 m) of ≥4 existing `sawhorse/barrier/cone/drum` items: 1 group per site, 1.5-3 m from the cluster centre on the building side; + ~20 at waterfront `dock` items with |x| > 700 |
| Wooden crates | ~250 (stacks of 1-3, random yaw ±15°, a 2nd crate rotated on top) | beside ~1/3 of the 350 food carts (`cart`, `cart2`, 1.2-1.8 m behind the cart, building side), beside ~1/5 of the 507 `dumpster` items, and with the construction groups |
| Pigeons | ~900 (flocks of 4-9, 1.8 m radius) | ~130 spots: park benches (1246 benches with a park lamp within 25 m: one flock per ~12 benches), plazas around `kiosk` (57) / `subway` (44) / `news` stands, 1 per ~4 food carts; ground y 0.15 |
| Seagulls | ~80 (1-3 per spot) | waterfront: benches/docks with |x| > 700 or the south tip (z > 3100); a few on seawall tops only if a measured top height is available (else ground only) |
| Cats | ~60 (single) | building-side stoops next to `bags` piles / `dumpster` items in non-avenue streets (street frontage, `abs(N.x) < 0.1`), facing the street |
| Squirrels | ~120 (single, some in pairs) | parks: within 1-4 m of park trees (`trees-park-near` / `ez-park*` items) and park benches, never on paths' walk band |
| Rats (optional) | ~40 | next to `bags` / `dumpster` items, building side, at most 1 per 150 m |
| Dogs, flight birds, humans, accessories, lamps, re-imported street props | 0 | skipped (§2) |

Total ≈ 1,600 instances, ~130 HISM tile actors.

## 7. Delivery shape

* `unreal/WebHomage/Scripts/build_props_m3.py` (PA), same two-mode pattern as `build_life.py`:
  * plain python3 step `prep` (CPU only): read the 9 kept GLBs from the read-only folder, downscale textures, decimate + rig-tag in Blender
    background (`-b --factory-startup`, no render), write `~/sm2-n1/_scratch/final/assets/prep/*.glb|png` + `placements.json` (the rules
    above, computed from `layout.json` / `walk.txt` / `signals.txt`, with a placement audit PNG top view per district).
  * in-Unreal steps (`SM2_PROPS_M3_STEPS=clean,import,mat,map,test`) run by the orchestrator through the GPU coordinator
    (`tools/gpu/gpu_slot.sh capture`, headless commandlet `-nullrhi`), never by PA directly without an admitted slot.
  * Output: `/Game/PropsM3/{Meshes,Textures,Materials}` and **one** level **`/Game/PropsM3/Maps/PropsM3_Island`** (non-WP level, all HISM
    tile actors, no lights, no PlayerStart, no game mode) for the orchestrator to add as a LevelInstance (LEVEL_STREAMING, not spatially
    loaded) to `Manhattan_Island{,_Midday,_Night}` via `sm2_common.ISLAND_COMMON_LEVELS` + `build_manhattan.py` `build_island_showcase`
    (orchestrator-owned; `validate_island` composition list must be updated with it). Nothing is written into `Manhattan_WP` or any showcase map by PA.
  * PA's own verification map `/Game/PropsM3/Maps/PropsM3_Test`: a flat 60×60 m slab (tagged WHGround), one of each item at real scale in a
    row with a 1.8 m reference box, a mini plaza with a pigeon flock / cat / crates, the golden rig level instance, PlayerStart.
* Estimated content: textures 2 × 2048² BC1 (≈2.7 MB each with mips) + 5 × 1024² (≈0.7 MB) ≈ 9 MB; meshes 7 × ≈0.3 MB; materials,
  level and HISM data ≈ 3 MB. **≈ 15 MB total** (vs ~600 MB of source GLBs). Runtime: ~1,600 instances, ≤3000 tris each, culled at 45-120 m.

## 8. Verification plan

1. Offline (CPU, PA): contact sheet of the prepared LOD0/LOD1 meshes with rig parts coloured (critterfit's "render every item" rule),
   real-scale lineup beside a 1.70 m crowd body, placements.json audit (counts per class, min distance to walk edges / pool items / masts,
   zero on asphalt) as JSON + top-view PNGs.
2. Commandlet (via coordinator): build log `SM2_BUILD_OK`, asset list, every component NoCollision, no `MISS` entries.
3. `PropsM3_Test` stills (golden + night) through `tools/m5/guarded_preview.py` / `tools/showcase/with_holder.sh` (one renderer, admitted slot).
4. After the orchestrator wires the level: real `-game` binary, fixed 1/60 s `-dumpmovie`, street-level golden **and** night stills in 4
   districts: Midtown avenue start (x 249, z 178 m, the S1 PlayerStart), a construction/food-cart corner on 8th Av (x -250), the Central Park
   south edge (benches + squirrels/pigeons, z ≈ -800), and the Battery/waterfront south tip (z > 3000, gulls). Plus one swing route with
   `-WHTravDumpPrims` to prove PropsM3 rows are `excluded-ism`, and the existing swing route checked for unchanged anchor picks (same
   anchor list with and without the level). Labelled as offline visual evidence, never perf.

## 9. Open questions for the orchestrator / owner

1. Owner intent check: the street props and civilians are **already in** (from the same files). Is the expected deliverable just the new
   animals + drum/crate, or does the owner want a *quality upgrade* of the existing 16 prop pools (e.g. 2048² textures + 8-10k-tri LOD0
   swapped into `/Game/City/Props/SM_*`)? That touches `build_city.py` content, which PA does not own.
2. Dogs: skip (default), or a few lying/standing beside park benches knowing no owner walks them?
3. Accessories on Unreal walkers (beanie/headphones/bag as in the browser) would need `Life/` changes: wanted, and by whom?
4. A C++ pigeon flock (port of `pigeons.js` incl. take-off when the hero lands) would make the flight model usable; outside PA scope.
5. Should rats be night-only? One shared level means they appear in every preset unless the orchestrator adds a night-only variant.

## 10. Phase 2 as built (2026-10-08, orchestrator-approved scope)

Approved: new placements of blue oil drum, wooden crate (1), pigeon (1), seagull (1), orange tabby cat (1), squirrel (1), rat (1). Everything
else in §2 stays skipped (final). Build: `python3 unreal/WebHomage/Scripts/build_props_m3.py` (steps `prep,content,map,validate`; `checkmaps` /
`dropcheck` make and delete the temporary verification copies). Every commandlet ran through `tools/gpu/gpu_slot.sh capture` on
`~/.cache/gpu-slot`; every render through `tools/m5/guarded_preview.py` (wrapper `tools/final/assets/capture_props_m3.py` waits while any holder,
waiter or renderer exists).

Deliverable level (wire this one): **`/Game/PropsM3/Maps/PropsM3_Island`** (non World Partition, 264 actors `PropsM3_prop_<kind>__t<x>_<z>`,
one HISM each per kind per 256 m tile, no lights, no PlayerStart). Test map: `/Game/PropsM3/Maps/PropsM3_Test` (lineup + flock + crate stack
on a slab, PropsM3_Island + Look_Rig_golden as always-loaded sublevels, an invisible engine Cube so FWebTravWorld runs SolidMode 2).
Content: `/Game/PropsM3/{Textures,Meshes,Materials,Maps}` = 19 MB on disk.

Changes against the phase-1 plan (each forced by the approved limits or by what the stills showed):
* **No street sidewalks at all.** With the crowd band (avenue -2.25..+0.25 m, street -1.65..+0.2 m) plus 2 m, every 4-5 m sidewalk is covered
  kerb to wall, so hydrant/cart-corner rules were dropped. Paved city surface is used only >= 6 m from any road (plazas, courtyards, promenade
  interiors); a first pass that allowed walk-graph-free sidewalks (east of 2nd Av, along 12th Av) put crates on ordinary sidewalks and was removed.
* Ground model = 0.5 m raster from the same exports the maps are built from (island sidewalks / asphalt / coast meshes, which are stored
  relative to their tile centre; terrain park ground, paths, drives, ponds, furniture, rocks; piers + sheds; footprints).
* Drums / crates stand against a wall (1.0-1.8 m from a footprint / pier shed) or a waterfront railing, never free on a path (a first pass
  put drum rows in the middle of park piers and promenades). Crate stacks: 1-3 (third crate on top).
* Animals: Central Park only on mowed lawn (park-mask tuft height <= 12 cm) or paths; never on the park / street lamp light-pool decals (those
  render as white discs in daylight: existing look, not PropsM3), picnic blankets, reeds, rocks, water. Pigeon albedo desaturated 60 %
  (Tripo's was violet-blue). Flocks of 5-15 within 2.2 m.
* Idle motion: `M_PropM3_Critter` World Position Offset (no C++): birds peck (head pitch bursts) and look around (yaw); cat / squirrel / rat
  sway the tail and turn the head; part id + weight in UV1 (critterfit rig), pivots as material-instance parameters, per-instance custom data
  0 phase, 1 activity, 2 rate, 3 albedo brightness. Verified: frame difference of two stills 1 s apart changes only bird heads (`stills/wpo_diff.jpg`).

Placement counts (`~/sm2-n1/_scratch/final/assets/prep/audit.json`): oil drum 150, crate 251, pigeon 911 (94 flocks, 5-15 each), gull 81, cat 60,
squirrel 120, rat 27 = 1,600 instances. Checks: 0 on road / water / building / obstacle cells; nearest traversal zip point to any animal 5.2 m
(all roof / ledge / lamp-top perches are >= 4.35 m up); highest instance y 0.81 m (top crate of a stack); min building distance 1.0 m (drums /
crates against walls), animals >= 2.5 m (cats) / 2 m.

Collision proof (`evidence/`): `prims_island_propsm3.csv` = FWebTravWorld's `-WHTravDumpPrims` on the island check map with the level as a
LevelInstance: all 264 PropsM3 components `excluded-ism`, `coll_after 0`; `prims_test_ismsolid_propsm3.csv` = the test map with
`-WHTravIsmSolid=1` (instanced props solid again): all 225 PropsM3 components (earlier placement revision, same names) still `excluded` by name, `coll_after 0`.
In-editor validate step: every component a HISM with the NoCollision profile, no simple collision shapes, Nanite off, 'prop' token in every name,
no WHGround tag, counts equal placements.json.
