# Water round 03: resolved wind chop, near-field gloss, slimmer far field (Opus 5.5)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Build: `night1/water` at ef5ffab (shader) + `PARAMS` = autopick V3 (`ChopK 2.6, MicroK 2.0, ScatK 0.04, FarVarK 0.1, FoamK 1.8, BendK 0.3,
RoughN 0.06, SpecK 2.0`, committed as the defaults in bd4f98a). One capture hold (04:56:50 to 05:19:10, 1340 s, `gpu_slot capture`,
cap 2 at the time): build, 1080p iteration stills of base / V1 / V2 / V3 (`iter/`, `iter/autopick.json`), final build, stills, dollies.
Stills: 3840x2160 and 1920x1080 output at **native internal resolution** (`r.ScreenPercentage 100`), t = 16 s. Dollies: 1920x1080 at 100 %,
60 fps, t = 6 to 16 s kept (600 frames). `river_sun_dolly.mp4` was re-encoded at CRF 23 from the same frames to stay under 15 MB (11.3 MB).

## What changed in the shader (see `build_water.py` `hlsl_ps`)
- Resolved 0.15 to 0.5 m wind chop (`T_WaterChop`, 3 to 10 cycles on 1.5 / 1.17 m tiles, two realizations scrolling in two directions).
- Near field (<= 150 m): textures sampled with true gradients (no mip bias), GGX roughness from `RoughN` only (cap 0.08).
- Pale wind-streak and slick terms deleted. Whitecap and contact foam computed only in the near field and faded to zero by 150 m.
- Beyond 150 m: one spectrum realization per layer, no chop sample, no foam or contact-map lookup (perf).
- Dark body: `ScatK` 0.04 (round 02: 0.2).

## Numbers (`spec.json`, `python3 tools/water/water_spec.py all docs/night1/water/round-03`)
| check | target | round 02 | round 03 |
|---|---|---|---|
| river_low near hp sd | >= 12 | 8.5 | **9.93** FAIL (up) |
| river_low near p99.5 | >= 150 | 122 | 112.3 FAIL |
| river_low near glints (Y >= 140) | >= 1 % | 0.11 % | 0.0 % FAIL |
| river_low near mean Y | <= 80 | 79.3 | **78.5** PASS |
| river_low near p1 | <= 25 | 46 | 41.3 FAIL |
| river_sun sparkle width | >= 50 % | 35.5 % | 37.8 % FAIL |
| river_sun near mean Y | <= 90 | 137 | 148.4 FAIL |
| river_sun near glints | 3 to 15 % | 44.9 % | 52.9 % FAIL |
| harbour crop hp sd | >= 10 | 4.33 | 4.3 FAIL |
| harbour crop glints | >= 2 % | 0 % | 0.0 % FAIL |
| harbour pale blobs >= 20 px | 0 | 109 | **2** FAIL (from 109) |
| river_low dolly autocorr at 80 px | <= 0.10 | 0.006 | **0.053** PASS |
| river_sun dolly autocorr at 80 px | <= 0.10 | 0.041 | **0.015** PASS |
| S4 C14 | 5 to 35 | 22.0 | **17.9** PASS |
| seawall contact foam | present | present | **ABSENT: REGRESSION** (see below) |
| perf: frame delta / SLW at river_low | <= 2.5 / <= 2.5 ms | +1.23 / 0.80 (TSR 67 %) | **-0.25 / 1.00** PASS (native 100 %) |

Iteration stills (1080p, before the final build; 1080p reads lower on hp sd than 4K): every variant sat within a few Y of the base
(river_low p99.5 99 to 116, p1 43 to 48; harbour hp sd 2.8 to 2.9). Parameter tuning does not move these targets.

## Why the targets did not move (measured on our own frames)
1. **river_low ceiling = the sky it reflects.** In `base_river_low` the sky band the near water mirrors measures mean 114 to 121 Y (p99 137
   to 163). Even a perfect mirror at grazing Fresnel tops out near 120 Y, so p99.5 >= 150 and Y >= 140 glints cannot come from physical
   reflection under this look rig (the reference has a misty sky around 200 Y). The sun (az 238, elev 9) is behind-left, so there is no
   sun lobe. W does not own the sky or fog.
2. **river_low floor.** `ScatK` 0.04 to 0.09 moves p1 by less than 5 Y, so the trough floor (about 41) is not the water body. It is Fresnel
   times sky plus height fog / aerial perspective over 10 to 60 m of water (look rig).
3. **river_sun** is a broad golden sheen: the bright sky around the sun reflects off the whole near field (mean 148), not discrete sparkles.
   Making the sparkles discrete needs the body and the sky reflection darker away from the sun lobe. Neither ScatK nor SpecK did that.
4. **harbour_high** from 260 m is entirely in the far field (> 150 m), so the resolved chop never reaches it. The sun is behind-left of the
   view, so there are no glints. The pale blobs are gone (109 to 2) because foam is cut beyond 150 m.

## Regression: seawall contact foam missing
`crop_river_low_4k_seawall_foam.jpg` (and the base / V1 / V2 / V3 iteration stills and every dolly frame checked: 400 / 600 / 800 / 950)
show no bright band along the bulkhead. Instead there are small dark specks across the near field, densest at the wall. Round 02 had a
21 px band at Y 227. The inputs are unchanged: the contact map reads 14 to 21 (1.7 to 2.6 m) at the wall, same box and encoding. The
material wiring is also unchanged apart from the new `tK` input. Two hypotheses, not yet separated:
(a) the foam pixels inherit the steep chop normal (`NormalW = lerp(N, up, wf * 0.6)`, per-axis RMS slope about 0.34). With a 9° sun most
    of them are lit only by the sky, so they render as the dark specks.
(b) the coverage itself dropped inside the new `[branch] if (nearW > 0.0)` block.
First step next round: one 1080p still of `Water_View_RiverLow` with `Dbg 4` (`wf, cf, gust` as colour) to separate (a) from (b). If (a),
set the foam normal to the long-wave normal (`normalize(float3(-sl2, 1))`) at full `wf`.

## PERF (`perf.json`, `perf_gpu.json`)
Exclusive `gpu_slot perf`, native 3840x2160 at 100 % (no TSR upscale), static camera, frames 16 to 31 s, water map vs the same map with P1's
flat plane. `GPU-LOCK: class=perf exclusive=yes util_before=0% util_after=0% util_during_avg=57.4% wait_s=3858 instances_before=1
instances_max=2 contaminated=false`. ioreg Device Utilization before the hold: 0 %. Disclosure: another session's `island` editor process
was open during the hold (instances 1 to 2, not a capture); the lock judged the run uncontaminated (GPU 0 % before and after).
| view | GPU frame water / flat (ms) | frame delta | SingleLayerWater pass | SLW depth prepass | Lumen reflections delta | water passes sum |
|---|---|---|---|---|---|---|
| river_low | 38.51 / 38.76 | **-0.25** | **1.00** | 0.47 | +1.22 | 2.66 |
| S4 | 47.99 / 47.07 | **+0.91** | 0.85 | 0.56 | +0.21 | 1.38 |
| river_sun | 31.67 / 33.80 | -2.13 | 1.62 | 0.47 | +0.52 | 2.19 |
Gates: frame delta <= 2.5 ms PASS (all three); SingleLayerWater pass at river_low <= 2.5 ms PASS (1.00). Negative deltas are run-to-run
noise / content differences (the flat base still renders its own plane); the delta is not a cost saving. Round 02's "SingleLayerWater
3.68 ms" came from the CSV profiler's footer row (value 2160) being included in the mean. The true round-02 SLW pass was 0.80 ms at TSR 67 %
(round 03 measures native 100 %: 1.00 ms).
