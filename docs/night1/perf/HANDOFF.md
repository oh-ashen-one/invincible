# F 4K/60 perf: handoff after round 05

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Branch `night1/perf`, worktree `~/sm2-n1/perf`, pushed to `origin/night1/perf`. Owns `tools/perf_ue2/` (imports P4's `tools/perf_ue/run_perf.py`) and `docs/night1/perf/`. Scratch `/Users/midir/sm2-n1/_scratch/perf/` (NOT committed: export, tex, logs, raw 4K stills
`r03/before` (as-found reference of the round-03 build), `r04/final`, `r05/final` (shipped), `r05/r4ctl` (round-04 content on the round-05 build), `r05/p3`/`p4` (proxy probes), `rtproxy/` (proxy GLBs), `tree_dump.json`, `life/` (P6 derived inputs copy)).
Spec `SPEC.md` (P1-P11), shot list `SHOTLIST.md` (round-05 update at the end), evidence `round-01` .. `round-05/` (`NOTES.md` = every fact of the round, `TABLE.md`, `LOOK_GATE_raw.md` / `look_gate_final.json`, `perf/<session>/`, `stills/`, `cmp/`, `route_30s.mp4`, `content_audit.json`, `rtproxy_report.json`).
Critics: r01 FAILS, r02 APPROACHES, r03 FAILS, r04 APPROACHES (`critic/`). Round-05 blind pack: `/Users/midir/sm2-n1/_scratch/critic-F-r05/pack` (key `pack.key.json` next to it, `pairs.json`), NOT scored yet.

## State at the end of round 05 (all numbers `round-05/NOTES.md`; valid exclusive session `round-05/perf/g1`, 3840x2160 output, internal 1920x1080, fixed step)
Build: integration 3aa92ba merged (traversal r14 camera = different route frames than rounds 03/04; characters staged from P2 head 8ab861a = r07 WIP).
Shipped path: preset `overrides/perf60_hwl2.cvars` + `r.ScreenPercentage 50` in `Config/Mac/MacEngine.ini`; content = rebuilt + `perf_apply rt_lite_trees,rt_proxy_trees,cloud`:
the tree HISMs (leaves, crowns, bark) are OUT of ray tracing and **402 per-tile merged proxies** (`/Game/PerfF/RTProxy`, actors `City/RTProxy`, hidden in game + affect indirect lighting while hidden, no collision) are IN.
| line | result | pass |
|---|---|---|
| tree RT instances <= 1 k | 402 (level total 920; was 42 337 leaf instances) | yes |
| mean FT - GPU <= 0.9 | ship_a 1.29 / ship_b 0.48 / ship_c 0.39 (Metal per-process GPUTime offset) | **no in 1 of 3** |
| in-game p95 <= 17.9 x3 | 17.81 / 17.86 / 17.87 (CSV p95 17.79 / 17.76 / 17.75, p50 15.65-15.72) | yes, **margin 0.03-0.09 ms** |
| S1 round-02 crop >= 0.97 | 0.929 (same-content repeat 0.986; control r4 0.945) | **no** |
| S1 canopy luma | 0.998 of as found (r4 control 0.908) | yes |
| same-session control r4 (round-04 content) | p50 15.93 / 16.10, in-game p95 17.80 / 18.21, gap 1.90 / 1.45 | proxies: -0.28 ms p50, -0.15 ms p95 |
| **traffic + crowd ON** (`/Game/PerfF/Life/Manhattan`) | p50 17.1, CSV p95 19.4-19.6, in-game p95 19.9-20.2, 1 hitch | **FAILS P1 and P2** |
| P3 static S2 | 14.40 / 15.61 | yes |

