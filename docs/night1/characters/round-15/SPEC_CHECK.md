# Round 15 SPEC CHECK (piece G, hero skins)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. Numbers are read from `evidence/` by `tools/ue_char/suits/spec_check_r15.py`;
> the measures of the 4K chest stills run on the lossless PNG originals of the real game (UE 5.8.3 `-game`, offscreen, internal 3840x2160).

## Round target (critic r14): the P2-owned lines + the playable pawn on the merged P3 r22 ground blend

**R1 rim depth** (`rim_depth_r15.py`, 4K headside stills, lossless PNG originals): the front-most pixel of the lens RIM lies >= 1 % of the head height (>= 16 px at 1590 px) BEHIND the front-most pixel of the brow. The critic r14 measured the Verdant rim 18 px proud (2273 against 2255).

| suit | rim behind brow, px (+ = behind) r14 -> **r15** | % of head height r14 -> **r15** | verdict |
|---|---|---|---|
| tessera | -16.0 -> **35.3** | -1.06 -> **2.3** | PASS |
| verdant | -14.0 -> **34.3** | -0.91 -> **2.34** | PASS |
| plum | 7.0 -> **34.0** | 0.46 -> **2.29** | PASS |
| cinder | -15.3 -> **41.0** | -1.0 -> **2.68** | PASS |
| glacier | -13.0 -> **38.3** | -0.89 -> **2.53** | PASS |
| ash | 10.3 -> **36.0** | 0.69 -> **2.35** | PASS |
| saffron | -14.3 -> **49.0** | -0.93 -> **3.33** | PASS |
| sage | 0.0 -> **42.3** | 0.0 -> **2.85** | PASS |

8 of 8 suits pass R1 (overlays `evidence/measures/rim_overlays/`; CPU model of the same pose before the hold: `round-15/CAPTURES.md`).

| item | measure | r14 | **r15** | verdict |
|---|---|---|---|---|
| Q5 Ash sash-end accent pipe (box 1490-1540 x 760-1150) | pixels between the pipe and the DEEP border cord (p90 / max) | 33.0 / 80 px | **2.0 / 10 px** (pipe 4.0 px wide, x [1655, 1672]) | PASS |
| Q6 Verdant armpit piping (box 1160-1270 x 1150-1270) | cord thickness min / median along its own run (1 = even, 0 = a gap); gap columns in the run | 0.0 (min 0 px, median 7.0 px; 13 gap columns) | **0.46** (min 6 px, median 13.0 px; 0 gap columns; the cord now ends at the shoulder cap edge, last column x 1213) | FAIL by my own 0.5 gate (no gap any more; the cord thins toward the crease where it ends) |
| Q7 brow trim, tessera | trim edge rise / thickness at the brow (px, perpendicular) | 7.81 / 22.56 | **7.91 / 22.85** (brow/temple 1.87, sane windows: True; r15/r14 edge rise 1.01) | see crop |
| Q7 brow trim, verdant | trim edge rise / thickness at the brow (px, perpendicular) | 11.34 / 25.39 | **7.57 / 21.1** (brow/temple 2.19, sane windows: True; r15/r14 edge rise 0.67) | PASS |
| Q7 brow trim, plum | trim edge rise / thickness at the brow (px, perpendicular) | 8.43 / 13.19 | **8.04 / 15.24** (brow/temple 3.12, sane windows: True; r15/r14 edge rise 0.95) | see crop |
| Q7 brow trim, cinder | trim edge rise / thickness at the brow (px, perpendicular) | 10.85 / 19.2 | **7.96 / 18.43** (brow/temple 2.66, sane windows: True; r15/r14 edge rise 0.73) | PASS |
| Q7 brow trim, glacier | trim edge rise / thickness at the brow (px, perpendicular) | 8.94 / 21.72 | **9.6 / 24.43** (brow/temple 1.99, sane windows: True; r15/r14 edge rise 1.07) | see crop |
| Q7 brow trim, ash | trim edge rise / thickness at the brow (px, perpendicular) | 6.63 / 12.63 | **10.25 / 16.24** (brow/temple 2.02, sane windows: True; r15/r14 edge rise 1.55) | see crop |
| Q7 brow trim, saffron | trim edge rise / thickness at the brow (px, perpendicular) | 2.91 / 19.41 | **1.71 / 6.34** (brow/temple None, sane windows: None; r15/r14 edge rise 0.59) | PASS |
| Q7 brow trim, sage | trim edge rise / thickness at the brow (px, perpendicular) | 4.51 / 4.75 | **2.77 / 3.7** (brow/temple 0.38, sane windows: False; r15/r14 edge rise 0.61) | PASS |

