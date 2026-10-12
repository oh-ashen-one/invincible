# Round 14 SPEC CHECK (piece G, hero skins)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. Numbers are read from `evidence/` by `tools/ue_char/suits/spec_check_r14.py`;
> the measures of the 4K chest stills run on the lossless PNG originals of the real game (UE 5.8.3 `-game`, offscreen, internal 3840x2160).

## Round target (critic round 13): finish the shared mask sculpt

Measured by `tools/ue_char/suits/head_check_r14.py` on the lossless 4K PNG originals of the real game: `head` = 12 deg off the face axis (1.0 m), `headfront` = the same framing straight on (0 deg), `head34` = the round-12 head framing (25 deg), `headside` = profile (1.25 m).
**G1** headside: the silhouette between the brow's front-most point and the nose tip dips >= 1.5 % of the head height (crown to chin, 1590 px at this framing) behind the brow -> nose-tip chord. **G2** the brow's front-most point is >= 1 % of the head height in front of the top of the lens (front-most glass pixel of the top quarter of its rows); G2b = the same with a 3.1 mm rim allowance. **G3** horizontal luma lines through the cheek bones (the band lens bottom + 15 px .. + 200 px, every 15 px, 15 px smoothing, head interior minus 30 px at each edge): >= 3 extrema of prominence >= 20 luma on >= 70 % of the lines, swing >= 20 on every line. Kept from round 13 (head_check_r13.py): H1 nose-bridge luma profile, H2 nose bump >= 2 % of head height, H3 lens >= 1.6x round 12, H4 ONE closed raised rim >= 6 px on >= 90 % of 48 angles, H5 raised face seam (lit / shadow pair >= 20 luma, no black run), H6 lenses inside the outline.

| suit | G1 recess % HH (px) | G2 brow over lens top % HH (with rim) | G3 cheek lines >= 3 extrema: 12 deg / 0 deg / 25 deg (min swing) | H3 near lens x r12 (mean 12 deg) | H4 rim px, closed (head / head34) | H5 seam pair | H1 / H2 / H6 | verdict |
|---|---|---|---|---|---|---|---|---|
| tessera | **6.69** (100.9 px) | **3.45** (2.08) | 13/13 (129.8) / 13/13 (134.3) / 13/13 (123.3) | 1.825 (1.81) | 10.8, 0.354 ; 9.5, 0.354 | 136.1 | 5/160.4 / 9.55 / [265, 28] | FAIL H4 |
| verdant | **6.61** (101.3 px) | **3.72** (2.37) | 13/13 (149.3) / 13/13 (151.6) / 13/13 (141.6) | 1.766 (1.672) | 19.8, 0.542 ; 13.0, 0.708 | 136.7 | 3/165.4 / 9.76 / [246, 39] | FAIL H4 |
| plum | **6.57** (99.4 px) | **4.29** (2.93) | 13/13 (128.2) / 13/13 (128.0) / 13/13 (111.1) | 1.824 (1.701) | 23.8, 0.896 ; 14.0, 0.812 | 141.1 | 5/162.4 / 11.16 / [220, 50] | FAIL H4 |
| cinder | **6.6** (101.1 px) | **3.76** (2.42) | 13/13 (156.3) / 13/13 (153.6) / 13/13 (139.2) | 1.82 (1.763) | 10.0, 0.542 ; 11.5, 0.604 | 146.9 | 3/177.6 / 9.72 / [144, 48] | FAIL H4 |
| glacier | **6.81** (99.6 px) | **3.62** (2.21) | 13/13 (132.9) / 13/13 (123.4) / 13/13 (132.9) | 1.727 (1.696) | 42.8, 0.979 ; 42.2, 1.0 | 81.7 | 4/91.5 / 13.25 / [39, 55] | PASS |
| ash | **6.63** (99.0 px) | **3.77** (2.39) | 13/13 (151.4) / 13/13 (152.8) / 13/13 (149.2) | 1.834 (1.81) | 23.8, 0.792 ; 21.5, 0.771 | 131.9 | 5/169.3 / 10.32 / [128, 30] | FAIL H4 |
| saffron | **6.64** (101.7 px) | **3.76** (2.42) | 13/13 (180.9) / 13/13 (181.9) / 13/13 (175.8) | 1.755 (1.651) | 10.5, 0.583 ; 13.8, 0.625 | 171.2 | 3/195.5 / 9.8 / [263, 35] | FAIL H4 |
| sage | **6.53** (98.8 px) | **4.23** (2.86) | 13/13 (148.9) / 13/13 (140.8) / 13/13 (143.4) | 1.779 (1.67) | 42.8, 1.0 ; 41.8, 1.0 | 92.8 | 6/117.7 / 11.16 / [223, 56] | PASS |

