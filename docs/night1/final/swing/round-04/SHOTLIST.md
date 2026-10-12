# Final swing loop: shot list (builder SW)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Round `round-04`; build commit 57c12fc9 (round 00 = behaviour of tag `final-before` 16d24911 plus telemetry-only columns); scripts `docs/night1/traversal/scripts/final/`.

## Settings (every clip)
- real `-game` (`tools/final/swing/run_clip.py` -> `tools/showcase/play.py --capture`), `-WHProfile=playable -WHResScale=100`, `-WHPerfPreset=unreal/WebHomage/Config/PerfPlayableFast.cvars`, TSR (r.AntiAliasingMethod 4)
- output 1920x1080, internal 1920x1080 (r.ScreenPercentage 100), fixed 1/60 s (`-benchmark -fps=60`), `-dumpmovie` through `-WHMovieAsync`, `-WHTravPreroll=1.5` (the 1.5 s of pre-roll frames are cut: frames - telemetry rows)
- default suit (DA_HeroSuits entry 0, Tessera); maps `/Game/Showcase/Maps/Manhattan_Island` (golden: s1-s4) and `Manhattan_Island_Night` (s5); H.264 mp4 <= 15 MB (crf raised until it fits)
- evidence = offline visual evidence of scripted input routes, never perf

- scene difference against round 00: from round 01 on the island maps also compose /Game/PropsM3/Maps/PropsM3_Island (supplied props, mostly on lawns and plazas, tiny from swing height) -- not a swing change

## Clips
### s1_swing_chain (20.0 s, 1199 frames, 13.0 MB, crf 31, engine wall 129 s)
- `s1_swing_chain` (20.0 s): spawn [250, 560, 24] yaw -90.0 vel [0, -22, 0]; a skilled player holding RMB: release on the rising front, re-press 0.3 s later (r26 a_swing_chain rule, gap 0.3 / repressVz 99), bottoms >= 14 m: 20 s
  keys: `[{"t": 0.0, "move": [0, 1], "heading": -90, "swing": false}, {"t": 0.4, "autoChain": true, "releasePhase": 0.55, "gap": 0.3, "repressVz": 99.0, "trickEvery": 0, "skyEvery": 0, "skyTricks": 1, "skyRepressH": 30, "skyPhase": 0.8, "skyMax": 2.8}]` tune `ArcLowMin=15,ArcDropShallow=8,ArcDropDeep=12,WallClearance=14,AltChain=0,AnchorAltDeg=8,AnchorElevMin=0.1,AnchorAheadMin=-2`
  render throughput: s1_swing_chain 1291 frames in 129 s = 10.0 fps
### s5_night_swing (20.0 s, 1199 frames, 12.9 MB, crf 28, engine wall 135 s)
- `s5_night_swing` (20.0 s): spawn [250, 560, 24] yaw -90.0 vel [0, -22, 0]; s1 inputs, night map
  keys: `[{"t": 0.0, "move": [0, 1], "heading": -90, "swing": false}, {"t": 0.4, "autoChain": true, "releasePhase": 0.55, "gap": 0.3, "repressVz": 99.0, "trickEvery": 0, "skyEvery": 0, "skyTricks": 1, "skyRepressH": 30, "skyPhase": 0.8, "skyMax": 2.8}]` tune `ArcLowMin=15,ArcDropShallow=8,ArcDropDeep=12,WallClearance=14,AltChain=0,AnchorAltDeg=8,AnchorElevMin=0.1,AnchorAheadMin=-2`
  render throughput: s5_night_swing 1291 frames in 135 s = 9.6 fps
### s4_release_float (20.0 s, 1199 frames, 11.7 MB, crf 31, engine wall 149 s)
- `s4_release_float` (20.0 s): spawn [250, 240, 40] yaw -90.0 vel [0, -22, 0]; autoChain releases with no trick, re-press 1.6 s after each release (long air): 20 s
  keys: `[{"t": 0.0, "move": [0, 1], "heading": -90, "swing": false}, {"t": 0.4, "autoChain": true, "releasePhase": 0.55, "gap": 1.6, "repressVz": -8.0, "trickEvery": 0, "skyEvery": 0, "skyTricks": 1, "skyRepressH": 30, "skyPhase": 0.8, "skyMax": 2.8}]`
  render throughput: s4_release_float 1291 frames in 149 s = 8.7 fps
### s3b_flip_cases (26.5 s, 1589 frames, 14.6 MB, crf 31, engine wall 361 s)
- `s3_c1_fwd` (3.8 s): spawn [250, 200, 110] yaw -90.0 vel [0, -22, 6]; F pressed 0.4 s in with the stick fwd [0, 1], swing 2.0 s later
  keys: `[{"t": 0.0, "move": [0, 0], "swing": false}, {"t": 0.3, "move": [0, 1]}, {"t": 0.4, "trick": true}, {"t": 0.5, "trick": false}, {"t": 2.4, "swing": true}, {"t": 3.5, "swing": false}]` tune `FlipKStart=2`
