# P5 combat, round 03: notes

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Builder: Claude Sonnet 5.5. Branch `night1/combat`. **Nothing below has been reviewed by a critic yet.** Target of the round: the round-02 critic's single biggest gap,
**hit reaction and impact** (`critic/round-02-CRITIC.md`): freeze only the hero and the victim for 3-5 frames while the camera keeps a 2-4 px shake (whole-frame diff >= 1.0), an additive red-orange flare
covering 1-3 % of the frame gone by frame 8, victim rotates >= 30 deg and moves >= 0.5 m within 0.3 s, heavy / finisher blows launch >= 2 m. Test: victim-crop diff < 1.0 for >= 3 frames while the whole-frame diff
is >= 1.0, whole-frame frozen frames <= 3 % (r02: 7.3 %).

**Verdict on my own numbers: the reaction, flare, shake and whole-frame-frozen targets are met; the combined pixel test (crop < 1.0 AND whole >= 1.0 for 3 frames) is met on only 15 of 34 blows (44 %) in the
published mp4** (crop < 1.0 alone: 24 / 34). See "Why the combined test still fails" and `HANDOFF.md` for the next setting to try. A second capture with that setting could not be taken: the GPU wedged
(see "Hazards").

## What ran

| item | how |
|---|---|
| map | `/Game/Tests/Combat/Combat_Street`, rebuilt by `Scripts/build_combat.py --steps combat` inside the capture hold (now also builds `M_CmbFlare`; `ue/map_build.out`: 191 actors, 183 boxes) |
| fight | `scripts/fight30.json`: reactive record run of `scripts/fight30_record.json`, **seed 14** picked out of a 13-seed nullrhi sweep (11-23, `ue/seed_sweep.txt`; `pick_seed.py` now also charges reaction misses), frozen to fixed times by `freeze_script.py` (59 beats: 44 scripted + 15 reflex dodges). Replay and movie event logs are **identical to the record run (381 / 381 events)**: better determinism than r02 (377 / 377 nullrhi only, movie drifted) |
| movie | `run_fight.sh movie` (real game, `-game -RenderOffScreen -benchmark -fps=60 -dumpmovie`), 1920x1080 output, **internal resolution 100 % (1920x1080, TSR native)**; `fight30_1080p60.mp4` = that movie without its first 0.9 s, x264 crf 30, 14.2 MB. The master (crf 18) is measured too (`measure_master.*`) |
| stills | `run_fight.sh stills`: 10 native 3840x2160 frames, `r.ScreenPercentage 100` (internal 3840x2160), JPEG q2, times from `still_times.py` |
| measurements | `measure_r03.py` (pixels of the **published mp4** with `--trim 54` = `measure.md/json`, and of the master = `measure_master.md/json`; per-blow tables, 8 hit strips in `hit_strips/`), `react_metrics.py` (victim push / twist / launch from the frame record), `sim_metrics.py`, `boxes_check.jpg` (projection check) |
| GPU lock | seed sweep + freeze + replay + movie + stills in one `gpu_slot.sh capture` hold: `wait_s 1531, hold_s 850, util_before 0, util_after 0, instances_before 1, instances_max 5, contaminated true (no-exclusive-lock)`. **No perf run this round: there are no frame-time numbers.** |

## Numbers against `SPEC.md` (published mp4, 1831 frames measured, fight start + 0.5 s to the end)

