# Terrain (piece E) — HANDOFF (round 05 DONE: captures + blind critic pack; critic not run by me)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Branch `night1/terrain` (pushed; r04 and r05 are NOT merged — the integration branch still has r03), worktree `/Users/midir/sm2-n1/terrain`, scratch `/Users/midir/sm2-n1/_scratch/terrain` (r05 notes / drivers in `r05/`).
Owns `/Game/Terrain*`, `tools/export/{export_terrain.mjs,collect_terrain.js,gen_terrain_shaders.mjs}`, `tools/terrain/`, `unreal/WebHomage/Scripts/{build_terrain.py,terrain_materials.py}`,
`unreal/WebHomage/Shaders/Terrain/`, `docs/night1/terrain/`. Spec / shot list / cameras: `SPEC.md` (E1 reconciled in r05, E11 = r05 targets), `SHOTLIST.md`, `shots.json`. Nothing of mine is running.

## Round 05 (2026-10-03 03:30-07:00, Claude Opus 5.5 high via Devin): crowns as lit leaf volumes — final state (every number: `round-05/README.md`)
Target (Opus director after the r04 critic): crowns as lit leaf volumes that cast shadows on the lawn; E1 reconciled (eye level >= 8, aerial follows the reference). Built in committed scripts (nothing binary committed):
`Foliage.ush` (`tfSummer` summer palette for the browser's per-tree tints, `tfClumpShade` world-space light / shade clumps on the leaf cards, edge-on card fade, distance / hull saturation, fixed
shadow-pass coverage), `build_terrain.py` (near leaf cards out to 520 m, the LOD1 0.85-core pool not built, darker bark tint, furniture / reeds read their vertex colours, olive reeds, crown shadow proxies),
`terrain_materials.py` (bark furrows, blades R x1.53, lawn grade R 0.8, turf normal bent toward the sun, pond Specular 0.25, greyer rock, FILL 650), `Lawn.ush` (aerial fade 90-200 m, `lwTurfNormal`).
Final captures on `/Game/TerrainR5b` (stills + movies from the same content): `round-05/stills/*.jpg` (9 views, 3840x2160 out, internal 1920x1080), `round-05/t5_avenue_to_park.mp4` (11.7 MB) + `t4_lawn_sprint.mp4`
(12.3 MB) (1920x1080 native, hero hidden); a complete fallback package of the previous build (`/Game/TerrainR5`, white reeds) in `round-05/build4/`.
**Measured** (`tools/terrain/measure_r05.sh`, `round-05/README.md` table): (1) p1 crown sigma-3 median 12.06 (r04 8.13), 19 / 24 >= 9, min 6.11 — median met, all-crops not; (2) crown saturation median
0.636 (r04 0.518) — not met; (3) E9c 40.3 px (r04 54.1; the longest segment is a stepped building roof, no crown edge > 40 px), no hull balls / saucer cards — met; (4) crown shadow on the p4 lawn:
none (ratio 1.01, the one isolated tree measurable by geometry) — not met; (5) E1: p10 sigma-6 18.68 / guard 16.31, R / G 0.920 — met; p4 aerial sigma-6 5.48 (r04 10.85) — not met (<= 5).
Guards: E10 (b) PASS (sat >= 0.700), (c) 1 flat patch (a smooth sunlit ez trunk at t4 1.0 s, 109 x 52 px; build 4: 0), (d) PASS (t5 25-40 m median 9.16, min 5.75).
GPU ms: not measured (perf lock refused, exit 75, Mac unattended); capture-run GPU ms (contaminated) p1 163.5 / p10 92.9 / p4 105.5 (r04 165.1 / 104.5).
Blind critic pack (not judged by me): `/Users/midir/sm2-n1/_scratch/critic-E-r05/pack` (16 pairs: 9 views vs refs, 5 progress pairs r03-merged vs r05, 2 movies; every 4K image also as `_2048.jpg`), `pairs.json` beside it, key outside (`pack.key.json`).
Content in this worktree: `/Game/TerrainR5b` (final), `/Game/TerrainR5` (build 4), `/Game/TerrainR4`, `/Game/Terrain` (HEAD of r03/r04). A rebuild of R5b with today's scripts also builds the shadow proxies for park / elm trees (R5b has them for conifers only).

## Open items, in order
1. **Crown shadows on the lawn (r05 target 4) — not solved, root cause not found.** Facts (`round-05/diag/NOTES.md`): trunks and lamp posts cast crisp shadows on our lawn (the sunlit strip on the
   east side of the Great Lawn in p4); the leaf-card crowns cast none, with VSM or CSM, MegaLights off, VSM non-Nanite thresholds off; the city's own flat land (VB_p4) shows tree shadows; the
   hidden shadow-only crown proxies (`ISM_shadowproxy_*`, `SM2_TERRAIN_SHADOW_PROXY`, k 0.85) were only built for the conifers in R5b and showed nothing. Next tests, cheapest first:
   (a) a debug map: one big cube on the lawn + one cards pool on a plain opaque two-sided material (does anything leaf-card-shaped write shadow depth?);
   (b) the full proxy build (the loop fix is committed: `build_terrain.py` builds them per kind now) and look for crown shadows in the sunlit strip;
   (c) under the golden rig (sun 9 deg, az 238, look piece) large parts of the park floor read as sky-lit only; check the West Side skyline's shadow (the midtown collision export does not cover it).
