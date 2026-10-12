# C — Integrated Manhattan map: handoff after round 01

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. Nothing here is meant to infringe. See `DISCLAIMER.md`.

Branch `night1/manhattan`, worktree `~/sm2-n1/manhattan` (base: integration `Opus-5.5-Loop-Night-1` at 30d6926). UE MCP port 8777 (not used:
everything is headless commandlets + `-game`), browser dev port 5208. Owned: `/Game/Maps/Manhattan*`, `unreal/WebHomage/Scripts/build_manhattan.py`,
`docs/night1/manhattan/`. Scratch: `/Users/midir/sm2-n1/_scratch/manhattan/` (export, textures, staged P2 inputs, logs, capture frames).
No `.uasset` / `.umap` is committed: the build script recreates everything.

## How to build (editor closed; ~12 min from an empty Content/)

```
python3 unreal/WebHomage/Scripts/build_manhattan.py                       # all steps, in dependency order
python3 unreal/WebHomage/Scripts/build_manhattan.py --steps look,map      # any subset; order is always the one below
```
| step | what it runs (each Unreal step = one headless `-run=pythonscript -nullrhi -RenderOffScreen -NoSound` commandlet, waits while 3+ Unreal run) | time |
|---|---|---|
| `cpp` | `Scripts/build_editor.sh` | 30 s |
| `city_export` | own vite on :5208 + P1 `tools/export/export_city.mjs` -> `_scratch/manhattan/export/midtown3x3` (own Chrome profile) | 40 s |
| `city_prep` | P1 `patch_export.py`, `prep_textures.py` (IP sanitiser), `gen_street_signs.py`, `street_kit.py`, `street_props.py`, `gen_shaders.mjs`; manifest texture URLs rewritten 5208 -> 5202 (P1 tools key on `5202/`) | 40 s |
| `city` | P1 `Scripts/build_city.py` unchanged, pass 1 `clean,tex,mat,mesh,proto,map`, pass 2 `kit` (after `Module Load StaticMeshEditor`, see issues) | 7 min |
| `traversal` | P3 `Scripts/build_traversal.py` (HeroDev hero + 49 clips, Trav_Canyon) | 30 s |
| `characters` | stages P2's derived inputs (rsync, read-only) into `_scratch/manhattan/chars`, then P2 `Scripts/build_characters.py` with its 4 path constants relocated and steps `clean,tex,mat,mesh,citizens,rename,abp,map` (no `prep`) | 45 s |
| `look` | P4 `Scripts/build_look.py` (`geo,rigs,maps`, all 3 presets) on this export | 70 s |
| `map` | `build_manhattan.py` itself inside Unreal: the maps below + `_scratch/manhattan/hero_swap_check.json` | 25 s |