| id | target | r02 (critic / measured) | r03 measured |
|---|---|---|---|
| CB1 hit-stop, crop < 1.0 for >= 3 frames | every hero blow | r02 froze the WHOLE frame (39 hit-stops of 4-6 frames, camera included) | **24 / 34** blows (master 22 / 34), median run 4 frames; hero-hit contacts (attacker + hero held) 7 / 9 |
| CB1 ... and whole-frame diff >= 1.0 in those frames (the critic test) | every hero blow | - | **15 / 34** (master 16 / 34), median run 2. Whole-frame diff during the 189 held frames: min 0.59, 10th percentile 1.01 |
| CB1 whole-frame frozen frames (diff < 0.3, 480x270 gray) | <= 3 % | **7.3 %** (critic); same method on the whole r02 mp4: 7.0 % at 30 fps, 9.7 % at 60 fps | **0.0 %** in the measured fight window; whole r03 mp4 (incl. the opening): **0.21 % at 30 fps, 0.32 % at 60 fps** |
| CB2 victim moves >= 0.5 m within 0.3 s | every blow | "barely moves over 24 frames" | **34 / 34** (min 0.52 m; light 0.77 m at 6.5 m/s decaying exp(-6 t)) |
| CB2 victim rotates >= 30 deg within 0.3 s | every blow | - | **34 / 34** (min 36.8 deg): hit twist about the vertical axis, 72 % of 38-72 deg in the contact frame |
| CB2 heavy / finisher / launcher >= 2 m (1 s) | every non-armoured heavy blow | - | **18 / 18** (min 2.71 m) |
| CB3 flare covers 1-3 % of the frame | peak over frames 0..6 | "2-px ticks" | median 2.4 %, min 1.4, max 3.3 %; **28 / 34** inside 1-3 % |
| CB3 flare gone by frame 8 | every blow | - | **32 / 33** (blows with no other contact within 9 frames): of the pixels showing the flare at frame +3, <= 20 % still do at +8 (worst 0.72) |
| CB13 camera hit shake | 2-4 px | none (camera held exactly) | 3.5 px at the frame edge (roll + zoom pulse, 5 Hz), logged per frame |
| CB4 aggression | longest gap <= 1.0 s | 0.817 s | **0.80 s** (65 attack starts) |
| CB5 telegraph | lead >= 0.4 s | 0.42 s | 0.42 s; a warning marker or aim line on screen in 92 % of frames |
| CB6 enemies in frame | >= 5 in >= 80 % of frames | 95.7 % | 89.9 % (median 8) |
| CB7 camera | hero box >= 5 % from every edge | 100 % | 100 % (min 5.7 %); distance 4.7 / 5.9 / 7.5 m (5 / 50 / 95 %), pitch down 16.5 / 21 deg |
| CB8 occlusion | <= 15 % of the frame | 6.0 % | 7.9 % (0 frames > 15 %) |
| CB9 continuity | no whole-frame diff > 25 | 25 frames | **1 frame** (15.3 s, diff 28.7: the finisher's slow-mo cut-in). The r02 spikes came from whole-frame freezes releasing |
| CB10 move set | see spec | 3 launchers, 9 air hits, 2 finishers, 5 web hits | same: 3 launchers, 9 air hits, 2 finishers, 4 web hits, 34 hero blows, 46 hit-stops (189 held hero frames), 15 dodges (14 perfect) |
| CB12 determinism | replay == record | movie drifted | **381 / 381** for the nullrhi replay and for the rendered movie |

Per blow kind (published mp4, combined test): light 3 / 4, ender 3 / 15, launch 3 / 3, air 2 / 6, slam 1 / 3, web strike 1 / 1, finisher 2 / 2. Enders are the blow that mostly fails: they are the
last hit of a combo, the victim is thrown across the frame and neighbours are close.

## What changed since round 02 (all in `Source/WebHomage/Combat`, `Scripts/build_combat.py`, `docs/night1/combat`)

1. **Local hit-stop** (`HitStop(frames, victim)`): the global time dilation is gone from hits (it stays for slow-mo only). A blow holds the hero (dt 0 for his sim / clips, actor time dilation 0.002 for the
   traversal + anim tick), the victim and every enemy within `HoldRadius` (2.5 m) of the victim for **5 frames** at 60 fps (`HoldUntil` in director real time, `bHeld` per enemy). The rest of the world
   keeps running. Held bodies are immovable in `Separate()`. The framing camera's state (yaw search, dolly, margin pass) does not advance during the hold, so nothing drifts across the victim's crop.
   Why the brawl neighbours are held too: in experiments 2-3 (victim only) neighbours and their long shadows crossed the victim's crop and broke the < 1.0 test on 20 of 31 and 5 of 11 blows.
2. **Hit shake** (`HitShake`): a radial shake, roll + zoom (FOV) pulse in quadrature, 3.5 px displacement at the frame edge, 5 Hz, from the contact frame for the hold + 2 frames. Proportional to the
   distance from the frame centre, so the hero / victim near the middle move well under a pixel while buildings and far enemies move 2-4 px. Experiments 1-3 (below) found that a plain 2 px
   translation moves every crop by ~1.4 gray levels per frame (fails the < 1.0 test on its own) and that a plain sine has zero speed at its peak, which is where the whole-frame diff dipped below 1.0.
3. **Impact flare** (`FWHCombatFx::Impact`, material `M_CmbFlare` built by `build_combat.py`): unlit additive sphere with a soft radial falloff (1 - Fresnel, exponent 0.4, no depth test), a red-orange halo (HDR 1.0, 0.085, 0.008)
   and a hotter core plus 8-16 radial spark streaks (0.02-0.03 m wide, 0.25-0.6 m long). Radius from the camera distance so it covers ~2 % of the frame (`FlareFrac`). Static for the hold,
   fades over 2.3 frames, so it is gone at frame 8. The r02 disc and 2-px ticks are replaced. First versions (HDR 3.4 / 2.0) saturated to a yellow-white ball; the colours were lowered until it reads orange.
4. **Victim reaction** (`WHEnemy`): every blow twists the whole body about the vertical axis (`StartTwist`, 38-72 deg, 72 % of it in the contact frame, peak at 0.09 s, gone by 0.6 s; a blow landing on a
   twisting body reverses it, so the change is always >= 30 deg); light stagger slide 2.6 -> 6.5 m/s; brute 2.4 -> 6.2 m/s; ender / strike knock 6.5 / 7.5 -> 8 / 9 m/s (+ up 3.8 -> 4.2); finisher 8 -> 9.5 m/s;
   air-juggle hit shove 0.8 -> 3.0 m/s; an ender on an airborne victim knocks him away (r02: 4 m/s); the flinch clip enters with no fade (flinch pose complete in the contact frame).
5. Ground-pound landings get a flare too; every blow logs its `hit` event, the frame record now carries the hero-held flag, the shake, each enemy's visual yaw and held flag.
6. **Tools**: `measure_r03.py`, `react_metrics.py`, `exp_r03.sh` (experiment hold with `-WHCmbSweep=1`: every blow cycles shake / hold-radius / flare-size variants, logged as `variant` events),
   `final_r03.sh` / `capture_r03.sh` / `prep_r03.sh` / `package_r03.sh` / `critic_pack_r03.sh`, `movie_r03.sh` (two hit-feel settings in one hold, automatic pick, then the stills), `pick_movie.py`.
   Director flags: `-WHCmbShakePx= -WHCmbShakeHz= -WHCmbHoldR= -WHCmbFlareK= -WHCmbFlareI= -WHCmbVigA= -WHCmbSweep=1`; `run_fight.sh` passes `WHCMB_EXTRA` to every mode.

## Experiments (16-32 s movies of the reactive record script, `-WHCmbSweep=1`; raw tables are not kept in the repo)

| exp | what varied | result |
|---|---|---|
| 1 | translation shake 0 / 2 / 3 / 4 px, 3-6 Hz, flare size | crop diff per frame ~ px per frame: 2 px @ 6 Hz gave a mean crop diff of 1.4 (fails), 0 px gave 0.6; flare K 1.0 = ~2 % of the frame; the flare was a hard yellow-white ball (values too high) |
| 2 | radial shake (roll + zoom) 2.5-4 px | hero-crop diffs 0.3-0.8 at 2.5-4 px @ 4 Hz; but only 11 / 31 blows had a < 1.0 run: neighbours' bodies and shadows moving through the crop (diff maps showed only the moving neighbours changing) |
| 3 | hold radius 0 / 2.5 / 4 m x shake 0 / 3 px | radius 2.5: crop test 12 / 14 (no shake) but the whole-frame diff fell below 1.0 (everything near the fight frozen); with 3 px shake 7 / 10; radius 4: worse (5 / 12) |
| final1 | radius 2.5, quadrature shake 3.5 px @ 5 Hz | the captured movie: crop 24 / 34, combined 15 / 34 |

## Why the combined test still fails (what I measured, not guesses)

- 10 blows fail the crop test alone (mostly enders): a moving neighbour or its shadow inside the victim's box, or an off-centre victim whose high-contrast silhouette shifts with the radial shake
  (a 0.15 px shift at 480x270 already moves a dark body on a bright street by ~1 gray level over the crop).
- 9 more pass the crop test but the whole-frame diff drops below 1.0 in one of the 3 frames: holding the neighbours removes most of the motion, and the shake's per-frame edge speed is ~1-2 px.
- Next try (coded, never rendered, off by default): `-WHCmbHoldR=1.5 -WHCmbShakePx=3.5 -WHCmbShakeHz=2.5 -WHCmbVigA=0.8` (a slower shake keeps the off-centre crops still, an edge-only vignette pulse lifts
  the whole-frame diff without touching the middle). `movie_r03.sh` captures it against the current defaults in one hold and picks the better one automatically.

## Known problems / honest limits

- The combined pixel test is met on 44 % of blows (see above); the critic's own crop boxes may differ from mine (fixed box of the contact frame + 25 %, 480x270 gray, both from the mp4 at 60 fps).
- Holding the brawl neighbours (2.5 m) deviates from "freeze only the hero and the victim": the hero is held for 189 of 1831 frames (10 %), 5 frames at a time, imperceptible in play, but a critic who counts every frozen
  body will see it. Remove it with `-WHCmbHoldR=0`: the crop test then passed 6 / 11 (experiment 3) and 11 / 31 (experiment 2) blows.
- The flare is a soft additive sphere, not a shaped starburst; against bright surfaces it reads orange-white.
- Armoured brutes are pushed (0.55 m) and twisted but do not stagger or fly (by design).
- Ground-pound (silent) victims: 2-3 hits at the same time; some of them show the combined test failing because their neighbours are held for a different blow.
- Still not fixed (critic r02 secondary list): opening shot (backlit, eye level, roll for the first ~3 s: the movie starts 0.9 s in and the first still is still backlit), T-pose on a spawning enemy, the hero passing
  through enemies, the finisher has slow-mo + push-in but no hard cut, the white spider chest emblem on the P2 hero mesh is copied (P2's asset, not mine).
- `hero_armor` / `hero_min_hp 30` / reflex dodges are capture aids of the scripted hero (unchanged). Not ported: throwables, Space jump-evade, HUD, audio, crime flow, Niagara, Manhattan.
- No frame-time numbers (no `gpu_slot.sh perf` run): every run here is `contaminated` by construction.

## Hazards found (for the orchestrator)

- **GPU wedge at 06:54 EDT (07:16 still wedged when I stopped)**: the health monitor had raised the slot count to 5 (`slots=5`); five engines ran at once (mine, traversal, perf, life, city). My movie A stopped
  at frame 609 (0 % CPU, GPU at 100 %), every other engine idled with it, two of them (`life`, `city`, pids 17555 / 17831) became `?E` zombies (stuck exiting in the driver, 20+ min) and the GPU stayed
  at 100 % with only my sleeping engine alive; a `CrashReportClient` (pid 4946, project of pid 3980, not mine) spins at 100 % CPU for 50+ min. The measured ceiling in RULES.md was ~4 instances; **slots=5 is above it**.
- What I did: paused my own chain (SIGSTOP of the chain bash), SIGTERM to my own engine only (it logged "Engine exit requested" but is blocked in the render thread), and SIGSTOP of my own
  `gpu_slot.py` wrapper (pid 49574) so that its 40-minute max hold cannot SIGKILL a wedged engine (the wrapper's `finally` block SIGKILLs the child group). Nothing of anyone else was touched. My engine (pid 10060)
  and the stopped wrapper are still there: **do not SIGCONT the wrapper before the engine is gone**.
