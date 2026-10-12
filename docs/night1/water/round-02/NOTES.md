# River water, round 02 (Opus 5.5): capture notes

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Build: `night1/water` = integration 914de97 + round-02 water (`unreal/WebHomage/Scripts/build_water.py`, `tools/water/water_inputs.py`).
City: `build_manhattan.py` (unchanged) through the scratch wrapper (HANDOFF.md), export cloned from the integrator's morning showcase stage.
Every Unreal process (commandlets included) ran inside `gpu_slot.sh capture --label water` holds; perf under `gpu_slot.sh perf` (exclusive).
Numbers: `python3 tools/water/water_spec.py all docs/night1/water/round-02 --json docs/night1/water/round-02/spec.json`
(instrument calibrated on the round-01 critic numbers: see the docstring; reproduces build O's 90.6 / 4.4 / 117 and the 0.22 autocorrelation).

## What changed vs round 01
1. **Ring artifact / periodicity:** the 12 analytic capillary sinusoids summed into a lattice (top-down emulation shows a crystal pattern),
   and the warped wind-streak foam closed into loops. Replaced by 4 layers of a baked random-phase wind-sea slope spectrum
   (`T_WaterSlope`, k^-4, 3..24 cycles / tile, 2 realizations, tiles 21 / 6.7 / 2.2 / 0.73 m, scrolled at their phase speed, mip bias +1,
   unresolved variance -> roughness). Streaks no longer make foam and are straight (warp 26 -> 5 m), at half strength.
   Dolly autocorrelation at 80 px: round 01 **0.224** -> round 02 **see table** (target <= 0.10).
2. **Contact foam:** round 01's depth-based foam (SceneDepthWithoutWater) did not show. Added `T_WaterContact`: distance to the nearest
   place where the city export's geometry crosses the water plane (seawalls, bulkheads, pier piles, bridge piers; island shore box,
   0.89 m/px, 120 844 crossing segments from 54 GLBs, positions offset by each mesh's manifest tile centre). Foam band 0.1..~2.5 m,
   lapping, noise-broken; FoamK 1.8.
3. **Darker, choppier water:** ScatK 0.2 (body scattering x0.2), ChopK 2.6, BendK 0.3 (facets whose reflection would point below the
   horizon are bent up: Lumen would otherwise trace into the void). Picked from tuning variants (table below).
4. **New views:** `river_sun` (across the Hudson into the golden sun: glitter path) and `harbour_high` (coverage: harbour + both rivers);
   `harbour_high` shows the water wrapping the island (the grid follows the camera to 81 km; contact map covers the island's whole shore).
5. Build hygiene: /Game/Water is rebuilt from an empty folder (an in-place material rebuild failed to compile for Metal SM6 twice ->
   default material; the hold scripts now abort if the game log reports it).

## Look rig changed since round 01
The integrated golden rig (look piece, merged after round 01) is not the same: S4 far shore Y **150** (round 01: 171), cloudier sky.
Round-01 vs round-02 brightness comparisons are therefore not like for like; the previous-vs-this pair in the critic pack shows it.

## Files (all real game, offscreen, every run inside a `gpu_slot.sh capture --label water` hold)
| file | map | output | internal |
|---|---|---|---|
| `S4_golden_{1080,4k}.jpg` | /Game/Maps/Manhattan_View_S4 | 1920x1080 / 3840x2160 | native (r.ScreenPercentage 100), t = 16 s |
| `river_low_{1080,4k}.jpg` | /Game/Water/Maps/Water_View_RiverLow | same | native |
| `river_sun_{1080,4k}.jpg` | /Game/Water/Maps/Water_View_RiverSun | same | native |
| `harbour_high_{1080,4k}.jpg` | /Game/Water/Maps/Water_View_HarbourHigh | same | native |
| `river_low_dolly.mp4`, `river_sun_dolly.mp4` | `*_Dolly` maps | 1920x1080 60 fps, 10 s (t = 6..16 s) | TSR default for 1080p output; -benchmark -fps=60 -dumpmovie; sun dolly crf 23 (size) |
| `crop_river_low_4k_seawall_foam.jpg` | crop of river_low_4k (x 1500-2700, y 1250-2160) | | |
| `variant_G/` | same set with variant G (ChopK 1.6, ScatK 0.3, BendK 0.5, FoamK 1.0) | | |
| `iter1/` | first iteration (1080p) with round-02 defaults before tuning + variants A/B + debug (R = foam, G = contact, B = gust) | | |

## Tuning variants (1080p river_low near crop; S4 C14) — iteration 3, 2026-10-02 00:47
| variant | ChopK | ScatK | BendK | mean Y | p99.5 | glint >=140 | hp sd (1080) | C14 |
|---|---|---|---|---|---|---|---|---|
| default r02 start | 1.0 | 0.55 | 1.0 | 115.3 (iter 1) | 158 | 6.9 % | 5.0 | 6.8 |
| G | 1.6 | 0.3 | 0.5 | 95.5 | 139 | 0.48 % | 5.6 | - |
| C | 2.0 | 0.3 | 0.5 | 89.2 | 128 | 0.23 % | 5.6 | 16.9 |
| **E (picked)** | 2.6 | 0.2 | 0.3 | 75.1 | 116 | 0.08 % | 5.7 | 21.0 |
| J | 3.2 | 0.1 | 0.2 | 61.2 | 102 | 0.0 % | 5.7 | 24.3 |
An automatic score (closest to all four near-crop targets) picked G; E was chosen by hand: it passes mean Y and keeps C14 mid-range, its
river_sun glitter view is far closer to the into-the-sun reference (G's is washed out, mean 161), and G's extra highlights still fail.
1080 -> 4K: high-pass sd x1.4-1.5 on the same view (G: 5.66 -> 7.95; E: 5.68 -> 8.46).

## Final numbers (E, `spec.json`)
river_low 4K near crop: mean Y 79.3, rgb (86, 79, 61), p1 46, p99.5 122, high-pass sd 8.46, glint 0.11 % (>= 130: 0.26 %).
river_sun 4K near crop: mean Y 136.8, p99.5 248.6, high-pass sd 27.3, glint 44.9 %.
harbour_high 4K: mean Y 80.5. C14 at S4: 22.0 (4K) / 21.0 (1080); far shore 151.0, river 129.0.
Dollies: autocorrelation at 80 px 0.006 (river_low; round 01 0.224) / 0.041 (river_sun); water dT per 10-fps sample 3.06 / 7.30 (round 01 1.47).

## GPU cost (`perf.json`, sidecar `perf_gpu.json`)
3840x2160 output, TSR 67 % (internal 2573x1447), static camera, t = 16..36 s, `tools/perf_ue/run_perf.py -csvGpuStats`, all six maps in ONE
exclusive lock: `GPU-LOCK: class=perf exclusive=yes util_before=0% util_after=0% util_during_avg=59.9% wait_s=7573.75 instances_before=0 instances_max=1 contaminated=false`.

| view | GPU avg ms water / flat base | frame delta | SingleLayerWater | SLW depth prepass | LumenReflections delta | sum of water passes |
|---|---|---|---|---|---|---|
| Water_View_RiverLow | 25.89 / 24.67 | +1.23 | 3.68 | 0.24 | +0.66 | 4.55 |
| Water_Perf_S4 | 30.85 / 30.43 | +0.42 | 0.58 | 0.28 | +0.12 | 0.97 |
| Water_View_RiverSun | 21.11 / 21.42 | -0.31 | 3.64 | 0.26 | +0.29 | 4.16 |

Reading: end to end the round-02 water costs **+1.23 ms** (river_low), **+0.42 ms** (S4) and **-0.31 ms** (river_sun, noise) of GPU frame time over
the flat P1 plane: inside the 2.5 ms budget. The per-pass stats tell a different story at the near, water-filled views: the SingleLayerWater
pass reads **3.6-3.7 ms** (round 01: 0.75 at river_low), so the attributable-pass sum is 4.2-4.6 ms there (0.97 at S4). The M3 overlaps passes
(the per-pass sum exceeds the frame delta), so the frame delta is the honest total, but the SLW pixel shader got ~5x heavier and is the
first thing to cut next round (8 biased slope-texture samples + 3 wave/streak noise lookups + 8192x2625 contact-map sample per pixel).
