# F perf, round 01: notes (neutral facts, no self-assessment)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. Numbers are from the RUNNING game (`-game`, offscreen, 3840x2160 back buffer)
> on piece C's integrated `/Game/Maps/Manhattan` (golden rig), the 30 s swing route `route_30s_warmup15.json`, window = game seconds 15..45, fixed step
> (`-benchmark -fps=60`), CSV profiler (1800 frames per run), every run inside `gpu_slot.sh perf` (exclusive lock, GPU < 15 % for 10 s before the run,
> `perf_valid: true` in the sidecar next to each session; util before every session 0-4 %). Build under test = branch base `1bbd260` (integration before look R2 / water),
> content rebuilt by C's scripts on 2026-09-29 22:25. Raw rows: `TABLE_probes.md` (every run of the round), `perf/` (official runs incl. `result.json`).

## 1. What the frame was made of (Unreal Insights, headless: `tools/perf_ue2/insights_frame.py`)
- **The perf harness itself cost 11.6 ms.** With `-WHTravCsv` the hero spawned two 480x270 `SceneCaptureComponent2D`, capture-every-frame (hero mask + a FULL-scene depth
  capture = a second Nanite / VSM / prepass pass). Off (this round's local patch, `p3_capture_gate.diff`): TSR 50 % route p50 38.03 -> 26.45 ms in the same session.
  Every earlier number of this project (perf, look, manhattan) includes it.
- **4K output is not free at a 1080p internal.** Same internal 1920x1080: 1080p output at `r.ScreenPercentage 100` = p50 23.11 ms vs 4K output at 50 % = 27.96 ms (+4.85; two different sessions, so +-1.6). Two parts:
  Nanite measures its cluster error against the OUTPUT resolution (NaniteVisBuffer 3.99 -> 6.79 ms, so `r.Nanite.MaxPixelsPerEdge 1` at 4K output = 2 sub-pixel-dense triangles per internal pixel),
  and the TSR / post chain runs at 3840x2160 (Epic tier: `r.TSR.History.ScreenPercentage 200` = a 7680x4320 history).
- **The frame is GPU-bound, but the GPU graphics-queue timeline has holes.** Trace (base config): render thread 26 of 28 ms in `InitViews > OcclusionCullPipe >
  RHIGetRenderQueryResult_GPU_Wait` (waits for the GPU's previous frame); `GPU0-Graphics0`: SceneRender 17-22 ms, ~3 ms idle before PostProcessing (TSR / post at 4K),
  ~1.3 ms idle after the ray-tracing scene build. Turning hardware occlusion queries off (`r.AllowOcclusionQueries 0`) moves the render thread to 10 ms and changes the frame time by 0.0-0.3 ms: GPU-bound.
- With software Lumen (perf60) the same trace shows a continuous graphics queue: no idle hole before PostProcessing, none after the ray-tracing scene build (there is none); PostProcessing (TSR + post at 4K) = 2.5 ms.
  So hardware RT costs its passes (~3 ms) plus ~4 ms of GPU bubbles; that is why the master switch is worth -4.6 ms while the pass table only shows -3 (`insights/base50_defaults.txt`, `insights/cand1_perf60.txt`).
- `GPUTime` and the per-pass CSV columns do not add up to the frame time (`GPU/Unaccounted` 1.6-3.6 ms, and passes swap between `Postprocessing` and `Unaccounted` between runs); the frame p50 is the
  ground truth, pass tables are only indicative to ~1 ms.

## 2. Session drift: every delta below is against a control in the SAME session
Identical configs measured in different sessions differ by up to 1.6 ms (base TSR 50: 27.96 in the first session, 26.45 in later ones; mpe4+hwrt0: 18.35 vs 16.76). Four "wins" of one session
(`sg.AntiAliasingQuality 2`, `r.TSR.History.ScreenPercentage 100`, `sg.PostProcessQuality 2`, `r.MotionBlur.HalfResGather 1`, each -1.6 ms against the first session's 27.96) were this drift: against the later control 26.45 they are -0.1 / +0.1 / -0.3 / -0.1.
`gate_on50` / controls are in `TABLE_probes.md`.

## 3. Probe results (TSR 50 %, 3840x2160 output, 1920x1080 internal, p50 frame ms; delta = config minus its session's control; V0 = content untouched)
| probe | p50 | delta | note |
|---|---|---|---|
| `r.Nanite.MaxPixelsPerEdge` 2 / 3 / 4 / 6 | 25.09 / 23.24 / 22.53 / 22.14 | -2.9 / -4.7 / -5.4 / -5.8 (vs 27.96) | NaniteVisBuffer 6.8 -> 4.2 / - / 1.8 ms. Trees, street furniture and detail tiles only (facade, roofs, far LOD are non-Nanite). 4 px keeps SSIM 0.99 vs 1 px (S1 / S2 / S7, `cmp/`) |
| `r.Nanite.ProgrammableRaster 0` (diagnostic) | 26.53 | -1.4 | masked leaf cards become opaque quads: not usable; NaniteVisBuffer 6.8 -> 2.7 = the masked-material share |
| `r.Lumen.HardwareRayTracing 0` (software Lumen) | 23.37 | -4.6 | master switch; GI-only (`ScreenProbeGather.HardwareRayTracing 0`) -0.4, reflections-only (`Reflections.HardwareRayTracing 0`) -0.7: the cost is the ray-tracing scene + both users |
| mpe4 + hwrt0 | 16.76 (control 26.45) | -9.7 | additive |
| `r.Shadow.Virtual.Cache 0` | 34.45 | +6.5 | cache works: 137 of 2048 pages requested, static-cached; skipping dynamic invalidation = 0.05 ms, so no per-frame invalidator |
| VSM `ResolutionLodBiasDirectional 1` | 27.30 | -0.66 | kept (`cheap`) |
| VSM `NonNanite.IncludeInCoarsePages 0`, `Clipmap.LastLevel 18` | 27.87, 27.73 | -0.1, -0.2 | nothing |
| `sg.GlobalIlluminationQuality 2`, `sg.ShadowQuality 2` | 27.84, 27.83 | -0.1, -0.1 | nothing (GPU stat -1.6 ms but the frame did not move) |
| fog grid 16, cloud `ViewRaySampleMaxCount 512`, sky capture 64 px | 27.65, 27.77, 27.55 | -0.3, -0.2, -0.4 | small, kept (`cheap`) |
| sky real-time capture off (diagnostic) | 27.16 | -0.8 | not usable (ambient sky light) |
| `r.AllowOcclusionQueries 0`, `NumBufferedOcclusionQueries 2`, `HZBOcclusion 1` | 28.15, 27.62, 32.65 | +0.2, -0.3, +4.7 | frame is GPU-bound (Insights); HZB occlusion is slower |
| `r.Lumen.ScreenProbeGather.DownsampleFactor 32`, `TracingOctahedronResolution 6` | 26.15, 26.43 | -0.3, 0.0 | (control 26.45) |
| `r.VolumetricRenderTarget.Mode 2` + scale 0.7 | 27.38 | +0.9 | worse |
| TSR / post: `r.TSR.History.ScreenPercentage 100`, `sg.AntiAliasingQuality 2`, `sg.PostProcessQuality 2`, `MotionBlur.HalfResGather 1` | 26.55, 26.35, 26.17, 26.39 | +0.1, drift, drift, -0.1 | nothing once controlled |
| on top of perf60 (`ctlF` 16.71 / 16.52): `SMRT.RayCountDirectional 4`, `TimeSlice 1` (sky), cloud 256, VSM moving bias | 16.29, 16.48, 16.49, 16.47 | -0.3, -0.1, -0.1, -0.1 | kept as `extra`; cloud `DistanceToSampleMaxCount 8` 16.53 (0) |
| Nanite `MaxPixelsPerEdge 6` on top of perf60 | 15.93 (official 15.79) | -0.65 | reserve lever, look check `cmp/perf60mpe6_*` |
| floor: TSR 25 % (960x540 internal), mpe4 + hwrt0 + occ0 | 14.14 | - | 4K-output fixed cost floor of this frame |

## 4. Content transformations (`tools/perf_ue2/perf_apply.py`, local content only; each cumulative on perf60 candidate 1, control 16.41 / 19.83)
| step | what | p50 / p95 |
|---|---|---|
| `static` | 87 City/Props + City/Far instanced components Movable -> Static | 16.34 / 20.31 |
| `far_plain` | hinterland (28 965 Nanite instances) non-Nanite | 16.43 / 19.90 |
| `kit_plain` | street-kit + detail tiles (20 meshes) non-Nanite | 16.43 / 19.83 |
None moved the frame: with the Nanite error at 4 px and software Lumen the instance count / mobility / masked kit are no longer the cost. Content restored to the build (V0) afterwards.

## 5. Late-route cost (why p95 misses)
Per 3 s window of `perf60` at TSR 50 %: first 3 s p50 13.85 ms; 21-24 s 18.41 ms. The difference is VolumetricCloud 0.34 -> 2.35 ms (looking at the horizon over the far LOD) and NaniteVisBuffer 1.21 -> 3.09 ms;
256 of the last 600 frames exceed 18.2 ms vs 23 of the first 600. The cloud pass does not react to `ViewRaySampleMaxCount` / `DistanceToSampleMaxCount` / render-target mode (the component's own
tracing distance, 50 km in the preset, is the untested lever), Nanite reacts to the error bound (mpe6: 2.29 ms).

## 6. Visual checks (S1 / S2 / S7 4K stills + route t 20 / 28 s, TSR 50 %, `cmp/`)
- mpe4 alone vs before: PSNR 36.5-46.1 dB, SSIM 0.990-0.995, mean |dY| 0.7-2.0. Looks identical at viewing size.
- perf60 (mpe4 + software Lumen + cheap + extra) vs before: see `cmp/perf60_vs_before/compare.json` (software Lumen changes bounce colour and ambient: mean Y S1 82.8 -> 87.2, S2 97.7 -> 93.1, route t28 68.5 -> 78.6;
  near-black fraction and clipped fraction unchanged within 1 %). The route stills are not pixel-identical between runs (the shot fires on game time, not on the fixed step), so route PSNR is indicative only.
