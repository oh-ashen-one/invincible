# F perf, round 05: notes (neutral facts, no self-assessment)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. Numbers are from the RUNNING game (`-game`, offscreen, 3840x2160 back buffer, **internal 1920x1080 = TSR 50 %**, read back from `wh_perf.internal_w/h`)
> on the rebuilt integrated `/Game/Maps/Manhattan` (golden rig), the 30 s swing route `route_30s_warmup15.json`, window = game s 15..45, fixed step (`-benchmark -fps=60`), CSV profiler (1800 frames per run),
> every perf run inside `gpu_slot.sh perf` (exclusive, `perf_valid`, util before 0 %, one Unreal instance, `-notraceserver`; no Unreal Insights / trace server was started).
> Valid session: **`perf/g1`** (`GPU-LOCK: class=perf exclusive=yes util_before=0% util_after=0% util_during_avg=72.1% wait_s=64.31 instances_before=0 instances_max=1 contaminated=false`).
> Raw rows: `TABLE.md`, `perf/g1/<config>/{result.json,run.txt,csv.csv.gz,<config>_perf.json}`, `perf/g1/serial.json`, `perf/g1/gap_over.json`.

## 0. Build
- Merged `origin/Opus-5.5-Loop-Night-1` (fast-forward to 3aa92ba: traversal r14, characters r6). Rebuilt with `build_map.py --steps cpp,characters,map` (city / look / traversal script inputs unchanged since round 04; the characters step stages P2's derived inputs from P2's worktree head **8ab861a = P2 r07 WIP**, piece C's staging rule, not the merged r06), then `tree_proxy,perf_apply,perf_preset,perf_audit`.
- **The route camera is P3's r14 camera.** Route frames differ from round 03 / 04 (framing, timing), so round-04 route numbers and route stills are not like-for-like with this round. The same-session control `r4_*` (round-04 content on today's build) is the comparison.