2 of 8 suits pass every gate (G1, G2, G2b, G3 x 3 views, H1 - H6); 8 of 8 pass the three critic tests G1 + G2 + G3 (12 deg and 0 deg) (`evidence/head_check.json`, overlays in `evidence/measures/head_overlays/`).

Mesh silhouette of the finished head (CPU, the GLB the engine imports; `head_profile_r14.py`): recess 6.05 % HH, brow over the lens top 4.3 % HH, over every rim vertex 1.4 % HH, nose bump 20.18 % HH, mouth / chin groove 6.89 mm; lens-to-outline clearance in a 12 deg view 49.2 px (glass) / 33.2 px (rim).

## Image quality: the four defects of the round-13 critic (iq_check_r14.py; crops in `evidence/measures/iq/`, read them: a number does not replace looking)

| item | measure | round 13 | round 14 |
|---|---|---|---|
| Ash sash end (1410-1440, 700-1050) | end line rms deviation px / stitch dashes in the 70 px strip beyond the end | 7.24 / 1 | **6.73 / 8** |
| Ash armpit stitches (1120-1200, 1530-1600) | stitch-dash blobs in the armpit box / in the critic box / orientation spread deg | 7 / 2 / 7.6 | **0 / 0 / 0.0** |
| Sage trapezius groove (head34) | dark thin-line pixels % of the box / longest dark line px | 10.311 / 262 | **0.07 / 9** |
| Cinder shoulder silhouette (chest still) | contour vertices per 1000 px at eps 4 px / longest straight segment px / max turn deg | 12.19 / 118.5 / 12.4 | **10.87 / 146.7 / 58.1** |
| trapezius skin folds (CPU skinning, folded faces: original -> r12 -> r14 weights) | 5236 | idle@0.00 0 -> 0 -> 0; idle@1.00 0 -> 0 -> 0; idle@2.20 0 -> 0 -> 0; run@0.00 4 -> 2 -> 1; run@0.10 0 -> 0 -> 0; run@0.20 0 -> 0 -> 0; run@0.30 4 -> 2 -> 1; sprint@0.00 14 -> 14 -> 5; sprint@0.15 0 -> 0 -> 0; fightIdle@0.00 7 -> 5 -> 0 | |

## Keep: the round-12 lines (raised piping, nothing under the sash, no fold)

| suit | relief: 64 px cells with a lit / shadow pair >= 20 luma (r13 -> r14) | median cell delta (r13 -> r14) | sash: longest dark run px, target <= 10 (r13 -> r14) | sash verdict |
|---|---|---|---|---|
| tessera | 0.588 -> **0.485** (175 of 361 cells) | 23.8 -> **19.5** | 8 -> **6** | PASS |
| verdant | 0.35 -> **0.383** (88 of 230 cells) | 14.0 -> **14.2** | 8 -> **8** | PASS |
| plum | 0.588 -> **0.637** (195 of 306 cells) | 25.7 -> **26.8** | 6 -> **7** | PASS |
| cinder | 0.613 -> **0.678** (156 of 230 cells) | 25.6 -> **30.6** | 6 -> **5** | PASS |
| glacier | 0.675 -> **0.627** (151 of 241 cells) | 28.6 -> **29.0** | None -> **None** | n/a |
| ash | 0.567 -> **0.613** (187 of 305 cells) | 23.5 -> **25.6** | 5 -> **3** | PASS |
| saffron | 0.527 -> **0.522** (118 of 226 cells) | 21.7 -> **20.4** | 6 -> **6** | PASS |
| sage | 0.592 -> **0.607** (159 of 262 cells) | 24.5 -> **25.7** | None -> **None** | n/a |

| Verdant chevron edge at the critic's columns x 1320-1400 | target | round 13 | round 14 | verdict |
|---|---|---|---|---|
| largest column-to-column jump beyond its slope | <= 2 px | 29.24 px | **no edge in the critic columns** | n/a: since round 14 the Verdant V ends at |x| = 0.118 m (a straight piped end), so the chevron's upper edge no longer runs into the armpit where the r13 step was; the instrument finds no edge in its ROI. The step is gone from the frame (crop `evidence/measures/iq/chest_verdant.jpg`), not measured to 0 |

