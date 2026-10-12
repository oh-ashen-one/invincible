# P5 Combat: handoff after round 04 (PROVISIONAL: written while the capture was still waiting for the GPU; the final version replaces it)

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. See `DISCLAIMER.md`.

Branch `night1/combat`, worktree `~/sm2-n1/combat`. UE MCP port 8775, dev port 5206; nothing here uses the editor or MCP: everything is headless commandlets plus `-game`. P5 owns
`Source/WebHomage/Combat`, `/Game/Combat`, `/Game/Tests/Combat`, `Scripts/build_combat.py`, `docs/night1/combat/`. Scratch: `/Users/midir/sm2-n1/_scratch/combat/` (r04 work: `r04/final1`).

## Update 2026-10-01 07:10 EDT (Claude Sonnet 5.5): round 04 captured

The queued chain never ran (the 02:02 WindowServer reset). Re-run by hand with cap 1: `final_r04.sh /Users/midir/sm2-n1/_scratch/combat/r04c/final <15 still times>` (06:47-07:05, ~18 min, hero = HeroDev proxy), `package_r04.sh`, `critic_pack_r04.sh /Users/midir/sm2-n1/_scratch/critic-P5-r04`
(13 pairs, pairs.json beside `pack/`). Evidence in `round-04/` (facts in `round-04/NOTES.md`). Open items: `final_r04_tessera.sh` (P2's Tessera hero) not run; movie B (no-flare control) diverges from the record at 11.05 s (381 vs 377 events);
`replay_diff.py` cannot read the stills run (`still_events.jsonl`, 15 extra marker events). No critic verdict exists for r04 yet.

## State when this text was written (2026-10-01 01:25 EDT, round 04 resumed by Claude Opus 5.5)

- Merged `origin/Opus-5.5-Loop-Night-1` (1fe4c46: Tessera suit, characters r8-r10, traversal r17) into `night1/combat` (bcaa11f), clean merge, `build_editor.sh` OK.
- The GPU is healthy again (no `PAUSED`, cap 2). The one-hold capture chain is queued in `gpu_slot.sh` (FIFO):
  `final_r04.sh /Users/midir/sm2-n1/_scratch/combat/r04b/final <15 still times>` (chain pid in `.../r04b/final/chain.pid`, log `chain.out`).
  If a successor finds `.../r04b/final/movieA/fight.mp4` + `movieB` + `stills` complete, skip straight to `package_r04.sh` and `critic_pack_r04.sh`.
- Still no round-04 frames when this was written: everything below is unverified on screen until `round-04/measure_r04.md` exists.

## What round 04 changed (all untested on screen until the capture exists)

See `round-04/NOTES.md` when it exists; the code map is unchanged from r03 except:
- `WHCombatFx::Impact`: no disc, no halo sphere, no `Hit()` sparks. N = 6 / 7 / 8 tapered streaks (6 stacked cylinders each, `M_CmbFlare`, additive, no depth test) in the camera image plane, hollow centre (start 0.03 frame widths out),
  length 0.098-0.127 frame widths, hot core 3.5 % of the frame width. `SetCam(P, fov, rot)`; own RNG (`-WHCmbFlare=0` = no starburst, everything else identical: the A/B rerun for `measure_r04.py`).
- `WHEnemy`: `StartTwist` also starts a recoil lean about the knees (`RecAmp` 0.62-0.88 rad = 35-50 deg, 65 % in the contact frame, gone by 0.56 s, biased sideways on the screen by the camera's right axis, passed in `FWHHitIn::CamRight`).
  `SyncActor` composes `Rec * Twist * Tilt`. `TiltNow` is logged per enemy in `fight_frames.jsonl` (16th field).
- `WHCombatDirector::LogRenderRes` (`WH_CMB_RES` log line at frame 40), `WH_CMB_FLARE` per starburst.
- The sim is unchanged since r03 (frozen script `scripts/fight30.json`, record `round-03/ue/record`): the movie must replay 381 / 381 events.

## Run the capture (one hold, ~15-20 min once it has the slot)

```
docs/night1/combat/final_r04.sh /Users/midir/sm2-n1/_scratch/combat/r04/final1 1.87,2.66,3.05,4.34,7.01,7.78,8.22,9.37,10.25,12.52,15.42,15.65,20.04,22.14,26.68   # map rebuild, movie A (starburst), movie B (-WHCmbFlare=0), 15 native 4K stills
docs/night1/combat/package_r04.sh /Users/midir/sm2-n1/_scratch/combat/r04/final1     # -> round-04/ (mp4 <= 15 MB, measurements, stills, strips)
docs/night1/combat/critic_pack_r04.sh /Users/midir/sm2-n1/_scratch/critic-P5-r04     # blind pack
```
Rules that bit (RULES.md): never SIGKILL a rendering engine; `stop_ue.sh` only; one engine at a time; the wrapper's max hold is raised to 5400 s in `final_r04.sh` so that it never SIGKILLs an engine on a timer; watch the movie and
`SIGSTOP` the wrapper before `SIGTERM`-ing a wedged engine (r03 recipe).
