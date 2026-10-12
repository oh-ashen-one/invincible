# P1 City — handoff after round 11 (for the next builder)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Branch `night1/city`, worktree `/Users/midir/sm2-n1/city`. Browser dev port **5202** (only for a full re-export; start Vite for the export, stop it after), UE MCP port 8771 (not needed: everything runs as `-nullrhi` commandlets and `-game` captures through the GPU lock).
Owned: `tools/export/`, `/Game/City`, `/Game/Tests/City`, `docs/night1/city/`, plus (flagged to the integrator) `unreal/WebHomage/Shaders/City/` and `unreal/WebHomage/Scripts/{build_city.py,city_shots.json}`.
Content/ is NOT committed (public fork, no LFS): everything is rebuilt by the committed scripts from the browser city.

## State at the end of round 11 (Sonnet 5.5 xhigh via Devin, 2026-10-03)
Critic r10: FAILS TARGET, axes [5, 5, 5, 5, 5]; its single gap: the S4 far-shore towers (flat pale extrusions, no windows) plus the S8 upper glass. Round-11 target (Opus director): far-LOD facade with window grid, crown / setback variation, mid-grey albedo for the S4 far-shore towers.
Measured on the settled r11 frames (`round-11/`, 1080p auto screen percentage internal 1399x787; native 4K internal 3840x2160; `tools/export/r11_numbers.py`, `s4_far_check.py`, `city_spec_check.py`):
| line | r10 | r11 1080p | r11 4K (reduced) | target |
|---|---|---|---|---|
| T1 S4 silhouette-top std, x 0-1300 (px, min of 3 definitions) | 19.0 | 23.6 | 23.6 | >= 12 |
| T2 S4 box (0,150,1300,300) above Y 204 (%) | 29.5 | 6.6 | 6.9 | <= 10 |
| T4 flat bright 8x8 blocks in (540,110,900,260), share of ALL blocks (%) | 24.3 | 1.4 | 1.5 | <= 10 |
| T4 same, share of the BRIGHT blocks (%) | 46.1 | 45.8 | 48.0 | <= 10 (other reading) |
| C11 far_shore lap / sky lap | 20.8 | 30.3 | 27.8 | >= 6 |
| C11 far_shore flat 8x8 (%) | 4.1 | 0.0 | 0.0 | <= 40 |
| C12 far_shore (B-R) - sky (B-R) | -1.7 | -0.1 | +0.8 | +-10 |
| C13 far_shore Y - sky Y (committed box) | -38.5 | -68.2 | -66.3 | -35..-25 |
| C13 with the box (0,150,1300,215) the critic used in r10 | -29.6 | -57.1 | -55.6 | -35..-25 |
| C14 far_shore Y - river Y | +16.9 | +23.3 | +26.4 | 5..35 |
| C15 rms far_shore / near_city | 0.24 | 0.31 | 0.31 | 0.25..0.45 |
| T5 S8 glass box (1270,0,1640,300) above Y 204 (%) | 70.4 | 0.69 | 0.37 | <= 1.5 |
| C1 daylight facade boxes passing (<= 1.5 % above 204; 16 boxes, 1080p) | 15 | 15 | - | 16 |
| C2 daylight facade boxes with mean Y 52-119 (16 boxes, 1080p) | 16 | 16 | - | 16 |
| S3 / S7 share of pixels below Y 25 (%) | 13.2 / 1.4 | 17.0 / 3.5 | - | <= 25 / <= 30 |
| C4 / C6 vehicles at YOLO conf 0.30: S1 / S2 | 17 / 15 | 17 / 16 | - | 5-19 / 14-22 |
Billboard: the native-4K S3 frame shows the board with MORE SHADE / ON EVERY / STREET in full (`round-11/builder_checks/S3_board_4k.jpg`); OCR of the 4K frames vs the denylist: see `round-11/ip_ocr_check.txt`.
Not met / worse than r10: C13 (-68 vs -35..-25; r10 -38.5, and -29.6 with the box the critic used), the "flat blocks" sentence read as a share of the BRIGHT blocks (46 % vs 46 %), black crush S3 17.0 % (r10 13.2 %) and S7 3.5 % (r10 1.4 %), dusk glass `s7_left_glass` mean Y 48 (C2 floor 52, informational). Unchanged: S5 mid tower 6.0 % above 204, S6 curb 14.65 %, `s5_grey_tower` C1 3.66 %.
Critic pack for r11: `/Users/midir/sm2-n1/_scratch/critic-P1-r11/pack` (key outside the pack: `pack.key.json`; `pairs.json`: 9 reference pairs at 1920x1080, 3 native-4K pixel crops, 6 r10-vs-r11 pairs). The critic was NOT run by the builder.


