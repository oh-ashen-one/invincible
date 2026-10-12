# P5 combat, round 02: notes

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Builder: Claude Sonnet 5.5 (resumed the interrupted Opus 5.5 round-02 WIP; both are on this branch). Branch `night1/combat`. Nothing below has been reviewed by a critic yet.
Target of the round: the round-01 critic's single biggest gap, **hit-stop plus a readable reaction on every contact** (`critic/round-01-CRITIC.md`), with the two next gaps
(enemy aggression and telegraphs, combat camera) done in the same round because the WIP already carried them.

## What ran

| item | how |
|---|---|
| map | `/Game/Tests/Combat/Combat_Street`, rebuilt by `Scripts/build_combat.py --steps combat` inside the capture hold (`ue/map_build.out`: 191 actors, 183 boxes) |
| fight | `scripts/fight30.json`: reactive record run of `scripts/fight30_record.json` (seed 23, picked out of a 16-seed sweep, `ue/seed_sweep.txt`), frozen to fixed times by `freeze_script.py` (59 beats: 44 scripted + 15 reflex dodges) |
| movie | `run_fight.sh movie` (real game, `-game -RenderOffScreen -benchmark -fps=60 -dumpmovie`), 1920x1080 output, **internal resolution 100 % (1920x1080, TSR native)**; `fight30_1080p60.mp4` = that movie without its first 0.9 s (P3 chase camera + exposure adaptation), x264 crf 30, 13.6 MB |
| stills | `run_fight.sh stills`: 10 native 3840x2160 frames, `r.ScreenPercentage 100` (internal 3840x2160), JPEG q2 from the PNGs. Times chosen from the record run's events by `still_times.py` |
| measurements | `measure_r02.py` (pixels + per-frame C++ boxes of the movie run) -> `measure.md`, `measure.json`; `sim_metrics.py` -> `sim_metrics.json`; `boxes_check.jpg` = 6 frames with the logged boxes drawn (projection check) |
| GPU lock | whole chain in one `gpu_slot.sh capture` hold: `wait_s 576, hold_s 925, util_before 0, util_after 3, instances_before 3, instances_max 4, contaminated true (no-exclusive-lock)`. **No perf run this round: there are no frame-time numbers.** The movie / stills use a fixed game step. |

## Numbers against `SPEC.md` (movie run `ue/movie/`, 1831 frames measured, fight start + 0.5 s to the end)

