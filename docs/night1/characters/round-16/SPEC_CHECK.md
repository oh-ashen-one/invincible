# Round 16 SPEC CHECK (piece G, hero skins)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. Numbers are read from `evidence/` by `tools/ue_char/suits/spec_check_r16.py`;
> every measure of a still runs on the lossless 3840x2160 PNG originals of the real game (UE 5.8.3 `-game`, offscreen, internal 3840x2160); the round-15 baseline = the r15 PNG originals.

## Part 1: round-16 target (critic r15 image-quality defects; first-pass acceptance line IQ >= 6)

**(1) Back bleed** (`back_bleed_r16.py`, 8 back stills at 4K): accent-family pixels (the front emblem / sash fill colour and its darker shade, colour direction within 20 deg) inside the back torso mask; gate: no cluster >= 20 px.

| suit | clusters >= 20 px r15 -> **r16** | largest cluster px r15 -> **r16** | accent px in the mask r15 -> **r16** | verdict |
|---|---|---|---|---|
| tessera | 4 -> **0** | 7792 -> **0** | 8271 -> **0** | PASS |
| verdant | 4 -> **0** | 7577 -> **0** | 7994 -> **0** | PASS |
| plum | 8 -> **0** | 3444 -> **0** | 6959 -> **0** | PASS |
| cinder | 5 -> **0** | 6296 -> **0** | 6645 -> **0** | PASS |
| glacier | 3 -> **0** | 297 -> **0** | 388 -> **0** | PASS |
| ash | 6 -> **0** | 6687 -> **0** | 6931 -> **0** | PASS |
| saffron | 1 -> **0** | 10276 -> **0** | 10345 -> **113** | PASS |
| sage | 4 -> **0** | 385 -> **0** | 1099 -> **0** | PASS |

8 of 8 backs pass (overlays `evidence/measures/back_bleed/`, mask yellow, accent pixels magenta). All 8 back stills are committed at 4K (`stills/skin_<suit>_back_4k.jpg`).

**(2) Cord jogs** (`cord_jog_r16.py`, 8 chest stills: the yoke seam cord tracked across the image-left torso side under the arm, the largest row step between neighbouring columns beyond the local slope; gate <= 4 px). The r15 critic boxes: Verdant ~(1300, 1310), Ash / Cinder the same side.

| suit | max jump r15 -> **r16** (px) | at (x, y) r16 | tracked columns r16 | verdict |
|---|---|---|---|---|
| tessera | 17.1 -> **0.9** | [1305, 1312] | 411 | PASS |
| verdant | 14.0 -> **0.5** | [1586, 1316] | 491 | PASS |
| plum | 8.0 -> **0.9** | [1169, 1288] | 516 | PASS |
| cinder | 18.6 -> **0.6** | [1481, 1315] | 371 | PASS |
| glacier | 13.3 -> **0.5** | [1588, 1269] | 439 | PASS |
| ash | 36.2 -> **0.9** | [1431, 1310] | 501 | PASS |
| saffron | 10.2 -> **0.5** | [1471, 1321] | 480 | PASS |
| sage | 32.0 -> **0.6** | [1158, 1285] | 570 | PASS |

8 of 8 chest stills pass (overlays `evidence/measures/cord_jog/`).

**(3) Face centre seam** (`seam_track_r16.py`, 8 headfront stills: the light seam cord tracked row by row from the crown to the chin; `dev100` = the largest lateral change over 100 rows; gate <= 10 px). r16: the headfront portrait follows the head bone (`WHShot.bHeadLock`, log `evidence/headlock_log.txt`).

