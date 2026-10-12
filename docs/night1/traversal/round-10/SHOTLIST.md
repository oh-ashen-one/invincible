# Traversal (P3) — round 10 shot list

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. Nothing here is meant to infringe.

- Build: branch `night1/traversal`, commit `9bfd962`, UE 5.8.3, map `/Game/Maps/Manhattan` (golden preset; the integrated lit city built in this worktree by `unreal/WebHomage/Scripts/build_manhattan.py`; hero = the `/Game/Traversal/HeroDev` dev proxy).
- Reproduce: `docs/night1/traversal/capture_round.sh <round dir>` (runs `unreal/WebHomage/Scripts/run_game.sh`, real `-game`, offscreen).
- Game mode `AWebTravGameMode` -> pawn `AWebTravCharacter`. Hero: the browser build's GLB (`public/assets/spiderman.glb`, 58 bones, 79 clips at 30 fps) imported by `build_traversal.py` into `/Game/Traversal/HeroDev` (dev proxy), animated by the C++ `UWebTravAnimInstance` (clip nodes with the browser's per-transition blend times, 3-way swing blend by arc phase, web-hand arm aimed at the anchor, air-phase clip timelines that differ from the previous cycle, procedural roll/pitch sway in the air, whole-body trick spins). Tricks happen only when the trick input is pressed. Web strands = chain of thin cylinders.
- Round 06 wall-run: body up along the wall, chest toward it, torso leaned back 0.16 rad; the hero's sprint clip plays at 1.8-2.6 steps/s mapped from wall speed 6-14 m/s. Top-out: air sub-state `topOut` playing the `releaseFlip` clip, then the `landTopOut` landing (`perchLand` clip, 0.62 s) before idle. Hero textures are forced resident; `capture_round.sh` renders an unrecorded warm-up pass, then runs each sequence with a 0.8 s pre-roll (`-WHTravPreroll`: start pose rendered, simulation not stepped, camera state restored) that is cut from the video; video and still times are sequence times.
- Round 07 swings: virtual-pivot pendulum with a rope of 30-34 m (random per swing), at least 14 m + 0-5 m (random) below the entry height, pivot at most 30 m ahead. A web release keeps at most 8 m/s of upward speed (16 m/s within 12 m of the floor); the rest is added to forward speed. With the swing button held, the next anchor is searched 0.22 s after a release; a web found while rising faster than 5 m/s is attached (strand drawn) at once and its pendulum starts when the upward speed drops to 5 m/s or after 0.5 s. While a web is held, the hips are rotated so the hips->head line points at the anchor (weight 1.0 at the bottom of the arc, 0.6 at the ends). Scripts a and d: auto-chain rule (release after the swing has descended, at swing phase 0.7 while rising or at the forward apex; re-press 0.15 s after release; trick on every 3rd release), baked to plain keys. Script b: release + trick at 3.0 s (round 06: 3.2 s).
- Round 08 canyon keeping: 8 horizontal rays (every 0.05 s) find the facades beside the travel direction (wall normal within 60 deg of perpendicular to it); along each wall's normal the approach speed is limited to 2.5 m/s per metre above 3.5 m, and between two opposite walls the velocity along the normal is steered (rate 2.5 /s) toward 1.2 /s per metre off the centre line (<= 8 m/s). Active while swinging and in the air after a release. Web strands: 1.2 cm wide (at least ~1.2 px), grey, no emissive. Motion blur: amount 0.35 x smoothstep(speed, 28, 50 m/s) (diving x 1.3), none on foot / walls; max 1-3 %.
- Round 09: the arc depth alternates (odd swings 10.2 m, even swings 17.5 m below the entry, + 0-1.5 m; a high anchor lowers the virtual pivot instead). The anchor search heading is turned 30 deg toward the side opposite the previous web (the swing plane keeps the travel heading). While swinging, the canyon spring's target line sits 0.45 x the active anchor's offset from the centre (<= 6 m); in the air no centring inside +/-8 m. Pivot keeps 25 % of the anchor's side offset (was 10 %). Web: 1.6 cm (>= ~2 px), dark grey (0.09). Hero skeletal mesh: per-bone motion blur off. Perch / top-out landings start the perchLand clip at 0.22 s (its impact crouch). Dive: fast-fall / calm-fall blend oscillating with a 0.8 s period, plus the air sway. Scripts a and d re-baked from the same rule.
- Round 10 (Manhattan): a *sky launch* is a jump-release with a trick buffered; the launch speed is solved so the apex lands 3 m over the lower street wall's roofline ahead (peak clamped 38-58 m over the street, climb gravity x1.4, hang x0.55 under 7 m/s), followed by a long web (<= 50 m rope) built to bottom 5-9 m over the street; no web is searched on the way up. Script rule: a release is a sky launch when >= `skyEvery` releases have passed and the lower wall ahead is reachable (or 5.5 s after the last one); plain releases at phase 0.55; any swing is let go 1.25-1.55 s in, a stale swing after 2.4 s. While swinging, touching a wide facade with the stick held into it lets go of the web and wall-runs up it. A new web never anchors below 3 m over the body or behind it. Hero mesh / clip paths are data (`HeroMeshPath`, `HeroClipRoot`, ...).

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

