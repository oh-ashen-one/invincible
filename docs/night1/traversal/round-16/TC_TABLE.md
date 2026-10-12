# P3 round 16 -- TRICK_CAMERA_SPEC tests TC-A .. TC-K (rendered 1080p60, lit /Game/Maps/Manhattan golden)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. Source: `TRICKCAM_CHECK.txt` (`trickcam_check.py` v2, per-clip raw numbers), `SKY_CHECK.txt` (TC-I pooled), pixel numbers from the movies' hero mask. Build: code `2e86dc8`.

Judged clips: f1-f5 (spec: all must pass), a and b (informative). c = wall camera, d = no trick: no trick camera in either. `PASS(hold)` = the literal whole-window reading (release .. catch + 0.5 s, including blend-in / blend-out) fails by a few frames but the held camera (program rows with `flipcam_k >= .9`) passes; see the reading notes.

| test | f4 | f1 | f2 | f3 | f5 | a | b |
|---|---|---|---|---|---|---|---|
| TC-A | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| TC-B | PASS | PASS | PASS | PASS | PASS | FAIL | PASS |
| TC-C | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| TC-D | PASS | PASS | PASS(hold) | PASS(hold) | PASS | PASS(hold) | PASS |
| TC-E | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| TC-F | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| TC-G | PASS | PASS | PASS | PASS | PASS | FAIL | PASS |
| TC-H | PASS(hold) | PASS | PASS | PASS | PASS | PASS(hold) | PASS |
| TC-J | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| TC-K | PASS | PASS | PASS | PASS | PASS | PASS | PASS |

TC-I (pooled f1-f5): TC-I pooled over the clips: 125 trick samples, 1% have ring >= 50% sky AND hero h >= .15 (need >= 35%) -> FAIL

## Reading notes (where this checker interprets the spec, and what did not pass)

