# F perf, round 03: notes (neutral facts, no self-assessment)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. Numbers are from the RUNNING game (`-game`, offscreen, 3840x2160 back buffer) on the REBUILT integrated
> `/Game/Maps/Manhattan` (golden rig), the 30 s swing route `route_30s_warmup15.json`, window = game seconds 15..45, fixed step (`-benchmark -fps=60`), CSV profiler (1800 frames per run), every
> run inside `gpu_slot.sh perf` (exclusive lock, `perf_valid: true`, one Unreal instance, no Unreal Insights / trace server: every launch passes `-notraceserver`). Spec: `../SPEC.md` (P1-P9).
> Raw rows: `TABLE.md` (every run), `SERIAL.md` (frame vs GPU time chain per run), `perf/<session>/<config>/result.json`; session folders `a1 b1 c1 d1 e1 f1 g1` (`run.txt` = the exact command line of each config).

## 1. What was built (all by committed scripts; nothing under `Content/` or `Config/Mac/` is committed)
- Merge `origin/Opus-5.5-Loop-Night-1` (c4fffda) into `night1/perf`: 60 commits (city r07-r09 shade fill / trees / cars / traffic, traversal flips, combat, life, look).
- `python3 tools/perf_ue2/build_map.py --steps cpp,city_export,city_prep,city_extra,city,traversal,characters,look,map` = C's unchanged `build_manhattan.py` (scratch `_scratch/perf`, F's own vite port 5209) plus the
  F-owned step `city_extra` (P1's `export_vehicles / street_cars / street_trees / street_traffic / bake_sunmask`, which `build_manhattan.py` of round 01 predates and `build_city.py` r08 / r09 needs). 625 s from the merged sources.
  As built: 117 506 instances in the hardware ray-tracing scene (`content_audit_asbuilt.json`), cloud tracing 50 / 40 / 30 km, 13 street people in the ray-tracing scene.
- `python3 tools/perf_ue2/build_map.py --steps perf_apply,perf_preset,perf_audit` then turns the rebuilt content into the shipped perf state (`content_audit.json`):
  - `perf_apply` steps `rt_lite,cloud`: `visible_in_ray_tracing = False` on 235 components (hinterland `City/Far`, trees + street props + parked cars `City/Props`, far ground `City/far`): **518 of 117 506 instances stay in the ray-tracing scene**
    (facades, roofs, ground, streetkit, detail, signage, markings, stopped traffic); `VolumetricCloud.TracingMaxDistance` 4 km in the golden / midday / night rigs (was 50 / 40 / 30).
  - `perf_preset` writes the cvar preset `tools/perf_ue2/overrides/perf60_hwl.cvars` + `r.ScreenPercentage 50` as a marked `[ConsoleVariables]` block of `unreal/WebHomage/Config/Mac/MacEngine.ini` (generated, untracked).
    Every Mac launch of this checkout (editor, `-game`, commandlets) reads it: the log shows `LogConfig: Set CVar [[r.ScreenPercentage:50]]`, and perf runs with spec `name@ini` pass NO cvar and no `r.ScreenPercentage` on the command line.
    `Saved/Config/MacEditor/Engine.ini` does not work for this: the engine DELETES it at exit when it holds only console variables (measured). Removal: `build_map.py --preset-off`.
    Integrator adoption = the same lines as a `[Mac DeviceProfile]` `+CVars=` block in `DefaultDeviceProfiles.ini` (integrator-owned, not edited here).
  - Shipped-path proof: session `f1` runs with spec `@ini`: `wh_perf` reports `internal 1920x1080`, `screen_percentage_mode manual` without any `r.ScreenPercentage` argument.

## 2. Result on the shipped path (`perf/f1`, exclusive lock, util before 2 % / after 0 %, 3840x2160 output, internal 1920x1080 = the as-found internal resolution, preset `perf60_hwl`)
| run | p50 ms (fps) | p95 ms (fps) | p99 | max | hitches | frame - GPUTime | |
|---|---|---|---|---|---|---|---|
| `hwl_a` route | **15.46 (64.7)** | **17.88 (55.9)** | 19.62 | 24.11 | 0 | 0.82 | P1 pass (<= 16.67), P2 pass (<= 18.18) |
| `hwl_b` route (repeat, same session) | **15.34 (65.2)** | **17.91 (55.8)** | 19.70 | 24.84 | 0 | 0.83 | P1 / P2 pass |
| `hwl_s2` static S2 view | 14.49 (69.0) | 15.45 | 15.90 | 16.62 | 0 | 0.88 | P3 pass (<= 18.2) |
P6 cloud pass (`GPU/VolumetricCloud`, last 600 route frames): 0.49 / 0.49 ms (<= 0.7; as found 2.3). P2 margin is 0.27-0.30 ms; session drift of identical configs in this round was +-0.1 ms (`ship_a/b/c` 15.27 / 15.26 / 15.21).
Crop SSIM (P7, 8x8 box SSIM on luma of the 1920x1080 downsample, vs the as-found still of the same rebuilt map at TSR 50, `crop_ssim_final.json`, crops in `tools/perf_ue2/crop_ssim.py` set `r03`):
**S1 glass 0.9733, S2 windows 0.9921, S2 gold 0.9773 (all >= 0.97: pass).** The `r03` S1 crop is (775,0,900,215): the street trees of the rebuilt city cover the round-02 crop; the glass curtain wall + the window tower behind it sit above y 215.

## 3. The serialisation (P8): what it was, what removed it (`SERIAL.md`, `perf/*/result.json`)
Method without Insights: CSV columns `FrameTime`, `GPUTime`, `Exclusive/RenderThread/*`, per-pass `GPU/*`, then least-squares `FrameTime[n] = a + b*GPUTime[n-1] + c*GPUTime[n]` (`tools/perf_ue2/serial.py`).
- **The frame chains to the previous frame's GPU time** (b ~ 1.0, R2 0.8 in every route run): the render thread sits 11-12 ms per frame in `EventWait/Visibility` (`InitViews > OcclusionCullPipe`, waiting for the previous frame's GPU); this is the same in the software-Lumen twin. Breaking it did nothing for the frame:
  `r.AllowOcclusionQueries 0` moves the render thread from 16.5 to 4.7 ms (the RHI thread then absorbs the 13.5 ms wait) and p50 stays 16.57 vs 16.39; `r.NumBufferedOcclusionQueries 2` changes nothing (16.38). The frame is GPU-bound on the rebuilt map; the round-02 gap (2.89 ms) was mostly the extra cost below.
