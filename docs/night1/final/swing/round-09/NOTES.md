# Round 09 (builder SW)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Answers critic r08's three orchestrator-verified gaps (s3 trick-camera occlusion; flip shape quality; W8 release retract), plus the adjacent P1-air and night W5 halo items. Build commit `a650c9bb` (every clip below rendered on `a650c9bb` in one detached chain after two in-round probe builds were discarded). Same maps / profile / settings as round 08 (`-WHSuit=tessera`, playable + Fast, 1920x1080, fixed 1/60 s, 1.5 s pre-roll cut); scripts / keys / spawns unchanged.

## Code changes (all in owned paths)

- `WebTravCamera.cpp/.h` — trick-camera occlusion (gap 1): the round-05 visibility watchdog explicitly decayed `UnseenT` while the trick camera was in (`FlipK > 0.05 || bFlip || bFlipSoon || bFlipPre`); it now runs in trick mode (and on the wall). The trick camera answers the watchdog inside TC11's constraints: the held view dollies IN along its axis (up to 45 %, immediate while the watchdog fires), the 4-point visibility lift and the watchdog lift run in trick mode too (straight up along the held axis, never a yaw / side re-pick), and past 0.25 s fully unseen + the abort grace the trick view falls back to the plain chase, whose watchdog boost (distance / lift / slew) owns the recovery. While the watchdog fires the output slew caps and the look-up cap relax (FlipPitchUpMax + 14 deg at full boost); TC-B's 150 deg/s yaw cap still binds whenever the hero is seen. `ChaseFbAir` 0.315 -> 0.33 (P1 air: the tuckier r08 drift poses shrink the mask bbox under the 0.18 floor).
- `WebTravCharacter.cpp` + `WebTraversalComponent.cpp` — W8 (gap 3): the r08 retract (`B -> hand` with a smoothstep over 0.30 s) spent its first ~0.15 s off-screen and crossed the frame in ~5 frames (the critic's 950 -> 0 px in 0.07 s). The retract now runs LINEAR-in-length with an ease-out (`1-(1-x)^2`) over 0.36 s toward the hand: fast while the far end is off-screen, slow while the endpoint crosses the frame near the hero; slack droop from the first frames; fade 0.14 -> 0.38 s; the strand slot dies at 0.42 s (was 0.35). (An intermediate variant that parked the near end at the release point was probed and dropped: at 50 m/s the camera passes the release point in ~4 frames.)
- `WebTravAnimInstance.cpp` — flip shape quality (gap 2): the pencil and straddle clips end their 1 s timelines in tucked-up / knees-bent keys; the LEG overlay now samples those clips at a scaled hold (pencil x0.25, straddle x0.55) so the held shapes keep their straight-leg keys while the upper body plays the full timeline (the arms carry the hold's motion).
- `WebTravFlips.cpp` — frontPikeSwan: swan hold 0.32 -> 0.38 s and Swan inertia 7.5 -> 10.0 (r08 F4 measured 0.27 s; the axis-correction catch-up stacked on the swan's ~140 deg/s pushed the rendered rate over the 150 deg/s hold bar).
- `WebTraversalComponent.h` — night W5 halo: `RopePxMax` 3.4 -> 3.3 px (7 of 8 s5 W5 fails were width > 4 px on near-vertical strands over dark glass).
- `tools/final/swing/run_clip.py` — queue label r08 -> r09.

## Measured (round-09/CHECK.txt; flip_check = docs/night1/traversal/flip_check.py; vs round-08)

Gap 1 (s3 trick-camera occlusion): longest fully-invisible stretch (`hero_occl == 1` run) s3 0.60 -> 0.15 s, s3b 0.65 -> 0.17 s; the r08 t~16.0-17.6 sequence (1.6 s off-screen + facade burial + ~2 s black courtyard) does not occur — the trick window t=15.8-17.7 holds `hero_occl` 0 on every frame and the abort/dolly path engages on the two later roof-edge passes. P1 "no hero pixels" samples: s3 20 -> 5, s3b 18 -> 4. s3 W7 100 blocked frames -> 0 (the alley strand-through-geometry frames went with the camera loss). Note: the s3 route shifted slightly (the frontPikeSwan program is 0.06 s longer, so the chain's release/catch times move) — same script and spawn.

Gap 2 (flip shape quality): flip_check rendered rotations on the long programs s3 1.93-2.10, s3b 1.93-2.01 (r08: 2.06-2.10 — the r08 hold-off did not truncate programs; per-release rotation count was already ~2 and stays ~2). F4 longest <= 150 deg/s hold: frontPikeSwan 0.27 -> 0.36 s (PASS); s3b holds 0.54-0.87 s all PASS (s3b A7 100 % of shape segments >= 8 frames, was 100 %; s3 97 %, was 88 %). The pencil/straddle leg overlay keeps the straight-leg keys through the holds (clip-time scale above; pixel confirmation is the critic's). F12: wallFront fires on the s3 route (t=22.12, 0.46 rendered rotations before the landing cuts it) and on s3b (t=3.58, 1.00 rendered rotation) — present in both rounds' telemetry; r08's "missing" read is a visibility/cut-short question, not absence.

Gap 3 (W8 retract): drawn-after-release duration median 0.28 -> 0.30-0.35 s per clip (min 0.30; checker band 0.15-0.40 s holds on all six). The projected strand length now moves on every frame of the window instead of 3 static frames + a 5-frame collapse (s1 telemetry endpoint projections, e.g. the t=8.50 release: 685 -> 26 px over 0.23 s; t=16.90: 954 -> 74 px over 0.22 s; the r08-measured t~4.6 release: progressive from frame 1). Pixel-length measurement on the mp4 is the critic's.

Adjacent items: P1 air s1/s5 79 -> 82 % (still under the 90 % bar), s4 air 88 -> 89 %, s2 air 72 -> 69 % (small-sample churn; swing side 95 -> 94 %). Night W5 halo: s5 94 -> 95 % (PASS at the bar); s3 91 -> 95 %, s3b 72 -> 75 % (trick-cam end-on / short frames remain the low clip). W5 judged-pass held: s1 89 %, s2 95 %, s4 98 %. s3 W4 25 -> 38 % <= 400, worst 774 -> 796 deg/s (>700: 2 -> 1; the r08 t=10.68 gait-spike route point moved with the timing shift; the wall-entry gait path was not root-caused). s3 W10: the r08 t=16.92 unanswered press does not occur (6/6 resolve). s3 catch delay median 0.00 s (held); s3b A5 263 -> 233 deg/s (held); s3 A5 catch chest-rate median 512 -> 599 deg/s (1/7 <= 400 both rounds). s2 wall-press arm-up: W2 arrival median 2 deg (unchanged; the steep-rope bias code untouched). A4 longest held pose <= 0.28 s on all clips (held). Barani F3 rendered peak 1018 deg/s on s3b (unchanged — not addressed this round; s3 barani 820 -> 841). F3 rendered peaks > 800 remain on s3 frontDouble/frontPikeSwan/rudi/wallFront (814-937).

## Not reached / known-remaining (measured)

- P1 air side under the 90 % bar on every clip (s1/s5 82 %, s3 63 %, s3b 67 %, s4 89 %); swing side 63-97 % (s3 63 % unchanged).
- F3 rendered peaks > 800 deg/s on 4 of 8 s3 tricks; barani F2 mean 291 deg/s (under the 300 floor this round, was 303); barani F3 1018.
- s3 W4 38 % (wall-entry / gait path, not root-caused); s3b W4 67 %, s1/s5 W4 85 % (at the floor).
- s3b A3 5/6 (one release's 0.1 s signature change just under 0.10; r08 6/6).
- s2 W9 8/9, W10 t=2.25 unanswered press, s2/s3b/s4 W3 (4-8 of 7-9 shots) — the web-shot path was not touched.
- s3b W5 75 % (13 of 75 web-on frames not judged: short / off-screen; contrast median 48 the low clip).

## Environment notes

- All six clips come from ONE detached chain on build `a650c9bb`; two earlier in-round builds (watchdog + W8-anchor-retract variant; + wall-mode watchdog / pitch-cap relief) were captured for s3/s1 probes and discarded; each engine was stopped between iterations (driver SIGTERM -> guard -> engine; the coordinator log shows clean releases; no PAUSED, no foreign-process stops).
- Per-case engine walls 64-79 s (s2/s3b cases) and 175-197 s (s1/s3/s4/s5); no mid-chain admission retries this round.
- The W5 material asset (M_TravWeb) was not rebuilt (the runtime parameters own the live look; the asset's fallback defaults match them since r08).