Pixel check: `PX_CHECK.txt` (`docs/night1/traversal/px_check.py`) — hero height in pixels at 1080p from a depth scene capture that renders only the hero meshes from the rendered camera (480x270 capture scaled to 1920x1080), and the web anchor projected through the engine's rendered camera at each attach.

Animation check (T-pose / no-clip frames; air silhouettes sampled at 6 fps, pose signature = head / hands / feet relative to the hips in camera right / up; consecutive air cycles compared by node sequence): `ANIM_CHECK.txt` (`docs/night1/traversal/anim_check.py`).

Per-frame camera / framing check (hero screen bbox height and centre-Y, in-frame flag, camera-hero distance, camera-in-geometry flag, camera pitch / height; min / max per sequence and hero screen travel per swing): `CAM_CHECK.txt` (`docs/night1/traversal/cam_check.py`).

Inputs are replayed from JSON (`docs/night1/traversal/scripts/city/`, `-WHTravScript=`), sampled once per frame and fed to the same code path as the keyboard / pad. `heading` = the stick is set every frame to the world direction given (yaw deg), expressed relative to the current camera. Sequences a and d (round 10) run the `autoChain` rule live (rule-form keys in the JSON: release / re-press / sky-launch timing decided in the game tick from the physical state, seed 1234; the fixed 1/60 s replay is deterministic); b and c are hand-timed keys.

