# Round 07: captures of the running characters maps

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.

**Round target (critic r06, single biggest gap):** walker avoidance with a capsule radius of at least 0.35 m, the key see-through fix, then re-capture `crowd_key_c_4k` and `crowd_key_a_4k`: zero pixels with G>R+40 inside a garment silhouette, no two walker masks overlapping, no detached polygon larger than 4 px; close the 3 ankle-cuff gaps; prove it with 3x crops. Numbers: `SPEC_CHECK.md`.

**Source.** Real `-game` runs (UE 5.8.3, Metal, offscreen `-RenderOffScreen -NoSound`) through `unreal/WebHomage/Scripts/run_game.sh` (driver `tools/ue_char/run_r7_captures.sh`, key movie `tools/ue_char/crowd/key_movie.sh`, id movie `tools/ue_char/crowd/id_movie.sh`), 2026-09-30 13:03-15:5x. Content rebuilt from the committed scripts (`build_characters.py`, steps `clean,tex,mat,mesh,citizens,rename,abp,map,maps5,mapkey,mapavoid`; the refit citizens of round 06 plus the round-07 ankle skin gradient); no `.uasset` / `.umap` is committed. Every Unreal launch (builds, telemetry runs, captures) went through `gpu_slot.sh capture --label characters`, one engine of mine at a time, waiting up to 20 min behind other agents' exclusive perf runs; nothing was bypassed. Every release logged `contaminated=true reasons=no-exclusive-lock` (shared capture slot): **no frame time here is a performance result**.

**Resolution (disclosed).** Stills: native 3840x2160 output, internal 3840x2160 (`r.ScreenPercentage 100`, mode `manual`, in every `evidence/perf_*.json`). The two key stills `crowd_key_a_4k.png` / `crowd_key_c_4k.png` are frames of a fixed-step 4K movie run (`key_movie.sh`: 3840x2160 output = internal, 1/60 s steps, motion blur off), picked by frame number. Movies: fixed-step `-movie` runs, 1920x1080 output = 1920x1080 internal, H.264 crf 20 (crf 17 for the four trimmed clips), motion blur off, every clip <= 5 MB. `-movie` output says nothing about real-time speed.

**Trimmed clips (texture-streaming warm-up).** The first ~0.4 s of every `-movie` run shows the lowest texture mips and the walkers standing in the rest pose. The first clip of each run (`hero_run_side`, `hero_run_chase`, `street_fight_wide`, `crowd_tracking`) therefore starts 0.6 s into the run (`tools/ue_char/trim_clips_r7.sh`, re-encoded crf 17). The 0.5-5.9 s measurement windows were taken on the trimmed clips where they still fit.

## What changed in the content this round

- **Crowd layout** (`build_characters.py` `MID7` / `NEAR7`, found by `tools/ue_char/crowd/layout_search.py --seed 1 --flip`): straight lanes that keep every pair of walkers >= 130 cm apart for 2 s beyond both director shots, two-way flow in the mid lane, the near lane walks one way (with the tracking camera) so no two near-lane silhouettes ever overlap on screen. Same 18 citizens.
- **Walker avoidance** (C++ `AWHCharLoopWalker`, `bAvoid`, capsule radius 40 cm): each walker looks 2 s ahead at where the others will be and steps sideways (never faster than 0.47 x its own speed, right-hand bias) so that no two capsules overlap; whatever is left at the current instant is pushed apart (hard limit 2R + 0.5 cm). On in every citizen of `Char_Crowd`; `Char_CrowdAvoid` = the round-06 (colliding) layout WITH avoidance, the engine test of the avoidance itself; `-WHNoAvoid` switches it off for the A/B baseline.
- **Chroma key replaced.** Round 05/06 keyed the street geometry; its green bounce and green sky capture tinted every garment, which the critic read as "key-green jeans" (the rear leg of `crowd_key_c_4k`, 19.5k px of green-lit JEANS, not a hole). `Char_CrowdKey` is now a copy of `Char_Crowd` (identical sun, sky, fog, street) whose citizens write custom-depth stencil; a post-process material before bloom with the material's own stencil test (== 0) paints every non-citizen pixel one flat key green (measured (8,235,3) after tonemapping) and never touches a citizen pixel. UE 5.8 cannot read custom stencil after tonemapping (`PostProcessMaterial.cpp`: "target size differences"); the first attempt did exactly that and came out with a 90 px smeared border and no key (kept out of the evidence). Bloom and vignette are off in the key / id maps. `Char_CrowdID`: each citizen's pixels carry its own colour (id = r + 3g + 9b, three levels per channel), everything else black.
- **Mid-lane walkers stand on the pavement.** The south sidewalk box is 30 cm thick centred on z = 0 (top face z = +15 cm) and every round so far spawned the mid lane at z = 0: shoes and ankles were 15 cm inside the pavement. The stencil key exposed it as pale foot-shaped blobs (custom stencil ignores scene occlusion); in round 06 the same buried ankles were the "ankle-cuff gaps" (the green floor plane slicing through the foot). Mid lane now spawns at z = 15 cm.
- **Ankle skin gradient** (`tools/ue_char/eval/weights_r6.py` `ankle_blend`): shin <-> foot weights blend across the ankle joint so a cuff and the shoe collar under it move together (offline: cross-shell openings above 5 mm 358 -> 100 pairs, 18 citizens).

