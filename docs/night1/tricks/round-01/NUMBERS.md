# Tricks (C) — round 01 measured numbers

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Source: `t60_trick_reel_telemetry.csv` (3629 rows, 60 Hz, stitched by window: `tools/tricks/stitch_telemetry.py`, 0 rows differ from the
last window's run in position / flip state) and `t60_trick_reel_pose.csv.gz`, measured with `tools/tricks/tricks_check.py` (full output:
`CHECK.txt`). Reel: 1920x1080 native internal (r.ScreenPercentage 100), 60 fps, 3629 frames, 60.48 s, 13.5 MB. Build: night1/tricks after
merging Opus-5.5-Loop-Night-1 2e812770; the rendered run's telemetry equals the `-nullrhi` probe row for row (positions / flip state).

| Line | Target | Measured | |
|---|---|---|---|
| P | >= 10 distinct programs in one 60 s clip | 12 programs, 22 instances, route airborne / swinging for all 60 s (0 ground, wall or landing rows) | PASS |
| V1 | same-type pairs differ >= 40 deg/s in a 0.1 s sample | 10 pairs; smallest max difference 141 deg/s (program rate), 199 deg/s (rendered body axis) | PASS |
| V2 | durations vary 10-20 % (some < 0.90, some > 1.10, none beyond +-22 %) | flip_scale 0.850-1.131; 12 of 22 instances deviate >= 10 % | PASS |
| K | wrists <= .15 m from the shins, knees <= .25 m apart, held >= .25 s | 9 tuck holds >= .25 s, each with >= .25 s inside both limits (longest 1.28 s); knee gap max .197 m; wrist-shin max inside a hold .295 m (outside the tight part) | PASS |
| L | 0 slow-limb samples | 4 of 345: 28.50 s corkscrew straddle .094 m, 38.20 s frontSingle reach .074 m, 54.10 s frontPikeSwan swan .085 m, 57.60 s backDouble kick-out .097 m | FAIL |
| G1 | layout hip and knee >= 170 deg | 6 held layouts; lowest median hip 177.6, knee 176.4 deg (single-row minimum hip 156.9 / knee 138.3 at layout edges) | PASS (median rule) |
| G2 | toes pointed in >= 90 % of trick samples | 99.9 % of 4378 foot samples within 35 deg of the shin line | PASS |
| G3 | head spots the landing (>= 15 deg) in >= 12 of 13 | 22 of 22; smallest open-out head change 24.4 deg | PASS |
| G4 | open-out <= 300 deg/s over the last 0.15 s in >= 12 of 13 | 22 of 22 open; highest rate 124 deg/s | PASS |
| A/B | flips >= 8 vs the owner clip | blind critic (pack in _scratch, not committed) | — |
| R | no traversal axis below merged r26; traversal code untouched | `git diff origin/Opus-5.5-Loop-Night-1 -- unreal/` = WebTravFlips.{h,cpp} only; axes: blind critic | — |

Changes this round (resume): per-program tempo alternation (a repeat is always the other performance: V1), reach / kick-out legs march a
quarter cycle apart with even foot-height steps, windmill right arm in the swan, pencil tuck-up, twist arm drive, reach / kick-out
back-and-forth past the program end (L), dump-window world-render skip (`-WHTrickWarm`).
