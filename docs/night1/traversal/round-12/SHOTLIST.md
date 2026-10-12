# Traversal (P3) — round 12 shot list

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. Nothing here is meant to infringe.

- Build: branch `night1/traversal`, commit `ff0eb47+`, UE 5.8.3, map `/Game/Maps/Manhattan` (golden preset; the integrated lit city built in this worktree by `unreal/WebHomage/Scripts/build_manhattan.py`; hero = the `/Game/Traversal/HeroDev` dev proxy).
- Reproduce: `docs/night1/traversal/capture_round.sh <round dir>` (runs `unreal/WebHomage/Scripts/run_game.sh`, real `-game`, offscreen).
- Game mode `AWebTravGameMode` -> pawn `AWebTravCharacter`. Hero: the browser build's GLB (`public/assets/spiderman.glb`, 58 bones, 79 clips at 30 fps) imported by `build_traversal.py` into `/Game/Traversal/HeroDev` (dev proxy), animated by the C++ `UWebTravAnimInstance` (clip nodes with the browser's per-transition blend times, 3-way swing blend by arc phase, web-hand arm aimed at the anchor, air-phase clip timelines that differ from the previous cycle, procedural roll/pitch sway in the air, whole-body trick spins). Tricks happen only when the trick input is pressed. Web strands = chain of thin cylinders.
- Round 06 wall-run: body up along the wall, chest toward it, torso leaned back 0.16 rad; the hero's sprint clip plays at 1.8-2.6 steps/s mapped from wall speed 6-14 m/s. Top-out: air sub-state `topOut` playing the `releaseFlip` clip, then the `landTopOut` landing (`perchLand` clip, 0.62 s) before idle. Hero textures are forced resident; `capture_round.sh` renders an unrecorded warm-up pass, then runs each sequence with a 0.8 s pre-roll (`-WHTravPreroll`: start pose rendered, simulation not stepped, camera state restored) that is cut from the video; video and still times are sequence times.
- Round 07 swings: virtual-pivot pendulum with a rope of 30-34 m (random per swing), at least 14 m + 0-5 m (random) below the entry height, pivot at most 30 m ahead. A web release keeps at most 8 m/s of upward speed (16 m/s within 12 m of the floor); the rest is added to forward speed. With the swing button held, the next anchor is searched 0.22 s after a release; a web found while rising faster than 5 m/s is attached (strand drawn) at once and its pendulum starts when the upward speed drops to 5 m/s or after 0.5 s. While a web is held, the hips are rotated so the hips->head line points at the anchor (weight 1.0 at the bottom of the arc, 0.6 at the ends). Scripts a and d: auto-chain rule (release after the swing has descended, at swing phase 0.7 while rising or at the forward apex; re-press 0.15 s after release; trick on every 3rd release), baked to plain keys. Script b: release + trick at 3.0 s (round 06: 3.2 s).
- Round 08 canyon keeping: 8 horizontal rays (every 0.05 s) find the facades beside the travel direction (wall normal within 60 deg of perpendicular to it); along each wall's normal the approach speed is limited to 2.5 m/s per metre above 3.5 m, and between two opposite walls the velocity along the normal is steered (rate 2.5 /s) toward 1.2 /s per metre off the centre line (<= 8 m/s). Active while swinging and in the air after a release. Web strands: 1.2 cm wide (at least ~1.2 px), grey, no emissive. Motion blur: amount 0.35 x smoothstep(speed, 28, 50 m/s) (diving x 1.3), none on foot / walls; max 1-3 %.
- Round 09: the arc depth alternates (odd swings 10.2 m, even swings 17.5 m below the entry, + 0-1.5 m; a high anchor lowers the virtual pivot instead). The anchor search heading is turned 30 deg toward the side opposite the previous web (the swing plane keeps the travel heading). While swinging, the canyon spring's target line sits 0.45 x the active anchor's offset from the centre (<= 6 m); in the air no centring inside +/-8 m. Pivot keeps 25 % of the anchor's side offset (was 10 %). Web: 1.6 cm (>= ~2 px), dark grey (0.09). Hero skeletal mesh: per-bone motion blur off. Perch / top-out landings start the perchLand clip at 0.22 s (its impact crouch). Dive: fast-fall / calm-fall blend oscillating with a 0.8 s period, plus the air sway. Scripts a and d re-baked from the same rule.
- Round 10 (Manhattan): a *sky launch* is a jump-release with a trick buffered; the launch speed is solved so the apex lands 3 m over the lower street wall's roofline ahead (peak clamped 38-58 m over the street, climb gravity x1.4, hang x0.55 under 7 m/s), followed by a long web (<= 50 m rope) built to bottom 5-9 m over the street; no web is searched on the way up. Script rule: a release is a sky launch when >= `skyEvery` releases have passed and the lower wall ahead is reachable (or 5.5 s after the last one); plain releases at phase 0.55; any swing is let go 1.25-1.55 s in, a stale swing after 2.4 s. While swinging, touching a wide facade with the stick held into it lets go of the web and wall-runs up it. A new web never anchors below 3 m over the body or behind it. Hero mesh / clip paths are data (`HeroMeshPath`, `HeroClipRoot`, ...).
- Round 11 flips: a trick is a *flip program* = a timeline of held shapes (tuck, pike, layout, swan, pencil, straddle, throne, twist, reach) keyed in Blender on the hero rig (`docs/night1/traversal/blender/`); body rotation about the body centre follows one angular momentum per program with per-shape effective inertia (tuck 1 .. pencil / throne 9), solved to end upright; twist segments turn about the long axis; the upper body samples the timeline 0.04 s ahead and the legs 0.07 s behind; a cut program springs back to the body frame in ~0.07 s. The next web is searched only in the program's final reach (held up to 0.2 s). Wall-run top-out = program wallFront. Flip camera: orbit 40 deg off the travel axis toward the side with more space, 1.6 m under the hero, framing 0.42, look-up <= 18 deg.
- Round 12 (critic r11: tricks low in the canyon, facades behind the hero): a trick pressed at a web release is a sky launch; its speed is solved so the apex sits 6 m over the tallest roof within 30 m of the stretch of path the flip will cover (down-ray grid), peak <= 90 m over the street, launch <= 60 m/s; the program is armed on the climb, starts when the climb slows to 9 m/s and plays at 0.32 g (it stays over the roofs). The chain rule only launches where that apex is reachable. Flip camera: every 0.15 s it scores orbit yaw offsets (-120..120 deg from behind) x look-up elevations (30-60 deg, camera below the hero) by the share of 16 rays around the hero (the hero box + 40 px at 1080p) that reach open sky within 900 m, preferring a 3/4 side view (55 deg) and the lowest clear look-up; springs 0.3 s, 3.4 m from the hero. backDouble = tuck 0.55 / layout 0.5 / tuck 0.55 / layout 0.5 / reach 0.2 s.

