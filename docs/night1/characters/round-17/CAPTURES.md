# Round 17: captures (P2 hero skins: the lineup corruption, measured and removed; r16 gains kept; Verdant re-blocked)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.

**Round target (director, after the r16 critic [hero 6, anim 5, enemies 4, civilians 5, IQ 4; IP PASS]; round 17 was started by a Claude Code session that hit its usage limit and resumed by Sonnet 5.5 xhigh via Devin from the pushed WIP d2df6f7d / 9b71fc21 / 65366270):**
(1) remove the enemy blotch overlay and halos and capture after warm-up with no ghosting - at the same camera `enemy_lineup_4k.jpg` differs from the previous clean lineup by > 20 luma in <= 2 % of the pixels and shows no duplicate weapon - and PROVE the cause (streaming vs content) with a measurement;
(2) keep every r16 gain (back bleed 0 on 8, cord jog <= 4 px on 8 / 8, face seam dev100 <= 10 px on all 8 with Verdant tracked, net ends 0, IP guard, OCR, swap 7 / 7, pawn 0 pops);
(3) secondaries: every 40 px run of a sash or groove edge within 4 px of its line, the face seam joined through the chin, the cord ends finished, the crowd cut, the 9.933 s turn;
(4) re-block Verdant away from a known green-and-yellow costume (original, approved family) with an updated swatch sheet.
Numbers: `SPEC_CHECK.md` (every number read from `evidence/` by `tools/ue_char/suits/spec_check_r17.py`).

## Source, holds and resolution (disclosed)

The REAL game: UE 5.8.3 `-game`, Metal, offscreen (`Scripts/run_game.sh`), every engine run through the GPU lock (`gpu_slot.sh capture --label characters`; cap 3 by owner decision at 20:35, renders at background priority), driven by `tools/ue_char/suits/chain_r17.sh` from a snapshot (`hold_r17.sh`, READY gate). One engine of mine at a time, no OS dialog, every stop by the script's own quit or by `stop_ue.sh` (SIGTERM, never SIGKILL).
The content was rebuilt from the committed scripts inside the stills hold (`build_fight.sh clean,...,skins,skinsmap`, `/Content` not committed); the hero GLB (`prep_hero_r17.sh`) and the suit maps (`gen_suits.py --n 4096 --n-color 8192`, `hero_suit_r8.py --n 8192`) were prepared on the CPU first.

**The capture protocol is new (r17):** `WHCharShowDirector` flags `-WHSettleFrames=N -WHSettleSeconds=S` (stills + lineups: 32 frames / 2 s, lineups 4 s): when a shot's stage time arrives the director freezes the stage clock, every skeletal animation, every lane walker's Tick and the camera, waits until no asset is compiling, no shader is compiling and every texture of the visible actors is resident, then counts N RENDERED frames in which neither the camera nor any pose inside the camera frustum moved, and only then requests the screenshot (`WH_STAGE_SHOT ... settle_frames=34 static_world_s=... resets=0`). `-WHPreload` (movies, whose frames are a fixed 1/60 s step and cannot wait): finish every asset compile and stream everything in on the 2nd tick, before the first recorded frame. `-WHProbeFrames=N` (per-frame residency probe) and `-WHSettleDump=1,2,4,...` (the convergence curve) are the measurement flags.

| hold | when (EDT) | what it gave | used |
|---|---|---|---|
| A (previous session) | 15:40 - 16:20 | build + the first settle-protocol lineup, which never settled (the player pawn and 31 lane walkers moved: 25 min, max hold 2400 s exceeded, crash count 1 from the missing WH_QUIT) | diagnosis only |
| B | 20:42 | E0 (the r16 command, probe) + E1 (settle) which spun on the falling pawn; stopped by me with `stop_ue.sh` ("stopped cleanly") | E0 |
| C | 20:46 - 20:51 (316 s) | lineup, lineup34 (settle), E1 (settle + streaming + convergence dump), E2 (settle + `-NoTextureStreaming`), 0 crashes | E1, E2 |
| mini | 20:56 - 20:59 (170 s) | 8 settled stills of Tessera on `Char_Skins` (the protocol on the stills map and the head-lock shot) | test only |
| **D** | 21:00 - 21:23 (1367 s) | **content build + `enemy_lineup_4k` + `enemy_lineup_34_4k` + all 56 stills** (every one `settle_frames=34`, 0 resets, 0 timeouts, wall 5.5 - 7.2 s each; the first lineup waited 64.6 s for 23 compiling assets after the clean build), 0 crashes | **every still, both lineups, the swatch sheet** |
| **E** | 21:23 - 21:48 (1485 s) | pawn swap movie (`-WHPreload`), orbit movie, 0 crashes (its `lineupx0` step was a `-shots` time list: all shots fired in frames 1 - 3, discarded) | **pawn, orbit** |
| **F** | 21:48 - 21:57 (506 s) | crowd tracking movie | **crowd** |
| **H** | 21:57 - 21:59 (107 s) | dose-response of the r16 protocol (`-WHShotFrames`) | cause table |

