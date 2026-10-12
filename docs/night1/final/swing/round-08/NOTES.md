# Round 08 (builder SW)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Answers critic r07's three orchestrator-filtered gaps (W5 strand rendering; s2 wall-adjacent press pose; s4 float carry + evolution), plus the adjacent s3 W4 wall-entry snap and barani F3. Build commits `21d8903b` + `88792456` + `33992601` + `aeb81e25` + `737ff46c` (final; every clip below rendered on `737ff46c` in one detached chain after the in-round probes were discarded). Same maps / profile / settings as round 07 (`-WHSuit=tessera`, playable + Fast, 1920x1080, fixed 1/60 s, 1.5 s pre-roll cut); scripts / keys / spawns unchanged.

## Code changes (all in owned paths)

- `WebTraversalComponent.h` — W5 root cause: the two-tone strand's adaptivity never fired (CoreBright == CoreDark pinned the core share at 0.5 of the width and Pivot 100 sat above every exposure-applied luminance reading, so the bright-core + dark-rim mix averaged back to the background on every mid-toned facade). The core share now switches at Pivot 0.30 (exposure-applied pre-tonemap units): over dark backgrounds the bright core fills RopeCoreDark 0.9 of the width, over bright ones the dark rim (1 - RopeCoreBright 0.15) carries the line; CoreLvl 0.9 -> 1.15, RimLvl 0.08 -> 0.03; screen clamp 3.6-4.0 -> 3.2-3.4 px (the checker's measured width runs ~0.5-0.9 px of AA halo over the drawn width) with the anchor taper 0.62 -> 0.72 (far end stays >= 2 px).
- `traversal_web_material.py` — fallback PARAMS synced to the runtime values (the character pushes them onto the dynamic instance every frame; the material asset itself was not rebuilt, so the in-material Occ depth margin stays 25 cm).
- `WebTravAnimInstance.cpp/.h` — (a) steep-rope arm bias (s2): as the rope direction steepens toward the body axis (dot > 0.72 ramped to 0.92) the firing arm's aim slides up to ~14 deg toward the firing side, so the palm and the strand's first metres sit beside the head instead of behind it; (b) free arm on slow hangs: at SwingSpeedK 0 it hangs low-out (-BodyUp 0.55, was 0.15) instead of mirroring the web arm horizontally; (c) air-drift layer (s4): in Air (not trick / topOut / launches), weight 0.42 fading 38 -> 48 m/s, the arms alternate ~0.4 m forward/down against each other and the legs scissor against them, a full left/right cycle every 1.1 s, eased in 0.12 s so the first second of a float evolves; (d) the six air flavors tighten to ~0.2 s segments with the tail alternation at 0.3 s from 0.72-0.8 s; (e) air_tuck / air_spread are held off while a strand is inbound (WebShotK >= 0) and during the first 0.7 s of a cycle: the tightened timeline otherwise lands the tuck entry's fast chest motion on the auto-chain re-press + attach window (measured 778 deg/s at s1 t=6.43 / 18.62 in the first r08 build).
- `WebTravCharacter.cpp/.h` — the attach body spring stays live into a wall entry fresh off a swing until it converges (or 0.5 s): the swing -> wall mode flip no longer replaces the rope frame with the wall frame in one step (s3 t=10.43 read 1576 deg/s in r07).
- `WebTravFlips.cpp` — barani's first twist 0.38 -> 0.44 s (twist rate 474 -> 409 deg/s, still above the 250 deg/s correction freeze; 720 deg / 2.34 s = 308 deg/s mean stays inside F2).
- `WebTraversalComponent.cpp` — net unchanged: the air-drag cap raise (32 -> 36 + 3*chain, "more carry") was probed in-round and reverted: any drag change re-rolls the fixed-step routes (s1 picked up a 734 deg/s attach and P1-air / A1 dips at cap 36). The float work ships as pose evolution only.
- `tools/final/swing/run_clip.py` — queue label r07 -> r08; new `--tune` passthrough (probe-only `-WHTravTune` override; not used for the round captures).

## Measured (round-08/CHECK.txt; flip_check = docs/night1/traversal/flip_check.py)

