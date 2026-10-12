# P3 round 26 -- clip provenance

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

All movies: real `-game` (`Scripts/run_game.sh -movie`, offscreen, `/Game/Maps/Manhattan` golden), 1920x1080 output, internal resolution
1920x1080 (`r.ScreenPercentage 100`), fixed 1/60 s step, 0.8 s pre-roll trimmed, H.264 <= 15 MB, every run inside `gpu_slot.sh capture`
(background priority, shared GPU: no perf claim). Hero suit in every run: the log line `WH_TRAV hero suit` / `WH_SUIT start` below.
Split = two deterministic runs of the same replay (A: frames up to tm + 0.5 s; B: `-WHMovieFrom=tm`, frames from tm), merged at tm after a
pixel comparison of the 0.5 s overlap (`split/<clip>_OVERLAP.txt`). `-WHMovieAsync` = the same lossless PNG frames written off the game thread.

| clip | capture | frames / rows | suit (log) | body path vs r25 | camera vs r25 |
|---|---|---|---|---|---|
| a_swing_chain | split t=7.0 / split 7.0 s, A + B on build bb7107e6 (-WHMovieAsync) | 935 rows | WH_TRAV hero suit: DA_HeroSuits entry MI_Hero_Suit; WH_SUIT start suit 0 (tessera) from default, persist=0 live=0 | SAME | SAME |
| c_wallrun_perch | full run / full run on build bb7107e6 (-WHMovieAsync) | 629 rows | WH_TRAV hero suit: DA_HeroSuits entry MI_Hero_Suit; WH_SUIT start suit 0 (tessera) from default, persist=0 live=0 | SAME | differs (max 2.28 m) |
| f1_flow_backDouble | full run / full run on build bb7107e6 (-WHMovieAsync) | 539 rows | WH_TRAV hero suit: DA_HeroSuits entry MI_Hero_Suit; WH_SUIT start suit 0 (tessera) from default, persist=0 live=0 | SAME | SAME |
| f4_chain_flips | split t=6.0 / split 6.0 s, A + B on build bb7107e6 (-WHMovieAsync) | 797 rows | WH_TRAV hero suit: DA_HeroSuits entry MI_Hero_Suit; WH_SUIT start suit 0 (tessera) from default, persist=0 live=0 | SAME | SAME |
| m1_mouse_swing | full run / full run on build bb7107e6 (-WHMovieAsync) | 359 rows | WH_TRAV hero suit: DA_HeroSuits entry MI_Hero_Suit; WH_SUIT start suit 0 (tessera) from default, persist=0 live=0 | SAME | SAME |
| p1_pawn_run | split t=5.5 / split 5.5 s, A + B on build bb7107e6 (-WHMovieAsync) | 719 rows | WH_TRAV hero suit: DA_HeroSuits entry MI_Hero_Suit; WH_SUIT start suit 0 (tessera) from default, persist=0 live=0 | SAME | SAME |
| r1_roofrun_zip | full run / full run on build bb7107e6 (-WHMovieAsync) | 569 rows | WH_TRAV hero suit: DA_HeroSuits entry MI_Hero_Suit; WH_SUIT start suit 0 (tessera) from default, persist=0 live=0 | SAME | differs (max 2.28 m) |
| s1_high_swing | full run / full run on build bb7107e6 (-WHMovieAsync) | 359 rows | WH_TRAV hero suit: DA_HeroSuits entry MI_Hero_Suit; WH_SUIT start suit 0 (tessera) from default, persist=0 live=0 | SAME | differs (max 1.06 m) |
| w1_wallrun_tall_zip | split t=4.0 / split 4.0 s, A + B on build 3470d057 (sync PNG frames) | 449 rows | WH_TRAV hero suit: DA_HeroSuits entry MI_Hero_Suit; WH_SUIT start suit 0 (tessera) from default, persist=0 live=0 | SAME | differs (max 1.06 m) |
| w2_wallrun_side_zip | full run / full run on build bb7107e6 (-WHMovieAsync) | 419 rows | WH_TRAV hero suit: DA_HeroSuits entry MI_Hero_Suit; WH_SUIT start suit 0 (tessera) from default, persist=0 live=0 | SAME | differs (max 1.06 m) |
| x1_rmb_cancel_flip | full run / full run on build bb7107e6 (-WHMovieAsync) | 239 rows | WH_TRAV hero suit: DA_HeroSuits entry MI_Hero_Suit; WH_SUIT start suit 0 (tessera) from default, persist=0 live=0 | SAME | SAME |
| x2_rmb_cancel_wall | full run / full run on build bb7107e6 (-WHMovieAsync) | 299 rows | WH_TRAV hero suit: DA_HeroSuits entry MI_Hero_Suit; WH_SUIT start suit 0 (tessera) from default, persist=0 live=0 | SAME | differs (max 1.38 m) |