| id | target | r01 (critic) | r02 measured |
|---|---|---|---|
| CB1 hit-stop | victim-crop diff < 1.0 for >= 3 consecutive frames at every contact | 0 % of frames below 0.3, no frame held | **47 / 48 contacts** (median frozen run 4 frames, min 2). The miss: `hero->e8 light` at 14.27 s (run 2). 208 frozen frames of 1922, 40 hit-stops of 5 / 6 / 7 frames |
| CB2 reaction | victim root >= 0.3 m in 0.5 s | no flinch on the black-jacket thug | **38 / 39 hero blows** (3D distance). The miss: `hero->e5 ender` on the armored brute at 11.73 s (0.21 m; armored brutes do not stagger, by design) |
| CB3 flash | new near-white area <= 3 %, ~0 six frames later | opaque disc ~12 % of frame width | light / air / launch / finisher contacts **<= 1.62 %**; the three ground-pound contacts (slam landings, dust cloud) 2.57 / 2.73 / **3.20 %** (six frames later up to 3.95 %) -> **just over the limit on the slam landings**, see Known problems |
| CB4 aggression | longest gap between attack starts <= 1.0 s | 0.93 s window with nobody attacking | **0.817 s** (65 attack starts in 32 s) |
| CB5 telegraph | indicator >= 0.4 s before the blow, aim line for gunmen | none | min lead **0.42 s**; a warning marker or laser is on screen in 92 % of frames |
| CB6 enemies in frame | >= 5 standing enemies (>= 5 % height) in >= 80 % of frames | 4-6 early, 1-3 from 6 s | **95.7 %** of frames (median 8) |
| CB7 camera | hero box >= 5 % from every edge in 100 % of frames; 4-6 m back, 15-25 deg down | hero cut at the edge @5.5-6.5, @12.0-13.3 | **100 %** (min margin 5.7 %). Distance 4.47 / **5.52** / 7.50 m (5 / 50 / 95 %), pitch down 16.2 / 21.0 / 21.0 deg, 2.0 m over the hero's centre. The 95th percentile is beyond 6 m (the margin controller dollies out) |
| CB8 occlusion | nothing hides > 15 % of the frame in front of the hero | bat in the foreground @13.2 | max **6.0 %**, 0 frames > 15 %. A separate check counts a body filling >= 12 % of the frame: 5 frames |
| CB9 continuity | whole-frame diff <= 25 | one snap of 25.8 @16.73 | **25 frames** above 25 (3.6-3.7 s, 13.1, 14.95-14.98, 21.55-21.62, 22.4, 25.0, 29.1, 32.0): fast slam / finisher choreography with dust, not camera moves (camera turn <= 0.94 deg per frame, pitch <= 0.40 deg; 24 frames have a dolly step > 0.3 m, max 0.98 m at 14.97 / 29.1 / 32.0 s, from the margin pass, see Known problems) |
| CB10 move set | jab combo, dodge, launcher + 3-hit juggle, web shots, web strike, wall pin, finisher with a camera beat | missing: web-strike, juggle, finisher | **3 launchers, 9 air hits (3 x 3, each ends in a slam), 2 finishers, 5 web hits, 1 web strike, wall / ground pins, 14 dodges (10 perfect), 39 hits, 6 KOs** (movie run) |
| CB11 brute silhouette | reads bulkier than a thug | not distinguishable | scale 1.3 tall, x1.4 / x1.45 wide (mesh scaled non-uniformly, not a new mesh); read in the stills |
| CB12 determinism | frozen replay == record | identical (r01) | nullrhi replay == nullrhi record (377 / 377 events). **The rendered movie is not identical to the record**: the first 170 events match, then it drifts (372 events; 39 hits vs 42; the same launchers / finishers) |

Movie run totals (`ue/movie/fight_summary.json`): 39 hits, 0 whiffs, 6 KOs, 3 launches, 9 air hits, 2 finishers, 14 dodges (10 perfect), 5 web hits, 40 hit-stops (208 frozen
frames), 10 slow-mos (8.9 s real below scale 1), hero hp floor 30 (capture aid), 9 enemy melee hits, 36 shots (3 hits), 16 enemies spawned (9 + reinforcements, 9-10 alive).

## What changed since round 01 (all in `Source/WebHomage/Combat`, `Scripts/build_combat.py`, `docs/night1/combat`)

1. **Hit-stop**: `HitStop(frames)` = world freeze (global dilation 0.002) of 5 / 6 / 7 frames (light / heavy / finisher) on every contact, ground-pound landings 6, hits on the
   hero 5 / 6. The victim's flinch pose (stumble clip entered at 0.1 s, 0.02 s fade, head / torso snap) and a hit push (~0.4 m) are in the contact frame. The combat camera holds
   exactly while the *world* is frozen (the dilation set on one tick applies to the next, so the hold uses `bDtFrozen`); the sparks are real-time objects that hold for the same
   frames. Why 5-7 and not 3-5: TSR needs two frames to settle after the pose change, the critic's test needs three stable frames after that.
2. **Impact FX**: the opaque disc is gone (small additive core <= ~0.2 m + streaks, gone in ~10 frames); dust darker and smaller (daylight made the old grey read as white discs).
3. **Aggression**: several committed attackers (melee tokens up to 3, gun tokens up to 2), pressure swings when 0.8 s pass without a wind-up, the ring stays inside the camera arc,
   `keep 9` / `reserve` reinforcements run in from 13 m. **Telegraphs**: a glowing "!" over every attacker (orange melee, red brute / gun) plus a red aim line for gunmen.
