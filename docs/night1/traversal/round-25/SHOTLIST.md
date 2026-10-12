# Traversal (P3) — round 25 shot list

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. Nothing here is meant to infringe.

- Build: branch `night1/traversal`, commit `c48462e8`, UE 5.8.3, map `/Game/Maps/Manhattan` (golden preset; the integrated lit city built in this worktree by `unreal/WebHomage/Scripts/build_manhattan.py`; hero = the `/Game/Traversal/HeroDev` dev proxy).
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
- Round 16 (director's TRICK_CAMERA_SPEC.md, replacing the r11-r15 sky search / side-on orbit): while a flip program plays the camera is a HELD 3/4-behind chase. At the release frame ONE yaw offset of 40-55 deg from the travel-behind direction is chosen (obstruction first: the spot must be sweep-reachable with 1.5 m free beyond it and a clear path 0.5 s along the travel; then the sun rule, view >= 100 deg from the level's sun; then open space) and is never re-searched; it is held on its WORLD azimuth. The camera sits 4.4 m from the hero (0.6 m closer while his shape is a tuck / pike; pulled in along the same axis by an obstruction, to 4.0 m, else blended to the plain chase), 1.0 m under his body centre, hero framed at 0.36 of the frame height with a 3 deg lead-room yaw bias toward his travel; look-up capped at 7.5 deg; no roll, no attach yaw beat; FOV / kick / punch / shake untouched. Blend in: critically damped springs (0.35 s horizontal, 0.15 s height), blend out: smoothstep over 0.9 s from the web attach, the chase camera keeps running underneath (polar blend about the hero). No other flip or swing rule changed; scripts are the r15 ones.
- Round 17 (flips above the rooftops): the f-series runs EAST along the northern cross street (y -560): north side a park / 2-6 storey strip (10-30 m) with open sky and the far skyline behind it, south side 46-466 m blocks to web onto; the sun (due west) is behind every view. Arcs bottom >= 14 m over the street there (script tuning; over the 10-14 m street trees) and the hero keeps >= 9 m from the south facades. A flip on every release; each flow flip's climb is solved so its APEX puts the hips >= 4 m over the lower roofline within 30 m (highest top >= 16 m per street side, lower side; unreachable rooflines keep the round-13 climb), and a swing that ends in a flip is held on its rising front until that apex is reachable. Trick camera (round 16 held 3/4 view kept): the side is chosen sun-first (35-55 deg, view >= 100 deg from the sun), then by background sky share; the blend-in follows a minimum-time profile (<= 140 deg/s, k >= 0.9 at ~0.3 s). Asymmetric keyed shapes (tuck grab, pike with one arm swept back, stag swan, layout, scissor kick-out).

## Capture settings (all sequences)

| | video | stills |
|---|---|---|
| output | 1920x1080, 60 fps, H.264 mp4 | 3840x2160, JPEG q92 (converted from PNG) |
| internal resolution | 1920x1080 (`r.ScreenPercentage 100`) | 3840x2160 (`r.ScreenPercentage 100`) |
| time step | fixed 1/60 s (`-benchmark -fps=60 -dumpmovie`) | fixed 1/60 s (`-benchmark -fps=60`) |
| AA / GI | TSR, Lumen (project defaults) | same |

The video frames are rendered offline at a fixed step; they say nothing about real-time frame rate.
No 4K stills were captured this round (the stills column above does not apply): only the 1920x1080 movies (internal = output, `r.ScreenPercentage 100`). Every run went through `gpu_slot.sh capture` on a GPU shared with other sessions (`contaminated`: no perf claim). Seven movies (f1-f5, a, b) were captured with the final build of this round (see Build above) in one GPU hold; c and d come from the first round-16 hold (wall camera / no trick camera: untouched by the later trick-camera edits); warm-up pass skipped (shader cache warm).

Camera (round 05 chase camera): 3.8 m behind the hero along the lagged heading yaw (horizontal spring 0.07 s, held 3.5-5.0 m), 1.1 m above his centre (vertical spring 0.05 s, held 0.7-1.8 m), 0.3 m shoulder offset; yaw toward the hero; pitch places the hero at screen height 0.48 (arc bottom) .. 0.40 (arc ends), clamped 5-22 deg down. At each web attach (first 0.5 s) the view pitches up and, if needed, turns and widens (<= 26 deg of extra vertical FOV) so the anchor on the facade is inside the frame with the hero. Collision: sphere sweeps + clear-orbit search (see round 03). Vertical FOV 58 + 13 x smoothstep(speed, 12, 44 m/s) + 5 diving + kick / punch springs; vertical FOV converted to Unreal's horizontal FOV with the viewport aspect.

Round 06 camera changes: on a wall (and while rising in the top-out) the camera blends (spring 0.16 s in, 0.22 s out) to a position 2.2 m below the hero's centre and 2.2 m out from the wall (at least 0.6 m over the street; further out when the street clamps it, keeping 3.2 m to the hero), yaw facing the wall, pitch up so the hero's centre sits at 0.68 of the frame height, vertical FOV +4 deg. Chase pitch may exceed 22 deg down when collision lifts the camera, so the hero's centre stays at or above 0.62 of the frame height. Script c: the camera-turn key looks up (pitch-down rate -10 deg/s) instead of down (+4).