| suit | dev100 r15 -> **r16** (px) | lateral range r15 -> **r16** | residual from a line r16 | tracked rows r16 | verdict |
|---|---|---|---|---|---|
| tessera | 3.9 -> **4.5** | 6.2 -> **5.9** | 3.9 | 940 | PASS |
| verdant | 4.7 -> **None** | 6.4 -> **None** | None | None | FAIL |
| plum | 4.6 -> **4.7** | 7.4 -> **5.7** | 3.1 | 994 | PASS |
| cinder | 15.9 -> **10.9** | 52.8 -> **33.8** | 14.9 | 1768 | FAIL |
| glacier | 13.8 -> **10.6** | 18.6 -> **12.2** | 10.1 | 368 | FAIL |
| ash | 6.8 -> **6.7** | 12.5 -> **10.8** | 5.2 | 1409 | PASS |
| saffron | 2.9 -> **2.6** | 4.2 -> **4.2** | 2.8 | 1154 | PASS |
| sage | 7.7 -> **8.4** | 9.4 -> **10.0** | 6.7 | 442 | PASS |

5 of 8 headfront stills pass (overlays `evidence/measures/seam_track/`).

Supplementary (NOT the committed set): the same content in this round's hold 2 (13:01, same maps except Saffron's arm ring cords; idle phase differs): dev100 tessera 5.6, verdant 5.6, plum 4.6, cinder 7.4, glacier 8.8, ash 6.6, saffron 2.8, sage 8.6 - the residual depends on the idle phase (the lower face is partly neck-weighted, the head lock follows the head bone only).

**(4a) Net ends** (`net_end_check_r15.py --n 4096`, the paint itself): dead-end blobs in open fabric r15 **83** -> r16 **0** (armpit crease zone, folded under the arm, not counted: 95 -> 45).

| suit | open fabric r15 -> **r16** | by layer r16 |
|---|---|---|
| tessera | 14 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| verdant | 6 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| plum | 8 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| cinder | 7 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| glacier | 16 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| ash | 3 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| saffron | 21 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| sage | 8 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |

**(4b) Q6 Verdant armpit cord** (`iq_check_r15.py`, its keys: r14 = the baseline = r15 stills, r15 = this round): pinch ratio (min / median thickness along the run) r15 0.46 -> **r16 0.54** (min 7 px, median 13.0 px, 0 gap columns); gate >= 0.5: **PASS**.

**(4c) Ash notch smear (~1480, 1170)** and **(5) the no-new-defect crop pass**: read by eye on `evidence/measures/crops/crops_<suit>.jpg` (r15 row over r16 row); the list is in `CAPTURES.md`.

**Summary of the measured gates:** back PASS, jog PASS, seam FAIL, net PASS, q6 PASS

## Part 2: the round-15 instrument set re-run on round 16 (baseline = round 15)

### (round-15 set) Round 16 SPEC CHECK (piece G, hero skins)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. Numbers are read from `evidence/` by `tools/ue_char/suits/spec_check_r15.py`;
> the measures of the 4K chest stills run on the lossless PNG originals of the real game (UE 5.8.3 `-game`, offscreen, internal 3840x2160).

## Round target (critic r15): the P2-owned lines + the playable pawn on the merged P3 r22 ground blend

**R1 rim depth** (`rim_depth_r15.py`, 4K headside stills, lossless PNG originals): the front-most pixel of the lens RIM lies >= 1 % of the head height (>= 16 px at 1590 px) BEHIND the front-most pixel of the brow. The critic r15 measured the Verdant rim 18 px proud (2273 against 2255).

| suit | rim behind brow, px (+ = behind) r15 -> **r16** | % of head height r15 -> **r16** | verdict |
|---|---|---|---|
| tessera | 35.3 -> **38.0** | 2.3 -> **2.48** | PASS |
| verdant | 34.3 -> **34.3** | 2.34 -> **2.32** | PASS |
| plum | 34.0 -> **33.0** | 2.29 -> **2.19** | PASS |
| cinder | 41.0 -> **40.3** | 2.68 -> **2.63** | PASS |
| glacier | 38.3 -> **38.0** | 2.53 -> **2.51** | PASS |
| ash | 36.0 -> **37.3** | 2.35 -> **2.44** | PASS |
| saffron | 49.0 -> **47.7** | 3.33 -> **3.22** | PASS |
| sage | 42.3 -> **44.0** | 2.85 -> **2.92** | PASS |

