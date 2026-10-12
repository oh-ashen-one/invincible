# Supplied GLB inventory (PA phase 1, measured 2026-10-08)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Source (read-only): `~/Documents/SpiderMan_Asset_Import_M3_2026-10-08_task-4/GLBs/`. Measured by `tools/final/assets/glb_inspect.py` + `mesh_topo.py` (CPU, direct GLB parse); renders by `preview_glbs.py` (Blender 4 background, Cycles CPU). Raw JSON: `~/sm2-n1/_scratch/final/assets/{inspect,topo}.json`.

Provenance: 38 of the 56 files are byte-identical (SHA-256) to copies in `~/sm2-assets/raw{,2}/` used by the earlier crowdfit / critterfit
builds; the other 18 are their near-duplicate (Tripo UUID names only) or untextured twins (see PLAN.md §1).

Common to all 56: generator Tripo 2.0, 1 node / 1 mesh / 1 primitive / 1 material, no skin, no animation, glTF Y-up, unit-less with the largest extent normalised to 1.0 (0.9995), pivot at the base centre (min Y = 0, X/Z centred), front = +X (critterfit README; confirmed on the animal renders). Textured files: one 8192² baseColor JPEG, metallic 0, roughness 0.9, no normal/ORM maps. Untextured files: no TEXCOORD_0, flat grey 0.8 factor. 'Parts' = connected components after welding (bolts, slats, fur cards; not floating debris: none visible in the renders). Open edges are Tripo open shells/slat ends, invisible in the renders.