## Capture settings (all sequences)

| | video | stills |
|---|---|---|
| output | 1920x1080, 60 fps, H.264 mp4 | 3840x2160, JPEG q92 (converted from PNG) |
| internal resolution | 1920x1080 (`r.ScreenPercentage 100`) | 3840x2160 (`r.ScreenPercentage 100`) |
| time step | fixed 1/60 s (`-benchmark -fps=60 -dumpmovie`) | fixed 1/60 s (`-benchmark -fps=60`) |
| AA / GI | TSR, Lumen (project defaults) | same |

The video frames are rendered offline at a fixed step; they say nothing about real-time frame rate.

Camera (round 05 chase camera): 3.8 m behind the hero along the lagged heading yaw (horizontal spring 0.07 s, held 3.5-5.0 m), 1.1 m above his centre (vertical spring 0.05 s, held 0.7-1.8 m), 0.3 m shoulder offset; yaw toward the hero; pitch places the hero at screen height 0.48 (arc bottom) .. 0.40 (arc ends), clamped 5-22 deg down. At each web attach (first 0.5 s) the view pitches up and, if needed, turns and widens (<= 26 deg of extra vertical FOV) so the anchor on the facade is inside the frame with the hero. Collision: sphere sweeps + clear-orbit search (see round 03). Vertical FOV 58 + 13 x smoothstep(speed, 12, 44 m/s) + 5 diving + kick / punch springs; vertical FOV converted to Unreal's horizontal FOV with the viewport aspect.

Round 06 camera changes: on a wall (and while rising in the top-out) the camera blends (spring 0.16 s in, 0.22 s out) to a position 2.2 m below the hero's centre and 2.2 m out from the wall (at least 0.6 m over the street; further out when the street clamps it, keeping 3.2 m to the hero), yaw facing the wall, pitch up so the hero's centre sits at 0.68 of the frame height, vertical FOV +4 deg. Chase pitch may exceed 22 deg down when collision lifts the camera, so the hero's centre stays at or above 0.62 of the frame height. Script c: the camera-turn key looks up (pitch-down rate -10 deg/s) instead of down (+4).

