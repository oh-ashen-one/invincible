# Round 11 captures (first-pass piece G: the hero's original suits)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. Every suit is generated from 3D position functions (`tools/ue_char/suit8/design.py`), no image generator, no reference image of any real suit.

All frames are the REAL game (UE 5.8.3, standalone `-game -RenderOffScreen`, Metal) of this worktree, launched through `gpu_slot.sh` (cap 1; the lock refused every launch while the owner played GTA V, see `evidence/chain_gpu_wrapper.log`: waited 1458 s, then one hold of 600 s, `instances_max=1`, 0 crashes).
Chain script `tools/ue_char/suits/chain_r11_final2.sh` (out dir `$P2_SCRATCH/r11/chain4`), post-processing `tools/ue_char/suits/post_r11.sh`. Content was rebuilt in that hold by `build_fight.sh skins,skinsmap` (nothing under `/Content` is committed).

## Exposure (found and fixed this round)

The first manual-exposure stills (bias -0.3) came out BLACK. AEM_Manual exposure = camera EV100 (f/4, 1/60 s, ISO 100 = 9.9) minus the bias, and the stage's sun is 8 lux. Measured on the real map (1080p cinder front, bare-floor luma, sRGB): bias +9 -> 121, bias +10 -> 172 (auto exposure gave 170 on the same floor in the first chain). The stage now runs a fixed **+10.0** (`build_characters.py` `skin_ev`, every run also passes `-WHExposure=10.0`): a dark suit filling the frame is no longer brightened to pastel and all eight suits are lit by the same fixed exposure. Floor luma of the final tessera front still: 172.2. Numbers and the two calibration frames: `evidence/exposure_calib.txt`, `evidence/exposure_ev9_cinder_front.jpg`, `evidence/exposure_ev10_cinder_front.jpg`.

## Files

