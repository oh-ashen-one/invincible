# Traversal (P3) — round 15 shot list

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. Nothing here is meant to infringe.

- Build: branch `night1/traversal`, commit `0c2934a`, UE 5.8.3, map `/Game/Maps/Manhattan` (golden preset; the integrated lit city built in this worktree by `unreal/WebHomage/Scripts/build_manhattan.py`; hero = the `/Game/Traversal/HeroDev` dev proxy).
- Reproduce: `docs/night1/traversal/capture_round.sh <round dir>` (runs `unreal/WebHomage/Scripts/run_game.sh`, real `-game`, offscreen).
- Game mode `AWebTravGameMode` -> pawn `AWebTravCharacter`. Hero: the browser build's GLB (`public/assets/spiderman.glb`, 58 bones, 79 clips at 30 fps) imported by `build_traversal.py` into `/Game/Traversal/HeroDev` (dev proxy), animated by the C++ `UWebTravAnimInstance` (clip nodes with the browser's per-transition blend times, 3-way swing blend by arc phase, web-hand arm aimed at the anchor, air-phase clip timelines that differ from the previous cycle, procedural roll/pitch sway in the air, whole-body trick spins). Tricks happen only when the trick input is pressed. Web strands = chain of thin cylinders.
- Round 06 wall-run: body up along the wall, chest toward it, torso leaned back 0.16 rad; the hero's sprint clip plays at 1.8-2.6 steps/s mapped from wall speed 6-14 m/s. Top-out: air sub-state `topOut` playing the `releaseFlip` clip, then the `landTopOut` landing (`perchLand` clip, 0.62 s) before idle. Hero textures are forced resident; `capture_round.sh` renders an unrecorded warm-up pass, then runs each sequence with a 0.8 s pre-roll (`-WHTravPreroll`: start pose rendered, simulation not stepped, camera state restored) that is cut from the video; video and still times are sequence times.
- Round 07 swings: virtual-pivot pendulum with a rope of 30-34 m (random per swing), at least 14 m + 0-5 m (random) below the entry height, pivot at most 30 m ahead. A web release keeps at most 8 m/s of upward speed (16 m/s within 12 m of the floor); the rest is added to forward speed. With the swing button held, the next anchor is searched 0.22 s after a release; a web found while rising faster than 5 m/s is attached (strand drawn) at once and its pendulum starts when the upward speed drops to 5 m/s or after 0.5 s. While a web is held, the hips are rotated so the hips->head line points at the anchor (weight 1.0 at the bottom of the arc, 0.6 at the ends). Scripts a and d: auto-chain rule (release after the swing has descended, at swing phase 0.7 while rising or at the forward apex; re-press 0.15 s after release; trick on every 3rd release), baked to plain keys. Script b: release + trick at 3.0 s (round 06: 3.2 s).
- Round 08 canyon keeping: 8 horizontal rays (every 0.05 s) find the facades beside the travel direction (wall normal within 60 deg of perpendicular to it); along each wall's normal the approach speed is limited to 2.5 m/s per metre above 3.5 m, and between two opposite walls the velocity along the normal is steered (rate 2.5 /s) toward 1.2 /s per metre off the centre line (<= 8 m/s). Active while swinging and in the air after a release. Web strands: 1.2 cm wide (at least ~1.2 px), grey, no emissive. Motion blur: amount 0.35 x smoothstep(speed, 28, 50 m/s) (diving x 1.3), none on foot / walls; max 1-3 %.
- Round 09: the arc depth alternates (odd swings 10.2 m, even swings 17.5 m below the entry, + 0-1.5 m; a high anchor lowers the virtual pivot instead). The anchor search heading is turned 30 deg toward the side opposite the previous web (the swing plane keeps the travel heading). While swinging, the canyon spring's target line sits 0.45 x the active anchor's offset from the centre (<= 6 m); in the air no centring inside +/-8 m. Pivot keeps 25 % of the anchor's side offset (was 10 %). Web: 1.6 cm (>= ~2 px), dark grey (0.09). Hero skeletal mesh: per-bone motion blur off. Perch / top-out landings start the perchLand clip at 0.22 s (its impact crouch). Dive: fast-fall / calm-fall blend oscillating with a 0.8 s period, plus the air sway. Scripts a and d re-baked from the same rule.
- Round 10 (Manhattan): a *sky launch* is a jump-release with a trick buffered; the launch speed is solved so the apex lands 3 m over the lower street wall's roofline ahead (peak clamped 38-58 m over the street, climb gravity x1.4, hang x0.55 under 7 m/s), followed by a long web (<= 50 m rope) built to bottom 5-9 m over the street; no web is searched on the way up. Script rule: a release is a sky launch when >= `skyEvery` releases have passed and the lower wall ahead is reachable (or 5.5 s after the last one); plain releases at phase 0.55; any swing is let go 1.25-1.55 s in, a stale swing after 2.4 s. While swinging, touching a wide facade with the stick held into it lets go of the web and wall-runs up it. A new web never anchors below 3 m over the body or behind it. Hero mesh / clip paths are data (`HeroMeshPath`, `HeroClipRoot`, ...).
- Round 11 flips: a trick is a *flip program* = a timeline of held shapes (tuck, pike, layout, swan, pencil, straddle, throne, twist, reach) keyed in Blender on the hero rig (`docs/night1/traversal/blender/`); body rotation about the body centre follows one angular momentum per program with per-shape effective inertia (tuck 1 .. pencil / throne 9), solved to end upright; twist segments turn about the long axis; the upper body samples the timeline 0.04 s ahead and the legs 0.07 s behind; a cut program springs back to the body frame in ~0.07 s. The next web is searched only in the program's final reach (held up to 0.2 s). Wall-run top-out = program wallFront. Flip camera: orbit 40 deg off the travel axis toward the side with more space, 1.6 m under the hero, framing 0.42, look-up <= 18 deg.
- Round 12 (critic r11: tricks low in the canyon, facades behind the hero): a trick pressed at a web release is a sky launch; its speed is solved so the apex sits 6 m over the tallest roof within 30 m of the stretch of path the flip will cover (down-ray grid), peak <= 90 m over the street, launch <= 60 m/s; the program is armed on the climb, starts when the climb slows to 9 m/s and plays at 0.32 g (it stays over the roofs). The chain rule only launches where that apex is reachable. Flip camera: every 0.15 s it scores orbit yaw offsets (-120..120 deg from behind) x look-up elevations (30-60 deg, camera below the hero) by the share of 16 rays around the hero (the hero box + 40 px at 1080p) that reach open sky within 900 m, preferring a 3/4 side view (55 deg) and the lowest clear look-up; springs 0.3 s, 3.4 m from the hero. backDouble = tuck 0.55 / layout 0.5 / tuck 0.55 / layout 0.5 / reach 0.2 s.
- Round 13 (critic r12: tricks were isolated set pieces, 1.7 s rise + trick + 1.3 s dive + a one-frame camera cut): a trick pressed at a web release is a *flow flip*: the program starts AT the release (no sky launch), the climb is solved so the catch window (the program's final Reach, 1.5 s in) opens ~2 m over the release height inside the canyon, and the next web attaches in that reach; a program keeps its shapes (no ballistic downgrade). backDouble = tuck double + a keyed Kickout (2 shapes). The chase camera's `too close: cut` rule is removed and the camera output is slew-limited per frame (3 deg pitch, 4 deg yaw, 1.2 m position at 60 fps); the flip camera blends out over >= 0.4 s. A hero-only fill light (5000 cd, 18000 cd in a flip) lifts the backlit silhouette. Camera hold: when the hero himself overlaps geometry (street-tree canopy at a swing bottom) the view is held RELATIVE to him (the first capture froze it absolutely: 20 m away).
- Round 14 (critic r13: the flip camera looked up from under the hero, so the rotation did not read, and stayed tilted up into the next swing): during a flip program the camera orbits to a SIDE view -- 70-115 deg off the travel-behind direction, one side for the whole trick, 4-28 deg below the hero, 3.3 m out, a spot with 1.5 m of free space beyond it and a clear path 0.5 s along the travel -- the flip look-up is capped at 27 deg and every non-wall view at 29 deg up; from 0.25 to 0.5 s after each web attach the pitch settles into 5.5-11.5 deg down. Flip rotation is eased: each segment's effective inertia rises toward its ends (tuck entries / exits ~40-60 % of the mid-tuck rate) and the keyed shapes' own hips->head lean is taken out of the root pitch, so the visible body axis follows the eased timeline. backDouble = Tuck 1.20 s + Kickout 0.60 s (<= ~100 deg/s), frontPikeSwan = Pike 0.40 / Swan 0.55 / Tuck 0.38 / Reach 0.26 s (no pencil), corkscrew = Layout 0.31 / Twist 0.42 / Swan 0.36 / Tuck 0.34 / Reach 0.24 s. f4 runs north from y 375 (11.6 s, 4 flips); b fires the zip from the flip's final Reach at 2.88 s.
- Round 15 (critic r14: the trick camera climbed to 20-27 deg up and looked into the sun, flaring out the flips): the side-on trick view is searched at elevations -3..6 deg around the hero's height (preferring 1 deg below), its look-up capped at 8 deg (every other non-wall view at 10 deg), and a view whose direction is closer than 100 deg to the sun (the level's atmosphere sun light: 8 deg up, due west in this map) is rejected (staged fallbacks keep the sun rule before any clearance rule); the flip camera blends in over 0.30 s. Wall-run camera: 1.3 m below and 3.1 m out from the hero, hero at 0.60 of the frame height, look-up capped at 30 deg. When the hero is inside a street-tree canopy the camera spot is lifted out of the foliage. A flow flip's rise targets 3 m over the lower street wall's roofline (buildings >= 16 m) when that needs <= 14 m of rise, else the round-13 3 m rise. While the trick camera frames a flip the zip reticle aims along the chase heading (b: zip fired from the final Reach at 2.88 s).