Round 07 camera changes: height over the hero 1.8 m (held 1.2-2.6 m; round 05-06: 1.1 m, 0.7-1.8 m), look-down at least 10 deg (was 5). The attach look-up toward the anchor is scaled by 1 - (fall speed - 8) / 14 (clamped 0..1) and keeps the hero 12 deg inside the bottom edge (was 8); the attach yaw turn is capped at 25 deg with a 0.12 s spring (was 0.035 s). 0.4 m closer while swinging / airborne.

Round 08 camera change: sideways facade clearance measured from the camera along its right / left: a 0.15 s spring toward 3 m and a hard 1.5 m minimum, moved only as far as the line of sight to the hero stays clear.

Round 09 camera changes: height over the hero 0.6 m (held 0.2-1.8 m), look-down floor -8 deg (looking up allowed), framing target 0.44 (arc bottom) .. 0.37 (arc ends); attach FOV widening <= 10 deg (round 08). During a swing chain the camera position slides 1.3 m toward the side of the active anchor (0.3 s spring; off after 0.8 s without a web, in a dive, and outside chains) and still turns toward the hero; roll toward that side up to 6 deg, weighted by smoothstep(|rope angle|, 0.55, 1.0) rad.

Round 10 camera changes: the attach look-up stops where the hero centre reaches 0.64 of the frame height; attach springs 0.035 -> 0.12 s; the first composed frame starts at its framing / attach targets (no pop at t = 0); arc-bottom framing target 0.44 -> 0.50 (hero centre-Y spread); roll: yaw-rate lean 0.03 (cap 4 deg), bank 0.04, leans under 1 deg dropped. Sky launch: the camera sinks 1.2 m under the hero and frames him at 0.40, looking up <= 10 deg.

Inputs are replayed from JSON (`docs/night1/traversal/scripts/city/`, `-WHTravScript=`), sampled once per frame and fed to the same code path as the keyboard / pad. `heading` = the stick is set every frame to the world direction given (yaw deg), expressed relative to the current camera. Sequences a and d (round 10) run the `autoChain` rule live (rule-form keys in the JSON: release / re-press / sky-launch timing decided in the game tick from the physical state, seed 1234; the fixed 1/60 s replay is deterministic); b and c are hand-timed keys.

Telemetry CSV columns (one row per rendered frame): frame, t, mode, sub, body position x/y/z (m, UE axes), velocity, speed, horizontal speed, height above the floor below, swing anchor x/y/z, rope length, web tension 0..1, momentum-chain level, trick, zip target present + position, camera position / yaw / pitch / vertical FOV / distance, motion-blur factor, input state; round 06 adds head_hip_dz (head minus hips height, m) and limb_z (hand L, hand R, foot L, foot R height minus hips, m); round 07 adds body_rope_deg (hips->head vs hips->anchor, deg, while swinging; -1 otherwise) and web_on (a web strand stuck); round 08 adds wall_frac and hero_occl (see the facade check); round 09 adds hero_cx (projected bone box centre x) and pcm_roll.

## a_swing_chain — Swing chain up the avenue at speed (lit Manhattan map, golden)

Airborne start 24 m over the north-south avenue (x 250 m) with 22 m/s forward velocity heading north (-Y); scripted swing chain (autoChain rule: release on the rising front, re-press after 0.8 s; a sky launch = jump-release + trick where the lower street wall ahead is within reach, at most every 2nd release).

Files: `a_swing_chain.mp4`, `a_swing_chain_telemetry.csv`

Spawn: position [250, 240, 24] m, yaw -90 deg, camera pitch 0.12 rad, initial velocity [0, -22, 0] m/s. Script: `scripts/city/a_swing_chain.json`.

| t (s) | input change |
|---|---|
| 0.000 | stick (x right, y fwd) = [0, 1], heading (world yaw deg) = -90, RMB swing up |
| 0.400 | autoChain down, releasePhase = 0.55, gap = 0.8, repressVz = -8.0, trickEvery = 3, skyEvery = 0, skyTricks = 1, skyRepressH = 30, skyPhase = 0.8, skyMax = 2.8 |

Measured over the video (935 frames, 15.57 s): speed 22.0-44.7 m/s; height above the floor 7.5-34.1 m; Y (north = -Y) travelled -433 m; vertical FOV 58.0-70.7 deg; camera distance 3.5-5.2 m; max momentum-chain level 0; tricks: backDouble.

State sequence (mode/sub-state, start time s): air 0.00 -> swing 0.40 -> air/release 1.67 -> air 2.07 -> air/dive 3.37 -> swing 3.40 -> air/release 4.78 -> air 5.18 -> air/dive 6.73 -> swing 6.77 -> air/trick 7.80 -> air 9.25 -> air/dive 10.12 -> swing 10.15 -> air/release 11.67 -> air 12.07 -> air/dive 13.42 -> swing 13.45 -> air/release 14.77 -> air 15.17

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

