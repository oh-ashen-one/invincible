# P5 combat, round 01: notes

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Builder: Claude Opus 5.5. Branch `night1/combat` (merged `Opus-5.5-Loop-Night-1` at 464dfaa first). Nothing below has been critic-reviewed.

## What was run

| item | how | result |
|---|---|---|
| map | `/Game/Tests/Combat/Combat_Street`, built headless by `Scripts/build_combat.py` (steps traversal, characters, combat) | lit procedural test street, 183 boxes (layout in `../combat_street_layout.json`) |
| fight | `scripts/fight25.json`: spec `mgbmgm` (e1 melee, e2 gunman, e3 brute, e4 melee, e5 gunman, e6 melee) at 7 m (gunmen 11 m), 40 beats, 1.0 s pre-roll, 27 s total | 40 / 40 beats fired (`ue/fight_beats.jsonl`) |
| logic replay | `run_fight.sh logic` (`-game -nullrhi -benchmark -fps=60`) | event log identical to the record run (140 / 140 events) |
| video | `run_fight.sh movie` through `gpu_slot.sh capture` (1920x1080, `-dumpmovie`, fixed 1/60 s) | `fight25_1080p60.mp4` (1622 frames, re-encoded crf 27 to 10.8 MB); same summary as the nullrhi replay |
| 4K stills | `run_fight.sh stills` through `gpu_slot.sh capture`, 3840x2160, `r.ScreenPercentage 100` | `stills/still_NN_tSS.SS.jpg` ×10 (true 3840x2160, native, JPEG q92 from the PNGs) + `stills_sheet.jpg`; lock sidecar `wait_s 150.5, hold_s 104.8, util_before 0, util_after 75, contaminated true (no-exclusive-lock)`; same summary as the other runs (28 hits, 4 KO) |
| browser reference | `node browser_fight.mjs scripts/fight25.json <out>` on dev port 5206, headless Chrome on SwiftShader | `browser/` (40 / 40 beats fired, no console errors) |
| comparison | `compare_logs.py ue browser COMPARE.md compare.json` | `COMPARE.md` |

GPU lock sidecar for the movie: `wait_s 197.8, hold_s 494.8, util_before 0, util_after 0, instances_before 5, instances_max 6, contaminated true (no-exclusive-lock)`. No perf
run was made this round, so there are no frame-time numbers. The movie and stills use a fixed game step, which means they show nothing about real-time performance.

## Scripted beats (Unreal, `ue/fight_events.jsonl`)

| beat | fired at (real s) | what happened |
|---|---|---|
| combo A (4 presses) | 1.50-2.90 | cross (flying kick in: gap 5.3 m > 5.2), hook, kick, rising uppercut ender -> e4 knocked (hp 1) |
| perfect dodge 1 | 4.67 | back flip, PERFECT (e3 brute swing), slow-mo 0.85 s x0.22, focus +0.35 |
| counter + launcher + air combo | 5.00-6.65 | counter jab (1.6x) -> hold -> launcher on e6, 3 air hits, slam, ground pound |
| web shooter x4 | 7.80-8.95 | 2 webs on e1, 2 on gunman e5 (disarmed: mesh swapped to unarmed, stand-in pistol thrown) |
| web strike (E) | 9.70 | pull-in kick on e2 at 10.3 m, 20 dmg, knocked |
| combo C + perfect dodge 3 | 11.40-13.37 | 4-hit string on e1, perfect dodge (e5) |
| finisher (Q) | 14.60 | finisher on e2 with the side-angle cinematic, then wall pin (cine 'pin') |
| brute section | 16.77-20.03 | 2 webs (web 0.67: brute stunned), strike, launcher on the stunned brute, 3 air hits, slam |
| perfect dodge 4 + counter | 20.83-22.32 | e1 KO |
| finisher 2 | 23.27 | on e1 (the scripted `toward e3` did not win the target choice: e3 was in the air) |
| combo E | 25.35-26.05 | e5 staggered twice |

Totals: 28 hits, 0 whiffs, 4 KO, 2 launches, 6 air hits, 2 finishers, 3 dodges (3 perfect), 6 web hits; hero took 33 damage (hp 67); 27 hit-stops, 8 slow-mo
requests, minimum time scale 0.05 (finisher hit-stop), 7.6 s of real time below time scale 1. Two enemies were still standing at 27 s (e3 brute hp 90, e5 hp 17).

## Unreal vs browser (same beats at the same real times; `COMPARE.md`)

The fights diverge after the first random choice: different worlds (test street vs a browser city street at x 250, z 183) and different RNG streams. The 3 record-run
dodge times were tuned to the Unreal fight, so in the browser all 3 dodges were plain (0 perfect), and there was less slow-mo (4.6 s vs 7.6 s real) and more damage taken
(69 vs 33). The first move started by each beat matched in 26 of 40 beats. Rule-level values that match: hit-stop count (27 vs 26), minimum time scale 0.05, combo
move names and damage (jab 9, cross 10, hook 11, ender 16/17, web strike 20, finisher 999), air-combo segments (9/9/14 + ground pound 8), web amount per shot (0.34;
0.17 on gunmen, who are disarmed by it), brute stun at web >= 0.6.

## Observed in the frames (builder, not a critic)

- Enemies face the hero, their clips play (idle, stumbles, knockdown, get-up, gun aim), and the hero's combat clips blend over the traversal animation.
- Hit flashes, sparks and web strands render. The dust puffs are grey spheres, and the web cocoon is visible as white blobs.
- The street lighting is flat, with a blue haze from fog and sky. The street is empty apart from the fight.
- The combat camera sometimes gets too close to the hero, with bodies filling the frame. The finisher cinematic changes the camera angle abruptly.
- The pinned gunman appears as a white splat on the facade; the body is hard to read.

## Not done this round

Throwables (props.js), the Space jump-evade and jump-cancel (these need a P3 input hook), the HUD (hud.js), combat audio, Niagara FX, the Manhattan map (see HANDOFF),
perf measurement, and a critic pass.