## Keep-passing lines

| line | target | measured | verdict |
|---|---|---|---|
| CH1 front stills (hero height / frame height, all 8 suits) | 0.48 - 0.62 | 0.543 - 0.544 | PASS |
| IP guard palette P1 - P7 (round-14 hood lift / face tone / piped sash ends) | 0 failures | min palette distance 38.4 over 28 pairs, fails: none | PASS |
| UV seam runs at 4K (texture level) | <= 40 px | worst 4.3 px, runs > 40 px: 0 | PASS |
| OCR of every 4K still | 0 hits | 1 hits over 56 images | REVIEW |
| Tessera stays the default; generator regression (r8 legacy texel for texel + r14 default) | PASS | REGRESSION PASS | PASS |
| swap on the pixels (playable pawn, real T presses) | <= 500 ms | 7 of 7 presses found, worst 33.3 ms | PASS |

## Hero animation (stage hero, Char_Hero, 1080p60 fixed step) and the playable pawn

| line | target | measured | verdict |
|---|---|---|---|
| CH6 run step rate, side clip (head-blob bob, the round-08 instrument and window) | 3.2 - 3.8 steps/s | **3.542 Hz** (round 08 clip: 3.542 Hz) | PASS |
| CH6 run step rate, chase clip (whole-mask top bob; the head cannot be isolated from behind) | 3.2 - 3.8 | **3.542 Hz** (round 08: 3.542 Hz) | PASS |
| CH7 sprint torso lean, side clip (head to mid-torso band) | >= 15 deg | median **33.5 deg** (round 08 clip: 25.5 deg) | PASS |
| CH2 chase framing | 0.39 - 0.53 | hero height median **0.392** (round 08 clip: 0.372) | PASS |
| CH10 stage-hero blends | >= 0.15 s | the stage clips use the round-08 animation set unchanged (same ABP_Hero_Lineup / ABP_Hero_Leap); `video_checks.py takeoff` reads 1 - 2 frames on BOTH the round-08 and the round-14 leap clips (its ground line is set from the bobbing run, not a usable instrument) | not re-measured |
| playable pawn (P3 `WebTravAnimInstance`, NOT P2) run cadence | (P3) 3.2 - 3.8 | 4.0 steps/s (FFT 4.133 Hz, bob period 15.0 frames) | logged for the traversal brief |
| playable pawn idle -> run start | (P3) blend >= 0.15 s | largest one-frame change of the silhouette: height 0.09, width 0.769 at t = 0.183 s | logged for the traversal brief |
| playable pawn start, from its own telemetry | (P3) | clip switches A_Hero_idle -> A_Hero_walk @0.817 s -> A_Hero_jog @0.867 s -> A_Hero_run @0.983 s, all at blend weight 1.0; the 10-number pose signature then needs 28 frames (0.467 s) for 90 % of its change (largest single frame 5.8 %) | logged for the traversal brief |

## Enemy pack (unchanged since round 13: paused in the first pass)

| line | measured |
|---|---|
| lineup 4K still, wall / floor mean RGB (round 04 -> round 12 -> round 13 -> round 14) | {'wall': [208.3, 208.7, 212.9], 'floor': [165.2, 182.8, 201.4], 'brick': [165.7, 132.3, 132.0]} -> {'wall': [207.5, 208.1, 212.4], 'floor': [164.7, 183.0, 202.3], 'brick': [163.3, 126.4, 126.3]} -> {'wall': [140.1, 140.3, 148.6], 'floor': [86.8, 103.5, 128.4], 'brick': [87.3, 65.5, 65.5]} -> **{'wall': [139.6, 139.2, 147.2], 'floor': [87.5, 105.6, 130.5], 'brick': [87.2, 65.5, 65.4]}** |
| the skins-stage EV (+10) leaking into Char_Lineup | NO: the r04 and r12 lineups have the same exposure (wall 208 / 207 of 255); the washed-out look is the pale sunlit wall, the -0.6 EV bias and the weaker fill of round 13 are unchanged |
| fight script / choreography / weapon fit vs the round-10 commit | IDENTICAL (git diff --stat empty) |

Resolution: stills output 3840x2160, internal 3840x2160 (`r.ScreenPercentage 100`). Movies 1920x1080, fixed 1/60 s step.
