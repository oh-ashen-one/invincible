# Round 13 SPEC CHECK (piece G, hero skins)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. Numbers are read from `evidence/` by `tools/ue_char/suits/spec_check_r13.py`;
> the measures of the 4K chest stills run on the lossless PNG originals of the real game (UE 5.8.3 `-game`, offscreen, internal 3840x2160).

## Round target (critic round 12): sculpt the shared mask head

Measured by `tools/ue_char/suits/head_check_r13.py` on the lossless 4K PNG originals of the real game: `head` = 12 deg off the face axis (1.0 m), `head34` = the round-12 head framing (25 deg), `headside` = profile (1.25 m).
H1 nose-bridge luma profile (vertical, midline between the lenses, 11 px smoothing): extrema with prominence >= 20 luma, count >= 3 and swing >= 20. H2 silhouette nose bump >= 2 % of head height (profile still: front-most silhouette column above the line brow point -> chin point). H3 lens width >= 1.6x round 12 (lens px width / head silhouette width at the lens row; PASS = the near lens in the round-12 framing and the mean of both lenses in the 12 deg still; the far lens of a 25 deg view is foreshortened and partly behind the silhouette: reported, not gated). H4 rim: the contiguous band around each lens whose luma differs from the mask by >= 15 (of 255) is >= 6 px wide on >= 90 % of 48 angles. H5 face seam: lit / shadow pair >= 20 luma across the midline cord at 12 heights, no black run >= 12 px. H6 both lenses >= 3 px from the background in the 12 deg view (the lenses wrap the face and lie against its outline).

| suit | H1 extrema / swing (head, head34) | H2 nose bump % of head height | H3 lens / head width (r12 -> r13), ratio | H4 rim px median, closed (head / head34) | H5 seam pair, black run | H6 lens edge distance px | verdict |
|---|---|---|---|---|---|---|---|
| tessera | 4 / 144.1 ; 2 / 141.7 | **8.69** | 0.1888 -> 0.332; near lens **1.949x**, far lens 1.556x, mean (12 deg still) **1.88x** | 13.0, 0.854 ; 11.0, 0.854 | 65.6, 0 | [284, 12] | FAIL H4 |
| verdant | 3 / 99.3 ; 3 / 150.2 | **8.7** | 0.2064 -> 0.3192; near lens **1.889x**, far lens 1.161x, mean (12 deg still) **1.741x** | 35.0, 0.854 ; 34.2, 0.729 | 85.3, 0 | [233, 44] | FAIL H4 |
| plum | 2 / 178.8 ; 5 / 174.2 | **8.59** | 0.2064 -> 0.338; near lens **1.905x**, far lens 1.391x, mean (12 deg still) **1.754x** | 26.8, 0.979 ; 15.0, 0.917 | 49.2, 0 | [250, 27] | PASS |
| cinder | 2 / 92.2 ; 2 / 88.5 | **10.33** | 0.1975 -> 0.3372; near lens **1.913x**, far lens 1.534x, mean (12 deg still) **1.85x** | 18.0, 0.958 ; 15.8, 0.938 | 83.3, 0 | [224, 3] | FAIL H1 |
| glacier | 4 / 122.3 ; 3 / 99.6 | **9.4** | 0.2041 -> 0.3104; near lens **1.89x**, far lens 1.052x, mean (12 deg still) **1.776x** | 42.8, 0.979 ; 43.8, 1.0 | 78.6, 0 | [32, 49] | PASS |
| ash | 6 / 175.5 ; 6 / 173.1 | **9.33** | 0.189 -> 0.3266; near lens **1.924x**, far lens 1.522x, mean (12 deg still) **1.853x** | 25.0, 0.604 ; 23.0, 0.521 | 115.9, 0 | [279, 20] | FAIL H4 |
| saffron | 2 / 171.2 ; 2 / 186.9 | **8.73** | 0.2064 -> 0.3202; near lens **1.88x**, far lens 1.18x, mean (12 deg still) **1.738x** | 32.8, 0.75 ; 28.2, 0.562 | 148.1, 0 | [233, 45] | FAIL H1, H4 |
| sage | 5 / 136.2 ; 3 / 117.8 | **8.58** | 0.2072 -> 0.3314; near lens **1.877x**, far lens 1.344x, mean (12 deg still) **1.725x** | 42.2, 0.958 ; 43.5, 1.0 | 99.5, 0 | [250, 33] | PASS |

3 of 8 suits pass every gate H1 - H6 (`evidence/head_check.json`, overlays in `evidence/measures/head_overlays/`).

## Keep: the round-12 lines (raised piping, nothing under the sash, no fold)

