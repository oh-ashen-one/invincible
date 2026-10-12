# Tricks (C) — handoff (round 1 captured, awaiting the blind critic)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation.

Branch `night1/tricks`, worktree `~/sm2-n1/tricks`, scratch `/Users/midir/sm2-n1/_scratch/tricks`. Owned: `Source/WebHomage/Traversal/WebTravFlips.{h,cpp}`,
the flip programs and keyed shape clips (`docs/night1/traversal/blender/make_flip_shapes.py`), the trick input mapping (`WebFlips::ChooseForInput`),
`docs/night1/tricks/`, `tools/tricks/`. NOT owned: WebTravAnimInstance.cpp, WebTravCamera.*, WebTraversalComponent.*, WebTravCharacter.*
(requests go to `REQUEST-traversal.md`). Integration merged at the start of the resume: `origin/Opus-5.5-Loop-Night-1` 2e812770 (traversal r26,
characters r17, terrain r05, city r11); `git diff origin/Opus-5.5-Loop-Night-1 -- unreal/` touches only WebTravFlips.{h,cpp}.

## State
- Round 01 is captured and measured, not yet judged: `docs/night1/tricks/round-01/` (reel `t60_trick_reel.mp4` 60.48 s 1920x1080 native,
  stitched telemetry + pose CSVs, `CHECK.txt`, `NUMBERS.md`, `SHOTLIST.md`, `shapes_ours.jpg`). Measured: P 12 programs / 22 instances,
  V1 PASS (min 141 / 199 deg/s), V2 PASS (0.850-1.131), K PASS, **L FAIL 4 of 345** (28.50 corkscrew straddle, 38.20 frontSingle reach,
  54.10 frontPikeSwan swan, 57.60 backDouble kick-out; .074-.097 m), G1 PASS (median rule; single rows down to 156.9 / 138.3 deg),
  G2 99.9 %, G3 22/22, G4 22/22.
- Blind critic pack (owner-clip pairs, local only): `/Users/midir/sm2-n1/_scratch/critic-C-r01/pack` (12 pairs, key outside the pack:
  `critic-C-r01/pack.key.json`; sources + `pairs.json` in `critic-C-r01/`). The critic has not run.
- Code: WebTravFlips.cpp -- tempo sign alternates per program repeat; reach / kick-out play back and forth past the program end;
  `-WHTrickWarm=<s>` skips world rendering outside the dump window. make_flip_shapes.py -- reach / kick-out march (legs a quarter cycle
  apart, even foot-height steps `_LEG_A.._LEG_D`), swan right-arm windmill + left stag, pencil tuck-up, twist arm drive.
- Next (L): the 4 remaining slow samples; `SCAN=1 limb_sim.py --validate` on the round's telemetry lists the weak phases (kick-out of the
  back programs, swan 0.5-0.9, pencil 0.4-0.6). Any clip change needs `STEPS=traversal` + a probe + a full 4-window re-render (~2 holds;
  the movie dump runs at ~1.4 frames/s, rendering itself ~15 fps).
- Traversal requests: `REQUEST-traversal.md` items 1-6 (ChooseTrick hook still not wired; r26 T4 fallCalm note).

## How to rebuild / capture (all engine work inside `gpu_slot.sh capture --label tricks`)
- C++: `unreal/WebHomage/Scripts/build_editor.sh` (no engine of this worktree running). A C++ change made while a hold's content build runs:
  `touch /Users/midir/sm2-n1/_scratch/tricks/REBUILD_CPP` -- `probe_reel.py` compiles it first inside the hold.
- Content: `python3 tools/tricks/run_build.py <steps>` (build_manhattan.py with its own 3-instance poll disabled; run it INSIDE a hold).
  Full set after a merge: `city_prep,city_extra,city,traversal,characters,look,map` -- the city step alone took 30 min on 2026-10-03, so a
  full rebuild needs two 40-min holds (`hold_r01d.sh` with `STEPS=`). Flip clips only: `STEPS=traversal` (~2.6 min).
- One hold: `STEPS=traversal RENDER_ANY=1 gpu_slot.sh capture --label tricks -- tools/tricks/hold_r01d.sh` = content steps -> `probe_reel.py`
  (-nullrhi probe of the reel script with telemetry + pose log, route score, `tricks_check.py`, writes `_scratch/tricks/probe_d/VERDICT`) ->
  render the reel windows that have no `DONE` marker while >= 22 min of the hold remain (`capture.sh`, SEGS 0:15,15:30,30:45,45:60.5,
  `-WHTrickWarm=4`). Re-queue with `BUILD=0 PROBE=0 RENDER_ANY=1` to continue the windows; the merge into `round-01/` runs once all 4 exist.
- Offline: `tools/tricks/limb_sim.py <HeroFlips_report.json> --validate <telemetry.csv>` replays the keyed clips (Blender report) on a
  capture's measured pitch / twist and counts L-rule slow samples at every 0.1 s phase (`SCAN=1`: also over arm-lead / leg-lag variants);
  `make_flip_shapes.py` runs headless in ~5 s (`blender -b --factory-startup -P ... -- public/assets/spiderman.glb out.glb report.json`).
- Critic pack: `tools/tricks/make_pairs.py <reel.mp4> <telemetry.csv> docs/night1/traversal/round-26/f4_chain_flips.mp4 <out dir>` then
  `python3 /Users/midir/spider-man-2-astra6/tools/night1/abpack.py <pack> <out dir>/pairs.json` (owner-clip material stays in _scratch).

## Gotchas
- Pollers must not `pgrep -f` / `stop_ue.sh` a string their own command line contains: build the pattern from two pieces
  (`P=/Users/midir/sm2-n1/tri; P="${P}cks"`).
- Queueing a second hold while one runs can acquire the other free slot (the lock allows one slot per process, not per piece): do not.
- The L rule (critic pose.py) samples every 6th telemetry row; synchronous keys put every limb's turnaround at the same instant. Keep
  keyed limbs out of phase (the reach / kick-out march: legs a quarter cycle apart, even foot-height steps).