Gap 1 (W5 strand): judged-frame pass: s1 26 -> 89 %, s2 44 -> 95 % (FAIL -> PASS), s3 57 -> 91 %, s3b 10 -> 72 %, s4 77 -> 98 % (FAIL -> PASS), s5 97 -> 94 % (PASS -> marginal FAIL). Measured width median 3.0-3.5 px (r07: 2.0-2.5); contrast median 48-170/255 by clip (r07: 23-114). s2 frames over dark backgrounds (band < 80/255): 47/47 pass (the r07 dark-glass case). s1's pale-facade (0.9-1.1 s) and dark-glass (10.5-11.2 s) probe windows pass. Remaining s1/s5 fails: a repeated t~10.6-10.7 pair where the strand runs end-on toward the lens and reads rope == band, plus width > 4 px frames on near-vertical strands close to the camera (bright core + AA halo measures 4.25-7.25 px over dark night glass).

Gap 2 (s2 wall-adjacent press): the c3 wall-run press (case t=2.6) now hangs with the firing arm raised along the strand and the strand beside the head silhouette (frame-verified on the final build at case t=2.8/3.1); the free arm hangs low-out. W2 unchanged in character (arrival median 2-10 deg, all <= 20). W2 stays FAIL on s1/s5/s2/s3/s3b on the <=30 deg-over-swing clause (11/13, 8/9, 7/8, 6/7) — the steep-rope bias costs up to ~14 deg there (max-over-swing median 17-19 deg, was 5-7).

Gap 3 (s4 float): air-pose turnover — s4 air node frames now cycle rise/apex/fall with the drift overlay from the first 0.12 s (tucks/spreads join at 0.7 s); A4 longest held pose: s4 0.28 s (r07: 0.38), all clips <= 0.28 s. Carry (drag cap) probed and reverted (see above): the float's momentum profile is r07's.

Adjacent: s3 W4 t=10.43: the wall-entry frame now reads 167 deg/s (1576 in r07 on the same route point); a separate one-frame 841 deg/s spike 0.17 s into the wall run (t=10.68) remains — pose-side, inside the gait, not root-caused this round. s3 W4 overall 25 % <= 400, worst 774 (r07: 33 %, 1576). F3 rendered peaks: s3b barani 1063 -> 1018 (still > 800), s3 barani 868 -> 820; other programs 724-826 (r07: 733-874). A5 s3b: median 263, 6/6 <= 400 (held). s3 catch delay median 0.00 s (held).

## Regressions / not reached (measured, vs round-07 CHECK)

- P1 air side on s1/s5: 91 -> 79 % (the r07 floats held wider spreads; the r08 drift/scissor poses shrink the hero mask bbox under the 0.18 floor more often). Swing side held: s1/s5 94 -> 93 %, s4 96 -> 97 % swing / 92 -> 88 % air.
- W4 s1/s5: 92 -> 85 %, worst 420 -> 573 (no > 700 either round): the release-clip (releaseSpread/releaseTuck) motion inside the +-1-frame attach edge of the window; the tuck guard removed the 778 pair but two attaches still read 459-573.
- W5 night s5: 97 -> 94 % (the brighter core's halo measures > 4 px wide on near-vertical strands over dark glass; 7 of the 8 fails are width, not contrast).
- s3b W5 72 %: 13 of 83 web-on frames not judged (short / off-screen) plus the trick-cam end-on strands; contrast median 48 is the low clip.
- s3 W4 25 % and the t=10.68 841 deg/s gait spike; s3/s3b P1 swing 63/80 %, air ~60-66 % (unchanged in character); s2 W4 89 % (worst 410); s3b W3 4/7, s4 W3 7/8, s2 W3 8/9 (web-shot path not touched); s3 W10 t=16.92 press unanswered (was t=23.38 in r07 — the route shifted); barani F3 1018; A2 on s2/s3 small-sample as before. s1 W7 39 blocked frames (r07: 39, same route).
- Occlusion: longest hero_occl > 0 stretches per the telemetry columns (unchanged paths): s1/s5 0.03 s, s4 0.02 s, s2 0.18 s, s3 0.75 s (t~17.7, trick-cam TC11), s3b 0.65 s (t~3.7, TC11) — same character as r06/r07.

## Environment notes

- All six clips come from ONE detached chain on build `737ff46c`; three earlier in-round builds (21d8903b tone+bias+drift, 88792456 carry variant, aeb81e25 first tuck guard) were captured for probes and discarded; each engine was stopped between iterations (driver SIGTERM -> guard -> engine; the coordinator log shows clean releases; no PAUSED, no foreign-process stops).
- Per-case engine walls 64-79 s (s2/s3b cases) and 178-194 s (s1/s3/s4/s5); one mid-chain admission retry this round.
- The W5 material asset (M_TravWeb) was not rebuilt: the runtime parameters own the live look (pushed per frame); the in-asset Occ depth margin is still 25 cm and the asset's fallback defaults now match the runtime values for the next content build.