## Capture settings (all sequences)

| | video | stills |
|---|---|---|
| output | 1920x1080, 60 fps, H.264 mp4 | 3840x2160, JPEG q92 (converted from PNG) |
| internal resolution | 1920x1080 (`r.ScreenPercentage 100`) | 3840x2160 (`r.ScreenPercentage 100`) |
| time step | fixed 1/60 s (`-benchmark -fps=60 -dumpmovie`) | fixed 1/60 s (`-benchmark -fps=60`) |
| AA / GI | TSR, Lumen (project defaults) | same |

The video frames are rendered offline at a fixed step; they say nothing about real-time frame rate.
No 4K stills were captured this round (the stills column above does not apply): only the 1920x1080 movies (internal = output, `r.ScreenPercentage 100`). Every run went through `gpu_slot.sh capture` on a GPU shared with other sessions (`contaminated`: no perf claim). All nine movies were captured with the final build of this round (see Build above), in two GPU holds (f1-f5, then a-d); warm-up pass skipped (shader cache warm).

Camera (round 05 chase camera): 3.8 m behind the hero along the lagged heading yaw (horizontal spring 0.07 s, held 3.5-5.0 m), 1.1 m above his centre (vertical spring 0.05 s, held 0.7-1.8 m), 0.3 m shoulder offset; yaw toward the hero; pitch places the hero at screen height 0.48 (arc bottom) .. 0.40 (arc ends), clamped 5-22 deg down. At each web attach (first 0.5 s) the view pitches up and, if needed, turns and widens (<= 26 deg of extra vertical FOV) so the anchor on the facade is inside the frame with the hero. Collision: sphere sweeps + clear-orbit search (see round 03). Vertical FOV 58 + 13 x smoothstep(speed, 12, 44 m/s) + 5 diving + kick / punch springs; vertical FOV converted to Unreal's horizontal FOV with the viewport aspect.