- **4K stills:** output 3840x2160 = internal 3840x2160 (`r.ScreenPercentage 100`), committed as 4K JPEG (q2) for EVERY view (`stills/skin_<suit>_<view>_4k.jpg`, 56 files); every measure ran on the lossless PNG originals (`$P2_SCRATCH/r17/chainD/run/stills`). The lineups are the PNG originals re-encoded to 4K JPEG (q2).
- **Movies:** 1920x1080 output = internal, `-movie` = every frame at a fixed 1/60 s step, H.264 crf 18 - 20 (`swap_pawn_T_key.mp4`, `orbit_all_suits.mp4`, `crowd_tracking.mp4`; sizes in the Files list, all <= 15 MB). The first 0.1 s of camera binding are trimmed as in r14 - r16.
- **Not re-shot this round** (content unchanged except the r17 skin weights; the lock ran movies at 0.5 - 1.4 fps): the stage-hero run / chase clips and the fight clip. The critic pack uses the round-16 / round-15 files for them (`make_pairs_r17.py` falls back); `evidence/fight_unchanged_since_r10.txt` holds.
- GPU load: every hold shared the lock with 2 other holders (cap 3, `contaminated=true`), so **no frame time here is a performance number**.


## The lineup corruption: cause (measured, `evidence/lineup_cause.json`, `evidence/lineup_cause.md`)

Same camera (`Char_Lineup` shot 5), same content, same lock load; luma = 8-bit gray, the test is the share of pixels differing by > 20 luma from the previous clean lineup (round 14 = round 15, 0.003 % apart; r16 itself: **13.664 %**).