- **The animated hero is the whole dynamic ray-tracing cost.** `GPU/RayTracingScene` = 1.5 ms EVERY frame of the moving route (0.03 ms in the static view and in every run without skeletal meshes in the ray-tracing scene). Same session (`b1`, `c1`):
  | config (TSR 46, software GI) | p50 | p95 | `RayTracingScene` ms |
  |---|---|---|---|
  | control (hero + 13 people in the RT scene) | 16.43 / 16.39 / 16.45 | 18.79 / 18.92 / 19.02 | 1.51 |
  | 13 street people out (`Cl4P` map copy), hero in | 16.29 / 16.36 | 18.77 / 19.07 | 1.48 |
  | `r.RayTracing.Geometry.SkeletalMeshes 0` (hero + people out) | **14.79 / 15.05 / 14.90** | **17.41 / 17.68 / 17.44** | 0.03 |
  | software Lumen twin | 14.37 | 16.91 | - |
  The hero (SpiderMan 27 291 vertices + Lenses 1 723, one LOD) costs 1.5 ms; the 13 people (17-19 k vertices each) 0.1 ms together. A dynamic-geometry update budget of 1 primitive (`r.RayTracing.DynamicGeometry.MaxUpdatePrimitivesPerFrame 1`) changes nothing (16.34),
  nor does forcing the Metal fast-build mode (`r.Metal.RayTracing.DebugForceBuildMode 1`: 16.75 vs 16.70): the cost is the per-frame acceleration-structure build / encoder switch of a MOVING instance, not its triangle count. Adopted: skeletal meshes out of the ray-tracing scene (preset line).
  Price: characters are not mirrored by the ray-traced reflections; they stay in every raster pass and in Lumen's screen-space reflection traces.