## What round 11 changed, and why (details: `round-11/README.md`, `EXPORT.md` "Far skyline")
Critic r10 (FAILS TARGET, lowest 5) named ONE gap: the S4 far-shore towers were flat pale extrusions (29.5 % of (0,150,1300,300) above Y 204, 25 % of the 8x8 blocks of (540,110,900,260) bright and flat), plus the S8 upper glass (70.4 % above Y 204 for three rounds).
Root causes found by masks, projection previews and sweeps (not guessed):
1. **The pale band was mostly NOT the towers' albedo.** The r10 S4 frame's pixels above 204 were (a) sunlit faces that clip under the test lighting (sun 6, +2 EV), (b) sky and fogged bare ground between low roofs, (c) the sky itself in the top three block rows of the critic's box (121 of the 197 flat bright blocks, Y 229, std < 1). Material work alone could not fix (c); the skyline had to rise into the box.
2. **The bare fogged ground** between the browser's `farCityMass` blocks and the 6-17 km hinterland boxes (rows 165-230 of the S4 view) was Y ~ the sky. It is now covered by a carpet of mid-rise blocks on the Palisades plateau (`far_skyline.py` `fabric()`, 2 270 blocks, M_CityFarMass).
3. **S8 glass**: the curtain-wall tint (F0 0.2-0.62 x F0Scale 0.8) reflects a sky that the 1.7 SkyLight makes brighter than the visible sky (Y 229): F0Scale 0.8 -> 0.5 -> 0.35 -> 0.25 gave 70.4 -> 43.6 -> 6.8 -> 3.1 % above 204; the last 3 % was ONE side face of the tower seen at a grazing angle (Fresnel x clipped horizon). Fix: below N.V 0.5 the coated glass becomes a low-F0 dielectric (Specular 0.04 -> F90 0.16): 0.72 %.
What was built:
- `tools/export/far_skyline.py`: plateau towers are now far-LOD facade towers (five archetypes: stepped deco, slab with setback + chamfer overlay, twin shafts, glass slab, brick block; crowns: stepped pyramid / penthouse + mechanical box / lift core / spire), vertex-alpha window codes 0.40 punched / 0.62 ribbon / 0.90 glass-with-fins, authored tones = albedo 0.22-0.36 (vertex colour = albedo / FarGain 4);
  the plateau fabric carpet; hinterland boxes get 1-3 setback tiers, 22 % are yawed 8-35 degrees, the central columns 500-940 of the S4 view are a downtown cluster (roofs on rows 98-150, a backdrop row on rows 98-120 so the top of the critic's box is towers, not sky).
- `M_CityFarMass` / `M_CityHinter` (build_city.py): window grid kept, plus 18 x 26 m tonal panels, pier lines every 12 m, a darker mechanical floor every 52 m (fade with the pixel footprint), 64 x 110 m coarse panels on the hinterland; MPC `FarLitK` (sun-facing faces of OUR towers x 0.3; the test lighting clips any lit albedo above ~0.1, so the authored 0.25-0.35 grey is scaled, not authored lower),
  `FarFill` 0.12 (emissive sky / ground bounce on the shaded faces: from the S4 perch the sun is behind the far shore and nearly every visible face is shaded). M_CityHinter lit faces x FarLitK x 0.7.
- `M_CityFacade`: grazing-angle curtain glass (above); MPC defaults `F0Scale` 0.8 -> 0.25.
- S4 map atmosphere (`city_shots.json`): height fog 0.004 starting at 4 500 m (`fogstart`, new per-shot key), colour (0.60, 0.62, 0.66) (r10: 0.0012 from 400 m, 0.76/0.78/0.80). The near / mid field is clear, the 5-12 km skyline gets real atmospheric perspective.
- `ip_original_art.py` P27: caption "MORE SHADE ON EVERY STREET" on three lines in the left 77 % of the board (the first r11 frame lost the last letter behind the water tank and the top of 'MORE' above the frame).
- Tools: `r11_plan.sh` (plan runner: build / mpc / variants / cap / score inside ONE gpu_slot hold, settle pair, GPU-util record, watchdog), `settle_check.py`, `s4_far_check.py` (T4 + the critic's C13 box), `s4_mask.py`, `s4_proj.py` (CPU preview of the S4 skyline coverage), `box_stats.py`, `make_pairs_r11.py`, `post_round_r11.sh`, `r11_final_plan.py`; `view_variants.py` knows `fs_<n>` (fog start, metres).


## Ranked to-do for round 12
1. **C13 vs T2 (decision for the director, not a build item):** no configuration tried (FarLitK, FarFill, fog density / colour / start distance, see `round-11/README.md`) gave far-shore mean 25-35 below the sky AND <= 10 % of the box above Y 204 AND C15 >= 0.25; the r10 pass of C13 came from a white haze band (49 % of its rows 150-215 above Y 204). Either relax C13 for S4 to the measured ref ratio at the T2 level, or re-measure it on a box that excludes the river / shore (the critic's own box changed between rounds).
2. T4 read as a share of the bright blocks: 11 flat of 24 bright blocks are one pale lit face (x 740-790, y 142-175 of the 1080p frame) of a plateau glass tower (`M_CityFarMass` glass branch `gl` colour 0.34-0.46 at height, lit). Texture or darken that branch (window codes 0.90).
3. Secondary r10 items still open: S6 curb crop (1150,760,1920,1080) 14.65 % above 204 and red steps (sat 0.30, V 163 vs ref >= 0.44), S5 mid tower 6.0 %, `s5_grey_tower` 3.66 %, S3 white roof primitives (1590-1760, 960-1060), cars (clearcoat is in, plates are generic), S2 traffic (16 vehicles at conf .30 is inside 14-22), people / traffic lights (P6).
4. Image quality: black crush rose with F0Scale 0.25 (S3 17.0 %, S7 3.5 %); `DayEmisK` or a floor on the glass interior (`InteriorGain`) would bring the window interiors back without touching the sky reflection. `s7_left_glass` at dusk fell under the C2 floor.
5. r09 to-dos that were never done: measure the shade-fill march under `gpu_slot.sh perf` (needs an attended Mac; add the `k <= 0.0001` early-out first), extend the height field beyond the detailed block (the fill is 0 above 8 m outside it), far tree crowns as clumps.
6. `capture_round.sh` still shoots at t = 28 s (cold-start unsafe, gotcha 36): switch it to the 34 / 38 s pair or use `r11_plan.sh`; `run_game.sh` is not P1's file.
7. Integration: the fabric carpet / backdrop row / fog start only exist in the S4 view map (fog) and the shared geometry level; if C (Manhattan) reuses `City_Midtown_Geo` the far skyline comes with it (about 2.3 k blocks, 590 hinterland boxes, no shadow casting, no distance fields), the S4 fog does not.


## Commands (all from the worktree root; the GPU lock wraps every Unreal launch)
```
# merge + C++:       git merge origin/Opus-5.5-Loop-Night-1 ; unreal/WebHomage/Scripts/build_editor.sh      (50 s)
# export (3 min):    (nohup npx vite --port 5202 --host 127.0.0.1 --strictPort > $SCR/vite.log 2>&1 &) ; node tools/export/export_city.mjs ; stop the vite node + npm exec processes YOU started (lsof -iTCP:5202)
# CPU preparation:   tools/export/build_city.sh without its first and last lines: patch_export, prep_textures (IP sanitiser + original art), gen_street_signs, street_kit, street_props, export_vehicles,
#                    street_cars, street_trees, street_traffic, far_skyline, bake_sunmask, gen_shaders.mjs   (the scratch export in /Users/midir/sm2-n1/_scratch/city can be deleted between rounds)
# full content:      tools/export/ue/run_commandlet.sh unreal/WebHomage/Scripts/build_city.py steps=clean,tex,mat,mesh,proto,kit,fsky,map     (~35 min on a clean Content/; steps=tex,mat,fsky,map is 2-6 min)
# iterate in ONE hold with a plan file (build / mpc / variants / cap / score lines, tools/export/r11_plan.sh header):
/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label city -- zsh tools/export/r11_plan.sh <out_dir> <plan.txt>
# final plans:       python3 tools/export/r11_final_plan.py <dir>   (final_1080.txt, final_4k.txt)
# checks:            tools/export/settle_check.py <raw> | s4_far_check.py <frame> | s4_mask.py <frame> <png> | box_stats.py <frame> x0 y0 x1 y1 | city_spec_check.py <round_dir> --res 1080 --yolo --ip | s4_proj.py (CPU preview of the S4 skyline)
```
Stop an engine of yours with `/Users/midir/sm2-n1/_scratch/gpu/bin/stop_ue.sh "[/]Users/midir/sm2-n1/city/unreal/WebHomage"` (bracket form; kill your plan driver by PID first: gotcha 38); never `kill -9` a rendering engine.

### New gotchas (r11)
36. **Cold start after a content rebuild: the first rendered frame can arrive at game time ~27 s** (asset registry scan + shader / DDC fill; the clean build leaves Intermediate/DDC cold). `run_game.sh -shots 24,28 -perf 18:28` then fires both screenshots on the first frames: mean |dY| between the pair 4.5, 14 % of the pixels differ by > 8 levels, `WH_PERF frames=1 avg_ms=5786`. r11 runs take the pair at t = 34 / 38 s with the perf window 26:38 (`r11_plan.sh`) and `tools/export/settle_check.py <raw>` must print mean |dY| < 1 and < 1 % of pixels differing by > 8 levels before a frame is used (settled baseline: 0.33 / 0.05 %). The old `capture_round.sh` still shoots at 28 s.
37. **A clean content build takes ~35 min** (the clean step 4.6 min, 511 tile meshes ~25 min, protos 5 min, kit 2 min, fsky 1-5 min, map 1 min). Never use `clean` for a material or far-skyline change: `steps=mat,fsky,map` is 2-6 min. The scratch export (`_scratch/city/export`, `tex`) can disappear between rounds: the CPU preparation chain is in `tools/export/build_city.sh` (run its python/node lines by hand, one `export_city.mjs` + Vite on 5202 for ~3 min).
38. **`stop_ue.sh <pattern>` also matches the calling shell** when the pattern is a plain path: use the bracket form `"[/]Users/midir/sm2-n1/city/unreal/WebHomage"`. It finds drivers by command-line match only: a plan runner started as `zsh tools/export/r11_plan.sh /Users/.../_scratch/...` does NOT match, so kill that driver (and its `( sleep N; stop_ue ...)` watchdog subshell) by PID first, then call stop_ue.sh for the engine.
39. Each farsky tile mesh (non-Nanite) spent 7-12 s on its mesh distance field at import; the plateau fabric (30 tiles) sets `distance_field_resolution_scale 0` (they are 2.5-8 km away).
40. **T4 counts sky.** In the r10 S4 frame 121 of the 197 flat bright 8x8 blocks of the critic's box (540,110,900,260) are the top three block rows (rows 110-133), i.e. sky above a low skyline (Y 229, std < 1). No material fixes that: the central skyline has to rise into the box (far_skyline.py `central` cluster, `tools/export/s4_proj.py` previews the coverage on the CPU).
41. **The health monitor can SIGTERM a run and pause the lock without any crash** (r11, 12:27: WindowServer CPU 97 % while the owner was working, `STOP(TERM) newest -game ... WS-HOT`, then `PAUSED`; the engine log ends with "Engine exit requested (reason: Mac GracefulTerminationHandler)", rc=1 after 25 s). It is not an engine crash: stop your plan driver by PID (it would try the next view), wait for the `AUTO-LIFT` (10 calm minutes, no loop engine rendering), re-run only the missing views (`wait_and_run.sh` pattern: poll for PAUSED, one hold).

## Earlier rounds (kept for reference; the r10 section below was written before this round)
## Read this first: round 10 (Sonnet 5.5, 2026-10-01) — WORK IN PROGRESS NOTE, final numbers are in `round-10/README.md`
Critic r09 (FAILS TARGET, lowest 4) named ONE gap: **the S4 far-shore band** (x 0-1300, y 150-300): white box plateau (silhouette-top row std 6.1 px, 38.8 % of the box above Y 204), grey wall embankment, no trees.
Tests: T1 silhouette-top std >= 12 px, T2 <= 10 % of (0,150,1300,300) above Y 204, C11-C15 still pass. `tools/export/s4_far_check.py <frame>` measures T1 / T2 / C11-C15 (it reproduces the critic's numbers on the r08 / r09 frames: 6.0 / 6.1, 38.7 / 38.8 %); `city_spec_check.py` (regions v3) includes them plus the other critic boxes (S8 glass, S5 mid tower, S6 curb).
- **What was built** (details: `EXPORT.md` "Far skyline ..."): `tools/export/far_skyline.py` (pure Python, seeded; writes `<export>/mesh/farsky`, `proto/farsky_clump.glb`, `farsky.json`): plateau towers, a hinterland skyline designed by screen row, a displaced wooded bluff replacing the flat `palisadesCliff` wall, seawall / promenade / piers, tree clumps (one HISM) incl. trees on the far-land lawns. `build_city.py` step `fsky` imports it, `build_geo_level` spawns it (folder `City/Far`), `arg farsky=0` builds without.
- **Measured (hold 1, 1080p, e2.0 = the test-map default, old FarGain 7.6)**: T1 5.9 -> **19.6-20.4** (all three definitions). T2 38.6 % -> 29.1 %, C13 -33.6 -> -42.4 (the strip got darker): both still to fix. **Exposure response of the S4 map** (old content, `view_variants.py`): bias 2.0 / 1.0 / 0.5 -> sky Y 229 / 204 / 186, far shore 195 / 157 / 135: C13 (absolute -25..-35 below the sky) is a relative spec measured on refs whose sky is Y 120-130; at a lower exposure the far / sky RATIO stays ~0.73-0.77, so C13 fails; and at sky < 215 the 'first row with Y < 215' silhouette definition degenerates. => keep exposure 2.0 and fix the far band by albedo / haze instead.
- **Root cause of the white plateau**: `M_CityFarMass` multiplies the exporter's block colour (0.10-0.33 linear) by MPC `FarGain` 7.6 and caps at 0.85, so nearly every far block was albedo 0.85 white; under sun 6 / +2 EV any sunlit albedo above ~0.15 clips to white anyway. New: MPC **`FarSunK`** (default 0.15) = luma cap of sun-facing far blocks / hinterland boxes (`M_CityFarMass`, `M_CityHinter`), FarGain to be lowered (4.0, sweep) so brick / stone tints survive.
- Secondary r09 items touched (all unverified until the final frames are in the README): sidewalk albedo knee (`M_CitySidewalk`, SunK x 2.4; the first version used the normal-map vector of `CitySidewalk` and did nothing -> uses the vertex normal now), prop weathering + luma cap 0.15 (`M_CityProp`: S3 'white untextured props'), clear-coated car paint + generic licence plates (`M_CityCar`, `export_vehicles.py` writes plate UVs, `veh` step), TKTS steps (`MI_tsTKTS` FillK 0.2, rougher), F0Scale / DayEmisK sweep for S8 glass and S5.
- **GPU queue reality**: the shared lock was 20-60 min per hold on 2026-10-01 (traversal / life / characters / perf holds of 20-25 min each). One of my queued holds lost its ticket (another agent's `reap_stale` removed it: `ps` call timed out under load, `gpu_slot.log` `stale-recovered dead_pid=<mine>`): watch `gpu_slot.log` and re-queue (kill the old waiter with SIGINT, not SIGTERM).

## State at the end of round 09 (previous round, still valid below) (Sonnet 5.5, 2026-09-30 04:10-08:30)
Critic r08 (facades 5, street 5, skyline 4, composition 5, image quality 4, FAILS) named ONE gap: **shadowed facades are crushed** (S1 crops (0,0,480,300) / (1360,0,1740,400) mean Y 22.5 / 19.7 against the C2 floor of 52; Y < 25 on 72.2 % of S3 and 62.5 % of S7).
**Round 09 fixed it** (`round-09/README.md`, `round-09/shade_check.md`, `round-09/city_spec_check.md` + `.json`):
| line | r08 | r09 (1080p, ShadeFill 0.12 / GlassSky 0.11) | target |
|---|---|---|---|
| Test 1 S1 crop (0,0,480,300) / (1360,0,1740,400) mean Y | 22.5 / 19.7 | **66.6 / 53.8** | >= 52 |
| Test 2 S3 / S7 share Y < 25 | 72.2 % / 62.5 % | **19.7 % / 3.6 %** | <= 25 % / <= 30 % |
| C2 facade boxes in range (spec_regions v2, 16 daylight) | 10 / 16 | **15 / 16** (`s2_dark_tower` 47.1) | 16 / 16 |
| C1 facade boxes | 15 / 16 | 15 / 16 (`s5_grey_tower` 3.70 %, unchanged) | 16 / 16 |
| C11-C15 far field (S4) | pass | pass, same numbers (but S4 is the first-variant frame, see below) | pass |
| C4 / C6 YOLO conf .30 S1 / S2 vehicles | 16 / 17 | 17 / 19 | >= 5 / >= 14 |
**Only 1080p frames exist for r09 (no 4K, no mp4 — `SHOTLIST.md` has no movements — no clean perf).** The GPU driver wedged before the 4K set could be captured, see gotcha 30. `S4_perch_skyline_1920x1080.jpg` is from the FIRST variant of the fill (uniform, no shadow information), not the committed shader. The margin of the S1 right crop is thin (+1.8): one frame of the same shader at ShadeFill 0.17 measured 80.4 / 64.5, i.e. **`set_mpc.py ShadeFill=0.17 GlassSky=0.15` is the first thing to try** (no rebuild), then re-run `shade_check.py` on all views.
Critic pack for r09: `/Users/midir/sm2-n1/_scratch/critic-P1-r09/pack` (key outside the pack: `pack.key.json`; pairs `pairs.json`: the 9 reference pairs at 1080p + `progress-street` / `progress-rooftop` / `progress-sunset` = r08 vs r09).

### What round 09 changed and why (details: `docs/night1/city/EXPORT.md` "Canyon shade fill", header of `Shaders/City/ShadeFill.ush`)
- **Root causes** (found by masks and sweeps, not guessed): (1) Lumen sees a slit of sky inside a 30 m avenue, so shaded walls get almost no indirect light; (2) the r07 albedo cap `SunK` is keyed on N.L, not on shadow: a west wall that faces the sun but sits in canyon shade got the 0.08 luma cap AND no sun. The second one is why the S1 right tower (a west face) was black.
- **Fix = an emissive fill in every city material** (`M_CityFacade / Detail / Roof / Prop / VC (untextured solids) / Kit / Signage (non-emissive kinds) / Leaves (x 0.35)`): the surface's own albedo (before the sun cap, `^0.65`) x a constant sky-bounce irradiance (MPC `ShadeFill` 0.12), tinted warm and weaker at low sun, faded out 0.9-2.2 km (far field untouched: C11-C15 unchanged) and by `1 - NightK`; coated curtain glass gets a sky-gradient reflection instead (MPC `GlassSky` 0.11, tint = the glass F0).
- **Where the fill applies comes from a baked building height field** (`tools/export/bake_sunmask.py` -> `sunmask_h.png` -> `/Game/City/Textures/sunmask_h`, imported by build step `sunh`, part of `tex`): rasterised roof / terrace triangles of the exported roof meshes (exact tiers) + facade vertices + footprint boxes outside the detailed block, 1 m texels, height in R/G (0.02 m), B = height / 400 m. `CityShadeW` = enclosure (mean height around the point from mips 5 / 7 vs the point's height: 1 on the canyon floor .. 0 above the local skyline) x (1 - 0.88 x sunlit), `CitySunLit` = 28-step ray march toward the sun. **The first version added the fill everywhere and blew the sunlit facades** (S2 gold glass mean Y 133, S8 pale glass 148, S8 brick C1 3.2 %, C2 upper bound 119): the mask brought them back to their r08 values (`round-09/README.md` table). Facade `DebugMode 12` shows the weight (blue = full fill, red = none) and matched the real VSM shadows (S2 diagonal shadow on the left tower).
- Trees: the crowns (`M_CityLeaves`) get 0.35 of the wall fill, otherwise the dark shaded leaves kept the S1 left crop under 52.
- `spec_regions.json` **v2** (r08 to-do 1): four boxes had grown over the street trees (green share 30-82 %); re-placed foliage-free, two dropped (`s1_left_glass`, `s6_right_white`). v1 kept as `spec_regions_v1.json`. C1 / C2 counts are 16 daylight boxes now (was 18): not comparable with r07 / r08.
- Tools: `bake_sunmask.py`, `shade_check.py` (the critic's two tests), `shade_sweep.sh` (rebuild + sweep MPC pairs + measure inside ONE gpu_slot hold), `capture_round.sh` hardened (see gotcha 30).

### Log to P4 (look / lighting; the part of the problem that is not materials)
- The shade fill is a stand-in for missing indirect light. The proper fix is in the lighting: sky light in the test maps is 1.7 with Lumen; a canyon wall receives ~2 % of it. Test maps use **manual exposure +2 EV** (+2.3 at sunset), SkyLight 1.7, sun 6 / 4. If P4 raises the sky / bounce contribution (or switches to physical exposure), **lower `ShadeFill` / `GlassSky` (MPC, no recompile: `tools/export/ue/set_mpc.py ShadeFill=.. GlassSky=..`) and re-run `shade_check.py` + `city_spec_check.py`**; the fill must not double-count. `ShadeFill 0` zeroes the fill (the march still runs until the early-out in to-do 2 is added).
- The sun direction the mask uses is `ResolvedView.DirectionalLightDirection` (toward the sun, world space); the mask is correct for any sun angle, but it knows only the buildings of the export block (x -384..640, z -640..384); taller far buildings outside it do not shadow.
- The far skyline was not re-lit (fill fades 0.9-2.2 km): if P4 re-lights the maps, re-run the far-field check (the C13 / C15 window is ~0.01 wide).

### Ranked to-do for round 10
1. **Get the GPU sane again, then re-capture the full set** (`tools/export/capture_round.sh <dir>`: 8 views x 1080p + 4K, now with the zombie guard; needs a free slot lock). Before anything else: `ps -axo pid,stat,etime,comm | grep UnrealEditor | grep -E ' \?E| Z'` must be empty. Set `ShadeFill 0.17 GlassSky 0.15` (or tune), re-run `shade_check.py` + `city_spec_check.py --yolo --ip`, replace `S4` and add the 4K frames. r09 numbers above are 1080p only.
2. **Measure the cost of the shade march under `gpu_slot.sh perf`** (exclusive; A/B with `ShadeFill=0`: that zeroes the fill but the march still runs, so first add `if (k <= 0.0001) return 0.0;` to `CityShadeW`, then it is a true kill switch). Cheap options that change the picture little: 20 steps with growth 1.3 + `if (vis < 0.02) break`; skip when enclosure < 0.02 or beyond 2.2 km (fill already 0 there); or a max-pyramid cone trace (10-12 steps). I wrote and reverted a 20-step version because it could not be rendered before the wedge: the diff is in `git show 8a017c0` (`ShadeFill.ush`, `CityShadeW` gains `cam, k`).
3. **Extend the height field beyond the detailed block** (x -384..640, z -640..384): outside it the fill degrades to "no fill above 8 m" (clamped texels = height 0). The integrated Manhattan map needs the whole island (bake from the `facadeLod` masses + footprints of all tiles, bigger texture or two levels).
4. `s2_dark_tower` (47.1) and dusk `s7_mid_dark` (51.4) under the C2 floor, `s5_grey_tower` C1 (3.70 %, P4 sun / sky ratio: `SunK -> 1`), the first thing K 0.17 should show.
5. r08 critic secondary items still open: S8 glass crop (1270,0,1640,300) 70 % above Y 204 (the fill does not touch it: it is Lumen's sky reflection at +2 EV; `GlassSpec` / P4 exposure), S4 far band silhouette (seawall + piers, top-row std >= 12 px at x 0-1300 y 150-260), cars matte / no plates (clearcoat, taxi toppers), card interiors, flat green sidewalk shed texture, S6 red steps saturation and the white curb (14.6 % > Y 204 at (1150,760,1920,1080)), people (P6), traffic lights (C4 >= 1, YOLO finds 0).
6. Far tree crowns read as solid green masses (hedge-like); the crown-clump LOD (browser `trees-street-near / -far` pools) would look better and cost less than 5 k-15 k triangle leaf cards per tree.
7. If P4 re-lights the maps: lower `ShadeFill` / `GlassSky` accordingly and re-run the far-field check (the C13 / C15 window is ~0.01 wide).

### New gotchas (r09)
30. **Zombie engines and the nested lock (2026-09-30 06:54).** `gpu_slot.sh` checks for engines stuck exiting (`ps` stat `E` / `Z`, shown as `(UnrealEditor)`) only when a hold is ACQUIRED; my hold ran 16 nested captures and launched the next engine on top of a process that was still exiting. That launch (S2, 1080p) hung 15 min in start-up, and `run_game.sh`'s own `-timeout 900` then did `kill -9` on it (the harness rule the owner set after the 23:08 panic: never SIGKILL a rendering engine). Both processes became `?E` zombies (PPID 1, unkillable, GPU reported 100 % with nothing running) and the lock has refused every launch of every agent since (traversal, look, perf, characters, combat, my own queued hold were all waiting >1 h). One of the two was probably not mine (started 3 s earlier). `capture_round.sh` now: refuses to launch while any UnrealEditor is `?E` (waits 25 min, exit 6), passes `-timeout 7200`, runs a watchdog that calls `stop_ue.sh` after 480 s, aborts (exit 7) if an engine is left stuck after a run, stops launching after `CAPTURE_DEADLINE_S` (default 2100, exit 8; the max hold is 2400 s). It cannot fix a wedge; only a reboot / the driver releasing the contexts does. `run_game.sh` (not P1's file) still has the SIGKILL timeout: always pass `-timeout` large.
31. **Blanket string replaces in Custom-node code.** Renaming a call site with `str.replace(tail, ...)` also hit three unrelated `dot(n, ...xyz)` lines (`sunf`); caught by grepping the diff. Check `git diff` of `build_city.py` after every scripted edit: a broken Custom node compiles to the default material in `-game` without failing the commandlet.
32. `rm -rf "$VAR"/...` in a tool call is refused by the sandbox check unless written `"${VAR:?}"/...`; keep scratch cleanups literal.
33. The height field texture is point-filtered (R/G hold a split integer, filtering would corrupt them); the B channel (height / 400 m) is read at mips 5 / 7 with a manual 4-tap bilinear in `CityMeanH`. Import settings: RGB8 uncompressed, linear, clamp, simple-average mips, never_stream (step `sunh`, also run by `tex`).
34. Facade `DebugMode 12` = shade-fill weight, needs `set_mpc.py DebugMode=12` and back to `DebugMode=0` (the MPC is saved in the asset: a forgotten 12 turns every later capture into a mask).
35. A `-game` capture with a MODIFIED material compiles shaders lazily: the first capture after a `mat` step is slow, later ones hit the DDC. `tools/export/shade_sweep.sh` runs rebuild + MPC + captures inside ONE hold so the queue wait is paid once; the queue wait on 2026-09-30 was 10-45 min per hold (perf runs of other agents hold the lock exclusively).

### What round 08 changed, root causes (details in round-08/README.md; docs/night1/city/EXPORT.md "Street life")
- **Why the streets were empty:** the browser's parked cars and traffic are runtime simulation (`npc/traffic.js` `parkedFor`, streamed around the camera), not `Pool` instances, so `export_city.mjs` never saw them; and r05's `thin()` had deleted 45-100 % of the S1 / S2 street trees while `street_props.py` added empty iron tree pits (the critic's "empty tree pit").
- **Cars:** `tools/export/export_vehicles.py` exports the browser's Blender car models (`public/assets/city/vehicles.glb`, LOD0, 12 bodies) as `proto/veh_*.glb` + manifest records; the livery atlas is NOT used (IP); part colours in vertex colour; `M_CityProp` renders them (paint = per-instance tint). `street_cars.py` (parked, 197 cars / 37 taxis, browser rules) and `street_traffic.py` (stopped lane traffic, 195 cars, own actors under `City/Traffic`) write `streetcars.json` / `streettraffic.json`; `build_city.py` `make_ism()` spawns them.
- **Trees:** `street_trees.py` plants every empty pit and every > 9 m gap on both sidewalks of the four avenues (`streettrees.json`, `_remove` = browser trees within 16 m of a street-level shot camera); `thin()` is gone. **`M_CityLeaves` distance alpha** (`steps=leaves`): alpha-tested leaf cards lose coverage in the texture mips, beyond ~25 m every card was discarded (bare branches in S2 / S8).
- **Density tuning of the lane traffic** was done against the checker (lane cars per block -> S2 vehicles / S1 cars at conf .30): 13.7 -> 58 / 18, 7.1 -> 34 / 19, 4.9 -> 24 / 15, 4.1 -> 15 / 18 (margin to the >= 14 test too thin), 4.6 -> 17 / 16 (final). S1 and S2 look down the same avenue: their counts move together only roughly (+-3 from a re-hash), so re-run YOLO after ANY change of car positions.
- Camera keep-outs (`CAMS` in `street_cars.py`, `street_traffic.py`, `street_trees.py`): no car within 15 m of a street-level shot camera or in the 22 m corridor ahead of it, no tree within 16 m (a hatchback 10 m from the S1 lens filled a third of the frame).
- Checker: `city_spec_check.py` YOLO worker at conf 0.30 (the critic's test; `CITY_YOLO_CONF`), reports `vehicles_c35` too, `CITY_YOLO_ANN=<dir>` writes box-only annotated frames. `builder_crops.py` now writes the r08 evidence crops.

### How a round runs now (measured wall times; the shared GPU queue took 2-15 min per wait on 2026-09-30, other agents' captures + perf runs)
ONE slot hold for the whole sequence (nested `gpu_slot.sh` calls pass through; max hold 40 min INCLUDING `wait_slot.sh` sleeps while 4+ Unreal processes of other agents run: the r08 finals took 14-30 min):
```
cat > final.sh <<'X'   # zsh; strictly sequential, one Unreal process at a time
WT=/Users/midir/sm2-n1/city
$WT/tools/export/ue/run_commandlet.sh $WT/unreal/WebHomage/Scripts/build_city.py steps=leaves,map   # veh,leaves,map when the car meshes changed; map only when only the JSON placements changed (~20 s)
while pgrep -f "MacOS/UnrealEditor .*$WT/unreal" >/dev/null; do sleep 3; done
$WT/tools/export/capture_round.sh <raw_dir>            # 8 views x (1080p, 4K), perf window 18-28 s
X
/Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label city -- zsh final.sh     # run with nohup ... & and poll the .out file
python3 tools/export/assemble_round.py <raw_dir>/raw docs/night1/city/round-NN NN
CITY_YOLO_ANN=docs/night1/city/round-NN/builder_checks/yolo python3 tools/export/city_spec_check.py docs/night1/city/round-NN --yolo --ip --json docs/night1/city/round-NN/city_spec_check.json --md docs/night1/city/round-NN/city_spec_check.md
python3 tools/export/builder_crops.py docs/night1/city/round-NN
```
Placement scripts (`export_vehicles.py`, `street_cars.py`, `street_trees.py`, `street_traffic.py`) are pure Python on the export in `_scratch/city/export/midtown3x3` (no browser, no Unreal): edit, run, then `steps=map` and capture. A full 8-view + 4K round is ~8 min of GPU when the queue is empty.
If the driver script exits 5 (`gpu_slot ... release exit=5`) the commandlet failed (rc != 0) and NO capture ran: read `Saved/Logs/city_cmdlet.log` (`grep -a 'Error\|WARN\|build_city  '`).
Never run two of your own captures at once (one Unreal process per agent: do not queue a second hold while one is waiting). There is no `timeout` command on macOS; block on the log with `until grep -q DONE file; do sleep 5; done`.

### New gotchas (r08)
24. **Do not rename / delete a referenced mesh in a commandlet**: `EAL.rename_asset(old, old_ts)` leaves a redirector at the old path and the next `rename_asset(new, old)` fails ("An asset already exists at this location"), `delete_asset` returns False; the run then keeps the OLD mesh silently and exits rc=1. `build_city.py` now imports over an existing prop as `SM_<name>_v<N>` (`next_version()`); `sm_path()` picks the newest for the ISMs. A `clean` rebuild recreates everything.
25. **Interchange keeps `TEXCOORD_1` as (part id, 0) with `use_full_precision_u_vs`**: the vehicle protos use the same `aPart.x` convention as every other prop, so `mi_for()` picks `M_CityProp`; vertex colour is linear part colour x AO, `TEXCOORD_0` zeros (no atlas).
26. **Alpha-tested foliage and mips**: masked leaf cards vanish with distance (coverage loss in the alpha mips). Fix in the material (alpha cut falls with distance), not in the mesh.
27. **YOLO is a moving target under re-hash**: any change of a car's position moves S1 / S2 counts by +-3 (S1 18 / 19 / 15 / 18 / 16 for five densities, see above). Keep >= 3 margin to the test threshold (>= 14 in S2) and re-run the checker on the FINAL frames, not on the iteration frames.
28. `Scripts/run_game.sh` frames of one hold share one map build: capture only after `commandlet rc=0` (my `final.sh` aborts on rc != 0).
29. The three street-level cameras (S1, S5, S6) define the keep-out discs; if `city_shots.json` moves a camera, re-run the three placement scripts.

### What round 07 changed, root causes (details in round-07/README.md; still valid)
- **CITY-SPEC measured once**: `spec_regions.json` (hand-placed boxes, 1080p + 4K per line), `city_spec_check.py` (texture statistics on the 1080p-normalised frame, mean-type statistics on the native frame; `--overlay <dir>` draws the boxes). r06's builder / critic disagreement was different boxes.
- **`M_CityFarMass` never compiled in r06** (`vc.a` on an RGB-only custom-node input): every far-shore block of r03-r06 was the default grey material. New input kind `vca` in `make_material`. Then: per-24 m tone jitter `FarJit` (1.3), floor banding, ~1 block in 6 dark glass,
  window grid never below 18 %; `M_CityFarLand` canopy / lots / street lines; `M_CityCliff` basalt columns; water Fresnel (`WaterSpec` 0.035).
- **Atmosphere of the view maps** (`add_lighting`; `FOG_DENSITY` etc.): fog 0.0008, inscattering (0.76, 0.78, 0.80), aerial scale 0.34. **Trade line** (S4, sweep table in README): fog -1e-4 = C13 -1.7 Y and C15 +0.011; FarGain +1 = C13 +1.8 Y (only +0.8 above ~6) and C15 -0.004; FarJit +0.3 = C13 -1.5 Y, C15 +0.005.
  MPC values (saved asset and script defaults agree): FarGain 7.6, FarJit 1.3, FarLandGain 1.6, WaterSpec 0.035, SunK 0.08.
- **Facade albedo cap `SunK`**: sun-facing base colour luma limited to SunK via `ResolvedView.DirectionalLightDirection` (N.L ramp 0..0.4), faded out over 0.9-2.2 km so the far skyline keeps its albedo; in M_CityFacade / M_CityDetail / M_CityRoof; `AlbKnee/AlbSlope/F0Scale` in the facade.
  C1 10/18 -> 17/18. **Do not put code after a `//` on the same line inside a Custom-node string**: the interrupted WIP did that (the whole cap commented out; the committed 20:20 frames had no cap).
- IP: MTA slogan, racing-franchise key art, sneaker photography replaced by original art (`ip_original_art.py`); 0 OCR hits. Sign atlases `never_stream`; `tsFrames` panelled cladding; 7 shop-interior types.
- Scripts: `run_commandlet.sh` (headless `-nullrhi` commandlet through the GPU slot) is the way to run any editor script; `launch_editor.sh` (`open -n`, not slot-wrapped) should not be used while the lock is in force. Neither `pkill -9`s an engine any more.

### Gotchas (r07)
16. Custom-node vertex colour input is RGB; alpha needs the `A` output (`kind 'vca'`). A failed compile = default material in -game, silently: `grep "Failed to compile" <capture>.log`.
17. Editor Python / materials / MPC / maps run fine in a `-nullrhi` commandlet; shaders compile lazily in the -game process.
18. Sun direction in a material: `ResolvedView.DirectionalLightDirection.xyz` (toward the atmosphere sun) compiles in Custom nodes. The material cannot know shadows.
19. After the 2026-09-29 16:43 GPU incident: <= 1 Unreal process per agent, everything through `gpu_slot.sh capture`, `wait_slot.sh` cap 4 (`SM2_MAX_UNREAL`). After the 23:08 kernel panic: never SIGKILL an engine (`stop_ue.sh`), never launch while an UnrealEditor is stuck exiting (the lock refuses). `Scripts/run_game.sh` still `kill -9`s after its `-timeout` (900 s; not P1's file): a normal capture takes ~50 s, so watch and use `stop_ue.sh` first.
20. `S4v?` variant maps (a..r) are scratch in Content/ (not committed, regenerable with atmo_variants.py); the last sweep left S4va..S4ve there.
21. `set_mpc.py` prints the parameter dict to `Saved/Logs/city_cmdlet.log`, not to stdout: `grep -a "'FarGain'" .../city_cmdlet.log | tail -1`.
22. Comment lines in a Custom-node string swallow the rest of their physical line: one statement per line.
23. Lumen bounce: capping near albedo also lowers the far shore Y by ~1 (S4 -1.2) and river by ~0.8: re-measure S4 after any near-field albedo change.
Detailed block = 768 m long (tiles ix -1..1 -> x -256..512); the 30 s route leaves it at ~22.6 s. Not extended.

## State (round 06, still valid)
- Critic rounds: r01-r05 FAIL (r05: facades 5, street 4, skyline 3, Manhattan 4, IQ 5; gap: far skyline, S4 and everything past ~1 km).
  r06 = far field: far-shore blocks with real window grids, coast / far-land materials instead of white slabs, thinner warm-neutral haze, real-water
  Fresnel, IP exclusions (HAUTE UNLIMITED, Hotel Astoria, Madison Arena, Boreal Outdoor, New York Knights).
- **What was wrong (root causes, all found by rendering with fog off and by mask captures):**
  1. `farCityMass` (far-shore blocks, farshore.js) encodes a window flag in vertex colour blue (+10 / +20); the exporter clamped colour to 0..1 and the flag
     became saturated blue for every block (the "lavender boxes"). `export_city.mjs` now decodes the flag into vertex ALPHA (0 / 0.5 / 1) and restores blue.
  2. Coast, far-land, cliff and water were imported with the generic white vertex-colour material (`M_CityVC`): the near-white shoreline / "snow" slabs.
  3. Height fog density 0.006 with blue inscattering + full aerial perspective washed the far field out.
- **New materials** (build_city.py): `M_CityFarMass` (createMassMaterial port: window grid, spandrels, glass towers, night lights; warm push), `M_CityCoast`
  (createCoastMaterial port: atlas granite / riprap / planks / bulkhead, lawn, pavers, ribbed metal, picket cards), `M_CityFarLand` (the browser's baked far-land
  ground map, exported by `export_city.mjs` as `farland_map.png`) and `M_CityCliff`. `far_material(rec)` maps mesh names to them. `M_CityWater` Specular 0.25
  (real water F0 0.02; 0.5 read as milky glass). New build step **`far`** (re-imports `farCityMass` as `SM_*_r06`, retargets the other far meshes, swaps level
  actors); `build_geo_level` prefers `_r06` / `_r04` re-imports, so a `map` step no longer reverts them (before this, round-05 map rebuilds silently restored the
  original tsFrames housing).
- (SUPERSEDED by r07: fog 0.0008, aerial 0.34, inscattering 0.76,0.78,0.80) **Atmosphere of the view maps** (`add_lighting`, args `fog=`, `fogc=`, `aerial=`; variants: `tools/export/ue/atmo_variants.py`): height fog 0.0065, sky-neutral
  inscattering (0.6, 0.62, 0.64) (r05: blue 0.32, 0.40, 0.52), SkyAtmosphere `aerial_pespective_view_distance_scale` 1.0 (sic, UE spells it "pespective").
  History: I first thinned the haze (fog 0.001, aerial 0.25) for the best-looking far field, then CITY-SPEC C11-C15 (added mid-round) asked for the opposite
  (far shore 25-35 luma under the sky, aerial contrast falloff 0.25-0.45): the current values are the spec-driven ones. The sky is blown (Y 229, manual exposure
  +2 EV in the test maps): P4 owns exposure / sky; the far-shore / sky RATIO is what these values fix, so it should survive an exposure change.
- Facade far LOD (`gen_shaders.mjs` uePatch): window-cell box filter 1.8x -> 1.15x (grid readable further out) and a warm-neutral albedo push where lod -> 1.
- **Measurements** (round-06/README.md has the tables; scripts in tools/export): `spec_farfield.py` (CITY-SPEC C11-C15), `far_stats.py` (shore strip vs water, masks =
  MPC_City.DebugMode 3 captured on `City_View_S4vm` = S4 with fog and aerial off, because haze washes the mask colours out), `facade_c1.py` (C1 / C2, facade mask =
  DebugMode 11), `ip_ocr_check.py` (denylist OCR). r06 numbers: C11 6.7x sky Laplacian / flat blocks 22 %, C12 +1.9, C13 -32.6, C15 0.25 pass; **C14 fails** (river 13.5
  brighter than the far shore: the river is veiled by the same haze; fixing it needs a distance-dependent haze model or a lower sky exposure, not more fog tuning);
  shore strip darker than water by 0.104 luma (crop x 0-2800, y 550-700); C1 fails on S2 (sunlit pale stone 30.7 % above Y 204, mean 134) and S2 right glass tower (3.8 %),
  passes on S1 / S8; S1 right tower (canyon-shadowed dark glass, mean Y 20) is under C2's 52. Those are lighting-driven (sun 6, sky fill 1.7, exposure +2 EV): for P4.

## Round 05 (street level; still valid)
- Critic rounds: r01-r03 FAIL; r04 FAILS-improving (facades 5, street 3, skyline 4, Manhattan 4, IQ 5; gap: street level 0-3 storeys unbuilt).
  r05 = street-level kit + crisp shop interiors + supplemental street furniture + sidewalk slabs + two more IP cell exclusions.
- Detailed block: tiles ix -1..1, iz -2..0 (x -256..512, z -512..256). Far: facade-LOD masses for the whole island, far shores, bridges, hinterland
  boxes, land polygon, one water plane at y = -1.6 m, height-fog haze from 400 m. Views: 8 maps `/Game/Tests/City/City_View_<id>` (S1..S8).
- **Street-level kit (r05)**: `tools/export/street_kit.py` reads every ground-floor face of the exported facade meshes (`street_faces.py`: face frame,
  storefront height gH, bay layout of the shader) and builds real geometry in front of the shader wall: stone / brick piers with plinth + capital, a
  stepped stone cornice with dentils (metal canopy on curtain-wall podiums), 3D storefront frames (jambs, head, transom, mullions, door leaves with kick
  plates + pull bars), fascia sign boards, fabric awnings (stripes, lettered valance) or metal marquees, and fire escapes (grated platforms, railings,
  stair flights, drop ladder aligned with a pier) on ~90 % of pre-war faces and on side / deco faces. 578 faces, 2225 bays, ~580 k tris, 9 GLBs
  (`mesh/streetkit/`), Nanite, material `M_CityKit`. Signage = `gen_street_signs.py` (original generic shop names, system fonts).
- **Crisp shop interiors (r05)**: the atlas photos were ~85 px / m and blurry at street distance. `gen_shaders.mjs` `uePatch` list now draws four shop
  types analytically (grocery shelves + produce crates, cafe slat wall + jars + menu boards + pendant lamps, boutique rails + mannequins, pharmacy /
  bank), customers, checker floor, side walls, soffit + ceiling tubes; anti-aliased from the pixel footprint.
- **Street furniture (r05)**: `street_props.py` adds a hydrant, trash can, newspaper box and tree pit every ~20 m of avenue frontage (149 / 151 / 143 / 127
  instances) to the browser pools' ISMs (`streetprops.json`, merged in `build_city.py`). Sidewalk shader patch: 1.5 m slab joints, bevel, per-slab tone,
  hairline cracks, gum spots (`gen_shaders.mjs`, Sidewalk block). S1 corridor street trees thinned (45 %; the deco podium in front of the fire escape is
  cleared: `thin()` in build_city.py) and SkyLight intensity 1.7 in every view map.
- IP: `ip_sanitize.py` also excludes COLTEX SPORT (L27), COLTEX (P27) and COLEXCO (P38) ad cells. See `IP_EXCLUSIONS.md`.

## Round 04 numbers (details: round-04/README.md, window_stats.json, window_crops/)
Share of window pixels above 80 % luminance in 400 px crops of the 4K frames (round 03 -> round 04): S1 right facade 0.0 % -> 0.0 % (median luminance
0.286 -> 0.071: the tower is in canyon shade and now reads near-black glass), S8 brick tower centre-right 11.97 % -> 3.11 %, S8 brick tower left
21.26 % -> 0.0 %, S2 left stone tower 24.13 % -> 0.49 %, S7 right masonry wall 68.93 % -> 0.0 %, S7 left glass wall 0.0 % -> 0.0 % (median 0.388 -> 0.129).
Open: S1's right tower may now be too dark (median 0.07); DayEmisK / InteriorGain are the knobs (MPC, no recompile). Window mask frames
(`_scratch/city/r04/mask4k`, DebugMode 3) were captured once; a rerun after geometry changes needs new masks (set DebugMode=3, capture the 4 views at 4K, reset to 0).

## Commands (all from the worktree root)
```
npx vite --port 5202 --host 127.0.0.1 --strictPort &        # browser city (exporter needs it; only for a full rebuild with export)
tools/export/build_city.sh                                  # FULL: export -> patch_export -> prep textures (IP sanitiser) -> street signs -> street kit -> street props -> gen shaders -> build_city.py (this last step goes through uejob.py = a P1 EDITOR
                                                            # with the job server; on a clean checkout run the last line of that script through tools/export/ue/run_commandlet.sh instead: `run_commandlet.sh unreal/WebHomage/Scripts/build_city.py steps=clean,tex,mat,mesh,proto,kit,map`)
tools/export/ue/run_commandlet.sh <script.py> [k=v ...]     # ANY editor script (build_city.py steps=mat,map | set_mpc.py FarGain=.. | atmo_variants.py ...) headless -nullrhi, through gpu_slot; needs the P1 editor closed
tools/export/ue/launch_editor.sh                            # legacy: `open -n` editor with MCP :8771 + job server; NOT slot-wrapped, do not use while the GPU lock is in force
tools/export/capture_round.sh <raw_dir> [ids...]            # run_game.sh per view, 1080p + 4K, perf + GPU util (waits for a free Unreal slot)
python3 tools/export/assemble_round.py <raw_dir>/raw docs/night1/city/round-NN NN   # JPGs + perf.json + README
python3 tools/export/window_stats_round.py <lit_dir> <mask_dir> out.json [crop_dir]  # window brightness test (mask = DebugMode 3 frames)
node tools/export/browser_views.mjs <out> [ids]             # browser captures from the same cameras (A/B)
python3 tools/export/bake_sunmask.py                          # (r09) height field for the shade fill -> <TEX>/sunmask_h.png (build_city.sh runs it; import = build_city.py step `sunh`)
python3 tools/export/shade_check.py <round_dir> [--json f]  # (r09) the critic's Test 1 / Test 2 (S1 crops, share Y < 25)
python3 tools/export/ue/uejob.py file.py [k=v]  |  -c "code" # run editor Python in the P1 editor (JOB_ARGS dict)
```
Stop an engine of yours: `/Users/midir/sm2-n1/_scratch/gpu/bin/stop_ue.sh "[/]Users/midir/sm2-n1/city/unreal/WebHomage"` (drivers first, SIGTERM, wait; NEVER `kill -9` a rendering engine). **Owner rule 2026-09-29: the editor is
closed whenever it is not needed** (captures use `run_game.sh`, they do not need it) and no Unreal process is started while 3+ are running
(`tools/export/ue/wait_slot.sh`). Typical r04 loop: launch editor -> `uejob.py build_city.py steps=mat` / set MPC -> stop editor -> capture.
Full build ~9 min, export ~2 min, mat step ~15 s (the shader compiles lazily in the game process), one view capture ~70-120 s.

## Job runner (legacy editor route; r07 uses run_commandlet.sh instead)
The official MCP has no Python exec, and `-ExecutePythonScript` QUITS the editor. The editor runs `job_server.py` (slate tick, polls
`_scratch/city/uejobs/*.py`, writes `.out` / `.done`). Jobs run on the game thread; a modal dialog blocks it (deleting referenced maps /
materials / meshes did that) -> build_city.py never deletes referenced assets: maps are opened + emptied, materials reused, and the
`frames` step re-imports a mesh under a new name (`_r04`) and re-points the level actors instead of deleting.
No numpy inside the editor's Python.

## File map
- `tools/export/export_city.mjs` + `collect_page.js`: headless Chrome export. `patch_export.py`: post-export mesh clean-up (r04: removes
  dark hovering tsFrames housings within 25 m of a shot camera). `ip_sanitize.py` + `prep_textures.py`: IP-clean Unreal copies of the
  ads / signs atlases (see `IP_EXCLUSIONS.md`).
- `tools/export/glsl2hlsl.mjs` + `gen_shaders.mjs`: browser GLSL -> `Shaders/City/{Facade,Detail,Roof,Asphalt,Sidewalk}.ush`. **Facade.ush is
  generated: never edit it by hand.** UE-only changes go into the `uePatch(...)` list in gen_shaders.mjs (each patch must match exactly once).
- `unreal/WebHomage/Scripts/build_city.py`: textures, materials (Custom nodes), meshes, protos, maps, `frames` step. `city_shots.json`: the 8 cameras.
- Materials: M_CityFacade/Detail/Roof/Asphalt/Sidewalk (ports), M_CitySignage (signage.js port, r04), M_CityKit (street kit, r05), M_CityFrame (gunmetal billboard housings,
  r04), M_CityProp, M_CityVC, M_CityLeaves, M_CityCrown, M_CityLand, M_CityWater (placeholder, P6), M_CityHinter, MPC_City.

## MPC_City (Content/City/Materials/MPC_City, defaults in build_city.py MPC_DEFAULTS)
NightK, DnTime, InteriorGain 0.5, ShopGain 0.7, EmissiveScale 3.0 (r03) plus r04: **DayEmisK 0.22** (facade interior / sign emission scale in
daylight, 1.0 at night: rooms behind glass are ~10x darker than sunlit masonry), **GlassSpec 0.5** (UE Specular of dielectric sash glass = F0 0.04), r06-r07: **FarGain 7.6, FarJit 1.3, FarLandGain 1.6, WaterSpec 0.035** (far field), **AlbKnee 0.30, AlbSlope 0.48, F0Scale 0.8, SunK 0.08** (facade albedo cap, C1),
**DebugMode**: facade: 1 emissive only, 2 no emissive, 3 window mask (red = glass pixel; used by window_stats), 4/8/9 gLodI, 5/7 raw interior
atlas, 6 interior(), 10 raw signs atlas, 11 facade-only mask (facade_c1.py); r06 far field, mode 3: coast + far land red, water blue, far-shore blocks green; mode 9 (M_CityFarMass): vertex alpha. Change values without recompiling: `run_commandlet.sh tools/export/ue/set_mpc.py Name=value` (or `uejob.py` in an editor) (edits
the MPC defaults and saves; `tools/export/capture_one.sh <dir> <id> [WxH]` = single frame).

## Facade patch layer (gen_shaders.mjs, r04) — what made the windows read as glass
1. `gLodI` -2.5 mips (interior mapping sampled the room atlas 2-4 mips too high because UE renders at 50-73 % internal resolution: every room was
   the atlas average = beige).
2. Rooms 25 bays wide with the back-wall photo wrapping once per bay / per storefront (`gRoomWrap`): at street angles a 3 m room exits through its
   side wall after 1 m, so all windows showed one flat side-wall tint.
3. Lit / dim / dark rooms in ~10 / 30 / 60 %, unlit rooms 0.2x, ceilings 0.42 (was 0.72), shop floor 0.3, blinds albedo x0.5.
4. Material: Emis x DayEmisK; sash glass Specular 0.5 instead of 0.1375 (the old value removed all reflection); curtain glass unchanged (metal mirror).
Result: dark glass with Lumen reflections, visible room interiors (desks, paintings, shelves) in the lit share of windows, blinds and curtains.

## Gotchas (each cost hours)
1. **Nanite keeps only 4 UV channels.** Facade / roof / ground meshes must be non-Nanite AND rebuilt (symptom: facades without windows).
2. **The editor caches shader source files**: edits to `Shaders/City/*.ush` are ignored until `recompileshaders changed` (build_city.py mat step runs it).
3. **Material usage flags must be saved** (Nanite, InstancedStaticMeshes) or -game draws the default material.
4. Custom-node HLSL: `Texture2DSample`/`...SampleGrad` wrappers, float literals with `f`, derivatives (ddx/fwidth) only in uniform control flow, textures
   passed through every function (TEXDECL / TEXPASS).
5. three.js textures are v-flipped: sample at (u, 1 - v) (fl2/fl3 helpers).
6. Glass: coated curtain glass = metal mirror; sash glass = dielectric Specular 0.5 (r04).
7. `EditorAppToolset.CaptureViewport` renders unconverged frames; judge in `-game` (run_game.sh).
8. Interchange glTF: UE = (x, z, y) x 100; per-file subfolders `_in/<name>/StaticMeshes/`.
9. `MPC.scalar_parameters` names are `Name` objects: compare with `str()` or every run appends `NightK1`, `NightK2` ... (fixed in build_city.py).
10. GLB coordinates are tile-local: world = local + manifest `center` (x, z).
11. Handedness: UE is left-handed. A hand-made camera ray needs `right = cross(up, f)` and `up = cross(f, right)` (the first S5 probes were wrong).
12. GPU is shared: every perf number so far was taken at 50-99 % utilization before the run.
13. Mask captures see haze: fog / aerial perspective add a ~75/255 veil to every pixel, so mask colours are detected by channel differences (far_stats.py),
    not absolute levels; set Specular 0 + roughness 1 in the mask branch of a material or reflections leak in.
14. Interchange keeps vertex ALPHA and clamps vertex colour to 0..1 (8-bit): never encode data in colour values > 1 (exporter decodes farshore.js flags into alpha).
15. Debug recipe: replace the return of a Custom node by a debug value scaled by 0.05 (emissive 1.0 saturates at the +2 EV manual exposure), capture
    1080p in `-game`, read pixel values with PIL.

## Known problems / next rounds (the round-09 to-do list is at the top; this list is older and partly fixed: FIXED r07 / r08 marked)
- Far field (r06 text; r07 added tone jitter, banding, dark-glass blocks, canopy clumps, basalt cliff, see top): the far-shore blocks are boxes with a window grid; no brick / trees / parks colour variety like the browser (the browser bakes park
  greens and lot tones into the far-land map, which is used, but the 2-4 km facade ring stays tone-flat). No bridges texture work, no far water towers.
  Horizon hinterland (> 5 km) is sub-pixel windows only. Hazy sky band stays bright (sky / exposure belong to P4).
- Test-map atmosphere (r07: fog 0.0008, aerial 0.34, inscattering 0.76,0.78,0.80) is mine; if P4's look pass re-lights the maps, re-run `city_spec_check.py` (it supersedes spec_farfield.py / far_stats.py / facade_c1.py, which stay for mask captures).
- The window-brightness numbers of round 04 (window_stats_round.py) were superseded by CITY-SPEC C1 (facade_c1.py); the r04 script still works with DebugMode 3.
- FIXED r08: parked cars / traffic (C4 / C6) and the S1 street-tree count. CITY-SPEC C4 people, C7 storefront count, C8 checklist, C9 S3 water towers (>= 2 in frame), C10 are still hand counts / P6.
- `frames` / `far` steps leave the previous imports behind as `*_old<ts>` assets; a `clean` rebuild removes them.
- Fire escapes are in the S1 crop x 0-1600, y 800-1700 only at its top-right corner (the lowest platforms of the far deco tower, x ~1525-1600,
  y 800-1000); nearer escapes start above the 6 m cornice, above that crop. If the critic wants them lower in frame: move the camera or add a
  retracted-ladder variant. Drop ladders end at 2.6 m and are aligned with a pier (behind awnings they are hidden at oblique angles).
- Street kit density: every ground-floor bay gets a fascia board; ~38 % of bays get a fabric awning, ~21 % a marquee (curtain-wall podiums: marquee only);
  bays that already carry a browser awning mesh (fabric / marquee bulbs) get no second awning. Awnings are dark-ish (palette in `street_kit.py` AWN).
- Shop interiors are analytic (crisp) but simple: no depth-of-field cues, customers are flat silhouettes, no per-shop signage inside. Upper wall / soffit
  is a dark band; the glass reflects the sky (white panes at grazing angles).
- S5 / S6 (Times Square): the kit also dresses those podiums; tree guards there still hold no trees; red steps flat; white clipping on the curb.
- Sunset (S7) and night: interior emission only follows NightK; a dusk ramp belongs to P4.
- FIXED r07 (lavender boxes, white shoreline slabs); bridges and piers on the far shore still missing (critic secondary issue).
- FIXED r08: parked cars, stopped avenue traffic (static, folder City/Traffic) and trees; still no pedestrians (P6); sidewalk joints are visible in sun only (the avenue sidewalks sit in canyon shade).
- Perf r05: see round-05 README; captures ran with other Unreal sessions active, numbers are contaminated (GPU util column).
- Window brightness test (r04 numbers in the section above) was not re-measured in r05 (upper-floor glass unchanged; SkyLight 1.0 -> 1.7 brightens
  reflections slightly): re-run `window_stats_round.py` with fresh DebugMode-3 masks before quoting.
