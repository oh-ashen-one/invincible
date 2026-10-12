# Round 09: captures of the running characters maps

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.

**Round target (critic r08, single biggest gap):** give the enemies real combat reactions: in a re-captured 8 s `street_fight_34` at least 3 distinct hit reactions, at least 1 knockdown with the torso on the ground for >= 1 s, and no 1 s window in which all 7 hold the guard idle. Secondary: tee-mask see-through holes, the thug collar skin wedge, rigid civilian coats, the rear shin going horizontal. Numbers: `SPEC_CHECK.md`.

**Source.** Real `-game` runs (UE 5.8.3, Metal, offscreen `-RenderOffScreen -NoSound`) through `unreal/WebHomage/Scripts/run_game.sh` (driver `tools/ue_char/run_r9_captures.sh` -> `run_r8_captures.sh` -> `capture_r5.sh`), 2026-09-30 19:55 - 20:48. Content rebuilt from the committed scripts with `tools/ue_char/fight/build_fight.sh clean,tex,mat,mesh,citizens,rename,fightclips,abp,map,maps5,mapkey,mapavoid` (full wipe + rebuild, ~100 s in the lock, four times this round; no `.uasset` / `.umap` is committed). Every Unreal launch (builds, bone log, captures) went through `gpu_slot.sh capture --label characters`, one engine of mine at a time (other agents' exclusive perf runs held the queue for 20 - 40 min per launch); nothing was bypassed; every release logged `exit=0 contaminated=true reasons=no-exclusive-lock`: **no frame time here is a performance result**.

**Which build made which file.** The fight clips, the three fight 4K stills, the bone log and the five enemy faces come from the LAST clean build (nape fix v3 in the thug atlas, stage-clock screenshots, corrected bone names). The crowd clips and crowd stills come from the build before it (identical citizen content: same FBX takes with the swing-foot lift cap, same maps; only the thug atlas and the director's bone-log names differ).

**Resolution (disclosed).** Stills: native 3840 x 2160 output, internal 3840 x 2160 (`r.ScreenPercentage 100`, mode `manual`, in `evidence/gF1_perf_final_stills.json`, `gE1_perf.json`, `gE2_perf.json`, `gC1_perf.json`). Movies: fixed-step `-movie` runs (1/60 s), 1920 x 1080 output = 1920 x 1080 internal, H.264 crf 17 - 20, motion blur off, every clip <= 15 MB; `-movie` output says nothing about real-time speed. The 4K stills are real-time runs (21 - 32 fps average on the shared GPU).

**Trimmed clips (texture-streaming warm-up).** The first ~0.4 s of every `-movie` run shows the lowest texture mips: `street_fight_wide.mp4` and `crowd_tracking.mp4` start 0.6 s into their run (`tools/ue_char/trim_clips_r8.sh` equivalent, re-encoded crf 17; stage time of `street_fight_wide` frame 0 = 0.65 s). `street_fight_34.mp4` = stage 8.05 - 16.05 s, `street_fight_orbit.mp4` = 16.05 - 24.05 s.

## What changed in the content this round

- **The fight is a script** (`tools/ue_char/fight/`, `Source/WebHomage/Characters/WHCharStage.h`, `FWHScriptBeat`, `FWHPathKey`): hero + 6 enemies, pure function of the stage clock; 57 timed clips and 577 path keys over 26 s; 15 hero strikes (punch 1 / 2 / 3, kick, uppercut at the measured contact instants) and 3 hero flinches; 20 enemy strikes (17 swings from range, 3 that land on the hero); 15 enemy hit reactions (4 stagger back, 3 recoil left, 3 stagger right, 1 brute flinch = hero `hitReact` at weight 0.55, 4 knockdowns held on the ground) and 4 get-ups (the browser thug clips written IN PLACE). Details and the rules for changing it: `HANDOFF.md`.
- **Cameras of `Char_Fight`** (all three look at the hero): wide (-30, -900, 500) FOV 52; 3/4 (-660, -335, 410) FOV 48 (between two enemies, so the hero is not hidden); orbit radius 830, camera 280 cm above the aim point, 16 deg/s from azimuth 250.
- **Street enemies:** tee mask see-through slivers flipped (`people/mask.py flip_seethrough`); thug nape texels darkened (`people/nape_fix.py`, found with `people/pose_view.py`).
- **Citizens:** swing-foot lift of the five crowd walks capped at 10 % of stature (`crowd/lift_cap.py` hooked into `eval/citizen_rig.py`); the FBX takes were re-exported for all 18.
- **Capture tooling:** `-WHBoneLog`, `-WHStageShot` (director), `STAGE_SHOTS=1` in `capture_r5.sh`, `analyze_r9.sh`, `fight_check.py`, `contact_check.py`, `video_activity.py`, `seethrough_4k.py`, `wedge_4k.py`, `fbx_lift.py`, `preview_cpu.py`, `pose_view.py`.

## Files

| File | Shot | Content |
|---|---|---|
| `street_fight_wide.mp4` (trimmed) | Char_Fight shot 0, stage 0.65 - 8.05 s | wide camera, the enemies walk in, first exchanges (stagger back, recoil, flinch) |
| `street_fight_34.mp4` | shot 1, stage 8.05 - 16.05 s | **the round target clip**: uppercut knockdown (Tee), hook, knockdown (Thug), kick, punch; feints and an enemy strike in between |
| `street_fight_orbit.mp4` | shot 2, stage 16.05 - 24.05 s | orbiting camera: brute knocked down, tee reels, oxblood knocked down, beard hit |
| `street_fight_wide_4k.jpg`, `street_fight_34_4k.jpg`, `street_fight_orbit_4k.jpg` | stage 3.8 / 13.6 / 19.0 s (real-time 4K, stage-clock screenshots) | the thug staggering after the first counter; a thug on the ground while the hero kicks the hood; the brute on the ground while the tee reels |
| `street_fight_1080.jpg` | movie frame | one 1080p frame of the movie run |
| `thug_face_4k.jpg`, `tee_face_4k.jpg`, `brute_face_4k.jpg`, `hood_face_4k.jpg`, `beard_face_4k.jpg` | Char_Lineup 10 - 14 | enemy face close-ups (tee mask and thug collar changed) |
| `crowd_tracking.mp4` (trimmed), `crowd_wide.mp4`, `crowd_tracking_4k.jpg`, `crowd_wide_4k.jpg`, `crowd_*_1080.jpg` | Char_Crowd shots 0 / 1 | the crowd with the capped swing-foot lift |
| `crops_3x/` | | 3x Lanczos crops, round 08 | round 09: `tee-mouth`, `thug-collar`, `knockdown` (the same region of the round-08 still shows the guard stance) |

**Not re-captured this round (content unchanged; the round-08 files stand):** every `hero_*` clip and still, `suit_closeup_4k`, `crowd_key_*`, the walker telemetry, `crowd_id_*`. The blind critic pack uses the round-08 hero files for the standing hero pairs.

## Evidence (`evidence/`)

- Fight: `fight_bones_final.csv.gz` (the real bone log, 60 Hz, 7 walkers x 7 joints), `fight_check_street_fight_{wide,34,orbit}.{json,txt}`, `contact_check.{json,txt}`, `video_activity_*.json`, `count_videos.txt`, `yolo_street_fight_*_4k.json`, `gF1_perf_final_stills.json`; the script's own prediction (`script_expected_check.json`, `script_contact_check.json`) for comparison.
- Faces: `tee_seethrough_r8|r9.{json,png}`, `thug_wedge_r8|r9.{json,png}` (overlays), `tee_seethrough_cpu_before_after.json`.
- Crowd: `fbx_lift_citizens.json`.
- `lagged_realtime_still_9.6_automation_clock.jpg`: the still taken at the automation clock's 9.6 s in the first real-time run (stage time ~7.2 s: nobody on the ground yet), kept as the evidence of the clock lead.

## Incidents to disclose (nothing left running)

- A first capture of the fight (old cameras, the 3/4 view hid the hero behind a foreground enemy) was queued in the lock; I cancelled it by PID before it started, changed the cameras after a CPU preview, and queued again. A partial rebuild (`fightclips,abp,maps5`) failed at `abp` (an asset that exists cannot be deleted while a map references it) and changed nothing; every later build is `clean`.
- `build_fight.sh` wipes the two content folders BEFORE it waits for the lock, so the content is empty while a build is queued.
- Real-time stills at `-shots` times were not stage-exact (see `SPEC_CHECK.md`); the first bone log had zero hands / feet (bone names); both fixed in the committed code, the first captures re-taken.
- The nape fix needed four iterations (each checked on a CPU render of the skinned thug first); the last still leaves a lighter strip.