## How to reproduce / rebuild (editor and game closed; wrap EVERY Unreal launch, commandlets included, in the lock; never run a commandlet while your own perf session runs)
```
G=/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh
$G capture --label perf -- python3 tools/perf_ue2/build_map.py        # ALL steps; round 05 ran --steps cpp,characters,map then tree_proxy,perf_apply,perf_preset,perf_audit
#   tree_proxy = tree_proxy_dump.py (commandlet, 17 s) + tree_proxy_build.py (numpy, 6 s) -> _scratch/perf/rtproxy; knobs SM2_PERF_PROXY_K0 (1) / K1 (16) / COVER (3.5) / BARK_* / TILE_M (200)
#   perf_apply rt_proxy_trees imports + builds 402 meshes: ~16 min. SM2_PERF_PROXY_REUSE=1 = flags / collision only on the existing meshes (~2.5 min)
$G capture --label perf -- tools/perf_ue2/build_life_variant.sh      # P6 life content (P6's unchanged build_life.py, F's scratch) + /Game/PerfF/Life/Manhattan (spec name@ini+variant:Life)
SM2_PERF_RTVARS=R,N SM2_PERF_RTVAR_CLOUD_KM=20 <UE commandlet> make_rtvars.py   # controls RTvRk20 (round-04 content) / RTvNk20 (no trees in RT); re-make after any proxy rebuild (copies of the geo level)
python3 tools/perf_ue2/perf_queue.py --out <dir> --tag x --configs "warm@ini,ship_a@ini,r4_a@ini+variant:RTvRk20,...,s2@ini+view:S2,lwarm@ini+variant:Life,..." -- --budget-s 870
$G capture --label perf -- tools/perf_ue2/stills2.sh <out> "ship@ini" "S1 S2 S7 route"     # env SM2_PERF_ROUTE_SHOTS=20,28,38,42
$G capture --label perf -- tools/perf_ue2/route_movie.sh <out> "movie@100+set:perf60_hwl2"
python3 tools/perf_ue2/look_gate.py /Users/midir/sm2-n1/_scratch/perf/r03/before <stills dir>
python3 tools/perf_ue2/serial.py <run dirs>                           # FT - GPU gap (P8)
```
- **After any content change, check a route still / the run log for `Couldn't spawn Pawn`**: round 05 lost two perf sessions (`round-05/perf/void_nohero/`) because collision on the hidden proxies blocked the PlayerStart and the "route" ran with no hero.
- `render_in_main_pass = False` removes a primitive from ray tracing AND Lumen card capture; ray-tracing-only = `hidden_in_game` + `affect_indirect_lighting_while_hidden` (engine `RayTracing.cpp` 1368).
- `unreal/WebHomage/Config/Mac/MacEngine.ini` is GENERATED and UNTRACKED: never `git add -A` / `git add unreal`. Content / DDC / Intermediate are local and kept (the proxies are 717 MB of local .uasset).
- Every F launch passes `-notraceserver`. Stop an engine only with `_scratch/gpu/bin/stop_ue.sh "<pattern of your own path>"`. One Unreal process of F at a time. Start every perf session with a throw-away `warm@ini`; deltas need a same-session control.
- CSVs committed gzipped, logs pruned (keep `csv.csv.gz`, `*_perf.json`, `result.json`, `run.txt`); `_scratch/perf/r05/prune.sh <session dir>`.

## Decisions and open items (facts, ranked)
1. **Traffic + crowd ON fails P1 / P2** (p50 17.1, p95 19.4-20.2). The shipped map has no life content, so the "60 fps" claim only holds without it. Next lever candidates: P6's crowd cost (+1.4 ms p50 / +1.7 ms p95; in g1 GameThread 1.85 -> 4.3 ms and RHI thread 2.7 -> 5.2 ms with life, GPU 14.4 -> 16.9 ms), `r.RayTracing.Culling.Angle` for the vehicles, crowd shadow / RT policy.
2. P2 margin without life is 0.03-0.09 ms in-game (CSV 0.39-0.43 ms). The gap line fails in 1 of 3 runs (1.29 ms) because Metal's GPUTime has a per-process offset; a trace-free, offset-proof gap measure (e.g. RenderThread idle / critical-path columns) would settle it.
3. S1 crop 0.929 < 0.97; repeat noise of the same content is 0.964-0.986. Brightness now matches (0.998); the leaf-level GI pattern differs from the as-found masked any-hit. Options: proxies for the near LOD0 trees kept alpha-masked (costs any-hit), card shape instead of shrunk quads.
4. Route stills vs `r03/before` are no longer like-for-like (P3 r14 camera): a new as-found reference on this build needs a content rebuild without `perf_apply` and `--preset-off`.
5. Integrator: adopt `perf60_hwl2` + SP 50 as `[Mac DeviceProfile]`, and run `build_map.py` steps `tree_proxy,perf_apply` after the city build (or move the proxy build into `build_city.py`); the proxies must stay collision-free.
6. Hero and street people remain out of the RT scene (round 03).
