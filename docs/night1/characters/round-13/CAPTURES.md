# Round 13: captures (P2 hero skins, the sculpted mask head)

> Fan homage project. Not an official Marvel, Sony or Insomniac game. No affiliation. See `DISCLAIMER.md`.

**Round target (critic r12, single biggest gap):** sculpt the shared mask head (brow, nose bridge, cheek, chin relief); lenses >= 1.6x their r12 width, each with ONE closed raised dark rim >= 6 px at 4K sealed to a curved glossy lens; the 12 px black face seam as raised piping.
Merge gate: the enemy pack at its r10 content (7 enemies in the lineup frame, weapons gripped, fight clip = the unchanged r10 choreography), keep r12's passing lines (piping, CH1, CH6, CH7), Verdant / Saffron / Plum without IP watch items. The owner must approve the suits (`SWATCH_SHEET.jpg`) before any merge.
Numbers: `SPEC_CHECK.md` (every number is read from `evidence/` by `tools/ue_char/suits/spec_check_r13.py`).

**Source.** The REAL game: UE 5.8.3 `-game`, Metal, offscreen (`Scripts/run_game.sh`), through the GPU lock (`gpu_slot.sh capture`), driven by `tools/ue_char/suits/chain_r13.sh`
(`STEPS="build stills lineup pawn orbit hero chase fight crowd"`, `EV=10.0`, snapshot `.chain_r13b_run.sh`). **This folder is the SECOND hold: 2026-10-02 03:20:54 - 03:44:26, 1412 s of hold after 7617 s in the queue, 0 engine crashes, one engine of mine at a time, GPU 0 % before
every run (`evidence/gpu_util_before_runs.txt`); the lock reported `contaminated=true` (no exclusive lock): no frame time here is a performance number.** The content was rebuilt from the committed scripts first inside the hold (`build_fight.sh clean,tex,mat,mesh,citizens,rename,fightclips,abp,map,maps5,skins,skinsmap`, 63 s;
`/Content` is not committed; the compiled C++ `FrameMaterial` field is in the sources). The FIRST hold (00:45 - 01:11, `chainA`, not committed) was rejected after looking at its frames: see "What the first hold got wrong".
**Resolution (disclosed).** 4K stills: output 3840x2160, internal 3840x2160 (`r.ScreenPercentage 100`, `evidence/stills_perf.json`, `evidence/lineup_perf.json`), committed as 4K JPEG (q2) (front, chest, head, head34, headside, lineups) or 1920 px (back);
the measures ran on the lossless PNG originals (scratch dir `$P2_SCRATCH/r13/chainA/v2/stills`). Movies: 1920x1080 output = 1920x1080 internal, `-movie` = every frame dumped at a fixed 1/60 s step, H.264 crf 18-20, each <= 7.3 MB.

| file | map / shot | what |
|---|---|---|
| `stills/skin_<suit>_head_4k.jpg` (8) | Char_Skins, view `head`: 12 deg off the face axis, 1.0 m, FOV 26, aim 164, EV bias +10 | the sculpted head: gates H1, H4, H5, H6 |
| `stills/skin_<suit>_head34_4k.jpg` (8) | view `head34`: the ROUND-12 head framing exactly (25 deg, 1.0 m, aim 160) | lens width against the r12 still (H3); r12 stills of the same view are `round-12/stills/skin_<suit>_head_1080p.jpg` |
| `stills/skin_<suit>_headside_4k.jpg` (8) | view `headside`: profile, 1.25 m, aim 166.5, whole head in frame | nose bump against the head height (H2) |
| `stills/skin_<suit>_front_4k.jpg`, `..._chest_4k.jpg` (8 + 8) | views front (7.85 m, CH1) and chest (1.5 m) | CH1 0.542 - 0.544; the raised-piping / sash / jog measures |
| `stills/skin_<suit>_back_1080p.jpg` (8) | view back | |
| `SWATCH_SHEET.jpg` | composed from the 4K stills (front + back + chest + head of all 8 suits) | **the owner's sheet** |
| `swap_pawn_T_key.mp4` (11.4 s) | Char_SkinsPlay, the PLAYABLE pawn, 7 injected real T presses | swap movie: 7 / 7 presses on the pixels, worst 33 ms |
| `orbit_all_suits.mp4` (11.4 s) | Char_Skins orbit shots | the stage hero orbiting through every suit |
| `hero_run_side.mp4`, `hero_run_34.mp4`, `hero_run_leap_side.mp4`, `hero_run_chase.mp4`, `hero_run_toward.mp4` | Char_Hero shots 1-3 / 6-7 (as round 08) | the stage hero (Tessera, new head): CH6 / CH7 / CH2 instruments |
| `street_fight_wide.mp4` (8.0 s) | Char_Fight shot 0, the round-10 scripted fight, unchanged | `evidence/fight_unchanged_since_r10.txt`: fight script, choreography, weapon fit identical to the r10 commit; exposure identical to r12 (sky 219 / 213 / 203, floor 119 / 113 / 108 of 255 at the same frame) |
| `crowd_tracking.mp4` (8.0 s) | Char_Crowd shot 0, unchanged | |
| `enemy_lineup_4k.jpg`, `enemy_lineup_34_4k.jpg` | Char_Lineup shots 5 (wide) / 6 (3/4), 4K real-time still at 3.0 s | **7 enemies** in frame (bat x 2, pipe x 2, pistol x 2, one unarmed), wall luma 140 (r04 / r12: 208) |

