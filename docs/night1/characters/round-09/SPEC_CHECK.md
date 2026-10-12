# Round 09: spec check (P2 Characters)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.

Every number below was measured on the REAL game (UE 5.8.3, Metal, offscreen, through `gpu_slot.sh`; provenance in `CAPTURES.md`) with the committed tools; raw outputs are in `evidence/`. Round-08 critic: all five axes 5, biggest gap "the enemies hold a guard idle for 4 s of `street_fight_34`, 0 knockdowns, 0 hit reactions". **No frame time here is a performance result** (every lock release logged `contaminated=true reasons=no-exclusive-lock`).

## Round target: enemy combat reactions in `street_fight_34` (CH-C, section 3 of the spec)

Instrument: the walkers' bone log of the run (`-WHBoneLog`, 60 Hz, hips / spine2 / head / hands / feet in world cm, `evidence/fight_bones_final.csv.gz`), read by `tools/ue_char/fight/fight_check.py`; the clip's pixels by `video_activity.py`; the number of people by `analyze_r5.sh` (YOLO11x, CPU). The stage clock of the choreography is the capture director's shot clock; clip time = stage time - 0.05 s (the director starts 3 frames into the run).

| Target (director) | Round 08 (critic) | Round 09 (measured) | Evidence |
|---|---|---|---|
| >= 3 distinct hit reactions (stagger / recoil) in the 8 s `street_fight_34` (stage 8.0 - 16.0 s) | 0 reactions in 32 frames | **5 enemy reactions, all visible (spine2 or head moves >= 12 cm within 0.7 s): knockdown (Tee 8.42 s), recoil to the left (Oxblood 10.70 s), knockdown (Thug 12.14 s), stagger to the right (Hood 13.47 s), stagger back (Beard 14.80 s); 4 distinct clips (`down`, `hitBack`, `hitLeft`, `hitRight`)** | `evidence/fight_check_street_fight_34.json` (`reactions`) |
| >= 1 knockdown with the torso on the ground >= 1 s | 0 knockdowns | **2 in the window: Tee on the ground 9.02 - 11.95 s (2.93 s), Thug 12.73 - 15.65 s (2.92 s)** (torso on the ground = spine2 < 45 cm and pelvis < 60 cm; both lie flat, see `captures/street_fight_34_4k.jpg`, stage 13.6 s) | same, `knockdowns_ge_1s_in_window` |
| no 1 s window in which all 7 hold the guard idle | every thug idle from 1.5 to 5.5 s (frame-diff 1.2 - 2.0 % px) | **0 windows with every walker inactive (window step 0.1 s over 8 - 16 s); at least 3 of the 7 walkers are actively moving (a bone > 60 cm/s or the actor > 20 cm/s) in EVERY 1 s window**; guard idle measures 5 - 9 cm/s (hero 5.8, brute 5.4, tee / beard / oxblood 9.2 in the first second) | same, `idle_windows_all_walkers_inactive`, `min_walkers_active_in_any_1s_window` |
| pixel activity of the clip (mean % of luma pixels changing > 12/255 per frame, 1 s windows, 480 x 270 proxy) | not recorded; recomputed on the round-08 clip: min 0.26, median 0.58, max 1.97 | **min 0.94, median 1.73, max 2.86** (the camera is closer than in round 08, so only the minimum is a fair comparison: no window is nearly still) | `evidence/video_activity_street_fight_34.json`, `video_activity_r08_street_fight_34.json` |
| every enemy box shows motion | - | per-walker frame difference inside the walker's projected box, minimum over the windows: hero 5.6 %, thug 1.6, brute 3.2, hood 1.7, tee 4.0, beard 0.6, oxblood 1.6 | `fight_check_street_fight_34.json` (`video_box_frame_diff_pct`) |

The same run also covers the other two shots: `street_fight_wide` (stage 0 - 8 s): 4 reactions (stagger back, recoil left, stagger right, brute flinch), 0 all-idle windows, >= 2 active walkers in every window; `street_fight_orbit` (16 - 24 s): 6 reactions, 2 more knockdowns (Brute 16.92 - 20.72 s, Oxblood 20.17 - 22.95 s), 0 all-idle windows, >= 3 active walkers (`evidence/fight_check_street_fight_wide.json`, `..._orbit.json`).

**Do the blows land?** `contact_check.py`: at each of the 18 strike instants of the run (15 hero strikes, 3 enemy strikes on the hero) the distance from the striking wrist / foot to the victim's head and chest joints: median 22 cm, worst 35 cm (a wrist 15 - 30 cm from the head joint touches the face); round 08's enemies stood 2.7 - 3.0 m from the hero and punched air (`evidence/contact_check.txt`).

