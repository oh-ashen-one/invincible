# Round 01 (builder SW): web deployment, chain, camera, swing body -- probe results (no clips rendered yet)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Evidence = nullrhi fixed-step probes (1/60 s, 1.5 s pre-roll) of the round-00 scripts (regenerated: s1/s5/s4 chain rule changed, s3 per-case program start), `tools/final/swing/probe_clip.py` +
`final_check.py`. `PROBE_CHECK_*.txt` = the tables (build after the last C++ change except s2 case 7, re-run on a short dev render: W10 2/2). `DELTA_TABLE.txt` = round 00 > round 01 pass flags.
W5 (pixels) needs a render: measured on an 8 s dev render of s1 (not a round clip): 40/61 judged frames pass (66 %), width median 3.0 px.

## Changes (Traversal/**, tools/final/swing/**)
- **W1** strands drawn in `PostAnimTick` (`FWebTravPostTick`, TG_PostUpdateWork, prerequisite = hero mesh tick); origin = hand bone + 7 cm along the finger axis (hand -> middle1 in the reference pose); the telemetry row is completed
  in a TG_LastDemotable tick with the final-pose palm (`fw_pl_*` / `fw_pr_*`): start == palm to 0.0 cm on every web-on frame. Segments are spaced `(k/12)^1.6` (short at the hand) and the lens-hide uses the nearest point of a segment (1.2 m).
- **W2** firing-arm aim weight reaches 1 in 0.04 s; the aim is a layer re-applied after every other layer (air arch/track arms, flips, tuck); shoulder-raise anticipation 0.14 s.
- **W3** `ShootDur = clamp(dist / 250 m/s, 0.06, 0.20)`; every air press now pends: the body stays ballistic while the tip flies, the pendulum starts when it lands (`PendingShoot`); pending body frame leans onto the rope frame.
- **W4** body frame onto the rope through a critically damped spring (omega 10, capped 320 deg/s) + a 0.12 s spine-bank smoothing + hips-to-rope alignment over 0.7 s + the air-sway roll decays in 0.1 s instead of vanishing in the first swing frame.
- **W10** no-anchor press = reach gesture (arm up/forward along the camera aim, 0.3 s, no strand; also on a fresh press while the button was already held); a swing pressed right after a jump answers in 0.04 s (cooldown 0.12 -> 0.04).
- **W9** hand from the anchor side relative to the velocity heading (was the steering-blended direction).
- **W7** anchor candidates whose hand->anchor line is blocked (geometry raycast, tree-crown spheres, skimming angle) are skipped; crown spheres from the streamed `ISM_ez_*leaves` instances (`FWebTravWorld::SegmentHitsCrown / CrownTopAt / PushOutOfCrowns`).
- **W5/W6/W8** one light tone (core 70 %, dark rim, level 1.0), width clamp 3.6-4.0 px with a 0.7 taper to the anchor, wave straight 0.08 s after landing; release: the far end lets go and comes home to the hand over 0.30 s drooping and fading (was: retracting toward the anchor, 0.17 s).
- **Gap 2** canopy-aware arc bottom (feet >= crown top + 1.5 m over the street along the path); s1/s5/s4 scripts: gap 0.3 s, `repressVz 99`, `trickEvery 0`, tune `ArcLowMin=15,...,WallClearance=14,AltChain=0`, spawn y 560 (the chain no longer reaches Times Square's low anchors within 20 s).
- **Gap 3** camera pushed out of crown spheres (0.5 m); see the finding below.
- **Gap 4** swing life ported from spiderbench `animator.js swingLife` into `UWebTravAnimInstance` (springs 2.1 / 2.8 / 2.0 Hz; styles split / tuck / long / stride, never repeated; phase targets).
- **Secondary** s3: each case starts at another program of its stick pool (`FlipKStart`); night hero-only fill stays at 1400 cd at NightK 1 (`HeroFillNightCd`). Not done: F11 (arms lead legs at flip shape changes).

## Gap 2 diagnosis (the "reach without web" at s1 8.4-9.6 s of round 00)
It was a flow flip (`trickEvery 3`): the release became an `air/trick` with a final reach (flipReach), and the script re-pressed only once falling at -8 m/s (1.0 s later); the web-on share of s1 was 40 %. Not a no-anchor search.
Now (s1 probe): web-on 77.5 %, longest stretch without a strand 0.40 s (all re-presses 0.30 s after the release), no unpowered fall > 0.8 s, swing bottoms median 15.4 m over the floor (min 7.4 at the last swing of the clip).

## Gap 3 finding
The logged camera (telemetry == rendered: the projected strand matched the frames to 1 px median) was already 4.6-22 deg down in s1 (median 10.5), s4 (4.3-22), and `hero_bbox_h` 0.20 median (73 % of s1 frames in 0.15-0.30) -- not 40-70 deg.
The impression comes from the hero swinging 15-25 m over the street with a 59-71 deg vertical FOV (90+ deg horizontal): the street fills the lower half. The island floor / `camPitch` script input are not involved (`spawn.camPitch` 0.12).
s3 5.0 s (`c2`): hero bbox 0.11 of the frame at the tuck (bbox of a tucked body in a wide lens; flip camera 4.9 m, elevation 11.5 deg): unchanged this round. The head cut at s1 0.0 s is the initial camera distance (3.5 m, hero 0.39 of the frame): unchanged.

## Probe numbers (round 00 > round 01)
See `DELTA_TABLE.txt`. s1: W1 0 % > 100 % of 953 frames; W2 arrival 48 deg > 3 deg (15/15 <= 20); W3 0/6 > 15/15; W4 chest worst 2155 > 934 deg/s (40 % <= 400; >700: 4 of 15, all attaches that start head-down at 130-150 deg);
W6 PASS; W7 63/1191 frames blocked (all clear fraction >= 0.8: grazing 2.5-10 m before the anchor); W8 0.28 s; W9 15/15; W10 15/15; A1 43 % > 83 %.
s2: W2 still FAIL (8/9 within 30 deg over the swing), W9 8/9, W10 9/11 -> the two misses were case 1 (a ground press jumps first, the strand follows 0.1 s later) and case 7's second press (fixed afterwards: 2/2).
s3: W1-W3, W6, W9, W10, A1, A6, A7 pass; W4 worst 1071; A5 catch 0.67 s median (not addressed). s4: W1-W3, W6-W10 pass (web-on 46.8 % by design: gap 1.6 s).

## Open (not passing on probes)
- W4: 4 of 15 head-down attaches exceed 700 deg/s over the 0.15 s after the attach; all others <= 460.
- W5: one light tone vs a bright sky / pale facade = low contrast (66 % of judged frames on the dev render; round 00's adaptive black/white strand passed 100 %).
  Trade-off for the lead: a thin dark outline (rim) is the cheap fix; a mid-grey core was tried (44 %), a lighter core 69 %.
- W7 (see above), W2 in s2 case 3 (wall-run press, arm 30+ deg during the swing), A5 (catch after a trick), F11, s3 as one continuous chain.
- `tools/showcase/with_holder.sh` (not my path) has an uncommitted retry for the launch refused while the resident takes the perf lock before its holder file appears.