8 of 8 suits pass R1 (overlays `evidence/measures/rim_overlays/`; CPU model of the same pose before the hold: `round-16/CAPTURES.md`).

| item | measure | r15 | **r16** | verdict |
|---|---|---|---|---|
| Q5 Ash sash-end accent pipe (box 1490-1540 x 760-1150) | pixels between the pipe and the DEEP border cord (p90 / max) | 2.0 / 10 px | **2.0 / 80 px** (pipe 4.0 px wide, x [1609, 1633]) | PASS |
| Q6 Verdant armpit piping (box 1160-1270 x 1150-1270) | cord thickness min / median along its own run (1 = even, 0 = a gap); gap columns in the run | 0.46 (min 6 px, median 13.0 px; 0 gap columns) | **0.54** (min 7 px, median 13.0 px; 0 gap columns; the cord now ends at the shoulder cap edge, last column x 1229) | PASS |
| Q7 brow trim, tessera | trim edge rise / thickness at the brow (px, perpendicular) | 7.91 / 22.85 | **7.9 / 22.82** (brow/temple 1.85, sane windows: True; r16/r15 edge rise 1.0) | see crop |
| Q7 brow trim, verdant | trim edge rise / thickness at the brow (px, perpendicular) | 7.57 / 21.1 | **9.37 / 21.02** (brow/temple 2.72, sane windows: True; r16/r15 edge rise 1.24) | see crop |
| Q7 brow trim, plum | trim edge rise / thickness at the brow (px, perpendicular) | 8.04 / 15.24 | **8.43 / 16.85** (brow/temple 3.28, sane windows: True; r16/r15 edge rise 1.05) | see crop |
| Q7 brow trim, cinder | trim edge rise / thickness at the brow (px, perpendicular) | 7.96 / 18.43 | **8.03 / 17.74** (brow/temple 2.69, sane windows: True; r16/r15 edge rise 1.01) | see crop |
| Q7 brow trim, glacier | trim edge rise / thickness at the brow (px, perpendicular) | 9.6 / 24.43 | **9.59 / 24.41** (brow/temple 1.99, sane windows: True; r16/r15 edge rise 1.0) | see crop |
| Q7 brow trim, ash | trim edge rise / thickness at the brow (px, perpendicular) | 10.25 / 16.24 | **10.28 / 17.13** (brow/temple 2.02, sane windows: True; r16/r15 edge rise 1.0) | see crop |
| Q7 brow trim, saffron | trim edge rise / thickness at the brow (px, perpendicular) | 1.71 / 6.34 | **1.68 / 6.73** (brow/temple None, sane windows: None; r16/r15 edge rise 0.98) | see crop |
| Q7 brow trim, sage | trim edge rise / thickness at the brow (px, perpendicular) | 2.77 / 3.7 | **2.62 / 3.28** (brow/temple 0.36, sane windows: False; r16/r15 edge rise 0.95) | see crop |

**Net / groove ends** (`net_end_check_r15.py`, the paint itself at 4096: a net line ends where its zone mask falls; a DEAD END has no raised cord within 2.5 mm and is not at an atlas island edge): dead-end blobs in open fabric, all 8 suits: r15 switches **83** -> r16 **0** (torso net: 1 -> 0; armpit crease zone, folded away under the arm, not counted: 95 -> 45).