Round 07 camera changes: height over the hero 1.8 m (held 1.2-2.6 m; round 05-06: 1.1 m, 0.7-1.8 m), look-down at least 10 deg (was 5). The attach look-up toward the anchor is scaled by 1 - (fall speed - 8) / 14 (clamped 0..1) and keeps the hero 12 deg inside the bottom edge (was 8); the attach yaw turn is capped at 25 deg with a 0.12 s spring (was 0.035 s). 0.4 m closer while swinging / airborne.

Round 08 camera change: sideways facade clearance measured from the camera along its right / left: a 0.15 s spring toward 3 m and a hard 1.5 m minimum, moved only as far as the line of sight to the hero stays clear.

Round 09 camera changes: height over the hero 0.6 m (held 0.2-1.8 m), look-down floor -8 deg (looking up allowed), framing target 0.44 (arc bottom) .. 0.37 (arc ends); attach FOV widening <= 10 deg (round 08). During a swing chain the camera position slides 1.3 m toward the side of the active anchor (0.3 s spring; off after 0.8 s without a web, in a dive, and outside chains) and still turns toward the hero; roll toward that side up to 6 deg, weighted by smoothstep(|rope angle|, 0.55, 1.0) rad.

Round 10 camera changes: the attach look-up stops where the hero centre reaches 0.64 of the frame height; attach springs 0.035 -> 0.12 s; the first composed frame starts at its framing / attach targets (no pop at t = 0); arc-bottom framing target 0.44 -> 0.50 (hero centre-Y spread); roll: yaw-rate lean 0.03 (cap 4 deg), bank 0.04, leans under 1 deg dropped. Sky launch: the camera sinks 1.2 m under the hero and frames him at 0.40, looking up <= 10 deg.

Inputs are replayed from JSON (`docs/night1/traversal/scripts/city/`, `-WHTravScript=`), sampled once per frame and fed to the same code path as the keyboard / pad. `heading` = the stick is set every frame to the world direction given (yaw deg), expressed relative to the current camera. Sequences a and d (round 10) run the `autoChain` rule live (rule-form keys in the JSON: release / re-press / sky-launch timing decided in the game tick from the physical state, seed 1234; the fixed 1/60 s replay is deterministic); b and c are hand-timed keys.

Telemetry CSV columns (one row per rendered frame): frame, t, mode, sub, body position x/y/z (m, UE axes), velocity, speed, horizontal speed, height above the floor below, swing anchor x/y/z, rope length, web tension 0..1, momentum-chain level, trick, zip target present + position, camera position / yaw / pitch / vertical FOV / distance, motion-blur factor, input state; round 06 adds head_hip_dz (head minus hips height, m) and limb_z (hand L, hand R, foot L, foot R height minus hips, m); round 07 adds body_rope_deg (hips->head vs hips->anchor, deg, while swinging; -1 otherwise) and web_on (a web strand stuck); round 08 adds wall_frac and hero_occl (see the facade check); round 09 adds hero_cx (projected bone box centre x) and pcm_roll.

## c_wallrun_perch — Swing into a facade -> wall-run up -> perch

Airborne swing start 22 m over the avenue, the stick turns east into the 45 m loft facade (x 266 m), swing let go at 1.7 s, wall-run up, top-out onto the roof, camera turn, web-zip to the roof edge over the avenue, perch.

Files: `c_wallrun_perch.mp4`, `c_wallrun_perch_telemetry.csv`

Spawn: position [250, 240, 22] m, yaw -90 deg, camera pitch 0.12 rad, initial velocity [0, -22, 0] m/s. Script: `scripts/city/c_wallrun_perch.json`.

| t (s) | input change |
|---|---|
| 0.000 | stick (x right, y fwd) = [0, 1], heading (world yaw deg) = -90, RMB swing down |
| 0.900 | heading (world yaw deg) = 0 |
| 1.700 | RMB swing up |
| 6.600 | stick (x right, y fwd) = [0, 0], heading off |
| 7.100 | look (deg/s yaw, pitch-down) = [-150.0, -10.0] |
| 8.300 | look (deg/s yaw, pitch-down) = [0, 0] |
| 8.500 | E zip down |
| 8.600 | E zip up |