Re-running any step is idempotent (maps are opened and emptied, never deleted; P2 content is wiped on disk first like P2's own wrapper).

## What is integrated (maps)

| map | content |
|---|---|
| `/Game/Maps/Manhattan` | always-loaded sublevels: P1 `City_Midtown_Geo` (as patched by P4 geo: components WorldDynamic, ground tagged `WHGround`) + P4 `Look_Boxes` (6683 boxes; the game indexes 7076 building boxes) + P4 `Look_Rig_golden` (lighting, post, MPC_City sequence) + `Manhattan_Actors`. Game mode `WebTravGameMode`: the P3 hero with the HeroDev mesh + `UWebTravAnimInstance` is the default pawn. |
| `/Game/Maps/Manhattan_Midday`, `Manhattan_Night` | the same with the midday / night rig. Switch = open the other map (`-map` or `open Manhattan_Night`). |
| `/Game/Maps/Manhattan_Actors` | PlayerStart on the avenue at (249, 178) m facing north (the look / city player start); 13 P2 street people on the avenue sidewalks (z 0.15 m): 2 standing thugs + 1 standing brute (loitering groups), 1 pacing thug, 1 pacing brute, 8 pacing citizens (4 citizen meshes, `ABP_Citizen_Lineup`). Pacing = P2 `AWHCharLoopWalker` Loop mode on a 0.3 m x L/2 ellipse (walk loop at the clip's natural speed). |
| `/Game/Maps/Manhattan_View_S1/S2/S4` | golden map + the P1 shot camera from `Scripts/city_shots.json` (default game mode; for stills). |

The game default map is NOT changed (`Config/` untouched); captures pass `-map`.

## Verification tools (docs/night1/manhattan)
- `scripts/route_30s.json`: P3 script format; spawn (249, 176) m facing north, sprint, jump 1.8 s, first web 2.6 s, P3 a/d autoChain rule
  (releasePhase 0.7, gap 0.15, repressVz 99, trick every 3rd release). `scripts/route_30s_warmup15.json` = the same after 15 s of standing (perf).
- `capture_round.sh <round> [movie|stills|views]`: warm-up render, 1080p60 `-movie` of the route (0.8 s P3 pre-roll trimmed), telemetry,
  `route_check.py` + P3 `anim_check.py`, 4K route stills, 4K S1/S2/S4 view stills. Every run under `gpu_slot.sh capture`.
- `route_check.py <telemetry.csv>`: fall-through (z or floor clearance < -0.3 m), stuck (speed < 1 m/s > 1.5 s, or < 10 m net progress in any 3 s
  window, or > 3 s in wall/perch/zip), T-pose (anim weight < 0.5), inside the detailed block.
- Perf: `gpu_slot.sh perf ... -- python3 tools/perf_ue/run_perf.py --map /Game/Maps/Manhattan --script .../route_30s_warmup15.json --configs tsr67 --window 15:45 --fixed-step` (P4's harness).

## Round 01 results (details: `round-01/NOTES.md`)
- 30 s route in `/Game/Maps/Manhattan`: 0 fall-through frames, 0 stuck windows, 0 T-pose frames, 18 attaches, 0 camera-in-geometry frames;
  the hero leaves the detailed block at t = 22.6 s (see P1 issue 4). Movie `round-01/route_30s.mp4` (1080p60), 4K native stills (route + S1/S2/S4).
- Perf (exclusive `gpu_slot.sh perf`, perf_valid, util before 0 % / after 0 %): 3840x2160 output, TSR 67 % = 2573x1447 internal, 30 s route:
  avg 51.99 ms (19.2 fps), p50 51.93, p95 59.00, p99 62.79, max 70.74, 0 hitches, GPU 42.2 ms, render thread 50.6 ms.
- Street people are in the map but read poorly: small, in canyon shade, often behind P1 street props; only ~2 are readable in view_S1.

## Integration issues found (per piece)

**P1 city**
1. `build_city.py` is not headless as written: in a `-run=pythonscript` commandlet `get_editor_subsystem(StaticMeshEditorSubsystem)` returns None
   (`finish_mesh` crashes). Fix used here, without editing P1's file: run `Module Load StaticMeshEditor` first.
2. The street kit (r05) is not in the default steps, and the `kit` step loads `City_Midtown_Geo`, which a clean build only creates in `map`:
   a fresh build needs two passes (`...,map` then `kit`), and P4 `geo` must run after `kit` (kit actors are WorldStatic 256 m tiles otherwise).
3. Paths hard-coded to P1's scratch: `street_faces.py` (default export + its `__main__` write), defaults of the other tools; texture URLs keyed on
   the string `5202/` (an export from any other dev port must be rewritten). `build_city.py` falls back to `~/sm2-n1/city/.../city_shots.json`.
4. The detailed block is 768 m long on the avenue (y 256 .. -512). At P3 round-09 speeds (up to 62 m/s, ~37 m/s mean) the straight route leaves it
   at t = 22.6 s and swings over the park edge / far-LOD area (flat dark ground, no street detail) for the last 7.4 s.

**P2 characters**
1. `build_characters.py` hard-codes `WT=/Users/midir/sm2-n1/characters`, `_scratch/characters/ueimport` and `CIT_TMP`, and its `prep` step runs
   P2's tools that write into P2's worktree + scratch: not relocatable. Manhattan relocates the 4 constants (text substitution, fails loudly if they
   change) and uses a copy of P2's derived inputs, so its build depends on P2 having run `prep` locally (`chars/STAGED.json` records P2's HEAD).
2. `AWHCharLoopWalker` Line mode moves along world X whatever the actor yaw: it cannot walk a north-south sidewalk. Used a thin Loop ellipse instead.
3. Citizens have only walk / run / idle; thugs have no idle-variety loop on the street (the thug idle is the fight idle `thugIdle`).
   The 4-light "enemy fill" of the lineup map is not in the city, so enemies are lit only by the look rig.

**P3 traversal**
1. Hero swap to `/Game/Characters/Hero/SK_Hero` is NOT possible from the map: the pawn loads its mesh and clips from hard-coded paths in C++
   (`SetupHeroMesh`: `/Game/Traversal/HeroDev/.../SpiderMan`, `Lenses`; `UWebTravAnimInstance::ClipRoot` `/Game/Traversal/HeroDev/<clip>`).
   Compatibility (`round-01/hero_swap_check.json`): both skeletons have the same 58 bones (names identical ignoring case, all bones the P3 code needs exist),
   but they are different skeleton assets (HeroDev's is named `Lenses_Skeleton`), P2 names clips `A_Hero_<clip>` in `/Game/Characters/Hero/Anims`,
   and P2's lenses are material slots on the body mesh, not a separate mesh. Needs a P3 change (mesh path + ClipRoot + clip-name prefix, lens mesh optional).
2. Turning off the avenue pins the hero on a facade: a heading change to west (180 deg) mid-block (t 14 s) or at a 10 m cross street (t 20 s) left him
   swinging in place against the facade at x = 236 m for 10+ s (< 10 m net progress per 3 s); turns at the 18 m cross street at t 21.0 / 20.8+21.5 s
   stalled at x = 172 m after 6 s. Probe telemetry: `_scratch/manhattan/probe_var*` (not committed).
3. autoChain with releasePhase 0.85 / gap 0.35: the hero hangs motionless at 49 m (235, -159) from t 15.8 s to the end of the run (a swing that never
   reaches the release phase and never ends). releasePhase 0.95 / repressVz 0 (P4's old perf rule) now oscillates on one web (4 attaches in 28 s).

**P4 look**
1. `rebuild_look.sh`, `rebuild_city.sh`, `launch_editor.sh`, `job_server.py` default to P4's scratch and worktree; `build_look.py` itself is fine
   with `SM2_CITY_EXPORT` (used here).
2. `Look_Boxes` must be rebuilt after every city build (P4 geo patches P1's level in place): the Manhattan build orders it so.

## Missing / next
- Hero swap (needs P3), combat (P5), traffic / crowd density / water (P6), a runtime time-of-day switch (currently three maps).
- A route that stays in the detailed block for 30 s needs either a bigger P1 detail region or working turns in P3.
- People are static loops (no avoidance, no reaction to the hero); they are placed by hand on the S1 avenue only.