4. **Camera**: mid-high framing camera (yaw picked by scoring hero + 3 nearest enemies on screen, no body within 3.6 m of the lens, no wall, no looking into the sun, turn <= 55 deg/s), hero-margin
   controller (soft target 10 % with 0.18 s look-ahead, hard pass 5.5 %), a 3.2 m bubble around the lens that enemies respect (radius grows with scale, brute x1.15, +0.9 m during the
   finisher), a finisher **push-in** (same camera, +-18 deg orbit, 3.4 m, 14 deg pitch, fov 68, eased 0.7 s in / 0.8 s out; the yaw search pauses during it).
5. **Moves**: launcher chain in scripted play (`launcher` key, target = best non-brute within 4.5 m), juggle presses wait until the hero hangs in the air (`react: air`), chained
   beats (`rel`), so a hit or a moving target cannot break a combo. `hero_armor` (script flag, capture aid): a committed launcher is not interrupted and heavy blows stagger instead of
   knocking down; `hero_min_hp 30`.
6. **Look**: the map is now a daylight street (warm sun 32 deg high along the street axis with cast shadows, sky light 0.6, thin haze). The first r02 dusk (WIP, sun 7 deg) was
   blue-black. Look sweeps with `-WHCmbLook=` presets (`look_sweep.sh`, no map rebuild): low suns of any colour stay blue (the shade is sky-lit and the low sun barely reaches the floor),
   overrides of sun intensity alone change nothing (exposure adapts and the sky scales with the sun), a 30+ deg sun along the axis with a dim sky light gives warm key + cast shadows
   and the best readability; a bright fog luminance (0.35) washed everything to pale blue-grey and was replaced by 0.08 / 0.07 / 0.09.
7. **Tools**: `sim_metrics.py`, `measure_r02.py`, `sweep.sh` / `sweep_report.py` / `pick_seed.py`, `prep_r02.sh`, `capture_r02.sh`, `final_r02.sh`, `look_sweep.sh`, `still_times.py`,
   `package_r02.sh`, `replay_diff.py`. Every Unreal launch (commandlets included) goes through `gpu_slot.sh capture`.

## Known problems / honest limits

- Slam-landing dust reads near-white (3.2 % max, limit 3 %). One light-hit contact only freezes 2 clean frames; one armored-brute blow does not push.
- Whole-frame diff spikes (25 frames > 25) from slam and finisher choreography; 24 frames with a camera dolly step of 0.3-0.98 m come from the bone-based margin pass when the hero's
  pose jumps. The soft look-ahead removed most of them but not all.
- The camera sits 5.5 m back at the median, 7.5 m at the 95th percentile; the hero is small in the frame in those moments.
- The look is a procedural test street: flat boxes, no materials worth judging; cool-neutral shade with hard shadows. Backlit moments (camera facing the sun) still show black silhouettes
  (e.g. the still at 3.05 s and the first frames).
- The sim is not bit-exact between nullrhi and rendered runs (millimetre noise from t = 7 s grows); record and movie therefore differ in detail. `pick_seed.py` chooses on the nullrhi
  record, `measure_r02.py` and every number above are from the rendered movie run itself.
- The scripted hero is a capture aid: hp floor 30, armored launcher, reflex dodges. Not ported: throwables, Space jump-evade, HUD, audio, crime flow, Niagara FX, Manhattan.
- Reference-only text: the `ue/record/` and `ue/movie/` logs are this round's raw evidence; `fight_frames.jsonl.gz` has one row per frame (camera, screen boxes of every character).

## Hazards found (for the orchestrator)

- `gpu_slot.py` `run_wrapped` `finally` block sends SIGTERM and, 0.3 s later, SIGKILL to the child's process group whenever the wrapper itself is terminated. `stop_ue.sh` kills the
  drivers first, so on a wrapped run it ends in a SIGKILL of the engine 0.3 s after the SIGTERM. Stop a wrapped engine by SIGTERM to the UnrealEditor pid only, and let the wrapper exit
  when its child does. (Not edited: not this piece's file.)
- `Scripts/run_game.sh` still has `kill -9 $PID` on its `-timeout`; `run_fight.sh` passes 2400 s, so it only fires on a hang.
- The exclusive perf lock of other agents made every capture wait 5-15 min this round (`wait_s` above).