Measured over the video (629 frames, 10.47 s): speed 0.0-60.1 m/s; height above the floor 0.4-61.8 m; Y (north = -Y) travelled -30 m; vertical FOV 58.0-66.9 deg; camera distance 2.7-7.7 m; max momentum-chain level 0; tricks: none.

State sequence (mode/sub-state, start time s): swing 0.00 -> air/release 1.70 -> wall/wallRun 2.08 -> air/topOut 3.85 -> land/landTopOut 4.77 -> ground 5.12 -> zip 8.50 -> zip/zipFlight 8.55 -> zip 8.83 -> perch/perchLand 9.12 -> perch 9.62

## f1_sky_backDouble — Round 12 flip: apex sky launch with the backDouble program over the rooftops, catch into the next swing

West avenue (x -250), airborne start 28 m over the street at y 170 heading south (24 m/s); chain rule from 0.4 s; a release is a sky launch only where the flip apex clears every roof within 30 m (skyEvery 1); program backDouble armed on the climb, starts at vz <= 9 m/s; web re-pressed in the program's final reach.

Files: `f1_sky_backDouble.mp4`, `f1_sky_backDouble_telemetry.csv`

Spawn: position [-250, 170, 28] m, yaw 90 deg, camera pitch 0.12 rad, initial velocity [0, 24, 0] m/s. Script: `scripts/city/f1_sky_backDouble.json`.

| t (s) | input change |
|---|---|
| 0.000 | stick (x right, y fwd) = [0, 1], heading (world yaw deg) = 90, RMB swing up, flip = backDouble |
| 0.400 | autoChain down, releasePhase = 0.55, gap = 0.8, repressVz = 99.0, trickEvery = 0, skyEvery = 1, skyTricks = 1, skyRepressH = 30, skyPhase = 0.8, skyMax = 2.8 |

Measured over the video (479 frames, 7.97 s): speed 24.0-57.1 m/s; height above the floor 8.1-78.1 m; Y (north = -Y) travelled 218 m; vertical FOV 58.0-83.2 deg; camera distance 2.7-4.9 m; max momentum-chain level 0; tricks: backDouble.

State sequence (mode/sub-state, start time s): air 0.00 -> swing 0.40 -> air/release 1.67 -> air 2.07 -> air/trick 3.35 -> air/dive 5.85 -> swing 6.97

## f2_sky_pikeSwan — Round 12 flip: apex sky launch with the frontPikeSwan program, catch into the next swing

As f1 from y 180, program frontPikeSwan.

Files: `f2_sky_pikeSwan.mp4`, `f2_sky_pikeSwan_telemetry.csv`

Spawn: position [-250, 180, 28] m, yaw 90 deg, camera pitch 0.12 rad, initial velocity [0, 24, 0] m/s. Script: `scripts/city/f2_sky_pikeSwan.json`.

| t (s) | input change |
|---|---|
| 0.000 | stick (x right, y fwd) = [0, 1], heading (world yaw deg) = 90, RMB swing up, flip = frontPikeSwan |
| 0.400 | autoChain down, releasePhase = 0.55, gap = 0.8, repressVz = 99.0, trickEvery = 0, skyEvery = 1, skyTricks = 1, skyRepressH = 30, skyPhase = 0.8, skyMax = 2.8 |

Measured over the video (479 frames, 7.97 s): speed 22.9-60.8 m/s; height above the floor 5.5-77.9 m; Y (north = -Y) travelled 200 m; vertical FOV 58.0-75.1 deg; camera distance 2.9-4.9 m; max momentum-chain level 0; tricks: frontPikeSwan.

State sequence (mode/sub-state, start time s): air 0.00 -> swing 0.40 -> air/release 1.67 -> air 2.07 -> air/trick 3.32 -> air/dive 5.50 -> swing 7.02

## f3_sky_corkscrew — Round 12 flip: apex sky launch with the corkscrew program, catch into the next swing

As f1 from y 190, program corkscrew.

Files: `f3_sky_corkscrew.mp4`, `f3_sky_corkscrew_telemetry.csv`

Spawn: position [-250, 190, 28] m, yaw 90 deg, camera pitch 0.12 rad, initial velocity [0, 24, 0] m/s. Script: `scripts/city/f3_sky_corkscrew.json`.

