# P6 City life, round 01: capture notes (neutral, for the critic)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. Nothing here is a claim of matching any reference game.

## What is in this folder

| file | what |
|---|---|
| `stills/S1_street_{1080p,4k}.jpg` | `Life_View_S1`: P1 shot camera S1 (street level in the avenue, looking north), game t = 28 s, golden-hour rig. 4K = native 3840x2160 with `r.ScreenPercentage 100` |
| `stills/S2_avenue_{1080p,4k}.jpg` | `Life_View_S2`: shot camera S2 (42 m above the avenue, looking north) |
| `street_clip_1080p60.mp4` | 20 s street-level walk through the avenue's curb channel (`Life_Street_Clip`), fixed 1/60 s steps (`-benchmark -fps=60 -dumpmovie`: smooth 60 fps footage that says nothing about real-time speed), 1920x1080, H.264 |
| `SPEC_TABLE.md` | C4, C6, CH16, CH17, CH19 against this build, with the counting method |
| `probe_*.txt`, `feet_*.csv`, `feet_analysis.json` | raw engine-side measurements (frame counts, foot log, gait phases) |
| `perf_*` | GPU-locked frame times with the life actors on and off (see below) |
| `ip_check.txt` | OCR check of the sanitised vehicle atlas and the 4K stills against the IP denylist |

## What to look at

- Vehicles: real LOD0 Blender models of the browser build (taxis, cabs, vans, box trucks, SUVs, buses) on the P1 avenue; taxi roof signs show four of the eight browser ad tiles (the other four are removed: `IP_EXCLUSIONS.md`); brake lights come on when a car brakes.
- People: 20 citizen models x 3 outfits walking on the sidewalks (walk cycle at the exact ground speed) and standing at crosswalks waiting for the walk signal; random gait phases.
- Traffic behaviour (visible in the clip and in the probe's `stopped` count): platoons released by the lights, queues at red, left turns waiting for a gap, cars stopping short of a full junction exit.

## Known problems seen in these captures (not hidden)

1. **Signal heads are not driven.** P1's traffic-light props keep whatever state they were built with; the cars and pedestrians obey the 40 s phase of `props.js` on their own clock.
2. **People and cars ignore the props and each other across kinds.** Walkers pass through P1's street furniture (benches, trash cans, planter boxes in the S1 still, left sidewalk) and through each other's lanes at corners; cars do not yield to people on crosswalks and do not react to the hero.
3. **Identical looks** (same mesh AND outfit) were 0 in every probe report of these runs, but the assignment only avoids them among on-screen walkers at the moment of assignment / re-assignment (farther walker of a pair, >= 30 m), so a brief twin pair can appear. The mesh alone repeats often: only 20 citizen meshes exist; the outfit variants are recolours of the same atlas tiles (hue-shifted clothes, some hi-vis vests turn green / purple).
4. **Foot planting** is by construction (ground speed = animation speed) and measured with the ankle bone only: per-walker median stance displacement 12-21 cm at 4K (heel-to-toe roll is ~20-25 cm), 2-4 % of individual stances travel more than 45 cm (turns at corners, speed changes at crosswalks). No toe bone, so a sole-level slide is not measured.
5. **Vehicle interiors** (driver and passengers) are photographic cards seen through dark glass; the wheels do not rotate (the browser models have static wheels).
6. **Region only**: the Midtown 3x3 block (x -262..514 m, z -512..256 m); cars appear at and disappear into the region edges; Broadway has 2 short links in the region; no water, no boats, no pigeons / fauna yet.
7. **Cost / ray tracing**: the vehicle instances and the walkers are invisible to ray tracing (that setting made the first build cost +14 ms GPU), so they do not appear in Lumen reflections or GI. See `PERF_TABLE.md`.
8. **Camera in the road**: the P1 S1 camera stands in a traffic lane, so cars pass through the camera position now and then (a car may fill the frame, as in the S1 stills).

## Counting method

See the header of `SPEC_TABLE.md`. The probe is not a detector: it counts what is on screen at the stated pixel size and not blocked by city geometry.