| id | file | what | how / resolution |
|---|---|---|---|
| S1 | `stills/skin_<suit>_front_4k.jpg` x 8 | every suit, full body, front | 3840x2160 output, **internal 3840x2160** (`r.ScreenPercentage 100`, screen-percentage mode manual, `evidence/stills_perf.json`), real-time run, stage-clock screenshot 2.2 s into each 3 s shot |
| S2 | `stills/skin_<suit>_back_1080p.jpg` x 8 | back | same 4K capture, **committed at 1920x1080** (repo size); the 4K originals stay in the scratch dir `r11/chain4/stills_a` and went into the critic pack |
| S3 | `stills/skin_<suit>_chest_4k.jpg` x 8 | chest close-up (glyph, net, sash, stitching) | 3840x2160, internal 3840x2160 |
| S4 | `stills/skin_<suit>_head_1080p.jpg` x 8 | head close-up (hood, lens, vent) | 4K capture, committed at 1920x1080 |
| S5 | `SWATCH_SHEET.jpg` | all eight suits, front + back + chest on one sheet (for the owner) | composed from S1 - S3 by `swatch_sheet.py`, 5464x1744 |
| S6 | `swap_pawn_T_key.mp4` | the PLAYABLE pawn (`AWebTravCharacter`, P3's, unedited) wearing the hero, plum from the console `wh.Suit 2`, then 7 REAL T key presses (injected through the player controller) cycle cinder, glacier, ash, saffron, sage, tessera, verdant; the run ends in verdant | 1920x1080 output, fixed 1/60 s step (`-movie`), 11.4 s (first 0.1 s trimmed: the director's camera settling). The default screen percentage was NOT forced and is not logged (nominally 100 %). The clip has one camera cut at 10.0 s (the director's second pawn shot) |
| S7 | `persist_start.jpg` + `evidence/persist_*` | persistence: the second launch starts in verdant, the suit the pawn run saved | 960x540 still at 3 s |
| S8 | `settings_menu_suit_row.jpg` | settings menu (`-WHShowSettings`), section HERO, row "Suit" showing Verdant read from `GameUserSettings.ini` | 1920x1080 still at 4 s |
| S9 | `orbit_all_suits.mp4` | the stage hero turning once while the suit changes every 1.5 s through all eight | 1920x1080, fixed 1/60 s step (`-movie`), `r.ScreenPercentage 100` passed (internal resolution nominally 1920x1080 at 100 %; it is not separately logged for the movie), 11.4 s. RE-SHOT in a second lock hold (see the orbit note) |
| M1 | `evidence/swap_latency.json`, `SPEC_CHECK.md` | swap latency | see SPEC_CHECK |

## Orbit note (second hold, 2026-10-01 17:09 - 17:13)

The orbit movie of the main chain showed the default pawn of `Char_Skins` as a small dark post on the horizon beside the hero (its off-stage PlayerStart was 60 m away). `build_characters.py` now places that start 1.8 km away, and the orbit was re-shot in a second, short hold: `STEPS="build orbit" EV=10.0 tools/ue_char/suits/chain_r11_final2.sh $P2_SCRATCH/r11/chain5` (build `skins,skinsmap` 26 s, orbit 1080p `-movie`, hold 223 s, 0 crashes, same exposure bias +10.0 as every other run). The committed `orbit_all_suits.mp4` is that re-shot movie (`post_r11.sh` with `ORBIT_OUT=chain5`; trimmed 0.6 s at the start for the 8192 px Tessera streaming, see below).
Checked by hand on the new movie: 23 frames at 2 fps cropped around the hero show no stray object; `evidence/orbit_post_removed_before_after.png` is the same frame (0.5 s) of the old (left) and the new (right) movie. Evidence: `evidence/orbit_reshoot_chain.log`, `evidence/orbit_reshoot_gpu_wrapper.log` (waited 150 s for the lock behind another agent's capture; `instances_max=2` there is another agent's `-nullrhi` commandlet (island `city_pass1.py`, no renderer), not a second renderer: my hold had one `-game` engine at a time, `contaminated=true` because no exclusive lock), `evidence/orbit_suit_log.txt` (8 swaps, `textures_resident=4/4` on every one, `apply_ms` <= 0.04; `wall_ms` of 680 - 790 is the movie-frame dump, as in the other movies).

## Honest notes

- 4K stills are a REAL-TIME run on a shared GPU (the lock logged `contaminated=true`, GPU utilisation 0 % before the run): the frame times in `evidence/stills_perf.json` (37 fps average) are not a performance result.
- Back views are darker than the front views: the key sun is in front of the hero (four low fill lights lift the back, intentionally not equal).
- Light suits (glacier, sage) read at the same fixed exposure as the dark ones, so glacier's hood and body are near the white end of the range.
- The first frames of a movie show the first suit's 8192 px Tessera maps still streaming in (white, then blurred mips for ~0.4 s of game time); the orbit movie is trimmed by 0.6 s for that reason. This is a load-time effect of the 8192 px maps, not of a swap: every later swap had `textures_resident=4/4`.
- The swap timing in the movies: a -movie run spends ~0.22 s of WALL time per dumped PNG frame, so the `wall_ms` of `WH_SUIT swap_done` in the movie logs (~450 ms) is the dump; the real-time numbers are in `evidence/stills_a_suit_log.txt` (64 - 68 ms for 3 frames at 4K, 17 swaps) and on the pixels of the movie (every T press shows the new suit 2 frames = 33 ms after the injection).
- The chest close-ups show a small stair-step in the left-chest sash end (viewer's left, near the armpit) on every suit: a UV island boundary of the shared body atlas. `suit_seams.py` measures it at 3 - 5 px at the texture level (limit 40 px) but it is visible at 4800 px / m.
- OCR of the 4K stills gave one denylist hit (`MILES` on the verdant chest): tesseract noise on the rib stripes, reviewed by eye, `evidence/ocr_review.txt`.
- Exposure sets b (+0.7) and c (-1.3) of the earlier plan were never shot: superseded by the calibration above.