TRAVERSAL-SPEC check: `SPEC_CHECK.txt` — `docs/night1/traversal/spec_cam_check.py` (lines T8-T14, T16, T19 from the telemetry: hero pixel box, the rendered camera's pitch / yaw / roll / horizontal FOV, occlusion) and the spec's own instruments run on the 1080p videos: `vp_cam.py` (roll / pitch / yaw / FOV from vanishing points) and `nearflow.py 8` (near-field coverage by optical flow; CSVs in `spec/`).

Facade check: `FACADE_CHECK.txt` (`docs/night1/traversal/facade_check.py`) — per frame of the rendered video, from a full-scene depth capture (480x270, same camera as the view, web strands hidden) and the hero-only depth capture: share of the frame covered by non-hero surfaces closer than 6 m to the camera, and share of the hero's pixels with geometry more than 0.3 m in front of him; plus hero / camera horizontal distance to the nearest building box of the layout.

Swing cadence check: `CADENCE_CHECK.txt` (`docs/night1/traversal/cadence_check.py`) — over the first 12 s: web attaches, attach -> release time per swing, release -> next web stuck (web-less) time, drop per swing, frames with a web stuck and the hero inside the frame, body axis (hips -> head) vs the web (hips -> anchor) at each swing's low point.

Wall-run check: `WALL_CHECK.txt` (`docs/night1/traversal/wall_check.py`) — on 6 fps samples of the wall-run: number of distinct hand / foot height arrangements relative to the hips (distinct = more than 0.12 m apart), head above the hips (world up), foot L/R height crossings per second, hero pixel box fully inside the frame from the wall-run start to the end of the top-out landing, camera pitch / height below the hero / distance on the wall.

Swing arc test output (per swing: height at the preceding release, low point, drop, rope length, duration, horizon travel on screen): `DROP_TEST.txt` (generated by `docs/night1/traversal/drop_test.py` from the telemetry CSVs of the videos).

Telemetry CSV columns (one row per rendered frame): frame, t, mode, sub, body position x/y/z (m, UE axes), velocity, speed, horizontal speed, height above the floor below, swing anchor x/y/z, rope length, web tension 0..1, momentum-chain level, trick, zip target present + position, camera position / yaw / pitch / vertical FOV / distance, motion-blur factor, input state; round 06 adds head_hip_dz (head minus hips height, m) and limb_z (hand L, hand R, foot L, foot R height minus hips, m); round 07 adds body_rope_deg (hips->head vs hips->anchor, deg, while swinging; -1 otherwise) and web_on (a web strand stuck); round 08 adds wall_frac and hero_occl (see the facade check); round 09 adds hero_cx (projected bone box centre x) and pcm_roll.

## a_swing_chain — Swing chain up the avenue at speed (lit Manhattan map, golden)

Airborne start 24 m over the north-south avenue (x 250 m) with 22 m/s forward velocity heading north (-Y); scripted swing chain (autoChain rule: release on the rising front, re-press after 0.8 s; a sky launch = jump-release + trick where the lower street wall ahead is within reach, at most every 2nd release).

Files: `a_swing_chain.mp4`, `a_swing_chain_telemetry.csv`, `stills/a_swing_chain_00_t001.0.jpg`, `stills/a_swing_chain_01_t002.6.jpg`, `stills/a_swing_chain_02_t003.4.jpg`, `stills/a_swing_chain_03_t005.9.jpg`, `stills/a_swing_chain_04_t009.5.jpg`

Spawn: position [250, 240, 24] m, yaw -90 deg, camera pitch 0.12 rad, initial velocity [0, -22, 0] m/s. Script: `scripts/city/a_swing_chain.json`.

| t (s) | input change |
|---|---|
| 0.000 | stick (x right, y fwd) = [0, 1], heading (world yaw deg) = -90, RMB swing up |
| 0.400 | autoChain down, releasePhase = 0.55, gap = 0.8, repressVz = 99.0, trickEvery = 0, skyEvery = 2, skyTricks = 2, skyRepressH = 30, skyPhase = 0.8, skyMax = 2.8 |

Measured over the video (935 frames, 15.57 s): speed 22.0-57.7 m/s; height above the floor 3.2-50.1 m; Y (north = -Y) travelled -494 m; vertical FOV 58.0-81.5 deg; camera distance 3.5-4.9 m; max momentum-chain level 1; tricks: corkscrew, layout, scissor, tuckFlip.

State sequence (mode/sub-state, start time s): air 0.00 -> swing 0.40 -> air/trick 1.67 -> air 2.37 -> air/trick 2.38 -> air 3.68 -> air/dive 4.00 -> swing 4.53 -> air/release 5.97 -> air 6.37 -> swing 6.77 -> air/trick 7.93 -> air 8.72 -> air/trick 8.73 -> air 9.43 -> air/dive 10.03 -> swing 10.60 -> air/release 12.17 -> air 12.57 -> swing 12.97 -> air/trick 14.28 -> air 15.18 -> air/trick 15.20

## b_release_trick_dive_zip — Release + trick + dive + zip to a rooftop

Airborne start 30 m over the avenue (26 m/s north), one swing, jump-release with a trick (sky launch), second trick at the top, dive, web-zip to a roof point, perch.

Files: `b_release_trick_dive_zip.mp4`, `b_release_trick_dive_zip_telemetry.csv`, `stills/b_release_trick_dive_zip_00_t000.8.jpg`, `stills/b_release_trick_dive_zip_01_t001.9.jpg`, `stills/b_release_trick_dive_zip_02_t002.5.jpg`, `stills/b_release_trick_dive_zip_03_t004.4.jpg`, `stills/b_release_trick_dive_zip_04_t005.8.jpg`

Spawn: position [250, 170, 30] m, yaw -90 deg, camera pitch 0.12 rad, initial velocity [0, -26, 0] m/s. Script: `scripts/city/b_release_trick_dive_zip.json`.

| t (s) | input change |
|---|---|
| 0.000 | stick (x right, y fwd) = [0, 1], heading (world yaw deg) = -90, RMB swing down |
| 1.400 | Space down, F trick down |
| 1.420 | RMB swing up, Space up, F trick up |
| 2.300 | F trick down |
| 2.320 | F trick up |
| 3.300 | C drop/dive down |
| 3.900 | C drop/dive up |
| 4.000 | E zip down, stick (x right, y fwd) = [0, 0], heading off |
| 4.100 | E zip up |

Measured over the video (419 frames, 6.97 s): speed 0.0-60.0 m/s; height above the floor 0.7-59.9 m; Y (north = -Y) travelled -122 m; vertical FOV 58.0-71.9 deg; camera distance 3.5-7.5 m; max momentum-chain level 0; tricks: layout, scissor.

State sequence (mode/sub-state, start time s): swing 0.00 -> air/trick 1.40 -> air 2.10 -> air/trick 2.30 -> air/dive 3.60 -> zip 4.00 -> zip/zipFlight 4.07 -> zip 4.82 -> perch/perchLand 5.08 -> perch 5.58

## c_wallrun_perch — Swing into a facade -> wall-run up -> perch

Airborne swing start 22 m over the avenue, the stick turns east into the 45 m loft facade (x 266 m), swing let go at 1.7 s, wall-run up, top-out onto the roof, camera turn, web-zip to the roof edge over the avenue, perch.

Files: `c_wallrun_perch.mp4`, `c_wallrun_perch_telemetry.csv`, `stills/c_wallrun_perch_00_t001.0.jpg`, `stills/c_wallrun_perch_01_t002.6.jpg`, `stills/c_wallrun_perch_02_t003.6.jpg`, `stills/c_wallrun_perch_03_t004.9.jpg`, `stills/c_wallrun_perch_04_t009.8.jpg`

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

## d_sprint_jump_first_swing — Ground sprint -> jump -> first swing

Street start on the avenue; run north, charged jump, first swing, then the round-10 chain rule (as a).

Files: `d_sprint_jump_first_swing.mp4`, `d_sprint_jump_first_swing_telemetry.csv`, `stills/d_sprint_jump_first_swing_00_t002.3.jpg`, `stills/d_sprint_jump_first_swing_01_t005.6.jpg`, `stills/d_sprint_jump_first_swing_02_t007.6.jpg`, `stills/d_sprint_jump_first_swing_03_t011.8.jpg`

Spawn: position [250, 244, 0.95] m, yaw -90 deg, camera pitch 0.14 rad. Script: `scripts/city/d_sprint_jump_first_swing.json`.

| t (s) | input change |
|---|---|
| 0.000 | stick (x right, y fwd) = [0, 1], heading (world yaw deg) = -90, Shift down |
| 1.800 | Space down |
| 2.200 | Space up |
| 2.600 | RMB swing down, autoChain down, releasePhase = 0.55, gap = 0.8, repressVz = 99.0, trickEvery = 0, skyEvery = 2, skyTricks = 2, skyRepressH = 30, skyPhase = 0.8, skyMax = 2.8 |

Measured over the video (719 frames, 11.97 s): speed 0.6-56.3 m/s; height above the floor 0.2-39.1 m; Y (north = -Y) travelled -293 m; vertical FOV 58.0-77.4 deg; camera distance 3.9-4.9 m; max momentum-chain level 1; tricks: corkscrew, layout, scissor, tuckFlip.

State sequence (mode/sub-state, start time s): ground 0.00 -> air/jumpLaunch 2.20 -> air 2.37 -> swing 2.68 -> air/release 3.95 -> air/trick 4.00 -> air 4.78 -> air/trick 4.80 -> air 5.70 -> air/dive 6.17 -> swing 6.48 -> air/release 7.87 -> air 8.27 -> swing 8.67 -> air/trick 10.10 -> air 11.40 -> air/trick 11.42