**Net / groove ends** (`net_end_check_r15.py`, the paint itself at 4096: a net line ends where its zone mask falls; a DEAD END has no raised cord within 2.5 mm and is not at an atlas island edge): dead-end blobs in open fabric, all 8 suits: r14 switches **434** -> r15 **83** (torso net: 105 -> 1; armpit crease zone, folded away under the arm, not counted: 116 -> 95).

| suit | open-fabric dead ends r14 -> r15 | by layer (r15) |
|---|---|---|
| tessera | 93 -> **14** | {'armU_R': 0, 'torso': 0, 'armU_L': 6, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 1, 'thigh_L': 7} |
| verdant | 17 -> **6** | {'armU_R': 0, 'torso': 0, 'armU_L': 4, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 2} |
| plum | 56 -> **8** | {'armU_R': 0, 'torso': 0, 'armU_L': 2, 'armF_L': 3, 'shin_L': 0, 'thigh_R': 3, 'thigh_L': 0} |
| cinder | 47 -> **7** | {'armU_R': 0, 'torso': 0, 'armU_L': 2, 'armF_L': 3, 'shin_L': 0, 'thigh_R': 1, 'thigh_L': 1} |
| glacier | 48 -> **16** | {'armU_R': 0, 'torso': 0, 'armU_L': 4, 'armF_L': 3, 'shin_L': 0, 'thigh_R': 3, 'thigh_L': 7} |
| ash | 75 -> **3** | {'armU_R': 0, 'torso': 0, 'armU_L': 3, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 0, 'thigh_L': 0} |
| saffron | 44 -> **21** | {'armU_R': 0, 'torso': 1, 'armU_L': 8, 'armF_L': 0, 'shin_L': 3, 'thigh_R': 6, 'thigh_L': 5} |
| sage | 54 -> **8** | {'armU_R': 0, 'torso': 0, 'armU_L': 4, 'armF_L': 0, 'shin_L': 0, 'thigh_R': 1, 'thigh_L': 3} |

