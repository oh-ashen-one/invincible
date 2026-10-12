# Round 05: captures of the running characters maps

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.

**Source:** real `-game` runs (UE 5.8.3, Metal, offscreen `-RenderOffScreen -NoSound`) through F1's `unreal/WebHomage/Scripts/run_game.sh`, driven by `tools/ue_char/capture_r5.sh`. Content rebuilt headless (`tools/ue_char/build_characters_headless.sh`, `-nullrhi` commandlet, ~50 s). Every Unreal launch (build, movie runs, still runs) ran inside `gpu_slot.sh capture --label characters`; every release logged `contaminated=true reasons=no-exclusive-lock` (a shared capture slot, not an exclusive perf lock), so **no frame time here is a performance result**.

**Maps (all light: sun 8 lux + atmosphere, real-time sky light, height fog, auto exposure; 4 shadowless fills on lighting channel 1 for the characters in the fight; a test stage, not the city):**
- `Char_Hero`: hero only (the director hides every other actor per shot). Shots: whole-body turntable, run side, run 3/4, run -> leap side, chest close-up, face + lens close-up, **chase camera (behind, 5 m, FOV 62)**, **toward the camera (5.6 m)**.
- `Char_Fight`: hero (`ABP_Hero_Fight` sequence) in the middle of 6 enemies (bat, pipe, pistol carriers relaxed with the weapon hanging until they swing; three unarmed enemies in the boxing guard punching / kicking / reeling).
- `Char_Crowd`: 18 distinct citizens, two-way flow: mid lane 6 walking +X and 6 walking -X, near lane (4.5 m from the tracking camera) 3 + 3; gait phases spread by the golden ratio.
- `Char_CrowdKey`: `Char_Crowd` with street / facades / windows replaced by an unlit pure-green material, no fog, no sky. Green enclosed by a person = see-through crack (`tools/ue_char/eval/key_holes.py`).
- `Char_Lineup`: standing enemies, used for the five face close-ups only.

**Movies (1080p60, fixed-step `-movie` runs: 1/60 s step, H.264 crf 20, motion blur OFF (`r.MotionBlurQuality 0`)):** frames before the director's first cut are the default camera, so clips are cut at +0.05 s. `-movie` output says nothing about real-time speed. Internal resolution = output resolution (1920x1080, screen percentage 100 by default in `-game`; not upscaled).

**Stills (native 3840x2160):** real-time runs with `-exec "r.ScreenPercentage 100,r.MotionBlurQuality 0"`; every group's perf json reports internal 3840x2160, manual screen percentage (`evidence/perf_4k_groups_contaminated.json`). The director clock runs behind the automation clock, so shots are 6-8 s long and several stills share one run. The leap still comes from a fixed-step 4K `-movie` run (blur off; frames 1.85 s and 1.95 s).

**Which run each file comes from (three content builds happened during the round; the hero, enemies, weapons and hero maps are identical in all of them, only the citizens and the maps' shot lists changed):**
- Hero movies (`hero_run_*`), `hero_turntable_4k`, `hero_jump_4k`: second build, blur off.
- Fight movies (motion blur ON, the first capture batch), fight and face 4K stills, `suit_closeup_4k`, `hero_face_lens_4k`, `hero_run_side_4k`: first batch (`hero_turntable_4k` there cut the legs off, replaced by the whole-body one).
- Crowd movies, `crowd_*_4k`, `crowd_key_*`: final build (skirt rig, hull fixes, 3 mm expanded triangles).
- `crowd_key_before_*`: the same key shots on the build before those citizen changes (the WIP citizens Opus 5.5 left, hull v1), captured after the interruption.

| File | Shot | Content |
|---|---|---|
| `hero_run_side.mp4` (6 s), `hero_run_34.mp4` (5 s) | side 5.6 m / 3/4 4.8 m, FOV 40 | Hero running on an empty street |
| `hero_run_leap_side.mp4` (6.5 s) | side 8.2 m, FOV 42 | Run, take-off crouch (1.3 s), `runLeap`, landing, run, second jump (`runLeapB`) |
| `hero_run_chase.mp4` (6 s), `hero_run_toward.mp4` (6 s) | behind 5 m / toward 5.6 m, FOV 62 | Gameplay cameras (CH1 / CH2) |
| `street_fight_wide.mp4`, `street_fight_34.mp4`, `street_fight_orbit.mp4` (8 s each) | static wide 10 m / static 3/4 / orbit 9.5 m | The staged fight (blur on, earlier run) |
| `crowd_tracking.mp4` (8 s), `crowd_wide.mp4` (6 s) | side tracking 11.5 m, FOV 64 / wide | Two-way flow, near-lane walkers |
| `*_1080.jpg` | | 1080p frames of the movies |
| `hero_turntable_4k` (whole body), `hero_run_side_4k`, `hero_jump_4k`, `suit_closeup_4k`, `hero_face_lens_4k` | | Hero: moving turntable, run side, the leap at its apex, chest close-up (weave, thread relief), face + lens close-up |
| `street_fight_wide_4k`, `street_fight_34_4k`, `street_fight_orbit_4k` | | The fight |
| `crowd_tracking_4k`, `crowd_wide_4k` | | The crowd (CH18 test image) |
| `crowd_key_*_4k`, `crowd_key_before_*_4k`, `keyholes_*.png` | | Chroma-key crowd (final / before) and the detected holes (red = thin cracks, magenta = wide gaps) |
| `thug_face_4k`, `brute_face_4k`, `hood_face_4k`, `tee_face_4k`, `beard_face_4k` | | Masks and faces of the five enemies |

**Evidence (`evidence/`):** `cracks_stills.txt` (critic's `cracks.py`), `cracks_classify.jsonl` (`eval/cracks_classify.py`: flagged components split into head / skin / cloth), `key_holes_cap8.jsonl` (final) / `key_holes_cap_key_before.jsonl` (before), `count_crowd.txt` / `count_fight.txt` (critic's `count.py`), `yolo_*.json`, `head_pitch_clips.json`, `video_*.json` (head bob / lean / hero height), `leap_track.json` (head-top and feet-bottom per frame through the leap), `gait_phase.json`, `hull_stats.json`, `perf_*.json` (per 4K still group: internal 3840x2160; contaminated, shared GPU), `gpu_util_before_4k.txt`.