- **`FrameTime - GPUTime` is an unreliable instrument on this platform**: identical configs show 1.2 or 2.7 ms depending on the process (`b1/p` 1.24 vs `b1/p2` 2.76, same config; `GPUTime` 15.1 vs 13.7 at the same frame time), the value is constant inside a run, and `GRHISupportsGPUTimestampBubblesRemoval` is on for Metal.
  With hardware GI on (the shipped preset) every run shows 0.76-0.88 ms (`f1`: 0.82 / 0.83, static S2 0.88; software-Lumen twin 0.66); the P8 line (<= 1.0 ms) is met on that number, but the evidence that matters is the A/B above:
  ray-tracing reflections now cost +0.45 ms over the software twin in the same session (`f1/hwl_a` / `hwl_b` 15.46 / 15.34 vs `hwl_sw` 14.95) instead of +1.96 ms in round 02 (`s2` session: 17.26 vs 15.30, both TSR 50), and the chain intercept `a` (CPU work serialised behind the GPU) is 0.71-0.73 ms (`f1`) vs -0.29 for the twin, 0.37 vs 0.02 at preset v1 (`d1`); round 02: 2.9 vs 0.8.

## 4. Hardware GI is free now, and TSR 50 needs it (look levers on the rebuilt map; stills S1 / S2, `lookprobe/crop_ssim_levers.json`)
| still set | S1 glass | S2 windows | S2 gold | all >= 0.97 |
|---|---|---|---|---|
| v1: software GI, hardware reflections, TSR 48, Nanite 6 (the round-02 preset on the rebuilt map) | 0.9427 | 0.9796 | 0.9425 | no |
| v1 + TSR 50 | 0.9546 | 0.9882 | 0.9555 | no |
| v1 + hardware GI (TSR 48) | 0.9618 | 0.9837 | 0.9603 | no |
| v1 + Nanite error 1 | 0.9461 | 0.9794 | 0.9388 | no |
| v1 + TSR 50 + hardware GI + Nanite error 1 | 0.9707 | 0.9931 | 0.9784 | yes |
| v1, trees / street furniture + cars / everything back in the RT scene (RT policy only) | 0.9447 / 0.9431 / 0.9450 | 0.9739 / 0.9731 / 0.9738 | 0.9486 / 0.9433 / 0.9483 | no |
| hardware GI, TSR 48, Nanite 8 | 0.9611 | 0.9837 | 0.9604 | no |
| hardware GI, TSR 50, Nanite 6 | 0.9698 | 0.9920 | 0.9787 | no (S1 by 0.0002) |
| **hardware GI, TSR 50, Nanite 8 = `perf60_hwl`** | **0.9733** | **0.9921** | **0.9773** | **yes** |
Same settings via cvars (`gi50m8`) and via the ini (`final`): 0.9734 / 0.9733 (capture-to-capture repeatability ~0.0001). The Nanite error does not move the crops; TSR 50 (= the internal resolution of the as-found still) and hardware GI together do.
Cost (same lock session, `e1`, preset at TSR 48 / 50): hardware GI on 15.10 / 15.60 vs software GI 15.20-15.27 / 15.64-15.67 p50: **no measurable cost** once the ray-tracing scene is the 518-instance RT-lite scene and the hero is out of it
(round 01 measured +0.4 ms for it with the full scene). Nanite error 8 vs 6: -0.1 ms p50 (`e1/m8_50` 15.40 vs `c1/sk0_50` 15.65); 10 vs 8: 0 (`f1/hwl_m10`); probe density `DownsampleFactor 32`: -0.03 (`d1/pd32`); VSM `SamplesPerRayDirectional 4`: -0.02. None adopted beyond Nanite 8.
TSR sweep, software GI, hero out (`c1`): 46 / 48 / 50 -> p50 15.05 / 15.21 / 15.67, p95 17.68 / 17.74-17.81 / 18.12-18.29 (TSR 50 sat on the 18.18 line without Nanite 8).