- `s3_c2_back` (3.8 s): spawn [250, 200, 110] yaw -90.0 vel [0, -22, 6]; F pressed 0.4 s in with the stick back [0, -1], swing 2.0 s later
  keys: `[{"t": 0.0, "move": [0, 0], "swing": false}, {"t": 0.3, "move": [0, -1]}, {"t": 0.4, "trick": true}, {"t": 0.5, "trick": false}, {"t": 2.4, "swing": true}, {"t": 3.5, "swing": false}]` tune `FlipKStart=1`
- `s3_c3_right` (3.8 s): spawn [250, 200, 110] yaw -90.0 vel [0, -22, 6]; F pressed 0.4 s in with the stick right [1, 0], swing 2.0 s later
  keys: `[{"t": 0.0, "move": [0, 0], "swing": false}, {"t": 0.3, "move": [1, 0]}, {"t": 0.4, "trick": true}, {"t": 0.5, "trick": false}, {"t": 2.4, "swing": true}, {"t": 3.5, "swing": false}]` tune `FlipKStart=4`
- `s3_c4_left` (3.8 s): spawn [250, 200, 110] yaw -90.0 vel [0, -22, 6]; F pressed 0.4 s in with the stick left [-1, 0], swing 2.0 s later
  keys: `[{"t": 0.0, "move": [0, 0], "swing": false}, {"t": 0.3, "move": [-1, 0]}, {"t": 0.4, "trick": true}, {"t": 0.5, "trick": false}, {"t": 2.4, "swing": true}, {"t": 3.5, "swing": false}]` tune `FlipKStart=3`
- `s3_c5_neutral` (3.8 s): spawn [250, 200, 110] yaw -90.0 vel [0, -22, 6]; F pressed 0.4 s in with the stick neutral [0, 0], swing 2.0 s later
  keys: `[{"t": 0.0, "move": [0, 0], "swing": false}, {"t": 0.3, "move": [0, 0]}, {"t": 0.4, "trick": true}, {"t": 0.5, "trick": false}, {"t": 2.4, "swing": true}, {"t": 3.5, "swing": false}]` tune `FlipKStart=6`
- `s3_c6_fwd_right` (3.8 s): spawn [250, 200, 110] yaw -90.0 vel [0, -22, 6]; F pressed 0.4 s in with the stick fwd_right [0.7, 0.7], swing 2.0 s later
  keys: `[{"t": 0.0, "move": [0, 0], "swing": false}, {"t": 0.3, "move": [0.7, 0.7]}, {"t": 0.4, "trick": true}, {"t": 0.5, "trick": false}, {"t": 2.4, "swing": true}, {"t": 3.5, "swing": false}]` tune `FlipKStart=5`
- `s3_c7_back_left` (3.8 s): spawn [250, 200, 110] yaw -90.0 vel [0, -22, 6]; F pressed 0.4 s in with the stick back_left [-0.7, -0.7], swing 2.0 s later
  keys: `[{"t": 0.0, "move": [0, 0], "swing": false}, {"t": 0.3, "move": [-0.7, -0.7]}, {"t": 0.4, "trick": true}, {"t": 0.5, "trick": false}, {"t": 2.4, "swing": true}, {"t": 3.5, "swing": false}]` tune `FlipKStart=8`
  render throughput: s3_c1_fwd 319 frames in 55 s = 5.8 fps; s3_c2_back 319 frames in 52 s = 6.1 fps; s3_c3_right 319 frames in 51 s = 6.2 fps; s3_c4_left 319 frames in 51 s = 6.2 fps; s3_c5_neutral 319 frames in 51 s = 6.2 fps; s3_c6_fwd_right 319 frames in 50 s = 6.4 fps; s3_c7_back_left 319 frames in 51 s = 6.2 fps
### s3_flip_chain (24.0 s, 1439 frames, 11.5 MB, crf 31, engine wall 155 s)
- `s3_flip_flow` (24.0 s): spawn [250, 560, 40] yaw -90.0 vel [0, -22, 6]; one continuous chain: a flow flip on every release, stick changing between flips, 24 s
  keys: `[{"t": 0.0, "move": [0, 1], "swing": false}, {"t": 0.4, "autoChain": true, "releasePhase": 0.55, "gap": 0.3, "repressVz": 99.0, "trickEvery": 1, "skyEvery": 0, "skyTricks": 1, "skyRepressH": 30, "skyPhase": 0.8, "skyMax": 2.8}, {"t": 3.0, "move": [0.7, 0.7]}, {"t": 6.0, "move": [0, 1]}, {"t": 9.0, "move": [-0.7, 0.7]}, {"t": 12.0, "move": [0, -0.8]}, {"t": 15.0, "move": [0, 1]}, {"t": 18.0, "move": [0.7, 0.7]}, {"t": 21.0, "move": [-0.7, 0.7]}]` tune `ArcLowMin=15,ArcDropShallow=8,ArcDropDeep=12,WallClearance=14,AltChain=0,AnchorAltDeg=8,AnchorElevMin=0.1,AnchorAheadMin=-2`
  render throughput: s3_flip_flow 1531 frames in 155 s = 9.9 fps
