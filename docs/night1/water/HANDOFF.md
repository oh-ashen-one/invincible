# River water: handoff after round 03 (Opus 5.5)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. Nothing here is meant to infringe. See `DISCLAIMER.md`.

Branch `night1/water`, worktree `~/sm2-n1/water`, scratch `/Users/midir/sm2-n1/_scratch/water/`. Owned: `/Game/Water`,
`unreal/WebHomage/Scripts/build_water.py`, `docs/night1/water/`, `tools/water/`. No `.uasset` / `.umap` committed. No copied IP: the
spectrum, chop and noise textures are generated, the distance maps are rasterised from the layout and the city export, and the rest is code.
Blind critic pack r03: `/Users/midir/sm2-n1/_scratch/critic-W-r03/pack` (key `pack.key.json` beside it, `pairs.json`; 8 pairs: 4 against
references, 4 previous-vs-this: river_low still, harbour still, river_low dolly, river_sun dolly).

## Round 03 result (`round-03/NOTES.md`, `round-03/spec.json`)
Shader: resolved 0.15 to 0.5 m wind chop (`T_WaterChop`, two scroll directions), near-field (<= 150 m) GGX roughness <= 0.08 with true
texture gradients, streak / slick terms deleted, foam only within 150 m, one realization and no chop / foam / contact lookup beyond 150 m.
Committed `PARAMS` = captured pick V3 (`ChopK 2.6, MicroK 2.0, ScatK 0.04, FarVarK 0.1, SpecK 2.0, RoughN 0.06`).
| check | target | r02 | r03 |
|---|---|---|---|
| river_low near hp sd / p99.5 / glints / mean / p1 | >=12 / >=150 / >=1 % / <=80 / <=25 | 8.5 / 122 / 0.11 / 79.3 / 46 | 9.93 / 112 / 0 / **78.5** / 41 |
| river_sun sparkle width / near mean / glints | >=50 % / <=90 / 3-15 % | 35.5 / 137 / 44.9 | 37.8 / 148 / 52.9 |
| harbour crop hp sd / glints / pale blobs | >=10 / >=2 % / 0 | 4.33 / 0 / 109 | 4.3 / 0 / **2** |
| autocorr 80 px (low / sun dolly) | <= 0.10 | 0.006 / 0.041 | **0.053 / 0.015** |
| S4 C14 | 5-35 | 22.0 | **17.9** |
| seawall contact foam | present | present | **ABSENT (regression)** |
| perf (frame delta, SLW pass at river_low) | <= 2.5 / <= 2.5 ms | +1.23 / 0.80 (TSR 67) | **-0.25 / 1.00** PASS (native 100 %) |

## What blocks the remaining targets (measured, see NOTES "Why")
- river_low: the sky this view mirrors is about 114 to 121 Y, so a mirror reflection cannot reach p99.5 150 or Y 140 glints. The trough
  floor (p1 about 41) is fog / Fresnel times sky, not the body (ScatK 0.04 to 0.09 moves it by less than 5 Y). These are look-rig items
  (sky / fog over water), not W's, so they need an orchestrator decision: change the rig at these views, or change the target.
- river_sun: a broad golden sheen from the bright sky around the sun (mean 148). Discrete sparkles need the off-lobe reflection darker.
- harbour_high (260 m up) is all far field, and the sun is behind the view. Glints there need either a far-field glitter term or a
  sun-facing framing. The resolved chop never reaches it.

## Next round (suggested order)
1. **Seawall foam regression.** One 1080p still of `Water_View_RiverLow` with material param `Dbg` = 4 (`wf, cf, gust` as colour) to
   separate "foam pixels lit dark by the steep chop normal under the 9° sun" from "coverage lost in the new near-field branch". If it is
   the normal, set the foam normal to the long-wave normal `normalize(float3(-sl2, 1))` at full `wf`. The dark specks in the near field
   are probably the same foam pixels.
2. Get an orchestrator decision on the river_low sky / fog (above) before more water-side tuning. Parameter variants V1 to V3 barely moved
   the numbers.