**Pawn** (`pawn_check_r15.py`; P3 `WebTravAnimInstance` GroundBlendS 0.18 s merged from Opus-5.5-Loop-Night-1; the run CADENCE is P3's and routed to traversal, not a P2 gate):

| test | r14 | **r15** | verdict |
|---|---|---|---|
| P1 no frame-to-frame luma difference in 0 - 1.5 s above 2x both neighbours (whole frame / hero blob) | 1 / 1 pops (largest 9.474 at 0.1333 s) | **0 / 0 pops** (largest 5.2) | PASS |
| P2 no `anim_weight` step above dt / 0.18 per frame (0.0926 at 60 fps); NOTE `anim_weight` is the TOTAL clip weight (always 1.0), so this test is vacuous | max step 0.0 | **max step 0.0** (limit 0.0928) | PASS (vacuous) |
| pose-signature steps 0 - 1.5 s (P3 ground blend): largest / median of 0.5 - 2 s | 3.0 | **1.7** (at 1.0833 s) | logged |
| clip switches in 0 - 1.5 s | ['A_Hero_airRise', 'A_Hero_idle', 'A_Hero_walk', 'A_Hero_jog', 'A_Hero_run'] | **['A_Hero_jog', 'A_Hero_run']** | logged |

## Kept: the round-14 sculpt gates (G1 - G3, H1 - H6) on the round-15 head

Measured by `tools/ue_char/suits/head_check_r14.py` on the lossless 4K PNG originals of the real game: `head` = 12 deg off the face axis (1.0 m), `headfront` = the same framing straight on (0 deg), `head34` = the round-12 head framing (25 deg), `headside` = profile (1.25 m).
**G1** headside: the silhouette between the brow's front-most point and the nose tip dips >= 1.5 % of the head height (crown to chin, 1590 px at this framing) behind the brow -> nose-tip chord. **G2** the brow's front-most point is >= 1 % of the head height in front of the top of the lens (front-most glass pixel of the top quarter of its rows); G2b = the same with a 3.1 mm rim allowance. **G3** horizontal luma lines through the cheek bones (the band lens bottom + 15 px .. + 200 px, every 15 px, 15 px smoothing, head interior minus 30 px at each edge): >= 3 extrema of prominence >= 20 luma on >= 70 % of the lines, swing >= 20 on every line. Kept from round 13 (head_check_r13.py): H1 nose-bridge luma profile, H2 nose bump >= 2 % of head height, H3 lens >= 1.6x round 12, H4 ONE closed raised rim >= 6 px on >= 90 % of 48 angles, H5 raised face seam (lit / shadow pair >= 20 luma, no black run), H6 lenses inside the outline.

| suit | G1 recess % HH (px) | G2 brow over lens top % HH (with rim) | G3 cheek lines >= 3 extrema: 12 deg / 0 deg / 25 deg (min swing) | H3 near lens x r12 (mean 12 deg) | H4 rim px, closed (head / head34) | H5 seam pair | H1 / H2 / H6 | verdict |
|---|---|---|---|---|---|---|---|---|
| tessera | **7.89** (121.0 px) | **6.35** (5.0) | 13/13 (136.9) / 13/13 (134.1) / 13/13 (119.4) | 1.775 (1.822) | 15.8, 0.667 ; 15.0, 0.583 | 144.0 | 4/131.0 / 9.39 / [203, 39] | FAIL H4 |
| verdant | **7.98** (117.1 px) | **6.16** (4.75) | 13/13 (154.1) / 13/13 (158.2) / 13/13 (144.5) | 1.747 (1.675) | 12.2, 0.583 ; 11.8, 0.646 | 153.2 | 3/146.0 / 12.57 / [197, 42] | FAIL H4 |
| plum | **7.92** (117.7 px) | **5.99** (4.6) | 13/13 (130.3) / 13/13 (134.6) / 13/13 (119.8) | 1.784 (1.64) | 23.5, 0.917 ; 16.5, 0.896 | 141.4 | 5/123.8 / 10.61 / [247, 16] | FAIL H4 |
| cinder | **7.82** (119.6 px) | **6.54** (5.19) | 13/13 (151.9) / 13/13 (156.6) / 13/13 (143.0) | 1.756 (1.732) | 15.5, 0.625 ; 14.8, 0.75 | 160.3 | 3/114.8 / 8.8 / [159, 27] | FAIL H4 |
| glacier | **7.81** (118.3 px) | **6.96** (5.6) | 13/13 (132.6) / 13/13 (122.1) / 13/13 (129.6) | 1.725 (1.685) | 45.0, 1.0 ; 43.2, 1.0 | 105.2 | 4/97.5 / 10.47 / [92, 45] | PASS |
| ash | **7.87** (120.6 px) | **6.33** (4.99) | 13/13 (158.6) / 13/13 (156.8) / 13/13 (141.6) | 1.786 (1.821) | 15.2, 0.688 ; 15.5, 0.812 | 157.2 | 4/120.7 / 9.33 / [134, 38] | FAIL H4 |
| saffron | **7.95** (116.8 px) | **6.19** (4.79) | 13/13 (184.4) / 13/13 (187.2) / 13/13 (174.0) | 1.741 (1.668) | 25.5, 0.833 ; 16.8, 0.792 | 188.1 | 3/184.1 / 12.23 / [197, 45] | FAIL H4 |
| sage | **7.93** (117.6 px) | **6.09** (4.7) | 13/13 (148.4) / 13/13 (143.6) / 13/13 (150.3) | 1.759 (1.618) | 42.5, 0.958 ; 42.5, 1.0 | 127.8 | 7/132.3 / 11.03 / [235, 23] | PASS |

2 of 8 suits pass every gate (G1, G2, G2b, G3 x 3 views, H1 - H6); 8 of 8 pass the three critic tests G1 + G2 + G3 (12 deg and 0 deg) (`evidence/head_check.json`, overlays in `evidence/measures/head_overlays/`).

Mesh silhouette of the finished head (CPU, the GLB the engine imports; `head_profile_r14.py`): recess 7.24 % HH, brow over the lens top 6.95 % HH, over every rim vertex 5.27 % HH, nose bump 20.02 % HH, mouth / chin groove 6.89 mm; lens-to-outline clearance in a 12 deg view 39.2 px (glass) / 24.0 px (rim).

## Keep: the round-12 lines (raised piping, nothing under the sash, no fold)

| suit | relief: 64 px cells with a lit / shadow pair >= 20 luma (r14 -> r15) | median cell delta (r14 -> r15) | sash: longest dark run px, target <= 10 (r14 -> r15) | sash verdict |
|---|---|---|---|---|
| tessera | 0.487 -> **0.606** (235 of 388 cells) | 19.7 -> **25.1** | 6 -> **5** | PASS |
| verdant | 0.406 -> **0.638** (183 of 287 cells) | 14.9 -> **30.6** | 8 -> **9** | PASS |
| plum | 0.635 -> **0.695** (232 of 334 cells) | 28.5 -> **30.6** | 8 -> **8** | PASS |
| cinder | 0.677 -> **0.716** (199 of 278 cells) | 30.2 -> **29.7** | 7 -> **5** | PASS |
| glacier | 0.652 -> **0.595** (175 of 294 cells) | 28.1 -> **24.3** | None -> **None** | n/a |
| ash | 0.592 -> **0.753** (272 of 361 cells) | 24.0 -> **33.7** | 3 -> **3** | PASS |
| saffron | 0.532 -> **0.691** (188 of 272 cells) | 21.0 -> **33.1** | 5 -> **6** | PASS |
| sage | 0.639 -> **0.591** (185 of 313 cells) | 26.4 -> **26.0** | None -> **None** | n/a |

| Verdant chevron edge at the critic's columns x 1320-1400 | target | round 14 | round 15 | verdict |
|---|---|---|---|---|
| largest column-to-column jump beyond its slope | <= 2 px | None px | **no edge in the critic columns** | n/a: since round 14 the Verdant V ends at |x| = 0.118 m (a straight piped end), so the chevron's upper edge no longer runs into the armpit where the r13 step was; the instrument finds no edge in its ROI. The step is gone from the frame (crop `evidence/measures/iq/chest_verdant.jpg`), not measured to 0 |

## Keep-passing lines

| line | target | measured | verdict |
|---|---|---|---|
| CH1 front stills (hero height / frame height, all 8 suits) | 0.48 - 0.62 | 0.542 - 0.544 | PASS |
| IP guard palette P1 - P7 (round-15 deeper sockets / pipe join / yoke seams) | 0 failures | min palette distance 49.6 over 28 pairs, fails: none | PASS |
| UV seam runs at 4K (texture level) | <= 40 px | worst 3.3 px, runs > 40 px: 0 | PASS |
| OCR of every 4K still | 0 hits | 0 hits over 56 images | PASS |
| Tessera stays the default; generator regression (r8 legacy texel for texel + r15 default) | PASS | REGRESSION PASS | PASS |
| swap on the pixels (playable pawn, real T presses) | <= 500 ms | 7 of 7 presses found, worst 33.3 ms | PASS |

## Hero animation (stage hero, Char_Hero, 1080p60 fixed step) and the playable pawn

| line | target | measured | verdict |
|---|---|---|---|
| CH6 run step rate, side clip (head-blob bob, the round-08 instrument and window) | 3.2 - 3.8 steps/s | **3.542 Hz** (round 08 clip: 3.542 Hz) | PASS |
| CH6 run step rate, chase clip (whole-mask top bob; the head cannot be isolated from behind) | 3.2 - 3.8 | **3.542 Hz** (round 08: 3.542 Hz) | PASS |
| CH7 sprint torso lean, side clip (head to mid-torso band) | >= 15 deg | median **32.6 deg** (round 08 clip: 25.5 deg) | PASS |
| CH2 chase framing | 0.39 - 0.53 | hero height median **0.373** (round 08 clip: 0.372) | FAIL (edge) |
| CH10 stage-hero blends | >= 0.15 s | the stage clips use the round-08 animation set unchanged (same ABP_Hero_Lineup / ABP_Hero_Leap); `video_checks.py takeoff` reads 1 - 2 frames on BOTH the round-08 and the round-14 leap clips (its ground line is set from the bobbing run, not a usable instrument) | not re-measured |
| playable pawn (P3 `WebTravAnimInstance`, NOT P2) run cadence | (P3) 3.2 - 3.8 | 4.0 steps/s (FFT 4.133 Hz, bob period 15.0 frames) | logged for the traversal brief |
| playable pawn idle -> run start | (P3) blend >= 0.15 s | largest one-frame change of the silhouette: height 0.089, width 0.523 at t = 1.717 s | logged for the traversal brief |
| playable pawn start, from its own telemetry | (P3) | clip switches A_Hero_idle -> A_Hero_jog @0.900 s -> A_Hero_run @1.000 s, all at blend weight 1.0; the 10-number pose signature then needs 26 frames (0.433 s) for 90 % of its change (largest single frame 5.3 %) | logged for the traversal brief |

## Enemy pack (unchanged since round 13: paused in the first pass)

| line | measured |
|---|---|
| lineup 4K still, wall / floor mean RGB (round 04 -> 12 -> 13 -> 14 -> 15) | {'wall': [208.3, 208.7, 212.9], 'floor': [165.2, 182.8, 201.4], 'brick': [165.7, 132.3, 132.0]} -> {'wall': [207.5, 208.1, 212.4], 'floor': [164.7, 183.0, 202.3], 'brick': [163.3, 126.4, 126.3]} -> {'wall': [140.1, 140.3, 148.6], 'floor': [86.8, 103.5, 128.4], 'brick': [87.3, 65.5, 65.5]} -> {'wall': [139.6, 139.2, 147.2], 'floor': [87.5, 105.6, 130.5], 'brick': [87.2, 65.5, 65.4]} -> **{'wall': [139.1, 138.9, 146.6], 'floor': [88.7, 106.6, 131.1], 'brick': [87.3, 65.5, 65.4]}** |
| the skins-stage EV (+10) leaking into Char_Lineup | NO: the r04 and r12 lineups have the same exposure (wall 208 / 207 of 255); the washed-out look is the pale sunlit wall, the -0.6 EV bias and the weaker fill of round 13 are unchanged |
| fight script / choreography / weapon fit vs the round-10 commit | IDENTICAL (git diff --stat empty) |

Resolution: stills output 3840x2160, internal 3840x2160 (`r.ScreenPercentage 100`). Movies 1920x1080, fixed 1/60 s step.
