# PERF-STRATEGY — Fable 5.1 director, 2026-09-29 18:45 (planning only)

Evidence: manhattan round-01 `perf/tsr67/csv.csv` + `tsr67.log`, look round-01 PERF.md, build scripts, `WebTravCharacter.cpp`.

## 1. Honest target
60 fps at 4K OUTPUT is realistic only with **TSR 50 % (1920x1080 internal)**; stretch 58 % (2227x1253). TSR 67 % will not hold 60 with Lumen + VSM; native 4K/60 is out (42 ms GPU at 1447p today). No frame generation exists for Metal in UE 5.8 (no MetalFX/FSR/DLSS plugin ships; interpolated frames would not count as gameplay 60 anyway). Acceptance: 30 s Manhattan route, fixed step, exclusive lock, `perf_valid: true`: **p50 ≥ 60 fps, p95 ≥ 55**, plus the S2-type high view ≥ 55. 1080p internal is the budget class SM2 uses in PS5 performance mode; disclose it.

## 2. The "render-thread problem" is not CPU work
RenderThreadTime 50.6 = `RenderThreadOther` 40.2 + `EventWait` 6.1 + ~4 ms real. Per-frame correlation of RenderThreadOther with GPUTime = **0.989**; RT ≈ GPU + 8.5 ms in every 5 s block, and in all six look configs RT = GPU + 3 ms at three resolutions. The render thread is blocked on the GPU (offscreen, no vsync), not on draw calls. **Verdict: GPU-bound.** No tile merging, HLOD, World Partition or facade-to-Nanite (8 UV → data texture) rewrite now; revisit only if RT stays > 12 ms once the GPU is fixed.

## 3. Where the 42 ms GPU goes (causes found in code)
- **Every perf run rendered the scene three times.** `WebTravCharacter.cpp:385-420`: with `-WHTravCsv` the hero spawns two `SceneCaptureComponent2D`, `bCaptureEveryFrame`, 480x270 — a hero mask and a FULL-scene depth capture (Nanite culling of 116k instances, VSM, prepass again). CSV `Ticks/SceneCaptureComponent2D` = 2 every frame. All numbers to date include this.
- **NaniteVisBuffer 10.1 ms** (look r1: < 0.6). New since: r05 street kit (Nanite, `M_CityKit` masked two-sided → programmable raster), `M_CityLeaves` masked two-sided on Nanite trees, 29k Nanite hinterland instances tens of km out.
- **ShadowDepths 5.8 + projection 1.6** (VSM): log `[VSM] Non-Nanite Marking Job Queue overflow`; `SceneCulling/NumDynamicInstances` 55,644 vs 450 static → pages likely invalidated every frame.
- LumenScreenProbeGather 7.5, SceneLighting 1.6, SceneUpdate 0.9 (Epic tier); Clouds 1.2 + VolFog 1.2 + sky capture 0.7 + Unaccounted 3.7. (`TranslucentLighting` 2.1 avg is one 3840-ms outlier; ignore.)

## 4. Work list (payoff order; savings at tsr67; each A/B under `gpu_slot.sh perf`, same `route_30s_warmup15.json`, tsr50 + tsr67, one variable per run)
1. **P3** (Sonnet xhigh, ~1 h): gate both captures behind `-WHTravMask`, off by default; C's route/anim checks pass the flag. **F** measures first with a local patch. −4…−10 ms.
2. **F** (Opus high): cost probes, one cvar per run: `r.Nanite.ProgrammableRaster 0`, `r.Shadow.Virtual.Cache 0/1` + `ShowStats`, `sg.GlobalIlluminationQuality 2`, `sg.ShadowQuality 2`, `r.VolumetricFog.GridPixelSize 16`. Output: attributed table + cvar set → P4 presets (never DefaultEngine.ini).
3. **P1** (Sonnet xhigh): split `M_CityKit` opaque/masked (gratings, railings, ladders as real bars or non-Nanite); leaves opaque cards or non-Nanite; hinterland 29k → ≤ 8 merged static meshes (non-Nanite, no shadow). −3…−6 ms.
4. **F + P4**: VSM — `ResolutionLodBiasDirectional 1`, `NonNanite.IncludeInCoarsePages 0`, clipmap ≤ 2 km with DF shadows beyond; find and kill the per-frame invalidator (anything moving in the rig/sequence, WPO on trees). −2…−4 ms.
5. **P4**: Lumen High-tier cvars from F, HW RT kept; fog grid 16, cloud sample scale 0.4; sky capture time-sliced or static. −3…−5 ms.
6. **C**: re-integrate after each merge; only `/Game/Maps/Manhattan` numbers count.
Sum −12…−25 ms → ~12–20 ms at 50 %: 60 fps at TSR 50 % is reachable, 67 % is not. If GPU stays > 14 ms: tree impostors > 400 m, Lumen reflection downsample, then facade Nanite.

## 5. Must not be sacrificed
Lumen GI (L1–L3 near-black limits, L14 p10 15–30); height fog + aerial perspective + clouds (L9–L12, C11–C15); facade shader at street distance (C1–C3, interior mapping); trees ≥ 3 in S1 (C7); Lumen reflections on glass (L17); motion blur (L18/T20); VSM within 2 km (contact shadows on fire escapes and cornices, C3). Cuts only in probe density, far shadow resolution, fog grid, sky capture, masked-material geometry. A blind look critic checks S1/S2/S7 before/after every preset change.

## 6. Owner decisions
1. Confirm "60 fps at 4K" = 4K output at TSR 50–58 % internal, disclosed. Native or 67 % would mean dropping Lumen or VSM — not recommended.
2. Approve Lumen High tier + VSM bias, gated on the spec lines above still passing.
3. Approve P1 spending its next round on the kit/leaves/hinterland restructure instead of a look gap.