## 1. What was built (round-04 critic: merge the ~42 k leaf / crown ray-tracing instances per city tile into <= 1 k proxies)
- `tools/perf_ue2/tree_proxy_dump.py` (commandlet, read-only): every tree HISM instance's world matrix (79 903 instances: leaves, crown masses, bark).
- `tools/perf_ue2/tree_proxy_build.py` (numpy): one merged mesh per 200 m city tile = **402 meshes / 402 ray-tracing instances** (was 42 337 leaf / crown instances; audit `content_audit.json`: 920 ray-tracing instances in the whole geometry level). Proto GLBs are the same files build_city imported; the mesh-local frame was checked against the imported meshes' bounds (error 0.0 cm for all 43 meshes).
  - leaf cards: LOD0 street / small trees + hedges keep EVERY card (`K0 = 1`), all other trees every 16th card (`K1 = 16`, phase varies per tree); each kept card is scaled about its centre by `sqrt(k * coverage * 3.5)` (coverage = the leaf texture's alpha > 0.5 area inside the card: ash 0.167, oak 0.212, pine 0.218, aspen 0.122). The factor 3.5 was set from the S1 canopy luma (see 3); it is disclosed tuning.
  - crown masses (`trees_*_crownfar`) whole; bark = the largest triangles up to 60 % of each bark mesh's area, <= 160 per tree (**bark is back in the ray-tracing scene**, round 04 had it out).
  - 32.6 M triangles in total (28.6 M leaf, 4.1 M bark; largest tile 2.06 M). `rtproxy_report.json`.
- `perf_apply.py` step `rt_proxy_trees`: imports the proxies into `/Game/PerfF/RTProxy` (no Nanite, no distance field, no collision), section `leaf` = `M_CityCrown` (opaque two-sided foliage), `bark` = the city bark MI; one actor per tile in `City/RTProxy`, **hidden in game + affect indirect lighting while hidden**, no shadow; the original tree HISMs leave the ray-tracing scene (raster, shadows, distance fields unchanged). `build_map.py` step `tree_proxy`; default perf_apply steps now `rt_lite_trees,rt_proxy_trees,cloud`.

## 2. Mistakes and void numbers (facts)
- First form `render_in_main_pass = False`: the proxies were not in ray tracing at all (engine `RayTracingMaterialHitShaders.cpp` 512 and `LumenSceneRendering.cpp` 400 skip primitives that do not render in the main pass): S1 canopy luma 1.93x as found. Replaced by hidden-in-game + indirect-while-hidden (`RayTracing.cpp` 1368 keeps it for the game view).
- **Sessions `perf/void_nohero/p1` and `perf/void_nohero/f1` are VOID**: the Interchange-default complex collision of the (hidden) proxy meshes blocked the PlayerStart ("FindPlayerStart: NO PLAYERSTART with positive rating", "Couldn't spawn Pawn"), so there was no hero and the camera stood still for the whole "route" (p50 ~14.2-14.7). Found from the route stills (all four identical). Fixed by collision-free proxy meshes (`CTF_USE_SIMPLE_AS_COMPLEX` + no simple shapes + `NoCollision` profile); `g1` logs have no spawn failure and the telemetry shows the swing. The void numbers are kept (`void_nohero/VOID.txt`) and never used.
- Characters staged from P2's r07 WIP (see 0), not the merged r06.

## 3. Round target and result (`perf/g1`, shipped path `@ini`, no per-run cvars)
| line | target | result | pass |
|---|---|---|---|
| ray-tracing instances of the trees | <= 1 k | 402 proxies (whole level 920) | yes |
| mean FrameTime - GPUTime | <= 0.9 ms | ship_a **1.29**, ship_b 0.48, ship_c 0.39 (mean of the 3: 0.72); control r4_a / r4_b 1.90 / 1.45; notree 0.50 | **no in ship_a** (2 of 3 runs pass). Metal GPUTime carries a per-process offset (SPEC P8 caveat), which is why one run of the same config reads 0.9 ms higher |
| in-game `wh_perf` p95 | <= 17.9 ms in 3 runs | **17.81 / 17.86 / 17.87** | yes, **margin 0.03-0.09 ms** |
| round-02 S1 crop (485,0,710,490) SSIM vs as found (`_scratch/perf/r03/before`, same crop) | >= 0.97 | **0.9292** (earlier capture of the same content 0.9282); control r4 0.9454 | **no** |
| S1 canopy luma vs as found | +-10 % | **0.998** (control r4 0.908) | yes |

Other lines (same session):
| config | CSV p50 | CSV p95 | in-game p95 | p99 | max | frames > 18.18 | hitches | gap |
|---|---|---|---|---|---|---|---|---|
| ship_a / b / c (proxies) | 15.65 / 15.68 / 15.72 | 17.79 / 17.76 / 17.75 | 17.81 / 17.86 / 17.87 | 18.90 / 18.78 / 18.93 | 28.3 / 22.0 / 25.8 | 51 / 50 / 51 | 0 | 1.29 / 0.48 / 0.39 |
| r4_a / r4_b (round-04 content, same build, `/Game/PerfF/RTvRk20`) | 15.93 / 16.10 | 17.73 / 18.06 | 17.80 / 18.21 | 18.55 / 18.98 | 20.6 / 24.0 | 36 / 77 | 0 | 1.90 / 1.45 |
| notree (no tree geometry in RT, `RTvNk20`) | 14.83 | 16.93 | 17.02 | 17.68 | 22.8 | 7 | 0 | 0.50 |
| s2 (P3 static S2) | 14.40 | 15.61 | 15.62 | 16.17 | 19.8 | 8 | 0 | 3.12 |
| **life** lwarm / a / b / c (P6 traffic + crowd ON, `/Game/PerfF/Life/Manhattan`) | 17.07 / 17.13 / 17.13 / 17.11 | 19.46 / 19.61 / 19.47 / 19.37 | 19.96 / 20.15 / 19.91 / 19.94 | 20.7-20.9 | 31.7 / 37.8 / 25.8 / 30.6 | 410-428 | 0 / **1** / 0 / 0 | 0.23 / 0.18 / 1.17 / 0.26 |
- Proxies vs the round-04 content on the same build: p50 -0.28 ms (15.68 vs 15.96 mean), CSV p95 -0.14 ms, in-game p95 -0.15 ms, gap -0.9 ms mean. Trees in ray tracing cost +0.85 ms p50 over no trees (round 04: +1.1 ms).
- **With traffic and crowd ON the route FAILS P1 and P2**: p50 17.1 (> 16.67), CSV p95 19.4-19.6 and in-game p95 19.9-20.2 (> 18.18), one hitch (37.8 ms, life_a). Life costs +1.4 ms p50 / +1.7 ms p95 (P6's own round-02 number: +2.85 ms GPU at 4K / 67 %). The round-04 route had no traffic / crowd; the shipped `/Game/Maps/Manhattan` still has none.
- Life thread times (g1): GameThread 1.85 -> 4.3 ms, RHI thread 2.7 -> 5.2 ms, GPU 14.4 -> 16.9 ms (ship_a vs life_a / life_c).
- The worst frames of the ship runs (28.3 / 25.8 ms) are single spikes below the hitch rule (> 25 ms AND > 2x median = 31 ms).

## 4. Look (`LOOK_GATE_raw.md`, `look_gate_final.json`; stills `stills/final_*.jpg` = 1920x1080 JPEG of the 3840x2160 PNGs, internal 1920x1080)
- S1: crop SSIM 0.929 (fails 0.97), canopy luma 0.998, saturation 1.005, S2 windows 0.992 / gold 0.982 (S2 gold below 0.97 was not a round-04 line either: round 04 0.985).
- **Noise floor of the crop measure**: two captures of the SAME shipped content: 0.9859 (final vs `p4`); one earlier pair (before the collision fix, no hero in the level) read 0.964. The 0.97 line sits near the repeat noise of this capture; the gate was NOT changed.
- The proxy canopy structure differs leaf by leaf from the as-found masked any-hit (`cmp/S1_crop_r02_asfound_r04ctl_r05.jpg`): per-leaf brighter / darker speckle; brightness matches (the round-04 content was 9 % too dark). Decimating the near trees made it worse (every 4th card 0.913, every 6th card at coverage 1.0: canopy 1.32x too bright).
- Route stills are NOT comparable to the as-found set any more (new camera); the gate's route rows (t28 / t38 saturation "FAIL", sky ratios) compare different frames and are not evidence either way. Same-build comparison with the round-04 content (`cmp/route_t20_r04ctl_r05.jpg`, `cmp/route_t42_r04ctl_r05.jpg`): canopy at t20 68.9 vs 61.1 (as found on the old camera: 72.0); trunks and bark in shade again occlude GI (bark back in ray tracing).
- Disclosed visual differences vs as found: leaf-level canopy GI pattern (above); far trees (l1, > ~50 m) are represented by every 16th card enlarged ~3x in ray tracing (coarser far-canopy occlusion / reflection); proxies are not in reflection captures; characters out of ray tracing (unchanged since round 03); far shadows from VSM (round 04); cloud 20 km (round 04).

## 5. Clip
`route_30s.mp4` (14.6 MB, 30.0 s; hero spawned, no spawn errors in its log): see `route_30s_settings.json` (1920x1080 output at native 1080p internal, Nanite error 4, fixed 1/60 s step, footage only, says nothing about real-time speed).

## 6. Cost of the proxies (facts)
- Content: 717 MB of local `.uasset` (never committed), import + build ~16 min in the commandlet (`perf_apply rt_proxy_trees`).
- Per-pass GPU (void session f1, same content, no hero; for the direction only): the proxies add ~+0.2 ms to `LumenScreenProbeGather` vs the round-04 content (`void_nohero/f1/gpu_pass_diff.txt`).

## 7. Critic pack
`/Users/midir/sm2-n1/_scratch/critic-F-r05/pack` (8 pairs: S1 / S2 / S7 / route t28 / clip vs the private references, round 04 vs round 05 S1, round 05 vs as found S1, round 05 vs round-04 content route t20 on the same build), key `pack.key.json`, `pairs.json`.