Round 06 camera changes: on a wall (and while rising in the top-out) the camera blends (spring 0.16 s in, 0.22 s out) to a position 2.2 m below the hero's centre and 2.2 m out from the wall (at least 0.6 m over the street; further out when the street clamps it, keeping 3.2 m to the hero), yaw facing the wall, pitch up so the hero's centre sits at 0.68 of the frame height, vertical FOV +4 deg. Chase pitch may exceed 22 deg down when collision lifts the camera, so the hero's centre stays at or above 0.62 of the frame height. Script c: the camera-turn key looks up (pitch-down rate -10 deg/s) instead of down (+4).

Round 07 camera changes: height over the hero 1.8 m (held 1.2-2.6 m; round 05-06: 1.1 m, 0.7-1.8 m), look-down at least 10 deg (was 5). The attach look-up toward the anchor is scaled by 1 - (fall speed - 8) / 14 (clamped 0..1) and keeps the hero 12 deg inside the bottom edge (was 8); the attach yaw turn is capped at 25 deg with a 0.12 s spring (was 0.035 s). 0.4 m closer while swinging / airborne.

Round 08 camera change: sideways facade clearance measured from the camera along its right / left: a 0.15 s spring toward 3 m and a hard 1.5 m minimum, moved only as far as the line of sight to the hero stays clear.

