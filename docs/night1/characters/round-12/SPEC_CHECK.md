# Round 12 SPEC CHECK (piece G, hero skins)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. Numbers are read from `evidence/` by `tools/ue_char/suits/spec_check_r12.py`;
> the measures of the 4K chest stills run on the lossless PNG originals of the real game (UE 5.8.3 `-game`, offscreen, internal 3840x2160).

## Round target (critic round 11): raised piping, nothing under the sash shows through, no fold / jog

| suit | relief: 64 px cells with a lit / shadow pair >= 20 luma (r11 -> r12) | median cell delta (r11 -> r12) | sash: longest dark run px, target <= 10 (r11 -> r12) | sash verdict |
|---|---|---|---|---|
| tessera | 0.319 -> **0.59** (245 of 415 cells) | 6.2 -> **23.7** | 20 -> **11** | FAIL |
| verdant | 0.413 -> **0.348** (86 of 247 cells) | 15.6 -> **13.5** | 9 -> **8** | PASS |
| plum | 0.528 -> **0.596** (195 of 327 cells) | 22.0 -> **25.5** | 4 -> **9** | PASS |
| cinder | 0.506 -> **0.592** (155 of 262 cells) | 20.1 -> **24.7** | 108 -> **10** | PASS |
| glacier | 0.354 -> **0.577** (168 of 291 cells) | 11.2 -> **24.0** | None -> **None** | n/a |
| ash | 0.322 -> **0.578** (203 of 351 cells) | 11.7 -> **24.6** | 70 -> **3** | PASS |
| saffron | 0.396 -> **0.519** (120 of 231 cells) | 16.1 -> **21.7** | 98 -> **6** | PASS |
| sage | 0.317 -> **0.616** (178 of 289 cells) | 11.4 -> **25.7** | None -> **None** | n/a |

Critic probe Tessera (1412, 1240): round 11 luma 85.0 vs local panel median 109.3; round 12 luma 110.4 vs 107.2 (inside panel: True).

| Verdant chevron edge, lower edge, x 1290-1640 y 1500-1850 of the 4K chest (the critic.s jog at 1333-1357, 1610-1680) | target | round 11 | round 12 | verdict |
|---|---|---|---|---|
| largest column-to-column jump of the edge beyond its slope at the critic's columns x 1320-1400 | <= 2 px | 68.56 px | **1.23 px** | PASS |
| the same over the whole tracked edge (x 1290-1640) | <= 2 px | 68.56 px at [1359, 1610] | **4.11 px** at [1528, 1821] | FAIL |
| max deviation of the edge from a 61 px quadratic fit | (info) | 34.46 px | 3.64 px | |

Torso-side fold (CPU skinning of the hero mesh, folded = posed face normal against its vertex normals, dot < 0.3, in the 3396-face region): idle@0.00 4 -> **2**, idle@1.00 2 -> **2**, run@0.00 62 -> **18**, run@0.10 70 -> **43**, run@0.20 65 -> **24**, run@0.30 62 -> **19**, sprint@0.00 85 -> **37**, sprint@0.15 60 -> **50**, fightIdle@0.00 34 -> **7** (`evidence/fold_check.json`).

Normal map vs the mesh tangent basis per UV island (`tools/ue_char/suits/tangent_check.py`): ash PASS (all-texel median cos 0.99, large-island min 0.983, no flipped island: True); tessera PASS (all-texel median cos 0.994, large-island min 0.99, no flipped island: True); verdant PASS (all-texel median cos 0.993, large-island min 0.987, no flipped island: True).

## Keep-passing lines

| line | target | measured | verdict |
|---|---|---|---|
| CH1 front stills (hero height / frame height, all 8 suits) | 0.48 - 0.62 | 0.541 - 0.545 | PASS |
| IP guard palette P1 - P7 (Verdant / Saffron re-blocked) | 0 failures | min palette distance 52.3 over 28 pairs, fails: none | PASS |
| UV seam runs at 4K (texture level) | <= 40 px | worst 4.6 px, runs > 40 px: 0 | PASS |
| OCR of every 4K still | 0 hits | 0 hits over 32 images | PASS |
| Tessera stays the default; generator regression (r8 legacy texel for texel + r12 default) | PASS | REGRESSION PASS | PASS |
| swap on the pixels (playable pawn, real T presses) | <= 500 ms | 7 of 7 presses found, worst 33.3 ms | PASS |

## Hero animation (stage hero, Char_Hero, 1080p60 fixed step) and the playable pawn

| line | target | measured | verdict |
|---|---|---|---|
| CH6 run step rate, side clip (head-blob bob, the round-08 instrument and window) | 3.2 - 3.8 steps/s | **3.542 Hz** (round 08 clip: 3.542 Hz) | PASS |
| CH6 run step rate, chase clip (whole-mask top bob; the head cannot be isolated from behind) | 3.2 - 3.8 | **3.542 Hz** (round 08: 3.542 Hz) | PASS |
| CH7 sprint torso lean, side clip (head to mid-torso band) | >= 15 deg | median **20.6 deg** (round 08 clip: 25.5 deg) | PASS |
| CH2 chase framing | 0.39 - 0.53 | hero height median **0.389** (round 08 clip: 0.372) | FAIL (edge) |
| CH10 stage-hero blends | >= 0.15 s | the stage clips use the round-08 animation set unchanged (same ABP_Hero_Lineup / ABP_Hero_Leap); `video_checks.py takeoff` reads 1 - 2 frames on BOTH the round-08 and the round-12 leap clips (its ground line is set from the bobbing run, not a usable instrument) | not re-measured |
| playable pawn (P3 `WebTravAnimInstance`, NOT P2) run cadence | (P3) 3.2 - 3.8 | 4.0 steps/s (FFT 4.133 Hz, bob period 15.0 frames) | logged for the traversal brief |
| playable pawn idle -> run start | (P3) blend >= 0.15 s | largest one-frame change of the silhouette: height 0.088, width 0.769 at t = 0.183 s | logged for the traversal brief |
| playable pawn start, from its own telemetry | (P3) | clip switches A_Hero_idle -> A_Hero_walk @0.817 s -> A_Hero_jog @0.867 s -> A_Hero_run @0.983 s, all at blend weight 1.0; the 10-number pose signature then needs 28 frames (0.467 s) for 90 % of its change (largest single frame 5.8 %) | logged for the traversal brief |

Resolution: stills output 3840x2160, internal 3840x2160 (`r.ScreenPercentage 100`). Movies 1920x1080, fixed 1/60 s step.