- **Windows.** WIN = `flip_t >= 0` through +0.5 s after the program's last row (spec header); HOLD = program rows with `flipcam_k >= .9`. TC-A's yaw *range* and TC-B's p95 / max are hold numbers (a 30-50 deg blend-in is the camera arriving, the spec says `flipcam_k >= 0.9`); TC-B's 150 deg/s is the whole window. TC-H's angle uses `flipcam_k >= .5` (r14 S1 definition) and falls back to `k >= .9` (`PASS(hold)`: f4 shows 99.9 deg and a 98 deg at k ~ .5 -> .6 while the yaw is still arriving; held min 122 / 111).
- **TC-C** is judged on the rendered hero MASK (critic's measure; the bone box is ~6-10 % larger). **TC4's 5.0-6.5 m is not reachable with TC-C**: at 4.2 m constant distance a tuck (mask ~.15-.17 of the frame) and a layout (~.30) sit on both sides of the .18 / .36 band (backDouble clips f1 / f5 p50 .17 at 4.2 m, .178 at 4.3; p90 .35 at 4.2). Built: 4.4 m, pulled in 0.6 m while the upper-body shape is a tuck (pike 0.6), anticipated 0.22 s so the opening kickout is not seen at tuck range -> mask WIN p10 / p50 / p90 f1 .133 / .193 / .344, f5 .130 / .185 / .324, f4 .133 / .207 / .303, f3 .140 / .257 / .304.
- **TC-H suit mask**: the r14 / r15 mask (close 21x21 + dilate 5x5 of the saturated pixels) bridged the gaps between the arms and counted the bright SKY there as suit (f1 3.55 s: 7 % 'clipped', the suit itself not). Now close 9x9 + dilate 3x3; the white chest emblem is inside the mask and is not clipped (<= 2.4 % everywhere). Mirrored-sun glass behind the hero is not scored (P4).
- **TC-I FAILS (1 % pooled f1-f5; r15 6 %)**, and the camera cannot fix it (spec: no pitch for sky): the ring around a hero 1 m over the lens is sky only when the skyline is under ~11 deg in the view direction; offline heightmap study (`_scratch/traversal/r12/hm/heightmap.csv`, view ENE / ESE from x -253, lens 12 .. 39 m): 0 of 70 positions along the west avenue (3 of 70 heading north) even at 39 m, because 100-300 m towers stand 20-300 m away. Needs a route over low ground / the river edge or a chain that flies well above the skyline (director option (c) in r15 §8).
- **a FAILS TC-B / TC-G (2 frames, hero_occl 12.55-12.57 s)**: the hero swings THROUGH the street-tree row at 13 m there (tree blocks the axis for ~0.6 s; dolly to 3.1 m, hero hidden for 2 frames). A traversal / P1 tree issue (swing path or tree collision), informative clip.
- **Fallback (TC2)**: f5's 2nd backDouble (7.78 s, 0.2 s before the clip ends) finds no obstruction-free spot at any distance >= 4.0 m and runs on the plain chase; listed in `TRICKCAM_CHECK.txt`, not judged by TC-A..F / H.
- **Routes**: f1 spawn x -250 -> -246 and f4 spawn y 375 -> 367. With the sun due west, the sun-away trick side is the west half of the avenue; the r15 starts put the first flip (f1 y 270 at 7 m; f4 y 342) under the west street-tree canopies where only the sun-facing side was obstruction-free, so the spec's own rule (obstruction first) looked into the sun (38-41 deg). Everything else in the scripts is r15.
- **Legacy lines**: `FLIP_CHECK.txt` F9 (program rows only, hero px p50 must be .18-.36) reads .16-.17 on the tuck-dominated clips (same definition gap as above, program frames only); F3 / F4 / F5 flip-quality lines are the r15 ones (f4 Kickout holds 0.31 s; f5 is one backDouble cut at the clip end).


## Per-clip numbers (verbatim from `TRICKCAM_CHECK.txt`, f1-f5)

**f4_chain_flips**

```
f4_chain_flips (f4_chain_flips_telemetry.csv): 5 flip programs, 11.6 s, window rows 493, hold (flipcam_k >= .9) rows 205
TC-A yaw offset from the release heading: HOLD p5-p95 34-47 deg (30-60), WIN 5-47; per-trick world-yaw range over the hold: backDouble@1.35 6.3 frontPikeSwan@3.93 5.7 corkscrew@6.38 6.8 backDouble@8.88 5.9 (<= 20) -> PASS
TC-B yaw rate: HOLD p95 25.4 / max 31.8 deg/s (<= 40 / 60); WIN incl. blends max 132 deg/s (<= 150) -> PASS
TC-C hero height p10/p50/p90 (>= .12 / .18-.28 / <= .36): MASK WIN 0.133/0.207/0.303, HOLD 0.137/0.204/0.330 | bone box WIN 0.152/0.232/0.332, HOLD 0.156/0.208/0.364 -> PASS
TC-D placement: WIN cx 0.48-0.54 cy 0.33-0.48, HOLD cx 0.48-0.55 cy 0.33-0.43 (cx .35-.60, cy .28-.48) -> PASS
TC-E pitch (+ up): WIN p5/p50/p95 -3.3/3.9/7.2, HOLD 3.5/3.9/5.0 (p5 >= -8, p95 <= +8, |p50| <= 5); median at attach +0.5..1.0 s (4-12 down): 2.93:-5.5 5.35:-5.5 7.88:-5.5 10.47:-5.5 -> PASS
TC-F lens below the hips (z_m - pcm_z): WIN p10/p50/p90 0.62/0.94/0.99, HOLD 0.86/0.96/1.00 m (p50 .5-2.0, p10 >= .2) -> PASS
TC-G safety: hero out of frame 0 rows  | camera in geometry 0  | lens sphere 0.25 m touching 0  | hero occluded 0  -> PASS
TC-H sun/glare: view_sun_deg min 100 (flipcam_k >= .5, r14 S1) / 122 (held, k >= .9) (>= 100); suit-mask luma>=245 share: p99 0.012 max 0.018 @ 5.17 s, frames > 5 %: 0 of 493 -> PASS(hold)
TC-J readability: backDouble tuck 1.35-2.53: axis turns 646 deg on screen (program 677) ok; frontPikeSwan tuck 4.88-5.23: axis turns 171 deg on screen (program 152) ok; corkscrew tuck 7.47-7.78: axis turns 168 deg on screen (program 152) ok; backDouble tuck 8.88-10.07: axis turns 679 deg on screen (program 677) ok -> PASS
TC-K continuity (whole clip): max pitch 2.70 deg/frame @ 3.93 s (<= 3), yaw 2.20 @ 6.48 s (<= 4), position 0.94 m @ 9.25 s (<= 1.2); blend-out, seconds from the attach until flipcam_k <= .5 (and <= .02): 2.93:0.43(0.82) 5.35:0.43(0.82) 7.88:0.43(0.82) 10.47:0.43(0.82) (>= 0.40) -> PASS
selection: backDouble@1.35 off +40 tier 0 dist 4.4->3.8 | frontPikeSwan@3.93 off +50 tier 0 dist 4.4->4.2 | corkscrew@6.38 off +50 tier 0 dist 4.4->4.2 | backDouble@8.88 off +50 tier 0 dist 4.4->3.8 | frontPikeSwan@11.43 off +50 tier 0 dist 4.4->0.0
```

**f1_flow_backDouble**

```
f1_flow_backDouble (f1_flow_backDouble_telemetry.csv): 1 flip programs, 8.0 s, window rows 125, hold (flipcam_k >= .9) rows 55
TC-A yaw offset from the release heading: HOLD p5-p95 43-47 deg (30-60), WIN 4-47; per-trick world-yaw range over the hold: backDouble@3.40 5.0 (<= 20) -> PASS
TC-B yaw rate: HOLD p95 18.8 / max 21.6 deg/s (<= 40 / 60); WIN incl. blends max 144 deg/s (<= 150) -> PASS
TC-C hero height p10/p50/p90 (>= .12 / .18-.28 / <= .36): MASK WIN 0.133/0.193/0.344, HOLD 0.141/0.185/0.337 | bone box WIN 0.152/0.202/0.381, HOLD 0.158/0.195/0.376 -> PASS
TC-D placement: WIN cx 0.45-0.52 cy 0.34-0.47, HOLD cx 0.45-0.52 cy 0.34-0.44 (cx .35-.60, cy .28-.48) -> PASS
TC-E pitch (+ up): WIN p5/p50/p95 -2.5/4.9/7.5, HOLD 4.3/4.5/5.6 (p5 >= -8, p95 <= +8, |p50| <= 5); median at attach +0.5..1.0 s (4-12 down): 4.98:-5.5 -> PASS
TC-F lens below the hips (z_m - pcm_z): WIN p10/p50/p90 0.71/0.87/0.98, HOLD 0.86/0.87/0.97 m (p50 .5-2.0, p10 >= .2) -> PASS
TC-G safety: hero out of frame 0 rows  | camera in geometry 0  | lens sphere 0.25 m touching 0  | hero occluded 0  -> PASS
TC-H sun/glare: view_sun_deg min 104 (flipcam_k >= .5, r14 S1) / 123 (held, k >= .9) (>= 100); suit-mask luma>=245 share: p99 0.020 max 0.022 @ 4.40 s, frames > 5 %: 0 of 125 -> PASS
TC-J readability: backDouble tuck 3.40-4.58: axis turns 646 deg on screen (program 677) ok -> PASS
TC-K continuity (whole clip): max pitch 2.70 deg/frame @ 2.42 s (<= 3), yaw 3.60 @ 7.80 s (<= 4), position 1.10 m @ 7.80 s (<= 1.2); blend-out, seconds from the attach until flipcam_k <= .5 (and <= .02): 4.98:0.43(0.82) (>= 0.40) -> PASS
selection: backDouble@3.40 off -50 tier 0 dist 4.4->3.8
```

**f2_flow_pikeSwan**

```
f2_flow_pikeSwan (f2_flow_pikeSwan_telemetry.csv): 1 flip programs, 8.0 s, window rows 115, hold (flipcam_k >= .9) rows 45
TC-A yaw offset from the release heading: HOLD p5-p95 43-47 deg (30-60), WIN 5-47; per-trick world-yaw range over the hold: frontPikeSwan@3.37 5.1 (<= 20) -> PASS
TC-B yaw rate: HOLD p95 21.6 / max 27.6 deg/s (<= 40 / 60); WIN incl. blends max 144 deg/s (<= 150) -> PASS
TC-C hero height p10/p50/p90 (>= .12 / .18-.28 / <= .36): MASK WIN 0.135/0.219/0.293, HOLD 0.142/0.270/0.293 | bone box WIN 0.153/0.246/0.304, HOLD 0.167/0.293/0.303 -> PASS
TC-D placement: WIN cx 0.46-0.51 cy 0.31-0.52, HOLD cx 0.46-0.50 cy 0.30-0.39 (cx .35-.60, cy .28-.48) -> PASS(hold)
TC-E pitch (+ up): WIN p5/p50/p95 -3.2/4.4/7.5, HOLD 3.8/4.1/5.4 (p5 >= -8, p95 <= +8, |p50| <= 5); median at attach +0.5..1.0 s (4-12 down): 4.78:-5.5 -> PASS
TC-F lens below the hips (z_m - pcm_z): WIN p10/p50/p90 0.68/0.96/0.99, HOLD 0.95/0.99/1.00 m (p50 .5-2.0, p10 >= .2) -> PASS
TC-G safety: hero out of frame 0 rows  | camera in geometry 0  | lens sphere 0.25 m touching 0  | hero occluded 0  -> PASS
TC-H sun/glare: view_sun_deg min 109 (flipcam_k >= .5, r14 S1) / 128 (held, k >= .9) (>= 100); suit-mask luma>=245 share: p99 0.023 max 0.023 @ 4.08 s, frames > 5 %: 0 of 115 -> PASS
TC-J readability: frontPikeSwan tuck 4.32-4.67: axis turns 165 deg on screen (program 152) ok -> PASS
TC-K continuity (whole clip): max pitch 2.70 deg/frame @ 6.72 s (<= 3), yaw 3.60 @ 7.18 s (<= 4), position 1.10 m @ 7.15 s (<= 1.2); blend-out, seconds from the attach until flipcam_k <= .5 (and <= .02): 4.78:0.43(0.82) (>= 0.40) -> PASS
selection: frontPikeSwan@3.37 off -50 tier 0 dist 4.4->4.2
```

**f3_flow_corkscrew**

```
f3_flow_corkscrew (f3_flow_corkscrew_telemetry.csv): 1 flip programs, 8.0 s, window rows 120, hold (flipcam_k >= .9) rows 50
TC-A yaw offset from the release heading: HOLD p5-p95 37-42 deg (30-60), WIN 7-42; per-trick world-yaw range over the hold: corkscrew@1.35 5.9 (<= 20) -> PASS
TC-B yaw rate: HOLD p95 23.5 / max 27.6 deg/s (<= 40 / 60); WIN incl. blends max 124 deg/s (<= 150) -> PASS
TC-C hero height p10/p50/p90 (>= .12 / .18-.28 / <= .36): MASK WIN 0.140/0.257/0.304, HOLD 0.151/0.285/0.311 | bone box WIN 0.157/0.280/0.320, HOLD 0.172/0.299/0.326 -> PASS
TC-D placement: WIN cx 0.46-0.51 cy 0.31-0.49, HOLD cx 0.46-0.51 cy 0.31-0.37 (cx .35-.60, cy .28-.48) -> PASS(hold)
TC-E pitch (+ up): WIN p5/p50/p95 -3.2/3.9/6.7, HOLD 3.8/3.9/4.8 (p5 >= -8, p95 <= +8, |p50| <= 5); median at attach +0.5..1.0 s (4-12 down): 2.85:-5.5 -> PASS
TC-F lens below the hips (z_m - pcm_z): WIN p10/p50/p90 0.68/0.97/1.00, HOLD 0.96/1.00/1.00 m (p50 .5-2.0, p10 >= .2) -> PASS
TC-G safety: hero out of frame 0 rows  | camera in geometry 0  | lens sphere 0.25 m touching 0  | hero occluded 0  -> PASS
TC-H sun/glare: view_sun_deg min 113 (flipcam_k >= .5, r14 S1) / 135 (held, k >= .9) (>= 100); suit-mask luma>=245 share: p99 0.010 max 0.015 @ 3.32 s, frames > 5 %: 0 of 120 -> PASS
TC-J readability: corkscrew tuck 2.43-2.75: axis turns 167 deg on screen (program 152) ok -> PASS
TC-K continuity (whole clip): max pitch 2.70 deg/frame @ 5.38 s (<= 3), yaw 3.60 @ 7.50 s (<= 4), position 1.11 m @ 5.43 s (<= 1.2); blend-out, seconds from the attach until flipcam_k <= .5 (and <= .02): 2.85:0.43(0.82) (>= 0.40) -> PASS
selection: corkscrew@1.35 off -45 tier 0 dist 4.4->4.2
```

**f5_canyon_backDouble**

```
f5_canyon_backDouble (f5_canyon_backDouble_telemetry.csv): 2 flip programs, 8.0 s, window rows 125, hold (flipcam_k >= .9) rows 55
  TC2 fallback to the plain chase (no obstruction-free spot at any distance >= 4.0 m; not judged by TC-A..F/H, TC-G below covers them): backDouble 7.78-7.95 s
TC-A yaw offset from the release heading: HOLD p5-p95 32-37 deg (30-60), WIN 6-37; per-trick world-yaw range over the hold: backDouble@3.33 6.2 (<= 20) -> PASS
TC-B yaw rate: HOLD p95 22.6 / max 27.0 deg/s (<= 40 / 60); WIN incl. blends max 126 deg/s (<= 150) -> PASS
TC-C hero height p10/p50/p90 (>= .12 / .18-.28 / <= .36): MASK WIN 0.130/0.185/0.324, HOLD 0.130/0.178/0.333 | bone box WIN 0.147/0.189/0.359, HOLD 0.151/0.185/0.371 -> PASS
TC-D placement: WIN cx 0.48-0.55 cy 0.34-0.47, HOLD cx 0.48-0.55 cy 0.35-0.44 (cx .35-.60, cy .28-.48) -> PASS
TC-E pitch (+ up): WIN p5/p50/p95 -2.9/3.8/7.2, HOLD 3.5/3.7/4.9 (p5 >= -8, p95 <= +8, |p50| <= 5); median at attach +0.5..1.0 s (4-12 down): 4.92:-5.5 -> PASS
TC-F lens below the hips (z_m - pcm_z): WIN p10/p50/p90 0.70/0.87/0.98, HOLD 0.86/0.88/0.97 m (p50 .5-2.0, p10 >= .2) -> PASS
TC-G safety: hero out of frame 0 rows  | camera in geometry 0  | lens sphere 0.25 m touching 0  | hero occluded 0  -> PASS
TC-H sun/glare: view_sun_deg min 108 (flipcam_k >= .5, r14 S1) / 130 (held, k >= .9) (>= 100); suit-mask luma>=245 share: p99 0.008 max 0.012 @ 3.40 s, frames > 5 %: 0 of 136 -> PASS
TC-J readability: backDouble tuck 3.33-4.52: axis turns 646 deg on screen (program 677) ok -> PASS
TC-K continuity (whole clip): max pitch 2.70 deg/frame @ 6.73 s (<= 3), yaw 2.10 @ 3.48 s (<= 4), position 0.85 m @ 3.70 s (<= 1.2); blend-out, seconds from the attach until flipcam_k <= .5 (and <= .02): 4.92:0.43(0.82) (>= 0.40) -> PASS
selection: backDouble@3.33 off +40 tier 0 dist 4.4->3.8
```