## Files

| File | Shot | Content |
|---|---|---|
| `crowd_tracking.mp4` (7.4 s, trimmed), `crowd_wide.mp4` (6 s) | side tracking 11.5 m, FOV 64 / static wide | the round-07 crowd (two-way flow, near lane one way, avoidance on) |
| `crowd_avoidance_demo.mp4` (8 s) | same tracking camera | the ROUND-06 layout (walkers that walked through each other) with avoidance on: the A/B of the avoidance alone |
| `crowd_tracking_4k`, `crowd_wide_4k` (+ `_1080` movie frames) | | the crowd, colour |
| `crowd_key_a_4k.png`, `crowd_key_c_4k.png` | frames 194 / 261 of the 4K key movie (game 3.18 s / 4.30 s into the shot; picked with the id movie where no near-lane silhouette touches a mid-lane walker, `_c` has one mild contact); the real-time stills at 3.5 / 7.5 s are in `evidence/realtime_key_stills/` | stencil-keyed crowd (CH18 test images) |
| `crowd_key_tracking_4k.png`, `crowd_key_wide_4k.png` | real-time stills 5.5 s / 11.5 s | stencil-keyed crowd |
| `crowd_id_*_4k.png` | real-time stills | per-walker id masks (id map in `evidence/stencil_ids.json`) |
| `hero_run_side`, `hero_run_34`, `hero_run_leap_side`, `hero_run_chase`, `hero_run_toward` (.mp4), `hero_turntable_4k`, `hero_run_side_4k`, `hero_jump_4k*`, `suit_closeup_4k`, `hero_face_lens_4k` | | hero (content unchanged since round 05, re-captured) |
| `street_fight_wide`, `street_fight_34`, `street_fight_orbit` (.mp4), `street_fight_*_4k`, `street_fight_1080` | | the fight (unchanged, re-captured) |
| `thug_face_4k`, `brute_face_4k`, `hood_face_4k`, `tee_face_4k`, `beard_face_4k` | | enemy faces (unchanged, re-captured) |
| `crops_3x/*_3x.jpg` | | **3x Lanczos crops, round 06 (left) | round 07 (right)** of the regions the critic named: `jeans-leg`, `overlap-near`, `ankle-close`, `floating-shape` |

## Evidence (`evidence/`)

- `telemetry/`: per-frame walker telemetry of the engine (`*_walkers.csv.gz`: frame, time, label, x, y, yaw, lane offset, smallest centre distance) and `*_separation.json/png` (smallest centre-to-centre distance between any two walkers, per rendered frame): `avoid_off_r6layout` (round-06 layout, avoidance OFF), `avoid_on_r6layout` (same, ON), `crowd_r7layout` (round-07 layout, nullrhi), `crowd_walkers` (the very `-movie` run the crowd clips are cut from).
- `keycheck/`: `key_check_r7.py` per still (`*_check.json`, overlays `*_check.png`), the enclosed-gap montages `*_components.jpg` (classified by eye), `spikes.jsonl`; `keycheck_round06/` = the same tool on the round-06 stills.
- `id_overlap_*.json`: per-walker silhouettes of the id movie frame by frame (visible walkers, touching pairs).
- `ankle_gap_*`, `island_drift_round07.txt`, `offline_ch18_gate_round07.json`: offline mesh checks of the ankle gradient.
- `count_videos.txt`, `yolo_*`, `video_hero_run_*`, `leap_track.json`, `gait_phase.json`, `cracks_*`: the other SPEC lines.