| t (s) | input change |
|---|---|
| 0.000 | stick (x right, y fwd) = [0, 1], heading (world yaw deg) = 90, RMB swing up, flip = corkscrew |
| 0.400 | autoChain down, releasePhase = 0.55, gap = 0.8, repressVz = 99.0, trickEvery = 0, skyEvery = 1, skyTricks = 1, skyRepressH = 30, skyPhase = 0.8, skyMax = 2.8 |

Measured over the video (479 frames, 7.97 s): speed 24.0-52.3 m/s; height above the floor 7.7-71.7 m; Y (north = -Y) travelled 221 m; vertical FOV 58.0-82.6 deg; camera distance 2.9-4.9 m; max momentum-chain level 0; tricks: corkscrew.

State sequence (mode/sub-state, start time s): air 0.00 -> swing 0.40 -> air/release 1.67 -> air 2.07 -> air/trick 3.22 -> air/dive 5.27 -> swing 6.33

## f4_chain_flips — Round 12 flips: 13 s swing chain; a flip on every release whose apex clears the roofs

West avenue from y 120 heading south, 24 m over the street; chain rule, skyEvery 1 (only where the apex clears the roofs), skyTricks 1; requested programs cycle backDouble, frontPikeSwan, corkscrew.

Files: `f4_chain_flips.mp4`, `f4_chain_flips_telemetry.csv`

Spawn: position [-250, 120, 24] m, yaw 90 deg, camera pitch 0.12 rad, initial velocity [0, 22, 0] m/s. Script: `scripts/city/f4_chain_flips.json`.

| t (s) | input change |
|---|---|
| 0.000 | stick (x right, y fwd) = [0, 1], heading (world yaw deg) = 90, RMB swing up, flip = backDouble,frontPikeSwan,corkscrew |
| 0.400 | autoChain down, releasePhase = 0.55, gap = 0.8, repressVz = 99.0, trickEvery = 0, skyEvery = 1, skyTricks = 1, skyRepressH = 30, skyPhase = 0.8, skyMax = 2.8 |

Measured over the video (779 frames, 12.97 s): speed 22.0-63.3 m/s; height above the floor 5.4-72.5 m; Y (north = -Y) travelled 421 m; vertical FOV 58.0-80.5 deg; camera distance 2.7-4.9 m; max momentum-chain level 1; tricks: backDouble.

State sequence (mode/sub-state, start time s): air 0.00 -> swing 0.40 -> air/release 1.67 -> air 2.07 -> swing 2.47 -> air/release 3.85 -> air 4.25 -> air/trick 5.70 -> air/dive 8.20 -> swing 8.25 -> air/release 9.75 -> air 10.15 -> swing 10.62 -> air/release 12.37 -> air 12.77

## f5_canyon_backDouble — Round 12 check: the round-11 f1 stretch of the Midtown avenue (no launch can clear its 140-250 m towers)

Avenue x 250 from y 170 heading north, same rule as f1: every release is checked, none can clear the roofs, so no sky launch and no flip.

Files: `f5_canyon_backDouble.mp4`, `f5_canyon_backDouble_telemetry.csv`

Spawn: position [250, 170, 30] m, yaw -90 deg, camera pitch 0.12 rad, initial velocity [0, -26, 0] m/s. Script: `scripts/city/f5_canyon_backDouble.json`.

| t (s) | input change |
|---|---|
| 0.000 | stick (x right, y fwd) = [0, 1], heading (world yaw deg) = -90, RMB swing up, flip = backDouble |
| 0.400 | autoChain down, releasePhase = 0.55, gap = 0.8, repressVz = 99.0, trickEvery = 0, skyEvery = 1, skyTricks = 1, skyRepressH = 30, skyPhase = 0.8, skyMax = 2.8 |

Measured over the video (479 frames, 7.97 s): speed 26.0-52.8 m/s; height above the floor 0.7-28.9 m; Y (north = -Y) travelled -287 m; vertical FOV 58.0-75.3 deg; camera distance 3.5-4.9 m; max momentum-chain level 3; tricks: none.

State sequence (mode/sub-state, start time s): air 0.00 -> swing 0.40 -> air/release 1.53 -> air 1.93 -> swing 2.33 -> air/release 3.72 -> air 4.12 -> swing 4.52 -> air/release 5.67 -> air 6.07 -> swing 6.47 -> air/release 7.77