3. river_sun: a darker off-lobe body plus less sky sheen at moderate angles (lower `SpecK` away from the sun lobe), keeping the sharp near
   lobe. Re-measure the sparkle width.
4. harbour: a far-field (> 150 m) sun-glitter term (the existing `gw` facets out to 900 m only light when the sun is in front).
5. Island export for contact foam (`SM2_WATER_EXPORT`), and the `/Game/Maps/Manhattan_WP` check, as in round 02.

## How to rebuild (all headless; every Unreal process inside a gpu_slot hold)
```
S=/Users/midir/sm2-n1/_scratch/water
# 0. inputs (CPU): water grid, noise, shore map, wind-sea slope spectrum, contact-distance map from the city export
SM2_WATER_SCR=$S SM2_WATER_EXPORT=<city export dir with manifest.json> python3 unreal/WebHomage/Scripts/build_water.py --steps inputs
# 1+2. one GPU hold: Manhattan content (if Content/ is empty) + water + optional iteration stills
/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label water --timeout 14400 -- bash $S/hold1.sh
# 3. captures + perf (stills = 1080 + 4K of S4 / river_low / river_sun / harbour_high; movie = both dollies; perf = exclusive)
SM2_WATER_SCR=$S tools/water/capture_round.sh docs/night1/water/round-NN stills,movie water
GPU_SLOT_PERF_WAIT_TIMEOUT=14400 SM2_WATER_SCR=$S tools/water/capture_round.sh docs/night1/water/round-NN perf water
# 4. numbers
python3 tools/water/water_spec.py all docs/night1/water/round-NN --json docs/night1/water/round-NN/spec.json
```
Scratch helpers (not committed, recreate from this text if the scratch dir is gone):
- `run_manhattan.py`: imports the integrator's `build_manhattan.py` unchanged and overrides `SCR`/`EXPORT`/`TEX`/`CHAR_STAGE` to
  `$S/manhattan/...`, `UE` to `$S/bin/ue_locked.sh` (= `gpu_slot.sh capture --label water -- <UnrealEditor> "$@"`), `stage_characters` to a
  no-op (P2 inputs cloned once from `_scratch/showcase/manhattan/chars`), and `wait_slot` to count `pgrep -x UnrealEditor` only.
  The export (`$S/manhattan/export/midtown3x3`) and `tex/` were cloned (`cp -Rc`) from `_scratch/showcase/manhattan/` (prepped city r10 export).
  Run: `python3 $S/run_manhattan.py --steps city,traversal,characters,look,map` (~9 min of commandlets).
- `hold1.sh`: run_manhattan (unless `$S/hold1.skip_city` exists) + `build_water.py --steps ue` with `SM2_WATER_VARIANTS=$(cat variants.json)`
  + `iter_stills.sh` (aborts if the game log says `M_RiverWater ... Failed to compile Material`) + optional autopick / `hold3.sh`.
- Round 03 used a single script instead: `_scratch/water/r03/hold_r03.sh` (build base + variants, 1080p iteration stills, `autopick_r03.py`,
  final build, `capture_round.sh stills` + `movie`), then `r03/perf_chain.sh` (one exclusive perf hold, native 100 %, 6 maps). Copy them for round 04.
- `hold3.sh`: final `build_water.py --steps ue` with `SM2_WATER_PARAMS=$(cat final_params.json)` + capture_round stills + movie.

## State at hand-off
- Nothing of ours is running: capture hold done 05:19, perf hold done 06:29 (exit 0), `perf_chain.sh` exited, no engine, no waiter.
  `stop_ue.sh` was run on this worktree as a final check.
- Content (Manhattan + `/Game/Water`, V3 params) is built in this worktree's `unreal/WebHomage/Content` (git-ignored). Intermediate and
  DerivedDataCache were kept, because the next round rebuilds here (about 10 min plus queue).
- Scratch kept: `_scratch/water/manhattan` (export / tex / chars clones), `iter/r03`, `cap/` (6.4 GB: dolly PNG frames for both dollies plus still captures and perf runs,
  delete them once round 04 has its own), `r03/` scripts and logs.