## 5. The trade that remains (measured, not hidden): canopy and skyline are brighter than as-found
With hardware GI the trees are not in the ray-tracing scene (RT-lite), so GI rays leave through the canopy: whole-still luma (`cmp/compare.json`, `final` vs the as-found still):
| still | mean Y as-found -> now | SSIM luma |
|---|---|---|
| view_S1 (street level, trees) | 92.1 -> 103.6 | 0.856 |
| view_S2 | 96.6 -> 97.7 | 0.968 |
| view_S7 | 55.4 -> 56.3 | 0.979 |
| route t20 | 89.5 -> 101.7 | 0.817 |
| route t28 / t38 | 60.0 -> 55.4 / 69.6 -> 65.1 | 0.951 / 0.951 |
| route t42 (high, far city) | 98.7 -> 114.1 | 0.840 |
The cause is the trees: the same frames with the trees back in the ray-tracing scene (`rtvC`, hardware GI) measure S1 90.9, t20 83.2, t42 94.5 (as-found 92.0 / 89.4 / 98.6); far ground / hinterland back in (`rtvD/E/F`) changes nothing (S1 103.4-103.5).
Cost of the trees in the ray-tracing scene (`g1`, same session, TSR 50, preset): trees in 17.67 p50 / 20.32 p95 (+2.2 ms); trees within 100 m (`r.RayTracing.Culling.Radius 10000`) 16.77 / 19.40; within 50 m 16.14 / 18.78 (and it culls the facades beyond 50 m out of the reflections too);
street furniture + parked cars in (trees out) 16.31 / 18.74 (+0.86); everything in 17.90. The control in the same session: 15.45 / 17.92. So the S1 mean luma (103.6) is above the look-spec line L1 (<= 100) and t42 (114.1) is 15 above as-found. The software-GI alternative (`perf60_hwrefl_sk0`, TSR 48, below) keeps luma within -2 .. -6 of as-found
but fails the crop gate (0.943 / 0.980 / 0.943) and was flagged by the round-02 critic as 6 % darker.
Fallback preset for the director's choice: `SM2_PERF_PRESET=perf60_hwrefl_sk0 SM2_PERF_PRESET_SP=48 python3 tools/perf_ue2/build_map.py --steps perf_preset` (`perf/d1`: p50 15.27 / 15.25, p95 17.61 / 17.86, static S2 14.01; measured on the same content).

## 6. Sessions (raw; `TABLE.md` has every run with its lock verdict)
| session | what | result |
|---|---|---|
| a1 | shipped v1 baseline + occlusion probes + TSR 50 / 58 | ctl 16.39 / 18.92 (TSR 46, hero in); occ0 16.57; occb2 16.38; TSR 50 17.2-17.3, 58 19.0 |
| b1 | hero vs people, software twin, TSR 48 / 50 | see section 3 |
| c1 | skeletal meshes out, TSR 46 / 48 / 50, update budget | sk0 15.05 / 15.21 / 15.67; dg1 16.34 |
| d1 | preset v1 official (`perf60_hwrefl_sk0`, TSR 48) + Metal fast build, probe density, software twin | ship_a / b 15.27 / 15.25 p50, 17.61 / 17.86 p95; S2 14.01; hero in 16.70; fb1 16.75; pd32 15.22; sw48 14.74 |
| e1 | hardware GI cost, Nanite error 8, TSR 46-50 | gi48 15.10, gi50 15.60, gi50m8 15.42 / 18.03, m8_50 15.40 / 17.93 |
| f1 | **official, preset `perf60_hwl` @ini** | hwl_a / b 15.46 / 15.34, 17.88 / 17.91; S2 14.49; hero in 16.94 / 19.48; software twin 14.95 / 17.30 |
| g1 | trees / props back in the ray-tracing scene (map copies `RTvA/B/C`) | section 5 |
Cold first runs (`warm*`) are not evidence. Local map copies (`/Game/PerfF/*`, `tools/perf_ue2/make_variants.py` tag `Cl4P`, `make_rtvars.py` tags A-F) are rebuilt by those scripts; nothing of them is committed.

## 7. Events and limits (facts)
- Lock waits this round: 0-14 min per perf session (other agents' captures); all runs valid. The machine was rebooted at ~10:00 (uptime 9 min at the start); no other agent's process was touched.
- `UnrealTraceServer` is auto-launched by every engine start (`FTraceAuxiliary::Initialize`, unless `-notraceserver`) and listens on `*:1981 / *:1989`; other agents' engines (traversal / characters) had started one at 10:08. F's launches (perf, stills, movie, commandlets) now pass `-notraceserver`.
  F did not start or stop any trace server. `route_movie.sh` watchdog now stops a hung engine with `stop_ue.sh` (drivers first, SIGTERM, 60 s wait) instead of `kill -9`.
- Not done: the hero-in-ray-tracing variant with a cheaper instance (nothing in cvars reduces it; needs a code-side RT proxy or a static hero reflection proxy); a decimated tree occluder set for the ray-tracing scene (would cost ~0.5 ms at half the trees, which the p95 margin of 0.27 ms cannot carry);
  the `DeviceProfiles` adoption by the integrator; the route leaves the detailed block at ~22.6 s (C's issue 4, unchanged).
- The `@ini` path and the `-dpcvars` path were compared once: `e1/gi50m8` (cvars) 15.42 / 18.03 vs `f1/hwl_a` (ini) 15.46 / 17.88, same frames.
