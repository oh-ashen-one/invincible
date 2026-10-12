# Round 12: captures (P2 hero skins, raised piping)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.

**Round target (critic r11):** raised piping on all 8 suits with a lit / shadow edge pair on every line, nothing of the net / panel lines showing through the sash or chevron,
no faceted shade patches / weave flip / armpit stair-step, the Verdant chevron jog <= 2 px, Verdant and Saffron re-blocked; every r8 axis re-proven.

**Source.** The REAL game: UE 5.8.3 `-game`, Metal, offscreen (`Scripts/run_game.sh`), one GPU-lock hold (`gpu_slot.sh capture`, 2026-10-01 22:37:54 - 23:00:09, 1335 s, 0 engine crashes,
one engine of mine at a time) running `tools/ue_char/suits/chain_r12.sh` (snapshot `.chain_r12_run.sh`) with STEPS `build stills pawn orbit hero chase fight crowd lineup`:
the content was rebuilt from the committed scripts first, inside the same hold (`build_fight.sh clean,tex,mat,mesh,citizens,rename,fightclips,abp,map,maps5,skins,skinsmap`, exit 0, 65 s;
`/Content` is not committed). Post-processing and every number: `tools/ue_char/suits/post_r12.sh` -> `SPEC_CHECK.md` (`spec_check_r12.py`).
GPU utilisation before every run: `evidence/gpu_util_before_runs.txt` (0 %). Real-time runs carry the frame cap that `run_game.sh` got from another session at 18:12 (non-perf captures capped; movies
are fixed 1/60 s steps either way); no perf claims are made this round.

**Resolution (disclosed).** 4K stills: output 3840x2160, internal 3840x2160 (`r.ScreenPercentage 100`, mode manual: `evidence/stills_perf.json`, `evidence/lineup_perf.json`);
front + chest stills are committed as 4K JPEG (q2), back + head at 1920 px (the measures ran on the lossless 4K PNG originals in the scratch dir).
Movies: 1920x1080, `-movie` = every frame dumped at a fixed 1/60 s step, H.264 crf 18-20.

| file | map / shot | what |
|---|---|---|
| `stills/skin_<suit>_front_4k.jpg` (8) | Char_Skins, view front, **7.85 m** (was 5.6), FOV 40, EV bias +10 | CH1-framed full body: hero 0.541 - 0.545 of the frame height |
| `stills/skin_<suit>_chest_4k.jpg` (8) | view chest, 1.5 m, FOV 30 | S3: the raised piping / sash test view |
| `stills/skin_<suit>_back_1080p.jpg`, `..._head_1080p.jpg` | views back (7.85 m) / head | |
| `SWATCH_SHEET.jpg` | composed from the 4K stills (`swatch_sheet.py`) | owner sheet: front + back + chest of all 8 suits |
| `swap_pawn_T_key.mp4` (11.4 s) | Char_SkinsPlay, the PLAYABLE pawn, 7 injected real T presses | swap movie (kept from r11, re-shot) |
| `orbit_all_suits.mp4` (11.4 s) | Char_Skins orbit shots | the stage hero orbiting through every suit |
| `hero_run_side.mp4` (5.4 s), `hero_run_34.mp4`, `hero_run_leap_side.mp4` | Char_Hero shots 1-3 (as round 08) | stage-hero run side / 3/4 / run -> leap, Tessera r12 |
| `hero_run_chase.mp4` (5.4 s), `hero_run_toward.mp4` | Char_Hero shots 6-7 (as round 08) | chase camera / toward the camera |
| `street_fight_wide.mp4` (8.0 s) | Char_Fight shot 0 (the round-10 scripted fight, unchanged) | hero + 6 enemies, from 0.6 s (texture warm-up trimmed) |
| `crowd_tracking.mp4` (8.0 s) | Char_Crowd shot 0 (unchanged) | civilians past a tracking camera |
| `enemy_lineup_4k.jpg` | Char_Lineup shot 5, 4K real-time still at 3.0 s | the 7-enemy lineup (unchanged content) |

The hero mesh in every map is the round-12 one (torso-side skin weights, `FOLD.md`); the enemies, civilians, fight script and crowd layout are unchanged from round 10.

## Evidence (`evidence/`)
- `measures/`: relief / sash / jog JSON + overlays for every suit and the round-11 baseline of the same views (`relief_check_r12.py`), CH1 (`loco_r12.py ch1`), CH6 / CH7 / CH2 with the
  round-08 instruments on the round-12 AND round-08 clips (`video_checks.py`), the pawn's cadence and start (`loco_r12.py bob|pop|tpop`, telemetry `pawn_telemetry.csv`).
- `tangent_<suit>.json` (normal map vs tangent basis per UV island), `fold_check.json` + `fold_cpu_idle2.2_before_after.jpg` (CPU skinning, `FOLD.md`), `ipguard.json`, `seams.json`,
  `ocr_stills.json`, `regression.txt`, `swap_latency.json`, `characters_build.log`, `chain.log`.

## Earlier pass of this round (not committed as evidence)
A first hold (19:10 - 19:23, `$P2_SCRATCH/r12/chain`, v1 maps) captured stills / pawn / orbit: the net no longer crossed the sash (Tessera probe 135 vs panel 115), but the relief was weak
(Tessera 41 % of line cells >= 20) and the Verdant jog was still 53 px (the first weight smoothing had only moved the fold). That led to v2 / v3: cords x2 with mid-tone net colour,
softer stage fills (0.8 -> 0.5), chest-side arm weights stripped below the armpit, crisp sash ends. The rest of that chain was lost to a script edited while bash ran it.