| suit | open-fabric dead ends r15 -> r16 | by layer (r16) |
|---|---|---|
| tessera | 14 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| verdant | 6 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| plum | 8 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| cinder | 7 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| glacier | 16 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| ash | 3 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| saffron | 21 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| sage | 8 -> **0** | {'armU_R': 0, 'torso': 0, 'armU_L': 0, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |

**Pawn** (`pawn_check_r15.py`; P3 `WebTravAnimInstance` GroundBlendS 0.18 s merged from Opus-5.5-Loop-Night-1; the run CADENCE is P3's and routed to traversal, not a P2 gate):

| test | r15 | **r16** | verdict |
|---|---|---|---|
| P1 no frame-to-frame luma difference in 0 - 1.5 s above 2x both neighbours (whole frame / hero blob) | 0 / 0 pops (largest 5.2 at None s) | **0 / 0 pops** (largest 5.172) | PASS |
| P2 no `anim_weight` step above dt / 0.18 per frame (0.0926 at 60 fps); NOTE `anim_weight` is the TOTAL clip weight (always 1.0), so this test is vacuous | max step 0.0 | **max step 0.0** (limit 0.0928) | PASS (vacuous) |
| pose-signature steps 0 - 1.5 s (P3 ground blend): largest / median of 0.5 - 2 s | 1.7 | **1.7** (at 1.0833 s) | logged |
| clip switches in 0 - 1.5 s | ['A_Hero_jog', 'A_Hero_run'] | **['A_Hero_jog', 'A_Hero_run']** | logged |

## Kept: the round-15 sculpt gates (G1 - G3, H1 - H6) on the round-16 head

Measured by `tools/ue_char/suits/head_check_r14.py` on the lossless 4K PNG originals of the real game: `head` = 12 deg off the face axis (1.0 m), `headfront` = the same framing straight on (0 deg), `head34` = the round-12 head framing (25 deg), `headside` = profile (1.25 m).
**G1** headside: the silhouette between the brow's front-most point and the nose tip dips >= 1.5 % of the head height (crown to chin, 1590 px at this framing) behind the brow -> nose-tip chord. **G2** the brow's front-most point is >= 1 % of the head height in front of the top of the lens (front-most glass pixel of the top quarter of its rows); G2b = the same with a 3.1 mm rim allowance. **G3** horizontal luma lines through the cheek bones (the band lens bottom + 15 px .. + 200 px, every 15 px, 15 px smoothing, head interior minus 30 px at each edge): >= 3 extrema of prominence >= 20 luma on >= 70 % of the lines, swing >= 20 on every line. Kept from round 13 (head_check_r13.py): H1 nose-bridge luma profile, H2 nose bump >= 2 % of head height, H3 lens >= 1.6x round 12, H4 ONE closed raised rim >= 6 px on >= 90 % of 48 angles, H5 raised face seam (lit / shadow pair >= 20 luma, no black run), H6 lenses inside the outline.

| suit | G1 recess % HH (px) | G2 brow over lens top % HH (with rim) | G3 cheek lines >= 3 extrema: 12 deg / 0 deg / 25 deg (min swing) | H3 near lens x r12 (mean 12 deg) | H4 rim px, closed (head / head34) | H5 seam pair | H1 / H2 / H6 | verdict |
|---|---|---|---|---|---|---|---|---|
| tessera | **7.86** (120.4 px) | **6.46** (5.12) | 13/13 (136.8) / 13/13 (132.7) / 13/13 (118.8) | 1.78 (1.826) | 15.5, 0.625 ; 13.5, 0.5 | 143.8 | 4/127.4 / 8.95 / [204, 37] | FAIL H4 |
| verdant | **7.96** (117.6 px) | **6.18** (4.78) | 13/13 (154.4) / 13/13 (158.0) / 13/13 (143.8) | 1.741 (1.676) | 14.0, 0.604 ; 12.5, 0.646 | 151.5 | 3/149.7 / 11.23 / [197, 43] | FAIL H4 |
| plum | **7.9** (118.8 px) | **6.12** (4.75) | 13/13 (130.0) / 13/13 (133.6) / 13/13 (118.9) | 1.784 (1.637) | 24.5, 0.917 ; 17.8, 0.917 | 141.3 | 5/121.8 / 8.78 / [248, 16] | PASS |
| cinder | **7.83** (119.9 px) | **6.49** (5.14) | 13/13 (153.5) / 13/13 (157.4) / 13/13 (144.0) | 1.758 (1.718) | 11.2, 0.521 ; 14.2, 0.729 | 158.6 | 3/88.2 / 8.85 / [132, 22] | FAIL H4 |
| glacier | **7.81** (118.2 px) | **6.94** (5.57) | 13/13 (132.8) / 13/13 (120.6) / 13/13 (129.4) | 1.725 (1.685) | 45.5, 1.0 ; 42.8, 1.0 | 103.4 | 4/101.4 / 10.47 / [46, 45] | PASS |
| ash | **7.87** (120.6 px) | **6.28** (4.94) | 13/13 (158.2) / 13/13 (155.3) / 13/13 (142.3) | 1.783 (1.823) | 16.5, 0.688 ; 16.5, 0.812 | 157.9 | 4/121.3 / 9.25 / [136, 38] | FAIL H4 |
| saffron | **7.92** (117.3 px) | **6.13** (4.73) | 13/13 (184.4) / 13/13 (186.7) / 13/13 (171.6) | 1.733 (1.669) | 23.2, 0.854 ; 13.8, 0.729 | 187.5 | 3/184.1 / 11.19 / [197, 45] | FAIL H4 |
| sage | **7.89** (118.8 px) | **6.11** (4.74) | 13/13 (148.6) / 13/13 (144.0) / 13/13 (150.9) | 1.756 (1.627) | 43.2, 0.958 ; 42.8, 0.979 | 128.6 | 7/131.7 / 8.68 / [231, 28] | PASS |

3 of 8 suits pass every gate (G1, G2, G2b, G3 x 3 views, H1 - H6); 8 of 8 pass the three critic tests G1 + G2 + G3 (12 deg and 0 deg) (`evidence/head_check.json`, overlays in `evidence/measures/head_overlays/`).

Mesh silhouette of the finished head (CPU, the GLB the engine imports; `head_profile_r14.py`): recess 7.24 % HH, brow over the lens top 6.95 % HH, over every rim vertex 5.27 % HH, nose bump 20.02 % HH, mouth / chin groove 6.89 mm; lens-to-outline clearance in a 12 deg view 39.2 px (glass) / 24.0 px (rim).

## Keep: the round-12 lines (raised piping, nothing under the sash, no fold)

| suit | relief: 64 px cells with a lit / shadow pair >= 20 luma (r15 -> r16) | median cell delta (r15 -> r16) | sash: longest dark run px, target <= 10 (r15 -> r16) | sash verdict |
|---|---|---|---|---|
| tessera | 0.618 -> **0.633** (250 of 395 cells) | 25.9 -> **26.6** | 5 -> **5** | PASS |
| verdant | 0.658 -> **0.685** (189 of 276 cells) | 35.4 -> **32.1** | 9 -> **11** | FAIL |
| plum | 0.701 -> **0.703** (237 of 337 cells) | 31.1 -> **31.4** | 7 -> **8** | PASS |
| cinder | 0.689 -> **0.723** (206 of 285 cells) | 30.3 -> **30.6** | 6 -> **6** | PASS |
| glacier | 0.599 -> **0.621** (177 of 285 cells) | 25.3 -> **25.1** | None -> **None** | n/a |
| ash | 0.751 -> **0.735** (255 of 347 cells) | 33.0 -> **33.8** | 3 -> **3** | PASS |
| saffron | 0.703 -> **0.661** (187 of 283 cells) | 34.4 -> **33.9** | 6 -> **5** | PASS |
| sage | 0.596 -> **0.599** (185 of 309 cells) | 27.0 -> **28.4** | None -> **None** | n/a |

| Verdant chevron edge at the critic's columns x 1320-1400 | target | round 14 | round 15 | verdict |
|---|---|---|---|---|
| largest column-to-column jump beyond its slope | <= 2 px | None px | **no edge in the critic columns** | n/a: since round 14 the Verdant V ends at |x| = 0.118 m (a straight piped end), so the chevron's upper edge no longer runs into the armpit where the r13 step was; the instrument finds no edge in its ROI. The step is gone from the frame (crop `evidence/measures/iq/chest_verdant.jpg`), not measured to 0 |

## Keep-passing lines

| line | target | measured | verdict |
|---|---|---|---|
| CH1 front stills (hero height / frame height, all 8 suits) | 0.48 - 0.62 | 0.542 - 0.544 | PASS |
| IP guard palette P1 - P7 (round-16 deeper sockets / pipe join / yoke seams) | 0 failures | min palette distance 49.3 over 28 pairs, fails: none | PASS |
| UV seam runs at 4K (texture level) | <= 40 px | worst 2.7 px, runs > 40 px: 0 | PASS |
| OCR of every 4K still | 0 hits | 1 hits over 56 images | REVIEW |
| Tessera stays the default; generator regression (r8 legacy texel for texel + r16 default) | PASS | REGRESSION PASS | PASS |
| swap on the pixels (playable pawn, real T presses) | <= 500 ms | 7 of 7 presses found, worst 33.3 ms | PASS |

## Hero animation (stage hero, Char_Hero, 1080p60 fixed step) and the playable pawn

| line | target | measured | verdict |
|---|---|---|---|
| CH10 stage-hero blends | >= 0.15 s | the stage clips use the round-08 animation set unchanged (same ABP_Hero_Lineup / ABP_Hero_Leap); `video_checks.py takeoff` reads 1 - 2 frames on BOTH the round-08 and the round-15 leap clips (its ground line is set from the bobbing run, not a usable instrument) | not re-measured |
| playable pawn (P3 `WebTravAnimInstance`, NOT P2) run cadence | (P3) 3.2 - 3.8 | 4.0 steps/s (FFT 4.133 Hz, bob period 15.0 frames) | logged for the traversal brief |
| playable pawn idle -> run start | (P3) blend >= 0.15 s | largest one-frame change of the silhouette: height 0.089, width 0.519 at t = 1.717 s | logged for the traversal brief |
| playable pawn start, from its own telemetry | (P3) | clip switches A_Hero_idle -> A_Hero_jog @0.900 s -> A_Hero_run @1.000 s, all at blend weight 1.0; the 10-number pose signature then needs 26 frames (0.433 s) for 90 % of its change (largest single frame 5.3 %) | logged for the traversal brief |

## Enemy pack (unchanged since round 13: paused in the first pass)

| line | measured |
|---|---|
| lineup 4K still, wall / floor mean RGB (round 04 -> 12 -> 13 -> 14 -> 15) | {'wall': [208.3, 208.7, 212.9], 'floor': [165.2, 182.8, 201.4], 'brick': [165.7, 132.3, 132.0]} -> {'wall': [207.5, 208.1, 212.4], 'floor': [164.7, 183.0, 202.3], 'brick': [163.3, 126.4, 126.3]} -> {'wall': [140.1, 140.3, 148.6], 'floor': [86.8, 103.5, 128.4], 'brick': [87.3, 65.5, 65.5]} -> {'wall': [139.6, 139.2, 147.2], 'floor': [87.5, 105.6, 130.5], 'brick': [87.2, 65.5, 65.4]} -> **{'wall': [139.1, 138.9, 146.6], 'floor': [88.7, 106.6, 131.1], 'brick': [87.3, 65.5, 65.4]}** |
| the skins-stage EV (+10) leaking into Char_Lineup | NO: the r04 and r12 lineups have the same exposure (wall 208 / 207 of 255); the washed-out look is the pale sunlit wall, the -0.6 EV bias and the weaker fill of round 13 are unchanged |
| fight script / choreography / weapon fit vs the round-10 commit | IDENTICAL (git diff --stat empty) |

Resolution: stills output 3840x2160, internal 3840x2160 (`r.ScreenPercentage 100`). Movies 1920x1080, fixed 1/60 s step.