**CH11 / CH12 (YOLO11x on the clips, every 2nd frame):** people per frame median 7 (p10 6 - 7, max 7 - 9) in all three clips, all 7 at >= 3 % height; person height median 0.295 H (wide), 0.388 (3/4), 0.372 (orbit); max 0.48 (spec 0.16 - 0.60); each 4K still shows 7 people, 0.13 - 0.43 H (the lowest values are the bodies lying on the ground) (`evidence/count_videos.txt`, `yolo_*_4k.json`).

## Secondary issues of the round-08 critic

| Issue | Round 08 | Round 09 (measured on the 4K close-ups, same camera) | Evidence |
|---|---|---|---|
| tee mask see-through holes (CH18) | 3 components inside the mask: **188 px, 72 px, 22 px** (the critic's 198 / 91 / 24) | **0 components >= 20 px**; three slivers of 12, 12 and 4 px remain at the mouth crease | `evidence/tee_seethrough_r8.json` / `_r9.json` (`seethrough_4k.py`), CPU proof `tee_seethrough_cpu_before_after.json` |
| thug collar skin wedge (100 x 180 px) | one separate skin-coloured component of 7,336 px (95 x 173 px at 1750,1353) | **1,790 px (70 x 151 px at 1742,1348): -76 %, NOT removed.** It is no longer pink: the nape texels take the hood colour (the sun still lifts that strip above the shadowed hood, so it reads as a lighter grey-tan patch); fix is the texels only | `evidence/thug_wedge_r8.json` / `_r9.json` (`wedge_4k.py`), `captures/crops_3x/thug-collar_3x.jpg` |
| civilians: rear shin horizontal at 18 % of stature | crowd walks lift the swing ankle 14.0 - 20.9 % of stature (walkF 18.8 %) | **capped at 10 %: 9.9 - 10.5 % measured in the exported FBX takes of all 18 citizens** (sole height above the floor, 5 walk styles); in the crowd clip the rear foot of the hijab walker at 0.25 s is about 25 cm above the floor instead of a horizontal shin | `evidence/fbx_lift_citizens.json` (`fbx_lift.py`, Blender), `captures/crowd_tracking.mp4` |
| rigid civilian coats | hem weights: 50 % thighs, 30 - 45 % pelvis (hijab coat) | **unchanged** (not attempted: the coat weights already follow the thighs; no secondary cloth motion) | - |

## Not changed in round 09 (round-08 numbers stand)

Hero model, suit, eyes and hero clips (`round-08/captures/hero_*` are the current captures), crowd density (10 - 11 people in `crowd_tracking`, CH16 low end), hero showcase framing (0.79 H vs CH1 0.48 - 0.62), run start / stop / turn / idle clips (CH10, section 5), crowd head contacts, citizen triangle counts.

## Offline checks that preceded the engine runs (not game results)

- `choreo.py --check` (script timeline), `preview_cpu.py` (real meshes posed and blended like the engine: caught the hero hidden behind a foreground enemy and the Brute filling the wide shot), `preview_cpu.py --bones` (the script's predicted bone log: `evidence/script_expected_check.json`, `script_contact_check.json`); the engine's own log reproduced the predicted knockdown intervals to the millisecond (9.017 - 11.95 s, 12.733 - 15.65 s).
- `pose_view.py` (CPU): the thug wedge was reproduced without the engine; `nape_fix.py` went through four iterations on it (the first two missed the strip because of a skin-hue threshold that excluded dim skin texels and a radius window that excluded the hood-collar triangles).

## Honest notes

- The first real-time 4K stills (`-shots`) showed other moments of the choreography than their names: the automation clock of a real-time run leads the stage clock by a varying 0.4 - 2.4 s. The final stills use `-WHStageShot` (stage-clock screenshots, `stage T=3.802 / 13.612 / 19.000` in `gF1.log`); the first, wrongly timed still is kept as `evidence/lagged_realtime_still_9.6_automation_clock.jpg`.
- The first bone log had (0,0,0) for hands and feet (UE names them `hand_L`, ...): fixed in `WHCharShowDirector.cpp`; every number above is from the corrected log.
- Tee knockdown (8.4 - 11.9 s) is mostly hidden behind the hero from the 3/4 camera; the Thug knockdown (12.7 - 15.6 s) lies in plain view (and is the one in the 4K still).
- The hero is in the Tessera suit in every frame; the three unarmed / armed enemy ABPs keep a relaxed (armed) or boxing (unarmed) base idle.
