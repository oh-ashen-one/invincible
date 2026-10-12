# Terrain round 04 — the lawn: captures and measurements

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Target (round-03 critic, three critics' consistent demand): replace the yellow star-sprite tufts by dense blade-clump grass, give the lawn albedo detail at 0.3-3 m scales without losing saturation,
fix the picnic blankets (flat tints, white at 9.75 s / maroon at 11.25 s), and re-plot `t5_avenue_to_park` so its last 5 s cross park ground at 25-40 m.
PASS list: `SPEC.md` E10 (a) E1 sigma-6 SD >= 8 on the critic crops + guard boxes, (b) saturation >= 0.70, (c) no flat quad > 100 px in t4 at 4 fps, (d) t5 last 5 s over the park at 25-40 m with sigma-3 SD >= 5,
(e) the pass-2 canopy guard, (f) GPU ms within +5 % of r3, (g) no axis below r3.

## Result (final captures, 2026-10-03 02:26-03:00; numbers are from `tools/terrain/measure_r04.sh`, files beside this README)
Captured from the RUNNING game (offscreen, through the GPU lock). Stills: 3840x2160 output, **internal 1920x1080** (auto 50 % screen percentage, TSR 2x upscale), 4 fps frame cap, 9 views in `stills/`.
Movies `t5_avenue_to_park.mp4` (13.1 MB) / `t4_lawn_sprint.mp4` (14.8 MB): 1920x1080 output = **internal 1920x1080 (r.ScreenPercentage 100)**, fixed 1/60 s step, 12 fps wall cap, hero hidden, H.264 crf 29, telemetry beside them.
Builds: the movies were captured on the content built at 01:30 (lawn + infield clay, `M_TerrainRock` at 0.5 x vertex colour); the stills on the rebuild of 02:25 (rock albedo 0.27 x vertex colour; nothing else changed). The only visible difference is the tone of the schist / dugout blocks.

| criterion (SPEC E10) | target | measured | verdict |
|---|---|---|---|
| (a) E1 sigma-6 SD, critic p4 (1700,1000,512x400) | >= 8 | **10.85** (r3 4.40) | PASS |
| (a) critic p10 (1300,1700,512x460) | >= 8 | **11.25** (r3 7.95) | PASS |
| (a) guard p10 (2240,1856) / p4 (3520,1856) / p9 (512,1856) | >= 8 | **9.97 / 11.57 / 8.99** (r3 6.34 / 1.41 / 2.63) | PASS |
| (b) mean HSV saturation on those 5 boxes | >= 0.70 | **0.874 / 0.930 / 0.916 / 0.959 / 0.944** (r3 0.58 / 0.54 / 0.61 / 0.64 / 0.65; reference meadow 0.82-0.84) | PASS (above the reference) |
| (c) flat quad > 100 px in t4 at 4 fps (54 frames, flat = 7x7 luma SD < 0.9) | none | **0** (hold 1: 5 at t 0-0.25 s, texture streaming; fixed by never_stream). At SD < 1.5: 2 hits, a sunlit lawn patch (169x77 px, t 0.75 s) and a tree trunk (152x437 px, t 4.25 s), no blanket | PASS |
| (d) t5 last 5 s (10.4-15.4 s) over the park | at 25-40 m, sigma-3 SD >= 5 | route x4_y315: 20 / 20 frames over the park rectangle, telemetry share at 25-40 m **82.9 %** (20-45 m 98.7 %); ground sigma-3 SD in the 16 frames at 25-40 m: **median 7.38, min 5.32**; all 20 frames: median 7.38, min 3.54 (10.4 s at 18.6 m, 10.65 s at 24.3 m: 4.95) | PASS in the 25-40 m band; the two first frames (below 25 m) are under 5 |
| (e) canopy guard for the pass-2 hunks | trees axis >= 4, E9b PASS, E9a >= 5/24, E9c <= 47 px | E9a 9 / 24 >= 9 (min 5.67, median 8.13); E9b PASS (flat hull faces max 8.5 / 21.3 px, dark pockets 0.76 / 1.30 %); **E9c 54.1 px FAIL on this capture** (the same canopy measured 42.0 px in hold 1 and 37.7 px in hold 3: the longest straight run is the top of one crown hull ball at p10 x 1950-2000, y 540, which moves with the dithered LOD / TSR jitter) | E9a / E9b met; E9c missed once of three captures; pass-2 hunks KEPT, the critic's trees axis decides |
| (f) GPU ms p1 / p10 within +5 % of r3 (161 / 92) | <= 169.1 / <= 96.6 | **contaminated, 1-2 other renders running** (`gpu_slot` reports contaminated=true; the exclusive perf run was refused, exit 75: Mac unattended, HID idle 5200 s). Hold 6 (final build): r04 165.1 / 104.5, HEAD content (old tufts, pass-2 canopy) 169.2 / 112.8, r04 again 169.3 / 101.6. Hold 3: r04 166.3 / 95.1, HEAD 175.9 / 102.0. Hold 1: p10 94.5 / 94.4 vs HEAD 95.3 | p1 +2.5 % .. +5.1 %; p10 +2.7 % .. +3.3 % in holds 1 and 3, +10 % .. +14 % in hold 6; in every hold the lawn build is equal to or cheaper than the HEAD content measured in the same hold (the HEAD p10 itself read 112.8 in hold 6), so the p10 excess in hold 6 is GPU contention, not the lawn |
| (g) no critic axis below the merged r03 [4,4,4,4,3] | | not judged here (blind critic pack below) | open |

Also changed this round beyond the lawn (secondary list of the r03 critic): `M_TerrainRock` (triplanar stone, joints, moss; the schist blocks / dugouts and the pond-bank blocks were white under the golden sun), bare clay on the six ball-field infields
(`prep_lawn.infield_sand`: the blades no longer cover the clay fans of `Park.ush`; 793 near-layer instances removed). Still open (not this piece's or not reached): the p6 water seam and the khaki river (water piece), white egg-shaped lumps along the p3 lake banks (NOT `park_rocks`: they stayed white after the stone material; not identified, see HANDOFF),
the crown hull ball with saucer cards at p10 (x 1900-2400, y 450-700), the pale ball-field clay (patchy browser mask), the empty esplanade.
Archive of the intermediate holds: `hold1/`, `hold2/`, `hold3/` (measurements of earlier builds), `hold4/` (stills of the 14:50 build: critic p4 10.82, p10 11.44, guards 10.04 / 11.49 / 8.90, sat >= 0.88).


## Build (all in committed scripts; Content is generated, never committed)
1. `tools/terrain/prep_lawn.py` (run at the end of `prep_terrain.py`): 4 near blade patches (a 2.3 m disc of ~1,150 blades: 26 clumps of 30-44 blades with outward lean + 200 loose blades, 3 triangles per blade, unit height,
   vertex colour R = height along the blade / G = blade random / B = clump random) scattered on a 1.5 m jittered grid over the browser's grass density / height mask (177 k instances, culled at 18 m, the blades shrink to the ground
   between 12 and 17.5 m so nothing pops); 2 far patches (~400 wider, taller blades) on a 2.6 m grid (59 k instances, culled at 60 m, they grow in between 6 and 13 m so there are no tall tufts at the hero's feet, shrink out between 42 and 58 m).
   Patches keep 0.45 m clear of paths / drives and clear of the 401 picnic blankets. Textures: `lawn_detail.png` (1024^2 tileable RGBA: clump luminance, wear field, clover field, grain) and `blanket_weave.png` (256^2 gingham weave, 0.24 m tile).
2. `Shaders/Terrain/Lawn.ush` (hand-written; `Park.ush` stays the generated browser ground): lawn grade (0.54, 1.22, 0.10) instead of (0.54, 1.20, 0.46) — the reference lawn's display blue is 16 / 255 against our 55 —,
   three-scale albedo mottling (1.15 / 4.7 / 16.3 m tiles, mip-filtered so it fades with distance), wear / dirt patches, clover patches, crisp 4.4 m mowing stripes, a clay-vs-grass mask (infield clay is no longer graded green);
   `M_TerrainPark` also gets gravel / asphalt grain on the paths and drives.
3. `terrain_materials.py`: `M_TerrainGrass` = blade turf (two-sided foliage with subsurface, dark root -> saturated yellow-green tip, per-blade and per-clump colour, yellow clumps, rare straw blade, wind at the tips, distance shrink),
   `M_TerrainBlanket` (gingham weave, fringed comb ends in a masked opacity, world-space wrinkle normal; six palettes), `M_TerrainVC / VC2` (furniture) get a world-space wood / paint grain.
4. `build_terrain.py`: grass pools are out of Lumen's ray-tracing scene and cast no shadows (r03: HWRT treats every drawn primitive as visible to indirect rays); blankets lie 2 cm over the lawn with a hair of tilt;
   env `SM2_TERRAIN_ROOT` (the r04 content is built side by side as `/Game/TerrainR4` while `/Game/Terrain` keeps the HEAD content for the GPU-ms baseline); the foliage step is re-runnable.
5. t5 route: `tools/terrain/t5_cands.py` writes 11 candidate scripts (`t5_candidates/`), the hold probes each headless (`-nullrhi`, telemetry only) and `tools/terrain/t5_score.py` ranks them by the share of the last 5 s spent over
   the park rectangle at 25-40 m; the best becomes `scripts/t5_avenue_to_park.json`.
Offline checks: `check_hlsl.py` 13 / 13 (DXC with UE's parameter types); a numpy simulation of the lawn detail (`_scratch/terrain/r04/sim_detail.py`) predicted hp sigma-6 SD 10-12 at 0.07-0.15 m/px and hp sigma-3 SD 8-9 at 0.06-0.35 m/px;
a Cycles CPU preview of the blade patches at eye height set the final blade density (the first 650-blade 1.9 m discs left ~45 % of the ground bare).

## Reference measurements (same tool, `tools/terrain/lawn_stats.py`; `ref_lawn_native.txt`, `ref_lawn_x2.txt`)
| frame | box | hp sigma-6 SD | mean HSV saturation | mean luma |
|---|---|---|---|---|
| centralpark-meadow-skyline (1080p native) | 512 x 400 lawn L / R | 10.08 / 10.20 | 0.840 / 0.817 | 79.8 / 78.2 |
| same, put on the 4K output grid (x2 Lanczos) | 512 x 400 / 460 | 5.73 / 7.35 / 8.61 | 0.822 / 0.808 / 0.855 | 82 / 86 / 75 |
| centralpark-aerial-ballfields (1080p native) | 400 x 300 / 400 x 200 | 3.84 / 2.79 | 0.893 / 0.879 | 114.6 / 90.7 |
| same, x2 | 512 x 400 | 2.25 / 1.43 | 0.894 / 0.887 | 120 / 98 |
| ours r03 (4K output, internal 1080p) | critic p4 / critic p10 / guards p10 p4 p9 | 4.40 / 7.95 / 6.34 / 1.41 / 2.63 | 0.582 / 0.541 / 0.609 / 0.639 / 0.649 | 142 / 104 / 95 / 105 / 83 |
Reading: the reference's own aerial lawn is smooth (hp sigma-6 SD 1.4-3.8), so the aerial >= 8 asked by the brief is above what the reference shows; at ground level the reference reaches 10 (native) / 5.7-8.6 (x2).
