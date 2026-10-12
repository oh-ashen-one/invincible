# Round 10: captures of the running characters maps

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.

**Round target (critic r09, single biggest gap):** in EVERY 8 s fight clip (`street_fight_34` and `street_fight_wide`, which had 0 knockdowns) >= 4 hit reactions (head / torso >= 0.1 stature within 0.2 s of contact), >= 2 knockdowns with 2 enemies down together >= 1 s, >= 2 distinct get-ups, no enemy holding one guard pose > 2 s. Regression first: the untextured grey "hero arm" at 1.30 - 1.50 s. Secondary: thug collar wedge, hair-card faults, hijab walker's rear shin. Numbers: `SPEC_CHECK.md`.

**Source.** Real `-game` runs (UE 5.8.3, Metal, offscreen `-RenderOffScreen -NoSound`) through `unreal/WebHomage/Scripts/run_game.sh` (driver `tools/ue_char/capture_r5.sh`), 2026-10-01 00:05 - 01:00 for the final fight files. Content rebuilt from the committed scripts with `tools/ue_char/fight/build_fight.sh clean,tex,mat,mesh,citizens,rename,fightclips,abp,map,maps5,mapkey,mapavoid` (full wipe + rebuild, ~66 s in the lock after 7 min in the queue; no `.uasset` / `.umap` is committed) after `tools/ue_char/people/build_people.sh` (new weapon fit) and `choreo.py` (new `fight_script.json`). Every Unreal launch (builds, captures) went through `gpu_slot.sh capture --label characters`, one engine of mine at a time; nothing was bypassed; every release logged `exit=0 contaminated=true reasons=no-exclusive-lock`: **no frame time here is a performance result**. The lock's cap was 1 slot for most of the session (health monitor) and the queue wait per launch was 7 - 26 min.

**Which build made which file.** The three fight clips, the bone log (`evidence/fight_bones_final.csv.gz`) and the three 4K fight stills come from the FINAL build (weapon tilt -10 deg, re-timed choreography). The five enemy faces (`*_face_4k.jpg`) come from the build before it (the clean rebuild of 2026-09-30 22:21, identical face meshes and textures; only the weapon fit and `fight_script.json` differ) and were captured 2026-09-30 23:40: a re-take on the final build was queued but waited 1 h behind other agents' jobs and I cancelled it by PID (nothing of it ever started). An earlier capture of the first round-10 build (weapon tilt +58 deg) is NOT in this folder; its numbers are quoted in `SPEC_CHECK.md` section 0 as "before".

**Resolution (disclosed).** Stills: native 3840 x 2160 output, internal 3840 x 2160 (`r.ScreenPercentage 100`, mode `manual`, `evidence/gF1_perf_final_stills.json`). Movies: fixed-step `-movie` runs (1/60 s), 1920 x 1080 output = 1920 x 1080 internal, H.264 crf 20, motion blur off, every clip <= 15 MB (3.5 / 4.3 / 5.2 MB); `-movie` output says nothing about real-time speed. The 4K stills are real-time runs (34 fps average on the shared GPU, contaminated). The stills are stage-clock screenshots (`-WHStageShot`: stage T = 4.604 / 12.003 / 20.802 s).

**Clip timing.** The capture director's shot 0 lasts 8.6 s (0.6 s of texture-streaming warm-up + a full 8 s clip), so every clip is a full 8.0 s: `street_fight_wide.mp4` = stage 0.65 - 8.65 s, `street_fight_34.mp4` = 8.65 - 16.65 s, `street_fight_orbit.mp4` = 16.65 - 24.65 s (clip time = stage time - 0.05 s).

## What changed in the content this round