Round 09 camera changes: height over the hero 0.6 m (held 0.2-1.8 m), look-down floor -8 deg (looking up allowed), framing target 0.44 (arc bottom) .. 0.37 (arc ends); attach FOV widening <= 10 deg (round 08). During a swing chain the camera position slides 1.3 m toward the side of the active anchor (0.3 s spring; off after 0.8 s without a web, in a dive, and outside chains) and still turns toward the hero; roll toward that side up to 6 deg, weighted by smoothstep(|rope angle|, 0.55, 1.0) rad.

Round 10 camera changes: the attach look-up stops where the hero centre reaches 0.64 of the frame height; attach springs 0.035 -> 0.12 s; the first composed frame starts at its framing / attach targets (no pop at t = 0); arc-bottom framing target 0.44 -> 0.50 (hero centre-Y spread); roll: yaw-rate lean 0.03 (cap 4 deg), bank 0.04, leans under 1 deg dropped. Sky launch: the camera sinks 1.2 m under the hero and frames him at 0.40, looking up <= 10 deg.

Inputs are replayed from JSON (`docs/night1/traversal/scripts/city/`, `-WHTravScript=`), sampled once per frame and fed to the same code path as the keyboard / pad. `heading` = the stick is set every frame to the world direction given (yaw deg), expressed relative to the current camera. Sequences a and d (round 10) run the `autoChain` rule live (rule-form keys in the JSON: release / re-press / sky-launch timing decided in the game tick from the physical state, seed 1234; the fixed 1/60 s replay is deterministic); b and c are hand-timed keys.