| suit | relief: 64 px cells with a lit / shadow pair >= 20 luma (r12 -> r13) | median cell delta (r12 -> r13) | sash: longest dark run px, target <= 10 (r12 -> r13) | sash verdict |
|---|---|---|---|---|
| tessera | 0.592 -> **0.602** (254 of 422 cells) | 23.4 -> **24.2** | 11 -> **8** | PASS |
| verdant | 0.339 -> **0.353** (85 of 241 cells) | 13.6 -> **13.5** | 8 -> **8** | PASS |
| plum | 0.605 -> **0.585** (190 of 325 cells) | 25.4 -> **25.4** | None -> **6** | PASS |
| cinder | 0.598 -> **0.633** (162 of 256 cells) | 25.6 -> **26.1** | 10 -> **6** | PASS |
| glacier | 0.602 -> **0.657** (182 of 277 cells) | 25.4 -> **28.8** | None -> **None** | n/a |
| ash | 0.575 -> **0.575** (206 of 358 cells) | 25.0 -> **25.0** | 3 -> **4** | PASS |
| saffron | 0.52 -> **0.552** (122 of 221 cells) | 21.8 -> **22.7** | 6 -> **4** | PASS |
| sage | 0.6 -> **0.613** (165 of 269 cells) | 25.7 -> **24.7** | None -> **None** | n/a |

| Verdant chevron edge at the critic's columns x 1320-1400 | target | round 12 | round 13 | verdict |
|---|---|---|---|---|
| largest column-to-column jump beyond its slope | <= 2 px | 1.24 px | **14.4 px** | FAIL |

## Keep-passing lines

| line | target | measured | verdict |
|---|---|---|---|
| CH1 front stills (hero height / frame height, all 8 suits) | 0.48 - 0.62 | 0.542 - 0.544 | PASS |
| IP guard palette P1 - P7 (Verdant / Saffron re-blocked, Plum recoloured) | 0 failures | min palette distance 45.0 over 28 pairs, fails: none | PASS |
| UV seam runs at 4K (texture level) | <= 40 px | worst 4.3 px, runs > 40 px: 0 | PASS |
| OCR of every 4K still | 0 hits | 0 hits over 48 images | PASS |
| Tessera stays the default; generator regression (r8 legacy texel for texel + r13 default) | PASS | REGRESSION PASS | PASS |
| swap on the pixels (playable pawn, real T presses) | <= 500 ms | 7 of 7 presses found, worst 33.3 ms | PASS |

## Hero animation (stage hero, Char_Hero, 1080p60 fixed step) and the playable pawn

| line | target | measured | verdict |
|---|---|---|---|
| CH6 run step rate, side clip (head-blob bob, the round-08 instrument and window) | 3.2 - 3.8 steps/s | **3.542 Hz** (round 08 clip: 3.542 Hz) | PASS |
| CH6 run step rate, chase clip (whole-mask top bob; the head cannot be isolated from behind) | 3.2 - 3.8 | **3.542 Hz** (round 08: 3.542 Hz) | PASS |
| CH7 sprint torso lean, side clip (head to mid-torso band) | >= 15 deg | median **33.0 deg** (round 08 clip: 25.5 deg) | PASS |
| CH2 chase framing | 0.39 - 0.53 | hero height median **0.391** (round 08 clip: 0.372) | PASS |
| CH10 stage-hero blends | >= 0.15 s | the stage clips use the round-08 animation set unchanged (same ABP_Hero_Lineup / ABP_Hero_Leap); `video_checks.py takeoff` reads 1 - 2 frames on BOTH the round-08 and the round-13 leap clips (its ground line is set from the bobbing run, not a usable instrument) | not re-measured |
| playable pawn (P3 `WebTravAnimInstance`, NOT P2) run cadence | (P3) 3.2 - 3.8 | 4.0 steps/s (FFT 4.133 Hz, bob period 15.0 frames) | logged for the traversal brief |
| playable pawn idle -> run start | (P3) blend >= 0.15 s | largest one-frame change of the silhouette: height 0.089, width 0.769 at t = 0.183 s | logged for the traversal brief |
| playable pawn start, from its own telemetry | (P3) | clip switches A_Hero_idle -> A_Hero_walk @0.817 s -> A_Hero_jog @0.867 s -> A_Hero_run @0.983 s, all at blend weight 1.0; the 10-number pose signature then needs 28 frames (0.467 s) for 90 % of its change (largest single frame 5.8 %) | logged for the traversal brief |

## Enemy pack (restored to the round-10 content; round-13 lineup)

| line | measured |
|---|---|
| lineup 4K still, wall / floor mean RGB (round 04 -> round 12 -> round 13) | {'wall': [208.3, 208.7, 212.9], 'floor': [165.2, 182.8, 201.4], 'brick': [165.7, 132.3, 132.0]} -> {'wall': [207.5, 208.1, 212.4], 'floor': [164.7, 183.0, 202.3], 'brick': [163.3, 126.4, 126.3]} -> **{'wall': [140.1, 140.3, 148.6], 'floor': [86.8, 103.5, 128.4], 'brick': [87.3, 65.5, 65.5]}** |
| the skins-stage EV (+10) leaking into Char_Lineup | NO: the r04 and r12 lineups have the same exposure (wall 208 / 207 of 255); the washed-out look is the pale sunlit wall, fixed this round with a -0.6 EV bias and a weaker fill |
| fight script / choreography / weapon fit vs the round-10 commit | IDENTICAL (git diff --stat empty) |

Resolution: stills output 3840x2160, internal 3840x2160 (`r.ScreenPercentage 100`). Movies 1920x1080, fixed 1/60 s step.