- **E0, the r16 capture command re-run** (`-shots 3.0 -perf 2:5 -quit 6`, no settle): the still is taken at engine frame **12** (world 2.24 s). At that frame **12 assets are still compiling** (27 at frame 1; the dose-response run below reaches 0 at engine frame 17 - 20), **0 textures are not resident** (max over the run: 0; streaming is not the problem), shaders compiling 0. The still has > 20 luma in **3.638 %** of the pixels (**9.273 %** inside the characters' band): copper blotches on the garments, halos, duplicate (ghost) weapons, as in r16.
- **E1, settle protocol, texture streaming ON**: everything resident after 0.9 s wall (3 frames; the shot waited for 0 compiling assets / shaders and every visible texture resident, with the stage clock, every animation, the lane walkers and the camera frozen). **After 1 static rendered frame** the still has > 20 luma in **0.063 %** of the pixels (band 0.208 %) - already clean; the curve over 1 / 2 / 4 / 8 / 16 / 24 static frames moves only the mean luma (auto exposure; mean |diff| 5.35 / 4.628 / 3.501 / 1.989 / 0.822 / 1.007): the blotches do not depend on the number of rendered frames after the compile. Final shot (34 static frames, 8.74 world s, 0 resets): **0.094 %** (band 0.311 %).
- **E2, settle protocol, `-NoTextureStreaming`**: everything resident after 0.1 s wall (1 frames; the shot waited for 0 compiling assets / shaders and every visible texture resident, with the stage clock, every animation, the lane walkers and the camera frozen). **After 1 static rendered frame** the still has > 20 luma in **0.474 %** of the pixels (band 1.567 %) - already clean; the curve over 1 / 2 / 4 / 8 / 16 / 24 static frames moves only the mean luma (auto exposure; mean |diff| 1.464 / 1.491 / 1.471 / 1.46 / 1.489 / 1.534): the blotches do not depend on the number of rendered frames after the compile. Final shot (34 static frames, 8.96 world s, 0 resets): **0.493 %** (band 1.628 %).

**Dose-response of the r16 protocol** (one run, plain screenshots at engine frame numbers, no settle, the probe at each frame; `Char_Lineup` shot 5 lasts 6 s of world time, so the frames after it - 24, 32, 48, 72 - show the NEXT director shot and are excluded):

| still | frame | assets compiling | textures not resident | > 20 luma vs clean lineup (whole / band) |
|---|---|---|---|---|
| x0_f0003.png | 3 | 27 | 0 | 7.149 % / 14.68 % |
| x0_f0005.png | 5 | 23 | 0 | 7.099 % / 13.812 % |
| x0_f0008.png | 8 | 18 | 0 | 5.174 % / 9.282 % |
| x0_f0010.png | 10 | 15 | 0 | 5.08 % / 9.62 % |
| x0_f0012.png | 12 | 12 | 0 | 4.463 % / 8.393 % |
| x0_f0014.png | 14 | 10 | 0 | 5.142 % / 11.429 % |
| x0_f0016.png | 16 | 8 | 0 | 4.998 % / 11.594 % |
| x0_f0020.png | 20 | 0 | 0 | 1.534 % / 5.065 % |

**Verdict on the cause (measured, not guessed):** NOT the content (the same garments, textures and meshes render clean the moment the capture waits) and NOT texture streaming (0 textures not resident at every bad shot above; E2 with `-NoTextureStreaming` is no different). Two capture-moment effects, each isolated by a measurement: **(a) assets still compiling** - in the dose-response run the corruption share falls from 7.149 % (27 compiling) through 4.463 % (12 compiling) to 1.534 % once the last asset has compiled (frame 20), a 3x drop at exactly the frame the count reaches 0; **(b) the characters' idle animations and the lane walkers still running** - at frame 20 (0 assets compiling) the running scene still has > 20 luma in 1.534 % of the pixels (5.065 % in the characters' band), while E1 after 1 static frame (engine frame ~17, the same compile state, the animations frozen) has 0.063 % (0.208 %): moving skinned meshes leave temporal ghosts (halos, duplicate weapons, blotched garments). The r16 "3.0 s" automation clock fired at engine frame 12 (the first frames of a 4K run on the cap-3 lock take 0.15 - 6 s each), with 12 of 27 assets compiling and everything moving; in r16 the lock was over-subscribed (4 - 6 holders) so it was worse (13.664 % vs 3.638 % today). The fix is the capture protocol (wait for 0 compiling assets, freeze animations / walkers / camera, count static frames), not the content.

Two defects of the first r17 protocol were found by the probe and fixed (`WHCharShowDirector`): (a) the r17a lineup run never settled in 25 min because the camera / pose signature included the **player pawn** (it falls from its off-stage PlayerStart for ~30 frames) and the **31 lane walkers** of `Char_Lineup` (they move in `Tick`, in world time) - now walkers' Tick is disabled while a shot settles and only skeletal meshes inside the camera frustum count; (b) the 240 s timeout is now checked BEFORE the reset branch, so a never-static scene still ends (flagged `SETTLE_TIMEOUT`).

## Results (details: `SPEC_CHECK.md`)