| File | What it is | Tris | Extent X×Y×Z (glTF Y-up, max=1) | Texture | Open edges / parts |
|---|---|---|---|---|---|
| `blue+mailbox+3d+model.glb` | USPS-style blue collection box | 17728 | 0.53×1.00×0.51 | 8192² JPEG | 1979 / 67 |
| `blue+oil+drum+3d+model.glb` | blue 55-gal steel drum | 21059 | 0.65×1.00×0.65 | 8192² JPEG | 259 / 2 |
| `fire+hydrant+3d+model.glb` | red NYC hydrant | 20080 | 0.50×1.00×0.55 | 8192² JPEG | 1050 / 44 |
| `food+cart+3d+model.glb` | steel food cart w/ canopy | 19281 | 0.63×1.00×0.70 | 8192² JPEG | 1431 / 84 |
| `french+bulldog+3d+model.glb` | French bulldog, standing | 19871 | 1.00×0.86×0.37 | 8192² JPEG | 687 / 58 |
| `golden+retriever+3d+model.glb` | golden retriever, standing | 19802 | 1.00×0.77×0.25 | 8192² JPEG | 763 / 38 |
| `headphones+3d+model.glb` | over-ear headphones (accessory) | 6280 | 0.42×1.00×0.91 | 8192² JPEG | 22 / 1 |
| `hijab+fashion+model+3d.glb` | civilian: runner, teal tank top (crowd 19) | 6521 | 0.20×1.00×0.70 | 8192² JPEG | 99 / 8 |
| `human+3d+model.glb` | civilian: graphic tee + cap (crowd 11) | 6158 | 0.20×1.00×0.68 | 8192² JPEG | 136 / 11 |
| `human+character+3d+model (1).glb` | civilian: woman, blue sweatshirt (crowd 04) | 5802 | 0.20×1.00×0.69 | 8192² JPEG | 208 / 10 |
| `human+character+3d+model (2).glb` | civilian: teen, purple hoodie + backpack (crowd 14) | 5872 | 0.26×1.00×0.63 | 8192² JPEG | 439 / 17 |
| `human+character+3d+model (3).glb` | civilian: black polo (crowd 07) | 6173 | 0.19×1.00×0.64 | 8192² JPEG | 295 / 7 |
| `human+character+3d+model.glb` | civilian: beanie + plaid vest (crowd 16) | 6411 | 0.23×1.00×0.65 | 8192² JPEG | 68 / 10 |
| `human+figure+3d+model.glb` | civilian: black hoodie + shades (crowd 06) | 6083 | 0.23×1.00×0.66 | 8192² JPEG | 408 / 23 |
| `knitted+beanie+3d+model.glb` | orange knit beanie (accessory) | 6584 | 0.77×1.00×0.85 | 8192² JPEG | 546 / 2 |
| `leather+bag+3d+model.glb` | brown leather messenger bag (accessory) | 6007 | 0.58×0.74×1.00 | 8192² JPEG | 269 / 19 |
| `leather+jacket+man+3d+model.glb` | civilian: leather jacket (crowd 02) | 6364 | 0.23×1.00×0.56 | 8192² JPEG | 24 / 4 |
| `male+character+3d+model.glb` | civilian: white tee (crowd 03) | 5894 | 0.18×1.00×0.63 | 8192² JPEG | 191 / 12 |
| `mesh+trash+can+3d+model (1).glb` | green wire-mesh litter basket | 17533 | 0.75×1.00×0.75 | 8192² JPEG | 3447 / 13 |
| `mesh+trash+can+3d+model.glb` | green wire-mesh litter basket | 17533 | 0.75×1.00×0.75 | 8192² JPEG | 3447 / 13 |
| `metal+shopping+cart+3d+model (1).glb` | shopping cart | 19259 | 0.97×1.00×0.60 | 8192² JPEG | 792 / 76 |
| `metal+shopping+cart+3d+model.glb` | shopping cart | 19259 | 0.97×1.00×0.60 | **none** (no UVs) | 792 / 76 |
| `orange+tabby+cat+3d+model (1).glb` | orange tabby cat, standing, tail up | 18796 | 1.00×1.00×0.31 | 8192² JPEG | 409 / 41 |
| `orange+tabby+cat+3d+model.glb` | orange tabby cat, standing, tail up | 18796 | 1.00×1.00×0.31 | 8192² JPEG | 409 / 41 |
| `park+bench+3d+model (1).glb` | NYC slatted park bench | 20098 | 0.43×0.51×1.00 | 8192² JPEG | 448 / 39 |
| `park+bench+3d+model.glb` | NYC slatted park bench | 20098 | 0.43×0.51×1.00 | 8192² JPEG | 448 / 39 |
| `parking+meter+3d+model (1).glb` | single-head parking meter | 17935 | 0.22×1.00×0.25 | 8192² JPEG | 857 / 12 |
| `parking+meter+3d+model.glb` | single-head parking meter | 17935 | 0.22×1.00×0.25 | **none** (no UVs) | 857 / 12 |
| `pigeon+3d+model (1).glb` | rock pigeon, standing | 20319 | 1.00×0.71×0.33 | 8192² JPEG | 198 / 11 |
| `pigeon+3d+model.glb` | rock pigeon, standing | 20319 | 1.00×0.71×0.33 | 8192² JPEG | 198 / 11 |
| `pigeon+in+flight+3d+model (1).glb` | pigeon, wings spread (flight pose) | 20132 | 0.62×0.33×1.00 | **none** (no UVs) | 66 / 1 |
| `pigeon+in+flight+3d+model.glb` | pigeon, wings spread (flight pose) | 20132 | 0.62×0.33×1.00 | **none** (no UVs) | 66 / 1 |
| `potted+plant+3d+model (1).glb` | concrete planter with shrub | 19238 | 0.81×1.00×0.80 | 8192² JPEG | 1831 / 18 |
| `potted+plant+3d+model.glb` | concrete planter with shrub | 19238 | 0.81×1.00×0.80 | **none** (no UVs) | 1831 / 18 |
| `rat+3d+model (1).glb` | brown rat (fur cards) | 14606 | 1.00×0.50×0.49 | 8192² JPEG | 5397 / 493 |
| `rat+3d+model.glb` | brown rat (fur cards) | 14606 | 1.00×0.50×0.49 | 8192² JPEG | 5397 / 493 |
| `red+metal+cabinet+3d+model (1).glb` | red newspaper vending box | 16345 | 0.44×1.00×0.54 | 8192² JPEG | 555 / 32 |
| `red+metal+cabinet+3d+model.glb` | red newspaper vending box | 16345 | 0.44×1.00×0.54 | **none** (no UVs) | 555 / 32 |
| `seagull+3d+model (1).glb` | herring gull, standing | 19673 | 1.00×0.72×0.29 | 8192² JPEG | 429 / 17 |
| `seagull+3d+model.glb` | herring gull, standing | 19673 | 1.00×0.72×0.29 | 8192² JPEG | 429 / 17 |
| `squirrel+3d+model (1).glb` | grey squirrel (fur cards) | 18752 | 1.00×0.61×0.26 | 8192² JPEG | 1058 / 3 |
| `squirrel+3d+model.glb` | grey squirrel (fur cards) | 18752 | 1.00×0.61×0.26 | **none** (no UVs) | 1058 / 3 |
| `street+food+cart+3d+model (1).glb` | hot-dog cart w/ umbrella | 19865 | 0.76×1.00×0.79 | 8192² JPEG | 995 / 51 |
| `street+food+cart+3d+model.glb` | hot-dog cart w/ umbrella | 19865 | 0.76×1.00×0.79 | **none** (no UVs) | 995 / 51 |
| `street+lamp+3d+model (1).glb` | cast-iron park lamp post | 20678 | 0.13×1.00×0.13 | 8192² JPEG | 86 / 8 |
| `street+lamp+3d+model.glb` | cast-iron park lamp post | 20678 | 0.13×1.00×0.13 | **none** (no UVs) | 86 / 8 |
| `traditional+man+outfit+3d+model.glb` | civilian: kurta + waistcoat (crowd 09) | 5995 | 0.23×1.00×0.62 | 8192² JPEG | 104 / 6 |
| `traffic+barrel+3d+model (1).glb` | orange/white traffic barrel | 18102 | 0.76×1.00×0.77 | 8192² JPEG | 176 / 10 |
| `traffic+barrel+3d+model.glb` | orange/white traffic barrel | 18102 | 0.76×1.00×0.77 | 8192² JPEG | 176 / 10 |
| `trash+bags+3d+model (1).glb` | black trash-bag pile | 21469 | 1.00×0.76×0.89 | 8192² JPEG | 35 / 6 |
| `trash+bags+3d+model.glb` | black trash-bag pile | 21469 | 1.00×0.76×0.89 | **none** (no UVs) | 35 / 6 |
| `weathered+sawhorse+3d+model (1).glb` | blue wooden sawhorse barricade | 16428 | 0.40×0.51×1.00 | 8192² JPEG | 1445 / 35 |
| `weathered+sawhorse+3d+model.glb` | blue wooden sawhorse barricade | 16428 | 0.40×0.51×1.00 | **none** (no UVs) | 1445 / 35 |
| `woman+fashion+3d+model.glb` | civilian: denim jacket + sundress (crowd 12) | 6192 | 0.24×1.00×0.63 | 8192² JPEG | 170 / 17 |
| `wooden+crate+3d+model (1).glb` | wooden slatted crate | 20767 | 0.90×1.00×0.89 | 8192² JPEG | 260 / 61 |
| `wooden+crate+3d+model.glb` | wooden slatted crate | 20767 | 0.90×1.00×0.89 | **none** (no UVs) | 260 / 61 |