- **Hand weapons** (`tools/ue_char/weapons/add_weapon.py`): tilt of the bat / pipe in the fist +58 -> -10 deg. The Brute's pipe (and the Thug's bat) no longer pass through the hero: 0.00 s of 24 s inside his body (was 1.40 s pipe, 5.80 s bat; `tools/ue_char/fight/weapon_clip_check.py`). The pipe is gunmetal (round-10 WIP).
- **Fight choreography v2** (`tools/ue_char/fight/choreo.py`, `fight_script.json`): per 8 s window 2 knockdowns (two enemies down together 1.8 - 1.95 s, 2 different get-ups: `getUp` = the hero's backward roll, `getUp2` = new elbow-propped sit-up through a squat authored in `make_fight_clips.py compose_getup2`), 4 - 5 more hit reactions, one enemy blow that lands on the hero, feints / shuffles so nobody keeps one guard > ~2 s, shove impulse on every reaction, knocked-down bodies end 150 cm from the hero (feet clearance 40 - 50 cm). Round-10 re-timing of two enemy blows (the hero had been turned away mid-punch).
- **Street enemies:** Hood loose hair-ribbon shells removed, Beard temple hair gap bridged, Beard / Hood hair materials two-sided, thug nape strip: vertex normals turned to the collar direction + hue-preserving shade.
- **Tooling:** `fight/r10_check.py`, `fight/weapon_clip_check.py`, `fight/video_grounded.py`, `crops_r10.py`, `analyze_r10.sh`, `make_pairs_r10.py`, `capture_r5.sh` (8.6 s first shot).

## Files

| File | Shot | Content |
|---|---|---|
| `street_fight_wide.mp4` | Char_Fight shot 0, stage 0.65 - 8.65 s | wide camera: walk-in, Thug and Oxblood knocked down (both on the ground 3.0 - 4.8 s of the clip), the pistol-whip lands on the hero, backward-roll and sit-up get-ups |
| `street_fight_34.mp4` | shot 1, stage 8.65 - 16.65 s | 3/4 camera: Hood and Beard knocked down, bat swing lands, get-ups |
| `street_fight_orbit.mp4` | shot 2, stage 16.65 - 24.65 s | orbiting camera: Brute and Tee knocked down, Beard hit twice |
| `street_fight_wide_4k.jpg`, `street_fight_34_4k.jpg`, `street_fight_orbit_4k.jpg` | stage 4.6 / 12.0 / 20.8 s (real-time 4K, stage-clock screenshots) | two enemies on the ground in each |
| `street_fight_1080.jpg` | movie frame | one 1080p frame of the movie run |
| `thug_face_4k.jpg`, `tee_face_4k.jpg`, `brute_face_4k.jpg`, `hood_face_4k.jpg`, `beard_face_4k.jpg` | Char_Lineup 10 - 14 | enemy face close-ups |
| `crops_3x/` | | 3x Lanczos crops, this round (`r10_*`) against round 09 (`r9_*`): `arm` (street_fight_34 1.30 / 1.40 / 1.50 s, the region of the r09 grey limb), `hero_wide|34|orbit` (hero-centred, same three instants of every clip), `thug-collar`, `beard-hair`, `hood-hair` |

**Not re-captured this round (content unchanged; the earlier files stand):** every `hero_*` clip and still (`round-08/captures`), `suit_closeup_4k`, `crowd_*` clips and stills (`round-09/captures`), `crowd_key_*`, the walker telemetry, `crowd_id_*`. The blind critic pack uses the round-08 hero files for the standing hero pairs and the round-09 crowd files for the crowd pair.

## Evidence (`evidence/`)

- Fight: `fight_bones_final.csv.gz` (the real bone log, 60 Hz, 7 walkers x 7 joints), `r10_check.json` (+ `r10_check_on_r9_log.json`: the same instrument on the round-09 log), `contact_check.{json,txt}`, `facing_check.json`, `weapon_clip_r10_before|after.json`, `grounded_*.json` / `grounded_r9_*.json` (YOLO lying-people check), `video_activity_*.json`, `count_videos.txt`, `yolo_*_4k.json`, `gF1_perf_final_stills.json`.
- Faces: `tee_seethrough_r10.json`, `thug_wedge_r10.json`.

## Incidents to disclose (nothing left running)

- The first capture of the round-10 choreography (before the weapon and timing fixes) was taken, measured (all windows PASS on the bone log) and then rejected after looking at the frames: the Brute's pipe still pierced the hero's back at 3.25 - 3.45 s, the Thug's bat his waist, and the hero faced away from the Tee at the instant of a punch (165 deg). Those files were kept in scratch only, not committed.
- `build_fight.sh` wipes the two content folders BEFORE it waits for the lock; a queued capture would find an empty content folder if a rebuild were launched meanwhile (I did not).
- The lock queue was 7 - 26 min per launch and the cap was 1 slot for most of the session; no launch was forced.
- A re-take of the face stills on the final build was queued in the lock for ~1 h (cap 1, a perf run and two other agents' holds ahead) and cancelled by PID before it started; the face files are the identical-content ones of the build before.
- Frame dumps of the movie runs (3 GB each) were deleted from scratch after the clips were cut.
