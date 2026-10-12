# Terrain round 01 — captures and measurements

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Build: branch `night1/terrain`, base Manhattan content rebuilt in this worktree 2026-10-01 ~20:35 + `build_terrain.py` run 23:08 (v2). Every run through `gpu_slot.sh capture` (cap 1), offscreen, throttled (`WH_CAPTURE_MAXFPS`).

| file | what | resolution (disclosed) |
|---|---|---|
| `stills/p1_south.jpg` ... `p10_lawn_eye.jpg` | terrain stills (`shots.json`, maps `/Game/Terrain/Maps/V_<id>`), game time 2 s, `-benchmark -fps=30` | **3840x2160 output, internal 1920x1080** (r.ScreenPercentage auto = 50 %, TSR 2x upscale) |
| `stills/base_*.jpg` | the same cameras on the city alone (`VB_<id>`): the "previous round" baseline | same |
| `t4_lawn_sprint.mp4` (+ `_telemetry.csv`) | hero sprints 130 m north across the lawn onto a path, ground mode all the way (0 fall-through, floor height 0) | **1920x1080 output, internal 1920x1080** (r.ScreenPercentage 100), 60 fps fixed step, 805 frames |
| `t5_avenue_to_park.mp4` (+ csv) | street sprint + swing chain north up 5th Av, ends airborne over the park edge (y -620 m) | same, 925 frames |
| `stills/t*_t*s_1920x1080.jpg` | contact frames of the movies | 1920x1080 |
| `browser/parkHigh|parkLow|parkClose.jpg` | the browser game's own park shots (the look the port starts from) | 1920x1080 |
| `evidence_v1/` | the first run's two worst frames (v1: Reservoir hidden under the city's flat land polygon; opaque crown blobs) | 3840x2160 |
| `stats.json`, `shore_audit.json`, `hlsl_check.txt`, `crop_manual.json` | measurements | — |

GPU: `ioreg` utilisation was 0-4 % before every launch (logged per run in `_scratch/terrain/turn*.log`); captures are movie / still runs, NOT performance numbers (no perf claim is made).

## Measured against `SPEC.md`
- **E1 park-crop high-pass sd >= 8: FAIL.** Hand-picked pure-lawn 512x512 crops (`crops.json`): eye-level lawn 4.92, aerial lawn 4.65 / 6.93, great lawn with ball-field infields 15.09 (min 4.65). Baseline (city alone) same eye-level crop: 2.57.
  The lawn micro-detail is too soft at eye level and from the air; first fix of round 2.
- **E2 grass cover: 89.9 %** of open park land (target 90 %; 94.5 % excluding the schist outcrops; 76.5 % of all park land incl. paths, which the browser design caps at ~87.5 %).
- **E3 shoreline: 0 gaps > 5 m** after the granite bulkhead patch (the browser coast has 12, max 12 m, all at the Inwood tip). Geometry audit; the v2 shore stills use cameras that sit inside buildings (fixed in `shots.json`, not re-rendered).
- **E7 collision:** `t4_lawn_sprint` telemetry: ground mode over the lawn for the whole run.
- **E5 axes:** not judged here (blind critic).

## Known defects visible in these captures (v2)
1. Opaque low-poly crown blobs ("green polyhedra") in the tree canopy at every distance: per-instance cull distances did not hide the city's far-crown instances. v3 (committed, not rendered): `M_TerrainCrown` clips them by camera distance (< 520 m) and tints them.
2. Lawn micro-detail soft (E1). 3. Grass tufts dark next to the lawn (v3: gain 1.7). 4. Pier / shore stills (`p6`-`p8`) frame buildings, not the shore (v3 cameras in `shots.json`).
5. The hero in the movies is the default HeroDev red-and-blue suit with a white emblem: this worktree's base build skips the characters step (original-suit generator belongs to the characters piece). Judge the terrain, not the suit.

## Round 2 note (movies removed)
`t4_lawn_sprint.mp4`, `t5_avenue_to_park.mp4` and their contact frames were removed from the tree in round 2 (`git rm`): they showed the hero's dev-suit emblem (critic r1 brand flag). Their telemetry CSVs / log excerpts stay.
Round-02 movies are captured with the hero hidden (`ShowFlag.SkeletalMeshes 0`). History keeps the old files (`git show 77d0946:docs/night1/terrain/round-01/t4_lawn_sprint.mp4`).