TRAVERSAL-SPEC check: `SPEC_CHECK.txt` — `docs/night1/traversal/spec_cam_check.py` (lines T8-T14, T16, T19 from the telemetry: hero pixel box, the rendered camera's pitch / yaw / roll / horizontal FOV, occlusion) and the spec's own instruments run on the 1080p videos: `vp_cam.py` (roll / pitch / yaw / FOV from vanishing points) and `nearflow.py 8` (near-field coverage by optical flow; CSVs in `spec/`).

Telemetry CSV columns (one row per rendered frame): frame, t, mode, sub, body position x/y/z (m, UE axes), velocity, speed, horizontal speed, height above the floor below, swing anchor x/y/z, rope length, web tension 0..1, momentum-chain level, trick, zip target present + position, camera position / yaw / pitch / vertical FOV / distance, motion-blur factor, input state; round 06 adds head_hip_dz (head minus hips height, m) and limb_z (hand L, hand R, foot L, foot R height minus hips, m); round 07 adds body_rope_deg (hips->head vs hips->anchor, deg, while swinging; -1 otherwise) and web_on (a web strand stuck); round 08 adds wall_frac and hero_occl (see the facade check); round 09 adds hero_cx (projected bone box centre x) and pcm_roll.

## a_swing_chain — Swing chain up the avenue at speed (lit Manhattan map, golden)

Airborne start 24 m over the north-south avenue (x 250 m) with 22 m/s forward velocity heading north (-Y); scripted swing chain (autoChain rule: release on the rising front, re-press after 0.8 s; a sky launch = jump-release + trick where the lower street wall ahead is within reach, at most every 2nd release).

Files: `a_swing_chain.mp4`, `a_swing_chain_telemetry.csv`

Spawn: position [250, 240, 24] m, yaw -90 deg, camera pitch 0.12 rad, initial velocity [0, -22, 0] m/s. Script: `scripts/city/a_swing_chain.json`.

| t (s) | input change |
|---|---|
| 0.000 | stick (x right, y fwd) = [0, 1], heading (world yaw deg) = -90, RMB swing up |
| 0.400 | autoChain down, releasePhase = 0.55, gap = 0.8, repressVz = 99.0, trickEvery = 3, skyEvery = 0, skyTricks = 1, skyRepressH = 30, skyPhase = 0.8, skyMax = 2.8 |

Measured over the video (935 frames, 15.57 s): speed 22.0-60.9 m/s; height above the floor 0.6-25.7 m; Y (north = -Y) travelled -643 m; vertical FOV 58.0-80.1 deg; camera distance 2.9-4.9 m; max momentum-chain level 6; tricks: backDouble, frontPikeSwan.

State sequence (mode/sub-state, start time s): air 0.00 -> swing 0.40 -> air/release 1.67 -> air 2.07 -> swing 2.47 -> air/release 3.85 -> air 4.25 -> swing 4.65 -> air/trick 5.68 -> swing 7.27 -> air/release 8.35 -> air 8.75 -> swing 9.15 -> air/release 10.12 -> air 10.52 -> swing 10.92 -> air/trick 11.93 -> swing 13.35 -> air/release 14.23 -> air 14.63 -> swing 15.03

## b_release_trick_dive_zip — Release + trick + dive + zip to a rooftop

Airborne start 30 m over the avenue (26 m/s north), one swing, release with a trick (frontPikeSwan) at 1.4 s, web-zip pressed as soon as the zip target reappears after the program (3.08 s, 0.27 s after its Reach; round 13: no web-less dive), zip to a roof point, perch.

Files: `b_release_trick_dive_zip.mp4`, `b_release_trick_dive_zip_telemetry.csv`

Spawn: position [250, 170, 30] m, yaw -90 deg, camera pitch 0.12 rad, initial velocity [0, -26, 0] m/s. Script: `scripts/city/b_release_trick_dive_zip.json`.

| t (s) | input change |
|---|---|
| 0.000 | stick (x right, y fwd) = [0, 1], heading (world yaw deg) = -90, RMB swing down, flip = frontPikeSwan |
| 1.400 | RMB swing up, F trick down |
| 1.420 | F trick up |
| 2.880 | E zip down, stick (x right, y fwd) = [0, 0], heading off |
| 2.980 | E zip up |

Measured over the video (419 frames, 6.97 s): speed 0.0-59.8 m/s; height above the floor 0.7-47.7 m; Y (north = -Y) travelled -104 m; vertical FOV 58.0-69.4 deg; camera distance 2.5-5.4 m; max momentum-chain level 0; tricks: frontPikeSwan.

State sequence (mode/sub-state, start time s): swing 0.00 -> air/trick 1.40 -> zip 2.88 -> zip/zipFlight 2.95 -> zip 3.62 -> perch/perchLand 3.88 -> perch 4.38

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

Measured over the video (629 frames, 10.47 s): speed 0.0-60.1 m/s; height above the floor 0.4-61.8 m; Y (north = -Y) travelled -30 m; vertical FOV 58.0-66.9 deg; camera distance 2.6-7.7 m; max momentum-chain level 0; tricks: none.

State sequence (mode/sub-state, start time s): swing 0.00 -> air/release 1.70 -> wall/wallRun 2.08 -> air/topOut 3.85 -> land/landTopOut 4.77 -> ground 5.12 -> zip 8.50 -> zip/zipFlight 8.55 -> zip 8.83 -> perch/perchLand 9.12 -> perch 9.62

## d_sprint_jump_first_swing — Ground sprint -> jump -> first swing

Street start on the avenue; run north, charged jump, first swing, then the round-10 chain rule (as a).

Files: `d_sprint_jump_first_swing.mp4`, `d_sprint_jump_first_swing_telemetry.csv`

Spawn: position [250, 244, 0.95] m, yaw -90 deg, camera pitch 0.14 rad. Script: `scripts/city/d_sprint_jump_first_swing.json`.

| t (s) | input change |
|---|---|
| 0.000 | stick (x right, y fwd) = [0, 1], heading (world yaw deg) = -90, Shift down |
| 1.800 | Space down |
| 2.200 | Space up |
| 2.600 | RMB swing down, autoChain down, releasePhase = 0.55, gap = 0.8, repressVz = 99.0, trickEvery = 3, skyEvery = 0, skyTricks = 2, skyRepressH = 30, skyPhase = 0.8, skyMax = 2.8 |

Measured over the video (719 frames, 11.97 s): speed 0.6-52.5 m/s; height above the floor 0.2-22.9 m; Y (north = -Y) travelled -268 m; vertical FOV 58.0-76.7 deg; camera distance 2.8-5.0 m; max momentum-chain level 4; tricks: none.

State sequence (mode/sub-state, start time s): ground 0.00 -> air/jumpLaunch 2.20 -> air 2.37 -> swing 2.68 -> air/release 3.95 -> air 4.35 -> swing 4.75 -> air/release 6.08 -> air 6.48 -> swing 6.88 -> air/release 7.92 -> air 8.32 -> swing 8.72 -> air/release 9.70 -> air 10.10 -> swing 10.50 -> air/release 11.58

## f1_flow_backDouble — Round 13 flow flip: swing, web release, backDouble program from the release, next web in its final reach

West avenue (x -250), airborne start 28 m over the street at y 170 heading south (24 m/s); chain rule from 0.4 s (release phase 0.55); a trick pressed at every 2nd release starts the flip program AT the release (flow flip: the climb is solved so the catch window opens ~2 m over the release height); program backDouble = tuck + keyed kick-out, the next web is searched in its final reach (catch window 1.5 s).

Files: `f1_flow_backDouble.mp4`, `f1_flow_backDouble_telemetry.csv`

Spawn: position [-250, 170, 28] m, yaw 90 deg, camera pitch 0.12 rad, initial velocity [0, 24, 0] m/s. Script: `scripts/city/f1_flow_backDouble.json`.

| t (s) | input change |
|---|---|
| 0.000 | stick (x right, y fwd) = [0, 1], heading (world yaw deg) = 90, RMB swing up, flip = backDouble |
| 0.400 | autoChain down, releasePhase = 0.55, gap = 0.8, repressVz = 99.0, trickEvery = 2, skyEvery = 0, skyTricks = 1, skyRepressH = 30, skyPhase = 0.8, skyMax = 2.8 |

Measured over the video (479 frames, 7.97 s): speed 24.0-45.0 m/s; height above the floor 3.2-26.9 m; Y (north = -Y) travelled 259 m; vertical FOV 58.0-79.3 deg; camera distance 3.0-4.9 m; max momentum-chain level 3; tricks: backDouble.

State sequence (mode/sub-state, start time s): air 0.00 -> swing 0.40 -> air/release 1.62 -> air 2.02 -> swing 2.42 -> air/trick 3.42 -> swing 5.00 -> air/release 6.13 -> air 6.53 -> swing 6.93

## f2_flow_pikeSwan — Round 13 flow flip: frontPikeSwan program from the release

As f1 from y 180, program frontPikeSwan (pike, pencil, swan, tuck, reach).

Files: `f2_flow_pikeSwan.mp4`, `f2_flow_pikeSwan_telemetry.csv`

Spawn: position [-250, 180, 28] m, yaw 90 deg, camera pitch 0.12 rad, initial velocity [0, 24, 0] m/s. Script: `scripts/city/f2_flow_pikeSwan.json`.

| t (s) | input change |
|---|---|
| 0.000 | stick (x right, y fwd) = [0, 1], heading (world yaw deg) = 90, RMB swing up, flip = frontPikeSwan |
| 0.400 | autoChain down, releasePhase = 0.55, gap = 0.8, repressVz = 99.0, trickEvery = 2, skyEvery = 0, skyTricks = 1, skyRepressH = 30, skyPhase = 0.8, skyMax = 2.8 |

Measured over the video (479 frames, 7.97 s): speed 24.0-52.9 m/s; height above the floor 3.3-26.9 m; Y (north = -Y) travelled 272 m; vertical FOV 58.0-80.7 deg; camera distance 3.0-4.9 m; max momentum-chain level 3; tricks: frontPikeSwan.

State sequence (mode/sub-state, start time s): air 0.00 -> swing 0.40 -> air/release 1.57 -> air 1.97 -> swing 2.37 -> air/trick 3.37 -> swing 4.78 -> air/release 5.87 -> air 6.27 -> swing 6.67 -> air/release 7.75

## f3_flow_corkscrew — Round 13 flow flip: corkscrew program from the release

As f1 from y 190, program corkscrew (layout with a full twist, swan, tuck, reach); a flip on every release (trickEvery 1): on every 2nd release the corkscrew did not fit at the low 2nd release and the 4th landed on a roof 0.3 s in.

Files: `f3_flow_corkscrew.mp4`, `f3_flow_corkscrew_telemetry.csv`

Spawn: position [-250, 190, 28] m, yaw 90 deg, camera pitch 0.12 rad, initial velocity [0, 24, 0] m/s. Script: `scripts/city/f3_flow_corkscrew.json`.

| t (s) | input change |
|---|---|
| 0.000 | stick (x right, y fwd) = [0, 1], heading (world yaw deg) = 90, RMB swing up, flip = corkscrew |
| 0.400 | autoChain down, releasePhase = 0.55, gap = 0.8, repressVz = 99.0, trickEvery = 1, skyEvery = 0, skyTricks = 1, skyRepressH = 30, skyPhase = 0.8, skyMax = 2.8 |

Measured over the video (479 frames, 7.97 s): speed 24.0-50.2 m/s; height above the floor 2.9-26.9 m; Y (north = -Y) travelled 256 m; vertical FOV 58.0-78.0 deg; camera distance 3.0-7.9 m; max momentum-chain level 3; tricks: corkscrew.

State sequence (mode/sub-state, start time s): air 0.00 -> swing 0.40 -> air/trick 1.35 -> swing 2.85 -> air/release 3.85 -> air 4.25 -> swing 4.78 -> air/release 5.82 -> air 6.22 -> swing 6.62 -> air/release 7.70

## f4_chain_flips — Round 13 flows: 13 s swing chain, a flip on every release

West avenue from y 120 heading south, 24 m over the street; chain rule, trickEvery 1; requested programs cycle backDouble, frontPikeSwan, corkscrew.

Files: `f4_chain_flips.mp4`, `f4_chain_flips_telemetry.csv`

Spawn: position [-250, 375, 24] m, yaw -90 deg, camera pitch 0.12 rad, initial velocity [0, -22, 0] m/s. Script: `scripts/city/f4_chain_flips.json`.

| t (s) | input change |
|---|---|
| 0.000 | stick (x right, y fwd) = [0, 1], heading (world yaw deg) = -90, RMB swing up, flip = backDouble,frontPikeSwan,corkscrew |
| 0.400 | autoChain down, releasePhase = 0.55, gap = 0.8, repressVz = 99.0, trickEvery = 1, skyEvery = 0, skyTricks = 1, skyRepressH = 30, skyPhase = 0.8, skyMax = 2.8 |

Measured over the video (695 frames, 11.57 s): speed 22.0-55.6 m/s; height above the floor 0.6-23.1 m; Y (north = -Y) travelled -444 m; vertical FOV 58.0-79.4 deg; camera distance 2.9-4.8 m; max momentum-chain level 4; tricks: backDouble, corkscrew, frontPikeSwan.

State sequence (mode/sub-state, start time s): air 0.00 -> swing 0.40 -> air/trick 1.35 -> swing 2.93 -> air/trick 3.93 -> swing 5.35 -> air/trick 6.38 -> swing 7.88 -> air/trick 8.87 -> swing 10.45 -> air/trick 11.42

## f5_canyon_backDouble — Round 13 check: the Midtown avenue (x 250, towers 140-250 m)

Avenue x 250 from y 170 heading north, same rule as f1: flow flips inside the canyon.

Files: `f5_canyon_backDouble.mp4`, `f5_canyon_backDouble_telemetry.csv`

Spawn: position [250, 170, 30] m, yaw -90 deg, camera pitch 0.12 rad, initial velocity [0, -26, 0] m/s. Script: `scripts/city/f5_canyon_backDouble.json`.

| t (s) | input change |
|---|---|
| 0.000 | stick (x right, y fwd) = [0, 1], heading (world yaw deg) = -90, RMB swing up, flip = backDouble |
| 0.400 | autoChain down, releasePhase = 0.55, gap = 0.8, repressVz = 99.0, trickEvery = 2, skyEvery = 0, skyTricks = 1, skyRepressH = 30, skyPhase = 0.8, skyMax = 2.8 |

Measured over the video (479 frames, 7.97 s): speed 26.0-49.7 m/s; height above the floor 0.4-28.9 m; Y (north = -Y) travelled -291 m; vertical FOV 58.0-77.3 deg; camera distance 3.0-4.9 m; max momentum-chain level 3; tricks: backDouble.

State sequence (mode/sub-state, start time s): air 0.00 -> swing 0.40 -> air/release 1.53 -> air 1.93 -> swing 2.33 -> air/trick 3.33 -> swing 4.92 -> air/release 5.90 -> air 6.30 -> swing 6.70 -> air/trick 7.78

