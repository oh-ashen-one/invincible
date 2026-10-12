# PERF-SPEC (piece F: 4K output at 60 fps on the Mac Studio M3 Ultra)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. Written by the F builder, round 1, from
> `docs/night1/director/PERF-STRATEGY.md` (Fable director, 2026-09-29). Fixed targets; a round only closes on a critic verdict backed by these numbers.

## What "60 fps at 4K" means here (director section 1, owner decision 6.1 pending)
- **Output** 3840x2160, real `-game` run, offscreen, true 3840x2160 back buffer. **Internal (pre-TSR) resolution is always disclosed**
  from `wh_perf.internal_w/h` of the run: `r.ScreenPercentage 50` = 1920x1080, 58 = 2227x1253, 67 = 2573x1447, 100 = native.
  1080p internal is the budget class Marvel's Spider-Man 2 uses in PS5 performance mode.
- No frame generation exists for Metal in UE 5.8, and interpolated frames would not count as gameplay 60 anyway.

## Lines
| id | line | how measured |
|---|---|---|
| P1 | 30 s Manhattan route (piece C `route_30s_warmup15.json`, game seconds 15..45): **p50 frame time <= 16.67 ms (60 fps)** | `tools/perf_ue2/perf_route.py` under `gpu_slot.sh perf`, sidecar `perf_valid: true`, CSV profiler over the window |
| P2 | same run: **p95 <= 18.2 ms (55 fps)**, hitches (frame > 25 ms and > 2x median) = 0 | same |
| P3 | heavy static view (P1 shot S2, 42 m over the avenue): **p50 <= 18.2 ms (55 fps)** | `perf_route.py --script none --map /Game/Maps/Manhattan_View_S2` |
| P4 | no visual regression: S1 / S2 / S7 4K stills before / after, luma stats inside the look spec lines (L1 mean Y 61-100, near-black <= 8 %, clipped <= 1.8 %), SSIM / PSNR vs the pre-change still, blind A/B of before vs after | `tools/perf_ue2/stills.sh`, `compare_stills.py`, `abpack.py` |
| P5 | contamination: every number carries the `gpu_slot.sh summary` line (util before / after, instances before) | sidecar json |
| P6 | (round 02, from the round-01 critic) cloud pass: `GPU/VolumetricCloud` mean over the LAST 600 frames of the route window <= 0.7 ms (control 2.3 ms); t20 / t28 route stills keep SSIM >= 0.98 vs the same config with the as-found cloud distance | `tools/perf_ue2/windows.py`, `compare_stills.py` |
| P7 | (round 02) glass reflections / lit windows: hardware-RT Lumen reflections ON, or crop SSIM >= 0.97 (S1 glass tower, S2 lit windows, S2 gold tower) against the as-found hardware-RT look with software Lumen | `tools/perf_ue2/crop_ssim.py` |
| P8 | (round 03, from the round-02 critic) CPU / GPU serialisation: mean `FrameTime - GPUTime` over the route window <= 1.0 ms (round 02: 2.89 ms with hardware-RT reflections, 0.81 ms with software Lumen); no Unreal Insights / trace server: found with CSV profiler columns (`FrameTime`, `GPUTime`, `Exclusive/RenderThread/*`). **Caveat (round 03): on Metal `GPUTime` has a per-process offset (the same config reads 1.2 or 2.7 ms), so the absolute gap is reported together with a same-session software-Lumen twin and the chain fit `FrameTime[n] = a + b*GPUTime[n-1] + c*GPUTime[n]`; the twin-relative cost of hardware-RT reflections is the evidence** | `tools/perf_ue2/serial.py` on the run CSV |
| P9 | (round 03) shipped path: the round-02 preset (cloud 4 km, RT-lite scene, `perf60_hwrefl` cvars, TSR 46 %) is carried by the REBUILT integrated `/Game/Maps/Manhattan` through committed scripts only (`tools/perf_ue2/build_map.py`); P1 / P2 measured on that map with NO per-run cvars (spec `@ini`), internal resolution disclosed | `content_audit.json`, `perf_route.py` spec `name@ini` |
| P10 | (round 04, from the round-03 critic) VSM: `GPU/ShadowDepths` p95 over the route window <= 2.5 ms (round 03: 4.22) | CSV column of the P1 run |
| P11 | (round 04, from the round-03 critic) look gate vs the as-found stills of the same build (`_scratch/perf/r03/before`): round-02 S1 crop (485,0,710,490) SSIM >= 0.97 (never moved), canopy luma (as-found green-dominant pixels) within +-10 % in every still where the mask covers >= 1 %, route saturation within 5 %; cloud TracingMaxDistance >= 20 km, trees within ~100 m in the ray-tracing scene. **P6 (0.7 ms at 4 km) is superseded by the 20 km demand** | `tools/perf_ue2/look_gate.py` |

## Must not be sacrificed (director section 5)
Lumen GI (L1-L3 near-black limits, L14 p10 15-30), height fog + aerial perspective + clouds (L9-L12, C11-C15), facade shader at street distance
(C1-C3), trees >= 3 in S1 (C7), Lumen reflections on glass (L17), motion blur (L18 / T20), VSM within 2 km (C3). Cuts only in probe density, far
shadow resolution, fog grid, sky capture, masked-material geometry.

## Method rules
- One variable per run; a config is a screen percentage plus a cvar set applied at startup with `-dpcvars` (and re-applied with `-ExecCmds`),
  or a content transformation (`tools/perf_ue2/perf_apply.py`) with a control run of the untouched content in the same lock session.
- A/B of one look / content setting: `tools/perf_ue2/make_variants.py` makes map copies under `/Game/PerfF/<tag>/` (cloud distance, ray-tracing scene) so control and treatment share one lock session (`+variant:<tag>` in a perf_route spec; `+view:S2` = static view).
- The first run of a session (and any new map / cvar combination) is cold: p50 is fine, p95 is not (shader / PSO / streaming hitches up to 0.8 s). Put a throw-away `warm` config first and repeat any config whose p95 decides a verdict; hitch frames are reported.
- Fixed step (`-benchmark -fps=60`) so every config sees the same frames; the perf window starts after 15 s of standing warm-up.
- Any number not taken inside `gpu_slot.sh perf` is CONTAMINATED and not used as evidence.
- Cvar sets and content changes for other pieces are documented here and in HANDOFF.md; nothing is written to DefaultEngine.ini (integrator-owned).