## What changed in the content this round
- **Head** (`tools/ue_char/suit8/hero_head_r13.py`, one numpy script on the hero GLB, run by `build_characters.py` 'prep' before the eyes, so every suit inherits it): the browser egg (8 mm triangles) is refined twice in the face zone (~2 mm), a Gaussian relief field is added in z
  (brow ridge 5.8 mm + glabella, eye sockets -4.2, nose bridge / tip 16 mm / alae / undercut, cheek bones 5.2 + hollows, mouth bulge + groove, chin 6.5), the head is 6 mm wider each side at the eye level, normals are recomputed (delta of welded normals). UVs, weights and the suit paint are untouched.
- **Eyes** (`tools/ue_char/hero_lens_r13.py`): pill / bean lenses 63 mm x 28 mm (r12 38.5 x 17.7 mm), 3 deg tilt, 3.4 mm raised rim 3.6 mm proud, dome 2.6 mm; one closed bezel ring sealed to each lens, buried 0.9 mm in the mask.
- **Rim material per suit** (C++ `FWHHeroSuitEntry::FrameMaterial`, applied by `UWHHeroSuitSubsystem` to the `LensFrame` slot; `build_characters.py` 'skins'): polished silver-gunmetal (base 0.22, metallic 0.9) on near-black hoods (Tessera, Plum, Cinder), dark graphite (0.06) on mid / pale ones.
- **Face seam** (`design.py`): the 2.2 mm INK groove is a raised cord (2.2 mm) in the body colour; the hood is satin (roughness 0.50) and halfway to the crown colour; the crown piping arc and the brow flashes moved up for the bigger lenses; the front glyph is laid in DEEP where it lies on the accent sash (Cinder: cyan on cyan).
- **Suits:** Plum jade / mint -> apricot gold (the r12 critic's "watch Plum"); Verdant / Saffron keep their r12 re-blocks (IP guard P1 - P7 pass, min palette distance 45.0).
- **Enemy pack:** `Char_Lineup` has the grey hood back (7 enemies, 100 cm spacing), a -0.6 EV bias and enemy fill 1.0 lux (r04 / r12 had wall luma 208 in both: the washed-out look is the pale sunlit wall, NOT a leak of the skins-stage EV, measured); everything else (fight, crowd, hero maps, weapons, citizens) is the r10 / r12 content.

## What the first hold got wrong (found by looking at its frames, fixed on CPU before this hold; none of it is in this folder)
1. My lineup `-0.6 EV` block was also pasted into `new_stage()` (one `replace` hit two identical lines): the hero / fight / crowd clips were 0.6 EV darker than r10 / r12 and the CH2 / CH7 colour-mask instrument picked the dark sky up (hero height 0.209, lean nan).
2. The Tessera front still (first, at 2.2 s) was a white mannequin: the 8192 px maps were still streaming (now 3.7 s). 3. The stills run's `-quit` counted from process start (~35 s of start-up): the last 7 stills were lost (now +40 s). 4. One silver rim for every suit lost the rim on mid / pale masks.

## Known problems (honest list)
- Head gates (strict, my own definitions, `head_check_r13.py`): H2 nose bump 8.6 - 10.3 % of the head height (gate 2 %), H3 lens 1.73 - 1.88x r12 (near lens 1.88 - 1.95x), H5 seam pair 49 - 148 luma (gate 20), H6 8 / 8; **H1 6 / 8** (Cinder: near-black hood, Saffron: the seam cord dominates the profile),
  **H4 4 / 8** (rim closed >= 90 % of the angles: Plum, Cinder, Glacier, Sage; Tessera 0.85, Verdant 0.85 / 0.73, Ash 0.60 / 0.52, Saffron 0.75 / 0.56: a polished metal rim reflects the sky and crosses the mask's luma at some angles; the rim reads by eye on all 8, crops in `evidence/measures/head_overlays/`). **3 of 8 suits pass every gate.**
- The lenses are very wide for the face: the far lens of a 25 deg view is foreshortened (far-lens ratio 1.05 - 1.56x) and lies against the head outline (>= 3 px, Cinder 3 px at the 12 deg view); the face wraps (surface 60 deg off the view axis at 70 mm from the midline).
- The Verdant chevron's upper edge has a ~20 px step near the armpit in BOTH the r12 and the r13 chest stills (`jog_verdant.json` 14.4 px at the critic's columns, r12 1.24 px: the measure is idle-phase dependent, the visible step is the same); the Ash armpit stitch smear and the unpiped sash ends of the r12 critic are untouched.
- Grips: pipes / bats lie across a loose fist in the stand idle (the guard idle holds them vertically in front of the face); the brute's pipe butt end shows beside the little finger.
- Lineup exposure is NOT "r10": r10 / r12 are wall 208, this is wall 140 on purpose (the critic r12 called the lineup washed out).

## Evidence (`evidence/`)
`head_check.json` / `head_check.txt` + `measures/head_overlays/*.jpg` (lens masks, midline, the profile's front-most column and chord on every still), `measures/` (relief / sash / jog of the chest stills, CH1, CH2 / CH6 / CH7 of the clips), `ipguard.json`, `seams.json`, `ocr_stills.json`, `regression.txt`,
`swap_latency.json`, `lineup_exposure.json`, `fight_unchanged_since_r10.txt`, `characters_build.log`, `chain.log`, `fold_check.json`, `pawn_*`. Critic pairs: `critic_pairs.json` (28 pairs); the pack is in `/Users/midir/sm2-n1/_scratch/critic-P2-r13/pack` (key outside it).
