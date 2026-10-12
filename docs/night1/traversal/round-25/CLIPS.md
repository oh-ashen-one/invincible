# P3 round 25 -- clip provenance

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

All movies: real `-game` (`Scripts/run_game.sh -movie`, offscreen, `/Game/Maps/Manhattan` golden), 1920x1080 output, internal resolution
1920x1080 (`r.ScreenPercentage 100`), fixed 1/60 s step, 0.8 s pre-roll trimmed, H.264 <= 15 MB. Every run went through
`gpu_slot.sh capture` (background priority, shared GPU: no perf claim). No 4K stills this round.

Builds of this round (all on branch `night1/traversal`):
- build 1 = `1034b587` (two-tone strand, perch recenter yaw hold, run anchor 9.3 m/s)
- build 2 = `ae40de7b` (single-tone strand after motion blur, manual depth test, 2.8-3.4 px clamp; M_TravWeb rebuilt by the commandlet)
- build 3 = `e0ae46c9` (`RopeKeepProxy`: unused web segments kept registered at a 1e-4 scale)
- build 4 = `54ddbbf5` (`RopeWavePx` 1.5: shot-strand wave bounded on screen) = the final code of the round

Builds 2-4 change only the web strand drawing (`UpdateWebs`, M_TravWeb); paths and cameras are identical across builds 1-4
(`round-24/tools/same.py` on -nullrhi probes / captures).

| clip | captured on | path / camera check |
|---|---|---|
| a_swing_chain | build 4 | script changed this round (`repressVz` -8); build 3 and build 4 captures SAME |
| c_wallrun_perch | build 2 | SAME as the build-1 capture; body path = r24; camera = r24 until the zip flight at 8.65 s (the gate fix); perch gate PASS (R25_GATES.txt). The zip strand's first frame / wave differ from build 4 |
| p1_pawn_run | build 1 | no web in the clip (web_on 0 on every row); build-2 -nullrhi probe SAME -> the build-4 frames would be identical |
| w1_wallrun_tall_zip | build 3 | body path = r24 on every row; camera = r24 until the perch at 5.80 s (r25 perch recenter yaw hold, max 3.2 m); wall_check.py numbers identical; the zip strand's wave differs from build 4 |
| m1_mouse_swing | build 4 | SAME as r24 |
| f1_flow_backDouble | build 4 | SAME as r24 |
| w2_wallrun_side_zip | build 4 | body path = r24 on every row; camera = r24 until the perch at 6.43 s (perch recenter, max 1.4 m) |
| x2_rmb_cancel_wall | build 4 | SAME as r24 |
| x1_rmb_cancel_flip | build 4 | SAME as r24 |
| s1_high_swing | build 4 | SAME as r24 |
| r1_roofrun_zip | build 4 | SAME as r24 (build-1 probe; capture check in R24_CHECK / OWNER_BUGS) |
| f4_chain_flips | not re-captured: `round-24/f4_chain_flips.mp4` | build-4 -nullrhi probe SAME as r24 (only the strand look differs) |