### s2_press_variety (33.9 s, 2031 frames, 12.7 MB, crf 34, engine wall 462 s)
- `s2_c1_roof_jump` (5.0 s): spawn [287, 138, 69.2] yaw 180 vel [0, 0, 0]; sprint west across the roof of E x266..291 z125..151 (h 68), jump at the edge, swing 0.2 s after the jump
  keys: `[{"t": 0.0, "move": [0, 1], "heading": 180, "sprint": true, "swing": false}, {"t": 1.9, "jump": true}, {"t": 2.05, "jump": false}, {"t": 2.25, "swing": true}, {"t": 4.2, "swing": false}]`
- `s2_c2_midfall` (3.6 s): spawn [250, 150, 62] yaw -90.0 vel [0, -20, -14]; free fall over the avenue (vz -14, 20 m/s north), swing pressed 0.5 s in
  keys: `[{"t": 0.0, "move": [0, 1], "heading": -90, "swing": false}, {"t": 0.5, "swing": true}, {"t": 2.6, "swing": false}]`
- `s2_c3_wallrun` (5.2 s): spawn [250, 105, 30] yaw 0 vel [12, 0, 5]; airborne into the east facade (x 266) of z 88..122 h 97, wall run, swing pressed 2.6 s in
  keys: `[{"t": 0.0, "move": [0, 1], "heading": 0, "sprint": true, "swing": false}, {"t": 0.6, "heading": false}, {"t": 2.6, "swing": true}, {"t": 4.3, "swing": false}]`
- `s2_c4_flip_cancel` (3.8 s): spawn [250, 200, 50] yaw -90.0 vel [0, -22, 4]; a backDouble flip requested at the start, swing pressed 0.9 s into the flip
  keys: `[{"t": 0.0, "move": [0, 1], "heading": -90, "swing": false, "flip": "backDouble"}, {"t": 0.05, "trick": true}, {"t": 0.15, "trick": false}, {"t": 0.95, "swing": true}, {"t": 2.8, "swing": false}]`
- `s2_c5_repress` (3.8 s): spawn [250, 190, 30] yaw -90.0 vel [0, -22, 0]; swing 0.2..1.3 s, released, pressed again 0.15 s after the release, again released 2.4 s
  keys: `[{"t": 0.0, "move": [0, 1], "heading": -90, "swing": false}, {"t": 0.2, "swing": true}, {"t": 1.3, "swing": false}, {"t": 1.45, "swing": true}, {"t": 2.9, "swing": false}]`
- `s2_c6_side_anchor` (3.2 s): spawn [262.5, 160, 22] yaw -90.0 vel [0, -20, 2]; low and fast beside the east facade (x 262.5), stick held left (west) while pressing: the nearest face is the facade, the open anchors are across the avenue
  keys: `[{"t": 0.0, "move": [-1, 0.2], "swing": false}, {"t": 0.3, "swing": true}, {"t": 2.2, "swing": false}]`
- `s2_c7_no_anchor` (3.0 s): spawn [250, 150, 330] yaw -90.0 vel [0, -6, 0]; high above the roofline (z 330 m, 6 m/s north): nothing to attach to, swing pressed 0.3 s and 1.4 s in
  keys: `[{"t": 0.0, "move": [0, 1], "heading": -90, "swing": false}, {"t": 0.3, "swing": true}, {"t": 0.7, "swing": false}, {"t": 1.4, "swing": true}, {"t": 1.8, "swing": false}]`
- `s2_c8_close_facade` (3.2 s): spawn [264.5, 150, 35] yaw -90.0 vel [0, -18, 0]; 1.5 m from the east facade (x 266), 18 m/s north, swing pressed 0.3 s in
  keys: `[{"t": 0.0, "move": [0, 1], "heading": -90, "swing": false}, {"t": 0.3, "swing": true}, {"t": 2.2, "swing": false}]`
- `s2_c9_trees` (3.2 s): spawn [258, 244, 14] yaw -90.0 vel [0, -20, 0]; low over the east sidewalk trees (x 262, z 229 / 218 / 211), swing pressed 0.2 s in
  keys: `[{"t": 0.0, "move": [0, 1], "heading": -90, "swing": false}, {"t": 0.2, "swing": true}, {"t": 2.2, "swing": false}]`
  render throughput: s2_c1_roof_jump 391 frames in 73 s = 5.4 fps; s2_c2_midfall 307 frames in 49 s = 6.3 fps; s2_c3_wallrun 403 frames in 54 s = 7.5 fps; s2_c4_flip_cancel 319 frames in 50 s = 6.4 fps; s2_c5_repress 319 frames in 51 s = 6.2 fps; s2_c6_side_anchor 283 frames in 46 s = 6.2 fps; s2_c7_no_anchor 271 frames in 46 s = 5.9 fps; s2_c8_close_facade 283 frames in 47 s = 6.0 fps; s2_c9_trees 283 frames in 46 s = 6.2 fps
