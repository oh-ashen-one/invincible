# Island (piece A) — HANDOFF (round 04 STOPPED mid-rebuild 2026-10-03 21:50; nothing of the island is running)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Branch `night1/island` (pushed), worktree `/Users/midir/sm2-n1/island`, scratch `/Users/midir/sm2-n1/_scratch/island` (symlink to the exFAT SD card:
exports / GLBs / logs / frames only, never Content or DDC; exFAT writes `._*` files next to every file, skip them in globs).
Owns `tools/export/*`, `Scripts/build_city.py`, `Scripts/build_manhattan.py`, `Scripts/island_wp_sources.py`, `Shaders/City/`, `/Game/City`,
`/Game/Tests/City`, `/Game/Maps/Manhattan*`, `docs/night1/island/`. Traversal C++ is P3's: `REQUEST-traversal-r03.md`, `REQUEST-traversal-r04.md`.
Merged `Opus-5.5-Loop-Night-1` at 8b7a8301 (merge commit 70ce4f12, no conflicts); C++ rebuilt (`build_editor.sh`, 15.7 s).

## Read first: `round-04/README.md` (sections 1-7), `REQUEST-traversal-r04.md`

## STATE: the content is HALF-BUILT — there is no playable island map
The round-04 fresh rebuild deleted Content/City, Content/Tests/City and the WP map on disk (16:49) and rebuilt, one GPU-lock hold per
commandlet: tex, mat, all 1,642 tile meshes, protos, 128 / 136 street-kit tiles (11,262 s of holds). From 20:33 the GPU lock was PAUSED by
the health monitor (WindowServer starved, GPU 100 % with no Unreal / Blender running: another session's load); at 21:50 the build driver
was stopped (no engine was running). **First thing to do:**
```
df -k /Users/midir            # >= 150 GB (decimal) free, build_manhattan re-checks before every commandlet
ls /Users/midir/sm2-n1/_scratch/gpu/PAUSED   # must not exist
cd /Users/midir/sm2-n1/island && SPLIT_FROM=kit nohup docs/night1/island/build_r04.sh > /Users/midir/sm2-n1/_scratch/island/r04/logs/build_r04b.log 2>&1 &
```
Remaining: kit (8 street-kit + 136 fire-escape tiles, resumable, ~2 holds), `fsky,map,coll` (1 hold), `wp` (1 hold, ~1,700 s), traversal,
characters, look, manhattan_map. Every commandlet is `gpu_slot.sh capture --label island` (exit 75 = re-queued automatically). Then:
1. `docs/night1/island/capture_r04.sh` (warm-up + r1 r2 r3 r4 r5 r5b -> round-04, consecutive holds, 1080p movies + telemetry + stills);
2. `docs/night1/island/analyze_r04.sh` (route checks, fire-escape test, foliage share, ropes through crowns, trajectory diffs vs the merge-only
   sims, m2 pass lines + road band, IP gate);
3. `python3 docs/night1/island/critic_prep_r04.py` then `python3 /Users/midir/spider-man-2-astra6/tools/night1/abpack.py /Users/midir/sm2-n1/_scratch/critic-A-r04/pack /Users/midir/sm2-n1/_scratch/critic-A-r04/pairs.json .`;
4. add the fresh-rebuild total + `du -sh Content` to README §6 (I8), fill README §7.

## What round 04 changed (all script-generated, measured on telemetry sims)
* **Fire escapes** (`tools/export/street_kit.py` `fire_escape`): solids = the landings only (grating, lip + side beams) with open stair wells
  (1.5 x 0.7 m) and a drop-ladder hatch; railings / stairs / ladders / brackets are visual-only (street-kit tiles); the grating (drawn and
  solid) starts 0.40 m off the wall (`SM2_FE_GAP`). r3 sim from t = 2.4 s: 0 top-outs at the r03 loop spot (r03: 6), hero at x -218 at
  t = 3.5 s. Still in r3 (not fire escapes): short-rope stalls at x -206 / -198 / -85 / -40 (traversal, REQUEST-r04).
* **WHBox rule 5** (`island_boxes.py` `fill_hollow`): +2,574 boxes; audit raw hollow 17.68 -> 16.43 %, I5 phantom 0.25 % / hollow 0.36 %.
* **Leaf fade** (`M_CityLeaves`): cards cut < 3.5 m from the lens, dithered to 8.5 m (needs the rebuilt `mat` step: done in Content now).
* **Merged traversal on the routes**: every route departs from round 03 within seconds (r1 3.95 s, r4 2.57 s, r5 1.68 s, r3 10.8 s). r5 with
  the default r24 altitude chain fails the re-web lines (max gap 5.55 s); `scripts/r5_m2_avenue_alt0.json` (`tune AltChain=0`) passes them
  exactly like round 03 (0.30 s, 100 %, 1,481.6 m). Capture both (`r5`, `r5b`).
* Build: resumable batched mesh / kit import with a projected deadline (`SM2_ISLAND_DEADLINE`/`BUDGET_S` 1,950, batches 10 / 8), each
  commandlet its own hold, free-disk floor 150 GB decimal, on-disk fresh clean. `fepatch` step re-imports chosen kit tiles into the WP map.

## Files
| what | where |
|---|---|
| fresh rebuild driver / log / per-step lines | `build_r04.sh`, `round-04/build_r04_log.txt`, `round-04/build_r04_steps.txt` |
| one-hold sims (+ fepatch) | `hold_r04a.sh` (env MERGE_SIMS, FE_OUT, SM2_ISLAND_FE_TILES, KIT_LOG, EXTRA_SIMS) |
| capture / analysis / pack | `capture_r04.sh`, `analyze_r04.sh`, `critic_prep_r04.py`, `ip_gate_r04.py` |
| checkers (new) | `tools/export/island_fe_check.py`, `island_foliage_check.py`, `island_rope_canopy.py`, `island_traj_diff.py` |
| sim evidence | `round-04/sims/` (merge-only r1-r5 + r5 alt0, fire-escape variants with their checks) |

## Gotchas learned this round
* build_city's `clean` (`EditorAssetLibrary.delete_directory`) loads every asset before deleting it: > 40 min for the island. Delete on disk.
* Interchange glTF import does not apply `use_full_precision_u_vs` / `recompute_tangents`: every mesh is built twice (import + finish_mesh).
* A commandlet can hang for minutes after `DONE` (engine shutdown); budget the hold for it (city_kit_02: rc 124 at 2,403 s).
* Long tool waits: the shell tool backgrounds a command that prints nothing for 10 s and caps one call at ~280 s; pipes buffer output.
* Relative `-WHTravScript` paths are resolved from the engine's cwd: always pass absolute paths.
* run_game.sh in this worktree was edited by another session earlier (frame caps): not mine, left as found.

# (older handoffs: `git log -p docs/night1/island/HANDOFF.md`; round 01 / 02 / 03 / 04 READMEs hold their results)