Measured over the video (629 frames, 10.47 s): speed 0.0-37.9 m/s; height above the floor 0.5-24.4 m; Y (north = -Y) travelled -52 m; vertical FOV 58.0-65.3 deg; camera distance 1.8-6.2 m; max momentum-chain level 0; tricks: none.

State sequence (mode/sub-state, start time s): swing 0.00 -> air/release 1.70 -> air 2.10 -> ground 2.37 -> air 2.40 -> wall/wallRun 2.55 -> air/topOut 4.33 -> land/landTopOut 5.50 -> ground 5.85 -> zip 8.50 -> zip/zipFlight 8.55 -> zip 8.75 -> perch/perchLand 8.92 -> perch 9.42

## f1_flow_backDouble — Round 17 flow flips over the roofline: backDouble on every release

Northern cross street (y -560), airborne start 30 m over the street at x -225 heading EAST (26 m/s); chain rule from 0.4 s; a trick at every release starts the flip program AT the release, its climb solved for an apex >= 4 m over the lower roofline within 30 m; program backDouble = tuck double + keyed kick-out, the next web in its final reach.

Files: `f1_flow_backDouble.mp4`, `f1_flow_backDouble_telemetry.csv`

Spawn: position [-225, -560, 30] m, yaw 0 deg, camera pitch 0.12 rad, initial velocity [26, 0, 0] m/s. Script: `scripts/city/f1_flow_backDouble.json`.

| t (s) | input change |
|---|---|
| 0.000 | stick (x right, y fwd) = [0, 1], heading (world yaw deg) = 0, RMB swing up, flip = backDouble |
| 0.400 | autoChain down, releasePhase = 0.55, gap = 0.8, repressVz = 99.0, trickEvery = 1, skyEvery = 0, skyTricks = 1, skyRepressH = 30, skyPhase = 0.8, skyMax = 2.8 |

Measured over the video (539 frames, 8.97 s): speed 26.0-49.3 m/s; height above the floor 12.5-29.1 m; Y (north = -Y) travelled -0 m; vertical FOV 58.0-76.0 deg; camera distance 3.5-5.2 m; max momentum-chain level 3; tricks: backDouble.

State sequence (mode/sub-state, start time s): air 0.00 -> swing 0.40 -> air/trick 1.35 -> swing 2.77 -> air/trick 3.77 -> swing 5.15 -> air/trick 5.72 -> swing 7.30 -> air/trick 8.38



## Round 25 -- every clip in this folder

The generated sections above describe only the a / c / f-series scripts (text carried from earlier rounds). Round 25 captured the 11
clips below plus the new pawn run; per-clip build and path / camera checks are in `CLIPS.md`. All: 1920x1080 output, internal resolution
1920x1080 (`r.ScreenPercentage 100`), fixed 1/60 s step, real `-game` offscreen in `/Game/Maps/Manhattan`, 0.8 s pre-roll trimmed.

| clip | view / movement | script (`scripts/city/`) | quit (s) |
|---|---|---|---|
| a_swing_chain | swing chain north up the Midtown avenue (x 250), autoChain, flow flip every 3rd release; r25 re-press at -8 m/s | a_swing_chain.json | 15.6 |
| c_wallrun_perch | swing -> wall-run up the loft facade -> roof -> camera turn -> zip -> perch (perch gate 8.6-10.5 s) | c_wallrun_perch.json | 10.5 |
| p1_pawn_run | NEW: 12 s full-stick street run up the avenue, chase camera behind (cadence hard line) | p1_pawn_run.json | 12.0 |
| w1_wallrun_tall_zip | vertical wall-run up a tall facade, zip from the wall, perch | w1_wallrun_tall_zip.json | 7.5 |
| w2_wallrun_side_zip | vertical then side wall-run, zip, perch | w2_wallrun_side_zip.json | 7.0 |
| r1_roofrun_zip | roof run, wall-run, zip to a ledge, perch | r1_roofrun_zip.json | 9.5 |
| s1_high_swing | high swing start | s1_high_swing.json | 6.0 |
| m1_mouse_swing | scripted swing chain with injected mouse look (`-WHTravInputTest=mouseLook -WHMouseTestPx=40`) | m1_mouse_swing.json | 6.0 |
| x1_rmb_cancel_flip | RMB cancels a flip into a swing | x1_rmb_cancel_flip.json | 4.0 |
| x2_rmb_cancel_wall | RMB cancels a wall run into a swing | x2_rmb_cancel_wall.json | 5.0 |
| f1_flow_backDouble | flow flip (backDouble) on every 2nd release, cross street east | f1_flow_backDouble.json | 9.0 |
| f4_chain_flips | not re-captured (`round-24/f4_chain_flips.mp4`; build-4 probe bit-identical path / camera) | f4_chain_flips.json | 13.3 |
