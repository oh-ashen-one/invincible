# Traversal (P3) — round 20 shot list

> Homage fan game. Not an official Marvel, Sony or Insomniac game; no affiliation. Nothing here is meant to infringe.

- Engine: UE 5.8.3, real `-game` (`unreal/WebHomage/Scripts/run_game.sh`, offscreen, `-RenderOffScreen`), map `/Game/Maps/Manhattan` (golden preset, built in this worktree), hero = `/Game/Traversal/HeroDev` dev proxy.
- Reproduce one movie: `SKIP_WARM=1 /Users/midir/sm2-n1/_scratch/gpu/bin/gpu_slot.sh capture --label traversal -- docs/night1/traversal/capture_round.sh docs/night1/traversal/round-20 <name>` (deterministic scripted input, `docs/night1/traversal/scripts/city/<name>.json`).
- Output 1920x1080, 60 fps H.264, **internal resolution 1920x1080** (`r.ScreenPercentage 100`, TSR, Lumen), fixed 1/60 s step (`-benchmark -fps=60 -dumpmovie`), 0.8 s pre-roll cut, no 4K stills this round. Offline fixed-step frames: no real-time frame-rate claim; the GPU was shared (every run `contaminated`).
- Builds: A = `8261138`, B = `8b4d356`, C/D = `40baf8f` (the final round-20 source; differs from B only by the perched-camera 4-point visibility rule).

| Movie | What is pressed | Build |
|---|---|---|
| `a_swing_chain.mp4` | airborne start 24 m over the north-south avenue (x 250), scripted swing chain (release on the rising front, re-press, a flip every 3rd release) | C |
| `c_wallrun_perch.mp4` | swing into the 45 m loft facade, stick into it -> vertical wall run, setback mantle, top-out flip, camera look-up, E -> zip to a roof edge, perch | D |
| `w1_wallrun_tall_zip.mp4` | swing onto the 97 m tower (x 266), long wall run, E at 3.6 s -> zip to the facade top (parapet), perch, E at 6.2 s -> point launch | D |
| `w2_wallrun_side_zip.mp4` | side run along the 97 m tower, E at 3.5 s -> zip to the facade top, perch | D |
| `r1_roofrun_zip.mp4` | c's start, roof run, E at 6.2 s -> zip to the highlighted roof edge, perch | D |
| `f1_flow_backDouble.mp4` | y -560 cross street heading east, a backDouble flow flip on every 2nd release | A |
| `f4_chain_flips.mp4` | same street, a flip on every release (backDouble, frontPikeSwan, corkscrew cycled) | A |
| `s1_high_swing.mp4` | RMB held 48 m over the y -560 street, flies into a tower, vertical wall run, fresh RMB at 5.3 s on the wall | C |
| `x1_rmb_cancel_flip.mp4` | chain, a flip, fresh RMB 1.75 s into the flip (repro: RMB cancels a trick into a swing) | B |
| `x2_rmb_cancel_wall.mp4` | w1 start, side wall run, fresh RMB at 3.2 s on the wall with the stick turned along the run (repro: RMB cancels a wall run) | B |
| `m1_mouse_swing.mp4` | a's chain with real mouse-axis events injected in the hardware form: 40 px/frame right 0.5-2.5 s, 26 px/frame up 3.0-4.0 s | B |

Numbers: `R20_CHECK.txt` (`python3 docs/night1/traversal/r20_checks.py docs/night1/traversal/round-20`) and `R19_CHECK.txt` (flip variation / tuck, `r19_checks.py`).
