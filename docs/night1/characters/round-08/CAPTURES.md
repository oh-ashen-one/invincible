# Round 08: captures of the running characters maps

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.

**Round target (critic r07, single biggest gap):** replace the copied suit layout with an original one (`SUIT_ORIGINALITY.md`), rebuild each eye lens as one closed rim sealed to a lens that sits inside the head silhouette, re-capture `hero_face_lens_4k` plus the hero turnaround and run clips, and check at 3x crops: 0 background pixels between rim and lens, no lens beyond the mask outline, no web-line stair step wider than 2 px. Secondary: the shoe shards, the thug collar shards, lips poking through the mask, the two fused heads in `crowd_tracking_4k`. Numbers: `SPEC_CHECK.md`.

**Source.** Real `-game` runs (UE 5.8.3, Metal, offscreen `-RenderOffScreen -NoSound`) through `unreal/WebHomage/Scripts/run_game.sh` (driver `tools/ue_char/run_r8_captures.sh`, groups `H X E F D C Q M S K`; crowd key movie `tools/ue_char/crowd/key_movie.sh`, colour movie `colour_movie.sh`, id movie `id_movie.sh`), 2026-09-30 16:46 onward. Content rebuilt from the committed scripts (`build_characters.py`, steps `clean,tex,mat,mesh,citizens,rename,abp,map,maps5,mapkey,mapavoid`; the hero maps are the 8192 Tessera maps of `hero_suit_r8.py`, the eyes come from `hero_lens_r8.py`); no `.uasset` / `.umap` is committed. Every Unreal launch (builds and captures) went through `gpu_slot.sh capture --label characters`, one engine of mine at a time (other agents held both slots for up to 25 min per launch; nothing was bypassed). Every release logged `contaminated=true reasons=no-exclusive-lock` (shared capture slot): **no frame time here is a performance result**.

**Resolution (disclosed).** Stills: native 3840x2160 output, internal 3840x2160 (`r.ScreenPercentage 100`, mode `manual`, in every `evidence/perf_*.json`). The hero key stills (`hero_key_*_4k.png`) and the four crowd key stills `crowd_key_*_4k.png` are lossless PNG (a 4:2:0 JPEG would bleed the key colour into edge pixels); the crowd stills picked by frame number come from fixed-step 4K movie runs (output = internal 3840x2160, 1/60 s steps, motion blur off). Movies: fixed-step `-movie` runs, 1920x1080 output = 1920x1080 internal, H.264, motion blur off, every clip <= 15 MB; `-movie` output says nothing about real-time speed. The hero maps are 8192 x 8192 (base colour, normal, ORM): BC compressed in the engine, a texel is 0.15 mm on the face (6,650 texels/m on the head, about 4,600 on the body) so a 4K close-up magnifies each texel 2x.

**Trimmed clips (texture-streaming warm-up).** The first ~0.4 s of every `-movie` run shows the lowest texture mips and the walkers in the rest pose. The first clip of each run (`hero_run_side`, `hero_run_chase`, `street_fight_wide`, `crowd_tracking`) therefore starts 0.6 s into the run (`tools/ue_char/trim_clips_r8.sh`, re-encoded crf 17); the untrimmed originals are in `untrimmed/` (scratch only).

## What changed in the content this round

- **Hero suit**: the original Tessera suit (procedural, 8192 maps), see `SUIT_ORIGINALITY.md`. Material: Cloth shading with a teal fuzz colour, tiled 2/2 twill detail normal (0.45 mm yarn), per-panel roughness.
- **Hero eyes**: one closed bezel ring per eye, sealed to a lens dome, both conformed to the mask surface; amber lens, graphite bezel (`hero_lens_r8.py`).
- **Street enemies**: tee mask hangs over the mouth (`mask.hang(uncover_mouth=True)`), thug collar (`mask.sink_neck`, softened neck atlas texels).
- **Citizens**: the triangles that float as detached polygons (`shards_r8.py`: skater 50, punk artist 2, chrome shades 1) are dropped; offline CH18 cracks did not rise (`evidence/offline_ch18_gate_round08_changed.json`).
- **New test map** `Char_HeroKey` (hero on the stencil key, flat class colours with `-WHFlatClasses`) and the tools that read it.

## Files

