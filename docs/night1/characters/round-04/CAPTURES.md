# Round 04: captures of the running lineup map

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.

**Source:** real `-game` runs of `/Game/Tests/Characters/Char_Lineup` (UE 5.8.3, Metal, offscreen, `-RenderOffScreen -NoSound`) through F1's `unreal/WebHomage/Scripts/run_game.sh`. `AWHCharShowDirector` drives the camera. Content rebuilt headless (`tools/ue_char/build_characters_headless.sh`, `-nullrhi` commandlet). Every Unreal launch (build commandlet, movie runs, still runs) and the headless browser check ran inside `gpu_slot.sh capture --label characters`; every release logged `contaminated=true reasons=no-exclusive-lock` (a shared capture slot, not an exclusive perf lock).

**Movies (1080p60):** `tools/ue_char/capture_segments.sh` = three short fixed-step `-movie` runs (1920x1080, 1/60 s step, H.264 crf 20, motion blur on) instead of round 03's single 91 s run: A = director shots 1-3 (hero), B = shots 5-9 (enemies), C = shots 15-16 (civilians). The first 3 frames of each run are the default camera before the director's first cut (measured by frame differencing), so clips are cut at +0.05 s (`SEG_OFFSET=0.05`). Internal resolution of the 1080p output: the auto screen percentage (not re-measured). `-movie` output says nothing about real-time speed.

**Stills (native 4K):** `tools/ue_char/capture_4k_stills.sh`, real-time runs with `-exec "r.ScreenPercentage 100,r.MotionBlurQuality 0"`; every group's perf json reports internal 3840x2160, `screen_percentage_mode` manual (`evidence/perf_4k_groups_contaminated.json`; frame times there are contaminated by the shared GPU and are not a perf result). The director clock drifts behind the automation clock in real-time runs, so each group starts at its own shot; the three 3 s face shots (hood, tee, beard) now have one run each. The `hero_takeoff_4k` / `hero_jump_4k` stills landed before the takeoff (drift); the takeoff is measured on the movie.

**Build order this round (what each capture shows):**
- A (hero clips, `hero_run_*`): after the second lean edit of `run` (clip-level head-to-hip lean 25.6 deg).
- C (civilians): after the civilian start positions were pulled together (x 0.45) and the tracking camera moved to 11.5 m / FOV 64.
- B (enemies) and the enemy 4K stills: after the pistol holders were switched from `thugGunAim` (deep crouch aiming ~40 deg up) to a standing idle with the pistol lowered. The hood face still is from the final build (lettering removed from the sunglasses temple); the B movie predates that texture change (the lettering is below 1 px at 1080p there).

| File | Shot | Content |
|---|---|---|
| `hero_run_side.mp4` (6 s) | side, 5.6 m, FOV 40 | Hero running +X on the lineup street, no hop. |
| `hero_run_34.mp4` (5 s) | three-quarter, 4.8 m | Same run. |
| `hero_run_jump_side.mp4` (6.5 s) | side, 6.2 m, FOV 42 | Run, takeoff crouch at 1.35 s, jump, landing, run again (second jump at about 4.3 s). |
| `enemy_lineup.mp4` (11 s) | wide 0-6 s, three-quarter 6-11 s | Seven street enemies in two staggered rows: 2 bats, 2 pipes, 2 pistols, 1 unarmed; 5 outfits + 2 tint variants. |
| `thug_brute_pair_side.mp4` (6 s) | side tracking 4.2 m | Thug (bat) and brute (pipe) walking abreast. |
| `thug_side_3m.mp4`, `brute_side_3m.mp4` (5 s each) | side tracking 3 m | One enemy each, walking at the clip's foot speed (114 / 110 cm/s). |
| `civilians_tracking.mp4` (8 s) | side tracking 11.5 m, FOV 64 | 12 civilians, both directions, camera following a tracker at 1.1 m/s. |
| `civilians_wide.mp4` (6 s) | wide, static | Same 12 civilians from behind / three-quarter. |
| `enemy_lineup_1080.jpg`, `civilians_tracking_1080.jpg`, `civilians_wide_1080.jpg` | | 1080p frames of the movies. |
| `*_4k.jpg` (18 files) | | Native 3840x2160: hero turntable / run side / run 3/4 / takeoff / jump / suit close-up; enemy lineup wide / 3/4; pair side; thug 3 m; brute 3 m; thug / brute / hood / tee / beard face; civilians tracking / wide. |

**Lighting:** unchanged from round 03 (sun 8 lux + atmosphere, real-time sky light, height fog, auto exposure; 4 shadowless fills on lighting channel 1, enemies only). Test stage, not the city.

**Evidence (`evidence/`):** `video_hero_run_side.jsonl` (step rate + lean on the side run), `hero_takeoff_r4.json` + `hero_liftoff_strip_1500-1667ms.jpg`, `hero_clips_r4.json` (clip-level, `measure_clip.py`), `hero_run_r4b_side_blender.jpg` (Workbench, final `run`), `yolo_*.json` (YOLO11x person counts, same weights as `specs/tools`), `civilians_tracking_legs_strip.jpg` (legs every 5 frames), `crowd_gait.json`, `enemy_heads_ortho.jpg`, `prep_*.json`.
