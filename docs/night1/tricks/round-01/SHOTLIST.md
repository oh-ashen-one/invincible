# Tricks (C) — round 01 shot list

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. Nothing here is meant to infringe.

| Clip | What | How |
|---|---|---|
| `t60_trick_reel.mp4` | ONE continuous 60.5 s web-swing chain in the lit city with a flip program on every release; the 12 release programs are cycled (the second lap repeats them, so same-type instances can be compared). Route: the y -560 edge street east (sun behind), turn south into 5th Av (x 250) at 12.63 s, heading 92 from 28 s; south of y ~256 the city is the low-detail facade layer | script `docs/night1/tricks/scripts/t60_trick_reel.json`, `tools/tricks/capture.sh` (windows, below), route verified by a `-nullrhi` probe of the same build (`tools/tricks/probe_reel.py`) |
| `t60_trick_reel_telemetry.csv` | per-frame traversal telemetry of the run (60 Hz, every row) — `flip_prog`, `flip_t`, `flip_scale`, `flip_rate_dps`, `flip_shape(_legs)`, `body_pitch_deg`, `tuck_*`, `limb_z`, `px_*` | WebTravCharacter (`-WHShotDir`); rows of window k taken from window k's run (pixel columns valid everywhere), `tools/tricks/stitch_telemetry.py` |
| `t60_trick_reel_pose.csv.gz` | rendered bone positions per frame (`-WHTrickPose`), joined to the telemetry by position | WebTravFlips.cpp |
| `CHECK.txt` | `tools/tricks/tricks_check.py` output on the two CSVs above (every SPEC line) + ffprobe of the mp4 | |
| `NUMBERS.md` | the SPEC lines with the measured numbers | |
| `shapes_ours.jpg` | our held shapes (tuck, pike, layout, twist, straddle, pencil, kick-out, reach) from different programs, cropped around the hero (`tools/tricks/ab_sheet.py --ours-only`) | |

## Capture settings

| | |
|---|---|
| output | 1920x1080, 60 fps, H.264 mp4 (<= 15 MB) |
| internal resolution | 1920x1080 (`r.ScreenPercentage 100`, native) |
| time step | fixed 1/60 s (`-benchmark -fps=60 -dumpmovie`), offscreen `-game` (`Scripts/run_game.sh`), 0.8 s pre-roll cut |
| AA / GI | TSR, Lumen (project defaults), map `/Game/Maps/Manhattan` (golden) rebuilt in this worktree after merging integration (traversal r26, characters r17, terrain r05, city r11) by `build_manhattan.py` |
| GPU | every run under `gpu_slot.sh capture` (background priority) on a GPU shared with other sessions: no perf claim |

**Rendered in 4 windows of one deterministic run** (0-15, 15-30, 30-45, 45-60.5 s): each window is a full engine run of the same
script that writes movie frames only inside its window (`-WHTrickDumpFrom/To`) and skips world rendering before `From - 4 s`
(`-WHTrickWarm=4`: simulation, animation and telemetry unchanged; 4 s of rendered frames settle streaming, Lumen and TSR history
before the first kept frame). `capture.sh` stitches the windows by sequence frame and prints a determinism line (telemetry of every
window's run compared row by row: position and flip state). A window boundary can show a small lighting / TSR-history difference.