| File | Shot | Content |
|---|---|---|
| `hero_turntable_4k.jpg` | Char_Hero shot 0, 4.5 s | hero moving turntable, whole body (round 07: same shot, old suit) |
| `hero_run_side.mp4` (trimmed), `hero_run_34.mp4`, `hero_run_leap_side.mp4`, `hero_run_chase.mp4` (trimmed), `hero_run_toward.mp4` | Char_Hero shots 1-3, 6, 7 | hero run side / 3/4 / run -> leap / chase (behind) / toward the camera |
| `hero_run_side_4k.jpg`, `hero_jump_4k_t1.85.jpg`, `hero_jump_4k_t1.95.jpg` | | 4K stills of the run and the leap apex |
| `suit_closeup_4k.jpg` | Char_Hero shot 4, 3.0 s | suit fabric close-up (chest, shoulder cap, badge, net, stitching) |
| `hero_face_lens_4k.jpg` (+ `_a`, `_b`) | Char_Hero shot 5, 10.0 s (+ 8.0 s, 11.5 s) | hero face + eye close-up, three turntable angles |
| `hero_key_face_4k.png` (+ `_a`, `_b`), `hero_key_suit_4k.png` | Char_HeroKey shots 5 / 4 | the same shots on the stencil key with flat class colours (lens magenta, bezel yellow, suit blue, key green); read by `lens_check_r8.py` |
| `street_fight_wide.mp4` (trimmed), `street_fight_34.mp4`, `street_fight_orbit.mp4`, `street_fight_*_4k.jpg`, `street_fight_1080.jpg` | Char_Fight | the staged fight, hero + 6 enemies |
| `thug_face_4k.jpg`, `brute_face_4k.jpg`, `hood_face_4k.jpg`, `tee_face_4k.jpg`, `beard_face_4k.jpg` | Char_Lineup 10-14 | enemy faces (tee mask and thug collar changed) |
| `crowd_tracking.mp4` (trimmed), `crowd_wide.mp4`, `crowd_tracking_1080.jpg`, `crowd_wide_1080.jpg` | Char_Crowd shots 0 / 1 | the crowd (layout, avoidance, citizens unchanged except the skater, punk artist and chrome-shades triangles) |
| `crowd_tracking_4k.jpg` | frame 342 of a fixed-step 4K movie of Char_Crowd (shot 0, game 5.70 s) | crowd close-up tracking still, picked where no head touches another walker (`crowd/head_overlap.py`, `pick_frames.py`) |
| `crowd_key_a_4k.png`, `crowd_key_c_4k.png`, `crowd_key_tracking_4k.png`, `crowd_key_wide_4k.png` | Char_CrowdKey (real-time `-game`, 3840x2160, internal 3840x2160, 2026-09-30 18:39) | the crowd on the stencil key (walkers in their own colours on key green), lossless PNG; checked by `key_check_r7.py`, `spike_key.py`, `small_components_r8.py` (`evidence/keycheck/`, `evidence/small_components_round08.*`). The real-time crowd is not frame-deterministic: these are not the same frames as round 07's key stills |
| `crops_3x/` | | 3x Lanczos crops, round 07 (left) | round 08 (right): `hero-eye` (far eye, `hero_face_lens_4k` r07 x3000-3700 y740-1400 vs r08 x2780-3400 y960-1520), `hero-lines` (web lines vs piping + stitching), `thug-collar`, `tee-mouth`, `crowd-heads` |

**Not re-captured this round (content unchanged; the round-07 files stand):** `crowd_avoidance_demo.mp4` (the round-06 lanes with avoidance on; no character of this round's changes is in it), `crowd_id_*_4k.png` (per-walker id stills), the walker telemetry of the two baseline runs (`evidence/telemetry` of round 07). The four crowd key stills (`crowd_key_*_4k.png`) were captured in the last group of the round (the GPU queue held them for 26 min behind other agents' exclusive perf runs) and are in the file table.

## Evidence (`evidence/`)

- `lenscheck/`: `lens_check_r8.py --flat --auto` on the three face key stills (`*_lenscheck.json`, class overlays `*_classes.png`: magenta lens, yellow bezel, blue suit, green exterior, red = background enclosed near an eye).
- `suit_distinct.json` / `suit_distinct_atlas.jpg` / `suit_side_by_side.jpg` / `suit_design_sheet_cpu_preview.jpg`: palette and structure comparison of the old and the new suit (the last one is a CPU render of the rest pose from the real textures, four views).
- `head_overlap_crowd_tracking.json`, `id_overlap_crowd_tracking.json` (+ summaries): per-frame head contacts and silhouette contacts of the id movie; `telemetry/`: per-frame walker separation of this round's crowd run (smallest centre distance 130.0 cm).
- `count_videos_*.txt`, `yolo_*.json`, `leap_track.json`, `offline_ch18_gate_round08_changed.json`, `small_components_*.json`, `*_perf.json` (resolution of every 4K run).
