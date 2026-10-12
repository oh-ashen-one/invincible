# Round 17 SPEC CHECK (piece G, hero skins)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. Numbers are read from `evidence/` by `tools/ue_char/suits/spec_check_r17.py`;
> every measure of a still runs on the lossless 3840x2160 PNG originals of the real game (UE 5.8.3 `-game`, offscreen, internal 3840x2160); the round-16 baseline = the r16 PNG originals.

## Part 1: round-17 target (critic r16: the lineup corruption; keep every r16 gain; secondaries; Verdant re-block)

**(1) Enemy lineup: cause and fix** (`lineup_cause_r17.py`, `lineup_diff_r17.py`; 3840x2160, camera = Char_Lineup shot 5, previous clean lineup = round 14 = round 15 (0.003 % apart)). Luma = 8-bit gray; the test is the share of pixels differing by > 20.

- **E0 = the r16 capture command** (`-shots 3.0 -perf 2:5 -quit 6`, no settle protocol) re-run today: the still is taken at engine frame **12** (world 2.24 s); at that frame **12 assets are still compiling** (27 at frame 1; the first frame with 0 is after the shot (dose-response run: engine frame 17 - 20)), shaders compiling 0, **textures not resident: 0** (max over the run 0). The still differs from the clean lineup by > 20 luma in **3.64 %** of the pixels (9.27 % inside the characters' band): copper blotches, halos, ghost bats as in r16 (r16 itself, taken on a 4-holder lock: 13.664 %).
- **E1 = settle protocol, texture streaming ON** (same camera and content): everything resident after 0.9 s wall (3 frames); the shot waits for 0 compiling assets and every visible texture resident, freezes the stage clock, every animation, the walkers and the camera, then counts static rendered frames. Already **after 1 static frame** the still differs from the clean lineup by > 20 luma in **0.063 %** (band 0.208 %); the final shot (34 static frames, 8.74 world s, 0 resets): **0.09 %** (band 0.31 %). The 1 -> 24 frame curve moves only the mean luma (auto exposure: mean |diff| 5.35 -> 1.248), not the blotches.
- **E2 = settle protocol, -NoTextureStreaming** (same camera and content): everything resident after 0.1 s wall (1 frames); the shot waits for 0 compiling assets and every visible texture resident, freezes the stage clock, every animation, the walkers and the camera, then counts static rendered frames. Already **after 1 static frame** the still differs from the clean lineup by > 20 luma in **0.474 %** (band 1.567 %); the final shot (34 static frames, 8.96 world s, 0 resets): **0.49 %** (band 1.63 %). The 1 -> 24 frame curve moves only the mean luma (auto exposure: mean |diff| 1.464 -> 1.574), not the blotches.

**Dose-response of the r16 protocol** (one run, plain screenshots at engine frame numbers 3 .. 72, no settle, probe at the shot frame; Char_Lineup shot 5 lasts 6 s of world time, so the frames after it - 24, 32, 48, 72 - show the next director shot and are excluded):

| still | frame | assets compiling | textures not resident | > 20 luma vs clean lineup (whole / band) |
|---|---|---|---|---|
| x0_f0003.png | 3 | 27 | 0 | 7.15 % / 14.68 % |
| x0_f0005.png | 5 | 23 | 0 | 7.10 % / 13.81 % |
| x0_f0008.png | 8 | 18 | 0 | 5.17 % / 9.28 % |
| x0_f0010.png | 10 | 15 | 0 | 5.08 % / 9.62 % |
| x0_f0012.png | 12 | 12 | 0 | 4.46 % / 8.39 % |
| x0_f0014.png | 14 | 10 | 0 | 5.14 % / 11.43 % |
| x0_f0016.png | 16 | 8 | 0 | 5.00 % / 11.59 % |
| x0_f0020.png | 20 | 0 | 0 | 1.53 % / 5.07 % |

**Verdict on the cause:** two capture-moment effects, each isolated: (a) assets still compiling (the corruption share drops 3x at the frame the count reaches 0), (b) animations / walkers still running (frame 20 with 0 compiling assets still has the residual above, E1 after 1 static frame at the same compile state does not). Textures were resident at every bad shot (0 not resident) and the content renders clean once the capture waits: not streaming, not content. See `CAPTURES.md`.

| lineup (committed) | > 20 luma vs r14 whole / character band | vs r15 | vs r16 (the corrupted one) | ghost / duplicate weapon |
|---|---|---|---|---|
| enemy_lineup_4k.jpg (wide) | **0.45 % / 1.50 %** (gate <= 2 %) | 0.44 % / 1.44 % | 17.64 % / 28.86 % | by eye: none (`evidence/measures/lineup/`) |
| enemy_lineup_34_4k.jpg (3/4) | **0.31 % / 1.02 %** (gate <= 2 %) | 0.30 % / 0.99 % | 4.35 % / 12.74 % | by eye: none (`evidence/measures/lineup/`) |

**(2) Kept: r16 gains** (details in part 2): back bleed, cord jog <= 4 px, face seam dev100 <= 10 px on all 8, net ends, IP guard, OCR, swap, pawn pops.

**(3a) Sash / groove edge steps** (`line_step_r17.py`: colour regions of the chest still -> polygon edges; a JOG = two straight runs >= 40 px, near-parallel (< 8 deg, same direction), joined by <= 4 short polygon edges, the second run's line more than 4 px beside the first: the edge does not stay within 4 px of ONE line over the two runs).

| suit | jogs > 4 px r16 -> **r17** | largest step r16 -> **r17** (px) | long-edge jogs (both runs >= 100 px) r16 -> **r17**, largest | where the largest long-edge jog is (r17) |
|---|---|---|---|---|
| tessera | 30 -> **29** | 29.6 -> **13.1** | 1 -> **2**, 29.6 -> **8.2** | (1765, 1300) |
| verdant | 35 -> **41** | 26.6 -> **20.7** | 3 -> **4**, 13.7 -> **10.2** | (2539, 854) |
| plum | 47 -> **38** | 29.4 -> **31.0** | 5 -> **0**, 29.4 -> **0** | - |
| cinder | 40 -> **28** | 17.6 -> **45.5** | 1 -> **0**, 5.3 -> **0** | - |
| glacier | 33 -> **31** | 16.0 -> **14.4** | 1 -> **0**, 9.8 -> **0** | - |
| ash | 29 -> **32** | 26.9 -> **11.4** | 4 -> **1**, 26.9 -> **5.2** | (1479, 1291) |
| saffron | 46 -> **44** | 58.1 -> **59.0** | 3 -> **5**, 9.3 -> **7.5** | (2056, 680) |
| sage | 30 -> **26** | 68.3 -> **66.9** | 2 -> **1**, 14.8 -> **7.2** | (1200, 1790) |

long-edge jogs over all 8 chests: r16 **20** -> r17 **13** (the instrument has limits: it needs contrast and counts design corners where a panel boundary legitimately steps; overlays `evidence/measures/line_step/`). The named defects: Ash sash lower edge (r16: 24 - 28 px shelf at (2370, 1894)), Verdant groove step (r16: 11.6 px at (2383, 1312)) - see the Ash / Verdant rows.

**(3b) Cord jogs, both sides** (`cord_jog_r17.py`: every long near-horizontal cord of the chest across the whole torso width, JOG = largest row change beyond the local slope; gate <= 4 px): tessera 3.5, verdant 4.1, plum 3.8, cinder 3.6, glacier 3.1, ash 3.9, saffron 3.5, sage 3.1 px.

**(3c) Cuts** (`cut_check_r17.py`, frame-to-frame mean |luma| difference, 480 px wide):

| clip | r16 / r15 | **r17** |
|---|---|---|
| pawn swap clip, step at 9.933 s | 15.49 against neighbours 3.48 -> cuts 1 | **5.1** against neighbours 3.79; cuts: []; largest step {'t': 7.733, 'diff': 5.37} |
| crowd clip, step at 7.483 s | 55.6 against neighbours 1.89 -> cuts 2 | **2.27** against neighbours 2.02; cuts: []; largest step {'t': 1.283, 'diff': 2.84} |

The r16 'yaw snap' (9.933 s) and the r16 crowd cut (7.483 s) were DIRECTOR SHOT ENDS (`WHCharShowDirector`: the pawn map's shot 0 lasted 10 s and the director cut to the front 3/4 shot; the crowd shot 0 lasted 8 s and the director cut to 'crowd wide'); the r17 maps make those shots 16 s / 12 s (`build_characters.py`), so no cut falls inside the clips.

**(4) Verdant re-block** (`suits.json`): forest green body, dark pine panels / hood, copper accent (was brass yellow), no accent forearm / shin blocks, plain crown (no yellow crown stripes), mask brow ticks and net lines in copper. IP guard (`ip_guard.py palette`): P1 - P7 PASS (0 fails), min palette distance over all pairs 43.5; Verdant's nearest suits: tessera|verdant 43.5, verdant|ash 44.2, verdant|sage 55.1. Swatch sheet: `SWATCH_SHEET.jpg`.

## Part 2: the round-16 instrument set re-run on round 17 (baseline = round 16)

### (round-16 set) Round 17 SPEC CHECK (piece G, hero skins)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. Numbers are read from `evidence/` by `tools/ue_char/suits/spec_check_r16.py`;
> every measure of a still runs on the lossless 3840x2160 PNG originals of the real game (UE 5.8.3 `-game`, offscreen, internal 3840x2160); the round-16 baseline = the r16 PNG originals.

## Part 1: round-17 target (critic r16 image-quality defects; first-pass acceptance line IQ >= 6)

**(1) Back bleed** (`back_bleed_r16.py`, 8 back stills at 4K): accent-family pixels (the front emblem / sash fill colour and its darker shade, colour direction within 20 deg) inside the back torso mask; gate: no cluster >= 20 px.

| suit | clusters >= 20 px r16 -> **r17** | largest cluster px r16 -> **r17** | accent px in the mask r16 -> **r17** | verdict |
|---|---|---|---|---|
| tessera | 0 -> **0** | 0 -> **0** | 0 -> **0** | PASS |
| verdant | 0 -> **0** | 0 -> **0** | 0 -> **0** | PASS |
| plum | 0 -> **0** | 0 -> **0** | 0 -> **0** | PASS |
| cinder | 0 -> **0** | 0 -> **0** | 0 -> **0** | PASS |
| glacier | 0 -> **0** | 0 -> **0** | 0 -> **0** | PASS |
| ash | 0 -> **0** | 0 -> **0** | 0 -> **0** | PASS |
| saffron | 0 -> **0** | 0 -> **0** | 113 -> **167** | PASS |
| sage | 0 -> **0** | 0 -> **0** | 0 -> **0** | PASS |

8 of 8 backs pass (overlays `evidence/measures/back_bleed/`, mask yellow, accent pixels magenta). All 8 back stills are committed at 4K (`stills/skin_<suit>_back_4k.jpg`).

**(2) Cord jogs** (`cord_jog_r16.py`, 8 chest stills: the yoke seam cord tracked across the image-left torso side under the arm, the largest row step between neighbouring columns beyond the local slope; gate <= 4 px). The r16 critic boxes: Verdant ~(1300, 1310), Ash / Cinder the same side.

| suit | max jump r16 -> **r17** (px) | at (x, y) r17 | tracked columns r17 | verdict |
|---|---|---|---|---|
| tessera | 0.9 -> **0.5** | [1505, 1278] | 411 | PASS |
| verdant | 0.5 -> **1.0** | [1191, 1311] | 540 | PASS |
| plum | 0.9 -> **1.0** | [1487, 1267] | 536 | PASS |
| cinder | 0.6 -> **0.9** | [1240, 1320] | 317 | PASS |
| glacier | 0.5 -> **1.3** | [1464, 1302] | 384 | PASS |
| ash | 0.9 -> **5.3** | [1665, 1282] | 567 | FAIL |
| saffron | 0.5 -> **0.8** | [1196, 1311] | 534 | PASS |
| sage | 0.6 -> **1.0** | [1378, 1271] | 570 | PASS |

7 of 8 chest stills pass (overlays `evidence/measures/cord_jog/`).

**(3) Face centre seam** (`seam_track_r16.py`, 8 headfront stills: the light seam cord tracked row by row from the crown to the chin; `dev100` = the largest lateral change over 100 rows; gate <= 10 px). r17: the headfront portrait follows the head bone (`WHShot.bHeadLock`, log `evidence/headlock_log.txt`).

| suit | dev100 r16 -> **r17** (px) | lateral range r16 -> **r17** | residual from a line r17 | tracked rows r17 | verdict |
|---|---|---|---|---|---|
| tessera | 4.5 -> **4.3** | 5.9 -> **5.3** | 3.6 | 919 | PASS |
| verdant | None -> **4.3** | None -> **4.7** | 3.2 | 1256 | PASS |
| plum | 4.7 -> **4.0** | 5.7 -> **4.9** | 2.7 | 1011 | PASS |
| cinder | 10.9 -> **5.2** | 33.8 -> **7.4** | 4.1 | 1797 | PASS |
| glacier | 10.6 -> **11.2** | 12.2 -> **12.5** | 7.7 | 640 | FAIL |
| ash | 6.7 -> **5.8** | 10.8 -> **6.8** | 4.4 | 1404 | PASS |
| saffron | 2.6 -> **2.6** | 4.2 -> **4.1** | 2.7 | 1155 | PASS |
| sage | 8.4 -> **8.7** | 10.0 -> **10.6** | 7.4 | 441 | PASS |

7 of 8 headfront stills pass (overlays `evidence/measures/seam_track/`).

**(4a) Net ends** (`net_end_check_r15.py --n 4096`, the paint itself): dead-end blobs in open fabric r16 **0** -> r17 **0** (armpit crease zone, folded under the arm, not counted: 45 -> 45).

| suit | open fabric r16 -> **r17** | by layer r17 |
|---|---|---|
| tessera | 0 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| verdant | 0 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| plum | 0 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| cinder | 0 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| glacier | 0 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| ash | 0 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| saffron | 0 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| sage | 0 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |

**(4b) Q6 Verdant armpit cord** (`iq_check_r15.py`, its keys: r15 = the baseline = r16 stills, r16 = this round): pinch ratio (min / median thickness along the run) r16 0.75 -> **r17 0.27** (min 3 px, median 11.0 px, 0 gap columns); gate >= 0.5: **FAIL**.

**(4c) Ash notch smear (~1480, 1170)** and **(5) the no-new-defect crop pass**: read by eye on `evidence/measures/crops/crops_<suit>.jpg` (r16 row over r17 row); the list is in `CAPTURES.md`.

**Summary of the measured gates:** back PASS, jog FAIL, seam FAIL, net PASS, q6 FAIL

## Part 2: the round-16 instrument set re-run on round 17 (baseline = round 16)

### (round-16 set) Round 17 SPEC CHECK (piece G, hero skins)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. Numbers are read from `evidence/` by `tools/ue_char/suits/spec_check_r15.py`;
> the measures of the 4K chest stills run on the lossless PNG originals of the real game (UE 5.8.3 `-game`, offscreen, internal 3840x2160).

## Round target (critic r16 / r17 lines): the P2-owned lines + the playable pawn on the merged P3 r22 ground blend

**R1 rim depth** (`rim_depth_r15.py`, 4K headside stills, lossless PNG originals): the front-most pixel of the lens RIM lies >= 1 % of the head height (>= 16 px at 1590 px) BEHIND the front-most pixel of the brow. The critic r16 measured the Verdant rim 18 px proud (2273 against 2255).

| suit | rim behind brow, px (+ = behind) r16 -> **r17** | % of head height r16 -> **r17** | verdict |
|---|---|---|---|
| tessera | 38.0 -> **33.0** | 2.48 -> **2.2** | PASS |
| verdant | None -> **41.7** | None -> **2.72** | PASS |
| plum | 33.0 -> **50.0** | 2.19 -> **3.3** | PASS |
| cinder | 40.3 -> **36.0** | 2.63 -> **2.35** | PASS |
| glacier | 38.0 -> **22.0** | 2.51 -> **1.49** | PASS |
| ash | 37.3 -> **46.7** | 2.44 -> **3.13** | PASS |
| saffron | 47.7 -> **42.7** | 3.22 -> **2.79** | PASS |
| sage | 44.0 -> **62.3** | 2.92 -> **4.12** | PASS |

8 of 8 suits pass R1 (overlays `evidence/measures/rim_overlays/`; CPU model of the same pose before the hold: `round-17/CAPTURES.md`).

| item | measure | r16 | **r17** | verdict |
|---|---|---|---|---|
| Q5 Ash sash-end accent pipe (box 1490-1540 x 760-1150) | pixels between the pipe and the DEEP border cord (p90 / max) | 2.0 / 80 px | **2.0 / 20 px** (pipe 4.0 px wide, x [1540, 1561]) | PASS |
| Q6 Verdant armpit piping (box 1160-1270 x 1150-1270) | cord thickness min / median along its own run (1 = even, 0 = a gap); gap columns in the run | 0.75 (min 3 px, median 4.0 px; 0 gap columns) | **0.27** (min 3 px, median 11.0 px; 0 gap columns; the cord now ends at the shoulder cap edge, last column x 1176) | FAIL by my own 0.5 gate (no gap any more; the cord thins toward the crease where it ends) |
| Q7 brow trim, tessera | trim edge rise / thickness at the brow (px, perpendicular) | 7.9 / 22.82 | **5.62 / 20.77** (brow/temple 1.31, sane windows: True; r17/r16 edge rise 0.71) | PASS |
| Q7 brow trim, verdant | trim edge rise / thickness at the brow (px, perpendicular) | None / None | **0.27 / 3.22** (brow/temple None, sane windows: None; r17/r16 edge rise None) | see crop |
| Q7 brow trim, plum | trim edge rise / thickness at the brow (px, perpendicular) | 8.43 / 16.85 | **9.18 / 13.11** (brow/temple 3.48, sane windows: True; r17/r16 edge rise 1.09) | see crop |
| Q7 brow trim, cinder | trim edge rise / thickness at the brow (px, perpendicular) | 8.03 / 17.74 | **8.0 / 18.54** (brow/temple 2.69, sane windows: True; r17/r16 edge rise 1.0) | see crop |
| Q7 brow trim, glacier | trim edge rise / thickness at the brow (px, perpendicular) | 9.59 / 24.41 | **9.14 / 22.43** (brow/temple 1.92, sane windows: True; r17/r16 edge rise 0.95) | see crop |
| Q7 brow trim, ash | trim edge rise / thickness at the brow (px, perpendicular) | 10.28 / 17.13 | **9.31 / 17.77** (brow/temple 1.67, sane windows: True; r17/r16 edge rise 0.91) | see crop |
| Q7 brow trim, saffron | trim edge rise / thickness at the brow (px, perpendicular) | 1.68 / 6.73 | **1.69 / 5.25** (brow/temple None, sane windows: None; r17/r16 edge rise 1.01) | see crop |
| Q7 brow trim, sage | trim edge rise / thickness at the brow (px, perpendicular) | 2.62 / 3.28 | **1.71 / 2.85** (brow/temple 0.23, sane windows: False; r17/r16 edge rise 0.65) | PASS |

**Net / groove ends** (`net_end_check_r15.py`, the paint itself at 4096: a net line ends where its zone mask falls; a DEAD END has no raised cord within 2.5 mm and is not at an atlas island edge): dead-end blobs in open fabric, all 8 suits: r16 switches **0** -> r17 **0** (torso net: 0 -> 0; armpit crease zone, folded away under the arm, not counted: 45 -> 45).

| suit | open-fabric dead ends r16 -> r17 | by layer (r17) |
|---|---|---|
| tessera | 0 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| verdant | 0 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| plum | 0 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| cinder | 0 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| glacier | 0 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| ash | 0 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| saffron | 0 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| sage | 0 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |

**Pawn** (`pawn_check_r15.py`; P3 `WebTravAnimInstance` GroundBlendS 0.18 s merged from Opus-5.5-Loop-Night-1; the run CADENCE is P3's and routed to traversal, not a P2 gate):

| test | r16 | **r17** | verdict |
|---|---|---|---|
| P1 no frame-to-frame luma difference in 0 - 1.5 s above 2x both neighbours (whole frame / hero blob) | 0 / 0 pops (largest 5.172 at None s) | **0 / 0 pops** (largest 5.183) | PASS |
| P2 no `anim_weight` step above dt / 0.18 per frame (0.0926 at 60 fps); NOTE `anim_weight` is the TOTAL clip weight (always 1.0), so this test is vacuous | max step 0.0 | **max step 0.0** (limit 0.0928) | PASS (vacuous) |
| pose-signature steps 0 - 1.5 s (P3 ground blend): largest / median of 0.5 - 2 s | 1.7 | **1.7** (at 1.0833 s) | logged |
| clip switches in 0 - 1.5 s | ['A_Hero_jog', 'A_Hero_run'] | **['A_Hero_jog', 'A_Hero_run']** | logged |

## Kept: the round-16 sculpt gates (G1 - G3, H1 - H6) on the round-17 head

Measured by `tools/ue_char/suits/head_check_r14.py` on the lossless 4K PNG originals of the real game: `head` = 12 deg off the face axis (1.0 m), `headfront` = the same framing straight on (0 deg), `head34` = the round-12 head framing (25 deg), `headside` = profile (1.25 m).
**G1** headside: the silhouette between the brow's front-most point and the nose tip dips >= 1.5 % of the head height (crown to chin, 1590 px at this framing) behind the brow -> nose-tip chord. **G2** the brow's front-most point is >= 1 % of the head height in front of the top of the lens (front-most glass pixel of the top quarter of its rows); G2b = the same with a 3.1 mm rim allowance. **G3** horizontal luma lines through the cheek bones (the band lens bottom + 15 px .. + 200 px, every 15 px, 15 px smoothing, head interior minus 30 px at each edge): >= 3 extrema of prominence >= 20 luma on >= 70 % of the lines, swing >= 20 on every line. Kept from round 13 (head_check_r13.py): H1 nose-bridge luma profile, H2 nose bump >= 2 % of head height, H3 lens >= 1.6x round 12, H4 ONE closed raised rim >= 6 px on >= 90 % of 48 angles, H5 raised face seam (lit / shadow pair >= 20 luma, no black run), H6 lenses inside the outline.

| suit | G1 recess % HH (px) | G2 brow over lens top % HH (with rim) | G3 cheek lines >= 3 extrema: 12 deg / 0 deg / 25 deg (min swing) | H3 near lens x r12 (mean 12 deg) | H4 rim px, closed (head / head34) | H5 seam pair | H1 / H2 / H6 | verdict |
|---|---|---|---|---|---|---|---|---|
| tessera | **7.88** (118.0 px) | **6.08** (4.7) | 13/13 (128.8) / 13/13 (135.5) / 13/13 (122.0) | 1.792 (1.787) | 14.2, 0.646 ; 13.2, 0.667 | 138.8 | 5/93.4 / 9.2 / [245, 17] | FAIL H4 |
| verdant | **7.87** (120.4 px) | **6.58** (5.23) | 13/13 (155.5) / 13/13 (158.8) / 13/13 (143.3) | None (None) | 21.0, 0.688 ; 14.2, 0.729 | 159.5 | 3/111.1 / 8.93 / [228, 26] | FAIL H3, H4 |
| plum | **7.8** (118.1 px) | **6.94** (5.57) | 13/13 (134.2) / 13/13 (132.7) / 13/13 (109.0) | 1.787 (1.682) | 24.8, 0.938 ; 17.5, 0.792 | 147.6 | 4/131.2 / 10.5 / [196, 41] | FAIL H4 |
| cinder | **7.87** (120.6 px) | **6.39** (5.05) | 13/13 (158.7) / 13/13 (158.9) / 13/13 (138.0) | 1.775 (1.745) | 5.8, 0.438 ; 12.8, 0.688 | 162.5 | 3/120.3 / 9.34 / [140, 38] | FAIL H4 |
| glacier | **7.99** (117.9 px) | **6.17** (4.77) | 13/13 (132.2) / 13/13 (123.8) / 13/13 (135.0) | 1.713 (1.686) | 44.8, 1.0 ; 43.0, 1.0 | 101.8 | 4/100.4 / 11.6 / [42, 45] | PASS |
| ash | **7.87** (117.3 px) | **6.15** (4.76) | 13/13 (153.4) / 13/13 (157.5) / 13/13 (147.2) | 1.792 (1.795) | 15.8, 0.729 ; 17.0, 0.812 | 152.2 | 5/120.1 / 9.91 / [119, 21] | FAIL H4 |
| saffron | **7.88** (120.4 px) | **6.58** (5.23) | 13/13 (182.4) / 13/13 (184.9) / 13/13 (172.2) | 1.733 (1.652) | 21.8, 0.854 ; 15.5, 0.75 | 185.7 | 3/184.4 / 8.82 / [219, 33] | FAIL H4 |
| sage | **7.81** (118.2 px) | **6.89** (5.53) | 13/13 (151.3) / 13/13 (142.5) / 13/13 (144.4) | 1.756 (1.658) | 45.5, 0.958 ; 44.2, 1.0 | 127.2 | 5/116.7 / 10.5 / [197, 45] | PASS |

2 of 8 suits pass every gate (G1, G2, G2b, G3 x 3 views, H1 - H6); 8 of 8 pass the three critic tests G1 + G2 + G3 (12 deg and 0 deg) (`evidence/head_check.json`, overlays in `evidence/measures/head_overlays/`).

Mesh silhouette of the finished head (CPU, the GLB the engine imports; `head_profile_r14.py`): recess 7.24 % HH, brow over the lens top 6.95 % HH, over every rim vertex 5.27 % HH, nose bump 20.02 % HH, mouth / chin groove 6.89 mm; lens-to-outline clearance in a 12 deg view 39.2 px (glass) / 24.0 px (rim).

## Keep: the round-12 lines (raised piping, nothing under the sash, no fold)

| suit | relief: 64 px cells with a lit / shadow pair >= 20 luma (r16 -> r17) | median cell delta (r16 -> r17) | sash: longest dark run px, target <= 10 (r16 -> r17) | sash verdict |
|---|---|---|---|---|
| tessera | 0.632 -> **0.661** (265 of 401 cells) | 27.6 -> **27.6** | 5 -> **6** | PASS |
| verdant | 0.675 -> **0.535** (159 of 297 cells) | 34.1 -> **21.6** | None -> **8** | PASS |
| plum | 0.696 -> **0.708** (240 of 339 cells) | 31.0 -> **32.9** | 8 -> **9** | PASS |
| cinder | 0.713 -> **0.752** (209 of 278 cells) | 31.4 -> **31.6** | 6 -> **6** | PASS |
| glacier | 0.632 -> **0.574** (187 of 326 cells) | 24.1 -> **22.6** | None -> **None** | n/a |
| ash | 0.729 -> **0.765** (283 of 370 cells) | 34.4 -> **37.2** | 3 -> **4** | PASS |
| saffron | 0.645 -> **0.587** (186 of 317 cells) | 32.6 -> **25.4** | 5 -> **6** | PASS |
| sage | 0.57 -> **0.588** (201 of 342 cells) | 27.3 -> **25.3** | None -> **None** | n/a |

| Verdant chevron edge at the critic's columns x 1320-1400 | target | round 14 | round 15 | verdict |
|---|---|---|---|---|
| largest column-to-column jump beyond its slope | <= 2 px | None px | **no edge in the critic columns** | n/a: since round 14 the Verdant V ends at |x| = 0.118 m (a straight piped end), so the chevron's upper edge no longer runs into the armpit where the r13 step was; the instrument finds no edge in its ROI. The step is gone from the frame (crop `evidence/measures/iq/chest_verdant.jpg`), not measured to 0 |

## Keep-passing lines

| line | target | measured | verdict |
|---|---|---|---|
| CH1 front stills (hero height / frame height, all 8 suits) | 0.48 - 0.62 | 0.543 - 0.544 | PASS |
| IP guard palette P1 - P7 (round-17 deeper sockets / pipe join / yoke seams) | 0 failures | min palette distance 43.5 over 28 pairs, fails: none | PASS |
| UV seam runs at 4K (texture level) | <= 40 px | worst 2.7 px, runs > 40 px: 0 | PASS |
| OCR of every 4K still | 0 hits | 1 hits over 56 images | REVIEW |
| Tessera stays the default; generator regression (r8 legacy texel for texel + r17 default) | PASS | REGRESSION PASS | PASS |
| swap on the pixels (playable pawn, real T presses) | <= 500 ms | 6 of 7 presses found, worst 33.3 ms | PASS |

## Hero animation (stage hero, Char_Hero, 1080p60 fixed step) and the playable pawn

| line | target | measured | verdict |
|---|---|---|---|
| CH10 stage-hero blends | >= 0.15 s | the stage clips use the round-08 animation set unchanged (same ABP_Hero_Lineup / ABP_Hero_Leap); `video_checks.py takeoff` reads 1 - 2 frames on BOTH the round-08 and the round-16 leap clips (its ground line is set from the bobbing run, not a usable instrument) | not re-measured |
| playable pawn (P3 `WebTravAnimInstance`, NOT P2) run cadence | (P3) 3.2 - 3.8 | 4.0 steps/s (FFT 4.133 Hz, bob period 15.0 frames) | logged for the traversal brief |
| playable pawn idle -> run start | (P3) blend >= 0.15 s | largest one-frame change of the silhouette: height 0.09, width 0.521 at t = 1.717 s | logged for the traversal brief |
| playable pawn start, from its own telemetry | (P3) | clip switches A_Hero_idle -> A_Hero_jog @0.900 s -> A_Hero_run @1.000 s, all at blend weight 1.0; the 10-number pose signature then needs 26 frames (0.433 s) for 90 % of its change (largest single frame 5.3 %) | logged for the traversal brief |

## Enemy pack (unchanged since round 13: paused in the first pass)

| line | measured |
|---|---|
| lineup 4K still, wall / floor mean RGB (round 04 -> 12 -> 13 -> 14 -> 15) | {'wall': [208.3, 208.7, 212.9], 'floor': [165.2, 182.8, 201.4], 'brick': [165.7, 132.3, 132.0]} -> {'wall': [207.5, 208.1, 212.4], 'floor': [164.7, 183.0, 202.3], 'brick': [163.3, 126.4, 126.3]} -> {'wall': [140.1, 140.3, 148.6], 'floor': [86.8, 103.5, 128.4], 'brick': [87.3, 65.5, 65.5]} -> {'wall': [139.6, 139.2, 147.2], 'floor': [87.5, 105.6, 130.5], 'brick': [87.2, 65.5, 65.4]} -> **{'wall': [139.1, 138.9, 146.6], 'floor': [88.7, 106.6, 131.1], 'brick': [87.3, 65.5, 65.4]}** |
| the skins-stage EV (+10) leaking into Char_Lineup | NO: the r04 and r12 lineups have the same exposure (wall 208 / 207 of 255); the washed-out look is the pale sunlit wall, the -0.6 EV bias and the weaker fill of round 13 are unchanged |
| fight script / choreography / weapon fit vs the round-10 commit | IDENTICAL (git diff --stat empty) |

Resolution: stills output 3840x2160, internal 3840x2160 (`r.ScreenPercentage 100`). Movies 1920x1080, fixed 1/60 s step.