2. Crown saturation median 0.64 against 0.65: the far crowns (p1 y 450-750, 300-1000 m) read 0.54-0.64 through the golden haze; the >= 520 m hull already gets +50 % albedo saturation.
3. p1 crown crops (2250,1800), (1500,1950), (2100,1950), (2400,1650), (3450,1200) are mostly dark lawn between crowns (luma 52-74): sigma-3 6-8.
4. p4 critic lawn box sigma-6 5.48 against <= 5: the box holds a crown corner, an infield edge and a bench (lawn-only part ~3.4-4.4).
5. Picnic blankets read as pale flat slabs at 20-60 m in p10 (beige palettes 0.42-0.52); the pond 'white egg' lumps were the reeds' white default tint (fixed in R5b).
6. Water seam p6 / khaki river p7 belong to the water piece; t5 storefront text and city signs are the city piece's.

## Next-session recipe (everything idempotent)
- Content: `SM2_TERRAIN_ROOT=/Game/TerrainR5b /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label terrain -- tools/terrain/run_build.sh` (full ~11 min nullrhi; `mat` alone ~1.5 min after a
  material-only change; run it through the lock). Offline first: `python3 tools/terrain/check_hlsl.py` (14 / 14).
- Captures: `docs/night1/terrain/round5.sh` (copy it for round 06), detached from your own shell, never inside a hold: `STAGE=T` (warm + p4 p1 p10 -> `round-05/<TEST_NAME>`), `STAGE=S` (warm + nine stills),
  `STAGE=M` (t5 + t4 movies, same content), `TERRAIN_ROOT` selects the content. Chain holds from a driver outside the holds (`_scratch/terrain/r05/chain_C.sh`). Timings: warm 1-1.5 min, still ~1.2 min,
  t5 ~13 min, t4 ~12 min + encode (crf 30-32 to fit 15 MB).
- Numbers: `tools/terrain/measure_r05.sh <round dir>`, `tools/terrain/tree_shadow_auto.py <still> p4_greatlawn <out.json> --iso 12 --preview <jpg>`; pack: `LAWN_PROGRESS=1 python3 tools/terrain/make_pairs.py
  <round dir> <critic dir>/pairs.json docs/night1/terrain/round-03` (r03 = the merged state), `abpack.py`, `tools/terrain/pack_small.py <critic dir>/pack`.
- Safety learned this round: the engine starts UnrealTraceServer (listening on 1981 / 1989) unless `-notraceserver` is passed — `capture_round.sh` and `run_build.sh` now pass it; stop engines only with
  `stop_ue.sh /Users/midir/sm2-n1/terrain` (it does not match drivers in `_scratch/terrain`: stop those by PID); `ShowFlag.DirectLighting 0` / `r.Lumen.DiffuseIndirect.Allow 0` draw default materials
  (uncompiled permutations) and are useless as diagnostics.

## Older rounds (history; numbers in `round-0N/README.md`)
- **r04 (Sonnet 5.5)**: dense blade lawn (`prep_lawn.py`, `Lawn.ush`), woven blankets, triplanar rock, infield clay; critic [4,4,4,4,3], preferred the old build 4 / 5, E9c 54 px; not merged.
- **r03 (Opus 5.5)**: leaf-card LOD1 165-520 m, clump hull >= 520 m, foliage pools out of the ray-tracing scene (black cards fixed), water sublevel merged; critic [4,4,4,4,3]. Merged.
- **r02**: the browser's park-tree chain (46 HISM pools, `Foliage.ush`), lawn grade. **r01**: ground, ponds, furniture, rocks, shore audit, collision.

## What exists (all committed; Content is generated, never committed)
- `tools/export/export_terrain.mjs` + `collect_terrain.js` (headless-Chrome export -> `<scratch>/export`), `tools/terrain/prep_terrain.py` (+ `prep_lawn.py`), `tools/export/gen_terrain_shaders.mjs` -> `Shaders/Terrain/Park.ush`.
- `Shaders/Terrain/Foliage.ush` (LOD bands, clump crown, leaf cards, r05 `tfSummer` / `tfClumpShade`), `Lawn.ush` (lawn detail, r05 aerial fade + `lwTurfNormal`), `terrain_materials.py` (all Custom-HLSL materials).
- `build_terrain.py` steps clean, tex, mat, mesh, foliage, trees, map, views (env `SM2_TERRAIN_ROOT`, `SM2_TERRAIN_NEAR_FAR` (520), `SM2_TERRAIN_SHADOW_PROXY` (0.85; 0 = off)).
- Tools: `measure_r05.sh`, `tree_shadow_auto.py`, `shadow_ratio.py`, `crown_stats.py` (+ saturation), `lawn_stats.py`, `flatquad_check.py`, `t5_*`, `make_pairs.py`, `pack_small.py`, `check_hlsl.py`, `shore_audit.py`.