| line | r16 | **r17** (real game, 4K PNG originals) | verdict |
|---|---|---|---|
| (1) `enemy_lineup_4k.jpg` > 20 luma vs the previous clean lineup (gate <= 2 %) | 13.664 % / band 26.623 % | **0.453 % / band 1.497 %** (vs r15 0.436 % / band 1.441 %) | PASS |
| (1) `enemy_lineup_34_4k.jpg` (3/4) | 3.027 % / band 9.313 % | **0.309 % / band 1.019 %** | PASS |
| (2) back bleed: accent clusters >= 20 px in the back torso | 0 on 8 | **0 on 8** | PASS |
| (2) yoke-seam cord jog under the arm, gate <= 4 px | 0.5 - 0.9 | **0.5 - 5.3** (max over 8: 5.3; under-arm run only: Ash 1.0) | **7 / 8** by the instrument (Ash: 5.3 px at x 1665 = the cord's end cap at the sash border, see below) |
| (2) face centre seam dev100 <= 10 px | 5 / 8 measured (Cinder 10.9, Glacier 10.6, Verdant untracked) | tessera 4.3, verdant 4.3, plum 4.0, cinder 5.2, glacier 11.2, ash 5.8, saffron 2.6, sage 8.7 | **7 / 8** (Glacier: tracker reading, see below) |
| (2) net-end dead ends in open fabric (paint, 4096 px) | 0 | **0** | PASS |
| (2) IP guard (P1 - P7) / OCR hits | PASS (49.3) / 1 reviewed noise hit | **PASS** (min palette distance 43.5) / 1 reviewed noise hit (`evidence/ocr_review.txt`) | PASS |
| (2) swap: presses visible / latency | 7 of 7, 33 ms | **6 of 7**, [33.3] ms | 6 of 7 by the histogram matcher; the 7th press (Tessera -> Verdant, engine set at 8.717 s frame 522, swap_done 4/4 textures resident) is visible between 8.55 s and 8.9 s (`evidence/measures/swap7_tessera_to_verdant.jpg`) but the matcher found no step |
| (2) pawn luma pops 0 - 1.5 s | 0 | **0** (largest 5.183) | PASS |
| (2) Q6 Verdant armpit piping pinch ratio (own gate >= 0.5) | 0.54 | **0.27** (min 3 px, median 11.0 px; the copper cord is intact and tapers into the crease like r16, `evidence/measures/q6_pair.jpg`) | FAIL by the instrument |
| (2) R1 lens rim behind the brow (>= 1 pct of head height = 16 px) | 8 / 8 (33 - 48 px) | tes 33.0 px, ver 41.7 px, plu 50.0 px, cin 36.0 px, gla 22.0 px, ash 46.7 px, saf 42.7 px, sag 62.3 px | PASS 8 / 8 |
| (2) G1 / G2 / G3 (head sculpt) | 8 / 8 each | G1 8 / G2 8 / G3 12 deg 8, 0 deg 8, 25 deg 8 of 8 | PASS |
| (3) sash / groove edge steps > 4 px on long edges (both runs >= 100 px), 8 chests (`line_step_r17.py`) | 20 (largest per suit: tes 29.6, ver 13.7, plu 29.4, cin 5.3, gla 9.8, ash 26.9, saf 9.3, sag 14.8) | **13** | the named defects are gone (Ash shelf 26.9 px, Verdant step 13.7 px); 13 long-edge jogs of 4.5 - 10 px remain: NOT met |
| (3) pawn clip step at 9.933 s | 15.49 vs neighbours 3.48 (a director shot end) | **5.1** vs neighbours 3.79; cuts in the clip: 0 | PASS |
| (3) crowd clip step at 7.483 s | 55.6 vs neighbours 1.89 (a director shot end) | **2.27** vs neighbours 2.02; cuts in the clip: 0 | PASS |
| (3) face seam through the chin / cheek-cord ends | Cinder seam broke and jogged at the chin; cheek cords cut square | seam continuous through the chin on all 8 (`evidence/measures/chin_crops.jpg`, r16 row over r17 row); the four cheek cords close in a rounded tip (`design.py`, EXPECT_R17) | by eye |
| (4) Verdant | brass yellow accent, yellow forearm / shin blocks, yellow crown stripes | forest green + dark pine + copper, no yellow, plain crown; IP guard PASS, nearest suits tessera 43.5, ash 44.2 | `SWATCH_SHEET.jpg`, `VERDANT_BEFORE_AFTER.jpg` |

## Honest limits and open items

- **Sash / groove edge steps NOT fully met**: the colour-region instrument (`line_step_r17.py`) still finds long-edge jogs of 4.5 - 10 px (see the table row): the named r16 defects are gone (Ash sash shelf 26.9 px, Verdant groove step 13.7 px) but the yoke-seam cord still steps ~8 px where it crosses the Tessera sash's top-left corner, the Verdant ring-net line wobbles ~10 px at the image-right armpit, and Saffron / Sage keep 5 - 7 px steps on the collar line. These sit in the trapezius / collar band (y > 1.38) and the pec <-> arm boundary, outside the sternum strip this round smoothed.
- **Cord jog 7 / 8 by the instrument**: Ash reads 5.3 px at x 1665 = the cord's thicker end cap meeting the sash border (the tracker is pulled up by the border cord); the under-arm run, where the r15 stair-steps were, reads 1.0 px. Overlay `evidence/measures/cord_jog/cordjog_ash.jpg`.
- **Face seam dev100 7 / 8**: Glacier reads 11.2 px; `evidence/seam_instrument_note.txt` + `evidence/measures/glacier_seam_glabella_1p6x.jpg`: the tracker follows the bright centroid, which moves 12 px where the dark crown meets the pale face; the cord itself is straight. Cinder (r16 10.9) is 5.2, Verdant is tracked now (4.3), the chin steps are 6.6 px (Cinder) / 5.3 px (Ash) at the last 350 tracked rows.
- **Q6 Verdant armpit pinch ratio 0.27 (own gate 0.5)**: the copper cord is intact and tapers into the armpit crease like the brass one did (`evidence/measures/q6_pair.jpg`, r16 | r17); the instrument's colour thresholds were tuned on brass. H3 (lens >= 1.6x the r12 lens) is not computed for Verdant after the re-block (the r12 baseline segmentation expects the old lens colour); its lens widths are unchanged (594 / 389 px vs 575 / 419 px at another idle phase). H4 (own, ONE closed raised rim) 2 / 8 (r16 3 / 8).
- **Dose-response limit**: `Char_Lineup` shot 5 lasts 6 s of world time, so only frames <= 20 of the r16-protocol run are comparable; the residual > 20 luma share of the frame-20 shot (1.53 % whole / 5.07 % band, 0 assets compiling) is the running animation (E1 after 1 static frame: 0.06 %).
- **Not re-shot**: the stage-hero run / chase clips and the fight clip (lock at 0.5 - 1.4 fps for movies; content unchanged except the r17 weights); the Tessera back changed in r16, so the r15 / r16 chase clips in the pack still show the old back.
- The lock ran with 2 other holders for every hold (`contaminated=true`): no frame time is a performance number.
- The Verdant accent is copper (#c4703a) next to Tessera's amber (#e0780c): IP guard PASS (palette distance 43.5 to Tessera, 44.2 to Ash) but five of the eight suits now carry an orange-family accent (Tessera amber, Verdant copper, Plum apricot, Glacier coral, Sage clay): variety is the owner's call on `VERDANT_BEFORE_AFTER.jpg` / `SWATCH_SHEET.jpg` (a cool accent - mint, ice - is the alternative).


## Files

- Stills: `stills/skin_<suit>_<view>_4k.jpg` (56: front, back, chest, head, head34, headside, headfront x 8 suits), `SWATCH_SHEET.jpg` (owner sheet, all 8 suits, front + back + chest + head), `VERDANT_BEFORE_AFTER.jpg` (r16 | r17).
- Lineups: `enemy_lineup_4k.jpg`, `enemy_lineup_34_4k.jpg` (settled); `evidence/measures/lineup/` (diff maps vs r14 / r15 / r16, `weapons_crops.jpg`: r14 | r16 | r17 crops of the bat, the pistols, the garments).
- Clips (1920x1080 internal = output): `crowd_tracking.mp4` 4.5 MB, `orbit_all_suits.mp4` 5.0 MB, `swap_pawn_T_key.mp4` 7.2 MB
- Evidence: `evidence/lineup_cause.json` + `.md`, `evidence/lineup_experiment/*.txt` (the probe / settle / shot lines of E0, E1, E2 and the frame run), `evidence/lineup_diff_*.json`, `evidence/cut_check_*.json`, `evidence/line_step_*.json` (+ `_r16_`), `evidence/cord_jog*.json`, `evidence/seam_track*.json`, `evidence/back_bleed*.json`, `evidence/net_end*.json`, `evidence/head_check.json`, `evidence/rim_depth*.json`, `evidence/iq_check.json`, `evidence/ipguard.json`, `evidence/ocr_stills.json` (+ `ocr_review.txt`), `evidence/swap_latency.json`, `evidence/pawn_check.json`, `evidence/measures/` (overlays, crop sheets, `chin_crops.jpg`, `cuts/r16_director_cuts.jpg`), `SPEC_CHECK.md`, `critic_pairs.json`.

